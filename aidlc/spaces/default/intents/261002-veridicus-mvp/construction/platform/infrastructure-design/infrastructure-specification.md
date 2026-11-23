# Especificación de infraestructura — U2 platform

**Revisión 2 (2026-11-23).** Es la segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2. Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git. Las secciones §1–§8
conservan su número y lo nuevo empieza en §9. Lo que sale queda «Retirado», sin renumerar. Las precisiones
nuevas son IDS-U2-01 en adelante (§10), y §9 cierra los hallazgos R-01 a R-09 de `reviews/review-01.md`.

**Insumos.**
- Diseño de seguridad de `nfr-design/security-design.md` revisión 2 (security-design): zonas, red §2.1,
  Ingress sin disco §3, imágenes §4, endurecimiento §5, Secrets §6, datos persistentes §7, dónde se aplican
  las políticas §8, nada aplica cambios §9, observabilidad §11, respaldos §12, recursos §13 y precisiones
  NFRD-U2-01 a NFRD-U2-16.
- U2 es `packaging` y no produjo performance-design, scalability-design, reliability-design,
  observability-design ni logical-components propios. Lo que esos documentos de otras unidades piden a U2
  llega por la tabla NFRD de cada `security-design.md` y por sus tablas de recursos: picos de
  `semantic-agent` y del trabajador de `session-api`, de `model-whisper`, `model-tts` y `audio-worker`, del
  proxy y del `Job` de retención. La lista está en §4.
- Las peticiones de NFR Design dirigidas a U2: puerto 9090 y raspado del proxy con su panel; entrada a la
  síntesis solo desde la API de `session-api`; `log_error_verbosity: terse`; ningún manifiesto con
  `VERIDICUS_LIMIT_RETENTION_MAX_DAYS`; el plazo de inactividad por transacción con `SET LOCAL`, fuera de
  `veridicus-pg`.
- Requisitos NFR1.1–NFR15.2 de `nfr-requirements/security-requirements.md` y decisiones D1–D17 de
  `nfr-requirements/tech-stack-decisions.md`.
- Dependencias externas y frontera del clúster de `inception/domain-design/components.md` (components).
- C1, C14–C16, C21, C22, C25, CD-04 y CD-06 de `inception/contract-design/contract-summary.md`
  (contract-summary). U2 no tiene functional-spec propio; los de U3, U9, U10 y U13 (functional-spec)
  llegan a través de las tablas de NFR Requirements que cita security-design.
- Respuestas P1–P8 de `infrastructure-design-questions.md` (P6–P8 de la segunda pasada, delegadas por el
  humano el 2026-11-23).
- `## Deployment` de `team.md` y las prohibiciones de `project.md`.

