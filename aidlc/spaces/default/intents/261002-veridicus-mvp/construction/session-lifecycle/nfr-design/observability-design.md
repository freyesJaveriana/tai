# Diseño de observabilidad — U6 session-lifecycle

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Salen la marca de lote, los eventos de publicación por lote y la versión de escenario.
  Entran la importación, el modo final, la pausa, la terminación, la retirada y la cancelación. Las
  métricas van en `contracts/metrics/session-lifecycle.v1.yaml` (NFRD-U1-05) con la etiqueta `error_code`.
- **Numeración.** §1–§4 conservan su tema; §5 (precisiones de la revisión 1) queda «Superado».

**Insumos.** `nfr-requirements/observability-requirements.md` (observability-requirements: NFR15.1–NFR15.5),
`performance-requirements.md` (performance-requirements), `security-requirements.md`
(security-requirements), `scalability-requirements.md` (scalability-requirements),
`reliability-requirements.md` (reliability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions); flujos F2–F9 y §8 de `functional-design/functional-spec.md` (functional-spec); C1,
C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); formateador de logs de U3,
NFR Design de U1 (NFRD-U1-05) y de U4 (eventos `run.*`, `/metrics` del trabajador).

## 1. Logs (NFR15.2, NFR15.3, NFR15.4) · cambia

- El formateador JSON de `libs/` (U3) con la lista blanca de `security-design.md` §4. La prueba centinela
  (NFR10.4) verifica que no aparecen el texto pegado o importado, el nombre del archivo, un mensaje de
  `ImportProblem` ni datos del consentimiento.
- **Correlación.** `paste_batch_id` se crea antes de la transacción del pegado y viaja en el contexto del
  *logger*; el evento `run.queued` de U4 de la corrida del bloque lo lleva junto con `run_id`. Con
  `session_id` → `paste_batch_id` → `run_id` + `attempt` (U4) se sigue un bloque hasta su resultado, sin
  trazas distribuidas.

| Evento | Proceso | Nivel | Campos |
|---|---|---|---|
| `transcript.pasted` | API | `INFO` | `session_id`, `paste_batch_id`, `turn_count`, `char_count`, `run_id` o nulo, `duration_ms` |
| `transcript.rejected` | API | `WARNING` | `session_id`, `code`, conteos |
| `transcript.replayed` (reenvío idempotente) | API | `INFO` | `session_id`, `paste_batch_id`, `run_id` o nulo |
| `session.imported` | API | `INFO` | `session_id`, `origin`, `turn_count`, tamaño en bytes, `duration_ms` |
| `session.import_rejected` | API | `WARNING` | `code`, `problem_count`, tamaño en bytes |
| `final_run.requested` | API | `INFO` | `session_id`, `run_id` |
| `session.paused`, `session.analysis_resumed`, `session.terminated`, `session.consent_withdrawn` | API | `INFO` | `session_id`, `cancelled_runs`; `run_id` o nulo en `analysis_resumed` |
| `session.suspended` | Trabajador | `INFO` | `session_id`, `actor_system = session-supervisor`, `idle_seconds` |
| `session.resumed` | API | `INFO` | `session_id`, `user_id` |
| `heartbeat.write_failed` | API | `WARNING` | `session_id`, `code` |
| `session.sweep_failed` | Trabajador | `ERROR` | `code` |
| `run.publish_failed`, `run.cancel_key_failed` (de U4) | API | `ERROR` | `session_id`, `run_id`, `code` (NFRD-U6-17) |

El latido omitido por `SKIP LOCKED` no se registra en el log (sería ruido cada pocos segundos). Prueba de
nivel 1: una sesión que se importa, lanza el modo final, se suspende, se reanuda y se termina se
reconstruye solo con los logs capturados.

## 2. Métricas (NFR15.1, NFR15.5) · cambia

La API en su `/metrics` del puerto interno; el trabajador en el `/metrics` de su puerto interno, el mismo
de U4. U2 raspa los dos. Se declaran en `contracts/metrics/session-lifecycle.v1.yaml` (NFRD-U1-05).

