# Ronda 1 — U01-T18c

VEREDICTO: NO-VERDE

Todo lo que se pidió en el código pasa: CA-1 a CA-6, las sondas de E-30 y la cobertura. Lo único que bloquea es una regla de la bitácora (F-01).

## Criterios de aceptación, verificados por mí (HEAD `b322de4`, código en `be6cfb7`)
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Lecturas de vuelta y validador sin cambios | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18c/contracts pytest tests/contracts/test_correcciones_t18c.py --no-cov -p no:cacheprovider -q --color=no` | pasa: `67 passed in 0.93s` |
| 2 | Suite completa | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18c/contracts pytest tests --cov=veridicus_contracts --cov-branch --cov-report=term-missing --cov-fail-under=0 -p no:cacheprovider -q --color=no -rs` | pasa: `2325 passed, 1 warning in 323.55s`, sin ninguna F ni SKIPPED en la salida (lo comprobé con grep) |
| 3 | Cada contrato solo añade la versión | `git -C /workspace/.worktrees/U01-T18c diff feat/b1-contratos...HEAD -- contracts/cli contracts/integrity contracts/model_calls contracts/profiles contracts/errors` | pasa (diff abajo) |
| 4 | Solo los archivos permitidos | `git -C /workspace/.worktrees/U01-T18c diff --name-only feat/b1-contratos...HEAD` | pasa (lista abajo) |
| 5 | Instalación editable y rueda | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18c/contracts pytest tests/test_package_map.py --no-cov -p no:cacheprovider -q --color=no` | pasa: `8 passed in 3.35s` |
| 6 | Tipos, lint y CI | `uv run … mypy --strict src` / `uv run … ruff check .` / `bash /workspace/.worktrees/U01-T18c/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18c` | pasa: `Success: no issues found in 34 source files`, `All checks passed!`, `0 apariciones` |

**Diff literal de CA-3** (solo las líneas cambiadas, con su hunk):
```
contracts/cli/report.schema.v2.yaml            +x-veridicus-version: "2.0.0"
contracts/errors/error-codes.v2.yaml           -version: 2
                                               +version: "2.0.0"
