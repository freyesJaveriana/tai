# Especificación de infraestructura — U3 identity-access

**Insumos.** Presupuestos y pool de `nfr-design/performance-design.md` (performance-design); controles
de `nfr-design/security-design.md` (security-design); modelo de una réplica y estado compartido de
`nfr-design/scalability-design.md` (scalability-design); *timeouts*, falla cerrada y salud de
`nfr-design/reliability-design.md` (reliability-design); métricas y logs de
`nfr-design/observability-design.md` (observability-design); inventario y entrega a Infrastructure
Design de `nfr-design/logical-components.md` (logical-components); flujos F1–F9 de
`functional-design/functional-spec.md` (functional-spec); procesos y dependencias externas de
`inception/domain-design/components.md` (components); C1, C12, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); D1–D12 y ajustes de
`nfr-requirements/tech-stack-decisions.md`; respuesta P1 de `infrastructure-design-questions.md`;
infraestructura común de U2 (`platform/infrastructure-design/infrastructure-specification.md`).

U3 es el primer Bolt que construye `session-api` (B2). Este documento fija el despliegue del proceso
y lo que U3 necesita de la plataforma; U4–U7 lo amplían en sus diseños sin cambiar su forma.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Modelo de cómputo | Contenedor en un `Deployment` `session-api` del namespace `veridicus`; Uvicorn con **1 proceso** por pod (D1) | Un pod por réplica es fácil de dimensionar (NFR8.1) |
| Réplicas | **1** en `values-cpu.yaml` y `values-gpu.yaml`; cambiarlo es un PR. Sin HPA ni KEDA para `session-api` | scalability-design §1: ≤ 20 sesiones web y ≤ 10 inicios simultáneos |
| Imagen | `ghcr.io/<repo>/session-api@sha256:…`, construida en varias etapas sobre `python:3.12-slim` fijada por digest; usuario sin root (UID 10001); incluye `contracts/` (C1 y catálogo de límites) y `data/common-passwords.txt`, cuyos SHA-256 comprueba el arranque | NFR10.2, NFR10.9 (el mapa de rutas sale de C1 empaquetado) |
| Puertos | `http` 8080 (API, `/healthz`, `/readyz`) y `metrics` 8081 (solo `/metrics`) | logical-components §4: Prometheus por un puerto distinto del de la API |
| Entrada | Ruta `/api/` del `Ingress` de U2 (TLS con `mkcert`, `veridicus.local`) | La cookie `Secure` exige HTTPS (security-design §4) |
| Dirección de origen | `VERIDICUS_TRUSTED_PROXY=10.244.0.0/16` (*pod CIDR* de Calico) | Solo los pods de `ingress-nginx` alcanzan el puerto 8080 (§3), así que solo ellos pueden fijar `X-Forwarded-For` |
| Sistema de archivos | `readOnlyRootFilesystem: true` y `emptyDir` en memoria para `/tmp`; el *helper* de seguridad de U2 | NFR10.2 de U2 |
| Estrategia | `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0` | Sin corte; las sesiones viven en PostgreSQL (reliability-design §4) |
| Configuración | `ConfigMap` `session-api-config` con los ajustes `VERIDICUS_*` de §2; Secrets por `secretKeyRef` | Una configuración faltante impide arrancar (D2) |
| Entornos | Máquina de desarrollo y máquina GPU, mismo chart y mismos valores para U3 | U3 no usa GPU |

### 1.1 Recursos (NFR8.1, NFR3.1)

| Contenedor | `requests` CPU / memoria | `limits` CPU / memoria | Por qué |
|---|---|---|---|
| `session-api` | 0,5 / 384 MiB | 2 / 768 MiB | Base del proceso FastAPI + SQLAlchemy ≈ 200 MiB, más 2 × 64 MiB de Argon2id del semáforo (≥ 160 MiB, logical-components §4), más margen; 2 CPU permiten 2 verificaciones a la vez dentro del p95 de 1 s. U4–U7 revisan estos valores |
| `create-admin-job` | 0,1 / 128 MiB | 0,5 / 256 MiB | Un Argon2id de 64 MiB |

