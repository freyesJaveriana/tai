# Requisitos de seguridad — U9 voice

**Insumos.** Flujos F1–F4, la frontera AUTONOMIA-04 (§1) y los cambios X1–X5 (§4) de
`functional-design/functional-spec.md` (functional-spec); reglas BR1–BR7 de `functional-design/rules.md`
(rules); FR10.2, FR10.4 y NFR1, NFR4, NFR5, NFR10–NFR12 de
`inception/requirements-analysis/requirements.md` (requirements); C1 (`/voice-turns`,
`/questions/{id}/audio`), C5, C13, C14 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1 y P2 de `nfr-requirements-questions.md`; reglas AUTONOMIA-01..05 de
`team.md` y prohibiciones de `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de team-practices: nivel 0
(unitarias, contratos y políticas, cada PR), nivel 1 (integración con PostgreSQL y Redis reales, cada
PR), nivel 2 (evaluación de IA; para U9, la **corrida de voz** de `reliability-requirements.md` §3),
nivel 3 (E2E y humo) y manual. Los comandos están en `tech-stack-decisions.md` §5. La autenticación, el
anti-CSRF y la convención de auditoría vienen de U3; los *timeouts*, la cola y los logs del turno, de
U4; la `NetworkPolicy` de salida denegada y `models.lock`, de U2. Aquí solo se exige que U9 los use y lo
que U9 añade.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| AnalystConsole (grabación y «Escuchar audio») | Navegador del analista | Audio crudo **solo** hacia `session-api` por C1 (HTTPS, mismo origen); WAV de la pregunta de vuelta. Nada a terceros: ni Web Speech API ni SDK externos (NFR1.3). El audio vive en memoria y nunca en el almacenamiento del navegador (NFR10.5) | Confidencial |
| `session-api` (ConsoleApi, InterviewSession) | Dentro del clúster | Audio en tránsito (memoria, nunca disco, NFR10.2) hacia Redis; texto transcrito a PostgreSQL y a C2; texto de la pregunta aprobada hacia `audio-worker` | Confidencial |
| Redis (`veridicus:audio`, `veridicus:transcripts`) | Dentro | Audio en base64 hasta `XDEL`; texto hasta `XDEL`. Riesgo residual del AOF declarado en NFR10.4 | Confidencial |
| `audio-worker` (SpeechProcessing) | Dentro; pod etiquetado como de datos sin anonimizar, bajo la `NetworkPolicy` de salida denegada | Audio hacia `model-whisper`; texto de la pregunta hacia `model-tts`; solo alcanza Redis, esos dos servidores y DNS (NFR1.1) | Confidencial |
| `model-whisper` y `model-tts` | Dentro (pods de U2 sin salida a internet) | Reciben audio o texto; no lo registran ni lo dejan en el disco del nodo (NFR10.6, NFR10.2) | Confidencial en tránsito |
| ModelGateway (adaptadores `transcribe` y `synthesize`) | `libs/`, en `audio-worker` | Solo URL internas del clúster (NFR1.2) | — |

**Ningún componente de U9 llama fuera del clúster**, así que no aplica el anonimizador (U10). Aunque
en el MVP todo audio es sintético (NFR12.1), se trata como dato confidencial.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | `audio-worker` (o un servidor de modelos) envía audio o texto a internet | Information disclosure | Alto | NFR1.1, NFR1.2 |
| T2 | El navegador transcribe o sintetiza con un servicio de terceros (Web Speech API de Chrome envía audio a Google) | Information disclosure | Alto | NFR1.3 |
| T3 | El audio queda en el almacenamiento del navegador, en el disco de un pod o en un archivo temporal de subida | Information disclosure | Alto | NFR10.2, NFR10.5 |
| T4 | El audio o el texto quedan en los *streams* después de usarse, o en las entradas de fallidos | Information disclosure | Alto | NFR10.3 |
| T5 | El audio persiste en el AOF o en un RDB de Redis hasta la reescritura | Information disclosure | Medio | NFR10.4 (riesgo residual declarado, §5) |
| T6 | Audio, texto transcrito o texto de la pregunta en logs, métricas o en el cuerpo de un error | Information disclosure | Alto | NFR10.6 |
| T7 | Un analista envía voz a una sesión ajena o escucha la pregunta de otra sesión; un `admin` envía voz | Elevation of privilege | Medio | NFR10.7 |
| T8 | Se sintetiza una pregunta no aprobada y llega al compareciente sin decisión humana (AUTONOMIA-03) | Elevation of privilege | Alto | NFR10.8 |
| T9 | Otro pod llama a la ruta interna de síntesis de `audio-worker` | Spoofing | Medio | NFR10.9 |
| T10 | Archivo enorme, de duración falsa o binario disfrazado que agota memoria o explota el decodificador | Denial of service, Tampering | Medio | NFR10.1, NFR10.2 |
| T11 | Un modelo de Whisper o una voz alterados, o un formato con código ejecutable | Tampering | Medio | NFR10.10 |
| T12 | Alguien corrige el texto transcrito para cambiar lo que dijo el compareciente | Tampering, Repudiation | Medio | NFR10.11, NFR11.1 |
| T13 | Whisper «alucina» palabras que nadie dijo (p. ej. frases de subtítulos en silencio) | Tampering | Medio | NFR4.2 (`reliability-requirements.md`), NFR10.11 (rótulo «transcripción automática») |
| T14 | Una instrucción dictada en voz («ignora lo anterior…») cambia la evaluación | Tampering | Alto | NFR5.1 |
| T15 | No se sabe qué modelo transcribió un turno | Repudiation | Bajo | NFR10.10, NFR11.1 |
| T16 | Un analista autenticado inunda la cola de audio (hasta 8 MB por mensaje en Redis) | Denial of service | Bajo | Riesgo aceptado (§5) |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | `audio-worker` no tiene salida a internet (BR6.1). | El render del chart (`values-cpu.yaml` y `values-gpu.yaml`) da al pod `audio-worker` la etiqueta de datos sin anonimizar y lo cubre la `NetworkPolicy` de negar todo; su salida permitida es **solo** Redis (6379), `model-whisper` (8080), `model-tts` (8080) y DNS; su entrada, solo `session-api` en el puerto interno de síntesis y Prometheus en `/metrics`. La política Kyverno falla con un control negativo (pod sin etiqueta o con una regla de salida a `0.0.0.0/0`). En el clúster, `kubectl exec` en `audio-worker` con `curl -m 5 https://example.org` termina con código ≠ 0. | Nivel 0 y manual antes de la sustentación |
| NFR1.2 | Las URL de modelos y de síntesis son internas (BR6.2, AC9.1.4). | `VERIDICUS_WHISPER_URL`, `VERIDICUS_TTS_URL` (en `audio-worker`) y `VERIDICUS_SPEECH_URL` (en `session-api`) deben ser `http(s)://<nombre>.<namespace>.svc.cluster.local[:puerto]` o un nombre de servicio sin puntos; cualquier otra (IP pública, dominio externo, `localhost` fuera de pruebas) impide arrancar con un log que nombra el ajuste. Una prueba por forma rechazada y su control positivo, con el mismo validador de U4 (NFR1.1 de U4). | Nivel 0 |
| NFR1.3 | La consola no usa servicios de voz del navegador ni de terceros. | Una regla de ESLint (`no-restricted-globals` / `no-restricted-properties`) prohíbe `speechSynthesis`, `SpeechSynthesisUtterance`, `SpeechRecognition` y `webkitSpeechRecognition` en `frontend/src`; la grabación solo sube a la ruta relativa `/sessions/{id}/voice-turns` (mismo origen). Control negativo: un archivo de prueba con `speechSynthesis.speak` hace fallar el *lint*. | Nivel 0 |

