# U01-T05: mensajes de cola C2, C3 y C5 v2

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con PD-9 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 7 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`). Respalda AC3.2.1 y AC3.6.2.
**Depende de:** U01-T04 (ola 5, en paralelo con U01-T06 y U01-T07).
---

## Alcance

**Dentro:**

> Los tres contratos AsyncAPI 3.0 de la cola: `contracts/queues/runs.v2.yaml` (C2), `results.v2.yaml` (C3) y `speech.v2.yaml` (C5, con `x-veridicus-priority: SHOULD`), con sobre `schema_version`, `message_id` y `attempt ≥ 1`; `entrada` y `salida` por `$ref` canónico a la copia de C6; `effective_config` contra C18; `audio_base64` con `x-veridicus-limit: audio_base64_max_chars`; `servers` internos; y el esquema estricto de las entradas de `<cola>:failed` (solo `message_id`, ID de la corrida o del audio, `attempt` y `code`; NFRD-U1-07, NFR-U4-07, NFR-U9-03). Además, el esquema de C18 `contracts/profiles/effective-config.v1.yaml` (estricto), que C2 referencia; la huella de `effective-config.valid.json` es su `sha256_jcs` (BR9.7) (E-5). Los *fixtures* y `tests/contracts/test_queue_messages.py` ya existen (T03): **esta tarea solo escribe los contratos**.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- `queues/indexing.v1.yaml` (C4): **no** se entrega. Tampoco el umbral ni las calificaciones retiradas (BR2.2, BR2.4 y BR2.5 «Retirado»).
- Comprobar las marcas `x-veridicus-limit` contra C25: es `checks/limits_match.py` en T15 (paso 16, PD-8). Aquí la marca solo se escribe.
- El resto de `profiles/` (`profile-base`, `profiles.schema`, `prices.schema`) y `profiles.validate`: es T09 (paso 11).
- Excepción a «no editar las pruebas de T03»: solo los textos que siguen citando E-2 o T09 para C18 (docstrings de `tests/contracts/test_queue_messages.py:9,120` y `test_profiles_contract.py:3`) se ponen al día con E-5 (F-07 de la ronda 2 de U01-T03). Ninguna aserción cambia.
- Lógica de productores y consumidores (U4, U9).
- Editar los *fixtures* o las pruebas de T03. Si una prueba parece mal, el codificador para y lo informa al orquestador (`docs/loop/CANDIDATAS.md`); no la cambia.
- **Archivos de las tareas vecinas de la ola 5**, que corren en paralelo y no se pisan:

  | Tarea | Archivos que toca |
  |---|---|
  | **T05 (esta)** | `contracts/queues/runs.v2.yaml`, `results.v2.yaml`, `speech.v2.yaml`, si va aparte el esquema de `<cola>:failed` dentro de `contracts/queues/`, y `contracts/profiles/effective-config.v1.yaml` |
  | T06 | `contracts/integrity/review-suggestion.v2.json`, `contracts/src/veridicus_contracts/checks/suggestion_conditions.py`, `contracts/tests/checks/test_suggestion_conditions.py` |
  | T07 | `contracts/errors/error-codes.v2.yaml`, `contracts/src/veridicus_contracts/checks/error_codes.py`, `contracts/tests/checks/test_error_codes.py`, `contracts/tests/test_errors_catalog.py` y todo `libs/errors/` |

  Ninguna de las tres toca `contracts/pyproject.toml`, `contracts/uv.lock`, `contracts/hatch_build.py`, `contracts/tests/conftest.py`, `contracts/tests/helpers.py`, `checks/__init__.py` ni los *fixtures* y pruebas de T03. Si alguna lo necesita, para y lo informa.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 7, PD-1, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C2, C3 y C5 (revisión 3).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: F2, E1–E3 y FD-U1-01 a FD-U1-14.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.1–BR1.3, BR2.1, BR2.3.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.2, §4.3, §4.9 y §10 (NFRD-U1-07).
- `contracts/analyzer/v1/` (copia de C6, solo lectura) y `contracts/queues/fixtures/` (*fixtures* de T03).
- `docs/loop/revisiones/U01-T01/ronda-4.md`: aviso F-11.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: los mensajes de cola aceptan y rechazan sus *fixtures* (verificación del paso 7).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_queue_messages.py --no-cov
  ```
  Esperado: verde. Cada *fixture* de `queues/fixtures/runs/`, `results/` y `speech/` se acepta, o se rechaza por su `reject_reason`: E1 sin `entrada` (BR2.1), E2 mayor desconocido (BR1.2), E3 menor con campo nuevo aceptado (BR1.3), `salida` que no cumple C6 (BR2.3) y fallido con un campo `text` (NFRD-U1-07).

