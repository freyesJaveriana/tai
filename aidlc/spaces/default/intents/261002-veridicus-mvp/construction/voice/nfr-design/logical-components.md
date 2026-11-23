# Componentes lógicos — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03. Salen `QuestionAudioRoute`,
`VoiceUploadReader` propio (lo sustituye el lector compartido de U6) y el `DeadlineSweeper` ampliado (lo
sustituye el código de U9 sobre el `run-supervisor` de U4). Entran `ClarificationAudioRoute`, `SpeechText`,
`VoiceGuards`, `TurnAudioStore` y su barrido, `HoldRelease`, el adaptador de voz en `libs/model_gateway` y la
ampliación de la función de cancelación de InterviewSession.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D10, D13–D16) de esta unidad; §1 y F1–F8 de `functional-design/functional-spec.md`
(functional-spec); C1, C5, C13, C14 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary) y SpeechProcessing e InterviewSession de `inception/domain-design/components.md`; los
demás documentos de esta carpeta.

## 1. Inventario

| Componente lógico | Proceso (dentro o fuera del clúster) | Responsabilidad | Patrones de NFR |
|---|---|---|---|
| `VoiceRecorder` y `wavEncoder.worker` | Consola, navegador (fuera) | Grabar en memoria y codificar WAV 16 kHz | Web Worker; pistas detenidas; `blob:` revocadas |
| `VoiceSubmit` | Consola | Enviar con reintento y el mismo `client_request_id` | Reintento 1, 2, 4, 8 s, solo red y `5xx` |
| `VoiceTurnRoute` | API de `session-api` (dentro) | `POST /voice-turns` en el orden de `security-design.md` §3 | `GuardedRoute`; tope por cabecera; sin bloqueo al leer |
| `multipart_memory` (U6) | API de `session-api` | Leer la subida en memoria | Corte en `voice_body_max_bytes` |
| `AudioValidator` | API de `session-api` | Cabecera y duración medida | Sin decodificar; 100 % de ramas |
| `VoiceGuards` | API de `session-api` (`interview/domain/`) | Guardias de BR2.2 y BR8.1, dos veces | Función pura; 100 % de ramas |
| `TurnAudioStore` y `TurnAudioSweeper` | API de `session-api` | Archivo antes que fila, cuota, huérfanos | `O_EXCL`, `fsync`, `os.replace`; contador |
| `VoiceTurnEnqueuer` | API de `session-api` | Transacción con bloqueo, plazo proporcional, `XADD` tras `COMMIT` | Orden sesión → ronda |
| `ClarificationAudioRoute` | API de `session-api` | Dueño, aprobación, estado, tema y llamada interna | `no-store`; *timeout* 15 s; tope de respuesta |
| `TranscriptIngestor` | Trabajador de `session-api` | Consumir C5, guardar texto, crear corrida, liberar esperas | Idempotencia por intento; `XDEL` tras `COMMIT` |
| `HoldRelease` | `interview/domain/hold_release.py` | Crear y liberar esperas | Módulo único; 100 % de ramas |
| Ampliación del supervisor (U4) | Trabajador de `session-api` | Vencer turnos de voz, liberar esperas, recortar por `MINID` | Cada 15 s; código de U9 en B9 |
| Ampliación de la cancelación (U4) | API de `session-api` | Esperas y turnos de voz por motivo de la transición | En la transacción de U6 |
| Ampliación de `CancellationKeys` (U4) | API y trabajador de `session-api` | Escribir y reescribir la clave de voz | Tras `COMMIT`; al reconectar |
| `AudioConsumer` + `audio_lifecycle` | `audio-worker` (dentro) | Consumir C5, transcribir, publicar, borrar | 1 a la vez; `MULTI`; tope de entregas; 100 % de ramas |
| `LoopHeartbeat` | `audio-worker` | Latido que distingue espera de procesamiento | `reliability-design.md` §4 |
| `AofRewriteRequester` | `audio-worker` | `BGREWRITEAOF` con la cola vacía (P2 = A) | Ventana de 60 s; 100 % de ramas |
| `SpeechEndpoint` + `SpeechText` | `audio-worker` | Ruta interna, composición y validación de la frase | Bearer en tiempo constante; semáforo de 1; módulo puro |
| `SpeechLocalAdapter` (`transcribe`, `synthesize`) | `libs/model_gateway`, en `audio-worker` | Hablar con `model-whisper` y `model-tts` | URL internas; *timeouts*; sin anonimizador |
| `model-whisper`, `model-tts` | Pods de U2 (dentro) | Inferencia | Sin salida; `/tmp` en memoria |

