# Especificación de infraestructura — U4 text-flow

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** La revisión 1 ponía en el clúster el evaluador propio de U4: juez, *embeddings*, umbral,
  indexación de escenarios y *prompt* en un `ConfigMap`. Ahora U4 orquesta las corridas de la biblioteca de
  U11 (C17) dentro de `semantic-agent`, con la cola C2/C3 en Redis, la ingesta y el supervisor en el
  trabajador de `session-api`, y la consola M3–M4. Los servidores de modelos, la red, los Secrets y los
  `requests`/`limits` son de U2; este documento fija lo que U4 necesita de cada pod y lo que pide a U2.
- **Numeración.** §1–§4 y §6 conservan su tema. §5 (evaluación de nivel 2 por `port-forward`) queda
  «Retirado». La tabla de precisiones de la revisión 1 (§7) se retira entera (IDS-U4-11) y la sustituye la
  tabla IDS-U4-01 a IDS-U4-15. §8 cierra los hallazgos de `reviews/review-01.md`.
- **Supuesto de máquina.** Una sola máquina de 64 GB, solo CPU y sin máquina GPU; Minikube con 50 GiB y
  16 CPU, decidido por U2 (IDS-U2-01). Hoy el trabajo corre en un contenedor sobre WSL2.
- **Preguntas.** Ninguna en esta pasada (`infrastructure-design-questions.md`, sección del 2026-11-23).

**Insumos.**
- De `nfr-design/` de esta unidad (revisión 2): performance-design §1, §3, §5, §7–§9;
  security-design §1, §5, §6, §7, §8, §10–§12 y la tabla NFRD-U4-01 a NFRD-U4-17; scalability-design
  §1–§4; reliability-design §1, §3, §4, §6, §10–§14; observability-design §1–§4; logical-components §1–§5.
- `functional-design/functional-spec.md` (functional-spec: F3–F8, F10–F15 y la frontera AUTONOMIA-04 de §1).
- InterviewSession, AnalysisWorker, ConsoleApi y la tabla de fronteras de
  `inception/domain-design/components.md` (components).
- C1–C3, C10, C11, C15–C17, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements/tech-stack-decisions.md` (D9, D11–D13, D17–D20, §2 y §5).
- Peticiones de NFR Design a U4: NFRD-U5-07, NFRD-U6-05/06/07/15, NFRD-U8-02/08/11/12, NFRD-U9-01/05/08 y
  NFRD-U13-05/06.
- Infrastructure Design revisión 2 de U2 (§1, §2, §3, §4, §5 e IDS-U2-01 a IDS-U2-15), de U3 (pool y
  `connectionLimit`) y de U10; `cicd-pipeline.md` de U11 (IDS-U11-04, -07 y -08).
- `## Deployment` y `## Testing Posture` de `team.md`, y las reglas de `project.md`.

## 1. Despliegue

