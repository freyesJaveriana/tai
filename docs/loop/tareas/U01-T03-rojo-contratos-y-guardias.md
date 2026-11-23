# U01-T03: ROJO, pruebas de contratos de datos y guardias AUTONOMIA-03/04/05

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con PD-9 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 5 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Las pruebas respaldan AC3.2.1, AC3.6.2, AC5.5.3, AC8.3.1, AC12.6.1, AC13.3.1 y AC15.4.7.
**Depende de:** U01-T02 (ola 3)

---

## Alcance

**Dentro:**

> La tarea **ROJO** del Testing Contract (PD-5). Se escriben, **antes de cualquier contrato**, los *fixtures* sintéticos de C6, C2, C3, C5, C7, C18, C19 y C21, el catálogo `contracts/fixtures/synthetic-names.yaml`, las pruebas de `tests/contracts/` y de `tests/guards/` (AUTONOMIA-03, 04 y 05), `tests/helpers.py`, los marcadores por contrato de PD-8 y la herramienta `veridicus_contracts.tools.check_red`. Se corren y la suite queda **en rojo comprobable: fallos, no errores**.

**Esta tarea no escribe ningún contrato.** Ni esquemas, ni catálogos, ni AsyncAPI, ni OpenAPI, ni módulos de `checks/`. Su producto son pruebas que fallan porque los contratos aún no existen.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Cualquier contrato: `analyzer/v1/*.schema.json` y `SHA256SUMS` (los pone el humano en T04, PD-4), `queues/*.v2.yaml` (T05), `integrity/review-suggestion.v2.json` (T06), `errors/error-codes.v2.yaml` (T07), C13 (T08), C18 (T09), C25 (T10), C8 y rótulos (T11), C19 (T12), C21, C16 y voz (T13), C1 (T14).
- F7 en `pytest_sessionstart` (T04). Las pruebas pueden llamar a F7, pero no lo implementan.
- Cualquier módulo de `src/veridicus_contracts/checks/` y cualquier herramienta distinta de `check_red`.
- Leer o copiar nada de `/insumos`. Los datos del piloto del TG nunca entran al repositorio; todos los *fixtures* son sintéticos.
- CI y *pre-commit* (paso 24).

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 5, PD-5, PD-8, PD-9, la tabla «Comandos de verificación» y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: F1, F2, F4, F7, escenarios E1–E44 y precisiones FD-U1-01 a FD-U1-14.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.2, BR1.3, BR1.7, BR2.1, BR2.3, BR3.1–BR3.6, BR4.1–BR4.4, BR5.1, BR6.1–BR6.3, BR7.1, BR9.3, BR9.9, BR10.1, BR10.2.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/entities.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.3, §4.8, §4.9, §4.10 (formato de *fixture*), §4.17, §4.18 y §4.19.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-requirements/security-requirements.md`: NFR1.1–NFR1.4, NFR10.2, NFR10.8, NFR10.10, NFR11.3–NFR11.5.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C2, C3, C5, C6, C7, C13, C18, C19 y C21 (forma de cada contrato, para escribir los *payloads*).
- `docs/loop/revisiones/U01-T01/ronda-4.md`: aviso F-11.
- `aidlc/spaces/default/memory/team.md`: Testing Posture (Mapa AUTONOMIA) y Code Style.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: la recolección no tiene errores (paso 5, primera parte).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --co -q
  ```
  Esperado: código 0 y ningún `error` de recolección. Ver la decisión pendiente A-1 en Notas.

- [ ] **CA-2**: la suite de contratos y guardias está en rojo por fallos, no por errores (paso 5, segunda parte).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --no-cov --junitxml=build/red.xml
  ```
  Esperado: código 1. El resumen dice `N failed` y no dice `error`. Lo normal es `0 passed`; toda prueba que pase ya en esta tarea se justifica una por una en la bitácora (no debe haber ninguna que pase en vacío porque su contrato no existe).

- [ ] **CA-3**: `check_red` confirma el rojo leyendo el informe real de pytest (paso 5, tercera parte).
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.check_red build/red.xml
  ```
  Esperado: código 0. La herramienta sale con código distinto de 0 si `errors` no es `"0"` o si `failures` es 0 (lectura de vuelta: lee el `build/red.xml` que acaba de escribir CA-2).

