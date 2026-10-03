# Especificación de infraestructura — U9 voice

**Insumos.** Camino crítico, recepción en *streaming*, plazos y topes de memoria por pod de
`nfr-design/performance-design.md` (performance-design §1–§7); frontera, ciclo de vida del audio,
`AofRewriteRequester`, ruta interna con Bearer y modelos fijados de `nfr-design/security-design.md`
(security-design §1–§9); capacidad, colas y memoria de Redis de `nfr-design/scalability-design.md`
(scalability-design §1–§5); *timeouts*, sondas y recuperación de `nfr-design/reliability-design.md`
(reliability-design); métricas y reglas informativas de `nfr-design/observability-design.md`
(observability-design); inventario, recursos compartidos y entrega a Infrastructure Design de
`nfr-design/logical-components.md` (logical-components §1–§4); flujos F1–F4 y frontera de
`functional-design/functional-spec.md` (functional-spec); procesos SpeechProcessing, InterviewSession
y ModelGateway de `inception/domain-design/components.md` (components); C1, C5, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); D1–D12 y ajustes de
`nfr-requirements/tech-stack-decisions.md`; respuestas **P1 = A** (CTranslate2 y ONNX admitidos como
lista cerrada por servidor), **P2 = A** (imagen propia `services/tts-server/` con `piper-tts` fijado) y
**P3 = A** (voz encendida por defecto en `values-cpu.yaml` y `values-gpu.yaml`, en CPU) de
`infrastructure-design-questions.md`; infraestructura de U2, U3, U4 y U8 (sus
`infrastructure-specification.md`); `## Deployment` de `team.md` y prohibiciones de `project.md`.

U9 añade al clúster un `Deployment` propio (`veridicus-audio-worker`), un servidor de modelo nuevo
(`veridicus-tts`, imagen propia), ajustes al servidor de Whisper de U2, un `Ingress` dedicado a la voz y
ajustes de Redis. Todo se escribe en Code Generation; aquí solo se fija su forma y sus valores.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Modelo de cómputo | Contenedores en el Minikube de U2: `veridicus-audio-worker` (1 réplica, imagen propia en GHCR), `veridicus-tts` (1 réplica, imagen propia `services/tts-server/`) y `veridicus-whisper` de U2 con los ajustes de §2; la API y el trabajador de `session-api` llevan el código de voz en su imagen | D10 (un proceso en `audio-worker`); P2 = A; logical-components §4 |
| Activación (P3 = A) | `whisper.enabled`, `tts.enabled` y `audioWorker.enabled` en `true` en `values-cpu.yaml` y en `values-gpu.yaml`; las tres banderas van juntas: el chart falla al renderizar si difieren (`/readyz` de `audio-worker` depende de Whisper y del TTS) | NFR2.2 (la voz se mide con `values-cpu.yaml`); NFR8.8 (convivencia medida en la máquina de desarrollo) |
| Perfil de cómputo | Whisper y el TTS en **CPU en las dos máquinas**; `values-gpu.yaml` no cambia nada de la voz. Un Whisper en GPU queda solo como mitigación por PR si la corrida de voz no cumple (scalability-design §5) | P3 = A; NFR2.2 |
| Máquinas | Desarrollo: Minikube 20 GiB y 10 CPU, `values-cpu.yaml`. Demostración (32 GB): Minikube 28 GiB, `values-gpu.yaml` + `values-extras.yaml` de U8. Mismos digests y mismos valores de voz en las dos | Decisiones de U2/U4/U8 |
| Red de entrada | El `Ingress` de U2 (`/api/` → `session-api`) más un `Ingress` dedicado `veridicus-voice` para las dos rutas de voz, sin *buffering* a disco (§4) | NFR10.2: ingress-nginx escribe en un archivo temporal todo cuerpo mayor que su búfer |
| Red interna | Negar todo de U2 más las reglas de §5; `audio-worker` lleva la etiqueta de datos sin anonimizar | NFR1.1, NFR10.9; AUTONOMIA-04 |
| Almacenamiento | **Ninguno nuevo.** `audio-worker` sin volúmenes escribibles; `veridicus-whisper` y `veridicus-tts` con el PVC de modelos de solo lectura y `/tmp` en memoria; el único disco que toca el audio es el AOF de `veridicus-redis` (acotado por el `AofRewriteRequester`) | security-design §2; NFR10.2, NFR10.4 |
| Modelos (P1 = A) | Whisper `base` en CTranslate2 y voz Piper `es_MX-ald-medium` en ONNX, fijados en `deploy/models.lock` con un campo `format` y una lista cerrada por servidor (§3) | NFR10.10; precisión a `team.md` en §9 |
| Imágenes | `audio-worker` y `tts-server` sobre `python:3.12-slim` por digest, UID 10001, `readOnlyRootFilesystem`, `capabilities: drop: [ALL]`, `seccompProfile: RuntimeDefault`; publicadas en GHCR por SHA; `ghcr-pull` como en U2 | team.md; Pod Security `restricted` de U2 |
| IaC | Subcharts `audio-worker` y `tts` dentro del chart paraguas `deploy/veridicus` de U2; el humano aplica o Argo CD sincroniza tras la fusión del PR | AUTONOMIA-01 |
| Estrategia | `audio-worker`: `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0` (dos consumidores en el grupo no duplican efectos, scalability-design §2). `veridicus-tts` y `veridicus-whisper`: `Recreate` como todo `model-*` de U2 | NFR8.9; U2 §5 |

