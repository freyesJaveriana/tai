# Reglas de negocio — U9 voice

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02.** Sustituye a la revisión 1 del
2026-10-03. Ningún ID se renumera y ninguna regla se retira.
- **Siguen sin cambios:** BR1.1, BR1.2, BR1.4–BR1.6, BR2.1, BR2.4, BR3.1, BR3.2, BR3.5, BR4.4, BR5.2,
  BR6.1–BR6.4 y BR7.1.
- **Siguen y se reescriben:** BR1.3 (catálogo de límites), BR2.2 (orden de las guardias), BR2.3 (límites y
  `413`), BR2.5 y BR4.1 (sin estado guardado en el turno; la corrida nace en la ingesta), BR3.3, BR3.4 y
  BR3.6 (codes de C5 y clave de entrega doble, R-05), BR4.2 y BR4.3 (sin la ruta de reintento) y
  BR5.1, BR5.3 y BR5.4 (la aclaración aprobada sustituye a la pregunta).
- **Nuevas:** BR5.5–BR5.7 (frase y validación de la voz, P7 = A), BR7.2–BR7.3 (accesibilidad), BR8.1–BR8.6
  (autorización de voz y audio conservado, P4 = A) y BR9.1–BR9.7 (orden de los turnos y ciclo de vida de
  la sesión, P5 = B y P6 = C).

**Fuentes.** `unit-of-work.md` y `unit-of-work-story-map.md` (U9, revisión 3), `requirements.md` y su
adenda 02, `components.md` y `contract-summary.md` (C1, C5, C8, C13, C14, C25).

**Alcance.** Grabación en la consola (BR1), recepción (BR2), transcripción (BR3), ingesta (BR4), voz de la
aclaración (BR5), frontera del clúster y registros (BR6), accesibilidad (BR7), consentimiento y audio
conservado (BR8) y orden y ciclo de vida (BR9). La autorización por dueño la aplica ConsoleApi (ADR-009).
Todo lo de U9 es SHOULD; VE-08 y VE-09 son MUST cuando U9 se construye.