U2 es `packaging`: este documento fija **dónde y con qué** corre todo el sistema. El chart y los *scripts*
se escriben en Code Generation; aquí solo se decide su forma y sus valores.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Distribución de Kubernetes | **Minikube** con el *driver* Docker, un solo nodo, Kubernetes **v1.31.4** fijado en `scripts/cluster-up.sh` y en los esquemas de `kubeconform` (P1 = A) | El PRD (S13) nombra Minikube; es la misma distribución en desarrollo y en la demostración |
| CNI | **Calico** (`--cni=calico`), *pod CIDR* `10.244.0.0/16` | Hace cumplir las `NetworkPolicy` (NFR1.1, AUTONOMIA-04); la verificación manual de security-design §2.4 confirma que se cumplen sobre el kernel de WSL2 |
| Máquina | **Un solo equipo** para desarrollo y demostración: Intel Core i7-14700KF (8 núcleos de rendimiento, 12 de eficiencia, 28 hilos), 64 GB de RAM, solo CPU, Windows con WSL2 (P7 = A, P8 = A) | Información del humano del 2026-11-22; desarrollo y demostración usan el mismo clúster sin recrearlo |
| Reparto de memoria | Windows conserva **8 GB**; WSL2 recibe **56 GB** (Docker, contenedor de trabajo, contenedores de nivel 1: unos 6 GB); Minikube recibe **50 GiB** | §4: los `requests` suman ≈ 41 GiB |
| Reparto de CPU | WSL2 recibe **20** procesadores (Windows conserva 8 hilos); Minikube **16** CPU | §4: los `requests` suman ≈ 14 CPU |
| Máquina de desarrollo de 24 GB (revisión 1) | **Retirado** (IDS-U2-01) | La sustituye el equipo de 64 GB |
| Máquina GPU (opcional) | **Retirado** (IDS-U2-02) | No hay GPU en este MVP; la evaluación por lotes de modelos locales va a ZINE, con scripts que lanza el humano |
| Namespaces | `veridicus` para la aplicación, la base, Redis, los servidores de modelos y los `Job`; operadores en `cnpg-system`, `ingress-nginx` y, en el módulo 8, `argocd` y `monitoring`; `keda` solo si se activa (P2 = A) | C14 (`*.veridicus.svc.cluster.local`) y la política de negar todo por namespace (security-design §2.2) |
| Pod Security | `veridicus` y `argocd` con `enforce: restricted`; los de operadores con `baseline` como mínimo y cada desvío con su motivo | security-design §5 (NFR10.2) |
| Entrada | Complemento `ingress` de Minikube (ingress-nginx) con tres `Ingress` para `veridicus.local`, todos con TLS `veridicus-tls`, sin disco y con su tope de cuerpo (§2.4) | security-design §3 (NFR10.14) |
| Acceso desde el navegador | En Windows: `kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8443:443` en WSL2, que WSL2 reenvía al `localhost` de Windows; el archivo `hosts` de Windows lleva `127.0.0.1 veridicus.local`; URL `https://veridicus.local:8443`. Dentro de WSL2, `veridicus.local` apunta a `minikube ip` (IDS-U2-04) | Con el *driver* Docker, la `minikube ip` no se alcanza desde Windows. El comando solo vive en el runbook |
| Salida de red | Negada por defecto en cada namespace; reglas por dependencia (§3) | NFR1.1 |
| Almacenamiento | `storage-provisioner` de Minikube (`StorageClass` `standard`, hostPath dentro del nodo) para los PVC; los modelos en un `PersistentVolume` estático de solo lectura (§2.3) | Los datos sobreviven a `minikube stop`, no a `minikube delete` (§6) |
| Imágenes | Propias en GHCR privado, etiqueta del SHA y uso por digest; el nodo descarga con el Secret `ghcr-pull` | `## Deployment` de team.md; NFR10.1 |
| IaC | Chart paraguas `deploy/veridicus` con **`values-cpu.yaml`** como único archivo de valores; `values-gpu.yaml` **Retirado** (IDS-U2-02). `deploy/jobs/` aparte (retención y `create-admin`). Operadores con chart oficial y versión exacta | D3; AUTONOMIA-01: ningún *script* aplica manifiestos (security-design §9) |
| Clasificación de datos | Etiqueta `veridicus.io/data-class: sensitive` en los pods que manejan testimonio, audio o CoT (`session-api`, `semantic-agent`, `audio-worker`, `anonymizer-proxy`, PostgreSQL, Redis, `model-*`, `retention-job`); `internal` en `frontend`, `migrations-job` y `create-admin-job` | Frontera de components |

### 1.1 `.wslconfig` de Windows (lo crea el humano)

Va en `C:\Users\<usuario>\.wslconfig` y se aplica con `wsl --shutdown`. Si se usa Docker Desktop con el
*backend* WSL2, el mismo archivo fija su memoria.

```ini
[wsl2]
memory=56GB
processors=20
swap=8GB
localhostForwarding=true
```

El contenedor de trabajo veía hasta hoy 8 procesadores y unos 3,8 GiB: ese límite desaparece con este
archivo. El disco de WSL2 necesita unos 150 GB libres en Windows: modelos ≈ 34 GB, el disco de Minikube de
80 GB e imágenes.

### 1.2 `scripts/cluster-up.sh` (revisable, lo ejecuta el humano)

```bash
minikube start --driver=docker --kubernetes-version=v1.31.4 \
  --cni=calico --cpus=16 --memory=50g --disk-size=80g \
  --mount --mount-string="/srv/veridicus/models:/models"
minikube addons enable ingress
minikube addons enable metrics-server
```

`/srv/veridicus/models` está en el sistema de archivos ext4 de la distribución de WSL2, nunca en `/mnt/c`:
leer por 9p un GGUF de 21 GB haría lentísimo cada arranque y cada `verify-model` (IDS-U2-05). Cambiar
`--memory` o `--cpus` exige `minikube delete`, que borra los PVC; por eso el runbook pide `backup-db.sh`
antes.

## 2. Servicios de infraestructura

