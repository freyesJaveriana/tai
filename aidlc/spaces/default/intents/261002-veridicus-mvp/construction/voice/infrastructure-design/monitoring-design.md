# Diseño de monitoreo — U9 voice

**Insumos.** Métricas, eventos de log, SLI y reglas informativas de
`nfr-design/observability-design.md` (observability-design §1–§4); presupuestos por tramo y topes de
memoria de `nfr-design/performance-design.md` (performance-design §1, §7); señales para escalar de
`nfr-design/scalability-design.md` (scalability-design §5); sondas y recuperación de
`nfr-design/reliability-design.md` (reliability-design §4, §10); rastro del AOF y logs sin datos de
`nfr-design/security-design.md` (security-design §2, §6); inventario y dominios de falla de
`nfr-design/logical-components.md` (logical-components §1–§2); flujos F1–F4 de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 = A, P2 = A y P3 = A
de `infrastructure-design-questions.md` (la voz está encendida en las dos máquinas, así que el
monitoreo de voz existe en las dos); kube-prometheus-stack mínimo sin Alertmanager, Loki ni
`redis_exporter` de U2; `infrastructure-specification.md` de esta carpeta.

El monitoreo es SHOULD (módulo 8) y no notifica a nadie: las alertas son reglas informativas que se ven en
el panel. Las metas de U9 se demuestran con la corrida de voz (nivel 2) y su reporte JSON, no con el
panel.

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| `veridicus_transcription_seconds{audio_length}` (histograma) | `audio-worker`, `PodMonitor` en `metrics` 8081 | p95 ≤ 12 s (`le30`), ≤ 40 s (`le120`) | Tramo dominante del turno de voz (NFR3.1, NFR3.2) |
| `veridicus_turn_latency_seconds{origin="voice"}` | Trabajador de `session-api` (U4) | p95 ≤ 75 s en clips ≤ 30 s; ≤ 100 s con 120 s | Turno de voz completo (NFR3.3) |
| `veridicus_transcriptions_total{result}` | `audio-worker` | `transcribed` ≥ 98 % de los clips con habla; `error` ≤ 3 en 15 min | Éxito y tipo de fallo (NFR15.4, NFR8.10) |
| `veridicus_audio_queue_depth` | `audio-worker` | ≤ 3 sostenido | Primera señal para escalar (scalability-design §5) |
| `veridicus_voice_submissions_total{outcome, reason}` | API de `session-api` | Rechazos por `size` o `header` = 0 en la corrida de voz | Separa errores de la consola de abusos (NFR10.1) |
| `veridicus_voice_upload_bytes` (histograma) | API de `session-api` | Máximo ≤ 6 000 000 | Confirma que el corte del tamaño funciona |
| `veridicus_speech_synthesis_seconds{result}` | `audio-worker` | p95 ≤ 5 s con 300 caracteres | «Escuchar audio» (NFR3.12) |
| `veridicus_question_audio_requests_total{result}` | API de `session-api` | `speech_unavailable` = 0 en la corrida de voz | Disponibilidad del TTS vista por el analista (NFR10.18) |
| `veridicus_aof_rewrite_requests_total{result}` | `audio-worker` | `error` = 0 | Única señal de que el audio podría quedar en el AOF más de lo diseñado (NFR10.4); no hay `redis_exporter` |
| `container_memory_working_set_bytes` de `veridicus-whisper`, `veridicus-tts`, `veridicus-audio-worker` | cAdvisor (kubelet) | ≤ tope de performance-design §7 (1 GiB, 512 MiB, 256 MiB) | Un pico sobre el tope es un hallazgo por PR (NFR8.1–NFR8.3) |
| `container_cpu_cfs_throttled_periods_total` de `veridicus-whisper` | cAdvisor | Informativo | Explica una transcripción lenta por el `limits.cpu` 4 (NFR8.8) |
| `kube_pod_container_status_restarts_total`, `kube_pod_container_status_last_terminated_reason="OOMKilled"` | kube-state-metrics | 0 `OOMKilled` | Objetivo de la corrida de voz (NFR8.10) |
| `kube_deployment_status_replicas_available` de los tres `Deployment` de voz | kube-state-metrics | = 1 | La voz es SHOULD: su caída no frena el flujo de texto, pero se ve |

Todas las etiquetas son enums cerrados (prueba de nivel 0 de U4 sobre el registro). `veridicus-tts` y
`veridicus-whisper` no exponen métricas propias: su latencia se mide desde `audio-worker` y sus recursos
desde cAdvisor.

