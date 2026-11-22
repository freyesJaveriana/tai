# Diseño de escalado — U5 human-review

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Las tablas ya se purgan por retención (C24). La cardinalidad cuenta el estado `discarded` y
  la purga, con reconciliación en la API (NFRD-U5-01). Sale la métrica de rechazos. Los índices usan
  `change_seq` (NFRD-U5-06).
- **Numeración.** §1–§6 conservan su número.

**Insumos.** `nfr-requirements/scalability-requirements.md` (scalability-requirements: NFR8.2–NFR8.6),
`performance-requirements.md` (performance-requirements), `security-requirements.md`
(security-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions: D2, D4, D7, D13, D14) de esta unidad; F2, F5–F7 de
`functional-design/functional-spec.md` (functional-spec); C11, C15 v2, C24 y C25 de `contract-summary.md`
(contract-summary); NFRD-U4-11 de U4.

## 1. Modelo de capacidad

| Dimensión | Esperado | Probado | Margen |
|---|---|---|---|
| Analistas a la vez | 1 | 2 hilos y 2 instancias de la aplicación por sesión | Coordinación en la base |
| Sugerencias por sesión | ≤ 25 | 50 (`perf`) y 250 (NFR8.2) | 10× |
| Rondas por sesión | ≤ 4 | 10, con una `discarded` | 2,5× |
| Filas de `review_decision` | ≤ 30 000 (100 sesiones) | 30 000 cargadas (NFR8.3) | — |
| Series de `veridicus_session_dismissal_ratio` | ≤ 1 por sesión con ronda `open` y 8 decididas | 60 sesiones | Señal a 200 |

La unidad de serialización es **la sesión**: toda escritura que cambia una sesión toma primero su fila
(`change_cursor.bump`). Sesiones distintas no se esperan entre sí; dentro de una sesión hay un solo analista.

## 2. Carga de 10× (NFR8.2)

Variante `perf` de NFR3.1 con 250 sugerencias y 10 rondas, una `discarded`: decisión p95 ≤ 200 ms y estado
vigente de toda la sesión p95 ≤ 100 ms. Lo sostienen el número fijo de sentencias (`performance-design.md`
§2) y los índices de §3; ninguna consulta recorre rondas una por una.

## 3. Índices (NFR8.3, NFRD-U5-06)

| Tabla | Índice | Uso |
|---|---|---|
| `review_decision` | `(round_id, suggestion_id, change_seq)` único | Estado vigente de la sesión; purga por `round_id` |
| `review_decision` | `(suggestion_id, change_seq)` | Estado vigente de una sugerencia (sustituye a `(suggestion_id)`) |
| `review_decision` | `(round_id, change_seq)` | `changed_since` del sondeo de U4 (nuevo) |
| `review_round` | `(session_id, number)` único | Herencia, filtro de `discarded` y purga |
| `review_round` | `(session_id) WHERE status = 'open'` único parcial | Una sola ronda abierta |
| `observations_view` | `(suggestion_id, user_id)` único | Idempotencia, BR2.2 y purga |
| `review_suggestion` | `(session_id, change_seq)` (de U4, NFRD-U4-11) | Sondeo y purga |

**Verificación (nivel 1).** Una prueba consulta `pg_indexes` y exige los seis de U5. Con 30 000 decisiones
cargadas y `ANALYZE`, `EXPLAIN` del estado vigente, de `changed_since` y de los `DELETE` de `purge_session` no
muestra `Seq Scan` sobre `review_decision` ni `observations_view`.

## 4. Varias réplicas (NFR8.4)

- Toda la coordinación vive en PostgreSQL: el `bump` de la sesión, el bloqueo de la ronda, los índices
  únicos y los disparadores. Ningún estado de negocio vive en memoria del proceso.
- **Verificación (nivel 1).** Dos instancias de la aplicación (dos `TestClient` con *engines* separados)
  deciden la misma sugerencia a la vez: el resultado es el mismo que con una (2 filas en orden, o 1 fila y
  `409`).
- **Límite conocido.** La razón de descartes se calcula en el proceso que atendió la decisión (D7) y es
  exacta por proceso. El MVP corre **1 réplica**. Con más, cada réplica publica su valor y la reconciliación
  (§5) retira series viejas, pero el valor es solo eventualmente exacto. Para tenerlo exacto, la serie se
  calcula al leer `/metrics` desde la base: es un cambio de D7 por PR, con su medición de NFR3.6.

## 5. Crecimiento y cardinalidad (NFR8.5, NFR8.6)

- **Tablas.** `review_decision`, `observations_view`, `review_suggestion` y `review_round` son historial y
  solo las borra `purge_session` con el `Job` de retención. Con el peor caso de §1 ocupan < 50 MB, medido con
  `pg_total_relation_size` en la prueba de NFR8.3. Una sesión purgada deja 0 filas en las cuatro.
- **Series.** `veridicus_review_decisions_total` tiene 3. `veridicus_session_dismissal_ratio` existe solo
  mientras la sesión tiene ronda `open` y 8 decididas. Se retira así:

| Evento | Proceso | Cómo |
|---|---|---|
| `lock_round` | API (ruta de U7) | `apply(seq, None)` en `after_commit` |
| `discard_correction_round` | API (ruta de U7) | Igual |
| `purge_session` | `Job` de U13, otro proceso | La reconciliación de la API la retira en ≤ 60 s (NFRD-U5-01) |
| Una corrección registra decisiones | API | La serie vuelve si hay 8 decididas |

- **Verificación (nivel 1, amplía E31).** 60 sesiones con ventana completa: 20 consolidadas, 5 con la copia
  descartada y 5 purgadas desde otro *engine* que simula el `Job`; tras una vuelta de la reconciliación quedan
  30 series como máximo.

## 6. Señales para escalar

Sin autoescalado. Si el p95 de NFR3.1 pasa de 200 ms en la prueba `perf`, o las series de la razón pasan de
200, en este orden:
1. Revisar los índices de §3 y sus planes.
2. Calcular la razón al leer `/metrics` desde la base.
3. Retirar la etiqueta `session_id` con el cambio mayor de C15 que prevén las reglas de los contratos.

Cada cambio entra por PR con su medición.
