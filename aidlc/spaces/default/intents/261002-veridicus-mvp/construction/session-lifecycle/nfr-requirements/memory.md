<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:20:05Z — P2 = A dice que los turnos del entrevistador no cuentan para los 60; para acotar la transacción se fijó además un total de 200 turnos con el mismo transcript.too_large, y quedó en la tabla de precisiones para el humano.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:20:05Z — InterviewerLabels y los límites del pegado no son variables de entorno sino un archivo versionado compartido por consola y servidor, para que la vista previa nunca discrepe de la división del servidor; registrado como precisión de entities.md.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:20:05Z — Latido escrito como máximo cada 15 s con la hora de la base: ≤ 4 escrituras por minuto y sesión en vez de 30, a costa de que la suspensión pueda llegar desde 165 s tras el último sondeo real en vez de 180 s.
- 2026-10-03T02:20:05Z — Republicar en el reenvío idempotente en vez de una tabla outbox: sin piezas nuevas, a costa de depender de que el navegador reenvíe tras un 503 (si no, el plazo de U4 cierra los turnos en error).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:20:05Z — El pegado de 60 turnos llega al tope de 3 600 s sin margen si el juez va al p95 de 60 s; la corrida NFR3.11 dirá si hay que bajar el límite.
