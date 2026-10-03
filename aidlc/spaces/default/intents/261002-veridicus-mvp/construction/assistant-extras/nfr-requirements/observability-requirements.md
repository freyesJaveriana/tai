# Requisitos de observabilidad — U8 assistant-extras

**Insumos.** Flujos F1–F3 y §8 de `functional-design/functional-spec.md` (functional-spec); reglas
BR1.2, BR1.3, BR2.3, BR2.4 y BR3.1 de `functional-design/rules.md` (rules); NFR3, NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C3, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 de
`nfr-requirements-questions.md`.

## 1. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Logs estructurados sin datos sensibles. | El formato de U4 (NFR15.2 de U4) con estos identificadores adicionales: `claim_index`, `sustained`, `question_id`, `status` de la pregunta y `reason` (enum de NFR15.4). Nunca el texto de la pregunta, de las afirmaciones, de los pasajes, de la CoT de la segunda lectura ni la palabra afectiva encontrada (NFR10.8). |
| NFR15.3 | Cada extra deja rastro correlacionable. | En `semantic-agent`: `turn.permutation` (`turn_id`, `attempt`, número de candidatas y de sostenidas), `turn.question` (`turn_id`, `attempt`, `outcome`, `reason`) y `turn.affective` (`turn_id`, `attempt`, `matched` booleano). En `session-api`: `question.decided` (`question_id`, `turn_id`, `status`, `user_id`). Prueba de nivel 1 que sigue un turno con los tres extras por sus logs. |
| NFR15.4 | Los fallos de la pregunta se distinguen por motivo. | Una línea `WARNING` por pregunta omitida con `reason` ∈ {`invalid_schema`, `forbidden_vocabulary`, `timeout`, `unavailable`, `too_long`}; la supresión por afirmación «no documentada» (BR2.1) es `INFO` con `reason = undocumented`, porque es un resultado normal. |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno)

| ID | Métrica | Tipo | Etiquetas | Servicio |
|---|---|---|---|---|
| NFR15.1 | `veridicus_extras_enabled` | gauge (0/1) | `extra` (`permutation`, `suggest_question`, `affective`) | `session-api` |
| NFR15.1 | `veridicus_extra_judge_duration_seconds` | histogram (cubetas 5, 10, 20, 30, 45, 60, 90, 120, 180) | `call` (`second_read`, `question`), `result` (`ok`, `timeout`, `invalid_output`, `unavailable`) | `semantic-agent` |
| NFR15.1 | `veridicus_permutation_claims_total` | counter | `sustained` (`true`, `false`) | `semantic-agent` |
| NFR15.1 | `veridicus_suggested_questions_total` | counter | `outcome` (`published`, `omitted`), `reason` (`none`, `undocumented`, `invalid_schema`, `forbidden_vocabulary`, `timeout`, `unavailable`, `too_long`) | `semantic-agent` |
| NFR15.1 | `veridicus_affective_notes_total` | counter | ninguna | `semantic-agent` |
| NFR15.1 | `veridicus_question_decisions_total` | counter | `status` (`approved`, `discarded`) | `session-api` |

Las etiquetas solo llevan valores de enum, nunca identificadores ni texto. La latencia del turno sigue
siendo `veridicus_turn_latency_seconds` de C15 (U4); como no distingue extras, el p95 de NFR3.1 se
calcula en el reporte de nivel 2 agrupando por las opciones de cada sesión, y `veridicus_extras_enabled`
permite leer el panel. Estas métricas se añaden a C15 por un PR de U1, como las de U3 y U4 (precisión
en `security-requirements.md` §6).

## 3. Indicadores (SLI) y objetivos

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia con extras | p95 de `evaluated_at − submitted_at` en la corrida de nivel 2 con extras | ≤ 150 s (NFR3.1) |
| Tasa en línea de la permutación | `veridicus_permutation_claims_total{sustained="true"}` / total, en la corrida con extras | > 65 % (NFR4.4) |
| Preguntas en el Hecho No Documentado | Preguntas publicadas en el caso del Golden Dataset | 0 (NFR4.3) |
| Omisiones por vocabulario | `veridicus_suggested_questions_total{reason="forbidden_vocabulary"}` | Se reporta; cada caso se revisa en el reporte de nivel 2 |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, U2).** Junto al de U4: extras activos, duración de la segunda lectura y
  de la pregunta, tasa de sostenidas, preguntas publicadas y omitidas por motivo, y decisiones del
  analista por estado.
- **Alertas informativas** (ninguna despierta a alguien ni cambia nada del sistema, FR9.1): con
  `veridicus_extras_enabled` en 1, `veridicus_turn_queue_depth > 20` durante 10 minutos (se acerca al
  tope de 24 de NFR8.2), y más de 3 omisiones por `invalid_schema` o `forbidden_vocabulary` en 15
  minutos (indica un cambio de modelo o de *prompt* que hay que revisar).
- **Trazas distribuidas.** No: la correlación por `turn_id`, `attempt` y `question_id` basta.
