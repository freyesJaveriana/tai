# Especificación de infraestructura — U9 voice

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen las dos máquinas, `values-gpu.yaml`, los nombres `veridicus-whisper`, `veridicus-tts` y
  `veridicus-audio-worker`, las tres banderas de voz, los ajustes de voz que pasaron a C25, la ruta
  `/questions/{id}/audio` y el «sin almacenamiento nuevo». Entran el audio conservado en el PVC
  `veridicus-audio` (solo la API y el `Job` de retención), la aclaración por
  `GET /conductor-observations/{id}/audio`, la espera de corridas, la cota de 1 920 s del audio en Redis y la
  entrada a la síntesis solo desde la API.
- **Numeración.** §1–§8 conservan su tema. La tabla de precisiones de la revisión 1 (§9) se retira entera
  (IDS-U9-01) y la sustituye la tabla IDS-U9-01 a IDS-U9-21. §10 (nueva) cierra los hallazgos de
  `reviews/review-01.md`.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; Minikube con 50 GiB y
  16 CPU, decidido por U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2): performance-design §1–§9 (topes por pod en §7);
  security-design §1–§14 y la tabla NFRD-U9-01 a NFRD-U9-16; scalability-design §1–§6; reliability-design
  §1–§13; observability-design §1–§4; logical-components §1–§6 (entrega a U2 en §6).
