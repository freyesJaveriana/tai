# U01-T02b: el registro acepta el `$id` relativo de la copia de C6

> Tarea correctiva que el orquestador abrió el 2026-11-23 a partir del hallazgo H-1 del codificador de T03. Reabre una parte del paso 3 del plan (ya marcado). El humano la revisa antes del despacho.
>
> **Este archivo, con el paso del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 3 (registro), en `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Depende de:** U01-T02 (fusionada). **Debe fusionarse antes de despachar T04.** Puede correr en paralelo con la revisión de T03: no toca sus archivos.

---

## Problema

El paso 3 dice que el registro recorre los esquemas «bajo `https://veridicus.invalid/` + `$id`». La copia aprobada de C6 (que el humano pondrá en T04 y que **nunca se edita**, BR1.8) declara `$id` relativos, sin barra inicial: `veridicus/contracts/analyzer/v1/entrada` y `veridicus/contracts/analyzer/v1/salida`. Hoy `registry.build_registry` los rechaza con `LoadError … un $id absoluto solo se admite bajo vendor/`, así que con la copia dentro fallaría todo lo que valida por el registro.

## Alcance

**Dentro:**

> `contracts/src/veridicus_contracts/registry.py`: un `$id` relativo (con o sin barra inicial) se resuelve contra `https://veridicus.invalid/`, igual que hoy uno con barra. Las reglas de §4.2 y FD-U1-11 siguen: un `$id` absoluto ajeno fuera de `vendor/` se rechaza, y la recuperación de cualquier URI ajena lanza error. Sus pruebas en `contracts/tests/test_registry.py`.

**Fuera:**

- Copiar, leer en el repositorio o editar C6: la copia es del humano en T04. Las pruebas usan esquemas **sintéticos** en `tests/data/` con un `$id` de la misma forma (p. ej. `veridicus/contracts/ejemplo/v1/a`).
- Cualquier archivo de T03 (`tests/contracts/`, `tests/guards/`, *fixtures*, `check_red`).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: el registro acepta un `$id` relativo sin barra y resuelve una referencia hacia él.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_registry.py --no-cov
  ```
  Esperado: verde. Pruebas nuevas, en rojo primero (salida en la bitácora): (1) un esquema sintético con `$id: "veridicus/contracts/ejemplo/v1/a"` se registra en `https://veridicus.invalid/veridicus/contracts/ejemplo/v1/a`; (2) otro esquema con `$ref: "/veridicus/contracts/ejemplo/v1/a#/$defs/x"` se resuelve y valida por lectura de vuelta (una instancia válida pasa y una inválida falla); (3) un `$id` absoluto ajeno (`https://example.com/x`) fuera de `vendor/` sigue rechazado; (4) un `$id` relativo que intenta salir de la base (`../x`) se rechaza.

- [ ] **CA-2**: 100 % de ramas en `registry` y suite de tareas anteriores en verde.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py tests/test_validators.py tests/test_package_map.py tests/test_runner.py --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/registry.py" --fail-under=100
  ```
  Esperado: verde y 100 %.

- [ ] **CA-3**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-4**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Reglas de la app que aplican

- **NFR10.4 y NFR10.5:** ninguna URI ajena se recupera nunca; la suite no usa red.
- **BR1.8:** la copia de C6 no se edita; por eso el registro se adapta a ella.
- Solo datos sintéticos. No se copia nada de `/insumos`.

## Notas

- `registry` es módulo guardia: 100 % de ramas.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español, por ejemplo `fix(contracts): el registro acepta $id relativos (T02b)`.
