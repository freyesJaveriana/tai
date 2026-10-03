<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:01:33Z — En una unidad de tipo spec, las «entidades» son los documentos de contrato y los datos que describen; U1 no tiene comportamiento en ejecución, así que functional-spec.md documenta los flujos de validación y de cambio de contrato (F1–F6) en lugar de casos de uso.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:01:33Z — Las decisiones P1 (delimitador «» de cita literal) y P3/P4 (catálogo de rótulos y formato de fecha nuevos) precisan contract-summary.md ya aprobado; se registraron en una tabla de functional-spec.md sin editar el original, para que el humano decida en la aprobación.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:01:33Z — La lista de vocabulario prohibido 1.0.0 se queda en 9 términos (P2 = A) aunque deja sin detectar flexiones como «mienten» o «falsedad»; la limitación quedó visible como escenario E14 y cada ampliación entra por su PR con control negativo.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:01:33Z — El sensor de trazabilidad marca que ninguna historia del mapa se asigna a la unidad contracts; es estructural (U1 respalda criterios de US2.2, US3.2, US5.5 y US8.3 sin historias propias) y no se editó el mapa aprobado.