- `functional-design/functional-spec.md` (functional-spec: F1–F8 y la frontera de §1).
- SpeechProcessing, InterviewSession y ModelGateway de `inception/domain-design/components.md` (components).
- C1, C5, C13, C14, C16 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements/tech-stack-decisions.md` (D1–D16, §2, §5 y §6).
- Respuestas P1 = A, P2 = A y P3 = A de la revisión 1 (`infrastructure-design-questions.md`); P3 = A se lee
  ahora sobre una sola máquina (IDS-U9-02).
- Infrastructure Design revisión 2 de U2 (§2, §3, §4 e IDS-U2-01 a IDS-U2-15), U4 (IDS-U4-01 a IDS-U4-15), U5
  (IDS-U5-01 a IDS-U5-12), U6 (IDS-U6-01 a IDS-U6-15) y U11 (IDS-U11-04, -07 a -09).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

U9 añade al clúster el `Deployment` `audio-worker` (imagen propia), la imagen de `model-tts`
(`services/tts-server/`) y el código de voz de la API y del trabajador de `session-api`. U2 despliega
`model-whisper`, `model-tts`, el PVC `veridicus-audio`, la red y el `Ingress` `veridicus-voice`. Todo se escribe
en Code Generation (B9); aquí solo se fija su forma y sus valores.

## 1. Despliegue · cambia

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Contenedores en el Minikube de U2: `audio-worker` (1 réplica), `model-tts` (imagen `services/tts-server/`, P2 = A) y `model-whisper` (U2, imagen en IDS-U9-04); la API y el trabajador de `session-api` llevan el código de voz en su imagen | D10; logical-components §1 y §6 |
| Activación | `voice.enabled: true` por defecto en `values-cpu.yaml`, el único archivo de valores; una sola bandera enciende o apaga los tres pods de voz y las reglas de red que los nombran (IDS-U9-02) | P3 = A sobre una sola máquina; NFR2.2 |
| Perfil de cómputo | Todo en CPU; ningún render pide `nvidia.com/gpu` (política `no-gpu-requests` de U2) | IDS-U2-02; IDS-U9-13 |
| Máquina | Una sola: Minikube 50 GiB y 16 CPU sobre WSL2; la voz convive con el juez y el verificador | IDS-U2-01 |
| Red de entrada | `veridicus-voice` para `POST /api/v1/sessions/{id}/voice-turns` (tope 6 065 536) y `veridicus-web` para el resto, incluido el audio de la aclaración; los dos con el patrón sin disco de U2 (§4) | NFR10.2, NFR10.5; U2 §2.4 |
| Red interna | Negar todo de U2 más las filas de §5; `audio-worker` lleva `veridicus.io/data-class: sensitive` | NFR1.1, NFR10.9; AUTONOMIA-04 |
| Almacenamiento | `veridicus-audio` (3 GiB, de U2) solo en la API y en `retention-job`, para el audio conservado con autorización; `audio-worker`, `model-whisper` y `model-tts` sin volúmenes escribibles (solo `/tmp` en memoria); el AOF de `veridicus-redis` acotado por el `AofRewriteRequester` | NFR10.24, NFR10.27; security-design §2 y §12; NFRD-U2-15 |
| Modelos | Whisper `base` en CTranslate2 y voz Piper `es_MX-ald-medium` en ONNX, fijados en `deploy/models.lock` y verificados por `verify-model` (§3) | P1 = A; IDS-U2-08 |
| Imágenes | `audio-worker` y `tts-server` sobre `python:3.12-slim` por digest, UID 10001, *helper* `_securityContext.tpl` de U2; en GHCR por SHA, nunca `latest` | `team.md`; Pod Security `restricted` |
| IaC | Subchart `audio-worker` y valores de `model-whisper` y `model-tts` dentro de `deploy/veridicus`; el humano aplica el artefacto fusionado o lo sincroniza Argo CD | AUTONOMIA-01 |
| Estrategia | `audio-worker`: `RollingUpdate` (`maxSurge: 1`, `maxUnavailable: 0`): dos consumidores del grupo no duplican efectos. `model-whisper` y `model-tts`: `Recreate`, como todo `model-*` | scalability-design §2; U2 §5 |

### 1.1 Recursos frente a los picos (NFR8.1–NFR8.4)

Cifras de U2 §4 sin cambios. Regla: 1,2 × (pico + `/tmp` en memoria) ≤ `limits.memory`.

| Contenedor | Pico (performance-design §7) | `/tmp` en memoria | 1,2 × (pico + `/tmp`) | `requests` → `limits` (U2) | ¿Cabe? |
|---|---|---|---|---|---|
| `model-whisper` | ≤ 1 GiB (120 s de audio) | 64 MiB | 1 277 MiB | 1 / 768 MiB → 4 / 1,3 GiB | Sí |
| `model-tts` | ≤ 512 MiB | **16 MiB** (IDS-U9-06) | 634 MiB | 0,5 / 384 MiB → 2 / 640 MiB | Sí |
| `audio-worker` | ≤ 256 MiB | 16 MiB | 327 MiB | 0,1 / 192 MiB → 0,5 / 384 MiB | Sí |
| API de `session-api` | ≈ 14 MB por subida, sin acumulación (NFR8.4) | El de U3 | — | Los de U2 con la petición IDS-U12-01 | Sí, dentro del margen de U3 y U12 |
| `veridicus-redis` | `maxmemory` 384 MB + búfer de un `XADD` de 8 MB + copia en escritura de la reescritura | — | — | 0,1 / 256 MiB → 0,5 / 512 MiB | Se mide en nivel 1 (IDS-U9-05) |

### 1.2 Presupuesto de la máquina

| Bloque | CPU pedida | Memoria pedida | Memoria límite |
|---|---|---|---|
| Voz (`model-whisper`, `model-tts`, `audio-worker`), igual que U2 §4 | 1,6 | ≈ 1,3 GiB | ≈ 2,3 GiB |
| Cambio que pide U9 | 0 | 0 | 0 |

U9 **no cambia ninguna cifra de pod**: el total sigue en ≈ 14,5 CPU y ≈ 41 GiB pedidos frente a 16 CPU y 50 GiB
(U2 §4). Con la voz apagada (`voice.enabled: false`) se liberan 1,6 CPU y ≈ 1,3 GiB pedidos; es la palanca
para una medición que necesite holgura, siempre por PR.

### 1.3 Sondas (C16, NFR10.17)

| Proceso | `startupProbe` | `livenessProbe` | `readinessProbe` |
|---|---|---|---|
| `audio-worker` | `/healthz` en 8080, periodo 5 s, hasta 300 s (calentamiento de Whisper y de la síntesis) | `/healthz`, periodo 10 s, plazo 2 s, 3 fallos: falla solo si el último latido tiene más de 45 s **y** no hay un mensaje en curso con `busy_until` + 15 s sin vencer (NFRD-U9-07); el proceso no se mata a sí mismo | `/readyz`, periodo 10 s: configuración, Redis, `model-whisper`, `model-tts` y los dos calentamientos |
| `model-tts` | `/healthz` cada 5 s, hasta 120 s | `/healthz` cada 15 s | `/readyz` cada 5 s: voz cargada y síntesis de calentamiento hecha |
| `model-whisper` | La de U2 (`/health` cada 5 s, hasta 120 s) | La de U2 | La de U2 |

## 2. Servicios de infraestructura · cambia

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `audio-worker` | other (trabajador + ruta interna) | Un proceso (D10): bucle consumidor del grupo `audio-worker` en `veridicus:audio` (`XREADGROUP BLOCK 5000 COUNT 1`, `socket_timeout` 6 s, un audio a la vez) y FastAPI en un hilo. Puerto `http` 8080 (`/healthz`, `/readyz`, `POST /internal/v1/speech` con Bearer y semáforo de 1 con espera de 2 s); puerto `metrics` 8081; `AofRewriteRequester`; sin volúmenes salvo `/tmp` de 16 MiB | D10; NFRD-U9-06, NFRD-U9-07, NFRD-U9-13 |
| `model-tts` (imagen de U9, P2 = A) | other (modelo) | `services/tts-server/`: FastAPI + Uvicorn `--no-access-log`, `piper-tts` fijado en su lockfile, 2 hilos de ONNX Runtime, concurrencia 1; `POST /v1/audio/speech` con `{model, input, voice, response_format: "wav"}` e `input` de 1 a `speech_text_max_chars` (400) caracteres, o `422`; respuesta ≤ `speech_audio_max_bytes`; nunca registra el cuerpo; puerto 8080 | El adaptador `synthesize` de `libs/model_gateway` (D13) habla esta forma; C14 deja el TTS sin estándar |
| `model-whisper` (U2) | other (modelo) | `faster-whisper` tras `/v1/audio/transcriptions` (C14), `compute_type=int8`, `cpu_threads = 4`, `beam_size = 1`, VAD, idioma `es`, temperatura 0, una transcripción a la vez, modo sin conexión, sin registro del cuerpo; imagen en IDS-U9-04 | D1, D2; U2 §2.1 |
| `veridicus-redis` (U2) | queue | *Streams* `veridicus:audio` (grupo `audio-worker`) y `veridicus:transcripts` (grupo `session-api-transcripts`), y sus `:failed` con `MAXLEN ~ 1000`; claves `veridicus:transcribed:{turn_id}:{attempt}` y `veridicus:voice-cancelled:{session_id}` con TTL `voice_key_ttl_s` (1 920 s); `XTRIM veridicus:audio MINID <ahora − 1920 s>` cada 15 s en el supervisor del trabajador; `BGREWRITEAOF` sin renombrar; `maxmemory 384mb` con `noeviction`; PVC de 2 GiB | security-design §2; scalability-design §3; NFRD-U9-05; capacidad en §2.2 |
| `veridicus-pg` (U2) | database | Sin roles nuevos: la API y el trabajador usan `veridicus_app` con el *pool* de U3 y U4; `veridicus_app` sin `DELETE` sobre las tablas de voz, solo `veridicus_retention` borra; índice parcial sobre los turnos en `transcribing` y tablas `voice_turn_state`, `turn_audio` y `run_publication_hold` por la migración de B9 en su propio PR | NFR11.2; performance-design §3 |
| `veridicus-audio` (U2) | object-store | PVC `ReadWriteOnce` de 3 GiB (≥ 1,2 × `audio_store_max_bytes` = 2 147 483 648); montado en la API en `VERIDICUS_AUDIO_DIR`, con subdirectorio `audio/` `0700` creado por el proceso y archivos `0600`; cuota por contador del proceso; `TurnAudioSweeper` al arrancar; *prune* desactivado | D14; NFRD-U2-15; IDS-U9-08 |
| `ingress-nginx` (U2) | load-balancer | `veridicus-voice` con la expresión de U2 y el tope 6 065 536; el audio de la aclaración sale por `veridicus-web` (§4) | NFR10.2, NFR10.5 |
| Volumen de modelos (U2) | object-store | `/srv/veridicus/models` en el ext4 de WSL2, PV estático de solo lectura; `verify-model` en `model-whisper` y `model-tts` | IDS-U2-05 |
| `cdn`, `search`, DNS propio | — | No aplica | CoreDNS de U2 |

### 2.1 Ajustes de los contenedores (prefijo `VERIDICUS_`) · cambia

Las cifras de voz viven en `contracts/limits.v1.yaml` (C25) y no en los valores: `audio_max_bytes` 6 000 000,
`audio_base64_max_chars` 8 000 000, `voice_body_max_bytes` 6 016 384 (NFRD-U9-03), `voice_deadline_base_s` 360
y `voice_deadline_max_s` 1 800, `transcription_timeout_s` 90, `audio_claim_idle_ms` 120 000,
`audio_max_deliveries` 2, `tts_timeout_s` 12, `speech_route_timeout_s` 15, `speech_text_max_chars` 400,
`speech_audio_max_bytes` 4 194 304, `voice_key_ttl_s` 1 920 y `audio_store_max_bytes` 2 147 483 648. Una
`VERIDICUS_LIMIT_<NOMBRE>` solo puede bajarlas (`check-limits-env.sh` de U2).

| Variable | Valor en `values-cpu.yaml` | Procesos |
|---|---|---|
| `VERIDICUS_WHISPER_URL` | `http://model-whisper.veridicus.svc.cluster.local:8080` (U2) | `audio-worker` |
| `VERIDICUS_TTS_URL` | `http://model-tts.veridicus.svc.cluster.local:8080` (U2) | `audio-worker` |
| `VERIDICUS_SPEECH_URL` | `http://audio-worker.veridicus.svc.cluster.local:8080` | API de `session-api` |
| `VERIDICUS_WHISPER_MODEL`, `VERIDICUS_WHISPER_MODEL_SHA256` | `base` y el `sha256` de `model.bin` copiado de `models.lock` (una prueba de nivel 0 exige que coincidan) | `audio-worker` |
| `VERIDICUS_SPEECH_TEMPLATE` | Ruta de `contracts/integrity/clarification-speech.v1.yaml` dentro de la imagen | `audio-worker` |
| `VERIDICUS_AUDIO_DIR` | Ruta de montaje de `veridicus-audio` | API de `session-api` y `retention-job` |
| `VERIDICUS_AOF_REWRITE_MIN_INTERVAL_SECONDS` | `60` (entero de 10 a 600; fuera de rango impide arrancar) | `audio-worker` |
| `VERIDICUS_SPEECH_TOKEN` | `secretKeyRef` al Secret `veridicus-speech-token` | API de `session-api` y `audio-worker` |
| `VERIDICUS_DB_LOCK_TIMEOUT_MS` | `2000` (de U5); lo usan las transacciones de voz de la API y del trabajador | API y trabajador de `session-api`; no aplica a `audio-worker` (IDS-U9-12) |

