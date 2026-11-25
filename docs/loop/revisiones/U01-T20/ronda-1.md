# Ronda 1 — U01-T20

VEREDICTO: NO-VERDE

Todos los CA pasan en mi propia ejecución. Bloquea un solo NARANJA: la prueba de control de sin red no puede fallar por la regla que dice proteger.

Lo corrí en `/workspace/.worktrees/U01-T20`, HEAD ce37401, con `node_modules` instalado por mi `npm ci`. Al terminar, el worktree está limpio: `git status --short` vacío, y solo quedan `coverage/` y `node_modules/`, que ya existían y están ignorados.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1a | ci | `npm --prefix /workspace/.worktrees/U01-T20/contracts/ts ci` | pasa: `added 176 packages`, 0 vulnerabilidades, lockfile sin cambios |
| 1b | test ≤ 60 s, ≥ 80 % de líneas | `timeout 60 npm --prefix .../contracts/ts test` | pasa: 129/129 en 1,44 s; líneas 100 % (105/105), ramas 96,25 %; canonical.ts al 100 % en `coverage-summary.json` |
| 1c | typecheck | `npm --prefix .../contracts/ts run typecheck` | pasa, 0 errores |
| 1d | lint | `npm --prefix .../contracts/ts run lint` | pasa, 0 errores |
| 1e | gen:check | `npm --prefix .../contracts/ts run gen:check` | pasa: `gen_ts: 4 archivos al día` y `generated/console.ts al día` |
| 2 | audit | `npm --prefix .../contracts/ts audit --audit-level=high` | pasa: `found 0 vulnerabilities` |
| 3 | suite Python, mismos fixtures | `timeout 120 uv run --frozen --offline --directory .../contracts pytest tests -q --no-cov --durations=15 -p no:randomly` | pasa: 2619 passed (31,0 s), con `node_modules` presente |
| 3b | las dos listas de fixtures | Python: `fixtures(Path('.'))` de `fixture_coverage.py`. TS: `vitest run --reporter=verbose test/verdicts.test.ts` | 67 y 67, los mismos nombres en el mismo orden; `SOLO_PYTHON` vacía; 69/69 pruebas en verde |
| 4 | alcance del diff | `git -C /workspace/.worktrees/U01-T20 diff --name-only feat/b1-contratos...HEAD` | pasa. Todo está bajo `contracts/ts/` más la bitácora, salvo tres rutas que autoriza E-38: `checks/_contratos.py`, `tests/checks/test_contratos_recorrido.py` y `tests/checks/test_naming.py` |
| 5 | sin cambios al clúster | `bash .../scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T20` | pasa: `0 apariciones` |

## Los puntos del encargo

1. **E-37.** Leí las opciones efectivas de `createAjv()` cargando `src/registry.ts` en Node con un *resolver* en línea:
   - `strict`, `strictSchema`, `strictNumbers` y `strictTuples` quedan en `true`; `strictRequired` y `strictTypes` en `false`. `validateSchema` y `validateFormats` quedan en `true`, `allErrors` en `false`, `unicodeRegExp` en `true`, y no hay `loadSchema`. Solo se apagaron esas dos reglas.
   - Sondas sobre esquemas en memoria. Fallan: `minLenght` anidada, `x-veridicus-nueva` en la raíz y anidada, `format: formato-inventado`, un `prefixItems` sin `minItems`/`maxItems` y `maximum: NaN`. Compilan: un `required` suelto y `x-veridicus-limit`.
2. **NFR10.16.** Son 67 y 67, con nombres idénticos. Un contrato que la tabla no tiene es `expect.fail`, nunca un salto (`verdicts.test.ts:88`).
3. **Sin red.** El *setup* sustituye las seis salidas que pide la tarea. La prueba de control, en cambio, no demuestra que el *setup* esté conectado: es F-01.
4. **K-62.**
   - Python (`sha256_jcs`) da 200 de 200, y `vec-002 {'limite': -0.0}` da `b17af95d…bfbc27`.
   - TS (`sha256Jcs` cargado en Node) da 200 de 200, `Object.is(-0)` es `true` y sale la misma huella.
   - `effective-config.valid.json` da `b22a9783…787553` en las dos mitades, igual que `.sha256`.
   - Con una perturbación, la huella cambia. La prueba compara cada huella con la guardada, así que falla si una cambia.
5. **E-38.** `_contratos.py` queda al 100 % (15 sentencias, 10 ramas) en la corrida con cobertura. `test_naming.py:40` fija la lista exacta con `ts`. La única guardia que cambia es la línea `ts/x.json` de F-05, que E-38 sustituye; `build`, `dist`, `node_modules` y `src` se siguen recorriendo.
6. **V-SUITE.** `cat /proc/loadavg` daba `0.85 0.92 0.69` justo antes. `timeout 60 uv run … pytest tests -q` dio 2619 passed en **46,70 s**, por debajo de 60 s. Sí, algo de la rama lo encarece: es F-02.
7. **P-T20-4 y P-T20-7.** Ninguna esconde un defecto.
   - P-T20-4: `x-veridicus-version` solo se quita de la raíz de la copia, igual que `_desconocidas` de `validators.py:135`. Anidada sigue fallando (prueba en `registry.test.ts:185`), y con `createAjv().compile` directo también falla. Los 7 esquemas que lo llevan lo tienen en la raíz.
   - P-T20-7: la copia temporal se borra en `finally`. Una referencia sin reescribir hace fallar a openapi-typescript con ENOENT, como muestra el rojo de la bitácora (línea 876), así que no pasa en silencio.