## 2. Componentes en YAML

```yaml
components:
  - name: voice-turn-route
    path: services/session-api/session_api/console/voice_turns.py
    hosts: [session-api-api]
    boundary: inside
    data_in: raw_audio_from_browser
    data_out: audio_base64_to_redis
    guard: true
  - name: turn-audio-store
    path: services/session-api/session_api/interview/adapters/turn_audio_store.py
    hosts: [session-api-api]
    boundary: inside
    data_out: none
    readers: [retention-job]
    guard: true
  - name: transcript-ingestor
    path: services/session-api/session_api/interview/worker/transcript_ingestor.py
    hosts: [session-api-worker]
    boundary: inside
    data_out: none
    guard: false
  - name: hold-release
    path: services/session-api/session_api/interview/domain/hold_release.py
    hosts: [session-api-api, session-api-worker]
    boundary: inside
    data_out: none
    guard: true
  - name: audio-worker
    path: services/audio-worker
    hosts: [audio-worker]
    boundary: inside
    egress: [redis, model-whisper, model-tts]
    ingress_from: [session-api-api, prometheus-metrics-port]
    replicas: 1
    guard: true
  - name: speech-local-adapter
    path: libs/model_gateway/adapters/speech_local.py
    hosts: [audio-worker]
    boundary: inside
    data_out: internal_urls_only
    guard: true
```

## 3. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Radio |
|---|---|---|---|
| `model-whisper` | Turnos de voz nuevos (error en segundos) | Turnos escritos, revisión, aclaraciones | Turnos de voz de ese intervalo; las esperas se liberan |
| `model-tts` | «Escuchar audio» | Todo lo demás; la aclaración se lee en pantalla | Una acción |
| `audio-worker` | Transcripción y síntesis | Todo el flujo de texto (MUST) | Audios en cola: vuelven por reclamo o vencen; el supervisor recorta por `MINID` |
| Trabajador de `session-api` | Ingesta, supervisor, liberación | API y consola | Resultados pendientes hasta que vuelve |
| Redis | Encolar voz y texto; consola fuera de servicio (`/readyz` de U3) | Datos en PostgreSQL | Turnos nuevos |
| Volumen de audio lleno o fallando | Turnos de voz de sesiones con autorización de conservar | Turnos de voz sin esa autorización y turnos escritos | Sesiones con `autoriza_conservar_audio` |

La voz es SHOULD: ningún flujo MUST depende de un componente de esta tabla salvo Redis y el trabajador, que ya
son de U4.

## 4. Aislamiento y recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso API de `session-api` | U3–U8, U12, U13 | Lectura en memoria con corte; sin bloqueo durante la lectura; nada pesado en la API |
| Trabajador de `session-api` | U4, U6 | Un hilo de ingesta propio; el supervisor y el `HoldReleaser` de U4 con código de U9 |
| PostgreSQL | Todo `session-api` | Transacciones cortas; orden sesión → corrida → ronda; `statement_timeout` 2 s |
| Redis | U3 (limitador), U4, U6, U8 | Prefijos `veridicus:audio*`, `veridicus:transcripts*`, `veridicus:voice-cancelled:*`, `veridicus:transcribed:*`; *streams* vacíos tras procesar; recorte por `MINID`; `noeviction` |
| PVC `veridicus-audio` | Solo `session-api` y el `Job` de retención | Directorio `0700`, archivos `0600`, cuota propia |
| CPU de la máquina de desarrollo | Juez y verificador de U11 | `limits.cpu` de `model-whisper` (`scalability-design.md` §4) |
| `VERIDICUS_SPEECH_TOKEN` | `session-api` y `audio-worker` | Secret por referencia; tabla de consumidores de U2 |
| `libs/model_gateway` | U11 | Solo los métodos de voz y su adaptador; `Protocol` de dos métodos en `audio-worker` |

## 5. Calidad, pruebas y textos (NFR2.1, NFR2.2, NFR13.1, NFR13.2, NFR13.3, NFR14.1, NFR14.2, NFR14.3)

