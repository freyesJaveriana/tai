<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:38:33Z — La síntesis de la pregunta va de session-api a una ruta interna de audio-worker y de ahí al TTS, para respetar que SpeechProcessing vive en audio-worker y que solo audio-worker habla con los servidores de voz (U2); queda como precisión de contrato y de red.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:38:33Z — U2 no tiene subchart model-tts ni las reglas de red session-api → audio-worker y audio-worker → model-tts, y Redis no desactiva RDB; se registraron en la tabla de precisiones sin editar U2.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:38:33Z — Un solo Redis con AOF en vez de un Redis sin persistencia para el audio: menos piezas, a costa de que el audio quede en el AOF del PVC hasta la reescritura (declarado y probado en NFR10.4).
- 2026-10-03T02:38:33Z — Un Whisper caído deja el turno de voz en error en segundos en vez de devolver el mensaje a la cola como el juez de U4: respeta BR3.4 y da respuesta inmediata, a costa de perder el audio y grabar de nuevo.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:38:33Z — Una transcripción de más de 2 000 caracteres (habla rápida de 120 s) se trata como turn.error.invalid_output; confirmar en la aprobación si se prefiere admitir turnos de voz más largos.
