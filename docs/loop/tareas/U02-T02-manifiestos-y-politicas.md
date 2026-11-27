# U02-T02: los manifiestos, la NetworkPolicy, las políticas y los scripts del humano

**Unidad:** U2 `platform`   **Bolt:** B4-demo   **Rama base:** `bolt/b4-demo`, después de fusionar U02-T01
**Pasos del plan que cubre:** los pasos 4 a 7 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/platform/code-generation/code-generation-plan.md` (aprobado el 2026-11-26), con las precisiones DP-04, DP-07 y DP-08.
**Historias:** la demo en Kubernetes de B4-demo. Cubre las mitades de manifiestos de AUTONOMIA-01 y AUTONOMIA-04, y AC11.6.4 (mitad de U2), leída con DP-04.
**Depende de:** U02-T01: el paquete `deploy/` y la entrada sintética.
**Riesgo (ML-4):** alto. Es la frontera de red, el Secret y AUTONOMIA-01. La revisión la hace `revisor` con `opus`.

---

## Alcance

**Entra:**

> - **Paso 4, el namespace y el Job** (`deploy/demo-analyzer/`):
>   - `kustomization.yaml`:
>     - `namespace: veridicus-demo`;
>     - un `configMapGenerator` `veridicus-demo-entrada` con los dos archivos de `entrada/`;
>     - `images:` con `ghcr.io/freyesjaveriana/veridicus-analyzer-cli` y la etiqueta provisional `sha-pendiente`, que el paso 11 sustituye por el SHA real.
>   - `namespace.yaml`, con las etiquetas `pod-security.kubernetes.io/enforce: restricted`, `warn: restricted` y `audit: restricted`.
>   - `job.yaml`, con el Job `veridicus-analyzer-demo` y la etiqueta `app.kubernetes.io/name: veridicus-analyzer-demo`:
>     - `backoffLimit: 0`, `activeDeadlineSeconds: 900` y `ttlSecondsAfterFinished: 3600`;
>     - `restartPolicy: Never`;
>     - `automountServiceAccountToken: false` y una `ServiceAccount` propia, sin permisos;
>     - en el pod: `securityContext` con `runAsNonRoot: true`, `runAsUser: 10001`, `runAsGroup: 10001`, `fsGroup: 10001` y `seccompProfile: RuntimeDefault`;
>     - en el contenedor: `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false` y `capabilities.drop: [ALL]`;
>     - `resources`: requests de 250m de CPU y 256Mi de memoria, y limits de 1 CPU y 512Mi;
>     - volúmenes: `entrada` desde el ConfigMap, de solo lectura y montado en `/entrada`; `emptyDir` en `/salida` y en `/tmp`;
>     - variables de entorno:
>       - `VERIDICUS_ANTHROPIC_API_KEY`, por `secretKeyRef` al Secret `veridicus-anthropic`, con la llave `api-key` y `optional: false`;
>       - `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S="300"`;
>       - `VERIDICUS_DEMO_ENTRADA=/entrada` y `VERIDICUS_DEMO_SALIDA=/salida`;
>     - `imagePullSecrets: [{name: veridicus-ghcr}]`.
> - **Paso 5, la `NetworkPolicy`** (`networkpolicy.yaml`):
>   - `veridicus-deny-all`, con `podSelector: {}` y `policyTypes` de entrada y salida, sin reglas;
>   - `veridicus-allow-analyzer-egress`, que selecciona solo `app.kubernetes.io/name: veridicus-analyzer-demo`. Permite:
>     - TCP 443 hacia `0.0.0.0/0`, con `except` de `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` y `169.254.0.0/16`;
>     - UDP y TCP 53 hacia los pods `k8s-app: kube-dns` del namespace `kube-system`, seleccionado por `kubernetes.io/metadata.name`.
> - **Paso 6, las políticas estáticas:**
>   - `deploy/tests/test_manifests.py` (pytest con PyYAML, sobre la salida renderizada de los YAML de `deploy/demo-analyzer/`). Comprueba, con un control negativo por regla:
>     - **(a)** solo el Job referencia el Secret `veridicus-anthropic`, por `secretKeyRef`, `envFrom` o volumen;
>     - **(b)** ninguna imagen es `latest` ni va sin etiqueta;
>     - **(c)** todo pod cumple el `securityContext` del paso 4;
>     - **(d)** todo contenedor tiene requests y limits;
>     - la `NetworkPolicy` del paso 5: existe `deny-all` y ninguna otra política da salida a un selector distinto del Job.
>   - `deploy/tests/test_autonomia_01.py`, la comprobación estática de DP-08:
>     - recorre `.github/` y todo `*.sh`, `*.py`, `*.yml`, `*.yaml` y `Makefile` del repositorio, fuera de `.git`, `.venv`, `.worktrees`, `node_modules` y `deploy/tests/fixtures`;
>     - falla si aparece `kubectl apply|create|delete|patch|replace`, `helm install|upgrade`, `kustomize ... | kubectl` o `sbatch` fuera de `scripts/humano/`;
>     - también falla si un archivo de `scripts/humano/` no empieza, después del *shebang*, con `# Lo ejecuta el humano (AUTONOMIA-01)`, o si un workflow de `.github/` menciona `scripts/humano/`;
>     - los controles negativos son *fixtures* en `deploy/tests/fixtures/`: un workflow con `kubectl apply` y un script fuera de `scripts/humano/` con `helm upgrade`. Cada uno debe hacer fallar la comprobación al apuntarla a su carpeta.
>   - `deploy/policies/`, las mismas reglas (a) a (d) como `ClusterPolicy` de Kyverno en modo `Enforce`, con un `kyverno-test.yaml` por política y recursos de paso y de fallo en `deploy/policies/<política>/resources/`. Aquí no se corren, porque el contenedor no tiene Kyverno: las corre U02-T03 en la CI. Una prueba de pytest comprueba que cada política tiene su `kyverno-test.yaml` con al menos un resultado `pass` y uno `fail`.
> - **Paso 7, los scripts del humano** (`scripts/humano/`), cada uno con la marca de DP-08 y `set -euo pipefail`:
>   - `crear-secret-anthropic.sh`:
>     - lee `VERIDICUS_ANTHROPIC_API_KEY` de un archivo `.env` pasado como argumento, sin hacer `source`: lo analiza con `grep` y `cut` sobre una sola llave;
>     - crea el Secret con `kubectl create secret generic veridicus-anthropic --from-file=api-key=<archivo temporal 0600> --dry-run=client -o yaml | kubectl apply -f -`;
>     - borra el temporal con `trap`, nunca hace `echo` de la clave y nunca la pasa como argumento de la línea de comandos;
>   - `crear-pull-secret-ghcr.sh`: crea `veridicus-ghcr` del tipo `docker-registry`, con el usuario y un token de solo lectura de paquetes que se leen igual, del `.env`;
>   - `demo-analyzer.sh`:
>     - aplica con `kubectl apply -k deploy/demo-analyzer`;
>     - espera al Job con `kubectl wait --for=condition=complete --timeout=900s`;
>     - imprime `kubectl logs job/veridicus-analyzer-demo`;
>     - comprueba la red con un pod efímero de `curlimages/curl` fijado por digest, en el mismo namespace y sin la etiqueta del Job, que intenta `https://example.com` con un plazo de 10 s. El script termina distinto de 0 si ese pod **sí** llega;
>     - termina con el código del Job;
>   - `deploy/tests/test_scripts_humano.py` exige la marca, `set -euo pipefail`, el `trap`, que no haya ningún `echo` ni `printf` de la variable de la clave, ningún `--from-literal` y ningún `source` ni `.` del `.env`. Lleva un control negativo por regla, con *fixtures*.