| Facet | Choice | Rationale |
|---|---|---|
| Modelo de cómputo | Contenedores en el clúster Minikube de U2, namespace `veridicus`: `Deployment` `veridicus-session-api` (API, de U3), `Deployment` `veridicus-session-api-worker` (misma imagen, orden `python -m session_api.worker`), `Deployment` `veridicus-semantic-agent` y `Deployment` `veridicus-frontend` (consola) | D11, D12; logical-components §4; nombres `veridicus-` de `team.md` e IDS-U2-14 |
| Réplicas | 1 de cada uno, sin HPA, sin KEDA (apagado en U2) y sin `PodDisruptionBudget`; cambiar es un PR | scalability-design §1 y §4: una corrida a la vez y un solo consumidor que supone el cálculo del plazo |
| Procesos del trabajador | Cuatro hilos con su conexión cada uno: `ResultIngestor`, `RunSupervisor` (que también ejecuta el `XTRIM` del audio de U9), `HoldReleaser` y `SessionSupervisor` de U6 | logical-components §1; NFRD-U6-05; NFRD-U9-05 |
| Procesos de `semantic-agent` | Bucle consumidor de C2 (`analyze` de U11 en proceso), hilo `ClaimRenewer` y hilo `HealthServer` | D12; reliability-design §3 y §6 |
| Puertos | `http` 8080 (`/healthz`, `/readyz`; en la API, además `/api/v1`) y `metrics` 8081 (`/metrics`) en la API, el trabajador y `semantic-agent`; `frontend` solo 8080. Solo `/` y `/api/` los enruta el `Ingress` | C16; NFR10.23 de U3 (mismo par de puertos); IDS-U4-14 |
| Estrategia de actualización | API y `frontend`: `RollingUpdate` (`maxSurge: 1`, `maxUnavailable: 0`), de U2. **Trabajador y `semantic-agent`: `Recreate`** (IDS-U4-01, IDS-U4-02) | `Recreate` garantiza un solo consumidor de C2 (NFR8.7) y un solo juego de hilos del trabajador; los mensajes esperan en Redis y el plazo los cubre |
| Apagado | `terminationGracePeriodSeconds: 30` en el trabajador y en `semantic-agent`. Con `SIGTERM`, el trabajador deja de leer y termina el mensaje en curso (ingesta ≤ 5 s); `semantic-agent` deja de leer, marca su cancelación local (el `cancelled()` de C17 devuelve verdadero antes de la siguiente llamada), no publica y deja el mensaje pendiente (IDS-U4-04) | reliability-design §3 (mensaje pendiente y reclamo a los 60 s); cierra R-01 de la revisión 1 |
| Sondas | Tabla de §1.2 | reliability-design §6; NFRD-U6-05 |
| Imágenes | `session-api` (de U3, con el trabajador dentro) y `semantic-agent` sobre Python 3.12 mínimo por digest, sin root (UID 10001), en GHCR por SHA y usadas por digest. `semantic-agent` lleva `libs-incoherence-analyzer` y **no** `libs-anonymizer`, `psycopg` ni `sqlalchemy`. `frontend` sobre `nginx-unprivileged` por digest | `team.md` (Deployment); D18; security-design §10 |
| Almacenamiento | `readOnlyRootFilesystem: true`; `/tmp` como `emptyDir` `medium: Memory` de 16 MiB en el trabajador y en `semantic-agent` (IDS-U4-05), y `/var/cache/nginx` en memoria en `frontend`. Sin PVC: los datos viven en `veridicus-pg` y los mensajes en `veridicus-redis` hasta su `XDEL` | `memory-only-tmp` de U2; security-design §6 (memoria sin caché entre corridas) |
| Configuración montada | `ConfigMap` `veridicus-profiles` de U2 (`profiles.yaml` y `prices.yaml`) en solo lectura en la API, el trabajador y `semantic-agent` (IDS-U4-09); el catálogo `contracts/limits.v1.yaml` va **dentro de la imagen** (`VERIDICUS_LIMITS_PATH`) | NFR10.15 de U2; D20; security-design §8 |
| Red | Tabla de §3; la escribe U2 en `network-deps.yaml` | NFR1.1–NFR1.3; logical-components §4 |
| Entornos | Una sola máquina de 64 GB, solo CPU, con el mismo digest que publica la CI. Sin *staging* ni producción | Supuesto del brief; IDS-U2-01 |
| IaC | Subcharts `session-api` (con la plantilla del trabajador) y `semantic-agent`, y la plantilla de `frontend`, dentro del chart paraguas de U2 con `values-cpu.yaml`. Ningún *script* los aplica | AUTONOMIA-01: el humano aplica lo fusionado y, desde el módulo 8, Argo CD sincroniza |
| Recursos | Los de U2 §4, sin cambios: trabajador 0,25/384 MiB → 1/640 MiB; `semantic-agent` 0,25/512 MiB → 1/960 MiB; sin GPU | performance-design §7 con el `/tmp` en memoria (§1.1) |
| Clasificación | `veridicus.io/data-class: sensitive` en la API, el trabajador y `semantic-agent`; `internal` en `frontend` | Tabla de clasificación de U2; security-design §1 |

