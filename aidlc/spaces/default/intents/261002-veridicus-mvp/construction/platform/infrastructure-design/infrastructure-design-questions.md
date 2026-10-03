# Preguntas de Infrastructure Design — U2 platform

**Unidad.** U2 `platform` (tipo `packaging`): chart Helm `deploy/veridicus`, `NetworkPolicy`, servidores
de modelos, PostgreSQL con CloudNativePG, Redis, políticas de manifiestos y *scripts* revisables.

**Lo que ya está decidido y no se vuelve a preguntar.** Decisiones D1–D11 de `nfr-requirements/`
(`llama-server` para el juez y los *embeddings*, `faster-whisper`, chart paraguas con `values-cpu.yaml`
y `values-gpu.yaml`, CloudNativePG de 1 instancia con `pgvector`, Redis propio con AOF, modelos
descargados en la anfitriona y verificados por `sha256`, negar todo por defecto); diseño de seguridad
de `nfr-design/` (TLS en el *ingress* con `mkcert`, Kyverno solo como CLI, Pod Security `restricted`);
`## Deployment` de `team.md` (dos máquinas, imágenes en GHCR privado por SHA, Argo CD desde el
módulo 8 y aplicación manual de lo fusionado antes, migraciones como `Job` aparte, Secrets desde un
`.env` con `create-secrets.sh`, prueba de humo tras cada despliegue); tu respuesta 10 de Practices
Discovery (infraestructura mínima; la máquina GPU, de hasta 4 GPU y 32 GB de RAM, solo para lo que de
verdad lo necesite). Los modelos de U4 ya están fijados: juez Qwen2.5-7B Q4_K_M (pico ≤ 7 GiB) y
`multilingual-e5-base` (pico ≤ 1,5 GiB).

Quedan cuatro decisiones de infraestructura.

---

## P1 — Distribución de Kubernetes y CNI en las dos máquinas

El CNI tiene que **hacer cumplir** las `NetworkPolicy`, porque de eso depende que ningún pod con
testimonios salga a internet (NFR1.1, AUTONOMIA-04). Conviene la misma distribución en la máquina de
desarrollo y en la máquina GPU, para que el mismo chart se comporte igual. El PRD (Segmento 13) nombra
Minikube o Kind.

A. Minikube con el *driver* Docker y `--cni=calico` en las dos máquinas, un solo nodo; el complemento
   `ingress` (ingress-nginx) y el almacenamiento `storage-provisioner` (hostPath) que trae Minikube; en
   la máquina GPU, `--gpus all` con NVIDIA Container Toolkit. Calico hace cumplir las `NetworkPolicy`.
   (Recomendada)
B. Kind con el CNI por defecto desactivado y Calico instalado por manifiesto, e ingress-nginx por
   chart. Kind no expone GPU sin ajustes manuales, así que la máquina GPU usaría otra distribución
   (por ejemplo k3s), y el chart tendría dos entornos distintos que probar.
C. k3s instalado directamente en cada máquina (trae su propio controlador de `NetworkPolicy`, Traefik
   como *ingress* y almacenamiento `local-path`); requiere Linux nativo o WSL2 con systemd.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Namespaces

Los diseños aprobados suponen un solo namespace de aplicación llamado `veridicus` (la URL por defecto
de los modelos en C14 es `*.veridicus.svc.cluster.local`, y la política de negar todo y Pod Security
`restricted` se ponen en ese namespace). El PRD (Segmento 13, módulo 6) sugiere separar aplicaciones y
datos en dos namespaces.

A. Un namespace de aplicación `veridicus` (pods de aplicación, PostgreSQL, Redis y servidores de
   modelos) y cada operador de terceros en el suyo: `cnpg-system`, `ingress-nginx` y, en el módulo 8,
   `argocd` y `monitoring`. Coincide con lo ya aprobado y mantiene las reglas de red dentro de un
   namespace. (Recomendada)
