# U01-T01: estructura del paquete y ejecutor de pruebas

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` aprobado de U1 (revisión 2, `Approve Plan` del 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** pasos 1 y 2 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia. U1 es `spec` y respalda criterios de US3.6, US8.3, US12.6, US13.3 y US15.4; esta tarea solo deja lista la base.
**Depende de:** ninguna (ola 1)

---

## Alcance

**Dentro:**

> El esqueleto de la distribución `veridicus-contracts` en `contracts/`. Incluye su `pyproject.toml` con el mapa de rutas, las dependencias, la configuración de mypy, Ruff, pytest y cobertura, y su `uv.lock` versionado. También los directorios del inventario, `.gitattributes`, las entradas de `.gitignore` y un ejecutor de pruebas sin red con 2 pruebas en verde.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Ningún contrato (`*.yaml`, `*.json` de esquemas), *fixture* ni catálogo. Llegan desde la tarea T03 (paso 5).
- `loaders.py`, `validators.py`, `registry.py`, `canonical.py` y `vendor/`: son la tarea T02 (pasos 3 y 4).
- F7 en `pytest_sessionstart` (paso 6), `libs/errors/` (paso 9) y la mitad TypeScript `contracts/ts/` (paso 21).
- *Workflows* de CI: `contracts-level0.yml` es el paso 24. `repo-level0.yml` ya existe y no se toca.
- `.pre-commit-config.yaml` (paso 24).

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 1 y 2, la tabla «Comandos de verificación» y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-requirements/tech-stack-decisions.md`: D1, D5–D7 y D15, §2 (estructura del paquete) y §3 (dependencias).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: §1, inventario y tabla de rutas de la rueda.
- `aidlc/spaces/default/memory/team.md`: Code Style y Testing Posture.
- `.gitignore` y `.gitattributes` de la raíz (se modifican en su sitio).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: el lockfile existe, está versionado y coincide con `pyproject.toml`.
  ```bash
  uv lock --check --directory contracts
  ```
  Esperado: código 0.

- [ ] **CA-2**: la instalación reproducible funciona (con red).
  ```bash
  uv sync --frozen --directory contracts
  ```
  Esperado: código 0.

- [ ] **CA-3**: el ejecutor está listo y bloquea la red (paso 2).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_runner.py --no-cov
  ```
  Esperado: `2 passed`, código 0. Una prueba comprueba que abrir un *socket* lanza `SocketBlockedError` (lectura de vuelta: la excepción real de `pytest-socket`) y la otra, que `conftest.py` resuelve la raíz de `contracts/`.

- [ ] **CA-4**: tipos y *lint* sin errores sobre el esqueleto.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src python
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-5**: la configuración de pytest declara la red bloqueada y la cobertura con ramas.
  ```bash
  grep -n -E "disable-socket|cov-branch|cov-fail-under=80" contracts/pyproject.toml
  ```
  Esperado: las tres apariciones.

- [ ] **CA-6**: `.gitattributes` fuerza LF en `contracts/` y `.gitignore` cubre lo sensible.
  ```bash
  git check-attr eol -- contracts/pyproject.toml
  ```
  ```bash
  git check-ignore -v .env x.pem x.key kubeconfig secrets-x.yaml .worktrees/a build/a
  ```
  Esperado: `eol: lf`. Las siete rutas aparecen como ignoradas.

- [ ] **CA-7**: la CI del repositorio sigue en verde (no se rompió `repo-level0`).
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

Según el Testing Contract, el ejecutor queda listo **antes** de la primera prueba de contrato (`runner_ready_before_first_test`). En esta tarea solo se escriben las dos pruebas del ejecutor, en `tests/test_runner.py`. Las pruebas en rojo de contratos y guardias son de la tarea T03.

---

## Reglas de la app que aplican

- **AUTONOMIA-02:** cada criterio tiene un comando.
- **NFR10.5 y NFR2.1:** la suite no usa red (`--disable-socket`) y corre en ≤ 60 s.
- **team.md, Code Style:** Python 3.12, Ruff con reglas `S`; toda supresión `# noqa: S…` lleva su motivo. mypy estricto y `uv` con un lockfile por paquete.
- Solo datos sintéticos (aquí no hay datos).

---

## Notas

- Archivos que se **modifican en su sitio**: `.gitignore` (añadir solo lo que falte: `.env`, `*.pem`, `*.key`, `kubeconfig*`, `secrets*.yaml`, `.worktrees/`, `build/`) y `.gitattributes` (añadir `contracts/** text eol=lf`).
- `yamllint` va en el grupo de desarrollo (lo usa V-YAML en el paso 24).
- `uv lock` necesita red una vez. El `uv.lock` resultante se versiona.
- Con `src/veridicus_contracts/` todavía vacío, mypy necesita al menos un `__init__.py` y `py.typed`. No escribas lógica: cualquier módulo con comportamiento pertenece a otra tarea.
- Conventional Commits en español, con alcance `contracts`, por ejemplo `chore(contracts): esqueleto del paquete y ejecutor de pruebas (T01)`.