### NFR5 — Resistencia adversarial

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR5.1 | Una inyección dictada se trata como dato, igual que escrita (BR4.1). | La corrida de voz incluye un clip sintético con el texto de inyección del Escenario A del PRD. El texto transcrito se envía después como turno escrito en otra sesión con el mismo escenario y umbral: los dos turnos producen el mismo conjunto de alertas (por afirmación y pasaje citado). Como el texto es idéntico, la diferencia solo puede venir de U9; la resistencia de fondo la garantiza NFR5.1 de U4. | Nivel 2 (corrida de voz) |

### NFR10 — Seguridad de la aplicación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | El audio se valida antes de crear el turno (BR2.3). | En este orden y sin crear filas ni publicar en C5 si algo falla: rol y dueño (NFR10.7); sesión `open`; tamaño: el servidor **deja de leer** el cuerpo al pasar `VERIDICUS_VOICE_MAX_BYTES` = 6 000 000 bytes del archivo (P1 = A); formato declarado `wav` o `mp3`; cabecera real (RIFF/WAVE PCM o trama MPEG/ID3, sin fiarse de `Content-Type`); duración ≤ 120 s leída de la cabecera; `client_request_id` UUID. Cualquier fallo → `422` `validation.invalid_request` con el motivo en `detail` (en español, sin eco del contenido). Pruebas de nivel 1: 10 MB, MP3 con extensión WAV, WAV de 121 s, PNG renombrado, cuerpo vacío; cada una 422, 0 filas, `XLEN veridicus:audio` sin cambio y crecimiento de memoria del proceso ≤ 20 MiB con el archivo de 10 MB. | Nivel 1 |
| NFR10.2 | El audio nunca toca un disco por la aplicación (BR3.5). | `session-api` lee la subida en memoria (el analizador *multipart* no hace *spool* a archivo temporal; prueba de nivel 1 que hace fallar `tempfile` y la subida de 5 MB sigue respondiendo 202). `audio-worker` no monta ningún volumen escribible (política de nivel 0). `model-whisper` y `model-tts` solo escriben en un `/tmp` `emptyDir` con `medium: Memory` (precisión a U2, §6). Ninguna ruta de U9 escribe audio en PostgreSQL. | Nivel 0 y nivel 1 |
| NFR10.3 | Los *streams* no conservan audio ni texto tras usarlos (BR3.5). | `audio-worker` hace `XACK` + `XDEL` del mensaje de audio con **cualquier** resultado (texto, vacío, error, plazo vencido, duplicado, mensaje a fallidos). `session-api` hace `XACK` + `XDEL` de cada `TranscriptResult` ingerido (como NFR10.9 de U4). Las entradas de `veridicus:audio:failed` y `veridicus:transcripts:failed` llevan solo `message_id`, `turn_id`, `attempt` y `code`, recortadas a 1 000. Prueba de nivel 1 por cada resultado: tras procesar, `XLEN veridicus:audio` = 0, `XLEN veridicus:transcripts` = 0 y `XRANGE` de los fallidos no contiene la cadena centinela del audio ni del texto. | Nivel 1 |
| NFR10.4 | El rastro del audio en la persistencia de Redis está acotado y declarado. | Redis corre sin instantáneas RDB (`save ""`) y con AOF `everysec` de U2: un `XADD` de audio queda en el AOF del PVC de Redis, **dentro del clúster**, hasta la siguiente reescritura (`BGREWRITEAOF`), aunque ya se haya hecho `XDEL`. Prueba de nivel 1 con Redis real configurado igual: tras procesar un audio con un patrón centinela de 64 bytes, el patrón **sí** aparece en el AOF (lo que documenta el riesgo); tras `BGREWRITEAOF`, 0 apariciones en el directorio `appendonlydir`. `auto-aof-rewrite-min-size 16mb` (precisión a U2) hace que la reescritura ocurra como mucho tras unos 2 audios de 120 s. | Nivel 1 |
| NFR10.5 | El navegador no guarda el audio (BR1.x, functional-spec §1). | La grabación vive en memoria; nunca en `localStorage`, `sessionStorage`, IndexedDB, Cache Storage ni en un *service worker*. Las URL `blob:` se revocan al enviar o descartar, y las pistas del micrófono se detienen (`MediaStreamTrack.stop()`) al detener, al llegar a 120 s y al salir de la pantalla. Vitest comprueba `stop()` y `revokeObjectURL`; Playwright de nivel 3, tras grabar y enviar, comprueba los cuatro almacenamientos vacíos de audio (`indexedDB.databases()` sin bases nuevas) y 0 pistas activas. | Nivel 0 y nivel 3 |
| NFR10.6 | Ni el audio ni el texto aparecen en logs, métricas o errores (BR6.3). | Campos de log permitidos: `session_id`, `turn_id`, `question_id`, `message_id`, `attempt`, `code`, `byte_size`, `audio_seconds` y duraciones. Prueba de nivel 1 con tres centinelas (un patrón de bytes en el audio *fake*, una cadena en la transcripción del Whisper *fake* y otra en el texto de la pregunta): 0 apariciones en los logs capturados de `session-api` y `audio-worker`, incluidos los de error, y en el cuerpo de cada 4xx/5xx (el manejador de Problem Details de `libs/` nunca devuelve el `input` de la validación). Manual antes de la sustentación: tras la corrida E2E de voz en el clúster, los logs de `model-whisper` y `model-tts` no contienen la frase centinela del clip. | Nivel 1 y manual |
| NFR10.7 | Solo el dueño envía voz y escucha la pregunta (BR2.1, BR5.4, ADR-009). | `POST /sessions/{id}/voice-turns`: `x-veridicus-roles: [analista]`, `x-veridicus-owner-only: true` y `X-CSRF-Token` obligatorio. `GET /questions/{id}/audio`: los mismos rol y dueño (X4 de functional-spec). Pruebas `403` `auth.forbidden`: otro analista, `admin` e identidad de servicio en ambas rutas, y POST sin anti-CSRF; en todas, 0 filas, 0 `XADD` y 0 llamadas al TTS *fake*. | Nivel 1 |
| NFR10.8 | Solo se sintetiza una pregunta aprobada y solo al pulsar (BR5.1, BR5.2, AUTONOMIA-03). | La ruta consulta el puerto `is_question_approved(question_id)` de U8 (NFR10.7 de U8) antes de llamar a la síntesis; `proposed` o `discarded` → `409` `question.not_approved`. El TTS *fake* cuenta **0 llamadas** en: pregunta sin aprobar, pregunta aprobada que nadie escucha, y todo el ciclo de vida de una pregunta en la consola. El botón «Escuchar audio» está deshabilitado salvo con `approved` y mientras una petición está en curso (sin dobles llamadas). | Nivel 0 y nivel 1 |
| NFR10.9 | La ruta interna de síntesis solo la usa `session-api`. | `audio-worker` expone `POST /internal/v1/speech` en su puerto interno (precisión a C1/C5, §6). Exige `Authorization: Bearer` con `VERIDICUS_SPEECH_TOKEN` (Secret por referencia, comparación en tiempo constante) → si no, `401` sin llamar al TTS; cuerpo estricto `{ "text": string }` de 1 a 300 caracteres (el límite de la pregunta de U8) → si no, `422`. La `NetworkPolicy` de entrada solo admite `session-api` (NFR1.1). La respuesta es `audio/wav` de ≤ 2 MB. Pruebas de nivel 1 sin token, con token erróneo y con 301 caracteres. | Nivel 0 y nivel 1 |
| NFR10.10 | Los modelos de voz son los fijados (BR6.4). | Whisper `base` en formato CTranslate2 int8 (`model.bin`, `config.json`, `tokenizer.json`, `vocabulary.*`) y la voz Piper (`.onnx` + `.onnx.json`) con revisión y `sha256` en `deploy/models.lock` (U2 los verifica al arrancar, NFR10.4 de U2). Ningún archivo `.pt`, `.pkl` ni `.bin` de PyTorch, ni `trust_remote_code`. Cada `TranscriptResult` con texto lleva `model_digest` = `VERIDICUS_WHISPER_MODEL_SHA256` (el `sha256` de `model.bin` en `models.lock`), y `session-api` lo guarda con el turno (precisión, §6). Prueba de nivel 0 sobre el formato del *lock* y de nivel 1 sobre el campo. | Nivel 0 y nivel 1 |
| NFR10.11 | El texto transcrito no se edita y se rotula (BR1.6, BR4.4). | No existe ruta de C1 que cambie `Turn.text` (prueba de contrato sobre el OpenAPI); todo turno con `origin: voice` muestra «Turno por voz (transcripción automática)» (Vitest y nivel 3). Un turno de voz que falló al transcribir responde `409` `turn.audio_unavailable` en `POST /turns/{n}/retry` (X2). | Nivel 0 y nivel 3 |
| NFR10.12 | Los errores de U9 son Problem Details con `code` del catálogo. | `422` `validation.invalid_request`, `403` `auth.forbidden`, `409` `session.finalized`, `session.not_open`, `question.not_approved` y `turn.audio_unavailable`, `503` `speech.unavailable` (X3); `detail` en español, sin trazas ni texto del modelo. Una prueba por `code`. | Nivel 0 y nivel 1 |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | El turno de voz deja rastro como cualquier turno. | El turno nace con `origin: voice`; sus transiciones (`queued`·`transcribing` → `processing` → `retrieving` … o `error`) entran en el historial de U4 con actor y hora; `model_digest` de la transcripción queda guardado; el usuario de la aplicación no tiene `UPDATE` sobre `Turn.text` una vez escrito (prueba común de U3). | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Todo audio del repositorio y de la CI es sintético. | Los clips de prueba y de la corrida de voz se **generan** con la voz Piper fijada a partir de textos sintéticos marcados (catálogo de U1); no se graban voces humanas. `scripts/check-synthetic-audio.sh` falla si un `.wav` o `.mp3` del repositorio no figura en `evaluation/voice/manifest.json` con su `sha256` y su texto de origen; los clips grandes no se versionan, se regeneran. Durante el ensayo de la demostración la voz del analista no se guarda en ningún sitio (NFR10.2–NFR10.5). | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U9 |
|---|---|
| AUTONOMIA-01 | U9 no aplica nada al clúster: la `NetworkPolicy`, los modelos y los ajustes entran por PR (NFR1.1, NFR10.10); la verificación manual con `curl` es de lectura |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.8 (ninguna pregunta llega al compareciente sin aprobación), NFR10.11 y NFR11.1 (la transcripción es entrada rotulada, no un hallazgo, y no se reescribe). U9 no produce calificaciones ni etiquetas |
| AUTONOMIA-04 | §1, NFR1.1–NFR1.3, NFR10.2–NFR10.6, tarea de `NetworkPolicy` para `audio-worker` (NFR1.1) |
| AUTONOMIA-05 | No aplica directamente: el turno transcrito pasa por la guardia del umbral de U4 sin cambios (BR4.1, NFR5.1) |

