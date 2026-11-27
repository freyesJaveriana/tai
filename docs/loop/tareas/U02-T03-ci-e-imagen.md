# U02-T03: la CI de deploy y la imagen publicada en GHCR

**Unidad:** U2 `platform`   **Bolt:** B4-demo   **Rama base:** `bolt/b4-demo`, después de fusionar U02-T02 (#61)
**Pasos del plan que cubre:** los pasos 8 y 9 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/platform/code-generation/code-generation-plan.md` (aprobado el 2026-11-26), con DP-07 y DP-08. Además cierra las candidatas K-97, K-102, K-103 y K-104 de `docs/loop/CANDIDATAS.md`.
**Depende de:** U02-T01 (Dockerfile, punto de entrada y `test_dockerfile.py`) y U02-T02 (manifiestos, políticas de Kyverno y scripts del humano).
**Riesgo (ML-4):** bajo en el plan, pero sube a **medio** porque esta tarea crea el único job con `packages: write` y toca dos scripts del humano (K-104). La revisión la hace `revisor` con `opus`.

---

## Alcance

**Entra:**

> - **Paso 8, `.github/workflows/deploy-level0.yml`.** Se dispara en `pull_request` y en `push` a `main`, sin filtro de rutas (como `analyzer-level0.yml`, para que pueda ser una comprobación obligatoria). Lleva:
>   - `permissions: contents: read` en el nivel del workflow, `concurrency` y `timeout-minutes` en cada job;
>   - **solo** las dos acciones que ya usa el repositorio, con el mismo SHA: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (con `persist-credentials: false`) y `astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78` (uv `0.13.9`). **Ninguna acción nueva**, porque el repositorio tiene una lista de acciones permitidas. Las herramientas se descargan con `curl` y se verifican con `sha256sum -c` antes de usarlas;
>   - las pruebas de `deploy/` con `uv sync --frozen`, `uv lock --check`, `ruff check`, `ruff format --check`, `mypy --strict src tests` y `pytest` con `--cov=veridicus_demo --cov-branch --cov-fail-under=100`, con los pasos sin red en `--frozen --offline`;
>   - `kustomize build deploy/demo-analyzer`, que escribe el render en un archivo del job;
>   - `kubeconform -strict -summary -kubernetes-version 1.31.0` sobre el render. Los esquemas se descargan en el job desde la ubicación por defecto de kubeconform, fijada por la versión de Kubernetes. Si sabes fijarlos también por suma, mejor, pero no es obligatorio: decláralo en la bitácora;
>   - `kyverno test deploy/policies` (debe descubrir también `veridicus-secret-solo-job/otro-usuario/`; si no lo hace, añade un paso aparte para esa carpeta y anótalo);
>   - `kyverno apply` de las cuatro políticas sobre el render de `kustomize build`, que debe dar 0 fallos;
>   - `hadolint deploy/images/analyzer-cli/Dockerfile` con código 0;
>   - `shellcheck` sobre los scripts de shell del repositorio que elijas (como mínimo los de `scripts/humano/` y `scripts/check-no-*.sh`). **Cuidado con DP-08:** la guardia de AUTONOMIA-01 falla si un workflow **menciona** `scripts/humano/`. No la aflojes: lista los scripts sin escribir esa ruta en el workflow (por ejemplo, `git ls-files` con un patrón `*.sh` o un `find` sobre `scripts`);
>   - **controles negativos dentro de la CI**, que deben fallar y cuyo fallo se invierte para que el job pase: `kubeconform` sobre un manifiesto roto de `deploy/tests/fixtures/` y `kyverno apply` sobre un recurso de fallo de cada política. Así el rojo queda probado en cada corrida y no solo una vez.
> - **Versiones y sumas fijadas** (las sacó el orquestador de la API de GitHub, campo `digest` de cada asset de la release, el 2026-11-27; tú no tienes red):
>
>   | Herramienta | Versión | Asset | SHA-256 |
>   |---|---|---|---|
>   | kustomize | v5.8.3 | `kustomize_v5.8.3_linux_amd64.tar.gz` (release `kustomize/v5.8.3` de `kubernetes-sigs/kustomize`) | `cb9e31198d3f63b44848bd0afc4c8efc56e6cfef9c93a4a39a211940e6decd61` |
>   | kubeconform | v0.8.0 | `kubeconform-linux-amd64.tar.gz` (`yannh/kubeconform`) | `9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883` |
>   | Kyverno CLI | v1.20.0 | `kyverno-cli_v1.20.0_linux_x86_64.tar.gz` (`kyverno/kyverno`) | `06b8f3ca7b5626473be8fb4d343ad54ab84e317142766f72420e7d44b80942e2` |
>   | hadolint | v2.15.1 | `hadolint-linux-x86_64` (`hadolint/hadolint`) | `c7187db94eeeeca956519a6af171adc31453941a1e777961f6e680f697c8c507` |
>   | shellcheck | v0.11.0 | `shellcheck-v0.11.0.linux.x86_64.tar.xz` (`koalaman/shellcheck`) | `8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198` |
>   | Trivy | v0.76.2 | `trivy_0.76.2_Linux-64bit.tar.gz` (`aquasecurity/trivy`) | `bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf` |
>
>   Las URL son las de descarga de releases de GitHub (`https://github.com/<dueño>/<repo>/releases/download/<etiqueta>/<asset>`). La etiqueta de kustomize lleva barra (`kustomize/v5.8.3`), así que en la URL va codificada como `kustomize%2Fv5.8.3`.
> - **Paso 9, `.github/workflows/analyzer-image.yml`.**
>   - En `pull_request` que toca `libs/**`, `contracts/**`, `deploy/images/**` o el propio workflow: construye la imagen con `docker build` (contexto y `-f` como los dejó U02-T01) y la escanea con Trivy, **sin publicar** y sin `packages: write`.
>   - En `push` a `main` con esas mismas rutas: construye, escanea y, solo si Trivy pasa, publica en `ghcr.io/freyesjaveriana/veridicus-analyzer-cli` con la etiqueta del SHA completo del commit (`${{ github.sha }}`), nunca `latest`. El login va con `docker login ghcr.io --password-stdin` y el `GITHUB_TOKEN`, sin acciones nuevas.
>   - Trivy: `--severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`. Las excepciones solo en un `.trivyignore` versionado con motivo y fecha de caducidad (hoy no hace falta ninguna).
>   - `permissions: contents: read` en el workflow; `packages: write` **solo** en el job que publica, y ese job solo corre en `push` a `main`.
>   - El digest publicado (`docker inspect --format` con `RepoDigests`, o `docker push` y su salida) se escribe en `$GITHUB_STEP_SUMMARY`.
> - **Prueba de nivel 0 de los workflows**, `deploy/tests/test_workflows.py` (PyYAML), que falla si:
>   - un workflow nuevo no declara `permissions: contents: read` en su nivel superior;
>   - `packages: write` aparece en un job que puede correr en `pull_request`, o en más de un job;
>   - una acción no está fijada por un SHA de 40 hex, o no es una de las dos permitidas;
>   - una herramienta descargada con `curl` no se verifica con `sha256sum -c` antes de ejecutarse, o su suma no es una de las de la tabla;
>   - aparece `kubeconfig`, `KUBECONFIG`, `kubectl` o `latest` como etiqueta de imagen;
>   - un workflow menciona `scripts/humano/` (ya lo cubre AUTONOMIA-01; aquí basta con que la suite de AUTONOMIA-01 pase sobre los dos workflows nuevos).
>
>   Con un control negativo por regla (*fixtures* en `deploy/tests/fixtures/workflows/`).
> - **K-97.** `check_copy_from_pinned` en `deploy/tests/test_dockerfile.py` compara la clave `from=` sin distinguir mayúsculas y quita las comillas de cada campo de `--mount` (al estilo CSV). Controles negativos: `RUN --mount=type=cache,FROM=img:latest` y `RUN --mount="type=bind,from=img"` sin digest deben fallar.
> - **K-102.** La CI corre las mismas reglas de `test_manifests.py` sobre el render real de `kustomize build`, no solo sobre la lectura de primer nivel. Por ejemplo: `test_manifests.py` lee el render de un archivo cuya ruta llega por una variable de entorno (`VERIDICUS_RENDER`) y, si no está, renderiza como hoy. El paso de la CI pasa la ruta del render. En local, sin la variable, todo sigue igual.
> - **K-103.** `PINNED` de `humano_checks.py` rechaza `:latest@sha256:…`, igual que los manifiestos y Kyverno. Control negativo con `curlimages/curl:latest@sha256:<64 hex>`.
> - **K-104.** En `scripts/humano/crear-secret-anthropic.sh` y `crear-pull-secret-ghcr.sh`, la comprobación de la anotación `kubectl.kubernetes.io/last-applied-configuration` deja de usar `| grep -q .`. Usa `-o go-template` con `index .metadata.annotations "kubectl.kubernetes.io/last-applied-configuration"` que imprime un literal fijo (por ejemplo `si`) y compara su salida con ese literal. El valor de la anotación nunca pasa por un pipe ni por una variable. Se conserva el `exit 2` con el mensaje de `kubectl delete secret … --namespace …`. `test_scripts_humano.py` exige la forma nueva y falla con la vieja (control negativo).

**Fuera** (rechazar aunque se vea roto):

- La guía `deploy/demo-analyzer/README.md` y la fijación del SHA en `kustomization.yaml` son de U02-T04.
- K-99, K-100 y K-101 siguen como candidatas.
- No se toca `libs/` ni `contracts/`.
- **No se ejecuta ningún script de `scripts/humano/`, ni `kubectl`, `minikube`, `docker`, `kustomize`, `kubeconform`, `kyverno`, `hadolint`, `shellcheck` ni `trivy`.** No están en el contenedor y no tienes red; la CI es la que los corre.
- No se cambian ajustes de GitHub (protección de ramas, comprobaciones obligatorias, permisos de paquetes). Si algo hace falta, anótalo en la bitácora para el humano.

---

## Archivos de contexto

- Del plan aprobado: los pasos 8 y 9, DP-07, DP-08, R-B4d-1 y el mapa AUTONOMIA.
- `.github/workflows/analyzer-level0.yml` y `repo-level0.yml`: estilo, SHA de las acciones, separación de pasos con red y sin red, comentarios en español.
- `docs/loop/bitacoras/U02-T01.md` y `U02-T02.md`: cómo se construye la imagen y cómo están hechas las pruebas de `deploy/`.
- `docs/loop/revisiones/U02-T02/ronda-3.md`: F-15, F-16 y F-17 (K-102 a K-104).
- `docs/loop/CANDIDATAS.md`: K-97 y K-102 a K-104.

---

## Criterios de aceptación

Se corren desde la raíz del worktree `/workspace/.worktrees/U02-T03`.

- [ ] **CA-1 (pasos 8 y 9):** la prueba de los workflows.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_workflows.py -q
  ```
  Se espera: código 0, con un control negativo por regla que falla dentro de su prueba.
- [ ] **CA-2 (DP-08):** AUTONOMIA-01 sigue pasando con los dos workflows nuevos.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_autonomia_01.py tests/test_check_no_cluster_apply.py -q
  ```
- [ ] **CA-3 (K-97, K-102, K-103, K-104):**
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_dockerfile.py tests/test_manifests.py tests/test_scripts_humano.py -q
  ```
  ```bash
  bash -n /workspace/.worktrees/U02-T03/scripts/humano/crear-secret-anthropic.sh
  ```
  Se espera: código 0. El `bash -n` se repite con `crear-pull-secret-ghcr.sh`.
- [ ] **CA-4:** nada retrocede.
  ```bash
  uv run --frozen --offline --directory deploy pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q
  ```
  ```bash
  uv run --frozen --offline --directory deploy mypy --strict src tests
  ```
  ```bash
  uv run --frozen --offline --directory deploy ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory deploy ruff format --check .
  ```
  Además, los cuatro `scripts/check-no-*.sh` sobre el worktree dan `0 apariciones`, y `git -C /workspace/.worktrees/U02-T03 diff --stat origin/bolt/b4-demo -- libs contracts` sale vacío.
- [ ] **CA-5 (en la CI, lo verifica el orquestador después del push):** en el PR contra `bolt/b4-demo`, `deploy-level0` queda en verde con sus controles negativos invertidos, y `analyzer-image` construye y escanea sin publicar. El orquestador sube un commit de prueba que rompe un manifiesto, comprueba el rojo, lo revierte y guarda el enlace en la bitácora. Tú dejas preparado en la bitácora qué cambio de una línea usar para ese rojo.

---

## Casos sonda obligatorios (ML-11)

1. **Permiso de más:** `packages: write` en el nivel del workflow, o en un job que corre en `pull_request`, debe fallar CA-1.
2. **Acción sin fijar:** `uses: actions/checkout@v4` y una acción nueva con SHA de 40 hex que no está en la lista deben fallar.
3. **Herramienta sin verificar:** un `curl … | tar x` sin `sha256sum -c`, o con una suma distinta de la de la tabla, debe fallar.
4. **Credenciales del clúster:** un paso con `KUBECONFIG` o `kubectl` debe fallar.
5. **Imagen `latest`:** un `docker push …:latest` debe fallar.
6. **K-104 viejo:** el script con `| grep -q .` sobre la anotación debe fallar `test_scripts_humano.py`.

---

## Plan de pruebas (Testing Contract: custom)

1. **Primero, en rojo:** `test_workflows.py`, los controles nuevos de K-97, K-102, K-103 y K-104, y todos los casos sonda. Haz un commit del rojo con el mensaje `test(deploy): rojo de los workflows de deploy y de K-97, K-102 a K-104` y anota su SHA en la bitácora.
2. Después escribe los dos workflows y los arreglos hasta llegar al verde.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** la CI no despliega: sin `kubeconfig`, sin `kubectl` y sin invocar `scripts/humano/` (CA-1 y CA-2).
- **team.md, Deployment:** imágenes etiquetadas con el SHA y nunca `latest`; Trivy bloquea `HIGH`/`CRITICAL` con corrección; solo el job de *build* tiene `packages: write`; acciones fijadas por SHA; `permissions: contents: read` por defecto.
- **Solo datos sintéticos.** Ningún secreto en el repositorio: el único token es el `GITHUB_TOKEN` del job que publica.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U02-T03.md`, de una página como máximo. Lleva el SHA del rojo, la tabla de los pasos 8 y 9 y de K-97, K-102 a K-104 con su prueba (ML-14), lo que no pudiste verificar sin red (sintaxis de Kyverno 1.20, que `kyverno test` descubra la subcarpeta, las opciones exactas de cada herramienta) y el cambio de una línea para el rojo de CA-5.
- **Orden de publicación:** el plan publica la imagen en `push` a `main`. La imagen existirá cuando el Bolt se fusione en `main`; U02-T04 fija después el SHA. No añadas otro disparador de publicación (por ejemplo, la rama del Bolt) sin anotarlo como propuesta en la bitácora.
- **Bash:**
  - un comando simple por llamada;
  - sin `bash -c`, `time`, *pipes* ni redirecciones;
  - para la comilla invertida, `grep -P` con `\x60`.

  Los *pipes* sí van **dentro** de los workflows y de los scripts del humano, porque esos no los ejecutas tú.
- **Mutantes:** aplícalos en memoria (`mock.patch.object` o `python -c`), nunca con un script copiado fuera de `/workspace`.
- **Red:** ninguna, salvo `uv lock` y `uv sync` si de verdad hacen falta (no deberían: no hay dependencias nuevas).
- **Commits:** Conventional Commits en español, con los alcances `ci`, `deploy` y `scripts`.
- **Plan aprobado:** no lo edites.
- **Al terminar:** haz push de `tarea/U02-T03` y vuelve con tu informe. No fusionas tú.
