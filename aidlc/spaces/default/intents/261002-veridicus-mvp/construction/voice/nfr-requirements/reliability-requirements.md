# Requisitos de fiabilidad — U9 voice

**Revisión 2 (2026-11-22).** Sustituye a la revisión 1 del 2026-10-03.
- Los IDs se conservan. Lo nuevo es NFR10.26 y NFR10.27.
- Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o está **Retirado**.
- Los códigos de error pasan de `turn.error.*` a los de C5 (`analysis.*`, FD-U9-01).
- La reentrega se corta en 2 entregas.

**Insumos.**
- `functional-design/functional-spec.md` (functional-spec, revisión 2): flujos F1–F8, máquinas de estado
  de §3, errores de §6 y escenarios E1–E32.
- `functional-design/rules.md` (rules): reglas BR2.4, BR3.1–BR3.6, BR4.1–BR4.4, BR5.3, BR8.2 y BR9.1–BR9.7.
- `inception/requirements-analysis/requirements.md` (requirements, revisión 3): NFR2, NFR4, NFR8 y NFR10.
- `inception/contract-design/contract-summary.md` (contract-summary, revisión 3): C5, C13, C14, C16 y C25.
- P1 = A y P2 = A de `nfr-requirements-questions.md`.

## 1. Objetivos

El MVP no tiene SLA. Los objetivos medibles de U9 son:

