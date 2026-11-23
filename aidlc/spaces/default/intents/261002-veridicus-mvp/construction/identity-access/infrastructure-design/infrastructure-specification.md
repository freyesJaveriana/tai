# Especificación de infraestructura — U3 identity-access

**Revisión 2 (2026-11-23), segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2 de U3.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Se mantienen:** 1 proceso Uvicorn y 1 réplica, puertos 8080 y 8081, recursos base de `session-api`,
  `RollingUpdate` sin indisponibilidad, barrido de sesiones dentro del proceso, falla cerrada.
- **Cambian:** la sonda de disponibilidad usa el `/readyz` completo (P1 = B queda «Retirado»); nombres de
  recursos y de Secrets alineados con U2; `create-admin` pasa a `deploy/jobs/`; una sola máquina.
- **Nuevos:** rol `veridicus_app` en `managed.roles` (§2.4), anotaciones sin disco del Ingress (§2),
  cierre de los hallazgos de `reviews/review-01.md` (§6).
- **Sin preguntas** en esta pasada (`infrastructure-design-questions.md`); lo que precisa artefactos
  aprobados o pide algo a U2 está en §5 (IDS-U3-01 a IDS-U3-14).

**Insumos.**
- De esta unidad, en `nfr-design/` (revisión 2): presupuestos y *pool* de `performance-design.md`
  (performance-design); frontera, `GuardedRoute`, Secrets, usuarios de base y `create-admin` de
  `security-design.md` (security-design); una réplica y estado compartido de `scalability-design.md`
  (scalability-design); *timeouts*, falla cerrada y salud de `reliability-design.md`
  (reliability-design); métricas y logs de `observability-design.md` (observability-design); inventario,
  radio de impacto y entrega a Infrastructure Design de `logical-components.md` (logical-components).
- Flujos F1, F2, F7 y F13 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Procesos y dependencias externas de `inception/domain-design/components.md` (components).
- C1, C12, C16, C23 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- D1–D17 y ajustes de `nfr-requirements/tech-stack-decisions.md` (revisión 2).
- NFR Design de U2, revisión 2 (`construction/platform/nfr-design/security-design.md`): red, Ingress sin
  disco, Secrets, volúmenes, `deploy/jobs/`, observabilidad.
- Supuesto de máquina del 2026-11-22: una sola máquina de 64 GB, solo CPU, tamaño de Minikube por
  decidir en U2 (IDS-U3-02).

