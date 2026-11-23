# Ronda 2 — U01-T10

VEREDICTO: VERDE

Corrí todo yo mismo y nada bloquea. Los 6 criterios pasan. De 95 mutantes muere todo lo que no es equivalente. La prueba de pureza hace fallar de verdad `open`, `os.environ` y `os.getenv`. La suite completa tiene los mismos 52 fallos que la base, sin ninguno nuevo. Queda un aviso AMARILLO sobre el parche de `socket`.

Hash de la tarea: 778b771f…2bfd2, sin cambios. HEAD en f300a47. El worktree sigue limpio después de mis corridas (`git status --short` vacío). Entre 7b4bd48 y f300a47, `contracts/src`, `pyproject.toml` y `hatch_build.py` no cambian: solo cambian `limits.v1.yaml` (F-04) y las pruebas, todo líneas añadidas.

## Criterios de aceptación, verificados por mí
| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T10/contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q` | pasa: 161 en 2,67 s |
| CA-2 | `… pytest … --cov-fail-under=0 -q`, luego `… coverage report --include=src/veridicus_contracts/limits.py,src/veridicus_contracts/checks/limits_catalog.py --fail-under=100 --show-missing` | pasa: 100 % de líneas y de ramas (152 líneas y 66 ramas, 0 sin cubrir) |
| CA-3 | `timeout 300 uv run … pytest tests/test_package_map.py --no-cov -q` | pasa: 8 |
| CA-4 | `uv lock --check --directory /workspace/.worktrees/U01-T10/contracts` | pasa: 79 paquetes resueltos |
| CA-5 | `… mypy --strict src` y `… ruff check .` | pasa: «Success: no issues found in 11 source files» y «All checks passed!» |
| CA-6 | `bash /workspace/.worktrees/U01-T10/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T10` | pasa: 0 apariciones |

## Lo que pediste comprobar
- **Mutantes (F-01).** Saqué f300a47 con `git archive` a una copia en el scratchpad (`mut2/contracts`), con su propio `.venv`. Su `src/` es idéntico al de la ronda 1 (`diff -r` vacío), así que los mutantes aplican sin cambios.
  - Corrí los 89 de la ronda 1 más 6 de pureza, cada uno en un proceso de pytest aparte, y al final verifiqué que la copia volvía a pasar sin mutantes (161 pasan).
  - Murieron 94 de 95. El único vivo es el n.º 37 (`!= SECCIONES` → `not set(documento) <= SECCIONES`), que es equivalente: cuando falta una sección, otra rama ya la reporta (`schema_version`, `limits` o `relations`).
  - Los 23 que no son equivalentes y estaban vivos en la ronda 1 ahora mueren: las 8 relaciones obligatorias, las cuatro fórmulas con otros orígenes, el techo de la división por 3 con 6 000 001 y 6 000 002, la lista `UNIDADES`, los patrones `C`/`U`, `OBLIGATORIAS`, las relaciones de 4 elementos y los casos `5abc`, `5.`, `007.5` y `1.0` de `_convertir`.
- **Pureza (F-02).** Corrí solo `test_load_es_pura_sin_open_ni_entorno_ni_red` contra cada mutante que añade una llamada dentro de `load`:
  - `os.getenv`, `os.environ.get`, `list(os.environ)`, `"X" in os.environ`, `open(...)`, `io.open(...)` y una relectura del catálogo fallan todos con `AssertionError: limits.load no debe tocar archivos, entorno ni red (§4.15)`;
  - sin mutante, la prueba pasa.
- **`used_in` (F-04).** `web_session_max_s` y `web_session_idle_s` llevan ahora `used_in: [C1]`, como pide §4.4. La guardia los acepta (CA-1 en verde).
- **El rojo declarado es creíble.** No cambió código, solo pruebas, así que las pruebas nuevas pasan sobre el mismo código. El rojo solo se puede mostrar con mutantes; la bitácora da tres y mi barrido completo lo confirma. No se tocó ninguna prueba ni ningún umbral anteriores.
- **Suite completa.** El comando fue `uv run … pytest -q --no-cov --tb=no -p no:cacheprovider --junitxml=…/t10r2-junit.xml`: 52 fallos y 399 pasan.
  - Comparé el JUnit con el de la base. Mi copia es de 7c0eedb, pero `git diff --stat 7c0eedb db49734 -- contracts` sale vacío, así que vale para la base actual.
  - Resultado: 0 fallos nuevos, 0 arreglados, 0 pruebas desaparecidas frente a la base y frente a la ronda 1, 0 omitidas y 57 pruebas nuevas.
- **El diff no revierte nada.**
  - La base está en db49734 y los commits que avanzó desde cd702bf (23d9338, 3f7659b, db49734) solo tocan `docs/`.
  - El diff de tres puntos trae solo los 10 archivos de la tarea, y `git merge-tree --write-tree feat/b1-contratos f300a47` fusiona sin conflicto.
  - Con T08, que ya está en VERDE, no hay archivos en común y `git merge-tree` también fusiona sin conflicto.

## Hallazgos
### F-05 · AMARILLO · tests/test_limits.py · el parche de `socket.socket` no se prueba por sí mismo
`esperado = limits.load(...)` se calcula fuera de `monkeypatch.context()`. Por eso un mutante que llama a `socket.socket()` dentro de `load` lo mata `pytest-socket` (`SocketBlockedError`) antes de llegar al parche. El socket queda bloqueado de todos modos en toda la suite, así que no hay hueco real. Lo único es que el parche de `socket` dentro del bloque nunca llega a demostrar nada.

F-03 (mensajes con cifras) se queda así por decisión del orquestador. La recomprobación de las derivadas tras bajar una cifra queda como candidata K-10.

## Tareas candidatas
- Ninguna nueva.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/test_limits.py|el parche de socket.socket no se prueba por sí mismo (lo cubre pytest-socket)
INFORME: docs/loop/revisiones/U01-T10/ronda-2.md
```
