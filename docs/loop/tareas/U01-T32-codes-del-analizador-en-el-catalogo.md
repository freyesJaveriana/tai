# U01-T32: los tres `code` del analizador en el catálogo de errores

**Unidad:** U1 `contracts` (tarea correctiva, fuera del plan de U11)   **Rama base:** `main`
**Origen:** bloqueo de U11-T01, ronda 1. Las clases nuevas de `libs/errors` (PD-5 / CG-U11-04 de U11) no tienen su `code` en `contracts/errors/error-codes.v2.yaml`, y la guardia V-ERRORS falla. El humano decidió el 2026-11-26 resolverlo con una tarea de U1 aparte, que entra a `main` **antes** del PR del Bolt B11a.
**Depende de:** ninguna.
**Riesgo (ML-4):** bajo (catálogo de contratos, sin lógica) → `revisor` con `sonnet`.

---

## Alcance

**Dentro:**

> - Agregar al catálogo `contracts/errors/error-codes.v2.yaml` los tres `code` nuevos, todos con `unit: U11` y `http: false`, sin `status` ni `c6`:
>
>   | `code` | `class` |
>   |---|---|
>   | `run.cancelled` | `CancelledError` |
>   | `config.invalid_gateway` | `GatewayConfigError` |
>   | `system.interrupted` | `CliInterruptedError` |
>
>   Los nombres terminan en `Error` porque `contracts/tests/test_errors_catalog.py` lo exige. Así lo decidió el orquestador en la ronda 1, y esta versión de la tarea ya los trae corregidos.
>
>   Cada uno va en el bloque de su familia: `run.*`, `config.*` y `system.*`.
> - Dejar `libs/errors/src/veridicus_errors/__init__.py` y `libs/errors/tests/test_analyzer_errors.py` **idénticos byte a byte** a como están en la rama `tarea/U11-T01`. Así, la fusión posterior del Bolt encuentra los mismos cambios y no da conflicto.
>   - Se leen con `git -C /workspace show tarea/U11-T01:<ruta>` y se escriben con Write.
>   - La igualdad se comprueba con `sha256sum`.
> - Si V-ERRORS o cualquier otra prueba de `contracts` exige algo más para esos `code`, se agrega solo en `contracts/`. Algunos ejemplos: un `detail`, una entrada en la documentación del catálogo o un *changelog*.

**Fuera:**

- Cualquier otro cambio en `libs/errors`: los dos archivos quedan iguales a `tarea/U11-T01`.
- Si V-ERRORS exige otra forma de nombre o una clase distinta, **no** inventes una. Para y repórtalo, porque cambiaría el trabajo ya revisado de U11-T01.
- El resto de U11 y `libs/anonymizer`.

---

## Archivos de contexto

- `contracts/errors/error-codes.v2.yaml`
- `contracts/tests/checks/test_error_codes.py` (V-ERRORS)
- `libs/errors/src/veridicus_errors/__init__.py` y `libs/errors/tests/`, en `main` y en `tarea/U11-T01`
- `contracts/CHANGELOG.md`, si existe, para seguir la convención de versión

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U01-T32`.

- [ ] **CA-1:** V-ERRORS pasa.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks/test_error_codes.py --no-cov -q
  ```
  Esperado: código 0.
  Par falla-pasa: con el catálogo de `main` y los archivos de `libs/errors` copiados, esta prueba falla en 2 casos. Con el catálogo nuevo, pasa.

- [ ] **CA-2:** los dos archivos de `libs/errors` son idénticos a los de `tarea/U11-T01`.
  ```bash
  sha256sum libs/errors/src/veridicus_errors/__init__.py libs/errors/tests/test_analyzer_errors.py
  ```
  Esperado: los mismos dos *hash* que da `git -C /workspace show tarea/U11-T01:<ruta>`, comparados en la bitácora.

- [ ] **CA-3:** `libs/errors` sigue en verde.
  ```bash
  timeout 60 uv run --frozen --offline --directory libs/errors pytest
  ```
  Esperado: código 0.

- [ ] **CA-4:** la suite completa de `contracts` sigue en verde y con su cobertura.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest
  ```
  Esperado: código 0, sin pruebas omitidas nuevas. Anota en la bitácora el tiempo que tardó.

- [ ] **CA-5:** el *lint* del YAML y las guardias del repositorio siguen limpios.
  ```bash
  bash scripts/check-no-datos-personales.sh
  ```
  ```bash
  bash scripts/check-no-cluster-ids.sh
  ```
  Esperado: los dos imprimen `0 apariciones` y terminan con 0.

---

## Notas

- Commit en Conventional Commits en español: `fix(contracts): codes del analizador en el catálogo de errores (U01-T32)`.
- **Bitácora:** `docs/loop/bitacoras/U01-T32.md`, de una página como máximo.
- Este PR va contra `main`, no contra la rama del Bolt. Lo fusiona el humano.
