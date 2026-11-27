# Ronda 5 — U02-T03

VEREDICTO: VERDE

F-09 y F-10 quedan cerrados, los dos cambios a pruebas existentes no aflojan nada y CA-1 a CA-4 pasan con mis propias corridas. Ningún NARANJA ni ROJO sigue abierto. Encontré una variante nueva que solo aparece si alguien edita el workflow a propósito para burlar la guardia, y la marco como candidata a Accepted risk (K-108), según la regla de cierre del humano. CA-5, el rojo en la CI del PR #62, sigue pendiente del orquestador. El humano fusiona.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Prueba de los workflows | `uv run --frozen --offline --directory /workspace/.worktrees/U02-T03/deploy pytest tests/test_workflows.py -q` | 289 passed |
| CA-2 | AUTONOMIA-01 (DP-08) | `uv run … pytest tests/test_autonomia_01.py tests/test_check_no_cluster_apply.py -q` | 170 passed |
| CA-3 | K-97, K-102, K-103, K-104 | `uv run … pytest tests/test_dockerfile.py tests/test_manifests.py tests/test_scripts_humano.py -q`, más `bash -n` de los dos scripts (rutas absolutas) | 283 passed; los dos `bash -n` en 0 |
| CA-4 | Nada retrocede | `uv run … pytest --cov=veridicus_demo --cov-branch --cov-fail-under=100 -q`, más `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 847 passed, 100 % de líneas y ramas; mypy, ruff y formato en 0 |
| CA-4 | Los cuatro check-no-*.sh | `bash /workspace/.worktrees/U02-T03/scripts/check-no-<x>.sh /workspace/.worktrees/U02-T03`, uno por script | los cuatro dan `0 apariciones` |
| CA-4 | Sin cambios en libs/ ni contracts/ | `git -C /workspace/.worktrees/U02-T03 diff --stat origin/bolt/b4-demo -- libs contracts` | vacío |
| CA-5 | En la CI (#62) | no corresponde aquí | pendiente del orquestador |

- **Ningún workflow, Dockerfile ni script cambió:** `git -C … diff --stat 4ad4024 8b3be80 -- .github deploy/images scripts` sale vacío.
- **Estado del worktree:** `git status --short` sale limpio.
- **Orden del rojo:** dd0a0b4 trae solo pruebas y fixtures, antes que el verde 13fc973. El orden cumple el contrato.

## Mutantes en memoria
Los apliqué con `python -c` sobre los pasos reales de descarga (`workflow_checks.violations` tras un `replace`).

**Los workflows reales, sin cambios:** `deploy-level0.yml` y `analyzer-image.yml` dan `[]` los dos.

**F-09, atrapados:**
- **B8**, la suma inventada en el `env:` del job y la de la tabla de señuelo en el paso (`SUMA_TABLA`): «la variable SHA256 no se define en el env del paso con la suma de la tabla de trivy» y «se define también en el env del job o del workflow».
- **B8c**, lo mismo con la suma en el `env:` del workflow: las mismas dos violaciones.
- Las pruebas nuevas cubren además la suma de otra herramienta, en mayúsculas, vacía o más larga; un paso sin herramienta o con dos; y una variable sin definir en una ruta.

**F-10, atrapados:**
- **B9**, `gh release download … && ./x`: «no sigue la plantilla».
- **Descargas sin URL:** `wget`, `python3 -c "import urllib…"` y `pip download` tienen sus controles negativos en la suite.
- **Rutas atadas:** la ruta del `curl -o`, la de la verificación y la de `tar` o `mv` tienen que ser la misma cadena. B1 a B4 y la variante con `mv` ya fallan en el comprobador, no solo en ejecución.

## Juicio sobre los dos cambios a pruebas existentes
- **`ok.yml`:** la URL pasa de `a.tar.gz` al asset `trivy_0.76.2_Linux-64bit.tar.gz`. Hace falta porque ahora la herramienta se identifica por su asset, y su `SHA256` del paso coincide con la suma de Trivy de la tabla. No afloja nada: el fixture base sigue siendo exactamente la plantilla.
- **`test_f05_the_fixed_line_passes_alone_in_its_line`:** sale de la lista de líneas que pasan la variante `${RUNNER_TEMP}/a.tar.gz` con llaves. **Endurece:** esa ruta ya no es la misma cadena que la del `curl`, así que ahora se rechaza. El caso «ruta con llaves» de `PATH_MISMATCHES` lo fija como negativo, y `test_f10_the_same_literal_path_in_the_three_lines_passes_also_with_braces` conserva la forma con llaves cuando las tres líneas coinciden.

## Hallazgos

Ningún hallazgo (a) nuevo: ninguno deja pasar algo sin una edición maliciosa del workflow ni rompe un criterio de la tarea.

### F-11 · candidata a Accepted risk (K-108) · deploy/tests/workflow_checks.py, `_binding_violations` · Una suma escrita en `$GITHUB_ENV` por un paso anterior
Para que aparezca, alguien tiene que añadir antes del paso de Trivy un paso con `echo SHA256=<otra> >> "$GITHUB_ENV"`. El comprobador da `[]`, porque solo vigila el `env:` del job y del workflow, y no los pasos que escriben en `GITHUB_ENV`. No verifiqué si GitHub deja que el `env:` del paso gane sobre `GITHUB_ENV`; si gana, la variante no tiene efecto. Requiere editar el workflow a propósito, así que entra en la clase (b) y **no cuenta para el veredicto**. Si algún día se quiere cerrar, la salida es rechazar `GITHUB_ENV` en cualquier `run:` de los workflows de deploy.

Probé además definir `RUNNER_TEMP` en el `env:` del paso. El comprobador da `[]`, pero no es un defecto: las tres rutas siguen atadas a la misma cadena y la verificación se hace sobre el mismo archivo.

## Lo que queda para vigilar
- **De rondas anteriores, sin bloquear:** F-08, la versión fijada de libzstd1 que puede desaparecer del espejo, ya anotada en la bitácora; y las candidatas K-106 y K-107.
- **Lo no verificado que puede romper la CI de #62:** hadolint sobre el `RUN` de libzstd1, que esa versión exista hoy en el espejo, Kyverno 1.19.2 con `userinfo` y el render de kustomize en pytest.
- **Fuera del PR:** el primer publish en `main` depende del permiso del paquete en GHCR (nota de F-04 en la bitácora).

## Tareas candidatas (defectos reales fuera de alcance)
- K-106, el `kyverno apply` sobre el render no prueba nada.
- K-107, migrar las políticas a `ValidatingPolicy`.
- K-108, como Accepted risk: la suma escrita en `GITHUB_ENV` (F-11).

```
VEREDICTO: VERDE
INFORME: docs/loop/revisiones/U02-T03/ronda-5.md
```
