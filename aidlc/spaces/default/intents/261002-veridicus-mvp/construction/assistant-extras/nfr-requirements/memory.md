<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:19:30Z — P1 = A solo fija la humo con extras apagados; para un despliegue que active extras por PR se fijó N = 300 s (2 × p95 de 150 s), por analogía con 120 s ≈ 2 × 60 s de U4.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:19:30Z — El catálogo de C1 no tiene code para los 409 de la pregunta (ya decidida, no aprobada) ni C3 lleva source_passage_ids; se registraron question.already_decided, question.not_approved y los campos de C3 en la tabla de precisiones sin editar contract-summary.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:19:30Z — Con extras activos el plazo base sube a 600 s y el reclamo a 480 s para cubrir hasta 3 llamadas en serie al juez, a costa de que la cola solo admita 24 turnos sin vencer; por eso tres sesiones concurrentes con extras quedan fuera del MVP.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:19:30Z — Falta decidir si una pregunta aún proposed puede decidirse tras finalizar la sesión; Functional Design no lo fija y aquí no se inventó un code para ello.
