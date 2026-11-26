# U10-T02: paquete `libs/anonymizer`, pruebas en rojo de las guardias y `FakeTransport`

**Unidad:** U10 `anonymizer`   **Bolt:** B10a   **Rama base:** `bolt/b10a-anonymizer`
**Pasos del plan que cubre:** pasos 2 a 5 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md`
**Historias que implementa:** US11.3 (AC11.3.1, AC11.3.3, AC11.3.4 casos a–c, AC11.3.5, AC11.3.6 y AC11.3.7, todos solo **en rojo**) y US11.5 (AC11.5.1, en rojo). El `FakeTransport` es soporte de E19 y E23.
**Depende de:** ninguna. Corre en paralelo con U10-T01.
**Riesgo (ML-4):** alto (guardias AUTONOMIA-04 y 05) → `revisor` con `opus`

---

## Alcance

**Dentro:**

> - la estructura de `libs/anonymizer/` con *stubs* que lanzan `NotImplementedError` (paso 2);
> - el ejecutor de pruebas sin red (paso 3);
> - las pruebas en rojo de AUTONOMIA-04/05 y de los contratos de datos del módulo, en su propio commit (paso 4);
> - el `FakeTransport` y el control negativo `bypass`, implementados y probados (paso 5).

**Fuera** (rechazar aunque se vea roto):

- **Toda implementación del dominio, de la aplicación o del adaptador.** Los *stubs* solo lanzan `NotImplementedError`: los pasos 6 a 11 son de T03 y T04.
- Los archivos de datos de `data/`, salvo sus **esquemas** en `data/schemas/`, que necesita `test_data_files.py`. Los YAML los escribe T03.
- `contracts/`: es de U10-T01. Si `test_model_call_contract.py` falla por K-56, es el rojo esperado; no se arregla aquí.
- NER, proxy, OpenAI, Google y Corefile: van a B10b (DP-03).
- CI y guardias de `scripts/`: son de T05.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md`: decisiones PD-1 a PD-10, pasos 2 a 5 y Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/functional-design/functional-spec.md`: F1, F4 a F7 y los escenarios E1, E2, E5, E6, E9, E25, E26, E29 y E34.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/functional-design/rules.md`: BR1, BR2, BR3.1, BR4 y BR5.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/functional-design/entities.md`: `MaskTable`, `Marker`, `RestorationOutcome` y `FakeTransport`.
- `contracts/src/veridicus_contracts/model_calls.py` (C13: `GenerateRequest`, `ModelCall`, errores tipados y `AnonymizingProvider`).
- `contracts/model_calls/model-call.v1.yaml` y `contracts/limits.v1.yaml`.
- `libs/errors/pyproject.toml`, como modelo de configuración.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U10-T02`.

- [ ] **CA-1 (paso 2):** el paquete se instala, el lock está al día y los *stubs* tipan.
  ```bash
  timeout 600 uv sync --frozen --directory libs/anonymizer
  ```
  ```bash
  timeout 120 uv lock --check --directory libs/anonymizer
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer mypy --strict src
  ```
  Esperado: los tres terminan con 0.

- [ ] **CA-2 (paso 3):** el ejecutor está listo y bloquea la red.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/test_package.py -q
  ```
  Esperado: código 0, con al menos 2 pruebas. Una de ellas comprueba que `pytest-socket` rechaza una conexión.
  Lectura de vuelta: `grep -n "addopts" libs/anonymizer/pyproject.toml` muestra `--disable-socket` y **ningún** `--cov`.

- [ ] **CA-3 (paso 4, recolección):** las pruebas del rojo se recolectan sin errores.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts --collect-only -q
  ```
  Esperado: código 0, 0 errores de recolección y al menos 30 pruebas.

