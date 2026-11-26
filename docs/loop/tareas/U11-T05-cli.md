# U11-T05: la CLI `veridicus analyze`, sus fronteras y la prueba de punta a punta

**Unidad:** U11 `incoherence-analyzer`   **Bolt:** B11a   **Rama base:** `bolt/b11a-analyzer` en `3e164bc`, después de fusionar U11-T04
**Pasos del plan que cubre:** los pasos 10, 11 y 12 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md` (revisión 3, aprobada).
**Historias:** US11.3 (la frontera de salida, AC11.3.3 y AC11.3.7 de punta a punta), US3.4 y US3.5, y la demostración esperada de B11.
**Depende de:** U11-T04.
**Riesgo (ML-4):** alto. Abarca el fallo cerrado de la CLI, la frontera del disco y las fronteras de import-linter, y es la demostración del sábado. Por eso la revisión la hace `revisor` con `opus`.

ROJO_SHA: c7e6542c26f14ad6c4b35636bbfc791ff60a5145

---

## Alcance

**Entra:**

> - **Paso 10, la CLI (F9):**
>   - `cli/main.py`, con `argparse` y la costura PD-12: `main()` → `run(argv, env, *, transport=None)`;
>   - `cli/composition.py` (PD-7), un módulo guardia;
>   - `cli/io_atomic.py` y `cli/results_dir.py`, con las reglas BR11.2, BR11.4, BR11.5 y BR11.6 (R-11: `.gitignore` con `resultados-locales/`, prueba con `git check-ignore` y su control negativo);
>   - `cli/messages.py`, un catálogo cerrado en español, con un *canary* que comprueba que stderr no lleva testimonio (BR11.7);
>   - los códigos de salida 0, 2, 3, 4 y 5 (BR11.3);
>   - el aviso VE-01 y el de `same_family`, en stderr y en `AVISO.txt` (BR9.5, PD-2);
>   - sin `reporte.json` en B11a (CG-U11-13).
> - **Paso 11, las fronteras:**
>   - los contratos de import-linter `u11-no-infra`, `gateway-no-anonymizer`, `core-no-anonymizer` (con `cli.composition` como única excepción) y `layers`;
>   - en `tests/boundaries/`, un control negativo por contrato y una prueba AST de que ningún `__init__` reexporta `cli.composition`;
>   - en la lista prohibida de `libs/anonymizer/pyproject.toml`, `veridicus_integrity_policy` (CG-U11-08). Es la **única** excepción a «no tocar `libs/anonymizer/`».
> - **Paso 12, de punta a punta:**
>   - `tests/e2e/test_cli_fake.py`, con el `Anonymizer` real y el `FakeTransport` de B10a, en al menos 4 casos: contradicción sembrada, relato coherente, cita alterada y CLI del paso 3;
>   - `tests/manual/test_real_provider.py`, marcada `manual`. La corre el humano el viernes 27 con el comando de R-04, que va en el README y en la bitácora.
> - **Las pruebas rojas de la CLI del paso 3 pasan a verde sin cambiarlas.** CA-3 de U11-T04 dejó 6 en rojo.
> - **Lo que dejaron pendiente las tareas anteriores:**
>   - **A-04, de la ronda 2 de U11-T04:** el docstring de `build_output` en `domain/output.py` debe citar BR3.1, la huella de los bytes leídos, y no BR8.7. La diferencia entre BR3.1 y BR8.7 se anota en la bitácora como precisión para la tabla de la unidad.
>   - **A-02, de U11-T04:** la CLI traduce `import.invalid_transcript` por un número de turno repetido. Define con qué código de salida y con qué mensaje del catálogo.
>   - **Los límites desde el entorno:** la CLI compone los límites de C25 desde el entorno, con `limits.load(env)`, para que una bajada por `VERIDICUS_LIMIT_*` se aplique. Si hace falta, se los pasa a `analyze` sin cambiar su firma pública (por ejemplo, por la configuración). Si eso exige cambiar `execution_profiles` o `contracts`, para y repórtalo.

**Fuera** (rechazar aunque se vea roto):

- **Las 6 rutas congeladas no se editan:**
  - `libs/incoherence_analyzer/tests/guards`
  - `libs/incoherence_analyzer/tests/contracts`
  - `libs/execution_profiles/tests/contracts`
  - `libs/incoherence_analyzer/tests/support.py`
  - `libs/integrity_policy/tests/guards`
  - `libs/integrity_policy/tests/conftest.py`

  El cambio de la línea 109 que autorizó P-T04-1 ya está hecho. Si una prueba congelada pide algo imposible, para y repórtalo.
- **Pertenecen a T06:** la CI (`analyzer-level0.yml`), el `coverage_gate`, el README completo, `examples/`, el glosario y la versión 0.1.0. Solo escribe en el README la sección mínima del comando manual.
- **Diferido a B11b** (plan, líneas 495 a 504): el modo fragmentado, el alterno, `reporte.json`, BR2.4, BR2.6 a BR2.9 y BR5.8.
- **No se tocan:** `contracts/` ni `.gitleaks.toml`. De `libs/anonymizer/` solo se toca la lista prohibida de su `pyproject.toml`.
- **No se corre `tests/manual` contra el proveedor real:** la corre el humano.

---

## Archivos de contexto

- **El plan aprobado:**
  - los pasos 10, 11 y 12;
  - PD-2, PD-7 y PD-12;
  - R-04, R-08, R-11 y R-13;
  - CG-U11-08 y CG-U11-13;
  - el Testing Contract;
  - las líneas 495 a 504.
- **`functional-design/`:**
  - `rules.md`, BR9.5, BR10.5 y BR11.1 a BR11.7;
  - `functional-spec.md`, F9.
- **`nfr-design/`:** el orden de arranque (RD) y SD §1.
- **Las bitácoras de U11-T01 a U11-T04**, con los supuestos de firma (la composición de `load_config`, `load_prompt_reference`, `build` y `analyze`) y las excepciones que llegan a la CLI.
- **Las pruebas rojas de la CLI**, en `tests/guards` y `tests/contracts`, marcadas `cli`. Ellas fijan la firma de `run`.
- **El `FakeTransport` de B10a**, en `libs/anonymizer/`, y `libs/model_gateway/testing/`.

---

## Criterios de aceptación

Se corren desde la raíz del worktree `/workspace/.worktrees/U11-T05`.

- [ ] **CA-1 (paso 10):** la CLI, con 100 % de ramas en `composition.py`.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/cli tests/guards -m cli --cov=veridicus_incoherence_analyzer.cli.composition --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/cli --cov=veridicus_incoherence_analyzer.cli --cov-report=term-missing --cov-fail-under=90
  ```
  Se espera:
  - código 0 en los dos;
  - al menos 12 pruebas en `tests/cli`, con una por código de salida y una por regla BR11;
  - las pruebas `cli` congeladas pasan sin cambios.
