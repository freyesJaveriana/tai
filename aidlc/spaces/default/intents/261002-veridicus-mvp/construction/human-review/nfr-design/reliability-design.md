# Diseño de fiabilidad — U5 human-review

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F2–F5 y §8 de
`functional-design/functional-spec.md` (functional-spec); C1, C10, C11, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-design-questions.md`; diseño de U3 (*timeouts*, `503`) y de U4 (cursor `change_seq`, ingesta
idempotente).

U5 no usa colas ni modelos: su fiabilidad descansa en transacciones cortas de PostgreSQL, un orden de
bloqueo único y la ausencia de reintentos automáticos de decisiones.

## 1. Orden de bloqueo único y cursor de cambios (P1 = A)

**Regla para todo `session-api`:** una transacción que cambia algo de una sesión bloquea **primero la
fila de la sesión** y **después**, si la necesita, la fila de la ronda. Nunca al revés.

- **Primitiva compartida.** `session_api/shared/change_cursor.py` expone
  `bump(uow, session_id) -> int`: un `UPDATE interview_session SET change_seq = change_seq + 1 WHERE id
  = :id RETURNING change_seq`, que bloquea la fila. La `UnitOfWork` guarda el valor por sesión: una
  segunda llamada en la misma transacción devuelve el mismo número sin otro `UPDATE`. El módulo
  `shared` no importa ninguna unidad, así que U4, U5 y U7 lo usan sin ciclos (import-linter).
- **Quién lo llama.**

| Operación | Unidad | Paso 1 | Paso 2 | Marca con `change_seq` |
|---|---|---|---|---|
| Encolar, ingerir, vencer turnos | U4 | `bump` | — (o `propose`, que lee la ronda) | Turnos, sugerencias, paquetes |
| `decide` (C10) | U5 | `bump` | Ronda `open` `FOR UPDATE` | Nueva columna `review_decision.change_seq` |
| `open_round(for_update=True)` (C11) | U5, la llama U7 | `bump` dentro de la propia operación | Ronda `open` `FOR UPDATE` | — (la marca la fila de U7 o la ronda) |
| `lock_round`, `open_correction_round` (C11) | U5, las llama U7 | `bump` (devuelve el valor ya tomado) | Ronda | `review_round.change_seq` |
| `cot-views` | U5 | Ninguno: no cambia el estado vigente | — | — |

- **Precondición comprobada.** El repositorio de rondas (`human_review/adapters/round_repository.py`)
  es el único sitio con `FOR UPDATE` sobre `review_round`, y antes de emitirlo exige que la `UnitOfWork`
  ya tenga el `bump` de esa sesión; si no, lanza un error de programación. `propose` exige lo mismo
  (U4 ya bloqueó la sesión al ingerir). Prueba de nivel 0: una llamada sin `bump` falla; un chequeo
  estático falla si aparece `FOR UPDATE` sobre `review_round` fuera de ese archivo.
- **Sondeo.** El sondeo de U4 añade las sugerencias con alguna decisión de `change_seq > cursor` y
  devuelve su estado vigente; la ronda y `can_consolidate` cambian con su propio `change_seq`. Como las
  escrituras de una sesión quedan en serie, ningún cambio confirma con un número menor que uno ya
  entregado (NFR10.20 de U4).

## 2. Transacciones y concurrencia (NFR10.10–NFR10.14)

| ID | Diseño | Verificación (nivel 1, PostgreSQL real, D9) |
|---|---|---|
| NFR10.10 | `decide` es una `UnitOfWork`: `bump` → ronda → estado vigente → validación → `INSERT` → `COMMIT`. Las métricas solo en `after_commit` | Fallo inyectado tras calcular el estado y tras insertar: 0 filas, contador sin cambio, `change_seq` de la sesión sin cambio |
| NFR10.11 | El bloqueo de la sesión (y el de la ronda) serializa las decisiones de una sesión antes de leer el estado vigente | Dos hilos con barrera, 50 repeticiones: aceptar y descartar a la vez dejan 2 filas en orden y el `previous_state` de la segunda es el `state` de la primera; dos idénticas dejan 1 fila y un `409` `review.invalid_transition` |
| NFR10.12 | `lock_round` es `UPDATE … WHERE round_id = :id AND status = 'open'` y comprueba 1 fila; si no, `report.conflict`. U7 empieza con `open_round(for_update=True)` | Dos consolidaciones: una gana y otra `report.conflict`; decisión simultánea a la consolidación: o aparece en `decisions` o recibe `409` `review.round_locked`; ninguna `at` posterior a `locked_at` |
| NFR10.13 | `propose` es idempotente por (`turn_id`, `attempt`, `claim_index`) con índice único; la ronda 1 se abre bajo el bloqueo de la sesión que ya tomó U4, y el único parcial queda como segunda barrera | Dos llamadas iguales: mismos `suggestion_id`, 0 filas nuevas; dos `propose` simultáneas en una sesión sin rondas: una sola ronda `open` |
| NFR10.14 | `cot-views` con `INSERT … ON CONFLICT DO NOTHING` | 10 llamadas iguales: 1 fila y 10 `204` |
| P1 = A | Orden sesión → ronda en todos los caminos | Tres hilos (decisión de U5, ingesta de U4 con `propose`, consolidación de U7 con `open_round(for_update=True)`) sobre la misma sesión, barrera, 50 repeticiones: 0 errores `40P01` (*deadlock*) y un sondeo desde el cursor inicial recibe todos los cambios confirmados |

## 3. *Timeouts* y fallos (NFR10.15–NFR10.17)

- **Espera acotada.** `statement_timeout` de 2 s (U3) y `lock_timeout` de 2 s
  (`VERIDICUS_DB_LOCK_TIMEOUT_MS`) por sesión de base, validados al arrancar. Al vencer: *rollback*,
  `503` `system.unavailable`, 0 filas, `WARNING` con `code`. El bloqueo de la sesión lo comparten ahora
  U4 y U7; sus transacciones bajo ese bloqueo son cortas (sin E/S de red), así que la espera esperada es
  de milisegundos. Prueba: una transacción retiene el bloqueo de la sesión 3 s → la decisión responde
  `503` en ≤ 2,5 s.
- **Sin reintentos de decisiones.** Una decisión no es idempotente: ni servidor ni consola la
  reintentan. Ante red caída o `503`, la consola conserva lo escrito, muestra el mensaje del catálogo y
  vuelve a pedir la sesión; un reenvío manual de una decisión que sí se guardó recibe `409`
  `review.invalid_transition` y la tarjeta muestra el estado vigente. `cot-views` sí se reintenta
  (0,5 s, 1 s, 2 s). Vitest con servidor *fake*.
- **Métricas que fallan.** Si el recálculo de la razón falla tras el *commit*: la respuesta sigue
  siendo `201`, `WARNING` `metrics.update_failed` y la serie conserva su valor. Al arrancar, la API
  reconstruye las series de las sesiones con ronda `open` con una consulta de ≤ 2 s; si falla, arranca
  igual. Prueba de nivel 1 con fallo inyectado.

## 4. Salud (NFR10.18)

`/readyz` de la API responde `503` si falta o es inválida la configuración de U5
(`VERIDICUS_AIR_WINDOW`, `VERIDICUS_REVIEW_TEXT_MAX_CHARS`, `VERIDICUS_DB_LOCK_TIMEOUT_MS`) o si
PostgreSQL no responde; una configuración inválida termina el proceso con código distinto de 0 antes
de escuchar. La reconstrucción de métricas no entra en `/readyz`. Prueba de nivel 1.

## 5. Recuperación y degradación

| Falla | Qué se pierde | Recuperación |
|---|---|---|
| Reinicio de la API en medio de una decisión | Nada (sin *commit*) | El analista ve el estado vigente y repite |
| Reinicio de la API | Valores en memoria de la razón | Reconstrucción al arrancar; contadores a 0 (`rate()` lo tolera) |
| PostgreSQL no responde | Nada guardado | `503`; la consola conserva lo escrito |
| Pérdida de la base | Según respaldo de CloudNativePG | Lo fija Infrastructure Design |
| Juez, Redis o Prometheus caídos | Nada de U5 | U5 solo necesita PostgreSQL: se revisa, decide y consolida igual |

## 6. Objetivo de punta a punta (NFR8.7)

`frontend/e2e/review.spec.ts` (desplegar la CoT, aceptar con nota, editar, descartar con nota, cambiar
una decisión, ver una sesión ajena en solo lectura y, en otra pestaña, ver la decisión llegar por el
sondeo incremental) pasa con 0 fallos en cada corrida de nivel 3 antes de etiquetar una entrega:
`npx --prefix frontend playwright test e2e/review.spec.ts`.

## 7. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `human-review/functional-design/entities.md` | `ReviewDecision` y `ReviewRound` llevan la columna `change_seq` (sin `UPDATE` sobre decisiones: se fija al insertar) | P1 = A |
| `human-review/nfr-requirements/tech-stack-decisions.md` (D3) | El bloqueo de la ronda va **precedido** del bloqueo de la fila de la sesión (`change_cursor.bump`); el orden sesión → ronda es obligatorio | P1 = A |
| `human-review/nfr-requirements/scalability-requirements.md` (NFR8.3) | Se añade el índice `review_decision (round_id, change_seq)` | P1 = A |
| `inception/contract-design/contract-summary.md` (C11) | `open_round(..., for_update=True)` incrementa primero el `change_seq` de la sesión y después bloquea la ronda; `lock_round` y `open_correction_round` marcan la ronda con el `change_seq` | P1 = A; NFR10.12 |
| `inception/contract-design/contract-summary.md` (C10) | `propose` y `decide` exigen que la `UnitOfWork` ya tenga el bloqueo de la sesión (`bump`) | P1 = A |
| `text-flow/nfr-design/reliability-design.md` y `performance-design.md` (U4) | El incremento de `change_seq` de U4 usa la primitiva compartida `session_api/shared/change_cursor.py`; el sondeo incluye las sugerencias con decisiones de `change_seq > cursor` | P1 = A |
| Functional Design y NFR de U7 | La consolidación y la corrección siguen el orden sesión → ronda; empezar con `open_round(for_update=True)` basta, porque esa operación toma la sesión primero | P1 = A |
| `contracts/limits.v1.yaml` (diseño de U1) | Nuevas entradas `review_text_max_chars: 2000` y `review_body_max_bytes: 65536`, dueño U5, usadas en C1 | NFR10.5 |
| `identity-access/nfr-design/observability-design.md` (U3) | La lista blanca del formateador de logs admite los campos `suggestion_id`, `round_id`, `decision_id`, `report_version_id`, `state`, `previous_state`, `kind` y `first` (solo identificadores y enums) | NFR15.5 |
