# Diseño de fiabilidad — U5 human-review

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** El orden de bloqueo pasa a usuario → sesión → ronda (BR3.8, NFRD-U3-01). Entran
  `discard_correction_round`, `purge_session` y la publicación en orden de la razón (cierra R-03). El
  sondeo en una instantánea (NFRD-U4-05) cierra R-01, y el supervisor por sesión (NFRD-U4-06) cierra R-02.
- **Numeración.** §1–§6 conservan su número; §7 (precisiones) queda **Retirado** y pasa a la tabla
  NFRD-U5-xx de `security-design.md` §11.

**Insumos.** `nfr-requirements/reliability-requirements.md` (reliability-requirements: NFR8.7,
NFR10.10–NFR10.18), `performance-requirements.md` (performance-requirements), `security-requirements.md`
(security-requirements), `scalability-requirements.md` (scalability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions: D3, D7, D9, D13, D14) de esta unidad; F2, F5–F7 y §10 de
`functional-design/functional-spec.md` (functional-spec); C1, C10, C11, C15 v2, C16 y C24 de
`contract-summary.md` (contract-summary); NFR Design de U3 (§5.4, reliability-design) y de U4 (NFRD-U4-05,
NFRD-U4-06).

U5 no usa colas ni modelos: su fiabilidad descansa en transacciones cortas de PostgreSQL, un orden de
bloqueo único y la ausencia de reintentos automáticos de decisiones.

## 1. Orden de bloqueo único y cursor de cambios (P1 = A)

**Regla para todo `session-api`:** `app_user` del principal `FOR SHARE` (lo toma `GuardedRoute`) →
`web_session` (si escribe actividad) → fila de la sesión (`change_cursor.bump`) → corrida (U4) → ronda. Nunca
al revés.

- **Primitiva compartida.** `session_api/shared/change_cursor.py` expone `bump(uow, session_id) -> int`:
  `UPDATE interview_session SET change_cursor = change_cursor + 1 WHERE id = :id RETURNING change_cursor`,
  que bloquea la fila. La `UnitOfWork` memoriza el valor por sesión: una segunda llamada en la misma
  transacción devuelve el mismo número sin otro `UPDATE`. El módulo `shared` no importa ninguna unidad. Lo
  escribe U4 en B3, que lo usa primero, con este diseño.

| Operación | Quién la llama | Paso 1 | Paso 2 | Marca con `change_seq` |
|---|---|---|---|---|
| `decide` (C10) | ConsoleApi | `bump` | Ronda `open` `FOR UPDATE` | `review_decision.change_seq` |
| `open_round(for_update=True)` (C11) | U7 | `bump` (memorizado si U7 ya lo hizo) | Ronda `open` `FOR UPDATE`, o crea la ronda 1 | `review_round.change_seq` si la crea |
| `lock_round`, `open_correction_round`, `discard_correction_round` (C11) | U7 | `bump` | Ronda | `review_round.change_seq` |
| `propose` (C10) | Ingesta de U4 | `bump` ya hecho por U4 | Ronda `open` | Sugerencias y ronda 1 (código de U4) |
| `record_observations_view` | ConsoleApi | Ninguno: no cambia el estado vigente | — | — |
| `purge_session` (C24) | `Job` de U13 | Ninguno: borra la sesión entera en la transacción del `Job` | — | — |

- **Precondición comprobada.** `human_review/adapters/round_repository.py` es el único sitio con
  `FOR UPDATE` sobre `review_round`, y antes de emitirlo exige que la `UnitOfWork` tenga el `bump` de esa
  sesión; si no, lanza un error de programación. Nivel 0: una llamada sin `bump` falla; un chequeo estático
  falla si aparece `FOR UPDATE` sobre `review_round` fuera de ese archivo.
- **Sondeo sin pérdidas (cierra R-01).** U4 lee en una sola transacción `REPEATABLE READ READ ONLY`: primero
  `change_cursor`, después las filas con `change_seq > n`, y devuelve el cursor leído (NFRD-U4-05). Las
  sugerencias cuyo estado vigente pudo cambiar las da `changed_since` de U5 (NFRD-U5-07), que cubre también
  el descarte de una copia.
- **Barrido de U4 en orden (cierra R-02).** El supervisor recorre las sesiones una a una, en orden de
  `session_id`, con `bump` primero (NFRD-U4-06).
- **`lock_timeout`.** `VERIDICUS_DB_LOCK_TIMEOUT_MS` (2 000) se fija al abrir cada conexión en
  `session_api/shared/db.py`, junto al `statement_timeout` de 2 s, para la API, el trabajador y los `Job`s
  (NFRD-U5-10).

