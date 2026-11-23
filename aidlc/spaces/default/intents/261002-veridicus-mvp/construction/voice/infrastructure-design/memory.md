<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:50:55Z — P1 = A se aplicó como campo `format` en `models.lock` con lista cerrada por servidor (gguf, ctranslate2 solo Whisper, onnx solo la voz); los pesos de Systran son float16 y el int8 se hace al cargar, sin archivo aparte.
- 2026-11-23T01:45:49Z — Segunda pasada sin preguntas: U9 no cambia ninguna cifra de pod del presupuesto de U2; P3 = A se lee como voice.enabled en true en values-cpu.yaml de la única máquina.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:50:55Z — Se añadió un Ingress `veridicus-voice` sin buffering de petición ni de respuesta, no pedido por NFR Design: ingress-nginx escribe en disco los cuerpos de más de 16 KiB y eso contradecía NFR10.2.
- 2026-11-23T01:45:49Z — El /tmp en memoria de model-tts baja de 64 a 16 MiB: con 64 MiB, 1,2 × (512 + 64) superaba su límite de 640 MiB de U2 (IDS-U9-06).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:50:55Z — Con la voz encendida en desarrollo (P3 = A) los limits suman ≈ 21,9 GiB frente a 20 GiB; se aceptó porque los requests (≈ 16,1 GiB) caben y solo el juez y Whisper pueden coincidir en su pico (≈ 8 GiB). Redis sube a 768 MiB por el fork de BGREWRITEAOF.
- 2026-11-23T01:45:49Z — No se pide subir Redis a 768 MiB: el AofRewriteRequester reescribe con la cola vacía, y una prueba de nivel 1 exige un pico de RSS ≤ 427 MiB; solo si falla se pide a U2 por PR (IDS-U9-05).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
