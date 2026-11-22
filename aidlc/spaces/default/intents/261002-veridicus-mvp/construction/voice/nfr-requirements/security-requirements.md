# Requisitos de seguridad — U9 voice

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U9.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos que siguen conservan su ID. Lo que sale queda «Retirado» sin renumerar. Lo nuevo
  toma el número siguiente de su grupo: NFR1.4, NFR10.22–NFR10.25 y NFR11.2. Cada fila dice si **se
  mantiene**, **cambia**, es **nuevo** o está **Retirado**.
- **Preguntas.** Ninguna en esta pasada: todo lo fijan las fuentes (segunda pasada de
  `nfr-requirements-questions.md`). P1 = A y P2 = A de la primera pasada siguen.
- **Conflicto de NFR-U11-11.** Se resuelve con C13 aprobado: `transcribe` y `synthesize` están en el puerto
  de U11 y los escribe U9 en B9, sin PR de U1 (D13 de `tech-stack-decisions.md`, NFR-U9-01).
- **Revisión 1.** Sus hallazgos R-01 a R-07 (`reviews/review-01.md`) se cierran en §7.

**Insumos.**
- Frontera de §1, flujos F1–F8 (F4 «Retirado»), máquinas de estado de §3, errores de §6, escenarios
  E1–E32 y tabla FD-U9-01 a FD-U9-14 de `functional-design/functional-spec.md` (functional-spec, revisión
  2); reglas BR1.1–BR9.7 de `functional-design/rules.md` (rules) y entidades de `functional-design/entities.md`.
- FR10.2, FR10.4 y NFR1–NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión
  3; NFR9 «Retirado»), y VE-06, VE-08, VE-09, VE-10 y VE-12 de `requirements-adenda-02.md`.
- C1, C5, C8, C13, C14, C15, C16, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3), y la arista voice → incoherence-analyzer de
  `inception/units-generation/unit-of-work-dependency.md`.
- Lo que fijaron hoy los NFR de U1, U2, U3, U4, U6, U8 y U11, citado por descripción o por su ID de
  precisión.
- Reglas AUTONOMIA-01..05 de `team.md` y prohibiciones de `project.md`.

Niveles de `team.md`: nivel 0 (unitarias, contratos y políticas, cada PR, sin red ni GPU), nivel 1
(integración con PostgreSQL y Redis reales y Whisper y TTS *fakes*, cada PR), nivel 2 (para U9, la
**corrida de voz** de `reliability-requirements.md` §3, fuera de la CI), nivel 3 (E2E y humo) y manual.
Cada prueba lleva su control negativo. Los comandos están en `tech-stack-decisions.md` §5. La sesión web,
el anti-CSRF, el dueño y la convención de auditoría son de U3; la tubería de corridas, la clave de
cancelación de corridas y el borrado de mensajes son de U4; la `NetworkPolicy`, `models.lock` y los
volúmenes son de U2. Aquí solo se exige que U9 los use y lo que U9 añade.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| AnalystConsole (grabación y «Escuchar audio») | Navegador del analista | Audio crudo **solo** hacia `session-api` por C1 (HTTPS, mismo origen); WAV de la aclaración de vuelta. Nada a terceros (NFR1.3). El audio vive en memoria, nunca en el almacenamiento del navegador (NFR10.5) | Restringido |
| `session-api` (ConsoleApi, InterviewSession) | Dentro del clúster | Audio en tránsito hacia Redis; texto transcrito a PostgreSQL y a C2; tema de la aclaración hacia `audio-worker` | Restringido |
| Volumen de audio de `session-api` | Dentro del clúster (PVC propio, U2) | Audio conservado **solo** con `autoriza_conservar_audio` (NFR10.24); no lo lee nada salvo el Job de retención | Restringido |
| Redis (`veridicus:audio`, `veridicus:transcripts`, claves `veridicus:voice-cancelled:*` y `veridicus:transcribed:*`) | Dentro | Audio en base64 hasta `XDEL`; texto hasta `XDEL`; las claves solo llevan IDs. Rastro en el AOF acotado (NFR10.4) | Restringido |
| `audio-worker` (SpeechProcessing) | Dentro; pod de datos sin anonimizar bajo la `NetworkPolicy` de salida denegada | Audio hacia `model-whisper`; frase compuesta hacia `model-tts`; solo alcanza Redis, esos dos servidores y DNS (NFR1.1) | Restringido |
| `ModelGateway`: métodos `transcribe` y `synthesize` y su adaptador local (C13, C14; código de U9 en `libs/model_gateway/`) | En el proceso de `audio-worker` | Solo URL internas (NFR1.2); no importa el anonimizador ni su cliente (NFR1.4) | — |
| `model-whisper` y `model-tts` | Dentro (pods de U2 sin salida) | Reciben audio o texto; no lo registran ni lo dejan en el disco del nodo (NFR10.2, NFR10.6) | Restringido en tránsito |

