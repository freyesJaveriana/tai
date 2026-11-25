# Ronda 1 — U10-T03

VEREDICTO: NO-VERDE

Pasan los seis criterios. CA-3 y CA-5 pasan con la excepción permitida. Aun así encontré dos fugas de AUTONOMIA-04 que se pueden reproducir. Antes y después de mis corridas, `git status --porcelain` no mostró nada: el worktree quedó limpio y solo hay archivos ignorados (`.coverage` y `.hypothesis/`).

## Criterios, corridos por mí
| # | Comando que corrí | Resultado |
|---|---|---|
| — | `timeout 600 uv sync --frozen --directory /workspace/.worktrees/U10-T03/libs/anonymizer` | código 0 |
| CA-1 | `pytest tests/domain/test_catalogs.py tests/contracts/test_data_files.py --cov=…catalogs --cov-branch --cov-fail-under=100` | 53 pasan; 100 % de ramas |
| CA-2 | `pytest tests/domain/test_sentence.py test_detection.py test_masking.py --cov=… --cov-branch --cov-fail-under=100` | 113 pasan; 100 % de ramas en los tres módulos |
| CA-3 | `pytest tests/domain/test_restoration.py tests/guards/test_autonomia_05_restoration.py --cov=…restoration --cov-branch --cov-fail-under=100` | 22 pasan, 9 fallan, todas por `NotImplementedError: build_anonymizer` (excepción permitida); 100 % de ramas |
| CA-4 | `git -C /workspace/.worktrees/U10-T03 diff --exit-code afa8f20 -- …tests/guards …contracts …support.py …fixtures` | código 0 |
| CA-5 | `pytest tests/guards tests/contracts -p no:cacheprovider --junitxml=<scratchpad>/ca5.xml` | 13 pasan, 87 fallan, 0 ERROR; en el JUnit las 87 dicen `NotImplementedError: build_anonymizer lo implementa U10-T04` |
| CA-6 | `mypy --strict src tests`, `ruff check .`, `ruff format --check .` | sin problemas (36 archivos) |
| CA-6 | `check-no-datos-personales.sh`, `check-no-cluster-ids.sh`, `check-no-insumos.sh` | `0 apariciones` en las tres |
| CA-6 | `grep` de `import time` o `datetime` en `domain/` | no imprime nada |
| extra | `grep` de `import re` o `regex` en `src/` | no imprime nada: el texto del relato solo pasa por `google-re2` |
| sondas | `uv run … python -c` con `pseudonymize` y `restore` sobre textos sintéticos | ver F-01 a F-05 |

## Hallazgos

### F-01 · ROJO · `domain/detection.py:36,72` · La red de seguridad solo mira la primera letra de cada palabra
El patrón de palabra une con guion, guion bajo y dígitos. Luego `safety_net` comprueba solo si el primer carácter es mayúscula (`Lu`). Por eso una palabra con mayúscula pegada a algo que no es mayúscula sale sin marca. Mis sondas, todas con apellidos o nombres de pila sintéticos:
- un prefijo en minúscula unido por guion a un apellido;
- un nombre de pila en minúscula unido por guion a otro con mayúscula;
- un apellido pegado a un guion bajo o a un dígito;
- en un mensaje que no es JSON, un salto de línea escrito como barra invertida y «n», justo antes de un nombre;
- en un mensaje que no es JSON, una tilde inicial escrita como escape de unicode.

En los cinco casos el apellido o el nombre salió **sin cambios**. PD-2 manda marcar como `ENTIDAD` toda palabra con mayúscula inicial. El único límite declarado es el apodo todo en minúscula, así que esto es una fuga no declarada. E9 la cubre solo cuando el contenido es JSON válido.

**Corrección:**
- Partir el texto en subpalabras en cada guion, guion bajo y en cada paso de minúscula o dígito a mayúscula, o bien enmascarar entera toda palabra que tenga alguna mayúscula (enmascara de más, que es el lado seguro).
- En los valores que no son JSON, cortar también delante de las secuencias de escape de salto de línea, tabulador y unicode.
- Añadir estas cinco formas como casos de `tests/domain/test_detection.py` y como estrategia de la propiedad Hypothesis.