### 2.1 Servicios

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-pg` (CloudNativePG) | database | `Cluster` de 1 instancia con la imagen oficial de PostgreSQL 16 de CloudNativePG por digest, **sin `pgvector`**; PVC de 10 GiB; `max_connections = 50`, `shared_buffers = 256MB`; `enableSuperuserAccess: false`; TLS `verify-full`. `postgresql.parameters`: `log_parameter_max_length: "0"`, `log_parameter_max_length_on_error: "0"`, `log_min_duration_statement: "-1"`, `log_statement: "none"` y `log_error_verbosity: "terse"` | El plazo de inactividad **no** va en el `Cluster` ni en los roles: cada transacción lo fija con `SET LOCAL`. Kyverno `cnpg-cluster-hardening` exige los cinco parámetros y rechaza `idle_in_transaction_session_timeout` en el `Cluster` |
| Roles de PostgreSQL | database | `managed.roles` con exactamente `veridicus_owner` (solo `migrations-job`), `veridicus_app` (`session-api`, `create-admin-job`; `connectionLimit: 25` y sin parámetros de rol) y `veridicus_retention` (`retention-job`), cada uno con su Secret | `veridicus_judge_ro` **Retirado** (C9 «Retirado») |
| `veridicus-redis` | queue | `StatefulSet` de 1 réplica, Redis **7.2** por digest, `redis.conf` de security-design §7.2 (AOF `everysec`, `save ""`, reescritura a 16 MB, `protected-mode yes`, contraseña por `include`, comandos peligrosos renombrados), `maxmemory 384mb` con `noeviction`; PVC de 2 GiB | `noeviction`: una cola llena responde error en vez de perder turnos |
| `model-judge` | other (modelo) | `llama-server` por digest con **Qwen3.6-35B-A3B Q4_K_M** (P6 = A), `--ctx-size 32768`, `--cache-type-k q8_0 --cache-type-v q8_0`, `--parallel 1`, `--threads 8`, caché de *prompt* activa; puerto 8080; clave por `LLAMA_API_KEY` | Solo lo usa el perfil `todo-local`. Archivo y SHA-256 en `deploy/models.lock` (§2.3). Se apaga con `models.todoLocalJudge.enabled=false` (IDS-U2-11) |
| `model-verifier` | other (modelo) | `llama-server` por digest con **gpt-oss-20b Q8_0** (el SHA-256 del reporte de ZINE), `--parallel 1`, `--threads 8`, caché de *prompt* activa; puerto 8080; clave por `LLAMA_API_KEY` | Verificador de `comercial-piloto`, `evaluacion-comercial` y `todo-local`; ≤ 14 GB de RAM |
| `veridicus-embeddings` | other (modelo) | **Retirado** (D1 revisión 2: sale el servidor de *embeddings*) | — |
| `model-whisper` | other (modelo) | `faster-whisper` detrás de `/v1/audio/transcriptions` (C14), modelo `base` multilingüe CTranslate2 int8, `cpu_threads = 4`, una transcripción a la vez, sin registro del cuerpo, `/tmp` en memoria de 64 Mi; puerto 8080 | Formato CTranslate2: pesos planos sin código ejecutable (IDS-U2-08) |
| `model-tts` | other (modelo) | Piper (ONNX) con una voz `es_*` `medium`, 2 hilos, voz cargada al arrancar; puerto 8080 | La imagen y su envoltorio HTTP los define Infrastructure Design de U9; U2 da el `Deployment`, la red, el volumen y los recursos |
| `anonymizer-proxy` | other (salida) | Imagen propia por digest; puerto de la API 8080, `/metrics` en **9090**; `/tmp` en memoria; NER desde `veridicus-models` en solo lectura; claves de `veridicus-provider-keys`; perfiles del `ConfigMap` `veridicus-profiles` | Único pod de aplicación con salida a internet: 443 y DNS (NFR1.5) |
| `ingress-nginx` | load-balancer | Complemento de Minikube; tres `Ingress` (§2.4) | Termina TLS; nada a disco |
| CoreDNS | dns | El del clúster con el `Corefile` de `deploy/coredns/` (unión de la lista del anonimizador y de `infra-domains.yaml`); lo aplica el humano tras la fusión | NFR1.4 |
| Volúmenes de la aplicación | object-store | `veridicus-reports` 2 GiB y `veridicus-audio` 3 GiB (`ReadWriteOnce`), montados solo por la API de `session-api` y `retention-job` | security-design §7.3 |
| `cdn`, `search` | — | No aplica | Todo es local |

### 2.2 Direcciones internas

| Variable | Valor en `values-cpu.yaml` |
|---|---|
| Base de lectura y escritura | `veridicus-pg-rw.veridicus.svc.cluster.local:5432`, `sslmode=verify-full` con la CA `veridicus-pg-ca` |
| Redis | `veridicus-redis.veridicus.svc.cluster.local:6379` |
| `VERIDICUS_JUDGE_URL` | `http://model-judge.veridicus.svc.cluster.local:8080` |
| `VERIDICUS_VERIFIER_URL` | `http://model-verifier.veridicus.svc.cluster.local:8080` |
| `VERIDICUS_WHISPER_URL` | `http://model-whisper.veridicus.svc.cluster.local:8080` |
| `VERIDICUS_TTS_URL` | `http://model-tts.veridicus.svc.cluster.local:8080` |
| URL del proxy para `semantic-agent` | `http://anonymizer-proxy.veridicus.svc.cluster.local:8080` |
| `VERIDICUS_EMBEDDINGS_URL` | **Retirado** |
| `VERIDICUS_TRUSTED_PROXY` | El *pod CIDR* de `network-ranges.yaml` (`10.244.0.0/16`), porque solo ingress-nginx alcanza el puerto 8080 |
| `model_call_timeout_s` | ≥ 270 s en todo despliegue con perfil comercial (el piso vive en `libs/execution_profiles`) |