| Métrica | Tipo | Etiquetas | Dónde se mide en el código |
|---|---|---|---|
| `veridicus_transcript_pastes_total` | counter | `outcome` (`accepted`, `rejected`), `error_code` | Al responder el pegado |
| `veridicus_transcript_paste_seconds` | histogram (0,1, 0,25, 0,5, 1, 2,5, 5) | `outcome` | Alrededor de la ruta completa |
| `veridicus_session_imports_total` | counter | `outcome`, `error_code`, `origin` (`corpus`, `sintetico`) | Al responder la importación |
| `veridicus_session_import_seconds` | histogram (0,25, 0,5, 1, 2, 3, 5) | `outcome` | Alrededor de la ruta completa |
| `veridicus_session_transitions_total` | counter | `state` (destino) | Tras insertar cada `SessionStatusChange`, en API y trabajador |
| `veridicus_sessions` | gauge | `state` | Trabajador, al rasparlo: `COUNT … GROUP BY status` con caché de 15 s |
| `veridicus_session_sweep_seconds` | histogram (0,01, 0,05, 0,1, 0,5, 1, 2) | `outcome` (`ok`, `error`) | Alrededor de cada vuelta de `SessionSupervisor` |
| `veridicus_run_cancellations_total` | counter | `outcome` (`key_written`, `key_deferred`) | En `SessionLifecycle` tras cada `CancellationKeys.write` |

- Las etiquetas solo llevan valores de la lista cerrada de U1; nunca `session_id` ni texto. La latencia
  de las corridas la mide U4 (`veridicus_run_latency_seconds{mode}`).
- **NFR15.5.** Prueba de nivel 1 que raspa los dos `/metrics` tras un pegado, una importación, una pausa y
  una suspensión: cada métrica aparece con sus etiquetas, ningún valor sale de su enum y una cadena
  centinela sembrada no aparece. Nivel 0: la comprobación de U1 compara el archivo de métricas con el
  registro del código.

## 3. SLI y objetivos del MVP · cambia

| SLI | Fuente | Objetivo |
|---|---|---|
| Latencia del pegado | p95 de `veridicus_transcript_paste_seconds` en la prueba `perf` | ≤ 2,5 s con el bloque máximo; ≤ 0,5 s con 60 turnos (NFR3.1) |
| Latencia de la importación | p95 de `veridicus_session_import_seconds` | ≤ 3 s con el archivo máximo; ≤ 1 s con 312 turnos (NFR3.13) |
| Detección de la suspensión | `SessionStatusChange.at` − `coalesce(last_heartbeat_at, created_at)` con reloj controlado | 180–210 s (NFR3.7) |
| Salud de la revisión | `veridicus_session_sweep_seconds_count{outcome="error"}` | 0 en las corridas de NFR8 y de humo |
| Cancelación | `veridicus_run_cancellations_total{outcome="key_deferred"}` | 0 en la demostración; un valor > 0 se investiga |

## 4. Panel y reglas informativas · cambia

- **Panel de Grafana (SHOULD, lo instala U2).** Sesiones por estado, transiciones por hora, pegados e
  importaciones aceptados y rechazados por `error_code`, importaciones por `origin` y cancelaciones por
  `outcome`, junto al panel de la cola de U4.
- **Reglas informativas** (no despiertan a nadie y no cambian el estado de ninguna sesión, FR9.1): más de
  2 revisiones con `outcome="error"` en 5 minutos y cualquier aumento de `key_deferred`.
- **Sin trazas distribuidas** en el MVP: `session_id`, `paste_batch_id` y `run_id` bastan.

## 5. Precisiones de la revisión 1 · Superado

Las métricas `veridicus_transcript_publish_total` y `veridicus_session_heartbeat_writes_total` y el evento
`transcript.republish_skipped` salen con la marca de lote; las superan la tabla de NFR15.1 revisión 2 y
NFRD-U6-17 (`security-design.md` §15).
