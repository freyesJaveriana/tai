# U01-T15b: correcciones de C1, C5, C19 y C25 que encontraron las guardias de T15

> El orquestador llenó esta tarea a partir de las decisiones E-10 a E-15 del humano (2026-11-23), tomadas tras la ronda 1 de U01-T15. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que corrige:** pasos 9 (C5), 12 (C19), 14 (C25) y 16 (C1) de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** ninguna tarea abierta; parte de `feat/b1-contratos` en 5ae613b o posterior. Se fusiona **antes** que U01-T15, que luego se rebasa sobre ella.

---

## Alcance

**Dentro:** las seis correcciones de abajo, ni una más. Cada una cita su decisión de `decisiones-humano.md`.

> 1. **C25, entradas nuevas (E-11, E-14).** En `contracts/limits.v1.yaml`, en el bloque de su dueño y sin tocar ninguna cifra existente:
>    - `session_body_max_bytes: {value: 32768, unit: bytes, owner: U4, used_in: [C1]}`
>    - `model_call_role_max_chars: {value: 32, unit: chars, owner: U1, used_in: [C19]}`
>    - `report_per_run_items: {value: 3, unit: runs, owner: U1, used_in: [C19]}`
>
>    Como `runs` no está en `UNIDADES` de `contracts/src/veridicus_contracts/checks/limits_catalog.py`, se añade ahí, con su caso en `tests/checks/test_limits_catalog.py` (precisión P-T15b-1). Si otra prueba de T10 fija el conjunto exacto de entradas o de unidades, se actualiza solo para sumar estas tres entradas y la unidad.
> 2. **C25, `used_in` (E-15).** Se añade `C5` a `used_in` de `turn_max_chars` y de `report_token_max_chars`. No se toca ningún otro `used_in`: eso lo alinea T15.
> 3. **C1, `POST /sessions` (E-14).** En `contracts/api/console.v2.yaml`:
>    - `x-veridicus-max-bytes: session_body_max_bytes` en el `requestBody`;
>    - `profile_name` con `pattern: '^[a-z0-9-]{1,48}$'`, el mismo patrón que `/sessions/import`;
>    - `413` con `$ref` a `Problem`, si las demás operaciones con `x-veridicus-max-bytes` lo declaran.
> 4. **C1, estados (E-12).** `validation.invalid_request` en `PATCH /users/{user_id}` y `ethics.text_version_outdated` en `POST /acknowledgements` pasan de la respuesta `409` a la `422`, que es el estado del catálogo.
>    - Si la `409` nombra además otro `code` con estado 409 en el catálogo, la `409` se queda solo con ese `code`.
>    - Si no queda ninguno, la `409` se retira.
>    - No cambia el catálogo de errores.
> 5. **C5 (E-15).** En `contracts/queues/speech.v2.yaml`, dentro de `TranscriptResult`:
>    - `text` lleva `maxLength: 20000` y `x-veridicus-limit: turn_max_chars`;
>    - `model_digest` lleva `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`.
> 6. **C19 (E-11, E-15).**
>    - En `contracts/model_calls/model-call.v1.yaml`, `/properties/role` lleva `x-veridicus-limit: model_call_role_max_chars` y `/$defs/token` lleva `x-veridicus-limit: report_token_max_chars`.
>    - En `contracts/cli/report.schema.v2.yaml`, cada `per_run` de `metric_ratio` y `metric_count` lleva `x-veridicus-limit: report_per_run_items`. Se conservan `minItems: 3` y `maxItems: 3`.
>
> **Pruebas de lectura de vuelta, con rojo primero:** un archivo nuevo, `contracts/tests/contracts/test_correcciones_t15b.py`. Lleva un caso por corrección: cada uno carga el contrato real con el cargador del paquete y comprueba la marca, la cifra, el patrón o el estado esperado. Lleva además un control negativo por corrección, sobre una copia en memoria a la que se le quita la marca o se le cambia la cifra.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Los módulos guardia de T15** (`auth_surface.py`, `strict_bodies.py`, `config_write.py`, `limits_match.py`, `_openapi.py` y la ampliación de `error_codes.py`) y sus pruebas. No están en esta base ni se copian.
- **La lista explícita de objetos abiertos de C21 (E-13).** La hace T15 en su ronda 2. C21 no cambia.
- **Cualquier otro defecto de un contrato.** Si lo ves, lo anotas en la bitácora como candidata y no lo corriges.
- **Cambiar cifras de C25, el catálogo de errores o C6** (`contracts/analyzer/v1/`).
- **Las pruebas de T03** (`tests/guards/`) y las de T11 a T14. Única excepción: una aserción de `tests/contracts/test_console.py` que fije las respuestas `409` de esas dos operaciones o la lista de límites de C1, ajustada solo a E-12 y E-14. Segunda excepción (P-T15b-2): en `tests/checks/test_report_closed.py` (T12), `test_una_cadena_de_model_call_no_exige_la_marca_pero_si_el_tope` afirma que `/$defs/token` de `model-call.v1.yaml` no lleva marca. Esa aserción pasa a exigir `x-veridicus-limit: report_token_max_chars`, y la docstring se ajusta a ese cambio; el resto de la prueba no cambia. Si ajustas alguna de las dos, la nombras en la bitácora.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.** Si necesitas tocarlos, paras y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-10 a E-15.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 9, 12, 14 y 16 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.3, §4.4 y §4.7.
- `docs/loop/revisiones/U01-T15/` no existe todavía. La salida de las guardias que encontraron estos defectos está en la bitácora de T15, en la rama `tarea/U01-T15` (55455f6): `git -C /workspace show 55455f6:docs/loop/bitacoras/U01-T15.md`.
- `contracts/limits.v1.yaml`, `contracts/api/console.v2.yaml`, `contracts/queues/speech.v2.yaml`, `contracts/model_calls/model-call.v1.yaml`, `contracts/cli/report.schema.v2.yaml`, `contracts/errors/error-codes.v2.yaml` (solo lectura) y `contracts/src/veridicus_contracts/checks/limits_catalog.py`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: las lecturas de vuelta de las seis correcciones.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/contracts/test_correcciones_t15b.py --no-cov
  ```
  Esperado: verde, con al menos 12 casos: uno positivo y uno negativo por corrección.

- [ ] **CA-2**: la suite de contratos y guardias sigue en verde con los contratos corregidos.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-3**: el catálogo de límites sigue válido con las entradas nuevas.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov
  ```
  Esperado: verde. El diff de `limits.v1.yaml` solo añade las tres entradas y `C5` en dos `used_in`:
  ```bash
  git -C /workspace/.worktrees/U01-T15b diff feat/b1-contratos -- contracts/limits.v1.yaml
  ```

