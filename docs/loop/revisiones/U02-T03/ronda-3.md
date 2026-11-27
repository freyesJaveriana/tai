# Ronda 3 — U02-T03

VEREDICTO: NO-VERDE

Queda un bloqueo, y sigue siendo de la misma clase. La forma fija de la línea de sha256sum cierra los mutantes N1 a N8 y P1 a P5. Pero la verificación todavía se anula si la línea queda dentro de una función, un subshell o un grupo de llaves seguidos de `|| true`, o con un `trap ERR`. Ninguno de esos casos sobrevive a la regla línea por línea; todos sobreviven a toda la suite.

Todo lo demás de la ronda está bien:
- F-06 queda cerrado.
- Kyverno 1.19.2 entra en el workflow con su URL y su suma, y en la tabla.
- El `RUN` del Dockerfile respeta lo de U02-T01.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de los workflows | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/deploy pytest tests/test_workflows.py -q` | 193 passed |
| CA-2 | AUTONOMIA-01 (DP-08) | `uv run … pytest tests/test_autonomia_01.py tests/test_check_no_cluster_apply.py -q` | 170 passed |
| CA-3 | K-97, K-102, K-103, K-104 | `uv run … pytest tests/test_dockerfile.py tests/test_manifests.py tests/test_scripts_humano.py -q`, más `bash -n` de los dos scripts (rutas absolutas) | 283 passed; los dos `bash -n` en 0 |
| CA-4 | Nada retrocede | `uv run … pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q`, más `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 751 passed, 100 % de líneas y ramas; mypy, ruff y formato en 0 |
| CA-4 | Los cuatro check-no-*.sh | `bash /workspace/.worktrees/U02-T03/scripts/check-no-<x>.sh /workspace/.worktrees/U02-T03`, uno por script | los cuatro dan `0 apariciones` |
| CA-4 | Sin cambios en libs/ ni contracts/ | `git -C /workspace/.worktrees/U02-T03 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| CA-5 | En la CI (#62) | no corresponde aquí | pendiente del orquestador |

- **Estado del worktree:** `git status --short` sale limpio.
- **Orden del rojo:** 25f664d y 2f28fa5 traen solo pruebas y fixtures, antes que los verdes 887bca4, 690eced y be26972. El orden cumple el contrato.
- **Los workflows reales cumplen todas las reglas:** `workflow_checks.violations` da `[]` en los dos.
- **Kyverno 1.20.0 ya no queda en ningún workflow:** con grep, solo aparece en la aserción negativa de `test_workflows.py:630-639`.

## Mutantes en memoria
Apliqué cada uno con `python -c` sobre el paso de Trivy de `analyzer-image.yml` (`workflow_checks.violations` tras un `replace`).

**Los de las rondas anteriores, todos atrapados:**
- N1, `&& echo ok`: «forma fija».
- N2, `set +e`, y N2b, `set +o errexit`: «relaja».
- N3, `if VL` y `then`: «forma fija».
- N3b, `if true; then` con la línea fija dentro: «va dentro de un if».
- N8, `&`: «forma fija».
- M16, `|| true` en la línea siguiente: «anula».
- N5, `:x$GITHUB_HEAD_REF`: «no viene entera del SHA».
- N6, `docker buildx build --push --tag "$IMAGE"`, y N7, `docker image push "$IMAGE"`: «latest implícito».

**Los nuevos que sobreviven al comprobador** (da `[]` en todos):
- **M4, una función:** `verificar() {`, la línea fija, `}` y luego `verificar || true`.
- **M5, un subshell:** `(`, la línea fija y `) || true`.
- **M5b, un grupo de llaves:** `{`, la línea fija y `} || true`.
- **M13, un trap:** `trap 'exit 0' ERR` tras el preludio.
- **M14, a nivel de paso:** `continue-on-error: true` en el paso que descarga.

## Hallazgos

### F-07 · NARANJA · deploy/tests/workflow_checks.py:79-86 y 207-219 (`_OPENS`, `_nesting_violations`) · La verificación se anula todavía con una función, un subshell, un grupo de llaves, un trap ERR o `continue-on-error`
- **M4, M5 y M5b son máscaras reales.** Con `set -e`, bash no sale cuando falla un comando dentro de una función, un `( … )` o un `{ … }` usados en una lista `||`. El `tar` siguiente corre sobre un archivo sin verificar y el paso termina en 0. `_OPENS` solo cuenta `if`, `while`, `until`, `case`, `for` y `select`, y la línea fija dentro de un grupo no tiene nada antes ni después en su línea.
- **M13 y M14 no ejecutan el archivo descargado, pero dejan el paso en verde sin la herramienta.** El script termina antes del `tar`. Los pasos siguientes usarían la versión preinstalada en el runner, si existe: en ubuntu-24.04 vienen shellcheck y kustomize, entre otras.

Las pruebas de forma de los workflows reales (`test_deploy_level0_downloads_each_tool…` y `test_trivy_is_downloaded…`) solo comprueban que el texto `sha256sum -c` exista y vaya antes de `tar`. Por eso los cinco mutantes **sobreviven a toda la suite**.

Propongo cerrar la clase de una vez con una plantilla del script entero, no con más casos:
- todo `run:` que descarga es exactamente `set -euo pipefail`, `mkdir -p …`, `curl …` (con su continuación), la línea fija, la extracción (`tar` o `mv` y `chmod`) y la línea `>> "$GITHUB_PATH"`, en ese orden y sin otras líneas;
- el paso no lleva `continue-on-error`.

Si no, como mínimo:
- rechazar `(`, `)`, `{`, `}`, `()`, `trap` y `continue-on-error` en todo paso que descarga;
- añadir un control negativo por cada uno.

### F-08 · AMARILLO · deploy/images/analyzer-cli/Dockerfile:39-43 · La versión exacta de libzstd1 puede desaparecer del espejo
El `RUN` cumple lo de U02-T01:
- crea el usuario con UID y GID 10001 y `--shell /usr/sbin/nologin`;
- corre como root, antes de `USER 10001:10001`;
- no usa `latest`, y los `FROM` y el `COPY --from` siguen con digest;
- está en una sola capa, con `rm -rf /var/lib/apt/lists/*`, `--no-install-recommends` y la versión fijada.

Las pruebas lo protegen: `test_the_final_stage_upgrades_libzstd1…` y `…stays_pinned_numeric_and_without_latest…`. Pero el repositorio de seguridad de Debian solo conserva la última revisión de cada paquete. Cuando salga una `+deb13u2`, `apt-get install libzstd1=1.5.7+dfsg-1+deb13u1` fallará y la construcción de la imagen se romperá. Falla cerrado, así que no es inseguro, solo frágil. Conviene anotarlo en la bitácora como algo a vigilar, con la salida prevista: subir la versión o el digest de la base por PR.

## Lo demás de la ronda
- **F-05:** la parte de la línea, el preludio, `if`, `while` y `until`, `&`, `!` y la conjunción está cerrada. La prueba de la conjunción se invirtió, que es lo correcto.
- **F-06:** cerrado, con buildx, `docker image …` y la etiqueta mixta.
- **Kyverno 1.19.2:** la URL, la suma y `TOOLS` son coherentes. La migración queda como candidata K-107, que es lo correcto.
- **Lo no verificado, ordenado por probabilidad de romper la CI:**
  1. shellcheck sobre los 9 scripts.
  2. Que la versión fijada de libzstd1 exista hoy en el espejo y que el build pase.
  3. hadolint sobre el `RUN` nuevo.
  4. Kyverno 1.19.2 con el `kyverno-test.yaml` que lleva `userinfo`.
  5. El render de kustomize en pytest.

## Tareas candidatas (defectos reales fuera de alcance)
- K-106, sin cambios.
- K-107: migrar las políticas a `ValidatingPolicy`, como la registró el codificador.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/workflow_checks.py:79-86|sha256sum -c anulado con función, subshell o llaves más «|| true», trap ERR o continue-on-error pasa la regla y toda la suite
AMARILLO|deploy/images/analyzer-cli/Dockerfile:39-43|la versión exacta de libzstd1 puede desaparecer del espejo de seguridad y romper el build
INFORME: docs/loop/revisiones/U02-T03/ronda-3.md
```