La política `internal-model-urls` rechaza cualquier URL de modelo que no termine en `.svc.cluster.local`
(NFR1.3). Ningún manifiesto define `VERIDICUS_LIMIT_RETENTION_MAX_DAYS`: la API y el `Job` leen la cifra del
catálogo `contracts/limits.v1.yaml` (§2.5).

### 2.3 Archivos de modelo

| Archivo | Uso | Tamaño aproximado | Origen del SHA-256 |
|---|---|---|---|
| Qwen3.6-35B-A3B Q4_K_M (GGUF) | `model-judge` (`todo-local`) | ≈ 21 GB | Se fija en `deploy/models.lock` con el PR de U2 en Code Generation |
| gpt-oss-20b Q8_0 (GGUF) | `model-verifier` | ≈ 12 GB | El del reporte de ZINE |
| Whisper `base` CTranslate2 int8 | `model-whisper` | ≈ 0,15 GB | `models.lock` |
| Voz Piper `es_*-medium` (ONNX y su JSON) | `model-tts` | ≈ 0,06 GB | `models.lock`, tras verificar la licencia de la voz |
| NER del anonimizador | `anonymizer-proxy` | El que fija U10 | `models.lock` |

| Paso | Diseño |
|---|---|
| Descarga | `scripts/fetch-models.sh` en WSL2 escribe en `/srv/veridicus/models` y verifica cada archivo contra `deploy/models.lock` (URL, revisión, `sha256`) |
| Montaje en el nodo | `--mount-string` de `cluster-up.sh` expone esa carpeta como `/models` dentro del nodo |
| Montaje en los pods | `PersistentVolume` estático `veridicus-models` (`ReadOnlyMany`) y su PVC, siempre con `readOnly: true` |
| Verificación al arrancar | `initContainer` `verify-model` (busybox por digest, `runAsUser 65532`) ejecuta `sha256sum -c` con la línea de `models.lock`; si no coincide, el servidor no arranca (NFR10.4) |

### 2.4 `Ingress` sin disco

Patrón único de security-design §3.2 en todo `Ingress` hacia `session-api`: `proxy-request-buffering: "off"`,
`proxy-buffering: "off"` y `proxy-max-temp-file-size: "0"`. Con eso desaparece el disco del Ingress en
`/api/`.

| `Ingress` | Rutas | Tope de cuerpo (bytes) |
|---|---|---|
| `veridicus-web` | `/` → `frontend:8080`; `/api/` → `veridicus-session-api:8080` | 2 113 536 |
| `veridicus-voice` | `^/api/v1/sessions/[0-9a-f-]{36}/voice-turns$` | 6 065 536 |
| `veridicus-research-reports` | `^/api/v1/research-reports$` | 8 454 144 |

Todos llevan `ssl-redirect`, HSTS y `proxy-read-timeout 30s`. `/metrics` no se enruta. Los topes salen de
`deploy/ingress-limits.yaml` y de `contracts/limits.v1.yaml` (security-design §3b).

### 2.5 Catálogo de límites

Toda cifra de límite se lee de `contracts/limits.v1.yaml`. El chart no repite ninguna;
`scripts/check-limits-env.sh <render>` falla si un manifiesto define `VERIDICUS_LIMIT_RETENTION_MAX_DAYS` o
cualquier variable `VERIDICUS_LIMIT_*` con un valor mayor que el del catálogo (control negativo: la variable
de retención en el `Job`).

## 3. Red permitida (NFR1.1, NFR1.5–NFR1.7, NFR10.6–NFR10.8)

La tabla de dependencias es la de security-design §2.1, en `deploy/network-deps.yaml`. Aquí se fijan los
rangos y las filas que esta revisión precisa:

| Origen | Destino | Puerto | Nota |
|---|---|---|---|
| `session-api` (pods de la API, `app.kubernetes.io/component: api`) | `audio-worker` (síntesis) | 8080 | El trabajador de `session-api` no llama a la síntesis; la regla de entrada solo admite la API |
| Prometheus (`monitoring`) | `anonymizer-proxy` | **9090** | Solo el puerto de métricas; la entrada a 8080 sigue siendo solo de `semantic-agent` |
| Prometheus | Puerto `metrics` de `session-api`, `semantic-agent`, `audio-worker` | El de cada unidad | Ni la API ni los servidores de modelos se raspan |
| `veridicus-pg` y operadores | API server: servicio `kubernetes` (`10.96.0.1:443`) y, tras DNAT, el nodo (`192.168.49.2:8443`) | 443, 8443 | Calico evalúa después del DNAT |
| `argocd-repo-server` | `0.0.0.0/0` con el `except` completo | 22, 443 | Solo `github.com` resuelve (CoreDNS) |
| `semantic-agent` | `model-judge` | 8080 | La regla solo aparece en el render si `models.todoLocalJudge.enabled` |

## 3.1 Forma de `deploy/network-ranges.yaml`

```yaml
schema_version: 1
pod_cidr: 10.244.0.0/16
service_cidr: 10.96.0.0/12
api_server:
  service: { ip: 10.96.0.1, port: 443 }
  node:    { ip: 192.168.49.2, port: 8443 }
private_except: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10, 169.254.0.0/16]
```

`192.168.49.2` es la IP que Minikube da al nodo con el *driver* Docker; si cambia, `cluster-up.sh` la imprime
y el humano corrige el archivo por PR.

## 4. Recursos por contenedor (`values-cpu.yaml`, NFR8.1)

Regla: `limits.memory` ≥ 1,2 × el pico medido o aprobado. En los servidores de `llama-server`, los pesos van
mapeados desde archivo y el kernel puede recuperar esa memoria sin matar el proceso, así que el límite es
**pesos + 1,2 × (caché KV + cálculo)** (IDS-U2-06).

| Contenedor | `requests` CPU / memoria | `limits` CPU / memoria | Origen del valor |
|---|---|---|---|
| `model-judge` | 4 / 20 GiB | 8 / 24 GiB | Pesos ≈ 19,7 GiB y KV q8_0 más cálculo ≈ 2,5 GiB; 8 hilos (uno por núcleo de rendimiento) |
| `model-verifier` | 4 / 12 GiB | 8 / 14 GiB | ≤ 14 GB del servidor del verificador; 8 hilos |
| `model-whisper` | 1 / 768 MiB | 4 / 1,3 GiB | Pico ≤ 1 GiB más 64 Mi de `/tmp` en memoria; `cpu_threads = 4` |
| `model-tts` | 0,5 / 384 MiB | 2 / 640 MiB | Pico ≤ 512 MiB; 2 hilos |
| `anonymizer-proxy` | 1 / 1536 MiB | 2 / 2 GiB | Pico de 1,5 GiB con el NER más su `/tmp` en memoria; `terminationGracePeriodSeconds: 290` (IDS-U2-13) |
| `veridicus-pg` | 0,5 / 1 GiB | 1 / 1,5 GiB | `shared_buffers` 256 MB y 50 conexiones |
| `veridicus-redis` | 0,1 / 256 MiB | 0,5 / 512 MiB | `maxmemory` 384 MB más el margen del AOF |
| `session-api` (API) | 0,5 / 512 MiB | 2 / 1,125 GiB | 768 MiB de U7 más 160 MiB de Argon2id y 16 MiB de `/tmp` en memoria de U3: 944 MiB × 1,2 ≈ 1 133 MiB |
| `session-api` (trabajador) | 0,25 / 384 MiB | 1 / 640 MiB | Pico ≤ 512 MiB ingiriendo un `RunResult` de 2 MiB |
| `semantic-agent` | 0,25 / 512 MiB | 1 / 960 MiB | Pico ≤ 768 MiB en un modo final de 250 000 caracteres |
| `audio-worker` | 0,1 / 192 MiB | 0,5 / 384 MiB | Pico ≤ 256 MiB más su `/tmp` en memoria |
| `frontend` | 0,05 / 32 MiB | 0,2 / 64 MiB | Archivos estáticos |
| `migrations-job`, `create-admin-job` | 0,1 / 128 MiB | 0,5 / 256 MiB | `create-admin` calcula un Argon2id de 64 MiB |
| `retention-job` | 0,25 / 256 MiB | 1 / 512 MiB | Cifras aprobadas de U13; `activeDeadlineSeconds` 3 600 |
| `verify-model` (`initContainer`) | 0,2 / 64 MiB | 1 / 128 MiB | `sha256sum` en flujo |

