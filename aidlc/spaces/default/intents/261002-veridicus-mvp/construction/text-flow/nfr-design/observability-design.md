# Diseño de observabilidad — U4 text-flow

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; `functional-design/functional-spec.md` (functional-spec);
C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P2 de
`nfr-design-questions.md`; formateador de logs de U3.

## 1. Logs (NFR15.2–NFR15.4)

- El mismo formateador JSON de `libs/` que usa U3, con lista blanca: `timestamp`, `level`, `service`,
  `event`, `session_id`, `turn_id`, `attempt`, `message_id`, `version_id`, `code`, `duration_ms`,
  `count`. Nada de texto de turnos, afirmaciones, pasajes, CoT ni *prompts* (security-design §6).
- **Correlación sin trazas distribuidas.** `message_id` lo asigna el productor al publicar C2 y viaja
  en C3; con `turn_id` + `attempt` + `message_id` se sigue un turno por la API, `semantic-agent` y el
  trabajador.

| Evento | Servicio | Nivel |
|---|---|---|
| `turn.queued`, `turn.processing`, `turn.evaluated` | API, `semantic-agent`, trabajador | `INFO` |
| `turn.error` con su `code` | Trabajador o `semantic-agent` | `WARNING` |
| `judge.retry` (P1 = A) con número de intento | `semantic-agent` | `WARNING` |
| `queue.failed` (mensaje a `<cola>:failed`) | Consumidor | `WARNING` |
| `scenario.indexed` / `scenario.error` | Trabajador | `INFO` / `WARNING` |
| Dependencia caída (base, Redis, modelo) | Cualquiera | `ERROR` |

## 2. Métricas (NFR15.1)

Todas en `/metrics` del puerto interno de cada proceso, con `prometheus-client`. En el trabajador de
`session-api`, que no tiene HTTP público, un servidor mínimo en un hilo expone el mismo puerto
interno.

| Métrica | Dónde se mide en el código |
|---|---|
| `veridicus_turn_latency_seconds{origin}` | Al ingerir: `evaluated_at − submitted_at` |
| `veridicus_turns_total{outcome, code}` | Al ingerir o al vencer el plazo |
| `veridicus_turn_queue_depth` | El hilo de plazos la recalcula cada 15 s con un `COUNT` |
| `veridicus_judge_duration_seconds{result}` | Alrededor de cada llamada al juez, incluidos los reintentos (`unavailable`) |
| `veridicus_judge_prompt_tokens` | Tras `count_tokens` |
| `veridicus_claims_total{grade, guard}` | Por afirmación, después de la guardia y del juez |
| `veridicus_alerts_total`, `veridicus_handoff_packages_total` | Al publicar C3 |
| `veridicus_embedding_duration_seconds{purpose}` | Alrededor de cada lote |
| `veridicus_scenario_indexing_seconds{result}` | Al terminar una versión |

Las etiquetas son enums cerrados; una prueba de nivel 0 recorre el registro y falla ante un valor
fuera del enum o una etiqueta con identificadores. Se añaden a C15 por un PR de U1.

## 3. SLI y objetivos del MVP

| SLI | Fuente | Objetivo |
|---|---|---|
| Latencia del turno | p95 de `veridicus_turn_latency_seconds{origin="typed"}` en nivel 2 | ≤ 60 s |
| Éxito de turnos | Corrida de NFR8 | ≥ 98 % de sesiones sin turnos en error |
| Salud de la cola | `veridicus_turn_queue_depth` | ≤ 30 sostenido |
| Visibilidad de la alerta | Prueba Playwright de nivel 3 | ≤ 3 s desde `evaluated_at` |

## 4. Panel y reglas informativas

- Panel de Grafana (SHOULD, U2): latencia p50/p95, profundidad de la cola, turnos en error por `code`,
  duración y reintentos del juez, *tokens* del *prompt*, CPU y memoria de los pods de IA.
- Reglas informativas (no despiertan a nadie, no cambian nada): cola > 30 durante 10 minutos; más de 3
  `turn.error.invalid_output` en 15 minutos; más de 5 `judge.retry` en 15 minutos (el juez se está
  reiniciando).
