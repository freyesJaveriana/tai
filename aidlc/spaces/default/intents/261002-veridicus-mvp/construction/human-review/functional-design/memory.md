<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — La herencia de decisiones entre rondas que ADR-007 dejó a esta etapa se fijó como «estado vigente»: la última decisión de la ronda o, si no hay, el estado vigente en la ronda bloqueada de la que parte la corrección.
- 2026-11-22T03:19:41Z — Segunda pasada (Modify) de U5 por el cambio 01, la adenda 02 y las revisiones 3: cambio menor. Siguen la máquina de estados, las rondas, la autorización y P1 = A (ahora sobre ObservationsView). Sale lo de la alerta (CoT, fragmento, cita del documento, CotView, review.cot_not_viewed, propuesta de umbral AIR) y las columnas de ronda que referenciaban ReviewReport (R-01 de Domain Design). Entran los campos protegidos de C7 v2, la retención (C24), el registro de acceso de las observaciones (FD-U3-05), change_seq y el orden usuario → sesión → ronda, y el cierre de R-01..R-05 de la revisión 1. U4 ya crea ReviewSuggestion, ReviewRound y propose; U5 no los reescribe. Solo se preguntan P2 (reformulación en una corrección) y P3 (decidir tras terminar o retirar el consentimiento).

- 2026-11-22T03:44:09Z — Volver a `pending` responde 422 por el enum del cuerpo de C1, no el 409 que dice AC5.1.4; el 409 `review.invalid_transition` queda para la decisión repetida sin cambios y se propone la precisión FD-U5-09.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T03:44:09Z — Se añadió el estado `discarded` de la ronda y `discard_correction_round` (BR3.9, FD-U5-04), que la lista acordada no nombraba: AC6.3.2 lo necesita, U7 ya lo había propuesto (X1) y C11 v2 no lo trae.
- 2026-10-02T23:52:08Z — Para cerrar el hallazgo R-02 de la revisión de U4, propose rechaza con review.round_locked cuando todas las rondas están bloqueadas, y se dejó en la tabla de precisiones que U4 limite el reintento en sesiones consolidadas.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — El evento «CoT consultada» vale por usuario y alerta en todas las rondas (P1 = A): menos fricción en la corrección, a costa de no exigir una relectura en cada ronda.

- 2026-11-22T03:44:09Z — `open_round(for_update=True)` abre la ronda 1 si la sesión no tiene ninguna (BR3.7): U7 siempre bloquea una ronda, a costa de que una lectura con bloqueo pueda crear una fila.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T03:44:09Z — NFR Requirements (segunda pasada) fija las cifras de `review_text_max_chars` y `review_body_max_bytes` en C25 y pasa el código de longitud a `limits.exceeded`.
- 2026-10-02T23:52:08Z — La ventana W de la razón AIR (C15) queda para NFR Requirements.
