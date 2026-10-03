# Requisitos de rendimiento — U9 voice

**Insumos.** Flujos F1–F4 y escenarios de §6 de `functional-design/functional-spec.md`
(functional-spec); reglas BR1.3–BR1.5, BR2.3, BR3.1, BR3.4 y BR5.3 de `functional-design/rules.md`
(rules); FR10.2, FR10.4, NFR2, NFR3 y NFR8 de `inception/requirements-analysis/requirements.md`
(requirements); C1, C5, C13, C14 y C15 de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1 y P2 de `nfr-requirements-questions.md`.

Todas las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2), con Whisper `base`
int8 en `faster-whisper`, idioma fijo `es` (P2 = A), y la voz Piper de `tech-stack-decisions.md` D3. El
perfil GPU puede ir más rápido, pero ninguna meta depende de él. Las metas que necesitan los modelos
reales se miden en la **corrida de voz** (`reliability-requirements.md` §3), con clips sintéticos
generados por la voz Piper fijada (NFR12.1). Una prueba de rendimiento inestable se arregla o se pone en
cuarentena con un *issue*; nunca se reintenta ni se baja su umbral (team-practices).

## 1. Transcripción y turno de voz de punta a punta

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Desde el `202` de `POST /voice-turns` hasta que el texto queda guardado en el turno (`processing_stage` pasa a `retrieving`) | **p95 ≤ 12 s** para clips de hasta 30 s (P2 = A; NFR3 de requirements acepta 8–12 s) | ≥ 30 clips de 5 a 30 s, uno a la vez, cola de audio vacía | Corrida de voz: el reporte JSON registra p50, p95 y máximo por tramo de duración, con las marcas de hora que guarda el sistema |
| NFR3.2 | Lo mismo para una grabación del máximo de 120 s | **p95 ≤ 40 s** (P2 = A) | ≥ 10 clips de 100 a 120 s | Ídem |
| NFR3.3 | Turno de voz completo: `submitted_at` → `evaluated_at` | p95 ≤ **75 s** para clips de hasta 30 s y ≤ **100 s** para clips de 120 s (NFR3.1/NFR3.2 más el p95 de 60 s del turno de texto de U4, NFR3.1 de U4) | Los turnos del Golden Dataset sintetizados en voz, una sesión a la vez | Corrida de voz; `veridicus_turn_latency_seconds{origin="voice"}` (C15) |
| NFR3.4 | Respuesta de `POST /sessions/{id}/voice-turns` (`202`) | p95 ≤ **500 ms** con un WAV de 3,84 MB (120 s), **también con el Whisper *fake* bloqueado** | 50 envíos seguidos | Prueba `perf` de nivel 1 en proceso con PostgreSQL y Redis reales; incluye validación, `XADD` y la fila |

**Presupuesto orientativo de NFR3.1** (lo confirma la medición, no la reemplaza): recepción y `XADD`
≤ 0,5 s; lectura del *stream* ≤ 0,5 s; Whisper `base` int8 sobre 30 s de audio ≤ 10 s; publicación,
ingesta y guardado ≤ 1 s.

## 2. Plazo del audio y *timeouts* (C5)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.5 | El plazo de la transcripción crece con la cola de audio, como el de U4. | Al encolar: `deadline_at = enqueued_at + 300 s × (1 + m)`, donde `m` es el número de turnos de voz en la etapa `transcribing` (`queued` o `processing`) de todo el sistema, con tope de 1 800 s. Pruebas de nivel 0 con `m = 0` (300 s), `m = 2` (900 s) y `m = 10` (1 800 s). Base y tope son configuración (`VERIDICUS_AUDIO_DEADLINE_BASE_SECONDS`, `VERIDICUS_AUDIO_DEADLINE_MAX_SECONDS`). La base cubre el peor caso de un audio: *timeout* de Whisper (90 s) + reclamo tras caída (120 s) + una segunda entrega (90 s). |
| NFR3.6 | Tras transcribir, el turno recibe el plazo de evaluación de U4. | Al publicar el turno en C2, `deadline_at` se recalcula con la fórmula de NFR3.5 de U4 (300 s × (1 + n), tope 3 600 s); los dos plazos son sucesivos y no se suman. Prueba de nivel 1. |
| NFR3.7 | La revisión de plazos de U4 cubre la transcripción. | La tarea de BR5.8 de U4 (cada 15 s) también pasa a `error` con `turn.error.timeout` un turno vencido en `transcribing`, a más tardar 30 s después de su `deadline_at`; un `TranscriptResult` posterior se descarta (BR4.3). Prueba de nivel 1 con reloj controlado. |
| NFR3.8 | La llamada a Whisper nunca pasa del plazo. | *Timeout* efectivo = `min(VERIDICUS_WHISPER_TIMEOUT_SECONDS` = 90 s, `deadline_at − ahora)`; si es ≤ 0, no hay llamada y el resultado es `turn.error.timeout` (BR3.4). 90 s ≈ 2 × el p95 de 120 s (NFR3.2). Pruebas de nivel 0 con reloj y Whisper *fake*. |

