# Ronda 1 — U01-T17b

VEREDICTO: VERDE

Corrí yo los seis criterios sobre `ce23ee7` (código en `5b771d7`, base `feat/b1-contratos` = `ca1baaf`) y todos pasan. Las cinco comprobaciones que pediste se cumplen. Quedan tres AMARILLOS que no bloquean: una aserción y un docstring desactualizados en `test_report_closed.py`, SHA de antes del rebase que la bitácora sigue citando, y una cifra mal contada en el resumen de CA-3. Al terminar, `git status --short` del worktree sale vacío. El worktree temporal que usé para el rojo estaba en el scratchpad y ya lo quité (`git worktree list` ya no lo muestra).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T17b/contracts pytest tests/contracts/test_correcciones_t17b.py --no-cov -p no:cacheprovider -v` | pasa: 32 passed. En los siete campos se acepta `…21:40:00Z` y se rechazan la fecha con fracción y la de desplazamiento |
| 2 | CA-2 | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T17b/contracts pytest tests --no-cov -p no:cacheprovider -q -rs` | pasa: 2155 passed, 0 skipped. La única advertencia es la de `test_socket_bloqueado`, que ya existía |
| 3 | CA-3 | `git -C /workspace/.worktrees/U01-T17b diff feat/b1-contratos...HEAD -- contracts/queues contracts/integrity contracts/model_calls contracts/cli` | pasa. Ver el detalle abajo |
| 4 | CA-4 | `git -C /workspace/.worktrees/U01-T17b diff --name-only feat/b1-contratos...HEAD` | pasa: los seis contratos, `test_report_closed.py` (la excepción nombrada), `test_correcciones_t17b.py` y la bitácora |
| 5 | CA-5 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T17b/contracts pytest tests/test_package_map.py --no-cov -p no:cacheprovider` | pasa: 8 passed |
| 6 | CA-6 | `uv run … mypy --strict src`, `uv run … ruff check .` y `bash /workspace/.worktrees/U01-T17b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T17b` | pasa: `Success: no issues found in 23 source files`, `All checks passed!` y `0 apariciones` |
| — | Cobertura de la guardia BR10.1 | `timeout 300 uv run … pytest tests/checks/test_report_closed.py -q -p no:cacheprovider --cov=veridicus_contracts.checks.report_closed --cov-branch --cov-report=term-missing --cov-fail-under=0` | `report_closed.py`: 348 sentencias y 190 ramas, todas cubiertas (100 %) |

**Lo que muestra el diff literal de CA-3:**
- Seis líneas de `pattern` añadidas, en C2 (dos), C3, C5, C7 y la llamada a modelo.
- Una línea de `pattern` cambiada en C19.
- La coma que el JSON necesita en `decided_at` (C7).
- En `at`, `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`, que P-T17b-1 (corregida en `ca1baaf`) permite.
- No cambia ningún `description`, `required` ni otra propiedad, y no se toca ningún *fixture*.

## Comprobaciones pedidas
1. **Patrón y validador: cumple.**
   - Los siete patrones son idénticos carácter por carácter al de `DateTime` en `contracts/api/console.v2.yaml:65`.
   - La prueba lee ese patrón de C1 con `load_contract(C1)…["DateTime"]["pattern"]`, en `test_correcciones_t17b.py:101-104`, y no lo copia. El literal que aparece en la línea 130 solo comprueba que C1 lo declara.
   - Para el rechazo, la prueba exige `e.validator == "pattern"` en la ruta del campo, así que no depende del verificador de formatos.
2. **El ajuste de `test_report_closed.py` no afloja nada.**
   - La aserción de `at` en la línea 216 compara ahora el objeto completo, con patrón, tope y marca. Es más estricta que antes.
   - La prueba vieja que daba por buenas `.123Z` y `-05:00` se partió en dos: una acepta solo la forma única y la otra rechaza esas dos fechas. Es exactamente E-22.
   - No cambia ningún archivo de `src/`, ni `limits.v1.yaml`, ni las demás pruebas.
3. **Fuentes aprobadas y otros `date-time`: cumple.**
   - BR8.1 (`rules.md:385`), `entities.md:149` y E16 (`functional-spec.md:379`) piden la fecha sin fracciones ni desfases. La pregunta de functional-design (opción A) dice lo mismo, y no encontré ninguna fuente que pida otra cosa para C19. `contract-summary.md:2465` solo dice `format: date-time`.
   - Con `grep -rn -e "date-time"` sobre `contracts/`, solo quedan sin patrón los tres de C6 (`analyzer/v1/`), que la tarea deja fuera.
   - Ningún *fixture* trae una fecha con fracción o desplazamiento. Lo comprobé con `grep -rnP` y un patrón de fracción o desfase.
4. **Rojo: lo repetí y coincide.** Usé un worktree temporal en el scratchpad, sobre `ca1baaf`, y cambié solo el archivo de prueba:
   - Con la prueba de `c02f8d9` salen 21 failed y 10 passed (`.FFFFFFF.........FFFFFFFFFFFFFF`).
   - Con la de `ff79063` salen 22 failed y 10 passed (`.FFFFFFFF.........FFFFFFFFFFFFFF`). La salida coincide línea por línea con la bitácora (`:154-180`), que la pega literal y completa.
   - Todos los fallos vienen de la regla:
     - `pattern None distinto del de C1` en seis campos;
     - el patrón viejo en C19;
     - `AssertionError: pattern` en la prueba de `at`;
     - `AssertionError: []` en los 14 rechazos.
   - No hay errores de importación. La prueba de `ff79063` es igual a la de HEAD (`git diff --stat ff79063 HEAD -- contracts/tests` solo muestra `test_report_closed.py`).
5. **SHA: hay SHA viejos, pero no bloquean.** Ver F-02.

## Hallazgos
### F-01 · AMARILLO · `contracts/tests/checks/test_report_closed.py:213-216` · la exención de `date-time` sin patrón para `model-call` ya no tiene prueba
Antes, la línea 216 comprobaba que `at` real tenía solo `format` y que `_problemas` daba `[]`. Con eso se probaba la rama de `report_closed.py:353` que deja pasar una cadena `date-time` sin patrón fuera del reporte. Ahora `at` lleva patrón, y `grep -n "date-time"` sobre la prueba solo da las líneas 218 y 224, así que ninguna prueba ni ningún contrato real usa esa exención. La cobertura de ramas sigue al 100 % porque coverage no mide las partes de un `and`.

Además, el docstring («cierra `at` con el formato») y el nombre de la prueba ya no describen lo que se comprueba. Lo hizo P-T17b-1 y no rompe ningún criterio. Va como candidata.

### F-02 · AMARILLO · `docs/loop/bitacoras/U01-T17b.md:15, 49, 96, 99, 126` · SHA de antes del rebase
- `d966a29`, `be54050`, `c05c24a`, `a5ddd4e` y `2c465ba` no están en `git log feat/b1-contratos..HEAD`, y tampoco en ninguna rama (`git branch -a --contains c05c24a` sale vacío).
- La línea 96 todavía dice «SHA vigentes de la rama: los de esta sección», y esos SHA son de los que ya no existen.
- La sección de las líneas 142-147 declara obsoletos todos los anteriores, y los SHA que da como vigentes (`c02f8d9`, `7f4a5ea`, `ff79063`, `5b771d7`) sí están en la rama. La evidencia que vale está entonces bien identificada.

Lo dejo como AMARILLO, igual que en U01-T15 ronda 3 (F-03) y U01-T14 ronda 2. Si esa regla del loop se aplica tal cual («citar solo SHA vigentes»), lo que hay que corregir es la frase de la línea 96.

### F-03 · AMARILLO · `docs/loop/bitacoras/U01-T17b.md:219` · resumen de CA-3 mal contado
Dice «una línea de `pattern` cambiada y siete añadidas». El diff tiene seis añadidas y una cambiada. Es un error del resumen, no del código.

## Tareas candidatas (defectos reales fuera de alcance)
- `report_closed.py:353`: con todos los `date-time` cerrados por patrón (E-22) y la guardia `datetime_format` de T17, la exención de `date-time` sin patrón fuera del reporte ya no se usa. Hay que quitarla, o fijarla con un caso sintético en la prueba y renombrar `test_el_formato_date_time_solo_cierra_una_cadena_de_model_call`, con su docstring al día.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/checks/test_report_closed.py:213-216|la exención de date-time sin patrón de model-call ya no tiene prueba ni contrato real que la use; docstring y nombre desactualizados (candidata)
AMARILLO|docs/loop/bitacoras/U01-T17b.md:15,49,96,99,126|cita SHA de antes del rebase (d966a29, be54050, c05c24a, a5ddd4e, 2c465ba) y la línea 96 todavía los llama vigentes; la sección final sí da los vigentes
AMARILLO|docs/loop/bitacoras/U01-T17b.md:219|el resumen de CA-3 dice siete patrones añadidos; son seis más uno cambiado
INFORME: docs/loop/revisiones/U01-T17b/ronda-1.md
```
