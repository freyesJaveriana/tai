<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T12:10:44Z — Primera pasada de U13. Pregunté solo siete puntos de criterio en los que las fuentes callan o se contradicen. Son «Salir» del diálogo frente a «ninguna demostración bloquea» (B13), el plazo por defecto y las sesiones sin plazo de FD-U4-22, desde cuándo cuenta el plazo, quién reduce el plazo, la fecha de corte del Job en el clúster, el reporte sin sesión (UG-01 frente a C1) y cómo se consulta lo registrado. Lo que fijan la adenda, C1, C23, C24 y los FD de U3–U9 va en la tabla de decididos.
- 2026-11-22T12:10:44Z — C1 exige `note` en `/problem-reports`, pero AC15.3.1 la quiere opcional. No hice una pregunta: lo dejé para resolver siguiendo la historia, como precisión a C1. También faltan en C25 las cifras de retención, de vigencia del reconocimiento y del intervalo de bienestar, que entran como precisión.

- 2026-11-22T12:58:10Z — El plazo vive en InterviewSessionRecord (U4), así que U13 no lo escribe directamente. Lo cambia por un puerto nuevo, EthicsSessionPort, que implementa U4, y guarda el quién y el cuándo en su propio historial, RetentionChange. No hay aristas nuevas, porque EthicsGovernance → InterviewSession ya existía (FD-U13-08).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T12:58:10Z — C1 no tenía ruta para reducir el plazo ni campo de retención en POST /sessions. Propuse PATCH /sessions/{id}/retention y retention_days opcional como precisiones (FD-U13-04, FD-U13-05), sin editar C1.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T12:58:10Z — El Job borra cada sesión en su propia transacción y sigue con las demás si una falla. A cambio, un archivo ya borrado antes de la reversión queda como file_missing en el siguiente intento, en vez de detener todo el borrado.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T12:58:10Z — Falta definir cómo monta el Job los volúmenes de reportes y de audio (PVC ReadWriteOnce compartido con session-api) y su activeDeadlineSeconds. Quedan para Infrastructure Design (§11, pregunta 4).
