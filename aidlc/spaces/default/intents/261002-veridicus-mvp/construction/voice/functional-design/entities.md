# Entidades — U9 voice

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02.** Sustituye a la revisión 1 del
2026-10-03. Respuestas: P1–P3 = A (siguen), P4 = A, P5 = B, P6 = C, P7 = A.
- **Siguen:** VoiceRecording, VoiceSubmission, AudioToTranscribe y TranscriptResult, reescritas para C5 1.1.0
  (`schema_version`, `retain_audio`, `hablante`) y para los codes de C5 (cierra R-07).
- **Sale (Retirado):** QuestionAudio y la referencia a SuggestedQuestion. La pregunta sugerida salió con el
  Paquete de Contexto de Traspaso (cambio 01).
- **Entran:** VoiceTurnState (lo que U9 suma al `Turn`, que ya no guarda su estado), TurnAudio (audio
  conservado con autorización, VE-08 y P4 = A), RunPublicationHold (espera en orden, P5 = B),
  VoiceCancellationKey (retirada del consentimiento, P6 = C), SpeechRequest y ConductorObservationAudio
  (voz de la aclaración, P7 = A) y ClarificationSpeechTemplate (plantilla versionada, P7 = A).

**Fuentes.** `unit-of-work.md` y `unit-of-work-story-map.md` (U9, revisión 3), `requirements.md` y su
adenda 02, `components.md` (SpeechProcessing, InterviewSession, TurnAudio) y `contract-summary.md` (C1, C5,
C8, C25).

**Alcance.** SpeechProcessing no tiene tablas propias (`components.md`: `entities: []`). Las tablas nuevas
son de InterviewSession (`session-api`), que es dueño del esquema. El audio crudo vive en el navegador
mientras se graba, en la petición HTTP y en el *stream* `veridicus:audio` hasta que el trabajador lo
confirma. Solo con `autoriza_conservar_audio` hay además un archivo en el volumen de InterviewSession.

## Modelo de entidades

