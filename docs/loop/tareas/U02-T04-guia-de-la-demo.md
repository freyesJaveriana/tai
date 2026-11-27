# U02-T04: la guía de la demo y el plan B de la imagen

**Unidad:** U2 `platform`   **Bolt:** B4-demo   **Rama base:** `bolt/b4-demo`, después de fusionar U02-T03 (#62)
**Pasos del plan que cubre:** el paso 10 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/platform/code-generation/code-generation-plan.md` (aprobado el 2026-11-26), con R-B4d-1 y R-B4d-2. El paso 11 (fijar el SHA en `kustomization.yaml`) no entra: solo se puede hacer cuando el Bolt esté en `main` y `analyzer-image.yml` haya publicado. Va en un PR aparte de una línea, que prepara el orquestador.
**Depende de:** U02-T01 (imagen), U02-T02 (manifiestos y scripts del humano) y U02-T03 (CI e imagen en GHCR).
**Riesgo (ML-4):** bajo, porque solo hay documentación y una prueba estática. Revisa `revisor`.

---

## Alcance

**Entra:**

- **Paso 10, `deploy/demo-analyzer/README.md`**, en español, de dos páginas como máximo. Lleva:
  - **Requisitos de la VM:** Ubuntu, Docker, `minikube start --cni=calico --memory=8g --cpus=4` (DP-06) y `kubectl`, más una comprobación de que Calico quedó activo antes de seguir (R-B4d-2).
  - **Orden de los scripts del humano:** `crear-secret-anthropic.sh`, `crear-pull-secret-ghcr.sh` y `demo-analyzer.sh`. Para cada uno, qué lee (el `.env` no versionado y las variables que espera), qué crea y con qué código sale si algo falta. Se toma del código real de los scripts, no se inventa.
  - **Qué se ve en los logs:** la salida del Job con la entrada `contradiccion.json` (1 o más hallazgos con dos citas) y con `coherente.json` (0 hallazgos), y cómo se distingue un `estado: error`. Se toma de `deploy/src/veridicus_demo/entrypoint.py` y de sus pruebas.
  - **Cómo comprobar la `NetworkPolicy`:** el pod sonda `curl` de `demo-analyzer.sh` no debe llegar a `https://example.com`, y qué significa que sí llegue (Calico no está activo).
  - **Reversión:** `kubectl delete -k deploy/demo-analyzer` y el borrado de los dos Secrets.
  - **Frontera de datos (AUTONOMIA-04, declaración por componente):** el Job corre dentro del clúster. Solo sale hacia Anthropic, por 443, texto sintético seudonimizado por el anonimizador que va dentro del proceso. Ningún otro pod tiene salida, y el Secret solo lo monta el Job.
  - **La imagen, sección «Plan A y plan B» (R-B4d-1):**
    - Plan A: la imagen publicada por `analyzer-image.yml` al fusionar el Bolt en `main`, con el SHA fijado en `kustomization.yaml` por el paso 11. Requisitos en GitHub: el paquete vinculado al repositorio con acceso de Actions en escritura y el `imagePullSecret` de `crear-pull-secret-ghcr.sh`.
    - Plan B, solo para la demo y declarado como desviación de team.md («las imágenes salen de la CI»): construir en la VM con `minikube image build` usando el mismo Dockerfile y el mismo contexto que la CI. La imagen se etiqueta con el nombre y la etiqueta que espera `kustomization.yaml`, y debe quedar claro qué pasa con `imagePullPolicy` y con el `imagePullSecret` en ese caso. Si el plan B exige cambiar un manifiesto, **no lo cambies**: descríbelo como paso manual que hace el humano y no se fusiona, y anótalo en la bitácora como propuesta.
- **Prueba de la guía, `deploy/tests/test_readme.py`** (verificación del paso 10). Falla si:
  - una ruta del repositorio citada en el README no existe (`scripts/humano/…`, `deploy/…`, `deploy/demo-analyzer/entrada/…`);
  - el README nombra un script del humano que no está en `scripts/humano/`, o falta alguno de los tres;
  - falta alguna de las secciones obligatorias: requisitos, orden de los scripts, logs, `NetworkPolicy`, reversión, frontera de datos y plan A y B;
  - aparece una clave, un token o algo con forma de `sk-ant-`, un `kubeconfig`, o `latest` como etiqueta de imagen;
  - el comando de `minikube start` no lleva `--cni=calico`.

  Con un control negativo por regla, con *fixtures* en `deploy/tests/fixtures/readme/`.

**Fuera** (rechazar aunque se vea roto):

- El paso 11 (el SHA en `kustomization.yaml`) y el paso 12 (la demo en la VM, que hace el humano).
- No se cambian los manifiestos, los scripts del humano, los workflows, el Dockerfile, `libs/` ni `contracts/`.
- **No se ejecuta** ningún script de `scripts/humano/`, ni `kubectl`, `minikube`, `docker` ni la CLI fuera de pytest. Tampoco hay red.
- No se cambian ajustes de GitHub.

---

## Archivos de contexto

- Del plan aprobado: el paso 10, DP-04, DP-06, R-B4d-1, R-B4d-2 y el mapa AUTONOMIA.
- `deploy/demo-analyzer/` (los manifiestos y la entrada), `scripts/humano/` (los tres scripts) y `deploy/src/veridicus_demo/entrypoint.py`.
- `docs/loop/bitacoras/U02-T01.md`, `U02-T02.md` y `U02-T03.md`, incluida la nota de GHCR de la ronda 2 de U02-T03.
- `.github/workflows/analyzer-image.yml`: el nombre de la imagen y cómo se etiqueta.

---

## Criterios de aceptación

Se corren desde la raíz del worktree `/workspace/.worktrees/U02-T04`.

- [ ] **CA-1 (paso 10):** la prueba de la guía.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_readme.py -q
  ```
  Se espera: código 0, con un control negativo por regla que falla dentro de su prueba.
- [ ] **CA-2:** nada retrocede.
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
  Además, los cuatro `scripts/check-no-*.sh` sobre el worktree dan `0 apariciones`, y `git -C /workspace/.worktrees/U02-T04 diff --stat origin/bolt/b4-demo -- libs contracts .github deploy/demo-analyzer/*.yaml scripts deploy/images` sale vacío.
- [ ] **CA-3 (en la CI, lo verifica el orquestador):** `deploy-level0` queda en verde en el PR contra `bolt/b4-demo`.

---

## Casos sonda obligatorios (ML-11)

1. **Ruta rota:** un README que cita `scripts/humano/no-existe.sh` debe fallar CA-1.
2. **Script olvidado:** un README sin `crear-pull-secret-ghcr.sh` debe fallar.
3. **Sin Calico:** `minikube start --memory=8g --cpus=4` sin `--cni=calico` debe fallar.
4. **Secreto pegado:** un README con `sk-ant-` seguido de caracteres debe fallar.
5. **Sin frontera:** un README sin la sección de frontera de datos debe fallar.

---

## Plan de pruebas (Testing Contract: custom)

1. **Primero, en rojo:** `test_readme.py` con sus *fixtures* y los casos sonda, antes de que exista el README. Haz un commit del rojo con el mensaje `test(deploy): rojo de la guía de la demo` y anota su SHA en la bitácora.
2. Después escribe el README hasta llegar al verde.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** la guía describe lo que hace el humano; ningún agente lo ejecuta.
- **AUTONOMIA-04:** la declaración por componente de qué corre dentro del clúster y qué datos cruzan la frontera.
- **Solo datos sintéticos** y ningún secreto en el repositorio: la guía nunca muestra una clave, ni siquiera de ejemplo con forma real.
- **team.md, Deployment:** imágenes etiquetadas con el SHA y nunca `latest`. El plan B queda declarado como desviación, solo para la demo.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U02-T04.md`, de una página como máximo. Lleva el SHA del rojo, la tabla del paso 10 con su prueba (ML-14), lo no verificado sin VM (los comandos de Minikube y de Calico) y la propuesta del plan B si exige algo más.
- **Bash:**
  - un comando simple por llamada;
  - sin `bash -c`, `time`, *pipes* ni redirecciones;
  - para la comilla invertida, `grep -P` con `\x60`.
- **Mutantes:** en memoria (`mock.patch.object` o `python -c`), nunca con un script fuera de `/workspace`.
- **Commits:** Conventional Commits en español, con los alcances `deploy` y `docs`.
- **Plan aprobado:** no lo edites.
- **Al terminar:** haz push de `tarea/U02-T04` y vuelve con tu informe. No fusionas tú.
