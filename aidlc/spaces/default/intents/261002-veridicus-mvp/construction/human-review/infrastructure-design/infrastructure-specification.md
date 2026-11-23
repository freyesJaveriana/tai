# Especificación de infraestructura — U5 human-review

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** La CoT pasa a observaciones (`observation-views`, tabla `observations_view`). El código de U5
  corre ahora en tres procesos de `session-api`: la API, el trabajador (`propose`, código de U4) y el `Job` de
  retención de U13 (`purge_session`, C24). Salen `VERIDICUS_AIR_WINDOW` y `VERIDICUS_REVIEW_TEXT_MAX_CHARS`
  (rigen C25 y su catálogo). La migración suma `veridicus_retention`, dos disparadores nuevos y los índices de
  NFRD-U5-06. La memoria se compara con el límite de 1,125 GiB de U2.
- **Numeración.** §1–§4 conservan su tema. La tabla de precisiones de la revisión 1 (§5) se retira entera
  (IDS-U5-11) y la sustituye la tabla IDS-U5-01 a IDS-U5-12. §6 cierra los hallazgos de `reviews/review-01.md`.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; Minikube con 50 GiB y 16 CPU,
  decidido por U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2): performance-design §1–§3, §5 y §6; security-design §1, §4, §5,
  §8 y la tabla NFRD-U5-01 a NFRD-U5-11; scalability-design §1, §3–§5; reliability-design §1, §3–§5;
  observability-design §1–§4; logical-components §1–§4.
- `functional-design/functional-spec.md` (functional-spec: F1–F7, §8 integración y §10 errores).
- HumanReview, su tabla de propiedad de entidades, dependencias externas y frontera de
  `inception/domain-design/components.md` (components).
- C1, C10, C11, C15 v2, C16, C23, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary).
- `nfr-requirements/tech-stack-decisions.md` (D3, D5, D7, D14, D15 y §5).
- Infrastructure Design revisión 2 de U2 (§1, §2, §4, §5, §6 e IDS-U2-01 a IDS-U2-15), de U3 (§1, §2, IDS-U3-01,
  -04, -10) y de U4 (§1, §2.1, IDS-U4-02, -03, -12).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

U5 no tiene `Deployment` propio: este documento fija qué añade U5 a los procesos de `session-api` y a
`veridicus-pg`, sin cambiar su forma.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Módulo `session_api.human_review` dentro de tres procesos de la imagen `session-api`: `Deployment` `veridicus-session-api` (API, de U3), `Deployment` `veridicus-session-api-worker` (de U4, donde corre `propose`) y `Job` `veridicus-retention` de U13 en `deploy/jobs/` (donde corre `purge_session`). Sin `Deployment`, `CronJob` ni hilo propio fuera de la reconciliación de series de la API | logical-components §1 y §4; IDS-U5-10 |
| Réplicas de la API | **1**, como fija U3. Para U5 es un requisito y no solo un valor: la razón de descartes se calcula en el proceso que atendió la decisión (D7). Pasar a 2 o más exige antes el cambio de scalability-design §6 (calcular la serie al leer `/metrics`) en su propio PR (IDS-U5-12) | scalability-design §4 (NFR8.4) |
| Estrategia | API: `RollingUpdate` `maxSurge: 1`, `maxUnavailable: 0` (U3). Durante el relevo conviven dos pods unos segundos; toda la coordinación de U5 está en la base, así que no hay doble efecto. La serie AIR puede verse en los dos pods hasta que el viejo termina (riesgo aceptado, IDS-U5-05). Trabajador: `Recreate` (IDS-U4-02) | reliability-design §1; scalability-design §4 |
| Imagen | La de `session-api` (U3), por digest. U5 añade código, la tabla de transiciones de functional-spec §3 como dato y su catálogo de mensajes; sin dependencias de sistema nuevas | security-design §1 |
| Puertos | Sin puertos nuevos: `decisions` y `observation-views` bajo `/api/v1` en `http` 8080; métricas de C15 v2 en `metrics` 8081 | security-design §1; C16 |
| Red | Sin reglas nuevas en ninguna `NetworkPolicy`: U5 solo usa la salida a `veridicus-pg:5432` que ya tienen la API, el trabajador y el `Job` de retención | NFR1.1; security-design §1 |
| Almacenamiento | Columnas nuevas en `review_round` y dos tablas nuevas en `veridicus-pg` (§2.2); sin PVC, volumen, archivo ni `/tmp` propio | scalability-design §5: < 50 MB en el peor caso |
| Configuración | Una sola clave de U5, `VERIDICUS_DB_LOCK_TIMEOUT_MS` = `2000`, en el `ConfigMap` `veridicus-session-api-config` de U3 y en los `Job` que abren conexiones con `db.py` (§2.1, IDS-U5-01, IDS-U5-02). Ninguna `VERIDICUS_LIMIT_REVIEW_*` en los manifiestos: rige el catálogo C25 | logical-components §4; NFRD-U5-03; NFRD-U5-10 |
| Sondas | Las de U3, sin cambios: la `readinessProbe` usa el `/readyz` completo (IDS-U3-01). La configuración de U5 se valida antes de abrir el puerto, así que una clave inválida deja el pod sin arrancar. La reconstrucción de las series al arrancar (≤ 2 s) y la reconciliación no entran en ninguna sonda y caben en la `startupProbe` de 60 s | reliability-design §3 y §4 |
| Recursos | Sin cambios en los valores de U2: API 0,5 / 512 MiB → 2 / 1,125 GiB; U5 cabe con margen (§1.1) | performance-design §5 (NFR8.1) |
| Entornos | Una sola máquina de 64 GB, solo CPU, con el mismo digest que publica la CI; un solo `values-cpu.yaml`; U5 no pide `nvidia.com/gpu` ni valores por máquina | NFR2.1; IDS-U2-01, IDS-U2-02 |
| IaC | Una revisión de Alembic en `db/migrations/` (§2.2) y la clave del `ConfigMap` en los valores del subchart `session-api` del chart paraguas de U2. Los escribe Code Generation y entran por PR; ningún *script* los aplica | AUTONOMIA-01; `## Deployment` de team.md |
| Frontera (AUTONOMIA-04) | Todo dentro del clúster; ver §3 | security-design §1 |