**Ningún componente de U9 llama fuera del clúster**, así que no aplica el anonimizador (U10): la
transcripción y la síntesis no son llamadas a un proveedor comercial. Aunque en el MVP todo audio del
repositorio es sintético (NFR12.1), el audio se trata como dato restringido.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | `audio-worker` o un servidor de modelos envía audio o texto a internet | Information disclosure | Alto | NFR1.1, NFR1.2, NFR1.4 |
| T2 | El navegador transcribe o sintetiza con un servicio de terceros | Information disclosure | Alto | NFR1.3 |
| T3 | El audio queda en el navegador, en el disco de un pod o en un archivo temporal sin autorización | Information disclosure | Alto | NFR10.2, NFR10.5 |
| T4 | Audio o texto en los *streams* tras usarse, o en las entradas de fallidos | Information disclosure | Alto | NFR10.3 |
| T5 | El audio persiste en el AOF de Redis hasta la reescritura | Information disclosure | Medio | NFR10.4 (riesgo residual, §5) |
| T6 | Audio, texto transcrito o tema en logs, métricas o errores | Information disclosure | Alto | NFR10.6 |
| T7 | Un analista envía voz a una sesión ajena o escucha la aclaración de otra; `admin` o `investigador` lo hacen | Elevation of privilege | Medio | NFR10.7 |
| T8 | Se sintetiza una aclaración sin aprobar y llega a la persona entrevistada | Elevation of privilege | Alto | NFR10.8 |
| T9 | Otro pod llama a la ruta interna de síntesis | Spoofing | Medio | NFR10.9 |
| T10 | Archivo enorme, de duración falsa o binario disfrazado | Denial of service, Tampering | Medio | NFR10.1 |
| T11 | Un modelo alterado o un formato con código ejecutable | Tampering | Medio | NFR10.10 |
| T12 | Alguien cambia el texto transcrito | Tampering, Repudiation | Medio | NFR10.11, NFR11.1 |
| T13 | Whisper «alucina» texto en silencio | Tampering | Medio | NFR4.2 (`reliability-requirements.md`), NFR10.11 |
| T14 | Una instrucción dictada cambia el análisis | Tampering | Alto | NFR5.1 |
| T15 | No se sabe qué modelo transcribió un turno | Repudiation | Bajo | NFR10.10, NFR11.1 |
| T16 | Un analista inunda la cola de audio | Denial of service | Bajo | Riesgo aceptado (§5) |
| T17 | El TTS pronuncia un texto distinto de la aclaración aprobada (la contradicción, «antes dijo», una cita o vocabulario prohibido) | Tampering, Information disclosure | Alto | NFR10.22 |
| T18 | Se graba sin consentimiento o sin la autorización de voz | Elevation of privilege | Alto | NFR10.23 |
| T19 | El audio conservado se lee, se descarga, se reprocesa o sobrevive a la retención | Information disclosure | Alto | NFR10.24, NFR11.2 |
| T20 | Tras la retirada del consentimiento, el audio en cola llega a Whisper | Information disclosure | Alto | NFR10.25 |
| T21 | Los métodos de voz del gateway abren un camino a un destino externo | Elevation of privilege, Information disclosure | Alto | NFR1.4 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | cambia | `audio-worker` no tiene salida a internet (BR6.1). | El render (`values-cpu.yaml` y `values-gpu.yaml`) da al pod la etiqueta de datos sin anonimizar y lo cubre `veridicus-default-deny`; su salida es **solo** Redis (6379), `model-whisper` (8080), `model-tts` (8080) y DNS; su entrada, solo `session-api` en el puerto interno de síntesis y Prometheus en `/metrics` (precisión NFR-U9-05). Política Kyverno con control negativo (pod sin etiqueta o con salida a `0.0.0.0/0`). Antes de la sustentación, desde `audio-worker`, `curl -m 5 https://example.org` termina con código ≠ 0 | Nivel 0 y manual |
| NFR1.2 | cambia | Las URL de modelos y de síntesis son internas (BR6.2). | `VERIDICUS_WHISPER_URL`, `VERIDICUS_TTS_URL` (en `audio-worker`) y `VERIDICUS_SPEECH_URL` (en `session-api`) solo admiten el nombre corto `http://veridicus-<nombre>:<puerto>` o un *host* que termina en `.svc.cluster.local[:puerto]` (forma de NFR-U1-06); otra forma impide arrancar con un log que nombra el ajuste sin su valor. El adaptador local de `transcribe` y `synthesize` repite la comprobación al construirse. Una prueba por forma rechazada (IP pública, dominio externo, `localhost` fuera de pruebas) y su control positivo | Nivel 0 |
| NFR1.3 | se mantiene | La consola no usa servicios de voz del navegador ni de terceros. | ESLint prohíbe `speechSynthesis`, `SpeechSynthesisUtterance`, `SpeechRecognition` y `webkitSpeechRecognition` en `frontend/src`; la grabación solo sube a `/sessions/{id}/voice-turns` (mismo origen). Control negativo: un archivo con `speechSynthesis.speak` hace fallar el *lint* | Nivel 0 |
| NFR1.4 | nuevo | Los métodos de voz del gateway no tienen camino a un destino externo (C13, D13). | Contrato `forbidden` de import-linter: `libs.model_gateway.adapters.speech_local` no importa `libs.anonymizer` ni `libs.model_gateway.adapters.anonymizer_http`. El lockfile de `audio-worker` no contiene `libs-anonymizer` y `sys.modules` no lo tiene tras arrancar. `audio-worker` no recibe el Secret `veridicus-provider-keys` (NFR10.12 de U2). Control negativo: un import sembrado | Nivel 0 |

