<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:37:07Z — Los turnos de la transcripción se tratan como cita literal (literal_testimony_quote de C8) en el escaneo del reporte, para que un compareciente que dice «falso» no bloquee la consolidación sin salida (hallazgo R-01 del Functional Design); quedó en la tabla de precisiones.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:37:07Z — La atomicidad depende de open_round(for_update=True), que no está en C11 ni en el Functional Design aprobado de U7; se registró como precisión junto con report.storage_failed, el margen de 300 s del barrido y la réplica única con Recreate.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:37:07Z — El archivo se escribe dentro de la transacción con la ronda bloqueada (P2 = A): nunca hay versión sin archivo, a costa de que una decisión simultánea espere hasta 2 s; se acota con p95 ≤ 1,5 s de la consolidación.
- 2026-10-03T02:37:07Z — Una sola réplica de la API por el PVC ReadWriteOnce y el barrido al arrancar: cierra la carrera del barrido sin bloqueos distribuidos, a costa de no poder escalar la API sin cambiar el almacenamiento.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:37:07Z — El RPO/RTO de los reportes depende del respaldo conjunto de CloudNativePG y del PVC, que fija Infrastructure Design; NFR10.20 solo verifica la restauración.
