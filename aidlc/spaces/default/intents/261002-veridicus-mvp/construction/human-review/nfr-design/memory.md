<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T03:34:42Z — P1 = A se implementó con una primitiva compartida `session_api/shared/change_cursor.bump` que la UnitOfWork memoriza por sesión; así U4, U5 y U7 toman la sesión antes que la ronda sin crear dependencias entre módulos.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T03:34:42Z — El diseño cambia D3 aprobado (sesión antes que ronda), añade `change_seq` a `ReviewDecision` y `ReviewRound` y precisa C10, C11 y los diseños de U1, U3 y U4; todo quedó en la tabla de precisiones de reliability-design §7 sin editar los originales.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T03:34:42Z — Las decisiones y los turnos de una misma sesión comparten ahora un bloqueo; se acepta porque hay un solo analista por sesión y las transacciones bajo ese bloqueo no hacen E/S de red, a cambio de un sondeo sin huecos y sin interbloqueos.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
