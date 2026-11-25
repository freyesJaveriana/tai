# Ronda 2 — U01-T20

VEREDICTO: VERDE

Los cinco CA pasan sobre ef6117d en mi propia ejecución. F-01, el único NARANJA de la ronda 1, está cerrado. Solo quedan AMARILLOS que no bloquean, y uno es nuevo (F-08). El worktree queda limpio: `git status --short --ignored` solo muestra artefactos ignorados (`.venv`, `__pycache__`, `coverage/`, `node_modules/`).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1a | ci | `npm --prefix /workspace/.worktrees/U01-T20/contracts/ts ci` | pasa: 176 paquetes, 0 vulnerabilidades |
| 1b | test ≤ 60 s, ≥ 80 % de líneas | `timeout 60 npm --prefix .../contracts/ts test` | pasa: 6 archivos, 132/132, 1,38 s; líneas 100 % (105/105) |
| 1c | typecheck | `npm --prefix .../contracts/ts run typecheck` | pasa, 0 errores |
| 1d | lint | `npm --prefix .../contracts/ts run lint` | pasa, 0 errores |
| 1e | gen:check | `npm --prefix .../contracts/ts run gen:check` | pasa: `gen_ts: 4 archivos al día` y `generated/console.ts al día` |
| 2 | audit | `npm --prefix .../contracts/ts audit --audit-level=high` | pasa: 0 vulnerabilidades |
| 3 | suite Python | `timeout 600 uv run --frozen --offline --directory .../contracts pytest tests --no-cov -q` | pasa: 2619 passed en 30,92 s, con `node_modules` presente |
| 3b | recuento de fixtures | `python -c "… fixtures(Path('.'))"` | Python 67; Vitest fija 67 y 69 archivos, y pasa |
| V-SUITE | con cobertura, ≤ 60 s | `timeout 60 uv run … pytest tests -q`, con loadavg `0.75 0.61 0.62` antes | pasa: 2619 passed en 46,91 s; `_contratos.py` al 100 % (10/10 ramas) |
| 4 | alcance del diff | `git -C /workspace/.worktrees/U01-T20 diff --name-only feat/b1-contratos...HEAD` | pasa: solo `contracts/ts/`, la bitácora y las tres rutas de E-38 |
| 5 | sin cambios al clúster | `bash .../scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T20` | pasa: 0 apariciones |

## Seguimiento de los hallazgos de la ronda 1

**F-01, cerrado.**
- **Sonda de importación.** Corrí `node --input-type=module -e 'import ".../test/sin-red.ts"; … await fetch("https://veridicus.invalid/") …'`. Salida: `ERROR: fetch failed ENOTFOUND`. Importar `sin-red.ts` ya no sustituye `fetch`, que sigue siendo el nativo.
- **Sonda sin `setupFiles`.** No tengo Edit ni Write, así que no pude quitar la entrada de `vitest.config.ts` y restaurarla. Hice lo equivalente sin escribir: correr el mismo archivo con una raíz que no tiene config, y por tanto sin `setupFiles`. Comando: `vitest run --root .../contracts/ts/test --no-cache --no-fsModuleCache --coverage.enabled=false no-network.test.ts`.
  - Resultado: fallan 6 de 7 (`fetch failed`; `expected [Function] to throw`). Las seis pruebas de control solo pasan si el *setup* se carga.
  - La séptima pasa en mi sonda porque el archivo de config sigue intacto. Exige `toContain("test/setup-no-network.ts")`, y el rojo literal del codificador muestra que falla sin la entrada (bitácora, líneas 1320-1432: 7 de 7).
  - `vitest.config.ts` no cambió respecto a ce37401: el diff de `contracts` solo toca los 5 archivos de prueba.

**F-03, cerrado.** La línea 23 de la bitácora dice ahora lo que de verdad se hizo, y los SHA anteriores al rebase van marcados como reescritos.

**F-04, cerrado a medias. Lo acepto.**
- Lo que sí está: `expect(fixtures).toBe(67)` y `toHaveLength(69)` fallan si cambia el número de fixtures en el árbol. Comprobé otra vez que Python da 67 sobre HEAD.
- Lo que falta: la causa del `reject` sigue sin compararse, y el codificador lo deja así para no duplicar `REGLAS`. Queda como AMARILLO.
- No pude probarlo con una mutación porque no puedo escribir *fixtures*. La aserción es una igualdad directa.

**F-05, cerrado.** Sometí en memoria la misma expresión de `data-dirs.test.ts` al texto real de `pyproject.toml`:
- Con el texto real da los 13 directorios de `DATA_DIRS`.
- Detecta cambios: añadir `"/nuevo"` suma `nuevo`, quitar `"/ui"` lo resta y `include  =` con doble espacio da `SIN BLOQUE`, así que en los tres casos la prueba falla.
- Lo mismo en `DIRECTORIOS` de `gen-types.mjs`: quitar `ui` o añadir `nuevo` cambia la lista.
- Tiene un límite, que es F-08.

**F-02** pasó a K-69, y **F-06** y **F-07** siguen como AMARILLO anotado. Como pediste, no cuentan como bloqueo.

## Hallazgos

### F-08 · AMARILLO · contracts/ts/test/data-dirs.test.ts:17 · Directorios con dígitos o guion se pasan por alto
El patrón `/"\/([a-z_]+)"/g` ignora sin avisar un directorio con dígito o guion. Mi sonda en memoria con `"/datos2"` y `"/datos-x"` devolvió la misma lista que el original, y la prueba seguiría en verde. Hoy todos los nombres son *snake_case* sin dígitos, así que no bloquea. Sugerencia: capturar `[^"]+` y quitar después `src/…`.

### F-04 (resto) · AMARILLO · contracts/ts/test/verdicts.test.ts · La causa del `reject` no se compara
Aceptado con su motivo: compararla obligaría a duplicar la tabla `REGLAS` de `fixture_coverage.py`.

### Nota sobre el rojo de F-01
Sin el *setup*, las pruebas de control llegan a hacer una consulta DNS real a `veridicus.invalid`, un dominio reservado que responde ENOTFOUND. Solo pasa en el escenario mutado y no envía datos. Lo anoto, no es un hallazgo.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna nueva. F-02 ya está como K-69.

```
VEREDICTO: VERDE
AMARILLO|contracts/ts/test/data-dirs.test.ts:17|El patrón [a-z_]+ ignora sin avisar directorios con dígito o guion
AMARILLO|contracts/ts/test/verdicts.test.ts|La causa del reject sigue sin compararse (F-04 a medias, aceptado)
INFORME: docs/loop/revisiones/U01-T20/ronda-2.md
```