| ID | Estado | Objetivo | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.10 | cambia | Los turnos de voz terminan. | En la corrida de voz, el 100 % de los turnos con habla termina `transcribed` o en `error` con su `code` antes de `voice_deadline_at + 30 s`, y ≥ 98 % termina `transcribed`. Ninguna corrida queda en espera tras el fin de su turno de voz (NFR10.26). 0 reinicios por `OOMKilled` de `audio-worker`, `model-whisper` y `model-tts` | Corrida de voz (§3) |
| NFR8.11 | cambia | U9 no rompe la prueba de humo. | 0 fallos atribuibles a U9 en cada corrida de `scripts/smoke.sh`: el *endpoint* de salud de `audio-worker` responde 200 (NFR3.14) | Nivel 3 |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.13 | cambia | Toda E/S de U9 tiene *timeout* explícito, leído de C25 y de la configuración validada al arrancar. | Whisper: `min(transcription_timeout_s, voice_deadline_at − ahora)` (NFR3.8). TTS: `tts_timeout_s` (12 s). `session-api` → `audio-worker`: `speech_route_timeout_s` (15 s). Conexión HTTP: 2 s. Redis: 0,5 s por operación, salvo `XADD` y `XREADGROUP` de `veridicus:audio`, que llevan 2 s por el tamaño del mensaje. PostgreSQL: ≤ 2 s por consulta, como U4. Escritura del audio conservado: 5 s | Nivel 0 (configuración) y nivel 1 |
| NFR10.14 | cambia | C5 entrega al menos una vez y sin efectos dobles (BR3.6, BR4.3); cierra R-03. | **Cierre de un audio.** `audio-worker` publica el `TranscriptResult` y luego, en una transacción `MULTI`, hace `XACK` + `XDEL` del audio y fija `veridicus:transcribed:{turn_id}:{attempt}` con TTL `voice_key_ttl_s` (NFR8.9). **Reclamo.** Un audio pendiente se reclama con `XAUTOCLAIM` tras `audio_claim_idle_ms` (120 000 ms, mayor que el *timeout* de Whisper). **Tope de entregas.** En la entrega número `audio_max_deliveries` + 1 (la 3.ª), el trabajador publica `error` con `analysis.system`, deja en `veridicus:audio:failed` solo IDs y `code`, y borra el audio. **Ingesta.** La de `veridicus:transcripts` sigue las reglas de U4 con `veridicus:transcripts:failed`. **Prueba de nivel 1:** se mata al trabajador a mitad de una transcripción; queda un solo texto por turno, el audio borrado al final y la segunda entrega dentro del plazo | Nivel 1 |
| NFR10.15 | cambia | Cada fallo de la transcripción tiene un único tratamiento, sin reintento (BR3.3, BR3.4, P2 = A de Functional Design). | **Casos:** <ul><li>texto vacío o solo espacios → `analysis.invalid_output`;</li><li>*timeout* → `analysis.timeout`;</li><li>conexión rechazada, 5xx o respuesta mal formada de Whisper → `analysis.system`;</li><li>mensaje con `voice_deadline_at` vencido → `analysis.timeout` **sin llamar** a Whisper;</li><li>mensaje repetido → se confirma y se borra sin llamar;</li><li>sesión con `veridicus:voice-cancelled:{session_id}` → se borra sin llamar (NFR10.25).</li></ul> **Siempre**, el audio se borra del *stream* (NFR10.3). Un Whisper caído **no** devuelve el mensaje a la cola: el audio no se guarda para reintentar, y el analista graba de nuevo o escribe (BR4.2, `project.md`). **Prueba:** una de nivel 0 por caso con el Whisper *fake* | Nivel 0 y nivel 1 |
| NFR10.16 | cambia | Ningún turno de voz queda en «Procesando audio…» para siempre. | El supervisor de NFR3.7 cubre `transcribing`. Todo turno de voz termina en `transcribed` o en `error` antes de `voice_deadline_at + 30 s`, también si se pierde el mensaje (Redis reiniciado, NFR10.4). Lo mismo con la sesión suspendida, en pausa o terminada (P6 = C) | Nivel 1 con reloj controlado |
| NFR10.17 | cambia | La salud de `audio-worker` refleja lo que necesita (C16). | `/readyz` responde `503` si la configuración es inválida o si no responden Redis, `model-whisper` o `model-tts`; cada uno lleva su nombre en `checks`, sin datos sensibles. También responde `503` si la plantilla de voz no cargó (BR6.2). El bucle consumidor no depende de la preparación: con el TTS caído, la transcripción sigue. Con configuración inválida o sin plantilla, el proceso termina con código ≠ 0 | Nivel 1 |
| NFR10.18 | cambia | Un fallo del TTS no rompe nada más (BR5.3). | **Fallos cubiertos:** TTS caído, *timeout*, `audio-worker` no preparado o respuesta mayor que `speech_audio_max_bytes`. **Respuesta:** `503` `speech.unavailable`, y la consola muestra el aviso del catálogo para leer la aclaración en pantalla. No hay reintento automático; el analista puede volver a pulsar. La aclaración, su decisión y los turnos no cambian. **Pruebas** de nivel 1 con el TTS *fake* caído y lento (13 s) | Nivel 1 y Vitest |
| NFR10.19 | se mantiene | Un corte de red al enviar no pierde la grabación ni duplica el turno (BR2.4). | **Reenvío.** Si `POST /voice-turns` falla por red o 5xx, la consola conserva la grabación **en memoria** y reenvía con el mismo `client_request_id` tras 1, 2, 4 y 8 s. Si sigue fallando, ofrece «Reintentar envío» y «Descartar». **Servidor.** Responde con el mismo turno; queda un solo mensaje en C5 y un solo archivo conservado. **Pruebas:** Vitest con un servidor *fake* que falla 3 veces, y nivel 1 con dos envíos iguales | Nivel 0 y nivel 1 |
| NFR10.20 | cambia | Una transcripción demasiado larga no entra en la tubería de corridas. | Si el texto, sin espacios en los extremos, supera `turn_max_chars` (20 000, U4), `audio-worker` publica `error` con `analysis.invalid_output`. Con 120 s de habla rápida no se pasa de unos 2 500 caracteres, así que es una defensa. Sale la cifra de 2 000 caracteres de la revisión 1. Prueba de nivel 0 con `turn_max_chars` + 1 caracteres del Whisper *fake* | Nivel 0 |
| NFR10.21 | cambia | La configuración de U9 se valida al arrancar (BR6.2). | **Cifras.** Las cifras se cargan con `limits.load` de C25; una variable de entorno solo puede bajarlas (`project.md`). **Reglas:** <ul><li>URL internas (NFR1.2);</li><li>`audio_claim_idle_ms` > `transcription_timeout_s`;</li><li>`voice_deadline_base_s` ≥ 2 × `transcription_timeout_s` + `audio_claim_idle_ms`;</li><li>`voice_key_ttl_s` ≥ `voice_deadline_max_s`;</li><li>`speech_route_timeout_s` > `tts_timeout_s`;</li><li>`VERIDICUS_WHISPER_MODEL_SHA256` de 64 hexadecimales igual a `models.lock`;</li><li>`VERIDICUS_SPEECH_TOKEN` presente;</li><li>plantilla de voz cargada y con un solo `{tema}`;</li><li>directorio de audio presente y escribible en `session-api`.</li></ul> **Fallo.** Un valor faltante o inválido impide arrancar, con un log que nombra el ajuste sin su valor. **Pruebas:** una de nivel 0 por regla | Nivel 0 |
| NFR10.26 | nuevo | Ninguna corrida queda en espera para siempre (BR9.1–BR9.4, FD-U9-07). | Cada fin de un turno de voz libera, en la misma transacción, las corridas en espera de la sesión que esperaban por él. Fines cubiertos: texto, `error` del trabajador, vencimiento por el supervisor, retirada del consentimiento y `TranscriptResult` descartado por tardío. Cada liberación fija `released_at` y `outcome`. Tras la retirada, la corrida liberada no se publica (VE-10 (a)). Una prueba de nivel 1 por fin. 100 % de ramas en el módulo de liberación (NFR13.2) | Nivel 1 |
| NFR10.27 | nuevo | Un audio autorizado o se guarda entero con su turno, o no queda nada (BR8.2). | Archivo antes que fila, como los reportes de U7: <ul><li>se escribe en un nombre temporal del mismo directorio, se hace `fsync`, se renombra a `audio_id` y se calcula el `sha256`;</li><li>luego, en una sola transacción, se insertan el turno, VoiceTurnState y TurnAudio;</li><li>después se hace el `XADD`.</li></ul> **Fallos:** si falla la escritura o se pasa la cuota, `503` `analysis.system` sin turno. Si falla la transacción, se borra el archivo. Si falla el `XADD`, el turno pasa a `error` con `analysis.system` y el archivo queda para la retención. Al arrancar, un barrido borra los archivos sin fila con más de 10 minutos. **Pruebas** de nivel 1 con fallo inyectado en cada paso | Nivel 1 |

