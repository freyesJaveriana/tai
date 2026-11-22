<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T01:27:54Z — U1 es de tipo spec: solo produce security-requirements, tech-stack-decisions y traceability; los NFR de rendimiento, escalado, fiabilidad y observabilidad en ejecución no aplican porque la unidad no corre. El tiempo de la suite (P6) se registró bajo NFR2 (CPU primero).
- 2026-10-03T01:27:54Z — Los servicios consumen contracts/ como dependencia de ruta de uv; se leyó la regla «solo libs/ se comparte» como referida a código de comportamiento, y contract-summary (regla 1) ya aprobó que los servicios importen contracts/.

- 2026-11-22T13:16:31Z — Segunda pasada: las cifras nuevas de C25 que piden U5, U10, U12 y U13 solo se nombran aquí; sus valores los fijan esas unidades en su NFR, y U1 valida la forma del catálogo y que cada maxLength coincida con su cifra.

- 2026-11-22T13:16:31Z — Revisión 2 generada con P7 = A y P8 = A: el catálogo de errores declara un estado por code (limits.exceeded = 413) y U1 suma contracts/ts/; la sección clarifications de U8 (FD-U8-09) entra en C19 v2 como cambio mayor, porque C19 es estricto (BR1.4).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T01:27:54Z — C1 aprobado tiene cuatro respuestas 409 descritas sin Problem Details, lo que la suite (BR7.2) rechazaría; no se editó contract-summary: se registró en la tabla de precisiones con el code de cada una y la falta de un code para la pregunta no aprobada.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T01:27:54Z — Meta-esquemas oficiales de OpenAPI 3.1 y AsyncAPI 3.0 copiados y fijados por SHA-256 (P2 = A) en vez de la CLI de AsyncAPI en Node: una sola pila y sin red, a costa de actualizar a mano la copia cuando cambie la especificación.
- 2026-10-03T01:27:54Z — Datos sintéticos con marca, catálogo cerrado de nombres y patrones de cédula y radicado (P4 = A): no detecta un nombre real que el autor no declare; ese riesgo residual queda en la revisión del PR.
- 2026-10-03T01:27:54Z — ruamel.yaml en modo seguro con claves duplicadas prohibidas, en vez de PyYAML: YAML 1.2 evita que valores como «no» se lean como booleanos y una clave repetida no sobrescribe en silencio la lista de C8.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T13:16:31Z — P7: limits.exceeded responde 413 en U4, U6 y U12 y 422 en U5 y U13; con una clase por code (BR7.4) no caben dos estados, así que se pregunta y no se generan artefactos.
- 2026-11-22T13:16:31Z — P8: la revisión 1 dejó la suite sin Node, pero la regla 1 de contract-summary y BR1.9, BR9.7 y BR12.3 piden ajv strict y JCS en TypeScript en nivel 0; dónde corre esa mitad cambia el alcance de B1.