### 1.1 Recursos con ≥ 20 % sobre el pico medido (performance-design §7, NFR8.1–NFR8.4)

| Contenedor | Pico de diseño | `requests` CPU / memoria | `limits` CPU / memoria | Margen de memoria |
|---|---|---|---|---|
| `veridicus-whisper` | ≤ 1 GiB con 120 s (NFR8.1) | 1 / 1 GiB | **4** / 1,25 GiB | 25 % |
| `veridicus-audio-worker` | ≤ 256 MiB (NFR8.2) | 0,1 / 256 MiB | 0,5 / 320 MiB | 25 % |
| `veridicus-tts` | ≤ 512 MiB (NFR8.3) | 0,25 / 384 MiB | 2 / 640 MiB | 25 % |
| `session-api` (API) | Base de U3 + ≤ 32 MiB por subida, sin acumulación (NFR8.4) | Sin cambio: 0,5 / 384 MiB | Sin cambio: 2 / 768 MiB | La subida cabe en el margen de U3 (≈ 160 MiB de Argon2id + 32 MiB) |
| `veridicus-redis` | `maxmemory` 384 MB + búferes de cliente (mensajes de 8 MB) + copia en escritura del *fork* de `BGREWRITEAOF` ≈ 600 MiB | 0,1 / 256 MiB | 0,5 / **768 MiB** | 28 % |
| `verify-model` (`initContainer` de `veridicus-tts`) | El de U2 | 0,2 / 64 MiB | 1 / 128 MiB | Valor de U2 |

Los `emptyDir` con `medium: Memory` cuentan dentro del límite del contenedor: los 64 MiB de `/tmp` de
Whisper y del TTS ya están dentro de su margen (el audio de 120 s ocupa 3,84 MB). Whisper sube su
`limits.cpu` de 2 (U2) a 4 por `cpu_threads = 4` (scalability-design §4); la CPU es comprimible y su
`request` sigue en 1.

### 1.2 Presupuesto de las dos máquinas (con la voz encendida, P3 = A)

| Bloque | `requests` memoria | `limits` memoria | `requests` CPU |
|---|---|---|---|
| MUST + sistema (U4) | ≈ 13 GiB | ≈ 17,2 GiB | ≈ 7,3 |
| Monitoreo y Argo CD (módulo 8, U2) | ≈ 1,5 GiB | ≈ 2,3 GiB | ≈ 0,7 |
| Voz (U9): Whisper, `audio-worker`, TTS | ≈ 1,6 GiB | ≈ 2,2 GiB | 1,35 |
| Redis con el nuevo límite (+256 MiB sobre U2) | — | +0,25 GiB | — |
| **Total** | **≈ 16,1 GiB** | **≈ 21,9 GiB** | **≈ 9,35** |

