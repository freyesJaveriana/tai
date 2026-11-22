<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-11-22T23:43:59Z — NFR10.14 dejaba a esta etapa el plazo de las lecturas: se tomó el statement_timeout común de 2 s de U3 en vez de una cifra propia (NFRD-U12-07).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T23:43:59Z — La subida no corre en la transacción única de GuardedRoute sino en tres cortas (T1 autoriza y confirma, T2 duplicado, T3 escritura con relectura del rol), como el inicio de sesión de U3; con el Ingress sin buffering y una validación de hasta 12 s, la conexión quedaba inactiva dentro de la transacción frente a un plazo de 5 s o 15 s (NFRD-U12-01).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T23:43:59Z — Bulkhead de 2 subidas con espera de 5 s y 503 para la tercera, a cambio de proteger la memoria de la API que comparten todas las unidades de session-api (NFRD-U12-04).
- 2026-11-22T23:43:59Z — El pico estimado de memoria por subida (≈ 230 MiB) deja poco margen frente a los 256 MiB de NFR3.8; si la medición lo supera, se arman las filas de las llamadas por lotes antes de tocar el tope.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
