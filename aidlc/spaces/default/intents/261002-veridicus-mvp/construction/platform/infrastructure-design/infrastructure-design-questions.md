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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Design revisión vigente (2026-11-23)

## Lo que ya está decidido

- **Fuentes aprobadas que esta pasada solo aplica.** El diseño de seguridad de U2, revisión 2
  (`nfr-design/security-design.md`, §1–§16 y NFRD-U2-01 a NFRD-U2-16), con sus decisiones D1–D17 y la red
  de §2.1. Las peticiones de NFR Design de otras unidades dirigidas a U2:
  - puerto 9090 y raspado del proxy (NFRD-U10-09);
  - entrada a la síntesis solo desde `session-api` (NFRD-U9-16);
  - `log_error_verbosity: terse` y ningún manifiesto que baje `retention_max_days` (NFRD-U13-09/10);
  - el plazo de inactividad por transacción con `SET LOCAL`, nunca en `veridicus-pg` (NFRD-U7-01).
- **Respuestas que siguen vigentes.** P1 = A (Minikube con Calico, un nodo), P2 = A (namespace
  `veridicus`) y P4 = A (volcado manual con `backup-db.sh`).
- **Lo que cambia con la información nueva del humano (2026-11-22).**
  - No hay máquina GPU. La evaluación por lotes de modelos locales va a ZINE, con scripts que lanza el
    humano.
  - La demostración corre en el equipo propio: 64 GB de RAM, solo CPU, Windows con WSL2.
  - El contenedor de trabajo ve hoy un Intel Core i7-14700KF (20 núcleos, 28 hilos), pero WSL2 solo le
    entrega 8 procesadores y unos 3,8 GiB de memoria. Hay un límite vigente que habrá que subir.
- **Lo que fijó U11 para esta etapa.**
  - El verificador local es gpt-oss-20b Q8_0 y su servidor usa como mucho 14 GB (NFR2.2 de U11).
  - El juez de `todo-local` es «un Qwen cuantizado que quepa en el clúster». Su archivo y su SHA-256 los
    fija esta etapa (NFR-U11-07).
  - El chart corre completo sin GPU con `todo-local` (NFR2.1 de U2).

## Cómo se registra la revisión

- `infrastructure-specification.md`, `monitoring-design.md` y `cicd-pipeline.md` pasan a la revisión 2. La
  revisión 1 queda en el historial de Git.
- Las secciones conservan su número. Lo que sale queda «Retirado», sin renumerar:
  - la máquina GPU, `values-gpu.yaml` y la política `gpu-only-in-gpu-values`;
  - `veridicus-embeddings`, `pgvector` y el rol `veridicus_judge_ro`.
- Las precisiones nuevas van en una tabla IDS-U2-xx.
- Ningún original aprobado se edita. La tabla propone actualizar, si lo decides en la aprobación, estos
  textos, cada uno en su propio commit:
  - `## Deployment` («Dos máquinas») y `## Testing Posture` («etapa separada del perfil GPU») de `team.md`;
  - la regla aprendida de `project.md` sobre la GPU opcional;
  - NFR2.1 de U2 («Solo `values-gpu.yaml` lo pide»).
- La regla de `project.md` sobre los 28 GiB y 20 GiB se supera con la respuesta a P7 y se registra en el
  ritual de aprendizajes, no a mano.

## Lo que el diseño resolverá sin preguntar

- **Sin GPU.** Sale `values-gpu.yaml`. La política Kyverno `no-gpu-requests` rechaza `nvidia.com/gpu` en
  todo render; su control negativo es un juez que pide GPU.
- **NFR Design revisión 2, tal como está aprobado.** Servidores del juez de `todo-local`, del verificador,
  de Whisper y de Piper. `anonymizer-proxy` con su puerto 9090 raspado. Los tres `Ingress` sin disco de
  §3.2. Los `Job` de `deploy/jobs/` fuera de Argo CD. Argo CD con salida solo a `github.com`. Los
  parámetros de log de `veridicus-pg` y el `SET LOCAL` fuera del `Cluster`.
