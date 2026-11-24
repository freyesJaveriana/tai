# U01-T23: documentación, glosario, etiqueta `contracts-v` y línea de instalación

> El orquestador llenó esta tarea a partir del paso 25 del plan y del cambio 05 de la app, §1 (E-32), que completa V-3 de `veridicus-03`. Por E-41 junta en una sola tarea lo que antes eran T23 y T26. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que implementa:**
- el paso 25;
- la precisión del paso 24 para el disparador por etiqueta;
- la definición de terminado del Bolt (BR12.2, con la precisión de E-32).

Todos están en `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`.
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T22, que deja `contracts-level0.yml` y los V-* como quedan en la CI. Es la última tarea antes del PR del Bolt a `main`.

---

## Alcance

**Precisión de BR12.2 (E-32).**
- **La etiqueta** pasa de `vX.Y.Z` a `contracts-v` más la versión de `[project].version` de `contracts/pyproject.toml`, que hoy es `0.1.0`. La versión del paquete es **igual** a la de su etiqueta.
- **La versión del contrato** es otra cosa y no cambia con el paquete: `contrato: "1.0.0"` en C6, `x-veridicus-version` o `info.version` en cada contrato propio.

**Dentro:**

> **1. `contracts/README.md`, en español.** Lleva estas secciones:
> - **Inventario de contratos.** Cada uno con su ID (C1, C2, …), su archivo y su versión. Se lee del árbol y del registro, no se inventa.
> - **Cómo cambiar un contrato (F5).**
>   - Versión semántica, con la mayor igual al `.vN` del nombre (E-28 y E-33).
>   - *Fixtures* positivos y negativos.
>   - Regenerar con `--write` lo que corresponda: `gen_ts`, `gen_jcs_vectors` y `security_surface`.
> - **La copia de C6 (F7).** Es la copia aprobada del principal y no se edita. Sus huellas están fijadas en `tests/conftest.py` (`HUELLAS_APROBADAS_C6`). Una versión nueva entra solo con un cambio aprobado en el principal (ADR-017).
> - **Uso desde un servicio.** Un ejemplo corto de `limits.load`, otro de `profiles.validate` y otro de `registry`. Se escriben con las firmas reales del paquete y con datos sintéticos.
> - **Comandos V-\*.** Cada uno tal como aparece en la tabla de V-* del plan y en `contracts-level0.yml`.
> - **Instalar desde otro repositorio.** Es la línea que `sistema` copia tal cual, con el repositorio, `tag` y `subdirectory`:
>   - **Forma `[tool.uv.sources]`:** `veridicus-contracts = { git = "https://github.com/freyesJaveriana/tai", tag = "contracts-v0.1.0", subdirectory = "contracts" }`.
>   - **Equivalente con `uv add`.**
>   - **Antes de escribirla,** verifica la sintaxis con `uv add --help` sin red, o con la documentación oficial de uv.
>
> **2. Glosario de identificadores**, en el mismo README, con su traducción del PRD:
> - `cancel_token` y `view_outdated` (NFRD-U7-11);
> - `review_report`, «reporte de revisión»;
> - `review_suggestion`, «sugerencia de revisión»;
> - `undocumented_fact`, «Hecho No Documentado».
>
> Ningún término se traduce de dos formas (`team.md`, Code Style).
>
> **3. Docstrings en español** donde falten. Van en estos sitios:
> - `loaders` y `validators`;
> - cada función pública pura;
> - cada módulo de `checks/`, con la regla que protege (BR o NFR).
>
> Solo cambian docstrings y comentarios, nunca el código.
>
> **4. Herramienta `src/veridicus_contracts/tools/check_tag.py`**, junto a las de T19 y T21. Se corre con `python -m veridicus_contracts.tools.check_tag` y usa solo la biblioteca estándar y `tomllib`, sin red. Lee `pyproject.toml` del directorio de trabajo (`uv run --directory contracts`), o del que indique `--pyproject RUTA`.
> - **Sin `--tag`:** imprime la etiqueta esperada, `contracts-v<versión>`, y termina con 0.
> - **Con `--tag ETIQUETA`:** termina con 0 solo si la etiqueta es exactamente la esperada. Si no, termina con 1 y un mensaje en español que nombra las dos.
> - **Versión sin forma semántica:** termina con 1 si `[project].version` no tiene la forma `MAYOR.MENOR.PARCHE`.
>
> **5. La CI al etiquetar.** En `.github/workflows/contracts-level0.yml`, el disparador suma `push` de etiquetas `contracts-v*`. Un paso, solo en ese evento, corre `check_tag --tag` con el nombre de la referencia del evento.
> - Mantiene `permissions: contents: read` y las acciones fijadas por SHA.
> - La guardia `ci_workflows` sigue en verde.
> - Nada del *workflow* escribe ni publica.
>
> **6. Pruebas:**
> - **`contracts/tests/test_readme.py`:**
>   - el README existe y su glosario tiene los cinco términos, con un control negativo: un README en memoria sin uno de ellos falla;
>   - la sección de instalación existe, y su etiqueta es la que imprime `check_tag`, para que al subir la versión el README no se quede atrás.
> - **`contracts/tests/tools/test_check_tag.py`:**
>   - pasa la etiqueta igual;
>   - falla otra versión;
>   - falla la forma vieja, `v0.1.0`;
>   - falla otro prefijo, como `analyzer-v0.1.0`;
>   - falla una versión sin forma semántica, en un `pyproject.toml` de prueba dentro de `tmp_path`;
>   - sin `--tag`, imprime la esperada.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si una función o un comando que debe citar el README no existe con ese nombre en el paquete o en el plan.
- Si escribir un docstring te obliga a cambiar código para que tenga sentido.
- Si una guardia de T18 rechaza algo de esta tarea: `fixture_coverage`, `loader_usage`, `package_map` o `ci_workflows`. Por ejemplo, el README dentro o fuera de la rueda, o el disparador nuevo.
- Si la sintaxis de uv para `git`, `tag` y `subdirectory` no es la de arriba.
- Si hace falta cambiar la versión `0.1.0` del paquete.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Poner la etiqueta.** La pone el humano al fusionar el PR del Bolt (BR12.2).
- **Las etiquetas de U10 y U11** (`anonymizer-v…` y `analyzer-v…`).
- **El código de `src/`**, salvo los docstrings, los comentarios y la herramienta nueva `check_tag.py`.
- **Los contratos, sus *fixtures* y `analyzer/`.**
- **`pyproject.toml` y `uv.lock`.** `pyproject.toml` solo se lee.
- **El resto del *workflow*, salvo el disparador y el paso de la etiqueta.** El `README.md` raíz tampoco se toca.