### 2.2 Capacidad de Redis con la cota de 1 920 s · nuevo

- Un mensaje de audio ocupa ≤ 8 000 000 caracteres en base64. En uso normal hay ≤ 2 en el *stream*
  (≤ 16 MB); tras `XACK` + `XDEL`, `XLEN` vale 0 (scalability-design §3).
- Aunque `audio-worker` no exista, el recorte por `MINID` impide que un audio siga en memoria más de
  1 920 + 15 s. Peor caso de un analista que graba y envía sin pausa: el corte de 120 s y la subida limitan el
  ritmo a ≈ 66,7 KB/s de base64, y 66,7 KB/s × 1 935 s ≈ 129 MB, del orden de los ≥ 128 MB que deja
  `maxmemory` para los *streams*, junto con los ≈ 81 MB de C2 que calculó U4 (IDS-U9-07).
- Con más analistas a la vez y sin consumidor, `noeviction` rechaza el `XADD`: el turno pasa a `error` con
  `analysis.system` y la consola pide grabar de nuevo; ninguna clave del limitador ni de las colas se expulsa.
  Se acepta como riesgo de la demostración (una persona, IDS-U2-12).
- El AOF crece con cada audio y lo reducen el `AofRewriteRequester` (cola vacía, ≥ 60 s entre peticiones) y
  la reescritura automática de U2; el PVC de 2 GiB es ≥ 2 × el AOF máximo de ≈ 400 MB.

