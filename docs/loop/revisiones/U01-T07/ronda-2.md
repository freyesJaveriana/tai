# Ronda 2 — U01-T07

VEREDICTO: VERDE

Los siete hallazgos de la ronda 1 quedaron cerrados y todos los criterios pasan con mi propia ejecución. Los 26 mutantes de la ronda 1 mueren, y también los 7 nuevos que añadí. No queda ningún ROJO ni NARANJA.

- **Tarea:** el sha256 sigue siendo `fe8ef913…5c41450`.
- **Rama:** 0e27d16, un commit de arreglo sobre el merge 4a06c59.
- **Worktree:** quedó limpio al terminar (`git -C /workspace/.worktrees/U01-T07 status --porcelain` no devuelve nada).

## Criterios de aceptación, verificados por mí
| # | Comando que corrí (rutas absolutas del worktree) | Resultado |
|---|---|---|
| 1 | `timeout 60 uv run --frozen --offline --directory …/contracts pytest tests/checks/test_error_codes.py tests/test_errors_catalog.py --no-cov` | pasa, 28 passed |
| 2 | `uv lock --check --directory …/libs/errors` | pasa, código 0 |
| 3 | `uv sync --frozen --directory …/libs/errors` | pasa, código 0 |
| 4 | `timeout 60 uv run --frozen --offline --directory …/libs/errors pytest` | pasa: 6 pruebas, 100 % de líneas |
| 5 | `uv run --frozen --offline --directory …/libs/errors mypy --strict src` | pasa, `Success` |
| 6 | `uv run --frozen --offline --directory …/libs/errors ruff check .` | pasa |
| 7 | las mismas pruebas con `--cov-fail-under=0`, y `coverage report --include=src/veridicus_contracts/checks/error_codes.py --fail-under=100` | pasa: 119 sentencias, 56 ramas, 100 % |
| 8 | los dos `grep` de la tarea | pasa, ninguna línea |
| 9 | `mypy --strict src` y `ruff check .` en `contracts` | pasa |
| 10 | `bash …/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T07` | pasa, 0 apariciones |

## Verificación de la ronda 1

**El diff no revierte nada de la rama del Bolt.**
- La base común con `feat/b1-contratos` es c2b8d71, el padre del merge.
- `git diff --stat --diff-filter=DM c2b8d71 tarea/U01-T07` no devuelve nada: ni borrados ni cambios en archivos del Bolt.
- El diff de tres puntos solo añade archivos de T07.
- Las tres eliminaciones que se ven en el diff de dos puntos (`CANDIDATAS.md` y los informes de U01-T05 y U01-T06) no son reversiones: son commits que entraron al Bolt después del merge (b058aea y 96cce0a).

**F-01, cerrado.**
- Los cinco estados ya coinciden con sus fuentes: `analysis.content_blocked` 451, `analysis.system` 503, `session.consent_missing` 409, `ethics.text_version_outdated` 422 y `report.forbidden_vocabulary` 409.
- La prueba `test_estados_que_fijan_las_fuentes_aprobadas` los fija.
- Repetí el barrido completo con un script que extrae pares estado-`code` de `construction/**/*.md` e `inception/contract-design/*.md` (prosa, tablas y respuestas de C21). Cubre 78 `code`. Quedan solo tres diferencias, y ninguna es una contradicción:
  - `anonymizer.incident` 409: es la opción B que se descartó en la pregunta 15.
  - `limits.exceeded` 422: P7 = A lo reemplazó por 413.
  - `research.invalid_type` 413: es la errata que corrige P-T07-2.

**F-02, cerrado.** Repetí los 26 mutantes en procesos aparte, sin tocar el worktree.
- Todos mueren, incluidos M17, M18, M22, M23 y M15.
- Añadí 7 mutantes más y también mueren: el control de `code` no textual, el de la base de familia, las dos mitades del control de raíz, `_familia_de` sin partir por `_`, y `RAIZ` cambiada a `Exception`.
- La línea base sigue en verde.

**F-03, cerrado.**
- En el guardia, sobre una copia del árbol real: con `SessionBlockedError(Exception)` reporta «su base debe ser SessionFamilyError (BR7.4)». Con `SpeechFamilyError(Exception)` reporta «la base de familia debe heredar de VeridicusError».
- En `libs/errors`, inyecté el módulo mutado y corrí `tests/test_hierarchy.py`. Las cuatro mutaciones mueren: hoja con base `Exception`, con base `VeridicusError`, con la familia equivocada, y familia que hereda de `Exception`. Así que `_hojas()` ya no oculta las hojas que quedan fuera de la jerarquía.

**F-04 a F-07, cerrados.**
- F-04: `anonymizer.incident` va con `http: false` y sin estado (P-T07-1), y la prueba lo afirma.
- F-05: un `code` no textual tiene su propio mensaje (E31).
- F-06: `dist/` está en `libs/errors/.gitignore`.
- F-07: la bitácora tiene corregida la sección «Propuestas y vacíos». Además declara con honestidad que no hubo rojo previo en las capas 2 y 3; el Testing Contract no lo exige.

Revisé de nuevo el contenido: no hay `detail` ni textos en las clases ni en el catálogo, y por grep no hay vocabulario de veracidad en los archivos del diff.

## Hallazgos

### F-08 · AMARILLO · checks/error_codes.py:116 · El guardia acepta herencia múltiple
El guardia solo comprueba que la familia esté entre las bases. Por eso `class X(SessionFamilyError, Exception)` pasaría. La prueba `test_hierarchy` de `libs/errors` sí lo detecta, porque exige que la lista de bases sea exactamente la familia. No bloquea.

## Tareas candidatas (defectos reales fuera de alcance)
- Algunas fuentes de otras unidades usan `code` que no están en el catálogo: `session.not_open` (409), `scenario.too_large` (413) y `transcript.too_large` (422). Están en session-lifecycle y en restos de diseños retirados, y review-01 de session-lifecycle ya los había marcado. Conviene limpiarlos en la tarea previa de cada Bolt.
- Para T15: el control (b) no ve los `code` que C21 nombra dentro de `description`, ni el `$ref ErrorCode` de C1.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/error_codes.py:116|El guardia acepta herencia múltiple con la familia (lo cubre test_hierarchy)
INFORME: docs/loop/revisiones/U01-T07/ronda-2.md
```
