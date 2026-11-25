# Ronda 1: U01-T22b

VEREDICTO: NO-VERDE

Los seis criterios pasan. El rojo es real y lo repetí con las pruebas finales. Los tres casos de la sonda de T22 ahora fallan, y los dos *workflows* reales dan 0 problemas. Lo que bloquea es un NARANJA: hay tres formas de YAML válido que dejan pasar `actions/checkout@v4` sin ningún problema y que `LIMITACIONES` no declara.

Comprobé la base: `feat/b1-contratos` es 890f08f, que es 8a5515a más la precisión P-T22b-1. El worktree sigue limpio al terminar: `git -C /workspace/.worktrees/U01-T22b status --porcelain` no da salida.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Guardia y pruebas | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T22b/contracts pytest tests/checks/test_ci_workflows.py --no-cov -v` | pasa: 68 passed, con la prueba de los dos *workflows* reales en verde |
| 2a | Fila de `ci_workflows.py` (P-T22b-1) | `timeout 60 uv run … pytest tests/checks/test_ci_workflows.py --cov=veridicus_contracts.checks.ci_workflows --cov-branch --cov-report=term-missing --cov-fail-under=100` | la fila da 64 sentencias, 26 ramas y 0 parciales, es decir 100 %. El TOTAL da 43 %, que es lo previsto por la precisión y no cuenta como hallazgo |
| 2b | V-GUARD del paso 5, sobre la suite completa | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T22b/contracts coverage report --include="src/veridicus_contracts/checks/*,src/veridicus_contracts/profiles.py,src/veridicus_contracts/limits.py,src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100` | pasa: TOTAL 2980/1416 al 100 %, código 0 |
| 3 | Suite completa | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T22b/contracts pytest -q` | pasa: 2646 passed, cobertura 97,93 %. La guardia `loader_usage` sigue al 100 % y en verde |
| 4 | Tipos y *lint* | `uv run … mypy --strict src` y `uv run … ruff check .` | pasa: «no issues found in 47 source files» y «All checks passed!» |
| 5 | AUTONOMIA-01 e `/insumos` | `bash /workspace/.worktrees/U01-T22b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T22b` y `bash /workspace/.worktrees/U01-T22b/scripts/check-no-insumos.sh /workspace/.worktrees/U01-T22b` | pasa: 0 apariciones en los dos |
| 6 | Archivos del diff | `git -C /workspace/.worktrees/U01-T22b diff --name-only feat/b1-contratos...HEAD` | pasa: solo los 3 archivos permitidos |

**Rojo.** Cargué la guardia de la base con `git show 890f08f:…/ci_workflows.py` y la inyecté en `sys.modules`. Después corrí el archivo de pruebas final de 770d2e7, que es igual al de 9782a24, porque `git diff --stat 9782a24 770d2e7` no toca las pruebas. Resultado: **21 failed, 47 passed**. Todos fallan por la regla (`assert [] == [...]`, `0 == 1` o la cadena de `REGLA`) y ninguno por un error de importación. Coincide con la bitácora, líneas 558-1097.

**SHA frente a versión** (la tarea deja esta comprobación al revisor). Usé `git -C … ls-remote https://github.com/<acción> refs/tags/<v>`:
- `actions/checkout` v7.0.1 da `3d3c42e5…b1`;
- `astral-sh/setup-uv` v7.6.0 da `37802adc…78`;
- `actions/setup-node` v7.1.0 da `949feb24…c1`.

Los tres coinciden con lo que fijan los *workflows*.

**Sonda.** Hice copias de `contracts-level0.yml` modificadas en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/sonda_t22b/<caso>/` y corrí `comprobar()` sobre cada una, con un solo `python -c` bajo `uv run`.

| Caso | Problemas | ¿Correcto? |
|---|---|---|
| copia real sin cambios | 0 | sí |
| `@v4` | 1 (línea 26) | sí |
| sin `permissions` | 1 | sí |
| raíz con `contents: write` | 1 | sí |
| `@main`, SHA de 39, SHA en mayúsculas | 1 cada uno | sí |
| `docker://alpine:3.20` | 1 | sí |
| `docker://…@sha256:<64>` | 0 | sí |
| local `./.github/actions/x` | 0 | sí |
| `dueno/repo/ruta@<40>` | 0 | sí |
| `uses:` entre comillas dobles o simples | 1 | sí |
| `uses: …@v4 # v4` (comentario al final) | 1 | sí |
| *job* con `packages: write` y raíz en `read` | 0 | sí |
| raíz `read-all`, `write-all`, sin `contents` o `{}` | 1 cada uno | sí |
| YAML que no carga | 1, con su mensaje | sí |
| *job* con `contents: 'write'` | 1 | sí |
| *job* con `<<: {contents: write}` | 1 | sí |
| *workflow* reutilizable con `@v1` | 1 | sí |
| **valor de `uses:` en la línea siguiente** | **0** | **no** |
| **clave entre comillas: `"uses": actions/checkout@v4`** | **0** | **no** |
| **espacio antes de los dos puntos: `uses : actions/checkout@v4`** | **0** | **no** |
| `{uses: x@v4}` (flujo, limitación declarada) | 0 | declarado |
| `uses: >-` con el valor debajo | 1, pero el mensaje nombra `>-` | parcial |
| raíz `contents: read` más `packages: write` | 0 | ver F-02 |