| Presupuesto de Minikube (50 GiB, 16 CPU) | CPU pedida | Memoria pedida | Memoria límite |
|---|---|---|---|
| Modelos (`model-judge`, `model-verifier`) | 8 | 32 GiB | 38 GiB |
| Voz (`model-whisper`, `model-tts`, `audio-worker`) | 1,6 | ≈ 1,3 GiB | ≈ 2,3 GiB |
| Aplicación y datos (proxy, base, Redis, `session-api`, `semantic-agent`, `frontend`) | 2,65 | ≈ 4,2 GiB | ≈ 6,7 GiB |
| Kubernetes, Calico, ingress-nginx, CloudNativePG, metrics-server | ≈ 1,5 | ≈ 2 GiB | ≈ 2,5 GiB |
| Módulo 8: `kube-prometheus-stack` mínimo y Argo CD sin Dex ni notificaciones | ≈ 0,8 | ≈ 1,5 GiB | ≈ 2,3 GiB |
| **Total** | **≈ 14,5 CPU** | **≈ 41 GiB** | **≈ 51,8 GiB** |

Los `requests` caben con 1,5 CPU y 9 GiB de margen (cierra R-05). Los límites superan en 1,8 GiB a los 50 GiB,
y se acepta por dos razones: el juez y el verificador nunca generan a la vez (una ranura cada uno, uno tras
otro en cada tramo), y sus pesos son memoria recuperable. Los `Job` son transitorios y no se suman. Si una
corrida de NFR8 muestra presión de memoria, el primer recorte es apagar el monitoreo durante esa corrida;
el segundo, apagar el juez de `todo-local` con su interruptor.

Durante una evaluación de nivel 2 con el verificador en la anfitriona (NFR2.2 de U11, ≤ 14 GB), el humano
apaga `model-judge` con `models.todoLocalJudge.enabled=false`, como artefacto revisable que él aplica
(AUTONOMIA-01).

## 5. Estrategia de actualización por componente

| Componente | Estrategia | Razón |
|---|---|---|
| `model-*` | `Recreate` | Dos réplicas del juez o del verificador no caben en memoria |
| `anonymizer-proxy`, `session-api`, `semantic-agent`, `audio-worker`, `frontend` | `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0` | Sin corte; las migraciones son *expand–contract* |
| `veridicus-redis` | `StatefulSet` `OnDelete` | Solo se reinicia a propósito |
| `veridicus-pg` | La gestiona CloudNativePG | Solo se actualiza por un cambio de imagen en un PR propio |
| `migrations-job` | `Job` con la revisión de Alembic en el nombre; en la ruta manual, `ttlSecondsAfterFinished: 3600`; con Argo CD, *hook* `Sync` en la onda −1 con `hook-delete-policy: BeforeHookCreation` | Prohibición de `project.md`; un `Job` es inmutable y no se acumulan (cierra R-04) |

## 6. Respaldo y recuperación (P4 = A)

| Situación | Qué se hace |
|---|---|
| Antes de la sustentación, de un cambio de esquema o de recrear el nodo | El humano ejecuta `scripts/backup-db.sh`: `pg_dump -Fc` por `kubectl exec` de solo lectura (lista cerrada de security-design §9) hacia `backups/`, ignorado por git, con poda por `retention_max_days` |
| Restaurar | Paso manual del humano en `docs/operacion/instalacion.md` (`pg_restore` sobre una base nueva); ningún *script* lo hace |
| `minikube delete` | Borra los PVC: se recrea el clúster, se restaura el último volcado o se vuelven a cargar el escenario y el conjunto sintético |
| Redis pierde datos | Las corridas en curso quedan en error y se relanzan a mano |

RPO: el último volcado manual. RTO: el de una restauración manual.

## 7. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `veridicus-pg` y sus roles | U2 (despliegue), `session-api` (esquema, por migraciones) | U3–U7, U9, U12 y U13 por `veridicus_app`; U13 por `veridicus_retention` | Rol por proceso; entrada al 5432 solo desde sus clientes |
| `veridicus-redis` | U2 | U3, U4, U9, U13 (y KEDA si se activa) | Contraseña única; prefijos por unidad; entrada solo desde sus clientes |
| `model-judge`, `model-verifier` | U2 | U4 (`semantic-agent`) con los perfiles de U11 | `LLAMA_API_KEY` y entrada solo desde `semantic-agent` |
| `model-whisper`, `model-tts` | U2 (despliegue), U9 (imagen de TTS) | U9 | Solo `audio-worker` |
| `anonymizer-proxy` | U10 (imagen), U2 (despliegue y red) | U4 | Entrada solo de `semantic-agent` (8080) y Prometheus (9090) |
| `Ingress` y TLS | U2 | Todas las pantallas | Tres grupos con tope y sin disco |
| Volumen de modelos | U2 | `model-*` y `anonymizer-proxy` | Solo lectura |
| Volúmenes `veridicus-reports` y `veridicus-audio` | U2 | U7, U9, U13 | API de `session-api` y `retention-job` |
| Prometheus y Grafana | U2 | Unidades con métricas (C15) | Solo los puertos `metrics` |