- **Dobles de prueba (NFR2.1).** `FakeWhisper` y `FakeTts` implementan `transcribe` y `synthesize` del
  `Protocol` de C13 con retardo, vacío, error, *timeout* y texto configurables; se escriben en B9 junto con la
  actualización de los *fakes* de U11 (D13). Redis y PostgreSQL reales en contenedor; ninguna prueba de los
  niveles 0 y 1 descarga un modelo, usa GPU o un micrófono real.
- **Perfil CPU (NFR2.2).** La corrida de voz usa `values-cpu.yaml`; el perfil GPU es opcional y corre en su
  etapa separada.
- **Cobertura (NFR13.1, NFR13.2).** ≥ 80 % de líneas en `services/audio-worker`, en los módulos de voz de
  `services/session-api`, en `libs/model_gateway/speech.py`, en `libs/model_gateway/adapters/speech_local.py` y
  en `frontend`. 100 % de ramas con `.coveragerc-guards` en `audio_lifecycle.py` (incluida la decisión de
  cancelación), `speech_text.py`, `AudioValidator`, `hold_release.py` y, por decisión de este diseño, en
  `VoiceGuards` y `AofRewriteRequester` (adicional a la regla del equipo, nunca en su lugar).
- **Fronteras (NFR13.3).** Los contratos de import-linter de `security-design.md` §14, cada uno con su control
  negativo.
- **Textos (NFR14.1).** Todos los literales visibles de la voz salen del catálogo de U1, incluidos los de
  FD-U9-14; la prueba de nivel 0 de U4 cubre los componentes de U9. La frase de voz sale de la plantilla.
- **Accesibilidad (NFR14.2).** `vitest-axe` sobre el control de grabación en `idle`, `recording`, `ready`,
  `sending` y error, y sobre «Escuchar audio»; `@axe-core/playwright` en `voice.spec.ts` con 0 violaciones
  `serious` o `critical`; teclado completo; región `aria-live="polite"` con los anuncios de BR1.2; estado con
  texto e icono; «Grabar» con `aria-disabled` y su motivo (BR7.2); sin anunciar cada cambio de estado (BR7.3).
- **Voz en español (NFR14.3).** Prueba de nivel 0 sobre `models.lock` (voz `es_*`) y, en la corrida de voz, 5
  frases de la plantilla sintetizadas y transcritas con WER ≤ 20 %.

## 6. Entrega a Infrastructure Design (U2)

- `Deployment` de `audio-worker` (1 réplica): raíz de solo lectura, `/tmp` en memoria y nada más escribible,
  etiqueta de datos sin anonimizar, puerto interno (síntesis) y puerto de métricas, `livenessProbe` en
  `/healthz` con el latido de `reliability-design.md` §4 y `readinessProbe` en `/readyz`.
- Subchart `model-tts` (Piper `es_*`, envoltorio HTTP que cierra Infrastructure Design) y ajustes de
  `model-whisper` (`cpu_threads = 4`, `limits.cpu` 4), ambos con `/tmp` en memoria y sin registrar cuerpos.
- Redis: `save ""`, `auto-aof-rewrite-percentage 100`, `auto-aof-rewrite-min-size 16mb`, `BGREWRITEAOF` sin
  renombrar, `maxmemory` con ≥ 128 MB para *streams*, `noeviction`, PVC con el doble del AOF máximo.
- PVC `veridicus-audio` de ≥ 1,2 × `audio_store_max_bytes`, montado solo por la API de `session-api` y el `Job`
  de retención.
- `NetworkPolicy` de `audio-worker` (salida a Redis, `model-whisper`, `model-tts` y DNS; entrada desde la API de
  `session-api` en el puerto de síntesis y desde Prometheus en métricas, NFRD-U9-16) y de los dos servidores de
  voz (entrada solo desde `audio-worker`).
- Ingress `veridicus-voice` sin guardar el cuerpo, con su tope de U2.
- Panel de Grafana de `observability-design.md` §4.
- Ajuste nuevo `VERIDICUS_AOF_REWRITE_MIN_INTERVAL_SECONDS` (NFRD-U9-06) y la cifra nueva de C25
  `voice_body_max_bytes` (NFRD-U9-03).
