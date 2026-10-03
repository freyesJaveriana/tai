# Entidades — U9 voice

**Alcance.** SpeechProcessing no tiene tablas propias (components: `entities: []`). El audio crudo nunca se
guarda en disco ni en la base: vive en el navegador mientras se graba, en la petición HTTP y en el
*stream* `veridicus:audio` hasta que el trabajador lo confirma. El turno de voz es un `Turn` de
InterviewSession con `origin: voice`. Aquí se modelan los valores y mensajes que U9 maneja y las
referencias a entidades de otros componentes.

```yaml
entities:
  - name: VoiceRecording
    owner: AnalystConsole
    kind: value-object
    description: Grabación push-to-talk en el navegador, antes de enviarla. Nunca se guarda en el almacenamiento del navegador.
    attributes:
      - { name: duration_seconds, type: decimal, required: true, min: 0.5, max: 120, description: "120 s máximo (P1 = A); la grabación se corta sola al llegar" }
      - { name: audio_format, type: enum, required: true, allowed: [wav], description: "la consola codifica a WAV PCM 16 bits, mono, 16 kHz, que el contrato admite y Whisper consume" }
      - { name: client_request_id, type: uuid, required: true, description: "se genera al pulsar «Enviar»; reenviar la misma grabación usa el mismo valor" }
      - { name: state, type: enum, required: true, allowed: [idle, recording, ready, sending], default: idle }

  - name: VoiceSubmission
    owner: InterviewSession
    kind: value-object
    description: Petición POST /sessions/{session_id}/voice-turns ya validada en la frontera.
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: client_request_id, type: uuid, required: true, unique: true, description: "único por sesión; repetirlo devuelve el mismo turno" }
      - { name: audio_format, type: enum, required: true, allowed: [wav, mp3] }
      - { name: byte_size, type: integer, required: true, min: 1, description: "máximo VERIDICUS_VOICE_MAX_BYTES, que fija NFR Requirements" }
      - { name: duration_seconds, type: decimal, required: true, max: 120, description: "se lee de la cabecera del audio" }

  - name: AudioToTranscribe
    owner: InterviewSession
    kind: message
    description: Mensaje del stream veridicus:audio (C5). Lleva el único ejemplar del audio fuera del navegador.
    attributes:
      - { name: message_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: uuid, required: true }
      - { name: session_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true, min: 1, description: "siempre 1 en un turno de voz: no hay reintento de transcripción (P2 = A)" }
      - { name: audio_format, type: enum, required: true, allowed: [wav, mp3] }
      - { name: audio_base64, type: string, required: true }
      - { name: deadline_at, type: UtcTimestamp, required: true }
    constraints:
      - "Se borra del stream (XDEL) en cuanto el trabajador lo confirma, con cualquier resultado (BR3.5)."
      - "No se escribe en ningún log ni volumen."

  - name: TranscriptResult
    owner: SpeechProcessing
    kind: message
    description: Mensaje del stream veridicus:transcripts (C5) con el texto o el error de la transcripción.
    attributes:
      - { name: message_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true, min: 1 }
      - { name: outcome, type: enum, required: true, allowed: [transcribed, error] }
      - { name: text, type: string, required: false, description: "solo si outcome es transcribed; nunca vacío ni solo espacios" }
      - { name: error_code, type: enum, required: false, allowed: [turn.error.system, turn.error.timeout, turn.error.invalid_output], description: "turn.error.invalid_output para texto vacío es una ampliación de C5 (X1)" }
      - { name: model_digest, type: string, required: false, description: "sha256 del modelo Whisper usado" }

  - name: QuestionAudio
    owner: SpeechProcessing
    kind: value-object
    description: Voz sintetizada de una pregunta aprobada. Se genera en cada pulsación y no se guarda.
    attributes:
      - { name: question_id, type: uuid, required: true }
      - { name: content, type: bytes, required: true, description: "audio/wav devuelto en la respuesta y descartado" }

references:
  - { name: Turn, owner: InterviewSession, used_for: "turno de voz con origin voice, processing_stage transcribing, texto transcrito, estado y code de error" }
  - { name: InterviewSessionRecord, owner: InterviewSession, used_for: "dueño y estado de la sesión (solo open admite turnos)" }
  - { name: SuggestedQuestion, owner: SemanticEvaluation, used_for: "texto y estado (proposed, approved, discarded) de la pregunta que se escucha (U8)" }
  - { name: User, owner: IdentityAccess, used_for: "dueño que graba o escucha" }
```

## Resumen

- **VoiceRecording** vive solo en la consola. Dura como mucho 120 s y se codifica a WAV mono de 16 kHz.
  Lleva un `client_request_id` para que un reenvío no cree dos turnos.
- **VoiceSubmission** es la petición validada. Formato, tamaño y duración se comprueban antes de crear el
  turno.
- **AudioToTranscribe** y **TranscriptResult** son los mensajes de C5. El audio existe solo en el primero y
  se borra al confirmarlo. El turno de voz tiene un solo intento de transcripción: si falla, se graba de
  nuevo (P2 = A).
- **QuestionAudio** es la voz de una pregunta aprobada. Se genera al pulsar «Escuchar audio» y no se
  guarda.
- El texto transcrito se guarda en el `Turn` de InterviewSession y no se corrige (P3 = A). Ninguna entidad
  guarda audio.