```yaml
entities:
  - name: VoiceRecording
    status: Sigue
    owner: AnalystConsole
    kind: value-object
    description: Grabación push-to-talk en el navegador, antes de enviarla. Nunca se guarda en el almacenamiento del navegador.
    attributes:
      - { name: duration_seconds, type: decimal, required: true, min: 0.5, max: 120, description: "audio_max_seconds del catálogo de límites (120 s, P1 = A); la grabación se corta sola al llegar" }
      - { name: audio_format, type: enum, required: true, allowed: [wav], description: "la consola codifica a WAV PCM de 16 bits, mono, 16 kHz" }
      - { name: hablante, type: enum, required: true, allowed: [ENT, TEST], default: TEST, description: "el mismo selector que el turno escrito" }
      - { name: client_request_id, type: uuid, required: true, description: "se genera al pulsar «Detener y enviar»; un reenvío usa el mismo valor" }
      - { name: state, type: enum, required: true, allowed: [idle, recording, ready, sending, unavailable], default: idle, description: "unavailable: «Grabar» deshabilitado con motivo (sin autorización de voz o sesión que no admite turnos)" }

  - name: VoiceSubmission
    status: Sigue (reescrita)
    owner: InterviewSession
    kind: value-object
    description: Petición POST /sessions/{session_id}/voice-turns ya validada en la frontera (C1).
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: client_request_id, type: uuid, required: true, description: "único por sesión; repetirlo devuelve el mismo turno" }
      - { name: hablante, type: enum, required: true, allowed: [ENT, TEST] }
      - { name: audio_format, type: enum, required: true, allowed: [wav, mp3], description: "el contrato admite MP3; solo entra por la API" }
      - { name: byte_size, type: integer, required: true, min: 1, description: "máximo audio_max_bytes del catálogo de límites" }
      - { name: duration_seconds, type: decimal, required: true, max: 120, description: "se mide sobre el audio decodificado, nunca sobre la cabecera (cierra R-07)" }
    constraints:
      - "Se valida antes de crear filas o publicar mensajes; un rechazo deja 0 filas y 0 mensajes."

  - name: VoiceTurnState
    status: Nueva
    owner: InterviewSession
    kind: entity-extension
    description: Atributos que U9 suma al Turn de origen voice. El estado de análisis del turno no se guarda (se deriva de su corrida); solo se guarda el de la transcripción.
    attributes:
      - { name: turn_id, type: uuid, required: true, unique: true, references: Turn.turn_id }
      - { name: voice_status, type: enum, required: true, allowed: [transcribing, transcribed, error], default: transcribing, description: "C1 Turn.voice_status" }
      - { name: voice_error_code, type: enum, required: false, allowed: [analysis.timeout, analysis.system, analysis.invalid_output, session.consent_withdrawn], description: "solo con voice_status error; analysis.invalid_output es la precisión FD-U9-01" }
      - { name: voice_deadline_at, type: UtcTimestamp, required: true, description: "plazo de la transcripción, con la fórmula de NFR Requirements de U9" }
      - { name: transcribed_at, type: UtcTimestamp, required: false }
      - { name: model_digest, type: string, required: false, description: "sha256 del modelo Whisper que transcribió" }
      - { name: audio_retained, type: boolean, required: true, default: false, description: "copia de autoriza_conservar_audio en el momento de recibir el audio" }
    constraints:
      - "voice_status solo avanza: transcribing → transcribed o transcribing → error; nunca vuelve."
      - "voice_status transcribed exige Turn.text no vacío y transcribed_at; error exige voice_error_code."
      - "Turn.text de un turno de voz no se edita (P3 = A)."

  - name: TurnAudio
    status: Nueva (la usa U9; componente InterviewSession)
    owner: InterviewSession
    kind: entity
    description: Audio conservado con autorización expresa (VE-08). Se escribe al recibirlo, sea cual sea el resultado de la transcripción, y no se usa para nada (P4 = A).
    attributes:
      - { name: audio_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: uuid, required: true, unique: true, references: Turn.turn_id }
      - { name: storage_path, type: string, required: true, description: "ruta relativa dentro del directorio de audio de session-api; el nombre es el audio_id, nunca un dato del testimonio" }
      - { name: sha256, type: string, required: true, description: "del archivo escrito" }
      - { name: audio_format, type: enum, required: true, allowed: [wav, mp3] }
      - { name: byte_size, type: integer, required: true, min: 1 }
      - { name: retained_until, type: UtcTimestamp, required: true, description: "el plazo de retención de la sesión (VE-12); lo borra solo el Job de retención" }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "Archivo antes que fila: nunca hay fila sin archivo; un archivo sin fila lo borra el barrido al arrancar."
      - "Sin autoriza_conservar_audio no existe fila ni archivo."
      - "Ninguna ruta de C1 lo lee, lo descarga ni lo reprocesa."

  - name: AudioToTranscribe
    status: Sigue (reescrita)
    owner: InterviewSession
    kind: message
    description: Mensaje del stream veridicus:audio (C5 1.1.0).
    attributes:
      - { name: schema_version, type: string, required: true, description: "1.x.y" }
      - { name: message_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: uuid, required: true }
      - { name: session_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true, min: 1, max: 1, description: "siempre 1: no hay reintento de la transcripción (P2 = A)" }
      - { name: audio_format, type: enum, required: true, allowed: [wav, mp3] }
      - { name: audio_base64, type: string, required: true }
      - { name: retain_audio, type: boolean, required: true, description: "informativo: session-api ya escribió el audio al recibirlo (P4 = A); el trabajador no lo usa" }
      - { name: deadline_at, type: UtcTimestamp, required: true, description: "igual a VoiceTurnState.voice_deadline_at" }
    constraints:
      - "Se borra del stream (XDEL) en cuanto el trabajador lo confirma, con cualquier resultado, también cuando se descarta por retirada."
      - "No se escribe en ningún log."

  - name: TranscriptResult
    status: Sigue (reescrita)
    owner: SpeechProcessing
    kind: message
    description: Mensaje del stream veridicus:transcripts (C5) con el texto o el error de la transcripción.
    attributes:
      - { name: schema_version, type: string, required: true }
      - { name: message_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true, min: 1 }
      - { name: outcome, type: enum, required: true, allowed: [transcribed, error] }
      - { name: text, type: string, required: false, description: "solo con transcribed; nunca vacío ni solo espacios" }
      - { name: error_code, type: enum, required: false, allowed: [analysis.system, analysis.timeout, analysis.invalid_output], description: "analysis.invalid_output es la precisión FD-U9-01" }
      - { name: model_digest, type: string, required: false }

  - name: RunPublicationHold
    status: Nueva
    owner: InterviewSession
    kind: entity
    description: Espera de una corrida incremental que no se publica mientras haya un turno de voz anterior sin resolver (P5 = B).
    attributes:
      - { name: run_id, type: uuid, required: true, unique: true, references: AnalysisRun.run_id }
      - { name: session_id, type: uuid, required: true }
      - { name: waiting_on_turn_n, type: integer, required: true, description: "el turno de voz anterior más antiguo sin resolver; se muestra en la consola" }
      - { name: created_at, type: UtcTimestamp, required: true }
      - { name: released_at, type: UtcTimestamp, required: false }
      - { name: outcome, type: enum, required: false, allowed: [released, cancelled] }
    constraints:
      - "Mientras released_at es nulo, la corrida está queued, no tiene deadline_at y no está en veridicus:runs."
      - "Se libera en el orden de los turnos; se cancela con la corrida al pausar, terminar o registrar la retirada."
      - "Es de solo inserción para la liberación: released_at y outcome se escriben una vez."

  - name: VoiceCancellationKey
    status: Nueva
    owner: InterviewSession
    kind: value-object
    description: Clave de Redis veridicus:voice-cancelled:{session_id} que InterviewSession escribe al registrar la retirada del consentimiento y que audio-worker solo lee (P6 = C).
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: ttl_seconds, type: integer, required: true, description: "al menos el plazo máximo de la transcripción; la cifra la fija NFR Requirements" }

  - name: SpeechRequest
    status: Nueva
    owner: SpeechProcessing
    kind: message
    description: Cuerpo de la ruta interna de audio-worker que ConsoleApi llama tras comprobar dueño, aprobación y estado de la sesión.
    attributes:
      - { name: observation_id, type: uuid, required: true }
      - { name: tema, type: string, required: true, description: "el tema de la aclaración aprobada, ya restaurado; nunca otro texto" }
      - { name: template_version, type: string, required: true, description: "versión de ClarificationSpeechTemplate que espera session-api" }

  - name: ClarificationSpeechTemplate
    status: Nueva (propuesta FD-U9-05)
    owner: IntegrityPolicy
    kind: versioned-file
    description: Plantilla versionada con la que se arma la frase que se pronuncia (P7 = A). Solo cambia por PR.
    attributes:
      - { name: version, type: string, required: true }
      - { name: template, type: string, required: true, description: "con un único marcador {tema}; propuesta: «¿Podría contarnos un poco más sobre {tema}?»" }

  - name: ConductorObservationAudio
    status: Nueva (sustituye a QuestionAudio)
    owner: SpeechProcessing
    kind: value-object
    description: Voz sintetizada de una aclaración aprobada. Se genera en cada pulsación de «Escuchar audio» y no se guarda.
    attributes:
      - { name: observation_id, type: uuid, required: true }
      - { name: content, type: bytes, required: true, description: "audio/wav devuelto en la respuesta y descartado" }

  - name: QuestionAudio
    status: Retirado
    description: "Retirado (cambio 01): la pregunta sugerida salió con el Paquete de Contexto de Traspaso. La sustituye ConductorObservationAudio."

references:
  - { name: Turn, owner: InterviewSession, used_for: "turno con origin voice, hablante, número y texto transcrito" }
  - { name: InterviewSessionRecord, owner: InterviewSession, used_for: "dueño, estado y bloqueo de la sesión" }
  - { name: ConsentRecord, owner: InterviewSession, used_for: "authorizes_voice, authorizes_audio_retention y la retirada" }
  - { name: AnalysisRun, owner: InterviewSession, used_for: "corrida incremental que la ingesta crea y que puede quedar en espera" }
  - { name: ConductorObservation, owner: InterviewSession, used_for: "tema y estado (proposed, approved, discarded) de la aclaración que se escucha (U8)" }
  - { name: User, owner: IdentityAccess, used_for: "dueño que graba o escucha" }
  - { name: SuggestedQuestion, status: Retirado, used_for: "Retirado (cambio 01)" }

relationships:
  - { from: InterviewSessionRecord, to: Turn, cardinality: "1:N" }
  - { from: Turn, to: VoiceTurnState, cardinality: "1:0..1", note: "solo turnos con origin voice" }
  - { from: Turn, to: TurnAudio, cardinality: "1:0..1", note: "solo con autorización de conservar el audio" }
  - { from: Turn, to: AudioToTranscribe, cardinality: "1:1", note: "un único mensaje, borrado tras confirmarlo" }
  - { from: AudioToTranscribe, to: TranscriptResult, cardinality: "1:0..1", note: "0 si se descarta por retirada o plazo vencido antes de llamar" }
  - { from: AnalysisRun, to: RunPublicationHold, cardinality: "1:0..1" }
  - { from: InterviewSessionRecord, to: VoiceCancellationKey, cardinality: "1:0..1" }
  - { from: ConductorObservation, to: SpeechRequest, cardinality: "1:N", note: "una por pulsación" }
  - { from: SpeechRequest, to: ConductorObservationAudio, cardinality: "1:0..1" }
  - { from: ClarificationSpeechTemplate, to: SpeechRequest, cardinality: "1:N" }
```

