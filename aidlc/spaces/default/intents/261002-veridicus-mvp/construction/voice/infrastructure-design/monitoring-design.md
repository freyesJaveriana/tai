# Diseño de monitoreo — U9 voice

**Revisión 2 (2026-11-23).** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git. Las
secciones conservan su número; lo que sale queda «Retirado». Cambian los nombres de los pods (`model-whisper`,
`model-tts`, `audio-worker`), las métricas (las de `contracts/metrics/voice.v1.yaml` con `outcome` y
`error_code`), la aclaración sustituye a la pregunta sugerida y entran la espera de corridas y el audio
conservado. Supuesto de máquina: una sola de 64 GB, solo CPU (IDS-U2-01).

**Insumos.**
- Métricas, eventos, SLI y reglas informativas de `nfr-design/observability-design.md` revisión 2
  (observability-design §1–§4); topes por pod de `nfr-design/performance-design.md` (performance-design §1 y
  §7); señales para escalar y cuota de `nfr-design/scalability-design.md` (scalability-design §5 y §6); sondas y
  latido de `nfr-design/reliability-design.md` (reliability-design §4); rastro del AOF y logs sin datos de
  `nfr-design/security-design.md` (security-design §2 y §6); dominios de falla de
  `nfr-design/logical-components.md` (logical-components §3).
- F1–F8 de `functional-design/functional-spec.md` (functional-spec); SpeechProcessing de
  `inception/domain-design/components.md` (components); C15 y C16 de
  `inception/contract-design/contract-summary.md` (contract-summary).
- Pila de U2 (`kube-prometheus-stack` sin Alertmanager, Loki ni `redis_exporter`; módulo 8) y
  `infrastructure-specification.md` revisión 2 de esta carpeta (IDS-U9-11, IDS-U9-17).

El monitoreo es SHOULD (módulo 8) y no notifica a nadie: las alertas son reglas informativas que se ven en el
panel. Las metas de U9 se demuestran con la corrida de voz (nivel 2) y su reporte versionado, no con el panel.

