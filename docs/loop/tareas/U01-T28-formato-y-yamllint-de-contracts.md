# U01-T28: `ruff format` y `yamllint` sobre `contracts/`

> Esta tarea la redactó el orquestador a partir de las candidatas K-61 (revisión 1 de U01-T18d) y K-71 (revisión 1 de U01-T22), y de la decisión E-44 del humano (2026-11-25). Es una correctiva, y el humano la revisa antes de que se despache.
>
> **Este archivo, junto con lo que cita, es todo lo que el codificador necesita leer.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Precisa:**
- `team.md`, Code Style: «Ruff para *lint* y formato» y «`yamllint`».
- `team.md`, Way of Working: «Pre-commit local con `gitleaks`, Ruff y `yamllint`; la CI repite todo».
- El paso 24 del plan (U01-T22).

**Historias que implementa:** ninguna propia, porque U1 es `spec`.
**Depende de:** U01-T22, U01-T22b y U01-T23, todas fusionadas. Va en paralelo con U01-T27, porque no comparten archivos: esta tarea toca `contracts-level0.yml` y `.pre-commit-config.yaml`, y T27 solo toca `repo-level0.yml`. Se fusiona antes del PR del Bolt a `main`.

---

## Alcance

**Los defectos.**
- **K-61.** `uv run --frozen --offline --directory contracts ruff format --check .` falla hoy en muchos archivos de `src/` y `tests/`: hay líneas largas sin partir y comillas distintas. Ni la CI ni el *pre-commit* corren `ruff format`, así que nada lo detecta. `libs/errors` ya está formateado («2 files already formatted»).
- **K-71.** `yamllint -s -c .yamllint.yaml` falla sobre varios YAML versionados de `contracts/`. Ejemplos:
  - `errors/error-codes.v2.yaml`, por espacios dentro de las llaves;
  - `analyzer/v1/fixtures/salida.valid.yaml` y `salida.incidente-anonimizacion.yaml`, por líneas de más de 120 caracteres;
  - `queues/results.v2.yaml` y varios *fixtures* de `queues/runs`, `analyzer` y `profiles`.

  V-YAML, el *pre-commit* y `repo-level0.yml` solo miran `.github/` y `.pre-commit-config.yaml`.

**Dentro:**

> **1. Formato de Python.**
> - Corre `ruff format` sobre `contracts/` (`src/`, `tests/` y `hatch_build.py`). Esta es la **única** excepción a «edita solo con Edit/Write», y vale solo para `ruff format`. Nunca uses `ruff --fix` ni otra herramienta que reescriba.
> - El formato no cambia el código. El AST de cada `.py` tocado debe quedar idéntico antes y después: compara `ast.dump` de `git show feat/b1-contratos:<f>` contra `HEAD:<f>`, todos los archivos en un solo `python -c` (CA-3).
> - Si `ruff format` y `ruff check` se contradicen en algún archivo, para y avisa. No toques la configuración de Ruff para resolverlo.
>
> **2. YAML de `contracts/`.**
> - Corrige cada YAML versionado de `contracts/` (`git ls-files`) hasta que pase `yamllint -s -c .yamllint.yaml`. Edítalos solo con Edit o Write.
> - **Lo que cargan los datos no puede cambiar.** Para cada YAML tocado, el valor que devuelve el cargador del paquete (`veridicus_contracts.loaders`) debe ser igual antes y después. Compáralo en un solo `python -c` (CA-4). Ojo con partir cadenas largas: un escalar plegado (`>-`) o una cadena entre comillas con `\` al final de la línea deben dar exactamente el mismo texto.
> - Si un archivo no puede pasar `yamllint` sin cambiar sus datos, no lo fuerces. Exclúyelo de la regla concreta con un comentario `# yamllint disable-line rule:<regla>` y su motivo, o con una entrada en `.yamllint.yaml` que diga el archivo y el motivo. Cada exclusión queda nombrada en la bitácora.
> - Fuera de esos archivos no toques `.yamllint.yaml`, y no relajes ninguna regla global.
>
> **3. Compuertas.**
> - **`contracts-level0.yml`:** dos pasos nuevos, justo después del Paso 6b (Lint de Python).
>   - *Formato de Python* (K-61): `uv run --frozen --offline --directory contracts ruff format --check .`
>   - *YAML de contracts* (K-71): `yamllint -s -c .yamllint.yaml contracts/`, con `yamllint==1.38.0` instalado igual que en `repo-level0.yml`, o el que ya trae el entorno de `uv`, el que sea más simple **sin red añadida**. La versión debe ser la misma 1.38.0.
>   - Los dos pasos van sin `uses:` nuevos y sin cambiar permisos, para que la guardia `ci_workflows` de T22b siga en 0.
> - **`.pre-commit-config.yaml`:**
>   - el gancho `ruff-format` del mismo `ruff-pre-commit` v0.17.6;
>   - `files` de `yamllint` ampliado a `^contracts/.*\.ya?ml$`.
>   - Actualiza los dos comentarios que hoy citan K-61 y K-71 como pendientes.
> - **Exclusiones:** `contracts/.venv/`, `contracts/build/` y `node_modules/` no se analizan. `yamllint` sobre el directorio entra en `.venv`, así que acótalo con `ignore:` en `.yamllint.yaml` o con la lista de `git ls-files`, y di cuál elegiste.
> - **README:** si `contracts/README.md` o su tabla de comandos V-\* nombran cómo se corre V-YAML o el *lint*, actualízalos. Si `tests/test_readme.py` compara esa tabla, mantenla verde y no relajes la prueba.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si una guardia de T18 (versión semántica, huellas, `SHA256SUMS`, `effective-config.valid.sha256` o vectores JCS) exige subir una versión o regenerar una huella porque cambiaron los bytes de un contrato. No subas versiones ni regeneres huellas por tu cuenta.
- Si un YAML de `contracts/analyzer/v1/` que cubre `SHA256SUMS` necesita cambiar. Es la copia de C6 y no se toca (F7).
- Si el AST de algún `.py` cambia con `ruff format`.
- Si `gen_ts --check` o `gen_jcs_vectors --check` fallan después de los cambios.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- `repo-level0.yml`, `scripts/` y `docs/validacion-zine/`, que son de T27.
- La lógica de cualquier módulo, prueba o contrato. Solo se cambian formato y espacios.
- `contracts/ts/`, porque Prettier ya lo cubre su `lint`.
- `libs/errors`, que ya está formateado.
- `pyproject.toml` y `uv.lock`, salvo que el gancho o el paso lo exijan. En ese caso, para y avisa.