U3 es el primer Bolt que construye `session-api` (B2). Este documento fija la forma del despliegue del
proceso y lo que U3 necesita de la plataforma; U4–U9, U12 y U13 la amplían en sus diseños sin cambiarla.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Modelo de cómputo | Contenedor `session-api` en el `Deployment` `veridicus-session-api` del namespace `veridicus`; Uvicorn con **1 proceso** por pod (D1), `--no-access-log` | Un pod por réplica es fácil de dimensionar (NFR8.1); el log de acceso de Uvicorn no pasa por la lista blanca (NFR10.7) |
| Réplicas | **1** en el archivo de valores de la máquina única de U2; cambiarlo es un PR. Sin HPA ni KEDA para `session-api` | scalability-design §1: ≤ 20 sesiones web y ≤ 10 inicios simultáneos |
| Imagen | `ghcr.io/<repo>/session-api@sha256:…`, varias etapas sobre `python:3.12-slim` fijada por digest; usuario sin root (UID y GID 10001). Instala `veridicus-contracts` (C1 y C25 se leen del paquete con `importlib.resources`, D14) y lleva la lista de D15 con su `SHA256SUMS`, que el arranque comprueba | NFR10.2, NFR10.9, NFR10.16 |
| Puertos | `http` 8080 (API `/api/v1`, `/healthz`, `/readyz`) y `metrics` 8081 (solo `/metrics`, servidor propio en un hilo) | logical-components §4; NFR10.23 |
| `Service` | `veridicus-session-api`, `ClusterIP`, puertos `http` y `metrics` | El Ingress solo apunta a `http`; el `ServiceMonitor` a `metrics` |
| Entrada | Ruta `/api/` del `Ingress` `veridicus-web` de U2, con TLS (`veridicus-tls`, `ssl-redirect`, HSTS) y sin disco (§2) | La cookie `Secure` exige HTTPS (security-design §5); NFR10.22 |
| Dirección de origen | `VERIDICUS_TRUSTED_PROXY` = pod CIDR de `deploy/network-ranges.yaml` de U2 (hoy `10.244.0.0/16`, Calico), nunca vacío | Solo `ingress-nginx` alcanza el puerto 8080 (§3); NFRD-U3-06; IDS-U3-14 |
| Sistema de archivos | `readOnlyRootFilesystem: true` con el *helper* `_securityContext.tpl` de U2; `/tmp` como `emptyDir` `medium: Memory`, `sizeLimit: 16Mi` (cuenta en el `limit`) | NFR11.4: la configuración no se escribe en ejecución; IDS-U3-11 |
| Identidad del pod | `ServiceAccount` `veridicus-session-api` sin `Role` ni `ClusterRole`; `automountServiceAccountToken: false` | NFR10.9 de U2 |
| Estrategia | `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0`; sin `PodDisruptionBudget` (con 1 réplica bloquearía el drenado del nodo) | Las sesiones viven en PostgreSQL (reliability-design §5) |
| Configuración | `ConfigMap` `veridicus-session-api-config` con los ajustes `VERIDICUS_*` de §2.1; Secrets por `secretKeyRef` o como archivo | Una configuración faltante impide arrancar (D2, `team.md`) |
| Entornos | **Una sola máquina** (equipo propio del humano, 64 GB, solo CPU, Minikube sobre WSL2); sin máquina ni perfil GPU | Cambio del 2026-11-22; tamaño de Minikube en U2 (IDS-U3-02) |
| IaC | Subchart `session-api` del chart paraguas `deploy/veridicus` de U2; `create-admin` en `deploy/jobs/` | El humano aplica lo fusionado (AUTONOMIA-01) |

### 1.1 Recursos (NFR8.1, NFR3.1)

| Contenedor | `requests` CPU / memoria | `limits` CPU / memoria | Por qué |
|---|---|---|---|
| `session-api` (parte de U3) | 0,5 / 384 MiB | 2 / 768 MiB | Base del proceso FastAPI + SQLAlchemy + validadores compilados de C1 ≈ 220 MiB; Argon2id 2 × 64 MiB = 128 MiB más 32 MiB de margen = 160 MiB (logical-components §4; cierra R-05); `/tmp` 16 MiB; resto de margen. 2 CPU permiten las 2 verificaciones del semáforo dentro del p95 de 1 s. U4–U13 suman su parte por PR |
| `create-admin` | 0,1 / 128 MiB | 0,5 / 256 MiB | Un Argon2id de 64 MiB y una conexión |

Con una máquina de 64 GB la parte de U3 no condiciona el tamaño de Minikube; U2 lo fija sumando las
partes de cada unidad (IDS-U3-02).

### 1.2 Sondas (NFR10.13, C16)

| Sonda | Ruta | Frecuencia y fallos | Qué comprueba |
|---|---|---|---|
| `startupProbe` | `/healthz` en `http` | Cada 2 s, hasta 30 fallos (60 s) | El proceso arrancó tras las comprobaciones de security-design §3.1 |
| `livenessProbe` | `/healthz` en `http` | Cada 10 s, *timeout* 1 s, 3 fallos | El proceso atiende; no toca dependencias, así que una caída de Redis o de la base no reinicia el pod |
| `readinessProbe` | `/readyz` en `http` | Cada 5 s, *timeout* 2 s, 2 fallos, 1 éxito para volver | `SELECT 1` (≤ 1 s) y `PING` (≤ 0,5 s); `access_log` y `pending_sessions` solo informan |
| `scripts/smoke.sh` | `/healthz` y `/readyz` | Tras cada despliegue | El mismo `/readyz`; cómo llega lo fija U2 (IDS-U3-06) |

La variante `/readyz?probe=kubernetes` de la revisión 1 queda **Retirado** (IDS-U3-01). Con Redis caído,
tras unos 10 s el único pod sale del Service y el Ingress responde `503` en toda la consola; vuelve solo
cuando Redis responde, sin reinicios (reliability-design §2, logical-components §2). Con PostgreSQL caído
pasa lo mismo.

