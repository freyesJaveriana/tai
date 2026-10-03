# Diseño de fiabilidad — U9 voice

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; flujos F1–F4 y máquinas de estado de §3 de
`functional-design/functional-spec.md` (functional-spec); C5, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 = A y P2 = A de
`nfr-design-questions.md`; diseño de fiabilidad de U4.

## 1. *Timeouts* (NFR10.13)

| Llamada | *Timeout* | Ajuste |
|---|---|---|
| Whisper | `min(90 s, deadline_at − ahora)` | `VERIDICUS_WHISPER_TIMEOUT_SECONDS` |
| TTS (`audio-worker` → `model-tts`) | 10 s | `VERIDICUS_TTS_TIMEOUT_SECONDS` |
| Síntesis (`session-api` → `audio-worker`) | 12 s | `VERIDICUS_SPEECH_TIMEOUT_SECONDS` |
| Conexión HTTP | 2 s | `httpx.Timeout(connect=2)` |
| Redis | 0,5 s por operación; 2 s para `XADD` y `XREADGROUP` de `veridicus:audio` (`BLOCK 5000` con *timeout* de socket de 7 s); `BGREWRITEAOF` 0,5 s (solo pide, no espera) | Cliente de Redis con *timeout* por comando |
| PostgreSQL | 2 s (`statement_timeout`) | Como U4 |
| Lectura de la subida | El *timeout* de lectura del servidor HTTP de U4 | Configuración de Uvicorn |

Verificación: nivel 0 sobre la configuración y nivel 1 con dependencias lentas *fake*.

## 2. Ciclo del mensaje de audio (NFR10.14, NFR10.15)

Un único módulo, `services/audio-worker/.../worker/audio_lifecycle.py` (100 % de ramas, NFR13.2), decide
el resultado y garantiza que el audio se borra en todos los caminos:

```python
def handle(msg, now):
    if dedup.exists(msg.turn_id, msg.attempt):
        return finish(msg, publish=None)                 # repetido: sin Whisper
    if now >= msg.deadline_at:
        return finish(msg, publish=error(msg, "turn.error.timeout"))
    outcome = transcribe_once(msg, now)                  # sin reintento (NFR10.15)
    return finish(msg, publish=outcome)

def finish(msg, publish):
    if publish: transcripts.xadd(publish)                # primero el efecto
    with redis.pipeline(transaction=True) as p:          # MULTI
        p.xack(AUDIO, GROUP, msg.id); p.xdel(AUDIO, msg.id)
        p.set(dedup.key(msg), 1, ex=1800); p.execute()
    aof.mark_dirty()                                     # security-design §2
```

| Resultado de `transcribe_once` | Publica | Métrica `result` |
|---|---|---|
| Texto no vacío y ≤ 2 000 caracteres | `transcribed` con `model_digest` | `transcribed` |
| Vacío o solo espacios | `error` `turn.error.invalid_output` | `empty` |
| Más de 2 000 caracteres (NFR10.20) | `error` `turn.error.invalid_output` | `too_long` |
| *Timeout* | `error` `turn.error.timeout` | `timeout` |
| Conexión rechazada, 5xx o respuesta mal formada | `error` `turn.error.system` | `error` |

- **Sin reintento ante Whisper caído.** A diferencia del juez de U4 (reintento acotado), un fallo de
  Whisper termina el turno en segundos y el analista graba de nuevo o escribe (BR4.2): reintentar
  obligaría a conservar el audio más tiempo.
- **Caída a mitad del procesamiento.** El mensaje queda pendiente; `XAUTOCLAIM` lo reclama a los 120 s
  (`VERIDICUS_AUDIO_RECLAIM_IDLE_SECONDS` > 90 s). Si el resultado ya se publicó pero el `MULTI` no
  corrió, la ingesta lo descarta por intento (efecto único). En la 3.ª entrega sin confirmar, publica
  `error` con `turn.error.system`, escribe en `veridicus:audio:failed` solo identificadores y `code`, y
  hace el mismo `finish`.
- **Ingesta.** La de `veridicus:transcripts` sigue las reglas de U4 (reclamo, 3 entregas,
  `veridicus:transcripts:failed`) y hace `XACK` + `XDEL` tras confirmar su transacción.

Verificación: una prueba de nivel 0 por fila de la tabla con el Whisper *fake*; nivel 1 que mata al
trabajador a mitad de una transcripción → un solo texto por turno y audio borrado al final.

## 3. Ningún turno queda en «Procesando audio…» (NFR10.16)

El `DeadlineSweeper` de U4 cubre `processing_stage = 'transcribing'` (performance-design §3). Si Redis
pierde el mensaje (AOF `everysec`) o el trabajador nunca lo toma, el turno termina en `error` con
`turn.error.timeout` antes de `deadline_at + 30 s`. Verificación de nivel 1 con reloj controlado y un
mensaje borrado a mano.

## 4. Salud de `audio-worker` (NFR10.17)

