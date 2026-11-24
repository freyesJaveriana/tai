# U01-T15c: tope del texto de los turnos y del mensaje en C2

> El orquestador llenó esta tarea a partir de las decisiones E-16 y E-17 del humano (2026-11-23), tomadas tras la ronda 2 de U01-T15. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que corrige:** paso 9 (C2) y paso 14 (C25) de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** ninguna tarea abierta. Se fusiona **antes** que U01-T15, que luego se rebasa sobre ella.

---

## Alcance

**Dentro:** las tres correcciones de abajo, ni una más.

> 1. **C2 (E-16).** En `contracts/queues/runs.v2.yaml`, `RunRequested.payload.properties.entrada` pasa a ser:
>    - un `allOf` con dos ramas: primero el `$ref` actual a `/veridicus/contracts/analyzer/v1/entrada`, y después una rama de refinamiento que solo trae `properties`;
>    - en esa rama, el camino `transcripcion` → `turnos` → `items` → `texto`, con `maxLength: 20000` y `x-veridicus-limit: turn_max_chars`;
>    - la rama no añade ninguna propiedad que C6 no declare, ni `required` ni `additionalProperties`;
>    - la `description` de `entrada` se conserva.
> 2. **C2, tope del mensaje (E-16).** `RunRequested` lleva `x-veridicus-max-bytes: run_message_max_bytes` en el mismo nivel en que C2 ya declara sus extensiones. Si C2 no tiene todavía ese nivel, ponlo en el `payload` del mensaje y anótalo en la bitácora.
> 3. **C25, `used_in` (E-17).** En `contracts/limits.v1.yaml`, `turn_max_chars` pasa a `used_in: [C1, C2, C5]` y `run_message_max_bytes` pasa a `used_in: [C2]`. No cambia ninguna cifra ni ningún otro `used_in`.
>
> **Pruebas, con rojo primero:** un archivo nuevo, `contracts/tests/contracts/test_correcciones_t15c.py`.
> - Lecturas de vuelta: comprueba la forma de `allOf` (el `$ref` sin tocar y la rama con su marca y su cifra), la extensión del tope del mensaje y los dos `used_in`.
> - **Lectura de vuelta con el validador real:** se valida un mensaje sintético `RunRequested` con el validador del paquete y el registro de esquemas (el mismo que ya usan las pruebas de C2). El mensaje con un `texto` de 20000 caracteres se acepta, y el de 20001 se rechaza.
> - Controles negativos: una copia en memoria sin la marca, otra con una cifra distinta y otra con una rama que añade una propiedad nueva.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **C6** (`contracts/analyzer/v1/`): es el contrato común y no cambia.
- **Los módulos guardia de T15** y sus pruebas. No están en esta base.
- **Cualquier otro contrato, cifra de C25 o entrada del catálogo de errores.** Si ves otro defecto, lo anotas en la bitácora como candidata.
- **Las pruebas existentes.** Única excepción: si una prueba de C2 o de C25 fija la forma exacta de `entrada` o los `used_in` de esas dos entradas, se ajusta solo a E-16 y E-17, y se nombra en la bitácora.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.** Si necesitas tocarlos, paras y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-16, E-17 y P-T15-5.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 9 y 14 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.4 y §5.
- `docs/loop/revisiones/U01-T15/ronda-2.md`: F-01.
- `contracts/queues/runs.v2.yaml`, `contracts/limits.v1.yaml` y `contracts/analyzer/v1/entrada.schema.json` (solo lectura).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: lecturas de vuelta y validación real del mensaje.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/contracts/test_correcciones_t15c.py --no-cov
  ```
  Esperado: verde, con el caso de 20000 caracteres aceptado y el de 20001 rechazado por el validador.

- [ ] **CA-2**: la suite completa sigue en verde.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-3**: el catálogo de límites sigue válido, y su diff solo toca dos `used_in`.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov
  ```
  ```bash
  git -C /workspace/.worktrees/U01-T15c diff feat/b1-contratos...HEAD -- contracts/limits.v1.yaml
  ```
  Esperado: verde, y el diff solo cambia los `used_in` de `turn_max_chars` y `run_message_max_bytes`.

- [ ] **CA-4**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T15c diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: un subconjunto de `contracts/queues/runs.v2.yaml`, `contracts/limits.v1.yaml`, `contracts/tests/contracts/test_correcciones_t15c.py`, las pruebas de C2 o C25 que ajuste la excepción de «Fuera» (cada una nombrada en la bitácora) y `docs/loop/bitacoras/U01-T15c.md`.

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

1. Escribe primero `test_correcciones_t15c.py`.
2. Haz su commit, corre el rojo contra `feat/b1-contratos` y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T15c.md`.
3. Haz las tres correcciones hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** el texto de los turnos que viaja en la cola queda acotado (§4.4), así que ningún campo abierto deja salir testimonio.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`): el mensaje de prueba usa texto sintético.

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `fix(contracts): tope del texto de los turnos y del mensaje en C2 (U01-T15c)`. Sin signo de dólar en el mensaje.