| Máquina | `requests` de memoria | `limits` de memoria | `requests` de CPU |
|---|---|---|---|
| Desarrollo (20 GiB, 10 CPU) | Caben (≈ 3,9 GiB libres) | Superan en ≈ 1,9 GiB: solo el juez se acerca a su pico; en la corrida mixta (NFR8.8) Whisper y el juez pueden coincidir, y sus picos suman ≈ 8 GiB, dentro de lo libre | ≈ 9,35 de 10 |
| Demostración (28 GiB) | Caben | Caben (≈ 6 GiB libres, también con los extras de U8, que no suben picos) | Las CPU de esa máquina |

Si una corrida muestra presión de memoria en desarrollo, el primer recorte sigue siendo el de U2:
apagar el monitoreo durante esa corrida. Nunca se bajan los `limits` de voz por debajo del 20 %.

### 1.3 Sondas (C16, NFR10.17)

| Proceso | `startupProbe` | `livenessProbe` | `readinessProbe` |
|---|---|---|---|
| `veridicus-audio-worker` | `/healthz` cada 5 s, hasta 300 s (calentamiento de Whisper y de la síntesis) | `/healthz` cada 10 s, 3 fallos; el proceso además termina solo si el latido del bucle pasa de 30 s | `/readyz` cada 10 s: configuración, Redis, `veridicus-whisper`, `veridicus-tts` y los dos calentamientos |
| `veridicus-tts` | `/healthz` cada 5 s, hasta 120 s | `/healthz` cada 10 s, 3 fallos | `/readyz` cada 10 s: voz cargada y síntesis de calentamiento hecha |
| `veridicus-whisper` | La de U2 (`/health` cada 5 s, hasta 120 s) | La de U2 | La de U2 |

