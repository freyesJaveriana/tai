<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T16:05:32Z — NFR15.1 pide la latencia en cada entrada de registro.llamadas, pero C6 es el contrato común del TG y no cambia (ADR-017): se mide en memoria y solo sus agregados van a C19 v2 (NFRD-U11-07); no se preguntó porque no hay otra salida que respete C6.
- 2026-11-22T16:05:32Z — El margen de 10 s del cliente de C21 (NFRD-U10-10) se descuenta del plazo de la corrida, para que ninguna corrida pase de run_deadline_* (NFRD-U11-04).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T16:05:32Z — El p95 ≤ 180 s con 4 llamadas al verificador en CPU depende de la caché del prefijo fijo y del orden hecho, tipo, cita_a, cita_b; es una estimación que decide el nivel 2, y si no alcanza se cambia el perfil por PR, nunca la meta.
- 2026-11-22T16:05:32Z — El piso de 270 s de model_call_timeout_s con perfil comercial vive como constante de libs/execution_profiles y no en C25, porque C25 guarda techos (DS9, NFRD-U11-03).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
