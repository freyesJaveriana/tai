# Requisitos de rendimiento — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03. Los IDs se conservan; lo nuevo
es NFR3.15 y NFR3.16. Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o está **Retirado**.

**Insumos.**
- Flujos F1–F8 (F4 «Retirado»), escenarios E1–E32 y §11 de `functional-design/functional-spec.md`
  (functional-spec, revisión 2).
- Reglas BR1.3–BR1.5, BR2.3, BR3.1, BR3.4, BR5.3 y BR9.1–BR9.4 de `functional-design/rules.md` (rules).
- FR10.2, FR10.4, NFR2, NFR3 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements,
  revisión 3).
- C1, C5, C13, C14, C15 y C25 de `inception/contract-design/contract-summary.md` (contract-summary,
  revisión 3).
- Lo fijado hoy por otras unidades:
  - U11: p95 del tramo incremental ≤ 180 s y *N* = 300 s.
  - U4: plazo de corridas, sondeo y liberación de una corrida en espera ≤ 1 s.
- P1 = A y P2 = A de `nfr-requirements-questions.md`.

Todas las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2):
- Whisper `base` int8 en `faster-whisper` con idioma fijo `es` (P2 = A).
- La voz Piper de `tech-stack-decisions.md` D3.

El perfil GPU puede ir más rápido, pero ninguna meta depende de él. Las metas que necesitan los modelos
reales se miden en la **corrida de voz** (`reliability-requirements.md` §3), con clips sintéticos (NFR12.1).
Las cifras de C25 son de NFR-U9-02 (`security-requirements.md` §6). Una prueba de rendimiento inestable
se arregla o se pone en cuarentena con un *issue*; nunca se reintenta ni se baja su umbral.

## 1. Transcripción y turno de voz de punta a punta

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | se mantiene | Desde el `202` de `POST /sessions/{id}/voice-turns` hasta que el texto queda guardado en el turno (`voice_status = transcribed`) | **p95 ≤ 12 s** para clips de hasta 30 s. Es la transcripción por turno que acepta NFR3 de requirements (8–12 s) | ≥ 30 clips de 5 a 30 s, uno a la vez, cola de audio vacía, sin corrida en paralelo | Corrida de voz: el reporte JSON registra p50, p95 y máximo por tramo de duración, con las marcas de hora que guarda el sistema |
| NFR3.2 | se mantiene | Lo mismo para una grabación del máximo, `audio_max_seconds` (120 s) | **p95 ≤ 40 s** (P2 = A) | ≥ 10 clips de 100 a 120 s | Ídem |
| NFR3.3 | cambia | Turno de voz completo: `submitted_at` → fin del tramo incremental que lo incluye | **Cifras derivadas, no metas propias** (cierra R-04): p95 ≤ **192 s** para clips de hasta 30 s y ≤ **220 s** para 120 s. Son NFR3.1 y NFR3.2 más el p95 incremental de U11 (≤ 180 s). Si se incumple, se atribuye por tramo con las marcas de hora | Relatos del conjunto sintético de U11 sintetizados en voz, una sesión a la vez | Corrida de voz; `veridicus_turn_latency_seconds{origin="voice"}` (C15) |
| NFR3.4 | cambia | Respuesta `202` de `POST /sessions/{id}/voice-turns` | p95 ≤ **500 ms** con un WAV de 3,84 MB (120 s), **también con el Whisper *fake* bloqueado** y con `autoriza_conservar_audio` (incluye escribir el archivo, NFR10.24) | 50 envíos seguidos | Prueba `perf` de nivel 1 en proceso, con PostgreSQL y Redis reales. Incluye guardias, validación con la duración medida, `XADD` y la fila |
| NFR3.15 | nuevo | Transcripción con una corrida del analizador en paralelo en la misma máquina (cierra R-05) | Se mantiene p95 ≤ 12 s para clips de hasta 30 s. Si se incumple, es un hallazgo sobre `cpu_threads` o los `limits.cpu` de `model-whisper` y del juez, que se corrige por PR; nunca se sube la meta | Los clips de NFR3.1 con un tramo incremental de U11 en curso | Corrida de voz, sección «mixta» del reporte |

