<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:00:42Z — La réplica única de session-api se trató como requisito de U5 (D7 calcula la razón AIR en el proceso) y no solo como valor por defecto de U3; pasar a más réplicas exige antes cambiar D7.
- 2026-11-23T01:31:23Z — Segunda pasada sin preguntas: U5 no añade procesos, memoria fuera del límite de 1,125 GiB de U2, red ni Secrets; su código corre en la API, el trabajador (propose) y el Job de retención (purge_session), y solo pide a U2 VERIDICUS_DB_LOCK_TIMEOUT_MS en cada contenedor de session-api que abre conexiones (IDS-U5-02).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:00:42Z — NFR10.20 (de U4) apareció citado en reliability-design y se añadió a traceability.json como N/A justificado para que el sensor pasara.
- 2026-11-23T01:31:23Z — El sensor de trazabilidad tomó NFR3.13 de reliability-design §3, que cita la consolidación de U7; entró como N/A justificado.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:00:42Z — Se mantuvieron los 768 MiB de la API: la suma de picos con U5 (≈ 392 MiB) deja margen holgado, a cambio de que U6 y U7 vuelvan a sumar sobre esa tabla.
- 2026-10-03T11:00:42Z — Durante el RollingUpdate la serie AIR puede publicarse desde dos pods; se resolvió con max by (session_id) en la regla de U2 (precisión) en lugar de cambiar la estrategia a Recreate, que cortaría la API.
- 2026-11-23T01:31:23Z — Se mantuvo lock_timeout = statement_timeout = 2 000 ms (valor aprobado del que dependen U7 y U13) con una prueba del empate, en vez de bajar el lock_timeout a 1 500 ms como sugería R-03: las dos cancelaciones dan el mismo 503.
- 2026-11-23T01:31:23Z — Se retiró la precisión max by (session_id) de la revisión 1: la regla AIR es de U2 con > 0.25, y la alerta doble de ≤ 60 s durante el relevo de pods queda como riesgo aceptado porque nadie recibe notificaciones.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
