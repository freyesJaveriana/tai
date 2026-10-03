<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T02:56:01Z — Los valores que la revisión de NFR Requirements echó en falta (R-02) ya los fijaron U3, U4, U6 y U9; no se volvieron a preguntar y entraron al catálogo de límites y a la cookie de C1.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T02:56:01Z — El diseño cambia el criterio aprobado de NFR10.6 (de 50 ms a análisis estático) y amplía NFR10.12 a toda operación de C1; no se editó security-requirements.md y quedó en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T02:56:01Z — Catálogo único de límites (P1 = A): contrato y servicio no pueden divergir, a costa de que U9 pierda el margen de VERIDICUS_VOICE_MAX_BYTES hasta 8 000 000 bytes, porque el entorno solo puede bajar el límite.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