**Presupuesto orientativo de NFR3.1.** Lo confirma la medición, no la reemplaza:
- recepción, validación y `XADD`: ≤ 0,5 s;
- lectura del *stream*: ≤ 0,5 s;
- Whisper `base` int8 sobre 30 s de audio: ≤ 10 s;
- publicación, ingesta y guardado: ≤ 1 s.

## 2. Plazo del audio, espera de corridas y *timeouts* (C5)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.5 | cambia | El plazo de la transcripción crece con la cola de audio (cierra R-03). | **Fórmula.** Al encolar: `voice_deadline_at = enqueued_at + voice_deadline_base_s × (1 + m)`, con tope `voice_deadline_max_s`. `voice_deadline_base_s` es 360 s, el tope es 1 800 s y `m` es el número de turnos de voz en `transcribing` de todo el sistema. **Por qué 360 s.** La base cubre el peor caso con 2 entregas (`audio_max_deliveries`): `transcription_timeout_s` (90 s) + `audio_claim_idle_ms` (120 s) + una segunda llamada (90 s) = 300 s, con 60 s de margen. **Pruebas de nivel 0:** `m = 0` (360 s), `m = 2` (1 080 s) y `m = 10` (1 800 s). |
| NFR3.6 | cambia | Tras transcribir, el turno entra en la tubería de corridas de U4 sin plazo propio de U9. | El turno transcrito se publica en C2 como cualquier turno escrito. El plazo de la corrida es el de U4. Una corrida que estaba en espera recibe su plazo al liberarse (NFR-U4-10), no al crearse. Los dos plazos son sucesivos y no se suman. Prueba de nivel 1. |
| NFR3.7 | cambia | El supervisor de plazos vence los turnos de voz (NFR-U9-07). | El `run-supervisor` pasa a `error` con `analysis.timeout` un turno de voz en `transcribing` a más tardar 30 s después de su `voice_deadline_at`. En la misma transacción libera las corridas en espera (BR9.2). Un `TranscriptResult` posterior se descarta y se borra (BR4.3). Prueba de nivel 1 con reloj controlado. |
| NFR3.8 | cambia | La llamada a Whisper nunca pasa del plazo (BR3.4). | *Timeout* efectivo = `min(transcription_timeout_s, voice_deadline_at − ahora)`, con `transcription_timeout_s` = 90 s (≈ 2 × el p95 de 120 s). Si el plazo ya venció, no hay llamada y el resultado es `analysis.timeout`. Pruebas de nivel 0 con reloj y Whisper *fake*. |
| NFR3.16 | nuevo | La espera en orden de las corridas tiene una cota (P5 = B, BR9.1–BR9.4). | **Liberación.** Una corrida en espera detrás de un turno de voz se publica en C2 en ≤ 1 s desde que termina la transcripción: texto, `error`, vencimiento o retirada (NFR-U4-10). **Cota de la espera.** La espera extra de un turno escrito posterior es como mucho `voice_deadline_at + 30 s` del turno de voz más antiguo en `transcribing` de la sesión. Con un solo turno de voz de 30 s en uso normal, la espera es ≤ NFR3.1. **Pruebas de nivel 1** con reloj controlado: liberación tras texto, tras error, tras vencimiento y tras retirada. Se mide con `veridicus_run_hold_wait_seconds`. |

