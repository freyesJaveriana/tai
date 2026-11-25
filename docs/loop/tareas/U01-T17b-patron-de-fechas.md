# U01-T17b: patrón único de fecha en los contratos fusionados

> El orquestador llenó esta tarea a partir de la decisión E-22 del humano (2026-11-24), tomada tras la parada C de la ronda 1 de U01-T17. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que corrige:** pasos 9 (C2, C3 y C5), 10 (C7), 11 (llamada a modelo) y 13 (C19) de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** ninguna tarea abierta. Se fusiona **antes** que U01-T17, que luego se rebasa sobre ella. Puede correr en paralelo con T16 y T18, porque no toca sus archivos.

---

## Alcance

**Dentro:** las siete correcciones de abajo, ni una más.

> El patrón único de BR8.1 es el que ya declara `DateTime` en C1 (`contracts/api/console.v2.yaml:65`), copiado carácter por carácter:
>
> ```
> ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$
> ```
>
> 1. **C2**, `contracts/queues/runs.v2.yaml`: `enqueued_at` (línea 101) y `deadline_at` (línea 104) añaden ese `pattern` junto a `format: date-time`.
> 2. **C3**, `contracts/queues/results.v2.yaml`: `finished_at` (línea 67), igual.
> 3. **C5**, `contracts/queues/speech.v2.yaml`: `deadline_at` (línea 100), igual.
> 4. **C7**, `contracts/integrity/review-suggestion.v2.json`: `decided_at` (línea 95), igual.
> 5. **Llamada a modelo**, `contracts/model_calls/model-call.v1.yaml`: `at` (línea 52), igual.
> 6. **C19**, `contracts/cli/report.schema.v2.yaml`: el `pattern` de `created_at` (línea 133) pasa a ser el patrón único. Ya no admite fracciones de segundo ni desplazamientos. `maxLength` y `x-veridicus-limit` no cambian.
> 7. Nada más en esos archivos: ni `description`, ni `required`, ni otras propiedades.
>
> Si un *fixture* válido de esos contratos trae una fecha con fracciones o con desplazamiento, se corrige a la forma `AAAA-MM-DDTHH:MM:SSZ` con el mismo instante en UTC, y se nombra en la bitácora. Si un *fixture* inválido dependía de que el patrón viejo aceptara algo, se conserva su `expectation` y se anota.
>
> **Pruebas, con rojo primero:** un archivo nuevo, `contracts/tests/contracts/test_correcciones_t17b.py`.
> - **Lectura de vuelta de la forma:** cada uno de los siete campos lleva `format: date-time` y exactamente el `pattern` de `DateTime` de C1, leído del archivo de C1 y no copiado en la prueba.
> - **Lectura de vuelta con el validador real:** para cada contrato, se valida con el validador del paquete y el registro de esquemas (el mismo que ya usan las pruebas de cada contrato) un mensaje o documento sintético mínimo válido. Con `2026-10-02T21:40:00Z` se acepta. Con `2026-10-02T21:40:00.123Z` y con `2026-10-02T16:40:00-05:00` se rechaza.
> - **Control negativo:** una copia en memoria de C2 sin el `pattern` en `deadline_at` da rojo en la prueba de forma.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si una fuente aprobada (contract-summary, functional-spec o security-design de U1) exige para C19 fracciones de segundo o desplazamientos, para y lo informas con la cita.
- Si encuentras otro `format: date-time` fuera de C6 que no esté en la lista, lo informas en la bitácora como candidata y no lo tocas.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **C6** (`contracts/analyzer/v1/`): es el contrato común y no cambia, aunque tenga fechas sin patrón.
- **C1**: ya cumple.
- **`contracts/format/datetime.v1.yaml` y los módulos guardia de T17** (`metrics.py`, `datetime_format.py`, `naming.py`). Son de T17.
- **Cualquier otro contrato, cifra de C25 o entrada del catálogo de errores.**
- **Las pruebas existentes.** Única excepción: si una prueba fija el patrón viejo de C19 o una fecha con fracciones o desplazamiento en un caso válido, se ajusta solo a E-22, y se nombra en la bitácora.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.** Si necesitas tocarlos, paras y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-22.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 9 a 13 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR8.1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E16.
- Los seis contratos de la lista, y `contracts/api/console.v2.yaml` (`DateTime`, solo lectura).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: lecturas de vuelta y validación real.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/contracts/test_correcciones_t17b.py --no-cov
  ```
  Esperado: verde, con la fecha sin fracciones aceptada y las otras dos rechazadas por el validador en cada contrato.

- [ ] **CA-2**: la suite completa sigue en verde.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-3**: el diff de los contratos solo añade o cambia `pattern`.
  ```bash
  git -C /workspace/.worktrees/U01-T17b diff feat/b1-contratos...HEAD -- contracts/queues contracts/integrity contracts/model_calls contracts/cli
  ```
  Esperado: solo las siete líneas de `pattern` (seis añadidas y una cambiada en C19), más los *fixtures* nombrados en la bitácora.

- [ ] **CA-4**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T17b diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: un subconjunto de los seis contratos, sus *fixtures* nombrados en la bitácora, `contracts/tests/contracts/test_correcciones_t17b.py`, las pruebas que ajuste la excepción de «Fuera» (cada una nombrada) y `docs/loop/bitacoras/U01-T17b.md`.

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

1. Escribe primero `test_correcciones_t17b.py`.
2. Haz su commit, corre el rojo contra `feat/b1-contratos` y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T17b.md`.
3. Haz las correcciones hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada.

---

## Reglas de la app que aplican

- **NFR11.2 y BR8.1:** un solo formato de fecha en todo el sistema.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `fix(contracts): patron unico de fecha en C2, C3, C5, C7, C19 y la llamada a modelo (U01-T17b)`. Sin signo de dólar en el mensaje.