## 2. Servicios de infraestructura que usa U3

| Servicio | Rol | Configuración para U3 | Notas |
|---|---|---|---|
| `veridicus-pg` (CloudNativePG) | database | Usuario `veridicus_app` en `veridicus-pg-rw:5432`, `sslmode=verify-full` con la CA del operador; *pool* `pool_size 5`, `max_overflow 5`, `pool_timeout 2 s`, `pool_pre_ping`, `pool_recycle 1 800 s`; `statement_timeout` 2 000 ms por conexión y `connect_timeout` 2 s | ≤ 10 conexiones por réplica, ≤ 20 durante un `RollingUpdate` (scalability-design §3) |
| Esquema de U3 | database | `app_user`, `web_session`, `user_change`, el `DOMAIN` `veridicus_actor_system` y `veridicus_apply_audit_grants()`, creados por Alembic en el `Job` de migraciones con `veridicus_owner`; la función concede los permisos desde la marca `veridicus-audit` y la migración suma `DELETE` sobre `web_session` | security-design §9; NFR11.1, NFR11.3 |
| `veridicus-redis` | cache (contadores del limitador) | `redis-py` con `socket_timeout` y `socket_connect_timeout` de 0,5 s; claves `veridicus:auth:fail:*` que caducan a los 900 s; scripts Lua por `EVALSHA` | Sin `EXPIRE NX`: los scripts no dependen de la versión 7 (security-design §6) |
| `ingress-nginx` | load-balancer | `Ingress` `veridicus-web`, ruta `/api/` → `veridicus-session-api:http`; `proxy-request-buffering: "off"`, `proxy-buffering: "off"`, `proxy-max-temp-file-size: "0"`, `proxy-body-size` del grupo (2 113 536 bytes); `use-forwarded-headers` en su valor por defecto (`false`) | Ningún cuerpo toca el disco (NFR10.22); sin caché, así que `Cache-Control: no-store` llega intacto (NFR10.10); el `413` lo da `session-api` |
| `queue`, `search`, `cdn` | — | U3 no los usa | — |

### 2.1 Configuración y Secrets

| Ajuste | Valor | Viene de |
|---|---|---|
| `VERIDICUS_ARGON2_MEMORY_KIB`, `_TIME_COST`, `_PARALLELISM` | 65536, 3, 1 | `ConfigMap` |
| `VERIDICUS_ARGON2_MAX_CONCURRENT`, `VERIDICUS_ARGON2_QUEUE_TIMEOUT_S` | 2, 5 | `ConfigMap` |
| `VERIDICUS_LOGIN_MAX_FAILURES`, `VERIDICUS_LOGIN_WINDOW_SECONDS` | 5, 900 | `ConfigMap` |
| `VERIDICUS_DB_STATEMENT_TIMEOUT_MS`, `VERIDICUS_REDIS_TIMEOUT_MS` | 2000, 500 | `ConfigMap` |
| `VERIDICUS_ACCESS_LOG_TIMEOUT_MS`, `VERIDICUS_WEB_SESSION_PURGE_DAYS` | 500, 7 | `ConfigMap` |
| `VERIDICUS_TRUSTED_PROXY` | Pod CIDR de `network-ranges.yaml` | `ConfigMap`, renderizado desde el archivo de U2 |
| Host, base y modo TLS de PostgreSQL; host de Redis | `veridicus-pg-rw`, `verify-full`; `veridicus-redis` | `ConfigMap` |
| `VERIDICUS_LIMIT_WEB_SESSION_*` | Sin valor: rigen las cifras de C25 | Solo podrían bajarlas (security-design §5.1) |
| Usuario y contraseña de `veridicus_app` | — | Secret `veridicus-db-app` (tipo `kubernetes.io/basic-auth`), el mismo que usa `managed.roles` (§2.4) |
| Contraseña de Redis | — | Secret `veridicus-redis-auth`, montado como archivo en solo lectura, como el resto de clientes de U2 |
| `VERIDICUS_RATE_LIMIT_HMAC_KEY` (≥ 32 bytes) | — | Secret `veridicus-auth`, solo en `session-api` |
| `VERIDICUS_BOOTSTRAP_ADMIN_USERNAME` / `_PASSWORD` | — | Secret `veridicus-bootstrap-admin`, **solo** en `create-admin`; se borra tras el primer uso (§2.2) |

