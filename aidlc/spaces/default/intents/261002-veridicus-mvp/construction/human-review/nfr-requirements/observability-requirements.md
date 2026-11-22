# Requisitos de observabilidad — U5 human-review

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U5. Sustituye a la revisión 1 del 2026-10-03.

**Qué cambia.**
- U5 tiene solo las dos métricas de C15 v2. La métrica de rechazos queda **Retirado**: su etiqueta
  `code` no está permitida.
- La ventana son las últimas *W* sugerencias decididas, como dice C15 v2. Salen las «ignoradas», lo que
  cierra R-01 de la revisión 1.
- *W* sale de C25.
- La CoT pasa a ser observaciones.
- Entran los eventos de descarte de la copia y de purga.

**IDs.** Se conservan NFR15.1–NFR15.5.

**Insumos.**
- Flujos F1–F7 de `functional-design/functional-spec.md` (functional-spec).
- Reglas BR3.2, BR3.4, BR3.9, BR4.1 y BR6.1 de `functional-design/rules.md` (rules).
- FR9.3, NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements).
- C15 v2, C16 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Respuesta P1 = A de `nfr-requirements-questions.md`.

## 1. Métricas (Prometheus, en `/metrics` del puerto interno de `session-api`)

| ID | Estado | Métrica | Tipo | Etiquetas | Cuándo cambia |
|---|---|---|---|---|---|
| NFR15.1 | se mantiene | `veridicus_review_decisions_total` (C15 v2) | counter | `state`: `accepted`, `edited`, `dismissed` | +1 después del *commit* de cada `ReviewDecision` (NFR10.10) |
| NFR15.1 | cambia | `veridicus_session_dismissal_ratio` (C15 v2) | gauge | `session_id` (UUID) | Se recalcula después de cada decisión confirmada (NFR10.17). Se retira al bloquear o descartar la ronda y al purgar (NFR8.6) |
| NFR15.1 | **Retirado** | `veridicus_review_rejections_total` | — | — | No entra en C15 v2 y su etiqueta `code` no está entre las permitidas. Los rechazos se cuentan con el evento de log `review.decision_rejected` (NFR15.5) |

Las etiquetas solo llevan valores de enum y el `session_id` (NFR10.8).

## 2. Cálculo de la razón de descarte (P1 = A, C15 v2)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | La ventana son las últimas *W* sugerencias decididas de la sesión, con *W* = `dismissal_window_w` = 8 de C25 (NFR-U5-04). | Se calcula sobre la ronda `open` de la sesión, con la herencia de BR3.2. Una sugerencia está **decidida** si su estado vigente es `accepted`, `edited` o `dismissed`, propio de la ronda o heredado. Una `pending` nunca cuenta. Las decididas se ordenan por el `change_seq` de la decisión que da su estado vigente; la heredada conserva el suyo. La ventana son las **8 más recientes**, y la razón es (descartadas en la ventana) / 8. **La serie no se publica hasta que la sesión tiene 8 decididas.** Sin ronda `open` no hay serie: tras consolidar, tras descartar la copia y tras purgar. |
| NFR15.3 | cambia | El cálculo es una función pura probada por tabla. | `domain/dismissal_window.py` recibe la lista de sugerencias con su estado vigente y el `change_seq` de su decisión. Devuelve la razón o «sin publicar». Casos de nivel 0: <br>• 7 decididas → sin publicar; <br>• 8 decididas con 2 descartadas → 0,25, que no supera el umbral de U2; <br>• 8 con 3 descartadas → 0,375; <br>• 10 decididas → solo cuentan las 8 de mayor `change_seq`; <br>• una `pending` entre decididas no cuenta, y la razón no sube mientras llegan sugerencias nuevas; <br>• cambiar una decisión de `dismissed` a `accepted` la mueve al final de la ventana; <br>• en una corrección, una sugerencia sin decisión nueva usa el estado y el `change_seq` heredados; <br>• una ronda `discarded` no aporta decisiones. <br>Prueba de nivel 1 de punta a punta: tras 8 decisiones (3 descartes), `/metrics` muestra `0.375` para esa sesión, y tras `lock_round` la serie ya no está. |
| NFR15.4 | se mantiene | U5 publica; U2 decide la alerta. | La regla de Prometheus de U2 compara con `> 0.25` y su anotación es una **propuesta** de revisión del *prompt* o del perfil por PR (FR9.3). Ninguna regla cambia nada (NFR11.4). U5 entrega a U2 un archivo de series de ejemplo para su `promtool test rules`: `services/session-api/tests/human_review/fixtures/air_series.yaml`, con una sesión en 0,25 (sin alerta) y otra en 0,375 (con alerta). |

## 3. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.5 | cambia | Cada hecho de U5 deja un evento estructurado sin texto. | JSON en una línea con `timestamp`, `level`, `service`, `event` y solo los campos de NFR10.6. Eventos `INFO`: <br>• `review.decision_recorded` (`decision_id`, `suggestion_id`, `round_id`, `previous_state`, `state`, `user_id`); <br>• `review.decision_rejected` (`suggestion_id`, `user_id`, `code`); <br>• `review.observations_viewed` (`suggestion_id`, `user_id`, `first`); <br>• `review.round_opened` (`round_id`, `session_id`, `kind`); <br>• `review.round_locked` (`round_id`, `session_id`); <br>• `review.round_discarded` (`round_id`, `session_id`, `user_id`); <br>• `review.session_purged` (`session_id` y conteos por tabla). <br>`WARNING` por *timeout* de bloqueo o de sentencia y por `metrics.update_failed`; `ERROR` si la base no responde. Nunca nota, reformulación, observaciones, hecho ni citas. Una prueba de nivel 1 reconstruye la historia de una sugerencia solo con sus logs: propuesta, observaciones consultadas, aceptada, descartada, ronda bloqueada, corrección descartada y purga. |

## 4. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia de la decisión | p95 de la prueba `perf` de NFR3.1 | ≤ 200 ms |
| Rechazos por observaciones no consultadas | Conteo de `review.decision_rejected` con `code` `review.observations_not_viewed` en los logs | Informativo. La consola deshabilita los botones (BR5.1), así que un valor > 0 en uso real indica un cliente que no es la consola |
| Señal AIR | `veridicus_session_dismissal_ratio` | Informativo; la propuesta la genera U2 por encima de 0,25 |

## 5. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Decisiones por estado y razón de descarte por sesión,
  junto al panel de U4.
- **Alertas.** Ninguna avisa a nadie en el MVP. La única regla relacionada con U5 es la de AIR de U2, que
  solo propone.
- **Trazas distribuidas.** No aplican: U5 vive en un solo proceso, y basta la correlación por
  `suggestion_id`, `round_id` y el identificador de la petición.