## 3. Modelos fijados (P1 = A, NFR10.10, NFR14.3) · cambia

| Servidor | Formato (IDS-U2-08) | Entrada de `models.lock` | Archivos, cada uno con `sha256` |
|---|---|---|---|
| `model-whisper` | `ctranslate2` | Repositorio ya convertido de `faster-whisper-base`, revisión fijada | `model.bin`, `config.json`, `tokenizer.json`, `vocabulary.txt` |
| `model-tts` | `onnx` | `rhasspy/piper-voices`, ruta `es/es_MX/ald/medium/`, revisión fijada | `es_MX-ald-medium.onnx`, `es_MX-ald-medium.onnx.json`, `MODEL_CARD` |

`verify-model` comprueba **todos** los archivos de la entrada con `sha256sum -c` (cierra R-06). Los
archivos de Systran guardan los pesos en `float16`; la cuantización int8 la hace `faster-whisper` al cargar,
sin archivo aparte. La voz se fija solo tras leer la licencia de su `MODEL_CARD` (tech-stack-decisions §6).

## 3.1 Forma de una entrada de `deploy/models.lock`

```yaml
- name: whisper-base
  server: model-whisper
  format: ctranslate2
  source: https://huggingface.co/Systran/faster-whisper-base
  revision: <commit fijado>
  files:
    - { path: model.bin, sha256: <64 hex> }
    - { path: config.json, sha256: <64 hex> }
    - { path: tokenizer.json, sha256: <64 hex> }
    - { path: vocabulary.txt, sha256: <64 hex> }
```

`scripts/check-models-lock.py` (nivel 0) rechaza un `format` fuera de la lista del servidor; `.pt`, `.pth`,
`.pkl`, `.pickle`, `.ckpt` o `.joblib`; un `.bin` fuera de una entrada `ctranslate2`; una entrada sin revisión
o con un archivo sin `sha256`; una voz sin prefijo `es_`; y cualquier `trust_remote_code`.

## 4. Entrada de la voz sin disco (NFR10.2, NFR10.5) · cambia

