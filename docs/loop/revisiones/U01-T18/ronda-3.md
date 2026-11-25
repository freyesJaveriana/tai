# Ronda 3: U01-T18

VEREDICTO: NO-VERDE

Corrí yo los cinco criterios sobre `75c396c` (el código es `be77acf`) y todos pasan. Se cierra el NARANJA que dejó la ronda 2 (BR1.1, E-28). El veredicto es NO-VERDE por un solo NARANJA nuevo: `REGLAS` no tiene prueba de lista exacta y se puede debilitar sin que nada falle. El arreglo es pequeño: una aserción de igualdad contra un literal, y su rojo. El resto son AMARILLOS o candidatas y no bloquean.

Lo que comprobé y está bien:
- **Alcance:** `git diff --name-status feat/b1-contratos...HEAD` da 16 archivos, todos añadidos: los 7 módulos de `checks/`, las 6 pruebas, la bitácora y los dos *fixtures* que autoriza E-28 (`queues/fixtures/runs/run.sin-schema-version.yaml` y `run.schema-version-sin-forma.yaml`). No toca ningún contrato, `pyproject.toml`, `conftest.py` ni `registry.py`.
- **Datos sintéticos:** los dos *fixtures* son copias de `run.valid.yaml` con `SINT-0003` y `Villa Rocamora`, que está en `fixtures/synthetic-names.yaml:10`. No hay datos del piloto.
- **SHA:** los 21 commits de `feat/b1-contratos..HEAD` cubren cada SHA vigente. Cada SHA anterior lleva su cadena «reescrito … ahora X» en su línea o en las líneas que mapean cada rebase (4380, 4764, 5192). Las bases (`5f36fb4`, `8a44673`, `e55aa4d`, `f4fa5e8`, `ccd1c29`, `ccec166`, `ecdc7c3`) están en `feat/b1-contratos`.
- **Worktree:** limpio al terminar (`git status --short` vacío). El *worktree* temporal que usé para el rojo ya está borrado.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 19 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18/contracts pytest tests/checks/test_loader_usage.py … test_ci_workflows.py --no-cov -q -p no:cacheprovider` | pasa: `193 passed in 6.40s` |
| 2a | Cobertura | `timeout 300 uv run … pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: `1877 passed in 266.83s (0:04:26)`, 33 s de margen. En parte corrió junto con CA-1, *lint*, mypy y el rojo. |
| 2b | 100 % en los seis | `uv run … coverage report --include=<los seis y _recorrido.py> --fail-under=100 --show-missing` | pasa: `TOTAL 512 0 236 0 100%` |
| 3 | Suite del Bolt | `timeout 300 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: `2524 passed, 1 warning in 122.07s` |
| 4 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py --no-cov -q`; `mypy --strict src`; `ruff check .` | pasa: `8 passed`; `Success: no issues found in 41 source files`; `All checks passed!` |
| 5 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T18/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18` | pasa: `0 apariciones` |
| E-28 | Rojo final, repetido | *Worktree* temporal en `be77acf`, con los 8 contratos de `ecdc7c3~1` (`git checkout ecdc7c3~1 -- <los 8>`) y `pytest tests/checks/test_fixture_coverage.py --no-cov --tb=short -vv` | `1 failed, 21 passed`, igual que la bitácora. Falla por la regla, en la aserción, con los 8 contratos: `cli/report.schema.v2.yaml`, `errors/error-codes.v2.yaml`, `integrity/review-suggestion.v2.json`, `model_calls/model-call.v1.yaml` y los cuatro de `profiles/`. |
| E-28 | Qué recorre la prueba | `python -c "…documentos(Path('.'))…"`, imprimiendo ruta, si se leyó, `$id` y cada campo de versión | 32 documentos, los 32 legibles: el filtro `legible` no exime ninguno. Solo quedan fuera `analyzer/v1/entrada.schema.json` y `salida.schema.json`. `find` confirma que fuera del recorrido solo hay `vendor/` (terceros). Los 7 esquemas con `$id` llevan `x-veridicus-version` con la mayor de su `.vN` o `/vN`. |

## Rondas anteriores
- **Ronda 1, F-01 a F-04:** se cerraron en la ronda 2, y no vi nada que los reabra.
- **Ronda 2, F-01 (NARANJA, BR1.1): cerrado.**
  - BR1.1 está en `REGLAS` con `{required, pattern}` y tiene dos *rejects* reales. La guardia exige que cada uno falle por su causa.
  - `test_e28_br1_1_…` comprueba que sus cargas son las del *accept*, salvo `schema_version`.
  - La parte «todo contrato tiene versión semántica» la cubre `test_e28_todo_contrato_propio_…`, con su control negativo de 19 casos rotos: mayor distinta del `$id`, `$id` sin `vN`, otra clave en un esquema, `"1.0"`, enteros, `None` y una lista.
  - Excluir `analyzer/` está justificado: es la copia byte a byte de C6 (ADR-017, BR1.7 y BR1.8). El filtro `startswith("analyzer/")` solo alcanza esa carpeta de primer nivel.
- **Ronda 2, F-02 (AMARILLO):** resuelto para `-a`, pero no para `--a`. Ver F-02 abajo.
- **Ronda 2, F-03 (AMARILLO):** cerrado con `LIMITACIONES` y su prueba (P-T18-16).
- **Ronda 2, F-04 (AMARILLO):** queda como K-55.

## Listas cerradas
- **Reparto:** `REGLAS` tiene 15 BR (y 3 NFR), `REGLAS_CON_CODIGO` 29 y `EXCLUIDAS` 9. Suman 53, igual que `rules.md`: 56 `id: BR` menos 3 `Retirado`. Ninguna regla está en dos listas.
- **`SIN_PRUEBA`:** no existe, y `test_p_t18_10_no_hay_una_tercera_lista` lo fija.
- **Pruebas citadas de BR8.1 y BR8.2:** existen en `test_console.py:640/669` y `test_metrics.py:139/198`, y prueban la `logic` de `rules.md:389` y `:398`.
- **BR1.1:** ya no cita ninguna prueba; la cubren sus *fixtures*.

## Hallazgos

### F-01 · NARANJA · `contracts/tests/checks/test_fixture_coverage.py` · `REGLAS` no tiene prueba de lista exacta: se puede debilitar sin que falle nada
`REGLAS_CON_CODIGO` y `EXCLUIDAS` se comparan contra un literal; `REGLAS` no. Solo se pide `set(REGLAS) <= rechazos`, `len >= 15`, la forma del ID y la unión de las BR. Por eso nada fija:
- las entradas NFR (`NFR1.3`, `NFR10.2`, `NFRD-U1-07`), que la unión de BR no ve;
- el conjunto de palabras clave de cada regla, que es lo que decide «falla por otra regla».

Lo probé mutilando el módulo en memoria antes de correr sus pruebas:
```
uv run … python -c "[m.REGLAS.pop('NFRD-U1-07'), m.REGLAS.pop('NFR10.2'), m.REGLAS.__setitem__('BR1.1', frozenset({'required','pattern','type','enum'})), print('exit', p.main(['tests/checks/test_fixture_coverage.py','--no-cov','-q','-p','no:cacheprovider']))] if (…) else 0"
22 passed in 3.16s
exit 0
```
Así se pueden quitar dos reglas de la guardia, entre ellas NFRD-U1-07 (entradas de `audio:failed` sin texto ni audio), y ampliar las causas de BR1.1 hasta casi cualquier error, con la suite en verde. La propia regla del equipo pide que esto no sea posible: «los umbrales nunca se bajan». Se corrige con `assert guardia.REGLAS == {…literal…}`, como `CON_CODIGO`, y su rojo con la mutación de arriba.

### F-02 · AMARILLO · `checks/ci_workflows.py:24` · `_OPCIONES` sigue retrocediendo de forma exponencial con opciones de doble guion
`-{1,2}` y `[\w.-]+` se solapan en el guion, así que `--a` se puede leer como `-`+`-a` o como `--`+`a`. Medido con `PROHIBIDOS[1][1].search('kubectl'+' --a'*n+' x')`:

| n | tiempo |
|---|---|
| 12 | 0.001 s |
| 16 | 0.016 s |
| 18 | 0.065 s |
| 20 | 0.261 s |
| 22 | 1.041 s |

El tiempo se duplica con cada opción. La prueba de F-02 solo usa `-a`. La entrada son *workflows* propios que entran por PR, así que no es un *bypass*. Se arregla con `(?:--?[\w.][\w.-]*)` y con un caso `--a` en la prueba.

### F-03 · AMARILLO · P-T18-11 a P-T18-20 no están en `decisiones-humano.md`
Ese archivo solo trae P-T18-1 y P-T18-10. Las precisiones de la 11 a la 20, incluida la nueva P-T18-20, solo viven en la bitácora (`U01-T18.md:5183-5186`, `5507-5509`).
- **El fondo de P-T18-20 se sostiene:** aplica E-29 («la prueba de E-28 lee `x-veridicus-version`»).
- **Lo que añade P-T18-20:** que la mayor coincida con el `$id`. Es más estricto que la fuente, no la contradice.

Registrarlas es tarea del orquestador.

## Tareas candidatas (defectos reales fuera de alcance)
- **`queues/speech.v2.yaml:4` (C5):** declara `info.version: 1.2.0` aunque su nombre dice v2. Todos los demás `.vN` sin `$id` coinciden. La prueba de E-28 solo compara la mayor con el `$id`, no con el nombre del archivo, y `VERSION_SEMANTICA` admite ceros a la izquierda (`01.0.0`). Conviene decidir si la mayor del nombre debe coincidir.
- **K-53, CA-2:** 266,83 s de los 300 (245 s en la ronda 1, 260,79 s en la ronda 2, 263,97 s según el codificador). No bloquea.
- **Siguen abiertas:**
  - K-51, K-52 y K-55;
  - ampliar `ci_workflows` a `create`, `replace`, `patch`, `delete`, `uninstall` y `rollback`;
  - `transcript/speaker-markers.v1.yaml` e `integrity/clarification-speech.v1.yaml`, que siguen sin existir.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/tests/checks/test_fixture_coverage.py|REGLAS sin prueba de lista exacta: quitar NFR10.2 y NFRD-U1-07 o ampliar las causas de BR1.1 deja las 22 pruebas en verde
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:24|_OPCIONES retrocede de forma exponencial con opciones --a (22 opciones tardan 1.04 s)
AMARILLO|decisiones-humano.md|P-T18-11 a P-T18-20 (P-T18-20 incluida) solo están en la bitácora; el orquestador debe registrarlas
INFORME: docs/loop/revisiones/U01-T18/ronda-3.md
```
