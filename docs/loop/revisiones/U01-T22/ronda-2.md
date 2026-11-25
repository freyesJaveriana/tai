# Ronda 2 — U01-T22

VEREDICTO: VERDE

Corrí yo los 7 criterios sobre d06225a y todos pasan. Quedan cerrados los dos NARANJA de la ronda 1: F-01 se arregló y F-02 ya tiene su evidencia. No queda ningún ROJO ni NARANJA. El worktree está limpio: `git -C /workspace/.worktrees/U01-T22 status --porcelain` no da salida.

Rama: `tarea/U01-T22` = d06225a, sobre `feat/b1-contratos` = 40770be. El único cambio de código de esta ronda es 6ab4bb2, que suma una línea `files:` y un comentario al gancho `yamllint`. `git diff 40770be...HEAD` deja el *workflow*, `repo-level0.yml`, `contracts/.gitignore` y `test_package_map.py` byte a byte como en la ronda 1 (el *workflow* sigue en el blob 57a4c2a). Por eso la comparación con §4.13, los SHA verificados con `git ls-remote` y K-69 de la ronda 1 siguen valiendo.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | V-YAML | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T22/contracts yamllint -s ../.github/ ../.pre-commit-config.yaml`, y también la V-YAML exacta del plan | código 0 en los dos |
| 2 | Guardia de *workflows* | `timeout 60 uv run --frozen --offline --directory .../contracts pytest tests/checks/test_ci_workflows.py --no-cov -q` | 41 passed in 0.11s |
| 3 | AUTONOMIA-01 e `/insumos` | `bash .../scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T22` y `bash .../scripts/check-no-insumos.sh /workspace/.worktrees/U01-T22` | `0 apariciones` en los dos, código 0 |
| 4 | Pasos 3–7, 10–12 de §4.13 y V-ERRORS | cada uno por separado, con los comandos del *workflow* | todos pasan (detalle abajo) |
| 5 | El *workflow* sigue §4.13 | el *workflow* no cambió desde la ronda 1 (mismo blob) | pasa, como en la ronda 1 |
| 6 | El diff solo toca lo permitido | `git -C /workspace/.worktrees/U01-T22 diff --name-only feat/b1-contratos...HEAD` | los 6 archivos esperados |
| 7 | V-SUITE con `node_modules` presente | `timeout 60 uv run --frozen --offline --directory .../contracts pytest -q`, con carga `0.29 0.10 0.04` | 2619 passed in 30.11s, 97.91 % |

Detalle de CA-4:

| Paso | Resultado |
|---|---|
| 3 | `audit_gate` en verde, sobre el `pip-audit.json` de la ronda 1; los lockfiles no cambiaron |
| 5 | `coverage report ... --format=total` da 100 |
| 6 | mypy: «Success: no issues found in 47 source files»; ruff: «All checks passed!» |
| 7 | gen_ts y gen_jcs_vectors, los dos al día |
| 10 | 132 passed, 100 % de líneas, 1.32 s |
| 11 | typecheck, lint y gen:check pasan |
| 12 | «check_package: correcto en 1.9 s» |
| V-ERRORS | 6 passed con 100 %; mypy y ruff pasan |

Medí K-69 otra vez: `test_package_map.py --durations=5` da 8 passed in 3.31s, con las mismas cuatro duraciones que pegó el codificador (±0.02 s).

## Comprobación de F-01 (ronda 1)
Leí el patrón del archivo con `yaml.safe_load`: queda `^(\.github/|\.pre-commit-config\.yaml$)`, con las barras invertidas intactas. Lo probé contra `git ls-files` en una sonda con `uv run ... python -c`.

- **Entran (4):** `.github/dependabot.yml`, `.github/workflows/contracts-level0.yml`, `.github/workflows/repo-level0.yml` y `.pre-commit-config.yaml`. Eso es todo lo que revisa `repo-level0` (`yamllint -s .github/`), más el archivo que suma la V-YAML.
- **Quedan fuera (95):** 93 son de `contracts/`; los otros dos son `.yamllint.yaml` y `docker/compose.yml`. La CI tampoco revisa esos dos, y además pasan `yamllint -s` con código 0.
- **Casos borde:** `a/.pre-commit-config.yaml`, `contracts/.github/x.yml` y `.pre-commit-config.yaml.bak` quedan fuera, y un `.github/workflows/x.yml` nuevo entra.

**Cerrado.**

## Comprobación de F-02 (ronda 1)
La bitácora, en las líneas 92 a 466, trae salidas completas que coinciden con mis corridas:
- V-SUITE: 2619 passed, 97.91 %, con la tabla completa.
- V-GUARD: la tabla completa, TOTAL 100 %.
- V-TYPES, V-LINT, V-AUDIT (1 y 2), V-GEN, V-SURFACE (17 passed) y V-TS (las 4).
- V-TS-AUDIT y V-PKG (12 líneas idénticas a las mías).
- V-ERRORS (pytest, mypy y ruff).
- K-69 antes y después: el después es literal y coincide con mi corrida; el antes, ver F-01 abajo.

El SHA del cambio de código, 6ab4bb2c98d5…, está en la línea 86. Lo que todavía queda resumido va en el AMARILLO F-01 de abajo. **Cerrado.**

F-03 (ronda 1) quedó anotado para el PR en las líneas 88 a 90. No bloquea.

## Hallazgos
### F-01 · AMARILLO · docs/loop/bitacoras/U01-T22.md:95-105, 271, 323, 327 · Detalles menores de la evidencia
1. Las líneas de comando de V-GUARD y V-GEN están abreviadas: dicen `--include=<lista de V-GUARD>` y `$ ...`. Las salidas, en cambio, son literales.
2. Falta la salida de `uv sync --frozen --directory libs/errors`, que es la primera parte de V-ERRORS.
3. La salida de K-69 de antes se presenta como «literal de la ronda 1», pero ahora trae 4 duraciones, y la bitácora de la ronda 1 solo traía 2. No puedo fecharla.

   Sí reproduje la base de forma independiente en la ronda 1: con la lista y el `.gitignore` viejos, el sdist pesaba 34 MB y tardaba 7.53 s por construcción. Las cifras de antes concuerdan con eso.

Nada de esto bloquea.

## Tareas candidatas (defectos reales fuera de alcance)
- K-70 y K-71 siguen como las dejó el humano: la correctiva U01-T22b y los YAML de `contracts/`. No las cuento como hallazgo.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U01-T22.md:95-105,271,323,327|Comandos de V-GUARD y V-GEN abreviados, falta la salida de uv sync de V-ERRORS, y el K-69 de antes no se puede fechar
INFORME: docs/loop/revisiones/U01-T22/ronda-2.md
```
