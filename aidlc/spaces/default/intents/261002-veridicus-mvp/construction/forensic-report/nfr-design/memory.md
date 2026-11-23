<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T03:57:26Z — El cursor del diálogo se compara como decode(expected_cursor) = valor del bump − 1, después de BR2.2–BR2.4 y BR2.7; como el latido de U6 y cot-views no incrementan change_seq, solo un cambio visible deja la vista desactualizada y no hay falsos rechazos.
- 2026-11-23T00:12:37Z — La contradicción 5 s (U6) / 15 s (U7) del plazo de inactividad era de alcance, no de valor: U4 y U6 lo fijan con SET LOCAL en sus transacciones y NFR10.17 fija 15 s para U7; se aplicó SET LOCAL en consolidar y exportar, sin valor por conexión, y no se preguntó (NFRD-U7-01).

## Deviations
- 2026-11-23T00:12:37Z — C1 revisión 3 no llevó el cuerpo expected_cursor de P1 = A; como ninguna fuente aprobada retiró la respuesta del humano, se mantuvo y se volvió a pedir a U1 (NFRD-U7-04) en vez de abandonarla.
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T03:57:26Z — Con P2 = A el barrido del arranque deja de ser el camino normal de limpieza y pasa a ser respaldo de report.cleanup_failed; se registró como precisión a D5/D6, NFR10.16 y NFR10.17, sin editar los originales.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T03:57:26Z — La consolidación retiene la fila de la sesión y la ronda desde el bump hasta el commit (≤ 2 s, con E/S local del volumen) para que el reporte sea exactamente el estado bloqueado; a cambio, una decisión simultánea de otra pestaña espera o recibe 503 a los 2 s.
- 2026-11-23T00:12:37Z — Ante un COMMIT fallido el archivo no se borra (resultado desconocido) y lo resuelve el barrido, que borra solo sin fila: nunca se pierde el archivo de una versión confirmada, a costa de un huérfano de hasta 6 minutos (DS4, cierra R-01).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