## 2. Servicios de infraestructura

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-audio-worker` | other (trabajador + ruta interna) | Puerto `http` 8080 (`/healthz`, `/readyz`, `POST /internal/v1/speech`), puerto `metrics` 8081; consumidor del grupo `audio-worker` en `veridicus:audio`, `XREADGROUP BLOCK 5000 COUNT 1`, `socket_timeout` 6 s; síntesis con concurrencia 1; `PYTHONDONTWRITEBYTECODE=1`; **sin volúmenes** | D10; security-design §2 y §4 |
| `veridicus-tts` (P2 = A) | other (modelo) | Imagen `services/tts-server/` (FastAPI + Uvicorn `--no-access-log`, `piper-tts` fijado en su lockfile); `POST /v1/audio/speech` con `{model, input, voice, response_format: "wav"}`, `input` de 1 a 300 caracteres (si no, `422`), concurrencia 1, 2 hilos de ONNX Runtime; carga `/models/piper/<revisión>/es_MX-ald-medium.onnx` del PVC de solo lectura; nunca registra el cuerpo; puerto 8080 | El adaptador `synthesize` de ModelGateway (C13) habla esta forma; C14 deja el TTS fuera del estándar |
| `veridicus-whisper` (U2) | other (modelo) | La imagen sigue siendo la que fije U2 (su hallazgo R-06); U9 exige: API `/v1/audio/transcriptions` de C14, modelo local `/models/whisper/<revisión>/` con `compute_type=int8`, `cpu_threads = 4`, una transcripción a la vez, sin descarga en ejecución (modo sin conexión), sin registro del cuerpo, `/tmp` `emptyDir` `medium: Memory` `sizeLimit: 64Mi`, entrada solo desde `audio-worker` | D1, D2; precisión en §9 |
| `veridicus-redis` (U2) | queue | *Streams* `veridicus:audio` (grupo `audio-worker`), `veridicus:transcripts` (grupo `session-api-transcripts`) y sus `:failed` con `MAXLEN ~ 1000`; `save ""`, `appendonly yes`, `appendfsync everysec`, `auto-aof-rewrite-percentage 100`, `auto-aof-rewrite-min-size 16mb`; `BGREWRITEAOF` **sin renombrar**; `maxmemory 384mb` `noeviction` (≥ 128 MB libres para los *streams*); PVC de 2 GiB (≥ 2 × el AOF máximo de ≈ 400 MB) | scalability-design §3; security-design §2; precisión en §9 |
| `veridicus-pg` (U2) | database | Sin roles nuevos: la ingesta usa `veridicus_app` del pool del trabajador de U4; índice parcial sobre `processing_stage = 'transcribing'` por migración de U9 | performance-design §3 (NFR3.5) |
| `ingress-nginx` (U2) | load-balancer | `Ingress` `veridicus-voice` con dos rutas por expresión regular y anotaciones propias (§4) | NFR10.2, NFR10.5 |
| Volumen de modelos (U2) | object-store | Carpetas por revisión `/srv/veridicus/models/<nombre>/<revisión>/`; `verify-model` en `veridicus-tts` y `veridicus-whisper` | Permite revertir un modelo sin volver a descargarlo |
| `cdn`, `search`, `dns` propio | — | No aplica | CoreDNS de U2 |

### 2.1 Configuración de voz en los *values* (prefijo `VERIDICUS_`)

| Ajuste | Valor en `values-cpu.yaml` y `values-gpu.yaml` | Pods |
|---|---|---|
| `VERIDICUS_WHISPER_URL` | `http://veridicus-whisper.veridicus.svc.cluster.local:8080` (de U2) | `audio-worker` |
| `VERIDICUS_TTS_URL` | `http://veridicus-tts.veridicus.svc.cluster.local:8080` | `audio-worker` |
| `VERIDICUS_SPEECH_URL` | `http://veridicus-audio-worker.veridicus.svc.cluster.local:8080` | API de `session-api` |
| `VERIDICUS_WHISPER_MODEL`, `VERIDICUS_WHISPER_MODEL_SHA256` | `base` y el `sha256` de `model.bin` copiado de `models.lock` (una prueba de nivel 0 exige que coincidan) | `audio-worker` |
| `VERIDICUS_VOICE_MAX_BYTES`, `VERIDICUS_VOICE_MAX_SECONDS` | `6000000`, `120` | API de `session-api` |
| `VERIDICUS_AUDIO_DEADLINE_BASE_SECONDS`, `_MAX_SECONDS` | `300`, `1800` | API y trabajador de `session-api` |
| `VERIDICUS_WHISPER_TIMEOUT_SECONDS`, `VERIDICUS_AUDIO_RECLAIM_IDLE_SECONDS` | `90`, `120` | `audio-worker` |
| `VERIDICUS_TTS_TIMEOUT_SECONDS`, `VERIDICUS_SPEECH_TIMEOUT_SECONDS` | `10`, `12` | `audio-worker`, API |
| `VERIDICUS_AOF_REWRITE_MIN_INTERVAL_SECONDS` | `60` | `audio-worker` |
| `VERIDICUS_SPEECH_TOKEN` | `secretKeyRef` al Secret `veridicus-speech-token` (nunca en los *values*) | API de `session-api`, `audio-worker` |

## 3. Modelos fijados (P1 = A, NFR10.10, NFR14.3)

| Servidor | Formatos admitidos | Entrada de `models.lock` | Archivos |
|---|---|---|---|
| `veridicus-judge`, `veridicus-embeddings` (U2) | `gguf` | Las de U2 y U4 | `.gguf` |
| `veridicus-whisper` | `ctranslate2` | Repositorio ya convertido de `faster-whisper-base`, revisión fijada | `model.bin`, `config.json`, `tokenizer.json`, `vocabulary.txt`, cada uno con `sha256` |
| `veridicus-tts` | `onnx` | `rhasspy/piper-voices`, ruta `es/es_MX/ald/medium/`, revisión fijada | `es_MX-ald-medium.onnx`, `.onnx.json` y `MODEL_CARD` (licencia revisada antes de fijarla) |