## Resumen

- **VoiceRecording** vive solo en la consola: como mucho 120 s, WAV mono de 16 kHz, con su `hablante` y un
  `client_request_id` para que un reenvío no cree dos turnos. Pasa a `unavailable` cuando la sesión no
  autoriza la voz o no admite turnos.
- **VoiceSubmission** es la petición validada: hablante, formato, tamaño y duración (medida sobre el audio
  decodificado) se comprueban antes de crear filas.
- **VoiceTurnState** guarda solo el estado de la transcripción. El estado del análisis se deriva de la
  corrida, como en un turno escrito, y la corrida se crea al ingerir el texto, no en el `202`.
- **TurnAudio** existe solo con `autoriza_conservar_audio`. Se escribe al recibir el audio, archivo antes
  que fila, y no lo lee nadie salvo el Job de retención.
- **AudioToTranscribe** y **TranscriptResult** son los mensajes de C5. Hay un solo intento de
  transcripción: si falla, se graba de nuevo.
- **RunPublicationHold** retiene una corrida mientras un turno de voz anterior se transcribe, para que la
  corrida vea lo mismo que si el relato se hubiera escrito en orden.
- **VoiceCancellationKey** hace que, tras la retirada, el audio en cola no llegue a Whisper.
- **SpeechRequest**, **ClarificationSpeechTemplate** y **ConductorObservationAudio** forman la voz de la
  aclaración: solo el tema de una aclaración aprobada, dentro de una frase versionada, sintetizada en el
  clúster y sin guardar.