**Fuera** (rechazar aunque se vea roto):

- La CI (`deploy-level0.yml` y `analyzer-image.yml`) es de U02-T03. Esta tarea no crea workflows.
- La guía `deploy/demo-analyzer/README.md` y la fijación del SHA son de U02-T04.
- No se toca `libs/`, `contracts/` ni el punto de entrada de U02-T01, salvo para añadir `pyyaml` (y `types-PyYAML`) al grupo de desarrollo de `deploy/pyproject.toml`.
- **No se ejecuta ningún script de `scripts/humano/`, ni `kubectl` ni `minikube`.** Solo los corre el humano.

---

## Archivos de contexto

- Del plan aprobado: los pasos 4 a 7, DP-04, DP-07, DP-08 y el mapa AUTONOMIA.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/platform/infrastructure-design/infrastructure-specification.md`: la `NetworkPolicy`, el `securityContext` y los Secrets del diseño completo. Úsalo como referencia; DP-04 manda en este corte.
- `docs/loop/bitacoras/U02-T01.md`: el paquete `deploy/`, el punto de entrada y sus variables.
- `.github/workflows/`: lo que la comprobación de AUTONOMIA-01 debe dejar pasar.

---

## Criterios de aceptación

Se corren desde la raíz del worktree `/workspace/.worktrees/U02-T02`.

- [ ] **CA-1 (pasos 4 y 5):** los manifiestos y la `NetworkPolicy`.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_manifests.py -q
  ```
  Se espera: código 0, con al menos un control negativo por regla (a) a (d) y por la regla de la `NetworkPolicy`. Cada control se prueba con un manifiesto alterado en memoria que hace fallar la comprobación.
