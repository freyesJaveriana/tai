<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:19:28Z — Se interpretó que el patrón de expediente cubre toda secuencia de 6 o más dígitos (cédulas y radicados de U1) por «enmascarar ante la duda»; quedó como precisión a BR1.2.
- 2026-11-22T13:37:41Z — Segunda pasada: el cambio 01 supera la parte de P1 = A que dejaba el proxy apagado y con un solo destino (FR11.3 MUST, FR14.1 y C13); se conserva el ADR del proveedor como condición para que un modelo entre a ProviderCapabilityTable, sin preguntar.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:19:28Z — El proxy recibe la lista de nombres del cliente en vez de cargarla de la base (F1 paso 2): el único pod con salida no tiene credencial de base de datos; registrado en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:19:28Z — 502/504 del proxy son finales y no vuelven por XAUTOCLAIM (precisión a NFR10.16 de U4), a costa de reintentos manuales, para que nada se reenvíe fuera del clúster.
- 2026-11-22T13:37:41Z — Las cifras de C25 de U10 (2 MiB y 0,15) se atan con comprobaciones de nivel 0 a transcript_max_chars y model_call_timeout_s de otras unidades, en vez de esperar a que U11 fije su plazo.
- 2026-11-22T13:51:20Z — La prueba de 0 fugas corre en nivel 1 con el NER real montado sin red, y el nivel 0 usa un NER diminuto de prueba: el nivel 0 no carga modelos, a costa de que la fuga por el NER solo se detecte en nivel 1 (también bloqueante).
- 2026-11-22T13:51:20Z — Los adaptadores usan httpx directo y no los SDK de los proveedores: los SDK reintentan, fijan su URL base y añaden cabeceras propias, y eso contradice NFR1.8 y NFR10.4.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:19:28Z — Confirmar en Infrastructure Design si el CNI admite políticas por FQDN y cómo limitar la resolución DNS externa (T15) antes de cualquier PR que habilite el proxy.
- 2026-11-22T13:37:41Z — Se preguntó solo el proveedor comercial de la primera rebanada (P2): ninguna fuente aprobada lo fija y decide qué tercero recibe primero el testimonio seudonimizado, incluido el piloto; no se generaron artefactos.
- 2026-11-22T13:51:20Z — P2 = A (Anthropic primero) obliga a que el generador del conjunto sintético sea de Google u OpenAI y distinto del verificador (NFR5.2, NFR-U10-07); lo decide U11 al fijar sus perfiles de evaluación.