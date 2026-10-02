<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T20:41:42Z — Las colas de petición y respuesta (turno → resultado, audio → texto) se modelan como una sola arista del solicitante hacia el evaluador o el transcriptor; la respuesta viaja como parte de la misma interacción, así el grafo de componentes queda sin ciclos.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T20:41:42Z — Se añadieron cuatro ADR que no salieron de las preguntas (ADR-006 a ADR-009) porque las historias ya fijaban la decisión (AC2.1.2, AC3.3.2, AC6.3.4, FR1.2) y solo faltaba registrar su consecuencia en los componentes.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T20:41:42Z — La propiedad de la sesión se verifica en ConsoleApi y no en HumanReview para evitar un ciclo InterviewSession ↔ HumanReview; el costo es que toda entrada futura debe repetir la verificación (ADR-009).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
