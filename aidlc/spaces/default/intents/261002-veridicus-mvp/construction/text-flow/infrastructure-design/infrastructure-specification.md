# Especificación de infraestructura — U4 text-flow

**Insumos.** Camino crítico, pools, indexación, separación de procesos y topes de memoria de
`nfr-design/performance-design.md` (performance-design); frontera, *prompt* inmutable, mínimo
privilegio y cargas de `nfr-design/security-design.md` (security-design); réplicas, colas y señales de
`nfr-design/scalability-design.md` (scalability-design); *timeouts*, fallos del juez, plazos y salud de
`nfr-design/reliability-design.md` (reliability-design); métricas y logs de
`nfr-design/observability-design.md` (observability-design); inventario, radio de impacto y entrega a
Infrastructure Design de `nfr-design/logical-components.md` (logical-components); flujos de
`functional-design/functional-spec.md` (functional-spec); procesos y dependencias externas de
`inception/domain-design/components.md` (components); C2–C4, C6–C9, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); ajustes y D1–D16 de
`nfr-requirements/tech-stack-decisions.md`; respuestas P1–P2 de `infrastructure-design-questions.md`;
infraestructura común de U2 y despliegue de `session-api` de U3 (sus `infrastructure-specification.md`).

U4 es la primera unidad que pone en el clúster el flujo de texto completo: el trabajador de
`session-api`, `semantic-agent`, la consola y el uso real del juez y de los *embeddings*.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Procesos | Tres `Deployment` en `veridicus`: `session-api` (API, de U3), `session-api-worker` (misma imagen, orden `python -m session_api.worker`) y `semantic-agent`; más `frontend` para la consola | performance-design §5 y logical-components §4: nada pesado en la API |
| Réplicas | 1 de cada uno en el MVP; cambiar es un PR. Sin KEDA en el MVP (COULD de U2) | scalability-design §1: el cuello de botella es la única ranura del juez |
| Imágenes | `session-api` (U3) y `semantic-agent` (nueva) sobre `python:3.12-slim` por digest, sin root (UID 10001); `frontend` sobre `nginx-unprivileged` por digest con los archivos compilados; todas en GHCR por SHA | team.md; NFR10.12 |
| Puertos | `http` 8080 (`/healthz`, `/readyz` y, en API y consola, el tráfico) y `metrics` 8081 en API, trabajador y `semantic-agent`; `frontend` solo 8080 | observability-design §2 |
| Entrada | `/api/` → `session-api`; `/` → `frontend`, en el `Ingress` de U2; `proxy-body-size` ≥ 1 MiB por la carga de escenarios | security-design §7 (1 048 576 bytes) |
| *Prompt* del juez | Archivo único `deploy/veridicus/charts/semantic-agent/files/judge-prompt.md`, publicado como `ConfigMap` `semantic-agent-prompt` y montado `readOnly` en `/etc/veridicus/prompt/`; su SHA-256 en `VERIDICUS_JUDGE_PROMPT_SHA256` de los *values* | security-design §3 (NFR10.3); Helm solo lee archivos dentro del chart, así que el archivo vive ahí y las pruebas de `semantic-agent` lo leen desde esa ruta |
| Umbral | `VERIDICUS_SIMILARITY_THRESHOLD: "0.80"` solo en los *values* (`ConfigMap` de API y `semantic-agent`); cambia únicamente por PR con el reporte del barrido | NFR4.1, NFR11.3 |
| Sistema de archivos | `readOnlyRootFilesystem: true` y `emptyDir` en memoria para `/tmp` (y `/var/cache/nginx` en `frontend`) | Pod Security `restricted` de U2 |
| Estrategia | `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0` en los tres; los consumidores comparten grupo, así que un segundo pod transitorio no duplica efectos | reliability-design §3 (idempotencia por `turn_id`, `attempt`) |
| Máquinas | Desarrollo: Minikube con **20 GiB** y 10 CPU (4 GB al sistema). Demostración, la de 32 GB: Minikube con **28 GiB** (4 GB al sistema), `values-gpu.yaml` con el juez en GPU | P1 y P2 |

### 1.1 Recursos con ≥ 20 % sobre el pico medido (P1, NFR8.1–NFR8.4)

| Contenedor | Pico medido (performance-design §7) | `requests` CPU / memoria | `limits` CPU / memoria | Margen de memoria |
|---|---|---|---|---|
| `veridicus-judge` | ≤ 7 GiB | 3 / 7 GiB | 6 / 8,5 GiB | 21 % |
| `veridicus-embeddings` | ≤ 1,5 GiB | 1 / 1,5 GiB | 2 / 1,8 GiB | 20 % |
| `semantic-agent` | ≤ 512 MiB | 0,25 / 384 MiB | 1 / 640 MiB | 25 % |
| `session-api-worker` | ≤ 768 MiB | 0,5 / 512 MiB | 1,5 / 960 MiB | 25 % |
| `session-api` (API) | — (U3: base + Argon2id) | 0,5 / 384 MiB | 2 / 768 MiB | Valor de U3 |
| `frontend` | — | 0,05 / 32 MiB | 0,2 / 64 MiB | Valor de U2 |