## Reglas

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
    trigger: Empezar o detener la grabación
    logic: SI la grabación empieza ENTONCES se ve «● Grabando mm:ss» con un icono, y una región aria-live anuncia «Grabación iniciada» y «Grabación detenida»; ningún otro cambio de la grabación se anuncia.
    violation: La prueba Vitest falla.
    source: AC10.2.3, AC5.6.3, AC5.6.5, mockups §6.11
  - id: BR1.3
    statement: Una grabación dura como máximo audio_max_seconds del catálogo de límites (120 s).
    category: constraint
    applies_to: VoiceRecording.duration_seconds
    trigger: Grabación en curso
    logic: SI la grabación llega al máximo ENTONCES se detiene sola y aparece «Se alcanzó el máximo de 2 minutos; envía este turno y graba el siguiente»; los últimos 15 s muestran el tiempo restante.
    violation: La prueba Vitest con reloj simulado falla.
    source: P1 = A, C25 (audio_max_seconds)
  - id: BR1.4
    statement: La consola envía WAV PCM de 16 bits, mono, 16 kHz.
    category: calculation
    applies_to: VoiceRecording.audio_format
    trigger: Pulsar «Detener y enviar»
    logic: SI se envía una grabación ENTONCES se codifica a WAV mono de 16 kHz, sin depender del formato nativo del navegador.
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
    logic: SI el actor no es el dueño, es admin o es una identidad de servicio ENTONCES 403 auth.forbidden, 0 filas y 0 mensajes.
    violation: 403 Problem Details.
    source: C1 (x-veridicus-owner-only), ADR-009
  - id: BR2.2
    statement: Un turno de voz se rechaza en el mismo orden y con los mismos codes que un turno escrito, y después por la autorización de voz.
    category: constraint
    applies_to: POST /sessions/{session_id}/voice-turns
    trigger: Petición de turno de voz, bajo el bloqueo de la fila de la sesión
    logic: "En este orden: SI no hay ConsentRecord ENTONCES 409 session.consent_missing; SI la sesión está bloqueada por incidente ENTONCES 409 session.blocked; SI hay retirada ENTONCES 409 session.consent_withdrawn; SI está terminated ENTONCES 409 session.terminated; SI está finalized o consolidated ENTONCES 409 session.finalized; SI es importada ENTONCES 409 session.closed_to_new_turns; SI está suspended ENTONCES 409 session.suspended; luego BR8.1 y luego BR2.3. En pausa el turno se acepta (BR9.7). Cada rechazo deja 0 filas, 0 archivos y 0 mensajes."
    violation: Una prueba de nivel 1 por guardia cuenta 0 filas y 0 mensajes en veridicus:audio.
    source: FR10.2 (mismo camino que un turno escrito), VE-06, VE-10, AC15.4.2, C1
  - id: BR2.3
    statement: El audio se valida antes de crear el turno.
    category: validation
    applies_to: VoiceSubmission
    trigger: Petición de turno de voz que pasó BR2.2
    logic: SI el formato declarado no es wav ni mp3, si el contenido no corresponde al formato o si el hablante no es ENT ni TEST ENTONCES 422 validation.invalid_request; SI pesa más que audio_max_bytes o el audio decodificado dura más que audio_max_seconds ENTONCES 413 limits.exceeded; en ambos casos 0 filas, 0 archivos y 0 mensajes. La duración nunca se toma de la cabecera.
    violation: 422 o 413 Problem Details; pruebas de nivel 1 con un WAV de cabecera manipulada y un MP3 de tasa variable.
    source: P1 = A, C1, C25, revisión 1 R-07
  - id: BR2.4
    statement: Reenviar la misma grabación no crea un segundo turno.
    category: constraint
    applies_to: VoiceSubmission.client_request_id
    trigger: Dos peticiones con el mismo client_request_id en la misma sesión
    logic: SI el client_request_id ya existe en la sesión ENTONCES se responde 202 con el mismo turno y no se publica otro mensaje de audio.
    violation: La prueba de nivel 1 envía dos veces y cuenta un turno.
    source: C1 (client_request_id), AC10.2.2
  - id: BR2.5
    statement: Un turno de voz aceptado se numera, queda en transcripción y no tiene corrida todavía.
    category: policy
    applies_to: Turn con origin voice
    trigger: Petición que pasó BR2.1 a BR2.4
    logic: SI la petición es válida ENTONCES, con BR8.2 si aplica, en una transacción se crea el turno con el siguiente número, origin voice y su hablante, y su VoiceTurnState (voice_status transcribing, voice_deadline_at, audio_retained); tras confirmar se publica AudioToTranscribe con schema_version, attempt 1, retain_audio y deadline_at, y se responde 202 con el turno sin run.
    violation: La prueba de nivel 1 falla.
    source: FR10.2, AC10.2.1, AC10.2.2, C1, C5

  # BR3 — Transcripción en audio-worker
  - id: BR3.1
    statement: El audio se transcribe con Whisper dentro del clúster, en español y con timeout.
    category: policy
    applies_to: audio-worker
    trigger: Mensaje AudioToTranscribe que pasó BR3.6 y BR9.6
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
    logic: SI el texto está vacío ENTONCES se publica outcome error con analysis.invalid_output (precisión FD-U9-01).
    violation: La prueba de nivel 0 con fake que devuelve vacío falla.
    source: P2 = A, C5
  - id: BR3.4
    statement: Un fallo o un plazo vencido de la transcripción se publica como error con su code, sin reintento.
    category: policy
    applies_to: TranscriptResult
    trigger: Timeout, error de Whisper o mensaje recibido después de deadline_at
    logic: SI el mensaje llega tarde ENTONCES outcome error con analysis.timeout sin llamar a Whisper; SI Whisper supera su timeout ENTONCES analysis.timeout; SI Whisper rechaza la conexión, responde 5xx o una respuesta mal formada ENTONCES analysis.system; la llamada nunca se reintenta y el mensaje no vuelve a la cola.
    violation: Una prueba de nivel 0 por caso con el Whisper fake.
    source: P2 = A, C5, project.md (ante Whisper caído no hay reintento)
  - id: BR3.5
    statement: El audio se borra del stream al confirmarlo, con cualquier resultado, y el trabajador nunca lo guarda.
    category: policy
    applies_to: AudioToTranscribe
    trigger: Publicar el TranscriptResult o descartar el mensaje
    logic: SI se publicó el resultado o se descartó el mensaje (BR3.6, BR9.6) ENTONCES se confirma (XACK) y se borra (XDEL); el trabajador no escribe el audio en disco, en un volumen ni en un log, con o sin retain_audio.
    violation: La prueba de nivel 1 comprueba que el stream queda sin el mensaje tras cada resultado.
    source: SpeechProcessing en components, C5, AUTONOMIA-04, VE-08
  - id: BR3.6
    statement: Un mensaje de audio repetido no produce dos transcripciones.
    category: constraint
    applies_to: audio-worker
    trigger: Entrega repetida del mismo mensaje
    logic: SI existe la clave veridicus:transcribed:{turn_id}:{attempt} ENTONCES el mensaje se confirma y se borra sin llamar a Whisper ni publicar; la clave se escribe con TTL justo antes de publicar el resultado.
    violation: La prueba de nivel 1 de entrega doble cuenta una llamada al fake y un resultado.
    source: C5 (entrega al menos una vez), revisión 1 R-05, precisión FD-U9-06

  # BR4 — Ingesta del resultado en session-api
  - id: BR4.1
    statement: Un turno transcrito sigue el mismo camino que un turno escrito.
    category: policy
    applies_to: Turn con origin voice
    trigger: TranscriptResult con outcome transcribed y voice_status transcribing
    logic: SI llega el texto ENTONCES, en una transacción con el orden sesión → ronda, se guarda Turn.text, voice_status transcribed, transcribed_at y model_digest; SI el turno es TEST, la sesión admite corridas y ninguna corrida ya cubre el turno (BR9.3) ENTONCES se crea la corrida incremental con desde_turno = hasta_turno = n, igual que para un turno escrito, sujeta a BR9.1. Un turno ENT, una sesión en pausa o terminada no crean corrida.
    violation: La prueba de nivel 1 compara la entrada de C2 y el resultado de un turno de voz con los del mismo texto escrito.
    source: FR10.2, AC10.2.1
  - id: BR4.2
    statement: Un error de transcripción deja el turno sin texto y se resuelve grabando de nuevo.
    category: policy
    applies_to: Turn con origin voice
    trigger: TranscriptResult con outcome error, o plazo vencido
    logic: SI la transcripción falló ENTONCES voice_status error con voice_error_code y sin corrida; la consola muestra «No se pudo transcribir el audio» con «Grabar de nuevo» y «Escribir el turno», que crean un turno nuevo. No hay reintento, porque el turno no tiene corrida y el audio no se conserva para reprocesar (P2 = A, BR8.4). Ninguna entrada de C6 incluye el turno.
    violation: La prueba de nivel 1 y la de Vitest fallan.
    source: P2 = A, project.md (sin audio guardado para reintentar)
  - id: BR4.3
    statement: Un resultado que llega tarde o repetido no cambia el turno.
    category: constraint
    applies_to: Ingesta de TranscriptResult
    trigger: Resultado para un turno cuyo voice_status ya no es transcribing
    logic: SI el turno ya está transcribed o en error (por plazo, por retirada o por un resultado anterior) ENTONCES el resultado se descarta, se confirma y no cambia ninguna fila.
    violation: La prueba de nivel 1 de resultado tardío falla.
    source: C5; plazo de transcripción de NFR Requirements de U9
  - id: BR4.4
    statement: El texto transcrito no se edita.
    category: constraint
    applies_to: Turn.text con origin voice
    trigger: Cualquier intento de cambiar el texto
    logic: SI se intenta cambiar el texto de un turno ENTONCES no existe ruta para hacerlo; las aclaraciones van en un turno nuevo y ambos quedan en el reporte.
    violation: La prueba de contrato confirma que no hay ruta de edición.
    source: P3 = A

  # BR5 — Voz de la aclaración aprobada (US10.4)
  - id: BR5.1
    statement: Solo se sintetiza una aclaración aprobada.
    category: constraint
    applies_to: GET /conductor-observations/{observation_id}/audio
    trigger: Pulsar «Escuchar audio»
    logic: SI la aclaración no existe ENTONCES 404 conductor_observation.not_found; SI no está approved ENTONCES 409 conductor_observation.not_approved; en ambos casos 0 llamadas a audio-worker y al TTS. La consola solo muestra «Escuchar audio» en una aclaración aprobada.
    violation: 404 o 409 Problem Details; la prueba de nivel 0 cuenta 0 llamadas al TTS fake.
    source: FR10.4, AC10.4.1, C1
  - id: BR5.2
    statement: El TTS solo se llama cuando el analista pulsa «Escuchar audio».
    category: policy
    applies_to: SpeechProcessing — síntesis
    trigger: Ciclo de vida de una aclaración
    logic: SI nadie pulsa «Escuchar audio» ENTONCES el TTS registra 0 llamadas, aunque la aclaración se apruebe o se muestre.
    violation: La prueba de nivel 0 con TTS fake cuenta 0 llamadas.
    source: AC10.4.1, FR10.4
  - id: BR5.3
    statement: La voz se sintetiza dentro del clúster en audio-worker en cada pulsación y no se guarda.
    category: policy
    applies_to: ConductorObservationAudio
    trigger: Petición que pasó BR5.1, BR5.4 y BR5.7
    logic: SI se pide el audio ENTONCES ConsoleApi llama a la ruta interna de audio-worker con SpeechRequest, audio-worker aplica BR5.6 y llama a ModelGateway.synthesize en CPU con timeout, y se devuelve audio/wav sin guardarlo; SI el TTS falla o vence su timeout ENTONCES 503 speech.unavailable (precisión FD-U9-02) y la consola dice «No se pudo generar el audio; puedes leer la aclaración en pantalla».
    violation: La prueba de nivel 0 con TTS fake y la de nivel 1 de la ruta interna fallan.
    source: AC10.4.1, C13, revisión 1 R-01
  - id: BR5.4
    statement: Solo el dueño de la sesión escucha la aclaración.
    category: authorization
    applies_to: GET /conductor-observations/{observation_id}/audio
    trigger: Petición de audio
    logic: SI el actor no es el dueño de la sesión de la aclaración ENTONCES 403 auth.forbidden y 0 llamadas al TTS.
    violation: 403 Problem Details.
    source: C1 (x-veridicus-owner-only), VE-09, ADR-009
  - id: BR5.5
    statement: Lo que se pronuncia es la plantilla versionada con el tema de la aclaración, y nada más.
    category: calculation
    applies_to: SpeechRequest, ClarificationSpeechTemplate
    trigger: Síntesis de una aclaración aprobada
    logic: SI se sintetiza ENTONCES audio-worker arma el texto sustituyendo {tema} en la plantilla de la versión cargada; SI template_version no coincide con la cargada ENTONCES rechaza con BR5.6. session-api solo envía el tema, nunca un texto libre.
    violation: La prueba de nivel 0 compara el texto entregado al TTS fake con la plantilla y el tema.
    source: P7 = A, VE-09, precisión FD-U9-05
  - id: BR5.6
    statement: El TTS rechaza todo texto que no sea una aclaración válida.
    category: validation
    applies_to: Ruta interna de síntesis de audio-worker
    trigger: SpeechRequest recibido
    logic: SI el texto compuesto no pasa la regla de DT23 (menciona la contradicción, dice «antes dijo» o una variante, o contiene una cita) o el escaneo de vocabulario prohibido, o la versión de la plantilla no coincide ENTONCES audio-worker responde 422 sin llamar al TTS y ConsoleApi responde 409 speech.text_rejected (precisión FD-U9-02); el registro lleva solo observation_id y el ID de la regla.
    violation: Una prueba de nivel 0 por caso de DT23 y de vocabulario con control negativo cuenta 0 llamadas al TTS fake.
    source: VE-05, VE-09, AC10.4.2, C8
  - id: BR5.7
    statement: Solo se escucha una aclaración mientras la sesión admite turnos nuevos.
    category: constraint
    applies_to: GET /conductor-observations/{observation_id}/audio
    trigger: Petición de audio que pasó BR5.4 y BR5.1
    logic: SI la sesión está bloqueada, tiene la retirada, está terminated, finalized, consolidated o suspended ENTONCES 409 con el code de esa situación en el orden de BR2.2 y 0 llamadas al TTS; en open y en paused se admite.
    violation: Una prueba de nivel 1 por estado.
    source: VE-09 (la voz es el canal hacia la persona entrevistada), VE-10, propuesta de esta etapa

  # BR6 — Frontera del clúster y registros (US9.1)
  - id: BR6.1
    statement: El audio-worker es un pod con datos sin anonimizar y no tiene salida a internet.
    category: constraint
    applies_to: Despliegue de audio-worker
    trigger: Política de manifiestos de nivel 0
    logic: SI el pod audio-worker no lleva la etiqueta de clasificación de datos sin anonimizar o no está cubierto por la NetworkPolicy de salida denegada ENTONCES la política falla; su salida permitida es solo Redis y los servidores Whisper y TTS internos, y su única entrada aparte de las sondas es la ruta interna de síntesis desde session-api.
    violation: La política de nivel 0 falla; la verificación manual con curl -m 5 a un host público termina con código distinto de 0.
    source: AC9.1.1, AC9.1.2, AUTONOMIA-04
  - id: BR6.2
    statement: El audio-worker no arranca con una URL de modelo externa al clúster.
    category: validation
    applies_to: Configuración de audio-worker
    trigger: Arranque
    logic: SI la URL de Whisper o la del TTS no es interna del clúster, o falta la plantilla de voz ENTONCES el pod no arranca.
    violation: La prueba de nivel 0 de configuración falla.
    source: C13, AUTONOMIA-04, Code Style de team.md (configuración faltante impide arrancar)
  - id: BR6.3
    statement: Ni el audio ni el texto transcrito ni el tema aparecen en los registros.
    category: policy
    applies_to: Logs de session-api y audio-worker
    trigger: Cualquier registro del flujo de voz
    logic: SI se registra un evento ENTONCES lleva solo session_id, turn_id, observation_id, message_id, audio_id, attempt, code y duración; un canary sembrado en el audio fake no aparece en ningún log capturado.
    violation: La prueba de nivel 1 del canary falla.
    source: AC9.1.4, Code Style de team.md
  - id: BR6.4
    statement: El modelo Whisper y el TTS se fijan por sha256 y se descargan en el aprovisionamiento.
    category: policy
    applies_to: Artefactos de modelo de U9
    trigger: Construcción de la imagen o aprovisionamiento
    logic: SI se usa un modelo ENTONCES su revisión está fijada y verificada con sha256, en un formato sin código ejecutable, y nunca se descarga en ejecución.
    violation: La comprobación de nivel 0 del manifiesto de modelos falla.
    source: Deployment de team.md, C14

  # BR7 — Accesibilidad (US5.6)
  - id: BR7.1
    statement: Los controles de voz cumplen la accesibilidad común.
    category: validation
    applies_to: Botones «Grabar», «Detener y enviar», «Grabar de nuevo», «Escribir el turno» y «Escuchar audio»
    trigger: Suite axe y recorrido con teclado
    logic: SI axe encuentra violaciones serious o critical, si grabar, detener, enviar o escuchar no se puede hacer solo con teclado, o si el estado de grabación, de transcripción o de error se identifica solo por color ENTONCES la prueba falla.
    violation: La prueba de nivel 3 o la de Vitest falla.
    source: AC5.6.1, AC5.6.2, AC5.6.3
  - id: BR7.2
    statement: «Grabar» deshabilitado recibe el foco y anuncia su motivo.
    category: validation
    applies_to: Botón «Grabar»
    trigger: Sesión sin autorización de voz o que no admite turnos
    logic: SI la sesión no autoriza la voz ENTONCES «Grabar» usa aria-disabled="true" con aria-describedby «La sesión no autoriza grabar la voz»; SI la sesión no admite turnos ENTONCES el mismo patrón con el motivo del estado; nunca disabled nativo.
    violation: La prueba Vitest falla.
    source: AC5.6.4, AC15.4.1
  - id: BR7.3
    statement: Los estados de los turnos de voz no se anuncian uno por uno.
    category: validation
    applies_to: Turnos de voz en la consola
    trigger: Cambio de voice_status o de la espera de una corrida
    logic: SI cambia el estado de la transcripción o de la espera ENTONCES no se anuncia en aria-live; se lee al enfocar el turno. Solo se anuncian el inicio y el fin de la grabación (BR1.2) y el error de un envío.
    violation: La prueba Vitest con diez turnos de voz cuenta los anuncios.
    source: AC5.6.5

  # BR8 — Autorización de voz y audio conservado (VE-06, VE-08)
  - id: BR8.1
    statement: Sin la autorización de voz, la grabación se rechaza aunque haya consentimiento.
    category: authorization
    applies_to: POST /sessions/{session_id}/voice-turns
    trigger: Petición que pasó las guardias de estado de BR2.2
    logic: SI el ConsentRecord de la sesión tiene authorizes_voice false ENTONCES 409 session.voice_not_authorized, 0 filas, 0 archivos y 0 mensajes; el turno escrito sigue aceptándose.
    violation: La prueba de nivel 1 cuenta 0 filas y 0 mensajes.
    source: VE-06, AC15.4.3, C1
  - id: BR8.2
    statement: Con la autorización de conservar el audio, se escribe al recibirlo, archivo antes que fila.
    category: policy
    applies_to: TurnAudio
    trigger: Petición válida con authorizes_audio_retention true
    logic: SI la sesión autoriza conservar el audio ENTONCES session-api escribe el archivo en su directorio de audio con permisos solo del proceso, calcula su sha256 y, en la misma transacción que numera el turno (BR2.5), crea TurnAudio con retained_until igual al plazo de retención de la sesión; sea cual sea el resultado de la transcripción, el archivo se queda. SI la escritura del archivo falla ENTONCES 503 sin turno ni mensaje.
    violation: La prueba de nivel 1 compara el sha256 del archivo con el del audio enviado, también con una transcripción fallida.
    source: VE-08, AC10.2.4, P4 = A, C5
  - id: BR8.3
    statement: Sin la autorización, tras confirmar la transcripción no queda audio en el volumen ni en la cola.
    category: constraint
    applies_to: Audio de un turno de voz
    trigger: Ingesta del TranscriptResult
    logic: SI la sesión no autoriza conservar el audio ENTONCES no existe archivo ni fila TurnAudio y, tras la confirmación del resultado, el mensaje ya no está en veridicus:audio; el audio solo estuvo en memoria y en el stream.
    violation: La prueba de nivel 1 recorre el directorio de audio y el stream tras cada resultado.
    source: VE-08, AC10.2.4
  - id: BR8.4
    statement: El audio conservado no se usa para nada.
    category: policy
    applies_to: TurnAudio
    trigger: Cualquier lectura del audio conservado
    logic: SI existe TurnAudio ENTONCES no habilita reintento, ni escucha, ni descarga, ni una segunda transcripción; ninguna ruta de C1 ni proceso salvo el Job de retención lo abre.
    violation: La prueba de contrato confirma que ninguna ruta lo expone; import-linter impide que audio-worker importe el módulo de TurnAudio.
    source: P4 = A, project.md (sin audio guardado para reintentar)
  - id: BR8.5
    statement: Un archivo de audio sin su fila se borra al arrancar.
    category: constraint
    applies_to: Directorio de audio de session-api
    trigger: Arranque de session-api
    logic: SI hay un archivo cuyo audio_id no tiene fila TurnAudio y es más antiguo que el arranque ENTONCES se borra y se registra solo el audio_id.
    violation: La prueba de nivel 1 siembra un huérfano y comprueba su borrado.
    source: P4 = A (archivo antes que fila), VE-08
  - id: BR8.6
    statement: El audio conservado se borra con la sesión al vencer su retención.
    category: policy
    applies_to: TurnAudio
    trigger: Job de retención sobre la sesión
    logic: SI el Job de retención borra una sesión ENTONCES borra antes cada archivo de TurnAudio y después su fila, y el acta lleva el audio_id y el sha256, nunca el audio.
    violation: La prueba de nivel 1 con reloj simulado del Job de retención (precisión FD-U9-09).
    source: VE-12, AC10.2.4 (hasta el vencimiento de la retención)

  # BR9 — Orden de los turnos y ciclo de vida de la sesión (P5 = B, P6 = C)
  - id: BR9.1
    statement: Una corrida incremental espera a que se resuelvan los turnos de voz anteriores.
    category: policy
    applies_to: AnalysisRun incremental de una sesión guiada
    trigger: Creación de una corrida incremental (turno escrito, ingesta de un texto o reanudación del análisis)
    logic: SI al crear la corrida hay en la sesión un turno de voz con número menor que hasta_turno y voice_status transcribing ENTONCES la corrida queda queued sin deadline_at y sin publicar, con RunPublicationHold apuntando al más antiguo de esos turnos; la consola muestra «En cola · esperando la transcripción del turno n».
    violation: La prueba de nivel 1 envía un turno de voz lento y uno escrito y comprueba que C2 del escrito sale después y lleva el texto del de voz.
    source: P5 = B, AC10.2.1, revisión 1 R-02
  - id: BR9.2
    statement: Las corridas en espera se liberan en orden cuando no queda ningún turno de voz anterior sin resolver.
    category: policy
    applies_to: RunPublicationHold
    trigger: Ingesta de un TranscriptResult o vencimiento del plazo de un turno de voz
    logic: SI en la misma transacción que resuelve un turno de voz ninguna corrida en espera tiene ya turnos de voz anteriores en transcribing ENTONCES se liberan en orden de hasta_turno; al liberar se asigna deadline_at con la fórmula del flujo de texto, la entrada de C6 se arma en ese momento con los turnos que tienen texto (los de voz en error no entran) y se publica en veridicus:runs tras confirmar.
    violation: Pruebas de nivel 1 con el turno de voz transcrito, en error y vencido.
    source: P5 = B, AC10.2.1, plazos de NFR Requirements de U9
  - id: BR9.3
    statement: Un turno de voz no recibe dos corridas incrementales.
    category: constraint
    applies_to: Ingesta del texto
    trigger: TranscriptResult transcribed de un turno TEST
    logic: SI ya existe una corrida creada después de aceptar el turno cuyo tramo lo cubre (en espera o publicada, p. ej. la de «Reanudar análisis») ENTONCES la ingesta guarda el texto y no crea otra corrida.
    violation: La prueba de nivel 1 de reanudación con un turno de voz en transcripción cuenta una sola corrida que lo cubre.
    source: P5 = B, la corrida única de «Reanudar análisis» (VE-10)
  - id: BR9.4
    statement: Tras terminar la sesión, el audio en cola se transcribe y el texto se guarda sin análisis.
    category: policy
    applies_to: Turnos de voz en transcribing de una sesión terminada
    trigger: «Terminar sesión»
    logic: SI se termina la sesión ENTONCES las corridas en espera se cancelan junto con las encoladas, los turnos de voz en transcribing siguen y su ingesta guarda el texto con voice_status transcribed y sin corrida; la consola los muestra «Transcrito · sin análisis».
    violation: La prueba de nivel 1 termina la sesión con un turno de voz en cola y cuenta 0 corridas nuevas.
    source: P6 = C, VE-10
  - id: BR9.5
    statement: Al registrar la retirada del consentimiento, los turnos de voz en transcripción terminan sin transcribirse.
    category: policy
    applies_to: Turnos de voz en transcribing de una sesión con retirada
    trigger: Registro de la retirada del consentimiento
    logic: SI se registra la retirada ENTONCES, en la misma transacción, cada turno de voz en transcribing pasa a error con session.consent_withdrawn y las corridas en espera se cancelan; tras confirmar se escribe VoiceCancellationKey con su TTL.
    violation: La prueba de nivel 1 registra la retirada con dos audios en cola y comprueba los dos turnos en error y 0 corridas.
    source: P6 = C, VE-10, el mecanismo de clave de cancelación de CD-06
  - id: BR9.6
    statement: El audio de una sesión con la retirada no llega a Whisper.
    category: constraint
    applies_to: audio-worker
    trigger: Mensaje AudioToTranscribe
    logic: SI existe veridicus:voice-cancelled:{session_id} ENTONCES el mensaje se confirma y se borra sin llamar a Whisper y sin publicar resultado. Un resultado de una llamada que ya había salido se descarta en la ingesta (BR4.3) y su texto no se guarda.
    violation: La prueba de nivel 1 cuenta 0 llamadas al Whisper fake tras la retirada y comprueba que el turno no tiene texto.
    source: P6 = C, VE-10, AUTONOMIA-04
  - id: BR9.7
    statement: En pausa, el turno de voz se acepta y su texto se guarda sin corrida.
    category: policy
    applies_to: Turnos de voz de una sesión en pausa
    trigger: Envío o ingesta con la sesión en pausa; «Pausar análisis»
    logic: SI la sesión está en pausa ENTONCES el envío responde 202 y la ingesta guarda el texto sin corrida; al pausar, las corridas en espera se cancelan con las encoladas; la corrida de «Reanudar análisis» sigue BR9.1 y BR9.3.
    violation: La prueba de nivel 1 de pausa con un turno de voz y la de reanudación.
    source: VE-10, AC10.2.1 (mismo camino que un turno escrito)
