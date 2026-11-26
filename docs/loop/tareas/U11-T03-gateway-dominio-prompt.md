# U11-T03: `ModelGateway`, dominio y *prompt* con esquemas de respuesta

**Unidad:** U11 `incoherence-analyzer`   **Bolt:** B11a   **Rama base:** `bolt/b11a-analyzer`, después de fusionar U11-T02
**Pasos del plan que cubre:** pasos 6, 7 y 8 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md` (revisión 3, aprobada)
**Historias:** US3.4 (verificación de citas), US3.5 (verificador) y US11.3 (frontera de salida, del lado del gateway).
**Depende de:** U11-T02.
**Riesgo (ML-4):** alto: frontera de salida de datos (AUTONOMIA-04), AUTONOMIA-05 y lo que sale al proveedor. → `revisor` con `opus`.

---

## Alcance

**Dentro:**

> - **Paso 6, `libs/model_gateway`:**
>   - `port.py`.
>   - `gateway.py::build(config, anonymizing_provider=None)`:
>     - si un papel es externo, exige el proveedor y el piso de 270 s, que se importa de `veridicus_execution_profiles.floors`;
>     - si un papel es local, lanza `GatewayConfigError` («adaptador local diferido a B11b»);
>     - registra cada `ModelCall` en orden y mide la latencia en memoria, fuera de C6.
>   - `adapters/anonymizing.py`:
>     - no reintenta;
>     - deja pasar tal cual los errores de `model_calls`;
>     - cualquier otra excepción la traduce a `AnonymizerUnavailable`, con una causa sin testimonio.
>   - Un *fake* determinista del gateway en `testing/`.
> - **Paso 7, `domain/` de `incoherence_analyzer`:**
>   - `quotes.py::verify_quote`, con la regla del piloto;
>   - `filter.py`, en el orden de BR5.2 y con la deduplicación de BR4.3;
>   - `run_state.py`, con la precedencia de `incidente_anonimizacion`;
>   - `output.py` e `ids.py`, según BR8.2, BR8.3 y BR8.5 a BR8.7;
>   - `tests/domain/test_quotes_perf.py`: 20 000 caracteres en 150 ms o menos.
> - **Paso 8:**
>   - `data/prompt.v1.md` y `data/prompt.v1.sha256` (PD-13);
>   - los cuatro esquemas de `data/schemas/`: dos locales cerrados y dos de cable sin palabras clave que Anthropic no admite (PD-11);
>   - `load_response_schema(role, kind)` y la lectura del *prompt* con `importlib.resources`;
>   - `application/messages.py::build_messages` (PD-6);
>   - `tests/application/test_messages.py`, con la propiedad Hypothesis del umbral;
>   - `tests/application/test_prompt_through_anonymizer.py` (R-14);
>   - la prueba de que el texto del *prompt* no lleva vocabulario de C8, hecha con el `scan` real de `integrity_policy`.
> - **El rojo que estos pasos deben poner en verde, sin cambiar las pruebas:**
>   - `tests/contracts/test_response_schemas.py`;
>   - lo que `analyze` no necesite en `tests/guards`.
>
>   El resto del rojo sigue esperando a `analyze` (T04) y a la CLI (T05).

**Fuera** (rechazar aunque se vea roto):

- **Las 6 rutas congeladas del rojo** (`ROJO_SHA: c7e6542c26f14ad6c4b35636bbfc791ff60a5145`) no se editan:
  - `libs/incoherence_analyzer/tests/guards`
  - `libs/incoherence_analyzer/tests/contracts`
  - `libs/execution_profiles/tests/contracts`
  - `libs/incoherence_analyzer/tests/support.py`
  - `libs/integrity_policy/tests/guards`
  - `libs/integrity_policy/tests/conftest.py`

  Si una prueba congelada pide algo imposible o contradictorio, para y repórtalo.
- **Pertenecen a T04 y T05:** `analyze`, `preflight`, `deadline`, `api.py` y la CLI.
- **K-88** (pasar la huella del *prompt* real a `load_config`) se resuelve en T04 y T05. Aquí basta con exponer una función pública que devuelva la referencia de `data/prompt.v1.sha256`.
- **No se tocan:** `contracts/` y `libs/anonymizer/`. Lo que encuentres ahí va a candidatas.

---

## Archivos de contexto

- **Plan aprobado:**
  - pasos 6 a 8;
  - PD-6, PD-11 y PD-13;
  - CG-U11-12;
  - R-05, R-09 y R-14;
  - Testing Contract.
- **Diseño funcional de la unidad**, en `functional-design/`:
  - `rules.md`: BR3, BR4.3, BR5, BR7, BR8 y BR10;
  - `functional-spec.md`: el contenido y la estructura del *prompt* y de las respuestas del juez y del verificador.
- **Diseño no funcional:** `nfr-design/security-design.md`.
- **Bitácoras:** las de U11-T01 y U11-T02, en `/workspace/.worktrees/U11-T03/docs/loop/bitacoras/`. Traen los supuestos de firmas:
  - `verify_quote(texto_turno, cita)` devuelve `verified` o `not_found`;
  - `load_response_schema(papel, wire|local)`;
  - `load_system_prompt(papel)`;
  - `build_finding(finding_id, candidate, turns)`;
  - el `turno` del juez es `T<n>`;
  - un campo ausente o nulo da `salida_invalida`, y `campo_faltante` aplica solo cuando el campo trae únicamente espacios.
- **`contracts/src/veridicus_contracts/`:**
  - `model_calls.py` (C13: `GenerateRequest`, `GenerateResult`, `ModelCall` y los errores);
  - `analyzer/v1.py` (C6).
- **`libs/anonymizer/`:**
  - `api.py`;
  - `testing/fake_transport.py`;
  - el adaptador de Anthropic, para saber qué palabras clave de esquema admite el cable.
- **Documentación oficial por MCP:** las salidas estructuradas de Anthropic, para comprobar qué palabras clave de JSON Schema se admiten. Solo con términos genéricos.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U11-T03`.

