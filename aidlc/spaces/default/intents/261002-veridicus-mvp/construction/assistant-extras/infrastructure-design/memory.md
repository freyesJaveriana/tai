<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:00:43Z — P1 = A se materializó como dos Application (veridicus-dev sin values-extras.yaml, veridicus-demo con values-gpu.yaml + values-extras.yaml) y una comprobación offline que impide incluirlo en desarrollo.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:00:43Z — La lista afectiva y el prompt de la pregunta pasan al directorio files/ del chart de semantic-agent (frente a D7 y D4) porque Helm no lee contracts/; quedó en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:00:43Z — La lista afectiva entra en el filtro de ai-eval-gate.yml aunque es determinista: más reportes de nivel 2, a cambio de medir la repetibilidad de lo que ve el analista.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
