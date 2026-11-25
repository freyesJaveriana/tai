# Ronda 2 — U01-T08

VEREDICTO: VERDE

Los cuatro hallazgos de la ronda 1 están cerrados (F-05 lo retiró el orquestador y no lo cuento). No queda ningún ROJO ni NARANJA, y todos los criterios pasan con mis propias corridas. Quedan tres AMARILLO, que no bloquean.

Revisé `tarea/U01-T08` en 8e05132 (el merge es aaaf381) frente a `feat/b1-contratos` en 3f7659b. El worktree quedó limpio (`git -C /workspace/.worktrees/U01-T08 status --porcelain` no devuelve nada).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 10 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T08/contracts pytest tests/typing tests/checks/test_protocol_surface.py tests/contracts/test_model_call.py --no-cov -q -p no:cacheprovider` | pasa, 44 passed |
| 1b | Paso 10 (tipos) | `uv run --frozen --offline --directory …/contracts mypy --strict src` | `Success: no issues found in 11 source files` |
| 2 | Guardias c13 | `timeout 60 uv run … pytest tests/guards -m c13 --no-cov --deselect "tests/guards/test_autonomia_03.py::test_ningun_nombre_ni_enum_declara_veracidad[c13-llamada]" -q -p no:cacheprovider` | pasa, 3 passed, 55 deselected |
| 3 | 100 % de ramas en la guardia | `timeout 120 uv run … pytest tests/typing tests/checks/test_protocol_surface.py --cov-fail-under=0 -q -p no:cacheprovider` y luego `uv run … coverage report --include=src/veridicus_contracts/checks/protocol_surface.py --fail-under=100 --show-missing` | pasa: 36 passed; 84 sentencias y 40 ramas, 0 sin cubrir, 100 % |
| 4 | Datos en la editable y en la rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa, 7 passed |
| 5 | Tipos y *lint* | `mypy --strict src` y `uv run … ruff check .` | `Success…` y `All checks passed!` |
| 6 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T08/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T08` | `0 apariciones`, código 0 |

**Lectura de vuelta (CA-4), fresca sobre 8e05132.** Construí la rueda con `git archive 8e05132 contracts` y `uv build --wheel --offline` en el scratchpad, la extraje y la importé con `python3 -I`.
- **Rueda:** `model_calls` resuelve a `model_calls.py`, los dos YAML se ven por `importlib.resources.files("veridicus_contracts") / "model_calls"`, la tabla trae sus 3 filas y `comprobar()` da `[]`.
- **Editable:** el mismo script en el venv del worktree da lo mismo.

