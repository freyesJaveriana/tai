# U01-T26: etiqueta `contracts-v<semver>` y línea de instalación

> **Retirada (E-41, 2026-11-24).** Su contenido pasó a U01-T23 (`docs/loop/tareas/U01-T23-documentacion-y-glosario.md`). No se despacha.

> El orquestador llenó esta tarea a partir del cambio 05 de la app, §1 (decisión E-32 del humano, 2026-11-24), que completa V-3 de `veridicus-03`. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que precisa:** paso 24 (CI), paso 25 (README) y la definición de terminado del Bolt (BR12.2), en `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`.
**Historias que implementa:** ninguna propia.
**Depende de:**
- **T22:** existe `.github/workflows/contracts-level0.yml`.
- **T23:** existe `contracts/README.md`.
- **T19:** existe `contracts/tools/`.

Va después de T23, antes del PR del Bolt a `main`.

---

## Alcance

**Dentro:**

> **Precisión de BR12.2 (E-32).** La etiqueta pasa de `vX.Y.Z` a `<paquete>-v<semver>`. Para este paquete es `contracts-v` más la versión de `[project].version` de `contracts/pyproject.toml`, hoy `0.1.0`. La versión del paquete es **igual** a la de su etiqueta. La versión del contrato (`contrato: "1.0.0"` de C6, `x-veridicus-version` de cada esquema) es otra cosa y no cambia con el paquete.
>
> **1. Herramienta `contracts/tools/check_tag.py`**, con la biblioteca estándar y `tomllib`, sin red:
> - Sin argumentos, imprime la etiqueta esperada, `contracts-v<versión>`, y termina con 0.
> - `--tag ETIQUETA` termina con 0 solo si la etiqueta es exactamente la esperada. Si no, termina con 1 y un mensaje en español que nombra las dos.
> - Termina con 1 si `[project].version` no tiene la forma `MAYOR.MENOR.PARCHE`.
>
> **2. Pruebas** en `contracts/tests/tools/test_check_tag.py`, con rojo primero:
> - la etiqueta igual pasa;
> - otra versión falla;
> - la forma vieja `v0.1.0` falla;
> - otro prefijo (`analyzer-v0.1.0`) falla;
> - una versión sin forma semántica, en un `pyproject.toml` de prueba en `tmp_path`, falla;
> - sin argumentos, imprime la esperada.
>
> **3. La CI al etiquetar.** En `.github/workflows/contracts-level0.yml`, el disparador suma `push` de etiquetas `contracts-v*`. Un paso, solo en ese evento, corre `check_tag.py --tag` con el nombre de la referencia del evento. Mantiene `permissions: contents: read`, las acciones fijadas por SHA y la guardia `ci_workflows` en verde.
>
> **4. README.** `contracts/README.md` suma una sección «Instalar desde otro repositorio», con la línea que `sistema` copia tal cual: repositorio, `tag` y `subdirectory`.
> - **Forma:** la de `[tool.uv.sources]`, `veridicus-contracts = { git = "https://github.com/freyesJaveriana/tai", tag = "contracts-v0.1.0", subdirectory = "contracts" }`, junto con su equivalente en `uv add`.
> - **Antes de escribirla,** verifica la sintaxis con `uv add --help`, sin red, o con la documentación oficial de uv.
>
> Una prueba en `tests/test_readme.py` exige que la sección exista y que su etiqueta sea la que imprime `check_tag.py`. Así, al subir la versión, el README no puede quedarse atrás.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si `ci_workflows` u otra guardia rechaza el disparador o el paso nuevo.
- Si la sintaxis de uv para `git`, `tag` y `subdirectory` no es la de arriba.
- Si hace falta cambiar la versión `0.1.0` del paquete.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Poner la etiqueta.** La pone el humano al fusionar el PR del Bolt (BR12.2).
- **Las etiquetas de U10 y U11** (`anonymizer-v…`, `analyzer-v…`).
- **Los contratos, `src/` y `checks/`.**
- **`pyproject.toml`**, salvo leerlo.
- **El resto del README y del *workflow*.**

---

## Archivos de contexto

- `/insumos/app/cambios/veridicus-05_etiquetas_y_repositorio_publico.md` §1: solo lectura.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-32.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR12.1 y BR12.2.
- `contracts/pyproject.toml`, `contracts/README.md`, `.github/workflows/contracts-level0.yml` y `contracts/tests/test_readme.py`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: la herramienta y el README.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/tools/test_check_tag.py tests/test_readme.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: la etiqueta esperada.
  ```bash
  uv run --frozen --offline --directory contracts python tools/check_tag.py --tag contracts-v0.1.0
  ```
  Esperado: código 0. Con `--tag v0.1.0`, código 1.

- [ ] **CA-3**: la guardia de *workflows* y la suite completa.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde, sin casos omitidos nuevos.

- [ ] **CA-4**: tipos, *lint*, YAML y la CI del repositorio.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `Success: no issues found`, `All checks passed!` y `0 apariciones`, con código 0. Además, V-YAML del plan con código 0.

---

## Plan de pruebas

1. Escribe primero las pruebas, con un esqueleto de firma de `check_tag.py`.
2. Corre el rojo y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T26.md`. Si es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.
3. Implementa hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

---

## Reglas de la app que aplican

- **BR12.2,** con la precisión de E-32: etiqueta `contracts-vX.Y.Z`.
- **BR12.1:** paquete instalable.
- **AUTONOMIA-01:** la CI no despliega ni tiene credenciales.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas, en los comandos que corres. Usa `grep -P` con `\x24` y `\x60`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): etiqueta contracts-v y linea de instalacion (U01-T26)`.