### 1.1 Memoria de la API con U5 (NFR8.1)

| Parte | Pico | Origen |
|---|---|---|
| Base del proceso FastAPI + SQLAlchemy + validadores de C1 | ≈ 220 MiB | U3 §1.1 |
| Semáforo de Argon2id (2 × 64 MiB + 32 MiB) | 160 MiB | U3 §1.1 (IDS-U3-08) |
| `/tmp` en memoria | 16 MiB | U3 (IDS-U3-11) |
| Rutas de U4 en la API | Dentro de la base de U3 | U4 §1.1 |
| **U5** (prueba `perf` de NFR3.1 frente a la misma corrida sin decisiones) | **≤ 32 MiB** | performance-design §5 |
| U7: 3 consolidaciones máximas simultáneas y una exportación de 8 MiB | ≤ 192 + 32 MiB | NFR Design de U7, performance-design §6 |
| **Suma de las partes conocidas** | **≈ 652 MiB** | — |
| 1,2 × suma | ≈ 782 MiB | Regla de U2 §4 |
| `limits.memory` de U2 | 1,125 GiB = 1 152 MiB → quedan ≈ 370 MiB para las partes de U6, U9, U12 y U13 | U2 §4 |

U5 no añade uso en reposo apreciable: el *gauge* y `last_seq` ocupan un entero y un `float` por sesión con
serie (≤ 60), menos de 1 MiB. En el trabajador, `propose` vive dentro del pico de 512 MiB de U4; en el `Job` de
retención, el recibo de `purge_session` en el peor caso (≈ 8 000 UUID) ocupa < 2 MiB dentro de los 512 MiB de
U13. **U5 no pide cambiar ninguna cifra de U2** ni suma memoria al presupuesto de 41 GiB y 14,5 CPU.

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | Rol `veridicus_app` (Secret `veridicus-db-app`) en la API y el trabajador, con sus *pools* (API 5 + 5 de U3; trabajador 4 de U4); rol `veridicus_retention` (Secret `veridicus-db-retention`) en el `Job` de U13. En cada conexión, `statement_timeout` 2 000 ms (U3) y **`lock_timeout` 2 000 ms** desde `VERIDICUS_DB_LOCK_TIMEOUT_MS`, en `session_api/shared/db.py`, con `hide_parameters=True` en el *engine* | U5 no abre conexiones propias: no cambia el `connectionLimit` (25 hoy, 30 pedido por IDS-U4-03) ni `max_connections = 50` |
| Esquema de U5 | database | Revisión de Alembic de U5 aplicada por `migrations-job` con `veridicus_owner` (§2.2) | Nunca al arrancar el pod (prohibición de `project.md`) |
| Prometheus (módulo 8, U2) | monitoring | Raspa `veridicus-session-api:8081` con el `ServiceMonitor` de U3 cada 30 s; la regla AIR y su panel viven en `charts/monitoring-rules/` de U2 | `monitoring-design.md` |
| `veridicus-redis`, servidores de modelos, `anonymizer-proxy` | — | U5 no los usa | logical-components §2: su caída no afecta al módulo (con Redis caído, la consola sale de servicio por `/readyz` de U3, NFRD-U5-08) |
| `ingress-nginx` (U2) | load-balancer | Ruta `/api/` del `Ingress` `veridicus-web`, sin disco y con tope de 2 113 536 bytes | El cuerpo de U5 (≤ 65 536 bytes) cabe; el `413` lo da `GuardedRoute` de U3 (NFRD-U5-04) |
| `queue`, `cache`, `search`, `cdn` | — | No aplica | Sin caché del estado vigente (security-design DS7) |

