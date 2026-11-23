# Diseño de observabilidad — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03. Las secciones conservan número y
tema. Cambian: las métricas van en `contracts/metrics/voice.v1.yaml` con las etiquetas `outcome` y
`error_code` de la lista cerrada de U1 (NFRD-U1-05); sale la pregunta sugerida y entran la aclaración, la espera
de corridas y el audio conservado; `audio_length` y `result` dejan de ser etiquetas.

**Insumos.** `nfr-requirements/observability-requirements.md` (observability-requirements, NFR15.1–NFR15.4),
`performance-requirements.md` (performance-requirements), `security-requirements.md`
(security-requirements, NFR10.6), `scalability-requirements.md` (scalability-requirements),
`reliability-requirements.md` (reliability-requirements) y `tech-stack-decisions.md` (tech-stack-decisions)
de esta unidad; F1–F8 de `functional-design/functional-spec.md` (functional-spec) y BR6.3 de
`functional-design/rules.md`; C15 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); NFR Design de U1 (§4.12), U2 (raspado de `audio-worker`, NFRD-U2-03), U3 (formateador) y
U4 (eventos y métricas).

## 1. Logs (NFR15.2, NFR15.3, NFR15.4)

- Formateador JSON único de `libs/` (U3) con los campos tipados de NFRD-U9-09. Nunca audio, base64, texto
  transcrito, tema, frase compuesta ni ruta absoluta del archivo conservado; la prueba de los cuatro centinelas
  lo verifica (`security-design.md` §6).
- **Correlación sin trazas distribuidas.** `session-api` asigna `message_id` al publicar `AudioToTranscribe`;
  `audio-worker` lo copia en el `TranscriptResult`; la ingesta lo registra y el turno sigue con los eventos de
  U4. `turn_id` + `attempt` + `message_id` (u `observation_id` en la síntesis) reconstruyen el camino.

| Evento | Servicio | Nivel |
|---|---|---|
| `voice.received`, `audio.stored` (solo con autorización), `audio.enqueued` | API de `session-api` | `INFO` |
| `voice.rejected` con `code` y `reason` (`size`, `format`, `header`, `duration`) | API de `session-api` | `WARNING` |
| `run.held`, `run.released` | API o trabajador de `session-api` | `INFO` |
| `transcript.ingested`, `voice.cancelled` | Trabajador o API de `session-api` | `INFO` |
| `audio.transcribing`, `audio.transcribed`, `audio.deleted`, `speech.synthesized` | `audio-worker` | `INFO` |
| Turno de voz en `error`, con `code` | `audio-worker` o trabajador | `WARNING` |
| Mensaje a `veridicus:audio:failed` o `veridicus:transcripts:failed` | Consumidor | `WARNING` |
| `speech.unavailable`; `speech.text_rejected` con `rule_id` | API de `session-api` y `audio-worker` | `WARNING` |
| `aof.rewrite_requested` / `aof.rewrite_failed` con `code` (P2 = A, NFRD-U9-06) | `audio-worker` | `INFO` / `WARNING` |
| Redis, Whisper o TTS caídos; fallo al escribir el audio conservado | Cualquiera | `ERROR` |

Verificación de nivel 1: una prueba sigue un turno de voz por sus logs desde `voice.received` hasta el fin de su
corrida, incluidos `audio.deleted` y `run.released`; otra comprueba un `WARNING` por cada caso de NFR15.4 y un
`ERROR` por cada dependencia caída.

## 2. Métricas (NFR15.1)

`prometheus-client` en `/metrics` del puerto interno de cada proceso; `audio-worker` lo expone en el servidor
FastAPI de D10 y U2 lo raspa (NFRD-U2-03). Todas salvo la primera se declaran en
`contracts/metrics/voice.v1.yaml` y las comprueba `checks/metrics.py` de U1 (NFRD-U9-10).

