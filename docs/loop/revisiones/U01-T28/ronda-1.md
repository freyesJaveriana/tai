# Ronda 1 — U01-T28

VEREDICTO: VERDE

Corrí yo mismo todos los criterios (CA-1 a CA-6) y pasan. No hay ningún ROJO ni NARANJA. Quedan tres AMARILLOS que no bloquean y una tarea candidata. Al terminar, el worktree está limpio: `git status` solo muestra archivos ignorados (`.venv`, cachés, `.coverage`). La rama `tarea/U01-T28` está en 2817d99 y su merge-base con `feat/b1-contratos` es d2adcdf.

No escribí el informe en `docs/loop/revisiones/U01-T28/ronda-1.md` porque no tengo herramientas de escritura. Este texto es su contenido.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Formato de Python | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T28/contracts ruff format --check .` | `113 files already formatted`, código 0: pasa |
| 2 | YAML de contracts | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T28/contracts yamllint -s -c /workspace/.worktrees/U01-T28/.yamllint.yaml /workspace/.worktrees/U01-T28/contracts` | Sin salida, código 0. Con `--list-files` salen solo los 94 YAML versionados de `contracts/`, ninguno de `.venv`: pasa |
| 3 | El AST no cambia | `python3 -I -c` propio: `ast.dump` de `git show feat/b1-contratos:<f>` contra `HEAD:<f>` para cada `.py` del diff. También comprueba que los bytes sí cambiaron y que el worktree es igual a HEAD | 70 `.py`, todos de `contracts/src` y `contracts/tests`. AST distintos: ninguno. Archivos sin cambio de bytes: ninguno. Worktree distinto de HEAD: ninguno. Pasa |
| 4 | Los datos no cambian | `uv run … --directory …/contracts python -I -c` propio. Compara base contra HEAD con `load_yaml_text` y con `yaml.safe_load` (PyYAML 6.0.4), por igualdad y por `json.dumps` sin ordenar claves, así que ve también el orden de las claves y los tipos (1, 1.0 y true) | 11 YAML, los 11 IGUAL, también `results.v2.yaml` con su `>-`. Pasa |
| 5 | Suite, tipos, lint, generados y V-GUARD | `timeout 60 uv run … pytest -q -p no:cacheprovider`; `mypy --strict src`; `ruff check .`; `gen_ts --check`; `gen_jcs_vectors --check`; el comando literal del Paso 5 (`coverage report --include=… --fail-under=100`) | 2903 pasadas en 30,99 s con 97,93 % de cobertura; mypy sin errores en 48 archivos; `All checks passed!`; 4 archivos al día; vectores al día; guardias al 100 % de ramas (3000 sentencias y 1430 ramas). Pasa |
| 6 | Guardias y diff | `pytest tests/checks/test_ci_workflows.py --no-cov`; `bash /workspace/.worktrees/U01-T28/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T28`; `bash …/check-no-insumos.sh /workspace/.worktrees/U01-T28`; `git -C … diff --name-only feat/b1-contratos...HEAD` | 79 pasadas, entre ellas `test_los_workflows_reales_…`, que corre la guardia sobre los workflows reales; `0 apariciones en …/U01-T28/.github …/U01-T28/scripts`, desde el worktree; `0 apariciones`; el diff tiene solo archivos permitidos. Pasa |

## Comprobaciones pedidas
- **Rojo en la base.** `/workspace` está en d2adcdf y limpio en `contracts/`. En la base, `ruff format --check` sale con código 1 y muchos archivos sin formato, y `yamllint -s -f parsable` sobre `errors`, `queues`, `analyzer` y `profiles` sale con código 1. Los errores de llaves y de largo de línea están en los 11 archivos que nombra la bitácora: el rojo existía.
- **Scripts del codificador.** `ca3.py` y `ca4.py` comparan de verdad `feat/b1-contratos:<f>` contra `HEAD:<f>` y cubren todos los `.py` y YAML de `contracts/` del diff. Sus cuentas (70 y 11) coinciden con las mías.
- **`ignore:`.** No se come ningún archivo versionado: `git ls-files` no tiene nada bajo `.venv`, `build/` ni `node_modules`. Comprobé que `ignore:` también filtra los archivos pasados de forma explícita, como hace el *pre-commit*: un YAML de `.venv` pasado así se descarta y `results.v2.yaml` se conserva. Lo que el *pre-commit* pasa son siempre archivos versionados, así que no pierde ninguno. `.github/` (los 3 YAML), `.pre-commit-config.yaml` y `.yamllint.yaml` siguen en la lista.
- **Paso 6d.** Lo corrí tal cual desde la raíz del worktree con `env --chdir=/workspace/.worktrees/U01-T28 uv run --frozen --offline --project contracts yamllint -s -c .yamllint.yaml contracts/`: sin salida y código 0.
  - yamllint 1.38.0 viene de `uv.lock` (línea 1843; el grupo de desarrollo de `pyproject.toml` lo pide con `>=1.35`). El Paso 1 instala el entorno con `uv sync --frozen`, así que el paso no añade red.
  - Con `--project`, el directorio de trabajo sigue siendo la raíz, donde vive `.yamllint.yaml`.
  - El paso no trae `uses:` nuevos ni cambia permisos, y la guardia `ci_workflows` sigue en verde.
