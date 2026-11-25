# U01-T07: catálogo de errores v2 y excepciones de `libs/errors/`

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con PD-9 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 9 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Cubre la definición de terminado 4 de B1 (`anonimizador_no_disponible` e `incidente_anonimizacion` con su `code`).
**Depende de:** U01-T04 (ola 5, en paralelo con U01-T05 y U01-T06)

---

## Alcance

**Dentro:**

> Tres piezas:
> 1. `contracts/errors/error-codes.v2.yaml`: por `code`, un solo `status`, su `class`, la unidad dueña y `http: true|false`. `limits.exceeded` = `413` (D16). Los de arranque y log (`config.invalid_profile`, `config.invalid_limit`, `run.publish_failed`) con `http: false` y sin estado. Los `code` de NFR10.3 y de contract-summary revisión 3, incluidos `session.blocked` (CD-11), `route.not_found` (`404`, NFRD-U3-10), `report.view_outdated` (`409`, NFRD-U7-04), `import.invalid_type` y `research.invalid_type` (`415`). La tabla `error.codigo` de C6 → `code`, uno a uno, con `proveedor` → `analysis.provider` (BR3.4, E34).
> 2. `libs/errors/` (PD-7): la distribución aparte `veridicus-errors`, importada como `veridicus_errors`, con su `pyproject.toml` (hatchling, Python 3.12, mypy estricto, Ruff con `S`, `pytest-cov` al 80 %), su `uv.lock` versionado, `src/veridicus_errors/` con una clase sin lógica por `code` (atributo de clase `code`) y su jerarquía (BR7.4), y `tests/` con 5–8 pruebas (jerarquía, `code` único, `status` no expuesto en la clase).
> 3. El módulo guardia `contracts/src/veridicus_contracts/checks/error_codes.py` (§4.7 a–e, sin la parte de C1): catálogo y clases uno a uno leyendo `libs/errors/src/` **con `ast`, sin importar** (nombre de clase, base y atributo `code`; E31, E44) y tabla de C6 completa (E34). Con `tests/checks/test_error_codes.py` y `tests/test_errors_catalog.py` (forma del catálogo, un `status` por `code`, `limits.exceeded` = 413, `http: false` en los de arranque).

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- La parte de C1 de `checks/error_codes.py`: el enum `ErrorCode` de C1 igual al catálogo (a), estados de las respuestas de C1 (c) y `$ref` a `Problem` (d). Se completa en T15 (paso 16). Aquí (b), «todo `code` usado existe», se escribe genérico sobre los contratos que haya y se prueba con copias en `tmp_path`, sin depender de los archivos de T05.
- El manejador que traduce a Problem Details: es de cada servicio.
- Que `contracts/` importe `veridicus_errors` o la declare como dependencia, o que sus clases entren en la rueda de contratos (PD-7).
- Editar la copia de C6 (BR1.8) o los *fixtures* y pruebas de T03.
- **Archivos de las tareas vecinas de la ola 5**, que corren en paralelo y no se pisan:

  | Tarea | Archivos que toca |
  |---|---|
  | T05 | `contracts/queues/runs.v2.yaml`, `results.v2.yaml`, `speech.v2.yaml` y, si va aparte, el esquema de `<cola>:failed` dentro de `contracts/queues/` |
  | T06 | `contracts/integrity/review-suggestion.v2.json`, `contracts/src/veridicus_contracts/checks/suggestion_conditions.py`, `contracts/tests/checks/test_suggestion_conditions.py` |
  | **T07 (esta)** | `contracts/errors/error-codes.v2.yaml`, `contracts/src/veridicus_contracts/checks/error_codes.py`, `contracts/tests/checks/test_error_codes.py`, `contracts/tests/test_errors_catalog.py` y todo `libs/errors/` |

  Ninguna de las tres toca `contracts/pyproject.toml`, `contracts/uv.lock`, `contracts/hatch_build.py`, `contracts/tests/conftest.py`, `contracts/tests/helpers.py`, `checks/__init__.py` ni los *fixtures* y pruebas de T03. T06 y T07 crean las dos la carpeta `contracts/tests/checks/`: **sin `__init__.py` ni `conftest.py`** en ella, para que las dos ramas no choquen.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 9, PD-7, la tabla «Comandos de verificación» (V-ERRORS, V-GUARD) y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: catálogo de `code` (revisión 3) y CD-01, CD-11.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E31, E34, E44.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR3.4, BR7.2, BR7.4.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-requirements/security-requirements.md`: NFR10.3.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-requirements/tech-stack-decisions.md`: D16 y §3 (versiones de las herramientas, para el `pyproject.toml` de `libs/errors/`).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.7 y §6 (NFRD-U3-10, NFRD-U7-04).