## 3. Consola

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.9 | se mantiene | Enviar voz no bloquea la consola (BR1.5). | Con un turno de voz en `transcribing` (Whisper *fake* de 12 s), cada una de estas interacciones responde en < 1 s: grabar, escribir y enviar otro turno, y abrir un hallazgo. Prueba Playwright de nivel 3 y Vitest con temporizadores falsos. |
| NFR3.10 | se mantiene | La codificación a WAV no congela la pantalla (BR1.4). | Codificar 120 s a WAV mono de 16 kHz tarda ≤ 1,5 s en Chromium, dentro de un Web Worker. No hay tareas largas de más de 200 ms en el hilo principal (`PerformanceObserver` de `longtask`). Playwright de nivel 3 con el audio *fake* de Chromium. |
| NFR3.11 | cambia | El texto transcrito se ve poco después de guardarse. | Usa el sondeo de U4 (`poll_interval_active_s` = 2 s con trabajo en curso): desde que el texto queda guardado hasta que aparece con su rótulo, ≤ 3 s. Playwright de nivel 3. |

## 4. Voz de la aclaración aprobada

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.12 | cambia | Escuchar la aclaración es rápido (BR5.3). | `GET /conductor-observations/{id}/audio` con frases de la plantilla de 60 a `speech_text_max_chars` (400) caracteres: p95 ≤ **5 s** con la voz Piper real en CPU (corrida de voz, 20 frases). Con el TTS *fake* instantáneo, la sobrecarga de la ruta tiene p95 ≤ 300 ms (prueba `perf` de nivel 1). La sobrecarga incluye rol y dueño, `is_observation_approved`, composición y validación de la frase, y el salto a `audio-worker`. La cifra de 300 caracteres de la pregunta sugerida sale. |
| NFR3.13 | cambia | *Timeouts* de la síntesis. | `audio-worker` → `model-tts`: `tts_timeout_s` = 12 s. `session-api` → `audio-worker`: `speech_route_timeout_s` = 15 s, que debe ser mayor que el anterior (se valida al arrancar). Conexión: 2 s. Al vencer, `503` `speech.unavailable` (BR5.3). Pruebas de nivel 0. |

## 5. Prueba de humo

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.14 | cambia | La prueba de humo de `team.md` no cambia por U9. | **`scripts/smoke.sh <url-base>`.** Usa el *N* = 300 s de U11. U9 solo añade `audio-worker` a la comprobación de salud de cada servicio (C16) y no consume tiempo del *N*. **Recorrido de voz.** Va en `frontend/e2e/voice.spec.ts` (nivel 3, antes de etiquetar una entrega), con un clip sintético de 20 s y el micrófono *fake* de Chromium (`--use-file-for-fake-audio-capture`). El texto aparece con su rótulo en ≤ 15 s, y el turno queda incluido en un tramo incremental terminado en ≤ 192 s (NFR3.3). |

## 6. Recursos

Los `requests` y `limits` concretos los fija Infrastructure Design con estos topes medidos:

| ID | Estado | Pod | Tope de memoria medido | Cómo se mide |
|---|---|---|---|---|
| NFR8.1 | se mantiene | `model-whisper` | Pico ≤ 1 GiB transcribiendo un clip de 120 s | Pico de RSS durante la corrida de voz |
| NFR8.2 | se mantiene | `audio-worker` | Pico ≤ 256 MiB: mensaje de 8 000 000 caracteres en base64, audio decodificado y una síntesis | Ídem |
| NFR8.3 | cambia | `model-tts` | Pico ≤ 512 MiB sintetizando una frase de 400 caracteres | Ídem |
| NFR8.4 | cambia | API de `session-api` | Crecimiento ≤ 32 MiB por subida de 6 MB, también con la escritura del audio conservado. Sin crecimiento acumulado tras 20 subidas seguidas: diferencia ≤ 32 MiB entre la 1.ª y la 20.ª | Prueba `perf` de nivel 1 con `tracemalloc` y RSS |

**CPU.** Whisper usa `cpu_threads = 4` y Piper 2 hilos; la configuración del servidor la aplica
Infrastructure Design. El efecto sobre el juez se mide con NFR8.8 (`scalability-requirements.md`) y el
efecto inverso con NFR3.15. El `limits.memory` de cada pod deja al menos un 20 % sobre el pico medido. Si
un pico supera su tope, es un hallazgo que se corrige por PR, no un tope que se sube en silencio.
