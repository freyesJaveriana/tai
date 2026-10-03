# Requisitos de fiabilidad — U9 voice

**Insumos.** Flujos F1–F4, máquinas de estado de §3 y errores de §5 de
`functional-design/functional-spec.md` (functional-spec); reglas BR2.4, BR3.1–BR3.6, BR4.1–BR4.3 y
BR5.3 de `functional-design/rules.md` (rules); NFR2, NFR4, NFR8 y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C5, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

## 1. Objetivos

El MVP no tiene SLA. Los objetivos medibles de U9 son:

| ID | Objetivo | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.10 | Los turnos de voz terminan. | En la corrida de voz, el 100 % de los turnos con habla termina `evaluated` o en `error` con su `code` antes de `deadline_at + 30 s`, y ≥ 98 % termina `evaluated`; 0 reinicios por `OOMKilled` de `audio-worker`, `model-whisper` y `model-tts`. | Corrida de voz (§3) |
| NFR8.11 | U9 no rompe la prueba de humo. | 0 fallos atribuibles a U9 en cada corrida de `scripts/smoke.sh` (el `/readyz` de `audio-worker` responde 200, NFR3.14). | Nivel 3 |

## 2. Requisitos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.13 | Toda E/S de U9 tiene *timeout* explícito, leído de la configuración validada al arrancar. | Whisper: `min(90 s, deadline_at − ahora)` (NFR3.8); TTS 10 s; `session-api` → `audio-worker` 12 s; conexión HTTP 2 s; Redis 0,5 s por operación salvo `XADD` y `XREADGROUP` de `veridicus:audio`, que llevan 2 s por el tamaño del mensaje; PostgreSQL ≤ 2 s por consulta (como U4). | Nivel 0 (configuración) y nivel 1 |
| NFR10.14 | C5 entrega al menos una vez y sin efectos dobles (BR3.6, BR4.3). | `audio-worker` publica el `TranscriptResult` y luego, en una transacción `MULTI`, hace `XACK` + `XDEL` del audio y fija la clave de deduplicación (NFR8.9). Un audio pendiente se reclama con `XAUTOCLAIM` tras 120 s de inactividad (`VERIDICUS_AUDIO_RECLAIM_IDLE_SECONDS`, mayor que el *timeout* de 90 s de Whisper); en la 3.ª entrega sin confirmar, el trabajador publica `error` con `turn.error.system`, deja en `veridicus:audio:failed` solo identificadores y `code`, y borra el audio. La ingesta de `veridicus:transcripts` sigue las reglas de U4 (NFR10.15 de U4) con `veridicus:transcripts:failed`. Prueba de nivel 1 que mata al trabajador a mitad de una transcripción: un solo texto por turno, y el audio borrado al final. | Nivel 1 |
| NFR10.15 | Cada fallo de la transcripción tiene un único tratamiento, sin reintento (BR3.3, BR3.4, P2 = A de Functional Design). | Texto vacío o solo espacios → `turn.error.invalid_output`; *timeout* → `turn.error.timeout`; conexión rechazada, 5xx o respuesta mal formada de Whisper → `turn.error.system`; mensaje con `deadline_at` vencido → `turn.error.timeout` **sin llamar** a Whisper; mensaje repetido → se confirma y se borra sin llamar. En todos, el audio se borra (NFR10.3). A diferencia del juez de U4, un Whisper caído **no** devuelve el mensaje a la cola: el analista ve el error en segundos y graba de nuevo o escribe (BR4.2). Una prueba de nivel 0 por caso con el Whisper *fake*. | Nivel 0 y nivel 1 |
| NFR10.16 | Ningún turno de voz queda en «Procesando audio…» para siempre. | La revisión de plazos de U4 cubre la etapa `transcribing` (NFR3.7): todo turno de voz `queued` o `processing` en `transcribing` termina en `retrieving` o en `error` antes de `deadline_at + 30 s`, también si se pierde el mensaje (Redis reiniciado, NFR10.4). | Nivel 1 con reloj controlado |
| NFR10.17 | `/readyz` de `audio-worker` refleja lo que necesita (C16). | `503` si la configuración es inválida, o si Redis, `model-whisper` o `model-tts` no responden (cada uno con su nombre en `checks`, sin datos sensibles). El bucle consumidor no depende de la preparación: con el TTS caído, la transcripción sigue. Configuración inválida → el proceso termina con código ≠ 0 (BR6.2). | Nivel 1 |
| NFR10.18 | Un fallo del TTS no rompe nada más (BR5.3). | TTS caído, *timeout* o `audio-worker` no preparado → `503` `speech.unavailable` y la consola muestra «No se pudo generar el audio; puedes leer la pregunta en pantalla»; sin reintento automático (el analista puede volver a pulsar). La pregunta, su decisión y el turno no cambian. Pruebas de nivel 1 con el TTS *fake* caído y lento (11 s). | Nivel 1 y Vitest |
| NFR10.19 | Un corte de red al enviar no pierde la grabación ni duplica el turno (BR2.4). | Si `POST /voice-turns` falla por red o 5xx, la consola conserva la grabación **en memoria** y reenvía con el mismo `client_request_id` tras 1, 2, 4 y 8 s; si sigue fallando, muestra «No se pudo enviar el audio» con «Reintentar envío» y «Descartar». El servidor responde con el mismo turno y un solo mensaje en C5. Vitest con un servidor *fake* que falla 3 veces, y prueba de nivel 1 con dos envíos iguales. | Nivel 0 y nivel 1 |
| NFR10.20 | Una transcripción demasiado larga no entra al camino de U4. | El turno escrito admite 1–2 000 caracteres (BR5.1 de U4); un habla rápida de 120 s puede pasar de ahí. Si el texto, sin espacios en los extremos, supera 2 000 caracteres, `audio-worker` publica `error` con `turn.error.invalid_output` y la consola pide grabar en partes más cortas (precisión de catálogo en `security-requirements.md` §6). Prueba de nivel 0 con 2 001 caracteres del Whisper *fake*. | Nivel 0 |
| NFR10.21 | La configuración de U9 se valida al arrancar. | `audio-worker`: URL internas (NFR1.2), *timeouts* positivos, reclamo > *timeout* de Whisper, `VERIDICUS_WHISPER_MODEL_SHA256` de 64 hexadecimales, `VERIDICUS_SPEECH_TOKEN` presente. `session-api`: `VERIDICUS_VOICE_MAX_BYTES` entre 1 y 8 000 000, base del plazo de audio > *timeout* de Whisper + reclamo, `VERIDICUS_SPEECH_TIMEOUT_SECONDS` > `VERIDICUS_TTS_TIMEOUT_SECONDS`. Un valor faltante o inválido impide arrancar con un log que nombra el ajuste. Una prueba de nivel 0 por regla. | Nivel 0 |