B. Dos namespaces de aplicación, como sugiere el PRD: `veridicus-apps` (frontend, `session-api`,
   `semantic-agent`, `audio-worker`) y `veridicus-system` (PostgreSQL, Redis, servidores de modelos),
   más los de los operadores. Las reglas entre ambos usan `namespaceSelector`, y la URL de C14 y el
   diseño de seguridad de U2 quedan en la tabla de precisiones.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Memoria y CPU que la máquina de desarrollo puede darle al clúster

Para fijar los `requests` y `limits` de cada pod en `values-cpu.yaml` (NFR8.1) necesito saber cuánta
memoria y cuántos núcleos tiene la máquina de desarrollo (la de CPU, donde ocurre casi todo el
trabajo). Estimación: lo MUST (juez ≤ 7 GiB, *embeddings* ≤ 1,5 GiB, PostgreSQL, Redis, los servicios,
el *ingress*, Calico y el propio Kubernetes) suma unos 12 GiB; Whisper, Prometheus/Grafana y Argo CD
(SHOULD) suman unos 4 GiB más. La máquina GPU tiene 32 GB.

A. 16 GB de RAM y 8 núcleos o más: Minikube con 12 GiB y 6 CPU. En esta máquina corre lo MUST; el
   monitoreo y Argo CD (SHOULD, módulo 8) se encienden por separado o se ensayan en la máquina GPU.
B. 32 GB de RAM y 8 núcleos o más: Minikube con 20 GiB y 6 a 8 CPU. Todo (MUST y SHOULD) cabe a la vez
   en la máquina de desarrollo.
C. Menos de 16 GB de RAM: el juez de 7B no cabe junto con el resto. El clúster completo correría solo
   en la máquina GPU, o habría que volver a NFR Requirements de U4 para elegir un juez más pequeño.
X. Other (please specify) — indica RAM, núcleos y, si tiene, la GPU de la máquina de desarrollo.

[Answer]: X. Una cifra intermedia, como 24 gb. Puedo poner todo el equipo en partición Ubuntu con Docker para pruebas y demostración **Mode:** guided

## P4 — Respaldo de PostgreSQL

Los datos son sintéticos (NFR12), pero en la base quedan las sesiones, decisiones y reportes
consolidados de la demostración. Ningún requisito exige respaldos; el PRD (Segmento 8) menciona que el
SRE revisa respaldos en un volumen local.

A. Sin respaldo automático en el MVP: el PVC de CloudNativePG usa el almacenamiento local de la
   máquina, y un *script* revisable `scripts/backup-db.sh` hace un `pg_dump` a la anfitriona a pedido
   (solo lectura, con `kubectl exec`), por ejemplo antes de la sustentación. Todo se puede recrear desde
   el escenario y el Golden Dataset. (Recomendada)
B. `ScheduledBackup` diario de CloudNativePG con Barman hacia un MinIO dentro del clúster (un
   componente más, unos 256 MiB y su propio PVC).
C. Instantáneas de volumen (`VolumeSnapshot`) de CloudNativePG con el *driver* CSI hostpath de
   Minikube.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Seguimiento de P3: núcleos y reparto de la memoria

En P3 respondiste que la máquina de desarrollo tiene unos 24 GB y que puedes dedicarla entera a una
partición Ubuntu con Docker para pruebas y demostración. Falta saber cuántos núcleos tiene, porque de
eso dependen los `limits` de CPU del juez (el componente que más CPU usa) y del resto. Con 24 GB
propongo darle a Minikube 18 GiB y dejar 6 GiB al sistema anfitrión; con eso caben lo MUST (~12 GiB)
y lo SHOULD (~4 GiB) a la vez.

A. 8 núcleos (o hilos): Minikube con 18 GiB y 6 CPU; el juez con `limits.cpu` de 4.
B. 12 o más núcleos: Minikube con 18 GiB y 10 CPU; el juez con `limits.cpu` de 6.
C. 4 a 6 núcleos: Minikube con 18 GiB y 4 CPU; el juez con `limits.cpu` de 3, y los turnos tardan más.
X. Other (please specify) — indica núcleos o un reparto de memoria distinto.

[Answer]: B **Mode:** guided
