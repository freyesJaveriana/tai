# Requisitos de observabilidad — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03.
- Los IDs se conservan (NFR15.1–NFR15.4).
- `question_id` se sustituye por `observation_id`, y la métrica de la pregunta sugerida queda «Retirado».
- Las etiquetas de las métricas pasan a `outcome` y `error_code`.
- Se añaden métricas de la espera de corridas, del audio conservado y de la síntesis rechazada.

**Insumos.**
- Flujos F1–F8 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR3.3–BR3.6, BR5.3–BR5.6, BR6.3, BR8.2 y BR9.1–BR9.6 de `functional-design/rules.md` (rules).
- NFR3, NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3).
- C5, C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- P1 = A y P2 = A de `nfr-requirements-questions.md`.

## 1. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | Logs estructurados sin audio, texto ni tema (BR6.3). | **Formato.** El de U4, con los campos permitidos de NFR10.6. **Nunca:** bytes de audio, base64, texto transcrito, tema ni frase de la aclaración, ni ruta absoluta del archivo conservado. **Prueba:** la de nivel 1 de los cuatro centinelas (NFR10.6). |
| NFR15.3 | cambia | Cada paso de un turno de voz deja rastro correlacionable. | **Eventos `INFO`.** <ul><li>`session-api`: `voice.received`, `audio.stored` (solo con autorización), `audio.enqueued`, `run.held`, `transcript.ingested`, `run.released` y `voice.cancelled`.</li><li>`audio-worker`: `audio.transcribing`, `audio.transcribed`, `audio.deleted` y `speech.synthesized`.</li><li>Después, los de U4.</li></ul> Todos llevan `turn_id`, `attempt` y `message_id`, o `observation_id` en la síntesis. Con ellos se reconstruye el camino del turno sin trazas distribuidas. **Prueba de nivel 1:** sigue un turno de voz por sus logs, con `audio.deleted` y `run.released`. |
| NFR15.4 | cambia | Los fallos se distinguen por `code`. | **Una línea `WARNING` por cada uno de estos casos:** <ul><li>turno de voz en `error`, con `code`;</li><li>subida rechazada, con su `code` y el motivo como enum (`size`, `format`, `header`, `duration`);</li><li>mensaje a `<stream>:failed`;</li><li>`speech.unavailable`;</li><li>`speech.text_rejected`, con el `rule_id`.</li></ul> Una caída de Redis, Whisper o TTS, o un fallo al escribir el audio conservado, deja `ERROR`. |

## 2. Métricas

Prometheus las lee en `/metrics` del puerto interno. Las de `audio-worker` necesitan la precisión
NFR-U9-05 (a).

| ID | Estado | Métrica | Tipo | Etiquetas | Servicio |
|---|---|---|---|---|---|
| NFR15.1 | se mantiene | `veridicus_turn_latency_seconds{origin="voice"}` (ya está en C15) | histogram (cubetas de U4) | `origin` | `session-api` |
| NFR15.1 | cambia | `veridicus_voice_submissions_total` | counter | `outcome` (`accepted`, `duplicate`, `rejected`); `error_code` (`none` o el `code` de NFR10.12) | `session-api` |
| NFR15.1 | se mantiene | `veridicus_voice_upload_bytes` | histogram (cubetas 0,25, 0,5, 1, 2, 4 y 6 MB) | ninguna | `session-api` |
| NFR15.1 | cambia | `veridicus_transcription_seconds` | histogram (cubetas 1, 2, 4, 8, 12, 20, 30, 40, 60 y 90) | ninguna; el tramo de duración lo da el reporte de la corrida de voz | `audio-worker` |
| NFR15.1 | cambia | `veridicus_transcriptions_total` | counter | `outcome` (`transcribed`, `failed`, `duplicate`, `cancelled`, `dead_letter`); `error_code` (`none`, `analysis.invalid_output`, `analysis.timeout`, `analysis.system`) | `audio-worker` |
| NFR15.1 | se mantiene | `veridicus_audio_queue_depth` | gauge | ninguna (`XLEN veridicus:audio` más pendientes) | `audio-worker` |
| NFR15.1 | cambia | `veridicus_speech_synthesis_seconds` | histogram (cubetas 0,5, 1, 2, 3, 5, 8 y 12) | `outcome` (`ok`, `timeout`, `error`, `rejected`) | `audio-worker` |
| NFR15.1 | Retirado | `veridicus_question_audio_requests_total` (salió con la pregunta sugerida) | — | — | — |
| NFR15.1 | nuevo | `veridicus_clarification_audio_requests_total` | counter | `outcome` (`ok`, `not_found`, `not_approved`, `forbidden`, `session_state`, `text_rejected`, `unavailable`) | `session-api` |
| NFR15.1 | nuevo | `veridicus_run_hold_wait_seconds` | histogram (cubetas 1, 5, 15, 30, 60, 120, 360 y 1 800) | `outcome` (`transcribed`, `error`, `timeout`, `withdrawn`) | `session-api` |
| NFR15.1 | nuevo | `veridicus_run_holds_active` | gauge | ninguna | `session-api` |
| NFR15.1 | nuevo | `veridicus_audio_store_bytes` | gauge | ninguna | `session-api` |

Las etiquetas solo llevan valores de enum, nunca identificadores ni texto (NFR-U9-08). La CPU y la memoria
de `model-whisper`, `model-tts` y `audio-worker` salen de las métricas del clúster que instala U2 (NFR15
de requirements).

## 3. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| Latencia de transcripción | p95 de `veridicus_transcription_seconds` para los clips de ≤ 30 s de la corrida de voz | ≤ 12 s (NFR3.1, NFR3.15) |
| Latencia del turno de voz | p95 de `veridicus_turn_latency_seconds{origin="voice"}` en la corrida de voz | ≤ 192 s para clips de ≤ 30 s (NFR3.3, derivada) |
| Éxito de la transcripción | `veridicus_transcriptions_total{outcome="transcribed"}` / clips con habla | ≥ 98 % (NFR8.10) |
| Espera de corridas | p95 de `veridicus_run_hold_wait_seconds` en la corrida de voz mixta | ≤ 12 s con clips de ≤ 30 s (NFR3.16) |
| Salud de la cola de audio | `veridicus_audio_queue_depth` | ≤ 3 sostenido (`scalability-requirements.md` §3) |
| Llenado del audio conservado | `veridicus_audio_store_bytes` / `audio_store_max_bytes` | < 80 % (NFR8.12) |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, lo instala U2).** Junto al panel del turno de U4, muestra:
  - la latencia de transcripción p50 y p95;
  - la profundidad de la cola de audio y las corridas en espera;
  - los resultados de transcripción por `outcome`;
  - la latencia de la síntesis;
  - el llenado del audio conservado;
  - la CPU y la memoria de `model-whisper`.
- **Alertas.** Ninguna avisa a nadie en el MVP (sin Alertmanager, decisión de Infrastructure Design en
  `project.md`). Hay cuatro reglas informativas:
  - `veridicus_audio_queue_depth > 3` durante 10 minutos;
  - más de 3 `veridicus_transcriptions_total{error_code="analysis.system"}` en 15 minutos (Whisper caído o
    mal configurado);
  - `veridicus_run_holds_active > 0` durante más de 30 minutos;
  - el llenado del audio conservado > 80 %.

  Ninguna regla cambia nada del sistema.
- **Trazas distribuidas.** No en el MVP: basta la correlación por `turn_id`, `attempt`, `message_id` y
  `observation_id` (NFR15.3).