## 3. Calidad de la transcripción y corrida de voz

La **corrida de voz** es el nivel 2 de U9: corre fuera de la CI, en CPU, con los modelos reales,
bloquea los PR que tocan el modelo de Whisper, la voz, `services/audio-worker` o la ingesta de voz, y
toda entrega etiquetada. Usa clips generados con la voz Piper fijada a partir de los turnos del Golden
Dataset y de textos sintéticos, más 3 clips de silencio o ruido. Su reporte JSON registra versión del
conjunto, `sha256` de Whisper y de la voz, perfil CPU/GPU y métricas.

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR4.1 | La transcripción es utilizable. | WER ≤ **20 %** sobre los clips con habla (texto normalizado: minúsculas, sin puntuación, números en palabras). El reporte registra además la fracción de nombres propios sintéticos bien transcritos (informativa, sin umbral). El umbral solo sube por PR con la medición. | Corrida de voz |
| NFR4.2 | El silencio no inventa texto (BR3.3). | Los 3 clips de silencio o ruido de fondo producen `turn.error.invalid_output` (0 textos no vacíos), con el filtro de voz (VAD) de `faster-whisper` activo. | Corrida de voz |
| NFR4.3 | La transcripción es repetible. | Temperatura 0, búsqueda voraz (`beam_size = 1`) e idioma fijo: dos corridas seguidas con el mismo modelo dan el mismo texto en el 100 % de los clips. | Corrida de voz |
| NFR4.4 | La voz conserva la equivalencia con el texto (BR4.1). | El reporte lista, por turno del Golden Dataset, las alertas del turno de voz y las del mismo turno escrito; además, para cada turno de voz, el texto transcrito reenviado como turno escrito da exactamente las mismas alertas (determinismo de U4, NFR4.2 de U4). | Corrida de voz |

## 4. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `audio-worker` a mitad de una transcripción | Nada | El audio vuelve por `XAUTOCLAIM` tras 120 s (NFR10.14) |
| Caída de `model-whisper` | Los audios que llegan mientras tanto | Cada uno termina en `turn.error.system` en segundos y se borra; el analista graba de nuevo o escribe (BR4.2) |
| Caída de `model-tts` o de `audio-worker` al escuchar | Nada | `503` `speech.unavailable`; la pregunta se lee en pantalla |
| Redis pierde hasta 1 s de mensajes (AOF `everysec` de U2) | Audios de ese segundo | Los turnos terminan por plazo (NFR10.16); el audio ya no existe, se graba de nuevo |
| Reinicio de `session-api` durante una subida | La subida en curso | La consola reenvía con el mismo `client_request_id` (NFR10.19) |

## 5. Degradación

Toda la voz es SHOULD: si `audio-worker`, Whisper o el TTS no están disponibles, la consola sigue
funcionando con turnos escritos y preguntas en pantalla, y ningún flujo MUST depende de U9. El botón
«Grabar» sigue visible: un fallo de transcripción se informa en el turno, no se oculta la función.