| Ruta | `Ingress` | Anotaciones | Por qué |
|---|---|---|---|
| `POST /api/v1/sessions/{id}/voice-turns` | `veridicus-voice` (U2), expresión de U2 §2.4 | `proxy-request-buffering: "off"`, `proxy-buffering: "off"`, `proxy-max-temp-file-size: "0"`, tope 6 065 536 | Con el *buffering* encendido, ingress-nginx guarda en disco todo cuerpo mayor que 16 KiB; apagado, el cuerpo pasa por trozos al lector en memoria de U6. El tope es mayor que `voice_body_max_bytes`, así que el `413` lo da la API con Problem Details |
| `GET /api/v1/conductor-observations/{id}/audio` | `veridicus-web` (U2) | Las mismas tres anotaciones | El WAV (≤ 4 194 304 bytes) no se escribe en un archivo temporal del *ingress*; `Cache-Control: no-store` lo pone la API (NFRD-U9-15) |

La precedencia de rutas con expresiones regulares (R-04) se comprueba en dos niveles: una prueba de nivel 0
sobre el render (`deploy/tests/level0/test_voice_ingress.py`: la ruta de voz existe solo en `veridicus-voice`,
con su tope y las tres anotaciones) y, tras cada despliegue, `scripts/check-ingress-routes.sh` de U2, que U9
amplía con dos casos de solo lectura: un `POST` de 6 100 000 bytes a la ruta de voz recibe `413` del *ingress*
y uno de 3 000 000 bytes a otra ruta de `/api/` recibe `413` del *ingress* de `veridicus-web`.

## 5. Red de U9 (NFR1.1, NFR1.2, NFR10.9) · cambia

| Origen | Destino | Puerto | Regla |
|---|---|---|---|
| `audio-worker` | `veridicus-redis`, `model-whisper`, `model-tts`, CoreDNS | 6379, 8080, 8080, 53 | Salida de `audio-worker` (U2 §2.1) |
| API de `session-api` (`app.kubernetes.io/component: api`) | `audio-worker` | 8080 | Única entrada al puerto de síntesis; el trabajador de `session-api` no la usa (NFRD-U9-16, ya en U2 §3) |
| Prometheus (`monitoring`) | `audio-worker` | 8081 | Solo el puerto de métricas (NFRD-U2-03) |
| `audio-worker` | `model-whisper`, `model-tts` | 8080 | Única entrada de cada servidor de voz; ninguno tiene salida salvo DNS |

Ningún pod de voz tiene `ipBlock`. Controles negativos de Kyverno (nivel 0): `audio-worker` sin la etiqueta
de datos sensibles; salida a `0.0.0.0/0`; `audio-worker` montando `veridicus-audio` (`volume-consumers`);
`model-tts` con `/tmp` en disco (`memory-only-tmp`); `veridicus-speech-token` en un pod distinto de la API y de
`audio-worker` (`secret-consumers`, NFR10.13 de U2); entrada al 8080 de `audio-worker` desde el trabajador de
`session-api`. La verificación manual de salida a internet es la de U2 (SLI de antes de la sustentación).

## 6. Frontera AUTONOMIA-04 por componente · cambia

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera | Disco |
|---|---|---|---|
| Consola (navegador del analista) | Fuera (equipo del analista, mismo origen HTTPS por `port-forward`) | Audio crudo hacia `ingress-nginx`; WAV de la aclaración de vuelta | Ninguno (memoria y `blob:` revocado) |
| `ingress-nginx` | Dentro | Audio y WAV en tránsito | Ninguno con las anotaciones de §4 |
| API de `session-api` | Dentro | Audio en memoria hacia Redis; `{observation_id, tema, template_version}` hacia `audio-worker` | `veridicus-audio` solo si la sesión autoriza conservar el audio (`0600`, cuota, retención de U13) |
| Trabajador de `session-api` | Dentro | Texto transcrito hacia PostgreSQL y C2 | El de PostgreSQL (igual que un turno escrito) |
| `veridicus-redis` | Dentro | Audio en base64 hasta el `XDEL`, o como mucho 1 920 + 15 s | AOF del PVC hasta la siguiente reescritura |
| `audio-worker` | Dentro, sin salida a internet | Audio hacia Whisper; frase compuesta hacia el TTS | Ninguno |
| `model-whisper`, `model-tts` | Dentro, sin salida | Reciben audio o la frase | `/tmp` en memoria |
| `retention-job` (U13) | Dentro | Borra archivos de `veridicus-audio` | El del PVC |
| Prometheus y Grafana (módulo 8) | Dentro | Solo métricas con etiquetas cerradas | El de Prometheus |

Ningún componente de U9 llama fuera del clúster; el anonimizador de U10 no interviene (import-linter sin
`libs.anonymizer` en `audio-worker`, NFR1.4).

