# Ronda 1 — U01-T06

VEREDICTO: NO-VERDE

Hay dos NARANJA y ningún ROJO. Los seis criterios pasan con mis propias corridas. C7 es idéntico al bloque C7 de `contract-summary.md` (líneas 1682–1714). El diff toca solo los cuatro archivos permitidos. Quedan dos defectos: C7 acepta una nota o una reformulación vacías, lo que BR4.4 prohíbe, y en el módulo guardia sobrevive un mutante.

Hash de la tarea comprobado: `sha256sum /workspace/docs/loop/tareas/U01-T06-sugerencia-de-revision.md` da `cca5b6d5…80233e`, que coincide. Revisé la rama `tarea/U01-T06` en `d0ec0c0`, con un solo commit sobre `feat/b1-contratos`.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | C7 y sus *fixtures*, y la guardia | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T06/contracts pytest tests/contracts/test_review_suggestion.py tests/checks/test_suggestion_conditions.py --no-cov -q` | pasa, `37 passed` |
| 2 | AUTONOMIA-05 entera | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T06/contracts pytest tests/guards/test_autonomia_05.py --no-cov -q` | pasa, `20 passed`, sin filtro de marcador |
| 3 | 100 % de ramas | `… pytest tests/checks/test_suggestion_conditions.py --cov-fail-under=0 -q` y luego `… coverage report --include=src/veridicus_contracts/checks/suggestion_conditions.py --fail-under=100 --show-missing` | pasa: 72 sentencias, 30 ramas, 0 parciales, 100 %. No hay `pragma`, `skip` ni `xfail` (lo busqué con grep) |
| 4 | Tipos y *lint* | `… mypy --strict src` y `… ruff check .` | pasa: `Success: no issues found in 8 source files` y `All checks passed!` |
| 5 | Solo sus archivos | `git -C /workspace/.worktrees/U01-T06 diff --name-only feat/b1-contratos...HEAD` | pasa: los 3 archivos de T06 y la bitácora |
| 6 | Sin aplicar al clúster | `bash /workspace/.worktrees/U01-T06/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T06` | pasa, `0 apariciones` |

Comprobaciones adicionales que pediste:
- **Archivos vetados y copia de C6:** `git diff --stat feat/b1-contratos...HEAD -- contracts/analyzer contracts/pyproject.toml contracts/uv.lock contracts/hatch_build.py contracts/tests/conftest.py contracts/tests/helpers.py …/checks/__init__.py contracts/integrity/fixtures contracts/tests/contracts contracts/tests/guards` no devuelve nada. `tests/checks/` no tiene `__init__.py` ni `conftest.py`.
- **AUTONOMIA-03:**
  - Los estados son `pending`, `accepted`, `edited` y `dismissed`.
  - Con el validador del proyecto (`helpers.validador_de`): `accepted` sin `decided_at` se rechaza; `pending` con `decided_by` se rechaza; `decided_by` que no es uuid se rechaza; `decided_at: ayer` se rechaza; `state: verdadero` se rechaza.
  - `additionalProperties: false` está en C7. Un grep de `truth|verdad|veraz|mient|falso|is_true|credib` sobre C7 no encuentra nada.
- **AUTONOMIA-05:** los 5 campos obligatorios se rechazan si faltan o están vacíos (fixtures `sin-*` y `vacio-*`). Las citas usan el `$ref` canónico, y una cita con un campo de más se rechaza.
- **Rojo primero:** la bitácora trae el rojo de T03 (31 fallos «contrato ausente») antes del verde. El orden cumple el Testing Contract.
- **Worktree:** limpio tras mis corridas. Solo hay cachés ignorados (`.coverage`, `.pytest_cache`, `__pycache__`, …).
- **Datos del piloto:** no hay ninguno en el diff ni en la bitácora.

## Hallazgos

### F-01 · NARANJA · contracts/integrity/review-suggestion.v2.json:76-82 · C7 acepta `note` y `reformulation` vacías, contra BR4.4
BR4.4 (`rules.md:239`) dice: «SI state es dismissed y note **falta o está vacía**, o SI state es edited y reformulation **falta o está vacía** ENTONCES la sugerencia es inválida». En C7, `note` y `reformulation` son `{type: string}` sin `minLength`.