### NFR5 — Resistencia adversarial

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR5.1 | cambia | Una inyección dictada se trata como dato, igual que escrita (BR4.1). | Con el Whisper *fake* devolviendo el texto de inyección del Escenario A, la entrada de C6 que arma la corrida del turno de voz es idéntica byte a byte (salvo IDs y fechas) a la de un turno escrito con el mismo texto en otra sesión igual. Como el texto es el mismo, la resistencia de fondo es la de U11 (NFR5.1 de U11); U9 solo prueba que no añade otro camino. Sustituye a la comparación de alertas de la revisión 1, que salió con el marco documental | Nivel 1 |

### NFR10 — Seguridad de la aplicación

Los *timeouts*, las entregas y el fallo de cada paso (NFR10.13–NFR10.21, NFR10.26 y NFR10.27) están en
`reliability-requirements.md`.

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | El audio se valida antes de crear el turno (BR2.2, BR2.3). | Tras rol y dueño (NFR10.7) y las guardias de NFR10.23: el servidor **deja de leer** el cuerpo al pasar `audio_max_bytes` (6 000 000) + 16 384 bytes de sobre `multipart` → `413` `limits.exceeded`; formato `wav` o `mp3`, cabecera real (RIFF/WAVE PCM o tramas MPEG) y hablante `ENT` o `TEST`, si no `422` `validation.invalid_request`; la duración se **mide sobre el audio** (muestras del bloque `data` en WAV, recuento de tramas en MP3; D7), nunca sobre la cabecera, y más de `audio_max_seconds` (120) → `413`. Cada rechazo: 0 filas, 0 archivos, `XLEN veridicus:audio` sin cambio. Pruebas: 10 MB, MP3 con extensión WAV, WAV de 121 s, WAV con cabecera que declara 60 s y trae 130 s, MP3 de tasa variable de 130 s con cabecera de 60 s (E31), PNG renombrado, cuerpo vacío; con 10 MB la memoria del proceso crece ≤ 20 MiB | Nivel 1 |
| NFR10.2 | cambia | El audio solo toca un disco con autorización expresa (BR3.5, BR8.2, BR8.3). | Sin `autoriza_conservar_audio`: `session-api` lee la subida en memoria (el analizador `multipart` no usa archivo temporal; una prueba que hace fallar `tempfile` sigue dando `202` con 5 MB) y no escribe nada en el volumen de audio. Con la autorización, la única escritura es el archivo de NFR10.24. `audio-worker` no monta ningún volumen escribible salvo `/tmp` `emptyDir` en memoria (política de nivel 0). `model-whisper` y `model-tts` solo escriben en `/tmp` `emptyDir` con `medium: Memory` (NFR-U9-05). El Ingress `veridicus-voice` no guarda el cuerpo en disco (decisión de Infrastructure Design de `project.md`). Ninguna ruta escribe audio en PostgreSQL | Nivel 0 y nivel 1 |
| NFR10.3 | cambia | Los *streams* no conservan audio ni texto tras usarlos (BR3.5). | `audio-worker` hace `XACK` + `XDEL` del audio con **cualquier** resultado: texto, vacío, error, plazo vencido, duplicado (BR3.6), cancelado por retirada (BR9.6) y mensaje a fallidos. `session-api` hace `XACK` + `XDEL` de cada `TranscriptResult`, también del descartado (BR4.3). Las entradas de `veridicus:audio:failed` y `veridicus:transcripts:failed` llevan solo `message_id`, `turn_id`, `attempt` y `code`, recortadas a 1 000. Prueba de nivel 1 por resultado: `XLEN` de los dos *streams* = 0 y `XRANGE` de los fallidos sin la cadena centinela del audio ni del texto | Nivel 1 |
| NFR10.4 | cambia | El rastro del audio en el AOF de Redis tiene una cota comprobable (cierra R-01). | Redis sin RDB (`save ""`), con AOF `everysec` (U2), `auto-aof-rewrite-percentage 100` y `auto-aof-rewrite-min-size 16mb` (NFR-U9-05). Cota declarada: un audio confirmado sigue en el AOF hasta que el AOF crece al menos 16 MB **y** el doble de su tamaño tras la última reescritura. Prueba de nivel 1 con Redis real configurado igual: tras confirmar un audio con un patrón centinela de 64 bytes, el patrón está en `appendonlydir` (documenta el riesgo); tras escribir y borrar mensajes hasta pasar la cota, `INFO persistence` muestra una reescritura más en ≤ 10 s y el patrón aparece 0 veces. El texto «unos 2 audios» de la revisión 1 sale | Nivel 1 |
| NFR10.5 | se mantiene | El navegador no guarda el audio. | Nunca en `localStorage`, `sessionStorage`, IndexedDB, Cache Storage ni *service worker*. Las URL `blob:` se revocan al enviar o descartar, también el WAV de «Escuchar audio» al terminar de sonar; las pistas del micrófono se detienen al detener, al llegar a 120 s y al salir de la pantalla. Vitest comprueba `stop()` y `revokeObjectURL`; Playwright, tras grabar, enviar y escuchar, encuentra los cuatro almacenamientos sin audio y 0 pistas activas | Nivel 0 y nivel 3 |
| NFR10.6 | cambia | Ni el audio, ni el texto, ni el tema aparecen en logs, métricas o errores (BR6.3). | Campos permitidos: `session_id`, `turn_id`, `observation_id`, `message_id`, `audio_id`, `attempt`, `code`, `rule_id`, `byte_size`, `audio_seconds`, `audio_format` y duraciones. Prueba de nivel 1 con cuatro centinelas (bytes en el audio *fake*, cadena en la transcripción del Whisper *fake*, cadena en el tema de la aclaración y cadena en el texto rechazado por BR5.6): 0 apariciones en los logs de `session-api` y `audio-worker`, también los de error, y en el cuerpo de cada 4xx/5xx. Manual antes de la sustentación: los logs de `model-whisper` y `model-tts` no contienen la frase centinela del clip | Nivel 1 y manual |
| NFR10.7 | cambia | Solo el dueño envía voz y escucha la aclaración (BR2.1, BR5.4, ADR-009). | `POST /sessions/{id}/voice-turns` y `GET /conductor-observations/{id}/audio`: `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`; el POST exige `X-CSRF-Token`. Pruebas `403`: otro analista, `admin`, `investigador` e identidad de servicio en ambas rutas, y POST sin anti-CSRF; en todas, 0 filas, 0 archivos, 0 `XADD` y 0 llamadas al TTS *fake* | Nivel 1 |
| NFR10.8 | cambia | Solo se sintetiza una aclaración aprobada, solo al pulsar y solo con la sesión abierta o en pausa (BR5.1, BR5.2, BR5.7). | La ruta consulta el puerto `is_observation_approved` de U8 antes de llamar a `audio-worker`: inexistente → `404` `conductor_observation.not_found`; `proposed` o `discarded` → `409` `conductor_observation.not_approved` (prueba de nivel 1 de U9, NFR-U8-07). Sesión bloqueada, con retirada, terminada, finalizada, consolidada o suspendida → `409` con su `code`, en el orden de BR2.2 (E29). El TTS *fake* cuenta **0 llamadas** en cada rechazo y en todo el ciclo de vida de una aclaración que nadie escucha. «Escuchar audio» solo aparece con `approved` y se deshabilita mientras hay una petición en curso | Nivel 0 y nivel 1 |
| NFR10.9 | cambia | La ruta interna de síntesis solo la usa `session-api` y solo acepta su cuerpo (FD-U9-04). | `POST /internal/v1/speech` en el puerto interno de `audio-worker`: `Authorization: Bearer` con `VERIDICUS_SPEECH_TOKEN` (Secret `veridicus-speech-token`, ≥ 32 bytes, comparación en tiempo constante) o `401` sin llamar al TTS; cuerpo estricto `{observation_id, tema, template_version}` (UUID, texto no vacío, versión) o `422`; la `NetworkPolicy` de entrada solo admite `session-api`. Respuesta `audio/wav` de ≤ `speech_audio_max_bytes` (4 194 304); `session-api` deja de leer al pasarla y responde `503` `speech.unavailable`. Pruebas de nivel 1 sin token, con token erróneo, con un campo de más y con `text` en lugar de `tema` | Nivel 0 y nivel 1 |
| NFR10.10 | se mantiene | Los modelos de voz son los fijados (BR6.4). | Whisper `base` CTranslate2 int8 y la voz Piper (`.onnx` + `.onnx.json`) con revisión y `sha256` en `deploy/models.lock`; U2 los verifica al arrancar. Ningún `.pt`, `.pkl` ni `trust_remote_code`. Cada `TranscriptResult` con texto lleva `model_digest` igual al `sha256` del `model.bin` de `models.lock`, y la ingesta lo guarda en VoiceTurnState | Nivel 0 y nivel 1 |
| NFR10.11 | cambia | El texto transcrito no se edita y se rotula (BR1.6, BR4.2, BR4.4). | No existe ruta de C1 que cambie el texto de un turno (prueba sobre el OpenAPI); todo turno de voz muestra «Turno por voz (transcripción automática)» (Vitest y nivel 3). Un turno de voz en `error` no tiene corrida ni reintento: la consola solo ofrece «Grabar de nuevo» y «Escribir el turno», que crean un turno nuevo. Sale `turn.audio_unavailable` de la revisión 1 (X2 «Superado») | Nivel 0 y nivel 3 |
| NFR10.12 | cambia | Los errores de U9 son Problem Details con `code` del catálogo (functional-spec §6). | `403` `auth.forbidden`; `404` `conductor_observation.not_found`; `409` `session.consent_missing`, `session.blocked`, `session.consent_withdrawn`, `session.terminated`, `session.finalized`, `session.closed_to_new_turns`, `session.suspended`, `session.voice_not_authorized`, `conductor_observation.not_approved` y `speech.text_rejected`; `413` `limits.exceeded` (nunca `422`, regla de U1); `422` `validation.invalid_request`; `503` `analysis.system` (audio autorizado sin escribir) y `speech.unavailable`. `detail` en español, sin trazas ni texto del modelo. Una prueba por `code`; `speech.*` entran por el PR de U1 de FD-U9-02 | Nivel 0 y nivel 1 |
| NFR10.22 | nuevo | El TTS solo pronuncia la plantilla con el tema de una aclaración aprobada y válida (BR5.5, BR5.6, VE-09). | `audio-worker` arma la frase con `contracts/integrity/clarification-speech.v1.yaml` (un solo marcador `{tema}`) y la rechaza con `422` y el ID de la regla, **sin llamar al TTS**, si: (a) `template_version` no es la cargada; (b) la frase no pasa la regla de DT23 (menciona la contradicción, «antes dijo» o una variante, o contiene una cita); (c) el escáner de C8 encuentra un término; (d) pasa de `speech_text_max_chars` (400). ConsoleApi traduce el `422` a `409` `speech.text_rejected`. Una prueba de nivel 0 por regla con su control negativo, más E28; 100 % de ramas en el módulo de composición y validación (NFR13.2) | Nivel 0 y nivel 1 |
| NFR10.23 | nuevo | Sin consentimiento o sin autorización de voz no entra audio (BR2.2, BR8.1, VE-06). | Bajo el bloqueo de la sesión y en este orden: `session.consent_missing`, `session.blocked`, `session.consent_withdrawn`, `session.terminated`, `session.finalized`, `session.closed_to_new_turns`, `session.suspended` y luego `session.voice_not_authorized`; en pausa se acepta (BR9.7). Una prueba de nivel 1 por guardia, con una sesión que cumple todas las anteriores: `409` con su `code`, 0 filas, 0 archivos y 0 mensajes; con `authorizes_voice: false` el turno escrito sigue aceptándose (E13, E14) | Nivel 1 |
| NFR10.24 | nuevo | El audio conservado se guarda aislado y no lo lee nada salvo la retención (BR8.2, BR8.4, BR8.6, VE-08, VE-12). | (a) Existe solo con `autoriza_conservar_audio`. (b) Vive en el volumen de audio de `session-api` (PVC propio de U2, distinto del de reportes, con *prune* desactivado), en un subdirectorio `audio/` con modo `0700` que crea el proceso, con archivos `0600` nombrados por `audio_id` y su `sha256`. (c) Ninguna ruta de C1 lo expone (prueba sobre el OpenAPI) y import-linter impide que `audio-worker` y los módulos de ConsoleApi importen el módulo de TurnAudio. (d) Solo el Job de retención lo borra, archivo antes que fila, y el acta lleva `audio_id` y `sha256`, nunca audio (prueba de nivel 1 de U13 con reloj simulado, FD-U9-09). (e) El directorio tiene una cuota propia, `audio_store_max_bytes` (2 147 483 648): si una escritura la pasaría, `503` `analysis.system` sin turno (BR8.2). (f) Sin cifrado en reposo (riesgo aceptado, §5) | Nivel 0 y nivel 1 |
| NFR10.25 | nuevo | Tras la retirada del consentimiento, ningún audio en cola llega a Whisper (BR9.5, BR9.6, VE-10 (a)). | Al registrar la retirada, en la misma transacción los turnos de voz en `transcribing` pasan a `error` con `session.consent_withdrawn`, y tras confirmar se escribe `veridicus:voice-cancelled:{session_id}` con TTL `voice_key_ttl_s` (1 920 s: el plazo máximo de la transcripción, 1 800 s, más un margen de 120 s igual al reclamo de C5). `audio-worker` consulta la clave antes de cada llamada. Con dos audios en cola, el Whisper *fake* cuenta **0 llamadas** y los dos mensajes se borran (E25). Al reconectar tras un reinicio de Redis, InterviewSession vuelve a escribir la clave de cada sesión cuya retirada tenga menos de `voice_key_ttl_s`, como la clave de corridas de U4. Un resultado de una llamada que ya había salido se descarta y su texto no se guarda (E26). La clave solo lleva el ID. 100 % de ramas en la decisión del trabajador | Nivel 1 |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | El turno de voz deja rastro como cualquier turno (convención de U3). | `Turn` sigue `history`. VoiceTurnState es `mutable` con disparador: `voice_status` solo avanza (`transcribing` → `transcribed` o `error`), `voice_error_code`, `transcribed_at` y `model_digest` se escriben una vez. RunPublicationHold es `mutable` con disparador: `released_at` y `outcome` pasan de nulo a valor una sola vez. TurnAudio es `history`. Los cambios por `TranscriptResult` llevan `actor_kind = system` y `actor_system = audio-worker` (valor nuevo de `ActorSystem`, NFR-U9-06); el vencimiento del plazo, `run-supervisor`; la retirada, la persona. Prueba común de U3 con las tres tablas y un `UPDATE` que intenta revertir cada columna | Nivel 1 |
| NFR11.2 | nuevo | El texto transcrito y el audio conservado no se reescriben ni se borran salvo por la retención (NFR11 de Inception, A-2). | El usuario de la aplicación no tiene `UPDATE` sobre el texto de un turno ya escrito ni `DELETE` sobre `Turn`, VoiceTurnState, TurnAudio ni RunPublicationHold; solo `veridicus_retention` borra, por `purge_session` de InterviewSession. Prueba de nivel 1 con los dos usuarios | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | cambia | Todo audio del repositorio y de la CI es sintético. | Los clips se **generan** con la voz Piper fijada a partir de turnos del conjunto sintético de `evaluation/` (U11) y de textos sintéticos marcados (catálogo de U1); no se graban voces humanas. `scripts/check-synthetic-audio.sh` falla si un `.wav` o `.mp3` del repositorio no figura en `evaluation/voice/manifest.json` con su `sha256` y su texto de origen; los clips grandes se regeneran y no se versionan. Los *fixtures* de la plantilla de voz siguen la marca `synthetic` de U1. En el ensayo de la demo, la voz del analista solo se conserva si la sesión lo autoriza (NFR10.24) | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U9 |
|---|---|
| AUTONOMIA-01 | U9 no aplica nada al clúster: `NetworkPolicy`, modelos, volúmenes, migraciones (`Job` aparte, en su propio PR) y cifras de C25 entran por PR; la verificación manual con `curl` es de lectura; el Job de retención lo lanza el humano (U2, U13) |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.8 y NFR10.22 (nada llega a la persona entrevistada sin aprobación ni con vocabulario prohibido), NFR10.11, NFR11.1 y NFR11.2 (la transcripción es entrada rotulada y no se reescribe). U9 no produce calificaciones ni etiquetas |
| AUTONOMIA-04 | §1, NFR1.1–NFR1.4, NFR10.2–NFR10.6, NFR10.24, NFR10.25; la tarea de `NetworkPolicy` de `audio-worker` (NFR1.1) |
| AUTONOMIA-05 | No aplica directamente: el turno transcrito entra en la misma corrida que un turno escrito (NFR5.1, NFR4.4 de `reliability-requirements.md`) |

