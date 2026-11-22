<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T03:03:51Z — P1 = A (UPDATE de last_seen_at en cada petición) mantiene exactas las pruebas de 1 799 s y 1 801 s de NFR10.3; con ≤ 20 sesiones el costo es despreciable.

- 2026-11-22T15:41:51Z — Segunda pasada sin preguntas: NFR10.3 revisión 2 (escritura cada 60 s) supera P1 = A, y el /notice de BR4.3 lo resuelve C1 con FD-U4-08 y NFRD-U1-12 (NFRD-U3-09).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-11-22T15:41:51Z — La actividad se escribe tras el bloqueo compartido del usuario y no al resolver la sesión (F2 paso 2): al revés cerraría un ciclo con la desactivación, que bloquea usuario y luego WebSession (NFRD-U3-01).
- 2026-11-22T15:41:51Z — El token anti-CSRF se deriva del token de sesión con HMAC-SHA256: entities.md solo guarda su hash y /auth/me debe devolverlo; la revisión 1 lo guardaba en claro contra NFR10.7 (NFRD-U3-03).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T03:03:51Z — Semáforo de Argon2id con espera de 5 s (P2 = A): picos de hasta 10 inicios terminan sin error, a cambio de un 503 con Retry-After si la cola dura más; un intento que no llegó a verificar no cuenta como fallo del limitador.

- 2026-11-22T15:41:51Z — /readyz sigue dependiendo de Redis (NFR10.13): con una réplica, Redis caído deja sin servicio toda la consola; se documenta en vez de ocultarlo (cierra R-01).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