### 1.2 Sondas (P1 = B)

| Sonda | Ruta | Frecuencia y fallos | Qué comprueba |
|---|---|---|---|
| `startupProbe` | `/healthz` | Cada 2 s, hasta 30 fallos (60 s) | El proceso arrancó (configuración validada antes de crear la aplicación) |
| `livenessProbe` | `/healthz` | Cada 10 s, *timeout* 1 s, 3 fallos | El proceso atiende; no toca dependencias |
| `readinessProbe` | `/readyz?probe=kubernetes` | Cada 5 s, *timeout* 2 s, 2 fallos | Configuración cargada y `SELECT 1` en ≤ 1 s; **no** consulta Redis |
| `scripts/smoke.sh` y monitoreo | `/readyz` | En cada despliegue y cada 30 s desde Prometheus | Todo lo de C16: configuración, base y Redis |

Con Redis caído el pod sigue en el Service: el inicio de sesión responde `503` `system.unavailable`
porque el limitador no puede comprobar (falla cerrada, NFR10.12), el envío de turnos de U4 también
responde `503`, y las sesiones abiertas, la revisión de alertas y la consulta de reportes siguen.
Con PostgreSQL caído el pod sale del Service, como antes.

```python
@router.get("/readyz", include_in_schema=False)
def readyz(probe: Literal["full", "kubernetes"] = "full") -> JSONResponse:
    checks = [check_config(), check_db(timeout_s=1.0)]
    if probe == "full":
        checks.append(check_redis(timeout_s=0.5))
    ok = all(c.ok for c in checks)
    return JSONResponse(ready_body(checks), status_code=200 if ok else 503)
```

## 2. Servicios de infraestructura que usa U3

| Servicio | Rol | Configuración para U3 | Notas |
|---|---|---|---|
| `veridicus-pg` | database | Rol `veridicus_app` en `veridicus-pg-rw:5432`, `sslmode=verify-full` con la CA `veridicus-pg-ca`; pool `pool_size 5`, `max_overflow 5`, `pool_timeout 2 s`, `pool_pre_ping`, `pool_recycle 1 800 s`; `statement_timeout 2 000 ms` y `connect_timeout 2 s` | Con 1 réplica, ≤ 10 de las 50 conexiones de la base (scalability-design §3) |
| Esquema de U3 | database | Tablas `app_user`, `web_session`, `user_change` y los índices de performance-design §3, creadas por Alembic en `migrations-job` con el rol `veridicus_owner`; la migración concede a `veridicus_app` solo `INSERT, SELECT` en `user_change` | El dueño distinto hace efectivo el `REVOKE` (NFR11.1) |
| `veridicus-redis` | cache (contadores) | `redis-py` con `socket_timeout 0,5 s`; claves `veridicus:auth:fail:*` que caducan a los 900 s; Redis 7.2 (≥ 7.0 para `EXPIRE NX`) | Despreciable en memoria (scalability-design §3) |
| `ingress-nginx` | load-balancer | Ruta `/api/`; no guarda en caché, así que `Cache-Control: no-store` llega intacto al navegador | NFR10.10 |
| `queue`, `search`, `cdn` | — | U3 no los usa | — |

### 2.1 Configuración y Secrets

| Ajuste | Valor | Viene de |
|---|---|---|
| `VERIDICUS_SESSION_IDLE_SECONDS` / `VERIDICUS_SESSION_MAX_SECONDS` | 1800 / 43200 | `ConfigMap`; deben coincidir con `web_session_idle_s` y `web_session_max_age_s` del catálogo de U1, y el arranque falla si difieren |
| `VERIDICUS_ARGON2_MEMORY_KIB`, `_TIME_COST`, `_PARALLELISM` | 65536, 3, 1 | `ConfigMap` |
| `VERIDICUS_ARGON2_QUEUE_SECONDS` | 5 | `ConfigMap` |
| `VERIDICUS_LOGIN_MAX_FAILURES`, `VERIDICUS_LOGIN_WINDOW_SECONDS` | 5, 900 | `ConfigMap` |
| `VERIDICUS_TRUSTED_PROXY` | `10.244.0.0/16` | `ConfigMap` |
| Usuario y contraseña de `veridicus_app` | — | Secret `veridicus-pg-app` |
| Contraseña de Redis | — | Secret `veridicus-redis` |
| `VERIDICUS_RATE_LIMIT_HMAC_KEY` (≥ 32 bytes) | — | Secret `veridicus-auth` |
| `VERIDICUS_BOOTSTRAP_ADMIN_USERNAME` / `_PASSWORD` | — | Secret `veridicus-bootstrap-admin`, montado **solo** en `create-admin-job` |