- [ ] **CA-4**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T15b diff --name-only feat/b1-contratos
  ```
  Esperado: un subconjunto de `contracts/limits.v1.yaml`, `contracts/api/console.v2.yaml`, `contracts/queues/speech.v2.yaml`, `contracts/model_calls/model-call.v1.yaml`, `contracts/cli/report.schema.v2.yaml`, `contracts/src/veridicus_contracts/checks/limits_catalog.py`, `contracts/tests/checks/test_limits_catalog.py`, `contracts/tests/test_limits.py`, `contracts/tests/contracts/test_console.py`, `contracts/tests/checks/test_report_closed.py`, `contracts/tests/contracts/test_correcciones_t15b.py` y `docs/loop/bitacoras/U01-T15b.md`.

- [ ] **CA-5**: los contratos están en la instalación editable y en la rueda.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-6**: tipos, *lint* y la CI del repositorio.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `Success: no issues found`, `All checks passed!` y `0 apariciones`, con código 0.

---

## Plan de pruebas

1. Escribe primero `test_correcciones_t15b.py` y el caso de la unidad `runs` en `test_limits_catalog.py`.
2. Haz su commit, corre el rojo contra `feat/b1-contratos` y pega la salida literal en `docs/loop/bitacoras/U01-T15b.md`.
3. Haz las seis correcciones hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con el archivo del commit final y pega esa salida.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** con estos topes, ningún texto de C1, C5 ni C19 queda abierto (§4.4), así que ningún campo sin acotar deja salir testimonio.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- **Precisión P-T15b-1:** `runs` entra en `UNIDADES` porque E-11 pide una entrada de C25 para un `maxItems` de corridas, y ninguna unidad existente las nombra. No es una cifra nueva.
- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`. En la ronda 1 de T15 se editó una prueba con un heredoc, y no debe repetirse.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`. Si el `.venv` del worktree no existe, puedes poblarlo una sola vez con `uv sync --frozen`, sin tocar `uv.lock`, y lo anotas en la bitácora.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `fix(contracts): topes y estados que encontraron las guardias de C1 (U01-T15b)`. Sin signo de dólar en el mensaje.
