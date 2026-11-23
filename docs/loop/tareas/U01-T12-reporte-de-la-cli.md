# U01-T12: reporte de la CLI C19 v2

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 14 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T05 a U01-T10, ya fusionadas, sobre todo `model_calls/model-call.v1.yaml` (T08) y C18 (T05 y T09). Corre en la ola 7, en paralelo con U01-T11 y U01-T13.

---

## Alcance

**Dentro:**

> - `contracts/cli/report.schema.v2.yaml` (C19), que referencia `model_calls/model-call.v1.yaml`:
>   - Toda cadena es `enum`, `const` o un patrón portátil sin espacios, con `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`.
>   - Todo entero lleva `minimum` y `maximum`: de 0 a 2^53 − 1; `seed` también admite negativos y `estimated_cost` va hasta 10^9.
>   - Campos `origin` y `blocking`, y latencia p50 y p95 por papel en ms enteros.
>   - Sección opcional `clarifications`, solo con enteros.
>   - Un `allOf` que restringe las llamadas a los tres papeles del analizador (§4.18, NFRD-U1-06, FD-U1-03).
> - `contracts/src/veridicus_contracts/checks/report_closed.py`, módulo guardia:
>   - E28 y E29;
>   - el límite declarado del *canary* de una palabra (FD-U1-05; lo cierra U12).
> - Pruebas nuevas en `contracts/tests/checks/test_report_closed.py`. Rojo primero.
> - Los *fixtures* de C19 y `tests/contracts/test_cli_report.py` ya existen (T03): este paso escribe el contrato y la guardia.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Comparar `report_token_max_chars` con C25: lo hace el paso 16 (T15, PD-8).
- La ingesta y la persistencia del reporte: son de U12.
- Editar los *fixtures* o las pruebas de T03, `model-call.v1.yaml` y los esquemas de perfiles.
- **Archivos de las tareas vecinas de la ola 7:** `contracts/integrity/`, `contracts/ui/`, `contracts/api/`, `contracts/health/`, `checks/veracity.py`, `checks/scan_cases.py` y `checks/servers.py`, con sus pruebas.
- `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`: `cli/` ya se empaqueta. Si necesitas tocarlos, para y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 14, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C19 (revisión 4, P12 = A: cada cadena permitida se cierra con `pattern`).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E28, E29, FD-U1-03 y FD-U1-05.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR10.1 y BR10.2.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.18 y NFRD-U1-06.
- `contracts/tests/contracts/test_cli_report.py` y `contracts/tests/guards/test_autonomia_04.py` (T03): ya esperan C19. Léelos, no los edites.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 14.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_cli_report.py tests/checks/test_report_closed.py --no-cov
  ```
  Esperado: verde, con los 4 *fixtures* de C19 aceptados o rechazados por su regla.

- [ ] **CA-2**: AUTONOMIA-04 sobre C19 (E-6: los casos `c19` se ponen en verde en este paso).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_04.py -m c19 --no-cov
  ```
  Esperado: verde. `test_c19_no_tiene_campos_de_texto_libre` pasa.

- [ ] **CA-3**: 100 % de ramas en `checks/report_closed.py` (módulo guardia).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/checks/test_report_closed.py --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/report_closed.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, 100 % de líneas y de ramas.

- [ ] **CA-4**: el contrato está en la instalación editable y en la rueda.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-5**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-6**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero `test_report_closed.py`, con un control negativo por regla:
   - una cadena sin `enum`, `const` ni `pattern`;
   - un patrón que admite espacios;
   - un entero sin `maximum`;
   - una llamada con un papel ajeno al analizador;
   - el *canary* de una palabra en un campo con patrón.
2. Mira fallar `test_report_closed.py` y `test_cli_report.py`, y pega la salida en rojo en `docs/loop/bitacoras/U01-T12.md`.
3. Escribe el contrato y la guardia hasta el verde.

---

## Reglas de la app que aplican

- **AUTONOMIA-04 y el repositorio público:** el reporte de la CLI solo lleva cifras, hashes, versiones y nombres de perfil, nunca testimonio. Por eso cada cadena se cierra con `pattern` (P12 = A).
- **AUTONOMIA-03:** ningún campo de veracidad.
- **Solo datos sintéticos** (`project.md`).
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): reporte de la CLI C19 v2 y su guardia (U01-T12)`. Sin signo de dólar en el mensaje.
