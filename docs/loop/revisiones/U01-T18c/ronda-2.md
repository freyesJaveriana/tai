# Ronda 2 — U01-T18c

VEREDICTO: VERDE

Los tres hallazgos de la ronda 1 se cierran, todos los SHA reescritos llevan su marca y CA-1 a CA-6 pasan sobre el HEAD.

## Criterios de aceptación, verificados por mí (HEAD `56ab0fb`, código en `88656ed`)
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Lecturas de vuelta y validador sin cambios | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18c/contracts pytest tests/contracts/test_correcciones_t18c.py --no-cov -p no:cacheprovider -q --color=no` | pasa: `73 passed in 0.94s` |
| 2 | Suite completa | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18c/contracts pytest tests --no-cov -p no:cacheprovider -q --color=no -rs` | pasa: `2331 passed, 1 warning in 114.09s`. No hay ninguna F ni SKIPPED. El aviso es `test_socket_bloqueado`, que ya existía |
| 3 | Cada contrato solo añade la versión | `git -C /workspace/.worktrees/U01-T18c diff feat/b1-contratos...HEAD -U0 -- contracts/cli contracts/integrity contracts/model_calls contracts/profiles contracts/errors contracts/src` | pasa: `8 files changed, 8 insertions(+), 1 deletion(-)`. Son las mismas líneas y los mismos blobs que en la ronda 1 (p. ej. `c8cf520..35b2fe8`, `f880b14..6eacb2c`, `1a06289..d94b2e7`) |
| 4 | Solo los archivos permitidos | `git -C /workspace/.worktrees/U01-T18c diff --name-only feat/b1-contratos...HEAD` | pasa: los mismos 12 archivos de la ronda 1 |
| 5 | Instalación editable y rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov …` | pasa: `8 passed in 3.23s` |
| 6 | Tipos, lint y CI | `uv run … mypy --strict src` / `uv run … ruff check .` / `bash /workspace/.worktrees/U01-T18c/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18c` | pasa: `Success: no issues found in 34 source files`, `All checks passed!`, `0 apariciones` |

**Cobertura de `validators.py`:** la medí con `pytest tests/test_validators.py tests/contracts/test_correcciones_t18c.py --cov=veridicus_contracts.validators --cov-branch …`. Da 137 sentencias, 54 ramas, 0 parciales, 99 %. Solo quedan sin cubrir las líneas 127-128 (`Unresolvable`), que ya existían.

La corrida de la suite completa con cobertura sigue en segundo plano y no la esperé. Como `validators.py` no cambió desde la ronda 1, el dato de la ronda 1 con la suite completa (54 ramas, 0 parciales) sigue valiendo.

El worktree queda limpio: `git status --porcelain` no devuelve nada.

## Comprobaciones pedidas
1. **Se cierran los tres hallazgos de la ronda 1:**
   - **F-01:** la línea 15 ahora dice «5dc366f, reescrito por rebase: ahora 20dde57».
   - **F-02:** el parametrizado anidado suma `if`, `then` y `prefixItems`. Hay además un parametrizado nuevo con `X-veridicus-version`, la clave con espacio al final y con espacio al inicio, en la raíz.
   - **F-03:** CA-3 y CA-4 van literales en la bitácora (líneas ~327-439).
2. **Los SHA reescritos llevan su marca en la misma línea.** Lo revisé con `grep -nP "\b[0-9a-f]{7,40}\b"` sobre la bitácora:
   - Llevan su marca todos los reescritos: `5dc366f`, `2011654`, `2bcf8ac`, `8343026`, `103cfcd`, `be6cfb7` y `b322de4`. Las líneas 197, 199, 201, 227, 230, 271 y 272 los marcan o los muestran en el mapa «X a Y».
   - Están en `feat/b1-contratos..HEAD` los vigentes (`20dde57`, `c0911a8`, `f7ae391`, `193322b`, `cae31f1` y `88656ed`) y además `56ab0fb`.
   - `36d2999` es un commit de la base, y los `index …` son blobs del diff, no commits.
   - Con `git -C … range-diff 36d2999..b322de4 c9d6f10..cae31f1` los cinco commits salen idénticos (`=`). El rebase no cambió nada y el rojo de la ronda 1 sigue valiendo.
3. **El diff de la ronda solo suma controles.** `git diff 193322b 88656ed -- contracts` solo toca `test_correcciones_t18c.py`: 16 líneas añadidas y 1 cambiada, que es la lista `ids`. No cambió `validators.py`, ningún contrato ni ninguna aserción anterior. Probé que los controles nuevos detectan algo: cargué una versión mutada del validador, que compara la clave con `strip().lower()` y la admite fuera de la raíz. Fallan las 7 anidadas y las 3 variantes, y la de `x-veridicus-limit` en la raíz sigue pasando, que es lo esperado. Que no haya un rojo nuevo es correcto: son guardias que ya pasan con el código vigente, y el rojo del comportamiento nuevo es el de la ronda 1, que yo mismo repetí.
4. **CA-1 a CA-6:** ver la tabla.

## Hallazgos
No queda ningún hallazgo ROJO ni NARANJA. F-01, F-02 y F-03 están cerrados.

## Tareas candidatas (defectos reales fuera de alcance)
Siguen las dos de la ronda 1, ya registradas en `docs/loop/CANDIDATAS.md`:
- `validate_json_schema` rechaza el `x-veridicus-limit` anidado de C19, C13 y C18 (`effective-config`), así que `validate_instance` falla con esos tres esquemas.
- El valor de `x-veridicus-version` no lo comprueba el validador. Le toca a T18 (E-28).

```
VEREDICTO: VERDE
INFORME: docs/loop/revisiones/U01-T18c/ronda-2.md
```