- [ ] **CA-4**: `check_red` tiene sus propias pruebas (precisión propuesta A-3).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/tools/test_check_red.py --no-cov
  ```
  Esperado: verde, con 5–8 pruebas: fallos sin errores → 0; algún error → distinto de 0; 0 fallos → distinto de 0; archivo ausente → distinto de 0; XML mal formado → distinto de 0.

- [ ] **CA-5**: toda prueba de contratos y guardias lleva al menos un marcador por contrato de PD-8, y los marcadores están registrados con `--strict-markers`.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --co -q --no-cov -m "c1 or c6 or c7 or c8 or c13 or c16 or c18 or c19 or c21 or labels or speech or asyncapi"
  ```
  ```bash
  grep -n -E "strict-markers|asyncapi" contracts/pyproject.toml
  ```
  Esperado: el primer comando recolecta **el mismo número** de pruebas que CA-1 (ninguna queda sin marcador). El segundo muestra `--strict-markers` en `addopts` y el bloque de marcadores registrados.

- [ ] **CA-6**: las tareas anteriores siguen en verde.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_runner.py tests/test_package_map.py tests/test_loaders.py tests/test_registry.py tests/test_canonical.py tests/test_validators.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-7**: no se escribió ningún contrato.
  ```bash
  git diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo rutas bajo `contracts/tests/`, bajo un directorio `fixtures/` de `contracts/`, `contracts/src/veridicus_contracts/tools/check_red.py`, `contracts/pyproject.toml` (marcadores) y `docs/loop/bitacoras/U01-T03.md`. Ningún archivo nuevo fuera de `fixtures/` en `analyzer/`, `api/`, `cli/`, `errors/`, `integrity/`, `profiles/`, `queues/`, `model_calls/` ni en `checks/`.

- [ ] **CA-8**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-9**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

Esta tarea **es** el rojo previo del Testing Contract (`ordering` custom, PD-5): las pruebas de contratos de datos y de las guardias AUTONOMIA-03/04/05 se escriben primero y se ven fallar. Orden:

1. `contracts/fixtures/synthetic-names.yaml` y el formato de *fixture* de §4.10: `fixture_id`, `contract`, `synthetic: true`, `expectation: accept|reject`, `reject_reason` (ID de regla, obligatorio en `reject`), `mentions` y `payload`.
2. Los *fixtures* de datos del paso 5, uno por escenario como mínimo, en `analyzer/v1/fixtures/`, `queues/fixtures/runs/`, `queues/fixtures/results/`, `queues/fixtures/speech/`, `integrity/fixtures/review-suggestion/`, `profiles/fixtures/`, `cli/fixtures/` y `api/fixtures/anonymizer-proxy/`. Incluye `anonimizador_no_disponible` e `incidente_anonimizacion` válidos en C6 (CD-01).
3. `tests/helpers.py` con `load_contract(path)`: un contrato ausente es `pytest.fail("contrato ausente: <ruta>")`, nunca una excepción sin capturar.
4. `tests/contracts/`: `test_analyzer_copy.py`, `test_queue_messages.py`, `test_review_suggestion.py`, `test_profiles_contract.py`, `test_cli_report.py`, `test_anonymizer_proxy.py` y `test_model_call.py`. Cada *fixture* se valida contra su contrato y debe aceptarse, o rechazarse **por su** `reject_reason` (NFR10.10, F1).
5. `tests/guards/test_autonomia_03.py`, `test_autonomia_04.py` y `test_autonomia_05.py`, con lo que enumera el paso 5 (incluidos los controles E15 `PUT /profiles` y C21 con `https://api.openai.com`, y «F7 detecta E18»).
6. `tools/check_red.py` y `tests/tools/test_check_red.py`.
7. Correr CA-1, CA-2 y CA-3 y **pegar la salida en rojo** en `docs/loop/bitacoras/U01-T03.md`.

Reglas para que el rojo sea un fallo y no un error:

- Nada que falte se importa en la cabecera del módulo de prueba. `veridicus_contracts.model_calls` (`AnonymizingProvider`, T08) y la función de F7 (T04) se importan **dentro** de la prueba, y un `ImportError` se convierte en `pytest.fail(...)` con el mismo criterio que `load_contract`.
- Ninguna guardia pasa en vacío: si un recorrido no encuentra el contrato que debe recorrer, falla con «contrato ausente».

