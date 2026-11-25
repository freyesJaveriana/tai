# Ronda 3 — U01-T01

VEREDICTO: NO-VERDE

Revisé el commit `9f47870` de `tarea/U01-T01` contra `feat/b1-contratos`. Los siete criterios pasan. F-05, F-06 y F-07 quedan cerrados: las dos vías de construcción dan la misma rueda y ya no hay enlaces simbólicos. Pero mypy no ve el mapa de rutas: cuando un módulo importa `veridicus_contracts.<módulo de python/>`, `mypy --strict src python` falla. La regla V-TYPES de las tareas siguientes se rompería en la primera importación cruzada.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | El lockfile coincide con `pyproject.toml` | `uv lock --check --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Resolved 78 packages» |
| CA-2 | La instalación reproducible funciona | `uv sync --frozen --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Checked 77 packages» |
| CA-3 | El ejecutor bloquea la red | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest tests/test_runner.py --no-cov` | pasa: `2 passed, 1 warning in 0.01s` |
| CA-4a | mypy estricto | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts mypy --strict src python` | pasa: `Success: no issues found in 4 source files` (pero ver F-08) |
| CA-4b | Ruff | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts ruff check .` | pasa: `All checks passed!` |
| CA-5 | La configuración de pytest declara red bloqueada y cobertura con ramas | `grep -n -E "disable-socket\|cov-branch\|cov-fail-under=80" /workspace/.worktrees/U01-T01/contracts/pyproject.toml` | pasa: línea 97 |
| CA-6a | LF forzado en `contracts/` | `git -C /workspace/.worktrees/U01-T01 check-attr eol -- contracts/pyproject.toml` | pasa: `eol: lf` |
| CA-6b | `.gitignore` cubre lo sensible | `git -C /workspace/.worktrees/U01-T01 check-ignore -v .env x.pem x.key kubeconfig secrets-x.yaml .worktrees/a build/a` | pasa: las 7 rutas |
| CA-7 | No se rompió `repo-level0` | `bash /workspace/.worktrees/U01-T01/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T01` | pasa: `0 apariciones` |
| extra | Suite completa (V-SUITE) | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest` | pasa: 8 passed, 87,10 %. `__init__.py` queda en 87 % porque no se cubren 2 ramas (ver F-09) |

**Rojo primero:** la bitácora registra los dos fallos previos por la vía sdist. **Enlaces:** `git -C ... ls-files -s contracts/src` solo lista archivos `100644`, ningún `120000`. **Alcance y reglas de la app:** sin desborde y sin violaciones. **Worktree:** limpio.

## Las tres preguntas

**(a) Las dos vías de construcción y la instalación limpia: pasan.** Trabajé sobre una copia en `.../scratchpad/r3` (`cp -a`) con `api/fixtures/sintetico.yaml` añadido.
- `uv build --offline --directory .../r3 --out-dir .../r3-sdist` y `uv build --wheel --offline --directory .../r3 --out-dir .../r3-wheel`: `unzip -Z1` da **las mismas 21 entradas** en las dos ruedas, con los 13 directorios, `_skeleton.py` y ninguna ruta `/fixtures/`.
- Creé `uv venv --offline --python 3.12 .../venv-r3` e instalé con `uv pip install --offline --no-deps --python .../venv-r3/bin/python .../r3-sdist/veridicus_contracts-0.1.0-py3-none-any.whl`.
- `.../venv-r3/bin/python -I -c "..."` muestra:
  - `__file__` en `site-packages/veridicus_contracts/__init__.py`;
  - `__path__` con **una sola** entrada;
  - un cargador `SourceFileLoader`, es decir, el `__init__` **no se activó**;
  - `_skeleton` importado desde `site-packages`;
  - `files()` con los 13 directorios de datos más `checks` y `tools`.

**(b) ¿El `__init__.py` de desarrollo es robusto?**
- **En tiempo de ejecución, robusto lo suficiente.** La condición de activación (que existan `python/` y `pyproject.toml` dos niveles arriba del paquete) no se cumple en `site-packages`, porque allí esa ruta es `lib/python3.12`, y lo comprobé arriba.
- **Puntos frágiles (AMARILLO, F-09):**
  - usa `importlib.resources.readers.MultiplexedPath`, un módulo que no está documentado como API pública;
  - sustituye `__spec__.loader` después de importar, cosa que `importlib.resources` respeta en 3.12;
  - `requires-python = ">=3.12"` no pone techo de versión;
  - la rama «rueda instalada» no tiene ninguna prueba automática (la cobertura muestra 2 ramas sin cubrir).