### 1.1 Recursos frente a los picos (NFR8.3, NFR8.12)

| Contenedor | Pico (performance-design §7) | `/tmp` en memoria | 1,2 × (pico + `/tmp`) | `limits.memory` de U2 | ¿Cabe? |
|---|---|---|---|---|---|
| `semantic-agent` | ≤ 768 MiB (modo final de 250 000 caracteres y respuestas de 2 MiB) | 16 MiB | 941 MiB | 960 MiB | Sí |
| Trabajador de `session-api` | ≤ 512 MiB (`RunResult` de 2 MiB) | 16 MiB | 634 MiB | 640 MiB | Sí |
| API de `session-api` | Cifra de U3 y U7 | 16 MiB (U3) | — | 1,125 GiB | Valor de U2 |

El cuarto hilo del trabajador solo suma una conexión y una pila de hilo (≈ 8 MiB); no cambia el pico. Con
`Recreate` nunca conviven dos pods del trabajador ni de `semantic-agent`, así que U4 **no suma memoria** al
presupuesto de 41 GiB y 14,5 CPU de U2 durante un despliegue.

### 1.2 Sondas (C16, NFR10.19)

| Proceso | `startupProbe` | `livenessProbe` | `readinessProbe` |
|---|---|---|---|
| API de `session-api` | La de U3 | La de U3 | `/readyz` de U3 (PostgreSQL y Redis); con Redis caído toda la consola queda fuera de servicio (NFRD-U6-08) |
| Trabajador | `/healthz` en 8080, periodo 2 s, 30 fallos (60 s) | `/healthz`, periodo 10 s, plazo 2 s, 3 fallos: los **cuatro** hilos con señal en los últimos 45 s (IDS-U4-06) | `/readyz`, periodo 10 s: PostgreSQL y Redis en su *timeout* |
| `semantic-agent` | `/healthz`, periodo 5 s, 12 fallos (60 s) | `/healthz`, periodo 10 s, plazo 2 s, 3 fallos: bucle con señal en los últimos 45 s, o corrida en curso con renovación viva | `/readyz`, periodo 10 s: perfiles y límites válidos, Redis, `check_ready()` del proxy si hay un perfil externo, servidores locales que informa U11 |
| `frontend` | — | `/healthz` (archivo estático), periodo 10 s | Ídem |

Una configuración inválida, un perfil externo por debajo del piso de 270 s o
`VERIDICUS_ANONYMIZER_PROXY_URL` fuera del clúster terminan el proceso antes de abrir el puerto
(NFRD-U4-09, NFRD-U6-09): el pod nunca pasa a listo. El trabajador y `semantic-agent` no tienen `Service`
de tráfico: su `readinessProbe` solo frena el despliegue, y mientras `/readyz` de `semantic-agent` falla el
propio bucle no lee la cola (reliability-design §6).

## 2. Servicios de infraestructura

