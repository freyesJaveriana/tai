# Ronda 4 — U01-T01

VEREDICTO: VERDE

Revisé `tarea/U01-T01` en `1b6579e` contra `feat/b1-contratos` (`5171a2f`, igual que `origin`), con la tarea actualizada: su sha256 `f6c8cf0e…dedff8` coincide. Corrí CA-1 a CA-8 yo mismo y todos pasan. No queda ningún ROJO ni NARANJA; dejo tres AMARILLO para tareas posteriores.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | El lockfile coincide con `pyproject.toml` | `uv lock --check --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Resolved 78 packages» |
| CA-2 | La instalación reproducible funciona | `uv sync --frozen --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Checked 77 packages» |
| CA-3 | El ejecutor bloquea la red | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest tests/test_runner.py --no-cov` | pasa: `2 passed, 1 warning in 0.01s` |
| CA-4a | mypy estricto | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts mypy --strict src` | pasa: `Success: no issues found in 2 source files` |
| CA-4b | Ruff | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts ruff check .` | pasa: `All checks passed!` |
| CA-5 | La configuración de pytest declara red bloqueada y cobertura con ramas | `grep -n -E "disable-socket\|cov-branch\|cov-fail-under=80" /workspace/.worktrees/U01-T01/contracts/pyproject.toml` | pasa: línea 123 |
| CA-6a | LF forzado en `contracts/` | `git -C /workspace/.worktrees/U01-T01 check-attr eol -- contracts/pyproject.toml` | pasa: `eol: lf` |
| CA-6b | `.gitignore` cubre lo sensible | `git -C /workspace/.worktrees/U01-T01 check-ignore -v .env x.pem x.key kubeconfig secrets-x.yaml .worktrees/a build/a` | pasa: las 7 rutas |
| CA-7 | No se rompió `repo-level0` | `bash /workspace/.worktrees/U01-T01/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T01` | pasa: `0 apariciones` |
| CA-8 | El mapa es el mismo en desarrollo y en la rueda | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest tests/test_package_map.py --no-cov -v` | pasa: 7 passed (inventario, subpaquetes, datos en la instalación editable, rueda directa, rueda por sdist, las dos idénticas, mypy con importación cruzada) |
| extra | Suite completa (V-SUITE) | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest` | pasa: 9 passed, 100 % |

**Rojo primero:** la bitácora registra `2 failed, 4 passed` antes del cambio y explica por qué la prueba de mypy ya nace en verde con PD-9. **Reglas de la app:** sin violaciones ni datos del piloto. **Worktree:** limpio.

## Lo que pediste evaluar

**(a) ¿Es aceptable el paquete de espacios de nombres?** Sí. Verifiqué los puntos de riesgo corriendo:
- **PEP 561 para un consumidor con mypy.** Construí desde una copia `git archive` con un `uno.py` tipado, la instalé en `.../scratchpad/venv-r4` y corrí `/workspace/.worktrees/U01-T01/contracts/.venv/bin/mypy --strict --no-incremental --config-file= --python-executable .../venv-r4/bin/python .../consumidor.py`:
  - con un error de tipos puesto a propósito: `Incompatible return value type (got "int", expected "str")`, código 1;
  - con el consumidor corregido: `Success`.

  mypy ve el paquete instalado como tipado.
- **Rueda instalada.** `.../venv-r4/bin/python -I -c "..."` muestra `_NamespacePath` con una sola entrada en `site-packages`, `uno.valor()` responde 1 y `files()` lista los 13 directorios más `py.typed`, `checks` y `tools`. La rueda no trae `/fixtures/` aunque la copia tenía `api/fixtures/sintetico.yaml`.
- **Cobertura:** `source = ["veridicus_contracts"]` mide `src/veridicus_contracts/*` (la tabla de la suite lo muestra).
- **`__version__` y `__init__`:** ni el plan ni PD-9 los piden; el paso 1 solo nombra `checks/`, `tools/` y `py.typed`.
- **import-linter de U4:** no está en este entorno y no lo pude correr. Para U4, `veridicus_contracts` es un paquete externo, así que el riesgo es bajo. U4 debe confirmarlo al configurar sus contratos.

**(b) ¿La copia editable se mantiene al día?** Con `uv run`, sí. Fuera de `uv run`, no. Lo comprobé sobre una copia limpia: `git archive`, `tar -xf` y `uv sync --frozen --offline`.
- Dato nuevo en un **subdirectorio nuevo** (`api/v9/esquema.yaml` = `uno`): `uv run --frozen --offline ...` reconstruye y lee `version: uno`. El glob `api/**` cubre los subdirectorios nuevos.
- Cambio a `dos`:
  - `.venv/bin/python -c ...` sigue leyendo **`version: uno`** (dato viejo);
  - `uv run --frozen --offline --no-sync ...` también lee **`version: uno`**;
  - `uv run --frozen --offline ...` reconstruye y lee `version: dos`.
- Borrado: `uv run` reconstruye y `is_file()` da `False`.
- Un *fixture* nuevo provoca la reconstrucción, pero `files()/'api'/'fixtures'` da `False`, así que no entra en la copia editable.

¿Puede dar un verde falso? Con los comandos del plan y de las tareas, que siempre usan `uv run` sin `--no-sync`, no. Sí puede ocurrir con un IDE, con `.venv/bin/pytest` o con `--no-sync`. Ver F-11.

**(c) ¿El diff revierte algo de la rama del Bolt?** No. `git diff --stat feat/b1-contratos tarea/U01-T01` (dos puntos) es idéntico al de tres puntos: 31 archivos y 2267 inserciones, sin borrados. El merge `9408e9e` trae la rama del Bolt sin revertir nada.

**(d) ¿`hatch_build.py` tiene comportamiento fuera de alcance?** No. Solo actúa cuando `version == "editable"`, lee `sources` de `pyproject.toml` y añade archivos a `force_include_editable` sin `fixtures/`. No usa red ni escribe fuera de la construcción. Es la configuración del mapa que pide el paso 1 (PD-9). Su supresión `type: ignore[type-arg]` lleva su motivo.

## Hallazgos

### F-11 · AMARILLO · contracts/pyproject.toml:80-98 · La copia editable solo se refresca con `uv run`, y el inventario no vigila `cache-keys`

- Con `.venv/bin/python`, un IDE o `uv run --no-sync`, los datos editados se leen viejos (demostrado arriba). Conviene una nota en el README de `contracts/` y en `unit-test-instructions.md`: «correr siempre con `uv run`, sin `--no-sync`».
- `test_inventario_del_mapa_coincide_con_el_arbol_y_con_pyproject` compara el árbol con `include` y `sources`, pero no con `[tool.uv] cache-keys`. Un directorio de datos nuevo registrado en los dos primeros pero no en `cache-keys` dejaría su copia editable congelada sin que nada falle. Conviene añadir esa comparación.

### F-12 · AMARILLO · contracts/hatch_build.py:31 · El hook ignora las entradas de `sources` que son archivos sueltos (aviso para T10)

`(raiz / nombre).rglob("*")` sobre un archivo devuelve una lista vacía. Lo comprobé con `python3 -I -c "from pathlib import Path; print(list(Path('/workspace/.worktrees/U01-T01/contracts/pyproject.toml').rglob('*')))"`, que da `[]`. Cuando T10 añada `limits.v1.yaml` a `include` y `sources`, ese archivo estará en la rueda pero **no** en la instalación editable, y tampoco tendrá entrada en `cache-keys`. T10 debe tratar los archivos sueltos en el hook, añadirlo a `cache-keys` y probarlo con `files()`.

### F-13 · AMARILLO · Tarea candidata de la ronda 3 · `vendor/` sigue sin mapa en la rueda

Queda anotado en la bitácora para T02 y T21. Lo repito para que no se pierda.

## Tareas candidatas (defectos reales fuera de alcance)
- `vendor/` en la rueda (meta-esquemas que necesita `registry` en el paso 3): T02 o T21.

```
VEREDICTO: VERDE
AMARILLO|contracts/pyproject.toml:80-98|La copia editable solo se refresca con uv run, y el inventario no vigila cache-keys
AMARILLO|contracts/hatch_build.py:31|El hook ignora las entradas de sources que son archivos sueltos (aviso para T10)
AMARILLO|tarea candidata de la ronda 3|vendor/ sigue sin mapa en la rueda
INFORME: docs/loop/revisiones/U01-T01/ronda-4.md
```