Todos los Secrets los crea el humano con `scripts/create-secrets.sh` desde su `.env` (U2).

### 2.2 `create-admin-job` (F7, NFR10.8, NFR10.14)

| Campo | Valor |
|---|---|
| Imagen | La misma de `session-api`, por digest |
| Orden | `python -m session_api.cli.create_admin` |
| Plantilla | `deploy/veridicus/charts/create-admin-job/`, renderizada solo con `createAdmin.enabled=true` (desactivado por defecto) |
| Ejecución | `restartPolicy: Never`, `backoffLimit: 0`, `activeDeadlineSeconds: 120`, `ttlSecondsAfterFinished: 600`, sin token de cuenta de servicio |
| Quién la aplica | El humano, una sola vez, tras fusionar su PR; fuera de la `Application` de Argo CD; nunca la CI |
| Resultado | Código 0 si creó el `admin`; código 2 si ya había uno (sin cambios) |

### 2.3 Tareas en segundo plano

El barrido diario de `web_session` (NFR8.3) corre **dentro** de `session-api` con
`pg_try_advisory_lock`, no como `CronJob`: no necesita otro pod ni otra imagen, y con varias réplicas
solo una lo ejecuta (scalability-design §2).

## 3. Red de `session-api` para U3 (NFR1.1)

| Dirección | Origen o destino | Puerto |
|---|---|---|
| Entrada | Namespace `ingress-nginx` | 8080 |
| Entrada | Namespace `monitoring` (módulo 8) | 8081 |
| Salida | `veridicus-pg` | 5432 |
| Salida | `veridicus-redis` | 6379 |
| Salida | CoreDNS | 53 UDP/TCP |

U3 no llama a ningún modelo ni a internet; la salida a `veridicus-embeddings` la añade U4 en la misma
política. `create-admin-job` solo sale a `veridicus-pg:5432`.

## 4. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| Proceso y `Deployment` de `session-api` | U3 (forma del despliegue, sondas, base de recursos) | U4–U7 | Cada unidad añade su configuración, su salida de red y su parte de memoria por PR; las sondas no cambian |
| `veridicus-pg`, `veridicus-redis`, `Ingress` | U2 | U3 entre otras | Ver la tabla de infraestructura compartida de U2 |

## 5. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C16) | `/readyz` acepta `probe=kubernetes`, que omite Redis; la sonda de disponibilidad de Kubernetes usa esa variante y `scripts/smoke.sh` y el monitoreo usan la completa | P1 = B |
| `identity-access/nfr-requirements/reliability-requirements.md` (NFR10.13) y `nfr-design/reliability-design.md` §2–§3 | Con Redis caído, `/readyz?probe=kubernetes` responde `200` y solo el `/readyz` completo responde `503`; el radio de impacto de Redis vuelve a ser «usuarios que intentan entrar» (logical-components §2) | P1 = B; hallazgo R-01 de NFR Design |
| `identity-access/nfr-design/security-design.md` §5 | `VERIDICUS_TRUSTED_PROXY` toma el *pod CIDR* `10.244.0.0/16`, y la clave por dirección agrupa a todos los navegadores de la máquina de la demostración (ver monitoring-design §3) | Topología de Minikube de U2 |
| `identity-access/nfr-requirements/tech-stack-decisions.md` §2 | El arranque comprueba que las duraciones de sesión coinciden con el catálogo de límites de U1 | Hallazgo R-07 de NFR Design |
