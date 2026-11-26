# U11-T02: perfiles de ejecución, configuración y escáner de vocabulario

**Unidad:** U11 `incoherence-analyzer` · **Bolt:** B11a · **Rama base:** `bolt/b11a-analyzer` (incluye U11-T01, merge del 2026-11-26)
**Pasos del plan que cubre:** pasos 4 y 5 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md` (revisión 3, aprobada)
**Historias:** US11.3 (validación del perfil y arranque rechazado, del lado de la configuración) y la parte de AUTONOMIA-03 que vive en `integrity_policy`.
**Depende de:** U11-T01 (fusionada).
**Riesgo (ML-4):** alto. Esta configuración decide si salen datos, y el escáner es AUTONOMIA-03 → `revisor` con `opus`.

---

## Alcance

**Dentro:**

> - **Paso 4, `libs/execution_profiles`:** `loader.py`, `validate.py`, `floors.py` (la constante ya existe; se revisa, no se duplica), `config/profiles.yaml` con el único perfil `demo-anthropic` (CG-U11-12) y la prueba de que ese perfil valida con `profiles.validate(..., kind="analyzer")` real.
>   - **Antes de escribir el perfil,** lee `contracts/profiles/profile-base.schema.v1*` y anota en la bitácora los nombres exactos de los campos de cada papel.
>   - El perfil lleva solo campos de `profiles.schema.v1.yaml` y de `profile-base`.
> - **Paso 5, `libs/integrity_policy`:**
>   - `scan.py`: `scan(text, literal_sources)` con la lista de C8, que excluye las citas literales y la cadena completa del aviso;
>   - `notice.py`: lee `notice.v1.yaml` y devuelve el texto y la versión;
>   - `tests/test_scan_cases.py`: todos los casos `rule: vocabulary` de `scan-cases.v1.yaml`, el conjunto de valores de `rule` fijado y el control negativo.
> - **El rojo pasa a verde, sin cambiar las pruebas:**
>   - `libs/execution_profiles/tests/contracts`, que es el contrato de perfiles del paso 3;
>   - `libs/integrity_policy/tests/guards`.

**Fuera** (rechazar aunque se vea roto):

- **Las 6 rutas congeladas del rojo** (`ROJO_SHA: c7e6542c26f14ad6c4b35636bbfc791ff60a5145`) **no se editan**. Son:
  1. `libs/incoherence_analyzer/tests/guards`
  2. `libs/incoherence_analyzer/tests/contracts`
  3. `libs/execution_profiles/tests/contracts`
  4. `libs/incoherence_analyzer/tests/support.py`
  5. `libs/integrity_policy/tests/guards`
  6. `libs/integrity_policy/tests/conftest.py`

  Si una prueba congelada parece pedir algo imposible o contradictorio, **para y repórtalo**.
- **Gateway, dominio, *prompt*, esquemas, `analyze` y CLI:** son de U11-T03 a U11-T05, y sus *stubs* siguen lanzando `NotImplementedError`.
- **`contracts/` y `libs/anonymizer/`:** no se tocan. Si encuentras un defecto en `contracts`, va a CANDIDATAS (ya está K-86: `cita_a.texto` en C8).
- **Cómo carga `semantic-agent` la configuración sin la clave** (K-87): se decide en U4. Aquí BR2.2 se cumple tal como lo dice el plan (la variable de `api_key_ref` debe existir en el entorno; si falta, error de configuración que nombra la variable).

---

## Archivos de contexto

- **Plan aprobado:** pasos 4 y 5, PD-1 a PD-13, CG-U11-12 y el Testing Contract.
- **`unit-test-instructions.md`**, junto al plan.
- **Diseño funcional:** `functional-design/rules.md` (BR2.1, BR2.2, BR2.3, BR2.5, BR2.10, BR2.11 y BR9.1 a BR9.5) y `nfr-design/` (NFRD-U11-03), bajo `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/`.
- **Bitácora de U11-T01:** `/workspace/docs/loop/bitacoras/U11-T01.md`, en la rama base. Trae los supuestos de firmas que T02 debe respetar, como `load_profiles(path=None)`, `validate_profile(documento, nombre, env)` y `load_config(nombre, env, path=None)`.
- **En `contracts/`:**
  - `src/veridicus_contracts/profiles.py`, `limits.py` y `canonical.py`;
  - `profiles/profiles.schema.v1.yaml` y `profile-base.schema.v1*`;
  - `effective-config.v1.yaml`;
  - `integrity/forbidden-vocabulary.v2.yaml` (C8), `integrity/notice.v1.yaml` e `integrity/scan-cases.v1.yaml`.
- **Pruebas congeladas que deben pasar a verde:**
  - `libs/execution_profiles/tests/contracts/test_profile_contract.py`;
  - `libs/integrity_policy/tests/guards/test_autonomia_03_scan.py`.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U11-T02`.