- [ ] **CA-2:** las rutas congeladas solo tienen el cambio de P-T04-1.
  ```bash
  git -C /workspace/.worktrees/U11-T05 diff --stat c7e6542c26f14ad6c4b35636bbfc791ff60a5145 -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts libs/incoherence_analyzer/tests/support.py libs/integrity_policy/tests/guards libs/integrity_policy/tests/conftest.py
  ```
  Se espera: un solo archivo, `test_autonomia_04_composite.py`, con el mismo cambio que en `3e164bc`. Además, `git -C /workspace/.worktrees/U11-T05 diff --exit-code 3e164bc -- <las 6 rutas>` debe salir con código 0.
- [ ] **CA-3:** ya no queda nada en rojo.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=no
  ```
  Se espera: código 0, sin ningún fallo ni `ERROR`.
- [ ] **CA-4 (paso 11):** las fronteras.
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> lint-imports
  ```
  Se corre en los cinco paquetes: `incoherence_analyzer`, `integrity_policy`, `execution_profiles`, `model_gateway` y `anonymizer`.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/boundaries --no-cov -q
  ```
  Se espera:
  - `lint-imports` con código 0 en los cinco;
  - al menos 5 pruebas, y cada control negativo hace fallar `lint-imports` dentro de su prueba.
- [ ] **CA-5 (paso 12):** de punta a punta y la prueba manual.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/e2e --no-cov -q
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/manual -m manual --no-cov --force-enable-socket --collect-only -q
  ```
  Se espera:
  - el primero, con código 0 y al menos 4 pruebas;
  - el segundo recolecta al menos 1 prueba;
  - la corrida por defecto no la ejecuta.
- [ ] **CA-6:** nada retrocede.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/application tests/guards tests/contracts --cov=veridicus_incoherence_analyzer.application --cov=veridicus_incoherence_analyzer.api --cov-branch --cov-fail-under=100 -m "not cli and not manual"
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/domain --cov=veridicus_incoherence_analyzer.domain --cov-branch --cov-fail-under=100
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest
  ```
  Se espera: código 0 en los tres.
- [ ] **CA-7:** tipos, *lint* y formato.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/incoherence_analyzer ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/incoherence_analyzer ruff format --check .
  ```
  Se repiten en `libs/anonymizer` si cambiaste su `pyproject.toml`.
  Se espera: código 0.
- [ ] **CA-8:** las guardias del repositorio.
  ```bash
  bash /workspace/.worktrees/U11-T05/scripts/check-no-datos-personales.sh /workspace/.worktrees/U11-T05
  ```
  ```bash
  bash /workspace/.worktrees/U11-T05/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U11-T05
  ```
  ```bash
  bash /workspace/.worktrees/U11-T05/scripts/check-no-insumos.sh /workspace/.worktrees/U11-T05
  ```
  Se espera:
  - los tres imprimen `0 apariciones`;
  - `grep -rnoP "sk-[A-Za-z0-9_-]{6,}"` sobre `libs/` solo encuentra `sk-sintetico-canario-7f3a91c2d4e5`;
  - `git check-ignore resultados-locales/x.salida.json` sale con código 0.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U11-T05.md`, de una página como máximo. Debe incluir:
  - el comando manual de R-04, tal cual;
  - la tabla de códigos de salida y la situación que produce cada uno;
  - las precisiones A-02, A-04 y la de los límites desde el entorno;
  - lo que T06 debe respetar.
- **La CLI nunca escribe testimonio en stderr ni en los registros.** Con el código 4 escribe solo la salida en error, y con un fallo de composición termina con código 3 y 0 llamadas.
- **Bash:**
  - nada de envolver comandos con `bash -c`, `time`, *pipes* ni redirecciones;
  - el tiempo se toma de la línea final de pytest o de `--durations`.
- **Claves de prueba:** solo `sk-sintetico-canario-7f3a91c2d4e5`. Un *canary* nuevo pone en rojo la CI de `main`.
- **Datos:** solo sintéticos.
- **Red:** ninguna, salvo `uv lock` y `uv sync`.
- **Commits:** en Conventional Commits en español.
- **Plan aprobado:** no lo edites; las casillas las marca el orquestador.
- **Al terminar:** haz push de `tarea/U11-T05` y vuelve con tu informe. No fusionas tú.
