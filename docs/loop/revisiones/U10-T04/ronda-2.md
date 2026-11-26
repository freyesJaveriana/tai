# Ronda 2 — U10-T04

**VEREDICTO: NO-VERDE.** Corrí los seis criterios, CA-1 a CA-6, y todos pasan. F-01 a F-07, F-09 y F-10 quedan cerrados. F-08 no: con el cambio de esta ronda, el texto del mensaje `system` ya no se revisa en ninguna prueba de `generate`. Hay un solo NARANJA y ningún ROJO. El worktree quedó limpio, y `domain/`, `contracts/`, `libs/errors`, `scripts/` y `.github` no cambian en el diff `954fde7...tarea/U10-T04`.

## Criterios, verificados por mí (en el worktree)
| # | Comando | Resultado |
|---|---|---|
| — | `uv sync --frozen --directory …/libs/anonymizer` | 0 |
| CA-1 | `pytest tests/providers --cov=…providers --cov-branch --cov-fail-under=100` | 57 pasan; 100 % de ramas |
| CA-2 | `uv lock --check` | 0 |
| CA-2 | `pytest tests/guards tests/contracts tests/application --cov=…application --cov=…api --cov-branch --cov-fail-under=100` | 137 pasan; 100 % de ramas |
| CA-2 | `grep` de `veridicus-contracts` y `veridicus-errors` en `uv.lock` | contracts 0.1.1 (l. 1680); errors 0.1.0 por ruta (l. 1713) |
| CA-3 | `git -C … diff --exit-code afa8f20 -- …tests/guards …tests/contracts …tests/support.py …tests/fixtures` | 0, sin cambios |
| CA-4 | `lint-imports` | 4 contratos kept, 0 broken |
| CA-4 | `pytest tests/boundaries --no-cov -q` | 18 pasan |
| CA-5 | `pytest -p no:cacheprovider` | 416 pasan, 0 FAILED y 0 ERROR |
| CA-6 | `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | limpios |
| CA-6 | las 3 guardias `scripts/check-no-*.sh` | `0 apariciones` cada una |

## Cierre de la ronda 1
- **F-01, cerrado.** Una sonda hizo fallar con un error inesperado `_replacements`, `_check_destination` y `restore`, con los dos *canaries* en el mensaje del error. En los dos primeros sale `AnonymizerUnavailable`, con 0 peticiones y sin `call`; en `restore` sale `ProviderError`, con 1 petición y su `ModelCall` (PD-9). En los tres, `__context__` y `__cause__` son `None` y ningún *canary* aparece en el `repr`. El `try` de `_prepare` no envuelve `send`.
- **F-02, cerrado.** Se prohíben 6 nombres, cada uno con su control negativo.
- **F-03, cerrado.** Los dos contratos juntos cubren el `__init__` raíz y todo módulo o subpaquete de primer nivel con sus descendientes. Los dos controles negativos rompen cada uno su contrato.
- **F-04, cerrado.** El mutante que pasa a `pseudonymize` un `has_budget` siempre verdadero deja en rojo la prueba del presupuesto de F-04.
- **F-05, cerrado.** `build_anonymizer` lanza `ConfigInvalidProfileError` y `ConfigInvalidLimitError`; los mensajes solo nombran variables. La dependencia está en `pyproject.toml` y en el lock.
- **F-07, cerrado.** Toda compresión declarada (en mayúsculas, con espacios, en lista, vacía) da `ProviderError` con 1 petición; sin la cabecera, un cuerpo comprimido no se descomprime y sale `InvalidOutput`. Seguir con `iter_bytes` es suficiente.
- **F-06, F-09 y F-10, cerrados.** F-06 queda documentado en `_exchange`; `jsonschema` ya es dependencia directa; `build_client` ya no cambia el nivel de los *loggers*.
- **Umbrales.** No baja ninguno.

## Hallazgos
### F-11 · NARANJA · `libs/anonymizer/tests/application/test_properties.py:95` · Nada comprueba que `system` salga seudonimizado (F-08 sigue abierto)
- **Qué falla.** La propiedad ahora genera las formas sonda también en `system`, pero quita todo el campo `system` del cuerpo antes de aplicar el oráculo. El límite que declaró U10-T03 solo cubre las palabras sueltas de un nombre. Con esta exclusión tampoco se comprueba el nombre completo.
- **Prueba.** Un mutante de `_mask` que devuelve los mensajes `system` sin seudonimizar, y el resto sí, deja **las 416 pruebas en verde**. Una regresión así llegaría al proveedor sin que nada la detecte (AUTONOMIA-04).
- **Lo que hace el código real.** Hoy el nombre completo sí se reemplaza en `system` por su marca. El defecto está en la prueba, no en el código.
- **Corrección.** En `system`, mantener el oráculo para las entidades sembradas completas y para las formas de la tabla de más de una palabra; excluir solo las palabras sueltas. Como alternativa, una prueba en `tests/application` con un nombre sembrado completo en `system`, que exija que no salga. El mutante descrito debe dejar al menos una prueba en rojo.

```
VEREDICTO: NO-VERDE
NARANJA|libs/anonymizer/tests/application/test_properties.py:95|El oráculo excluye todo system: un mutante que no seudonimiza system pasa las 416 pruebas
INFORME: docs/loop/revisiones/U10-T04/ronda-2.md
```
