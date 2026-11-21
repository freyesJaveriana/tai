<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — Los embeddings externos también se enmascaran (BR1.4); como los pasajes del escenario pasan por el mismo enmascarado, la comparación por similitud conserva sentido.
- 2026-11-21T22:41:38Z — Segunda pasada (Modify) por el cambio 01, la adenda 02 y las revisiones 3. U10 pasa de adaptador COULD a módulo MUST (C20) más `anonymizer-proxy` (C21) con los adaptadores nativos y sus claves (C22, CD-04). Siguen P1 = A y las reglas en español de P2 = A. Salen la lista de nombres del escenario, `embed` (BR1.4), `turn.error.system` y BR3.2–BR3.4, que pasan a U11 y U2. Entran NER local, restauración con detección de marcas alteradas, lista de dominios (US11.5), resolución del perfil en el proxy, transporte *fake* y subpaquete de adaptadores. Las preguntas P3–P8 solo cubren lo que C13/C20–C22, FR11.3 y las historias no fijan: categorías y red de seguridad, identidad de la marca, coherencia entre llamadas (FR11.3 «por entrevista» frente a C20 «por llamada»), alcance de las marcas alteradas, registro de las llamadas fallidas con `InvalidOutput` en el proxy, y salida JSON por proveedor (pregunta abierta de C22).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:52:08Z — Ninguna desviación del texto de la etapa.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — Marcadores consistentes por llamada con restauración dentro del clúster (P1 = A): el juez externo puede razonar sobre quién y dónde, a costa de mantener una tabla en memoria que nunca debe registrarse.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:52:08Z — Si un nombre propio sin patrón escapa del enmascarado, el riesgo residual queda para la decisión de usar o no un modelo externo.
