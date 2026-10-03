# Especificación de infraestructura — U5 human-review

**Insumos.** Camino de la decisión, presupuestos y tope de memoria de `nfr-design/performance-design.md`
(performance-design); frontera, autorización, entrada acotada e integridad en la base de
`nfr-design/security-design.md` (security-design); modelo de capacidad, índices y límite de una réplica
de `nfr-design/scalability-design.md` (scalability-design); orden de bloqueo, *timeouts*, salud y
recuperación de `nfr-design/reliability-design.md` (reliability-design); logs y métricas de
`nfr-design/observability-design.md` (observability-design); inventario, dominios de falla y entrega a
Infrastructure Design de `nfr-design/logical-components.md` (logical-components); flujos F1–F5 de
`functional-design/functional-spec.md` (functional-spec); módulo HumanReview y fachada ConsoleApi de
`inception/domain-design/components.md` (components); C1, C10, C11, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); requisitos de
`nfr-requirements/`; `infrastructure-design-questions.md` (sin preguntas abiertas); infraestructura
común de U2 (`platform/infrastructure-design/infrastructure-specification.md`), despliegue de
`session-api` de U3 (`identity-access/infrastructure-design/infrastructure-specification.md`) y
procesos de U4 (`text-flow/infrastructure-design/infrastructure-specification.md`).

U5 no tiene proceso propio: es el módulo `human_review` de la API de `session-api`, solo habla con
PostgreSQL y no usa Redis, modelos ni red externa. Este documento fija qué añade U5 al despliegue de U3
y a la base de U2, sin cambiar su forma.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Modelo de cómputo | Módulo dentro del `Deployment` `session-api` (API) de U3, namespace `veridicus`; sin `Deployment`, `Job` periódico ni `CronJob` propios | logical-components §4: todo U5 son transacciones cortas en la API |
| Réplicas | **1**, como fija U3; es un requisito de U5, no solo un valor por defecto: la razón AIR se calcula en el proceso que atendió la decisión (D7). Pasar a 2 o más exige antes el cambio de D7 (calcular la serie al leer `/metrics`) en su propio PR | scalability-design §4 (NFR8.4) |
| Estrategia | `RollingUpdate` `maxSurge: 1`, `maxUnavailable: 0` de U3. Durante el relevo conviven dos pods unos segundos; la coordinación de decisiones está en la base, así que no hay doble efecto, y la serie AIR duplicada se absorbe en la regla (monitoring-design §2) | reliability-design §1; scalability-design §4 |
| Imagen | La de `session-api` (U3), por digest; U5 añade código y las tablas de transición de functional-spec §3 como dato, sin dependencias de sistema nuevas | security-design §1 |
| Puertos | Sin puertos nuevos: rutas `decisions` y `cot-views` en `http` 8080 bajo `/api/`; métricas de C15 en `metrics` 8081 | security-design §1 |
| Red | Sin reglas nuevas en la `NetworkPolicy` de `session-api`: salida a `veridicus-pg:5432` (la que U5 usa), `veridicus-redis` y CoreDNS ya existentes; U5 no resuelve nombres nuevos, así que la lista blanca de CoreDNS de U10 no necesita entradas para U5 | NFR1.1; security-design §1 |
| Almacenamiento | Tres tablas nuevas y dos columnas `change_seq` en `veridicus-pg` (§2.2); sin PVC, volumen ni archivo | scalability-design §5: < 50 MB en el peor caso |
| Configuración | Tres claves nuevas en el `ConfigMap` `session-api-config` (§2.1), validadas al arrancar; sin Secrets nuevos | logical-components §4; NFR10.18 |
| Sondas | Sin cambios en la forma de U3: `/readyz?probe=kubernetes` añade la validación de la configuración de U5 a `check_config()`; la reconstrucción de las series AIR al arrancar (≤ 2 s) no entra en ninguna sonda y cabe en la `startupProbe` de 60 s | reliability-design §3–§4 |
| Recursos | Se mantienen 0,5 / 384 MiB – 2 / 768 MiB de la API (§1.1) | performance-design §5 (NFR8.1) |
| Máquinas | Mismo chart y mismos valores para U5 en la máquina de desarrollo (Minikube 20 GiB, 10 CPU) y en la de demostración (28 GiB); U5 no cambia con `values-gpu.yaml` ni con `values-extras.yaml` de U8 | NFR2.1: U5 no usa modelos ni GPU |
| IaC | Cambios en el subchart `session-api` de `deploy/veridicus` (claves del `ConfigMap`, regla y *fixture* de Prometheus) y una revisión de Alembic en `db/migrations/`; los escribe Code Generation y entran por PR | AUTONOMIA-01; `## Deployment` de team.md |
| Frontera (AUTONOMIA-04) | Todo dentro del clúster; ver §3 | security-design §1 |

