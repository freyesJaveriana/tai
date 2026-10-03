<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — Una afirmación cuyas dos lecturas no coinciden queda «no documentada» y va al paquete (P2 = A), así el analista ve la discrepancia en vez de perderla.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:52:08Z — El chequeo de trazabilidad pidió cubrir US5.5 y US5.6 porque el mapa de historias las cruza con U8; se añadieron BR4.1–BR4.4.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — El indicio afectivo usa una lista versionada sin LLM (P3 = A): determinista y auditable, a costa de no captar emociones expresadas sin palabras clave.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:52:08Z — El efecto de la segunda lectura sobre la latencia y NFR8 lo mide NFR Requirements.
