# Diseño de observabilidad — U9 voice

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; flujos F1–F4 de `functional-design/functional-spec.md`
(functional-spec); C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary);
respuestas P1 = A y P2 = A de `nfr-design-questions.md`; formateador de logs de U3 y observabilidad de
U4.

## 1. Logs (NFR15.2, NFR15.3, NFR15.4)

- El formateador JSON con lista blanca de `libs/` (U3), ampliado con `question_id`, `byte_size`,
  `audio_seconds` y `audio_format` (security-design §9). Nunca audio, base64, texto transcrito ni
  texto de la pregunta; la prueba de los tres centinelas lo verifica (nivel 1).
- **Correlación sin trazas distribuidas.** `session-api` asigna `message_id` al publicar
  `AudioToTranscribe`; `audio-worker` lo copia en el `TranscriptResult`; la ingesta lo registra y el
  turno sigue con los eventos de U4. Con `turn_id` + `attempt` + `message_id` se reconstruye el camino.

| Evento | Servicio | Nivel |
|---|---|---|
| `voice.received`, `audio.enqueued` | API de `session-api` | `INFO` |
| `voice.rejected` con `reason` (`size`, `format`, `header`, `duration`) | API de `session-api` | `WARNING` |
| `audio.transcribing`, `audio.transcribed`, `audio.deleted` | `audio-worker` | `INFO` |
| `transcript.ingested` | Trabajador de `session-api` | `INFO` |
| `turn.error` con `code` (turno de voz) | `audio-worker` o trabajador | `WARNING` |
| `queue.failed` (`veridicus:audio:failed`, `veridicus:transcripts:failed`) | Consumidor | `WARNING` |
| `speech.unavailable` | API de `session-api` | `WARNING` |
| `aof.rewrite_requested` / `aof.rewrite_in_progress` (P2 = A) | `audio-worker` | `INFO` |
| `aof.rewrite_failed` con `code` | `audio-worker` | `WARNING` |
| Dependencia caída (Redis, Whisper, TTS) | Cualquiera | `ERROR` |

Verificación de nivel 1: una prueba sigue un turno de voz por sus logs desde `voice.received` hasta
`turn.evaluated`, incluido `audio.deleted`; otra comprueba un `WARNING` por cada caso de NFR15.4.

## 2. Métricas (NFR15.1)

`prometheus-client` en `/metrics` del puerto interno de cada proceso (`audio-worker` expone el suyo en el
servidor FastAPI de D10).

| Métrica | Dónde se mide en el código |
|---|---|
| `veridicus_turn_latency_seconds{origin="voice"}` | En la ingesta de U4, `evaluated_at − submitted_at` |
| `veridicus_voice_submissions_total{outcome, reason}` | Al final de la ruta `POST /voice-turns` |
| `veridicus_voice_upload_bytes` | Tras leer la subida (performance-design §2) |
| `veridicus_transcription_seconds{audio_length}` | Alrededor de la llamada a Whisper |
| `veridicus_transcriptions_total{result}` | En `audio_lifecycle.finish` (reliability-design §2), con `late`, `duplicate` y `failed` para las salidas sin Whisper |
| `veridicus_audio_queue_depth` | `XLEN veridicus:audio` + pendientes del grupo, recalculado en cada vuelta del bucle |
| `veridicus_speech_synthesis_seconds{result}` | Alrededor de la llamada al TTS |
| `veridicus_question_audio_requests_total{result}` | Al final de `GET /questions/{id}/audio` |
| `veridicus_aof_rewrite_requests_total{result}` (nueva, P2 = A) | En el `AofRewriteRequester`; `result` = `requested`, `in_progress`, `error` |

Las etiquetas son enums cerrados; la prueba de nivel 0 de U4 que recorre el registro cubre las de U9. Se
añaden a C15 por un PR de U1.

## 3. SLI y objetivos del MVP

| SLI | Fuente | Objetivo |
|---|---|---|
| Latencia de transcripción | p95 de `veridicus_transcription_seconds{audio_length="le30"}` en la corrida de voz | ≤ 12 s |
| Latencia del turno de voz | p95 de `veridicus_turn_latency_seconds{origin="voice"}` en la corrida de voz | ≤ 75 s (clips ≤ 30 s) |
| Éxito de la transcripción | `veridicus_transcriptions_total{result="transcribed"}` / clips con habla | ≥ 98 % |
| Salud de la cola de audio | `veridicus_audio_queue_depth` | ≤ 3 sostenido |
| Rastro del audio en disco | `veridicus_aof_rewrite_requests_total{result="error"}` | 0 en la corrida de voz |

## 4. Panel y reglas informativas

- Panel de Grafana (SHOULD, U2), junto al de U4: latencia de transcripción p50/p95 por tramo, profundidad
  de la cola de audio, resultados por `result`, latencia de la síntesis, peticiones de reescritura del AOF
  y CPU y memoria de `model-whisper`, `model-tts` y `audio-worker`.
- Reglas informativas (no despiertan a nadie, no cambian nada): `veridicus_audio_queue_depth > 3` durante
  10 minutos; más de 3 `veridicus_transcriptions_total{result="error"}` en 15 minutos; cualquier
  `veridicus_aof_rewrite_requests_total{result="error"}` en 15 minutos (el audio podría quedar en disco
  más de lo diseñado).

## 5. Precisiones a artefactos ya aprobados

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `voice/nfr-requirements/observability-requirements.md` (§2) y C15 | Nueva métrica `veridicus_aof_rewrite_requests_total{result}` y eventos `aof.rewrite_*` | P2 = A |
