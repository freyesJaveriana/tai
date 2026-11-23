# U01-T10: catálogo de límites C25 y `limits.load`

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 12 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T05, U01-T06 y U01-T07 (ola 6, en paralelo con U01-T08 y U01-T09).

---

## Alcance

**Dentro:**

> - `contracts/limits.v1.yaml` lleva:
>   - las cifras de security-design §5;
>   - `transcript_body_max_bytes` (1 004 096);
>   - `import_body_max_bytes` (2 113 536), con `import_file_max_bytes` < `import_body_max_bytes` (NFRD-U6-01);
>   - `cursor_max_chars` (128, U4, NFRD-U7-04);
>   - `voice_body_max_bytes` (6 016 384, NFRD-U9-03);
>   - `research_report_read_timeout_s` (30, NFRD-U12-02).
>
>   Cada entrada lleva `value`, `unit` de la lista cerrada, `owner`, `used_in` y, opcional, `derived_from`. El archivo tiene una sección `relations` (§4.4, NFRD-U1-01, NFRD-U1-02).
> - `contracts/src/veridicus_contracts/limits.py`: `load(environ)` lee el catálogo empaquetado una sola vez. Aplica `VERIDICUS_LIMIT_<NOMBRE>` solo para bajar un límite.
>
>   Lanza `LimitsConfigError` (`config.invalid_limit`) ante: un intento de subir, un nombre inexistente, una variable `VERIDICUS_LIMIT_*` desconocida, un valor inválido para su unidad o una relación rota (BR11.1, §4.15, NFRD-U1-09).
> - `contracts/src/veridicus_contracts/checks/limits_catalog.py`, módulo guardia. Comprueba:
>   - la forma;
>   - los tipos: todo es entero salvo `ratio` y `s`;
>   - las derivadas: `audio_base64_max_chars` = 8 000 000;
>   - las relaciones.
> - Pruebas nuevas en `contracts/tests/test_limits.py` y `contracts/tests/checks/test_limits_catalog.py`, con E33 y E37.
> - **F-12 de la ronda 4 de U01-T01:** `contracts/hatch_build.py` hoy ignora las entradas de `sources` que son archivos sueltos. Esta tarea:
>   1. añade `limits.v1.yaml` a `include` y `sources` de `contracts/pyproject.toml`;
>   2. hace que el hook copie también los archivos sueltos;
>   3. añade `limits.v1.yaml` a `[tool.uv] cache-keys`;
>   4. lo prueba leyendo el archivo con `importlib.resources.files("veridicus_contracts")` en la instalación editable y en la rueda.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Las marcas `x-veridicus-limit` de C1 y su comprobación contra el catálogo (`checks/limits_match.py`): son T14 y T15 (paso 16, PD-8).
- Editar los *fixtures* o las pruebas de T03.
- **Archivos de las tareas vecinas de la ola 6:** los de la tabla de U01-T08 (`docs/loop/tareas/U01-T08-tipos-de-llamadas-y-puerta-unica.md`).
  - Esta es la **única** tarea de la ola que toca `contracts/hatch_build.py` y `contracts/pyproject.toml`, y en este último solo `include`, `sources` y `cache-keys`.
  - No toca `uv.lock`; si cambia, para y lo informa.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 12, PD-1, PD-9 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C25 (revisión 3).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E33 y E37.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR11.1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.4, §4.15, §5 y NFRD-U1-01, NFRD-U1-02 y NFRD-U1-09.
- `docs/loop/revisiones/U01-T01/ronda-4.md`: avisos F-11 y F-12.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 12.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov
  ```
  Esperado: verde, con E33 y E37.

- [ ] **CA-2**: 100 % de ramas en `limits.py` y `checks/limits_catalog.py` (módulos guardia, V-GUARD).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --cov=veridicus_contracts.limits --cov=veridicus_contracts.checks.limits_catalog --cov-branch --cov-fail-under=100
  ```
  Esperado: verde, 100 %.

- [ ] **CA-3**: el catálogo está en la instalación editable y en la rueda (F-12).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde. `test_package_map.py` gana el caso de `limits.v1.yaml` en la rueda y en la instalación editable; es el único archivo de pruebas anterior que esta tarea amplía.

- [ ] **CA-4**: el lockfile no cambia.
  ```bash
  uv lock --check --directory contracts
  ```
  Esperado: código 0.

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

1. Escribe primero las pruebas de `limits.load` y de `checks/limits_catalog.py`, y el caso nuevo de `test_package_map.py`.
2. Míralas fallar y pega la salida en rojo en `docs/loop/bitacoras/U01-T10.md`.
3. Implementa hasta el verde.

`load` se prueba con un `environ` en memoria, nunca con `os.environ`.

---

## Reglas de la app que aplican

- **Límites solo bajan** (`project.md`): una variable de entorno puede bajar un límite, nunca subirlo.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- Una configuración faltante o inválida impide arrancar (`team.md` › Code Style): `LimitsConfigError` es fatal.

---

## Notas

- F-11: corre siempre con `uv run` y nunca con `--no-sync`. Tras tocar `hatch_build.py` o `cache-keys`, la primera corrida puede reconstruir el entorno; anótalo en la bitácora.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): catálogo de límites C25 y load (T10)`. Sin signo de dólar en el mensaje.
