# Ronda 3 — U01-T09

VEREDICTO: VERDE

Corrí yo mismo los 6 criterios y pasan todos. R-01 y R-02 están cerrados, y no queda ningún hallazgo ROJO ni NARANJA.

Comprobaciones previas:
- **Hash de la tarea:** `sha256sum` da `6cf3570a…1a5`, igual que antes.
- **Rama:** dc174d3. El commit nuevo solo toca `profiles.py` (quita 2 líneas de `_MOTIVOS`), `tests/test_profiles.py` (una prueba nueva) y las bitácoras. Ningún esquema cambió desde la ronda 2.
- **Diff:** la rama del Bolt avanzó a cd702bf. Lo que cambió en ella desde f61764c son documentos (auditoría, decisiones, candidatas, informes y la tarea de T08), ninguno de T09. El diff de tres puntos solo trae los 8 archivos de T09, todo inserciones: no revierte nada. No toca `effective-config.v1.yaml` ni los archivos compartidos.
- **Worktree:** `git status --porcelain` queda vacío. `git worktree list` ya no muestra el worktree temporal del codificador.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 11 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T09/contracts pytest tests/test_profiles.py tests/contracts/test_profiles_contract.py --no-cov` | 68 passed |
| 2 | 100 % de ramas | `timeout 120 uv run … pytest tests/test_profiles.py --cov-fail-under=0`, luego `uv run … coverage report --include=src/veridicus_contracts/profiles.py --fail-under=100 --show-missing` | 61 passed; 95 sentencias, 30 ramas, 100 % |
| 3 | C2 / c18 | `timeout 60 uv run … pytest tests/contracts/test_queue_messages.py --no-cov` | 18 passed |
| 4 | Mapa de la rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov` | 7 passed |
| 5 | Tipos y *lint* | `uv run … mypy --strict src` y `uv run … ruff check .` | `Success: no issues found in 10 source files` y `All checks passed!` |
| 6 | Sin aplicar al clúster | `bash /workspace/.worktrees/U01-T09/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T09` | 0 apariciones, código 0 |

## R-01 · cerrado
Corrí las pruebas actuales contra el código y los esquemas de dcc2b16, con `mut_runner2.py dcc2b16 … tests/test_profiles.py tests/contracts/test_profiles_contract.py`.
- **Resultado:** 5 failed, 63 passed. Son las mismas 5 pruebas que pega la bitácora: F-03, F-01, F-07 (dos) y F-04.
- **Por qué 63 y no 62:** la bitácora dice 62 porque su corrida es anterior a la prueba de R-02. Esa prueba pasa sobre dcc2b16, porque los motivos ya existían.
- **Explicación del stash:** ahora es coherente. Solo se apartó `profiles.py` y los esquemas eran todavía los de la ronda 1, que es justo el estado que da rojo en F-03 y F-04.
- **Lo no reproducible queda marcado:** el bloque antiguo está rotulado como tal. La bitácora explica que las pruebas de orden fijan un comportamiento y no dan rojo, porque jsonschema ya ordena los nombres sobrantes.

## R-02 · cerrado
- `exclusiveMinimum` y `propertyNames` salieron de `_MOTIVOS`.
- `test_los_motivos_de_minproperties_y_de_const_son_exactos` fija los dos motivos exactos: `roles: {}` da `debe tener al menos un elemento` y `schema_version: "2.0.0"` da `valor distinto del exigido`.
- La cobertura sigue al 100 %.

## Mutación
Ejecutor: `mut_runner4.py` en el scratchpad del revisor, en procesos aparte y sin tocar el worktree. La línea base da 61 passed.

Corrí 57 mutantes:
- Los 34 de `profiles.py` que vienen de la ronda 1.
- Los 6 del código nuevo de la ronda 2.
- Uno por cada una de las 10 entradas que quedan en `_MOTIVOS`: `required`, `additionalProperties`, `unevaluatedProperties`, `minProperties`, `pattern`, `format`, `minimum`, `enum`, `const` y `type`.
- 7 de esquemas, incluido `minProperties: 1` de la base.

Mueren 55. Sobreviven 2, los dos equivalentes:
- `self.problems = tuple(problems)`: el argumento ya es una tupla.
- `_seguro` sobre los nombres de `required`: esos nombres salen del esquema, nunca de la instancia.

No repetí los mutantes del patrón de `api_key_ref` ni del `$ref` de precios: esos esquemas no cambiaron desde la ronda 2, donde ya morían.

## Hallazgos
Ninguno en pie.

## Tareas candidatas (defectos reales fuera de alcance)
- Siguen en pie K-08 (la copia de `destination` y `profile` en `effective-config.v1.yaml`, de T05) y K-09 (`same_family_declared`, de U11).

```
VEREDICTO: VERDE
INFORME: docs/loop/revisiones/U01-T09/ronda-3.md
```