## 7. Infraestructura compartida · cambia

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| `veridicus-redis` | U2 | U3, U4, U6, U8, U9, U13 | Prefijos `veridicus:audio*`, `veridicus:transcripts*`, `veridicus:transcribed:*` y `veridicus:voice-cancelled:*`; solo `session-api` y `audio-worker` los tocan; `BGREWRITEAOF` lo pide solo `audio-worker` |
| `model-whisper` | U2 (despliegue) | U9 | Solo `audio-worker` |
| `model-tts` | U2 (despliegue), U9 (imagen) | U9 | Solo `audio-worker` |
| `veridicus-audio` | U2 | U9 (escritura en la API), U13 (borrado en `retention-job`) | Tabla cerrada `volume-consumers.yaml`; `retention-job` con el mismo UID que `session-api` |
| Trabajador de `session-api` | U4 | U9 (ingesta de C5, vencimiento, `XTRIM` y liberación de esperas en el supervisor y el `HoldReleaser`) | Código de U9 por PR en B9; orden de bloqueo sesión → corrida → ronda |
| Proceso API de `session-api` | U3 | U3–U9, U12, U13 | Lector en memoria de U6 con corte; nada pesado en la API |
| `libs/model_gateway` | U11 | U9 (`transcribe`, `synthesize` y su adaptador) | Solo los métodos de voz; `generate` y los tipos compartidos no cambian (D13) |
| Secret `veridicus-speech-token` | U9 (lo crea el humano) | API de `session-api`, `audio-worker` | `secretKeyRef` solo en esos dos pods |
| CPU de la máquina | U2 | Juez, verificador, Whisper, TTS | `limits.cpu` 4 en Whisper y 2 en el TTS |

## 8. Secretos

| Secreto | Origen | Montaje | Rotación |
|---|---|---|---|
| `VERIDICUS_SPEECH_TOKEN` (≥ 32 bytes) | El humano lo genera en su `.env` no versionado; `create-secrets.sh` de U2 escribe el manifiesto fuera del repositorio | `secretKeyRef` en la API de `session-api` y en `audio-worker` | El humano cambia el `.env`, revisa y aplica el manifiesto, y reinicia los dos `Deployment` siguiendo `docs/operacion/instalacion.md` (AUTONOMIA-01) |
| Contraseña de Redis | U2 (`veridicus-redis-auth`) | `audio-worker` por `secretKeyRef` | La de U2 |

## 9. Precisiones y peticiones (IDS-U9-xx) · cambia

