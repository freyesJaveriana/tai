<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T03:56:35Z — P1 = A se aplicó a la API y al trabajador de session-api con raíz de solo lectura y /tmp en memoria, no solo a la ruta de voz; la lectura en streaming evita el disco y el montaje en memoria es la red de seguridad si otra ruta usara UploadFile.
- 2026-11-23T00:07:07Z — Revisión 2: BR3.6 («clave justo antes de publicar») se leyó como NFR10.14 (publicar y luego MULTI con XACK, XDEL y la clave), porque al revés un corte perdería el resultado; quedó como NFRD-U9-04.
- 2026-11-23T00:07:07Z — Revisión 2: las transiciones de pausa, terminación y retirada entran por la función de cancelación de InterviewSession con un motivo (NFRD-U9-08) para no crear una arista voice → session-lifecycle.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T03:56:35Z — P2 = A acota en el tiempo el riesgo T5 que NFR10.4 aprobado solo acotaba por bytes (AofRewriteRequester con BGREWRITEAOF y prueba de 0 apariciones en ≤ 120 s); quedó en la tabla de precisiones de security-design junto con no renombrar BGREWRITEAOF en Redis de U2.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T03:56:35Z — Sin reintento ante Whisper caído, a diferencia del juez de U4: el turno falla en segundos y el audio se borra, a cambio de que el analista grabe de nuevo; reintentar obligaría a conservar audio crudo más tiempo.
- 2026-11-23T00:07:07Z — Recorte por XTRIM MINID desde el supervisor de session-api (cierra R-02) en vez de guardar el message_id en la fila: sin columna nueva y sin depender del consumidor, a cambio de que la cota en memoria sea de 1 920 s y no de segundos.
- 2026-11-23T00:07:07Z — Guardias evaluadas antes de leer el cuerpo y repetidas bajo el bloqueo (NFRD-U9-14): no hay bloqueo de la sesión durante la lectura de 6 MB y la retirada siempre gana, a cambio de llamar dos veces a la misma función pura.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