Marcadores (PD-8): cada prueba lleva el marcador del contrato que lee (`c1`, `c6`, `c7`, `c13`, `c16`, `c18`, `c19`, `c21`, `c8`, `labels`, `speech`, `asyncapi`). Una comprobación que recorre varios contratos se parametriza **por contrato** con `pytest.param(..., marks=pytest.mark.<cN>)`, de modo que cada caso lleve un solo marcador. Así funcionan los filtros de los pasos siguientes: `-m c6` en T04, `-m "c8 or labels"` en T11 y `-m "not c1"` en T13. Por ejemplo, «enum de C6 iguales en C1, C7 y C19» son tres casos (`c1`, `c7`, `c19`). Los mensajes de cola C2, C3 y C5 llevan `asyncapi`; `speech` es la ruta interna de voz (`api/speech-internal.v1.yaml`, T13).

---

## Reglas de la app que aplican

- **AUTONOMIA-03** (Mapa AUTONOMIA): esquema sin campos de veracidad y vocabulario prohibido → `tests/guards/test_autonomia_03.py` (BR3.2, BR3.3, BR5.1, BR6.1–BR6.3, BR7.1, BR4.4).
- **AUTONOMIA-04**: `servers` internos, una sola puerta `generate`, C21 estricto y C19 sin texto libre → `tests/guards/test_autonomia_04.py` (NFR1.1–NFR1.4, BR9.9).
- **AUTONOMIA-05**: hallazgo rechazado sin cada campo obligatorio, `error` ⇒ hallazgos vacíos, C7 sin los 5 campos, F7 ante E18 → `tests/guards/test_autonomia_05.py` (BR3.1, BR3.6, BR4.1, BR1.7).
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`, NFR12.1): nombres y lugares de `synthetic-names.yaml`, inventados; ningún texto, nombre ni fragmento del piloto del TG; nada de la partición `referencia`; nada leído de `/insumos`.
- **team.md, Code Style:** mypy estricto, Ruff con reglas `S` y motivo en toda supresión.

---

## Notas

- Archivos que se **modifican en su sitio**: `contracts/pyproject.toml`, solo `[tool.pytest.ini_options]`: `--strict-markers` en `addopts` y la lista `markers` de PD-8. No se tocan dependencias ni `uv.lock`.
- `check_red` lee un XML que produce pytest en la propia máquina. Si usa `xml.etree`, Ruff marca `S314`: la supresión lleva su motivo («informe JUnit local generado por pytest, no es entrada externa»). No añadas `defusedxml` ni otra dependencia.
- `build/red.xml` queda bajo `contracts/build/`, que ignora `.gitignore`; pytest crea la carpeta si falta. No se versiona.
- Los archivos de prueba tienen nombres únicos en todo `tests/` y sus subcarpetas no llevan `__init__.py` (modo de importación por defecto, igual que hoy).
- Los *payloads* de C6 se escriben con la forma que da contract-summary §C6. La copia real llega en T04; ver la decisión pendiente A-4.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- PD-9: el único módulo nuevo es `contracts/src/veridicus_contracts/tools/check_red.py`. No crees `src/veridicus_contracts/__init__.py`.
- Desde esta tarea y hasta T15, la suite completa (`pytest` sin rutas, V-SUITE) queda en rojo a propósito. Ninguna tarea intermedia usa V-SUITE como criterio.
- Conventional Commits en español con alcance `contracts`, por ejemplo `test(contracts): pruebas en rojo de contratos de datos y guardias AUTONOMIA (T03)`.

### Decisiones pendientes para el humano (antes del despacho)

- **A-1.** El comando de recolección del plan (`--co -q`) no lleva `--no-cov`. Con `--cov-fail-under=80` en `addopts`, pytest-cov puede dar código 1 por cobertura aunque no haya errores de recolección. Propuesta: añadir `--no-cov` a CA-1. Si se deja tal cual y falla solo por cobertura, el codificador no baja el umbral; lo anota en la bitácora y para.
- **A-2.** El paso 5 lista `tests/contracts/test_model_call.py` pero no nombra *fixtures* de C13. Propuesta: `model_calls/fixtures/` con una llamada válida y E27 (`role: "Prueba A"`, rechazo por BR9.1).
- **A-3.** El plan no nombra las pruebas de `check_red`. CA-4 las propone (5–8 pruebas por componente, Testing Contract).
- **A-4.** Sin la copia de C6, los *payloads* de C6 se escriben desde contract-summary y pueden no coincidir con la copia real. Opciones: (a) permitir al codificador **leer** (nunca copiar) los dos `*.schema.json` de `/insumos/app/contratos/analizador/v1/`; (b) permitir que T04 ajuste solo el `payload` de los *fixtures* de C6, nunca su `expectation` ni su `reject_reason`, con cada ajuste justificado en su bitácora.