| Service | Role | Configuration | Notes |
|---|---|---|---|
| `veridicus-pg` (U2) | database | Rol `veridicus_app` (Secret `veridicus-db-app`) en la API y en el trabajador. API: *pool* de U3, 5 + 5. Trabajador: *pool* fijo de **4** (uno por hilo). `statement_timeout` 2 s al abrir cada conexión; la ingesta usa `SET LOCAL statement_timeout` e `idle_in_transaction_session_timeout` de 5 s, nunca en el `Cluster` ni en el rol | reliability-design §1; NFRD-U6-05; NFRD-U7-01. Presupuesto de conexiones en §2.1 |
| Función `veridicus_purge_lock_session(uuid)` | database | `SECURITY DEFINER` de `veridicus_owner`, solo `SELECT … FOR UPDATE` sobre `interview_session`, `EXECUTE` solo para `veridicus_retention`; entra con la migración de U4 | NFRD-U13-05 |
| `veridicus-redis` (U2) | queue | *Streams* `veridicus:runs` (grupo `analysis-worker`) y `veridicus:results` (grupo `session-ingest`), y sus `:failed` con `MAXLEN ~ 1000`; claves `veridicus:run-cancelled:{run_id}` con TTL; `XACK` + `XDEL` tras el efecto; `XREADGROUP BLOCK 5000` con `socket_timeout` 6 s; resto de operaciones con 0,5 s. Contraseña del Secret `veridicus-redis-auth` | scalability-design §2; security-design §6; reliability-design §11 |
| Capacidad de Redis | queue | Un mensaje C2 ocupa ≤ 1,35 MB con la transcripción máxima (≤ `run_message_max_bytes` = 2 097 152). Con 60 corridas en cola (el tope que deja vencer el plazo) son ≈ 81 MB de los 384 MB de `maxmemory`. Con `noeviction`, un `XADD` que no cabe falla, se registra `run.publish_failed` y el supervisor cierra la corrida | performance-design §9; reliability-design §10 |
| `anonymizer-proxy` (U10, desplegado por U2) | other | `VERIDICUS_ANONYMIZER_PROXY_URL` = `http://anonymizer-proxy.veridicus.svc.cluster.local:8080` en `semantic-agent`; U4 usa como mucho 1 de sus 4 peticiones simultáneas | security-design §10; NFR-U4-12 |
| `model-verifier`, `model-judge` (U2) | other | URL internas de U2 §2.2, que U11 lee del perfil; clave del Secret `veridicus-model-api-key` | Solo `semantic-agent` los llama; `model-judge` solo si `models.todoLocalJudge.enabled` |
| `ingress-nginx` (U2) | load-balancer | `veridicus-web`: `/` → `veridicus-frontend:8080` y `/api/` → `veridicus-session-api:8080`, sin disco y con tope de 2 113 536 bytes | El tope es mayor que el corte de un turno (84 096 bytes), así que el `413` siempre lo da `session-api` (security-design §7) |
| `cdn`, `search`, caché | — | No aplica | La búsqueda de pasajes salió con el cambio 01 (NFR8.9 «Retirado») |

### 2.1 Conexiones de `veridicus_app` (pico frente al límite)

| Quién | Conexiones | Pico en un despliegue |
|---|---|---|
| API de `session-api` (U3) | ≤ 10 por réplica | 20 (`RollingUpdate`) |
| Trabajador (U4) | 4 | 4 (`Recreate`, IDS-U4-02) |
| `create-admin-job` (U3) | 1 | 1 (lo lanza el humano) |
| **Total** | — | **25** |

El total iguala el `connectionLimit: 25` que fijaron U3 y U2 sin contar el trabajador, así que no queda
margen para una reconexión del *pool* antes de que PostgreSQL libere la conexión vieja. U4 pide a U2 subirlo
a **30** (IDS-U4-03): 30 de `veridicus_app`, ≤ 2 de `veridicus_owner`, ≤ 2 de `veridicus_retention` y 3
reservadas siguen cabiendo en `max_connections = 50`.

### 2.2 Ajustes del contenedor (prefijo `VERIDICUS_`)

