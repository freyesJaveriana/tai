<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T03:03:51Z — P1 = A (UPDATE de last_seen_at en cada petición) mantiene exactas las pruebas de 1 799 s y 1 801 s de NFR10.3; con ≤ 20 sesiones el costo es despreciable.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T03:03:51Z — Semáforo de Argon2id con espera de 5 s (P2 = A): picos de hasta 10 inicios terminan sin error, a cambio de un 503 con Retry-After si la cola dura más; un intento que no llegó a verificar no cuenta como fallo del limitador.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
