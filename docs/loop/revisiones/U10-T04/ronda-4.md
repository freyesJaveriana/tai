# Revisión acotada de F-12 en U10-T04 (arreglo corto por ML-5)

El arreglo de F-12 cumple: no queda ningún ROJO ni NARANJA en pie. Revisé el diff `c1b8c8c..1a2101c` y corrí cada comprobación en el worktree sin editar nada; al terminar, `git status --porcelain` sale limpio.

**1. Alcance.** El diff toca 4 archivos: `tests/application/test_properties.py`, `tests/application/test_system_message.py` y dos bitácoras en `docs/loop/bitacoras/`. No cambian `src/` ni `pyproject.toml`, y no baja ningún umbral.

**2. Mutantes** (en memoria con `mock.patch.object` sobre `generate._mask`):

| Mutante | Qué hace | Resultado |
|---|---|---|
| F-12 | En `system`, las formas sin espacio vuelven a su texto original | 2 fallan (`test_f12_…` y la propiedad), 417 pasan |
| F-12, solo el apodo | Solo el apodo vuelve a su texto en `system` | Fallan las mismas 2 pruebas; cada una detecta por sí sola la fuga del apodo |
| F-11 | `system` sale sin seudonimizar | 4 fallan: la propiedad, `test_f12_…` y los 2 casos parametrizados; 415 pasan |

**3. Oráculo.** `test_properties.py:119-122` excluye un elemento solo si no tiene espacio y es igual a una palabra de alguna entidad de varias palabras. El radicado, la cédula y los nombres de una sola palabra siguen siendo exigidos. Un identificador sin espacio solo quedaría fuera si coincidiera con una palabra de un nombre de varias palabras, y las entidades sembradas siguen exigidas aparte (línea 104).

**4. Prueba del apodo.** Aceptar `PERSONA` o `ENTIDAD` no la debilita: la comprobación que importa es que el apodo no aparezca en el cuerpo crudo (`test_system_message.py:59-60`), y esa falla con el mutante del apodo. Las otras dos entidades llevan `EXPEDIENTE` e `IDENTIFICADOR`. El cuerpo usa `ensure_ascii=False`, así que la búsqueda es fiable.

**5. Criterios:**

| Criterio | Comando | Resultado |
|---|---|---|
| CA-3 | `git -C … diff --exit-code afa8f20 -- …guards …contracts …support.py …fixtures` | código 0, sin cambios |
| CA-5 | `pytest -p no:cacheprovider -q` | 419 pasan |
| CA-6 | `mypy --strict src tests` | sin problemas en 47 archivos |
| CA-6 | `ruff check .` y `ruff format --check .` | limpios |
| CA-6 | las 4 guardias `scripts/check-no-*.sh` | 0 apariciones en cada una |

**Hallazgos**
- **F-13 · AMARILLO · `libs/anonymizer/tests/application/test_properties.py:121`.** `_not_parts_of_longer` junta las palabras de todas las entidades de la entrada, no de cada turno. Con el *fixture* actual no oculta nada, pero un apodo futuro igual a una palabra del nombre de otra persona quedaría fuera del oráculo sin aviso. No bloquea.

```
VEREDICTO: VERDE
AMARILLO|libs/anonymizer/tests/application/test_properties.py:121|_not_parts_of_longer junta las palabras de toda la entrada y no de cada turno
INFORME: docs/loop/revisiones/U10-T04/ronda-4.md
```