## 3. Calidad de la transcripción y corrida de voz

La **corrida de voz** es el nivel 2 de U9:
- **Dónde corre.** Fuera de la CI, en CPU, con los modelos reales.
- **Qué bloquea.** Los PR que tocan el modelo de Whisper, la voz, la plantilla de voz,
  `services/audio-worker`, el adaptador de voz de `libs/model_gateway` o la ingesta de voz, y toda entrega
  etiquetada.
- **Clips.** Generados con la voz Piper fijada a partir de turnos del conjunto sintético de `evaluation/`
  (U11) y de textos sintéticos, más 3 clips de silencio o ruido.
- **Reporte JSON.** Registra la versión del conjunto, el `sha256` de Whisper, de la voz y de la plantilla,
  el perfil CPU o GPU y las métricas.

NFR4 de requirements mide la calidad de la IA sobre el conjunto sintético. Estas filas miden la entrada
que le da la voz.

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR4.1 | se mantiene | La transcripción es utilizable. | WER ≤ **20 %** sobre los clips con habla, con el texto normalizado (minúsculas, sin puntuación, números en palabras). El reporte registra además la fracción de nombres propios sintéticos bien transcritos (informativa, sin umbral). El umbral solo sube por PR con la medición | Corrida de voz |
| NFR4.2 | cambia | El silencio no inventa texto (BR3.3). | Los 3 clips de silencio o ruido de fondo terminan en `analysis.invalid_output` (0 textos no vacíos), con el filtro de voz (VAD) de `faster-whisper` activo | Corrida de voz |
| NFR4.3 | se mantiene | La transcripción es repetible. | Temperatura 0, búsqueda voraz (`beam_size = 1`) e idioma fijo: dos corridas seguidas con el mismo modelo dan el mismo texto en el 100 % de los clips | Corrida de voz |
| NFR4.4 | cambia | La voz no rebaja las garantías del analizador (BR4.1). | Sobre 10 relatos del conjunto sintético sintetizados en voz, el analizador corre sobre el texto transcrito: <ul><li>el 100 % de las citas de lo emitido se verifica contra el texto **transcrito**, nunca contra el original;</li><li>0 % de error de formato JSON.</li></ul> El reporte lista, por relato, los hallazgos sobre el texto original y sobre el transcrito, y la sensibilidad de cada uno. Esta parte es informativa, sin umbral, y la revisión humana nombra la diferencia que decide. Control negativo: un relato con una cita alterada a mano no la emite. Sale la comparación de alertas de la revisión 1 | Corrida de voz |

## 4. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `audio-worker` a mitad de una transcripción | Nada | El audio vuelve por `XAUTOCLAIM` tras 120 s (NFR10.14) |
| Caída de `model-whisper` | Los audios que llegan mientras tanto | Cada uno termina en `analysis.system` en segundos y se borra del *stream*. Las corridas en espera se liberan, y el analista graba de nuevo o escribe (BR4.2) |
| Caída de `model-tts` o de `audio-worker` al escuchar | Nada | `503` `speech.unavailable`; la aclaración se lee en pantalla |
| Redis pierde hasta 1 s de mensajes (AOF `everysec` de U2) | Audios de ese segundo | Los turnos terminan por plazo (NFR10.16) y liberan sus corridas en espera. El audio no se reintenta: se graba de nuevo |
| Redis se reinicia tras una retirada | La clave de cancelación | InterviewSession la vuelve a escribir al reconectar (NFR10.25) |
| Reinicio de `session-api` durante una subida | La subida en curso y, si había autorización, un archivo sin fila | La consola reenvía con el mismo `client_request_id` (NFR10.19); el barrido de NFR10.27 borra el archivo huérfano |
| Sesión suspendida por latido (`heartbeat_timeout_s` de U6) | Nada | Los turnos de voz en `transcribing` terminan igual; al reanudar se ven con su estado |

## 5. Degradación

Toda la voz es SHOULD. Si `audio-worker`, Whisper o el TTS no están disponibles, la consola sigue
funcionando con turnos escritos y aclaraciones en pantalla, y ningún flujo MUST depende de U9. Las
corridas en espera se liberan por plazo (NFR10.26), así que un Whisper caído retrasa los turnos escritos
como mucho hasta `voice_deadline_at + 30 s`, y en la práctica unos segundos, porque el error es
inmediato. El botón «Grabar» sigue visible: un fallo de transcripción se informa en el turno, no se oculta
la función.
