# U10-T04: adaptador nativo de Anthropic, `Anonymizer.generate`, `build_anonymizer` y fronteras

**Unidad:** U10 `anonymizer`   **Bolt:** B10a   **Rama base:** `bolt/b10a-anonymizer`, con U10-T01, U10-T02 y U10-T03 fusionadas
**Pasos del plan que cubre:** pasos 9, 10 y 11 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md`
**Historias que implementa:** US11.3 (AC11.3.3, AC11.3.6, AC11.3.7), US13.3 (AC13.3.2, sin NER) y US13.6 (AC13.6.1 Anthropic, AC13.6.2). Pasa a verde el rojo de AUTONOMIA-04/05 de `afa8f20`.
**Depende de:** U10-T03 (dominio: catálogos, seudonimización y restauración).
**Riesgo (ML-4):** alto (salida al exterior, fallo cerrado de AUTONOMIA-04, fronteras) → `revisor` con `opus`

---

## Alcance

**Dentro:**

> - paso 9: `providers/http.py::default_transport()` y `providers/anthropic.py` (envío único, lectura con tope, clave solo en su cabecera, errores tipados con `ModelCall`);
> - paso 10: regenerar `libs/anonymizer/uv.lock` contra `contracts` 0.1.1; `application/generate.py` y `api.py` (`build_anonymizer(env, transport=None)`), con la comprobación del destino, el presupuesto de NFR3.5 y la liberación de la tabla;
> - paso 11: contratos de import-linter con sus controles negativos en `tests/boundaries/` y la prueba de logs con `caplog`.

**Fuera** (rechazar aunque se vea roto):

- **Las rutas del rojo no se tocan:** `tests/guards`, `tests/contracts`, `tests/support.py` y `tests/fixtures` quedan idénticas a `afa8f20` (CG-U10-08, CA-3).
- `domain/`: es de U10-T03. Si un defecto del dominio impide un verde, se describe en la bitácora como candidata y se para; no se arregla aquí.
- OpenAI y Google (fallan cerrado hasta B10b), NER, proxy y Corefile (DP-03).
- CI, `scripts/` y documentación: son de U10-T05.
- `contracts/` (salvo leerlo).

---

## Archivos de contexto

- El plan: PD-1, PD-7, PD-8, PD-9 y los pasos 9 a 11.
- `unit-test-instructions.md`, en la misma carpeta del plan.
- `construction/anonymizer/functional-design/functional-spec.md`: F1, F3b, F5 y F7 (con la fila de CG-U10-07), y los escenarios E19–E21, E23 y E27.
- `construction/anonymizer/functional-design/rules.md`: BR1.6, BR2.1–BR2.6, BR3.1, BR3.5 y BR5.1–BR5.5.
- `contracts/src/veridicus_contracts/model_calls.py` (C13) y `contracts/model_calls/model-call.v1.yaml`.
- `docs/loop/bitacoras/U10-T02.md` y `docs/loop/bitacoras/U10-T03.md` (costuras del rojo y estado de las pruebas que dejó T03).
- `docs/loop/revisiones/U10-T02/ronda-2.md` (F-12 y F-13).

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U10-T04`. Primero, una sola vez: `timeout 600 uv sync --frozen --directory libs/anonymizer`; después, `timeout 600 uv lock --directory libs/anonymizer` para regenerar el lock contra 0.1.1 (puede usar red) y `timeout 600 uv sync --frozen --directory libs/anonymizer` otra vez.

- [ ] **CA-1 (paso 9):**
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/providers --cov=veridicus_anonymizer.providers --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Esperado: código 0; al menos 10 pruebas; 100 % de ramas en `providers/`; 0 conexiones reales.

- [ ] **CA-2 (paso 10):**
  ```bash
  timeout 120 uv lock --check --directory libs/anonymizer
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts tests/application --cov=veridicus_anonymizer.application --cov=veridicus_anonymizer.api --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Esperado: los dos terminan con 0; **todas** las pruebas del rojo pasan; 100 % de ramas en `application/` y `api.py`. Lectura de vuelta: `grep -n -P "veridicus-contracts|version = \"0\.1\.1\"" libs/anonymizer/uv.lock` muestra la 0.1.1.

- [ ] **CA-3 (candado del rojo, CG-U10-08):**
  ```bash
  git -C /workspace/.worktrees/U10-T04 diff --exit-code afa8f20 -- libs/anonymizer/tests/guards libs/anonymizer/tests/contracts libs/anonymizer/tests/support.py libs/anonymizer/tests/fixtures
  ```
  Esperado: código 0.

- [ ] **CA-4 (paso 11):**
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer lint-imports
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/boundaries --no-cov -q
  ```
  Esperado: `lint-imports` termina con 0; las pruebas terminan con 0, con al menos 4; cada uno de los 3 controles negativos hace fallar `lint-imports` (código ≠ 0) dentro de su prueba.

