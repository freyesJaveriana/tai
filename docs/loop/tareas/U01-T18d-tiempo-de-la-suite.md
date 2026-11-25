# U01-T18d: la suite dentro de los 60 s de NFR2.1

> El orquestador llenó esta tarea a partir de la decisión E-33 (1) del humano (2026-11-24), que resuelve la candidata K-53. El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que corrige:** los pasos que ya están fusionados. La meta es que V-SUITE del paso 23 pase, según `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna.
**Depende de:** nada pendiente. Va en la ola 10, en paralelo con T19 y T21. Se fusiona antes que T24, que toca el mismo `tests/conftest.py`.

---

## Alcance

**La meta.** NFR2.1 y V-SUITE: `timeout 60 uv run --frozen --offline --directory contracts pytest` en verde, en ≤ 60 s y con ≥ 80 % de líneas. `addopts` ya añade `--disable-socket --cov=veridicus_contracts --cov-branch --cov-fail-under=80`. La meta de diseño es ≤ 20 s. Hoy la suite tarda unos 123 s sin cobertura, y `tests/checks` con cobertura, unos 270 s.

**Dentro:**

> **1. Medir primero.** Corre la suite con `--durations=40` y con cobertura. Pega en la bitácora, literal y completo:
> - el tiempo total;
> - las 40 pruebas más lentas;
> - la suma de tiempo por archivo de pruebas, calculada con un guion propio en el scratchpad a partir de la salida.
>
> Di dónde se va el tiempo antes de cambiar nada.
>
> **2. Acelerar sin quitar nada.** Estas palancas se permiten:
> - Construir una sola vez, con *fixtures* de sesión o de módulo o con `functools.cache`, lo que hoy se rehace en cada caso: el registro de esquemas, los validadores compilados, el recorrido del árbol de `contracts/`, la carga de YAML y las regex compiladas.
> - Mover a una *fixture* compartida el trabajo repetido entre casos parametrizados.
> - Quitar esperas, `sleep` o trabajo duplicado dentro de una prueba, sin cambiar qué afirma.
> - Optimizar el código de un módulo de `src/` cuando el tiempo está ahí, sin cambiar su comportamiento ni su interfaz pública. Así, el 100 % de ramas de los módulos guardia se mantiene.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si tras las palancas permitidas V-SUITE no baja de 60 s. Trae la medición de antes y de después, por archivo, y las salidas posibles.
- Si la única forma de bajar el tiempo es reducir ejemplos de Hypothesis, quitar o fusionar casos, cambiar un tope de tiempo de una prueba (como el de 1 s de ReDoS) o añadir una dependencia (`pytest-xdist` u otra).
- Si una *fixture* compartida haría que una prueba dependa del orden o del estado que deja otra.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Reducir lo que se prueba:**
  - el número de pruebas recogidas (`--collect-only -q`) no baja;
  - ningún `max_examples`, `deadline` ni tope de tiempo cambia;
  - ningún umbral de cobertura cambia.
- **`pyproject.toml` y `uv.lock`.** No cambian `addopts`, las dependencias ni los umbrales.
- **Los contratos y sus *fixtures*.**
- **Marcar pruebas para saltarlas** (`skip`, `xfail` o marcadores que las excluyan de la corrida por defecto).

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-33.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-requirements/security-requirements.md`: NFR2.1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: la tabla de V-* y el paso 23.
- `docs/loop/CANDIDATAS.md`: K-53.
- `contracts/tests/` y `contracts/src/veridicus_contracts/`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo, sin otras corridas en paralelo.

- [ ] **CA-1**: V-SUITE.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest
  ```
  Esperado: verde, con ≥ 80 % de líneas y código 0 antes del `timeout`. Pega el tiempo.

- [ ] **CA-2**: no se recogen menos pruebas.
  ```bash
  uv run --frozen --offline --directory contracts pytest --collect-only -q --no-cov
  ```
  Esperado: un número ≥ que el de `feat/b1-contratos` en la misma máquina. Pega los dos números.

- [ ] **CA-3**: los módulos guardia siguen al 100 % de ramas.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks
  ```
  Luego, `coverage report` sobre los módulos de `checks/`, con `--fail-under=100`.
  Esperado: verde y 100 %.

- [ ] **CA-4**: nada se aflojó.
  ```bash
  git -C /workspace/.worktrees/U01-T18d diff feat/b1-contratos...HEAD -- contracts/pyproject.toml contracts/uv.lock
  ```
  ```bash
  git -C /workspace/.worktrees/U01-T18d grep -n -E "max_examples|deadline=|skip|xfail" -- contracts/tests
  ```
  Esperado:
  - el diff sale vacío;
  - el `grep` devuelve las mismas líneas que en `feat/b1-contratos`.

- [ ] **CA-5**: tipos, *lint* y la CI del repositorio.
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

Esta tarea no añade pruebas nuevas. Su «rojo» es CA-1 sobre `feat/b1-contratos`:
- corta por el `timeout` o tarda más de 60 s;
- pega su salida **literal y completa** en `docs/loop/bitacoras/U01-T18d.md`;
- si es larga, redirígela a un archivo del scratchpad y anéxala con `cat >>`; no la condenses.

Después de cada palanca, vuelve a medir y anota en la bitácora cuánto bajó cada una.

---

## Reglas de la app que aplican

- **NFR2.1:** suite ≤ 60 s bajo `timeout 60`, sin red.
- **Testing Posture (`team.md`):** los umbrales nunca se bajan para que una compuerta pase, y ninguna prueba se reintenta para ocultar un fallo.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- **Edita solo con Edit o Write.** El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `perf(contracts): suite dentro de los 60 s de NFR2.1 (U01-T18d)`.
