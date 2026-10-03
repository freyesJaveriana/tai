# Requisitos de escalado — U5 human-review

**Insumos.** Flujos F2, F4 y F5 de `functional-design/functional-spec.md` (functional-spec); reglas
BR3.2, BR3.5 y BR4.1 de `functional-design/rules.md` (rules) y entidades de `entities.md`; NFR8 y los
supuestos de `inception/requirements-analysis/requirements.md` (requirements); C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real y sustentación) | Supuestos de requirements |
| Sugerencias por sesión | Decenas: ≤ 25 esperadas (≤ 15 turnos con pocas alertas cada uno); las pruebas usan 50 | Golden Dataset; NFR8.8 de U4 |
| Rondas por sesión | ≤ 3 esperadas (la inicial y una o dos correcciones); las pruebas llegan a 10 | Supuesto del MVP |
| Decisiones por sugerencia y ronda | ≤ 3 (decidir y cambiar de opinión) | Supuesto del MVP |
| Sesiones revisadas en total | ≤ 100 en el MVP (incluidas las de prueba) | Supuesto del MVP |
| Filas de `ReviewDecision` | ≤ 100 × 25 × 3 × 3 ≈ 22 500 en el peor caso | Cálculo |

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.2 | Las metas de rendimiento aguantan 10 veces la carga por sesión. | Variante de la prueba `perf` de NFR3.1 con 250 sugerencias y 10 rondas: decisión p95 ≤ 200 ms y consulta del estado vigente p95 ≤ 100 ms. |
| NFR8.3 | Las consultas de U5 usan índices. | Índices en `ReviewDecision (suggestion_id, round_id, at, seq)`, `ReviewRound (session_id, number)` único, `ReviewRound (session_id) WHERE status = 'open'` único parcial y `CotView (suggestion_id, user_id)` único. Prueba de nivel 1 que consulta `pg_indexes` y que, con 22 500 decisiones cargadas, `EXPLAIN` de la consulta del estado vigente no hace `Seq Scan` sobre `ReviewDecision`. |
| NFR8.4 | U5 no impide correr más de una réplica de `session-api` para las decisiones. | Toda la coordinación está en la base (bloqueo de la ronda, índices únicos, NFR10.11–NFR10.13); una prueba de nivel 1 decide la misma sugerencia desde dos instancias de la aplicación y obtiene el mismo resultado que con una. El MVP corre 1 réplica. **Límite conocido:** el valor de `veridicus_session_dismissal_ratio` se calcula en el proceso que atendió la decisión (D7); con más de una réplica, la serie debe pasar a calcularse al leer `/metrics` desde la base (cambio de D7 por PR). |
| NFR8.5 | Las tablas de U5 crecen poco y no se purgan. | `ReviewDecision`, `CotView` y `ReviewRound` son historial de auditoría (NFR11) y no se borran; con el peor caso de §1 ocupan < 50 MB. |
| NFR8.6 | La cardinalidad de las métricas está acotada (C15). | `veridicus_review_decisions_total` tiene 3 series y `veridicus_review_rejections_total` tantas como `code` de U5 (≤ 5). `veridicus_session_dismissal_ratio` tiene como mucho una serie por sesión con ronda `open` y ventana completa: la serie se retira al bloquear la ronda (consolidación) y vuelve si una corrección registra decisiones. Prueba de nivel 1 con 60 sesiones, 20 de ellas consolidadas: 40 series como máximo. |

## 3. Señal para escalar

No hay autoescalado. Si la consola tarda en decidir (p95 de NFR3.1 por encima de 200 ms en la prueba
`perf`) o el número de series de `veridicus_session_dismissal_ratio` pasa de 200, las opciones, en este
orden, son: revisar los índices de NFR8.3 y, para las métricas, calcular la razón al leer `/metrics` y
retirar la etiqueta `session_id` con el cambio mayor de C15 que el propio contrato prevé. Cada cambio
entra por PR con su medición.