---

## Archivos de contexto

- `/insumos/app/cambios/veridicus-05_etiquetas_y_repositorio_publico.md` §1: solo lectura.
- `code-generation-plan.md`: los pasos 24 y 25 y la tabla de V-*.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: F5 y F7.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.5, BR12.1, BR12.2 y la regla que protege cada módulo de `checks/`.
- `decisiones-humano.md`: hasta E-41.
- `aidlc/spaces/default/memory/team.md`, sección Code Style: el glosario y el idioma.
- `contracts/src/veridicus_contracts/`, `contracts/pyproject.toml` y `.github/workflows/contracts-level0.yml`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: el README y la herramienta.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_readme.py tests/tools/test_check_tag.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: la etiqueta esperada.
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.check_tag --tag contracts-v0.1.0
  ```
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.check_tag --tag v0.1.0
  ```
  Esperado: código 0 con la primera y código 1 con la segunda.

- [ ] **CA-3**: la suite completa (V-SUITE).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  Esperado: verde, con ≥ 80 % de cobertura y sin casos omitidos nuevos. La guardia `ci_workflows` va incluida.

- [ ] **CA-4**: los docstrings no cambian el código.
  ```bash
  git -C /workspace/.worktrees/U01-T23 diff feat/b1-contratos...HEAD --stat -- contracts/src
  ```
  Esperado: en la bitácora, una revisión archivo por archivo de que, salvo `tools/check_tag.py`, solo cambian docstrings y comentarios. Puede ser, por ejemplo, una comparación del AST de cada archivo antes y después, sin docstrings, con un guion del scratchpad.

- [ ] **CA-5**: tipos, *lint*, YAML y la CI del repositorio.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  bash scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T23
  ```
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T23
  ```
  Esperado: sin errores, `0 apariciones` y código 0. Además, V-YAML del plan con código 0.

- [ ] **CA-6**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T23 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado, solo estos archivos:
  - `contracts/README.md`;
  - `contracts/tests/test_readme.py` y `contracts/tests/tools/test_check_tag.py`;
  - `contracts/src/veridicus_contracts/tools/check_tag.py`;
  - archivos de `contracts/src/` donde solo cambian docstrings;
  - `.github/workflows/contracts-level0.yml`, solo el disparador y un paso;
  - `docs/loop/bitacoras/U01-T23.md`.

---

## Plan de pruebas

1. Escribe primero `test_readme.py` y `test_check_tag.py`, con un esqueleto de firma de `check_tag.py`.
2. Haz su commit y corre el rojo contra `feat/b1-contratos`. Debe fallar por la regla, es decir, porque falta el README, el glosario o la sección, o porque la etiqueta no es la esperada. No debe fallar por un error de importación.
3. Pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T23.md`. Si es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.
4. Implementa hasta el verde.
5. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

---

## Reglas de la app que aplican

- **BR1.5:** cada contrato documenta su versión y cómo cambia.
- **BR12.1:** el paquete es instalable.
- **BR12.2**, con la precisión de E-32: la etiqueta es `contracts-vX.Y.Z`.
- **NFR14.1:** la documentación va en español.
- **Code Style (`team.md`):** los identificadores van en inglés y los textos y comentarios en español, con un glosario único.
- **AUTONOMIA-01:** la CI no despliega ni tiene credenciales.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`): los ejemplos del README no llevan nombres ni testimonio. El repositorio es público: nada de `/insumos`.

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- **Bash:**
  - Solo caracteres ASCII imprimibles.
  - Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
  - Los `${{ … }}` del *workflow* se escriben con Write, nunca por Bash.
- Conventional Commits en español con alcance `contracts`. Ejemplos: `docs(contracts): README, glosario y docstrings (U01-T23)` y `feat(contracts): etiqueta contracts-v y linea de instalacion (U01-T23)`.
