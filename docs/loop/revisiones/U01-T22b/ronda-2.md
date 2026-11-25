# Ronda 2: U01-T22b

VEREDICTO: VERDE

Corrí todos los criterios sobre 5405c91 y pasan. El rojo de esta ronda falla por la regla. Los cinco hallazgos de la ronda 1 están corregidos. Quedan dos AMARILLO que no bloquean. Rama `tarea/U01-T22b` en 5405c91. La base `feat/b1-contratos` está en 4cc54ae. El worktree queda limpio al terminar: `git -C /workspace/.worktrees/U01-T22b status --porcelain` no da salida.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Guardia y pruebas | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T22b/contracts pytest tests/checks/test_ci_workflows.py --no-cov -q` | pasa: 79 passed |
| 2a | Fila de `ci_workflows.py` (P-T22b-1) | `timeout 60 uv run … pytest tests/checks/test_ci_workflows.py --cov=veridicus_contracts.checks.ci_workflows --cov-branch --cov-report=term-missing --cov-fail-under=100 -q` | la fila queda al 100 % (84 sentencias, 40 ramas, 0 parciales). El TOTAL da 47 %, como prevé P-T22b-1: no es hallazgo |
| 2b | V-GUARD del paso 5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T22b/contracts coverage report --include="src/veridicus_contracts/checks/*,src/veridicus_contracts/profiles.py,src/veridicus_contracts/limits.py,src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100` | pasa: TOTAL 3000 sentencias y 1430 ramas al 100 %, código 0 |
| 3 | Suite completa | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T22b/contracts pytest -q --no-header -p no:warnings` | pasa: 2657 passed, 97,94 %. `loader_usage.py` al 100 % y en verde |
| 4 | Tipos y *lint* | `uv run … mypy --strict src` y `uv run … ruff check .` | pasa: «no issues found in 47 source files» y «All checks passed!» |
| 5 | AUTONOMIA-01 e `/insumos` | `bash /workspace/.worktrees/U01-T22b/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T22b` y `bash /workspace/.worktrees/U01-T22b/scripts/check-no-insumos.sh /workspace/.worktrees/U01-T22b` | pasa: 0 apariciones en los dos |
| 6 | Archivos del diff | `git -C /workspace/.worktrees/U01-T22b diff --name-only feat/b1-contratos...HEAD` | pasa: solo los 3 archivos permitidos |

**Rojo.** El archivo de pruebas de 5405c91 es el de a371c3e: `git diff --stat a371c3e 5405c91` solo toca la guardia y la bitácora. Cargué la guardia de a371c3e, que es la de la ronda 1, con `git show` y la puse en `sys.modules`. Después corrí ese archivo de pruebas: **10 failed, 69 passed**.
- Todos los fallos son por la regla: `[] == [...]`, un mensaje que nombra `>-` en vez de la acción, `\x40` sin decodificar o `4 == 3` en la cuenta de `LIMITACIONES`.
- Ninguno es un error de importación.
- Coincide con la bitácora, líneas 1380-1691. La bitácora también marca los SHA que reescribió el rebase (línea 1377).

**Sonda.** Copias de `contracts-level0.yml` en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/sonda_t22b_r2/<caso>/`, revisadas con `comprobar()`.

