# Especificación de infraestructura — U2 platform

**Insumos.** Diseño de seguridad de `nfr-design/security-design.md` (security-design: zonas, red,
TLS, imágenes, endurecimiento, Secrets, datos persistentes, dónde se aplican las políticas);
decisiones D1–D11, estructura de `deploy/` y dependencias de red de
`nfr-requirements/tech-stack-decisions.md`; requisitos NFR1.1–NFR15.1 de
`nfr-requirements/security-requirements.md`; dependencias externas y frontera del clúster de
`inception/domain-design/components.md` (components); C9, C14, C15 y C16 y la tabla «Datos sensibles
por contrato» de `inception/contract-design/contract-summary.md` (contract-summary); picos de memoria
del juez y de *embeddings* de U4 (`text-flow/nfr-requirements`); entregas a Infrastructure Design de U3
(`identity-access/nfr-design/logical-components.md`); respuestas P1–P5 de
`infrastructure-design-questions.md`; `## Deployment` de `team.md` y prohibiciones de `project.md`.

U2 es `packaging`: este documento fija **dónde y con qué** corre todo el sistema. El chart y los
*scripts* se escriben en Code Generation; aquí solo se decide su forma y sus valores.

## 1. Despliegue

| Faceta | Elección | Razón |
|---|---|---|
| Distribución de Kubernetes | **Minikube** con el *driver* Docker, un solo nodo, Kubernetes **v1.31** fijado en `scripts/cluster-up.sh` y en los esquemas de `kubeconform`, en las dos máquinas (P1 = A) | El PRD (S13) nombra Minikube; el mismo chart se prueba igual en ambas máquinas; el *driver* Docker monta el volumen de modelos sin 9p |
| CNI | **Calico** (`--cni=calico`), *pod CIDR* `10.244.0.0/16` | Hace cumplir `NetworkPolicy` (NFR1.1, AUTONOMIA-04); permite las sondas del kubelet desde el nodo |
| Máquina de desarrollo | Ubuntu nativo con Docker, 24 GB de RAM y 12 o más núcleos; Minikube con **18 GiB y 10 CPU**, 6 GiB quedan para el sistema (P3, P5 = B) | Caben a la vez lo MUST y lo SHOULD (§4) |
| Máquina GPU (opcional) | Misma distribución con `--gpus all` y NVIDIA Container Toolkit; Minikube con 26 GiB y las CPU disponibles; solo para la etapa del perfil GPU y el ensayo de la demo | Respuesta 10 de Practices Discovery; NFR2.1 |
| Namespaces | `veridicus` para toda la aplicación, la base, Redis y los modelos; operadores en `cnpg-system`, `ingress-nginx` y, en el módulo 8, `argocd` y `monitoring` (P2 = A) | Coincide con C14 (`*.veridicus.svc.cluster.local`) y con la política de negar todo de security-design §2 |
| Pod Security | `veridicus` con `enforce: restricted` y `warn: restricted` | security-design §5 (NFR10.2) |
| Entrada (*ingress*) | Complemento `ingress` de Minikube (ingress-nginx) con un único `Ingress` para `veridicus.local`: `/` → `frontend:8080`, `/api/` → `session-api:8080`; TLS con el Secret `veridicus-ingress-tls` de `mkcert`, redirección a HTTPS y HSTS | security-design §3 (cookie `Secure` de U3) |
| Nombre de la consola | `veridicus.local` en `/etc/hosts` de la máquina de la demostración, apuntando a `minikube ip` | Sin DNS público ni salida a internet |
| Salida de red | Negada por defecto en `veridicus` (subchart `network-policies`); reglas por dependencia en §3 | NFR1.1 |
| Almacenamiento | `storage-provisioner` de Minikube (`StorageClass` `standard`, hostPath dentro del nodo) para los PVC de PostgreSQL, Redis, reportes y Prometheus; los modelos en un `PersistentVolume` estático de solo lectura (§2.3) | Sin otro componente; los datos sobreviven a `minikube stop` (no a `minikube delete`, ver §6) |
| Imágenes | Propias en GHCR privado, etiqueta con el SHA y uso por digest; el nodo las descarga con el Secret `ghcr-pull` (token de solo lectura de paquetes) referenciado en cada pod | `## Deployment` de team.md; NFR10.1 |
| IaC | Chart paraguas `deploy/veridicus` con `values-cpu.yaml` (por defecto) y `values-gpu.yaml`; operadores con chart oficial y versión exacta; `scripts/cluster-up.sh` solo crea el clúster local; la instalación de operadores y del chart la ejecuta el humano siguiendo `docs/operacion/instalacion.md` | AUTONOMIA-01: ningún *script* aplica manifiestos (security-design §9) |
| Clasificación de datos | Etiqueta `veridicus.io/data-class: sensitive` en los pods que manejan testimonio, audio o CoT (`session-api`, `semantic-agent`, `audio-worker`, PostgreSQL, Redis, `model-*`); `internal` en `frontend` y en los `Job` | Frontera de components; la política `deny-external-egress` aplica a todos igual |

