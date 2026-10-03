<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — Las líneas del entrevistador se guardan como turnos de contexto (role interviewer) que no se evalúan pero sí cuentan como turnos previos del paquete (P2 = A).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:52:08Z — Un rule source citaba un ID de regla de U4 y el chequeo de trazabilidad lo tomó como regla huérfana; se reemplazó por una descripción para no mezclar IDs entre unidades.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — La división de la transcripción se repite en la consola (vista previa) y en el servidor (autoridad) con la misma especificación y los mismos ejemplos, en vez de pedir la vista previa al servidor: respuesta inmediata a cambio de mantener dos implementaciones probadas igual.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:52:08Z — T del latido, intervalo de revisión y sondeo lento quedan para NFR Requirements.
