# U01-T06: sugerencia de revisión C7 v2 y su comprobación de condiciones

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con PD-9 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 8 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Respalda AC5.5.3.
**Depende de:** U01-T04 (ola 5, en paralelo con U01-T05 y U01-T07)

---

## Alcance

**Dentro:**

> `contracts/integrity/review-suggestion.v2.json` (C7 v2): JSON Schema 2020-12 estricto con `$id` versionado; `hecho`, `tipo`, `cita_a`, `cita_b` y `observaciones` obligatorios y no vacíos; citas por `$ref` canónico a `/veridicus/contracts/analyzer/v1/salida#/$defs/cita` (BR4.3); estados `pending`, `accepted`, `edited` y `dismissed` con las cuatro condiciones `if/then` de FD-U1-13 (BR4.4: fuera de `pending`, `decided_by` y `decided_at`; `dismissed` exige `note`; `edited` exige `reformulation`). Además, el módulo guardia `contracts/src/veridicus_contracts/checks/suggestion_conditions.py` (§4.8, NFR11.5), que exige que C7 declare las cuatro condiciones y que haya un *fixture* negativo por cada una, con 5–8 pruebas y 100 % de ramas.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- La máquina de estados en ejecución (U5) y cualquier persistencia.
- `checks/veracity.py` (T11) y las demás reglas de `checks/`.
- Los casos `c7` de `tests/guards/test_autonomia_03.py` que cruzan C7 con C1 o C19: pasan a verde cuando existan esos contratos (T12, T15).
- Editar la copia de C6 (BR1.8) o los *fixtures* y pruebas de T03. Si una prueba parece mal, el codificador para y lo informa al orquestador (`docs/loop/CANDIDATAS.md`); no la cambia.
- **Archivos de las tareas vecinas de la ola 5**, que corren en paralelo y no se pisan:

  | Tarea | Archivos que toca |
  |---|---|
  | T05 | `contracts/queues/runs.v2.yaml`, `results.v2.yaml`, `speech.v2.yaml` y, si va aparte, el esquema de `<cola>:failed` dentro de `contracts/queues/` |
  | **T06 (esta)** | `contracts/integrity/review-suggestion.v2.json`, `contracts/src/veridicus_contracts/checks/suggestion_conditions.py`, `contracts/tests/checks/test_suggestion_conditions.py` |
  | T07 | `contracts/errors/error-codes.v2.yaml`, `contracts/src/veridicus_contracts/checks/error_codes.py`, `contracts/tests/checks/test_error_codes.py`, `contracts/tests/test_errors_catalog.py` y todo `libs/errors/` |

  Ninguna de las tres toca `contracts/pyproject.toml`, `contracts/uv.lock`, `contracts/hatch_build.py`, `contracts/tests/conftest.py`, `contracts/tests/helpers.py`, `checks/__init__.py` ni los *fixtures* y pruebas de T03. T06 y T07 crean las dos la carpeta `contracts/tests/checks/`: **sin `__init__.py` ni `conftest.py`** en ella, para que las dos ramas no choquen.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 8, PD-8, la tabla «Comandos de verificación» (V-GUARD) y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C7 (revisión 3).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: F4, E9, E35 y FD-U1-13.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR4.1–BR4.4.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.2, §4.3 y §4.8.
- `contracts/analyzer/v1/salida.schema.json` (copia de C6, solo lectura) y `contracts/integrity/fixtures/review-suggestion/` (*fixtures* de T03).
- `docs/loop/revisiones/U01-T01/ronda-4.md`: aviso F-11.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: C7 acepta y rechaza sus *fixtures* y la comprobación de condiciones pasa (verificación del paso 8, primera parte).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_review_suggestion.py tests/checks/test_suggestion_conditions.py --no-cov
  ```
  Esperado: verde. E9 (sin cada uno de los 5 campos y con cada uno vacío, BR4.1), `is_truthful` (BR4.2) y E35 (una por condición de BR4.4) se rechazan por su `reject_reason`.

- [ ] **CA-2**: la guardia AUTONOMIA-05 queda entera en verde, C6 y C7 (verificación del paso 8, segunda parte).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_05.py --no-cov
  ```
  Esperado: verde, todo el archivo y sin filtro de marcador.

- [ ] **CA-3**: 100 % de ramas en el módulo guardia (V-GUARD acotado a esta tarea).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_suggestion_conditions.py --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/suggestion_conditions.py" --fail-under=100
  ```
  Esperado: el primer comando en verde y el informe en 100 %. La suite completa sigue en rojo a propósito hasta T15 (pruebas `c1`), por eso la cobertura se mide solo con las pruebas del módulo.

- [ ] **CA-4**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-5**: la tarea solo tocó sus archivos.
  ```bash
  git diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: los tres archivos de T06 de la tabla de arriba y `docs/loop/bitacoras/U01-T06.md`.

- [ ] **CA-6**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. **Rojo de T03:** antes de escribir C7, corre `tests/contracts/test_review_suggestion.py` y `tests/guards/test_autonomia_05.py` y pega la salida en rojo en `docs/loop/bitacoras/U01-T06.md`.
2. Escribe C7 hasta el verde de esos dos archivos.
3. **Capa `checks/`** (Testing Contract: implementar y enseguida probar): escribe `suggestion_conditions.py` y después `tests/checks/test_suggestion_conditions.py`, con 5–8 pruebas que incluyan controles negativos: C7 sin una de las cuatro condiciones → rojo; una condición sin su *fixture* negativo → rojo. Los controles negativos trabajan sobre copias en memoria o en `tmp_path`, nunca sobre el contrato versionado.

---

## Reglas de la app que aplican

- **AUTONOMIA-03** (Mapa AUTONOMIA): toda sugerencia tiene estado editable cambiado por un humano, con quién y cuándo (BR4.4) → CA-1 y CA-3. C7 no tiene ningún campo de veracidad (BR4.2, `is_truthful` rechazado).
- **AUTONOMIA-05:** sugerencia rechazada sin cada uno de sus 5 campos obligatorios; las citas son las de C6 por referencia canónica → CA-1 y CA-2.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **team.md, Testing Posture:** 100 % de ramas en los módulos guardia.
- Solo datos sintéticos.

---

## Notas

- La referencia a la cita usa la forma canónica bajo `https://veridicus.invalid/`; la forma antigua `contracts/analyzer/v1/salida.schema.json#/$defs/cita` no se resuelve (E36).
- PD-9: el módulo va en `contracts/src/veridicus_contracts/checks/`; `checks/__init__.py` ya existe y no se toca.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): sugerencia de revisión C7 v2 y sus condiciones (T06)`.
