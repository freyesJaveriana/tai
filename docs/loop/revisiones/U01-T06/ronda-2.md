# Ronda 2: U01-T06

VEREDICTO: VERDE

F-01 y F-02 están cerrados. Corrí yo los seis criterios y todos pasan. Ninguno de los 29 mutantes sobrevive, y el diff no revierte nada de la rama del Bolt.

Revisé la rama `tarea/U01-T06` en `1605393`. La tarea no cambió: su sha256 sigue siendo `cca5b6d5…80233e`. La base es `feat/b1-contratos`, que coincide con `origin/feat/b1-contratos` (`0bfaa40`).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | C7 y la guardia | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T06/contracts pytest tests/contracts/test_review_suggestion.py tests/checks/test_suggestion_conditions.py --no-cov -q` | pasa, `44 passed` |
| 2 | AUTONOMIA-05 entera | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T06/contracts pytest tests/guards/test_autonomia_05.py --no-cov -q` | pasa, `20 passed` |
| 3 | 100 % de ramas | `… pytest tests/checks/test_suggestion_conditions.py --cov-fail-under=0 -q` y luego `… coverage report --include=src/veridicus_contracts/checks/suggestion_conditions.py --fail-under=100 --show-missing` | pasa: `23 passed`; 83 sentencias, 36 ramas, 0 parciales, 100 % |
| 4 | Tipos y *lint* | `… mypy --strict src` y `… ruff check .` | pasa: `Success: no issues found in 8 source files` y `All checks passed!` |
| 5 | Solo sus archivos | `git -C /workspace/.worktrees/U01-T06 diff --name-status feat/b1-contratos...HEAD` | pasa: 7 archivos, todos nuevos (`A`). Son los 3 de T06, los 2 *fixtures* que permite P-T06-1 y las 2 bitácoras |
| 6 | Sin aplicar al clúster | `bash /workspace/.worktrees/U01-T06/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T06` | pasa, `0 apariciones` |

## Lo que pediste comprobar
- **F-01, cerrado.** C7 lleva ahora `minLength: 1` en `note` y en `reformulation`. Pasé cada *fixture* por el validador del proyecto:
  - `dismissed-note-vacia.yaml` se rechaza solo por `('minLength', '$.note')`.
  - `edited-reformulation-vacia.yaml` se rechaza solo por `('minLength', '$.reformulation')`.
  - Los cuatro `valid.*` siguen aceptándose sin errores.

  Los *fixtures* que ya existían no se tocaron: `git diff --name-status --diff-filter=MD feat/b1-contratos...HEAD -- contracts/integrity/fixtures` sale vacío. Los dos nuevos pasan el formato sintético de `cargar_fixture`.
- **F-02, cerrado.** Repetí los 19 mutantes de la ronda 1 y añadí 10 para lo nuevo. El 12 lo reescribí como `if not condicion.cumple(carga):` → `if 0:`, porque la línea original desapareció. Los 10 nuevos cubren `cumple`, `exigencia`, el `minLength >= 1`, su valor por defecto, la rama `vacio` de `_declara`, las dos condiciones nuevas y la comparación con `presente`.

  Cada mutante corrió en su propio subproceso, con el módulo mutado en memoria. Resultado: 29 de 29 mueren, y el control identidad pasa 23/23. El mutante 9, que sobrevivía en la ronda 1, ahora deja `1 failed, 22 passed`. La salida completa está en la transcripción de la llamada.
- **Tamaño del módulo de pruebas:** `grep -c -P "^def test_" …/test_suggestion_conditions.py` da `8`, dentro del máximo.
- **Nada revertido:** `git diff --name-status origin/feat/b1-contratos HEAD` solo trae altas, y `merge-base --is-ancestor origin/feat/b1-contratos HEAD` sale con código 0. No cambió ningún archivo vetado ni la copia de C6: `diff --stat` sobre `contracts/analyzer`, `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `helpers.py`, `checks/__init__.py`, `tests/contracts` y `tests/guards` sale vacío.
- **AUTONOMIA-03 y 05:** siguen como en la ronda 1. C7 no tiene ningún campo de veracidad, exige quién y cuándo fuera de `pending`, y rechaza cada uno de los 5 campos obligatorios si falta o está vacío.
- **Rojo primero:** la bitácora pega el rojo completo de esta ronda (8 fallos con su causa) antes del cambio.
- **Worktree:** queda limpio tras mis corridas (`git status --porcelain` sale vacío).

## Hallazgos
### F-03 · AMARILLO · contracts/integrity/review-suggestion.v2.json · el texto de solo espacios se acepta
Sigue en pie, ahora también para `note`: una nota de un espacio es válida (`note un espacio True`). `minLength: 1` es lo que fijan `contract-summary` y P-T06-1, así que no bloquea. El codificador lo deja como nota.

## Tareas candidatas (defectos reales fuera de alcance)
- Decidir si «vacío» en BR4.1 y BR4.4 incluye el texto de solo espacios. Si es así, añadir un `pattern` que exija algo distinto de espacio en `hecho`, `observaciones`, `note` y `reformulation`, con sus *fixtures* negativos.
- Llevar P-T06-1 a `contract-summary.md` al cerrar la etapa, como dice `decisiones-humano.md`.

```
VEREDICTO: VERDE
AMARILLO|contracts/integrity/review-suggestion.v2.json|el texto de solo espacios se acepta en hecho, observaciones, note y reformulation
INFORME: docs/loop/revisiones/U01-T06/ronda-2.md
```
