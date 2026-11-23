# Ronda 1 — U01-T07

VEREDICTO: NO-VERDE

Los 10 criterios de aceptación pasan con mi propia ejecución. Aun así quedan un ROJO y dos NARANJA. El ROJO es que cinco estados del catálogo contradicen fuentes aprobadas. Los dos NARANJA son que la función de entrada `comprobar()` del guardia pasa en vacío y que el guardia no comprueba la base de cada clase.

Antes de empezar comprobé tres cosas. El sha256 de la tarea es `fe8ef913…5c41450` y coincide con el del despacho. La rama `tarea/U01-T07` está en 5575e00, con un solo commit. El worktree quedó limpio al terminar: `git -C /workspace/.worktrees/U01-T07 status --porcelain` no devolvió nada.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Catálogo y uno a uno | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T07/contracts pytest tests/checks/test_error_codes.py tests/test_errors_catalog.py --no-cov` | pasa, 24 passed |
| 2 | El lockfile coincide | `uv lock --check --directory /workspace/.worktrees/U01-T07/libs/errors` | pasa, código 0 |
| 3 | Instalación | `uv sync --frozen --directory /workspace/.worktrees/U01-T07/libs/errors` | pasa, código 0 |
| 4 | Pruebas y cobertura | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T07/libs/errors pytest` | pasa: 6 pruebas, 100 % de líneas |
| 5 | Tipos | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T07/libs/errors mypy --strict src` | pasa, `Success` |
| 6 | *Lint* | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T07/libs/errors ruff check .` | pasa |
| 7 | 100 % de ramas | las mismas pruebas con `--cov-fail-under=0`, y luego `coverage report --include=src/veridicus_contracts/checks/error_codes.py --fail-under=100` | pasa: 103 sentencias, 46 ramas, 100 % (pero ver F-02) |
| 8 | `contracts/` no importa ni declara `veridicus_errors` (PD-7) | los dos `grep` de la tarea, con rutas absolutas | pasa, ninguna línea. Además, `grep -rn veridicus_errors` en `contracts/src` y `contracts/tests` solo encuentra un docstring y una ruta de prueba |
| 9 | Tipos y *lint* de `contracts/` | `mypy --strict src` y `ruff check .` | pasa |
| 10 | AUTONOMIA-01 | `bash /workspace/.worktrees/U01-T07/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T07` | pasa, 0 apariciones |

`libs/errors` es autocontenido: `uv.lock` solo resuelve dependencias de desarrollo de PyPI más `veridicus-errors` editable. No hay ningún `detail` ni texto en las clases ni en el catálogo. Por grep, no hay vocabulario de veracidad en ningún archivo del diff. Los umbrales de `contracts/pyproject.toml` no cambian. No hay desbordes de alcance.

## Hallazgos

### F-01 · ROJO · contracts/errors/error-codes.v2.yaml · Cinco estados contradicen fuentes aprobadas
NFR10.3 dice que «una ruta que declara un `code` con un estado distinto del catálogo pone la suite en rojo». La bitácora presenta estos cinco estados como propuestas «sin fuente», pero sí tienen fuente:

| `code` | Catálogo | Fuente aprobada |
|---|---|---|
| `analysis.content_blocked` | 502 | **451**: contract-summary C21 rev. 4 (respuesta `'451'`), U10 rules (`ContentBlocked → 451`) y U10 NFR10.9 («el estado HTTP único que declara el catálogo de U1») |
| `analysis.system` | 502 | **503**: voice/functional-spec §6, voice security-requirements NFR10 y scalability-design |
| `session.consent_missing` | 422 | **409**: text-flow/functional-spec E29 y voice/functional-spec (tabla y E14) |
| `ethics.text_version_outdated` | 409 | **422**: ethics-governance/functional-spec E7 y nfr-design/security-design |
| `report.forbidden_vocabulary` | 422 | **409**: forensic-report functional-spec (línea 312, §95), rules BR3.3 y NFR3.7 |

Cómo lo encontré: barrí las fuentes con `grep -rhoP` buscando pares estado-`code`, tanto en prosa como en tablas, en `construction/` y `inception/contract-design/`.

**Respuesta al punto 1 del codificador:**
- Todos los demás estados coinciden con alguna fuente aprobada.
- Solo quedan como propuestas sin fuente, para que T15 las contraste con C1, `run.not_in_error` (409) y `anonymizer.incident` (ver F-04).

### F-02 · NARANJA · checks/error_codes.py:180-188 · La entrada `comprobar()` pasa en vacío
Corrí 26 mutaciones en procesos aparte, con el script en mi scratchpad. Cada una sustituye el módulo en `sys.modules` y no toca el worktree. Murieron 21. Sobrevivieron estas:
- M17: quitar `comprobar_codes_usados` de `comprobar`.
- M18: dejar `CONTRATOS_CON_CODES = ()`.
- M22: quitar `comprobar_tabla_c6`.
- M23: quitar `comprobar_clases`.
- M15: ver F-05.

La causa es que la única prueba de `comprobar()` es la del árbol real, que espera `[]`, y una lista vacía también la cumple. Cualquier subcomprobación puede desconectarse sin que falle nada. El 100 % de ramas es real, pero no demuestra que la entrada detecte algo.

