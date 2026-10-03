# Requisitos de observabilidad — U5 human-review

**Insumos.** Flujos F1–F5 de `functional-design/functional-spec.md` (functional-spec) y reglas BR2.1,
BR3.2 y BR4.1 de `functional-design/rules.md` (rules); FR9.3, NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`.

## 1. Métricas (Prometheus, en `/metrics` del puerto interno de `session-api`)

| ID | Métrica | Tipo | Etiquetas | Cuándo cambia |
|---|---|---|---|---|
| NFR15.1 | `veridicus_review_decisions_total` (C15) | counter | `state`: `accepted`, `edited`, `dismissed` | +1 después del *commit* de cada `ReviewDecision` (NFR10.10) |
| NFR15.1 | `veridicus_session_dismissal_ratio` (C15) | gauge | `session_id` (UUID), como fija C15 | Se recalcula después de cada decisión confirmada; se retira al bloquear la ronda (NFR8.6) |
| NFR15.1 | `veridicus_review_rejections_total` (nueva) | counter | `code`: `review.cot_not_viewed`, `review.note_required`, `review.invalid_transition`, `review.round_locked`, `validation.invalid_request` | +1 por cada decisión rechazada por HumanReview o por la validación del cuerpo (los `403` ya los cuenta `veridicus_auth_rejections_total` de U3) |

Las etiquetas solo llevan valores de enum y el `session_id` (NFR10.8). `veridicus_review_rejections_total`
y la definición exacta de la ventana se añaden a C15 por un PR de U1, como las métricas de U3 y U4
(precisión en `security-requirements.md` §6).

## 2. Cálculo de la razón de descarte (P1 = A)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Definición de la ventana, con *W* = 8 (`VERIDICUS_AIR_WINDOW`). | Se calcula sobre la **ronda vigente** de la sesión (la `open`, con la herencia de BR3.2). Una alerta es **elegible** si tiene estado vigente `accepted`, `edited` o `dismissed`, o si sigue `pending` y una alerta creada después en la misma sesión ya tiene una decisión (el analista la dejó atrás: «ignorada», FR9.3). Una alerta `pending` sin decisiones posteriores no es elegible: sigue en la bandeja del analista. La ventana son las **8 alertas elegibles más recientes** por orden de creación de la sugerencia. Razón = (descartadas + ignoradas) / 8. **La serie no se publica hasta que la sesión tiene 8 alertas elegibles.** |
| NFR15.3 | El cálculo es una función pura probada por tabla. | `domain/dismissal_window.py` recibe la lista de alertas con su estado vigente y orden y devuelve la razón o «sin publicar». Casos de nivel 0: 7 elegibles → sin publicar; 8 elegibles con 2 descartadas → 0,25 (no supera el umbral de U2); 8 con 3 descartadas → 0,375; 10 elegibles → solo cuentan las 8 más recientes; una `pending` seguida de una decidida cuenta como ignorada; una `pending` al final no cuenta; en una ronda de corrección, una alerta sin decisión nueva usa el estado heredado. Prueba de nivel 1 de punta a punta: tras 8 decisiones (3 descartes), `/metrics` muestra `0.375` para esa sesión. |
| NFR15.4 | U5 publica; U2 decide la alerta. | La regla de Prometheus de U2 compara con `> 0.25` y su anotación es una **propuesta** de umbral (US10.6, FR9.3); ninguna regla cambia el umbral (NFR11.4). U5 entrega a U2 un archivo de series de ejemplo (`services/session-api/tests/human_review/fixtures/air_series.yaml`) para su `promtool test rules`: una sesión en 0,25 (sin alerta) y otra en 0,375 (con alerta). |

## 3. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.5 | Cada hecho de U5 deja un evento estructurado sin texto. | JSON en una línea con `timestamp`, `level`, `service`, `event` y solo los campos de NFR10.6. Eventos `INFO`: `review.decision_recorded` (`decision_id`, `suggestion_id`, `round_id`, `previous_state`, `state`, `user_id`), `review.decision_rejected` (`suggestion_id`, `user_id`, `code`), `review.cot_viewed` (`suggestion_id`, `user_id`, `first`), `review.round_opened` (`round_id`, `session_id`, `kind`), `review.round_locked` (`round_id`, `report_version_id`). `WARNING` por *timeout* de bloqueo o de sentencia y por `metrics.update_failed`; `ERROR` si la base no responde. Nunca nota, reformulación, CoT, fragmento ni cita. Prueba de nivel 1 que reconstruye la historia de una sugerencia (propuesta, CoT consultada, aceptada, descartada, ronda bloqueada) solo con sus logs. |

## 4. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia de la decisión | p95 de la prueba `perf` de NFR3.1 | ≤ 200 ms |
| Rechazos por CoT no consultada | `veridicus_review_rejections_total{code="review.cot_not_viewed"}` | Informativo: la consola deshabilita los botones (BR5.1), así que un valor > 0 en uso real indica un cliente que no es la consola |
| Señal AIR | `veridicus_session_dismissal_ratio` | Informativo; la propuesta la genera U2 sobre 0,25 |

## 5. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Decisiones por estado, rechazos por `code` y la razón de
  descarte por sesión, junto al panel de U4.
- **Alertas.** Ninguna despierta a alguien en el MVP. La única regla relacionada con U5 es la de AIR de
  U2, que solo propone.
- **Trazas distribuidas.** No aplican: U5 vive en un solo proceso; la correlación por `suggestion_id` y
  `round_id` basta.
