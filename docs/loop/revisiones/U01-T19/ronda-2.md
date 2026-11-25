# Ronda 2 — U01-T19

VEREDICTO: VERDE

Los cuatro hallazgos de la ronda 1 están resueltos y corrí yo mismo los seis criterios: todos pasan. Solo queda un AMARILLO, sobre la prueba nueva de la plantilla de PR, que no bloquea.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Pruebas de `tests/tools` | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T19/contracts pytest tests/tools --no-cov -p no:cacheprovider` | pasa: 65 passed en 7,11 s |
| 2a | V-SURFACE | `timeout 60 uv run … pytest tests/tools/test_security_surface.py --no-cov -q -p no:cacheprovider` | pasa: 17 passed |
| 2b | V-GEN | `uv run … python -m veridicus_contracts.tools.gen_ts --check` | pasa: «4 archivos al día», código 0 |
| 2c | Vectores JCS | `uv run … python -m veridicus_contracts.tools.gen_jcs_vectors --check` | pasa, código 0 |
| 2d | Huella al día | `uv run … python -m veridicus_contracts.tools.security_surface --check` | pasa, código 0 |
| 3 | Compuerta con la lista real de excepciones | `uv run … python -m veridicus_contracts.tools.audit_gate tests/data/pip-audit-vacio.json --ignore .pip-audit-ignore.yaml` | pasa, código 0 |
| 4 | Suite completa del Bolt | `timeout 600 uv run … pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2590 passed, 1 warning, 129 s |
| 5 | Rueda, tipos y *lint* | `pytest tests/test_package_map.py`, `mypy --strict src`, `ruff check .` | pasa: 8 passed, «Success: no issues found in 46 source files», «All checks passed!» |
| 6a | Sin cambios al clúster, con la raíz del worktree | `bash /workspace/.worktrees/U01-T19/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T19` | pasa: «0 apariciones en /workspace/.worktrees/U01-T19/.github /workspace/.worktrees/U01-T19/scripts.», código 0 |
| 6b | Ningún *workflow* con `--write` | `timeout 60 uv run … pytest tests/checks/test_ci_workflows.py --no-cov -q` | pasa: 41 passed |

- **Worktree:** queda limpio al terminar (`git status --porcelain` vacío). `git worktree list` no muestra ningún worktree temporal que haya quedado registrado.
- **Alcance:** el diff `18164f9...a4adbb2` no toca `tests/checks`, `checks/`, `pyproject.toml`, `uv.lock`, `conftest.py` ni `helpers.py`.

## Hallazgos de la ronda 1

- **F-01, plantilla de PR:** resuelto. La línea 27 ahora dice «credenciales de acceso al clúster» y el CA-6 da 0 apariciones con la raíz del worktree. La línea falsa de la bitácora quedó marcada como retractada (línea 65).
- **F-02, forma de `security`:** resuelto. Ahora es `[{esquema: [scopes ordenados]}]`, con las alternativas ordenadas por `json.dumps(sort_keys=True)`. Lo comprobé con una sonda sobre `_requisitos_de_seguridad`:
  - `[{sessionCookie: []}, {}]` y `[{}, {sessionCookie: []}]` dan el mismo resultado, y la alternativa anónima `{}` se conserva;
  - «todos» `[{a, b}]` y «cualquiera» `[{a}, {b}]` salen distintos;
  - los *scopes* `['y', 'x']` salen ordenados como `['x', 'y']` y se distinguen de `['x']`.

  La huella versionada solo tiene tres formas reales: `[{"sessionCookie": []}]` (39 veces), `[]` (5) y `[{"bearerAuth": []}]` (1). El orden es estable y `--check` pasa.
- **F-03, rojo literal:** resuelto.
  - `red2.txt` del scratchpad tiene 4051 líneas. Saqué las líneas 91 a 4141 de la bitácora y `diff -q` contra ese archivo no da diferencias, así que el anexo es literal.
  - `red3.txt` (68 líneas) coincide con las líneas 4151 a 4218.
  - Las pruebas no cambiaron entre el commit del rojo y el final: `git diff --stat a8f9b30 a4adbb2 -- contracts/tests` está vacío. Los 65 nombres que se recolectaron en el rojo coinciden con los del archivo final.
  - El rojo contra la implementación de la ronda 1 da 5 fallos, cada uno por su regla. El «módulo ausente» sobre la base sin herramientas lo admite la línea 142 de la tarea.
- **F-04, C1 en la prueba de comentarios y espacios:** resuelto. C1 ya entra (`test_security_surface.py:199`).

## Hallazgos nuevos

### F-05 · AMARILLO · `contracts/tests/tools/test_pull_request_template.py:30` · la prueba copia los términos del script a mano y se desalinea

La prueba busca una lista fija de subcadenas que no coincide con el patrón de `check-no-cluster-apply.sh`. Lo comprobé con `python3 -c "import re; p=r'…patrón del script…'; …"`:

| Texto de prueba | El script lo detecta | La prueba lo detecta |
|---|---|---|
| `copiar con rsync a zine` | sí | **no** (falta el término `(ssh\|scp\|rsync)…zine`) |
| `helm template del chart` | no | **sí** (la prueba es más estricta con `helm `) |

Además, si el script suma términos en U2 (B4), la prueba no los va a seguir. No bloquea, porque la CI corre el script mismo en `repo-level0.yml:55`. Lo propongo como mejora: que la prueba lea `patron=` del script o que lo ejecute con la raíz del repositorio como argumento.

## Tareas candidatas
- Ninguna nueva. Las notas de `-0.0` y de `build/` ya quedaron como K-62, como pediste, y no las cuento.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/tools/test_pull_request_template.py:30|La prueba de la plantilla copia a mano los términos del script y se desalinea con su patrón
INFORME: docs/loop/revisiones/U01-T19/ronda-2.md
```