## 1. Métricas y KPI · cambia

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_transcription_seconds` (histograma) | `audio-worker`, `ServiceMonitor` en `metrics` 8081 | p95 ≤ 12 s con clips ≤ 30 s y ≤ 40 s con 120 s; el tramo lo separa el reporte, no una etiqueta | Tramo dominante del turno de voz (NFR3.1, NFR3.2, NFR3.15) |
| `veridicus_turn_latency_seconds{origin="voice"}` (C15) | Trabajador de `session-api` | p95 ≤ 192 s con clips ≤ 30 s | Turno de voz completo (NFR3.3, derivada) |
| `veridicus_transcriptions_total{outcome, error_code}` | `audio-worker` | `transcribed` ≥ 98 % de los clips con habla; ≤ 3 `analysis.system` en 15 min | Éxito y tipo de fallo (NFR8.10, NFR15.4) |
| `veridicus_audio_queue_depth` | `audio-worker` | ≤ 3 sostenido | Primera señal para escalar (scalability-design §5) |
| `veridicus_voice_submissions_total{outcome, error_code}` | API de `session-api` | `rejected` con `limits.exceeded` = 0 en la corrida de voz | Separa errores de la consola de abusos (NFR10.1) |
| `veridicus_voice_upload_bytes` (histograma) | API de `session-api` | Máximo ≤ 6 000 000 | El corte del tamaño funciona |
| `veridicus_speech_synthesis_seconds{outcome}` | `audio-worker` | p95 ≤ 5 s | «Escuchar audio» (NFR3.12) |
| `veridicus_clarification_audio_requests_total{outcome}` | API de `session-api` | `unavailable` = 0 en la corrida de voz | Disponibilidad del TTS vista por el analista (NFR10.18) |
| `veridicus_run_hold_wait_seconds{outcome}`, `veridicus_run_holds_active` | API y trabajador de `session-api` | p95 ≤ 12 s con clips ≤ 30 s; ninguna espera activa > 30 min | Espera en orden de las corridas (NFR3.16, NFR10.26) |
| `veridicus_audio_store_bytes` / `audio_store_max_bytes` | API de `session-api` | < 0,8 | Cuota del audio conservado; Minikube no publica `kubelet_volume_stats` (NFR8.12) |
| `veridicus_aof_rewrite_requests_total{outcome}` | `audio-worker` | `error` = 0 | Única señal de que el audio podría quedar en el AOF más de lo diseñado (NFR10.4) |
| Memoria de trabajo de `model-whisper`, `model-tts`, `audio-worker` | cAdvisor (U2) | ≤ 1 GiB, 512 MiB y 256 MiB | Un pico sobre el tope es un hallazgo por PR (NFR8.1–NFR8.3) |
| *Throttling* de CPU de `model-whisper` | cAdvisor | Informativo | Explica una transcripción lenta por `limits.cpu` 4 frente al juez (NFR8.8) |
| `veridicus_question_audio_requests_total` | **Retirado** | — | La sustituye la de la aclaración (IDS-U9-11) |

Todas las etiquetas son enums cerrados del catálogo de U1, comprobados por `checks/metrics.py`
(NFRD-U9-10). `model-whisper` y `model-tts` no se raspan: su latencia se mide desde `audio-worker` y sus
recursos desde cAdvisor.

## 2. Alertas · cambia

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusVoiceQueueBacklog` | Cola de audio > 3 durante 10 min | warning (P3) | Panel «Veridicus — Voz»; sin notificación |
| `VeridicusVoiceTranscriptionErrors` | Más de 3 transcripciones con `analysis.system` en 15 min | warning (P3) | Panel |
| `VeridicusVoiceHoldStuck` | Esperas activas > 0 durante 30 min | warning (P3) | Panel |
| `VeridicusVoiceAudioStoreFilling` | Audio conservado > 80 % de la cuota | warning (P3) | Panel; decidir cuota y PVC o retención por PR (scalability-design §6) |
| `VeridicusVoiceAofRewriteFailed` | Cualquier error de reescritura del AOF en 15 min | critical (P3): el audio podría seguir en disco | Panel; el humano revisa el evento `aof.rewrite_failed` |
| `VoiceQueueBacklog`, `VoiceTranscriptionErrors`, `VoiceAofRewriteFailed`, `VoiceComponentDown`, `VoicePodOOMKilled`, `VoiceSpeechUnavailable` | **Retirado** (etiquetas viejas; la caída de pods y los OOM los cubren `VeridicusPodNotReady` y `VeridicusContainerRestarting` de U2) | — | — |

Los umbrales están por debajo de los objetivos para ver el problema antes de que una corrida falle. Las
reglas viven en el subchart `monitoring-rules` de U2 y solo se renderizan con `monitoring.enabled`.

## 2.1 Expresiones de las reglas (fuera de las tablas, cierra R-07)

```yaml
groups:
  - name: veridicus-voice
    rules:
      - alert: VeridicusVoiceQueueBacklog
        expr: veridicus_audio_queue_depth > 3
        for: 10m
      - alert: VeridicusVoiceTranscriptionErrors
        expr: increase(veridicus_transcriptions_total{error_code="analysis.system"}[15m]) > 3
      - alert: VeridicusVoiceHoldStuck
        expr: veridicus_run_holds_active > 0
        for: 30m
      - alert: VeridicusVoiceAudioStoreFilling
        expr: veridicus_audio_store_bytes / 2147483648 > 0.8
      - alert: VeridicusVoiceAofRewriteFailed
        expr: increase(veridicus_aof_rewrite_requests_total{outcome="error"}[15m]) > 0
```

`promtool test rules deploy/veridicus/charts/monitoring-rules/tests/voice.test.yaml` prueba cada regla con
un caso que dispara y otro que no (por ejemplo, cola 3 durante 10 min sin alerta y 4 con alerta; llenado 0,8
sin alerta y 0,81 con alerta). Corre en el paso 8 de `deploy-level0.yml` de U2. El divisor de la cuota se
copia de C25 y una prueba de nivel 0 compara los dos valores.

## 3. SLI y SLO · cambia