El juez pide 3 CPU (la CPU es comprimible) y puede usar hasta 6 con sus 6 hilos; así la suma de
`requests` de CPU cabe en 10.

| Presupuesto | Máquina de desarrollo (20 GiB, 10 CPU) | Máquina de demostración (28 GiB) |
|---|---|---|
| `requests` de memoria, MUST + sistema | ≈ 13 GiB | ≈ 13 GiB |
| `requests` de memoria con todo lo SHOULD | ≈ 15,8 GiB | ≈ 15,8 GiB |
| `limits` de memoria, MUST + sistema | ≈ 17,2 GiB (cabe) | Cabe |
| `limits` de memoria con todo lo SHOULD | ≈ 21,5 GiB: supera en ≈ 1,5 GiB; solo el juez se acerca a su pico | ≈ 21,5 GiB (cabe) |
| `requests` de CPU con todo lo SHOULD | ≈ 9,3 de 10 | Las CPU de esa máquina |

### 1.2 Sondas (C16, NFR10.19)

| Proceso | `startupProbe` | `livenessProbe` | `readinessProbe` (`/readyz`) |
|---|---|---|---|
| `session-api` (API) | La de U3 | La de U3 | `/readyz?probe=kubernetes` de U3 (base y configuración de U3 y U4, incluido el umbral); sin Redis, el envío de turnos responde `503` |
| `session-api-worker` | `/healthz` cada 2 s, hasta 60 s | `/healthz` cada 10 s, 3 fallos | `/readyz` cada 10 s: configuración, base, Redis, `veridicus-embeddings` y latido de sus tres hilos |
| `semantic-agent` | `/healthz` cada 5 s, hasta 600 s (el juez puede tardar en cargar) | `/healthz` cada 10 s, 3 fallos | `/readyz` cada 10 s: umbral, SHA-256 del *prompt*, base de solo lectura, Redis, juez, *embeddings* y calentamiento terminado |
| `frontend` | — | `/healthz` (archivo estático) cada 10 s | Ídem |

`semantic-agent` empieza a consumir C2 solo después del calentamiento del juez (performance-design §1).
Un hilo muerto del trabajador termina el proceso y Kubernetes lo reinicia (reliability-design §6).

## 2. Servicios de infraestructura que usa U4

| Servicio | Rol | Configuración para U4 | Notas |
|---|---|---|---|
| `veridicus-pg` | database | API: `veridicus_app`, pool 5 + 5. Trabajador: `veridicus_app` (ingesta, plazos) pool 3 y `veridicus_indexer` (indexador) pool 2. `semantic-agent`: `veridicus_judge_ro`, pool 2, solo `SELECT` de `truthframe.passage_search`. `statement_timeout` 2 s (5 s en la transacción de indexación) | 22 de las 50 conexiones con las tres réplicas; índice B-tree por `version_id`, sin índice aproximado (D5) |
| Roles nuevos | database | `veridicus_indexer` (insertar pasajes y actualizar las columnas de estado de `ScenarioVersion`) en `managed.roles` del `Cluster` de U2, con su Secret | security-design §5 |
| `veridicus-redis` | queue | *Streams* `veridicus:turns` (grupo `semantic-agent`), `veridicus:results` (grupo `session-api-ingest`), `veridicus:indexing` (grupo `session-api-indexer`), y sus `<cola>:failed` con `MAXLEN ~ 1000`; `XACK` + `XDEL` tras el efecto; `XREADGROUP BLOCK 5000` con `socket_timeout` 6 s | Las colas quedan vacías tras procesar: no presionan los 384 MB de `noeviction` |
| `veridicus-judge` | other | `VERIDICUS_JUDGE_URL` interna, `cache_prompt: true`, temperatura 0, `seed` 20261002, *timeout* 180 s, `--api-key` | Una ranura (NFR8.7) |
| `veridicus-embeddings` | other | `VERIDICUS_EMBEDDINGS_URL` interna; lotes de 32; *timeout* 30 s | Lo usan el trabajador (indexación) y `semantic-agent` |
| `cdn`, `search` | — | No aplica | La búsqueda vectorial es la consulta de C9 en PostgreSQL |

