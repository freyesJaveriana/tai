<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — La herencia de decisiones entre rondas que ADR-007 dejó a esta etapa se fijó como «estado vigente»: la última decisión de la ronda o, si no hay, el estado vigente en la ronda bloqueada de la que parte la corrección.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:52:08Z — Para cerrar el hallazgo R-02 de la revisión de U4, propose rechaza con review.round_locked cuando todas las rondas están bloqueadas, y se dejó en la tabla de precisiones que U4 limite el reintento en sesiones consolidadas.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — El evento «CoT consultada» vale por usuario y alerta en todas las rondas (P1 = A): menos fricción en la corrección, a costa de no exigir una relectura en cada ronda.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:52:08Z — La ventana W de la razón AIR (C15) queda para NFR Requirements.
