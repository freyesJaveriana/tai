# Ronda 2 — U01-T09

VEREDICTO: NO-VERDE

El código y los esquemas cierran F-01 a F-07, y en mi mutación no sobrevive ningún mutante no equivalente que afecte a un nombre o a una fuga de datos. El veredicto es NO-VERDE por una sola razón: el rojo que pega la bitácora de la ronda 2 no sale del diff actual. Es un problema de evidencia, no de código.

Comprobaciones previas:
- **Hash de la tarea:** `sha256sum` da `6cf3570a…1a5`, coincide.
- **Rama:** ca4175b, con el merge 301dcc5 de `origin/feat/b1-contratos`. `git rev-parse` da f61764c tanto para la rama local como para la remota.
- **Diff:** `git diff --stat feat/b1-contratos tarea/U01-T09` (dos puntos) es idéntico al de tres puntos: 7 archivos, todos de T09 o de su bitácora, y solo inserciones. No revierte nada de la rama del Bolt. No toca `effective-config.v1.yaml`, `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `helpers.py`, `checks/__init__.py`, los *fixtures* ni las pruebas de T03.
- **Worktree:** `git status --porcelain` queda vacío al terminar.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 11 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T09/contracts pytest tests/test_profiles.py tests/contracts/test_profiles_contract.py --no-cov` | 67 passed |
| 2 | 100 % de ramas | `timeout 120 uv run … pytest tests/test_profiles.py --cov-fail-under=0` y luego `uv run … coverage report --include=src/veridicus_contracts/profiles.py --fail-under=100 --show-missing` | 60 passed; 95 líneas, 30 ramas, 100 % |
| 3 | C2 / c18 | `timeout 60 uv run … pytest tests/contracts/test_queue_messages.py --no-cov` | 18 passed |
| 4 | Mapa de la rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov` | 7 passed |
| 5 | Tipos y *lint* | `uv run … mypy --strict src` y `uv run … ruff check .` | `Success: no issues found in 10 source files` y `All checks passed!` |
| 6 | Sin aplicar al clúster | `bash /workspace/.worktrees/U01-T09/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T09` | 0 apariciones, código 0 |

## Hallazgos de la ronda 1, con mis casos adversos sobre ca4175b
| Hallazgo | Estado | Lo que salió |
|---|---|---|
| F-01 | cerrado | Las claves `x'CANARY…'y` y `a"CANARY…"b`, y una clave con comillas en el perfil y en la raíz, salen todas como `ajuste ?`, sin fuga. Una clave que se llama literalmente `CANARY_ZXQ_7731` sí sale, porque tiene forma segura y es un nombre de ajuste, no un valor; es lo mismo que en la ronda 1. |
| F-02 | cerrado | Los mutantes n.º 19 y n.º 27 de la ronda 1 mueren. `roles: {"Clave CANARY… x": "texto"}` da `papel ?, ajuste ?: tipo incorrecto`. |
| F-03 | cerrado | Con un campo sobrante en el alterno sale un solo problema: `papel fallback_provider, ajuste sobra`. Un alterno válido se acepta, y la forma y el prefijo de su clave salen bien nombrados. |
| F-04 | cerrado | `extra_top` se rechaza igual con `base` y con `analyzer`. |
| F-05 | cerrado | Cinco pruebas de precios. Un mutante propio que anula el `$ref` al token muere (`test_precios_resuelve_la_referencia_al_token_del_analizador` y la del metaesquema). |
| F-06 | cerrado | Ahora se fijan el orden por ruta, la eliminación de duplicados y el formato de `str(error)`. Los mutantes de la ronda 1 n.º 20, 21 y 35 mueren. |
| F-07 | cerrado | `base_url` da `formato no válido` y `window: 0` da `valor por debajo del mínimo`. |

Decisión del orquestador: `same_family_declared` pasa a U11 (K-09). Sigue aceptándose con `purpose: evaluation`, que es lo esperado.

## Mutación (procesos aparte; módulo cargado con exec y esquemas mutados en memoria, sin tocar el worktree)
Los ejecutores están en `/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/mut_runner4.py` (módulo y esquemas de perfiles) y `/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/mut_runner5.py` (precios). La línea base da 60 passed.

En total corrí 55 mutantes válidos:
- **Los 34 de la ronda 1 que siguen aplicando:** los n.º 17 y 18 ya no existen tras el cambio. Mueren todos menos `self.problems = tuple(problems)`, que es equivalente.
- **11 del código nuevo:** sobreviven el n.º 37 (`_seguro` sobre los nombres de `required`, que salen del esquema: equivalente) y cuatro entradas de `_MOTIVOS` (n.º 43–46, en AMARILLO).
- **10 de esquemas:**
  - sobre cerrado de la base;
  - `fallback_provider: true`;
  - `unevaluatedProperties` del analizador;
  - `const: verifier`;
  - enum de `purpose`;
  - patrón de `api_key_ref`;
  - destino cerrado;
  - `format: uri`;
  - `$ref` del token de precios;
  - sin `const` en precios.

  Mueren todos.

## Hallazgos

### R-01 · ROJO · docs/loop/bitacoras/U01-T09.md:64-75 · El rojo declarado no sale del diff actual
La bitácora pega «6 failed, 54 passed» y cuenta entre los fallos `test_los_nombres_sobrantes_salen_ordenados_…`. Corrí las pruebas actuales contra dos estados:

| Estado | Resultado | ¿Falla esa prueba? |
|---|---|---|
| código y esquemas de la ronda 1 (dcc2b16), cargados con git show | 5 failed, 55 passed | no, pasa: jsonschema ya ordena los nombres sobrantes en su mensaje |
| `profiles.py` de la ronda 1 con los esquemas nuevos | 3 failed, 57 passed | no |

Ninguno de los dos estados reproduce la salida pegada. Los 5 fallos que sí reproduzco coinciden con lo que la bitácora atribuye a F-01, F-03, F-04 y F-07, así que el rojo primero es real en lo sustancial. Pero la transcripción pegada no pudo salir del diff actual.

Para cerrarlo: volver a correr el rojo sobre el estado de la ronda 1, pegar la salida real y corregir la frase sobre qué se apartó con `git stash`. No hace falta cambiar código.

### R-02 · AMARILLO · contracts/src/veridicus_contracts/profiles.py:46-59 · Entradas de `_MOTIVOS` sin probar o inalcanzables
- **`minProperties` y `const`** (mutantes n.º 45 y 46) se alcanzan, con `roles: {}` y `schema_version: "2.0.0"`, pero las pruebas solo buscan el nombre del ajuste, no el motivo. No son equivalentes; solo cambia el texto del motivo.
- **`exclusiveMinimum` y `propertyNames`** (n.º 43 y 44) no se alcanzan: ningún esquema de perfiles usa `exclusiveMinimum`, y jsonschema informa los errores de `propertyNames` como `pattern`. Hay que quitarlas o justificarlas.

## Tareas candidatas (defectos reales fuera de alcance)
- Siguen en pie las de la ronda 1: la copia de `destination` y `profile` en `effective-config.v1.yaml` (K-08), y `same_family_declared` en U11 (K-09).

```
VEREDICTO: NO-VERDE
ROJO|docs/loop/bitacoras/U01-T09.md:64-75|El rojo declarado (6 failed, test_los_nombres_sobrantes) no sale del diff actual: reproduzco 5 failed
AMARILLO|contracts/src/veridicus_contracts/profiles.py:46-59|Motivos minProperties y const sin probar; exclusiveMinimum y propertyNames inalcanzables
INFORME: docs/loop/revisiones/U01-T09/ronda-2.md
```