- [ ] **CA-1 (paso 4):** perfiles, con 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/execution_profiles pytest --cov=veridicus_execution_profiles.validate --cov=veridicus_execution_profiles.floors --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera:
  - código 0;
  - al menos 10 pruebas;
  - 100 % de ramas en `validate.py` y `floors.py`;
  - `tests/contracts/test_profile_contract.py` pasa sin cambios.

  Deben estar cubiertos estos pares:
  - 269 falla y 270 arranca, con un papel externo;
  - sin la variable de la clave, el error nombra la variable;
  - `base_url` privada con destino externo se rechaza;
  - misma familia sin `purpose: demonstration` se rechaza;
  - la configuración es inmutable.
- [ ] **CA-2 (paso 5):** escáner y aviso, con 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/integrity_policy pytest --cov=veridicus_integrity_policy.scan --cov=veridicus_integrity_policy.notice --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera:
  - código 0;
  - al menos 8 pruebas, más todos los casos de `scan-cases.v1.yaml`;
  - un caso positivo y uno negativo por cada término de la lista;
  - `tests/guards/` pasa sin cambios.
- [ ] **CA-3:** las rutas congeladas no cambiaron.
  ```bash
  git -C /workspace/.worktrees/U11-T02 diff --exit-code c7e6542c26f14ad6c4b35636bbfc791ff60a5145 -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts libs/incoherence_analyzer/tests/support.py libs/integrity_policy/tests/guards libs/integrity_policy/tests/conftest.py
  ```
  Se espera: código 0.
- [ ] **CA-4:** el rojo que queda sigue rojo por la razón correcta.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=line --rojo
  ```
  Se espera: 0 `ERROR`. Las pruebas que todavía fallan lo hacen solo por `NotImplementedError` de los *stubs* de T03 a T05. Anota en la bitácora cuántas pasaron ya a verde.
- [ ] **CA-5:** tipos, *lint* y formato en `execution_profiles` e `integrity_policy`.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/<P> ruff format --check .
  ```
  Se espera: código 0 en los dos paquetes.
- [ ] **CA-6:** guardias del repositorio.
  ```bash
  bash /workspace/.worktrees/U11-T02/scripts/check-no-datos-personales.sh /workspace/.worktrees/U11-T02
  ```
  ```bash
  bash /workspace/.worktrees/U11-T02/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U11-T02
  ```
  ```bash
  bash /workspace/.worktrees/U11-T02/scripts/check-no-insumos.sh /workspace/.worktrees/U11-T02
  ```
  Se espera: los tres imprimen `0 apariciones`.
- [ ] **CA-7:** el perfil no lleva valores de clave.
  ```bash
  grep -rnP "sk-|api_key\s*:" /workspace/.worktrees/U11-T02/libs/execution_profiles/config
  ```
  Se espera: ninguna coincidencia. Solo puede aparecer `api_key_ref: VERIDICUS_ANTHROPIC_API_KEY`.

---

## Notas

- Commits en Conventional Commits en español, con el alcance del paquete. Por ejemplo, `feat(execution_profiles): …` y `feat(integrity_policy): …`.
- **Bitácora:** `docs/loop/bitacoras/U11-T02.md`, de una página como máximo.
  - Anota los nombres de los campos de `profile-base`.
  - Anota cada supuesto de firma que T03 a T05 deban respetar.
- Las claves de las pruebas son *canaries* sintéticos. Nunca uses una clave real ni datos reales.
- No uses la red, salvo `uv lock` y `uv sync` si cambian las dependencias.
- Haz *push* de `tarea/U11-T02` y vuelve con tu informe. No fusionas tú.