| Variable | Valor en `values-cpu.yaml` | Procesos | Origen |
|---|---|---|---|
| `VERIDICUS_PROFILES_PATH` | `/etc/veridicus/profiles/profiles.yaml` (montado) | API, trabajador, `semantic-agent` | tech-stack §2; IDS-U4-09 |
| `VERIDICUS_LIMITS_PATH` | Catálogo empaquetado en la imagen | Los tres | D20 |
| `VERIDICUS_LIMIT_*` | Sin definir: rige `contracts/limits.v1.yaml` (solo se puede bajar) | Los tres | `check-limits-env.sh` de U2 |
| `VERIDICUS_ANONYMIZER_PROXY_URL` | URL interna de §2 | `semantic-agent` | security-design §10 |
| `VERIDICUS_DEADLINE_SWEEP_SECONDS` | 15 | Trabajador | reliability-design §4 |
| `VERIDICUS_RELEASE_POLL_MS` | 500 (entre 100 y 1 000) | Trabajador | NFRD-U4-14 |
| `VERIDICUS_CLAIM_RENEW_SECONDS` | 15 | `semantic-agent` | D17 |
| `VERIDICUS_PUBLISH_RETRIES` | 3 (entre 0 y 5) | `semantic-agent` | NFRD-U4-14 |
| `VERIDICUS_FAILED_STREAM_MAXLEN` | 1000 | Trabajador, `semantic-agent` | tech-stack §2 |
| Base de datos | `veridicus-pg-rw…:5432`, `sslmode=verify-full`; usuario y contraseña de `veridicus-db-app` por `secretKeyRef` | API, trabajador | NFR10.13 de U2 |
| Redis | `veridicus-redis…:6379`; contraseña de `veridicus-redis-auth` (clave `password`) por `secretKeyRef` | Los tres | IDS-U2-10 |
| Clave de los servidores locales | `veridicus-model-api-key` por `secretKeyRef`, con el nombre que fije el perfil de U11 | `semantic-agent` | NFR10.13 de U2 |

El plazo por llamada (`model_call_timeout_s` ≥ 270 s con perfil comercial) sale del perfil y de C25; el piso
es la constante `COMMERCIAL_MIN_CALL_TIMEOUT_S` de `libs/execution_profiles`, no una variable. Salen de la
revisión 1 `VERIDICUS_SIMILARITY_THRESHOLD`, `_TOP_K`, `_TURN_DEADLINE_*`, `_QUEUE_*`, `_JUDGE_*`,
`_EMBEDDINGS_*` y `_PASSAGE_MAX_CHARS`.

## 3. Red de U4 (NFR1.1–NFR1.3, AUTONOMIA-04)

| Proceso | Entrada | Salida |
|---|---|---|
| API de `session-api` | `ingress-nginx` → 8080; Prometheus → 8081 | `veridicus-pg`, `veridicus-redis`, `audio-worker` (U9), CoreDNS |
| Trabajador | Prometheus → 8081 | `veridicus-pg`, `veridicus-redis`, CoreDNS |
| `semantic-agent` | Prometheus → 8081 | `veridicus-redis`, `anonymizer-proxy` 8080, `model-verifier` 8080, `model-judge` 8080 (solo con el interruptor), CoreDNS. **Nunca** `veridicus-pg` |
| `frontend` | `ingress-nginx` → 8080 | CoreDNS |

Ningún proceso de U4 sale del namespace ni a internet; lo único que sale lo envía `anonymizer-proxy`, ya
seudonimizado (security-design §1). `kubectl port-forward` del humano (prueba de humo, prueba de carga) no
pasa por las `NetworkPolicy`: es un acceso humano fuera de la política y no cambia el clúster (IDS-U2-15).

### 3.1 Frontera por componente (AUTONOMIA-04)

| Componente | Dentro o fuera del clúster | Datos que cruzan su frontera |
|---|---|---|
| Rutas de U4 en la API | Dentro | Turnos, consentimiento y sugerencias hacia el navegador por C1 |
| Trabajador (ingesta, supervisores, liberación) | Dentro | Mensajes C2/C3 y claves de cancelación con Redis; filas con PostgreSQL |
| `semantic-agent` con la biblioteca de U11 | Dentro, sin salida externa | La transcripción en memoria solo hacia el proxy (C21) y los servidores locales (C14) |
| `anonymizer-proxy` | Dentro, único con salida | Solo el cuerpo seudonimizado, por 443 |
| Consola M3, M4 | Navegador | Solo habla con ConsoleApi |
| `run_batches.py` y `smoke.sh` | **Fuera**: WSL2 del equipo del humano | Solo datos sintéticos, por `port-forward` hacia la API (IDS-U4-08) |