## 5. Riesgos aceptados

| Riesgo | Tratamiento |
|---|---|
| **T5 — audio en el AOF de Redis.** Entre el `XADD` y la reescritura automática, los bytes siguen en el AOF del PVC de Redis | Dentro del clúster (AUTONOMIA-04 se cumple), con cota comprobable (NFR10.4). La alternativa, un Redis sin persistencia solo para `veridicus:audio` (D9), queda disponible por PR |
| **Audio conservado sin cifrado en reposo** | Mismo criterio que los reportes de U7 y que A-2 (sin KMS en el MVP): el archivo está en un PVC del clúster, con permisos solo del proceso, sin ruta que lo lea y con borrado por retención. Se presenta en la aprobación |
| **T16 — inundar la cola de audio** | Un analista graba a ritmo humano; la memoria de Redis la acota Infrastructure Design y la profundidad se vigila (`observability-requirements.md`) |
| **Bearer de la ruta interna en claro dentro del clúster** (cierra R-07) | `http` dentro del clúster: la `NetworkPolicy` de entrada solo admite `session-api` y no hay TLS interno en el MVP (U2 solo termina TLS en el Ingress) |
| **Tema largo que no cabe en la frase** | Una aclaración cuya frase pasa de 400 caracteres se rechaza (`409` `speech.text_rejected`) y se lee en pantalla; el analista no pierde la aclaración |