| SLI | SLO target | Measurement window |
|---|---|---|
| p95 de `veridicus_transcription_seconds` en clips ≤ 30 s | ≤ 12 s, sola y mixta | Corrida de voz (`values-cpu.yaml`) |
| p95 de `veridicus_transcription_seconds` en clips de 120 s | ≤ 40 s | Corrida de voz |
| p95 de `veridicus_turn_latency_seconds{origin="voice"}` en clips ≤ 30 s | ≤ 192 s | Corrida de voz y `voice.spec.ts` |
| `transcribed` / clips con habla | ≥ 98 % | Corrida de voz |
| Turnos de voz terminados antes de `deadline_at` + 30 s | 100 % | Corrida de voz con 1 y con 3 sesiones |
| p95 de `veridicus_run_hold_wait_seconds` | ≤ 12 s con clips ≤ 30 s | Corrida mixta |
| p95 de `veridicus_speech_synthesis_seconds{outcome="ok"}` | ≤ 5 s | Corrida de voz (20 aclaraciones) |
| `veridicus_aof_rewrite_requests_total{outcome="error"}` | 0 | Corrida de voz |
| Apariciones de los centinelas en los logs de los pods de voz | 0 | Nivel 1 y tras cada E2E de voz |
| `/readyz` de `audio-worker` en `scripts/smoke.sh` | 200 | Cada despliegue |

No se fija un porcentaje de disponibilidad mensual: la voz es SHOULD y el MVP corre a demanda en un solo
equipo (U2 §4).

## 4. Logs y trazas · cambia

| Aspecto | Diseño |
|---|---|
| Recolección | `kubectl logs` de cada pod (sin Loki); JSON de una línea; rotación del kubelet de U2 |
| Formato | Formateador de lista blanca de U3 con los campos tipados de NFRD-U9-09 (`session_id`, `turn_id`, `observation_id`, `message_id`, `audio_id`, `attempt`, `byte_size`, `audio_seconds`, `audio_format`, `reason`, `rule_id`); nunca audio, base64, texto transcrito, tema, frase compuesta ni ruta absoluta del archivo conservado |
| Eventos | Los de observability-design §1 (`voice.received` … `aof.rewrite_failed`) con su nivel |
| `model-tts` | Uvicorn con `--no-access-log`; solo arranque, voz cargada (nombre y `sha256`) y errores con tipo |
| `model-whisper` | Sin registro del cuerpo ni del texto (IDS-U9-04) |
| Comprobación sin datos (cierra R-02) | Nivel 1: la prueba de los cuatro centinelas sobre los logs capturados de `audio-worker`, la API y los *fakes*, umbral 0. Tras cada E2E de voz: `scripts/check-voice-logs.sh`, de solo lectura, lee con `kubectl logs` los pods `model-whisper`, `model-tts` y `audio-worker` y cuenta las apariciones de la frase centinela de `voice.spec.ts`; termina en 0 solo si son 0 |
| Retención | La del nodo; los logs no llevan datos sensibles |
| Trazas | Sin trazas distribuidas (NFR15.3); correlación por `message_id` + `turn_id` + `attempt` desde `voice.received` hasta el fin de la corrida |

## 5. Paneles · cambia

Panel «Veridicus — Voz» en `services/audio-worker/observability/grafana-dashboard.json`; U2 lo copia al
subchart `monitoring-rules` con el mismo SHA-256 (IDS-U9-17).

| Fila | Paneles |
|---|---|
| Turnos de voz | p50/p95 de transcripción; p95 del turno de voz; resultados por `outcome` y `error_code`; envíos por `outcome` |
| Cola, esperas y Redis | Cola de audio; esperas activas y p95 de espera; peticiones de reescritura del AOF por `outcome` |
| Síntesis | p95 de la síntesis; peticiones del audio de la aclaración por `outcome` |
| Audio conservado | Llenado frente a la cuota con la línea del 80 % |
| Recursos | CPU, *throttling* y memoria frente al límite de `model-whisper`, `model-tts` y `audio-worker` |
| Reglas | Estado de las cinco reglas de §2 |
