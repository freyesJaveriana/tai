<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T22:05:00Z — Las fronteras en proceso dentro de session-api (C10–C12) se trataron como contratos aunque no crucen la red, porque unen módulos de unidades distintas (U4, U5, U7) y la respuesta P4 pidió interfaces tipadas.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T22:05:00Z — Los hallazgos R-02 y R-03 de Units Generation se resolvieron en el contrato (ronda 1 abierta por propose; métricas AIR emitidas por U5) y se anotaron en una tabla para el humano, sin editar unit-of-work.md ya aprobado.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T22:05:00Z — El audio viaja en base64 dentro del Redis Stream (C5) para no compartir un volumen entre pods; queda como pregunta abierta cambiar a una referencia a volumen si el tamaño máximo lo hace inviable.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
