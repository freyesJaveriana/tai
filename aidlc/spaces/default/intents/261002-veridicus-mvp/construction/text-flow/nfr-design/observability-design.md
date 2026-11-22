# Diseño de observabilidad — U4 text-flow

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Salen las métricas del juez, de los *embeddings* y del umbral. Las métricas de U4 pasan a
  `contracts/metrics/text-flow.v1.yaml` con la lista cerrada de etiquetas de U1 (NFRD-U1-05) y suman
  `veridicus_runs_total` y `veridicus_sessions_blocked_total`. Lo nuevo: eventos de corrida entre servicios
  y el incidente visible (NFR15.5).

**Insumos.** `nfr-requirements/observability-requirements.md` (observability-requirements: NFR15.1–NFR15.5),
`security-requirements.md` (security-requirements: NFR10.7), `reliability-requirements.md`
(reliability-requirements), `performance-requirements.md` (performance-requirements),
`scalability-requirements.md` (scalability-requirements), `tech-stack-decisions.md`
(tech-stack-decisions), `functional-design/functional-spec.md` (functional-spec), C15 y C16 de
`contract-summary.md` (contract-summary); NFRD-U1-05; NFRD-U11-07.

## 1. Logs (NFR15.2–NFR15.5)

- **Formato.** El formateador JSON único de `libs/` (U3): `timestamp`, `level`, `service`, `event` y solo
  los campos de la lista blanca de NFR10.7. Un campo fuera de la lista se descarta y suma
  `veridicus_log_fields_dropped_total` de U3. Excepciones por tipo y `code` (`security-design.md` §6).
- **Eventos de corrida (NFR15.3).** Un `INFO` por transición con `run_id`, `attempt` y `message_id`:

| Evento | Quién | Cuándo |
|---|---|---|
| `run.queued` | API de `session-api` | Tras el `XADD` de C2 |
| `run.held` | API de `session-api` | Al crear la corrida en espera |
| `run.processing` | `semantic-agent` e ingesta | Al publicar e ingerir `RunStarted` |
| `run.completed`, `run.error`, `run.cancelled` | `semantic-agent` (salida) e ingesta (estado) | Al publicar `RunResult` y al confirmar |

- **Fallos (NFR15.4).** `WARNING` con `code` por corrida en `error`, mensaje a fallidos, `limits.exceeded`,
  `run.claim_lost`. `ERROR` por caída de dependencia y por `run.publish_failed`.
- **Incidente (NFR15.5).** `ERROR` `session.blocked` con `session_id`, `run_id` y `code`, y
  `veridicus_sessions_blocked_total` sube en `after_commit`. Prueba de nivel 1 con E36.
- **Prueba de nivel 1:** una corrida se reconstruye de punta a punta filtrando por `run_id` en los logs de
  los tres procesos; el *canary* aparece 0 veces.

## 2. Métricas (NFR15.1)

Declaradas en `contracts/metrics/text-flow.v1.yaml` (NFRD-U4-08); una prueba de nivel 0 falla si el código
registra una métrica o una etiqueta fuera del archivo, o un valor de etiqueta fuera de su enum.

| Métrica | Tipo | Etiquetas (valores) | Proceso |
|---|---|---|---|
| `veridicus_run_latency_seconds` | histogram (10 … 7 200) | `mode` (`incremental`, `final`), `outcome` (`completed`, `error`, `cancelled`) | Trabajador de `session-api`, al ingerir |
| `veridicus_runs_total` | counter | `mode`, `outcome`, `error_code` (catálogo de C1) | Trabajador de `session-api` |
| `veridicus_run_queue_depth` | gauge | — | Trabajador de `session-api`, cada 15 s con el supervisor |
| `veridicus_run_queue_wait_seconds` | histogram | `mode` | Trabajador de `session-api` (de `enqueued_at` a `RunStarted`) |
| `veridicus_ingest_duration_seconds` | histogram | `outcome` (`ok`, `discarded`, `invalid_output`, `rolled_back`) | Trabajador de `session-api` |
| `veridicus_model_input_tokens_total`, `veridicus_model_output_tokens_total` | counter | `provider`, `role` (C18) | Trabajador de `session-api`, desde `ModelCall` |
| `veridicus_sessions_blocked_total` | counter | — | API y trabajador de `session-api` |

- `outcome = completed` corresponde al estado de corrida `done`.
- Ninguna etiqueta lleva `session_id` de alta cardinalidad en U4. La latencia por llamada y el costo por
  proveedor solo existen en memoria de U11 y llegan agregados en C19 v2 (NFRD-U11-07); U4 no los duplica.
- Las métricas se exponen en `/metrics` de cada proceso (C16) y suben en `after_commit`: una transacción
  revertida no cambia ningún contador.

## 3. SLI y objetivos del MVP

| SLI | Objetivo | Fuente |
|---|---|---|
| Ingesta p95 | ≤ 5 s | `veridicus_ingest_duration_seconds` |
| Corridas que terminan sin `analysis.system` | 100 % en la prueba de carga | `veridicus_runs_total{error_code="analysis.system"}` |
| Espera en cola p95 | ≤ 3 600 s | `veridicus_run_queue_wait_seconds` |
| Sesiones bloqueadas | 0 en la prueba de carga | `veridicus_sessions_blocked_total` |

Son objetivos de verificación del MVP (prueba de carga y humo), no SLO con ventana de producción.

## 4. Panel y reglas informativas

- Panel de Grafana de U2 con una fila de U4: profundidad de cola, espera p95, corridas por resultado y
  código, ingesta p95, tokens por proveedor y papel, sesiones bloqueadas.
- Reglas informativas (sin Alertmanager, decisión de U2): cola > 20 durante 10 min; espera p95 > 3 600 s;
  cualquier aumento de `veridicus_sessions_blocked_total`; mensajes en `:failed` (por log).
