# U01-T04: copia del contrato común C6 (parada humana) y F7 en verde

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con PD-9 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 6 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Respalda AC3.2.1, AC3.6.2 y AC15.4.7.
**Depende de:** U01-T03 (ola 4). **Con parada humana** antes del despacho (PD-4).

---

## ⏸ Parada humana: la copia de C6 la pone el humano

El codificador **no se despacha** hasta que el humano termina estos pasos (PD-4, BR1.8, F7 paso 5):

1. El orquestador crea el worktree `.worktrees/U01-T04` en la rama `tarea/U01-T04` desde `feat/b1-contratos` y avisa al humano.
2. **El humano** copia `entrada.schema.json` y `salida.schema.json` desde `/insumos/app/contratos/analizador/v1/` a `.worktrees/U01-T04/contracts/analyzer/v1/`.
3. **El humano** recalcula las huellas **en `/insumos`** con `sha256sum` y escribe `contracts/analyzer/v1/SHA256SUMS` con exactamente dos líneas (`<sha256>  entrada.schema.json` y `<sha256>  salida.schema.json`).
4. Si los archivos quedan a nombre de root (intercambio con `docker cp`), el humano lo corrige desde el anfitrión antes del commit. El agente no los toca.
5. **El humano** hace un commit propio solo con esos tres archivos, por ejemplo `chore(contracts): copia del contrato común C6 v1.0.0 (PD-4)`, y le da al orquestador la ruta de origen y las dos huellas. El orquestador las copia en la descripción del PR de la tarea.

Solo entonces el orquestador despacha al codificador sobre ese worktree.

---

## Alcance

**Dentro:**

> F7 en `contracts/tests/conftest.py` (`pytest_sessionstart`): `SHA256SUMS` de exactamente dos líneas, SHA-256 de los bytes igual a su línea y `contrato: { const: "1.0.0" }` en los dos esquemas. Si algo falla, F7 aborta la sesión con el mensaje de F7 paso 4: «La copia del contrato común no es la aprobada; los cambios se proponen en el repositorio principal». Con la copia del humano, las pruebas `c6` de T03 pasan a verde, incluida E18 (copia en memoria de `salida.schema.json` con un byte cambiado en una `description` → F7 en rojo).

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Editar, generar, regenerar, formatear o renombrar** `contracts/analyzer/v1/entrada.schema.json`, `salida.schema.json` o `SHA256SUMS` (BR1.8, PD-4). Si la copia parece mal, el codificador para y lo informa; no la corrige.
- Leer o copiar nada de `/insumos`. Las huellas se comparan solo contra los archivos del worktree.
- Las pruebas `c7` de `tests/guards/test_autonomia_05.py`: pasan a verde en T06 (paso 8, PD-8).
- Cualquier otro contrato (T05 a T14) y cualquier módulo de `checks/`.
- Cambiar la `expectation` o el `reject_reason` de un *fixture* de T03. Para el `payload` de los *fixtures* de C6, ver la decisión pendiente A-4 de T03.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 6, PD-4, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: F1 paso 2, F7 y E18.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.7, BR1.8, BR3.1–BR3.6.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.19.
- `docs/loop/tareas/U01-T03-rojo-contratos-y-guardias.md` y `docs/loop/bitacoras/U01-T03.md`: las pruebas en rojo que esta tarea pone en verde.
- `docs/loop/revisiones/U01-T01/ronda-4.md`: aviso F-11.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: la copia de C6 entró solo por el commit del humano.
  ```bash
  git log --format="%h %s" feat/b1-contratos..HEAD -- contracts/analyzer/v1/entrada.schema.json contracts/analyzer/v1/salida.schema.json contracts/analyzer/v1/SHA256SUMS
  ```
  Esperado: exactamente una línea, el commit de copia del humano. Ningún commit del codificador toca esos tres archivos.

- [ ] **CA-2**: las huellas de los bytes coinciden con `SHA256SUMS` y con las que el humano anotó en el PR (lectura de vuelta).
  ```bash
  sha256sum contracts/analyzer/v1/entrada.schema.json contracts/analyzer/v1/salida.schema.json
  ```
  ```bash
  cat contracts/analyzer/v1/SHA256SUMS
  ```
  Esperado: dos líneas en `SHA256SUMS`, con los mismos dos hashes que da `sha256sum` y que figuran en la descripción del PR.

- [ ] **CA-3**: C6 y F7 en verde (verificación del paso 6).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_analyzer_copy.py tests/guards/test_autonomia_05.py -m c6 --no-cov
  ```
  Esperado: verde. Incluye E18 en rojo dentro de la prueba (F7 lo detecta) y los *fixtures* de C6 de T03 aceptados o rechazados por su `reject_reason`. Las pruebas `c7` de `test_autonomia_05.py` siguen en rojo hasta T06; no cuentan aquí.

- [ ] **CA-4**: F7 corre en `pytest_sessionstart` y no bloquea una sesión sana.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_runner.py --no-cov
  ```
  Esperado: `2 passed`. La prueba E18 de CA-3 demuestra la otra cara: con un byte cambiado, F7 da el mensaje de F7 paso 4.

- [ ] **CA-5**: el mapa de la rueda sigue igual con la copia dentro de `analyzer/v1/`.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-6**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-7**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

El rojo ya existe: lo escribió T03 (`-m c6` de `test_analyzer_copy.py` y de `test_autonomia_05.py`, incluida «F7 detecta E18»). Antes de tocar `conftest.py`, corre CA-3 con la copia del humano ya presente y pega la salida en rojo en `docs/loop/bitacoras/U01-T04.md`. Luego implementa F7 y vuelve a correrlo hasta el verde.

F7 se escribe como una función que recibe los bytes de los dos esquemas y el texto de `SHA256SUMS`. `pytest_sessionstart` la llama sobre los archivos reales y aborta la sesión (`pytest.exit` con código distinto de 0) si falla. La prueba E18 la llama sobre una copia **en memoria**, sin escribir en `analyzer/v1/` ni abortar la sesión. Si la prueba E18 de T03 ya cubre esto, no se duplica.

---

## Reglas de la app que aplican

- **BR1.7 y BR1.8:** el agente no edita la copia de C6; el ancla frente al repositorio principal es la revisión humana del PR de copia.
- **AUTONOMIA-05** (Mapa AUTONOMIA): `error` ⇒ hallazgos vacíos y hallazgo sin campo obligatorio rechazado → `tests/guards/test_autonomia_05.py -m c6`.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos:** la copia de C6 es un contrato, no datos del piloto (permitido por `project.md` › Decided). Ninguna otra cosa de `/insumos` entra al repositorio.

---

## Notas

- Archivos que se **modifican en su sitio**: `contracts/tests/conftest.py` (añadir F7 sin romper la resolución de rutas de T01).
- La copia llega con la forma que fijó el TG. Si un `$id` o un `$ref` canónico no se resuelve con el registro de T02, el codificador para y lo informa: no se adapta la copia, se revisa el registro o se lleva al humano.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `test(contracts): F7 comprueba la copia del contrato común (T04)`. El commit de copia es del humano.