contracts/integrity/review-suggestion.v2.json  +  "x-veridicus-version": "2.0.0",
contracts/model_calls/model-call.v1.yaml       +x-veridicus-version: "1.0.0"
contracts/profiles/effective-config.v1.yaml    +x-veridicus-version: "1.0.0"
contracts/profiles/prices.schema.v1.yaml       +x-veridicus-version: "1.0.0"
contracts/profiles/profile-base.schema.v1.yaml +x-veridicus-version: "1.0.0"
contracts/profiles/profiles.schema.v1.yaml     +x-veridicus-version: "1.0.0"
```
Cada esquema tiene un solo hunk `@@ -1,5 +1,6 @@` (C7: `-1,6 +1,7`), con la línea nueva justo después de `$id`. El catálogo tiene un hunk `-2,7 +2,7`. No cambia ningún otro campo.

**Salida literal de CA-4:**
```
contracts/cli/report.schema.v2.yaml
contracts/errors/error-codes.v2.yaml
contracts/integrity/review-suggestion.v2.json
contracts/model_calls/model-call.v1.yaml
contracts/profiles/effective-config.v1.yaml
contracts/profiles/prices.schema.v1.yaml
contracts/profiles/profile-base.schema.v1.yaml
contracts/profiles/profiles.schema.v1.yaml
contracts/src/veridicus_contracts/validators.py
contracts/tests/contracts/test_correcciones_t18c.py
contracts/tests/test_errors_catalog.py
docs/loop/bitacoras/U01-T18c.md
```
`validators.py` entra por E-30 y `test_errors_catalog.py:22` por la excepción de «Fuera», y la bitácora nombra los dos.

## Comprobaciones pedidas
1. **Versiones.** Leí los siete esquemas en Python. Cada `$id` lleva `.v2` o `/v2` (C7) y su versión es `'2.0.0'`, o `.v1` con `'1.0.0'`. El catálogo da `'2.0.0'` como cadena.
2. **E-30 en `validators.py`.** El cambio son tres líneas: la constante y `if clave == VERSION_DEL_CONTRATO and ruta == "$": continue`. Con una sonda sobre `validate_json_schema`:
   - **La acepta:** solo en la raíz. También acepta, como debe, una *propiedad* que se llama `x-veridicus-version`.
   - **La rechaza anidada en los 19 sitios que probé:** `properties`, `$defs`, `items`, `allOf`, `anyOf`, `oneOf`, `if`, `then`, `else`, `prefixItems`, `not`, `patternProperties`, `dependentSchemas`, `additionalProperties`, `propertyNames`, `contains`, `unevaluatedProperties` y `contentSchema`.
   - **Rechaza las variantes:** `x-veridicus-limit` en la raíz, `X-veridicus-version`, la clave con espacio al final o al inicio, con NBSP (U+00A0) y `x-veridicus-versio`.
   - **Lo demás sigue igual:** una clave desconocida junto a la versión se sigue rechazando, y el resto del validador no cambió.
3. **El validador acepta lo mismo que antes.**
   - `test_el_validador_da_el_mismo_resultado_con_y_sin_la_clave` compara las firmas de error, con y sin la clave, de los 9 *fixtures* de C19, C13 y C18 y de los 21 de C7. Los usa todos: no hay *fixtures* de precios.
   - Con `validate_json_schema`, cada uno de los siete esquemas da el mismo resultado con y sin la clave. Lo comprobé con una sonda.
4. **Los dos rojos.**
   - **Rojo de E-30:** lo repetí cargando el `validators.py` de `feat/b1-contratos` en lugar del nuevo y corriendo el mismo filtro `-k`. Da `1 failed, 5 passed`, con `$/x-veridicus-version: palabra clave desconocida`: falla por la regla. Que solo falle el caso positivo basta, porque el cambio de comportamiento es solo «admitir en la raíz». Los cinco negativos son guardias que no pueden fallar con el código anterior, pero sí atrapan un arreglo demasiado amplio: si se quita `ruta == "$"` falla `anidada`, y si se admite todo `x-` en la raíz falla `otra_clave`.
   - **Primer rojo (15 failed):** es completo y falla por la regla, sin errores de importación. Entre `2bcf8ac` y `103cfcd` el archivo de pruebas solo suma la sección 4, y el rojo de E-30 se corrió sobre `103cfcd`, que es idéntico al HEAD.
   - **CA-2 de la bitácora:** omite solo las líneas de puntos. No recorta ningún fallo: la línea resumen dice `2325 passed`, que coincide con mi corrida.
5. **Cobertura de `validators.py` con la suite completa:** 137 sentencias, 54 ramas, 0 parciales, 99 %. Solo quedan sin cubrir las líneas 127-128 (`Unresolvable`), que ya existían.
6. **SHA y alcance.**
   - En `feat/b1-contratos..HEAD` están `2bcf8ac`, `8343026`, `103cfcd`, `be6cfb7` y `b322de4`. Ver F-01.
   - Ningún código fuera de `contracts/` lee `version` del catálogo. En `libs/errors/` solo aparece un comentario, y `scripts/` y `.github/` no lo leen. Dentro de `contracts/src`, `veracity.py:283` lee el `version` del aviso, que es otro documento.
   - `pyproject.toml` y los umbrales no cambiaron.
   - El worktree quedó limpio al terminar: `.coverage` está ignorado por git.

## Hallazgos
### F-01 · NARANJA · `docs/loop/bitacoras/U01-T18c.md:15` · SHA reescrito sin su marca en la misma línea
Esta línea cita «commit de pruebas 5dc366f». Ese commit no está en `git log feat/b1-contratos..HEAD`: el rebase lo reescribió como `2bcf8ac`. La marca solo aparece en la línea 197, y las Notas de la tarea piden marcarlo «en la misma línea». El commit lo encontré con `grep -noP "\b[0-9a-f]{7,40}\b"` sobre la bitácora, y es el único SHA vigente o reescrito sin marca: `36d2999`, la otra cita fuera de ese rango, es la base `feat/b1-contratos`. El rojo sigue valiendo, porque el rebase solo trajo `docs/` (E-30). Corrección: añadir «(reescrito, ahora 2bcf8ac)» en la línea 15.

### F-02 · AMARILLO · `contracts/tests/contracts/test_correcciones_t18c.py:182-203` · Controles negativos de E-30 incompletos
La prueba cubre `properties`, `$defs`, `items` y `allOf`, pero no `if`/`then` ni `prefixItems`, ni las variantes de mayúsculas o espacios. Mis sondas muestran que el comportamiento es correcto en todos esos casos. Sumarlos al parametrizado fijaría ese comportamiento.

### F-03 · AMARILLO · `docs/loop/bitacoras/U01-T18c.md:242` · CA-3 sin su salida en la bitácora
La bitácora solo dice «Salida completa en el chat de la ronda», así que la evidencia no queda versionada.

## Tareas candidatas (defectos reales fuera de alcance)
- `validate_json_schema` rechaza el `x-veridicus-limit` anidado que ya traen C19 (`report.schema.v2.yaml`), C13 (`model-call.v1.yaml`) y C18 (`effective-config.v1.yaml`). Por eso `validate_instance` falla con esos tres esquemas, con la clave de versión o sin ella. El defecto es anterior a esta tarea, y la PARADA de la ronda lo atribuía solo a la versión.
- `validate_json_schema` admite cualquier valor de `x-veridicus-version` en la raíz (lo probé con `2` y con un objeto). La forma `MAYOR.MENOR.PARCHE` solo la comprueba la prueba de T18c. Para que el validador falle de verdad según BR1.1, debería comprobarla también, o hacerlo la prueba general de T18 (E-28).

```
VEREDICTO: NO-VERDE
NARANJA|docs/loop/bitacoras/U01-T18c.md:15|SHA reescrito 5dc366f sin su marca en la misma línea
AMARILLO|contracts/tests/contracts/test_correcciones_t18c.py:182-203|Controles negativos de E-30 sin if/then, prefixItems ni variantes de la clave
AMARILLO|docs/loop/bitacoras/U01-T18c.md:242|CA-3 sin su salida en la bitácora
INFORME: docs/loop/revisiones/U01-T18c/ronda-1.md
```