- **Modelos en WSL2.** `fetch-models.sh` escribe en el sistema de archivos ext4 de la distribución
  (`/srv/veridicus/models`), nunca en `/mnt/c`. Leer por 9p un GGUF de más de 20 GB haría lentísimo cada
  arranque y cada `verify-model`.
- **Consola desde el navegador de Windows.** Con el *driver* Docker, la `minikube ip` no se alcanza desde
  Windows. El runbook pide al humano un `kubectl port-forward` del servicio de ingress-nginx en
  `127.0.0.1:8443`, y WSL2 lo reenvía al `localhost` de Windows. En el archivo `hosts` de Windows,
  `veridicus.local` apunta a `127.0.0.1`, y solo `rootCA.pem` se instala en Windows, nunca la clave
  (security-design §3.1). El comando solo vive en el runbook, no en un *script*.
- **Calico sobre el kernel de WSL2.** La verificación manual de §2.4 decide si las `NetworkPolicy` se
  cumplen de verdad. Si falla, el respaldo es la opción D de P7.
- **Interruptor de memoria.** `models.todoLocalJudge.enabled`, activado por defecto (NFR2.1), permite
  liberar la memoria del juez local mientras corre una evaluación de nivel 2 con el verificador en la
  anfitriona. Cambiarlo es un artefacto revisable que aplica el humano (AUTONOMIA-01).
- **Recrear el nodo.** Cambiar `--memory` o `--cpus` exige `minikube delete`, que borra los PVC. Por eso el
  runbook pone `backup-db.sh` antes de recrearlo.

## P6 — Juez local del perfil `todo-local`

De este modelo depende casi la mitad de la memoria del clúster. El verificador gpt-oss-20b Q8_0 (14 GB)
está fijo, y el juez de ZINE es Qwen3.6-35B-A3B Q8_0 (unos 37 GB, demasiado para el clúster junto al
verificador).

A. **Qwen3.6-35B-A3B en Q4_K_M**: el mismo modelo que se evalúa en ZINE, con una cuantización menor.
   Ocupa unos 21 GB; su límite es de 24 GiB con la ventana de 40 turnos. Es un MoE con unos 3 mil millones
   de parámetros activos por token, así que en CPU genera más rápido que un modelo denso de 8B. La
   demostración muestra el mismo modelo que mide ZINE. El tamaño exacto y el SHA-256 se fijan con el
   archivo en `deploy/models.lock`. (Recomendada)
B. **Un Qwen denso de 7–8B en Q4_K_M** (por ejemplo Qwen3-8B): unos 5 GB, límite de 7 GiB. Libera unos
   17 GiB, pero es otro modelo distinto del evaluado en ZINE, de menor calidad y más lento por token en
   CPU.
C. **Sin juez local en el clúster.** `todo-local` queda solo para ZINE, y la demostración usa
   `comercial-piloto` (juez de Anthropic a través del anonimizador). El clúster cabe en unos 28 GiB, pero
   la demostración saca del clúster texto seudonimizado, y una caída del proveedor la detiene.
X. Other (please specify)

[Answer]: A
«La propuesta original era mantener contenedores hasta máximo 28 GB RAM, porque solo tenía 32 GB; ahora tengo 64, así que puedes ajustar lo que sea necesario para el demo.» (humano, 2026-11-23; delega el ajuste y se aplica la recomendada, que mantiene todo dentro del clúster)

## P7 — Memoria de Minikube, `.wslconfig` y una o dos configuraciones

Presupuesto con P6 = A, en límites de memoria:

| Bloque | Límite |
|---|---|
| Kubernetes, Calico, ingress-nginx, CloudNativePG, metrics-server | ≈ 2,5 GiB |
| PostgreSQL, Redis, `session-api`, `semantic-agent`, `frontend`, `anonymizer-proxy` con su `/tmp` | ≈ 5,5 GiB |
| Verificador gpt-oss-20b Q8_0 | 14 GiB |
| Juez de `todo-local` (P6 = A) | ≈ 24 GiB |
| Voz: Whisper, Piper y `audio-worker` | ≈ 3,3 GiB |
| Monitoreo y Argo CD (módulo 8) | ≈ 2,3 GiB |
| **Total** | **≈ 51,6 GiB** (pedidos ≈ 46 GiB) |

