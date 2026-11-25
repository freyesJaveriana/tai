# U01-T18c: versión semántica en los contratos propios

> El orquestador llenó esta tarea a partir de la decisión E-29 del humano (2026-11-24), tomada tras la parada de la ronda 3 de U01-T18. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que corrige:** los pasos que crearon estos ocho contratos, según `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: C7 (paso 10), C13 (paso 11), C18 y los esquemas de perfiles y precios (paso 12), C19 (paso 13) y el catálogo de errores (paso 8). No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** nada pendiente. Se fusiona **antes** que U01-T18, que luego rebasa sobre ella.

---

## Alcance

**Dentro:** las correcciones de abajo, ni una más. La lista sale de la parada de la ronda 3 de T18 (`docs/loop/bitacoras/U01-T18.md` de la rama `tarea/U01-T18`).

> **Regla que se cumple:** BR1.1 de `construction/contracts/functional-design/rules.md:35-43`: «Todo contrato tiene versión semántica… SI falta la versión o no tiene la forma MAYOR.MENOR.PARCHE ENTONCES el contrato… es inválido».
>
> **1. Siete esquemas JSON** reciben en su raíz `x-veridicus-version: "N.0.0"`, donde `N` es la versión mayor de su `$id` y de su nombre de archivo (`.vN`). Es una cadena entre comillas. La clave lleva prefijo `x-` para que los validadores de JSON Schema la traten como anotación y no cambie qué documentos se aceptan:
> - `contracts/cli/report.schema.v2.yaml` (C19)
> - `contracts/integrity/review-suggestion.v2.json` (C7)
> - `contracts/model_calls/model-call.v1.yaml` (C13)
> - `contracts/profiles/effective-config.v1.yaml` (C18)
> - `contracts/profiles/prices.schema.v1.yaml`
> - `contracts/profiles/profile-base.schema.v1.yaml`
> - `contracts/profiles/profiles.schema.v1.yaml`
>
> **2. El catálogo de errores** `contracts/errors/error-codes.v2.yaml` pasa de `version: 2` (entero) a `version: "2.0.0"` (cadena).
> - Si algún código de `contracts/src/` o alguna prueba de `contracts/tests/` lee ese campo como entero, se ajusta solo esa lectura a la cadena nueva, y se nombra en la bitácora.
> - Si lo lee código fuera de `contracts/` (por ejemplo `libs/errors/`), para y avisa.
>
> **3. Pruebas, con rojo primero.** Un archivo nuevo, `contracts/tests/contracts/test_correcciones_t18c.py`:
> - **Lectura de vuelta:** cada uno de los siete esquemas lleva `x-veridicus-version` en forma `MAYOR.MENOR.PARCHE`, y su mayor coincide con el `.vN` del `$id`. El catálogo lleva `version: "2.0.0"`.
> - **Nada cambia para el validador:** los documentos y *fixtures* `accept` y `reject` que ya existen para estos contratos dan el mismo resultado que antes.
> - **Control negativo:** una copia en memoria de C7 con `x-veridicus-version: "3.0.0"` (mayor distinta del `$id`) da rojo, y otra con `"2.0"` también.
>
> Nada más en esos archivos: ni `$id`, ni `description`, ni `required`, ni otras propiedades. **La copia de C6 (`analyzer/v1/`) no se toca**: ya declara su versión (`contrato: const 1.0.0`).

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si alguna guardia fusionada (`report_closed`, `limits_match`, `naming`, `refs`, `synthetic` u otra) rechaza la clave `x-veridicus-version`.
- Si la huella de los contratos o una lista de `SHA256SUMS` exige regenerarse por el cambio y no hay un comando del plan que lo haga.
- Si encuentras otro contrato propio sin versión semántica que no esté en la lista.
- Si la versión mayor del `$id` y la del nombre del archivo no coinciden en alguno de los siete.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **C6** (`contracts/analyzer/v1/`).
- **Los módulos guardia** (`checks/`) y sus pruebas. La prueba general de BR1.1 sobre todos los contratos la hace T18 (E-28).
- **Cualquier otro contrato, campo o entrada del catálogo.**
- **Las pruebas existentes.** Única excepción: una prueba que lea `version` del catálogo como entero se ajusta solo a esta tarea, y se nombra en la bitácora.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.**

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-28 y E-29.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md` y `unit-test-instructions.md`.
- `/workspace/.worktrees/U01-T18/docs/loop/bitacoras/U01-T18.md`: la parada de la ronda 3, solo lectura.
- Los ocho contratos de la lista (solo lectura, salvo lo que cambia).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: lecturas de vuelta y resultado del validador sin cambios.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/contracts/test_correcciones_t18c.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: la suite completa sigue en verde, incluidas las guardias.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-3**: el diff de cada contrato solo añade la versión.
  ```bash
  git -C /workspace/.worktrees/U01-T18c diff feat/b1-contratos...HEAD -- contracts/cli contracts/integrity contracts/model_calls contracts/profiles contracts/errors
  ```
  Esperado:
  - en cada uno de los siete esquemas, una sola línea añadida (`x-veridicus-version`);
  - en el catálogo, una sola línea cambiada (`version`).

- [ ] **CA-4**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T18c diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado:
  - los ocho contratos;
  - `contracts/tests/contracts/test_correcciones_t18c.py`;
  - las lecturas que ajuste la excepción de «Fuera», cada una nombrada;
  - `docs/loop/bitacoras/U01-T18c.md`.

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

1. Escribe primero `test_correcciones_t18c.py`.
2. Haz su commit, corre el rojo contra `feat/b1-contratos` y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T18c.md`. Si es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.
3. Haz las correcciones hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada.

---

## Reglas de la app que aplican

- **BR1.1:** versión `MAYOR.MENOR.PARCHE` en todo contrato.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `fix(contracts): version semantica en siete esquemas y el catalogo (U01-T18c)`. Sin signo de dólar en el mensaje.