### 2.1 Configuración de U5 (prefijo `VERIDICUS_`)

| Variable | Valor | Procesos | Validación al arrancar |
|---|---|---|---|
| `VERIDICUS_DB_LOCK_TIMEOUT_MS` | `2000` | API y trabajador (`veridicus-session-api-config`), `veridicus-retention` y `veridicus-create-admin` (IDS-U5-02) | Entero entre 100 y `VERIDICUS_DB_STATEMENT_TIMEOUT_MS`; si falta o es inválida, el proceso termina con código distinto de 0 |
| `VERIDICUS_LIMIT_REVIEW_TEXT_MAX_CHARS`, `_REVIEW_BODY_MAX_BYTES`, `_DISMISSAL_WINDOW_W` | **Sin definir**: rigen 2 000, 65 536 y 8 del catálogo `contracts/limits.v1.yaml` empaquetado en la imagen | API | `limits.load` solo deja bajar; pisos de U5: 1 carácter, 16 384 bytes, *W* ≥ 2 (NFRD-U5-03). `check-limits-env.sh` de U2 rechaza un valor mayor que el catálogo |
| `VERIDICUS_AIR_WINDOW`, `VERIDICUS_REVIEW_TEXT_MAX_CHARS` | **Retirado** (IDS-U5-01) | — | Los sustituyen `dismissal_window_w` y `review_text_max_chars` de C25 |

El empate de `lock_timeout` con `statement_timeout` (2 000 ms los dos) es deliberado: las dos cancelaciones
responden igual (`503` `system.unavailable`) y la prueba del empate está en `cicd-pipeline.md` §1 (IDS-U5-03).

### 2.2 Objetos de base de la migración de U5

| Objeto | Diseño | Requisito |
|---|---|---|
| `review_round` (la crea U4 en B3, con su marca `veridicus-audit`) | U5 suma `kind`, `based_on_round_id`, `opened_by`, `opened_actor_kind`, `opened_actor_system`, `locked_at`, `discarded_by`, `discarded_at` y `change_seq`, con `initial` y el actor de sistema `analysis-worker` en las filas que ya existan (FD-U5-08); único `(session_id, number)` y único parcial `(session_id) WHERE status = 'open'` | NFR8.3, NFR11.3, NFR11.6 |
| `review_decision` | `seq` de identidad, `change_seq`, actor y hora `NOT NULL`; `CHECK` de nota y reformulación no en blanco con `btrim(texto, :espacios)` y la lista exacta de `str.isspace()` (NFRD-U5-02) | NFR11.1 |
| `observations_view` | Único `(suggestion_id, user_id)`; sustituye a `cot_view` (**Retirado**) | NFR10.3, NFR10.14 |
| Índices | Los seis de U5 de scalability-design §3: `review_decision (round_id, suggestion_id, change_seq)` único, `(suggestion_id, change_seq)`, `(round_id, change_seq)`; `review_round (session_id, number)` único y el parcial de ronda `open`; `observations_view (suggestion_id, user_id)` único | NFR8.3; NFRD-U5-06 |
| Permisos de `veridicus_app` | `INSERT, SELECT` en `review_decision`, `observations_view` y `review_suggestion` por la marca `veridicus-audit` y la función `veridicus_apply_audit_grants()` de U3; en `review_round`, `INSERT, SELECT` y `UPDATE` solo sobre `status`, `locked_at`, `discarded_by`, `discarded_at` y `change_seq`; sin `DELETE` ni `TRUNCATE` | NFR11.1, NFR11.3 |
| Permisos de `veridicus_retention` | `SELECT, DELETE` en las cuatro tablas; nunca `UPDATE` | NFR11.5; NFR10.22 |
| Disparadores | `review_decision_round_open` (`BEFORE INSERT`: rechaza la fila si su ronda no está `open`) y `review_round_guard` (`BEFORE UPDATE`: solo `open` → `locked` u `open` → `discarded` en una `correction`, sin bajar `change_seq`). Sustituyen a `review_round_locked_is_final` (**Retirado**) | NFR11.2, NFR11.3 |
| Orden | Después de la migración de U3 (función de auditoría) y de la de U4 (`interview_session.change_cursor`, `review_suggestion`, `review_round`); antes del código de U5 (*expand–contract*) | `cicd-pipeline.md` §3 |