La tabla de la revisión 1 se retira entera (IDS-U9-01). No edité ningún artefacto aprobado ni de otra unidad;
las peticiones no se dan por aplicadas y decides en la aprobación si se llevan a su original.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U9-01 | Revisión 1 de esta etapa, §9 (diez precisiones) | Se retira la tabla entera: la lista de formatos ya la adoptó U2 (IDS-U2-08); Whisper con `cpu_threads = 4` y `limits.cpu` 4, Redis con `save ""` y `BGREWRITEAOF` sin renombrar, las URL internas, la red de voz y el `Ingress` sin disco ya están en U2 revisión 2; las banderas y el `ai-eval-gate.yml` de U4 salen (IDS-U9-02, IDS-U9-14); D1 y D3 ya los precisa tech-stack revisión 2 | U2 revisión 2; NFR Design revisión 2 |
| IDS-U9-02 | Revisión 1 de esta etapa, §1 y respuesta P3 = A («voz en las dos máquinas») | Se retiran las dos máquinas, `values-gpu.yaml`, `values-extras.yaml` y las banderas `whisper.enabled`, `tts.enabled` y `audioWorker.enabled`; P3 = A se lee como `voice.enabled: true` por defecto en `values-cpu.yaml` de la única máquina | IDS-U2-01; IDS-U2-02; U2 `cicd-pipeline.md` §7 |
| IDS-U9-03 | Revisión 1 de esta etapa, §2.1 | Se retiran `VERIDICUS_VOICE_MAX_*`, `VERIDICUS_AUDIO_DEADLINE_*`, `VERIDICUS_WHISPER_TIMEOUT_SECONDS`, `VERIDICUS_TTS_TIMEOUT_SECONDS`, `VERIDICUS_SPEECH_TIMEOUT_SECONDS` y `VERIDICUS_AUDIO_RECLAIM_IDLE_SECONDS`: sus valores viven en C25 (§2.1). También salen los nombres `veridicus-whisper`, `veridicus-tts` y `veridicus-audio-worker` | C25; U2 §2.1 |
| IDS-U9-04 | Infrastructure Design de U2 §2.1 (`model-whisper` sin imagen nombrada) y D2 de `tech-stack-decisions.md` | **Petición a U2:** la imagen de `model-whisper` es una imagen propia mínima `services/whisper-server/` (FastAPI + `faster-whisper` fijado, `/v1/audio/transcriptions`, `/health`, sin registro del cuerpo, modo sin conexión), con el mismo patrón que `tts-server` (P2 = A) y su *workflow* `whisper-server.yml` (cicd-pipeline §1); la escribe U9 en B9 y U2 la despliega. Cierra R-01 | R-01 de la revisión 1; D2 |
| IDS-U9-05 | `nfr-design/logical-components.md` §6 (Redis «con el margen del *fork*») y revisión 1 de esta etapa (`limits.memory` 768 MiB) | **No se pide subir el límite de Redis** (se queda en 512 MiB de U2): el `AofRewriteRequester` solo reescribe con la cola de audio vacía. La prueba de nivel 1 de 10 mensajes de 8 MB fuerza un `BGREWRITEAOF` y exige un pico de RSS de Redis ≤ 427 MiB (512 / 1,2); si lo supera, el hallazgo se corrige con un PR a U2 que sube el límite, medido | scalability-design §3; presupuesto de U2 |
| IDS-U9-06 | Revisión 1 de esta etapa, §1.1 (`/tmp` de 64 MiB en el TTS) | El `/tmp` en memoria de `model-tts` es de **16 MiB**: con 64 MiB, 1,2 × (512 + 64) = 691 MiB superaría su límite de 640 MiB. El WAV de respuesta vive en memoria del proceso, no en `/tmp`. **Petición a U2:** `sizeLimit: 16Mi` en `model-tts` | security-design §5 de U2 (el `sizeLimit` cuenta en el límite) |
| IDS-U9-07 | `nfr-design/scalability-design.md` §3 (cota sin consumidor) | Cifra de la cota de 1 920 s en Redis: ≈ 129 MB por analista sin pausa y sin consumidor; con más, `noeviction` rechaza el `XADD` y el turno pasa a `error` con `analysis.system`. Se acepta para una demostración de una persona | §2.2; IDS-U2-12 |
| IDS-U9-08 | Revisión 1 de esta etapa, §1 («almacenamiento: ninguno nuevo») | Sale: el audio conservado vive en `veridicus-audio` (3 GiB, ya adoptado por U2), solo en la API y en `retention-job`; `audio/` lo crea el proceso con `0700` porque Minikube ignora `fsGroup` | NFRD-U2-15; D14 |
| IDS-U9-09 | `nfr-design/logical-components.md` §6 (entrada a los servidores de voz) | La entrada a `model-whisper` y `model-tts` es solo desde `audio-worker`; la entrada al 8080 de `audio-worker` es solo desde la API (ya en U2 §3); se añade el control negativo «el trabajador de `session-api` alcanza el 8080 de `audio-worker`» | NFRD-U9-16 |
| IDS-U9-10 | Revisión 1 de esta etapa, §4 (segunda ruta en `veridicus-voice`) | La ruta del audio de la aclaración pasa a `GET /api/v1/conductor-observations/{id}/audio` y sale por `veridicus-web`, que ya lleva el patrón sin disco de U2; `veridicus-voice` queda con una sola ruta, la expresión de U2 | C1 revisión vigente; U2 §2.4 |
| IDS-U9-11 | Revisión 1 de `monitoring-design.md` (etiquetas `audio_length`, `result` y `reason`) | Las métricas son las de `contracts/metrics/voice.v1.yaml` con `outcome` y `error_code`; sale `veridicus_question_audio_requests_total` y entran `veridicus_clarification_audio_requests_total`, las de espera de corridas y la del audio conservado; las alertas usan esos nombres | NFRD-U9-10; observability-design §2 |
| IDS-U9-12 | Infrastructure Design de U5 (`VERIDICUS_DB_LOCK_TIMEOUT_MS` en la API, el trabajador y los Jobs) | `audio-worker` no abre conexiones a PostgreSQL, así que el ajuste no se le pone; las transacciones de voz de la API y del trabajador sí lo usan con 2000 | IDS-U5-02; NFR Design de U5 |
| IDS-U9-13 | `nfr-design/scalability-design.md` §5 («perfil GPU para la demostración») y NFR2.2 de `tech-stack-decisions.md` («el perfil GPU es opcional») | Sin GPU, las acciones ante la cola o la latencia de transcripción son, por PR y con medición: ajustar `cpu_threads`, subir `limits.cpu` de Whisper si el presupuesto lo deja, o una segunda pareja `audio-worker` + `model-whisper`; nunca bajar la meta | IDS-U2-02 |
| IDS-U9-14 | Revisión 1 de esta etapa (`libs.yml` y `ai-eval-gate.yml` de U4) | Salen: los adaptadores de voz de `libs/model_gateway` los prueba `analyzer.yml` de U11 (su filtro incluye `libs/model_gateway/**`); la corrida de voz la exige `voice-eval-gate.yml` | IDS-U11-08 |
| IDS-U9-15 | Infrastructure Design de U11, `cicd-pipeline.md` §4 (rutas de IA: `libs/model_gateway/**`) | **Petición a U11:** excluir `libs/model_gateway/speech.py` y `libs/model_gateway/adapters/speech_local.py` de las rutas de IA del nivel 2 del analizador; un cambio en ellos exige el reporte de la corrida de voz y no el del analizador | D13; cicd-pipeline §2 |
| IDS-U9-16 | Infrastructure Design de U2 (alcance de `check-no-cluster-apply.sh`) | **Petición a U2:** el alcance suma `evaluation/voice/`, donde viven `generate.py` y el arnés de la corrida de voz, como IDS-U4-07 e IDS-U6-05 | AUTONOMIA-01 |
| IDS-U9-17 | Infrastructure Design de U2 (`check-config-copy.sh`, paneles) | **Petición a U2:** el panel de voz se copia al chart de U2 y `check-config-copy.sh` compara su SHA-256 con `services/audio-worker/observability/grafana-dashboard.json` (control negativo: un byte distinto) | observability-design §4; IDS-U6-07 |
| IDS-U9-18 | `team.md` (comprobaciones obligatorias de `main`) | **Petición al humano:** añadir `audio-worker / gate`, `tts-server / gate`, `whisper-server / gate` (si se adopta IDS-U9-04) y `voice-eval-gate / check` a las comprobaciones obligatorias cuando B9 cree los *workflows* | IDS-U4-12; IDS-U11-09 |
| IDS-U9-19 | `team.md` (nivel 2: «el reporte JSON se adjunta al PR») | Igual que IDS-U11-04, el reporte de la corrida de voz se versiona en `evaluation/reports/voice/` con un YAML de evidencia (commit evaluado y digests de los modelos), y `scripts/check-voice-report.py` lo comprueba | IDS-U11-04 |
| IDS-U9-20 | Revisión 1 de esta etapa, `cicd-pipeline.md` §1 (imagen `tts-server`) | `tts-server` lleva `espeak-ng` (GPL-3.0) por el fonetizador de Piper, y `piper-tts` se fija en una versión MIT (el sucesor `piper1-gpl` es GPL-3.0). La imagen solo se publica en GHCR privado y el código del repositorio no enlaza con ellas; `pip-licenses` en `tts-server.yml` falla ante una licencia fuera de `services/tts-server/licenses-allowed.yaml`. Cierra R-06 (licencias) | tech-stack-decisions §6; R-06 |
| IDS-U9-21 | `nfr-design/scalability-design.md` §4 (corrida mixta con el juez) | La corrida mixta de NFR8.8 y NFR3.15 usa `todo-local` con `models.todoLocalJudge.enabled: true` (por defecto) en la misma máquina, porque es el único juez que comparte CPU con Whisper; con un perfil comercial no hay convivencia que medir | IDS-U2-11 |