- **Cobertura de V-GUARD por ruta:** funciona. Coverage reporta `python/_skeleton.py` con su ruta real, así que `--include=python/<módulo>.py` lo verá.
- **mypy:** **no funciona**; ver F-08.

**(c) ¿Es lógica fuera de alcance?** No lo considero desborde. Es la configuración del mapa que pide el paso 1 (D1/D15) para el entorno de desarrollo, no tiene comportamiento de contratos, y la tarea ya permitía un `__init__.py`. Es un mecanismo con efectos al importar, así que debe estar probado en sus dos ramas (F-09).

## Hallazgos

### F-08 · NARANJA · contracts/pyproject.toml:77-80 y el mapa python/ → veridicus_contracts · mypy no resuelve `veridicus_contracts.<módulo de python/>`

El `__path__` se amplía al importar, y mypy analiza el código sin ejecutarlo, así que no lo ve. En la copia `.../scratchpad/r3` creé `python/demo.py` (`def f() -> int`) y `src/veridicus_contracts/usa.py` (`from veridicus_contracts.demo import f`) y corrí:

`uv run --frozen --offline --directory .../scratchpad/r3 mypy --strict src python`

```
src/veridicus_contracts/usa.py:1: error: Cannot find implementation or library stub for module named "veridicus_contracts.demo"  [import-not-found]
src/veridicus_contracts/usa.py:5: error: Returning Any from function declared to return "int"  [no-any-return]
Found 2 errors in 1 file (checked 6 source files)
```

El mismo fallo aparecerá cada vez que algo en `src/` o en `python/` importe un módulo de `python/` por el nombre del paquete. Además, mypy analiza `python/<x>.py` como módulo de primer nivel, así que una importación relativa (`from .canonical import …`) tampoco se resolvería. El plan lo necesita: `checks/` usa `profiles`/`limits`, y los módulos de `python/` se importan entre sí. CA-4 pasa hoy solo porque todavía no hay importaciones cruzadas: es la misma clase de defecto que F-01, el mapa invisible para una herramienta de desarrollo, ahora en el verificador de tipos.

**Lo que se pide:** que `mypy --strict` resuelva el mapa, con una prueba o comprobación que lo demuestre con una importación cruzada real en el árbol. Si no hay forma de hacerlo sin mover `python/` dentro de `src/veridicus_contracts/` (que cambia las rutas aprobadas de functional-spec §1 y de V-GUARD), **lo decide el humano**: o se precisa el mapa, o se acepta la limitación como tarea candidata con aviso explícito a T02 y siguientes. El codificador no debe resolverlo cambiando rutas por su cuenta.

### F-09 · AMARILLO · contracts/src/veridicus_contracts/__init__.py · La rama «rueda instalada» no tiene prueba y depende de APIs poco estables

La rama de salida temprana (línea 43) y el caso `spec is None` no están cubiertos. La no activación en `site-packages` solo la demostré yo a mano (en (a)). Conviene:
- una prueba que instale la rueda en un venv temporal y compruebe `len(__path__) == 1` y que el cargador no se sustituyó;
- dejar anotada en el docstring la dependencia de `importlib.resources.readers.MultiplexedPath` y de Python 3.12.

### F-10 · AMARILLO · contracts/tests/test_package_map.py:14, 49-50 · Comentario obsoleto y aserción tautológica

- La línea 14 dice «limits.v1.yaml lo añade T10 junto con su enlace», pero ya no hay enlaces.
- Las líneas 49-50 comprueban `is_file()` sobre lo que devuelve `glob("*.py")`, que siempre es verdad. Eso no prueba nada del mapa de `python/`.

## Tareas candidatas (defectos reales fuera de alcance)
- `vendor/` queda en `NO_EMPAQUETADOS` y functional-spec §1 no lo mapea, pero el paso 3 hace que `registry` recorra los esquemas «incluido `vendor/`». En la rueda instalada no estarán los meta-esquemas. Hay que revisar el mapa en T02 o T21 (`check_package`).

```
VEREDICTO: NO-VERDE
NARANJA|contracts/pyproject.toml:77-80 y mapa python/ → veridicus_contracts|mypy no resuelve veridicus_contracts.<módulo de python/> en importaciones cruzadas
AMARILLO|contracts/src/veridicus_contracts/__init__.py|La rama «rueda instalada» no tiene prueba y depende de APIs poco estables
AMARILLO|contracts/tests/test_package_map.py:14, 49-50|Comentario obsoleto y aserción tautológica
INFORME: docs/loop/revisiones/U01-T01/ronda-3.md
```