```sql
-- Ilustrativo: lo que la función de U3 no concede (columnas y rol de retención)
GRANT UPDATE (status, locked_at, discarded_by, discarded_at, change_seq)
  ON review_round TO veridicus_app;
GRANT SELECT, DELETE ON review_decision, observations_view,
  review_suggestion, review_round TO veridicus_retention;
```

### 2.3 Respaldo y pérdida de la base

| Situación | Qué se hace |
|---|---|
| Antes de aplicar la migración de U5 | El humano ejecuta `scripts/backup-db.sh` (U2 §6, «antes de un cambio de esquema») |
| Pérdida de la base | `pg_restore` manual del último volcado (U2 §6). RPO: el último volcado manual; RTO: el de una restauración manual (NFRD-U2-13). Se pierden las decisiones posteriores al volcado; aceptable porque solo hay datos sintéticos (prohibición de `project.md`) |
| Restaurar un volcado anterior a una consolidación (R-05) | Las versiones de reporte posteriores al volcado pierden su fila y su rastro de quién y cuándo; sus archivos quedan huérfanos y los retira el barrido al arrancar de U7 («archivo antes que fila»). El reporte se vuelve a consolidar desde la consola. El runbook lo dice (IDS-U5-07) |
| Reinicio de la API | Nada se pierde (sin *commit* no hay fila); las series se reconstruyen desde la base (reliability-design §5) |
| `Job` de retención que falla a mitad de `purge_session` | La transacción se revierte entera; el humano lo relanza y purgar dos veces es seguro (E32) |

## 3. Frontera del clúster (AUTONOMIA-04, NFR1.1)

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera | Control de infraestructura |
|---|---|---|---|
| Rutas `decisions` y `observation-views` | Dentro (API de `session-api`) | Decisión, nota y reformulación desde el navegador; sugerencia con su estado vigente hacia el navegador, por HTTPS del `Ingress` | Entrada solo desde `ingress-nginx` a 8080 (U2, U3) |
| HumanReview en la API, el trabajador y el `Job` | Dentro | Filas de PostgreSQL; llamadas en proceso de ConsoleApi y U4 (C10), U7 (C11) y U13 (C24) | Salida solo a `veridicus-pg:5432` para lo que usa U5; negar todo por defecto de U2 |
| Puerto `AccessLog` (C23) | Dentro | Solo `user_id`, `resource_type` y `suggestion_id` | En proceso; adaptador de U13 sobre PostgreSQL |
| Métricas de C15 v2 | Dentro (`:8081/metrics`) | Contadores, enums y `session_id` (UUID) | Entrada solo desde `monitoring` |
| Tarjeta de la sugerencia | Navegador, servida por `frontend` | Solo habla con `/api/` | CSP `default-src 'self'` de U4 |

Ningún dato de U5 sale del clúster. Lo comprueban la política estática de nivel 0 de U2 y el contrato
`human_review_no_network` de import-linter (`cicd-pipeline.md` §1). `kubectl port-forward` del humano hacia el
Ingress (IDS-U2-04) es acceso humano fuera de la política y no cambia el clúster.