## 4. Consola (`frontend`)

| Aspecto | Diseño |
|---|---|
| Contenido | Archivos compilados de React + TypeScript; U4 aporta la base, M3, M4 y el aviso de propósito limitado (F13); U3 y U5–U9 añaden pantallas por PR a la misma imagen |
| Cabeceras | `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; object-src 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, en la configuración de nginx de la imagen |
| Caché | `index.html` con `Cache-Control: no-store`; archivos con *hash* en el nombre, `max-age` de un año |
| Sondeo | 2 s con corridas en `queued` o `processing` y 15 s sin ellas, cifras generadas en *build* desde C25; reintento a 2, 4, 8, 16 y 30 s ante red o 5xx; sin WebSockets (performance-design §6, reliability-design §7) |
| Acceso | `https://veridicus.local:8443` por el `port-forward` del Ingress (IDS-U2-04) |

## 5. Evaluación de nivel 2 · Retirado

Retirado: el nivel 2 es del analizador (U11) y corre con la CLI en WSL2 frente al verificador de la
anfitriona o a un proveedor comercial (`cicd-pipeline.md` de U11, IDS-U11-04 e IDS-U11-05). Con él salen
`scripts/eval-level2.sh`, el `port-forward` al juez y a los *embeddings* y la paridad de D16, y se cierran
R-02 y R-03 de la revisión 1. U4 conserva la prueba de carga de NFR8.5 (IDS-U4-08) y la paridad con la CLI
en niveles 0 y 1 (reliability-design §14).

## 6. Infraestructura compartida

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Trabajador de `session-api` | U4 | U6 (`SessionSupervisor`), U9 (vencimiento de voz y `XTRIM` en el supervisor; liberación de esperas), U7, U8 | Un hilo por responsabilidad; cada unidad añade su código por PR; orden de bloqueo sesión → corrida → ronda |
| `semantic-agent` | U4 | U8 (permutación por perfil), U11 (biblioteca en proceso) | Una corrida a la vez; import-linter sin `libs.anonymizer` ni drivers de base |
| `RunEnqueuer`, `CancellationKeys`, `EthicsSessionPort` | U4 | U6, U9, U13 | Funciones en proceso; U13 solo escribe claves en su `Job` (NFRD-U13-06) |
| `frontend` | U4 (base de la consola) | U3 y U5–U9 | Una sola imagen; textos solo del catálogo de U1 |
| `veridicus-pg`, `veridicus-redis`, `veridicus-profiles`, servidores locales, `anonymizer-proxy`, `Ingress` | U2 (U10 la imagen del proxy) | U4 entre otras | Tabla de infraestructura compartida de U2 §7 |
| `contracts/limits.v1.yaml`, C2, C3, C6 y `contracts/metrics/text-flow.v1.yaml` | U1 | U4 | Cambian por PR de U1 |

## 7. Precisiones y peticiones (IDS-U4-xx)

No edité ningún artefacto aprobado ni de otra unidad. En la aprobación decides cuáles se llevan al
original, cada una en su propio commit. Las peticiones a U2 no se dan por aplicadas. Todas salen de las
fuentes aprobadas o de un hecho técnico, y ninguna deja salir del clúster algo que hoy no sale.

