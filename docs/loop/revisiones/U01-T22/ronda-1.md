# Ronda 1 — U01-T22

VEREDICTO: NO-VERDE

Todos los criterios pasan cuando los corro yo. El NO-VERDE se debe a dos NARANJA: el gancho `yamllint` revisa todo el repositorio sin filtro y bloquea commits sobre YAML ya versionados, y la bitácora resume salidas que la tarea mandaba pegar literales. No hay ningún ROJO. El worktree queda limpio: `git status --porcelain` no da salida.

Rama `tarea/U01-T22` = adc44cd sobre `feat/b1-contratos` = 524799a. Carga antes de medir: `cat /proc/loadavg` → `0.34 0.38 0.24`.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | V-YAML | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T22/contracts yamllint -s ../.github/ ../.pre-commit-config.yaml`; también la V-YAML exacta del plan, y con `-c ../.yamllint.yaml` | pasa, código 0 (no hay `yamllint` global) |
| 2 | Guardia de *workflows* | `timeout 60 uv run --frozen --offline --directory .../contracts pytest tests/checks/test_ci_workflows.py --no-cov -q` | 41 passed in 0.10s |
| 3 | AUTONOMIA-01 e `/insumos` | `bash .../scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T22` y `bash .../scripts/check-no-insumos.sh /workspace/.worktrees/U01-T22` | `0 apariciones` en los dos, código 0 |
| 4 | Pasos de §4.13 y V-ERRORS en local | Todos, también los de red (1, 2, 8, 9 y 12), cada uno por separado | Paso 2: «No known vulnerabilities found». Paso 3: audit_gate pasa. Paso 4: 2619 passed, 97.91 %, 29.14 s. Paso 5: TOTAL 100 %. Paso 6: mypy da 0 problemas en 47 archivos; ruff «All checks passed!». Paso 7: los dos generados al día. Paso 9: 0 vulnerabilidades. Paso 10: 132 passed, 100 % de líneas, 1.32 s. Paso 11: typecheck, lint y gen:check pasan. Paso 12: «correcto en 1.2 s». V-SURFACE: 17 passed. V-ERRORS: sync, 6 passed con 100 %, mypy y ruff pasan |
| 5 | El *workflow* sigue §4.13 | `grep -n -E "run:\|uses:" .../contracts-level0.yml` | pasa (comparación abajo) |
| 6 | El diff solo toca lo permitido | `git -C /workspace/.worktrees/U01-T22 diff --name-only feat/b1-contratos...HEAD` | exactamente los 6 archivos esperados |
| 7 | V-SUITE con `node_modules` presente | `timeout 60 uv run --frozen --offline --directory .../contracts pytest -q -p no:randomly` (con `ts/node_modules` presente) | 2619 passed in 29.14s (antes de T20 eran unos 28 s) |

**CA-5, fila por fila contra §4.13.**
- Los 12 pasos están en orden, con comandos idénticos y `--frozen --offline` exactamente en los pasos sin red (3 a 7). Los pasos 1, 2 y 12 llevan solo `--frozen`, como en §4.13.
- El paso que crea `contracts/build` (K-62) va después del paso 1 y antes de `pip-audit`.
- El paso 5 usa las rutas `src/veridicus_contracts/{profiles,limits,canonical,registry}.py`, idénticas a las de V-GUARD. Comprobé que existen en el árbol y que `contracts/python/` ya no existe.
- El paso 6 usa `mypy --strict src`, igual que V-TYPES. Las dos precisiones de PD-9 están anotadas en la bitácora.
- `errors-level0` repite V-ERRORS al pie de la letra.
- No hay `--write`, ni `secrets`, ni `kube`, ni `tags`, ni `sbatch`: `grep -n -i -E "secrets|token|kube|tags|write|sbatch|ssh"` no da salida.
- Están `permissions: contents: read` y `concurrency`, y los disparadores son `pull_request` y `push` a `main`, sin etiqueta (E-41).
- Los SHA corresponden a su versión, comprobado con `git ls-remote`: checkout v7.0.1 = 3d3c42e5…, setup-uv v7.6.0 = 37802adc…, setup-node v7.1.0 = 949feb24….
- `repo-level0.yml` solo suma el paso `bash scripts/check-no-insumos.sh .`.

**K-69, medido por mí.**
- `test_package_map.py --durations=5` con `node_modules` presente da 8 passed in 3.39s.
- Reproduje la base en el scratchpad: una copia con la lista vieja y el `.gitignore` viejo.
  - Antes: `uv build` saca un sdist de 34 177 335 bytes en 7.53 s.
  - Después: 555 511 bytes en 0.48 s.
- La reducción es real. Hacen falta los dos cambios:
  - El `.gitignore` de `contracts/` es el que lee hatch para el sdist; `ts/.gitignore` no lo lee. Esto cubre `check_package` y la CI.
  - La lista `IGNORAR_EN_COPIA` cubre la copia de la prueba.
- `test_package_map.py` solo cambia esa lista.

**Pre-commit.**
- Versiones fijadas: gitleaks v8.30.1, ruff-pre-commit v0.17.6 y yamllint v1.38.0. Las tres etiquetas existen y coinciden con `uv.lock`, que trae ruff 0.17.6 y yamllint 1.38.0.
- El id `ruff-check` existe en la v0.17.6: lo comprobé en un clon del scratchpad.
- `gitleaks` usa `--config .gitleaks.toml`, y ese archivo existe.
- No hay `ruff format` (K-61).

## Hallazgos

### F-01 · NARANJA · .pre-commit-config.yaml:15-19 · El gancho `yamllint` revisa todo el repositorio y falla sobre YAML ya versionados
El gancho no tiene `files:`, así que corre sobre todo YAML que se prepara para commit. En cambio, la CI (`repo-level0`) solo revisa `.github/`.

Lo comprobé con `uv run --frozen --offline --directory .../contracts yamllint -s -c ../.yamllint.yaml -f parsable ../contracts/errors ../contracts/analyzer ../contracts/limits.v1.yaml ../contracts/profiles ../contracts/api ../contracts/queues`, que termina con código 1. Fallan:
- `contracts/errors/error-codes.v2.yaml`: decenas de `braces` y `line-length`;
- `contracts/analyzer/v1/fixtures/salida.valid.yaml:25` y `salida.incidente-anonimizacion.yaml:21`;
- `contracts/profiles/fixtures/analyzer-profile.extra-role.yaml:14-16`;
- `contracts/queues/results.v2.yaml:36`;
- seis *fixtures* de `contracts/queues/fixtures/runs/`, con líneas de 824 caracteres.

Cualquier commit que toque uno de esos archivos queda bloqueado por el gancho, y `pre-commit run --all-files` falla. Además, el gancho local queda más estricto que la CI, lo contrario de «la CI repite todo».

Arreglo dentro de alcance: acotar el gancho al alcance de la CI, por ejemplo `files: ^(\.github/|\.pre-commit-config\.yaml$)`. Arreglar esos YAML queda fuera de esta tarea.

### F-02 · NARANJA · docs/loop/bitacoras/U01-T22.md:12, 38-59 · Evidencia resumida donde la tarea pedía salidas literales
La tarea pide:
- Alcance 1: «Pega cada salida en la bitácora».
- 4b: «pega las dos salidas» de `--durations`.
- Plan de pruebas: «literales y completas … no la condenses».

La bitácora declara en la línea 12 «las largas resumidas con su última línea». Resume en una línea cada V-* del paso 23. La salida de K-69 de antes trae solo 2 de las líneas de `--durations`, y la de después es prosa («pasa de 19.58 s a 4.20 s … 1.88 s mypy cruzado …»).

Además, la línea 58 dice que CA-6 se verifica al hacer commit «(ver SHA abajo)», pero abajo no hay ningún SHA.

Las cifras coinciden con mis corridas, así que la evidencia no es falsa. Aun así, no es la que pide el contrato de pruebas. Basta con anexar con `cat >>` las salidas completas, como permite la tarea, y el SHA adc44cd.

### F-03 · AMARILLO · .github/workflows/contracts-level0.yml:101-116 · `gitleaks` duplicado y sin «acción»
El plan sí lo pide: el paso 24 dice «*job* `contracts-level0` con … y `gitleaks` sobre el repositorio (NFR12.2)». Por eso no es alcance de más.

Tiene dos detalles:
- Duplica byte a byte el paso de `repo-level0`, así que la misma comprobación corre dos veces por PR.
- El plan habla de «la acción fijada por SHA», y el codificador usó el binario con SHA-256 verificado, igual que `repo-level0`. Es equivalente y coherente con el modelo de forma.

Conviene anotar las dos cosas en el PR.

### F-04 · AMARILLO · bitácora, Rojo 1 · El rojo de la guardia es un verde declarado
El plan de pruebas lo prevé: «si no tiene un caso … dilo». El codificador lo dijo. Rojo 2 usa `grep` en vez de correr `check-no-insumos.sh`, y basta para mostrar que el paso no estaba conectado. No bloquea.

## Sonda de la guardia (punto 5 del encargo)
`ci_workflows.workflows()` sí recoge `contracts-level0.yml`: `reales: ['contracts-level0.yml', 'repo-level0.yml'] []`.

Probé copias modificadas en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/sonda_t22/`:

| Variante | Problemas que detecta la guardia |
|---|---|
| `uses: actions/checkout@v4`, sin SHA | 0 |
| `gen_ts --write` | 1 |
| sin `permissions` | 0 |
| `contents: write` | 0 |
| `KUBECONFIG` | 1 |

La guardia detecta `--write` y `kubeconfig`, pero **no** detecta una acción sin SHA ni la falta de `permissions: contents: read`. Eso contradice §4.13, línea 424: «`checks/ci_workflows.py` lo comprueba». Tampoco hay ningún caso que exija que `contracts-level0.yml` exista. Las guardias de `checks/` están fuera del alcance de esta tarea, así que lo dejo como candidata y no como hallazgo.

## Tareas candidatas (defectos reales fuera de alcance)
- **K-nueva (guardia de CI):** que `checks/ci_workflows.py` falle con un `uses:` que no esté fijado a un SHA de 40 caracteres y con un *workflow* sin `permissions: contents: read`, como ya afirma §4.13. Que `test_ci_workflows.py` exija que exista `contracts-level0.yml` (hoy solo exige `repo-level0.yml`).
- **K-nueva (YAML de contratos):** `error-codes.v2.yaml`, varios *fixtures* de `queues/runs`, `analyzer` y `profiles`, y `queues/results.v2.yaml` no pasan `yamllint -s` con `.yamllint.yaml`. Hay que decidir si se corrigen o se excluyen de forma explícita y con motivo.

```
VEREDICTO: NO-VERDE
NARANJA|.pre-commit-config.yaml:15-19|El gancho yamllint revisa todo el repositorio y falla sobre YAML ya versionados de contracts/
NARANJA|docs/loop/bitacoras/U01-T22.md:12,38-59|Evidencia resumida donde la tarea pedía salidas literales y completas; falta el SHA de CA-6
AMARILLO|.github/workflows/contracts-level0.yml:101-116|gitleaks duplicado con repo-level0 y con binario verificado en vez de acción
AMARILLO|docs/loop/bitacoras/U01-T22.md:15-17|El rojo de la guardia es un verde declarado (lo prevé el plan)
INFORME: docs/loop/revisiones/U01-T22/ronda-1.md
```