```

## Resumen de reglas

| Grupo | Reglas | Qué protegen |
|---|---|---|
| BR1 Grabación | BR1.1–BR1.6 | Micrófono negado sin bloquear el texto, indicador anunciado, máximo del catálogo, WAV mono de 16 kHz, consola no bloqueada, rótulo de transcripción automática |
| BR2 Recepción | BR2.1–BR2.5 | Dueño, orden de las guardias, audio válido con duración decodificada, sin duplicados, turno numerado sin corrida |
| BR3 Transcripción | BR3.1–BR3.6 | Whisper interno en español con timeout, vacío como error, codes de C5 sin reintento, audio borrado siempre, sin dobles transcripciones |
| BR4 Ingesta | BR4.1–BR4.4 | Mismo camino que el texto, error que se resuelve grabando de nuevo, resultados tardíos descartados, texto sin edición |
| BR5 Voz de la aclaración | BR5.1–BR5.7 | Solo aprobada, solo al pulsar, en `audio-worker` y sin guardar, solo el dueño, plantilla con el tema, rechazo de otro texto, solo con la sesión abierta o en pausa |
| BR6 Frontera | BR6.1–BR6.4 | Salida denegada, URL internas, registros sin audio ni texto, modelos fijados |
| BR7 Accesibilidad | BR7.1–BR7.3 | `axe` y teclado, «Grabar» deshabilitado con motivo, sin anuncios por turno |
| BR8 Consentimiento y audio | BR8.1–BR8.6 | Autorización de voz, audio conservado al recibirlo, nada sin autorización, sin uso, huérfanos, borrado por retención |
| BR9 Orden y ciclo de vida | BR9.1–BR9.7 | Espera en orden, liberación, una corrida por turno, terminación, retirada, clave de cancelación, pausa |
