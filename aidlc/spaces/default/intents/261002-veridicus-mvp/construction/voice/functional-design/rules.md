# Reglas de negocio — U9 voice

**Alcance.** Grabación en la consola (BR1), recepción en `session-api` (BR2), transcripción en
`audio-worker` (BR3), ingesta del resultado (BR4), voz de la pregunta (BR5), frontera del clúster y
registros (BR6) y accesibilidad (BR7). La autorización por dueño la aplica ConsoleApi (ADR-009). Todo lo
de U9 es SHOULD y solo se construye cuando el flujo de texto funciona (team-practices).

```yaml
rules:
  # BR1 — Grabación en la consola (US10.2)
  - id: BR1.1
    statement: Si el navegador niega el micrófono, se avisa y la entrada de texto sigue disponible.
    category: validation
    applies_to: Consola — botón «Grabar»
    trigger: Pulsar «Grabar» sin permiso de micrófono
    logic: SI el navegador niega el acceso ENTONCES aparece «No hay acceso al micrófono. Puedes seguir escribiendo el turno» y el campo de texto sigue habilitado.
    violation: La prueba Vitest falla.
    source: FR10.2, AC10.2.3
  - id: BR1.2
    statement: Mientras graba hay un indicador visible y anunciado a los lectores de pantalla.
    category: validation
    applies_to: Consola — estado recording
    trigger: Empezar a grabar
    logic: SI la grabación empieza ENTONCES se ve «Grabando…» con el tiempo transcurrido y un icono, y una región aria-live anuncia «Grabación iniciada» y «Grabación detenida».
    violation: La prueba Vitest falla.
    source: AC10.2.3, AC5.6.3
  - id: BR1.3
    statement: Una grabación dura como máximo 120 segundos.
    category: constraint
    applies_to: VoiceRecording.duration_seconds
    trigger: Grabación en curso
    logic: SI la grabación llega a 120 s ENTONCES se detiene sola y aparece «Se alcanzó el máximo de 2 minutos; envía este turno y graba el siguiente»; los últimos 15 s muestran el tiempo restante.
    violation: La prueba Vitest con reloj simulado falla.
    source: P1 = A, C5 (pregunta abierta de tamaño)
  - id: BR1.4
    statement: La consola envía WAV PCM 16 bits, mono, 16 kHz.
    category: calculation
    applies_to: VoiceRecording.audio_format
    trigger: Pulsar «Enviar»
    logic: SI se envía una grabación ENTONCES se codifica a WAV mono de 16 kHz, el formato que admite el contrato y consume Whisper, sin depender del formato nativo del navegador.
    violation: La prueba Vitest comprueba la cabecera del WAV generado.
    source: FR10.2, C1
  - id: BR1.5
    statement: Enviar un turno de voz no bloquea la consola.
    category: policy
    applies_to: Consola — envío de voz
    trigger: Respuesta 202 del envío
    logic: SI la API responde 202 ENTONCES el turno aparece con «Procesando audio…» y se puede grabar, escribir o enviar otro turno antes de que termine.
    violation: La prueba de nivel 1 con transcriptor fake de 12 s y la de Vitest fallan.
    source: AC10.2.2
  - id: BR1.6
    statement: Un turno de voz se rotula como transcripción automática y no se corrige.
    category: policy
    applies_to: Turn con origin voice
    trigger: Mostrar el turno
    logic: SI el turno es de voz ENTONCES se muestra «Turno por voz (transcripción automática)» y no hay acción para editar su texto; para aclarar, el analista escribe un turno nuevo.
    violation: La prueba Vitest falla.
    source: P3 = A, AC10.2.1

  # BR2 — Recepción en session-api
  - id: BR2.1
    statement: Solo el dueño envía turnos de voz.
    category: authorization
    applies_to: POST /sessions/{session_id}/voice-turns
    trigger: Petición de turno de voz
    logic: SI el actor no es el dueño, es admin o es una identidad de servicio ENTONCES 403 auth.forbidden y 0 filas.
    violation: 403 Problem Details.
    source: C1 (x-veridicus-owner-only), ADR-009
  - id: BR2.2
    statement: Un turno de voz solo entra en una sesión abierta.
    category: constraint
    applies_to: POST /sessions/{session_id}/voice-turns
    trigger: Petición de turno de voz
    logic: SI la sesión está finalized o consolidated ENTONCES 409 session.finalized; SI está suspended ENTONCES 409 session.not_open; en ambos casos 0 filas y no se publica audio.
    violation: 409 Problem Details.
    source: FR10.2 (mismo camino que FR3.2), reglas de U4
  - id: BR2.3
    statement: El audio se valida antes de crear el turno.
    category: validation
    applies_to: VoiceSubmission
    trigger: Petición de turno de voz
    logic: SI el formato declarado no es wav ni mp3, si la cabecera no corresponde al formato, si pesa más que VERIDICUS_VOICE_MAX_BYTES o si dura más de 120 s ENTONCES 422 validation.invalid_request con el motivo en detail, 0 filas y no se publica audio.
    violation: 422 Problem Details.
    source: P1 = A, C1, C5
  - id: BR2.4
    statement: Reenviar la misma grabación no crea un segundo turno.
    category: constraint
    applies_to: VoiceSubmission.client_request_id
    trigger: Dos peticiones con el mismo client_request_id en la misma sesión
    logic: SI el client_request_id ya existe en la sesión ENTONCES se responde 202 con el mismo turno y no se publica otro mensaje de audio.
    violation: La prueba de nivel 1 envía dos veces y cuenta un turno.
    source: C1 (client_request_id), AC10.2.2
  - id: BR2.5
    statement: Un turno de voz aceptado se numera y queda en la etapa de transcripción.
    category: policy
    applies_to: Turn con origin voice
    trigger: Petición válida
    logic: SI pasa BR2.1 a BR2.4 ENTONCES se crea el turno con el siguiente número, origin voice, status queued y processing_stage transcribing, se publica AudioToTranscribe con attempt 1 y deadline_at, y se responde 202.
    violation: La prueba de nivel 1 falla.
    source: FR10.2, AC10.2.1, C1, C5

  # BR3 — Transcripción en audio-worker
  - id: BR3.1
    statement: El audio se transcribe con Whisper dentro del clúster, en español y con timeout.
    category: policy
    applies_to: audio-worker
    trigger: Mensaje AudioToTranscribe
    logic: SI llega un mensaje antes de deadline_at ENTONCES se llama a ModelGateway.transcribe con language es y un timeout explícito contra el servidor Whisper interno, en CPU.
    violation: La prueba de nivel 1 con transcriptor fake verifica la llamada y su timeout.
    source: FR10.2, AC10.2.1, C13, C14
  - id: BR3.2
    statement: Una transcripción con texto se publica con el digest del modelo.
    category: policy
    applies_to: TranscriptResult
    trigger: Respuesta de Whisper con texto
    logic: SI el texto, sin espacios en los extremos, no está vacío ENTONCES se publica outcome transcribed con el texto y model_digest.
    violation: La prueba de nivel 1 falla.
    source: AC10.2.1, C5
  - id: BR3.3
    statement: Una transcripción vacía es un error de salida, no un turno vacío.
    category: validation
    applies_to: TranscriptResult
    trigger: Respuesta de Whisper vacía o solo con espacios
    logic: SI el texto está vacío ENTONCES se publica outcome error con turn.error.invalid_output (ampliación de C5, X1).
    violation: La prueba de nivel 1 con fake que devuelve vacío falla.
    source: P2 = A
  - id: BR3.4
    statement: Un fallo o un plazo vencido de la transcripción se publica como error con su code.
    category: policy
    applies_to: TranscriptResult
    trigger: Timeout, error de Whisper o mensaje recibido después de deadline_at
    logic: SI Whisper supera su timeout o el mensaje llega tarde ENTONCES outcome error con turn.error.timeout; SI Whisper responde con error o no está disponible ENTONCES outcome error con turn.error.system; no se reintenta la llamada.
    violation: Las pruebas de nivel 1 de timeout y de error fallan.
    source: P2 = A, C5
  - id: BR3.5
    statement: El audio se borra del stream al confirmarlo, con cualquier resultado, y nunca se guarda.
    category: policy
    applies_to: AudioToTranscribe
    trigger: Publicar el TranscriptResult
    logic: SI se publicó el resultado ENTONCES se confirma (XACK) y se borra (XDEL) el mensaje de audio; el trabajador no escribe el audio en disco, en un volumen ni en un log.
    violation: La prueba de nivel 1 comprueba que el stream queda sin el mensaje tras cada resultado.
    source: SpeechProcessing, C5, AUTONOMIA-04, P2 = A
  - id: BR3.6
    statement: Un mensaje de audio repetido no produce dos transcripciones.
    category: constraint
    applies_to: audio-worker
    trigger: Entrega repetida del mismo mensaje
    logic: SI ya se publicó un resultado para ese turn_id y attempt ENTONCES el mensaje se confirma y se borra sin volver a llamar a Whisper.
    violation: La prueba de nivel 1 de entrega doble cuenta una llamada al fake.
    source: C5 (entrega al menos una vez)

  # BR4 — Ingesta del resultado en session-api
  - id: BR4.1
    statement: Un turno transcrito sigue el mismo camino que un turno de texto.
    category: policy
    applies_to: Turn con origin voice
    trigger: TranscriptResult con outcome transcribed
    logic: SI llega el texto ENTONCES se guarda en el turno, processing_stage pasa a retrieving y el turno se publica en la cola de evaluación (C2) igual que un turno escrito.
    violation: La prueba de nivel 1 compara el resultado de un turno de voz con el del mismo texto escrito.
    source: FR10.2, AC10.2.1
  - id: BR4.2
    statement: Un error de transcripción deja el turno en «Error» y se resuelve grabando de nuevo.
    category: policy
    applies_to: Turn con origin voice
    trigger: TranscriptResult con outcome error
    logic: SI la transcripción falló ENTONCES el turno pasa a error con su code; la consola ofrece «Grabar de nuevo» y «Escribir el turno», que crean un turno nuevo; la ruta de reintento sobre ese turno responde 409 turn.audio_unavailable (code propuesto, X2).
    violation: La prueba de nivel 1 y la de Vitest fallan.
    source: P2 = A
  - id: BR4.3
    statement: Un resultado que llega tarde o repetido no cambia el turno.
    category: constraint
    applies_to: Ingesta de TranscriptResult
    trigger: Resultado para un turno que ya está en error por plazo o que ya tiene texto
    logic: SI el turno ya está en error por plazo o ya tiene su texto para ese intento ENTONCES el resultado se descarta y se confirma.
    violation: La prueba de nivel 1 de resultado tardío falla.
    source: reglas de plazo de U4, C5
  - id: BR4.4
    statement: El texto transcrito no se edita.
    category: constraint
    applies_to: Turn.text con origin voice
    trigger: Cualquier intento de cambiar el texto
    logic: SI se intenta cambiar el texto de un turno ENTONCES no existe ruta para hacerlo; las aclaraciones van en un turno nuevo y ambos quedan en el reporte.
    violation: La prueba de contrato confirma que no hay ruta de edición.
    source: P3 = A

  # BR5 — Voz de la pregunta aprobada (US10.4)
  - id: BR5.1
    statement: Solo se sintetiza una pregunta aprobada.
    category: constraint
    applies_to: GET /questions/{question_id}/audio
    trigger: Pulsar «Escuchar audio»
    logic: SI la pregunta no está approved ENTONCES 409 y 0 llamadas al TTS.
    violation: 409 Problem Details.
    source: FR10.4, AC10.4.1, C1
  - id: BR5.2
    statement: El TTS solo se llama cuando el analista pulsa «Escuchar audio».
    category: policy
    applies_to: SpeechProcessing.synthesize
    trigger: Ciclo de vida de una pregunta
    logic: SI nadie pulsa «Escuchar audio» ENTONCES el TTS registra 0 llamadas, aunque la pregunta se apruebe o se muestre.
    violation: La prueba de nivel 0 con TTS fake cuenta 0 llamadas.
    source: AC10.4.1, FR10.4
  - id: BR5.3
    statement: La voz se sintetiza dentro del clúster en cada pulsación y no se guarda.
    category: policy
    applies_to: QuestionAudio
    trigger: Pulsar «Escuchar audio» sobre una pregunta aprobada
    logic: SI se pide el audio ENTONCES se llama a ModelGateway.synthesize en CPU con timeout, se devuelve audio/wav y no se guarda; SI el TTS falla o vence su timeout ENTONCES 503 con code speech.unavailable (code propuesto, X3) y la consola dice «No se pudo generar el audio; puedes leer la pregunta en pantalla».
    violation: La prueba de nivel 0 con TTS fake falla.
    source: AC10.4.1, C13
  - id: BR5.4
    statement: Solo el dueño de la sesión escucha la pregunta.
    category: authorization
    applies_to: GET /questions/{question_id}/audio
    trigger: Petición de audio
    logic: SI el actor no es el dueño de la sesión de la pregunta ENTONCES 403 auth.forbidden y 0 llamadas al TTS.
    violation: 403 Problem Details.
    source: AC10.4.1 (la escucha es para leerla al compareciente), propuesta X4

  # BR6 — Frontera del clúster y registros (US9.1)
  - id: BR6.1
    statement: El audio-worker es un pod con datos sin anonimizar y no tiene salida a internet.
    category: constraint
    applies_to: Despliegue de audio-worker
    trigger: Política de manifiestos de nivel 0
    logic: SI el pod audio-worker no lleva la etiqueta de clasificación de datos sin anonimizar o no está cubierto por la NetworkPolicy de salida denegada ENTONCES la política falla; su salida permitida es solo Redis y los servidores Whisper y TTS internos.
    violation: La política de nivel 0 falla; la verificación manual con curl -m 5 a un host público termina con código distinto de 0.
    source: AC9.1.1, AC9.1.2, AUTONOMIA-04
  - id: BR6.2
    statement: El audio-worker no arranca con una URL de modelo externa al clúster.
    category: validation
    applies_to: Configuración de audio-worker
    trigger: Arranque
    logic: SI VERIDICUS_WHISPER_URL o la URL del TTS no es interna del clúster ENTONCES el pod no arranca.
    violation: La prueba de nivel 0 de configuración falla.
    source: AC9.1.4, C13
  - id: BR6.3
    statement: Ni el audio ni el texto transcrito aparecen en los registros.
    category: policy
    applies_to: Logs de session-api y audio-worker
    trigger: Cualquier registro del flujo de voz
    logic: SI se registra un evento ENTONCES lleva solo session_id, turn_id, message_id, attempt, code y duración; un canary sembrado en el audio fake no aparece en ningún log capturado.
    violation: La prueba de nivel 1 del canary falla.
    source: AC9.1.5, team-practices (Code Style)
  - id: BR6.4
    statement: El modelo Whisper y el TTS se fijan por sha256 y se descargan en el aprovisionamiento.
    category: policy
    applies_to: Artefactos de modelo de U9
    trigger: Construcción de la imagen o aprovisionamiento
    logic: SI se usa un modelo ENTONCES su revisión está fijada y verificada con sha256, en un formato sin código ejecutable, y nunca se descarga en ejecución.
    violation: La comprobación de nivel 0 del manifiesto de modelos falla.
    source: team-practices (Deployment), C14

  # BR7 — Accesibilidad
  - id: BR7.1
    statement: Los controles de voz cumplen la accesibilidad común.
    category: validation
    applies_to: Botones «Grabar», «Detener», «Enviar», «Grabar de nuevo» y «Escuchar audio»
    trigger: Suite axe y recorrido con teclado
    logic: SI axe encuentra violaciones serious o critical, si grabar, detener, enviar o escuchar no se puede hacer solo con teclado, o si el estado de grabación o de error se identifica solo por color ENTONCES la prueba falla.
    violation: La prueba de nivel 3 o la de Vitest falla.
    source: AC5.6.1, AC5.6.2, AC5.6.3
```

## Resumen de reglas

| Grupo | Reglas | Qué protegen |
|---|---|---|
| BR1 Grabación | BR1.1–BR1.6 | Micrófono negado sin bloquear el texto, indicador anunciado, máximo 120 s, WAV mono de 16 kHz, consola no bloqueada, rótulo de transcripción automática |
| BR2 Recepción | BR2.1–BR2.5 | Dueño, sesión abierta, audio válido, sin duplicados, turno numerado en `transcribing` |
| BR3 Transcripción | BR3.1–BR3.6 | Whisper interno en español con timeout, vacío como error, errores con code, audio borrado siempre, sin dobles transcripciones |
| BR4 Ingesta | BR4.1–BR4.4 | Mismo camino que el texto, error que se resuelve grabando de nuevo, resultados tardíos descartados, texto sin edición |
| BR5 Pregunta | BR5.1–BR5.4 | Solo aprobada, solo al pulsar, sin guardar, solo el dueño |
| BR6 Frontera | BR6.1–BR6.4 | Salida denegada, URLs internas, registros sin audio ni texto, modelos fijados |
| BR7 Accesibilidad | BR7.1 | axe, teclado y estados sin depender del color |