- [ ] **CA-2**: la tarea solo escribió contratos de `queues/` y no entregó C4.
  ```bash
  git diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo archivos de `contracts/queues/` fuera de `fixtures/` y `docs/loop/bitacoras/U01-T05.md`. No aparece `indexing.v1.yaml`.

- [ ] **CA-3**: el mapa de la rueda sigue igual.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-4**: tipos y *lint* del paquete siguen limpios.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-5**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

El rojo es de T03. Antes de escribir el primer contrato, corre CA-1 y pega la salida en rojo en `docs/loop/bitacoras/U01-T05.md`; después, contrato por contrato, hasta el verde. No se escriben pruebas nuevas: si falta un caso, va a `CANDIDATAS.md`.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** `servers` solo internos (ruta relativa, `http://veridicus-<nombre>:<puerto>` o `*.svc.cluster.local`, siempre `http`). La guardia `asyncapi` de `test_autonomia_04.py` los recorrerá en T13.
- **AUTONOMIA-05:** `salida` de C3 por `$ref` canónico a la copia de C6, sin redefinir el hallazgo.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **NFR10.2:** sobre y entradas de `<cola>:failed` estrictos; las fallidas no llevan texto.
- Solo datos sintéticos.

---

## Notas

- Las referencias a C6 usan la forma canónica bajo `https://veridicus.invalid/` del registro de T02; la forma antigua `contracts/analyzer/v1/salida.schema.json#/$defs/cita` no se resuelve (E36).
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): mensajes de cola C2, C3 y C5 v2 (T05)`.

### Ampliación de alcance para la ronda 2 (orquestador, 2026-11-23)

En la ronda 1, el codificador copió el esquema de C18 dentro de `runs.v2.yaml` en lugar de usar un `$ref`, porque el registro de T02 solo carga archivos `*.schema.json`. Esa copia incumple BR12.3: el registro carga **cada esquema del paquete** y es el único resolvedor; las referencias entre esquemas son rutas absolutas del `$id`. No hace falta cambiar el plan: se corrige el registro para que cumpla BR12.3.

- **Dentro, además:** `contracts/src/veridicus_contracts/registry.py` y `contracts/tests/test_registry.py`.
  - El registro carga también los esquemas YAML. Cuenta como esquema todo archivo `.yaml` o `.json` bajo `contracts/` cuyo documento raíz declare `$schema` y `$id`, fuera de `fixtures/` y de `tests/`.
  - Las reglas de T02b se mantienen: URI repetida, `$id` vacío o con fragmento, fuera de la base.
  - Pruebas en rojo primero; `registry` sigue al 100 % de ramas.
- `effective_config` de C2 pasa a `$ref: /veridicus/contracts/profiles/effective-config.v1` (o el `$id` que lleve C18), y se borra la copia de `components/schemas`.
- Ninguna tarea vecina de la ola 5 ni de la ola 6 toca `registry.py`.
- Criterio adicional, en dos comandos. Primero `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_registry.py --cov-fail-under=0` → verde. Después `uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/registry.py --fail-under=100` → 100 %. El total del paquete no cuenta aquí: `addopts` ya mide todo el paquete. Corrección del orquestador tras la ronda 2.

### Decisión tomada (2026-11-23)

- **A-5 → E-5: opción (a), T05 escribe `effective-config.v1.yaml`.** E-2 (opción c) se descartó porque el registro no resuelve C2 entero con el `$ref` ausente (ronda 1 de U01-T03). Contexto original: el paso 7 valida `effective_config` de C2 contra C18 (F2 paso 3, BR9.7), pero C18 (`profiles/effective-config.v1.yaml`) lo escribe el paso 11, en T09 (ola 6). PD-8 solo aplaza C25 y C1, no C18. Con el registro cerrado de T02, un `$ref` a un esquema ausente es un error y el *fixture* válido de C2 no puede pasar a verde en esta ola. Opciones: (a) adelantar a T05 solo `profiles/effective-config.v1.yaml` (T09 conserva `profile-base`, `profiles.schema`, `prices` y `profiles.validate`); (b) mover T05 a la ola 6, después de T09; (c) aplazar el caso de C2 con `effective_config` como PD-8 hace con C25. Las tres cambian el plan aprobado y piden volver a aprobarlo. Mientras no se decida, si el verde depende de C18, el codificador para y lo informa: no escribe C18.
