# Decisiones de pila — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03. Las decisiones D1–D12 conservan
su número. Lo nuevo es D13 a D16 y NFR13.3. Cada fila dice si **se mantiene**, **cambia** o es **nuevo**.

**Insumos.**
- Flujos F1–F8 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1–BR9 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- De `inception/requirements-analysis/requirements.md` (requirements, revisión 3): la pila fijada
  (Whisper ligero en CPU), FR10.2, FR10.4, FR15.1, NFR2, NFR3, NFR13 y NFR14. Además, VE-06, VE-08 y VE-09
  de la adenda 02.
- De `inception/contract-design/contract-summary.md` (contract-summary, revisión 3): C1, C5, C8, C13,
  C14, C16 y C25, y la arista voice → incoherence-analyzer de `inception/units-generation/unit-of-work-dependency.md`.
- P1 = A y P2 = A de `nfr-requirements-questions.md`, y `security-requirements.md`.
- Lo ya decidido por otras unidades:
  - U2: servidor de Whisper `faster-whisper` compatible con OpenAI, `models.lock`, Redis, volúmenes.
  - U3 y U4: base de `session-api`, colas y tubería de corridas.
  - U11: puerto `ModelGateway` y escáner de vocabulario.

Lo que ya fijan `team.md`, U2, U3, U4 y U11 no se repite: Python 3.12, FastAPI, Pydantic v2,
`redis-py`, `httpx` con verificación de URL interna, `jsonschema` para C5, `uv`, `pytest` + Hypothesis,
mypy estricto, Ruff, import-linter, React con TypeScript estricto, TanStack Query, Vitest, Playwright,
`@axe-core/playwright`, `vitest-axe` y Problem Details desde `libs/`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | se mantiene | Modelo de Whisper | **`base` multilingüe** convertido a CTranslate2 **int8** (`faster-whisper`), con `language = es`, `temperature = 0`, `beam_size = 1`, `vad_filter = true` y `condition_on_previous_text = false` | `tiny` int8 (más errores en nombres y fechas); `small` int8 (fuera de «ligero», arriesga 8–12 s); `beam_size = 5` | P2 = A. Voraz y sin condicionar al texto previo: más rápido, repetible y con menos bucles de alucinación. El VAD evita texto inventado en silencio | NFR3.1, NFR3.2, NFR4.1–NFR4.3 |
| D2 | cambia | Servidor de Whisper | El de U2: `faster-whisper` detrás de `/v1/audio/transcriptions` (C14), con `cpu_threads = 4`, una transcripción a la vez, sin registro del cuerpo y `/tmp` en memoria. **El servidor no cancela la transcripción cuando el cliente corta por *timeout*** (cierra R-05): la ranura queda ocupada hasta terminar, y lo cubre el reclamo de 120 s. | — (lo decidió U2) | Encaja en C14 sin adaptador propio | NFR8.1, NFR8.5, NFR10.2, NFR3.15 |
| D3 | cambia | Motor de TTS | **Piper** (VITS en ONNX, CPU) con una voz en español de calidad `medium`, preferentemente `es_MX` (p. ej. `es_MX-ald-medium`), por cercanía al español de Colombia. Corre con 2 hilos y da WAV mono PCM 16 bits a 22 050 Hz. El envoltorio HTTP de Piper en el pod `model-tts` lo cierra **Infrastructure Design** | eSpeak NG (robótico); Coqui XTTS-v2 (pesado en CPU, licencia no comercial); MMS-TTS (CC-BY-NC y código de `transformers`); Web Speech API (terceros, AUTONOMIA-04) | Ligero en CPU (p95 ≤ 5 s para 400 caracteres), voz natural en español, modelo ONNX sin código ejecutable, todo dentro del clúster | NFR3.12, NFR8.3, NFR1.3, NFR10.10 |
| D4 | cambia | Camino de la síntesis | **1. ConsoleApi (`session-api`):** comprueba rol y dueño, el estado de la sesión y `is_observation_approved` (U8). **2. Llamada interna:** envía `{observation_id, tema, template_version}` a `POST /internal/v1/speech` de `audio-worker` (SpeechProcessing). **3. `audio-worker`:** compone la frase con la plantilla, la valida (D15) y llama a `ModelGateway.synthesize` contra `model-tts` | `session-api` llama directo al TTS (saca la síntesis de `audio-worker`); petición por Redis; síntesis en el navegador | Respeta que SpeechProcessing vive en `audio-worker` y que solo `audio-worker` habla con los servidores de voz. Como la frase la compone quien la pronuncia, `session-api` no puede enviar un texto libre | NFR10.8, NFR10.9, NFR10.22, NFR3.12 |
| D5 | cambia | Transporte y tamaño del audio | Base64 dentro de `AudioToTranscribe` (C5), con `audio_max_bytes` = 6 000 000 y `audio_base64_max_chars` = 8 000 000, y borrado con `XDEL` al confirmar. Un audio más grande o más largo recibe `413` `limits.exceeded` antes de encolar | Volumen temporal con referencia (P1 B); 4 MB (P1 C) | P1 = A; cierra la pregunta abierta de C5. `413` por la regla de U1 | NFR10.1, NFR10.3, NFR8.7 |
| D6 | se mantiene | Grabación y codificación en la consola | `MediaRecorder` en el formato nativo, en memoria. Al detener, `decodeAudioData` y `OfflineAudioContext` a 16 kHz mono, y codificación a WAV PCM 16 bits en un **Web Worker** propio, sin dependencias | Enviar WebM/Opus (C1 solo admite WAV o MP3); `ffmpeg.wasm` (≈ 30 MB); `AudioWorklet` | BR1.4; el Web Worker deja libre el hilo principal | NFR3.10, NFR10.5 |
| D7 | cambia | Validación y duración del audio en `session-api` | **Lectura.** Por partes, con corte en el máximo y sin *spool* a disco. **WAV.** Se recorren los *chunks* con `wave` y `struct` de la biblioteca estándar; la duración sale de los **bytes reales** del bloque `data`, nunca del tamaño declarado. **MP3.** Un lector de tramas propio en Python puro (cabecera MPEG por trama, muestras por trama y tasa) suma la duración de **todas** las tramas, también con tasa variable. Se rechaza si hay más de 64 KiB que no son tramas. **Cabecera.** Se comprueba que sea real | `mutagen` (estima la duración de un MP3 de tasa variable desde la cabecera Xing, que se puede falsear, E31); `ffprobe` (binario nativo y superficie de ataque); fiarse de `Content-Type` | BR2.3: la duración se mide sobre el audio y no se decodifica en la API | NFR10.1, NFR10.2, NFR3.4 |
| D8 | cambia | Plazos y colas | Plazo de audio proporcional (base 360 s, tope 1 800 s), reclamo a 120 s, 2 entregas como máximo, deduplicación con clave de Redis con TTL y `XDEL` de audio y de transcripción. `attempt` siempre vale 1 | Plazo fijo; 3 entregas (la tercera no cabe en 300 s, R-03); deduplicar en memoria | Mismo patrón que U4, ajustado al *timeout* de Whisper | NFR3.5, NFR10.14, NFR8.9 |
| D9 | cambia | Persistencia de Redis y audio | Un solo Redis (U2) con `save ""`, `auto-aof-rewrite-percentage 100` y `auto-aof-rewrite-min-size 16mb`. El rastro en el AOF queda declarado, acotado y probado | Redis aparte sin persistencia para `veridicus:audio` (otro `StatefulSet`, `Secret` y `NetworkPolicy`); queda disponible por PR | El AOF está en un PVC dentro del clúster y la cota es comprobable | NFR10.4 |
| D10 | se mantiene | Procesos de `audio-worker` | Un solo proceso: bucle consumidor de C5 (un audio a la vez) y un servidor FastAPI + Uvicorn en un hilo, en el puerto interno, con `/healthz`, `/readyz`, `/metrics` y `/internal/v1/speech` (concurrencia 1) | Dos procesos o dos *Deployments* | Una sola imagen y pocas piezas; la síntesis es rara y corta | NFR8.5, NFR10.17 |
| D11 | cambia | Dobles de prueba | Whisper y TTS *fakes* deterministas que implementan `transcribe` y `synthesize` del `Protocol` de C13, con retardo, vacío, error, *timeout* y texto configurable. En nivel 3, el micrófono *fake* de Chromium con un WAV sintético | Grabar voces reales | `team.md`; NFR12 | NFR2.1, NFR12.1 |
| D12 | cambia | Clips sintéticos | `evaluation/voice/generate.py` sintetiza con la voz Piper fijada turnos del conjunto sintético de U11 y textos sintéticos, más 3 clips de silencio y ruido. Escribe `evaluation/voice/manifest.json` con el texto de origen y el `sha256`. Los clips se regeneran; solo se versionan los pequeños de prueba | Clips grabados por personas | NFR12; la referencia del WER es el texto de origen | NFR4.1, NFR4.4, NFR12.1 |
| D13 | nuevo | Métodos de voz de `ModelGateway` (resuelve NFR-U11-11) | **Puerto.** `transcribe` y `synthesize` se quedan en `libs/model_gateway/port.py` como los declara C13 v2.0.0 (SHOULD, solo locales). **Quién los escribe.** U9, en B9: añade los dos métodos al puerto y escribe `libs/model_gateway/speech.py` (`Transcript`), el adaptador `libs/model_gateway/adapters/speech_local.py` (C14, solo URL internas) y los *fakes*, y actualiza en el mismo PR los *fakes* de U11. **Qué entrega U11.** B11 entrega el puerto solo con `generate`. **Tipado.** `audio-worker` declara su dependencia contra un `Protocol` con solo los dos métodos de voz | PR de U1 sobre C13 (innecesario: C13 ya los declara y U1 solo es dueño de los tipos de `model_calls.py`, que no cambian); adaptadores propios dentro de `services/audio-worker` (sacan la voz del puerto que la arista voice → incoherence-analyzer y C14 asignan a ModelGateway) | Sigue C13, C14 y la arista aprobada, y la convención de C1 de que lo SHOULD existe solo cuando se construye su unidad. El PR de U9 no cambia `generate` ni los tipos compartidos | NFR1.2, NFR1.4, NFR2.1, NFR13.1 |
| D14 | nuevo | Almacén del audio conservado | Archivos en el PVC de audio de `session-api` (U2), en `VERIDICUS_AUDIO_DIR/audio/` con modo `0700`. Cada archivo es `0600`, se llama por `audio_id` y lleva su `sha256` en TurnAudio. Archivo antes que fila, con barrido de huérfanos al arrancar. Cuota propia por recuento del proceso. Sin cifrado en reposo | Guardar el audio en PostgreSQL (`bytea`: infla la base y sus copias); guardarlo en Redis (sin retención); cifrado con clave en un Secret (sin KMS en el MVP; la clave quedaría en el mismo nodo) | Mismo patrón que los reportes de U7 y que A-2. El borrado es del Job de retención | NFR10.24, NFR10.27, NFR8.12 |
| D15 | nuevo | Composición y validación de la frase de voz | `contracts/integrity/clarification-speech.v1.yaml`: versión y plantilla con un solo `{tema}`. En `audio-worker`, el módulo puro `speech_text.py` compone la frase y aplica, en este orden, la versión, la regla de DT23 (sin la contradicción, sin «antes dijo», sin citas), el escáner de C8 de `libs/integrity_policy` (sin `literal_sources`, porque la frase no lleva texto literal) y la longitud | Validar en `session-api` (quien pronuncia no comprobaría lo que pronuncia); texto libre de U8 sin plantilla (P7 de Functional Design) | VE-09 y BR5.5–BR5.6: lo que llega al TTS es solo lo aprobado | NFR10.22 |
| D16 | nuevo | Espera en orden de las corridas | RunPublicationHold en PostgreSQL de `session-api`. Al aceptar un turno escrito con un turno de voz anterior en `transcribing`, se crea la espera. La ingesta del `TranscriptResult`, el supervisor y la retirada la liberan en su propia transacción, que publica en C2 tras confirmar. El orden de bloqueo es sesión → ronda (`project.md`) | Publicar sin esperar (P5 A: las corridas verían el relato desordenado); espera en memoria (se pierde al reiniciar) | P5 = B; FD-U9-07 | NFR3.16, NFR10.26 |