- `contracts/analyzer/v1/salida.schema.json` (copia de C6, solo lectura: enum de `error.codigo`).
- `contracts/pyproject.toml`: modelo de configuración de mypy, Ruff y pytest que imita `libs/errors/pyproject.toml`.
- `aidlc/spaces/default/memory/team.md`: Code Style (errores en fronteras, glosario en inglés) y Testing Posture.
- `docs/loop/revisiones/U01-T01/ronda-4.md`: aviso F-11.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: catálogo y comprobación uno a uno (verificación del paso 9, primera parte).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_error_codes.py tests/test_errors_catalog.py --no-cov
  ```
  Esperado: verde, con controles negativos de E31 (`code` sin clase o clase sin `code`), E44 y E34 (código de C6 sin `code`), un `status` por `code`, `limits.exceeded` = 413 y `http: false` en los de arranque.

- [ ] **CA-2**: el lockfile de `libs/errors/` existe, está versionado y coincide con su `pyproject.toml`.
  ```bash
  uv lock --check --directory libs/errors
  ```
  Esperado: código 0.

- [ ] **CA-3**: V-ERRORS, instalación (con red).
  ```bash
  uv sync --frozen --directory libs/errors
  ```
  Esperado: código 0.

- [ ] **CA-4**: V-ERRORS, pruebas con cobertura.
  ```bash
  timeout 60 uv run --frozen --offline --directory libs/errors pytest
  ```
  Esperado: verde, 5–8 pruebas, ≥ 80 % de líneas.

- [ ] **CA-5**: V-ERRORS, tipos.
  ```bash
  uv run --frozen --offline --directory libs/errors mypy --strict src
  ```
  Esperado: `Success: no issues found`.

- [ ] **CA-6**: V-ERRORS, *lint*.
  ```bash
  uv run --frozen --offline --directory libs/errors ruff check .
  ```
  Esperado: `All checks passed!`.

- [ ] **CA-7**: 100 % de ramas en el módulo guardia (V-GUARD acotado a esta tarea).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_error_codes.py tests/test_errors_catalog.py --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/error_codes.py" --fail-under=100
  ```
  Esperado: el primer comando en verde y el informe en 100 %. La suite completa sigue en rojo a propósito hasta T15 (pruebas `c1`), por eso la cobertura se mide solo con las pruebas del módulo.

- [ ] **CA-8**: `contracts/` no importa ni declara `veridicus-errors` (PD-7; lectura de vuelta).
  ```bash
  grep -rn -E "^\s*(import|from) veridicus_errors" contracts/src contracts/tests
  ```
  ```bash
  grep -n "veridicus-errors" contracts/pyproject.toml contracts/uv.lock
  ```
  Esperado: ninguna línea en los dos comandos (código 1). `checks/error_codes.py` lee `libs/errors/src/` por ruta con `ast`.

- [ ] **CA-9**: tipos y *lint* de `contracts/`.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-10**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

Testing Contract (custom): el catálogo de errores no está entre los contratos de datos del rojo previo (T03). Cada capa se implementa y enseguida se escriben y corren sus pruebas, antes de la siguiente:

1. `errors/error-codes.v2.yaml` y `tests/test_errors_catalog.py`.
2. `libs/errors/` y sus pruebas (CA-2 a CA-6).
3. `checks/error_codes.py` y `tests/checks/test_error_codes.py`, con controles negativos sobre copias en `tmp_path` (nunca sobre los archivos versionados). 100 % de ramas.

Registra en `docs/loop/bitacoras/U01-T07.md` la salida de cada archivo de prueba antes y después de su capa.

---

## Reglas de la app que aplican

- **AUTONOMIA-04** (definición de terminado 4): `anonimizador_no_disponible` e `incidente_anonimizacion` de C6 tienen su `code` en la tabla (E34).
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **team.md, Code Style:** una jerarquía única de excepciones en `libs/`, traducida a Problem Details (RFC 9457) por un solo manejador de cada servicio con un `code` estable; identificadores en inglés; mypy estricto, Ruff con reglas `S` y motivo en toda supresión; `uv` con un lockfile por paquete.
- **team.md, Testing Posture:** 80 % de líneas en `libs/errors` y 100 % de ramas en el módulo guardia.
- Solo datos sintéticos (aquí no hay datos).

---

## Notas

- `libs/errors/` es un paquete nuevo en la raíz del monorepo (team.md: solo `libs/` se comparte entre servicios). Las clases no llevan lógica ni `status`: el estado vive en el catálogo.
- `uv lock --directory libs/errors` necesita red una vez; el `uv.lock` resultante se versiona. `uv` crea `libs/errors/.venv/` con su propio `.gitignore`; no se versiona.
- Si un `code` que necesitan C2, C3 o C5 (T05, en paralelo) no está en el catálogo, se verá al fusionar las dos ramas; no lo adivines desde aquí. Toma la lista de NFR10.3 y de contract-summary revisión 3.
- El *job* de CI `errors-level0` es de T22 (paso 24); aquí no se escribe ningún *workflow*.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español: alcance `contracts` para el catálogo y la comprobación, y `errors` para `libs/errors/`, por ejemplo `feat(errors): jerarquía de excepciones veridicus-errors (T07)`.
