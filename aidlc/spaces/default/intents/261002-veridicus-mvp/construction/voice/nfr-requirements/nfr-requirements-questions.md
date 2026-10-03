# Preguntas de NFR Requirements — U9 voice

**Unidad.** U9 `voice` (SHOULD): grabación por demanda, transcripción con Whisper ligero en CPU y audio
de la pregunta aprobada (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Máximo 120 s por grabación en WAV mono de
16 kHz (P1), audio borrado del *stream* tras confirmarlo, servidor de Whisper de U2 (`faster-whisper`
compatible con OpenAI), 8–12 s por turno de voz aceptados en CPU (NFR3 de requirements), y el camino del
turno de texto de U4 tras transcribir. Quedan para esta etapa el tamaño máximo del audio (pregunta
abierta de C5) y el modelo de Whisper.

---

## P1 — Tamaño máximo del audio y cómo viaja

120 s en WAV mono de 16 kHz ocupan unos 3,8 MB (unos 5,1 MB en base64 dentro del mensaje de Redis).
Functional Design propuso 6 MB y conservar el audio dentro del mensaje.

A. `VERIDICUS_VOICE_MAX_BYTES` = 6 MB y el audio viaja en base64 dentro del mensaje de C5, borrado con
   `XDEL` al confirmarlo; más grande → rechazo antes de encolar. (Recomendada)
B. 6 MB, pero el audio va a un volumen temporal y el mensaje lleva solo una referencia, con borrado
   tras transcribir.
C. 4 MB (unos 100 s), dentro del mensaje.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Modelo de Whisper

El PRD pide Whisper ligero (`tiny` o `base`) en CPU y acepta 8–12 s por turno de voz. Un modelo más
grande transcribe mejor el español pero tarda más.

A. `base` cuantizado int8 con `faster-whisper`, idioma fijo `es`: p95 ≤ 12 s por turno de hasta 30 s
   de audio y ≤ 40 s para una grabación de 120 s. (Recomendada)
B. `tiny` int8: unas dos veces más rápido, con más errores de transcripción en nombres y fechas.
C. `small` int8: mejor transcripción, fuera de «ligero» y con riesgo para los 8–12 s.
X. Other (please specify)

[Answer]: A **Mode:** guided
