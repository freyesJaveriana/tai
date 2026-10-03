# Preguntas de Functional Design — U9 voice

**Unidad.** U9 `voice` (tipo `service`, SHOULD): grabar un turno por voz y transcribirlo con Whisper en
CPU dentro del clúster (US10.2), y escuchar la pregunta aprobada (US10.4). El turno transcrito sigue el
mismo camino que un turno de texto (U4).

**Lo que ya está decidido y no se vuelve a preguntar.** La grabación es *push-to-talk* en WAV o MP3 y va
por `POST /sessions/{id}/voice-turns` asíncrono. La respuesta es `202` con el turno numerado en la etapa
`transcribing`, y la consola acepta otro envío antes de que termine (FR10.2, AC10.2.2, C1). El audio viaja
en base64 por el *stream* `veridicus:audio`. El `audio-worker` llama a Whisper con `language: es` por
ModelGateway y publica el texto en `veridicus:transcripts`. Con el texto, InterviewSession publica el
mismo turno en la cola de evaluación (C5, C13, C14). El audio crudo nunca sale del clúster y se borra del
*stream* tras confirmarlo (SpeechProcessing, AUTONOMIA-04). Si el navegador niega el micrófono, aparece
«No hay acceso al micrófono. Puedes seguir escribiendo el turno» (AC10.2.3). La voz de la pregunta se
sintetiza en CPU solo al pulsar «Escuchar audio» y solo para una pregunta aprobada (AC10.4.1, C1). Quedan
tres huecos.

---

## P1 — Duración máxima de una grabación

El audio viaja dentro del mensaje de Redis, y el contrato deja abierto su tamaño máximo (C5, pregunta
abierta de U9). Un turno muy largo hace pesado el mensaje y lento a Whisper en CPU. Sin un límite, una
grabación olvidada encendida podría bloquear al trabajador.

A. Máximo 120 segundos por turno. La consola muestra el tiempo que queda y detiene la grabación sola a los
   120 s con el aviso «Se alcanzó el máximo de 2 minutos; envía este turno y graba el siguiente». La API
   rechaza un audio más largo o más pesado que el límite con `422 validation.invalid_request` sin crear
   el turno. El límite en bytes y su valor por configuración los fija NFR Requirements. (Recomendada)
B. Máximo 60 segundos, con el mismo comportamiento.
C. Sin límite en la consola; solo la API rechaza por tamaño.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué pasa si la transcripción falla

Whisper puede fallar por *timeout* o error del sistema, o devolver un texto vacío (silencio, ruido). Hoy
«Reintentar» reprocesa el mismo turno, pero el audio se borra del *stream* tras confirmarlo, así que no
habría nada que volver a transcribir.

A. El turno pasa a «Error» con su `code` (`turn.error.timeout`, `turn.error.system`, o
   `turn.error.invalid_output` si el texto sale vacío) y el audio se borra igual. Un turno de voz con
   error en la transcripción no ofrece «Reintentar», sino «Grabar de nuevo» o escribir el turno, que
   crean un turno nuevo. El turno fallido queda en el reporte como «turno no evaluado». Nunca se guarda
   audio para reintentar. (Recomendada)
B. El audio se conserva cifrado en el *stream* hasta que el turno se transcribe bien o la sesión se
   finaliza, para permitir «Reintentar» sobre el mismo turno; después se borra.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — ¿El analista ve o corrige la transcripción antes de evaluarla?

Whisper puede transcribir mal un nombre o una fecha, y el juez evaluaría ese texto. Pero corregirlo
también es cambiar el testimonio, y el criterio pide que el turno de voz siga el mismo camino que el de
texto (AC10.2.1).

A. No hay paso de corrección. El texto transcrito se evalúa tal cual y se muestra rotulado «Turno por voz
   (transcripción automática)». Si la transcripción está mal, el analista escribe un turno nuevo con la
   aclaración, y los dos quedan en el reporte. (Recomendada)
B. Antes de evaluar, el analista ve la transcripción y puede corregirla y confirmarla. El turno espera en
   un estado nuevo «por confirmar», y el reporte guarda el texto de Whisper y el corregido.
X. Other (please specify)

[Answer]: A **Mode:** guided
