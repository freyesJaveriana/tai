<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T16:00:30Z — P3 = A aplicado: el exceso de tamaño en C21 responde 413 limits.exceeded con 0 peticiones y 422 queda para cuerpo inválido, perfil o papel inexistente y destino local (NFRD-U10-17); el cliente de U11 traduce 413 a AnonymizerUnavailable.
- 2026-10-03T03:31:30Z — La numeración estable de P1 = A se deriva de la lista que trae cada llamada (posición por categoría, detectados por reglas desde N + 1); así no rompe la ausencia de estado de NFR8.3 y escala sin afinidad.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T03:31:30Z — Con el adaptador anonimizador, 502 y 504 del proxy quedan fuera del reintento acotado de U4 (P1 = A de U4); reintentar reenviaría datos al destino externo. Solo 503 anonymizer.busy y la conexión rechazada son recuperables; registrado en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T16:00:30Z — Sin disyuntor ni reintentos: con una réplica y una corrida a la vez solo añadiría estado; a cambio, la reentrega de la cola de U4 puede reenviar el mismo cuerpo seudonimizado hasta 3 veces, declarado en el ADR (NFRD-U10-14).
- 2026-11-22T16:00:30Z — El NER corre en un hilo no abandonable con limitador de 1, y la espera cuenta en el presupuesto: nunca hay hilos huérfanos con la tabla viva, a cambio de que una cancelación espere al hilo (NFRD-U10-07).
- 2026-10-03T03:31:30Z — La lista de nombres se compila por llamada en vez de cachearla; cuesta parte del presupuesto de 250 ms, a cambio de no retener nombres propios en memoria entre llamadas.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-22T15:46:13Z — Segunda pasada: NFR10.8 y BR6.1 de U10 responden 422 ante un cuerpo de C21 demasiado grande, y el NFR Design de U1 (§4.3) exige 413 limits.exceeded en toda operación con x-veridicus-max-bytes, que C21 declara; se preguntó como P3 y no se generaron artefactos.
- 2026-11-22T15:46:13Z — La salida estructurada de Anthropic no admite minimum, maxLength, if/then ni oneOf, que usa C6; se resolverá sin preguntar con una proyección del esquema por proveedor y validación local completa (precisa NFR10.14).
- 2026-11-22T15:46:13Z — El escrito de la revisión 2 de security-design.md se revirtió a la revisión 1, byte a byte, al detectar la contradicción, para no dejar artefactos antes de la respuesta.
