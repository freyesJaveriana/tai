# Diseño de escalado — U5 human-review

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F2, F4 y F5 de
`functional-design/functional-spec.md` (functional-spec); C1, C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-design-questions.md`; diseño de U4 (cursor `change_seq`).

## 1. Modelo de capacidad

| Dimensión | Esperado | Probado | Margen |
|---|---|---|---|
| Analistas a la vez | 1 | 2 hilos concurrentes por sesión | Coordinación en la base |
| Sugerencias por sesión | ≤ 25 | 50 (perf) y 250 (NFR8.2) | 10× |
| Rondas por sesión | ≤ 3 | 10 | 3× |
| Filas de `ReviewDecision` | ≈ 22 500 peor caso | 22 500 cargadas (NFR8.3) | — |
| Series de `veridicus_session_dismissal_ratio` | ≤ 1 por sesión con ronda `open` | 60 sesiones, 20 consolidadas | Señal a 200 series |

La unidad de serialización es **la sesión**: con P1 = A toda escritura que cambia algo de una sesión
(turno de U4, decisión de U5, bloqueo y corrección de U7) toma primero la fila de la sesión. Sesiones
distintas no se esperan entre sí; dentro de una sesión hay un solo analista, así que la espera es
despreciable.

## 2. Carga de 10× (NFR8.2)

Variante `perf` de NFR3.1 con 250 sugerencias y 10 rondas: decisión p95 ≤ 200 ms y consulta del estado
vigente de toda la sesión p95 ≤ 100 ms. Lo sostienen el número fijo de sentencias (performance-design
§2) y los índices de §3; ninguna consulta recorre rondas una por una.

## 3. Índices (NFR8.3)

| Tabla | Índice | Uso |
|---|---|---|
| `review_decision` | `(suggestion_id, round_id, at, seq)` | Estado vigente (D2) |
| `review_decision` | `(round_id, change_seq)` | Sondeo con cursor (P1 = A) |
| `review_round` | `(session_id, number)` único | Herencia por número |
| `review_round` | `(session_id) WHERE status = 'open'` único parcial | Una sola ronda abierta |
| `cot_view` | `(suggestion_id, user_id)` único | Idempotencia y comprobación de BR2.2 |

**Verificación (nivel 1).** Una prueba consulta `pg_indexes` y exige los cinco; con 22 500 decisiones
cargadas y `ANALYZE`, `EXPLAIN` de la consulta del estado vigente y de la del sondeo no muestra
`Seq Scan` sobre `review_decision`.

## 4. Varias réplicas (NFR8.4)

- Toda la coordinación vive en PostgreSQL: bloqueo de la fila de la sesión y luego de la ronda,
  índices únicos y *trigger* de ronda bloqueada. Ningún estado de negocio vive en memoria del proceso.
- **Verificación (nivel 1).** Dos instancias de la aplicación (dos `TestClient` con *engines*
  separados) deciden la misma sugerencia a la vez; el resultado es el mismo que con una (2 filas en
  orden o 1 fila y `409`).
- **Límite conocido.** `veridicus_session_dismissal_ratio` se calcula en el proceso que atendió la
  decisión (D7). El MVP corre **1 réplica** de la API; para pasar a más, la serie se calcula al leer
  `/metrics` desde la base (cambio de D7 por PR, con su medición de NFR3.6).

## 5. Crecimiento y cardinalidad (NFR8.5, NFR8.6)

- `review_decision`, `cot_view` y `review_round` son historial de auditoría y no se purgan; el peor caso
  ocupa < 50 MB. La prueba de NFR8.3 mide `pg_total_relation_size` con las 22 500 filas: < 50 MB.
- `veridicus_review_decisions_total`: 3 series; `veridicus_review_rejections_total`: ≤ 5 series.
- `veridicus_session_dismissal_ratio`: la serie se retira (`remove`) en el `after_commit` de
  `lock_round` y vuelve si una corrección registra decisiones con ventana completa. Prueba de nivel 1
  con 60 sesiones, 20 consolidadas: ≤ 40 series.

## 6. Señales para escalar

Sin autoescalado. Si el p95 de NFR3.1 pasa de 200 ms o las series de la razón pasan de 200, en este
orden: revisar los índices de §3 y sus planes; calcular la razón al leer `/metrics`; retirar la
etiqueta `session_id` con el cambio mayor de C15 que el contrato prevé. Cada cambio entra por PR con su
medición.