## 4. Infraestructura compartida

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| `Deployment` y proceso API `veridicus-session-api` | U3 | U4–U9, U12, U13 | U5 añade una clave de `ConfigMap` y su parte de memoria por PR; no cambia sondas, réplicas ni estrategia |
| Trabajador `veridicus-session-api-worker` | U4 | U5 (`propose`), U6, U9 | U5 solo aporta la interfaz C10; el código que la llama es de U4 |
| `Job` `veridicus-retention` | U13 | U4, U5, U7 (`Purgeable`, C24) | Transacción por sesión del `Job`; U5 aporta `purge_session` y no lanza nada |
| Fila de la sesión (`interview_session.change_cursor`) y `session_api/shared/change_cursor.py`, `db.py` | U4 (columna), `session_api.shared` (primitivas) | U4–U7, U13 | Orden único usuario → sesión → ronda; `lock_timeout` 2 s; transacciones sin E/S de red |
| Tablas `review_round`, `review_decision`, `observations_view`, `review_suggestion` | U5 | U4 (C10), U7 (C11), U13 (C24) | Solo por las interfaces de C10, C11 y C24; único `FOR UPDATE` de rondas en `round_repository.py` |
| `veridicus-pg` y sus roles | U2 (despliegue), `session-api` (esquema) | U3–U7, U9, U12, U13 | Permisos por tabla en cada migración |
| `/metrics` de `session-api` | U3 | U3, U4, U5, U7 | Nombres de C15 v2; etiquetas validadas |
| Regla AIR y panel «Veridicus — AIR» | U2 (`charts/monitoring-rules/`) | U5 (publica la serie y entrega el *fixture*) | La regla solo propone; ningún código escribe el umbral (NFR11.4) |

