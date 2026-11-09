<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:01:33Z — En una unidad de tipo spec, las «entidades» son los documentos de contrato y los datos que describen; U1 no tiene comportamiento en ejecución, así que functional-spec.md documenta los flujos de validación y de cambio de contrato (F1–F6) en lugar de casos de uso.
- 2026-11-09T21:39:32Z — V-1 = A: el papel es texto con patrón en C13, C19 (registro) y C21; un perfil genérico (papeles, alias, un fallback) que el analizador especializa con exactamente judge y verifier; C6 no cambia y una tabla fija traduce los tres papeles del analizador.
- 2026-11-09T22:43:59Z — P9 = A: U1 publica tres funciones puras (profiles.validate, limits.load, registry) para que U10, U11 y sistema no reimplementen la validación; FD-U1-10 enmienda el «sin lógica» de unit-of-work.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:01:33Z — Las decisiones P1 (delimitador «» de cita literal) y P3/P4 (catálogo de rótulos y formato de fecha nuevos) precisan contract-summary.md ya aprobado; se registraron en una tabla de functional-spec.md sin editar el original, para que el humano decida en la aprobación.
- 2026-11-09T21:39:32Z — Las precisiones de la segunda pasada (papeles abiertos, perfil genérico, prefijo de api_key_ref, importaciones veridicus_contracts, rótulos de los 7 tipos, comparación por contenido de la copia de C6) se registraron como FD-U1-01..09 en functional-spec.md §9 sin editar contract-summary, components ni stories aprobados.
- 2026-11-09T22:43:59Z — Tras la revisión asesora, y con review-freeze bajado por el humano (opción B), U1 se corrigió después de la revisión: R-01 a R-09 resueltos y FD-U1-10..14 añadidas, sin editar contract-summary ni unit-of-work aprobados.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:01:33Z — La lista de vocabulario prohibido 1.0.0 se queda en 9 términos (P2 = A) aunque deja sin detectar flexiones como «mienten» o «falsedad»; la limitación quedó visible como escenario E14 y cada ampliación entra por su PR con control negativo.
- 2026-11-09T21:39:32Z — El prefijo VERIDICUS_ de api_key_ref pasa del esquema a un argumento de la función de validación: sistema reutiliza el mismo esquema con su prefijo, a costa de que el esquema solo ya no impida una clave de otro producto.
- 2026-11-09T22:43:59Z — P10 = A: los escenarios de vocabulario pasan a casos de escaneo que ejecuta U11 en B11; U1 queda sin lógica de escaneo a cambio de que esas pruebas no corran hasta B11.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:01:33Z — El sensor de trazabilidad marca que ninguna historia del mapa se asigna a la unidad contracts; es estructural (U1 respalda criterios de US2.2, US3.2, US5.5 y US8.3 sin historias propias) y no se editó el mapa aprobado.
- 2026-11-09T21:39:32Z — AC12.6.1 espera 201 con el texto descartado y CD-03 rechaza con 422; BR10.1 cubre ambos y la diferencia (FD-U1-05, misma que DP-01) se cierra en el Functional Design de U12.
- 2026-11-09T22:43:59Z — FD-U1-14: si un tramo «…» que es solo un término de la lista debe seguir excluido del escaneo (R-05), queda para que el humano decida en la aprobación.
