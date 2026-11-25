# Ronda 1 — U01-T08

VEREDICTO: NO-VERDE

Los seis criterios y la verificación del paso 10 pasan con mis propias corridas. El veredicto es NO-VERDE por dos hallazgos NARANJA en la guardia `protocol_surface.py`: la guardia se puede burlar, y 10 mutantes no equivalentes sobreviven. No hay ningún ROJO.

Revisé `tarea/U01-T08` en f8bea7b, con base 4425509 (que es la merge-base con `feat/b1-contratos`). Corrí la tarea en su versión actual (sha256 97a754d1…), con CA-2 ajustado por P-T08-1. El worktree quedó limpio (`git -C /workspace/.worktrees/U01-T08 status --porcelain` no devuelve nada).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 10 (E27, E42, E43) | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T08/contracts pytest tests/typing tests/checks/test_protocol_surface.py tests/contracts/test_model_call.py --no-cov -v` | pasa, 32 passed. E27: `[mayusculas]` y `model-call.role-mayusculas.yaml` |
| 1b | Paso 10, segunda mitad | `uv run --frozen --offline --directory …/contracts mypy --strict src` | `Success: no issues found in 11 source files` |
| 2 | Guardias c13 (sin `c13-llamada`) | `timeout 60 uv run … pytest tests/guards -m c13 --no-cov --deselect "…[c13-llamada]" -v -p no:cacheprovider` | pasa, 3 passed, 55 deselected |
| 3 | 100 % de ramas en la guardia | `timeout 120 uv run … pytest tests/typing tests/checks/test_protocol_surface.py --cov-fail-under=0 -q -p no:cacheprovider` y luego `uv run … coverage report --include=src/veridicus_contracts/checks/protocol_surface.py --fail-under=100 --show-missing` | pasa: 73 sentencias, 36 ramas, 0 sin cubrir, 100 % |
| 4 | Datos en la instalación editable y en la rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa, 7 passed. Además los leí de vuelta yo (ver abajo) |
| 5 | Tipos y *lint* | `mypy --strict src` y `uv run … ruff check .` | `Success…` y `All checks passed!` |
| 6 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T08/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T08` | `0 apariciones`, código 0 |

**Lectura de vuelta (CA-4)**
- **Rueda:** construí una rueda limpia del commit (`git archive f8bea7b contracts`, luego `uv build --wheel --offline`, todo en el scratchpad). Contiene `veridicus_contracts/model_calls.py`, `model_calls/model-call.v1.yaml` y `model_calls/role-translation.v1.yaml`, y ningún *fixture*. Al extraerla e importarla con `python3 -I`, `model_calls` resuelve al módulo, `importlib.resources.files("veridicus_contracts") / "model_calls"` lista los dos YAML, la tabla devuelve sus tres filas y `comprobar()` da `[]`.
- **Editable:** el mismo script en el venv del worktree da lo mismo.

