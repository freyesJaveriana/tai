# U11-T01: los cuatro paquetes de U11, el ejecutor de pruebas y el rojo de las guardias

**Unidad:** U11 `incoherence-analyzer`   **Bolt:** B11a   **Rama base:** `bolt/b11a-analyzer`
**Pasos del plan que cubre:** pasos 1 a 3 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md` (revisión 3, aprobada con `Approve Plan` el 2026-11-26)
**Historias que implementa:** US11.3 (AC11.3.3, AC11.3.7 y AC11.3.8, del lado de U11) y US3.4/US3.5 (verificación de citas y verificador). En esta tarea todo queda **en rojo**.
**Depende de:** ninguna.
**Riesgo (ML-4):** alto (guardias AUTONOMIA-03, 04 y 05) → `revisor` con `opus`. Antes de fijar el rojo hay una revisión corta con `sonnet` (ML-13).

---

## Alcance

**Dentro:**

> - Paso 1: los paquetes `libs/incoherence_analyzer/`, `libs/model_gateway/`, `libs/execution_profiles/` y `libs/integrity_policy/`, con *src layout*.
>   - Cada `pyproject.toml` se copia de `libs/anonymizer/pyproject.toml` (R-12), y su `uv.lock` se crea con `uv lock`.
>   - Los *stubs* de cada símbolo público lanzan `NotImplementedError`.
>   - Se agregan los errores nuevos de `libs/errors` (PD-5), implementados y con sus pruebas.
> - Paso 2: el ejecutor de pruebas sin red, con los marcadores `manual` y `cli`, y el `conftest` con la opción `--rojo` y su control negativo (N-03).
> - Paso 3: las pruebas en rojo de AUTONOMIA-03/04/05, K-84 y los contratos de datos, en **un commit propio**.

**Fuera** (rechazar aunque se vea roto):

- Toda implementación de perfiles, escáner, gateway, dominio, aplicación o CLI: son los pasos 4 a 12 (U11-T02 a U11-T05). Los *stubs* solo lanzan `NotImplementedError`.
- `config/profiles.yaml`, `data/prompt.v1.md`, `data/prompt.v1.sha256` y los esquemas de `data/schemas/`: los escriben T02 y T03. Las pruebas rojas **no leen archivos directamente**; todo pasa por los *stubs* `load_profiles`, `validate_profile` y `load_response_schema` (R-07).
- `contracts/` y `libs/anonymizer/`: no se tocan. La lista prohibida de U10 (CG-U11-08) es del paso 11.
- CI, README y glosario: son de U11-T06.

---

## Archivos de contexto

- El plan aprobado (ruta arriba): PD-1 a PD-13, pasos 1 a 3 y Testing Contract.
- `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/unit-test-instructions.md`
- En `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/`:
  - `functional-design/functional-spec.md`;
  - `functional-design/rules.md`: BR1, BR2.5, BR2.10, BR3, BR5, BR7, BR8.1, BR9 y BR10.1;
  - `functional-design/entities.md`;
  - `nfr-design/security-design.md`: §1, §2, §4 y §5.
- `contracts/src/veridicus_contracts/`:
  - `model_calls.py` (C13);
  - `profiles.py`: `validate(..., key_prefix="VERIDICUS_", kind="analyzer")`;
  - `analyzer/v1.py`;
  - `validators.py`: `validate_instance`;
  - `registry.py`: `build_registry`;
  - `limits.py`.
- `contracts/profiles/profiles.schema.v1.yaml` y `profile-base.schema.v1`.
- `libs/anonymizer/`:
  - `pyproject.toml`, como base de cada paquete;
  - `src/veridicus_anonymizer/api.py`: `build_anonymizer(env, transport)`;
  - `testing/fake_transport.py` y `testing/bypass.py`;
  - `tests/conftest.py`;
  - `tests/guards/`, como modelo de pruebas rojas.
- `libs/errors/`.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U11-T01`. `<P>` vale `incoherence_analyzer`, `model_gateway`, `execution_profiles` e `integrity_policy`; cada comando con `<P>` se corre una vez por paquete.

- [ ] **CA-1 (paso 1):** cada paquete tiene su lock, se instala y sus *stubs* tipan.
  ```bash
  timeout 600 uv lock --directory libs/<P>
  ```
  ```bash
  timeout 600 uv sync --frozen --directory libs/<P>
  ```
  En `incoherence_analyzer`, el `sync` se corre con `--extra cli`.
  ```bash
  timeout 120 uv lock --check --directory libs/<P>
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src
  ```
  Esperado: todos terminan con 0.

- [ ] **CA-2 (paso 1, errores):** los cuatro errores nuevos tienen su `code` estable y su `detail` en español.
  ```bash
  timeout 60 uv run --frozen --offline --directory libs/errors pytest
  ```
  Esperado: código 0, con al menos 4 pruebas nuevas, una por clase.

- [ ] **CA-3 (paso 2):** el ejecutor está listo y bloquea la red.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/<P> pytest tests/test_package.py -q
  ```
  Esperado: código 0 y al menos 2 pruebas por paquete, una de ellas con `pytest-socket` bloqueando una conexión.
  Lectura de vuelta: `grep -n "addopts" libs/<P>/pyproject.toml` muestra `--disable-socket`, `-m 'not manual'` y **ningún** `--cov`. Los marcadores `manual` y `cli` están declarados.

- [ ] **CA-4 (paso 2, `--rojo`):** el *hook* convierte en `ERROR` un fallo por una causa distinta de `NotImplementedError`.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/test_conftest_rojo.py -q
  ```
  Esperado: código 0. La prueba usa `pytester` o un equivalente y tiene control negativo: un `AssertionError` sale como `ERROR` y un `NotImplementedError`, como `FAILED`. El mismo *hook* está en `libs/execution_profiles/tests/conftest.py`.