## 6. Precisiones a artefactos ya aprobados (NFR-U9-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las filas de la revisión 1 quedan como registro, marcadas
«Superado». Ninguna sale de una pregunta: todas salen de las fuentes.

| ID | Estado | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|---|
| — (rev. 1) | Superado | `contract-summary.md` C5 (pregunta abierta) | Audio en base64 con `maxLength: 8000000`. Sigue con P1 = A, ahora con el nombre de C25 de NFR-U9-02 y `413` | P1 = A |
| — (rev. 1) | Superado | `contract-summary.md` C5 | `turn.error.invalid_output`. Lo sustituye FD-U9-01 (`analysis.invalid_output`) | Cambio 01 |
| — (rev. 1) | Superado | `contract-summary.md` C1 | Ruta interna `{text}`. La sustituye FD-U9-04 (`observation_id`, `tema`, `template_version`) | Functional Design revisión 2 |
| — (rev. 1) | Superado | `contract-summary.md` C1 | `turn.audio_unavailable` y `question.not_approved`. Salen con la pregunta sugerida y el reintento por turno | Cambio 01 |
| — (rev. 1) | Superado | Functional Design de U4 (`Turn`) | `transcription_model_digest` en `Turn`. Lo guarda VoiceTurnState (`model_digest`) | Functional Design revisión 2 de U9 |
| — (rev. 1) | Superado | Catálogo de mensajes de U1 | Mensaje de más de 2 000 caracteres. `turn_max_chars` es ahora 20 000 (U4) | NFR-U4-01 |
| NFR-U9-01 | Propuesta | NFR Requirements de U11 (NFR-U11-11), Functional Design de U9 (§9, fila de U11) y `contract-summary.md` (C13) | **`transcribe` y `synthesize` se quedan en el puerto `ModelGateway` de U11, como ya dice C13 revisión 3 (`port.py` v2.0.0, SHOULD, solo locales), y los escribe U9 en B9.** NFR-U11-11 afirma que C13 solo declara `generate`; C13 los declara, y la tabla de contratos y la arista voice → incoherence-analyzer ponen a U9 como consumidor. Por eso no hace falta un PR de U1: los tipos de `contracts/python/model_calls.py` no cambian, y `Transcript` vive en `libs/model_gateway/speech.py` porque no cruza hacia el anonimizador. B11 entrega el puerto solo con `generate`, como su Functional Design. B9 añade los dos métodos al puerto, el adaptador local `libs/model_gateway/adapters/speech_local.py` y los *fakes*, en un solo PR que actualiza también los *fakes* de U11 (regla 5 de contract-summary). La fila de U11 en §9 del Functional Design de U9 se lee como «U11 es dueño del puerto; U9 aporta los métodos de voz y su adaptador» | C13; C14; `unit-of-work-dependency.md`; D13 |
| NFR-U9-02 | Propuesta | `contract-summary.md` (C25) y U1 (catálogo de límites) | Cifras de U9: `audio_max_bytes` = 6 000 000 (`bytes`) y `audio_max_seconds` = 120 (`s`). Cifras nuevas: `audio_base64_max_chars` = 8 000 000 (`chars`), `voice_deadline_base_s` = 360 (`s`), `voice_deadline_max_s` = 1 800 (`s`), `transcription_timeout_s` = 90 (`s`), `audio_claim_idle_ms` = 120 000 (`ms`), `audio_max_deliveries` = 2 (`deliveries`), `voice_key_ttl_s` = 1 920 (`s`), `tts_timeout_s` = 12 (`s`), `speech_route_timeout_s` = 15 (`s`), `speech_text_max_chars` = 400 (`chars`), `speech_audio_max_bytes` = 4 194 304 (`bytes`) y `audio_store_max_bytes` = 2 147 483 648 (`bytes`). Entran por PR de U1 antes del código de B9 | NFR-U1-07; `project.md` (catálogo único) |
| NFR-U9-03 | Propuesta | `contract-summary.md` (C5) | `audio_base64` declara `x-veridicus-limit: audio_base64_max_chars`; la reentrega se corta en `audio_max_deliveries` (2) y la siguiente va a `veridicus:audio:failed` con `analysis.system`; las entradas de fallidos llevan solo IDs y `code`; `session-api` borra con `XDEL` cada resultado ingerido; los TTL de las dos claves de FD-U9-06 son `voice_key_ttl_s` | NFR10.3, NFR10.14, NFR10.25 |
| NFR-U9-04 | Propuesta | `contract-summary.md` (C1 o contrato nuevo, FD-U9-04) | La ruta interna lleva además: Bearer con `VERIDICUS_SPEECH_TOKEN`, cuerpo estricto, `401` sin token, `422` con `rule_id` (`template_version`, `dt23`, `vocabulary`, `length`), respuesta de ≤ `speech_audio_max_bytes` y concurrencia 1 | NFR10.9, NFR10.22 |
| NFR-U9-05 | Propuesta | NFR Requirements e Infrastructure Design de U2 | (a) Prometheus raspa también `/metrics` de `audio-worker` (NFR15.2 de U2 solo nombra `session-api` y `semantic-agent`) y la regla de red lo admite. (b) Redis con `save ""`, `auto-aof-rewrite-percentage 100` y `auto-aof-rewrite-min-size 16mb`. (c) `model-whisper` y `model-tts` montan `/tmp` como `emptyDir` en memoria con `sizeLimit` y no registran cuerpos. (d) El tamaño del PVC de audio cubre `audio_store_max_bytes` más un 20 %. (e) `audio-worker` monta `/tmp` en memoria y nada escribible | NFR10.2, NFR10.4, NFR10.24, NFR15.1 |
| NFR-U9-06 | Propuesta | NFR Requirements de U3 (`ActorSystem`) | `ActorSystem` suma `audio-worker` para los cambios que trae un `TranscriptResult` (texto, error, liberación de corridas en espera) | NFR11.1 |
| NFR-U9-07 | Propuesta | Functional Design de U4 (supervisor de plazos) | El `run-supervisor` de U4 también vence los turnos de voz en `transcribing` con `voice_deadline_at` pasado (`analysis.timeout`, ≤ 30 s de retraso) y, en la misma transacción, libera las corridas en espera (BR9.2). FD-U9-07 solo dice que el supervisor no toca las corridas en espera | Cierra R-02 de la revisión 1; BR9.2 |
| NFR-U9-08 | Propuesta | `contract-summary.md` (C15) | Métricas de U9 de `observability-requirements.md` §2 por PR de U1, con etiquetas de enum (`outcome`, `error_code`, además del `origin` que C15 ya trae), nunca identificadores ni texto | NFR15.1 |
| NFR-U9-09 | Hecho | §11 del Functional Design de U9 (preguntas abiertas) | Respondidas sin preguntar: espera de corridas (NFR3.16), audio en disco (NFR10.24, NFR8.12), TTL (NFR10.25) y latencia y concurrencia de la síntesis (NFR3.12, NFR8.5) | §11 del Functional Design |

## 7. Hallazgos de la revisión 1

| Hallazgo | Cierre |
|---|---|
| R-01 (cota del AOF) | NFR10.4 con cota comprobable y prueba de reescritura automática; NFR-U9-05 (b) |
| R-02 (cambios a U4 sin precisión) | El Functional Design revisión 2 los recoge (FD-U9-07, FD-U9-08); el vencimiento del plazo de voz queda en NFR-U9-07 |
| R-03 (tercera entrega fuera del plazo) | `audio_max_deliveries` = 2 y base de 360 s: 90 + 120 + 90 = 300 s deja 60 s de margen (NFR3.5, NFR10.14) |
| R-04 («por turno» como transcripción) | NFR3.1 y NFR3.2 son la transcripción; NFR3.3 declara sus cifras como derivadas (U11 + transcripción) |
| R-05 (CPU compartida y corte de Whisper) | NFR3.15 mide la transcripción con una corrida en paralelo; D2 declara que el servidor no cancela al cortarse la conexión |
| R-06 (puerto de aprobación de U8) | Existe: `is_observation_approved` (NFR10.7 de U8, NFR-U8-07) |
| R-07 (Bearer en claro) | Riesgo aceptado en §5 |