`scripts/check-models-lock.py` (nivel 0, §cicd-pipeline) rechaza: un `format` fuera de la lista del
servidor; `.pt`, `.pth`, `.pkl`, `.pickle`, `.ckpt` o `.joblib`; un `.bin` fuera de una entrada
`ctranslate2`; una entrada sin revisión o sin `sha256`; una voz sin prefijo `es_`; cualquier opción
`trust_remote_code`. Los archivos de Systran guardan los pesos en `float16`; la cuantización int8 la hace
`faster-whisper` al cargar (`compute_type=int8`), sin otro archivo.

```yaml
# deploy/models.lock (forma ilustrativa de una entrada)
- name: whisper-base
  server: veridicus-whisper
  format: ctranslate2
  source: https://huggingface.co/Systran/faster-whisper-base
  revision: <commit fijado>
  files:
    - { path: model.bin, sha256: <64 hex> }
    - { path: config.json, sha256: <64 hex> }
```

## 4. Entrada de la voz sin disco (NFR10.2, NFR10.5)

| Ruta | Anotaciones del `Ingress` `veridicus-voice` | Por qué |
|---|---|---|
| `POST /api/sessions/[^/]+/voice-turns$` | `use-regex: "true"`, `proxy-request-buffering: "off"`, `proxy-body-size: "7m"` (6 000 000 bytes + margen del *multipart*), `proxy-read-timeout: "30"` | Con el *buffering* encendido, ingress-nginx guarda en `/tmp/nginx/client-body` todo cuerpo mayor que su búfer (16 KiB): el audio crudo tocaría el disco del pod del *ingress*. Apagado, el cuerpo pasa por trozos a la lectura en *streaming* de `session-api` |
| `GET /api/questions/[^/]+/audio$` | `use-regex: "true"`, `proxy-buffering: "off"`, `proxy-max-temp-file-size: "0"` | La respuesta WAV (≤ 2 MB) no se escribe en un archivo temporal del *ingress*; `Cache-Control: no-store` lo pone `session-api` |

El resto de `/api/` sigue en el `Ingress` de U2. Verificación: política de nivel 0 sobre el render (las
dos rutas existen con esas anotaciones) y, manual y de solo lectura tras la corrida de voz,
`kubectl -n ingress-nginx exec deploy/ingress-nginx-controller -- find /tmp/nginx -type f` devuelve 0
archivos.

## 5. Red de U9 (NFR1.1, NFR1.2, NFR10.9)

| Origen | Destino | Puerto | Política |
|---|---|---|---|
| `veridicus-audio-worker` | `veridicus-redis`, `veridicus-whisper`, `veridicus-tts`, CoreDNS | 6379, 8080, 8080, 53 | `audio-worker-egress` (sustituye la regla de U2, que no tenía el TTS) |
| API de `session-api` | `veridicus-audio-worker` | 8080 | Se añade a la salida de `session-api` |
| API de `session-api` | — | — | Entrada a `audio-worker` 8080 **solo** desde pods `app.kubernetes.io/name: session-api, component: api` (`audio-worker-ingress`) |
| Namespace `monitoring` | `veridicus-audio-worker` | 8081 | `allow-prometheus` de U2 |
| `veridicus-audio-worker` | `veridicus-tts` | 8080 | Única entrada de `veridicus-tts` (`tts-ingress`); sin salida salvo DNS |
| `veridicus-audio-worker` | `veridicus-whisper` | 8080 | Única entrada de `veridicus-whisper` |

