# Requisitos de observabilidad — U6 session-lifecycle

**Insumos.** Flujos F1, F2, F4 y F5 y §8 «Errores y bordes» de `functional-design/functional-spec.md`
(functional-spec); reglas BR2.5, BR4.2, BR4.5 y BR4.6 de `functional-design/rules.md` (rules); NFR10 y
NFR15 de `inception/requirements-analysis/requirements.md` (requirements); C1, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

## 1. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Logs estructurados de U6 sin datos sensibles. | El mismo formato JSON de una línea de U4 (NFR15.2 de U4) con los campos permitidos de NFR10.4: identificadores, `paste_batch_id`, conteos e `idle_seconds`. **Nunca** el texto pegado, el texto de un turno ni el nombre de un hablante. La prueba de la cadena centinela de NFR10.4 lo verifica. |
| NFR15.3 | Cada operación de U6 deja un evento correlacionable. | Un evento `INFO` por operación: `transcript.pasted` (`session_id`, `paste_batch_id`, `turn_count`, `testimony_count`, `char_count`, duración); `transcript.rejected` (`session_id`, `code`, conteos); `session.suspended` (`session_id`, `actor_kind = system`, `idle_seconds`); `session.resumed` (`session_id`, `user_id`); `scenario.version_created` (`scenario_id`, `version_id`, `version_number`). Los eventos `turn.queued` de U4 de un pegado llevan además `paste_batch_id`, así se sigue un lote completo hasta cada turno. Prueba de nivel 1 que reconstruye un pegado de 15 turnos solo con los logs. |
| NFR15.4 | Los fallos de U6 se distinguen. | `WARNING` con `code` por cada pegado rechazado y por cada escritura de latido fallida; `ERROR` por `transcript.publish_failed` (NFR10.11) y por cada revisión de suspensión que no pudo correr (NFR10.12). |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno de `session-api`)

| ID | Métrica | Tipo | Etiquetas | Proceso |
|---|---|---|---|---|
| NFR15.1 | `veridicus_transcript_pastes_total` | counter | `outcome` (`accepted`, `rejected`), `code` | API |
| NFR15.1 | `veridicus_transcript_paste_turns` | histogram (cubetas 1, 5, 10, 15, 30, 45, 60) | `role` (`testimony`, `interviewer`) | API |
| NFR15.1 | `veridicus_transcript_paste_seconds` | histogram (cubetas 0,1, 0,25, 0,5, 1, 2, 5) | ninguna | API |
| NFR15.1 | `veridicus_session_status_changes_total` | counter | `to_status`, `actor_kind` | API y trabajador |
| NFR15.1 | `veridicus_sessions` | gauge | `status` (`open`, `suspended`, `finalized`, `consolidated`) | trabajador (se actualiza en cada revisión) |
| NFR15.1 | `veridicus_suspension_sweep_seconds` | histogram (cubetas 0,01, 0,05, 0,1, 0,5, 1, 2) | `result` (`ok`, `error`) | trabajador |
| NFR15.1 | `veridicus_turn_latency_seconds{origin="pasted"}` (C15, ya declarada) | histogram | `origin` | API (al ingerir, U4) |

Las etiquetas solo llevan valores de enum, nunca `session_id` ni texto. Estas métricas se añaden a C15
por un PR de U1, como las de U3 y U4 (`security-requirements.md` §6). La latencia de un turno pegado
incluye su espera en la cola, así que `origin="pasted"` no se compara con la meta de 60 s de los turnos
escritos (NFR3.1 de U4).

## 3. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia del pegado | p95 de `veridicus_transcript_paste_seconds` en la prueba `perf` | ≤ 2 s en el peor caso; ≤ 0,5 s con 15 turnos (NFR3.1) |
| Detección de la suspensión | `suspended_at − last_heartbeat_at` en la prueba con reloj controlado | Entre 180 y 210 s (NFR3.7) |
| Salud de la revisión | `veridicus_suspension_sweep_seconds{result="error"}` | 0 en las corridas de NFR8 y de humo |
| Pegados sin vencimientos | Turnos con `turn.error.timeout` en la corrida de NFR3.11 | 0 |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Sesiones por estado, suspensiones y reanudaciones por
  hora, pegados aceptados y rechazados por `code`, y turnos por pegado, junto al panel de la cola de U4.
- **Alertas.** Ninguna despierta a alguien en el MVP. Una regla informativa en Grafana: más de 2
  revisiones de suspensión con `result="error"` en 5 minutos (la base no responde al trabajador).
  Ninguna regla cambia el estado de una sesión.
- **Trazas distribuidas.** No en el MVP: `paste_batch_id`, `session_id` y `turn_id` bastan para
  correlacionar (NFR15.3).