---

## Archivos de contexto

- `docs/loop/CANDIDATAS.md`: K-61 y K-71.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-44.
- `aidlc/spaces/default/memory/team.md`: Code Style y Way of Working.
- `.github/workflows/contracts-level0.yml`, `.github/workflows/repo-level0.yml` (cómo instala `yamllint`), `.pre-commit-config.yaml` y `.yamllint.yaml`.
- `contracts/README.md` y `contracts/tests/test_readme.py`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1: formato.**
  ```bash
  uv run --frozen --offline --directory contracts ruff format --check .
  ```
  Esperado: «… files already formatted», con código 0.

- [ ] **CA-2: YAML de `contracts/`.**
  ```bash
  uv run --frozen --offline --directory contracts yamllint -s -c /workspace/.worktrees/U01-T28/.yamllint.yaml /workspace/.worktrees/U01-T28/contracts
  ```
  Esperado: sin salida y código 0, sin entrar en `.venv`. Si `yamllint` no está en el entorno de `contracts`, usa el mismo comando que el paso nuevo del *workflow* y escríbelo literal en la bitácora.

- [ ] **CA-3: el AST no cambia.** Un `python -c` que compare `ast.dump` de `git show feat/b1-contratos:<f>` contra el archivo de HEAD, para cada `.py` del diff.
  Esperado: IGUAL en todos. La bitácora nombra cuántos archivos se compararon.

- [ ] **CA-4: los datos no cambian.** Un `python -c` que, para cada YAML del diff, cargue la versión de `feat/b1-contratos` y la de HEAD con `veridicus_contracts.loaders` y compare los valores.
  Esperado: IGUAL en todos. La bitácora nombra cuántos se compararon y lista cada exclusión con su motivo.

- [ ] **CA-5: suite, tipos, *lint* y generados.**
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check
  ```
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_jcs_vectors --check
  ```
  Y V-GUARD del Paso 5, con su comando literal de `contracts-level0.yml`.
  Esperado:
  - la suite en verde, con al menos 80 % de cobertura y en menos de 60 s;
  - sin errores de tipos ni de *lint*;
  - los generados al día;
  - V-GUARD al 100 %.

- [ ] **CA-6: guardias y diff.**
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T28
  ```
  ```bash
  git -C /workspace/.worktrees/U01-T28 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado:
  - las pruebas en verde;
  - `0 apariciones` en las dos guardias;
  - en el diff, solo archivos `.py` y `.yaml`/`.yml` de `contracts/`, más `.github/workflows/contracts-level0.yml`, `.pre-commit-config.yaml`, `.yamllint.yaml` (solo si hubo exclusiones o `ignore:`), `contracts/README.md` y `contracts/tests/test_readme.py` (solo si el punto 3 lo exige) y `docs/loop/bitacoras/U01-T28.md`.

---

## Plan de pruebas

1. **El rojo es la compuerta.** Antes de tocar nada, corre CA-1 y CA-2 sobre la base. Deben fallar.
   - Pega en `docs/loop/bitacoras/U01-T28.md` el resumen literal de cada uno: la última línea de `ruff format --check` con la cuenta de archivos, y la cuenta de errores de `yamllint` por archivo.
   - La salida completa va al scratchpad, y en la bitácora queda su ruta.
2. **Formato de Python.** Aplica `ruff format` y haz commit. Corre CA-3.
3. **YAML.** Corrige los YAML, haz commit y corre CA-4.
4. **Compuertas.** Añade los pasos del *workflow* y los ganchos, haz commit y corre CA-5 y CA-6.
5. **Si un rebase o un cambio posterior toca algo**, repite CA-3 y CA-4 con el commit final.

---

## Reglas de la app que aplican

- **`team.md`, Code Style:** Ruff para *lint* y formato, y `yamllint`.
- **`team.md`, Way of Working:** el *pre-commit* corre Ruff y `yamllint`, y la CI repite todo.
- **Testing Posture:** ningún umbral se baja y ninguna regla se relaja para que una compuerta pase.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- **Edita con Edit o Write.** La única excepción es `ruff format` (punto 1). No uses `ruff --fix` ni `git stash`.
- **Bitácora:** sigue la regla 12 para anexar. En un heredoc, ninguna línea puede empezar por `#`.
- **SHA:** cita en la bitácora solo los vigentes. Si un rebase reescribe alguno, márcalo en la misma línea.
- **F-11:** corre siempre con `uv run`, nunca con `--no-sync`.
- **Bash:** solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
- **Commits:** Conventional Commits en español con alcance `contracts` o `ci`. Por ejemplo, `style(contracts): ruff format en src y tests (U01-T28, K-61)`.