## 10. Cierre de los hallazgos de la revisión 1 · nuevo

| Hallazgo de `reviews/review-01.md` | Cómo se cierra |
|---|---|
| R-01 (imagen de Whisper sin nombre ni puertas de CI) | IDS-U9-04 y `whisper-server.yml` en cicd-pipeline §1 |
| R-02 (revisión manual de logs sin comando ni umbral) | `monitoring-design.md` §4: prueba de nivel 1 automatizada con el centinela y, tras la corrida E2E, `scripts/check-voice-logs.sh` con umbral 0 apariciones |
| R-03 (`voice.spec.ts` sin máquina ni umbral) | cicd-pipeline §3: en WSL2 contra `https://veridicus.local:8443`, p95 del turno de voz ≤ 192 s con clips ≤ 30 s y 0 violaciones `serious` o `critical` de axe |
| R-04 (precedencia de rutas con expresiones regulares) | §4: prueba de nivel 0 sobre el render y dos casos más en `check-ingress-routes.sh` |
| R-05 (justificación del presupuesto) | §1.1 y §1.2: cada límite frente a 1,2 × (pico + `/tmp`) y presupuesto sin cambios frente a los 50 GiB |
| R-06 (`verify-model` de todos los archivos; licencias de Piper y espeak-ng) | §3 e IDS-U9-20 |
| R-07 (barras sin escapar en la expresión; sin `promtool test rules`) | `monitoring-design.md` §2: las expresiones viven en un bloque YAML fuera de las tablas y cada regla tiene su caso en `promtool test rules` |