- **README.** La fila V-LINT describe fielmente los pasos 6b y 6c, y el párrafo nuevo cita literalmente el comando del 6d. La fila V-YAML no cambió. `test_readme.py` solo pasó por `ruff format` (su AST es igual) y sigue en verde con 229 pasadas.
- **Lógica intacta.** El diff (`--stat`) tiene 70 `.py` con el mismo AST, 11 YAML con los mismos datos, el *workflow*, el *pre-commit*, `.yamllint.yaml`, el README y la bitácora. No toca ningún `*.json`, `SHA256SUMS`, `*.sha256`, `contracts/ts`, `pyproject.toml`, `uv.lock`, `libs/`, `scripts/`, `docs/validacion-zine/`, `repo-level0.yml` ni `hatch_build.py`. `SHA256SUMS` cubre solo `entrada.schema.json` y `salida.schema.json`, y ninguno cambió. Revisé a mano `run.valid.yaml`, `salida.valid.yaml`, `analyzer-profile.extra-role.yaml` y `error-codes.v2.yaml`: los mapas de flujo pasan a bloque y se quitan los espacios dentro de las llaves, nada más.

## Hallazgos
### F-01 · AMARILLO · .pre-commit-config.yaml:14 · `ruff-format` del *pre-commit* abarca más que la CI
El gancho no tiene `files:`, así que formatea todo `.py` del repositorio, mientras que el Paso 6c solo mira `contracts/`. `ruff format --check /workspace/.worktrees/U01-T28/docs/validacion-zine /workspace/.worktrees/U01-T28/libs/errors` da «6 files would be reformatted»: los 6 de `docs/validacion-zine/`, que son de T27. El primer commit que toque esos archivos se encontrará con el gancho reescribiéndolos. La tarea pedía el gancho tal cual, así que no es un desborde.

### F-02 · AMARILLO · docs/loop/bitacoras/U01-T28.md:33,38-39 · La bitácora no es exacta
- Dice que `test_readme.py` «no se tocaron», pero el diff lo incluye (reformateado, con el mismo AST).
- CA-3 y CA-4 se corrieron con scripts y no con el `python -c` que pide la tarea.
- `ca4.py` compara solo con `==`, que no distingue 1, 1.0 y true. Mi comprobación cubre ese hueco.

### F-03 · AMARILLO · .yamllint.yaml:6-9 · `contracts/build/` solo vale con rutas relativas a la raíz
En la sintaxis de gitignore, un patrón con barra en medio queda anclado al inicio de la ruta. Con rutas absolutas, como en CA-2, no coincidiría con `contracts/build/`. Hoy no hay YAML bajo `build/`, y en la CI (rutas relativas) sí coincide. `.venv/` y `node_modules/` coinciden en cualquier nivel.

## Tareas candidatas (defectos reales fuera de alcance)
- Formatear con `ruff format` los 6 `.py` de `docs/validacion-zine/`, o acotar los ganchos `ruff-check` y `ruff-format` a `^(contracts|libs)/`, para que el *pre-commit* y la CI cubran lo mismo. Va después de T27 o dentro de ella, porque esos archivos son de T27.

```
VEREDICTO: VERDE
AMARILLO|.pre-commit-config.yaml:14|ruff-format del pre-commit formatea todo el repositorio, mientras la CI solo mira contracts/ (6 archivos de docs/validacion-zine sin formato)
AMARILLO|docs/loop/bitacoras/U01-T28.md:33|La bitácora dice que test_readme.py no se tocó, y CA-3 y CA-4 se corrieron con scripts y no con python -c
AMARILLO|.yamllint.yaml:6-9|ignore contracts/build/ solo coincide con rutas relativas a la raíz
INFORME: docs/loop/revisiones/U01-T28/ronda-1.md
```
