<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T00:21:01Z — La consola codifica a WAV mono de 16 kHz porque el navegador graba en su formato nativo y el contrato solo admite WAV o MP3.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T00:21:01Z — Ninguna desviación del texto de la etapa; los huecos de contrato (X1–X5) quedan en una tabla del spec.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T00:21:01Z — Sin audio guardado para reintentar (P2 = A): se pierde el reintento sobre el mismo turno a cambio de no conservar nunca audio crudo.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T00:21:01Z — El tamaño máximo en bytes (propuesto 6 MB) lo confirma NFR Requirements.
