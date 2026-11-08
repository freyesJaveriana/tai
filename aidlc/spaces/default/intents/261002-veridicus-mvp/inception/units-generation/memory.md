<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T21:37:15Z — «La primera unidad del plan es el flujo de texto» (team-practices) se respetó como rebanada vertical U4 text-flow; como depende de contracts e identity-access, se dejó a Delivery Planning agruparlas en el primer Bolt en vez de meter el inicio de sesión dentro de text-flow.
- 2026-11-07T19:50:03Z — «Analizador sin rebaja» se fijó como U11, U10 y el AnalysisWorker de U4, y las VE de DD-07 se cumplen en la unidad dueña de su componente (UG-04), para unificar las dos definiciones de R-04.
- 2026-11-07T19:50:03Z — US14.1 quedó N/A en la trazabilidad, sin unidad, porque se cumplió antes del diseño con `docs/validacion-zine/`.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T21:37:15Z — US10.6 (propuesta de umbral AIR) quedó en platform, pero leyendo una métrica cuyo nombre fija contracts, para que platform no dependa de human-review y no aparezca un ciclo.
- 2026-11-07T19:50:03Z — La primera versión de P13 recomendó renombrar U7 con la premisa falsa de que Construction no había creado nada bajo `forensic-report`; ya había cuatro diseños aprobados. Se corrigió, se volvió a preguntar y U7 conserva su directorio.
- 2026-11-07T19:50:03Z — U8 depende explícitamente de incoherence-analyzer aunque la arista es transitiva por text-flow, porque US10.3 y US10.5 tocan el código de la biblioteca; el plan aprobado solo listaba text-flow.
- 2026-11-08T14:23:17Z — La jerarquía de excepciones de `libs/` pasó a U1 (spec) como traducción declarativa del catálogo de `code`, porque en U4 cerraba un ciclo con U10 y U11 (R-02 de la revisión 2).
- 2026-11-08T14:23:17Z — AC15.8.2 (MUST en U7) se cumple por un puerto de ConsoleApi que implementa U13, para que ninguna unidad MUST dependa de la demostración (R-01 = A, UG-09).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T21:37:15Z — La indexación de escenarios corre en session-api y no en semantic-agent: así el evaluador conserva su usuario de base de datos de solo lectura (AC3.3.2) aunque los embeddings se calculen en dos procesos.
- 2026-11-07T19:50:03Z — incoherence-analyzer depende de anonymizer (ModelGateway pasa por Anonymizer) en vez de al revés: la CLI no arranca con destino externo sin el módulo, a costa de que el anonimizador se construya antes que la biblioteca.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
