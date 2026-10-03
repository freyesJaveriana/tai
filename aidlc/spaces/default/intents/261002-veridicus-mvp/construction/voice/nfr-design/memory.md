<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T03:56:35Z — P1 = A se aplicó a la API y al trabajador de session-api con raíz de solo lectura y /tmp en memoria, no solo a la ruta de voz; la lectura en streaming evita el disco y el montaje en memoria es la red de seguridad si otra ruta usara UploadFile.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T03:56:35Z — P2 = A acota en el tiempo el riesgo T5 que NFR10.4 aprobado solo acotaba por bytes (AofRewriteRequester con BGREWRITEAOF y prueba de 0 apariciones en ≤ 120 s); quedó en la tabla de precisiones de security-design junto con no renombrar BGREWRITEAOF en Redis de U2.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T03:56:35Z — Sin reintento ante Whisper caído, a diferencia del juez de U4: el turno falla en segundos y el audio se borra, a cambio de que el analista grabe de nuevo; reintentar obligaría a conservar audio crudo más tiempo.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
