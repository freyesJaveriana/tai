# U01-T02: carga, registro, huella JCS y validación estándar

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con PD-9 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** pasos 3 y 4 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`); deja lista la carga y la validación que usan todas las tareas siguientes.
**Depende de:** U01-T01 (fusionada, PR #5)

---

## Alcance

**Dentro:**

> Los módulos `loaders.py`, `registry.py`, `canonical.py` y `validators.py` en `contracts/src/veridicus_contracts/` (PD-9), con sus pruebas. Los meta-esquemas empaquetados en `contracts/vendor/` con `vendor/SHA256SUMS`, registrados en el mapa de la rueda (`include`, `sources`, `cache-keys` y la prueba de inventario) para que estén en la instalación editable y en la rueda instalada.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Ningún contrato del sistema (`api/`, `errors/`, `queues/`, `analyzer/`…), ningún *fixture* de contrato ni catálogo: llegan desde T03 (paso 5). Las pruebas de esta tarea usan esquemas mínimos en `tests/data/`.
- La comprobación AST de uso de `loaders` (`checks/loader_usage.py`, paso 19) y cualquier otra regla de `checks/`.
- `limits.v1.yaml` y su tratamiento en `hatch_build.py` (T10, aviso F-12).
- CI y *pre-commit* (paso 24).

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 3 y 4, PD-9, la tabla «Comandos de verificación» y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-requirements/tech-stack-decisions.md`: D2–D5, D14.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: §4.1, §4.2 y E36.
- `docs/loop/revisiones/U01-T01/ronda-4.md`: avisos F-11 y F-13.
- `docs/loop/bitacoras/U01-T01.md`: apartado «Para T02 y siguientes».
- `aidlc/spaces/default/memory/team.md`: Code Style y Testing Posture.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: carga, registro y huella JCS (paso 3).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py --no-cov
  ```
  Esperado: verde, con 5–8 pruebas por módulo y los casos que nombra el paso 3 (clave duplicada, `!!python/object`, `no`/`on` como texto, `$ref` canónico, forma antigua E36 no resuelta, `https://` rechazado sin red, vectores JCS `1e21`, `-0`, `5e-324`, `0.1`).

- [ ] **CA-2**: validación estándar y meta-esquemas (paso 4).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_validators.py --no-cov
  ```
  Esperado: 7 pruebas en verde, entre ellas `vendor/` = `SHA256SUMS` y meta-esquema alterado que falla.

- [ ] **CA-3**: 100 % de ramas en los módulos guardia de esta tarea.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100
  ```
  Esperado: suite en verde con ≥ 80 % y el informe de cobertura en 100 %.

- [ ] **CA-4**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-5**: `vendor/` está en el mapa y en la rueda (F-13).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde, con `vendor/` en la prueba de inventario (`include`, `sources` y `cache-keys`, que además ahora compara `cache-keys`, aviso F-11) y en las dos vías de construcción.

- [ ] **CA-6**: `loaders.py` es el único punto que crea `YAML(...)`.
  ```bash
  grep -rn "YAML(" contracts/src
  ```
  Esperado: solo apariciones en `contracts/src/veridicus_contracts/loaders.py`.

- [ ] **CA-7**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

Testing Contract (custom): cada capa se implementa y enseguida se escriben y corren sus pruebas antes de la siguiente. El rojo previo obligatorio es para guardias AUTONOMIA y contratos de datos (T03); aquí basta registrar en la bitácora la salida de cada archivo de prueba antes y después. `registry` y `canonical` son módulos guardia: 100 % de ramas.

---

## Reglas de la app que aplican

- **AUTONOMIA-02:** cada criterio tiene un comando.
- **NFR10.4 y NFR10.5:** la suite no usa red; el registro nunca resuelve una URI ajena, ni siquiera con red disponible.
- **NFR10.9:** los meta-esquemas se descargan una sola vez de su fuente oficial, se versionan y se comprueban con `SHA256SUMS`; nunca se descargan en ejecución. Anota en la bitácora la URL y la fecha de cada uno.
- **team.md, Code Style:** mypy estricto, Ruff con reglas `S` y motivo en toda supresión.
- Solo datos sintéticos: los esquemas de `tests/data/` son mínimos e inventados.

---

## Notas

- PD-9: todo módulo nuevo va directo en `contracts/src/veridicus_contracts/`; no existe `contracts/python/`. El paquete es de espacios de nombres (sin `__init__.py` en la raíz) y no debe cambiar a paquete regular.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`: los datos se copian a la instalación editable y solo `uv run` los refresca.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): carga, registro y validación estándar (T02)`.
