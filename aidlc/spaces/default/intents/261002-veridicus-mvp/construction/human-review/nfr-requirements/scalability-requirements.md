# Requisitos de escalado — U5 human-review

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U5. Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia:**
  - las tablas ya se purgan por retención (C24, A-2);
  - la cardinalidad cuenta el estado `discarded` y la purga;
  - sale la métrica de rechazos;
  - los índices usan `change_seq`.
- **IDs.** Se conservan NFR8.2–NFR8.6.

**Insumos.**
- Flujos F2, F5, F6 y F7 de `functional-design/functional-spec.md` (functional-spec).
- Reglas BR3.2, BR3.8, BR3.9, BR4.1 y BR6.1 de `functional-design/rules.md` (rules) y entidades de
  `entities.md`.
- NFR8, NFR11 y los supuestos de `inception/requirements-analysis/requirements.md` (requirements), con
  VE-12 y A-2 de la adenda 02.
- C11, C15 v2, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Respuesta P1 = A de `nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real y sustentación) | Supuestos de requirements |
| Sugerencias por sesión | ≤ 25 esperadas; las pruebas usan 50 y el peor caso 250 | Conjunto sintético; NFR8.2 |
| Rondas por sesión | ≤ 4 esperadas (la inicial, una o dos correcciones y alguna descartada); las pruebas llegan a 10 | Supuesto del MVP |
| Decisiones por sugerencia y ronda | ≤ 3 (decidir y cambiar de opinión) | Supuesto del MVP |
| Sesiones vivas a la vez | ≤ 100 en el MVP, incluidas las de prueba. La retención las borra a los ≤ 90 días | Supuesto del MVP; VE-12 |
| Filas de `ReviewDecision` | ≤ 100 × 25 × 4 × 3 = 30 000 en el peor caso | Cálculo |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.2 | cambia | Las metas de rendimiento aguantan 10 veces la carga por sesión. | Es una variante de la prueba `perf` de NFR3.1, con 250 sugerencias y 10 rondas, una de ellas `discarded`. La decisión tarda p95 ≤ 200 ms y la consulta del estado vigente, p95 ≤ 100 ms. |
| NFR8.3 | cambia | Las consultas de U5 y la purga usan índices. | Índices: <br>• `ReviewDecision (round_id, suggestion_id, change_seq)`, único; <br>• `ReviewDecision (suggestion_id)`; <br>• `ReviewRound (session_id, number)`, único; <br>• `ReviewRound (session_id) WHERE status = 'open'`, único parcial; <br>• `ObservationsView (suggestion_id, user_id)`, único. <br>Una prueba de nivel 1 consulta `pg_indexes`. Con 30 000 decisiones cargadas, ni `EXPLAIN` de la consulta del estado vigente ni los `DELETE` de `purge_session` hacen `Seq Scan` sobre `ReviewDecision`. |
| NFR8.4 | cambia | U5 no impide correr más de una réplica de `session-api` para las decisiones. | Toda la coordinación está en la base: el *bump* de la sesión, el bloqueo de la ronda y los índices únicos (NFR10.11–NFR10.13). Una prueba de nivel 1 decide la misma sugerencia desde dos instancias de la aplicación y obtiene el mismo resultado que con una. El MVP corre 1 réplica. **Límite conocido:** el valor de `veridicus_session_dismissal_ratio` es exacto por proceso (NFR10.17). Con más de una réplica, cada una publica la serie de las decisiones que atendió, y su valor es eventualmente exacto. Para tenerlo exacto, la serie debe calcularse al leer `/metrics` desde la base, lo que es un cambio de D7 por PR. |
| NFR8.5 | cambia | Las tablas de U5 crecen poco y solo se purgan por retención. | `ReviewDecision`, `ObservationsView`, `ReviewSuggestion` y `ReviewRound` son historial de auditoría (NFR11). Solo las borra `purge_session`, con el `Job` de retención (NFR11.5). Con el peor caso de §1 ocupan < 50 MB. Una sesión purgada deja 0 filas en las cuatro tablas (NFR10.22). |
| NFR8.6 | cambia | La cardinalidad de las métricas está acotada (C15 v2). | `veridicus_review_decisions_total` tiene 3 series. `veridicus_session_dismissal_ratio` tiene como mucho una serie por sesión con ronda `open` y ventana completa. La serie se retira: <br>• al bloquear la ronda; <br>• al descartar la copia de trabajo; <br>• al purgar la sesión. <br>Vuelve si una corrección registra decisiones. Prueba de nivel 1 con 60 sesiones con ventana completa: 20 consolidadas, 5 con la copia descartada y 5 purgadas dejan 30 series como máximo (amplía E31). |

## 3. Señal para escalar

No hay autoescalado. Hay dos señales:
- la consola tarda en decidir (p95 de NFR3.1 por encima de 200 ms en la prueba `perf`);
- el número de series de `veridicus_session_dismissal_ratio` pasa de 200.

Las opciones, en este orden, son:
1. Revisar los índices de NFR8.3.
2. Para las métricas, calcular la razón al leer `/metrics` y retirar la etiqueta `session_id`, con el
   cambio mayor de C15 que prevén las reglas de propiedad de los contratos.

Cada cambio entra por PR con su medición.
