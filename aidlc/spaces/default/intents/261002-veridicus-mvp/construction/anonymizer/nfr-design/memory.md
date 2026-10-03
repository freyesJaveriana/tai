<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T03:31:30Z — La numeración estable de P1 = A se deriva de la lista que trae cada llamada (posición por categoría, detectados por reglas desde N + 1); así no rompe la ausencia de estado de NFR8.3 y escala sin afinidad.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T03:31:30Z — Con el adaptador anonimizador, 502 y 504 del proxy quedan fuera del reintento acotado de U4 (P1 = A de U4); reintentar reenviaría datos al destino externo. Solo 503 anonymizer.busy y la conexión rechazada son recuperables; registrado en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T03:31:30Z — La lista de nombres se compila por llamada en vez de cachearla; cuesta parte del presupuesto de 250 ms, a cambio de no retener nombres propios en memoria entre llamadas.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
