# Diseño de observabilidad — U6 session-lifecycle

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; flujos F1, F2, F4 y F5 de `functional-design/functional-spec.md`
(functional-spec); C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary);
respuestas P1–P2 de `nfr-design-questions.md`; formateador de logs de U3 y diseño de observabilidad de
U4.

## 1. Logs (NFR15.2, NFR15.3, NFR15.4)

- El formateador JSON de `libs/` (U3) con la lista blanca ampliada por U6 (security-design §4):
  `paste_batch_id`, `scenario_id`, `turn_count`, `testimony_count`, `char_count`, `idle_seconds`. La
  prueba centinela de NFR10.4 verifica que nunca aparece texto pegado ni nombres de hablantes.
- **Correlación de un lote.** `paste_batch_id` se crea en la transacción del pegado y viaja en el
  contexto del *logger* hasta la publicación; los eventos `turn.queued` de U4 de los turnos pegados lo
  llevan. Con `paste_batch_id` → `turn_id` + `attempt` + `message_id` (U4) se sigue un lote completo
  hasta cada resultado, sin trazas distribuidas.

| Evento | Proceso | Nivel | Campos |
|---|---|---|---|
| `transcript.pasted` | API | `INFO` | `session_id`, `paste_batch_id`, `turn_count`, `testimony_count`, `char_count`, `duration_ms` |
| `transcript.rejected` | API | `WARNING` | `session_id`, `code`, conteos |
| `transcript.republish_skipped` (marca encontrada, P1 = A) | API | `INFO` | `session_id`, `paste_batch_id` |
| `transcript.publish_failed` | API | `ERROR` | `session_id`, `paste_batch_id` |
| `session.suspended` | Trabajador | `INFO` | `session_id`, `actor_kind = system`, `idle_seconds` |
| `session.resumed` | API | `INFO` | `session_id`, `user_id` |
| `heartbeat.write_failed` | API | `WARNING` | `session_id`, `code` |
| `suspension.sweep_failed` | Trabajador | `ERROR` | `code` |
| `scenario.version_created` | API | `INFO` | `scenario_id`, `version_id`, `version_number` |

El latido omitido por `SKIP LOCKED` no se registra en el log (sería ruido cada pocos segundos); se cuenta
en una métrica. Prueba de nivel 1: un pegado de 15 turnos se reconstruye solo con los logs capturados.

## 2. Métricas (NFR15.1)

En `/metrics` del puerto interno: la API por su servidor HTTP y el trabajador por el hilo mínimo de U4.

| Métrica | Tipo | Etiquetas | Dónde se mide en el código |
|---|---|---|---|
| `veridicus_transcript_pastes_total` | counter | `outcome` (`accepted`, `rejected`), `code` | Al responder el pegado |
| `veridicus_transcript_paste_turns` | histogram (1, 5, 10, 15, 30, 45, 60) | `role` | Tras dividir un pegado aceptado |
| `veridicus_transcript_paste_seconds` | histogram (0,1, 0,25, 0,5, 1, 2, 5) | — | Alrededor de la ruta completa |
| `veridicus_transcript_publish_total` | counter | `result` (`published`, `already_published`, `failed`) | En `publish_batch` (P1 = A) |
| `veridicus_session_heartbeat_writes_total` | counter | `result` (`written`, `skipped_locked`, `not_due`, `error`) | En `HeartbeatWriter` (P2 = A) |
| `veridicus_session_status_changes_total` | counter | `to_status`, `actor_kind` | Tras insertar cada `SessionStatusChange` |
| `veridicus_sessions` | gauge | `status` | `SuspensionSweeper`, con un `count(*) … GROUP BY status` en cada vuelta |
| `veridicus_suspension_sweep_seconds` | histogram (0,01, 0,05, 0,1, 0,5, 1, 2) | `result` (`ok`, `error`) | Alrededor de cada vuelta |
| `veridicus_turn_latency_seconds{origin="pasted"}` | histogram | `origin` | Ingesta de U4 (ya en C15) |

Las etiquetas son enums cerrados; la prueba de nivel 0 de U4 que recorre el registro cubre también
estas. La latencia `origin="pasted"` incluye la espera en cola y no se compara con la meta de 60 s de
los turnos escritos.

## 3. SLI y objetivos del MVP

| SLI | Fuente | Objetivo |
|---|---|---|
| Latencia del pegado | p95 de `veridicus_transcript_paste_seconds` en la prueba `perf` | ≤ 2 s peor caso; ≤ 0,5 s con 15 turnos |
| Detección de la suspensión | `suspended_at − last_heartbeat_at` con reloj controlado | 180–210 s |
| Salud de la revisión | `veridicus_suspension_sweep_seconds_count{result="error"}` | 0 en las corridas de NFR8 y de humo |
| Pegados sin duplicados | `veridicus_transcript_publish_total{result="published"}` por `paste_batch_id` en la prueba de reenvío | 1 publicación por lote |
| Pegados sin vencimientos | `turn.error.timeout` en la corrida de NFR3.11 | 0 |

## 4. Panel y reglas informativas

- **Panel de Grafana (SHOULD, lo instala U2).** Sesiones por estado, suspensiones y reanudaciones por
  hora, pegados aceptados y rechazados por `code`, publicaciones por `result`, latidos por `result` y
  turnos por pegado, junto al panel de la cola de U4.
- **Reglas informativas** (no despiertan a nadie y no cambian el estado de ninguna sesión): más de 2
  revisiones con `result="error"` en 5 minutos; cualquier `veridicus_transcript_publish_total{result="failed"}`
  en 15 minutos (Redis no acepta el pegado).
- **Sin trazas distribuidas** en el MVP: los identificadores de §1 bastan.

## 5. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `session-lifecycle/nfr-requirements/observability-requirements.md` §2 y C15 de `contract-summary.md` | Se añaden `veridicus_transcript_publish_total{result}` y `veridicus_session_heartbeat_writes_total{result}`, por el mismo PR de U1 que añade las demás métricas de U6 | P1 = A, P2 = A |
| `session-lifecycle/nfr-requirements/observability-requirements.md` §1 | Se añaden los eventos `transcript.republish_skipped`, `heartbeat.write_failed` y `suspension.sweep_failed` con nombre propio | P1 = A, NFR15.4 |