Para los cuatro casos en 0, el cargador del paquete lee `steps[0].uses == 'actions/checkout@v4'`. Son YAML válido y fijan la acción por etiqueta.

## Hallazgos

### F-01 · NARANJA · contracts/src/veridicus_contracts/checks/ci_workflows.py:31-34,85-94 · `uses:` sin fijar que pasan sin declararse
La tarea pide que **cada** `uses:` de otro repositorio lleve un SHA. Tres formas de YAML válido dan 0 problemas y no están en `LIMITACIONES`:
- el valor en la línea siguiente;
- la clave entre comillas (`"uses":`);
- un espacio antes de los dos puntos (`uses :`).

Además, la forma `>-` sí se marca, pero el mensaje nombra `>-` y no la acción.

La causa es la misma en todos: `_USES` exige `uses:` seguido del valor en la misma línea. La única limitación nueva, la del flujo `{uses: x@v4}`, tapa un hueco que la tarea pedía cubrir. `scan_permisos` ya carga el documento, así que recorrer las claves `uses` del YAML cargado cubriría las cinco formas, aunque sin número de línea; la tarea admite las dos maneras de leerlas.

Cómo se corrige:
- leer los `uses:` del YAML cargado, o hacer las dos lecturas y comparar;
- añadir rojos en `tmp_path` para las tres formas y para el flujo;
- retirar o ajustar la limitación del flujo.

### F-02 · AMARILLO · ci_workflows.py:118-125 · Escrituras de otros alcances en la raíz no se marcan
Con la raíz `permissions: {contents: read, packages: write}` la guardia da 0 problemas, y así todos los *jobs* reciben `packages: write`. `team.md`, en Deployment, dice: «Solo el *job* de *build* tiene `packages: write`». La tarea solo excluye de la regla los permisos de escritura **de un *job***, así que esto no rompe ningún criterio. Conviene dejarlo como candidata o prueba.

### F-03 · AMARILLO · ci_workflows.py:39-44 · `_fijada` mal colocada
`_fijada` quedó entre `_DOCKER_FIJADA` y el comentario de `_OPCIONES`, sin línea en blanco. Ese comentario, que explica `_OPCIONES`, se lee ahora como si siguiera a la función. Es solo estético: ruff pasa.

### F-04 · AMARILLO · docs/loop/bitacoras/U01-T22b.md:1318,1367-1370 · Evidencia con marcador y CA-6 parcial
- La línea 1318 cita el comando como `--include=<la lista del Paso 5>` en lugar del literal.
- La salida de CA-6 se tomó antes de añadir la bitácora y muestra 2 archivos. Mi corrida da los 3 esperados.

Las salidas son coherentes con las mías, así que no es evidencia falsa.

### F-05 · AMARILLO · contracts/tests/checks/test_ci_workflows.py · Limitaciones nuevas sin prueba
Ninguna prueba fija las dos limitaciones nuevas, como sí lo hace `test_p_t18_16_…` con las de T18. Si F-01 se resuelve con el YAML cargado, la del flujo desaparece.

## Comprobaciones de las limitaciones nuevas
- «El SHA no se contrasta con la versión del comentario»: es cierto, y con `ls-remote` comprobé que los tres SHA actuales corresponden a su versión.
- «Un `uses:` en flujo no se detecta»: es cierto, pero se queda corta. Ver F-01.

## Tareas candidatas (defectos reales fuera de alcance)
- Si el humano lo decide, que la raíz no pueda declarar escrituras de otros alcances, porque `packages: write` solo debe ir en el *job* de *build* (F-02).

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/ci_workflows.py:31-34,85-94|Tres formas de YAML válido (valor en la línea siguiente, "uses": entre comillas, uses : con espacio) dejan pasar actions/checkout@v4 sin declararse como limitación
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:118-125|La raíz con contents: read más packages: write no se marca (team.md: solo el job de build)
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:39-44|_fijada quedó entre las constantes y el comentario de _OPCIONES
AMARILLO|docs/loop/bitacoras/U01-T22b.md:1318,1367-1370|Comando con marcador <la lista del Paso 5> y CA-6 tomado antes de añadir la bitácora
AMARILLO|contracts/tests/checks/test_ci_workflows.py|Las limitaciones nuevas no tienen prueba
INFORME: docs/loop/revisiones/U01-T22b/ronda-1.md
```