Ningún pod de voz tiene `ipBlock`. Kyverno CLI (nivel 0) prueba con controles negativos: pod de
`audio-worker` sin la etiqueta de datos sensibles, salida a `0.0.0.0/0`, un `emptyDir` sin
`medium: Memory` en Whisper o TTS, un volumen escribible en `audio-worker` y una referencia a
`veridicus-speech-token` desde un pod que no es la API ni `audio-worker`. Verificación manual (solo
lectura): `kubectl -n veridicus exec deploy/veridicus-audio-worker -- python -c "import socket;
socket.create_connection(('example.org', 443), 5)"` termina con código ≠ 0.

## 6. Frontera AUTONOMIA-04 por componente

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera | Disco |
|---|---|---|---|
| Consola (navegador del analista) | Fuera (equipo del analista, mismo origen HTTPS) | Audio crudo hacia `ingress-nginx`; WAV de la pregunta de vuelta | Ninguno (memoria y `blob:` revocado, NFR10.5) |
| `ingress-nginx` | Dentro | Audio y WAV de la pregunta en tránsito, cifrados hasta el *ingress* | Ninguno con las anotaciones de §4 |
| API de `session-api` | Dentro | Audio en memoria hacia Redis; texto de la pregunta hacia `audio-worker` | Ninguno (raíz de solo lectura, `/tmp` en memoria) |
| Trabajador de `session-api` | Dentro | Texto transcrito hacia PostgreSQL y C2 | El de PostgreSQL (texto del turno, igual que un turno escrito) |
| `veridicus-redis` | Dentro | Audio en base64 hasta el `XDEL` | AOF del PVC hasta la siguiente reescritura (≈ 2 min tras cola vacía) |
| `veridicus-audio-worker` | Dentro, sin salida a internet | Audio hacia Whisper; texto hacia el TTS | Ninguno |
| `veridicus-whisper`, `veridicus-tts` | Dentro, sin salida | Reciben audio o texto | `/tmp` en memoria |
| Prometheus, Grafana (módulo 8) | Dentro | Solo métricas con etiquetas cerradas | El de Prometheus (sin datos sensibles) |

Ningún componente de U9 llama fuera del clúster; el anonimizador de U10 no interviene.

## 7. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `veridicus-redis` | U2 | U3 (limitador), U4, U8, U9 | Prefijos `veridicus:audio*` y `veridicus:transcripts*`; solo `session-api` y `audio-worker` los tocan; `noeviction`; `BGREWRITEAOF` lo pide solo `audio-worker` |
| `veridicus-whisper` | U2 (despliegue), U9 (ajustes) | U9 | Solo `audio-worker` por `NetworkPolicy` |
| `veridicus-tts` | U9 | U9 | Solo `audio-worker` |
| Volumen de modelos | U2 | `model-*` | Solo lectura; `verify-model` en cada servidor |
| Proceso API de `session-api` | U3 | U3–U9 | Lectura de la subida en *streaming* con corte; ninguna tarea pesada en la API |
| Secret `veridicus-speech-token` | U9 | API de `session-api`, `audio-worker` | `secretKeyRef` solo en esos dos pods (política de nivel 0) |
| CPU de la máquina de desarrollo | U2 | Juez, *embeddings*, Whisper, TTS | `limits.cpu` de Whisper 4 y del TTS 2 |
| `Ingress` y certificado `veridicus-ingress-tls` | U2 | U9 (`veridicus-voice`) | Mismo host `veridicus.local` y mismo Secret TLS |

## 8. Secretos

| Secreto | Origen | Montaje | Rotación |
|---|---|---|---|
| `VERIDICUS_SPEECH_TOKEN` (≥ 32 bytes) | El humano lo genera (`openssl rand -hex 32`) en su `.env` no versionado; `create-secrets.sh` de U2 crea `veridicus-speech-token` | `secretKeyRef` en la API de `session-api` y en `audio-worker` | El humano cambia el `.env`, recrea el Secret con el *script* y reinicia los dos `Deployment` siguiendo `docs/operacion/instalacion.md` (paso manual, AUTONOMIA-01) |
| Contraseña de Redis | U2 | `audio-worker` la usa por `secretKeyRef` | La de U2 |