**Comprobaciones pedidas**
- **BR9.9:** el `Protocol` tiene solo `generate`, y el módulo importa solo `dataclasses`, `datetime` y `typing`.
- **Errores:** `AnonymizerUnavailable` no tiene `call` (`hasattr` da False); las otras cuatro subclases lo llevan.
- **role-translation:** exactamente `judge`, `verifier` y `verifier_permuted`, y su conjunto coincide con el enum `papel` de C6.
- **E42:** el control negativo es real: exige `[arg-type]` y `expected "AnonymizingProvider"` en la salida de mypy.
- **Vocabulario de veracidad:** ninguno de los nombres de `model-call.v1.yaml` (incluidos los valores del enum `provider`) cae en `TERMINOS_DE_C8` ni en `CATEGORIAS_PROHIBIDAS` según `con_veracidad`. El caso excluido `c13-llamada` debería pasar cuando exista C8.
- **Diff:** son 8 archivos, todos del alcance de T08 más su bitácora. No revierte nada y no toca `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `helpers.py` ni `checks/__init__.py`. `git merge-tree --write-tree feat/b1-contratos tarea/U01-T08` fusiona sin conflictos.
- **Rojo primero:** la bitácora trae el par falla-pasa (31 fallos y luego 32 verdes), con las pruebas escritas antes que el código.

## Hallazgos

### F-01 · NARANJA · contracts/src/veridicus_contracts/checks/protocol_surface.py:55-74, 35-52 · La guardia de la puerta única se puede burlar (BR9.9, E43)
`_comprobar_puerta` solo revisa el cuerpo de la clase y que una base se llame `Protocol`, y `_importaciones_ajenas` solo ve sentencias `import`. Pasé tres variantes por `comprobar_fuente` en un proceso aparte, y las tres dan `[]`:
- **herencia:** `class _Listo(Protocol): def check_ready(self) -> bool: ...` y después `class AnonymizingProvider(_Listo, Protocol):`. El `Protocol` queda con `check_ready`, que es justo lo que E43 prohíbe.
- **estatico:** `@staticmethod` sobre `generate`. La guardia no mira los decoradores.
- **dinamico:** `os = __import__('os')`. Es una importación ajena que no es una sentencia `import`.

El caso de la herencia lo atraparía hoy E42, por mypy (un doble con solo `generate` dejaría de cumplir el `Protocol`). Pero el módulo guardia es el que la tarea declara para hacer cumplir §4.17 y no lo detecta solo. La guardia debería exigir `clase.bases` igual a solo `Protocol`, rechazar `decorator_list` en `generate` y marcar las llamadas a `__import__` o `importlib`, cada caso con su prueba negativa.

### F-02 · NARANJA · contracts/tests/checks/test_protocol_surface.py · Sobreviven mutantes no equivalentes de la guardia (faltan controles positivos y el negativo de `comprobar`)
Mutación por AST de `protocol_surface.py`: 140 mutantes, cada uno en su propio subproceso, inyectado en `sys.modules` y sin escribir en el worktree. Mueren 116 y sobreviven 24. Los scripts están en el scratchpad del revisor (`mutar.py` y `lanzar_mutante.py`). El control con el original da 19 passed. Barrido de la clase:
- **m21, `comprobar(ruta)` → `return []`:** sobrevive. La única prueba de `comprobar` usa el archivo real y espera `[]`, así que la entrada por archivo nunca tiene un control negativo.
- **m22 y m53, sin `'veridicus_contracts'` en `IMPORTACIONES_PERMITIDAS`; m25 y m56, sin `'enum'`:** sobreviven. Ninguna prueba demuestra que una importación permitida (`from veridicus_contracts.x import y`, `import enum`) da cero problemas.
- **m116 y m132, sin `'typing.Protocol'` como base aceptada:** sobreviven. No hay caso `class AnonymizingProvider(typing.Protocol)`.
- **m130 (línea 39) y m139 (línea 44), `split(".")` alterado:** sobreviven. No hay caso de una importación con punto que esté permitida (`import typing.x`, `from veridicus_contracts.loaders import …`).
- **m79 (línea 42), `continue` → `pass`:** casi equivalente; solo duplica reportes o da `UnboundLocalError` si la importación relativa va primero.

Hacen falta controles positivos parametrizados y un caso negativo de `comprobar(tmp_path / "model_calls.py")`.

### F-03 · AMARILLO · test_protocol_surface.py · Los mutantes del texto de los mensajes sobreviven
m98, m100, m104, m113, m120 a m123, m125 y m127 cambian sufijos (`(BR9.9)`, `(E43)`) y separadores. m135 y m137 cambian `firma[0]` por `firma[1]` dentro del mensaje. Las pruebas comparan subcadenas sin el ID de la regla. m87 y m88 tocan una anotación de tipo y son equivalentes.

### F-04 · AMARILLO · contracts/src/veridicus_contracts/model_calls.py:70, 77-80 · `ModelCall` no cuadra del todo con su esquema
`provider` es `str`, mientras que `GenerateRequest` usa `Literal Provider` y el esquema cierra el enum. Los opcionales valen `None`, pero el esquema no admite `null`: quien serialice tiene que omitirlos.

### F-05 · AMARILLO · contracts/tests/typing/test_role_translation.py · Prueba de datos guardada en `tests/typing/`
No es una prueba de tipos. Está dentro del directorio permitido, pero ahí despista.

## Tareas candidatas (defectos reales fuera de alcance)
- `tests/test_package_map.py` (T01) solo exige *algún* archivo por directorio de datos en la rueda. Debería comprobar cada YAML y que el módulo y el directorio del mismo nombre convivan (caso `model_calls`).
- `tests/guards/test_autonomia_04.py::test_anonymizing_provider_declara_solo_generate` (T03) tiene el mismo punto ciego de F-01: acepta `check_ready` heredado de otra base y `@staticmethod`.
- **Riesgo con T10:** bajo. T10 añade `force-include` solo para `limits.v1.yaml` y deja intactas las entradas `include`, `sources` y `cache-keys` de `model_calls`. `git merge-tree --write-tree tarea/U01-T08 tarea/U01-T10` fusiona sin conflictos. Cuando entren las dos, conviene repetir la lectura de vuelta de la rueda: con `force-include` hatchling no aplica `exclude`, aunque hoy no afecta a `model_calls/fixtures`.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/protocol_surface.py:55-74|La guardia de la puerta única se burla con check_ready heredado, @staticmethod o __import__
NARANJA|contracts/tests/checks/test_protocol_surface.py|Sobreviven 10 mutantes no equivalentes: faltan controles positivos y el negativo de comprobar()
AMARILLO|contracts/tests/checks/test_protocol_surface.py|Los mutantes del texto de los mensajes (IDs de regla, firma) sobreviven
AMARILLO|contracts/src/veridicus_contracts/model_calls.py:70|ModelCall.provider es str y los opcionales None frente a un esquema cerrado y no anulable
AMARILLO|contracts/tests/typing/test_role_translation.py|Prueba de datos guardada en tests/typing/
INFORME: docs/loop/revisiones/U01-T08/ronda-1.md
```
