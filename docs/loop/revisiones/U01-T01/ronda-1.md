# Ronda 1 — U01-T01

VEREDICTO: NO-VERDE

Revisé el commit `88b64ba` de la rama `tarea/U01-T01` contra `feat/b1-contratos`. Son 28 archivos y un solo commit: `chore(contracts): esqueleto del paquete y ejecutor de pruebas (T01)`. Corrí los siete criterios y todos pasan. Aun así hay dos defectos NARANJA en el mapa de rutas del paso 1.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | El lockfile coincide con `pyproject.toml` | `uv lock --check --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Resolved 78 packages», código 0 |
| CA-2 | La instalación reproducible funciona | `uv sync --frozen --directory /workspace/.worktrees/U01-T01/contracts` | pasa: «Checked 77 packages», código 0 |
| CA-3 | El ejecutor bloquea la red | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest tests/test_runner.py --no-cov` | pasa: `2 passed, 1 warning in 0.01s`. La prueba espera la `SocketBlockedError` real de `pytest_socket` |
| CA-4a | mypy estricto | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts mypy --strict src python` | pasa: `Success: no issues found in 4 source files` |
| CA-4b | Ruff | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts ruff check .` | pasa: `All checks passed!` |
| CA-5 | La configuración de pytest declara red bloqueada y cobertura con ramas | `grep -n -E "disable-socket\|cov-branch\|cov-fail-under=80" /workspace/.worktrees/U01-T01/contracts/pyproject.toml` | pasa: las tres opciones, en la línea 74 |
| CA-6a | LF forzado en `contracts/` | `git -C /workspace/.worktrees/U01-T01 check-attr eol -- contracts/pyproject.toml` | pasa: `eol: lf` |
| CA-6b | `.gitignore` cubre lo sensible | `git -C /workspace/.worktrees/U01-T01 check-ignore -v .env x.pem x.key kubeconfig secrets-x.yaml .worktrees/a build/a` | pasa: las 7 rutas aparecen ignoradas |
| CA-7 | No se rompió `repo-level0` | `bash /workspace/.worktrees/U01-T01/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T01` | pasa: `0 apariciones` |

**Evidencia y orden de pruebas:** la bitácora coincide con mis corridas y sale del diff actual. El Testing Contract solo pide aquí `runner_ready_before_first_test`, sin un par rojo-verde obligatorio, y la bitácora registra el estado anterior al cambio. **Alcance:** sin desborde; no hay contratos, *loaders*, CI ni *pre-commit*. **Reglas de la app:** no encontré ninguna violación ni datos del piloto. **Umbrales:** el diff no baja ninguno, porque el archivo es nuevo. **Worktree:** sigue limpio; mis corridas solo dejaron rutas ignoradas (`.coverage`, cachés y `.venv`).

## Hallazgos

### F-01 · NARANJA · contracts/pyproject.toml:35-54 · El mapa de rutas de D1/D15 solo funciona en la rueda; en el entorno editable no existe

Sobre tu pregunta (2): **es un defecto dentro del alcance de T01**, no una tarea candidata.

El paso 1 pide «`python/` a la raíz del paquete» según functional-spec §1, que convierte `python/<módulo>.py` en `veridicus_contracts.<módulo>`. Todas las suites del plan corren con `uv run --directory contracts` sobre la instalación editable de `uv sync`: V-SUITE, los pasos 3 a 20 y V-GUARD. La instalación editable de hatchling solo añade `src/` al `sys.path` mediante el `.pth`, y no hace nada con `force-include`. Lo comprobé así:

- `uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts python -c "import veridicus_contracts._skeleton"` termina con `ModuleNotFoundError: No module named 'veridicus_contracts._skeleton'` y código 1.
- `.../site-packages/_editable_impl_veridicus_contracts.pth` contiene solo `/workspace/.worktrees/U01-T01/contracts/src`.
- `uv run ... python -c "import importlib.resources as r; import veridicus_contracts as v; print(v.__file__); print(sorted(p.name for p in r.files(v).iterdir()))"` responde `.../contracts/src/veridicus_contracts/__init__.py` y `['__init__.py', '__pycache__', 'checks', 'py.typed', 'tools']`.

La lista no incluye `api/`, `analyzer/` ni `_skeleton.py`: en el entorno de desarrollo no hay ni módulos de `python/` ni datos. Hatchling además copió los `force-include` de datos a `site-packages/veridicus_contracts/` como una foto fija, y esa copia ya está desactualizada: tiene un `.gitkeep` en la raíz y le falta `_skeleton.py`. Tampoco se puede alcanzar, porque el paquete regular de `src/` le gana a ese directorio, que no tiene `__init__.py`.