## 2. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VoiceQueueBacklog` | `veridicus_audio_queue_depth > 3` durante 10 min | Advertencia (informativa) | Panel «Veridicus — Voz» (sin Alertmanager) |
| `VoiceTranscriptionErrors` | `increase(veridicus_transcriptions_total{result="error"}[15m]) > 3` | Advertencia (informativa) | Panel |
| `VoiceAofRewriteFailed` | `increase(veridicus_aof_rewrite_requests_total{result="error"}[15m]) > 0` | Crítica (informativa): el audio podría seguir en disco | Panel; el humano revisa el log `aof.rewrite_failed` |
| `VoiceComponentDown` | `kube_deployment_status_replicas_available{deployment=~"veridicus-(audio-worker|whisper|tts)"} < 1` durante 5 min | Advertencia (informativa) | Panel |
| `VoicePodOOMKilled` | Cualquier `OOMKilled` en los pods de voz en 30 min | Advertencia (informativa) | Panel; hallazgo por PR |
| `VoiceSpeechUnavailable` | `increase(veridicus_question_audio_requests_total{result="speech_unavailable"}[15m]) > 3` | Informativa | Panel |

Los umbrales están por debajo de los objetivos (cola ≤ 3 sostenida, 0 errores del AOF) para ver el
problema antes de que una corrida falle. Las reglas viven en un `PrometheusRule` del subchart
`audio-worker`, que solo se renderiza con `monitoring.enabled`.

## 3. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 de `veridicus_transcription_seconds{audio_length="le30"}` | ≤ 12 s | Corrida de voz (perfil CPU, `values-cpu.yaml`) |
| p95 de `veridicus_transcription_seconds{audio_length="le120"}` | ≤ 40 s | Corrida de voz |
| p95 de `veridicus_turn_latency_seconds{origin="voice"}` en clips ≤ 30 s | ≤ 75 s | Corrida de voz y `voice.spec.ts` |
| `transcribed` / clips con habla | ≥ 98 % | Corrida de voz |
| Turnos de voz terminados antes de `deadline_at + 30 s` | 100 % | Corrida de voz con 1 y con 3 sesiones |
| p95 de `veridicus_speech_synthesis_seconds{result="ok"}` | ≤ 5 s | Corrida de voz (20 preguntas) |
| `veridicus_audio_queue_depth` | ≤ 3 sostenido | Ventana deslizante de 10 min en el panel |
| `veridicus_aof_rewrite_requests_total{result="error"}` | 0 | Corrida de voz y ventana de 15 min |
| `/readyz` de `audio-worker` en `scripts/smoke.sh` | 200 en cada despliegue | Cada ejecución de `smoke.sh` |

## 4. Logs y trazas

| Aspecto | Diseño |
|---|---|
| Recolección | `kubectl logs` de cada pod (no hay Loki, U2); salida estándar en JSON de una línea |
| Formato | Formateador de lista blanca de U3, ampliado con `question_id`, `byte_size`, `audio_seconds`, `audio_format`, `message_id`, `turn_id`, `attempt`, `code`, `reason`, `result`; nunca bytes, base64, texto transcrito ni texto de la pregunta (NFR10.6, NFR15.2) |
| Eventos | Los de observability-design §1 (`voice.received` … `aof.rewrite_failed`) con su nivel |
| `veridicus-tts` | Uvicorn con `--no-access-log`; el servidor solo registra arranque, voz cargada (nombre y `sha256`) y errores con tipo y `code` |
| `veridicus-whisper` | Configurado sin registro del cuerpo; comprobación manual antes de la sustentación: tras la corrida E2E, sus logs y los de `veridicus-tts` no contienen la frase centinela |
| Retención | La del nodo de Minikube (rotación del *runtime*); los logs no llevan datos sensibles, así que no hay purga especial |
| Trazas | Sin trazas distribuidas (U2). Correlación por `message_id` + `turn_id` + `attempt` desde `voice.received` hasta `turn.evaluated` (NFR15.3) |

## 5. Paneles

Panel de Grafana «Veridicus — Voz» como `ConfigMap` con la etiqueta `grafana_dashboard` del subchart
`audio-worker`, junto al de U4:

| Fila | Paneles |
|---|---|
| Turnos de voz | p50/p95 de transcripción por `audio_length`; p95 del turno de voz; resultados por `result`; envíos por `outcome` y `reason` |
| Cola y Redis | `veridicus_audio_queue_depth`; peticiones de reescritura del AOF por `result` |
| Síntesis | p95 de `veridicus_speech_synthesis_seconds`; peticiones de audio por `result` |
| Recursos | CPU, *throttling* y memoria frente al límite de `veridicus-whisper`, `veridicus-tts` y `veridicus-audio-worker`; reinicios y `OOMKilled` |
| Reglas | Estado de las seis reglas de §2 |