### 1.1 Memoria de la API con U5 (NFR8.1)

| Parte | Pico | Origen |
|---|---|---|
| Base del proceso FastAPI + SQLAlchemy | ≈ 200 MiB | U3 |
| Semáforo de Argon2id (2 × 64 MiB más margen) | ≥ 160 MiB | U3 |
| Rutas de U4 en la API (indexación y juez fuera, en trabajador y `semantic-agent`) | Dentro de la base de U3 | U4 §1.1 («valor de U3») |
| U5 (medido en la prueba `perf` de NFR3.1 frente a la misma corrida sin decisiones) | ≤ 32 MiB | performance-design §5 |
| **Suma de picos** | **≈ 392 MiB** | — |
| `limits.memory` | 768 MiB → margen ≈ 96 % (≥ 20 %) | Regla de ≥ 20 % de esta etapa |
| `requests.memory` | 384 MiB, igual al uso en reposo de U3; U5 no añade uso en reposo apreciable | U3 |

U6 y U7 vuelven a sumar su parte sobre esta tabla; si la suma de picos pasa de 640 MiB (768 / 1,2), el
`limits.memory` sube por PR.

## 2. Servicios de infraestructura

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-pg` | database | Rol `veridicus_app` por el pool de la API de U3 (5 + 5, `pool_timeout` 2 s); `statement_timeout` 2 000 ms (U3) y **`lock_timeout` 2 000 ms** fijado por sesión de base desde `VERIDICUS_DB_LOCK_TIMEOUT_MS` | U5 no abre conexiones nuevas: usa el pool de la API (≤ 10 de las 50 de la base) |
| Esquema de U5 | database | Revisión de Alembic de U5 aplicada por `migrations-job` con `veridicus_owner` (§2.2) | Nunca al arrancar el pod (prohibición de `project.md`) |
| Prometheus (módulo 8) | monitoring | Raspa `session-api:8081` con el `ServiceMonitor` de U3 cada 30 s; regla de U5 en la `PrometheusRule` del subchart | monitoring-design |
| `veridicus-redis`, `veridicus-judge`, `veridicus-embeddings` | — | U5 no los usa | logical-components §2: su caída no afecta a U5 |
| `queue`, `cache`, `search`, `cdn` | — | No aplica: sin caché del estado vigente (D2), sin colas | performance-design (sin caché) |
| `ingress-nginx` | load-balancer | Ruta `/api/` existente; el cuerpo de U5 (≤ 64 KiB) cabe en el `proxy-body-size` de U2/U4 (≥ 1 MiB); el corte real a 64 KiB lo hace la API (D12) | security-design §4 |

### 2.1 Configuración (`ConfigMap` `session-api-config`)

| Ajuste | Valor | Validación al arrancar |
|---|---|---|
| `VERIDICUS_AIR_WINDOW` | `8` | Entero ≥ 1; si falta o es inválido, el proceso sale con código ≠ 0 |
| `VERIDICUS_REVIEW_TEXT_MAX_CHARS` | `2000` | ≤ `review_text_max_chars` del catálogo `contracts/limits.v1.yaml` (solo puede bajar) |
| `VERIDICUS_DB_LOCK_TIMEOUT_MS` | `2000` | Entero entre 100 y el `statement_timeout`; se aplica como `SET lock_timeout` en cada conexión del pool |

El límite de 64 KiB del cuerpo (`review_body_max_bytes`) no es una variable: se lee del catálogo
empaquetado en la imagen.

### 2.2 Objetos de base de la migración de U5

| Objeto | Diseño | Requisito |
|---|---|---|
| `review_round` | `UNIQUE (session_id, number)`; único parcial `(session_id) WHERE status = 'open'`; columna `change_seq` | NFR8.3, NFR11.2 |
| `review_decision` | Columnas `seq` (identidad), `change_seq`; índices `(suggestion_id, round_id, at, seq)` y `(round_id, change_seq)`; `CHECK` de nota y reformulación no en blanco | NFR8.3, NFR11.1; P1 = A de NFR Design |
| `cot_view` | `UNIQUE (suggestion_id, user_id)` | NFR8.3, NFR10.14 |
| Permisos | `veridicus_app`: `INSERT, SELECT` en `review_decision` y `cot_view`; `INSERT, SELECT` y `UPDATE (status, locked_by_report_version_id, locked_at, change_seq)` en `review_round`; sin `DELETE` ni `TRUNCATE`; ambas tablas en `AuditConvention` de U3 | NFR11.1, NFR11.3 |
| *Trigger* | `review_round_locked_is_final`: rechaza todo `UPDATE` de una fila `locked` | NFR11.3 |
| Orden | Después de la migración de U4 (`interview_session.change_seq`, `review_suggestion`), antes del código de U5 (*expand–contract*) | cicd-pipeline §3 |

```sql
-- Ilustrativo: el corazón de los permisos de solo inserción
GRANT INSERT, SELECT ON review_decision, cot_view TO veridicus_app;
GRANT INSERT, SELECT ON review_round TO veridicus_app;
GRANT UPDATE (status, locked_by_report_version_id, locked_at, change_seq)
  ON review_round TO veridicus_app;