8. **El rojo.** Está literal.
   - Ronda 1: todo falla por módulo ausente (`importarOFallar`). Es la convención aceptada en U01-T18 (ronda 1, línea 61).
   - Ronda 2: se repitió con los 129 archivos de prueba finales. Las dos pruebas de E-37 fallan por la regla: `strictTypes` en `required` y `expected true to be false` en `strictRequired`.
   - Python: `test_contratos_recorrido` falla por la regla.
   - El defecto de evidencia de la bitácora es F-03.

## Hallazgos

### F-01 · NARANJA · contracts/ts/test/no-network.test.ts:8 · La prueba de control importa el *setup* y se activa sola
`no-network.test.ts` importa `MENSAJE_SIN_RED` de `./setup-no-network`, y esa importación ejecuta las sustituciones del módulo. Si alguien quita `setupFiles` de `vitest.config.ts:8`, esta prueba sigue en verde mientras `registry`, `verdicts` y las demás quedan con red. Nada fija que el *setup* esté conectado.

Lo demostré con:
`node --input-type=module -e 'import "/workspace/.worktrees/U01-T20/contracts/ts/test/setup-no-network.ts"; try { await fetch("https://veridicus.invalid/"); …'`
Salida: `BLOQUEADO POR LA SOLA IMPORTACION: red bloqueada por el setup de las pruebas (NFR10.4)`.

Arreglo sugerido: poner el mensaje en un módulo aparte, o comprobar en otro archivo de prueba, sin importar el *setup*, que `fetch` lanza. Otra opción es una prueba que lea `vitest.config.ts` y exija `setupFiles`.

### F-02 · AMARILLO · V-SUITE · `node_modules` entra en el sdist y encarece la suite unos 16 s
En `--durations`, los dos tiempos más altos son `test_package_map.py::test_las_dos_vias_de_construccion_dan_la_misma_rueda` (8,36 s) y `…[sdist-y-rueda]` (7,93 s). `[wheel-directa]` tarda 0,42 s.

La causa:
- `contracts/.gitignore` no lista `node_modules`; la regla está en `contracts/ts/.gitignore`.
- No hay target sdist en `pyproject.toml`.
- `_copiar` (`test_package_map.py:40`) no ignora `node_modules`.
- `du -sh` de `ts/node_modules` da 151M.

Así, tras `npm ci`, que la CI corre en el paso 8, el sdist arrastra la mitad TS. Sigue por debajo de 60 s, pero el margen con carga es poco. Leído y medido; no construí el sdist para no escribir en el árbol.

### F-03 · AMARILLO · docs/loop/bitacoras/U01-T20.md:23 · Una evidencia prometida que no está
La bitácora dice que «el rojo por la regla se muestra después con mutaciones de control (sección Verde)». Esa sección solo trae el control de ESLint (línea 888). No hay mutación para `loaders` (clave repetida), `canonical` (K-62) ni las extensiones. Además cita commits anteriores al rebase (15a89ef, f73c7cd). Los objetos existen y las pruebas de ts son idénticas a las de 070567f, pero conviene corregir el texto.

### F-04 · AMARILLO · contracts/ts/test/verdicts.test.ts:121 · La igualdad de las listas se compara a mano
La igualdad entre las dos listas de fixtures solo se comprueba por un recuento a mano. Además, un `reject` en TS no comprueba la causa, como sí hace `fixture_coverage._problemas_del_fixture`. Sugerencia: fijar la lista o su recuento en una prueba.

### F-05 · AMARILLO · contracts/ts/src/registry.ts:24 · `DATA_DIRS` no está fijada contra pyproject
`DATA_DIRS`, y `DIRECTORIOS` de `gen-types.mjs:26`, repiten el `include` de `pyproject.toml` sin ninguna prueba que los compare. Un directorio de datos nuevo no se registraría en TS sin que nada falle.

### F-06 · AMARILLO · contracts/ts/test/setup-no-network.ts:16 · Salidas a la red sin cubrir
Quedan fuera `http.get`/`https.get` (usan el `request` interno, no la propiedad sustituida), `tls.connect` y `net.Socket#connect`. La tarea solo pide las seis que sí están. Es una lectura del código, no lo ejecuté.

### F-07 · AMARILLO · contracts/src/veridicus_contracts/checks/_contratos.py:13 · La exención vale a cualquier profundidad
`ts` en `EXCLUIDOS` excluye un `ts/` a cualquier profundidad (por ejemplo `api/ts/`), igual que los demás nombres. La prueba nueva solo cubre la raíz.

## Tareas candidatas (defectos reales fuera de alcance)
- Sumar `node_modules/` (o `ts/`) a `contracts/.gitignore` o a un `exclude` del sdist, y a `IGNORAR_EN_COPIA` de `tests/test_package_map.py`. Es F-02: hoy el sdist construido tras `npm ci` incluye 151 MB de la mitad TS.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/ts/test/no-network.test.ts:8|La prueba de control importa el setup y se activa sola: no demuestra que setupFiles esté conectado
AMARILLO|V-SUITE (tests/test_package_map.py, contracts/.gitignore)|node_modules entra en el sdist y encarece la suite unos 16 s
AMARILLO|docs/loop/bitacoras/U01-T20.md:23|Mutaciones de control prometidas que no están, y commits anteriores al rebase
AMARILLO|contracts/ts/test/verdicts.test.ts:121|La igualdad de las listas de fixtures solo se compara a mano, y el reject no comprueba su causa
AMARILLO|contracts/ts/src/registry.ts:24|DATA_DIRS y DIRECTORIOS no están fijadas contra pyproject
AMARILLO|contracts/ts/test/setup-no-network.ts:16|Sin cubrir http.get, https.get, tls.connect y Socket#connect
AMARILLO|contracts/src/veridicus_contracts/checks/_contratos.py:13|La exención ts vale a cualquier profundidad
INFORME: docs/loop/revisiones/U01-T20/ronda-1.md
```