`scripts/cluster-up.sh` (revisable, lo ejecuta el humano):

```bash
minikube start --driver=docker --kubernetes-version=v1.31.4 \
  --cni=calico --cpus=10 --memory=18g --disk-size=80g \
  --mount --mount-string="/srv/veridicus/models:/models"
minikube addons enable ingress
minikube addons enable metrics-server
```

## 2. Servicios de infraestructura

### 2.1 Servicios

| Servicio | Rol | Configuración | Notas |
|---|---|---|---|
| `veridicus-pg` (CloudNativePG) | database | `Cluster` de 1 instancia, imagen de CloudNativePG con PostgreSQL 16 y `pgvector`, por digest; PVC de 10 GiB en `standard`; `max_connections = 50`, `shared_buffers = 256MB`; `enableSuperuserAccess: false`; TLS del operador | `postInitApplicationSQL` crea la extensión `vector` una sola vez al iniciar el clúster (necesita superusuario y no corre en ejecución) |
| Roles de PostgreSQL | database | `veridicus_owner` (dueño del esquema; solo lo usa `migrations-job`), `veridicus_app` (DML concedido por las migraciones; `session-api`, `create-admin-job`), `veridicus_judge_ro` (solo `SELECT` de C9; `semantic-agent`), declarados en `managed.roles` con Secret de contraseña | Separar dueño y aplicación hace efectivo el `REVOKE UPDATE, DELETE` de las tablas de historial (NFR11 de U3) |
| `veridicus-redis` | queue | `StatefulSet` de 1 réplica, Redis **7.2** por digest (≥ 7.0 para `EXPIRE NX` de U3, última versión con licencia BSD), AOF `appendfsync everysec` en PVC de 2 GiB, `maxmemory 384mb` con `noeviction`, `requirepass` desde Secret, `protected-mode yes`, comandos peligrosos renombrados | `noeviction`: una cola llena responde error en vez de perder turnos |
| `veridicus-judge` | other (modelo) | `llama-server` por digest con Qwen2.5-7B-Instruct Q4_K_M, `--ctx-size 12288`, `--parallel 1`, `--threads 6`, `--metrics`, `--api-key` desde Secret; puerto 8080 | Una sola ranura para resultados repetibles (U4) |
| `veridicus-embeddings` | other (modelo) | `llama-server --embedding --pooling mean` con `multilingual-e5-base` f16; `--threads 2`; puerto 8080 | Lo usan `session-api` (indexación) y `semantic-agent` |
| `veridicus-whisper` (SHOULD) | other (modelo) | `faster-whisper` con API compatible con OpenAI, modelo `base` en int8, CPU; puerto 8080 | El servidor de TTS lo elige U9 |
| `ingress-nginx` | load-balancer | Complemento de Minikube; `ssl-redirect`, HSTS, `proxy-read-timeout 30s`, `proxy-body-size` igual al mayor tamaño de C1 del catálogo de límites de U1 | Termina TLS; no guarda en caché |
| CoreDNS | dns | El del clúster | Única salida permitida a todos los pods (53 UDP/TCP) |
| Volumen de reportes | object-store | PVC de 2 GiB `ReadWriteOnce` montado solo en `session-api` (ForensicReport de components) | Lo dimensiona U7; aquí se reserva |
| `cdn`, `search` | — | No aplica | Todo es local; la búsqueda vectorial vive en PostgreSQL |

### 2.2 Direcciones internas

| Variable | Valor en `values-cpu.yaml` y `values-gpu.yaml` |
|---|---|
| Base de lectura y escritura | `veridicus-pg-rw.veridicus.svc.cluster.local:5432`, `sslmode=verify-full` con la CA `veridicus-pg-ca` |
| Redis | `veridicus-redis.veridicus.svc.cluster.local:6379` |
| `VERIDICUS_JUDGE_URL` | `http://veridicus-judge.veridicus.svc.cluster.local:8080` |
| `VERIDICUS_EMBEDDINGS_URL` | `http://veridicus-embeddings.veridicus.svc.cluster.local:8080` |
| `VERIDICUS_WHISPER_URL` | `http://veridicus-whisper.veridicus.svc.cluster.local:8080` |

La política `internal-model-urls` rechaza cualquier valor que no termine en `.svc.cluster.local`
(NFR1.3).

### 2.3 Archivos de modelo

