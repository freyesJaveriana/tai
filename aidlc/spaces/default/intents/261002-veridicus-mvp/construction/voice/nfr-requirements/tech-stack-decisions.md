# Decisiones de pila — U9 voice

**Insumos.** Flujos F1–F4 de `functional-design/functional-spec.md` (functional-spec) y reglas BR1–BR7
de `functional-design/rules.md` (rules); pila fijada (Whisper ligero en CPU), FR10.2, FR10.4 y NFR2,
NFR3, NFR13 y NFR14 de `inception/requirements-analysis/requirements.md` (requirements); C1, C5, C13,
C14 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`; `security-requirements.md`; las decisiones ya aprobadas de U2
(servidor de Whisper `faster-whisper` compatible con OpenAI, D2; `models.lock`, D7; Redis, D6), de U3 y
de U4 (base de `session-api`, ModelGateway, colas, D10–D14).

Lo que ya fijan `team.md`, U2, U3 y U4 no se repite: Python 3.12, FastAPI, Pydantic v2, `redis-py`,
`httpx` con verificación de URL interna (D10 de U4), `jsonschema` para C5 (D9 de U4), `uv`, `pytest` +
Hypothesis, mypy estricto, Ruff, import-linter, React con TypeScript estricto, TanStack Query, Vitest,
Playwright, `@axe-core/playwright` y `vitest-axe`, Problem Details desde `libs/`.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Modelo de Whisper | **`base` multilingüe** convertido a CTranslate2 **int8** (`faster-whisper`), `language = es`, `temperature = 0`, `beam_size = 1`, `vad_filter = true`, `condition_on_previous_text = false` | `tiny` int8 (más errores en nombres y fechas); `small` int8 (fuera de «ligero», arriesga 8–12 s); `beam_size = 5` | P2 = A. Voraz y sin condicionar al texto previo: más rápido, repetible y con menos bucles de alucinación; el VAD evita texto inventado en silencio | NFR3.1, NFR3.2, NFR4.1–NFR4.3 |
| D2 | Servidor de Whisper | El de U2 (D2): `faster-whisper` detrás de `/v1/audio/transcriptions` (C14), `cpu_threads = 4`, una transcripción a la vez, sin registro del cuerpo, `/tmp` en memoria | — (lo decidió U2) | Encaja en C14 sin adaptador propio | NFR8.1, NFR8.5, NFR10.2 |
| D3 | Motor de TTS | **Piper** (VITS en ONNX, CPU) con una voz en español de calidad `medium`, preferentemente `es_MX` (p. ej. `es_MX-ald-medium`), por cercanía al español de Colombia; 2 hilos; salida WAV mono PCM 16 bits a 22 050 Hz. El servidor concreto (envoltorio HTTP de Piper en el pod `model-tts`) lo cierra **Infrastructure Design** | eSpeak NG (muy ligero pero robótico: dificulta leer la pregunta al compareciente); Coqui XTTS-v2 (pesado y lento en CPU, licencia no comercial); MMS-TTS de Meta (licencia CC-BY-NC y código de `transformers`); Web Speech API del navegador (voces en línea de terceros, AUTONOMIA-04, y voz distinta en cada navegador) | Ligero en CPU (p95 ≤ 5 s para 300 caracteres), voz natural en español, modelo ONNX sin código ejecutable, todo dentro del clúster | NFR3.12, NFR8.3, NFR1.3, NFR10.10 |
| D4 | Camino de la síntesis | ConsoleApi (`session-api`) comprueba dueño y aprobación y llama por HTTP a la ruta interna `POST /internal/v1/speech` de `audio-worker` (SpeechProcessing), que llama a `ModelGateway.synthesize` contra `model-tts` | `session-api` llama directo al TTS (saca la síntesis de SpeechProcessing y de `audio-worker`, contra la ubicación aprobada en Units Generation); petición y respuesta por Redis (una ruta `GET` síncrona esperando una cola); síntesis en el navegador | Respeta que SpeechProcessing vive en `audio-worker` y la regla de U2 de que solo `audio-worker` habla con los servidores de voz; el salto extra cuesta milisegundos | NFR10.8, NFR10.9, NFR3.12 |
| D5 | Transporte y tamaño del audio | Base64 dentro de `AudioToTranscribe` (C5), `VERIDICUS_VOICE_MAX_BYTES = 6000000`, borrado con `XDEL` al confirmar; más grande → `422` antes de encolar | Volumen temporal con referencia (P1 B: volumen compartido entre pods y su borrado); 4 MB (P1 C: corta grabaciones de 120 s en MP3 de alta tasa) | P1 = A; cierra la pregunta abierta de C5 | NFR10.1, NFR10.3, NFR8.7 |
| D6 | Grabación y codificación en la consola | `MediaRecorder` en el formato nativo del navegador, en memoria; al detener, `decodeAudioData` y `OfflineAudioContext` a 16 kHz mono, y codificación a WAV PCM 16 bits en un **Web Worker** propio (≈ 60 líneas, sin dependencia) | Enviar el formato nativo (WebM/Opus: C1 solo admite WAV o MP3); `ffmpeg.wasm` (≈ 30 MB); captura con `AudioWorklet` (más código propio) | BR1.4; el Web Worker mantiene libre el hilo principal | NFR3.10, NFR10.5 |
| D7 | Validación del audio en `session-api` | Lectura del cuerpo por partes con corte en el máximo y sin *spool* a disco; WAV con `wave` de la biblioteca estándar; MP3 con `mutagen` (Python puro) para la duración; comprobación de cabecera real | `ffprobe` en `session-api` (binario nativo y superficie de ataque); fiarse de `Content-Type` | BR2.3 sin decodificar el audio en la API | NFR10.1, NFR10.2, NFR3.4 |
| D8 | Plazos y colas | Plazo de audio proporcional (base 300 s, tope 1 800 s); reclamo a 120 s; 3 entregas; deduplicación con clave de Redis con TTL; `XDEL` de audio y de transcripción | Plazo fijo; deduplicar en memoria | Mismo patrón que U4, ajustado al *timeout* de Whisper | NFR3.5, NFR10.14, NFR8.9 |
| D9 | Persistencia de Redis y audio | Un solo Redis (U2 D6) con `save ""` y `auto-aof-rewrite-min-size 16mb`; el rastro en el AOF queda declarado y probado (NFR10.4) | Redis aparte sin persistencia para `veridicus:audio` (otro `StatefulSet`, `Secret` y `NetworkPolicy`; queda disponible por PR si se prefiere cerrar el riesgo) | El AOF está en un PVC dentro del clúster y la reescritura es frecuente con mensajes de audio | NFR10.4 |
| D10 | Procesos de `audio-worker` | Un proceso: bucle consumidor de C5 (un audio a la vez) y un servidor FastAPI + Uvicorn en un hilo, en el puerto interno, con `/healthz`, `/readyz`, `/metrics` y `/internal/v1/speech` (concurrencia 1) | Dos procesos o dos *Deployments* | Una sola imagen y pocas piezas; la síntesis es rara y corta | NFR8.5, NFR10.17 |
| D11 | Dobles de prueba | Whisper y TTS *fakes* deterministas que implementan el `Protocol` de C13 (con retardo, vacío, error, *timeout* y texto configurable); micrófono *fake* de Chromium con un WAV sintético en nivel 3 | Grabar voces reales | team-practices; NFR12 | NFR2.1, NFR12.1 |
| D12 | Clips sintéticos | `evaluation/voice/generate.py` sintetiza con la voz Piper fijada los turnos del Golden Dataset y textos sintéticos, más 3 clips de silencio y ruido, y escribe `evaluation/voice/manifest.json` (texto de origen y `sha256`); los clips se regeneran, no se versionan salvo los pequeños de prueba | Clips grabados por personas | NFR12; la referencia de WER es el texto de origen | NFR4.1, NFR12.1 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_VOICE_MAX_BYTES` | 6000000 | Entero entre 1 y 8 000 000 | `session-api` |
| `VERIDICUS_VOICE_MAX_SECONDS` | 120 | Entero igual a 120 en el MVP (P1 de Functional Design) | `session-api` |
| `VERIDICUS_AUDIO_DEADLINE_BASE_SECONDS`, `_MAX_SECONDS` | 300, 1800 | Base > *timeout* de Whisper + reclamo; máximo ≥ base | `session-api` |
| `VERIDICUS_SPEECH_URL` | — | Obligatoria; solo URL interna (NFR1.2) | `session-api` |
| `VERIDICUS_SPEECH_TIMEOUT_SECONDS` | 12 | > `VERIDICUS_TTS_TIMEOUT_SECONDS` | `session-api` |
| `VERIDICUS_SPEECH_TOKEN` | — (Secret por referencia) | Obligatorio; ≥ 32 bytes | `session-api`, `audio-worker` |
| `VERIDICUS_WHISPER_URL`, `VERIDICUS_TTS_URL` | — | Obligatorias; solo URL internas (BR6.2) | `audio-worker` |
| `VERIDICUS_WHISPER_MODEL`, `VERIDICUS_WHISPER_MODEL_SHA256` | `base`, — | Nombre no vacío; 64 hexadecimales iguales a `models.lock` | `audio-worker` |
| `VERIDICUS_WHISPER_TIMEOUT_SECONDS` | 90 | Entre 10 y la base del plazo de audio | `audio-worker` |
| `VERIDICUS_TTS_TIMEOUT_SECONDS` | 10 | Entero positivo | `audio-worker` |
| `VERIDICUS_AUDIO_RECLAIM_IDLE_SECONDS` | 120 | > *timeout* de Whisper | `audio-worker` |
| `VERIDICUS_QUEUE_MAX_DELIVERIES` | 3 | El de U4 | ambos |
| `VERIDICUS_TRANSCRIPT_MAX_CHARS`, `VERIDICUS_TTS_MAX_CHARS` | 2000, 300 | Iguales al límite del turno de U4 y de la pregunta de U8 | `audio-worker` |

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U9 se prueba en CPU sin modelos reales en los niveles 0 y 1. | Whisper y TTS son *fakes* del `Protocol` de C13; Redis y PostgreSQL reales en contenedor. Ninguna prueba de los niveles 0 y 1 descarga un modelo, exige GPU ni usa un micrófono real. |
| NFR2.2 | Las metas de U9 se cumplen en el perfil CPU. | NFR3.1–NFR3.3, NFR3.12 y NFR4.1–NFR4.3 se miden con `values-cpu.yaml`; el perfil GPU (modelos de Whisper mayores) es opcional y corre a demanda en su etapa separada. |
| NFR13.1 | Cobertura de líneas. | ≥ 80 % en `services/audio-worker`, en los módulos de voz de `services/session-api`, en los adaptadores `transcribe`/`synthesize` de `libs/model_gateway` y en `frontend`, medido en la CI y bloqueante. |
| NFR13.2 | 100 % de ramas en el ciclo de vida del audio. | U9 no tiene módulos guardia de la lista de team-practices; por decisión de esta etapa (adicional, nunca en lugar de la regla del equipo) `services/audio-worker/.../worker/audio_lifecycle.py` (resultado → `XACK` + `XDEL` + deduplicación, NFR10.3, NFR10.14, NFR10.15) y la validación del audio de `session-api` (NFR10.1) llevan `--cov-branch` con `fail_under = 100`. |
| NFR14.1 | Textos visibles en español y del catálogo. | «Grabar», «Detener», «Enviar», «Grabando…», «Procesando audio…», «Turno por voz (transcripción automática)», «Escuchar audio» y los avisos de BR1.1, BR1.3, BR4.2 y BR5.3 salen del catálogo de U1; la prueba de nivel 0 de U4 (literal visible fuera del catálogo) cubre los componentes de U9. |
| NFR14.2 | Accesibilidad de la voz (BR1.2, BR7.1). | `vitest-axe` sobre el control de grabación (en `idle`, `recording`, `ready`, `sending` y error) y el botón «Escuchar audio»; `@axe-core/playwright` en `frontend/e2e/voice.spec.ts`: 0 violaciones `serious` o `critical`. Grabar, detener, enviar, descartar y escuchar se hacen solo con teclado (Tab, Enter y Espacio); la región `aria-live="polite"` anuncia «Grabación iniciada», «Grabación detenida», los 15 s restantes y el corte a 120 s; el estado de grabación y el de error llevan texto e icono, no solo color (prueba con la paleta en escala de grises). |
| NFR14.3 | La voz de la pregunta habla español. | La voz fijada es `es_*` (prueba de nivel 0 sobre `models.lock`); la corrida de voz transcribe con Whisper 5 preguntas sintetizadas y exige WER ≤ 20 % frente a su texto (comprueba voz e idioma). |