| Métrica | Tipo y etiquetas | Dónde se actualiza |
|---|---|---|
| `veridicus_turn_latency_seconds{origin="voice"}` | histogram (C15) | Al terminar la corrida que incluye el turno, `fin − submitted_at` |
| `veridicus_voice_submissions_total` | counter; `outcome` (`accepted`, `duplicate`, `rejected`), `error_code` (`none` o un `code` de NFR10.12) | Al final de `POST /voice-turns` |
| `veridicus_voice_upload_bytes` | histogram (0,25, 0,5, 1, 2, 4, 6 MB) | Tras leer la subida |
| `veridicus_transcription_seconds` | histogram (1, 2, 4, 8, 12, 20, 30, 40, 60, 90) | Alrededor de la llamada a Whisper |
| `veridicus_transcriptions_total` | counter; `outcome` (`transcribed`, `failed`, `duplicate`, `cancelled`, `dead_letter`), `error_code` (`none`, `analysis.invalid_output`, `analysis.timeout`, `analysis.system`) | En `audio_lifecycle.close` |
| `veridicus_audio_queue_depth` | gauge | `XLEN veridicus:audio` + pendientes del grupo, en cada vuelta |
| `veridicus_speech_synthesis_seconds` | histogram (0,5, 1, 2, 3, 5, 8, 12); `outcome` (`ok`, `timeout`, `error`, `rejected`) | Alrededor de la composición y la llamada al TTS |
| `veridicus_clarification_audio_requests_total` | counter; `outcome` (`ok`, `not_found`, `not_approved`, `forbidden`, `session_state`, `text_rejected`, `unavailable`) | Al final de `GET /conductor-observations/{id}/audio` |
| `veridicus_run_hold_wait_seconds` | histogram (1, 5, 15, 30, 60, 120, 360, 1 800); `outcome` (`transcribed`, `error`, `timeout`, `withdrawn`, `cancelled`) | En `hold_release`, `released_at − created_at` |
| `veridicus_run_holds_active` | gauge | Recuento de esperas sin `released_at`, en cada vuelta del supervisor |
| `veridicus_audio_store_bytes` | gauge | Contador de la cuota |
| `veridicus_aof_rewrite_requests_total` | counter; `outcome` (`requested`, `in_progress`, `error`) | En el `AofRewriteRequester` (NFRD-U9-06) |

`veridicus_question_audio_requests_total` queda «Retirado». Las etiquetas son solo de enum; nunca
identificadores ni texto. CPU y memoria de `model-whisper`, `model-tts` y `audio-worker` salen de las métricas
del clúster de U2.

## 3. SLI y objetivos del MVP

| SLI | Fuente | Objetivo |
|---|---|---|
| Latencia de transcripción | p95 de `veridicus_transcription_seconds` en los clips ≤ 30 s de la corrida de voz (el reporte separa por tramo de duración) | ≤ 12 s, sola y mixta (NFR3.1, NFR3.15) |
| Latencia del turno de voz | p95 de `veridicus_turn_latency_seconds{origin="voice"}` en la corrida de voz | ≤ 192 s para clips ≤ 30 s (NFR3.3, derivada) |
| Éxito de la transcripción | `veridicus_transcriptions_total{outcome="transcribed"}` / clips con habla | ≥ 98 % (NFR8.10) |
| Espera de corridas | p95 de `veridicus_run_hold_wait_seconds` en la corrida mixta | ≤ 12 s con clips ≤ 30 s (NFR3.16) |
| Salud de la cola de audio | `veridicus_audio_queue_depth` | ≤ 3 sostenido |
| Llenado del audio conservado | `veridicus_audio_store_bytes` / `audio_store_max_bytes` | < 80 % (NFR8.12) |
| Rastro del audio en disco | `veridicus_aof_rewrite_requests_total{outcome="error"}` | 0 en la corrida de voz |

## 4. Panel y reglas informativas

- **Panel de Grafana (SHOULD, lo instala U2)** junto al del turno de U4: latencia de transcripción p50 y p95,
  profundidad de la cola de audio y esperas activas, resultados por `outcome`, latencia de la síntesis, llenado
  del audio conservado, peticiones de reescritura del AOF, y CPU y memoria de `model-whisper`, `model-tts` y
  `audio-worker`. El JSON vive en `services/audio-worker/observability/grafana-dashboard.json` y U2 lo copia
  con el mismo SHA-256, como el de U10.
- **Reglas informativas** (sin Alertmanager; no despiertan a nadie ni cambian nada):
  - `veridicus_audio_queue_depth > 3` durante 10 minutos;
  - más de 3 `veridicus_transcriptions_total{error_code="analysis.system"}` en 15 minutos;
  - `veridicus_run_holds_active > 0` durante más de 30 minutos;
  - llenado del audio conservado > 80 %;
  - cualquier `veridicus_aof_rewrite_requests_total{outcome="error"}` en 15 minutos.
- **Trazas distribuidas:** no en el MVP (NFR15.3).
