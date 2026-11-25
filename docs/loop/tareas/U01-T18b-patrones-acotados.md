# U01-T18b: patrones acotados en los contratos fusionados

> El orquestador llenó esta tarea a partir de la decisión E-23 del humano (2026-11-24), tomada tras la parada de la ronda 1 de U01-T18. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que corrige:** pasos 9 (C2, C3 y C5), 12 (C18), 13 (C21 y la ruta interna de voz) y 14 (C25) de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T17b (PR #23), fusionada, porque toca los mismos tres archivos de colas. Se fusiona **antes** que U01-T18, que luego se rebasa sobre ella.

---

## Alcance

**Dentro:** las correcciones de abajo, ni una más. La lista sale de la bitácora de T18 (`docs/loop/bitacoras/U01-T18.md`, sección «PARADA», en la rama `tarea/U01-T18`).

> **1. Versiones y tokens sin tope.** Cada uno de estos campos conserva su `pattern` y recibe `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`, la cifra existente de C25 que ya usan C19 y C5 para tokens del mismo tipo (E-15):
> - C21 `api/anonymizer-proxy.v1.yaml`: `schema_version`;
> - `api/speech-internal.v1.yaml` (ruta interna de voz): `template_version`;
> - C18 `profiles/effective-config.v1.yaml`: `analyzer_version`;
> - C2 `queues/runs.v2.yaml`, C3 `queues/results.v2.yaml` y C5 `queues/speech.v2.yaml`: `schema_version` de `RunRequested`, `RunResult`, `AudioToTranscribe` y `TranscriptResult`, y de cualquier otro mensaje de esos tres archivos que tenga el mismo defecto.
>
> **2. `code` con repetición anidada.** En `RunFailed` (C2), `ResultFailed` (C3) y `AudioFailed` (C5), el `pattern` de `code` pasa de `^[a-z][a-z_]*(\.[a-z][a-z_]*)+$` a `^[a-z][a-z_]*\.[a-z][a-z_]*$`. Es la forma `dominio.motivo` del catálogo (ningún `code` de `errors/error-codes.v2.yaml` tiene dos puntos) y la que ya usa la respuesta 422 de la ruta interna de voz. Los tres reciben también `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`. La respuesta 422 de la ruta interna de voz (`code`) recibe solo el tope y la marca.
>
> **3. C25 `used_in`.** En `contracts/limits.v1.yaml`, `report_token_max_chars` suma a `used_in` los contratos nuevos que la usan (C2, C3, C18 y C21; C5 y C19 ya están), en orden. La ruta interna de voz no tiene identificador `C<n>` (K-32) y no se añade. No cambia ninguna cifra ni ninguna otra entrada.
>
> Nada más en esos archivos: ni `description`, ni `required`, ni otras propiedades. **La copia de C6 (`analyzer/v1/`) no se toca**: sus patrones van a la lista de excepciones de `redos`, que hace T18 (E-23).
>
> **Pruebas, con rojo primero:** un archivo nuevo, `contracts/tests/contracts/test_correcciones_t18b.py`.
> - **Lectura de vuelta de la forma:** cada campo de la lista lleva `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`, y conserva su `pattern`. Los tres `code` de las colas llevan exactamente el patrón nuevo. Los `used_in` de `report_token_max_chars` son los esperados.
> - **Lectura de vuelta con el validador real:** para cada contrato, un mensaje o documento sintético mínimo válido se acepta con el validador del paquete y el registro de esquemas. Con un `schema_version` o un `code` de 129 caracteres que case con el patrón, se rechaza por `maxLength`. Con `run.timeout` se acepta un `code`, y con `run.timeout.extra` se rechaza.
> - **Control negativo:** una copia en memoria de C2 sin `maxLength` en `schema_version` da rojo en la prueba de forma.
> - Las guardias de límites (`limits_match` y `limits_catalog`) siguen en verde sobre los contratos reales.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si algún `code` real de los *fixtures* o del catálogo tiene más de un punto y el patrón nuevo lo rechazaría.
- Si `limits_match` o `limits_catalog` exigen otra cosa para la ruta interna de voz (por ejemplo, un `used_in` que no puede existir por K-32).
- Si encuentras en estos archivos otro patrón con el mismo defecto fuera de la lista. Lo anotas en la bitácora y lo corriges solo si es la misma clase (versión, token o `code` en estos seis archivos); en otro archivo, paras.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **C6** (`contracts/analyzer/v1/`): es el contrato común y no cambia.
- **El módulo `checks/redos.py` y sus pruebas** (T18), y cualquier otro módulo guardia.
- **Cifras nuevas en C25.** Si `report_token_max_chars` no sirve para un campo, paras y lo informas.
- **Cualquier otro contrato o entrada del catálogo de errores.**
- **Las pruebas existentes.** Única excepción: una prueba que fije la forma exacta de uno de estos campos o los `used_in` de `report_token_max_chars` se ajusta solo a E-23, y se nombra en la bitácora.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.**

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-15, E-23 y P-T17b-1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 9 a 14 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.4 y §4.5.
- `docs/loop/bitacoras/U01-T18.md` de la rama `tarea/U01-T18` (`/workspace/.worktrees/U01-T18/docs/loop/bitacoras/U01-T18.md`), sección «PARADA», solo lectura.
- Los seis contratos de la lista, `contracts/limits.v1.yaml` y `contracts/errors/error-codes.v2.yaml` (solo lectura, salvo lo que cambia).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: lecturas de vuelta y validación real.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/contracts/test_correcciones_t18b.py --no-cov
  ```
  Esperado: verde, con los casos de 129 caracteres y de `code` con dos puntos rechazados por el validador.

- [ ] **CA-2**: la suite completa sigue en verde, incluidas las guardias de límites.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-3**: el diff de C25 solo toca el `used_in` de `report_token_max_chars`.
  ```bash
  git -C /workspace/.worktrees/U01-T18b diff feat/b1-contratos...HEAD -- contracts/limits.v1.yaml
  ```
  Esperado: una sola línea cambiada.

- [ ] **CA-4**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T18b diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: un subconjunto de los seis contratos, `contracts/limits.v1.yaml`, `contracts/tests/contracts/test_correcciones_t18b.py`, las pruebas que ajuste la excepción de «Fuera» (cada una nombrada) y `docs/loop/bitacoras/U01-T18b.md`.

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

1. Escribe primero `test_correcciones_t18b.py`.
2. Haz su commit, corre el rojo contra `feat/b1-contratos` y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T18b.md`. Si es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.
3. Haz las correcciones hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada.

---

## Reglas de la app que aplican

- **NFR10.6 (§4.5):** ningún patrón de un contrato propio admite retroceso catastrófico ni una entrada sin tope.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `fix(contracts): patrones acotados en colas, C18, C21 y la ruta de voz (U01-T18b)`. Sin signo de dólar en el mensaje.
