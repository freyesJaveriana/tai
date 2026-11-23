# U01-T09: perfiles de ejecución C18 y `profiles.validate`

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 11 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Respalda AC13.3.1.
**Depende de:** U01-T05, que ya escribió `effective-config.v1.yaml` (E-5). Va en la ola 6, en paralelo con U01-T08 y U01-T10.

---

## Alcance

**Dentro:**

> - `contracts/profiles/profile-base.schema.v1.yaml`, abierto. Lleva al menos un papel, `role_aliases`, un `fallback_provider`, `api_key_ref` con `^[A-Z][A-Z0-9_]{2,63}$` y `purpose` con patrón.
> - `contracts/profiles/profiles.schema.v1.yaml`, la especialización del analizador. Es cerrada, con `unevaluatedProperties: false`: exactamente `judge` y `verifier`, el alias `verifier_permuted → verifier` y `purpose` en su enum (FD-U1-02, FD-U1-12, BR9.2–BR9.5).
> - `contracts/profiles/prices.schema.v1.yaml` (C18, estricto).
> - `contracts/src/veridicus_contracts/profiles.py`, con `validate(data, *, key_prefix, kind)` sin E/S. Comprueba:
>   - el sobre: `schema_version: 1.0.0` y nombres `^[a-z0-9-]{1,48}$`;
>   - las referencias cruzadas de los alias;
>   - el prefijo de `api_key_ref`;
>   - la especialización con `kind: analyzer`.
>
>   Lanza `ProfileValidationError` (`config.invalid_profile`), que nombra el perfil, el papel y el ajuste, nunca su valor (F8, BR9.8, §4.15).
> - `contracts/tests/test_profiles.py`: E21–E26, E38 y E39. Incluye la pureza (con `open`, `os.environ` y `socket.socket` sustituidos) y un *canary* en `api_key_ref` que no aparece en ningún mensaje.
>
> `tests/contracts/test_profiles_contract.py` ya existe (T03). Esta tarea pone en verde los casos de perfiles y precios; los de `effective-config` ya pasaron en T05.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- `contracts/profiles/effective-config.v1.yaml`: lo escribió T05 (E-5) y no se edita aquí. Si parece mal, el codificador para y lo informa.
- Comprobar que las claves existan y que el anonimizador sea obligatorio: es U11.
- Editar los *fixtures* o las pruebas de T03. Hay una excepción, del supuesto de T03: si `profiles.schema` cierra una forma distinta de la de FD-U1-02, el codificador **para y lo informa**; no ajusta los *fixtures* por su cuenta.
- **Archivos de las tareas vecinas de la ola 6:** los de la tabla de U01-T08, `docs/loop/tareas/U01-T08-tipos-de-llamadas-y-puerta-unica.md`.
  - Esta tarea toca solo `profile-base.schema.v1.yaml`, `profiles.schema.v1.yaml`, `prices.schema.v1.yaml`, `profiles.py` y `tests/test_profiles.py`.
  - No toca `contracts/pyproject.toml`, `contracts/uv.lock`, `contracts/hatch_build.py`, `conftest.py`, `helpers.py` ni `checks/__init__.py`.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 11, PD-1 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-5.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C18 (revisión 3).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: F8, FD-U1-02, FD-U1-12, E21–E26, E38 y E39.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR9.2–BR9.8.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.15.
- `contracts/profiles/fixtures/` (de T03) y `contracts/profiles/effective-config.v1.yaml` (de T05), en solo lectura.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 11.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_profiles.py tests/contracts/test_profiles_contract.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: 100 % de ramas en `profiles.py` (módulo guardia, V-GUARD).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_profiles.py --cov=veridicus_contracts.profiles --cov-branch --cov-fail-under=100
  ```
  Esperado: verde, 100 %.

- [ ] **CA-3**: el caso `c18` de C2 sigue en verde (no se rompe lo de T05).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_queue_messages.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-4**: el mapa de la rueda sigue igual.
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

1. Corre CA-1 antes de escribir nada y pega la salida en rojo en `docs/loop/bitacoras/U01-T09.md`.
2. Escribe `tests/test_profiles.py` y míralo fallar.
3. Implementa los esquemas y `profiles.py` hasta el verde.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** `api_key_ref` es el nombre de una variable, nunca una clave. Ningún mensaje de error lo repite (*canary*). Las claves viven en un `Secret` que crea el humano.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Juez y verificador de familias distintas** (`project.md`): `same_family_declared` solo se admite en un perfil de demostración que lo declara.
- Solo datos sintéticos; ninguna clave real en los *fixtures*.

---

## Notas

- `validate` no hace E/S: recibe un `dict` ya cargado por los cargadores de T02.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): perfiles de ejecución y validate (T09)`. Sin signo de dólar en el mensaje.