- [ ] **CA-5 (paso 3, recolección):** las pruebas del rojo se recolectan sin errores.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts --collect-only -q
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/execution_profiles pytest tests/contracts --collect-only -q
  ```
  Esperado: código 0 en los dos, con 0 errores de recolección y al menos 35 pruebas entre ambos.

- [ ] **CA-6 (paso 3, rojo):** todas fallan por `NotImplementedError` y ninguna da error.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=line --rojo
  ```
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/execution_profiles pytest tests/contracts -p no:cacheprovider -rfE --tb=line --rojo
  ```
  Esperado: los dos terminan con código 1, el 100 % en `FAILED` y 0 en `ERROR`.

- [ ] **CA-7 (paso 3, commit):** el rojo está en un commit propio.
  Lectura de vuelta: `git -C /workspace/.worktrees/U11-T01 log --oneline -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts` muestra **un solo** commit, `test(analyzer): pruebas en rojo de AUTONOMIA-03/04/05 y contratos de datos`. La bitácora lleva una línea `ROJO_SHA: <sha de 40 caracteres>`.

- [ ] **CA-8:** tipos, *lint* y formato de todo lo que entrega la tarea.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> ruff format --check .
  ```
  Esperado: todos terminan con 0.

- [ ] **CA-9:** el anonimizador de B10a sigue en verde.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-fail-under=80
  ```
  Esperado: código 0.

- [ ] **CA-10:** las guardias del repositorio público siguen limpias con los *fixtures* nuevos.
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

1. Primero van los pasos 1 y 2: *stubs*, errores nuevos, ejecutor y `conftest --rojo`. Cada uno va en sus propios commits.
2. Después viene el **paso 3, en rojo**. Los archivos y el contenido de cada uno están en el paso 3 del plan:
   - `tests/guards/`:
     - `test_autonomia_05_quotes.py`;
     - `test_autonomia_05_error.py`;
     - `test_autonomia_03_vocabulary.py`;
     - `test_autonomia_04_composite.py`, con las variantes (a) a (d) de BR7.4, la (e) como CLI 3 sin salida C6 y el control negativo `bypass`;
     - `test_k84_system_fixed.py`;
   - `tests/contracts/test_c6_output.py` y `tests/contracts/test_response_schemas.py`;
   - `libs/execution_profiles/tests/contracts/test_profile_contract.py`.
3. **ALTO ANTES DEL COMMIT DEL ROJO (ML-13).** Con CA-5 y CA-6 cumplidos, **no hagas** el commit del rojo. Deja las pruebas sin preparar para el commit, escribe la bitácora hasta ese punto y vuelve con tu informe. El orquestador despacha una revisión corta de esas pruebas. Luego te vuelve a despachar con sus hallazgos para corregirlos, hacer el commit del rojo y cerrar CA-7 a CA-10.
4. Las pruebas del paso 3 **no se tocan** después de su commit. El paso 9 (U11-T04) lo comprueba con `git diff --exit-code <ROJO_SHA>`.

**Pruebas marcadas `cli`.** Llevan `@pytest.mark.cli` las pruebas del paso 3 que pasan por `cli.main.run`:
- el aviso VE-01 y el aviso `same_family`;
- «sin aviso → CLI 3»;
- «perfil externo sin `Anonymizer` → CLI 3»;
- la variante (e);
- `incidente_anonimizacion` → CLI 4.

---

## Reglas de la app que aplican

- **AUTONOMIA-05.** Un hallazgo sin uno de sus campos obligatorios se rechaza. Una cita alterada o de otro turno no sale. `error` implica hallazgos vacíos. La cita restaurada se verifica antes de salir.
- **AUTONOMIA-03.** El escáner de vocabulario prohibido excluye las citas literales. El esquema de salida no tiene campos de veracidad. El aviso VE-01 es visible.
- **AUTONOMIA-04.** Un destino externo sin anonimizador no arranca. La prueba del payload compuesto tiene su control negativo `bypass`. El fallo es cerrado, sin reintento.
- **AUTONOMIA-02.** Cada criterio tiene su comando.
- **Solo datos sintéticos.** Nada del piloto, de `/insumos` ni de la partición `referencia`. La clave de API es un *canary* inventado.

---

## Notas

- **Perfil `demo-anthropic`:** juez y verificador con `scope: external`, `provider: anthropic`, `model: claude-sonnet-5-5`, `family: claude` y `api_key_ref: VERIDICUS_ANTHROPIC_API_KEY`; además `role_aliases: {verifier_permuted: verifier}`, `permutation: true`, `purpose: demonstration` y `same_family_declared: true`. En esta tarea solo hace falta para los *fixtures* de prueba, que lo pasan a los *stubs*.
- **Red:** `uv lock` y `uv sync` son las únicas llamadas con red. Todo lo demás corre con `--frozen --offline`.
- **Bitácora:** `docs/loop/bitacoras/U11-T01.md`, de una página como máximo (ML-7). Lleva el par falla-pasa de cada criterio y la línea `ROJO_SHA:`.