Todos los Secrets los crea el humano con `scripts/create-secrets.sh` de U2 desde su `.env`; el *script*
no aplica nada. Los nombres de la revisión 1 `veridicus-pg-app` y `veridicus-redis` quedan «Retirado»
(IDS-U3-04).

### 2.2 `create-admin` (F7, NFR10.8, NFR10.14, AUTONOMIA-01)

| Campo | Valor |
|---|---|
| Imagen | La de `session-api`, por digest |
| Orden | `python -m session_api.cli.create_admin` |
| Manifiesto | `Job` `veridicus-create-admin` en `deploy/jobs/create-admin.yaml`, fuera de la `Application` de Argo CD; la bandera `createAdmin.enabled` de la revisión 1 queda «Retirado» |
| Ejecución | `restartPolicy: Never`, `backoffLimit: 0`, `activeDeadlineSeconds: 120`, `ttlSecondsAfterFinished: 3600`, sin token de cuenta de servicio, mismo *helper* de seguridad |
| Secrets | `veridicus-db-app` y `veridicus-bootstrap-admin` |
| Red | Salida solo a `veridicus-pg:5432` y a `kube-dns` por 53 UDP/TCP (cierra R-07) |
| Quién lo aplica | El humano, una vez, tras fusionar el PR que lo trae (aprobación registrada); nunca la CI ni Argo CD |
| Resultado | Código 0 y `bootstrap.admin_created`; código 2 y `bootstrap.admin_exists` si ya hay un `admin` activo, sin cambios |
| Después | El humano borra el Secret `veridicus-bootstrap-admin` y quita las dos líneas de su `.env` (cierra R-04); la contraseña del primer `admin` la cambia ese usuario si la consola lo ofrece, o queda solo en su gestor de contraseñas |

### 2.3 Tareas en segundo plano

El barrido de `web_session` (NFR8.3, D17) corre **dentro** de `session-api`, al arrancar y cada 24 h,
en lotes de 1 000 con `pg_try_advisory_xact_lock`, no como `CronJob` (NFR10.5 de U2 prohíbe todo
`CronJob`). Con dos pods durante un `RollingUpdate`, solo uno borra cada lote (scalability-design §2).

### 2.4 Usuario `veridicus_app` en CloudNativePG (D16, NFR10.19)

El `Cluster` `veridicus-pg` es de U2. U3 pide su entrada en `managed.roles` (§ siguiente) y nada más: la
migración solo concede permisos y ninguna contraseña llega a `db/migrations/` (security-design §9.3).
El rol no fija parámetros propios: el `statement_timeout` lo pone el cliente por conexión y el plazo de
inactividad en transacción, cuando una unidad lo necesita, se fija por transacción con `SET LOCAL`, nunca
en el rol ni en el `Cluster` (IDS-U3-05).

## Fragmento: entrada de `managed.roles` para `veridicus_app`

```yaml
managed:
  roles:
    - name: veridicus_app
      ensure: present
      login: true
      superuser: false
      createdb: false
      createrole: false
      replication: false
      bypassrls: false
      connectionLimit: 25        # 2 pods x (5 + 5) en RollingUpdate + create-admin + margen
      passwordSecret:
        name: veridicus-db-app
```

## 3. Red de `session-api` para U3 (NFR1.1, AUTONOMIA-04)

| Dirección | Origen o destino | Puerto | Nota |
|---|---|---|---|
| Entrada | `ingress-nginx` (namespace `ingress-nginx`) | 8080 | Fila de `deploy/network-deps.yaml` de U2 |
| Entrada | Prometheus (namespace `monitoring`, SHOULD) | 8081 | Solo el puerto `metrics` |
| Entrada | Sondas del kubelet desde el nodo | 8080 | Calico admite por defecto el tráfico del nodo hacia sus pods; no hace falta regla y lo confirma la verificación manual de U2 (cierra R-07) |
| Salida | `veridicus-pg` (primaria) | 5432 | TLS `verify-full` |
| Salida | `veridicus-redis` | 6379 | Con contraseña |
| Salida | `kube-dns` | 53 UDP/TCP | Todos los pods |