Arreglo propuesto: una prueba de `comprobar()` sobre una copia del árbol en `tmp_path`, con un defecto sembrado por cada subcomprobación (clase sin `code`, `error.codigo` de C6 sin traducir, `queues/x.yaml` con un `code` inventado).

### F-03 · NARANJA · checks/error_codes.py:73-126 · El guardia no comprueba la base de cada clase
PD-7 dice que el guardia lee «nombre de clase, base y atributo `code`», y BR7.4 exige «su jerarquía». Pero la base solo se usa para calcular `bases_usadas`.

Lo demostré con una mutación en mi scratchpad: cambié `class SessionBlockedError(SessionFamilyError)` por `(Exception)` y `comprobar_clases` devolvió `[]`.

`libs/errors/tests/test_hierarchy.py` tampoco lo detecta: `_hojas()` filtra por `issubclass(…, VeridicusError)`, así que una hoja fuera de la jerarquía simplemente desaparece de la lista. Un manejador que capture `VeridicusError` la convertiría en `500`.

Hoy el árbol está bien: comprobé con `ast` las 81 hojas y todas cuelgan de su familia. Arreglo propuesto: exigir que la base de cada clase con `code` sea `<Familia>FamilyError`, que esa familia herede de `VeridicusError`, y añadir un control negativo.

### F-04 · AMARILLO · error-codes.v2.yaml:54 · `anonymizer.incident` con `http: true` y 503 (punto 2)
- Los `analysis.*` con `http: true` están justificados: C21 los devuelve como respuesta (409/413/422/451/502/503/504), y `analysis.system` sale como 503 en la ruta de voz de U9.
- `anonymizer.incident` no es respuesta de ninguna ruta. Por CD-11, la corrida rechazada es `409 session.blocked` y `anonymizer.incident` es la causa (`blocked_code`) y el `codigo` de C6. El único `409 anonymizer.incident` que aparece en las fuentes es la opción B descartada de la pregunta 15. El 503 es invención.
- Debe quedar como propuesta explícita para T15 y el humano: o `http: false`, o un estado con fuente.

### F-05 · AMARILLO · checks/error_codes.py:67 · Mutante M15 vivo
Si se quita `isinstance(valor.value, str)`, la suite sigue en verde: `code = 400` todavía genera «sin clase». Es casi equivalente, pero ningún control afirma el caso de `code` no textual con su mensaje propio.

### F-06 · AMARILLO · libs/errors/.gitignore · Falta `dist/` (punto 4)
Respecto de `contracts/.gitignore`, faltan `dist/` y `.venv/`. `.venv/` ya lo cubre el `.gitignore` propio de uv. `dist/` no lo cubre nadie: el `.gitignore` raíz no tiene entradas de caché ni de *build*. Fuera de eso, el archivo es correcto y está dentro del alcance (todo `libs/errors/`).

### F-07 · AMARILLO · docs/loop/bitacoras/U01-T07.md · Falta el «antes» en las capas 2 y 3, y la nota de fuentes es inexacta (punto 3)
- El Testing Contract (PD-5 y la ordenación de team.md) solo exige rojo previo para las guardias AUTONOMIA y los contratos de datos. Las capas 2 y 3 se pueden escribir después de implementar, así que no hay NARANJA por eso.
- La tarea pedía la salida «antes y después» de cada capa, y para las capas 2 y 3 no está.
- La sección «Propuestas y vacíos» debe corregirse según F-01.

## Tareas candidatas (defectos reales fuera de alcance)
- T15: el (b) genérico solo ve `code` bajo las claves `code` y `error_code`. C21, en contract-summary, nombra los `code` dentro de `description`, y C1 los referencia con `$ref ErrorCode`. Sobre C21 tal como está aprobado, (b) pasaría en vacío. Conviene contrastarlo cuando exista el archivo.
- El catálogo tiene la pareja «413 | `research.invalid_type`» en una tabla de U12, mientras NFR-U12-02 dice 415. Es una errata en la fuente, no en esta tarea.

```
VEREDICTO: NO-VERDE
ROJO|contracts/errors/error-codes.v2.yaml:50,57,36,45,67|Cinco estados contradicen fuentes aprobadas (451, 503, 409, 422, 409)
NARANJA|contracts/src/veridicus_contracts/checks/error_codes.py:180|comprobar() pasa en vacío: mutantes M17, M18, M22 y M23 vivos
NARANJA|contracts/src/veridicus_contracts/checks/error_codes.py:73|El guardia no comprueba la base: una hoja con base Exception pasa
AMARILLO|contracts/errors/error-codes.v2.yaml:54|anonymizer.incident con http true y 503 sin fuente (CD-11)
AMARILLO|contracts/src/veridicus_contracts/checks/error_codes.py:67|Mutante M15 vivo (code no textual)
AMARILLO|libs/errors/.gitignore|Falta dist/
AMARILLO|docs/loop/bitacoras/U01-T07.md|Sin salida previa en las capas 2 y 3; la nota «sin fuente» es inexacta
INFORME: docs/loop/revisiones/U01-T07/ronda-1.md
```