## 5. Precisiones y peticiones (IDS-U5-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al original,
cada una en su propio commit. Las peticiones a otras unidades no se dan por aplicadas. Todas salen de las
fuentes aprobadas o de un hecho técnico, y ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U5-01 | Revisión 1 de esta etapa (§2.1, `ConfigMap` `session-api-config`) | El `ConfigMap` es `veridicus-session-api-config` (U3) y U5 solo le suma `VERIDICUS_DB_LOCK_TIMEOUT_MS`. Salen `VERIDICUS_AIR_WINDOW` y `VERIDICUS_REVIEW_TEXT_MAX_CHARS`; las cifras las da C25 y ningún manifiesto define `VERIDICUS_LIMIT_REVIEW_*` | logical-components §4; NFRD-U5-03; U2 §2.5 |
| IDS-U5-02 | Infrastructure Design de U2 §2.2 y `deploy/jobs/`; de U3 §2.2 (`create-admin`); de U4 §2.2 (ajustes del trabajador) | **Petición a U2:** `VERIDICUS_DB_LOCK_TIMEOUT_MS: "2000"` en todo contenedor con la imagen `session-api` que abra conexiones con `session_api/shared/db.py`: la API y el trabajador (por el `ConfigMap` común), `veridicus-retention` y `veridicus-create-admin`. Sin la variable esos procesos no arrancan (la configuración faltante impide arrancar). Comprobación propuesta en `deploy-level0`: el render falla si un contenedor de esa imagen no la define (control negativo: el `Job` de retención sin ella) | NFRD-U5-10; reliability-design §4; `team.md` (Code Style) |
| IDS-U5-03 | Revisión 1 de esta etapa (hallazgo R-03) y `nfr-design/reliability-design.md` §3 | Se mantiene `lock_timeout` = `statement_timeout` = 2 000 ms, que aprobó el NFR Design y con el que cuentan U7 y U13. Las dos cancelaciones (`55P03` y `57014`) se traducen al mismo `503` `system.unavailable` con `WARNING` y `duration_ms`, así que no hace falta distinguirlas. Se suma la prueba del empate (§1 de `cicd-pipeline.md`) | R-03; NFRD-U5-10 |
| IDS-U5-04 | Revisión 1 de esta etapa (§5, precisión `max by (session_id)` a U2; *fixture* con dos pods) | **Retirado.** La regla AIR es de U2, vive en `charts/monitoring-rules/` y compara `veridicus_session_dismissal_ratio > 0.25`, como ya dice U2 `monitoring-design.md` §3. El *fixture* de U5 (`services/session-api/tests/human_review/fixtures/air_series.yaml`) trae solo 0,25 sin alerta y 0,375 con alerta, y U2 lo usa en su prueba `promtool` | Cierra R-01; NFRD-U2-12; observability-design §2 |
| IDS-U5-05 | Revisión 1 de esta etapa (hallazgo R-02) | Durante un `RollingUpdate` de la API, la misma sesión puede tener serie en los dos pods y el viejo puede conservar un valor ya superado. La ventana dura lo que tarda el pod viejo en terminar (≤ 30 s de gracia) más una vuelta de raspado (30 s): ≤ 60 s. Se acepta: la regla solo anota en un panel, nadie recibe notificaciones y no cambia nada. `/readyz` no espera la reconstrucción de las series (reliability-design §3: C15 es SHOULD) | Cierra R-02 |
| IDS-U5-06 | Revisión 1 de esta etapa (`monitoring-design.md` §2: `VeridicusReviewCotNotViewed`, `VeridicusDismissalSeriesHigh`) | **Retirado.** La primera dependía de `veridicus_review_rejections_total`, que no entra en C15 v2; la segunda, porque observability-design §4 deja la regla AIR como única regla relacionada. La señal de 200 series pasa al panel. **Petición a U2:** el panel «Veridicus — AIR» suma `count(veridicus_session_dismissal_ratio)` con una línea en 200 y deja fuera los rechazos por `code` | observability-design §2 y §4; scalability-design §6 |
| IDS-U5-07 | Runbook de U2 (`docs/operacion/instalacion.md`, restauración de U2 §6) | **Petición a U2:** tras un `pg_restore`, el runbook avisa de que las consolidaciones posteriores al volcado se pierden y se rehacen desde la consola, y pide reiniciar `veridicus-session-api` para que corra el barrido de archivos huérfanos de U7 | Cierra R-05; AUTONOMIA-03 (quién y cuándo) |
| IDS-U5-08 | Revisión 1 de esta etapa (§1.1, límite de 768 MiB) | La suma de U5 se compara con el límite de 1,125 GiB de U2 (§1.1). U5 cabe con margen y no pide cambio | U2 §4; performance-design §5 |
| IDS-U5-09 | Revisión 1 de esta etapa (§2.2: `cot_view`, `review_round_locked_is_final`, permisos de solo `veridicus_app`) | La migración de U5 crea `observations_view`, los disparadores `review_decision_round_open` y `review_round_guard`, los permisos de `veridicus_retention` y los índices de NFRD-U5-06, y suma columnas a `review_round` de U4; los permisos de solo inserción pasan por la función de auditoría de U3 | security-design §5; NFRD-U5-02; NFRD-U5-06 |
| IDS-U5-10 | Revisión 1 de esta etapa (U5 solo en la API) | El código de U5 corre también en el trabajador (`propose`) y en el `Job` de retención (`purge_session`). Ninguno necesita Secret, red ni volumen nuevo; los dos usan los Secrets de su dueño (`veridicus-db-app`, `veridicus-db-retention`) | logical-components §1 y §4 |
| IDS-U5-11 | Revisión 1 de esta etapa (tabla de §5 y referencias de máquina y nombres) | Se retiran: las cinco precisiones de la revisión 1, los Minikube de 20 y 28 GiB, `values-gpu.yaml`, `/readyz?probe=kubernetes`, `session-api-config`, `veridicus-pg-app`, la `PrometheusRule` en el subchart `session-api`, el panel en `deploy/veridicus/dashboards/` y la URL de humo sin puerto | IDS-U2-01, IDS-U2-02, IDS-U2-04; IDS-U3-01, IDS-U3-04, IDS-U3-10 |
| IDS-U5-12 | Infrastructure Design de U3 §1 («Réplicas: 1 … cambiarlo es un PR») | La réplica única de la API es un requisito de U5 mientras la razón se calcule en el proceso: el PR que la suba debe traer antes el cambio de scalability-design §6 con su medición de NFR3.6 | scalability-design §4 (NFR8.4) |

## 6. Cierre de los hallazgos de la revisión 1

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (dueño y ruta de la regla AIR; *fixture* con dos pods) | IDS-U5-04: la regla es de U2 en `charts/monitoring-rules/`, sin `max by`; `monitoring-design.md` §2 |
| R-02 (valor viejo durante el relevo de pods) | IDS-U5-05: ventana ≤ 60 s como riesgo aceptado |
| R-03 (empate de `lock_timeout` y `statement_timeout`) | IDS-U5-03 y la prueba del empate en `cicd-pipeline.md` §1 |
| R-04 (escaneo de vocabulario solo en nivel 3) | `cicd-pipeline.md` §1: escaneo de nivel 0 sobre el catálogo de mensajes de U5 con un término sembrado (security-design §3) |
| R-05 (restaurar un volcado anterior a una consolidación) | §2.3 e IDS-U5-07 |