**Diff.** `git diff --stat feat/b1-contratos...tarea/U01-T08` muestra solo archivos de T08 y sus dos bitácoras.
- **Merge:** `git diff --stat aaaf381^2 aaaf381` muestra solo T08, así que el merge no revierte nada.
- **Lo que parece borrado:** el diff de dos puntos muestra `docs/loop/revisiones/U01-T09/ronda-3.md` como borrado, pero no es una reversión. Es el único commit que la rama del Bolt sumó después del merge (3f7659b).
- **Fusión:** `git merge-tree --write-tree feat/b1-contratos tarea/U01-T08` fusiona sin conflictos.
- **Archivos compartidos:** no se tocan `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `helpers.py` ni `checks/__init__.py`.

## Estado de los hallazgos de la ronda 1

**F-01 · cerrado.** Pasé cada variante por `comprobar_fuente` en un proceso aparte (`uv run … python -c …`):
- **herencia:** `… debe heredar solo de Protocol, no de: _Listo, Protocol (BR9.9, E43)`
- **@staticmethod:** `generate lleva decoradores: @staticmethod (BR9.9, E43)`
- **`__import__('os')`:** `llamada dinámica de importación: __import__ (E43)`
- **`importlib.import_module('os')`:** `llamada dinámica de importación: importlib.import_module (E43)`
- **Alias:** `import importlib as il` con `il.import_module(...)`, y `from importlib import import_module as im`, dan los dos `importa fuera del paquete de contratos: importlib (E43)`.
- **Control:** el `model_calls.py` real da `[]`.
- **Rojo primero:** la bitácora trae el rojo de las cinco pruebas nuevas (5 failed, 26 passed).

**F-02 · cerrado.** Con los mismos scripts de mutación (`mutar.py` y `lanzar_mutante.py`, en el scratchpad) sobre la guardia nueva salen 162 mutantes, incluidos los de las líneas nuevas. El control con el original da 31 passed. Mueren 156 y sobreviven 6.
- **Los nueve que pediste mueren:** `comprobar` → `[]`, quitar `veridicus_contracts` o `enum` de la lista de permitidos, quitar `typing.Protocol` y alterar `split('.')`. También mueren los de las líneas nuevas 37-40, 46-50, 70-73 y 83-85.
- **Vivos equivalentes:**
  - El `continue` de la línea 50: un `Call` no es `Import`, así que el `else` hace `continue` igual.
  - Los dos de la anotación `dict[str, ast.ClassDef]` (línea 103).
- **Vivo casi equivalente:** el `continue` de la línea 55. Solo duplica reportes de importaciones anteriores, o hace fallar la guardia con `UnboundLocalError` si la relativa va primero. Nunca oculta un problema.
- **Vivos de solo texto (ver A-02):** los separadores de las líneas 78 y 84.

**F-03 · cerrado.** Los 22 negativos comparan el mensaje exacto con `in comprobar_fuente(...)`, ID de regla incluido, y la firma se compara entera con `_firma_mala`.

**F-04 · cerrado.** `ModelCall.provider` pasa a ser `Provider`, y el docstring documenta que los opcionales `None` se omiten al serializar. mypy estricto da verde.

## Hallazgos de esta ronda

### A-01 · AMARILLO · contracts/src/veridicus_contracts/checks/protocol_surface.py:37-40 · La importación dinámica sin sentencia `import` sigue pasando
`m = __builtins__.__import__('os')` y `getattr(__builtins__, '__imp' + 'ort__')('os')` dan `[]`. La guardia compara el nombre exacto `__import__` y no mira `__builtins__`. Es ofuscación deliberada y no un descuido realista, y `import builtins` sí se marca. Por eso no bloquea. Se puede endurecer marcando todo atributo `__import__` y toda referencia a `__builtins__`.

### A-02 · AMARILLO · contracts/tests/checks/test_protocol_surface.py · Los separadores de mensajes con varios elementos no se prueban
Los mutantes del `"; "` (línea 78) y del `", "` (línea 84) sobreviven, porque ningún caso tiene dos miembros extra ni dos decoradores. Solo cambia el formato del mensaje.

### A-03 · AMARILLO · docs/loop/bitacoras/U01-T08.md:93 · La cifra de CA-3 en la bitácora no corresponde a su comando
Dice «44 passed con test_model_call», pero el comando de CA-3 no incluye `test_model_call.py`. Mi corrida da 36 passed. Las cifras de cobertura sí coinciden.

## Tareas candidatas (defectos reales fuera de alcance)
- Siguen en pie las dos de la ronda 1 (K-12 y K-13): `test_package_map.py` solo exige *algún* archivo por directorio de datos, y `test_autonomia_04.py::test_anonymizing_provider_declara_solo_generate` tiene el punto ciego de la herencia y los decoradores.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/protocol_surface.py:37-40|__builtins__.__import__ y getattr(__builtins__, …) no se marcan como importación dinámica
AMARILLO|contracts/tests/checks/test_protocol_surface.py|Los separadores de mensajes con varios miembros o decoradores no se prueban (2 mutantes de texto vivos)
AMARILLO|docs/loop/bitacoras/U01-T08.md:93|La cifra de CA-3 en la bitácora (44) no corresponde a su comando (36)
INFORME: docs/loop/revisiones/U01-T08/ronda-2.md
```
