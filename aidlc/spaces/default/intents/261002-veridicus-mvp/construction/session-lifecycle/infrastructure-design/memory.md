<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:00:11Z — U6 no añade procesos ni reglas de red; lo propio son tres ajustes en el bloque común de los values, un cuarto hilo del trabajador y una migración aditiva.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:00:11Z — veridicus_now() del clúster devuelve solo now(); la variante con hora inyectada la instala el fixture de nivel 1, para que ningún rol pueda adelantar la suspensión (precisión a D3).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:00:11Z — Tras minikube stop o la API caída > 180 s las sesiones abiertas se suspenden en la primera revisión; se acepta porque reanudar es un clic sin pérdida, en vez de complicar la revisión.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