## 2. Transacciones y concurrencia (NFR10.10–NFR10.14)

| ID | Diseño | Verificación (nivel 1, PostgreSQL real, D9) |
|---|---|---|
| NFR10.10 | `decide` corre en la `UnitOfWork` de la petición: `bump` → ronda → estado vigente → validación → `INSERT` → `COMMIT`. Las métricas y los logs de éxito solo en `after_commit` | Fallo inyectado tras calcular el estado y tras insertar: 0 filas, `change_cursor` y contador sin cambio |
| NFR10.11 | El bloqueo de la sesión, y luego el de la ronda, serializan las decisiones de una sesión antes de leer el estado vigente | Dos hilos con barrera, 50 repeticiones: aceptar y descartar a la vez dejan 2 filas con `change_seq` crecientes y el `previous_state` de la segunda es el `state` de la primera; dos idénticas dejan 1 fila y un `409` `review.invalid_transition` (E33) |
| NFR10.12 | `lock_round`: `UPDATE review_round SET status = 'locked', locked_at = :t, change_seq = :seq WHERE round_id = :id AND status = 'open'`; si afecta 0 filas, `report.conflict`. U7 empieza con `open_round(for_update=True)`, que con 0 sugerencias crea la ronda 1 (E20) | Dos consolidaciones: una gana y la otra `report.conflict` (E11); decisión simultánea a la consolidación: o aparece en `decisions` o recibe `409` `review.round_locked` (E18); ninguna decisión con `change_seq` mayor que el de su ronda al bloquearse |
| NFR10.13 | `propose` y su idempotencia son de U4 (C10). U5 aporta el único parcial de ronda `open` como segunda barrera | Dos `propose` simultáneas en una sesión sin rondas, más un `open_round(for_update=True)`: una sola ronda `open`, `kind: initial` |
| NFR10.14 | `record_observations_view`: `INSERT … ON CONFLICT (suggestion_id, user_id) DO NOTHING`, sin `bump` | 10 llamadas iguales: 1 fila, 10 `204` y 10 entradas de acceso |
| BR3.9 | `discard_correction_round`: `bump` → ronda `open` `FOR UPDATE` → si es `correction`, `UPDATE … SET status = 'discarded', discarded_by, discarded_at, change_seq`; si no hay copia, `report.conflict` | E25, E26; descartar y decidir a la vez: o la decisión entra antes y queda en el rastro, o recibe `409` |
| P1 = A | Orden usuario → sesión → ronda en todos los caminos | Cuatro hilos sobre la misma sesión (decisión de U5, ingesta de U4 con `propose`, consolidación de U7 y barrido del supervisor de U4), barrera, 50 repeticiones: 0 errores `40P01` y un sondeo concurrente desde el cursor inicial recibe todos los cambios confirmados |

## 3. *Timeouts* y fallos (NFR10.15–NFR10.17)

- **Espera acotada.** `statement_timeout` de 2 s (U3) y `lock_timeout` de 2 s, validados al arrancar. Al
  vencer: *rollback*, `503` `system.unavailable`, 0 filas y `WARNING` con `code` y `duration_ms`. Bajo el
  bloqueo de la sesión no hay E/S de red, así que la espera esperada es de milisegundos; el caso largo es la
  consolidación máxima de U7 (hasta 8 s), declarado en su NFR3.13. Prueba: una transacción retiene la
  sesión 3 s → la decisión responde `503` en ≤ 2,5 s.
- **Sin reintentos de decisiones.** Una decisión no es idempotente: ni el servidor ni la consola la
  reintentan. Ante red caída o `503`, la consola conserva lo escrito, muestra el mensaje del catálogo y
  vuelve a pedir la sesión; un reenvío manual de una decisión que sí se guardó recibe `409`
  `review.invalid_transition` y la tarjeta muestra el estado vigente. `observation-views` sí se reintenta a
  los 0,5 s, 1 s y 2 s, salvo ante `403`, `404` o `413`. Vitest con un servidor *fake* que falla y otro que
  responde `409`.
- **Métricas en orden (D13; cierra R-03).** `ReviewMetrics` guarda por sesión el último `change_seq`
  aplicado. Toda escritura en el *gauge* lleva el suyo y se aplica solo si es mayor o igual:

```python
def apply(session_id, seq, ratio_or_none):
    with lock_for(session_id):               # candado en proceso por sesión
        if seq < last_seq.get(session_id, -1):
            return                           # llegó tarde: se descarta
        last_seq[session_id] = seq
        if ratio_or_none is None:
            gauge.remove(str(session_id))    # sin ronda open o sin 8 decididas
        else:
            gauge.labels(str(session_id)).set(ratio_or_none)
```

  - El recálculo tras `decide` lee en una transacción `REPEATABLE READ READ ONLY` el `change_cursor` y la
    ventana con una sola sentencia. Si ya no hay ronda `open`, devuelve `None`, así que un recálculo tardío
    no recrea la serie que `lock_round` retiró.
  - `lock_round` y `discard_correction_round` retiran con su `change_seq` en `after_commit`.
  - Las entradas de `last_seq` de sesiones sin serie se borran en la reconciliación (`observability-design.md`
    §2).
  - Si el cálculo falla, la respuesta sigue en `201`, hay un `WARNING` `metrics.update_failed` y la serie
    conserva su valor.
  - **Prueba.** Dos decisiones simultáneas de la misma sesión, 50 repeticiones: el valor final es igual al de
    `dismissal_window` sobre la base. Una decisión cuyo recálculo se frena hasta después de `lock_round`: la
    serie no vuelve.
- **Reconstrucción al arrancar.** La API reconstruye las series de las sesiones con ronda `open` con una
  consulta de ≤ 2 s; si falla, arranca igual y `/readyz` no depende de ello (C15 es SHOULD).

## 4. Salud (NFR10.18)

- `/readyz` de la API responde `503` si PostgreSQL no responde (y si Redis no responde, por U3).
- Configuración de U5 validada antes de escuchar: `VERIDICUS_LIMIT_REVIEW_TEXT_MAX_CHARS`,
  `VERIDICUS_LIMIT_REVIEW_BODY_MAX_BYTES` y `VERIDICUS_LIMIT_DISMISSAL_WINDOW_W` por `limits.load` y los
  pisos de U5; `VERIDICUS_DB_LOCK_TIMEOUT_MS` entre 100 y el `statement_timeout` (NFRD-U5-03). Si falta, es
  inválida o intenta subir una cifra de C25, el proceso termina con código distinto de 0.
- La reconstrucción y la reconciliación de métricas no entran en `/readyz`.
- Pruebas: nivel 0 para cada variable inválida; nivel 1 para la base caída.

## 5. Recuperación y degradación

| Falla | Qué se pierde | Recuperación |
|---|---|---|
| Reinicio de la API en medio de una decisión | Nada (sin *commit*) | El analista ve el estado vigente y repite |
| Reinicio de la API | Valores en memoria de la razón | Reconstrucción al arrancar; el contador vuelve a 0 (`rate()` lo tolera) |
| PostgreSQL no responde | Nada guardado | `503`; la consola conserva lo escrito |
| Falla el `Job` de retención a mitad de `purge_session` | Nada: la transacción del `Job` se revierte entera | El humano relanza el `Job`; purgar de nuevo es seguro (E32) |
| Pérdida de la base | Hasta el último volcado manual | `pg_restore` manual del *runbook* de U2 (NFRD-U2-13) |
| Juez, anonimizador o Prometheus caídos | Nada de U5 | Se revisa, decide, consolida y corrige igual (BR3.10, E27) |
| Redis caído | Nada de U5 | Con 1 réplica, `/readyz` de U3 saca el pod del Service y la consola queda sin servicio hasta que Redis vuelve; U5 no tiene camino propio (NFRD-U5-08) |

## 6. Objetivo de punta a punta (NFR8.7)

`frontend/e2e/review.spec.ts` recorre: desplegar las observaciones, aceptar con nota, editar, descartar con
nota, cambiar una decisión, consolidar, abrir una corrección, descartarla, ver una sesión ajena en solo
lectura y, en otra pestaña, ver llegar la decisión y el descarte de la copia por el sondeo. Pasa con 0 fallos
en cada corrida de nivel 3 antes de etiquetar una entrega:
`npx --prefix frontend playwright test e2e/review.spec.ts`.

## 7. Precisiones a artefactos ya aprobados · Retirado

La tabla de la revisión 1 queda superada. Sus filas ya están en `entities.md` (`change_seq`), D3
(orden), C11 v2 (`open_round(for_update=True)`) y NFRD-U4-05 (primitiva compartida), o pasan a NFRD-U5-06
(índices) y NFRD-U5-11 (eventos). Las precisiones de esta revisión están en `security-design.md` §11.