## 5. Riesgos aceptados

- **T5 — audio en el AOF de Redis.** Entre el `XADD` y la siguiente reescritura, los bytes del audio
  siguen en el archivo AOF del PVC de Redis aunque el *stream* ya no los tenga. No sale del clúster
  (AUTONOMIA-04 se cumple) y la reescritura está acotada (NFR10.4). La alternativa sin este riesgo, un
  Redis aparte sin persistencia solo para `veridicus:audio`, se descartó para el MVP
  (`tech-stack-decisions.md` D9) y queda disponible por PR.
- **T16 — inundar la cola de audio.** Un analista autenticado puede encolar muchos audios de hasta
  8 MB en base64. En el MVP hay un solo analista que graba a ritmo humano; la memoria de Redis la acota
  Infrastructure Design y la profundidad se vigila con `veridicus_audio_queue_depth`
  (`observability-requirements.md`). No se añade un límite por sesión porque exigiría un `code` nuevo.

## 6. Precisiones a artefactos ya aprobados

Estas decisiones precisan artefactos ya aprobados o de otras unidades. No los edité; decides en la
aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C5, pregunta abierta) | **Cierra la pregunta abierta de C5:** el audio sigue en base64 dentro de `AudioToTranscribe`; `audio_base64` lleva `maxLength: 8000000` (base64 de `VERIDICUS_VOICE_MAX_BYTES` = 6 000 000); más grande se rechaza con `422` antes de encolar; se borra con `XDEL` al confirmarlo. Sin volumen compartido | P1 = A |
| `contract-design/contract-summary.md` (C5) | `error_code` añade `turn.error.invalid_output` (X1, ya propuesto en Functional Design) y lo usa también para un texto de más de 2 000 caracteres (NFR10.20); las entradas `<stream>:failed` llevan solo identificadores y `code`; `session-api` borra con `XDEL` cada `TranscriptResult` ingerido | NFR10.3, NFR10.20 |
| `contract-design/contract-summary.md` (C1 o contrato nuevo de U9) | Ruta interna `POST /internal/v1/speech` de `audio-worker` (Bearer, `{text}` 1–300 → `audio/wav`), por la que ConsoleApi pide la síntesis a SpeechProcessing; no la ve el navegador | NFR10.9, D4 de `tech-stack-decisions.md` |
| `contract-design/contract-summary.md` (C1 `ErrorCode`) | Confirma `turn.audio_unavailable`, `speech.unavailable` (X2, X3) y `question.not_approved` (de U8); `GET /questions/{id}/audio` declara `x-veridicus-roles: [analista]`, `x-veridicus-owner-only: true` y la respuesta `503` (X4) | NFR10.7, NFR10.8, NFR10.12 |
| NFR Requirements y chart de U2 (red) | Tabla de dependencias de red: `session-api` → `audio-worker` (puerto interno de síntesis); `audio-worker` → `model-tts` (8080); entrada de `audio-worker` solo desde `session-api` y Prometheus; Prometheus también recoge `/metrics` de `audio-worker`. Falta el subchart `model-tts` en `deploy/veridicus/charts/` | NFR1.1, D3 |
| NFR Requirements de U2 (Redis, D6) | Añade `save ""` (sin RDB) y `auto-aof-rewrite-min-size 16mb` a la configuración de Redis | NFR10.4 |
| NFR Requirements de U2 (servidores de modelos) | `model-whisper` y `model-tts` montan `/tmp` como `emptyDir` con `medium: Memory` y `sizeLimit` (la subida *multipart* del servidor puede hacer *spool* a disco); ninguno registra el cuerpo de las peticiones | NFR10.2, NFR10.6 |
| `deploy/models.lock` (U2) | Añade Whisper `base` CTranslate2 int8 y la voz Piper en español con su `sha256` | NFR10.10 |
| Functional Design de U4 (`Turn`) | `Turn` guarda `transcription_model_digest` (nulo en turnos escritos) | NFR10.10, NFR11.1 |
| Catálogo de mensajes de U1 | En un turno de voz, el mensaje de `turn.error.invalid_output` dice: «No se pudo usar la transcripción (vacía o de más de 2 000 caracteres). Graba de nuevo en partes más cortas o escribe el turno.» | NFR10.20 |
| `contract-design/contract-summary.md` (C15) | Añade las métricas de U9 de `observability-requirements.md` §2, por un PR de U1 como las de U3 y U4 | NFR15.1 |
