# Requisitos de escalabilidad — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR3, por el volumen que acotan las
  latencias).
- **Alcance.** El MVP corre en una sola máquina, con una réplica de la API de `session-api` (NFR8.6 de U7),
  un solo analista en la sustentación y ≤ 500 sesiones en la base (U6). Aquí se fijan los topes de C25 que
  son de U13, el crecimiento de sus tablas y qué hacer si se superan. No hay autoescalado.

**Insumos.** Preguntas abiertas 1, 4 y 5 del Functional Design (§11); BR2.4, BR3.5, BR3.6, BR5.2, BR5.7,
BR6.2 y BR7.1 de rules; C1, C24 y C25 de contract-summary; NFR3.9 de U5, NFR8.4–NFR8.6 de U7, NFR8.7 de
U6 y NFR8.11 de U4 (volumen de sus tablas); `review_body_max_bytes` de U5.

## 1. Dimensionamiento de las cifras de C25

| Cifra | Valor | Por qué |
|---|---|---|
| `retention_max_days` | **90** `days` | VE-12 («90 días como máximo por defecto»); P2 = A lo hace también el valor por defecto |
| `retention_min_days` | **1** `days` | AC15.7.1; la demo de B13 usa una sesión de 1 día (FD-U13-09) |
| `acknowledgement_validity_days` | **90** `days` | VE-04; el día 90 sigue vigente y el 91 no |
| `testimony_warning_words` | **8** `words` | AC15.3.3 |
| `problem_report_note_max_chars` | **2 000** `chars` | El mismo tope que las notas de la revisión humana (`review_text_max_chars` de U5). Una nota de 2 000 caracteres tiene como mucho unas 1 000 palabras y unas 1 000 secuencias de 8, así que el costo de la comparación lo manda la sesión (hasta 250 000 caracteres), no la nota (NFR3.1) |
| `ethics_body_max_bytes` | **32 768** `bytes` (nueva) | Cubre el peor caso válido de la nota (2 000 caracteres escapados como `\uXXXX\uXXXX`, 24 000 bytes) más los campos. Es la mitad de `review_body_max_bytes`, porque U13 tiene un solo texto |
| `wellness_reminder_interval_s` | **2 700** `s` (45 min) | Propuesta de esta etapa, sin cifra del protocolo del TG en el repositorio (NFR-U13-01). Se elige un intervalo menor que la hora para que el recordatorio aparezca al menos una vez en una sesión de revisión de una transcripción del conjunto sintético. El entorno puede bajarla para la demostración (`VERIDICUS_LIMIT_WELLNESS_REMINDER_INTERVAL_S`) |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR3.9 | nuevo | Crecimiento de las tablas de U13. | Con 500 sesiones típicas y 300 accesos por sesión (aperturas, observaciones y reportes), `AccessLogEntry` tiene 150 000 filas y ocupa **≤ 40 MiB** con índices. Cada `RetentionAct` de la sesión máxima ocupa **≤ 1 MiB**; con 500 actas, la tabla ocupa **≤ 100 MiB**. `ProblemReport`, `AnalystAcknowledgement` y `RetentionChange` ocupan **≤ 10 MiB** juntas con ≤ 10 reportes por sesión. `AccessLogEntry`, `AnalystAcknowledgement` y `RetentionAct` no se borran (BR2.4, BR5.10): Infrastructure Design suma esas cifras al volumen de PostgreSQL | `perf`, nivel 1 (diferencia de `pg_total_relation_size`) |
| NFR3.10 | nuevo | Las consultas de U13 usan índices. | Índices: `AnalystAcknowledgement (actor_user_id, at DESC)`; `AccessLogEntry (resource_id, at)` y `(actor_user_id, at)`; `ProblemReport (session_id)`, `(suggestion_id)` y `(reported_at) WHERE session_id IS NULL`; `RetentionChange (session_id)`; `RetentionAct (deleted_session_id)` y `(job_run_id)`. En U4, `InterviewSessionRecord (retention_until)` y `(created_at) WHERE retention_until IS NULL` (NFR-U13-06). Con las filas de NFR3.9 cargadas, `EXPLAIN` del estado de `/auth/me`, de `expired_sessions`, de la selección de reportes sin sesión, del borrado de BR5.5 y de cada consulta del comando no hace `Seq Scan` sobre esas tablas | Nivel 1 (`pg_indexes` y `EXPLAIN`) |
| NFR3.11 | nuevo | Volumen del `Job` de retención. | Una ejecución acepta todas las sesiones vencidas, sin tope por ejecución: con ≤ 500 sesiones en la base, el peor caso es que venzan todas a la vez. La duración crece de forma lineal con las candidatas (NFR3.6: 50 típicas en ≤ 5 min). `activeDeadlineSeconds` la fija Infrastructure Design con 2 × la ejecución medida de 500 sesiones típicas (NFR-U13-07). Si el plazo vence a mitad, la siguiente ejecución sigue donde quedó (NFR10.20) | `perf`, nivel 1, y revisión del manifiesto |
| NFR3.12 | nuevo | Concurrencia. | Dos `POST /problem-reports` simultáneos de la misma sesión terminan los dos en `201` con 2 filas. Dos `PATCH` simultáneos que reducen la misma sesión de 30 a 10 días dan un `200` y un `422` `retention.cannot_extend`, y dejan exactamente **1** `RetentionChange` (orden de bloqueo sesión primero, NFR11.7). Solo una ejecución del `Job` a la vez (NFR10.19). Un `Job` en curso no aumenta en más de 200 ms el p95 de `GET /sessions/{id}?since=` de U4 | Nivel 1 (barrera, 20 repeticiones sin fallos) |

## 3. Qué se degrada primero

| Señal | Qué pasa | Qué se hace |
|---|---|---|
| `AccessLogEntry` pasa de 1 000 000 de filas | El comando de consulta tarda más que NFR3.7 | Se decide por PR una política de archivo del registro; no se borra sin cambiar VE-11 |
| Muchas sesiones vencen a la vez | El `Job` tarda más que su `activeDeadlineSeconds` | Se relanza: cada sesión borrada ya está confirmada (NFR10.20); el plazo se ajusta por PR con la medición |
| Una nota legítima de más de 2 000 caracteres | `413` `limits.exceeded` | Se sube la cifra por PR de U1 tras medir NFR3.1; una variable de entorno solo puede bajarla |