## 2. Configuración

**Cifras de C25 (NFR-U9-02).** Se cargan con `limits.load`. Una variable `VERIDICUS_<CIFRA>` solo puede
bajarlas; si intenta subirlas, el servicio no arranca.

| Cifra de C25 | Valor | Unidad | Servicio que la usa |
|---|---|---|---|
| `audio_max_bytes` | 6 000 000 | `bytes` | `session-api` |
| `audio_max_seconds` | 120 | `s` | `session-api`, consola |
| `audio_base64_max_chars` | 8 000 000 | `chars` | `session-api`, `audio-worker` |
| `voice_deadline_base_s` / `voice_deadline_max_s` | 360 / 1 800 | `s` | `session-api` |
| `transcription_timeout_s` | 90 | `s` | `audio-worker` |
| `audio_claim_idle_ms` | 120 000 | `ms` | `audio-worker` |
| `audio_max_deliveries` | 2 | `deliveries` | `audio-worker` |
| `voice_key_ttl_s` | 1 920 | `s` | `session-api`, `audio-worker` |
| `tts_timeout_s` | 12 | `s` | `audio-worker` |
| `speech_route_timeout_s` | 15 | `s` | `session-api` |
| `speech_text_max_chars` | 400 | `chars` | `audio-worker` |
| `speech_audio_max_bytes` | 4 194 304 | `bytes` | `session-api`, `audio-worker` |
| `audio_store_max_bytes` | 2 147 483 648 | `bytes` | `session-api` |