```

### 2.3 Respaldo y pérdida de la base

| Situación | Qué se hace |
|---|---|
| Antes de aplicar la migración de U5 | El humano ejecuta `scripts/backup-db.sh` (U2 §6, «antes de un cambio de esquema») |
| Pérdida de la base | Restauración manual del último `pg_dump` (U2 §6); las decisiones posteriores al volcado se pierden. Aceptable en el MVP porque solo hay datos sintéticos (prohibición de `project.md`); la razón AIR se reconstruye sola al arrancar |
| Reinicio de la API | Nada se pierde (sin *commit* no hay fila); las series AIR se reconstruyen desde la base (reliability-design §5) |

## 3. Frontera del clúster (AUTONOMIA-04, NFR1.1)

| Componente | Dentro / fuera | Qué datos cruzan su frontera | Control de infraestructura |
|---|---|---|---|
| Rutas `decisions` y `cot-views` | Dentro (API de `session-api`) | Decisión, nota y reformulación desde el navegador, por HTTPS del `Ingress` | Entrada solo desde `ingress-nginx` a 8080 (U2/U3) |
| HumanReview | Dentro | Filas de PostgreSQL; llamadas en proceso de U4 (C10) y U7 (C11) | Salida solo a `veridicus-pg:5432` para lo que usa U5; política de negar todo de U2 |
| Métricas de C15 | Dentro (`:8081/metrics`) | Contadores, enums y `session_id` | Entrada solo desde `monitoring` |
| Tarjeta de sugerencia | Navegador, servida por `frontend` | Solo habla con `/api/` | CSP `default-src 'self'` de U4 |

Ningún dato de U5 sale del clúster. La comprobación es la política estática de nivel 0 de U2 más el
contrato `human_review_no_network` de import-linter (cicd-pipeline §1).

## 4. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `Deployment` y proceso API de `session-api` | U3 | U4, U5, U6, U7 | U5 añade claves de `ConfigMap` y su parte de memoria por PR; no cambia sondas, réplicas ni estrategia |
| Fila de la sesión (`interview_session.change_seq`) y `session_api/shared/change_cursor.py` | U4 (columna), `session_api.shared` (primitiva) | U4, U5, U7 | Orden único sesión → ronda; `lock_timeout` 2 s; transacciones sin E/S de red |
| Tablas `review_round`, `review_decision`, `cot_view` | U5 | U4 (`propose`, C10), U7 (C11, lectura y bloqueo) | Solo por las interfaces de C10/C11; único `FOR UPDATE` de rondas en `round_repository.py` |
| `veridicus-pg` y rol `veridicus_app` | U2 (despliegue), `session-api` (esquema) | U3–U7 | Permisos por tabla fijados en cada migración |
| `/metrics` de `session-api` | U3 | U3, U4, U5 | Prefijos `veridicus_review_*` y `veridicus_session_dismissal_ratio` |
| Regla AIR y panel «Veridicus — AIR» | U2 | U5 (publica la serie) | La regla solo propone; ningún código escribe el umbral (NFR11.4) |

## 5. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado ni de otra unidad; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `identity-access/infrastructure-design/infrastructure-specification.md` §1 y §2.1 | El `ConfigMap` `session-api-config` suma `VERIDICUS_AIR_WINDOW`, `VERIDICUS_REVIEW_TEXT_MAX_CHARS` y `VERIDICUS_DB_LOCK_TIMEOUT_MS`; la réplica única pasa a ser un requisito mientras D7 de U5 no cambie | logical-components §4; scalability-design §4 |
| `identity-access/infrastructure-design/infrastructure-specification.md` §1.1 | La suma de picos de la API con U5 es ≈ 392 MiB; 768 MiB se mantiene con margen ≥ 20 % | performance-design §5 |
| `platform/infrastructure-design/monitoring-design.md` §3 | La regla `VeridicusAirThresholdProposal` agrega con `max by (session_id)` para no duplicar la propuesta durante el relevo de pods | Estrategia `RollingUpdate` de U3 |
| `platform/infrastructure-design/monitoring-design.md` §5 | El panel «Veridicus — AIR» suma `veridicus_review_rejections_total` por `code` y el conteo de series de la razón | observability-design §4; scalability-design §6 |
| `platform/infrastructure-design/infrastructure-specification.md` §3 | La salida de `session-api` a `veridicus-embeddings` ya la había movido U4 al trabajador; U5 no añade salidas | U4 §7; NFR1.1 |