### 2.1 Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor en los *values* | Procesos |
|---|---|---|
| `SIMILARITY_THRESHOLD` | 0.80 | API, `semantic-agent` |
| `TOP_K` | 3 | API |
| `TURN_DEADLINE_BASE_SECONDS`, `_MAX_SECONDS` | 300, 3600 | API, trabajador |
| `DEADLINE_SWEEP_SECONDS` | 15 | Trabajador |
| `QUEUE_RECLAIM_IDLE_SECONDS`, `QUEUE_MAX_DELIVERIES` | 240, 3 | Trabajador, `semantic-agent` |
| `JUDGE_URL`, `EMBEDDINGS_URL` | URL internas de U2 | `semantic-agent`; `EMBEDDINGS_URL` también en el trabajador |
| `JUDGE_PROMPT_SHA256` | SHA-256 del archivo del *prompt* | `semantic-agent` |
| `JUDGE_SEED`, `JUDGE_TIMEOUT_SECONDS`, `EMBEDDINGS_TIMEOUT_SECONDS` | 20261002, 180, 30 | `semantic-agent`, trabajador |
| `JUDGE_TRANSIENT_RETRIES`, `JUDGE_RETRY_WAITS_SECONDS` | 2, `2,6` | `semantic-agent` |
| `JUDGE_MAX_DATA_TOKENS` | 6000 | `semantic-agent` |
| `PASSAGE_MAX_CHARS`, `EMBEDDINGS_BATCH` | 1000, 32 | Trabajador |
| Contraseñas de `veridicus_app`, `veridicus_indexer`, `veridicus_judge_ro`, Redis y `--api-key` del juez | Secrets de U2 (`create-secrets.sh`) | Según el proceso |

## 3. Red de U4 (NFR1.1, NFR1.2)

| Proceso | Entrada | Salida |
|---|---|---|
| `session-api` (API) | `ingress-nginx` → 8080; `monitoring` → 8081 | `veridicus-pg`, `veridicus-redis`, CoreDNS (la API no llama a modelos) |
| `session-api-worker` | `monitoring` → 8081 | `veridicus-pg`, `veridicus-redis`, `veridicus-embeddings`, CoreDNS |
| `semantic-agent` | `monitoring` → 8081 | `veridicus-pg`, `veridicus-redis`, `veridicus-judge`, `veridicus-embeddings`, CoreDNS |
| `frontend` | `ingress-nginx` → 8080 | CoreDNS (sirve archivos estáticos) |

Ningún proceso sale del namespace. La entrada a `veridicus-judge` solo admite `semantic-agent`; la de
`veridicus-embeddings`, al trabajador y a `semantic-agent`.

## 4. Consola (`frontend`)

| Aspecto | Diseño |
|---|---|
| Contenido | Archivos compilados de React + TypeScript (M0–M6); la misma imagen la amplían U3 y U5–U9 |
| Cabeceras | `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; object-src 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, en la configuración de nginx de la imagen |
| Caché | `index.html` con `Cache-Control: no-store`; archivos con *hash* en el nombre, `max-age` de un año |
| Sondeo | 2 s con turnos en curso y 15 s sin ellos (performance-design §6) contra `/api/`; sin WebSockets |

## 5. Evaluación de nivel 2 (Golden Dataset)

La evaluación usa el juez y los *embeddings* reales, así que corre en el clúster de la máquina que toque
(desarrollo en CPU, o la de demostración con `values-gpu.yaml` para el perfil GPU), nunca en la CI:

| Paso | Diseño |
|---|---|
| Acceso a los modelos | `scripts/eval-level2.sh` abre `kubectl port-forward` a `veridicus-judge` y `veridicus-embeddings` y ejecuta `uv run --directory evaluation python -m golden.run`; no cambia nada del clúster |
| Datos | Solo el Golden Dataset sintético de `evaluation/` (NFR12) |
| Reporte | JSON con versión del dataset, `prompt_sha256`, umbral, digest del modelo (de `deploy/models.lock`), perfil CPU o GPU y métricas; se adjunta al PR (team.md) |
| Paridad de *embeddings* | El mismo *script* corre la comprobación de 20 frases de D16 (coseno ≥ 0,99) antes del barrido |

## 6. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `session-api-worker` | U4 | U6 (latido y reanudación), U7, U8 | Hilos propios por cola; cada unidad añade su configuración por PR |
| `semantic-agent` | U4 | U8 (permutación, pregunta) | Un turno a la vez; U8 no cambia la ranura del juez |
| `frontend` | U4 (base de la consola y su accesibilidad) | U3 (M0, M6) y U5–U9 | Una sola imagen; cada unidad añade pantallas por PR |
| `ConfigMap` del *prompt* | U4 | U8 | Solo cambia por PR con reporte de nivel 2 |
| `veridicus-judge`, `veridicus-embeddings`, `veridicus-pg`, `veridicus-redis` | U2 | U4 entre otras | Ver la tabla de infraestructura compartida de U2 |

## 7. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `platform/infrastructure-design/infrastructure-specification.md` §1 y §4 | Minikube con 20 GiB en la máquina de desarrollo y 28 GiB en la de demostración (antes 18 y 26); límites del juez (8,5 GiB), *embeddings* (1,8 GiB), `semantic-agent` (640 MiB) y trabajador (960 MiB) con ≥ 20 %; el juez pide 3 CPU en vez de 4 | P1, P2; performance-design §7; hallazgos R-01 y R-05 de la revisión de U2 |
| `platform/infrastructure-design/infrastructure-specification.md` §2.1 y §3 | Rol `veridicus_indexer`; la salida a `veridicus-embeddings` es del trabajador, no de la API | security-design §5 |
| `identity-access/infrastructure-design/infrastructure-specification.md` | La consola (`frontend`) que entrega U3 en B2 usa el despliegue de §4 | Primera unidad con pantallas en el clúster |
