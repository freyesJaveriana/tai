# Requisitos de observabilidad — U9 voice

**Insumos.** Flujos F1–F4 de `functional-design/functional-spec.md` (functional-spec) y reglas BR3.3–BR3.6,
BR5.3 y BR6.3 de `functional-design/rules.md` (rules); NFR3, NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C5, C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

## 1. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Logs estructurados sin audio ni texto (BR6.3). | El formato de U4 (NFR15.2 de U4) con estos campos permitidos: `session_id`, `turn_id`, `question_id`, `message_id`, `attempt`, `code`, `byte_size`, `audio_seconds`, `audio_format` y duraciones. Nunca bytes de audio, base64, texto transcrito ni texto de la pregunta. Prueba de nivel 1 de los tres centinelas (NFR10.6). |
| NFR15.3 | Cada paso de un turno de voz deja rastro correlacionable. | Eventos `INFO`: `voice.received` y `audio.enqueued` (`session-api`); `audio.transcribing`, `audio.transcribed`, `audio.deleted` (`audio-worker`); `transcript.ingested` (`session-api`); y después los de U4 (`turn.processing`, `turn.evaluated`). Todos con `turn_id`, `attempt` y `message_id`. Con ellos se reconstruye el camino del turno sin trazas distribuidas. Prueba de nivel 1 que sigue un turno de voz por sus logs, incluido `audio.deleted`. |
| NFR15.4 | Los fallos se distinguen por `code`. | Una línea `WARNING` por cada turno de voz en `error` (con `code`), cada subida rechazada (con el motivo como enum: `size`, `format`, `header`, `duration`), cada mensaje a `<stream>:failed` y cada `speech.unavailable`; una caída de Redis, Whisper o TTS deja `ERROR`. |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno)

| ID | Métrica | Tipo | Etiquetas | Servicio |
|---|---|---|---|---|
| NFR15.1 | `veridicus_turn_latency_seconds{origin="voice"}` (ya en C15) | histogram (cubetas de U4) | `origin` | `session-api` |
| NFR15.1 | `veridicus_voice_submissions_total` | counter | `outcome` (`accepted`, `duplicate`, `rejected`), `reason` (`none`, `size`, `format`, `header`, `duration`, `forbidden`, `session_state`) | `session-api` |
| NFR15.1 | `veridicus_voice_upload_bytes` | histogram (cubetas 0,25, 0,5, 1, 2, 4, 6 MB) | ninguna | `session-api` |
| NFR15.1 | `veridicus_transcription_seconds` | histogram (cubetas 1, 2, 4, 8, 12, 20, 30, 40, 60, 90) | `audio_length` (`le30`, `le60`, `le120`) | `audio-worker` |
| NFR15.1 | `veridicus_transcriptions_total` | counter | `result` (`transcribed`, `empty`, `too_long`, `timeout`, `error`, `late`, `duplicate`, `failed`) | `audio-worker` |
| NFR15.1 | `veridicus_audio_queue_depth` | gauge | ninguna (`XLEN veridicus:audio` + pendientes) | `audio-worker` |
| NFR15.1 | `veridicus_speech_synthesis_seconds` | histogram (cubetas 0,5, 1, 2, 3, 5, 8, 10) | `result` (`ok`, `timeout`, `error`) | `audio-worker` |
| NFR15.1 | `veridicus_question_audio_requests_total` | counter | `result` (`ok`, `not_approved`, `forbidden`, `unavailable`) | `session-api` |

Las etiquetas solo llevan valores de enum, nunca identificadores ni texto. La CPU y la memoria de
`model-whisper`, `model-tts` y `audio-worker` salen de las métricas del clúster que instala U2 (NFR15
de requirements). Estas métricas se añaden a C15 por un PR de U1, y Prometheus recoge también
`/metrics` de `audio-worker` (precisiones en `security-requirements.md` §6).

## 3. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia de transcripción | p95 de `veridicus_transcription_seconds{audio_length="le30"}` en la corrida de voz | ≤ 12 s (NFR3.1) |
| Latencia del turno de voz | p95 de `veridicus_turn_latency_seconds{origin="voice"}` en la corrida de voz | ≤ 75 s para clips de ≤ 30 s (NFR3.3) |
| Éxito de la transcripción | `veridicus_transcriptions_total{result="transcribed"}` / clips con habla | ≥ 98 % (NFR8.10) |
| Salud de la cola de audio | `veridicus_audio_queue_depth` | ≤ 3 sostenido (`scalability-requirements.md` §3) |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Latencia de transcripción p50/p95 por tramo de
  duración, profundidad de la cola de audio, resultados de transcripción por `result`, latencia de la
  síntesis y CPU y memoria de `model-whisper`, junto al panel del turno de U4.
- **Alertas.** Ninguna despierta a alguien en el MVP. Dos reglas informativas: `veridicus_audio_queue_depth
  > 3` durante 10 minutos, y más de 3 `veridicus_transcriptions_total{result="error"}` en 15 minutos
  (Whisper caído o mal configurado). Ninguna regla cambia nada del sistema.
- **Trazas distribuidas.** No en el MVP: basta la correlación por `turn_id`, `attempt` y `message_id`
  (NFR15.3).
