# Ronda 2 — U02-T03

VEREDICTO: NO-VERDE

Queda un solo bloqueo, y es estrecho. La regla del sha256sum anulado (F-01, primera parte) todavía deja pasar formas de anular la verificación sin `||`, `;` ni pipe. Una nueva prueba incluso da por buena una de ellas. Todo lo demás de la ronda está bien:
- P1 a P5 quedan cerrados.
- F-02 está cerrado.
- La nota de F-04 está en la bitácora.
- K-105 y el `LABEL` están hechos.
- La prueba que se cambió endurece la regla.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de los workflows | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/deploy pytest tests/test_workflows.py -q` | 126 passed |
| CA-2 | AUTONOMIA-01 (DP-08) | `uv run … pytest tests/test_autonomia_01.py tests/test_check_no_cluster_apply.py -q` | 170 passed |
| CA-3 | K-97, K-102, K-103, K-104 | `uv run … pytest tests/test_dockerfile.py tests/test_manifests.py tests/test_scripts_humano.py -q`, más `bash -n` de los dos scripts (rutas absolutas) | 281 passed; los dos `bash -n` en 0 |
| CA-4 | Nada retrocede | `uv run … pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q`, más `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 682 passed, 100 % de líneas y ramas; mypy, ruff y formato en 0 |
| CA-4 | Los cuatro check-no-*.sh | `bash /workspace/.worktrees/U02-T03/scripts/check-no-<x>.sh /workspace/.worktrees/U02-T03`, uno por script | los cuatro dan `0 apariciones` |
| CA-4 | Sin cambios en libs/ ni contracts/ | `git -C /workspace/.worktrees/U02-T03 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| CA-5 | En la CI | no corresponde aquí | pendiente del orquestador |

- **Estado del worktree:** `git status --short` sale limpio.
- **Orden del rojo:** da3d419 trae solo pruebas y fixtures, antes que el verde (059a423 y fa692da). El orden cumple el contrato.

## Mutantes en memoria
Apliqué cada uno con `python -c` sobre `analyzer-image.yml` (`workflow_checks.violations` tras un `replace`).

**Los de la ronda 1, todos atrapados:**
- P1, `if:` de publish con `|| github.event_name == 'pull_request'`: «no es exactamente la condición de push a main».
- P2, `sha256sum -c - || true`: «anula el código de salida».
- P3, `docker push "$IMAGE"`, y P5, `docker build --tag "$IMAGE"`: «latest implícito».
- P4, `${{ github.event.pull_request.title }}` dentro de un `run:`: «expresión de Actions dentro de un run».
- N4 (nuevo), `IMAGE_TAG: ${{ github.head_ref }}`: «no es el SHA del commit».

**Los que sobreviven:**
- **N1**, `sha256sum -c - && echo ok`: `[]`.
- **N2**, `set +e` en lugar de `set -euo pipefail`: `[]`.
- **N3**, la verificación como condición de un `if` de varias líneas (`sha256sum -c -`, luego `then true` y `fi`): `[]`.
- **N8**, `sha256sum -c - &`: `[]`.

Ninguna prueba de forma atrapa N1, N2, N3 ni N8 en los workflows reales, porque solo comprueban que el texto `sha256sum -c` exista y vaya antes de `tar` o `chmod`. Así que **sobreviven a toda la suite**.

**Sobreviven al comprobador, pero no a la suite:**
- N5, `"$IMAGE:x$GITHUB_HEAD_REF"`, una etiqueta con una variable dentro.
- N6, `docker buildx build --push --tag "$IMAGE"`.
- N7, `docker image push "$IMAGE"`.

El comprobador da `[]` en los tres. Las aserciones exactas del texto de push y de build los atrapan en los workflows reales.

**El `LABEL`:** llamé a `test_the_final_stage_carries_the_oci_source_label…` con el Dockerfile alterado en memoria. Pasa con el real y falla en los tres casos que debe: movido a la etapa `build`, quitado y duplicado. La URL `https://github.com/freyesJaveriana/tai` coincide con `git remote -v`.