## 3. Consola

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.9 | Enviar voz no bloquea la consola (BR1.5, AC10.2.2). | Con un turno de voz en `transcribing` (Whisper *fake* de 12 s), grabar, escribir y enviar otro turno y abrir una alerta responden en < 1 s por interacción. Prueba Playwright de nivel 3 y Vitest con temporizadores falsos. |
| NFR3.10 | La codificación a WAV no congela la pantalla (BR1.4). | Codificar 120 s a WAV mono de 16 kHz tarda ≤ 1,5 s en Chromium en la máquina de desarrollo, en un Web Worker; durante la codificación no hay tareas largas del hilo principal de más de 200 ms (`PerformanceObserver` de `longtask`). Prueba Playwright de nivel 3 con audio *fake* de Chromium. |
| NFR3.11 | El texto transcrito se ve poco después de guardarse. | Usa el sondeo de U4 (2 s con turnos en curso, NFR3.7 de U4): desde que el texto queda guardado hasta que aparece en M4 con su rótulo, ≤ 3 s. Playwright de nivel 3. |

## 4. Voz de la pregunta aprobada

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.12 | Escuchar la pregunta es rápido. | `GET /questions/{id}/audio` para una pregunta de 300 caracteres (el máximo de U8): p95 ≤ **5 s** con la voz Piper real en CPU (corrida de voz, 20 preguntas); con el TTS *fake* instantáneo, la sobrecarga de la ruta (autorización, consulta de aprobación y salto a `audio-worker`) tiene p95 ≤ 300 ms (prueba `perf` de nivel 1). |
| NFR3.13 | *Timeouts* de la síntesis. | `audio-worker` → `model-tts`: `VERIDICUS_TTS_TIMEOUT_SECONDS` = 10 s; `session-api` → `audio-worker`: `VERIDICUS_SPEECH_TIMEOUT_SECONDS` = 12 s (debe ser mayor que el anterior; validación al arrancar); conexión 2 s. Al vencer → `503` `speech.unavailable` (BR5.3). Pruebas de nivel 0. |

## 5. Prueba de humo

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.14 | La humo de team-practices no cambia por U9. | `scripts/smoke.sh <url-base>` conserva *N* = 120 s y sus dos casos de texto (NFR3.10 de U4); U9 solo añade `audio-worker` a la comprobación de `/readyz` de cada servicio (C16). El recorrido de voz va en `frontend/e2e/voice.spec.ts` (nivel 3, antes de etiquetar una entrega), con el micrófono *fake* de Chromium (`--use-file-for-fake-audio-capture`) y un clip sintético de 20 s: el turno queda evaluado en ≤ 75 s (NFR3.3). |

## 6. Recursos

Los `requests` y `limits` concretos los fija Infrastructure Design con estos topes medidos:

| ID | Pod | Tope de memoria medido | Cómo se mide |
|---|---|---|---|
| NFR8.1 | `model-whisper` | Pico ≤ 1 GiB transcribiendo un clip de 120 s | Pico de RSS durante la corrida de voz |
| NFR8.2 | `audio-worker` | Pico ≤ 256 MiB (mensaje de 8 MB en base64 + audio decodificado + una síntesis) | Ídem |
| NFR8.3 | `model-tts` | Pico ≤ 512 MiB sintetizando 300 caracteres | Ídem |
| NFR8.4 | API de `session-api` | Crecimiento ≤ 32 MiB por subida de 6 MB y sin crecimiento acumulado tras 20 subidas seguidas (diferencia ≤ 32 MiB entre la 1.ª y la 20.ª) | Prueba `perf` de nivel 1 con `tracemalloc` y RSS |

**CPU.** Whisper usa `cpu_threads = 4` y Piper 2 hilos (configuración del servidor, la aplica
Infrastructure Design). El efecto sobre el juez se mide con NFR8.8 (`scalability-requirements.md`). El
`limits.memory` de cada pod deja al menos un 20 % sobre el pico medido; si un pico supera su tope, es un
hallazgo que se corrige por PR, no un tope que se sube en silencio.