## 9. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado ni de otra unidad; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `aidlc/spaces/default/memory/team.md` `## Deployment` (artefactos de modelo) | «Formatos sin código ejecutable» se lee como lista cerrada por servidor: GGUF y `safetensors`, más CTranslate2 (solo Whisper) y ONNX (solo la voz Piper); `models.lock` lleva `format` y la prueba de nivel 0 rechaza los formatos con `pickle`. Si lo apruebas, entra a `team.md` por el ritual de aprendizajes, no editándolo a mano | P1 = A |
| `platform/infrastructure-design/infrastructure-specification.md` §2.1 (`veridicus-whisper`) | Modelo local en CTranslate2 desde `models.lock`, `compute_type=int8`, `cpu_threads = 4`, sin conexión y sin registro del cuerpo; `limits` 4 CPU / 1,25 GiB (antes 2 / 1,5 GiB); la imagen sigue pendiente del hallazgo R-06 de U2 | D1, scalability-design §4; §1.1 |
| `platform/infrastructure-design/infrastructure-specification.md` §2.1 (`ingress-nginx`) | `proxy-body-size` global ya no tiene que igualar el audio: la ruta de voz tiene su `Ingress` `veridicus-voice` con 7m y sin *buffering*; el resto de `/api/` puede quedarse en el mayor tamaño que no sea audio (≥ 1 MiB de U4) | §4; NFR10.2 |
| `platform/infrastructure-design/infrastructure-specification.md` §2.1 (`veridicus-redis`) y `platform/nfr-design/security-design.md` §7 | `save ""`, `auto-aof-rewrite-min-size 16mb`, `BGREWRITEAOF` fuera de la lista de comandos renombrados (siguen `FLUSHALL`, `FLUSHDB`, `CONFIG`, `DEBUG`) y `limits.memory` 768 MiB (antes 512 MiB) por el *fork* de la reescritura | security-design §9; scalability-design §3 |
| `platform/infrastructure-design/infrastructure-specification.md` §2.2 y política `internal-model-urls` | Se añaden `VERIDICUS_TTS_URL` y `VERIDICUS_SPEECH_URL`; la política las valida igual (`.svc.cluster.local`) | NFR1.2 |
| `platform/infrastructure-design/infrastructure-specification.md` §3 | La regla de `audio-worker` suma `veridicus-tts` 8080; `session-api` suma salida a `audio-worker` 8080; nuevas `audio-worker-ingress` y `tts-ingress` | §5 |
| `platform/infrastructure-design/infrastructure-specification.md` §2.3 y `scripts/fetch-models.sh` | Carpetas por revisión y campo `format` en `models.lock`; `verify-model` también en `veridicus-tts` | P1 = A; reversión sin nueva descarga |
| `platform/infrastructure-design/cicd-pipeline.md` §7 (banderas) | Nueva bandera `tts.enabled`; las tres banderas de voz en `true` en `values-cpu.yaml` y `values-gpu.yaml` y obligadas a coincidir | P3 = A |
| `text-flow/infrastructure-design/cicd-pipeline.md` §1 (`ai-eval-gate.yml`) | Un cambio en `deploy/models.lock` que solo toca entradas de voz exige el reporte de la corrida de voz y no el del Golden Dataset; el *script* decide por las entradas cambiadas | cicd-pipeline.md §2 de esta carpeta |
| `voice/nfr-requirements/tech-stack-decisions.md` D3 | El servidor del TTS es la imagen propia `services/tts-server/` con la API estilo OpenAI `POST /v1/audio/speech`; el adaptador `synthesize` de C13 habla esa forma | P2 = A |
| `voice/nfr-requirements/tech-stack-decisions.md` D1 | El repositorio de Systran trae los pesos en `float16`; la cuantización int8 se hace al cargar, sin archivo aparte | §3 |
