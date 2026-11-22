<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T14:42:40Z — Sin preguntas: las cifras de C25, el volumen de la lista y las latencias salen de las fuentes; el costo de P1 = A (E18, E19) lo dejó el Functional Design para la aprobación, no para esta entrevista.
- 2026-11-22T14:42:40Z — Los topes se dimensionaron con un reporte sintético estimado de 240 corridas × 30 llamadas (~3,3 MB): 8 MiB y profundidad 8, frente a una profundidad natural de 5 en C19 v2.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T14:42:40Z — BR5.1 dice «ni en disco», pero `request.form()` de Starlette escribe en un archivo temporal por encima de 1 MiB y el Ingress guarda en disco los cuerpos de más de 16 KiB: se fijó un análisis del multipart en memoria (D2) y se pasó el Ingress a Infrastructure Design (NFR-U12-05).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
