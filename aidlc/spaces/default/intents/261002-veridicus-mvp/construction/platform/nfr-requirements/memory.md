<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T01:38:15Z — U2 es de tipo packaging y no tuvo Functional Design: los requisitos se derivan de unit-of-work, requirements, contract-summary y team.md; solo aplican seguridad, pila y trazabilidad.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T01:38:15Z — llama.cpp sirve juez y embeddings con una sola tecnología GGUF en CPU, a costa de que el esquema JSON se cumpla por gramática y no por un modo nativo; la validación contra C6 en U4 sigue siendo la que manda.
- 2026-10-03T01:38:15Z — NetworkPolicy de negar todo y abrir lo declarado (P4 = A): más reglas que mantener, pero ningún pod nuevo sale a internet por omisión.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T01:38:15Z — Confirmar en Infrastructure Design que el CNI elegido hace cumplir políticas de salida y que la imagen de CloudNativePG trae pgvector.