Los límites superan en 1,6 GiB a los 50 GiB de la opción A. Se acepta, como en la revisión 1, por dos
razones: el juez y el verificador nunca generan a la vez (una ranura cada uno, uno tras otro en cada
tramo), y sus pesos van mapeados desde archivo, así que el kernel puede recuperar esa memoria.

A. **Un solo equipo y un solo tamaño.** WSL2 recibe 56 GB, Minikube 50 GiB y Windows conserva 8 GB, que
   bastan para el navegador de la consola y las diapositivas si se cierran otras aplicaciones durante la
   demostración. Los 6 GB restantes de WSL2 son para Docker, el contenedor de trabajo y los contenedores
   de nivel 1. Desarrollo y demostración usan el mismo clúster, sin recrearlo. (Recomendada con P6 = A)
   En `C:\Users\<usuario>\.wslconfig` (se aplica con `wsl --shutdown`):

   ```ini
   [wsl2]
   memory=56GB
   processors=20
   swap=8GB
   localhostForwarding=true
   ```

   Y en `scripts/cluster-up.sh`: `--memory=50g --cpus=16` (los núcleos, según P8).
B. **Un solo tamaño más pequeño** (lo que corresponde a P6 = B): WSL2 con 44 GB, Minikube 36 GiB y
   Windows 20 GB.
C. **Dos tamaños**: «desarrollo» con 36 GiB, sin el juez local ni el monitoreo, y «demostración» con
   50 GiB completo. En un solo equipo, pasar de uno a otro exige `minikube delete`, que borra los PVC. Es
   más ceremonia sin ganar nada, porque el equipo es el mismo.
D. **Ubuntu nativo en una partición, sin WSL2** (lo que permitía tu respuesta P3): Minikube con 54 GiB,
   sin `.wslconfig` ni `port-forward`, y Calico sobre un kernel completo. A cambio, hay que cambiar de
   entorno a días de la demostración.
X. Other (please specify)

[Answer]: A
«La propuesta original era mantener contenedores hasta máximo 28 GB RAM, porque solo tenía 32 GB; ahora tengo 64, así que puedes ajustar lo que sea necesario para el demo.» (humano, 2026-11-23)

## P8 — Núcleos para WSL2, Minikube y los modelos

El i7-14700KF tiene 8 núcleos de rendimiento y 12 de eficiencia. `llama-server` rinde mejor con tantos
hilos como núcleos de rendimiento; si se le dan más, los núcleos de eficiencia frenan la sincronización
entre hilos.

A. **Es este mismo equipo.** `processors=20` en `.wslconfig` (Windows conserva 8 hilos),
   `--cpus=16` en Minikube y `--threads 8` con `limits.cpu` de 8 en el juez y el verificador; como
   alternan, no compiten. (Recomendada)
B. Este mismo equipo, más agresivo: `processors=24`, `--cpus=20` y `--threads 12`. Windows se queda con 4
   hilos (la consola y la proyección pueden ir a tirones), y los hilos de más caen en núcleos de
   eficiencia sin ganar velocidad.
C. **Es otro equipo**, de 12 a 16 hilos: `processors` igual a los hilos menos 2, `--cpus` igual a los
   hilos menos 4 y `--threads 6`. Los tramos tardan más y la evaluación de 6 h de NFR2.2 de U11 queda en
   riesgo.
X. Other (please specify): indica el procesador y el número de hilos.

[Answer]: A
«La propuesta original era mantener contenedores hasta máximo 28 GB RAM, porque solo tenía 32 GB; ahora tengo 64, así que puedes ajustar lo que sea necesario para el demo.» (humano, 2026-11-23; el contenedor de trabajo corre en ese mismo equipo, un i7-14700KF)
