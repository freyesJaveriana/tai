<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T00:09:14Z — Finalizar desde `suspended` se permite (U6 lo dejó a U7): una sesión suspendida y abandonada se podría cerrar sin reanudarla.
- 2026-10-03T00:09:14Z — AC6.2.2 se cubre con un code nuevo `report.not_consolidated`, porque la descarga va por versión y no existe versión antes de consolidar.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T00:09:14Z — Ninguna desviación del texto de la etapa; los huecos de contrato (X1–X6) quedan en una tabla del spec en vez de editar U5 o C11.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T00:09:14Z — Archivo antes que fila (P2 = A): nunca hay versión sin archivo, a cambio de un barrido de huérfanos al arrancar.
- 2026-10-03T00:09:14Z — La sugerencia editada muestra IA y analista (P3 = A): más largo, pero separa lo que dijo la máquina de lo que decidió la persona.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T00:09:14Z — Los cambios X1–X6 a U5, C1 y C11 necesitan la decisión del humano en la aprobación antes de Code Generation.