## 8. Precisiones a artefactos ya aprobados (revisión 1)

**Retirado como sección propia**: sus cuatro filas (Secret `ghcr-pull`, rol `veridicus_owner`, Redis 7.2 y
los *scripts* nuevos) ya están en el NFR Design revisión 2. Las precisiones de esta revisión están en §10.

## 9. Cierre de los hallazgos de la revisión 1

| Hallazgo | Dónde se cierra |
|---|---|
| R-01 (`limits` sin el 20 % sobre el pico) | §4: regla de 1,2 × pico y la de los servidores de `llama-server` (IDS-U2-06) |
| R-02 (CloudNativePG sin ruta al API server; exención de NFR10.9) | §3 y `network-ranges.yaml`; exención en security-design §5 |
| R-03 (`VERIDICUS_TRUSTED_PROXY`) | §2.2 |
| R-04 (orden de la ruta manual; `Job` acumulados) | §5 y `cicd-pipeline.md` §4.1 (instalación en dos pasos) |
| R-05 (presupuesto de CPU) | §4 |
| R-06 (imágenes sin origen; formato de Whisper) | §2.1 (imagen oficial sin `pgvector`) e IDS-U2-08 |
| R-07 (`securityContext` de terceros; sonda de Redis) | IDS-U2-09 e IDS-U2-10 |
| R-08 (*device plugin* de GPU; regla hacia el proxy) | GPU **Retirado**; la regla `semantic-agent` → `anonymizer-proxy` está en security-design §2.1 |
| R-09 (contrato de `check-no-cluster-apply.sh`) | security-design §9 |

## 10. Precisiones y decisiones aplicadas (IDS-U2-xx)

No edité ningún original. «Precisa» nombra el artefacto aprobado que la fila matiza; decides en la aprobación
si alguno se actualiza, cada uno en su propio commit.

