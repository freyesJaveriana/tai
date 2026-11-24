# U01-T24: huellas aprobadas de C6 fijadas en el código

> El orquestador llenó esta tarea a partir del cambio 05 de la app, §2 (decisión E-32 del humano, 2026-11-24). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que precisa:** paso 5 (F7) y paso 6 (copia de C6), en `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T18d, que también toca `tests/conftest.py`. Va en la ola 10b, en paralelo con T20 y T25 (E-33).

---

## Alcance

**Dentro:**

> **El defecto.** Hoy la copia de C6 (`contracts/analyzer/v1/`) se compara solo contra `SHA256SUMS`, en `tests/conftest.py` (`check_c6_copy`, F7) y en `tests/contracts/test_analyzer_copy.py`. Un PR que cambie un esquema y recalcule `SHA256SUMS` pasa sin que nada falle. Es el hallazgo R-04 de la revisión 2 del Functional Design de U1. El cambio 05 pide comparar el **contenido** con la versión aprobada en el repositorio principal.
>
> **1. Constantes.** Las huellas aprobadas quedan como constantes en el código de pruebas, en un solo sitio que importen los dos usos. Por ejemplo, `HUELLAS_APROBADAS_C6` en `tests/conftest.py`:
> - `entrada.schema.json`: `28606016b51dd19d873e7ee8fae7d959f0a98c225ab2690d0fd935296c3c41a8`
> - `salida.schema.json`: `e1528b7de1db9b5a3ca8c6f3e8eacb0eeec92522423014d6644ab39918bedeaf`
>
> Un comentario junto a las constantes dice que solo cambian con un cambio de contrato aprobado en el principal, es decir, con una v2 nueva.
>
> **2. F7 contra las constantes.** `check_c6_copy` informa un problema, con el mensaje de F7 (`MENSAJE_F7`), si el SHA-256 de los bytes de un esquema no es su constante, o si una línea de `SHA256SUMS` no coincide con la constante. Sigue comprobando todo lo que ya comprueba. `SHA256SUMS` se queda.
>
> **3. Pruebas, con rojo primero.** En `tests/contracts/test_analyzer_copy.py`, sin renombrar ni quitar ninguna prueba existente:
> - **Positivas:**
>   - los bytes de cada esquema dan su constante;
>   - las dos líneas de `SHA256SUMS` dan las mismas constantes.
> - **Control negativo (el hueco de R-04):** una copia en `tmp_path` con un esquema alterado y su `SHA256SUMS` recalculado. `check_c6_copy` devuelve un problema que nombra ese esquema.
> - **Control negativo:** una copia con los esquemas intactos y un `SHA256SUMS` con otra huella también devuelve un problema.
>
> **4. Versión de C5 (K-57, E-33).** `contracts/queues/speech.v2.yaml` declara `info.version: 1.2.0`, aunque su nombre dice v2.
> - **El contrato:** pasa a `info.version: 2.0.0`. Es la única línea que cambia en C5.
> - **La prueba:** la de versión semántica de E-28 (`contracts/tests/checks/test_fixture_coverage.py`, P-T18-20) exige además que la mayor coincida con el `.vN` del **nombre del archivo** en todo contrato propio que lo lleve, no solo con el `$id`.
> - **Controles negativos**, copias en memoria con la mayor distinta del nombre:
>   - una de C5 con `1.2.0`;
>   - una de un esquema JSON.
> - **El rojo:** la prueba extendida, sobre el C5 actual, falla nombrando `queues/speech.v2.yaml`.
> - **`VERSION_SEMANTICA`:** si hoy admite ceros a la izquierda (`01.0.0`), los rechaza, con su caso negativo.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si las huellas de la copia del árbol no son las dos constantes de arriba.
- Si otra prueba usa `check_c6_copy` o `SHA256SUMS` sobre una copia alterada y cambia su resultado. Por ejemplo, `tests/guards/test_autonomia_05.py:138-145` y `tests/test_validators.py`.
- Si una guardia fusionada falla por el cambio, por ejemplo las listas de `fixture_coverage` que citan pruebas de BR1.7.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **`contracts/analyzer/`:** ni los esquemas, ni `SHA256SUMS`, ni los *fixtures*. Es la copia aprobada (BR1.8, PD-4).
- **`src/` y los módulos guardia (`checks/`).** Si la constante `VERSION_SEMANTICA` vive en `src/` y no en la prueba, para y avisa.
- **`pyproject.toml`, `uv.lock` y `hatch_build.py`.**
- **Las pruebas existentes.** Solo se añaden las nuevas en `test_analyzer_copy.py` y se extiende la prueba de versión de E-28 en `test_fixture_coverage.py`.
- **Cualquier otro contrato**, aparte de la línea de versión de C5.

**Parada adicional:** si algún código, prueba o *fixture* lee la versión `1.2.0` de C5, para y avisa.

---

## Archivos de contexto

- `/insumos/app/cambios/veridicus-05_etiquetas_y_repositorio_publico.md` §2: solo lectura.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-32.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.7 y BR1.8.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/reviews/review-02.md`: R-04.
- `contracts/tests/conftest.py` y `contracts/tests/contracts/test_analyzer_copy.py`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: las pruebas de la copia.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/contracts/test_analyzer_copy.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: la suite completa.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-3**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T24 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: `contracts/tests/conftest.py`, `contracts/tests/contracts/test_analyzer_copy.py`, `contracts/tests/checks/test_fixture_coverage.py`, `contracts/queues/speech.v2.yaml` (una sola línea) y `docs/loop/bitacoras/U01-T24.md`.

- [ ] **CA-4**: tipos, *lint* y la CI del repositorio.
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

1. Escribe primero las pruebas nuevas.
2. Haz su commit y corre el rojo contra `feat/b1-contratos`. Debe fallar el control negativo de R-04, porque hoy `check_c6_copy` acepta la copia alterada. Pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T24.md`. Si es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.
3. Implementa hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada. Si el rojo necesita una constante que aún no existe, usa un esqueleto de firma.

---

## Reglas de la app que aplican

- **BR1.7 y BR1.8:** la copia de C6 es la aprobada, idéntica byte a byte.
- **ADR-017:** el contrato común es una fuente externa.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `test(contracts): huellas aprobadas de C6 fijadas en F7 (U01-T24)`. Sin signo de dólar en el mensaje.