| Paso | Diseño |
|---|---|
| Descarga | `scripts/fetch-models.sh` en la anfitriona escribe en `/srv/veridicus/models` y verifica cada archivo contra `deploy/models.lock` (URL, revisión, `sha256`) |
| Montaje en el nodo | `--mount-string` de `cluster-up.sh` expone esa carpeta como `/models` dentro del nodo de Minikube |
| Montaje en los pods | Un `PersistentVolume` estático `veridicus-models` (hostPath `/models`, `ReadOnlyMany`) y su PVC; los pods lo montan con `readOnly: true`. Pod Security `restricted` prohíbe volúmenes `hostPath` en el pod, pero sí admite un PVC |
| Verificación al arrancar | `initContainer` `verify-model` (busybox por digest) ejecuta `sha256sum -c` con el valor de `models.lock`; si no coincide, el servidor no arranca (NFR10.4) |

## 3. Red permitida (NFR1.1, NFR10.6–NFR10.8)

| Origen | Destino | Puerto | Política |
|---|---|---|---|
| Todos los pods de `veridicus` | CoreDNS (`kube-system`) | 53 UDP/TCP | `allow-dns` |
| Namespace `ingress-nginx` | `frontend`, `session-api` | 8080 | `allow-ingress-controller` |
| `session-api` | `veridicus-pg`, `veridicus-redis`, `veridicus-embeddings` | 5432, 6379, 8080 | Por pod |
| `semantic-agent` | `veridicus-pg` (rol `veridicus_judge_ro`), `veridicus-redis`, `veridicus-judge`, `veridicus-embeddings` | 5432, 6379, 8080 | Por pod |
| `audio-worker` (SHOULD) | `veridicus-redis`, `veridicus-whisper` | 6379, 8080 | Por pod |
| `migrations-job`, `create-admin-job` | `veridicus-pg` | 5432 | Por pod |
| Operador `cnpg-system` | Pods de `veridicus-pg` | 8000, 5432 | `allow-cnpg-operator` |
| Namespace `monitoring` (módulo 8) | Puerto `metrics` de cada servicio, `veridicus-pg` (9187) y `--metrics` de `llama-server` | 8081, 9187, 8080 | `allow-prometheus` |
| `anonymizer-proxy` (COULD) | Su destino externo declarado | 443 | Única regla con `ipBlock` |

Las descargas de imágenes las hace el *runtime* del nodo, no los pods, así que la política de negar
todo no las afecta. Argo CD (módulo 8) vive en `argocd`, fuera de esa política, y solo lee el
repositorio con su *deploy key*.

## 4. Recursos por contenedor (`values-cpu.yaml`, NFR8.1)

| Contenedor | `requests` CPU / memoria | `limits` CPU / memoria | Origen del valor |
|---|---|---|---|
| `veridicus-judge` | 4 / 6 GiB | 6 / 7,5 GiB | Pico ≤ 7 GiB de U4 con la ventana llena; 6 hilos |
| `veridicus-embeddings` | 1 / 1 GiB | 2 / 1,5 GiB | Pico ≤ 1,5 GiB de U4 |
| `veridicus-whisper` (SHOULD) | 1 / 1 GiB | 2 / 1,5 GiB | Modelo `base` int8 |
| `veridicus-pg` | 0,5 / 1 GiB | 1 / 1,5 GiB | `shared_buffers` 256 MB y 50 conexiones |
| `veridicus-redis` | 0,1 / 256 MiB | 0,5 / 512 MiB | `maxmemory` 384 MB más margen de AOF |
| `session-api` | 0,5 / 384 MiB | 2 / 768 MiB | Base del proceso más ≥ 160 MiB de Argon2id (U3); U4–U7 lo revisan en su diseño |
| `semantic-agent` | 0,25 / 256 MiB | 1 / 512 MiB | Lo afina U4 |
| `audio-worker` (SHOULD) | 0,25 / 256 MiB | 1 / 512 MiB | Lo afina U9 |
| `frontend` | 0,05 / 32 MiB | 0,2 / 64 MiB | Archivos estáticos |
| `migrations-job`, `create-admin-job` | 0,1 / 128 MiB | 0,5 / 256 MiB | `create-admin` calcula un Argon2id de 64 MiB |
| `verify-model` (`initContainer`) | 0,2 / 64 MiB | 1 / 128 MiB | `sha256sum` en flujo |

| Presupuesto de Minikube (18 GiB, 10 CPU) | Memoria pedida | Memoria límite |
|---|---|---|
| Aplicación y datos MUST | ≈ 8,9 GiB | ≈ 12,3 GiB |
| Kubernetes, Calico, ingress-nginx, CloudNativePG, metrics-server | ≈ 2 GiB | ≈ 2,5 GiB |
| SHOULD: Whisper y `audio-worker` | ≈ 1,3 GiB | 2 GiB |
| SHOULD (módulo 8): `kube-prometheus-stack` mínimo y Argo CD sin Dex ni notificaciones | ≈ 1,5 GiB | ≈ 2,3 GiB |
| **Total** | **≈ 13,7 GiB** | ≈ 19,1 GiB |

