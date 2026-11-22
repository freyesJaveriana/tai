<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T03:18:59Z — Leo U12 como validación y guarda de cifras de C19 más lista, detalle y comparación en M8. AC12.6.1 se cierra con FD-U1-05: el canary da 422 y 0 apariciones en filas y logs, y por eso el detail nunca repite valores ni nombres de campos desconocidos. Solo pregunto tres cosas de criterio: el canary de una palabra en un campo con patrón (residuo de R-06), qué se guarda de runs[] y de dónde sale el «Origen». C19 v2 (FD-U11-09) sigue pendiente de aprobación, así que se acepta la versión vigente que publique U1.

- 2026-11-22T03:38:44Z — AC12.6.1 se cerró con CD-03 sin excepción: el canary da 422 en un hallazgo, como nombre de campo y en los campos con patrón (P1 = A); solo el nombre del archivo no rechaza, porque no se guarda ni se registra (FD-U12-01).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T03:46:40Z — El version comercial que informa el proveedor (U10) no lo declara el perfil, así que P1 = A literal rechazaría todo reporte comercial; se admite «modelo» más segmentos que empiezan por dígito (BR3.3, FD-U12-11).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T03:46:40Z — El costo de M8 va solo en la fila Total (FD-U12-09): recalcularlo por papel duplicaría la fórmula de U11 en session-api, a cambio de perder el desglose que dibujaba §10.2.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T03:46:40Z — Con P1 = A, un reporte hecho antes de cambiar un perfil o la tabla de precios por PR ya no se puede subir (E18, E19); queda para decidir en la aprobación si basta con subir antes del cambio o hace falta guardar versiones anteriores en C18.
