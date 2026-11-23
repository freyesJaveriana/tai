# Ronda 2 — U01-T01

VEREDICTO: NO-VERDE

Revisé el commit `e8a07f6` de `tarea/U01-T01` contra `feat/b1-contratos`. Los siete criterios pasan, y F-01 y F-02 quedan cerrados para la instalación editable y para `uv build --wheel`. Pero el cambio a enlaces simbólicos introduce una regresión: `uv build` sin opciones, que es el comando que nombra D15, produce un paquete al que le faltan 11 de los 13 directorios de datos.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | El lockfile coincide con `pyproject.toml` | `uv lock --check --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Resolved 78 packages» |
| CA-2 | La instalación reproducible funciona | `uv sync --frozen --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Checked 77 packages» |
| CA-3 | El ejecutor bloquea la red | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest tests/test_runner.py --no-cov` | pasa: `2 passed, 1 warning in 0.01s` |
| CA-4a | mypy estricto | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts mypy --strict src python` | pasa: `Success: no issues found in 5 source files` |
| CA-4b | Ruff | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts ruff check .` | pasa: `All checks passed!` |
| CA-5 | La configuración de pytest declara red bloqueada y cobertura con ramas | `grep -n -E "disable-socket\|cov-branch\|cov-fail-under=80" /workspace/.worktrees/U01-T01/contracts/pyproject.toml` | pasa: las tres opciones, en la línea 60 |
| CA-6a | LF forzado en `contracts/` | `git -C /workspace/.worktrees/U01-T01 check-attr eol -- contracts/pyproject.toml` | pasa: `eol: lf` |
| CA-6b | `.gitignore` cubre lo sensible | `git -C /workspace/.worktrees/U01-T01 check-ignore -v .env x.pem x.key kubeconfig secrets-x.yaml .worktrees/a build/a` | pasa: las 7 rutas |
| CA-7 | No se rompió `repo-level0` | `bash /workspace/.worktrees/U01-T01/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T01` | pasa: `0 apariciones` |
| extra | Pruebas nuevas del mapa | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest tests/test_package_map.py --no-cov -v` | pasa: 3 passed |
| extra | Suite completa (V-SUITE) | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest` | pasa: 5 passed, 100 %, y ahora mide `python/_skeleton.py` (en la ronda 1 fallaba con 0 %) |

**Rojo primero:** la bitácora registra `FFF` antes del cambio, con los tres mensajes esperados. **Alcance:** sin desborde. **Reglas de la app:** sin violaciones ni datos del piloto. **Worktree:** limpio (`git status --porcelain` no devuelve nada).

## Estado de los hallazgos de la ronda 1

- **F-01: cerrado** para la instalación editable. `veridicus_contracts._skeleton` se importa y `importlib.resources` encuentra `api/`, `analyzer/`, `queues/` y `profiles/`.
- **F-02: cerrado** para la rueda directa. Lo comprobé sobre una copia que **conserva** los enlaces: `cp -a /workspace/.worktrees/U01-T01/contracts .../scratchpad/r2copia`, más `api/fixtures/sintetico.yaml`, y `uv build --wheel --offline --directory .../r2copia --out-dir .../r2copia-w`. `unzip -l ... veridicus_contracts/api/*` solo lista `api/.gitkeep`.
- **F-03 y F-04:** siguen siendo AMARILLO y quedan anotados en «Para T02 y siguientes». Lo acepto.

## Las tres preguntas

**(a) ¿La rueda contiene archivos reales?** Sí cuando se construye directamente. `uv build --wheel --offline --directory /workspace/.worktrees/U01-T01/contracts --out-dir .../scratchpad/r2w` y luego `unzip -Z -l` dan 21 entradas, todas `-rw-r--r--` (archivos regulares, ningún enlace), con los 13 directorios. `unzip -p .../r2w/veridicus_contracts-0.1.0-py3-none-any.whl veridicus_contracts/_skeleton.py` devuelve el docstring real. **Pero no cuando se construye por el sdist** (F-05).

**(b) ¿Contradice D1/D15?** La decisión no: D15 fija hatchling y el mapa de functional-spec §1, no el mecanismo, y la alternativa que rechaza es setuptools con `MANIFEST.in`. Pasar de `force-include` a enlaces solo cambia el mecanismo. Lo que sí se rompe es el comando que D15 nombra, `uv build` seguido de la instalación en un `uv venv` nuevo, y ese es el camino de `check_package` (paso 22).

**(c) ¿Riesgo en checkouts sin enlaces simbólicos?** `git -C /workspace/.worktrees/U01-T01 config --show-origin --get-all core.symlinks` termina con código 1: no está fijado, así que manda el valor por defecto de cada plataforma.
- **CI en ubuntu y el contenedor:** el valor por defecto es `true` y `actions/checkout` conserva los enlaces. Sin riesgo.
- **Git para Windows** (clon nativo en la máquina del humano, fuera de WSL o del contenedor): el valor por defecto es `core.symlinks=false`. Cada enlace se convierte en un archivo de texto con la ruta (`../../api`) y el paquete queda roto. El fallo sería ruidoso, porque `test_directorio_de_datos_se_encuentra_con_importlib_resources` caería. Riesgo bajo si el humano trabaja siempre en el contenedor. Ver F-07.

## Hallazgos

### F-05 · NARANJA · contracts/src/veridicus_contracts/* (enlaces) · `uv build` por el sdist pierde 11 de los 13 directorios de datos

`uv build --offline --directory /workspace/.worktrees/U01-T01/contracts --out-dir .../scratchpad/r2` construye primero el sdist y luego la rueda desde ese sdist. Así lo hacen por defecto `uv build` y la instalación desde un sdist.

- `tar -tvzf .../r2/veridicus_contracts-0.1.0.tar.gz`:
  - incluye `api/`, `analyzer/`, `cli/`, `errors/`, `format/`, `health/`, `integrity/`, `metrics/`, `model_calls/`, `profiles/` y `queues/` **solo en la raíz**;
  - incluye `transcript/` y `ui/` **solo bajo `src/veridicus_contracts/`**;
  - conserva `_skeleton.py` como enlace (`lrwxr-xr-x ... -> ../../python/_skeleton.py`).

  Hatchling recorre cada directorio real una sola vez, de modo que cada directorio enlazado aparece en un único sitio según el orden alfabético.
- `unzip -Z -l .../r2/veridicus_contracts-0.1.0-py3-none-any.whl` da 10 entradas. Solo trae `transcript/.gitkeep` y `ui/.gitkeep`; **faltan `api/`, `analyzer/`, `errors/`, `queues/`, `profiles/` y los demás.**

En cuanto lleguen esquemas, `check_package` y cualquier `sistema` que instale desde el sdist recibirán un paquete sin contratos. La prueba nueva no lo detecta por dos motivos: usa `uv build --wheel` y copia el árbol con `shutil.copytree` sin `symlinks=True`, que resuelve los enlaces, así que no ejercita el mecanismo real.

**Lo que se pide:** que `uv build` (sdist y luego rueda) produzca la misma rueda que `uv build --wheel`, y una prueba que lo demuestre construyendo por las dos vías sobre una copia que **conserve** los enlaces (`symlinks=True`). La prueba debe exigir que estén los 13 directorios del mapa y ningún `/fixtures/`. El mecanismo lo elige el codificador.

### F-06 · AMARILLO · contracts/src/veridicus_contracts/ · Cada módulo o directorio nuevo necesita un enlace a mano, y nada comprueba que exista

La bitácora lo deja anotado para T02 y siguientes, pero ninguna prueba lo vigila. Un directorio de datos sin enlace desaparecería del paquete sin que falle nada, a menos que alguna prueba lo lea. Conviene una prueba de inventario: cada `python/*.py` y cada directorio del mapa de §1 tiene su enlace en `src/veridicus_contracts/` y resuelve a un destino existente.

### F-07 · AMARILLO · .gitattributes / documentación · Checkout en Windows con `core.symlinks=false`

Conviene documentar en el README de `contracts/` que el repositorio exige soporte de enlaces simbólicos (WSL o el contenedor, o `core.symlinks=true` con permisos de enlace en Windows). Mejor aún, una comprobación temprana con un mensaje claro en lugar de un `is_dir()` fallido.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/* (enlaces)|uv build por el sdist pierde 11 de los 13 directorios de datos
AMARILLO|contracts/src/veridicus_contracts/|Cada módulo o directorio nuevo necesita un enlace a mano, y nada comprueba que exista
AMARILLO|.gitattributes / documentación|Checkout en Windows con core.symlinks=false
INFORME: docs/loop/revisiones/U01-T01/ronda-2.md
```
