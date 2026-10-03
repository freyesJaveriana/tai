# Componentes lógicos — U9 voice

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; `functional-design/functional-spec.md` (functional-spec); C1,
C5, C13, C14 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); respuestas
P1 = A y P2 = A de `nfr-design-questions.md`; los demás documentos de diseño de esta carpeta.

## 1. Inventario

| Componente lógico | Proceso (dentro o fuera del clúster) | Responsabilidad | Patrones de NFR |
|---|---|---|---|
| `VoiceRecorder` y `wavEncoder.worker` | Consola, navegador (fuera) | Grabar en memoria y codificar WAV 16 kHz | Web Worker; pistas detenidas y `blob:` revocadas |
| `VoiceSubmit` | Consola, navegador | Enviar con reintento y mismo `client_request_id` | Reintento 1, 2, 4, 8 s |
| `VoiceUploadReader` | API de `session-api` (dentro) | Leer el *multipart* en *streaming* (P1 = A) | Corte en el máximo; sin disco |
| `AudioValidator` | API de `session-api` | Cabecera y duración (100 % de ramas) | Sin decodificar; motivo como enum |
| `VoiceTurnEnqueuer` | API de `session-api` | Numerar, plazo de audio, `XADD` C5 | Bloqueo de la sesión de U4; plazo proporcional |
| `QuestionAudioRoute` | API de `session-api` | Dueño, aprobación, llamada a la ruta interna | `authorize`; `no-store`; *timeout* 12 s |
| `TranscriptIngestor` | Trabajador de `session-api` (dentro) | Consumir C5, guardar texto, publicar C2 | Idempotencia por intento |
| `DeadlineSweeper` (ampliado) | Trabajador de `session-api` | Vencer turnos en `transcribing` | Cada 15 s |
| `AudioConsumer` + `audio_lifecycle` | `audio-worker` (dentro) | Consumir C5, transcribir, publicar, borrar | 1 a la vez; `MULTI`; 100 % de ramas |
| `AofRewriteRequester` | `audio-worker` | Pedir `BGREWRITEAOF` con la cola vacía (P2 = A) | Ventana de 60 s |
| `SpeechEndpoint` | `audio-worker` | `POST /internal/v1/speech` | Bearer en tiempo constante; concurrencia 1 |
| `ModelGateway.transcribe` / `.synthesize` | `libs/model_gateway`, en `audio-worker` | Hablar con `model-whisper` y `model-tts` | URL internas; *timeouts* |
| `model-whisper`, `model-tts` | Pods de U2 (dentro) | Inferencia | Sin salida; `/tmp` en memoria |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Radio |
|---|---|---|---|
| `model-whisper` | Turnos de voz nuevos (error en segundos) | Turnos escritos, revisión, preguntas | Turnos de voz de ese intervalo |
| `model-tts` | «Escuchar audio» | Todo lo demás; la pregunta se lee en pantalla | Una acción |
| `audio-worker` | Transcripción y síntesis | Todo el flujo de texto (MUST) | Audios en cola (vuelven por reclamo o vencen) |
| Trabajador de `session-api` | Ingesta de voz y de texto | API y consola | Resultados llegan al reiniciar |
| Redis | Encolar voz y texto | Consultas de la consola | Turnos nuevos |

La voz es SHOULD: ningún flujo MUST depende de un componente de esta tabla salvo Redis y el trabajador,
que ya son de U4.

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso API de `session-api` | U3–U8 | Lectura en *streaming* con corte (sin picos de memoria acumulados); nada pesado en la API |
| Redis | U3 (limitador), U4, U8 | Prefijos `veridicus:audio` y `veridicus:transcripts`; *streams* vacíos tras procesar; `noeviction`; reescritura del AOF pedida por `audio-worker` |
| CPU de la máquina de desarrollo | `model-judge`, `model-embeddings` | `limits.cpu` de `model-whisper` (scalability-design §4) |
| `VERIDICUS_SPEECH_TOKEN` | `session-api` y `audio-worker` | Secret por referencia; solo esos dos pods lo montan |

## 4. Entrega a Infrastructure Design

- Un `Deployment` de `audio-worker` (1 réplica), raíz de solo lectura, sin volúmenes escribibles, etiqueta
  de datos sin anonimizar, puertos interno (síntesis) y de métricas.
- Subchart `model-tts` (Piper `es_*`) y ajustes de `model-whisper` (`cpu_threads = 4`, `limits.cpu` 4),
  ambos con `/tmp` `emptyDir` `medium: Memory` y `sizeLimit`.
- API y trabajador de `session-api` con `readOnlyRootFilesystem: true` y `/tmp` en memoria (P1 = A).
- Redis: `save ""`, `auto-aof-rewrite-min-size 16mb`, `maxmemory` con ≥ 128 MB para *streams*,
  `noeviction`, `BGREWRITEAOF` sin renombrar y PVC con espacio para el doble del AOF (P2 = A).
- `NetworkPolicy` de `audio-worker` (salida a Redis, `model-whisper`, `model-tts` y DNS; entrada desde
  `session-api` y Prometheus) y entrada de `model-tts` solo desde `audio-worker`.
- Topes de memoria medidos de performance-design §7 y `limits` con ≥ 20 % de margen.

## 5. Calidad, pruebas y textos (NFR2.1, NFR2.2, NFR13.1, NFR13.2, NFR14.1, NFR14.2, NFR14.3)

- **Dobles de prueba (NFR2.1).** `FakeWhisper` y `FakeTts` implementan el `Protocol` de C13 con retardo,
  vacío, error, *timeout* y texto configurables; Redis y PostgreSQL reales en contenedor; ninguna prueba
  de los niveles 0 y 1 descarga un modelo, usa GPU o un micrófono real.
- **Perfil CPU (NFR2.2).** La corrida de voz usa `values-cpu.yaml`; el perfil GPU es opcional y corre en
  su etapa separada.
- **Cobertura (NFR13.1, NFR13.2).** ≥ 80 % de líneas en `services/audio-worker`, en los módulos de voz de
  `services/session-api`, en los adaptadores de voz de `libs/model_gateway` y en `frontend`; 100 % de
  ramas con `.coveragerc-guards` en `audio_lifecycle.py`, en `AudioValidator` y en
  `VoiceUploadReader`, y en el `AofRewriteRequester` (decisión de este diseño, adicional a la regla del
  equipo).
- **Textos (NFR14.1).** Todos los literales visibles de la voz salen del catálogo de U1; la prueba de
  nivel 0 de U4 (literal fuera del catálogo) cubre los componentes de U9.
- **Accesibilidad (NFR14.2).** `vitest-axe` sobre el control de grabación en `idle`, `recording`,
  `ready`, `sending` y error, y sobre «Escuchar audio»; `@axe-core/playwright` en `voice.spec.ts` con 0
  violaciones `serious` o `critical`; teclado completo; región `aria-live="polite"` con los anuncios de
  BR1.2; estado con texto e icono (prueba en escala de grises).
- **Voz en español (NFR14.3).** Prueba de nivel 0 sobre `models.lock` (voz `es_*`) y, en la corrida de
  voz, 5 preguntas sintetizadas transcritas con Whisper con WER ≤ 20 %.
