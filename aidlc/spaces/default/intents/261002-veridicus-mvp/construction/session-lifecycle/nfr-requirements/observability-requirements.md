# Requisitos de observabilidad — U6 session-lifecycle

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U6. Sustituye a la revisión 1 del 2026-10-03. Los IDs NFR15.1–NFR15.4 se mantienen y se
añade NFR15.5. Se cierra R-05 de `reviews/review-01.md` (dónde se raspan las métricas del trabajador y el
desfase del indicador de sesiones).

**Insumos.**
- Flujos F2–F9 y §8 «Errores y bordes» de `functional-design/functional-spec.md` (functional-spec,
  revisión 2).
- Reglas BR2.5, BR4.2, BR4.5, BR4.6, BR7.9, BR8.3 y BR9.1–BR9.6 de `functional-design/rules.md` (rules).
- NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements).
- C1, C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary), con las etiquetas
  permitidas que fijó hoy U1.

## 1. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | Logs estructurados de U6 sin datos sensibles. | El formato JSON de una línea de U4 con los campos permitidos de NFR10.4: identificadores, `paste_batch_id`, `origin`, tamaños, conteos, `idle_seconds` y `code`. **Nunca** el texto pegado o importado, el nombre del archivo, un mensaje de `ImportProblem` ni datos del consentimiento. La prueba de la cadena centinela de NFR10.4 lo verifica |
| NFR15.3 | cambia | Cada operación de U6 deja un evento correlacionable. | Un evento `INFO` por operación: `transcript.pasted` (`session_id`, `paste_batch_id`, `turn_count`, `char_count`, `run_id` o nulo, duración); `session.imported` (`session_id`, `origin`, `turn_count`, tamaño en bytes, duración); `final_run.requested` (`session_id`, `run_id`); `session.paused`, `session.analysis_resumed` (`run_id` o nulo), `session.terminated` y `session.consent_withdrawn` (`session_id`, número de corridas canceladas); `session.suspended` (`session_id`, `idle_seconds`); `session.resumed` (`session_id`, `user_id`). Las corridas siguen con los eventos `run.*` de U4. Prueba de nivel 1 que reconstruye solo con los logs una sesión que se importa, lanza el modo final, se suspende, se reanuda y se termina |
| NFR15.4 | cambia | Los fallos de U6 se distinguen. | `WARNING` con `code` por cada pegado o importación rechazados y por cada escritura de latido fallida; `ERROR` por `run.publish_failed` (NFR10.11), por cada clave de cancelación que no se pudo escribir (NFR10.18) y por cada revisión de suspensión que no pudo correr (NFR10.12) |

## 2. Métricas (Prometheus)

La API de `session-api` las expone en su `/metrics` del puerto interno; el trabajador de `session-api`,
en el `/metrics` de su propio puerto interno, el mismo por el que U4 publica sus métricas de ingesta. U2
raspa los dos.

| ID | Métrica | Tipo | Etiquetas | Proceso |
|---|---|---|---|---|
| NFR15.1 | `veridicus_transcript_pastes_total` | counter | `outcome` (`accepted`, `rejected`), `error_code` | API |
| NFR15.1 | `veridicus_transcript_paste_seconds` | histogram (cubetas 0,1, 0,25, 0,5, 1, 2,5, 5) | `outcome` | API |
| NFR15.1 | `veridicus_session_imports_total` | counter | `outcome`, `error_code`, `origin` (`corpus`, `sintetico`; etiqueta nueva, NFR-U6-09) | API |
| NFR15.1 | `veridicus_session_import_seconds` | histogram (cubetas 0,25, 0,5, 1, 2, 3, 5) | `outcome` | API |
| NFR15.1 | `veridicus_session_transitions_total` | counter | `state` (estado de destino) | API y trabajador |
| NFR15.1 | `veridicus_sessions` | gauge | `state` | trabajador: se calcula al rasparlo con un `COUNT … GROUP BY status`, con caché de 15 s, así no depende del intervalo de la revisión |
| NFR15.1 | `veridicus_session_sweep_seconds` | histogram (cubetas 0,01, 0,05, 0,1, 0,5, 1, 2) | `outcome` (`ok`, `error`) | trabajador |
| NFR15.1 | `veridicus_run_cancellations_total` | counter | `outcome` (`key_written`, `key_deferred`) | API |

Las etiquetas solo llevan valores de enum de la lista de U1 (`state`, `outcome`, `error_code`) más
`origin`, que se propone sumar a esa lista con los dos valores del enum de C1; nunca `session_id` ni
texto. Estas métricas entran a C15 por un PR de U1 (NFR-U6-09). La latencia de las
corridas de un bloque o del modo final ya la mide U4 (`veridicus_run_latency_seconds{mode}`).

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.5 | nuevo | Las métricas de U6 existen y no exponen texto. | Prueba de nivel 1 que raspa los dos `/metrics` tras un pegado, una importación, una pausa y una suspensión: cada métrica de la tabla aparece con sus etiquetas; ninguna etiqueta tiene un valor fuera de su enum; una cadena centinela sembrada no aparece |

## 3. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia del pegado | p95 de `veridicus_transcript_paste_seconds` en la prueba `perf` | ≤ 2,5 s con el bloque máximo; ≤ 0,5 s con 60 turnos (NFR3.1) |
| Latencia de la importación | p95 de `veridicus_session_import_seconds` | ≤ 3 s con el archivo máximo; ≤ 1 s con 312 turnos (NFR3.13) |
| Detección de la suspensión | Tiempo entre el último latido registrado y el cambio a `suspended`, con reloj controlado | Entre 180 y 210 s (NFR3.7) |
| Salud de la revisión | `veridicus_session_sweep_seconds{outcome="error"}` | 0 en las corridas de NFR8 y de humo |
| Cancelación | `veridicus_run_cancellations_total{outcome="key_deferred"}` | 0 en la demostración; cualquier valor > 0 se investiga |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Sesiones por estado, transiciones por hora, pegados e
  importaciones aceptados y rechazados por `code`, importaciones por origen y cancelaciones, junto al
  panel de la cola de U4.
- **Alertas.** Ninguna despierta a alguien en el MVP. Dos reglas informativas en Grafana: más de 2
  revisiones de suspensión con `outcome="error"` en 5 minutos (la base no responde al trabajador) y
  cualquier aumento de `key_deferred`. Ninguna regla cambia el estado de una sesión (FR9.1).
- **Trazas distribuidas.** No en el MVP: `session_id`, `paste_batch_id` y `run_id` bastan para
  correlacionar (NFR15.3).
