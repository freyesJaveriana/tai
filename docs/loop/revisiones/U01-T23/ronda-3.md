# Ronda 3 — U01-T23

VEREDICTO: VERDE

Corrí yo los seis criterios sobre 0264a3c y todos pasan. F-06, F-07 y F-08 están cerrados, el rojo falla por la regla y el *workflow* pasa la guardia de 5405c91. No queda ningún ROJO ni NARANJA en pie; solo un AMARILLO que no bloquea.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | README y herramienta | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T23/contracts pytest tests/test_readme.py tests/tools/test_check_tag.py --no-cov -p no:cacheprovider -q` | pasa: 246 passed |
| 2 | Etiqueta esperada | `uv run ... python -m veridicus_contracts.tools.check_tag --tag contracts-v0.1.0` y `--tag v0.1.0` | pasa: código 0, y código 1 con un mensaje que nombra las dos etiquetas |
| 3 | V-SUITE | `timeout 60 uv run --frozen --offline --directory .../contracts pytest -p no:cacheprovider -q --no-header` | pasa: 2865 passed, 0 omitidos, 29,4 s, cobertura 97,90 % |
| 4 | El AST no cambia | `python -c` propio: `ast.dump` sin docstrings de `git show a0bde15:<f>` contra `HEAD:<f>` | pasa: IGUAL en los 15 archivos existentes, incluido `model_calls.py`; `check_tag.py` es nuevo |
| 5 | Tipos, *lint*, guardias, YAML | `mypy --strict src`, `ruff check .`, `check-no-cluster-apply.sh`, `check-no-insumos.sh`, V-YAML | pasa: sin errores, «All checks passed!», 0 apariciones, 0 apariciones, código 0 |
| 6 | Archivos del diff | `git -C /workspace/.worktrees/U01-T23 diff --name-only feat/b1-contratos...HEAD` (base común a0bde15) | pasa: solo archivos permitidos, más las dos respuestas que aceptaste; `.github` sigue con solo +12 líneas |

## Comprobaciones de los hallazgos anteriores
- **F-06 (cerrado).**
  - La fila de C13 dice 1.0.0 y el docstring de `model_calls.py` empieza por «C13 v1.0.0».
  - Contrasté las otras filas `.py` con el registro:
    - `contract-summary.md` trae `human_review.py — v2.0.0` (línea 1794), `report_ports.py — v2.0.0` (1836), `identity.py — v2.0.0` (1886), `model_calls.py — v1.0.0` (1921) y `access_log.py — v1.0.0` (2761).
    - Las secciones «Revisión 4» de C10, C11, C12, C13 y C23 (líneas 1826, 1862, 1908, 2053 y 2775) no suben ninguna versión.
    - C24 1.1.0 es fiel: la línea 2786 dice v1.0.0, pero la «Revisión 4 de C24», en la línea 2802, dice «v1.1.0 suma `count_session` (NFRD-U13-08)», y el docstring de `retention.py` dice «C24 v1.1.0».
    - Las cinco coinciden con el docstring de su módulo.
- **F-07 (cerrado).** Repetí mis casos de la ronda 2 sobre la función de HEAD:
  - una fila duplicada con C99 delante de la buena da `fila repetida de api/console.v2.yaml` más el aviso de ID equivocado;
  - una fila duplicada con el ID correcto da `fila repetida`;
  - `limits.v1.yaml` en 7.0.0 da el aviso de versión;
  - «(el del paquete)» en C13 también se detecta.
  - `versiones_del_arbol_que_no_coinciden` da `[]` con la tabla real y detecta dos versiones alteradas a la vez (`runs` 2.1.0 y `salida` 9.0.0) contra lo que declara cada archivo.
  - Solo SHA256SUMS y los 6 `.py` quedan sin contrastar con su archivo, porque no declaran versión como dato.
- **F-08 (cerrado).**
  - `workflows_que_no_coinciden` mira solo `fila.split("|")[-2]`, que es la celda «Lo corre». Lo probé cambiando solo esa celda de V-YAML a `contracts-level0.yml (corre …`: se detecta, aunque la celda del comando contiene `contracts-level0.yml`.
  - El control parametrizado cubre las 13 claves.
  - El texto sobre V-YAML es exacto: `repo-level0.yml:48-52` corre `yamllint -s .github/`, no el comando literal, y no valida `.pre-commit-config.yaml`.
- **Rojo.** `git diff 7128fe8 HEAD -- contracts/tests` está vacío. Pasé las funciones de HEAD sobre el README y el `model_calls.py` de 7128fe8:
  - el inventario da `model_calls.py: versión (el del paquete) y el registro dice 1.0.0`;
  - la aclaración de V-YAML falta (`False False`);
  - el docstring de C13 sin versión.
  - Falla por la regla, no por una importación.
- **Guardia de T22b.** El `ci_workflows.py` de 5405c91, leído con `git show` y corrido sobre el worktree, da `[]`.
- **Repositorio público.** Sin `/insumos` ni datos del piloto en el README ni en las respuestas.
- **Worktree.** Limpio.

## Hallazgos

### F-09 · AMARILLO · contracts/tests/test_readme.py (VERSION_POR_ARCHIVO, filas `.py`) · La versión de las filas `.py` no se ata a su docstring
Para los seis `.py`, la tabla fija es la única fuente. Hoy coinciden con el docstring de cada módulo («C10 v2.0.0», …, «C24 v1.1.0»), pero si un docstring sube de versión el README no fallaría. Sugerencia: leer «Cxx vX.Y.Z» de la primera línea del docstring en `version_declarada`. No bloquea.

## Tareas candidatas (defectos reales fuera de alcance)
- El correo del autor de los commits sale mal codificado en un repositorio público; conviene revisar `user.email` del contenedor (K-72).

  > Nota del orquestador: se omitió el correo, que el informe original citaba literal, por ser un dato personal. El resto es literal.
- `checks/ci_workflows.py`, que es de T22b, cita AUTONOMIA-01 pero ninguna regla BR o NFR en su docstring.

No pude escribir el informe en `docs/loop/revisiones/U01-T23/ronda-3.md` porque soy de solo lectura: el contenido es este mensaje y te toca guardarlo a ti. La fusión la decide el humano.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/test_readme.py (VERSION_POR_ARCHIVO, filas .py)|La versión de las filas .py no se ata al docstring de su módulo
INFORME: docs/loop/revisiones/U01-T23/ronda-3.md
```