## 4. Dependencias nuevas de U9

- `services/audio-worker`: `fastapi`, `uvicorn`, `pydantic-settings`, `redis`, `httpx`, `jsonschema`,
  `prometheus-client`; las de desarrollo de U3.
- `services/session-api`: añade `mutagen`.
- `libs/model_gateway`: adaptadores `transcribe` y `synthesize` con `httpx`; sin otras dependencias.
- `frontend`: ninguna en ejecución (el codificador WAV es propio); en desarrollo, las de U4.
- `evaluation/voice`: `jiwer` (WER) y el cliente HTTP de la voz Piper del clúster o su binario fijado.

Todas fijadas en el lockfile de cada servicio; `pip-audit` y `npm audit` en la CI (team-practices).

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y configuración (nivel 0) | `uv run --directory services/audio-worker pytest -m "not integration and not perf"` y lo mismo en `services/session-api` y `libs/` | Verde |
| Ramas del ciclo de vida del audio | `uv run --directory services/audio-worker pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1) | `uv run --directory services/audio-worker pytest -m integration` y lo mismo en `services/session-api` | Verde (NFR10.1–NFR10.9, NFR10.14–NFR10.19, NFR8.9) |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf -k voice` | NFR3.4, NFR3.12 (sobrecarga), NFR8.4 |
| Consola | `npm --prefix frontend run test -- --coverage`, `npm --prefix frontend run lint` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas; NFR1.3 |
| E2E de voz (nivel 3) | `npx --prefix frontend playwright test e2e/voice.spec.ts` | NFR3.9–NFR3.11, NFR3.14, NFR10.5, NFR14.2 |
| Políticas de manifiestos | `kyverno test deploy/policies/tests/` (casos de `audio-worker`) | NFR1.1, NFR10.2: cada control negativo falla como se espera |
| Audio sintético | `scripts/check-synthetic-audio.sh` | 0 archivos fuera del manifiesto (NFR12.1) |
| Corrida de voz (nivel 2, fuera de la CI) | `uv run --directory evaluation python -m voice.run --profile cpu --report out/voice.json` | NFR3.1–NFR3.3, NFR3.12, NFR4.1–NFR4.4, NFR5.1, NFR8.1–NFR8.3, NFR8.6, NFR8.8, NFR8.10, NFR14.3 |
| Egreso de `audio-worker` (manual) | `kubectl -n veridicus exec deploy/veridicus-audio-worker -- curl -m 5 https://example.org` | Código ≠ 0 (NFR1.1) |
| Humo (nivel 3) | `scripts/smoke.sh <url-base>` | Código 0; `audio-worker` listo (NFR3.14) |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en `services/audio-worker` | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Whisper `base` en CPU no llega a 12 s por 30 s de audio | Voraz, int8 y VAD; si falla, es un hallazgo que se resuelve por PR (`cpu_threads`, perfil GPU para la demostración), nunca subiendo la meta |
| Whisper transcribe peor nombres propios y el habla real que los clips de Piper | El WER de NFR4.1 mide clips limpios: es un detector de regresiones, no una promesa sobre audio real; el rótulo «transcripción automática» y el turno aclaratorio escrito (BR1.6) cubren el uso |
| Whisper inventa texto en silencio o ruido | VAD activo y NFR4.2; un texto vacío es error, nunca un turno |
| Licencias de Piper y de la voz | El motor original de Piper es MIT y su sucesor (`piper1-gpl`) es GPL-3.0; cada voz tiene su propia licencia en su `MODEL_CARD`. Se verifican antes de fijarlas en `models.lock`; si una voz no permite el uso académico, se elige otra `es_*` de la misma familia |
| El audio queda en el AOF hasta la reescritura | Declarado y probado (NFR10.4); alternativa D9 disponible por PR |
| El navegador no permite `MediaRecorder` o niega el micrófono | Aviso de BR1.1 y el turno escrito sigue disponible; la voz es SHOULD |
