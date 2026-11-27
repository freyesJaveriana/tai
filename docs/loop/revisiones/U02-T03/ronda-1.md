# Ronda 1 — U02-T03

VEREDICTO: NO-VERDE

Hay un solo NARANJA y es pequeño. Corrí los cuatro criterios y todos pasan. Los workflows reales están bien en permisos, expresiones, sumas, URL y orden de publicación. Lo que bloquea es un mutante que sobrevive a toda la suite en la regla de sha256sum, que es de seguridad.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de los workflows | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/deploy pytest tests/test_workflows.py -q` | 68 passed (0,98 s) |
| CA-2 | AUTONOMIA-01 (DP-08) | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/deploy pytest tests/test_autonomia_01.py tests/test_check_no_cluster_apply.py -q` | 170 passed |
| CA-3 | K-97, K-102, K-103, K-104 | `uv run … pytest tests/test_dockerfile.py tests/test_manifests.py tests/test_scripts_humano.py -q`, más `bash -n` de los dos scripts (rutas absolutas) | 280 passed; los dos `bash -n` en 0 |
| CA-4 | Nada retrocede | `uv run … pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q`, más `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 623 passed, 100 % de líneas y ramas; mypy, ruff y formato en 0 |
| CA-4 | Los cuatro check-no-*.sh | `bash /workspace/.worktrees/U02-T03/scripts/check-no-<x>.sh /workspace/.worktrees/U02-T03`, uno por script | los cuatro dan `0 apariciones` |
| CA-4 | Sin cambios en libs/ ni contracts/ | `git -C /workspace/.worktrees/U02-T03 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| extra | Guardia de contracts sobre los workflows | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/contracts pytest tests/checks/test_ci_workflows.py -q` | 79 passed; solo falla el piso global de cobertura, porque corrí un subconjunto |
| CA-5 | En la CI | no corresponde aquí | pendiente del orquestador |

- **Rojo primero:** f58f4d7 trae solo pruebas, fixtures y el ayudante `workflow_checks.py`, y los workflows llegan después en aba5811. El orden cumple el Testing Contract. No reproduje el rojo, porque eso exige hacer checkout.
- **Estado del worktree:** `git status --short` sale limpio. Solo quedaron archivos ignorados en `contracts/` (`.venv` y cachés), creados por mi corrida de contracts.

## Hallazgos

### F-01 · NARANJA · deploy/tests/workflow_checks.py:142-165 y test_workflows.py:167-180 · La regla de sha256sum mira si el texto aparece, no si la verificación tiene efecto
Probé mutantes en memoria con `python -c` sobre `analyzer-image.yml` (`workflow_checks.violations` tras un `replace`):
- P2, `sha256sum -c -` cambiado por `sha256sum -c - || true`: `[]`. Ninguna prueba de forma lo atrapa, porque `test_deploy_level0_downloads_each_tool…` y `test_trivy_is_downloaded…` solo comprueban que el texto `sha256sum -c` exista y vaya antes de `tar`/`chmod`. **El mutante sobrevive a toda la suite.** Si se cuela, la CI ejecuta binarios sin verificar.

Otros tres mutantes son de la misma clase: el comprobador da `[]`, pero las pruebas de forma exacta los atrapan en los workflows reales, así que son el mismo defecto con efecto menor:
- P1, el `if:` de publish más `|| github.event_name == 'pull_request'`: el comprobador da `[]`, porque `_MAIN_ONLY` se busca como subcadena. Lo atrapa `jobs["publish"]["if"] == ONLY_MAIN`.
- P3, `docker push "$IMAGE"`, y P5, `docker build --tag "$IMAGE"`: el comprobador da `[]`, porque no ve el `latest` implícito. Las aserciones exactas del texto de push y de build los atrapan.

Arreglo propuesto: rechazar que `sha256sum` vaya seguido de `||` en su línea (o exigir `set -e` y nada detrás). Exigir que la condición de un job con `packages: write` sea exactamente la de main, no que la contenga. Tratar como `latest` una referencia `"$IMAGE"` sin `:` en `docker build`, `tag` y `push`.

### F-02 · AMARILLO · deploy/tests/workflow_checks.py · Ninguna regla vigila la inyección de `${{ }}` en `run:`
Hoy no hay ninguna: con `grep -nP "\x24\{\{"` todas las expresiones están en `env:`, `concurrency` o `cancel-in-progress`. Pero la sonda P4, `run: echo ${{ github.event.pull_request.title }} && …`, pasa el comprobador (`[]`). Conviene una regla que rechace `${{` dentro de `run:`.

### F-03 · AMARILLO · deploy-level0.yml:158-165 · El `kyverno apply` sobre el render no prueba nada y solo mira el código de salida (K-106)
Las cuatro políticas cubren solo `Pod`, con la autogeneración en `none`, y el render trae un `Job`, así que da `pass: 0` y todo se salta. A diferencia de los controles negativos, este paso no comprueba el resumen con grep. Las mismas reglas sí corren sobre el render real con pytest (K-102), y eso cubre el hueco. Ver la sección de candidatas.

### F-04 · AMARILLO · docs/loop/bitacoras/U02-T03.md · Falta una nota para el humano sobre el permiso de GHCR
Si el paquete `veridicus-analyzer-cli` ya existe, creado a mano en P0.1, el `GITHUB_TOKEN` solo puede publicar si el paquete está vinculado al repositorio con acceso de Actions en escritura. La imagen tampoco lleva la etiqueta `org.opencontainers.image.source`, pero el Dockerfile es de U02-T01 y queda fuera de esta tarea. Si nadie lo revisa, el primer push a `main` puede fallar con `denied: permission_denied: write_package`.

## Juicio sobre los puntos del encargo
1. **Seguridad de los workflows: correcta.**
   - `contents: read` está en el nivel del workflow. `packages: write` aparece solo en `publish`, con la condición de push a `main`, y `build-scan` no tiene permisos propios ni usa secretos.
   - `persist-credentials: false` en todos los checkouts.
   - Ninguna `${{ }}` dentro de `run:`.
   - `sha256sum -c` va antes de cada `tar`/`mv`/`chmod`.
   - La URL de kustomize lleva `kustomize%2Fv5.8.3`.
   - Se extrae en `$RUNNER_TEMP/bin`: shellcheck con `--strip-components=1` y los demás tarballs completos (algún LICENSE se sobrescribe, sin efecto).
   - Trivy corre antes del login, el login usa `--password-stdin` y el push lleva la etiqueta del SHA.
2. **AUTONOMIA-01 / DP-08: correcto.** Ningún `kubectl` ni kubeconfig. La guardia no se tocó. `git ls-files -z -- 'scripts/*.sh'` (el `*` de un pathspec cruza `/`) solo pasa los scripts por shellcheck, sin ejecutarlos y sin nombrar la carpeta del humano.
3. **Controles negativos invertidos: no pueden pasar en falso.** El de kubeconform exige `Invalid: 1, Errors: 0`, así que un fallo de red o de esquema da `Errors` mayor que 0, el grep no encuentra nada y la CI queda en rojo. Los de kyverno exigen `fail: [1-9]`, y un error de carga o de sintaxis no deja ese resumen. Si `kyverno apply` saliera con 0 aun con fallos, el paso sale con `exit 1`, así que también falla cerrado.
4. **K-102: correcto.**
   - Solo renombra los ConfigMap cuyo nombre base está en `configMapGenerator` y que llevan un sufijo de 10 caracteres `[a-z0-9]`. No puede ocultar otra diferencia.
   - Si la variable apunta a un archivo que no existe o que está vacío, falla cerrado (FileNotFoundError o ValueError).
   - Un render recortado hace fallar los 8 usos de `_one`. Saltarse las reglas exige editar el workflow, y eso se ve en el PR.
5. **K-104: correcto.** Lo verifiqué con mutantes en memoria:
   - El valor de la anotación nunca sale de kubectl: la plantilla imprime `si` y la sustitución solo lo compara.
   - Quitar el último `exit 2` da `falta salir con 2`.
   - Volver a `jsonpath` o meter un pipe dan `no usa el literal fijo`.
   - El script de GHCR real da `[]`.
   - Si el Secret no tiene ninguna anotación, `index` sobre nil hace fallar a kubectl, la salida queda vacía y el script sigue, que es lo correcto porque no hay anotación.
6. **Candidatas del codificador:**
   - **K-105, rutas que disparan la imagen:** es un defecto real. La imagen copia `deploy/src`, `pyproject.toml` y `uv.lock`, y un cambio solo en esos archivos no se construye, no se escanea y no deja ninguna imagen con ese SHA. Pero la tarea fija las rutas al pie de la letra, y la primera fusión del Bolt en `main` sí dispara el workflow (toca `deploy/images/**` y el propio workflow). Mi recomendación: arreglarlo antes de U02-T04 con una línea, ampliando la tarea; aquí no es un hallazgo.
   - **K-106:** se queda como candidata. El arreglo toca políticas de U02-T02: la autogeneración para `Job`, o un `kyverno apply` sobre la plantilla del pod.
7. **Lo no verificado, ordenado por probabilidad de romper la CI:**
   1. **shellcheck** sobre 9 scripts que nunca pasaron por él. Cualquier hallazgo, incluso de estilo o informativo, da 1.
   2. **CLI de Kyverno 1.20:** el esquema de `kyverno-test.yaml`, el texto `fail: N` y el código de salida de `apply`.
   3. **hadolint** con el umbral por defecto (`info`) sobre el Dockerfile de U02-T01.
   4. **pytest sobre el render de kustomize 5.8.3**, si difiere de la emulación.
   5. **kubeconform:** que existan los esquemas `v1.31.0-standalone-strict` en `master`.
   6. Fuera del PR, el **primer publish en `main`** (F-04).

## Tareas candidatas (defectos reales fuera de alcance)
- K-105, como en el punto 6. Recomiendo hacerlo antes de U02-T04.
- K-106, como en el punto 6.
- Dockerfile: añadir `LABEL org.opencontainers.image.source` para vincular el paquete de GHCR.

```
VEREDICTO: NO-VERDE
NARANJA|deploy/tests/workflow_checks.py:142-165|sha256sum -c seguido de «|| true» pasa la regla y toda la suite
AMARILLO|deploy/tests/workflow_checks.py|ninguna regla vigila la inyección de ${{ }} en run:
AMARILLO|.github/workflows/deploy-level0.yml:158-165|kyverno apply sobre el render no prueba nada y solo mira el código de salida (K-106)
AMARILLO|docs/loop/bitacoras/U02-T03.md|falta la nota al humano sobre el permiso de GHCR para el primer publish
INFORME: docs/loop/revisiones/U02-T03/ronda-1.md
```
