<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:19:28Z — Se interpretó que el patrón de expediente cubre toda secuencia de 6 o más dígitos (cédulas y radicados de U1) por «enmascarar ante la duda»; quedó como precisión a BR1.2.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:19:28Z — El proxy recibe la lista de nombres del cliente en vez de cargarla de la base (F1 paso 2): el único pod con salida no tiene credencial de base de datos; registrado en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:19:28Z — 502/504 del proxy son finales y no vuelven por XAUTOCLAIM (precisión a NFR10.16 de U4), a costa de reintentos manuales, para que nada se reenvíe fuera del clúster.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:19:28Z — Confirmar en Infrastructure Design si el CNI admite políticas por FQDN y cómo limitar la resolución DNS externa (T15) antes de cualquier PR que habilite el proxy.
