# U01-T18e: la suite de `contracts` cabe en los 60 s de la CI con margen

**Unidad:** U1 `contracts`   **Rama base:** `main` en `a8d7756`   **Destino:** PR a `main`, que fusiona el humano
**Tipo:** tarea correctiva, como U01-T18d (E-33). La pidió el humano el 2026-11-26.
**Riesgo (ML-4):** medio. Toca la CI y la velocidad de las pruebas, pero no toca guardias ni contratos. Revisa `revisor`.

---

## Problema

`contracts-level0` sale en rojo de forma intermitente en `main` y en los PR (corridas 45825410358, 45828455842 y 45835564521). El paso 4, `timeout 60 uv run --frozen --offline --directory contracts pytest`, termina con código 124 cuando lleva un 98 %. No falla ninguna prueba.

- **En la CI:** pasan unos 7 s entre el inicio del paso y la cabecera de pytest, y la suite tarda unos 53 s más. El servidor es `ubuntu-24.04`, de un repositorio privado.
- **En local:** 2920 pruebas en 35,65 s, más la construcción del paquete (`Building veridicus-contracts`) dentro del mismo `uv run`.
- **El techo:** NFR2.1 (60 s en la máquina de desarrollo y en la CI) y la meta de diseño de 20 s o menos (`security-design.md` §4.13). NFR2.1 deja la instalación fuera del límite. Ninguno de los dos cambia.

## Alcance

**Entra:**

1. **Sacar del `timeout 60` todo lo que no sea correr la suite.** Mide qué pasa en esos ~7 s de la CI: la construcción o reinstalación del paquete propio, la sincronización del entorno, la carga de complementos o la recolección. Lo que sea instalación o construcción va a un paso previo **sin red** (`--offline`), por ejemplo `uv sync --frozen --offline --directory contracts`. Así el `uv run` del paso 4 no construye nada.
   - El comando del paso 4 queda **literal**. Es el de §4.13 y lo comprueba `checks/ci_workflows.py`.
   - Si `test_ci_workflows.py` o `checks/ci_workflows.py` exigen la lista exacta de pasos, actualízalos con su prueba en rojo primero, sin aflojar ninguna comprobación existente. Explícalo en la bitácora.
2. **Acelerar la suite sin quitar trabajo,** con las reglas de U01-T18d:
   - Mide primero con `--durations` y por archivo. Las más lentas en local son `test_redos.py::test_hypothesis_techo_de_1_s…` (2,45 s), las de `test_package_map.py` (mypy por subproceso y construcción de la rueda, 0,5 a 2 s cada una), `typing/` (mypy por subproceso) y `test_security_surface.py`.
   - Las palancas permitidas son construir una sola vez lo que se repite (una rueda o un mypy compartidos por *fixture* de sesión, por ejemplo), quitar trabajo duplicado y optimizar `src/` sin cambiar su comportamiento.

**Fuera** (rechazar aunque ayude):

- Quitar, saltar, marcar o fusionar pruebas, o reducir sus casos.
- Bajar `max_examples`, `deadline`, los topes de tiempo, la cobertura o cualquier umbral.
- Subir el `timeout 60` o mover pruebas fuera del paso 4.
- Dependencias nuevas, como `pytest-xdist`, o cambios en `pyproject.toml` y `uv.lock`.
- Tocar contratos, *fixtures*, `libs/`, otros *workflows* o artefactos de `aidlc/`.

Si con lo permitido la suite no baja de 25 s en local, para y trae las cifras.

## Archivos de contexto

- `/workspace/docs/loop/bitacoras/U01-T18d.md`: la corrección anterior y su medición.
- `.github/workflows/contracts-level0.yml`, `contracts/pyproject.toml` (`addopts`) y `contracts/tests/conftest.py`.
- `contracts/src/veridicus_contracts/checks/ci_workflows.py` y `contracts/tests/checks/test_ci_workflows.py`.
- Diseño de U1: `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md` §4.13 y `nfr-requirements/security-requirements.md` NFR2.1.
- Registros de la CI: `gh run view 45835564521 --repo freyesJaveriana/tai --log-failed` (solo lectura).

## Criterios de aceptación

Corren desde `/workspace/.worktrees/U01-T18e`.

- [ ] **CA-1 (rojo y verde):** la suite completa, con el comando literal del paso 4.
  ```bash
  timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18e/contracts pytest
  ```
  Se espera: código 0 y **22 s o menos** según la línea final de pytest. La base es 35,65 s. Pega en la bitácora la medición base y la final.
- [ ] **CA-2 (nada se construye dentro del límite):** después del paso previo nuevo, el `uv run` del paso 4 no imprime `Building`, `Built`, `Installed` ni `Uninstalled`. Pega la salida de las dos invocaciones seguidas, primero la del paso previo y luego la del paso 4.
- [ ] **CA-3 (no se quitó nada):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T18e/contracts pytest --collect-only -q --no-cov
  ```
  Se espera: `2920 tests collected`, o más si añadiste pruebas para `ci_workflows`.
  ```bash
  git -C /workspace/.worktrees/U01-T18e diff --exit-code origin/main -- contracts/pyproject.toml contracts/uv.lock
  ```
  Se espera: código 0.
  ```bash
  git -C /workspace/.worktrees/U01-T18e grep -c -E "max_examples|deadline=|skip|xfail" -- contracts/tests
  ```
  Se espera: los mismos conteos que en `origin/main`.
- [ ] **CA-4 (guardias al 100 %):** el paso 5 del *workflow*, `coverage report --include=… --fail-under=100`, sale con código 0 después de CA-1.
- [ ] **CA-5:**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T18e/contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T18e/contracts ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T18e/contracts ruff format --check .
  ```
  ```bash
  uv run --frozen --offline --project /workspace/.worktrees/U01-T18e/contracts yamllint -s -c /workspace/.worktrees/U01-T18e/.yamllint.yaml /workspace/.worktrees/U01-T18e/.github/workflows/contracts-level0.yml
  ```
  ```bash
  bash /workspace/.worktrees/U01-T18e/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18e
  ```
  ```bash
  bash /workspace/.worktrees/U01-T18e/scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T18e
  ```
  ```bash
  bash /workspace/.worktrees/U01-T18e/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T18e
  ```
  Se espera: código 0 en todos, y `0 apariciones` en los tres guiones.
- [ ] **CA-6 (en la CI, lo comprueba el orquestador en el PR):** el paso 4 de `contracts-level0` pasa en **40 s o menos** de principio a fin. Así quedan al menos 20 s de margen bajo el techo.

## Notas

- **Bitácora:** `docs/loop/bitacoras/U01-T18e.md`. Incluye la medición base, el diagnóstico de dónde se iba el tiempo, cada palanca usada con su ahorro y las salidas literales de los criterios.
- **Claves de prueba:** solo `sk-sintetico-canario-7f3a91c2d4e5`. No toques `.gitleaks.toml`.
- **Datos y red:** solo datos sintéticos y sin red, salvo `uv sync` con red si el entorno lo pide.
- **Commits:** Conventional Commits en español, con el alcance `contracts` o `ci`, y el pie de tu modelo.
- **Al terminar:** haz push de `tarea/U01-T18e` y vuelve con el informe. No abras el PR ni fusiones.
