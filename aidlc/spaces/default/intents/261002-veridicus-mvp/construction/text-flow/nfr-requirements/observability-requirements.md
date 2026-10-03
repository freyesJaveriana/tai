# Requisitos de observabilidad — U4 text-flow

**Insumos.** Flujos F2 y F4–F8 de `functional-design/functional-spec.md` (functional-spec) y reglas
BR5.8, BR7.3, BR8.1 y BR11.1 de `functional-design/rules.md` (rules); NFR3, NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C3, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P4 y S1 de
`nfr-requirements-questions.md`.

## 1. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Logs estructurados sin datos sensibles. | JSON en una línea con `timestamp`, `level`, `service`, `event` y solo los identificadores permitidos de NFR10.7 (`session_id`, `turn_id`, `attempt`, `message_id`, `version_id`, `code`, duraciones y conteos). Nunca texto de turnos, afirmaciones, pasajes, CoT ni *prompts*. |
| NFR15.3 | Cada transición de un turno deja rastro correlacionable. | Un evento `INFO` por transición (`turn.queued`, `turn.processing`, `turn.evaluated`, `turn.error`) con `turn_id`, `attempt` y `message_id`, en `session-api` y en `semantic-agent`; con ellos se reconstruye el camino de un turno entre servicios sin trazas distribuidas. Prueba de nivel 1 que sigue un turno por sus logs. |
| NFR15.4 | Los fallos se distinguen por `code`. | Cada `error` de turno, cada mensaje a `<cola>:failed` y cada versión en `error` deja una línea `WARNING` con su `code`; una caída de dependencia deja `ERROR`. |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno)

| ID | Métrica | Tipo | Etiquetas | Servicio |
|---|---|---|---|---|
| NFR15.1 | `veridicus_turn_latency_seconds` (C15) | histogram (cubetas 5, 10, 20, 30, 45, 60, 90, 120, 180, 300, 600) | `origin` | `session-api` (al ingerir) |
| NFR15.1 | `veridicus_turns_total` | counter | `outcome` (`evaluated`, `error`), `code` | `session-api` |
| NFR15.1 | `veridicus_turn_queue_depth` | gauge | ninguna | `session-api` (turnos `queued` + `processing`) |
| NFR15.1 | `veridicus_judge_duration_seconds` | histogram | `result` (`ok`, `timeout`, `invalid_output`, `unavailable`) | `semantic-agent` |
| NFR15.1 | `veridicus_judge_prompt_tokens` | histogram | ninguna | `semantic-agent` |
| NFR15.1 | `veridicus_claims_total` | counter | `grade`, `guard` | `semantic-agent` |
| NFR15.1 | `veridicus_alerts_total` y `veridicus_handoff_packages_total` | counter | ninguna | `semantic-agent` |
| NFR15.1 | `veridicus_embedding_duration_seconds` | histogram | `purpose` (`query`, `passage`) | ambos |
| NFR15.1 | `veridicus_scenario_indexing_seconds` | histogram | `result` (`ready`, `error`) | trabajador de `session-api` |

Las etiquetas solo llevan valores de enum, nunca identificadores de sesión ni texto. La CPU y la
memoria de los pods de IA salen de las métricas del clúster que instala U2 (NFR15 de requirements).
Estas métricas se añaden a C15 por un PR de U1, como las de U3.

## 3. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia del turno | p95 de `veridicus_turn_latency_seconds{origin="typed"}` en la corrida de nivel 2 | ≤ 60 s (NFR3.1) |
| Éxito de turnos | `veridicus_turns_total{outcome="evaluated"}` / total, en la corrida de NFR8 | ≥ 98 % de sesiones sin turnos en error (NFR8.5) |
| Salud de la cola | `veridicus_turn_queue_depth` | ≤ 30 sostenido (`scalability-requirements.md` §4) |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Latencia p50/p95 por turno, profundidad de la cola,
  turnos en error por `code`, duración del juez y *tokens* del *prompt*, y CPU de los pods de IA,
  junto al panel AIR de U5.
- **Alertas.** Ninguna despierta a alguien en el MVP. Dos reglas informativas en Grafana:
  `veridicus_turn_queue_depth > 30` durante 10 minutos, y más de 3 `turn.error.invalid_output` en 15
  minutos (indica un cambio de modelo o de *prompt* que hay que revisar). Ninguna regla cambia el
  umbral ni nada del sistema (FR9.1).
- **Trazas distribuidas.** No en el MVP: la correlación por `turn_id`, `attempt` y `message_id`
  (NFR15.3) basta para dos servicios y una cola.
