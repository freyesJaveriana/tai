<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T13:58:51Z — U11 es `library`: por el archivo de etapa le tocan security, tech-stack y traceability; se añadirán performance y reliability porque NFR3, NFR8 y los plazos de C25 recaen aquí.
- 2026-11-22T13:58:51Z — Las cinco cifras de C25 de la configuración efectiva (plazos por llamada y de corrida, ventana y solapamiento) se leen como de U11, porque C18 dice que U11 decide esos esquemas y B11 es su primer consumidor; el catálogo guarda el máximo (ZINE) y cada despliegue lo baja por entorno.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T13:58:51Z — Tres preguntas legítimas: verificador de `comercial-piloto` y familia del generador (cambia qué proveedor recibe datos y el alcance de B10; gpt-oss cuenta como línea de OpenAI), umbrales estadísticos del nivel 2 (riesgo de la compuerta) y composición mínima del conjunto (alcance de B11, R8).
