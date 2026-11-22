# Requisitos de observabilidad — U4 text-flow

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U4. Sustituye a la revisión 1 del 2026-10-03.

**Qué cambia.**
- Se mantienen los IDs NFR15.1–NFR15.4 y se añade NFR15.5.
- Las métricas del turno, del juez y de los *embeddings* de la revisión 1 quedan «Retiradas». Las del
  juez, el verificador y el *prompt* pasan a U11.

**Insumos.**
- Flujos F5–F8, F11 y F13–F15 de `functional-design/functional-spec.md` (functional-spec).
- Reglas BR5.8, BR9.1, BR11.1 y BR16.1–BR16.5 de `functional-design/rules.md` (rules).
- NFR3, NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements).
- C3, C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary).
- Respuesta S1 = A (adaptada) de `nfr-requirements-questions.md`.

## 1. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | Logs estructurados sin datos sensibles. | Cada línea es un JSON con `timestamp`, `level`, `service`, `event` y solo los identificadores permitidos de NFR10.7. Nunca llevan texto de turnos, citas, `hecho`, `observaciones`, consentimiento ni *prompts* |
| NFR15.3 | cambia | Cada transición de una corrida deja un rastro que se puede correlacionar. | Hay un evento `INFO` por transición (`run.queued`, `run.held`, `run.processing`, `run.completed`, `run.error`, `run.cancelled`) con `run_id`, `attempt` y `message_id`, en `session-api` y en `semantic-agent`. Con ellos se reconstruye el camino de una corrida entre servicios. Una prueba de nivel 1 sigue una corrida por sus logs |
| NFR15.4 | cambia | Los fallos se distinguen por su `code`. | Cada corrida en `error`, cada mensaje que va a `<cola>:failed` y cada rechazo por `limits.exceeded` deja una línea `WARNING` con su `code`. Una caída de una dependencia deja una línea `ERROR` |
| NFR15.5 | nuevo | Un incidente de anonimización se ve en el acto. | El bloqueo de una sesión (BR16.3) deja una línea `ERROR` `session.blocked` con `session_id`, `run_id` y `code`, y suma `veridicus_sessions_blocked_total`. Una prueba de nivel 1 comprueba las dos cosas con E36 |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno)

| ID | Métrica | Tipo | Etiquetas | Servicio |
|---|---|---|---|---|
| NFR15.1 | `veridicus_run_latency_seconds` | histogram (cubetas 10, 30, 60, 120, 180, 300, 600, 900, 1800, 3600, 7200) | `mode`, `outcome` | `session-api`, al ingerir |
| NFR15.1 | `veridicus_runs_total` | counter | `mode`, `outcome` (`completed`, `error`, `cancelled`), `error_code` | `session-api` |
| NFR15.1 | `veridicus_run_queue_depth` | gauge | ninguna | `session-api` (corridas `queued` + `processing`) |
| NFR15.1 | `veridicus_run_queue_wait_seconds` | histogram | `mode` | `session-api` (de `enqueued_at` a `RunStarted`) |
| NFR15.1 | `veridicus_ingest_duration_seconds` | histogram | `outcome` | trabajador de `session-api` |
| NFR15.1 | `veridicus_model_input_tokens_total` y `veridicus_model_output_tokens_total` | counter | `provider`, `role` | `session-api`, desde `ModelCall` |
| NFR15.1 | `veridicus_sessions_blocked_total` | counter | ninguna | `session-api` |

**Métricas retiradas de la revisión 1:**
- `veridicus_turn_latency_seconds`, `veridicus_turns_total` y `veridicus_turn_queue_depth`. Las
  sustituyen las de corrida.
- `veridicus_judge_*`, `veridicus_claims_total`, `veridicus_alerts_total` y
  `veridicus_handoff_packages_total`. Pasan a U11 o salen.
- `veridicus_embedding_duration_seconds` y `veridicus_scenario_indexing_seconds`. Salen.

**Reglas de las etiquetas y del registro.**
- Las etiquetas solo llevan valores de enum (NFR-U4-08), nunca identificadores ni texto.
- La CPU y la memoria de los pods salen de las métricas del clúster que instala U2.
- Estas métricas se añaden a C15 por un PR de U1.

## 3. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Ingesta | p95 de `veridicus_ingest_duration_seconds` en nivel 1 | ≤ 5 s (NFR3.1) |
| Éxito del flujo | Sesiones sin corridas en error, en la corrida de NFR8 | ≥ 98 % (NFR8.5) |
| Salud de la cola | `veridicus_run_queue_depth` | ≤ 10 sostenido (`scalability-requirements.md` §4) |
| Bloqueos | `veridicus_sessions_blocked_total` | 0 en la demostración; cualquier valor > 0 se investiga |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Muestra:
  - latencia de las corridas por modo;
  - profundidad y espera de la cola;
  - corridas en error por `code`;
  - *tokens* por proveedor y papel;
  - sesiones bloqueadas.
- **Alertas.** En el MVP ninguna despierta a nadie. Hay tres reglas informativas en Grafana:
  - `veridicus_run_queue_depth > 10` durante 10 minutos;
  - más de 3 `analysis.invalid_output` en 15 minutos;
  - cualquier aumento de `veridicus_sessions_blocked_total`.

  Ninguna regla cambia nada del sistema (FR9.1).
- **Trazas distribuidas.** No en el MVP. Basta la correlación por `run_id`, `attempt` y `message_id`
  (NFR15.3).