La suma de los `requests` cabe en 18 GiB; la de los `limits` la supera en ≈ 1 GiB porque no todos
llegan a su pico a la vez (el juez es el único que se acerca al suyo). Si la prueba de carga de NFR8
muestra presión de memoria, el primer recorte es apagar el monitoreo durante esa corrida.

`values-gpu.yaml` cambia solo lo que la GPU necesita: `veridicus-judge` pide `nvidia.com/gpu: 1` y
`--n-gpu-layers 999`; la política `gpu-only-in-gpu-values` impide que esa petición aparezca en
`values-cpu.yaml` (NFR2.1).

## 5. Estrategia de actualización por componente

| Componente | Estrategia | Razón |
|---|---|---|
| `model-*` | `Recreate` | Dos réplicas del juez a la vez no caben en memoria |
| `session-api`, `semantic-agent`, `audio-worker`, `frontend` | `RollingUpdate`, `maxSurge: 1`, `maxUnavailable: 0` | Sin corte; las migraciones son *expand–contract* |
| `veridicus-redis` | `StatefulSet` `OnDelete` | Solo se reinicia a propósito |
| `veridicus-pg` | La gestiona CloudNativePG | Actualizaciones solo por cambio de imagen en un PR propio |
| `migrations-job` | `Job` con nombre que incluye la revisión de migraciones; corre antes de las aplicaciones (onda −1 en Argo CD) | Prohibición de `project.md`; un `Job` es inmutable |

## 6. Respaldo y recuperación (P4 = A)

| Situación | Qué se hace |
|---|---|
| Antes de la sustentación o de un cambio de esquema | El humano ejecuta `scripts/backup-db.sh`: `pg_dump -Fc` dentro del pod de la base (con `kubectl exec`, solo lectura) hacia `backups/veridicus-<fecha>.dump` en la anfitriona; `backups/` está en `.gitignore` |
| Restaurar | Paso manual del humano en `docs/operacion/instalacion.md` (`pg_restore` sobre una base nueva); ningún *script* lo hace |
| `minikube delete` | Borra los PVC: se recrea el clúster, se restaura el último volcado o se vuelven a cargar el escenario y el Golden Dataset sintéticos |
| Redis pierde datos | Los turnos en curso quedan en error y se reintentan a mano (contrato C2/C3) |

## 7. Infraestructura compartida

| Recurso compartido | Unidad dueña | Unidades que lo usan | Frontera de acceso |
|---|---|---|---|
| `veridicus-pg` y sus roles | U2 (despliegue), `session-api` (esquema, por migraciones) | U3–U7 por `veridicus_app`; U4 y U8 por `veridicus_judge_ro` | Rol por proceso; `NetworkPolicy` de entrada al 5432 solo desde sus clientes |
| `veridicus-redis` | U2 | U3 (limitador `veridicus:auth:`), U4 y U8 (C2–C4), U9 (C5) | Contraseña única; prefijos de clave por unidad; entrada solo desde sus tres clientes |
| `veridicus-judge`, `veridicus-embeddings` | U2 | U4, U8 (juez); U4 (*embeddings* en `session-api` y `semantic-agent`) | `--api-key` y `NetworkPolicy` por cliente |
| `veridicus-whisper` y TTS | U2 (despliegue), U9 (elección del TTS) | U9 | Solo `audio-worker` |
| `Ingress` y TLS | U2 | U3 (cookie `Secure`), todas las pantallas | Solo `/` y `/api/` |
| Volumen de modelos | U2 | `model-*` | Solo lectura |
| Prometheus y Grafana (SHOULD) | U2 | U3, U4, U5 (C15) | Solo los puertos `metrics` |

## 8. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `platform/nfr-design/security-design.md` §6 | Se añade el Secret `ghcr-pull` (token de solo lectura de paquetes de GHCR) a los Secrets que crea `create-secrets.sh` | Imágenes privadas en GHCR (team.md) |
| `platform/nfr-design/security-design.md` §7 y `nfr-requirements/tech-stack-decisions.md` D5 | Un tercer rol `veridicus_owner` dueño del esquema, usado solo por `migrations-job` | Hacer efectivo el `REVOKE` de las tablas de historial |
| `platform/nfr-requirements/tech-stack-decisions.md` D6 | Redis fijado en 7.2 (≥ 7.0 para `EXPIRE NX`) | Hallazgo R-03 de NFR Design de U3 |
| `platform/nfr-requirements/tech-stack-decisions.md` §2 | Se añaden `scripts/cluster-up.sh`, `scripts/backup-db.sh`, `docs/operacion/instalacion.md` y el `PersistentVolume` estático de modelos | P1, P4 y Pod Security `restricted` |