U3 no llama a ningún modelo, al anonimizador ni a internet: nada sale del clúster. La salida a
`audio-worker` la añade U9 en la misma política. `create-admin` solo sale a `veridicus-pg:5432` y a
`kube-dns` (§2.2). Cada fila tiene su regla y ninguna regla sobra (`check-network-deps.sh` de U2).

## 4. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| Proceso, `Deployment` y `Service` `veridicus-session-api` | U3 (forma del despliegue, sondas, base de recursos, *helper* de seguridad) | U4–U9, U12, U13 | Cada unidad añade su configuración, su salida de red, sus volúmenes de la tabla cerrada de U2 y su parte de memoria por PR; las sondas, los puertos y la estrategia no cambian |
| Esquema de auditoría (`DOMAIN`, `veridicus_apply_audit_grants()`) | U3 | Toda unidad con tablas | Cada migración llama a la función al final; un actor nuevo entra por PR con el YAML y el dominio |
| `veridicus-pg`, `veridicus-redis`, `Ingress`, `network-ranges.yaml`, `secret-consumers.yaml` | U2 | U3 entre otras | Tablas de infraestructura compartida y políticas de U2 |
| `Job` de migraciones | U2 (manifiesto), cada unidad (migraciones) | U3 crea el primer esquema | Usuario `veridicus_owner`; PR propio (`project.md`) |

## 5. Precisiones a artefactos ya aprobados (IDS-U3-xx)