**Consecuencia:** la verificación del paso 3 (T02) importa `veridicus_contracts.registry` y `veridicus_contracts.canonical`, así que fallaría. La V-GUARD del plan mide `python/profiles.py` y otros por ruta de archivo, lo que da por hecho que los módulos se cargan desde `python/` en desarrollo. Ningún criterio de T01 lo detecta, porque CA-4 corre mypy sobre directorios y no sobre el paquete importado.

**Lo que se pide:** que el mapa funcione también en el entorno editable, en `pyproject.toml` y sin lógica de negocio, y una prueba en `tests/test_runner.py` (o similar) que lo demuestre leyéndolo de vuelta:
- importar un módulo de `python/` como `veridicus_contracts.<módulo>`;
- encontrar un dato de un directorio mapeado con `importlib.resources.files("veridicus_contracts")`.

Opciones posibles, a elección del codificador: el modo exacto de desarrollo de hatchling, o una ruta de paquete que incluya `python/` y la raíz de `contracts/`. Tiene que comprobarlo corriendo.

### F-02 · NARANJA · contracts/pyproject.toml:37 · `exclude = ["**/fixtures/**"]` no se aplica a `force-include`: los *fixtures* entrarían en la rueda

El paso 1 y functional-spec §1 exigen que `*/fixtures/` no se empaquete, y el comentario de la línea 33 lo afirma. Pero hatchling no aplica `exclude` a las rutas forzadas: `recurse_forced_files` en `hatchling/builders/plugin/interface.py:218-245` solo filtra `EXCLUDED_DIRECTORIES` y `EXCLUDED_FILES`. Lo demostré corriendo sobre una copia en el scratchpad, sin tocar el worktree:

- `cp -r /workspace/.worktrees/U01-T01/contracts /tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/copia-contracts`
- `mkdir -p .../copia-contracts/api/fixtures` y `touch .../copia-contracts/api/fixtures/sintetico.yaml`
- `uv build --wheel --offline --directory .../copia-contracts --out-dir .../scratchpad/wheel2`
- `unzip -l .../wheel2/veridicus_contracts-0.1.0-py3-none-any.whl veridicus_contracts/api/*` lista **`veridicus_contracts/api/fixtures/sintetico.yaml`**.

Hoy no hay *fixtures*, pero T03 los crea bajo los directorios mapeados, y el mapa que pide el paso 1 es el que los deja fuera. **Lo que se pide:** excluirlos de una forma que hatchling respete de verdad, por ejemplo con `exclude` sobre rutas incluidas por `include`/`sources` en lugar de `force-include`, y una comprobación que lo demuestre construyendo la rueda.

### F-03 · AMARILLO · contracts/python/_skeleton.py · El marcador es aceptable, pero se publica como módulo

Sobre tu pregunta (1): está justificado. `mypy --strict src python` (CA-4) falla si `python/` no tiene ningún `.py`, el archivo solo trae un docstring y lleva el motivo escrito. No lo considero desborde ni un *stub* prohibido. Como queda en la rueda como `veridicus_contracts._skeleton`, T02 tiene que borrarlo; conviene decirlo en la tarea de T02.

### F-04 · AMARILLO · contracts/pyproject.toml · `limits.v1.yaml` falta en el mapa y los `.gitkeep` van dentro de la rueda

- functional-spec §1 lleva `limits.v1.yaml` a `veridicus_contracts/limits.v1.yaml`, pero `force-include` no lo incluye. Como hatchling falla con «Forced include not found» si el archivo no existe, es razonable dejarlo para T10. Que T10 lo añada.
- Los `.gitkeep` se empaquetan, como reconoce la bitácora. Desaparecerán cuando lleguen los contratos.

### Nota (no es hallazgo)

`timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T01/contracts pytest` (V-SUITE) hoy termina con código 1: `Coverage failure: total of 0 is less than fail-under=80` y «Module veridicus_contracts was never imported». Es lo esperable sin código, y el paso 2 verifica con `--no-cov`. Pero cuando F-01 esté resuelto, el `source = ["veridicus_contracts"]` de cobertura tiene que medir también los módulos de `python/`, o V-GUARD no los verá.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna. El defecto del entorno editable cae dentro de T01 (F-01).

```
VEREDICTO: NO-VERDE
NARANJA|contracts/pyproject.toml:35-54|El mapa de rutas de D1/D15 solo funciona en la rueda; en el entorno editable no existe
NARANJA|contracts/pyproject.toml:37|exclude de fixtures no se aplica a force-include: los fixtures entrarían en la rueda
AMARILLO|contracts/python/_skeleton.py|El marcador es aceptable, pero se publica como módulo
AMARILLO|contracts/pyproject.toml|limits.v1.yaml falta en el mapa y los .gitkeep van dentro de la rueda
INFORME: docs/loop/revisiones/U01-T01/ronda-1.md
```
