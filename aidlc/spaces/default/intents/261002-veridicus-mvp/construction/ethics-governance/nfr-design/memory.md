<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-23T00:29:34Z — El orden de controles de NFR10.1 se leyó como el de GuardedRoute de U3: da el mismo resultado (0 filas y cuerpo sin leer) con una sola entrada para todas las unidades (NFRD-U13-01).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-23T00:29:34Z — PostgreSQL exige UPDATE para SELECT FOR UPDATE y veridicus_retention no lo tiene: el Job bloquea con funciones SECURITY DEFINER que solo bloquean, pedidas a U4 y U7 (NFRD-U13-05, NFRD-U13-07).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-23T00:29:34Z — Las claves de cancelación se escriben antes del borrado y dentro de la transacción de la sesión: una sesión revertida queda con sus corridas canceladas sin daño, a cambio de que ninguna llamada salga tras el COMMIT.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-23T00:29:34Z — El acta de la sesión máxima ronda 0,8 MiB frente al tope de 1 MiB (NFR3.9); se confirma con la medición en B13.