No edité ningún artefacto aprobado; en la aprobación decides cuáles se llevan al original, cada una en
su propio commit. Las peticiones a U2 se incorporan en su Infrastructure Design o en el PR de B2.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| IDS-U3-01 | Revisión 1 de esta etapa (P1 = B y sus precisiones sobre C16 y NFR10.13) | La `readinessProbe` usa el `/readyz` completo; `probe=kubernetes` queda «Retirado». Las dos precisiones de la revisión 1 se retiran sin llevarse a C16 ni a NFR10.13 | NFR10.13 revisión 2, C16 v2, reliability-design §2 y logical-components §4 aprobados después; `project.md` (NFRD-U6-08); cierra R-01 a y R-03 |
| IDS-U3-02 | Revisión 1 de esta etapa (§1 «Entornos», `values-gpu.yaml`) y `team.md` (Deployment, «dos máquinas») | Una sola máquina de 64 GB, solo CPU; U3 no usa archivo de valores GPU. El tamaño de Minikube y el nombre del archivo de valores los fija U2 | Cambio de máquinas del 2026-11-22; brief de la etapa |
| IDS-U3-03 | NFR Design de U2 §7.3 («contenedor `api` de `session-api`») | **Petición a U2:** `Deployment` y `Service` `veridicus-session-api`, contenedor `session-api`. La frase de U2 se lee como ese contenedor. Coincide con la línea `kubectl exec deploy/veridicus-session-api -c session-api` de U13 que entra en `readonly-exec-allowlist.yaml` | `team.md` (prefijo `veridicus-`); NFR Design de U13 |
| IDS-U3-04 | NFR10.13 de U2 y `secret-consumers.yaml` | **Petición a U2:** la tabla cerrada suma `veridicus-auth` (solo `session-api`) y `veridicus-bootstrap-admin` (solo `create-admin`), con un control negativo cada uno (`veridicus-auth` en `semantic-agent`; `veridicus-bootstrap-admin` en `session-api`) | logical-components §4; NFR10.5, NFR10.8 |
| IDS-U3-05 | NFR Design de U2 §7.1 (`managed.roles`) | **Petición a U2:** la entrada de `veridicus_app` del fragmento de §2.4, con `connectionLimit: 25` y sin parámetros de rol; debe caber en el `max_connections` que fije U2 junto con `veridicus_owner` y `veridicus_retention` | D16; NFRD-U7-01 (plazo por transacción); scalability-design §3 |
| IDS-U3-06 | C16 y NFR10.17 de U2 («puerto interno que no expone el Ingress»); `check-ingress-routes.sh` de U2 | `/healthz` y `/readyz` viven en la raíz del puerto 8080 (logical-components §4); el Ingress solo enruta `/api/`, así que no son alcanzables desde el navegador. La comprobación «`/api/v1/healthz` llega a `session-api`» se cumple con el `404` `route.not_found` en Problem Details (NFRD-U3-10), distinto del `404` HTML de nginx. **Petición a U2:** `smoke.sh` consulta `/readyz` de `session-api` con `kubectl port-forward` al `Service` (solo lectura, fuera de los verbos prohibidos) | Cierra R-01 b; logical-components §4 |
| IDS-U3-07 | `functional-spec.md` (F7) y security-design §8 | Tras `bootstrap.admin_created`, el humano borra `veridicus-bootstrap-admin` y lo quita del `.env` | Cierra R-04 |
| IDS-U3-08 | logical-components §4 («≥ 160 MiB») | 160 MiB = 2 × 64 MiB de Argon2id + 32 MiB de margen | Cierra R-05 |
| IDS-U3-09 | `cicd-pipeline.md` de la revisión 1 (*job* `test-perf`) | El *workflow* corre en el *runner* estándar de GitHub para repositorios públicos (`ubuntu-24.04`, 4 vCPU). Una falla de rendimiento sospechosa de inestable se pone en cuarentena con un *issue* enlazado; nunca se reintenta ni se baja el umbral | `team.md` (Testing Posture); cierra R-08 |
| IDS-U3-10 | Revisión 1 de `monitoring-design.md` (`PrometheusRule` en el subchart `session-api`, panel en `deploy/veridicus/dashboards/`) | Las reglas y el panel de U3 viven en `charts/monitoring-rules/` de U2, con su prueba `promtool`; las rutas de la revisión 1 quedan «Retirado» | NFR Design de U2 §11 |
| IDS-U3-11 | Revisión 1 de esta etapa (`/tmp` sin tope) | `/tmp` en memoria con `sizeLimit: 16Mi`, contado en el `limit`. `session-api` no escribe archivos temporales propios (security-design §2.3); el tope solo acota bibliotecas | NFR Design de U2 §5 («el `emptyDir` en memoria cuenta en el `limit`») |
| IDS-U3-12 | Revisión 1 de esta etapa (§2.2) | `create-admin` en `deploy/jobs/create-admin.yaml` con `activeDeadlineSeconds: 120` y `ttlSecondsAfterFinished: 3600`; sale a la base y a DNS | security-design §8; NFR10.16 de U2; cierra R-07 |
| IDS-U3-13 | Revisión 1 de esta etapa (§3) | Las sondas del kubelet no necesitan regla con Calico; si U2 eligiera otro CNI, la política de `session-api` debe admitir el rango del nodo en 8080 | Cierra R-07 |
| IDS-U3-14 | NFR10.5 y security-design §6 (contador por origen) | `VERIDICUS_TRUSTED_PROXY` se renderiza desde `network-ranges.yaml` de U2. Riesgo que se mantiene: en Minikube sobre WSL2 todos los navegadores llegan con la misma dirección, así que 5 fallos de cualquiera bloquean a todos 15 min; con un analista en la demostración se acepta y `VeridicusLoginThrottling` lo deja visible | Cierra R-06; riesgo ya aceptado en la revisión 1 |

## 6. Cierre de los hallazgos de la revisión 1

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (camino del `/readyz` completo) | §1.2 e IDS-U3-01 (la sonda de Kubernetes ya lo consulta); IDS-U3-06 (`smoke.sh`); `monitoring-design.md` §1 y §2 |
| R-02 (puertas de los manifiestos y las reglas) | `cicd-pipeline.md` §1.1 |
| R-03 (`probe` con valor desconocido) | Retirado con IDS-U3-01: `/readyz` no tiene parámetros |
| R-04 (Secret del primer `admin`) | §2.2; `cicd-pipeline.md` §3.1 |
| R-05 (cifra de 160 MiB) | §1.1; IDS-U3-08 |
| R-06 (pod CIDR y bloqueo global) | §1; IDS-U3-14 |
| R-07 (sondas del kubelet y DNS del `Job`) | §2.2, §3; IDS-U3-12, IDS-U3-13 |
| R-08 (*runner* de la prueba de rendimiento) | `cicd-pipeline.md` §1; IDS-U3-09 |