- [ ] **CA-5 (suite del paquete y firma):**
  ```bash
  timeout 600 uv run --frozen --offline --directory libs/anonymizer pytest -p no:cacheprovider
  ```
  Esperado: código 0, 0 `ERROR`, 0 `FAILED`. Una prueba de la firma comprueba que `build_anonymizer` solo acepta `env` y `transport` (PD-7).

- [ ] **CA-6:** tipos, *lint* y guardias.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff format --check .
  ```
  ```bash
  bash scripts/check-no-datos-personales.sh
  ```
  ```bash
  bash scripts/check-no-cluster-ids.sh
  ```
  ```bash
  bash scripts/check-no-insumos.sh
  ```
  Esperado: todos terminan con 0; las guardias imprimen `0 apariciones`.

---

## Plan de pruebas

Orden del Testing Contract `custom`: el rojo de las guardias y contratos ya existe (`afa8f20`) y debe pasar a verde **sin cambios**. En cada paso se implementa la capa y enseguida se escriben y corren sus pruebas propias (`tests/providers/`, `tests/application/`, `tests/boundaries/`), antes del paso siguiente (9 → 10 → 11).

- **Paso 9:** contrato con respuestas grabadas sintéticas contrastadas con la documentación (E27, lado Anthropic); E19, E20, E21 y E23; una sola petición ante un 503 seguido de un 200 (BR2.4); `default_transport` inspeccionado sin abrir red.
- **Paso 10:** el rojo completo en verde; la firma de `build_anonymizer`; la liberación de la tabla en todos los finales; `openai` y `google` fallan cerrado; excepción inesperada después del envío → `ProviderError` con `ModelCall` (PD-9).
- **Paso 11:** los tres contratos y sus tres controles negativos; `caplog` con solo los campos de BR2.3.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** nada sale sin seudonimizar; ante cualquier falla antes del envío, 0 peticiones (`AnonymizerUnavailable`); la clave solo en su cabecera y nunca en un log, un `repr` ni una excepción.
- **AUTONOMIA-05, lado U10:** se restaura antes de devolver; las marcas alteradas quedan sin restaurar y anotadas.
- **AUTONOMIA-01:** sin red en las pruebas; nunca una llamada real al proveedor.
- **AUTONOMIA-02:** cada criterio tiene su comando y su umbral.
- **Solo datos sintéticos.** La clave de las pruebas es un *canary* inventado.

---

## Notas

- **API de Anthropic, verificada por el orquestador en la documentación oficial** (cítala en la bitácora: `https://platform.claude.com/docs/en/api/errors` y `https://platform.claude.com/docs/en/build-with-claude/structured-outputs`):
  - `POST https://api.anthropic.com/v1/messages`; cabeceras `x-api-key`, `anthropic-version: 2026-10-21` y `content-type: application/json`.
  - Salida estructurada en `output_config.format` = `{"type": "json_schema", "schema": …}`; el JSON llega en el bloque de texto de `content`. Esfuerzo en `output_config.effort`.
  - Rechazo: HTTP 200 con `stop_reason: "refusal"` → `ContentBlocked`. `stop_reason: "max_tokens"` puede cortar el JSON → `InvalidOutput`.
  - Errores: forma `{"type":"error","error":{"type":…,"message":…},"request_id":…}`; 529 `overloaded_error`; 500 `api_error`; 504 `timeout_error`. Todo 5xx → `ProviderError` sin reintento (BR2.4).
  - Sin SDK: `httpx` directo (decisión de NFR Requirements).
- **F-12:** el presupuesto de NFR3.5 (`anonymizer_masking_budget_ratio` × `timeout_s`) se mide en `application/generate.py` con `application.generate.now`; el dominio no lee el reloj.
- **F-13:** `FakeTransport.http_error` devuelve `api_error` con cualquier estado. Para la sobrecarga, usa el *fixture* `error_529.json`, no `http_error(529)`.
- **CG-U10-08 (decisión del humano, 2026-11-25):** el candado del paso 10 cubre también `tests/support.py` y `tests/fixtures` (CA-3). El `ROJO_SHA` vigente es `afa8f20`; `32317a9` queda superado.
- **Mypy y `veridicus_contracts`:** sigue el arreglo de `mypy_path` que dejó U10-T02 (K-78); no lo amplíes.
- **Bitácora:** `docs/loop/bitacoras/U10-T04.md`, con el par falla-pasa por paso y, como máximo, una página (ML-7).
