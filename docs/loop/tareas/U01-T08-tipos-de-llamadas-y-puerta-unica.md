# U01-T08: tipos de llamadas a modelos (C13) y puerta única `AnonymizingProvider`

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 10 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Respalda AC11.6.4 y AC13.3.1.
**Depende de:** U01-T05, U01-T06 y U01-T07 (ola 6, en paralelo con U01-T09 y U01-T10).

---

## Alcance

**Dentro:**

> - `contracts/src/veridicus_contracts/model_calls.py`: tipos de C13.
>   - `Role` es un `str` con el patrón `^[a-z][a-z0-9_]{0,31}$` (FD-U1-01, BR9.1).
>   - `GenerateRequest`, `GenerateResult` y `ModelCall`.
>   - `ModelCallError` con sus cinco subclases. `ContentBlocked`, `Timeout`, `ProviderError` e `InvalidOutput` llevan `call: ModelCall`; `AnonymizerUnavailable` no lo lleva.
>   - El `Protocol` `AnonymizingProvider`, con solo `generate(self, request: GenerateRequest) -> GenerateResult`. El módulo no importa nada fuera de `veridicus_contracts`, `typing`, `dataclasses`, `enum` y `datetime` (BR9.9, revisión 3 de C13).
> - `contracts/model_calls/model-call.v1.yaml`: estricto, con `role` con patrón.
> - `contracts/model_calls/role-translation.v1.yaml`: traduce solo los tres papeles del analizador a `registro.llamadas` de C6 (BR9.6).
> - `src/veridicus_contracts/checks/protocol_surface.py`: módulo guardia, §4.17.
> - Pruebas nuevas:
>   - `tests/typing/test_anonymizing_provider.py` y `tests/checks/test_protocol_surface.py`, de 5 a 8 pruebas.
>   - Un doble con solo `generate` da 0 errores con `mypy.api.run --strict`; un doble sin él da el error esperado (E42).
>   - `check_ready()` en el `Protocol`, o una importación ajena, da rojo (E43).
>   - E27: `role: "Prueba A"` se rechaza.
>
> `tests/contracts/test_model_call.py` ya existe (T03) y esta tarea lo pone en verde.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- El ModelGateway y los adaptadores (U11, U10).
- Editar los *fixtures* o las pruebas de T03. Si una prueba parece mal, el codificador para y lo informa en `docs/loop/CANDIDATAS.md`; no la cambia.
- **Archivos de las tareas vecinas de la ola 6**, que corren en paralelo y no se pisan:

  | Tarea | Archivos que toca |
  |---|---|
  | **T08 (esta)** | `contracts/src/veridicus_contracts/model_calls.py`, `contracts/model_calls/*.yaml`, `contracts/src/veridicus_contracts/checks/protocol_surface.py`, `contracts/tests/typing/`, `contracts/tests/checks/test_protocol_surface.py` |
  | T09 | `contracts/profiles/profile-base.schema.v1.yaml`, `profiles.schema.v1.yaml`, `prices.schema.v1.yaml`, `contracts/src/veridicus_contracts/profiles.py`, `contracts/tests/test_profiles.py` |
  | T10 | `contracts/limits.v1.yaml`, `contracts/src/veridicus_contracts/limits.py`, `contracts/src/veridicus_contracts/checks/limits_catalog.py`, `contracts/tests/test_limits.py`, `contracts/tests/checks/test_limits_catalog.py`, `contracts/hatch_build.py` y las claves `include`, `sources` y `cache-keys` de `contracts/pyproject.toml` |

  T08 y T09 no tocan `contracts/pyproject.toml`, `contracts/uv.lock`, `contracts/hatch_build.py`, `contracts/tests/conftest.py`, `contracts/tests/helpers.py` ni `checks/__init__.py`. Si lo necesitan, paran y lo informan.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 10, PD-1, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C13 (revisión 3).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: FD-U1-01, E27, E42 y E43.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR9.1, BR9.6 y BR9.9.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.17.
- `contracts/analyzer/v1/salida.schema.json`, en solo lectura, para `registro.llamadas`.
- `docs/loop/bitacoras/U01-T03.md`: supuesto de T08 (`model_calls.py` junto al directorio de datos `model_calls/`).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 10.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/typing tests/checks/test_protocol_surface.py tests/contracts/test_model_call.py --no-cov
  ```
  Esperado: verde, con E27, E42 y E43 cubiertos.

- [ ] **CA-2**: las guardias que leen C13 pasan a verde.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards -m c13 --no-cov --deselect "tests/guards/test_autonomia_03.py::test_ningun_nombre_ni_enum_declara_veracidad[c13-llamada]"
  ```
  Esperado: verde. El caso excluido necesita también C8 (`integrity/forbidden-vocabulary.v2.yaml`, paso 13) y pasa a verde en la tarea que escribe C8. Este criterio lo añadió el orquestador: la verificación del paso 10 en el plan no incluye las guardias (precisión P-T08-1, ronda 1).

- [ ] **CA-3**: 100 % de ramas en `checks/protocol_surface.py` (módulo guardia).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/typing tests/checks/test_protocol_surface.py --cov-fail-under=0
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/protocol_surface.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, 100 % de líneas y de ramas. `addopts` ya mide todo el paquete con ramas, así que el umbral se aplica solo al módulo guardia con `coverage report --include`.

- [ ] **CA-4**: los datos de `model_calls/` siguen en la instalación editable y en la rueda, junto al módulo `model_calls.py`.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde. En la bitácora, la lectura de vuelta de los dos YAML con `importlib.resources.files("veridicus_contracts")` (no con `files("veridicus_contracts.model_calls")`, que ahora es el módulo).

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

El rojo de `test_model_call.py` es de T03. Corre CA-1 antes de escribir nada y pega la salida en rojo en `docs/loop/bitacoras/U01-T08.md`. Las pruebas nuevas de `tests/typing/` y `test_protocol_surface.py` se escriben primero y se ven fallar.

Las pruebas de tipos llaman a `mypy.api.run` sobre archivos de prueba escritos en `tmp_path`, nunca en `src/`.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** `AnonymizingProvider` es la única puerta hacia un proveedor. Tiene un solo método, `generate`, y nada de comprobaciones de estado públicas (NFR1.2, BR9.9).
- **AUTONOMIA-03:** ningún nombre ni enum con vocabulario de veracidad. La guardia de `test_autonomia_03.py` lo recorre.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- Solo datos sintéticos.

---

## Notas

- **Riesgo de T03:** con `model_calls.py` en `src/`, `veridicus_contracts.model_calls` resuelve al módulo y no al directorio de datos.
  - Los YAML se leen como recursos del paquete raíz: `files("veridicus_contracts") / "model_calls" / "…"`.
  - Si algo de T01 o T02 los busca de otra forma, el codificador para y lo informa.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): tipos de C13 y puerta única (T08)`. Sin signo de dólar en el mensaje.