| Caso | Problemas | ¿Correcto? |
|---|---|---|
| copia real sin cambios | 0 | sí |
| `@v4`, `@main`, SHA de 39, SHA en mayúsculas, `docker://alpine:3.20` | 1 cada uno, en la línea 26 | sí |
| sin `permissions` | 1 | sí |
| raíz `contents: write`, `read-all`, `write-all`, sin `contents` o `{}` | 1 cada uno | sí |
| `docker://…@sha256:<64>`, también con etiqueta delante | 0 | sí |
| acción local `./…` | 0 | sí |
| `dueno/repo/ruta@<40>` | 0 | sí |
| `uses:` entre comillas dobles o simples, o con comentario al final | 1 | sí |
| **valor en la línea siguiente** | **1 (línea 27)** | **sí, antes 0** |
| **clave `"uses":`** | **1** | **sí, antes 0** |
| **`uses :`** | **1** | **sí, antes 0** |
| **flujo `{uses: …}`** | **1 (línea 31)** | **sí, antes 0** |
| `>-` y `\|-` | 1, y el mensaje nombra la acción | sí |
| ancla y alias (`&u` / `*u`) | 2: el segundo va sin línea | sí |
| `uses:` vacío | 1, con el mensaje «None» | sí |
| `uses:` dentro de un `run: \|` | 0 (antes era un falso positivo) | sí |
| *workflow* reutilizable `@v1` | 1 | sí |
| YAML que no carga, o con dos documentos | 1, con su mensaje | sí |
| **raíz `contents: read` + `packages: write`** | 1, «(packages)» | sí (P-T22b-2) |
| **raíz con dos `write` (`packages`, `id-token`)** | 1, con los dos alcances | sí |
| raíz en flujo `{contents: read, actions: write}` | 1 | sí |
| ***job* con `packages: write`, con o sin `contents: read`** | 0 | sí (P-T22b-2) |
| *job* con `contents: 'write'`, `write-all` o `<<: {contents: write}` | 1 cada uno | sí |
| `uses: algo` dentro de `with:` | 1 | falso positivo (ver F-01) |
| comentario `# actions/checkout@v4` justo antes del paso | 1, pero en la línea 25 (el comentario) y no en la 26 | ver F-02 |

**Riesgo del falso positivo en `with:`.** Hoy no se dispara.
- `grep -rn -P "^\s*['\x22]?uses['\x22]?\s*:" /workspace/.worktrees/U01-T22b/.github/workflows` solo encuentra los 6 `uses:` de los pasos.
- Las entradas de `with:` de los dos *workflows* son `fetch-depth`, `persist-credentials`, `version`, `enable-cache` y `node-version-file`. Ninguna se llama `uses`, y ninguna de las tres acciones usadas (`checkout`, `setup-uv`, `setup-node`) tiene una entrada con ese nombre.
- Si algún día aparece, **bloquea**: es un problema de `comprobar()` y la CI fallaría. Falla de forma visible y del lado seguro: nunca deja pasar una acción sin fijar. Sí obligaría a tocar la guardia.

## Hallazgos

### F-01 · AMARILLO · contracts/src/veridicus_contracts/checks/ci_workflows.py:83-93 · Una clave `uses` dentro de `with:` se marca, y no está documentado
`_usos` recorre todo el documento, así que una entrada `uses` de una acción sería un falso positivo bloqueante. Hoy no ocurre, como muestra la medición de arriba. El codificador lo avisa, pero no está en el docstring ni en `LIMITACIONES`. Conviene anotarlo, o limitar la búsqueda a `jobs.*.steps[*].uses` y `jobs.*.uses`.

### F-02 · AMARILLO · ci_workflows.py:114 · La línea puede apuntar a un comentario
La línea se busca como subcadena (`valor in lineas[i]`). Si un comentario anterior contiene el mismo texto, el mensaje cita la línea del comentario: en la sonda dio 25 en lugar de 26. El problema se reporta igual; solo cambia el número de línea.

## Hallazgos de la ronda 1
| Hallazgo | Estado | Cómo lo comprobé |
|---|---|---|
| F-01 | resuelto | las cuatro formas, el flujo y `>-` dan 1 problema con la acción nombrada, y la limitación del flujo se retiró |
| F-02 | resuelto con P-T22b-2 | los casos de la raíz y del *job* de la tabla de arriba |
| F-03 | resuelto | `_fijada` está ahora junto a `workflows()`, en las líneas 56-60 |
| F-04 | resuelto | la bitácora trae el comando literal del paso 5 (línea 1912) y CA-6 con los 3 archivos (líneas 1965-1969) |
| F-05 | resuelto | `test_f05_…` fija la limitación que queda y su cuenta (3) |

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna nueva.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:83-93|Una clave uses dentro de with: se marca (falso positivo bloqueante, hoy sin casos) y no está documentado
AMARILLO|contracts/src/veridicus_contracts/checks/ci_workflows.py:114|La línea del mensaje puede apuntar a un comentario anterior con el mismo texto
INFORME: docs/loop/revisiones/U01-T22b/ronda-2.md
```