- [ ] **CA-4 (paso 4, rojo):** todas fallan, ninguna da error y están en su propio commit.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts -p no:cacheprovider -rf
  ```
  Esperado: código 1, el 100 % en `FAILED` y 0 en `ERROR`. El resumen `-rf` muestra `NotImplementedError`, o el rechazo de K-56 en `test_model_call_contract.py`.
  Lectura de vuelta: `git -C /workspace/.worktrees/U10-T02 log --oneline -- libs/anonymizer/tests/guards libs/anonymizer/tests/contracts` muestra **un** commit `test(anonymizer): pruebas en rojo de AUTONOMIA-04/05 y contratos de datos`. Su SHA va a la bitácora como `ROJO_SHA`.

- [ ] **CA-5 (paso 5):** el `FakeTransport` está implementado, con el 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/testing --cov=veridicus_anonymizer.testing.fake_transport --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Esperado: código 0, con al menos 6 pruebas y el 100 % de ramas en `testing/fake_transport.py`.

- [ ] **CA-6:** tipos y *lint* de todo lo que entrega la tarea.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff format --check .
  ```
  Esperado: los tres terminan con 0.

- [ ] **CA-7:** las guardias del repositorio público siguen limpias con los *fixtures* nuevos.
  ```bash
  bash scripts/check-no-datos-personales.sh
  ```
  ```bash
  bash scripts/check-no-cluster-ids.sh
  ```
  ```bash
  bash scripts/check-no-insumos.sh
  ```
  Esperado: los tres imprimen `0 apariciones` y terminan con 0.

---

## Plan de pruebas

Este es el orden del Testing Contract `custom`.

1. Primero, los pasos 2 y 3, con los *stubs* y el ejecutor listos.
2. Después, el **paso 4, en rojo**, en un commit propio. Los archivos y el contenido de cada uno están en el paso 4 del plan:
   - `tests/guards/test_autonomia_04_payload.py`;
   - `tests/guards/test_autonomia_04_fail_closed.py`, parametrizado y con su control positivo;
   - `tests/guards/test_autonomia_04_no_leak.py`, que busca en la petición cruda y recorre `__cause__` y `__context__`;
   - `tests/guards/test_autonomia_05_restoration.py`;
   - `tests/contracts/test_model_call_contract.py`;
   - `tests/contracts/test_data_files.py`.
3. Luego, el paso 5: se implementan `testing/fake_transport.py` y `testing/bypass.py`, y se escriben `tests/testing/test_fake_transport.py`.
4. Las pruebas del paso 4 **no se tocan** después de su commit. El paso 10 (U10-T04) comprueba con `git diff --exit-code ROJO_SHA` que siguen iguales.

---

## Reglas de la app que aplican

- **AUTONOMIA-04.** La prueba del payload saliente y la de fallo cerrado van aquí en rojo. El control negativo `bypass` debe hacer fallar la prueba del payload.
- **AUTONOMIA-05, del lado de U10.** La prueba de que la cita seudonimizada se restaura antes de verificarse va aquí en rojo.
- **AUTONOMIA-02.** Cada criterio tiene su comando.
- **Solo datos sintéticos.** Los nombres, lugares e identificadores son inventados. Nada del piloto, de `/insumos` ni de la partición `referencia`.
- La clave de API de las pruebas es un *canary* inventado, nunca una clave real.

---

## Notas

- **Proveedor:** Anthropic, `claude-sonnet-5-5` (PD-1). Los *fixtures* de respuesta van en `tests/fixtures/anthropic/`. La clave va en la cabecera de autenticación de Anthropic, y su nombre exacto sale de la documentación oficial (consulta por MCP, solo con términos técnicos genéricos).
- **«Abre oración»** tiene la definición de PD-2. El conjunto sembrado pone nombres con mayúscula en **cada** posición de apertura.
- **`FakeTransport`** guarda la petición **cruda** y oculta la clave solo al representarla (R-07).
- **`bypass`** reemplaza la función interna de seudonimización con `monkeypatch`. `build_anonymizer` no tiene ningún parámetro para saltársela (PD-7).
- **Rojo esperado:** `test_model_call_contract.py` puede fallar por K-56 hasta que U10-T01 se fusione. Eso cuenta como rojo.
- **Bitácora:** `docs/loop/bitacoras/U10-T02.md`, con el par falla-pasa, el `ROJO_SHA` y, como máximo, una página (ML-7).