- [ ] **CA-2 (paso 6 e):** AUTONOMIA-01.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_autonomia_01.py -q
  ```
  Se espera:
  - código 0 sobre el repositorio real;
  - cada *fixture* negativo falla dentro de su prueba;
  - `scripts/humano/` pasa porque lleva la marca.
- [ ] **CA-3 (paso 6, Kyverno):** cada política tiene su prueba.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_policies_layout.py -q
  ```
  Se espera: código 0, con 4 políticas y cada una con resultados `pass` y `fail`.
- [ ] **CA-4 (paso 7):** los scripts del humano.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_scripts_humano.py -q
  ```
  ```bash
  bash -n /workspace/.worktrees/U02-T02/scripts/humano/demo-analyzer.sh
  ```
  Se espera: código 0. El `bash -n` se repite con los otros dos scripts y solo comprueba la sintaxis, sin ejecutar nada.
- [ ] **CA-5:** nada retrocede, con tipos, *lint* y guardias.
  ```bash
  uv run --frozen --offline --directory deploy pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100
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
  Además corren los tres `scripts/check-no-*.sh` sobre el worktree, que deben dar `0 apariciones`, y `git -C /workspace/.worktrees/U02-T02 diff --stat origin/bolt/b4-demo -- libs contracts`, que debe salir vacío.

---

## Casos sonda obligatorios (ML-11)

1. **Otro pod con el Secret:** un Deployment con `envFrom: secretRef: veridicus-anthropic` debe fallar la regla (a). También debe fallar uno que lo monte como volumen.
2. **Salida abierta por otro camino:** una segunda `NetworkPolicy` con `podSelector: {}` y salida hacia `0.0.0.0/0` debe fallar. También debe fallar una con `ipBlock` sin `except` para el Job.
3. **DNS hacia cualquier destino:** una regla del puerto 53 sin `namespaceSelector` ni `podSelector` debe fallar, porque abriría el 53 hacia internet.
4. **AUTONOMIA-01 disfrazada:** `kubectl   apply` con varios espacios, `kubectl -n x apply` y `helm upgrade --install` fuera de `scripts/humano/` deben fallar.
5. **La clave en `ps`:** un script con `--from-literal=api-key=` debe fallar la prueba de scripts.

---

## Plan de pruebas (Testing Contract: custom)

1. **Primero, en rojo:** `test_manifests.py`, `test_autonomia_01.py` y `test_scripts_humano.py`, con todos los casos sonda. Haz un commit del rojo con el mensaje `test(deploy): rojo de manifiestos, AUTONOMIA-01 y scripts del humano` y anota su SHA en la bitácora.
2. Después escribe los manifiestos, la `NetworkPolicy`, los scripts y las políticas de Kyverno hasta llegar al verde.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** ningún workflow ni script del agente aplica nada al clúster; solo `scripts/humano/`, y lo corre el humano (CA-2).
- **AUTONOMIA-04:** la salida está negada salvo para el Job, y el Secret solo lo monta el Job (CA-1).
- **team.md, Secrets:** los manifiestos solo hacen referencia al Secret. El valor lo crea el humano desde un `.env` no versionado.
- **Solo datos sintéticos.**

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U02-T02.md`, de una página como máximo. Lleva el SHA del rojo, la tabla de viñetas de los pasos 4 a 7 con su prueba (ML-14) y cualquier supuesto sobre Minikube o Calico.
- **Bash:**
  - un comando simple por llamada;
  - sin `bash -c`, `time`, *pipes* ni redirecciones;
  - para la comilla invertida, `grep -P` con `\x60`.

  Los *pipes* sí van **dentro** de los scripts del humano, porque esos no los ejecutas tú.
- **Red:** ninguna, salvo `uv lock` y `uv sync`.
- **Commits:** Conventional Commits en español, con los alcances `deploy` y `scripts`.
- **Plan aprobado:** no lo edites.
- **Al terminar:** haz push de `tarea/U02-T02` y vuelve con tu informe. No fusionas tú.
