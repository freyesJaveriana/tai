<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-11-22T16:28:13Z — Segunda pasada sin preguntas: la coherencia con U10 (3 envíos como máximo) se logra con XCLAIM JUSTID, que no suma entregas, y con el tope de entregas leído tras XAUTOCLAIM (NFRD-U4-01).
- 2026-11-22T16:28:13Z — «El trabajador no reintenta por su cuenta» (BR15.6) se leyó como no repetir llamadas a modelos; republicar en Redis es idempotente y se permite (NFRD-U4-03).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T03:14:53Z — P1 = A cambia NFR10.16 aprobado (ahora hay hasta 2 reintentos en el proceso ante fallos pasajeros del juez) y P2 = A añade change_seq a entidades aprobadas; quedaron en la tabla de precisiones de reliability-design sin editar los originales.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-11-22T16:28:13Z — Ruta mínima del incidente en la ingesta: una transacción más a cambio de que un bloqueo nunca se pierda cuando el resultado no se puede ingerir entero (NFRD-U4-04).
- 2026-10-03T03:14:53Z — Calentar el juez al arrancar retrasa el readyz de semantic-agent unos segundos, a cambio de que el primer turno real no pague las instrucciones sin caché.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
