# U01-T22: suite completa, CI y ganchos locales

> El orquestador llenó esta tarea a partir de los pasos 23 y 24 del plan, de E-32 (conectar `check-no-insumos.sh`) y de las candidatas K-61 y K-62. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que implementa:** 23 y 24, en `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T20 (los pasos 8 a 11 de la CI corren la mitad TypeScript), U01-T24 y U01-T25 (`scripts/check-no-insumos.sh`). Abre la ola 11 y va antes de T23 y T26.

---

## Alcance

**Dentro:**

> **1. Paso 23: correr todo.** Corre cada V-* del paso 23 (V-SUITE, V-GUARD, V-TYPES, V-LINT, V-AUDIT, V-GEN, V-SURFACE, V-TS, V-TS-AUDIT, V-PKG y V-ERRORS) con el comando de la tabla de V-* del plan. Pega cada salida en la bitácora. Ningún umbral se baja. Si algo falla, para y avisa, salvo que el defecto esté dentro de esta tarea.
>
> **2. `.github/workflows/contracts-level0.yml` (paso 24).** El *job* `contracts-level0` lleva los 12 pasos de §4.13 de `security-design.md`, en ese orden y con esos comandos, más estas condiciones:
> - `permissions: contents: read`;
> - cada acción fijada por SHA con su comentario de versión, como en `repo-level0.yml`;
> - sin `kubeconfig` ni credenciales del clúster, y sin `--write` en ningún generador;
> - los pasos sin red con `--frozen --offline`.
>
> Además:
> - **K-62.** Antes del paso 2 (`pip-audit`), un paso crea `contracts/build/`, porque `audit_gate` corre después.
> - **Paso 5.** Usa las rutas reales de los módulos guardia del paquete, es decir, las que usa CA-3 de T18d: `src/veridicus_contracts/checks/*` y las que existan de las listadas en §4.13. Si una ruta de §4.13 no existe en el árbol (K-59, rutas viejas tras PD-9), anótalo en la bitácora como precisión y usa la ruta vigente. No la quites en silencio.
> - **El *job* hermano `errors-level0`** corre V-ERRORS (extensión de §4.13 por PD-7, R-13 de la revisión 2). El PR lo anota.
> - **Disparadores:** `pull_request` y `push` a `main`, como `repo-level0.yml`, con `concurrency`.
>
> **3. Guardia de `/insumos` en la CI (E-32).** Añade a `repo-level0.yml` un paso que corra `bash scripts/check-no-insumos.sh .`, junto al de AUTONOMIA-01. Es lo único que cambia en ese archivo.
>
> **4. `.pre-commit-config.yaml` en la raíz**, con `gitleaks`, Ruff y `yamllint`. Cada *hook* va fijado a una versión o SHA, y `gitleaks` usa `.gitleaks.toml`.
>
> **4b. K-69 (E-42).** Hoy, después de `npm ci`, el sdist de `contracts` arrastra `ts/node_modules`, que pesa 151 MB, y V-SUITE pasa de unos 28 s a unos 46 s. Para evitarlo:
> - añade `ts/node_modules/` (o `node_modules/`) a `contracts/.gitignore`;
> - añádelo también a la lista de lo que `_copiar` ignora en `contracts/tests/test_package_map.py`.
>
> Esa lista es lo único que cambia en ese archivo de pruebas. Rojo: con `node_modules` presente, mide `test_package_map.py` con `--durations` antes y después del cambio, y pega las dos salidas. Si hace falta un `exclude` del sdist en `pyproject.toml`, para y avisa.
>
> **5. El PR del Bolt.** Escribe en la bitácora, para el PR del Bolt, la petición de que `contracts-level0` sea comprobación obligatoria de `main`. La aplica el humano en GitHub.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si un V-* del paso 23 falla por algo fuera de esta tarea.
- Si `test_ci_workflows.py` o `check-no-cluster-apply.sh` rechazan el *workflow* nuevo y la única salida es tocar la guardia o su lista.
- Si un paso de §4.13 no se puede escribir tal cual (comando inexistente, ruta movida) y el cambio no es solo de ruta.
- Si `check-no-insumos.sh` falla sobre el repositorio real.
- **K-61, `ruff format`:** si quieres añadir `ruff format --check` a la CI o al gancho, para y avisa. Hoy falla en `loaders.py` y no está en §4.13, así que lo decide el humano.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- El código de `src/`, los contratos y sus *fixtures*, y las guardias de `checks/`.
- `pyproject.toml`, `uv.lock` y `contracts/ts/package-lock.json`.
- `scripts/check-no-cluster-apply.sh` y `scripts/check-no-insumos.sh`. Solo se llaman.
- El disparador por etiqueta, `check_tag.py` y el README: van en T23, que ya incluye lo que era T26 (E-41).
- La configuración de GitHub (protección de `main`, comprobaciones obligatorias). La aplica el humano.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md` §4.13: los 12 pasos.
- `code-generation-plan.md`: pasos 23 y 24 y la tabla de V-*.
- `decisiones-humano.md`: E-32 a E-35.
- `docs/loop/CANDIDATAS.md`: K-59, K-61 y K-62.
- `.github/workflows/repo-level0.yml`: el modelo de forma (SHA, `permissions`, `concurrency`).
- `contracts/tests/checks/test_ci_workflows.py` y `scripts/check-no-cluster-apply.sh`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: V-YAML.
  ```bash
  yamllint -s .github/ .pre-commit-config.yaml
  ```
  Esperado: código 0. Si `yamllint` no está instalado, usa el comando V-YAML del plan.

- [ ] **CA-2**: la guardia de *workflows*.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-3**: AUTONOMIA-01 y `/insumos`.
  ```bash
  bash scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T22
  ```
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T22
  ```
  Esperado: `0 apariciones` y código 0 en ambos.

- [ ] **CA-4**: el paso 23, en local, con los mismos comandos del *workflow*. Corre los pasos 3 a 7 y 10 a 12 de §4.13, más V-ERRORS, cada uno por separado. Los pasos con red (1, 2, 8 y 9) se corren solo si la tarea de instalación lo exige; si no, se anota que corren solo en la CI.
  Esperado: cada uno con código 0 y dentro de su tiempo.

- [ ] **CA-5**: el *workflow* sigue §4.13.
  ```bash
  grep -n -E "run:|uses:" .github/workflows/contracts-level0.yml
  ```
  Esperado:
  - los 12 pasos están en orden, más el que crea `build/`;
  - cada `uses:` lleva un SHA de 40 caracteres;
  - ningún `--write`.

  Pega la salida y compárala con la tabla de §4.13, fila por fila.

- [ ] **CA-6**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T22 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: `.github/workflows/contracts-level0.yml`, `.github/workflows/repo-level0.yml` (un paso), `.pre-commit-config.yaml`, `contracts/.gitignore` y `contracts/tests/test_package_map.py` (solo la lista de K-69) y `docs/loop/bitacoras/U01-T22.md`.

- [ ] **CA-7**: V-SUITE con `node_modules` presente (K-69).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  Esperado: verde. El tiempo va en la bitácora y debe quedar cerca del de antes de T20, unos 28 s.

---

## Plan de pruebas

Esta tarea no añade pruebas de Python. Su «rojo» son dos corridas sobre `feat/b1-contratos`, antes de crear el *workflow*:
- `test_ci_workflows.py`, que no encuentra `contracts-level0.yml`;
- `check-no-insumos.sh`, que no está conectado en `repo-level0.yml`.

Pega las dos salidas, literales y completas, en `docs/loop/bitacoras/U01-T22.md`. Si alguna es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.

Si `test_ci_workflows.py` no tiene un caso que exija el *job* `contracts-level0`, dilo en la bitácora. No lo añadas: la guardia está fuera.

**Evidencia del PR (no es criterio):** el *job* `contracts-level0` en verde en el PR, con su enlace.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** la CI no despliega, no tiene credenciales del clúster y no envía trabajos a ZINE.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **NFR12.2:** `gitleaks` en la CI y en el gancho local.
- **Testing Posture (`team.md`):** los umbrales nunca se bajan para que una compuerta pase.
- **El repositorio es público** (`project.md`): nada de `/insumos` entra.

---

## Notas

- **Edita solo con Edit o Write.** El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- **Bash:**
  - Solo caracteres ASCII imprimibles en los comandos.
  - Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
  - Los `${{ … }}` del *workflow* se escriben con Write, nunca por Bash.
- **Conventional Commits** en español con alcance `ci`, por ejemplo `ci(contracts): job contracts-level0 con los 12 pasos de 4.13 (U01-T22)`.