### F-02 · ROJO · `data/allowed-words.v1.yaml:283` · «Abril» es un nombre de pila
PD-2 dice que la lista **nunca** lleva un nombre de pila. «Abril» es un nombre de pila femenino común. Lo comprobé: una frase que empieza con ese nombre sale tal cual, y la prueba no lo detecta porque `common_word_names.json` no lo trae.

**Corrección:** quitar «Abril» de la lista. Revisar del mismo modo «Junio» y cualquier otro mes o día que sea nombre de pila. Como `tests/fixtures` queda fuera de esta tarea, la comprobación va en `tests/domain/test_catalogs.py` con su propia lista negativa.

### F-03 · AMARILLO · `domain/masking.py:152-161` · Claves JSON y números quedan intactos
Una clave JSON con un nombre completo y un número de celular escrito como número JSON salieron sin marca. Es lo que pide el diseño, pero es una puerta de fuga si U11 construye el bloque con claves dinámicas.

**Corrección:** declarar el límite. U10-T04 o U11 deben comprobar que las claves del bloque son fijas y que ningún número JSON lleva un identificador.

### F-04 · AMARILLO · `domain/masking.py:245-251` · Un apellido suelto en `system` no se propaga
Si en `user` aparece un nombre completo, la tabla solo guarda el tramo entero que crea F-11. Ese mismo apellido escrito solo en un mensaje `system` no recibe marca. El riesgo es bajo, porque `system` es un texto fijo.

**Corrección:** propagar también cada palabra del tramo como forma, o declarar el límite.

### F-05 · AMARILLO · `domain/detection.py:72` · Las escrituras sin mayúsculas nunca se detectan
Un nombre en escritura china o árabe (categoría `Lo`) salió sin marca. PD-2 define la red por la mayúscula, así que no es un defecto de esta tarea. Va a tareas candidatas.

## Sobre las decisiones declaradas
- **F-11:** la acepto. Una palabra permitida corta el tramo, pero la palabra siguiente se marca igual. Ver F-04.
- **F-12:** la acepto. `has_budget` lanza `MaskingBudgetExceeded` y la tabla se vacía si algo falla después de crearla. Es compatible con la guardia de BR1.8 en sus seis escenarios.
- **Precedencia EXPEDIENTE > IDENTIFICADOR > PERSONA > LUGAR > ENTIDAD:** la acepto, es la de BR1.2.
- **`domain/regex.py`:** lo acepto. Es el único lugar que importa `re2` y no hay `re` sobre el texto.
- **`MaskTable`:** su `repr` no muestra valores y `__reduce_ex__` impide `pickle` y copia.
- **Restauración:** devuelve la forma exacta. Una marca con otro uso de mayúsculas, con ceros a la izquierda o inventada queda sin restaurar y su puntero se anota. «persona 3» sin corchetes no se toca.
- **U10-T04:** ninguna decisión lo obliga a contradecir el plan ni a cambiar el rojo.
- **Alcance:** el diff solo toca `data/`, `domain/`, `tests/domain/` y la bitácora. `application/`, `api.py` y `providers/` siguen como *stubs*. Los umbrales no bajaron.

## Tareas candidatas
- Red de seguridad para escrituras sin mayúsculas (NER de B10b).
- Que U11 garantice que en el bloque de datos las claves son fijas y no hay identificadores como números JSON.

```
VEREDICTO: NO-VERDE
ROJO|libs/anonymizer/src/veridicus_anonymizer/domain/detection.py:36,72|La red de seguridad solo mira la primera letra: un nombre tras guion, guion bajo, dígito o escape sale sin marca
ROJO|libs/anonymizer/src/veridicus_anonymizer/data/allowed-words.v1.yaml:283|«Abril», nombre de pila, está en allowed-words
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/domain/masking.py:152-161|Claves JSON y números quedan intactos; límite sin declarar
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/domain/masking.py:245-251|Un apellido suelto en system no se propaga desde el nombre completo
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/domain/detection.py:72|Las escrituras sin mayúsculas nunca se detectan
INFORME: docs/loop/revisiones/U10-T03/ronda-1.md
```