Lo comprobé con el validador del proyecto, partiendo de `valid.dismissed.yaml` y `valid.edited.yaml`:
```
dismissed note vacia VALIDA
edited reformulation vacia VALIDA
```
Así, una sugerencia descartada puede guardarse sin el motivo del analista.

El texto de C7 en `contract-summary.md:1701-1702` tampoco pone `minLength`, así que el plan aprobado y BR4.4 se contradicen. La salida natural es añadir `minLength: 1` a `note` y `reformulation`, más un *fixture* negativo de cada caso vacío. Ese *fixture* pertenece a T03, que está fuera del alcance de T06. El orquestador debe decidir cómo se reparte y registrar la precisión en la tabla. La guardia `suggestion_conditions.py` tampoco exige que los dos campos no estén vacíos.

### F-02 · NARANJA · contracts/src/veridicus_contracts/checks/suggestion_conditions.py:70 · un mutante sobrevive: ninguna prueba fija `reject_reason`
Corrí 19 mutantes en memoria. Cada uno carga el módulo mutado en `sys.modules` y ejecuta `pytest tests/checks/test_suggestion_conditions.py`; el worktree no se toca. El control identidad pasa 16/16. Sobreviven 1 de 19:
```
MUTANTE 9 '!= REGLA:' -> '!= REGLA and 0:'
16 passed in 0.16s
```
La mutación anula solo la comprobación `fixture.get("reject_reason") != REGLA`. La única prueba que entra en esa rama (`test_un_fixture_negativo_que_no_ejerce_su_condicion_queda_en_rojo`) pone `expectation: accept`, así que el primer operando del `or` ya decide. La cobertura de ramas sale al 100 % aunque la segunda condición nunca se prueba sola.

El código original sí detecta el caso: con `reject_reason: BR4.1` en `dismissed-sin-note.yaml`, `comprobar_documentos` devuelve `['dismissed_con_nota: dismissed-sin-note.yaml debe rechazarse con reject_reason BR4.4']`. Ninguna prueba protege ese comportamiento. Falta un caso con `expectation: reject` y otra regla, dentro de las 8 pruebas como máximo.

Los otros 18 mutantes mueren: comparación de los estados, `then`/`else`, `not/anyOf`, igualdad frente a subconjunto, ausencia del *fixture*, `state`, presencia del campo, `payload` que no es objeto, archivos ausentes o ilegibles, y C7 que no es un objeto.

### F-03 · AMARILLO · contracts/integrity/review-suggestion.v2.json:37-40,64-67 · `hecho` de solo espacios es válido
`hecho: "   "` pasa la validación. `minLength: 1` sigue a `contract-summary`, pero «vacío» en BR4.1 admite la lectura «sin texto». Conviene una nota o una tarea candidata.

### F-04 · AMARILLO · docs/loop/bitacoras/U01-T06.md:15-18 · el rojo pegado está recortado
Solo se pegaron dos líneas de la salida y el conteo. Basta, pero la transcripción completa daría mejor evidencia.

## Tareas candidatas (defectos reales fuera de alcance)
- T03 o el orquestador: añadir los *fixtures* negativos `dismissed-note-vacia` y `edited-reformulation-vacia` cuando se resuelva F-01, y registrar la precisión de C7 (`minLength` en `note` y `reformulation`) frente a `contract-summary.md`.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/integrity/review-suggestion.v2.json:76-82|C7 acepta note y reformulation vacías, contra BR4.4
NARANJA|contracts/src/veridicus_contracts/checks/suggestion_conditions.py:70|un mutante sobrevive: ninguna prueba fija reject_reason
AMARILLO|contracts/integrity/review-suggestion.v2.json:37-40|hecho de solo espacios es válido
AMARILLO|docs/loop/bitacoras/U01-T06.md:15-18|el rojo pegado está recortado
INFORME: docs/loop/revisiones/U01-T06/ronda-1.md
```
