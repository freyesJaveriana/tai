<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T03:36:12Z — La marca del lote de P1 = A se vigila con WATCH además de MULTI/EXEC; sin WATCH, dos reenvíos simultáneos podían ver la marca ausente y publicar ambos el lote.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T03:36:12Z — El conteo de pendientes de la lista pasa a una vista de solo lectura de U5 (human_review.session_pending_suggestions) en vez del LEFT JOIN a sus tablas de D9; quedó en la tabla de precisiones de reliability-design; los límites nuevos del catálogo de U1 están en la de security-design.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T03:36:12Z — El latido se omite si la fila de la sesión está bloqueada (SKIP LOCKED) y no incrementa change_seq; el sondeo nunca espera un pegado, a cambio de que una escritura en curso retrase el latido hasta el siguiente sondeo.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
