# U01-T22b: la guardia de *workflows* comprueba SHA y permisos

> Esta tarea la redactó el orquestador a partir de la candidata K-70, que salió de la revisión 1 de U01-T22, y de la decisión E-43 del humano (2026-11-24). Es una correctiva. El humano la revisa antes de que se despache.
>
> **Este archivo, junto con los pasos del plan que cita, es todo lo que el codificador necesita leer.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Precisa:**
- `nfr-design/security-design.md` §4.13, línea 424: «El *workflow* declara `permissions: contents: read`, fija cada acción por SHA y no tiene credenciales del clúster. `checks/ci_workflows.py` lo comprueba (§4.11)».
- La guardia de U01-T18.

**Historias que implementa:** ninguna propia, porque U1 es `spec`.
**Depende de:** U01-T22, que ya debe estar fusionada para que exista `contracts-level0.yml`. Va en paralelo con U01-T23, porque no tocan los mismos archivos: T23 edita `contracts-level0.yml` y esta tarea solo lo lee. Debe fusionarse antes del PR del Bolt a `main`.

---

## Alcance

**El defecto.** La revisión 1 de T22 sondeó la guardia con copias de los *workflows* en el scratchpad:
- Una acción sin SHA (`uses: actions/checkout@v4`) da 0 problemas.
- Un *workflow* sin `permissions` da 0 problemas.
- Un *workflow* con `contents: write` da 0 problemas.
- Además, `test_ci_workflows.py` solo exige que exista `repo-level0.yml`.

Sin embargo, §4.13 dice que la guardia comprueba todo eso.

**Dentro:**

> **1. `contracts/src/veridicus_contracts/checks/ci_workflows.py`** suma dos reglas a lo que ya hace, que se queda igual: `--write`, `kubectl apply`, `helm install`, `helm upgrade` y `kubeconfig`.
> - **Acción fijada por SHA.** Cada `uses:` que apunta a otro repositorio (`dueño/repo@ref` o `dueño/repo/ruta@ref`) lleva como `ref` un SHA de 40 caracteres hexadecimales en minúscula. Una etiqueta, una rama o un SHA corto es un problema. Una acción local (`uses: ./…`) no lleva `ref` y pasa. Una `docker://…` que no esté fijada por `@sha256:` de 64 caracteres es un problema.
> - **Permisos.** Cada *workflow* declara en la raíz `permissions:` con `contents: read`.
>   - Es un problema que falte el bloque raíz.
>   - También lo es que la raíz tenga otro valor de `contents`, o que use `write-all` o `read-all`.
>   - En cualquier nivel, `contents: write` y `permissions: write-all` son un problema.
>   - Los permisos `write` de otros alcances en un *job* (p. ej. el futuro `packages: write` del *job* de *build*, `team.md`) quedan fuera de esta regla y no se marcan.
> - **Cómo se lee.**
>   - Los permisos se leen con el cargador YAML del paquete, el que exige la guardia `loader_usage`. Los `uses:` se pueden leer del YAML cargado o línea a línea, lo que sea más simple con 100 % de ramas.
>   - Un *workflow* que no se puede cargar es un problema con su mensaje, nunca un salto.
> - **Mensajes.** Llevan archivo, línea cuando se conoce, término y regla, en español, con el mismo formato que los de ahora. `REGLA` añade `team.md, Deployment`.
> - **Documentación.** Se actualizan el docstring del módulo y `LIMITACIONES`, si aparece alguna nueva.
>
> **2. `contracts/tests/checks/test_ci_workflows.py`:**
> - La prueba de los *workflows* reales exige que existan **`repo-level0.yml` y `contracts-level0.yml`**, y que los dos den 0 problemas.
> - Hay rojos parametrizados en `tmp_path`:
>   - `@v4`;
>   - `@main`;
>   - SHA de 39 caracteres;
>   - SHA en mayúsculas;
>   - `docker://imagen:tag`;
>   - sin `permissions`;
>   - raíz `contents: write`;
>   - raíz `write-all`;
>   - *job* con `contents: write`;
>   - YAML que no carga.
> - Hay verdes:
>   - acción local `./`;
>   - `docker://…@sha256:<64>`;
>   - `dueño/repo/ruta@<40>`;
>   - *job* con `packages: write` y raíz `contents: read`.
> - El módulo queda al **100 % de ramas** (V-GUARD).

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si uno de los dos *workflows* reales no cumple las reglas nuevas. Sería un defecto de T22 o de `repo-level0.yml`, y tú no lo corriges.
- Si la guardia `loader_usage` u otra guardia de T18 impide leer los *workflows* con el cargador del paquete.
- Si para cumplir el 100 % de ramas hace falta cambiar otra guardia o `pyproject.toml`.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Los *workflows* de `.github/workflows/`, que solo se leen.
- Las demás guardias de `checks/`, `scripts/`, `pyproject.toml` y `uv.lock`.
- K-71: los YAML de contratos que no pasan `yamllint`.
- Comprobar que el SHA corresponde de verdad a la versión del comentario. Eso necesita red y lo revisa el revisor.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md` §4.11 y §4.13.
- `aidlc/spaces/default/memory/team.md`, sección Deployment: «la CI … declara `permissions: contents: read` por defecto y fija las acciones por SHA».
- `docs/loop/revisiones/U01-T22/ronda-1.md`: la sonda de la guardia.
- `docs/loop/CANDIDATAS.md`: K-70.
- `decisiones-humano.md`: E-43.
- `contracts/src/veridicus_contracts/checks/ci_workflows.py`, `contracts/tests/checks/test_ci_workflows.py` y `.github/workflows/`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: la guardia y sus pruebas.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  Esperado: verde, con los dos *workflows* reales nombrados y 0 problemas.

- [ ] **CA-2**: 100 % de ramas en el módulo (V-GUARD).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --cov=veridicus_contracts.checks.ci_workflows --cov-branch --cov-report=term-missing --cov-fail-under=100
  ```
  Esperado: `100%` y código 0.