**Otros ajustes (prefijo `VERIDICUS_`).**

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_SPEECH_URL` | — | Obligatoria; solo URL interna (NFR1.2) | `session-api` |
| `VERIDICUS_SPEECH_TOKEN` | — (Secret `veridicus-speech-token`, por referencia) | Obligatorio; ≥ 32 bytes | `session-api`, `audio-worker` |
| `VERIDICUS_AUDIO_DIR` | — | Obligatorio; directorio del PVC de audio, escribible | `session-api` |
| `VERIDICUS_WHISPER_URL`, `VERIDICUS_TTS_URL` | — | Obligatorias; solo URL internas (BR6.2) | `audio-worker` |
| `VERIDICUS_WHISPER_MODEL`, `VERIDICUS_WHISPER_MODEL_SHA256` | `base`, — | Nombre no vacío; 64 hexadecimales, iguales a `models.lock` | `audio-worker` |
| `VERIDICUS_SPEECH_TEMPLATE` | `contracts/integrity/clarification-speech.v1.yaml` en la imagen | Presente, versión válida y un solo `{tema}` | `audio-worker` |

Salen de la revisión 1: `VERIDICUS_VOICE_MAX_BYTES`, `VERIDICUS_VOICE_MAX_SECONDS`,
`VERIDICUS_AUDIO_DEADLINE_*`, `VERIDICUS_WHISPER_TIMEOUT_SECONDS`, `VERIDICUS_TTS_TIMEOUT_SECONDS`,
`VERIDICUS_SPEECH_TIMEOUT_SECONDS`, `VERIDICUS_AUDIO_RECLAIM_IDLE_SECONDS`, `VERIDICUS_QUEUE_MAX_DELIVERIES`,
`VERIDICUS_TRANSCRIPT_MAX_CHARS` y `VERIDICUS_TTS_MAX_CHARS`. Sus cifras pasan a C25.

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | cambia | Todo U9 se prueba en CPU sin modelos reales en los niveles 0 y 1. | Whisper y TTS son *fakes* de `transcribe` y `synthesize` (D11), con Redis y PostgreSQL reales en contenedor. Ninguna prueba de los niveles 0 y 1 descarga un modelo, exige GPU ni usa un micrófono real. |
| NFR2.2 | se mantiene | Las metas de U9 se cumplen en el perfil CPU. | NFR3.1–NFR3.3, NFR3.12, NFR3.15 y NFR4.1–NFR4.4 se miden con `values-cpu.yaml`. El perfil GPU es opcional y corre a demanda en su etapa separada. |
| NFR13.1 | cambia | Cobertura de líneas. | ≥ 80 %, medido en la CI y bloqueante, en: `services/audio-worker`, los módulos de voz de `services/session-api`, `libs/model_gateway/speech.py`, `libs/model_gateway/adapters/speech_local.py` y `frontend`. |
| NFR13.2 | cambia | 100 % de ramas en los módulos que deciden qué audio o qué voz sale. | U9 no tiene módulos guardia de la lista de `team.md`. Por decisión de esta etapa (adicional, nunca en lugar de la regla del equipo), llevan `--cov-branch` con `fail_under = 100`: <ul><li>`audio_lifecycle.py` (NFR10.3, NFR10.14, NFR10.15);</li><li>la decisión de cancelación (NFR10.25);</li><li>`speech_text.py` (NFR10.22);</li><li>la validación y la duración del audio de `session-api` (NFR10.1);</li><li>la liberación de las esperas (NFR10.26).</li></ul> |
| NFR13.3 | nuevo | Las fronteras de import se hacen cumplir (D13, NFR1.4, NFR10.24). | Contratos de import-linter: <ul><li>el adaptador de voz no importa el anonimizador;</li><li>`audio-worker` no importa el módulo de TurnAudio ni `libs.anonymizer`;</li><li>los módulos de ConsoleApi no importan TurnAudio salvo el puerto de escritura de la ingesta.</li></ul> Cada contrato tiene un control negativo. |
| NFR14.1 | cambia | Textos visibles en español y del catálogo. | Todos salen del catálogo de U1, y la prueba de nivel 0 de U4 (literal visible fuera del catálogo) cubre los componentes de U9: <ul><li>«Grabar», «Detener», «Enviar», «Grabando…», «Procesando audio…», «Turno por voz (transcripción automática)», «Escuchar audio», «Grabar de nuevo» y «Escribir el turno»;</li><li>los avisos de BR1.1, BR1.3, BR4.2, BR5.3 y BR8.1;</li><li>los textos de las maquetas de FD-U9-14.</li></ul> La frase de voz sale de la plantilla versionada, no del catálogo. |
| NFR14.2 | se mantiene | Accesibilidad de la voz (BR1.2, BR7.1). | **Automática:** `vitest-axe` sobre el control de grabación (en `idle`, `recording`, `ready`, `sending` y error) y sobre «Escuchar audio», y `@axe-core/playwright` en `frontend/e2e/voice.spec.ts`; 0 violaciones `serious` o `critical`. **Teclado:** grabar, detener, enviar, descartar y escuchar se hacen solo con teclado (Tab, Enter y Espacio). **Anuncios:** la región `aria-live="polite"` anuncia el inicio y el fin de la grabación, los 15 s restantes y el corte a 120 s. **Color:** el estado de grabación y el de error llevan texto e icono, no solo color. |
| NFR14.3 | cambia | La voz de la aclaración habla español. | La voz fijada es `es_*` (prueba de nivel 0 sobre `models.lock`). La corrida de voz transcribe con Whisper 5 frases de la plantilla sintetizadas y exige WER ≤ 20 % frente a su texto. |

## 4. Dependencias nuevas de U9

- `services/audio-worker`: `fastapi`, `uvicorn`, `pydantic-settings`, `redis`, `httpx`, `jsonschema`,
  `pyyaml`, `prometheus-client`, y `libs/model_gateway` y `libs/integrity_policy`; en desarrollo, las de U3.
- `services/session-api`: ninguna en ejecución (el lector de tramas MP3 es propio; sale `mutagen`).
- `libs/model_gateway`: el adaptador de voz con `httpx`, sin otras dependencias.
- `frontend`: ninguna en ejecución (el codificador WAV es propio).
- `evaluation/voice`: `jiwer` (WER) y el cliente HTTP de la voz Piper del clúster o su binario fijado.

Todas van fijadas en el lockfile de cada servicio, con `pip-audit` y `npm audit` en la CI.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y configuración (nivel 0) | `uv run --directory services/audio-worker pytest -m "not integration and not perf"`, y lo mismo en `services/session-api` y `libs/model_gateway` | Verde |
| Ramas de los módulos de NFR13.2 | `uv run --directory services/audio-worker pytest --cov-branch --cov-config=.coveragerc-guards`, y lo mismo en `services/session-api` | 100 % (NFR13.2) |
| Fronteras | `uv run --directory services/audio-worker lint-imports`, y lo mismo en `services/session-api` | 0 contratos rotos (NFR1.4, NFR13.3) |
| Integración (nivel 1) | `uv run --directory services/audio-worker pytest -m integration`, y lo mismo en `services/session-api` | Verde (NFR10.1–NFR10.27, NFR11.1, NFR11.2, NFR8.9, NFR8.12) |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf -k voice` | NFR3.4, NFR3.12 (sobrecarga), NFR8.4 |
| Consola | `npm --prefix frontend run test -- --coverage`, `npm --prefix frontend run lint` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas; NFR1.3 |
| E2E de voz (nivel 3) | `npx --prefix frontend playwright test e2e/voice.spec.ts` | NFR3.9–NFR3.11, NFR3.14, NFR10.5, NFR14.2 |
| Políticas de manifiestos | `kyverno test deploy/policies/tests/` (casos de `audio-worker`) | NFR1.1, NFR10.2: cada control negativo falla como se espera |
| Audio sintético | `scripts/check-synthetic-audio.sh` | 0 archivos fuera del manifiesto (NFR12.1) |
| Corrida de voz (nivel 2, fuera de la CI) | `uv run --directory evaluation python -m voice.run --profile cpu --report out/voice.json` | NFR3.1–NFR3.3, NFR3.12, NFR3.15, NFR3.16, NFR4.1–NFR4.4, NFR8.1–NFR8.3, NFR8.6, NFR8.8, NFR8.10, NFR14.3 |
| Salida de `audio-worker` (manual, lectura) | `kubectl -n veridicus exec deploy/veridicus-audio-worker -- curl -m 5 https://example.org` | Código ≠ 0 (NFR1.1) |
| Humo (nivel 3) | `scripts/smoke.sh <url-base>` | Código 0; `audio-worker` listo (NFR3.14) |
| Tipos y *lint* | `uv run --directory services/audio-worker mypy --strict .` y `uv run --directory services/audio-worker ruff check .` | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Whisper `base` en CPU no llega a 12 s por 30 s de audio, sobre todo con el juez en paralelo | Voraz, int8 y VAD, y NFR3.15 lo mide. Si falla, es un hallazgo que se resuelve por PR (`cpu_threads`, `limits.cpu`, perfil GPU para la demostración), nunca subiendo la meta |
| Whisper transcribe peor los nombres propios y el habla real que los clips de Piper | El WER de NFR4.1 mide clips limpios: detecta regresiones, no promete nada sobre audio real. Lo cubren el rótulo «transcripción automática» y el turno escrito |
| Whisper inventa texto en silencio o ruido | VAD activo y NFR4.2; un texto vacío es un error, nunca un turno |
| El PR de B9 sobre `libs/model_gateway` choca con U11 | D13: no cambia `generate` ni los tipos de U1, y actualiza los *fakes* de U11 en el mismo PR |
| Licencias de Piper y de la voz | El motor original es MIT y su sucesor (`piper1-gpl`) es GPL-3.0; cada voz tiene su licencia en su `MODEL_CARD`. Se verifican antes de fijarlas en `models.lock`; si una voz no permite el uso académico, se elige otra `es_*` |
| El audio queda en el AOF hasta la reescritura | Cota declarada y probada (NFR10.4); la alternativa D9 queda disponible por PR |
| El audio conservado sin cifrar | Riesgo aceptado (`security-requirements.md` §5) |
| El navegador no permite `MediaRecorder` o niega el micrófono | Aviso de BR1.1, y el turno escrito sigue disponible; la voz es SHOULD |