| Sonda | Responde `503` si… |
|---|---|
| `/healthz` | Nunca, salvo que el proceso no atienda HTTP |
| `/readyz` | Configuración inválida; Redis, `model-whisper` o `model-tts` no responden (cada uno con su nombre en `checks`, sin datos); el calentamiento de Whisper o de la síntesis no terminó |

- El bucle consumidor no depende de `/readyz`: con `model-tts` caído la transcripción sigue.
- **Supervisión del hilo.** El bucle consumidor actualiza un latido en cada vuelta (`BLOCK 5000` asegura
  una vuelta cada ≤ 7 s); si el latido tiene más de 30 s o el hilo terminó por una excepción no
  controlada, el proceso registra `ERROR` y termina con código ≠ 0 para que Kubernetes lo reinicie.
- Configuración inválida → el proceso termina al arrancar con el log que nombra el ajuste.

Verificación de nivel 1 con cada dependencia caída y con el hilo forzado a fallar.

## 5. Fallos de la síntesis (NFR10.18)

TTS caído, *timeout*, `audio-worker` no preparado o `5xx` del puerto interno → `session-api` responde
`503` `speech.unavailable`; la consola muestra «No se pudo generar el audio; puedes leer la pregunta en
pantalla» y vuelve a habilitar «Escuchar audio». Sin reintento automático y sin cambios en la pregunta,
su decisión ni el turno. Verificación: nivel 1 con TTS *fake* caído y lento (11 s) y Vitest.

## 6. Envío desde la consola ante cortes (NFR10.19)

La mutación de envío conserva el WAV **en memoria** y reintenta con el mismo `client_request_id` tras 1,
2, 4 y 8 s ante error de red o `5xx` (no ante `4xx`). Si sigue fallando, la grabación queda en `ready`
con «No se pudo enviar el audio», «Reintentar envío» y «Descartar». El servidor deduplica por
(`session_id`, `client_request_id`) con la restricción única de U4 y responde el mismo turno, con un
solo mensaje en C5. Verificación: Vitest con servidor *fake* que falla 3 veces y nivel 1 con dos envíos
iguales (1 fila, 1 `XADD`).

## 7. Límites de texto y configuración (NFR10.20, NFR10.21)

- El límite de 2 000 caracteres se lee de `limits.get("turn_text_max_chars")` del catálogo de U1, no de
  una constante; prueba de nivel 0 con 2 001 caracteres del Whisper *fake*.
- La configuración de cada servicio es un `BaseSettings` de Pydantic con validadores cruzados:
  URL internas, *timeouts* positivos, reclamo > *timeout* de Whisper, base del plazo > *timeout* de
  Whisper + reclamo, `VERIDICUS_SPEECH_TIMEOUT_SECONDS` > `VERIDICUS_TTS_TIMEOUT_SECONDS`,
  `VERIDICUS_WHISPER_MODEL_SHA256` de 64 hexadecimales, `VERIDICUS_SPEECH_TOKEN` de ≥ 32 bytes,
  `VERIDICUS_VOICE_MAX_BYTES` ≤ el catálogo y `VERIDICUS_AOF_REWRITE_MIN_INTERVAL_SECONDS` entre 10 y
  600. Un fallo impide arrancar. Una prueba de nivel 0 por regla.

## 8. Calidad de la transcripción (NFR4.1–NFR4.4)

| Requisito | Diseño | Verificación |
|---|---|---|
| WER ≤ 20 % (NFR4.1) | D1 (`base` int8, idioma fijo); normalización común en `evaluation/voice/normalize.py` (minúsculas, sin puntuación, números en palabras) con `jiwer` | Corrida de voz |
| Silencio sin texto (NFR4.2) | `vad_filter = true` y texto vacío → `turn.error.invalid_output` (§2) | Corrida de voz: 3 clips de silencio o ruido, 0 textos |
| Repetible (NFR4.3) | `temperature = 0`, `beam_size = 1`, sin condicionar al texto previo | Corrida de voz: dos pasadas, 100 % de textos iguales |
| Equivalencia con el texto (NFR4.4) | El texto entra a C2 como un turno escrito; determinismo de U4 | Corrida de voz: mismas alertas al reenviar el texto como turno escrito |

## 9. Objetivos de punta a punta (NFR8.10, NFR8.11)

Estos patrones apuntan, en la corrida de voz, a 100 % de turnos con habla terminados antes de
`deadline_at + 30 s`, ≥ 98 % `evaluated` y 0 `OOMKilled`; y a 0 fallos atribuibles a U9 en
`scripts/smoke.sh` (`/readyz` de `audio-worker` en 200). Un fallo es un hallazgo con su `code` en el
reporte, no una corrida repetida.

## 10. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `audio-worker` | Nada | `XAUTOCLAIM` a los 120 s; el `AofRewriteRequester` queda sucio y pide reescritura al volver |
| Caída de `model-whisper` | Los audios de ese intervalo | `turn.error.system` en segundos y audio borrado |
| Caída de `model-tts` | Nada | `503` `speech.unavailable` |
| Redis pierde ≤ 1 s | Audios de ese segundo | Plazo (§3); se graba de nuevo |
| Reinicio de `session-api` en una subida | La subida | Reenvío con el mismo `client_request_id` (§6) |
