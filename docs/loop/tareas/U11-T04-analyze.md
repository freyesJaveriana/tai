# U11-T04: `analyze`, con validación previa, juez, verificador y permutación

**Unidad:** U11 `incoherence-analyzer`   **Bolt:** B11a   **Rama base:** `bolt/b11a-analyzer`, después de fusionar U11-T03
**Pasos del plan que cubre:** el paso 9 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md` (revisión 3, aprobada), que corresponde a F1 a F7.
**Historias:** US3.4 (verificación de citas), US3.5 (verificador) y US11.3 (frontera de salida). También cubre AC11.3.8.
**Depende de:** U11-T03.
**Riesgo (ML-4):** alto, porque cubre AUTONOMIA-05 de punta a punta, la salida en error sin resultados parciales (BR7) y el escáner de AUTONOMIA-03 sobre la salida. Por eso la revisión la hace `revisor` con `opus`.

ROJO_SHA: c7e6542c26f14ad6c4b35636bbfc791ff60a5145

---

## Alcance

**Entra:**

> - **Paso 9 del plan:**
>   - `application/preflight.py` (BR1.1 a BR1.4);
>   - `application/deadline.py` (BR7.2, PD-10);
>   - `application/analyze.py` (BR3.2, BR6.1 a BR6.4);
>   - `api.py`: la función `analyze(entrada, config, gateway, cancelled=None) -> Salida` y la clase `IncoherenceAnalyzer`, que cumple el `Protocol` de C17 (CG-U11-03, R-15);
>   - `tests/application/test_run_perf.py`: 2 000 turnos en 6 s o menos con el *fake* (R-09).
> - **Las pruebas rojas del paso 3 pasan a verde sin cambiarlas**, incluida `test_k84_system_fixed.py` (N-02). Solo quedan en rojo las de la CLI, que se resuelven en T05.
> - **Lo que dejaron pendiente las tareas anteriores:**
>   - **F-03 de U11-T03:** una prueba en la que cambiar un byte del *prompt*, en memoria, da `salida_invalida` sin llamar al modelo (BR3.1 y la línea 329 del plan).
>   - **K-88:** `analyze`, o quien lo componga, compara `config.prompt_sha256` con `load_prompt_reference()` de `application/messages.py`. Una prueba comprueba que el valor por defecto de `load_config`, 64 ceros, falla cerrado: `salida_invalida` y ninguna llamada.
>   - **F-06 de U11-T01:** en un archivo de pruebas no congelado, un caso con «era falso» escrito literalmente en un turno **no citado** (por ejemplo, T3). Debe salir sin descartes, porque el escáner recibe como `literal_sources` los textos de **todos** los turnos (BR9.3).
>   - **K-91 (F-12 de U11-T02):** en `integrity_policy/scan.py`, extender el final del tramo sobre las marcas descartadas que siguen a la última letra. `engañó` en NFD debe informarse como `engañó`, con su tramo completo. Agrega la prueba y conserva el 100 % de ramas de `scan.py`.
>   - **F-05 de U11-T03 (AMARILLO):** en `tests/domain/test_quotes.py`, alrededor de la línea 102, y en otros puntos del archivo, cambia los literales invisibles por escapes `\uXXXX` o por `chr(0x…)`. Esto incluye el U+2028, que corta las líneas al leerlas. Corrige también la frase de `docs/loop/bitacoras/U11-T03.md` según la cual `ruff format` los reescribía: el revisor comprobó que no lo hace.
>   - **Candidata de la ronda 1 de U11-T03:** una prueba compuesta en la que un `GenerateRequest` con un `destination` distinto del del perfil no sale. Si el `Anonymizer` lo rechaza, la prueba lo demuestra a través de `analyze`.

**Fuera** (rechazar aunque se vea roto):

- **Las 6 rutas congeladas** (`ROJO_SHA` arriba) no se editan:
  - `libs/incoherence_analyzer/tests/guards`
  - `libs/incoherence_analyzer/tests/contracts`
  - `libs/execution_profiles/tests/contracts`
  - `libs/incoherence_analyzer/tests/support.py`
  - `libs/integrity_policy/tests/guards`
  - `libs/integrity_policy/tests/conftest.py`

  Si una prueba congelada pide algo imposible o contradictorio, para y repórtalo.
- **Pertenecen a T05:** la CLI, `cli/` e import-linter.
- **Diferido a B11b:**
  - el modo fragmentado y BR5.8 `fuera_de_tramo` (plan, línea 495);
  - el alterno, BR7.3 (plan, línea 504);
  - BR2.4 y BR2.6 a BR2.9 (plan, línea 497).
- **No se tocan:** `contracts/`, `libs/anonymizer/` ni `.gitleaks.toml`. Lo que encuentres ahí va a candidatas.

---

## Archivos de contexto

- **Plan aprobado:**
  - el paso 9;
  - PD-10;
  - R-09 y R-15;
  - CG-U11-03;
  - el Testing Contract;
  - las líneas 495 a 504, con lo diferido.
- **`functional-design/`:**
  - `rules.md`: BR1, BR3, BR5, BR6, BR7, BR8 y BR9.3;
  - `functional-spec.md`: los flujos F1 a F7.
- **`nfr-design/`** de la unidad: los plazos, la cancelación y las métricas en memoria (NFRD-U11-07).
- **Bitácoras de U11-T01, U11-T02 y U11-T03**, con los supuestos de firma:
  - `load_config(nombre, env, path=None, *, prompt_sha256=...)` devuelve `.warnings`, y `warnings` no entra en C18;
  - `load_prompt_reference()` devuelve la referencia del *prompt*;
  - `verify_quote`, `filter_candidates`, `run_state.fail` y `output`;
  - el *fake* de `libs/model_gateway/testing/`.
- **`contracts/src/veridicus_contracts/`:**
  - `analyzer/v1.py` (C6);
  - `model_calls.py` (C13);
  - el `Protocol` de C17.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U11-T04`.

