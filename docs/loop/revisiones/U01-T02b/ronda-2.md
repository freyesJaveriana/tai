# Ronda 2 — U01-T02b

VEREDICTO: VERDE

Contexto: la rama `tarea/U01-T02b` está en 8371c54, que incluye el merge 86d31e6 de `origin/feat/b1-contratos`. La base local y la remota apuntan al mismo commit, 343f5ad (`git -C /workspace/.worktrees/U01-T02b rev-parse feat/b1-contratos origin/feat/b1-contratos`). Al terminar, `git status --short` sale vacío: el worktree está limpio.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Pruebas del registro | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts pytest tests/test_registry.py --no-cov` | pasa: 22 passed |
| 1-rojo | Las pruebas nuevas fallan contra el registro de la base | `timeout 60 uv run --frozen --offline --directory /workspace/contracts pytest -p no:cacheprovider /workspace/.worktrees/U01-T02b/contracts/tests/test_registry.py --no-cov -q --tb=no` | 10 failed y 12 passed. Fallan las 3 de la ronda 1, los 5 casos de `$id` vacío, con `#` o con `?`, y los 2 de URI repetida. Coincide con la bitácora: 7 rojos sobre el código de la ronda 1 más los 3 anteriores. |
| 2 | Suite de las tareas anteriores | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py tests/test_validators.py tests/test_package_map.py tests/test_runner.py --cov-fail-under=0` | pasa: 87 passed |
| 2 | 100 % de ramas en `registry` | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts coverage report --include=src/veridicus_contracts/registry.py --fail-under=100` | pasa: 54 sentencias, 26 ramas, 100 % |
| 3 | Tipos | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts mypy --strict src` | pasa: `Success: no issues found in 6 source files` |
| 3 | Lint | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02b/contracts ruff check .` | pasa: `All checks passed!` |
| 4 | AUTONOMIA-01 | `bash /workspace/.worktrees/U01-T02b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T02b` | pasa: `0 apariciones` |

## Hallazgos de la ronda 1, comprobados corriendo
- **F-01 (cerrado).** Lo comprobé con mis propios esquemas sintéticos en el scratchpad, usando `uv run … python -c` con `"\x24"`:
  - C6 sin barra frente a otro esquema con barra: `LoadError URI repetida https://veridicus.invalid/veridicus/contracts/analyzer/v1/salida: la declaran salida.schema.json y otro.schema.json`.
  - Dos `$id` idénticos: rechazado, nombrando `p.schema.json` y `q.schema.json`.
  - `./veridicus/x` frente a `veridicus/x`: rechazado.
  - Dos `$id` distintos: aceptados.
- **F-02 (cerrado).** `''`, `#`, `#frag`, `?`, `?q=1`, `veridicus/a#`, `veridicus/a#frag` y `veridicus/a?q` dan `el $id no puede ser vacío, con fragmento o con consulta`.
  - Los meta-esquemas empaquetados no se rompen:
    - `verify_vendor()` pasa sobre la copia instalada y `verify_vendor(Path(".../contracts/vendor"))` sobre el árbol fuente.
    - `build_registry` pasa sobre las dos carpetas `vendor` y sobre el paquete por defecto.
    - Del registro por defecto se recuperan `https://json-schema.org/draft/2020-12/schema` y `https://spec.openapis.org/oas/3.1/schema/2022-10-07`.
- **F-03 (cerrado).** La prueba exige `match="sale de la base"`, y contra la base falla, como debe.

## Lo demás que pidió el encargo
- **No se afloja el rechazo de URIs ajenas** (sondeo de `_uri_de`):
  - Se rechazan `https://example.com/x`, `file:///etc/passwd` y `data:…` («solo bajo vendor/»), y `//example.com/x`, `../x` y `a/../../x` («sale de la base»).
  - `%2e%2e/x` y `a\..\x` se aceptan, pero quedan tal cual dentro de `https://veridicus.invalid/` y no salen del host.
- **Lectura de vuelta de la forma de C6.** Un `$id` `veridicus/contracts/analyzer/v1/salida` con una `$ref` interna `#/$defs/t`, referenciado desde otro esquema por `/veridicus/contracts/analyzer/v1/salida#/$defs/cita`, da: instancia válida True, `texto: 5` False, sin `cita` False.
- **El diff no revierte nada.** El diff de dos puntos y el de tres puntos contra `feat/b1-contratos` son idénticos: 6 archivos, 143 líneas añadidas y 7 quitadas, todo de esta tarea (`registry.py`, `tests/data/registro_relativo/`, `test_registry.py` y las dos bitácoras).
- **Alcance.** No toca archivos de T03, no hay rastro de `/insumos` ni de C6 y los datos de prueba son sintéticos.

## Hallazgos

### F-04 · AMARILLO · contracts/src/veridicus_contracts/registry.py (mensaje de `URI repetida`) · El mensaje nombra solo el nombre del archivo, sin su carpeta
Con dos archivos del mismo nombre en carpetas distintas, el mensaje sale como `la declaran s.schema.json y s.schema.json`: no dice cuál es cuál. El rechazo funciona; solo el diagnóstico es ambiguo. Sugerencia: poner en el mensaje la ruta relativa a `raiz`.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/registry.py (mensaje de URI repetida)|El mensaje nombra solo el nombre del archivo, sin su carpeta
INFORME: docs/loop/revisiones/U01-T02b/ronda-2.md
```