## Hallazgos

### F-05 · NARANJA · deploy/tests/workflow_checks.py:66-70 y 178-181; deploy/tests/test_workflows.py, `test_f01_a_check_followed_by_a_conjunction_still_passes` · El sha256sum anulado sigue pasando sin `||`, `;` ni pipe
Con `set -e`, bash no sale si falla un comando de una lista `&&` que no es el último, ni si falla la condición de un `if`. Por eso `echo "…" | sha256sum -c - && echo ok` deja la suma mala sin efecto: el `tar` siguiente corre con un binario sin verificar y el paso termina en 0. Lo mismo pasa con `set +e` (N2), con la verificación dentro de un `if` (N3) y con `&` (N8).

La nueva prueba `test_f01_a_check_followed_by_a_conjunction_still_passes` afirma que `&& true` y `&& echo ok` deben pasar. Es decir, deja fijado el hueco.

Es el mismo hallazgo de clase de la ronda 1 (F-01), y el barrido quedó incompleto. Arreglo propuesto, en vez de una lista de máscaras:
- exigir la forma fija de la línea, `echo "${SHA256}  <ruta>" | sha256sum -c -`, como comando propio de su línea y sin nada detrás;
- exigir que el script empiece por `set -euo pipefail` y que no lleve `set +e`;
- exigir que la verificación no vaya dentro de un `if`, `while`, `until` ni tras un `!`;
- invertir la prueba de la conjunción para que falle, y añadir un control negativo por cada forma: N1, N2, N3 y N8.

### F-06 · AMARILLO · deploy/tests/workflow_checks.py:68-71 y 199-222 · El comprobador de etiquetas tiene puntos ciegos
N5 (una etiqueta que contiene una variable distinta del SHA), N6 (`docker buildx build`) y N7 (`docker image push`) pasan el comprobador. En los workflows reales los atrapan las pruebas de forma exacta, así que no bloquea. Si se toca el comprobador por F-05, vale la pena ampliar `_DOCKER` a `buildx build`, `image push` e `image tag`, y aceptar como variable de la etiqueta solo la que venga entera del SHA.

## Juicio sobre la prueba cambiada
`test_a_job_with_packages_write_is_fine_when_the_workflow_has_no_pull_request_trigger` **endurece la regla.** En la ronda 1 bastaba con que no hubiera disparador de `pull_request` para aceptar un job con `packages: write` sin `if`. Ahora se exige la condición exacta siempre. La nueva `test_f01_a_packages_write_job_without_an_if_fails_even_without_a_pull_request` lo fija.

## Lo demás de la ronda
- **F-02:** ninguna `${{` dentro de `run:`. Tiene sus controles negativos (P4, `${{github.sha}}` sin espacios y `$${{ … }}`), y la expresión sigue permitida en `env:`.
- **F-04:** la nota de GHCR para el humano está en la bitácora (sección «Ronda 2»).
- **K-105:** `deploy/src/**`, `deploy/pyproject.toml` y `deploy/uv.lock` están en `pull_request` y en `push`, cubiertos por `IMAGE_PATHS`.
- **`LABEL` OCI:** está solo en la etapa final, y no cambió nada más del Dockerfile.
- **K-106:** sigue como candidata, que es lo correcto.
- **Lo que más probablemente rompa la CI** no cambia: shellcheck, luego la CLI de Kyverno 1.20, luego hadolint, luego el render de kustomize en pytest. Fuera del PR, el primer publish en `main` (permiso del paquete en GHCR).

## Tareas candidatas (defectos reales fuera de alcance)
- K-106, sin cambios.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/workflow_checks.py:66-70|sha256sum -c anulado con «&& …», «set +e», un «if» o «&» pasa la regla y toda la suite; una prueba nueva da por buena la conjunción
AMARILLO|deploy/tests/workflow_checks.py:68-71|el comprobador de etiquetas no ve buildx, «docker image push» ni una etiqueta con una variable dentro
INFORME: docs/loop/revisiones/U02-T03/ronda-2.md
```