- [ ] **CA-1 (paso 9):** aplicación y API, con 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/application tests/guards tests/contracts --cov=veridicus_incoherence_analyzer.application --cov=veridicus_incoherence_analyzer.api --cov-branch --cov-fail-under=100 --cov-report=term-missing -m "not cli and not manual"
  ```
  Se espera:
  - código 0;
  - 100 % de ramas en `application/preflight.py`, `application/analyze.py`, `application/deadline.py` y `api.py`;
  - `test_run_perf.py` en 6 s o menos.
- [ ] **CA-2:** las rutas congeladas no cambiaron.
  ```bash
  git -C /workspace/.worktrees/U11-T04 diff --exit-code c7e6542c26f14ad6c4b35636bbfc791ff60a5145 -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts libs/incoherence_analyzer/tests/support.py libs/integrity_policy/tests/guards libs/integrity_policy/tests/conftest.py
  ```
  Se espera: código 0 (con P-T04-1, solo el cambio de la línea 109). Salida de `git diff c7e6542… -- <las 6 rutas>` tras el cambio:
  ```diff
  --- a/libs/incoherence_analyzer/tests/guards/test_autonomia_04_composite.py
  +++ b/libs/incoherence_analyzer/tests/guards/test_autonomia_04_composite.py
  @@ -106,7 +106,9 @@ def test_no_seeded_entity_leaves_in_the_bodies_of_judge_verifier_and_permuted_ve
       assert_no_entity_in_payload(provider, ENTITIES)
  -    assert any(b"[PERSONA_" in raw for raw in provider.bodies), "los cuerpos llevan marcas"
  +    assert any(b"[PERSONA_" in raw or b"[ENTIDAD_" in raw for raw in provider.bodies), (
  +        "los cuerpos llevan marcas"
  +    )
  ```
- [ ] **CA-3:** el rojo que queda es solo el de la CLI.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=no --rojo
  ```
  Se espera:
  - 0 `ERROR`;
  - los únicos fallos, por `NotImplementedError` de `run`, de la CLI.

  Anota en la bitácora cuántas pruebas pasan y cuántas quedan.
- [ ] **CA-4 (K-91):** el escáner sigue con 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/integrity_policy pytest --cov=veridicus_integrity_policy.scan --cov=veridicus_integrity_policy.notice --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera: código 0.
- [ ] **CA-5:** el dominio y el gateway no retroceden.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/domain --cov=veridicus_incoherence_analyzer.domain --cov-branch --cov-fail-under=100
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/model_gateway pytest --cov=veridicus_model_gateway --cov-branch --cov-fail-under=100
  ```
  Se espera: código 0 en los dos.
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
  Se corren en `incoherence_analyzer` (con `--extra cli`) y en `integrity_policy`.
  Se espera: código 0.
- [ ] **CA-7:** guardias del repositorio.
  ```bash
  bash /workspace/.worktrees/U11-T04/scripts/check-no-datos-personales.sh /workspace/.worktrees/U11-T04
  ```
  ```bash
  bash /workspace/.worktrees/U11-T04/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U11-T04
  ```
  ```bash
  bash /workspace/.worktrees/U11-T04/scripts/check-no-insumos.sh /workspace/.worktrees/U11-T04
  ```
  Se espera: los tres imprimen `0 apariciones`. Además, `grep -rnoP "sk-[A-Za-z0-9_-]{6,}"` sobre `libs/` solo encuentra `sk-sintetico-canario-7f3a91c2d4e5`.

---

## Decisión del humano (2026-11-26, ronda 1)

- **P-T04-1:** se autoriza cambiar **solo** la línea 109 de `libs/incoherence_analyzer/tests/guards/test_autonomia_04_composite.py`, que está congelada. Ahora debe aceptar `[PERSONA_` o `[ENTIDAD_` en los cuerpos que salen.
  - **Motivo:** B10a marca como `[ENTIDAD_n]` los nombres sembrados que no llevan tratamiento.
  - **Lo que no cambia:** la guardia de fuga de la línea 108 y la prueba de control negativo se quedan como están.
  - **El cambio en CA-2:** el `git diff` contra `ROJO_SHA` solo puede mostrar ese cambio de esa línea. Ninguna otra ruta congelada puede cambiar.
  - **Fuera de esta tarea:** que el anonimizador marque como `[PERSONA_n]` los nombres sin tratamiento queda como candidata de U10, para después de la demo.

## Notas

- **Bitácora:** `docs/loop/bitacoras/U11-T04.md`, de una página como máximo. Anota cada supuesto de firma que T05 deba respetar. Por ejemplo:
  - cómo compone la CLI `load_config`, `load_prompt_reference`, `build` y `analyze`;
  - qué excepciones llegan hasta la CLI y con qué código.
- **`analyze` nunca lanza una excepción por un fallo del modelo.** Una salida en error lleva hallazgos vacíos y ningún resultado parcial (AUTONOMIA-05, BR7).
- **Claves de prueba:** solo `sk-sintetico-canario-7f3a91c2d4e5`. Un *canary* nuevo pone en rojo la CI de `main`.
- **Datos:** solo sintéticos.
- **Red:** ninguna, salvo `uv lock` y `uv sync`.
- **Commits:** en Conventional Commits en español.
- **Al terminar:** haz push de `tarea/U11-T04` y vuelve con tu informe. No fusionas tú.