- [ ] **CA-3**: la suite completa (V-SUITE).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  Esperado: verde, con ≥ 80 % de cobertura.

- [ ] **CA-4**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: sin errores.

- [ ] **CA-5**: AUTONOMIA-01 e `/insumos`.
  ```bash
  bash scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T22b
  ```
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T22b
  ```
  Esperado: `0 apariciones` y código 0.

- [ ] **CA-6**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T22b diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo estos tres archivos:
  - `contracts/src/veridicus_contracts/checks/ci_workflows.py`;
  - `contracts/tests/checks/test_ci_workflows.py`;
  - `docs/loop/bitacoras/U01-T22b.md`.

---

## Plan de pruebas

1. Escribe primero las pruebas nuevas y haz su commit.
2. Corre el rojo contra la guardia de `feat/b1-contratos`. Los casos de SHA y de permisos deben fallar **por la regla**: la guardia devuelve 0 problemas donde la prueba espera uno. No deben fallar por un error de importación.
3. Pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T22b.md`. Si es larga, sigue la regla 12: Write al scratchpad y luego `bash -c "cat <archivo> >> <bitácora>"`. No la condenses.
4. Implementa hasta el verde.
5. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** la CI no aplica cambios ni tiene credenciales del clúster.
- **`team.md`, Deployment:** `permissions: contents: read` por defecto y acciones fijadas por SHA.
- **Testing Posture:** 100 % de ramas en los módulos guardia. Ningún umbral se baja para que pase.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- **Edita solo con Edit o Write.** También las pruebas. No uses `ruff --fix` ni `git stash`.
- **Bitácora:** sigue la regla 12 para anexar. En un heredoc, ninguna línea puede empezar por `#`.
- **SHA:** cita en la bitácora solo los vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- **F-11:** corre siempre con `uv run`, nunca con `--no-sync`.
- **Bash:** solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
- **Commits:** Conventional Commits en español con alcance `contracts`, por ejemplo `fix(contracts): la guardia de workflows exige SHA y permisos de lectura (U01-T22b, K-70)`.
