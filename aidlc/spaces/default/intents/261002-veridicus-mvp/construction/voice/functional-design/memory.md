<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T00:21:01Z — La consola codifica a WAV mono de 16 kHz porque el navegador graba en su formato nativo y el contrato solo admite WAV o MP3.
- 2026-11-22T04:05:24Z — Segunda pasada: «confirmar la transcripción» de AC10.2.4 se lee como la ingesta del TranscriptResult (P3 = A, sin paso de corrección); R-01, R-03 y R-04 ya los cerraron NFR Requirements y NFR Design de U9, y R-02 sigue abierto en el modelo del cambio 01 (pregunta 5).
- 2026-11-22T04:05:24Z — El estado del turno de voz ya no se guarda en el turno: se deriva de su corrida (U4) más `voice_status` de C1, así que la corrida se crea al ingerir el texto y no en el `202`.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T00:21:01Z — Ninguna desviación del texto de la etapa; los huecos de contrato (X1–X5) quedan en una tabla del spec.
- 2026-11-22T12:04:48Z — BR5.7 (escuchar solo con la sesión abierta o en pausa) no la pidió ninguna respuesta: la propuse por VE-09 y VE-10 y quedó en FD-U9-14 para que el humano decida.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T00:21:01Z — Sin audio guardado para reintentar (P2 = A): se pierde el reintento sobre el mismo turno a cambio de no conservar nunca audio crudo.
- 2026-11-22T12:04:48Z — Espera en orden (P5 = B) con RunPublicationHold: las corridas ven lo mismo que si el relato se hubiera escrito en orden, a costa de que el turno siguiente espere la transcripción y de una precisión al flujo de texto (FD-U9-07).
- 2026-11-22T12:04:48Z — Tras la retirada, el audio en cola se descarta con una clave por sesión que audio-worker solo lee; una llamada a Whisper que ya salió no se deshace y su texto se descarta en la ingesta.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T00:21:01Z — El tamaño máximo en bytes (propuesto 6 MB) lo confirma NFR Requirements.
- 2026-11-22T12:04:48Z — P4 = A conserva el audio autorizado aunque luego se retire el consentimiento; solo el Job de retención lo borra. Falta decidir si la retirada debe adelantar ese borrado.
