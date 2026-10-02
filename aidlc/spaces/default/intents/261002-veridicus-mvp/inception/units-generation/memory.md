<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T21:37:15Z — «La primera unidad del plan es el flujo de texto» (team-practices) se respetó como rebanada vertical U4 text-flow; como depende de contracts e identity-access, se dejó a Delivery Planning agruparlas en el primer Bolt en vez de meter el inicio de sesión dentro de text-flow.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T21:37:15Z — US10.6 (propuesta de umbral AIR) quedó en platform, pero leyendo una métrica cuyo nombre fija contracts, para que platform no dependa de human-review y no aparezca un ciclo.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T21:37:15Z — La indexación de escenarios corre en session-api y no en semantic-agent: así el evaluador conserva su usuario de base de datos de solo lectura (AC3.3.2) aunque los embeddings se calculen en dos procesos.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