- [ ] **CA-1 (paso 6):** gateway con 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/model_gateway pytest --cov=veridicus_model_gateway --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera:
  - código 0;
  - al menos 8 pruebas;
  - 100 % de ramas en `gateway.py` y `adapters/anonymizing.py`.

  Pares obligatorios:
  - papel externo sin proveedor → `GatewayConfigError`;
  - 269 s → falla, y 270 s → arranca;
  - papel local → `GatewayConfigError`;
  - `RuntimeError` del proveedor → `AnonymizerUnavailable`, sin testimonio en el mensaje;
  - un error de `model_calls` pasa tal cual;
  - una llamada no se reintenta: el proveedor se llama exactamente 1 vez.
- [ ] **CA-2 (paso 7):** dominio con 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/domain --cov=veridicus_incoherence_analyzer.domain --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera:
  - código 0;
  - al menos 20 pruebas;
  - 100 % de ramas en `domain/`;
  - la prueba de rendimiento, en 150 ms o menos.
- [ ] **CA-3 (paso 8):** mensajes, *prompt* y esquemas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/application/test_messages.py tests/application/test_prompt_through_anonymizer.py tests/contracts/test_response_schemas.py --cov=veridicus_incoherence_analyzer.application.messages --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera:
  - código 0;
  - al menos 8 pruebas;
  - la propiedad Hypothesis;
  - 100 % de ramas;
  - `test_response_schemas.py`, congelado, pasa sin cambios.
- [ ] **CA-4:** las rutas congeladas no cambiaron.
  ```bash
  git -C /workspace/.worktrees/U11-T03 diff --exit-code c7e6542c26f14ad6c4b35636bbfc791ff60a5145 -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts libs/incoherence_analyzer/tests/support.py libs/integrity_policy/tests/guards libs/integrity_policy/tests/conftest.py
  ```
  Se espera: código 0.
- [ ] **CA-5:** el rojo que queda falla solo por `NotImplementedError`.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=no --rojo
  ```
  Se espera:
  - 0 `ERROR`;
  - los únicos fallos, por `NotImplementedError` de `analyze` o de `run`.

  Anota en la bitácora cuántas pruebas pasaron y cuántas siguen rojas.
- [ ] **CA-6:** tipos, *lint* y formato.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> ruff format --check .
  ```
  Se corren en `model_gateway` y en `incoherence_analyzer`, con `--extra cli` en este último.
  Se espera: código 0.
- [ ] **CA-7:** guardias del repositorio.
  ```bash
  bash /workspace/.worktrees/U11-T03/scripts/check-no-datos-personales.sh /workspace/.worktrees/U11-T03
  ```
  ```bash
  bash /workspace/.worktrees/U11-T03/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U11-T03
  ```
  ```bash
  bash /workspace/.worktrees/U11-T03/scripts/check-no-insumos.sh /workspace/.worktrees/U11-T03
  ```
  Se espera: los tres scripts imprimen `0 apariciones`.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U11-T03.md`, de una página como máximo. Anota cada supuesto de firma que T04 y T05 deban respetar. Por ejemplo, cómo se obtiene la referencia del *prompt* para resolver K-88.
- **El *prompt*:**
  - no lleva testimonio, nombres ni vocabulario de C8;
  - sigue lo que fija el diseño funcional, sin inventar categorías;
  - va en español si el diseño no dice otra cosa.
- **Datos:** solo sintéticos, con claves *canary*.
- **Red:** ninguna, salvo `uv lock` y `uv sync`.
- **Commits:** en Conventional Commits en español.
- **Al terminar:** haz push de `tarea/U11-T03` y vuelve con tu informe. No fusionas tú.
