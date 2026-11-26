# U10-T01: el validador admite las marcas `x-veridicus-*` del catálogo (K-56)

**Unidad:** U10 `anonymizer`   **Bolt:** B10a   **Rama base:** `bolt/b10a-anonymizer`
**Pasos del plan que cubre:** paso 1 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna directa. Habilita BR2.5 de U10, que valida el `ModelCall` contra `model-call.v1.yaml`.
**Depende de:** ninguna
**Riesgo (ML-4):** alto (contratos) → `revisor` con `opus`

---

## Alcance

**Dentro:**

> `validate_json_schema` y `validate_instance` de `veridicus-contracts` admiten la lista cerrada de 10 marcas `x-veridicus-*` de PD-4 y comprueban la forma semver de `x-veridicus-version`. Sale `veridicus-contracts` 0.1.1.

**Fuera** (rechazar aunque se vea roto):

- Todo lo que está bajo `libs/anonymizer/`: es de U10-T02 y siguientes.
- Cambiar cualquier esquema de `contracts/` para que valide: se arregla el validador, no los contratos.
- K-57 (versión del nombre de archivo de C5) y cualquier otra candidata.
- Crear o subir la etiqueta `contracts-v0.1.1`: la pone el humano.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md` (PD-4, paso 1 y Testing Contract)
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/unit-test-instructions.md`
- `docs/loop/CANDIDATAS.md` (fila K-56)
- `contracts/src/veridicus_contracts/validators.py` (incluida la regla E-30, que solo admite `x-veridicus-version` en la raíz)
- `contracts/tests/test_validators.py`
- `contracts/model_calls/model-call.v1.yaml` y los esquemas de C18 y C19 bajo `contracts/`
- `contracts/pyproject.toml` y `contracts/uv.lock`

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U10-T01`.

- [ ] **CA-1 (rojo primero):** las pruebas nuevas `k56` fallan contra el validador sin arreglar. La bitácora guarda esta corrida, hecha antes de tocar `validators.py`.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_validators.py -k k56 --no-cov
  ```
  Esperado: código 1, con al menos 3 pruebas `k56` en `FAILED`.

- [ ] **CA-2:** con el arreglo, todas las pruebas `k56` pasan.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_validators.py -k k56 --no-cov -q
  ```
  Esperado: código 0, con al menos 6 pruebas `k56` que pasan. Al menos 4 son controles negativos: marca fuera de la lista, `x-veridicus-limit` anidado roto, `x-veridicus-version` que no es semver y `x-veridicus-version` fuera de la raíz.

- [ ] **CA-3:** la suite completa de `contracts` sigue en verde, con su cobertura de ramas y en ≤ 60 s.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  Esperado: código 0, sin bajar ningún umbral de `pyproject.toml`.

- [ ] **CA-4:** la versión es 0.1.1 y el lock está al día. Lectura de vuelta con la herramienta real:
  ```bash
  timeout 60 uv lock --check --directory contracts
  ```
  ```bash
  grep -n -P "^version = " contracts/pyproject.toml
  ```
  Esperado: el primer comando termina con 0; el segundo imprime `version = "0.1.1"`.

- [ ] **CA-5:** tipos y *lint*.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts ruff format --check .
  ```
  Esperado: los tres terminan con 0.

---

## Plan de pruebas

1. Primero, las pruebas `k56` en `contracts/tests/test_validators.py`. Cada una lleva `k56` en el nombre, para el filtro `-k`:
   - una instancia válida de `model-call.v1.yaml` pasa `validate_instance`, y lo mismo una de C18 y una de C19;
   - los 4 controles negativos de CA-2.

   Se ejecutan en rojo (CA-1), con un commit propio que deja constancia del rojo.
2. Después, el arreglo de `validators.py`. La lista cerrada de PD-4 va escrita como constante, y `x-veridicus-version` solo vale en la raíz. Luego se corren CA-2 a CA-5.

---

## Reglas de la app que aplican

- AUTONOMIA-02: cada criterio tiene su comando y su umbral.
- Los umbrales de cobertura nunca se bajan (team.md, Testing Posture).
- Solo datos sintéticos.

---

## Notas

- Se modifican en su sitio: `contracts/src/veridicus_contracts/validators.py`, `contracts/tests/test_validators.py`, `contracts/pyproject.toml` y `contracts/uv.lock`.
- La lista cerrada es la de PD-4: `x-veridicus-version`, `-limit`, `-max-bytes`, `-cookie`, `-owner-only`, `-owner-only-for-role`, `-priority`, `-roles`, `-access-log` y `-demo`. Las palabras `secreto`, `otra` y `mas` que aparecen hoy en las pruebas son sondas de marcas desconocidas y deben seguir rechazándose.
- La bitácora va en `docs/loop/bitacoras/U10-T01.md`: el par falla-pasa con los comandos y sus últimas líneas, en una página como máximo (ML-7).
- Si `uv lock --directory contracts` necesita red, corre antes `timeout 600 uv sync --frozen --directory contracts`.