| ID | Artefacto que precisa | Precisión | Origen |
|---|---|---|---|
| IDS-U4-01 | Infrastructure Design de U2 §5 (`semantic-agent` con `RollingUpdate`) | **Petición a U2:** `veridicus-semantic-agent` con estrategia `Recreate`. Con `maxSurge: 1`, el pod nuevo ya listo consume la siguiente corrida mientras el viejo termina la suya: dos corridas a la vez, 2 de las 4 peticiones del proxy y dos llamadas contra la ranura única de cada servidor local | NFR8.7; scalability-design §1 y §4; R-01 de la revisión 1 |
| IDS-U4-02 | Infrastructure Design de U2 §5 (`session-api` con `RollingUpdate`) | **Petición a U2:** el `Deployment` del trabajador con `Recreate`; la API sigue con `RollingUpdate`. El trabajador no sirve tráfico, sus efectos ya son idempotentes, y así nunca abre 8 conexiones ni ejecuta dos juegos de supervisores | §2.1; reliability-design §4 |
| IDS-U4-03 | Infrastructure Design de U2 §2.1 e IDS-U2-14, y de U3 (`connectionLimit: 25`) | **Petición a U2:** `connectionLimit: 30` para `veridicus_app`. El 25 se calculó con la API sola (2 × 10 + `create-admin` + margen); con el trabajador de 4 el pico es 25 exacto. `max_connections = 50` no cambia | §2.1; NFRD-U6-05 |
| IDS-U4-04 | `nfr-design/reliability-design.md` §3 y §6 | Apagado ordenado con `terminationGracePeriodSeconds: 30`: el trabajador termina el mensaje en curso; `semantic-agent` marca su cancelación local, no publica y deja el mensaje pendiente, que el pod nuevo reclama tras 60 s y cuenta como una entrega más. Un despliegue a mitad de corrida puede reenviar el mismo cuerpo seudonimizado dentro del tope de 3 (NFRD-U10-14); el runbook pide desplegar `semantic-agent` con `veridicus_run_queue_depth` = 0 y ninguna corrida en `processing` | R-01 de la revisión 1; NFRD-U4-01 |
| IDS-U4-05 | `nfr-design/performance-design.md` §7 | `/tmp` en memoria de 16 MiB en el trabajador y en `semantic-agent`; con él, 1,2 × (pico + `/tmp`) cabe en los límites de U2 (941 de 960 MiB y 634 de 640 MiB). Si una medición de B4 sube un pico, el límite sube por PR | `memory-only-tmp` de U2; §1.1 |
| IDS-U4-06 | `nfr-design/reliability-design.md` §6 («los tres hilos») | `/healthz` del trabajador exige señal de los **cuatro** hilos en los últimos 45 s y lo usa la `livenessProbe`: un hilo bloqueado sin excepción reinicia el pod en ≤ 75 s | NFRD-U6-05; R-06 de la revisión 1 |
| IDS-U4-07 | NFR Design de U2 §9 (alcance de `check-no-cluster-apply.sh`) | **Petición a U2:** el alcance suma `evaluation/load/` (Python), donde vive `run_batches.py`, que solo habla HTTP con la API y consulta Prometheus en modo lectura | AUTONOMIA-01; R-04 de la revisión 1 |
| IDS-U4-08 | `nfr-design/reliability-design.md` §14 y NFRD-U8-11 | `run_batches.py` corre en WSL2, llega a la API por `https://veridicus.local:8443` (IDS-U2-04) con un analista sintético cuyas credenciales vienen del `.env` no versionado, inicia sesión una vez y la reutiliza (el limitador por IP de U3 ve un solo cliente, IDS-U2-12), y consulta Prometheus por un `port-forward` de solo lectura que abre el humano. Usa `comercial-piloto` solo con datos sintéticos | NFR8.5; IDS-U2-12; `project.md` |
| IDS-U4-09 | NFR10.15 de U2 («montado en `session-api`») | «`session-api`» abarca los dos `Deployment`, API y trabajador: los dos validan perfiles al arrancar (security-design §8; NFRD-U8-12) | security-design §8 |
| IDS-U4-10 | NFR10.12 y NFR10.13 de U2 (`secret-consumers.yaml`) | **Petición a U2:** el trabajador referencia solo `veridicus-db-app` y `veridicus-redis-auth`; `semantic-agent` solo `veridicus-redis-auth` y `veridicus-model-api-key`. Control negativo nuevo: `veridicus-db-app` en `semantic-agent` falla (la mitad de manifiestos de NFR10.6) | security-design §5; DS3 |
| IDS-U4-11 | Revisión 1 de esta etapa (los cuatro artefactos) | Se retiran: el juez y los *embeddings* de U4, el `ConfigMap` del *prompt* y `VERIDICUS_JUDGE_PROMPT_SHA256`, el umbral, el rol `veridicus_indexer` y `veridicus_judge_ro`, `pgvector`, los *streams* `veridicus:turns` y `veridicus:indexing`, `scripts/eval-level2.sh`, los Minikube de 20 y 28 GiB y `values-gpu.yaml`, las métricas del juez y de la indexación, y la tabla de precisiones de §7 de la revisión 1 | Cambio 01; IDS-U2-01; IDS-U2-02 |
| IDS-U4-12 | `cicd-pipeline.md` de la revisión 1 (`libs.yml`, `ai-eval-gate.yml`) | Se adopta IDS-U11-08: los dos salen y los sustituyen `analyzer.yml` y `analyzer-level2-gate.yml` de U11. `semantic-agent.yml` conserva el filtro por `libs/**` y sigue el patrón de IDS-U11-07 (*job* `changes` y *job* `gate` como única comprobación obligatoria). **Petición al humano** (P0.1): `semantic-agent / gate` y `frontend / gate` en las comprobaciones obligatorias de `main` | IDS-U11-07; IDS-U11-08 |
| IDS-U4-13 | `team.md` (nivel 2 en «toda entrega etiquetada») | Una etiqueta del producto exige la salida de `smoke.sh` y el reporte de Playwright del mismo SHA, y un par de nivel 2 en `evaluation/reports/level2/` para la versión de `libs-incoherence-analyzer` que fija el `uv.lock` de `semantic-agent` (lo comprueba `check-level2-report.py` de U11) | IDS-U11-04; R-04 de la revisión 1 |
| IDS-U4-14 | NFR Design de U2 §2.1 («puerto `metrics` de cada unidad») | El puerto `metrics` de U4 es 8081 en la API, el trabajador y `semantic-agent`, igual que U3. Los `ServiceMonitor` y las reglas de U4 solo se renderizan con `monitoring.enabled: true`. **Petición a U2:** `check-config-copy.sh` compara también la fila del panel de U4 con su original en `services/session-api/observability/`, como hace con el panel de U10 | NFR10.23 de U3; R-07 de la revisión 1; IDS-U2-13 |
| IDS-U4-15 | `team.md` (`## Deployment`, dos máquinas y etapa GPU) | Con el supuesto del brief, U4 no tiene valores por máquina: un solo `values-cpu.yaml` y ninguna petición de `nvidia.com/gpu` | IDS-U2-01; IDS-U2-02 |

## 8. Cierre de los hallazgos de la revisión 1

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (rodadura de `semantic-agent` y periodo de gracia) | §1 (`Recreate` y apagado); IDS-U4-01, IDS-U4-04 |
| R-02 (acceso del arnés de nivel 2 a la base y a la clave del juez) | §5 «Retirado»: el nivel 2 es de U11 y no usa la base |
| R-03 (entrada del juez y `port-forward`) | §3 (el `port-forward` es acceso humano fuera de la política); el juez es de U2 |
| R-04 (puerta de etiquetado y AUTONOMIA-01 citada) | IDS-U4-07, IDS-U4-13; `cicd-pipeline.md` §4 |
| R-05 (unidades de memoria y conexiones) | §1.1 (cifras en MiB y GiB de U2) y §2.1 |
| R-06 (latido en la sonda de vida; *embeddings* caídos) | §1.2 e IDS-U4-06; los *embeddings* salieron |
| R-07 (`ServiceMonitor` sin el CRD) | IDS-U4-14; `monitoring-design.md` §1 |