| ID | Precisa | Qué | Dónde | Origen |
|---|---|---|---|---|
| IDS-U2-01 | `team.md` `## Deployment` («Dos máquinas»); regla de `project.md` de 28 GiB y 20 GiB; P3 y P5 de la revisión 1 | Un solo equipo de 64 GB, solo CPU, con WSL2: Windows 8 GB, WSL2 56 GB y 20 procesadores, Minikube 50 GiB y 16 CPU, un solo tamaño para desarrollo y demostración | §1, §1.1, §1.2, §4 | P7 = A, P8 = A |
| IDS-U2-02 | `nfr-requirements/security-requirements.md` NFR2.1 («Solo `values-gpu.yaml` lo pide»); `nfr-design/security-design.md` §5 y §8; `tech-stack-decisions.md` D3; `team.md` `## Testing Posture`; regla de `project.md` de la GPU opcional | Sale `values-gpu.yaml`; la política `gpu-only-in-gpu-values` pasa a `no-gpu-requests`, que rechaza `nvidia.com/gpu` en todo render (control negativo: el juez con GPU) | §1, `cicd-pipeline.md` §2 | Información del humano del 2026-11-22 |
| IDS-U2-03 | — | El juez de `todo-local` es Qwen3.6-35B-A3B Q4_K_M, el mismo modelo que se evalúa en ZINE con una cuantización menor; su SHA-256 entra en `models.lock` con el PR de Code Generation | §2.1, §2.3 | P6 = A |
| IDS-U2-04 | `nfr-design/security-design.md` §3.1 (`/etc/hosts` apunta a `minikube ip`) | Desde Windows, `veridicus.local` apunta a `127.0.0.1` y se entra por `kubectl port-forward` del ingress en `127.0.0.1:8443`; dentro de WSL2 sigue apuntando a `minikube ip`. `smoke.sh` y `check-ingress-routes.sh` reciben la URL base con el puerto | §1 | *Driver* Docker sobre WSL2 |
| IDS-U2-05 | — | Los modelos viven en el ext4 de la distribución de WSL2 (`/srv/veridicus/models`), nunca en `/mnt/c` | §1.2, §2.3 | Rendimiento de 9p con archivos de más de 20 GB |
| IDS-U2-06 | — | En los servidores de `llama-server` el margen del 20 % se aplica a la caché KV y al cálculo, no a los pesos mapeados desde archivo | §4 | R-01; los pesos son memoria recuperable |
| IDS-U2-07 | `cicd-pipeline.md` revisión 1 §4.1 | La ruta manual instala en dos pasos (datos y migraciones, luego servicios) y el `Job` de migraciones es un *hook* `Sync` con `BeforeHookCreation` en Argo CD | §5, `cicd-pipeline.md` §4 | R-04 |
| IDS-U2-08 | `team.md` `## Deployment` (formatos GGUF y `safetensors`) | CTranslate2 (Whisper) y ONNX (Piper) se admiten como formatos de pesos sin código ejecutable; siguen prohibidos `pickle` y `trust_remote_code` | §2.1 | R-06; D1 y D3 de U9 |
| IDS-U2-09 | — | Imágenes de terceros con `runAsUser` fijo: `llama-server` y busybox 65532; Redis 999 con `/data` en su PVC; ninguna escribe fuera de un `emptyDir` en memoria o de su PVC | §2.1, §2.3 | R-07; NFR10.2 |
| IDS-U2-10 | `nfr-design/security-design.md` §7.2 | El Secret `veridicus-redis-auth` lleva dos claves, `requirepass.conf` y `password`. La sonda de vida es `tcpSocket` 6379; la de disponibilidad, `redis-cli ping` con `REDISCLI_AUTH` leído del archivo, nunca como argumento | §2.1 | R-07 |
| IDS-U2-11 | `nfr-requirements/security-requirements.md` NFR2.1 | Interruptor `models.todoLocalJudge.enabled`, activado por defecto, para liberar 24 GiB durante una evaluación de nivel 2 con el verificador en la anfitriona | §2.1, §3, §4 | P6 = A; memoria del equipo |
| IDS-U2-12 | — | Con `port-forward`, todas las peticiones llegan a `session-api` con la IP `127.0.0.1`: el limitador por IP de U3 trata la demostración como un solo cliente. Se acepta para una demostración de una persona | §1 | IDS-U2-04 |
| IDS-U2-13 | `nfr-design/security-design.md` §13 | Se adoptan las propuestas de Infrastructure Design de U10: el proxy pide 1 CPU y 1536 MiB y limita a 2 CPU y 2 GiB; `terminationGracePeriodSeconds: 290`; `create-secrets.sh` termina con error si falta la clave de alguna `api_key_ref` externa de `config/profiles.yaml`; `fetch-models.sh --only ner` para la caché de la CI; `check-config-copy.sh` compara también el SHA-256 del panel | §4, `cicd-pipeline.md` §2 y §8, `monitoring-design.md` §5 | Infrastructure Design de U10 (IDS-U10-02, -03, -06, -07, -08) |
| IDS-U2-14 | `nfr-design/security-design.md` §6 y §7.1 | Se adoptan las peticiones de Infrastructure Design de U3: `Deployment` y `Service` `veridicus-session-api` con el contenedor `session-api` (el Ingress apunta a ese `Service`); `veridicus-auth` y `veridicus-bootstrap-admin` en `secret-consumers.yaml`; `veridicus_app` con `connectionLimit: 25` y sin parámetros de rol; `/tmp` en memoria de 16 MiB en la API | §2.1, §2.4, §4 | Infrastructure Design de U3 (IDS-U3-03 a IDS-U3-05) |
| IDS-U2-15 | `nfr-design/security-design.md` §11 (humo con `/healthz`) | `smoke.sh` comprueba además `/readyz` de los servicios con `kubectl port-forward`, que no cambia el clúster y no está entre los verbos prohibidos de `check-no-cluster-apply.sh` | `cicd-pipeline.md` §4 y §6 | Infrastructure Design de U3 (IDS-U3-06) |

## 11. Riesgos residuales

| Riesgo | Tratamiento |
|---|---|
| Calico no hace cumplir las `NetworkPolicy` sobre el kernel de WSL2 | La verificación manual de security-design §2.4 lo detecta antes de la sustentación; si falla, el respaldo es Ubuntu nativo en una partición (opción D de P7), con el mismo chart |
| Los límites suman 1,7 GiB más que Minikube | Los `requests` caben con 9 GiB de margen; recortes en orden: monitoreo, juez de `todo-local` |
| Windows con 8 GB durante la demostración | Cerrar otras aplicaciones; el navegador de la consola y las diapositivas caben |
| El tamaño exacto del GGUF del juez puede diferir de ≈ 21 GB | Se mide al fijarlo en `models.lock`; si el pico pasa de 22 GiB, el límite sube por PR dentro del margen de los `requests` |
