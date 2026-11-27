# U02-T01: la imagen de la CLI para el Job de la demo

**Unidad:** U2 `platform`   **Bolt:** B4-demo   **Rama base:** `bolt/b4-demo` (desde `main` en `31b431e`)
**Pasos del plan que cubre:** pasos 1, 2 y 3 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/platform/code-generation/code-generation-plan.md` (aprobado el 2026-11-26), con las precisiones DP-04 y DP-07.
**Historias:** la demo en Kubernetes de B4-demo, sobre US11.3 (anonimizador delante, fallo cerrado) y US3.4 (citas verificadas), sin cambiar su comportamiento.
**Depende de:** ninguna.
**Riesgo (ML-4):** alto. Empaqueta la clave del proveedor y el anonimizador, y es la demo del sábado. Revisa `revisor` con `opus`.

---

## Alcance

**Entra:**

> - **Paso 1, la entrada sintética:**
>   - `deploy/demo-analyzer/entrada/contradiccion.json`: una entrevista C6 de entrada sintética con **una contradicción sembrada** sobre un hecho central, entre dos turnos de la compareciente;
>   - `deploy/demo-analyzer/entrada/coherente.json`: un relato **coherente**, sin contradicciones;
>   - los dos inventados para la demo, en español, con nombres y lugares ficticios, y nada del piloto ni de `/insumos`. Puedes partir de `make_entrada` y `default_turns` de `libs/incoherence_analyzer/tests/support.py` (solo leerlo; esa ruta está congelada).
> - **Paso 2, el punto de entrada de la demo:**
>   - un paquete nuevo `deploy/` con su `pyproject.toml` y su `uv.lock`, que depende de `veridicus-incoherence-analyzer[cli]` por ruta (`../libs/incoherence_analyzer`, **sin** modo editable) y de las mismas rutas hermanas que usa ese paquete;
>   - `deploy/src/veridicus_demo/entrypoint.py` con `main()`, que:
>     - llama en proceso a `run(argv, env, transport=None)` de `veridicus_incoherence_analyzer.cli.main` con `analyze <dir-entrada> --perfil demo-anthropic --salida <dir-salida>`, tomando las rutas de `VERIDICUS_DEMO_ENTRADA` (por omisión `/entrada`) y `VERIDICUS_DEMO_SALIDA` (por omisión `/salida`);
>     - lee después cada `<nombre>.salida.json` y escribe en stdout, por archivo, una línea con el nombre, el `estado` y el número de hallazgos y, por cada hallazgo, `hecho`, `tipo`, y de `cita_a` y `cita_b` su turno y su texto;
>     - termina con el mismo código que la CLI, y si la CLI no dio 0, no lee ninguna salida ni imprime hallazgos;
>     - nunca imprime la clave, el entorno, la transcripción completa ni turnos que no sean una cita;
>   - una costura de pruebas igual que la de la CLI: `main_with(argv, env, *, transport=None, stdout=...)`, para inyectar el `FakeTransport` y capturar stdout.
> - **Paso 3, la imagen:**
>   - `deploy/images/analyzer-cli/Dockerfile`, en varias etapas:
>     - toda imagen `FROM` es `python:3.12-slim@sha256:<digest>`. El digest debe ser real; si no puedes obtenerlo sin red, deja `REEMPLAZAR_DIGEST` y **repórtalo**: el humano lo trae con `!`;
>     - la etapa de construcción usa `uv` (fijado por versión y digest) con `uv sync --frozen --no-dev --no-editable` del paquete `deploy/`;
>     - la etapa final copia solo el entorno virtual, corre con `USER 10001:10001` y su `ENTRYPOINT` es `["/app/.venv/bin/python", "-m", "veridicus_demo.entrypoint"]`;
>     - no copia `.env`, `resultados-locales/`, `tests/`, `.git` ni `docs/`;
>   - un `.dockerignore` en la raíz (el contexto del *build* es la raíz del repositorio), que excluye todo salvo `contracts/`, `libs/` y `deploy/`, y dentro de ellos `tests/`, `.venv/`, `resultados-locales/`, `__pycache__/` y `coverage.json`.

**Fuera** (recházalo aunque se vea roto):

- **Los manifiestos de Kubernetes, las políticas y los scripts del humano** son de U02-T02 (pasos 4 a 7). Esta tarea no crea `kustomization.yaml`, `Job` ni `NetworkPolicy`.
- **Los workflows de CI** son de U02-T03 (pasos 8 y 9).
- **No se toca nada de `libs/` ni de `contracts/`.** Si la CLI no puede correr fuera del repositorio (por ejemplo, porque busca `resultados-locales/` o exige que la salida esté ignorada por Git, o porque el *prompt* o un contrato no viaja como dato del paquete al instalar sin modo editable), **para y repórtalo** con la línea exacta: lo decide el orquestador.
- **No se construye la imagen ni se usa la red** (salvo `uv lock` y `uv sync`). El *build* real lo hace la CI.

---

## Archivos de contexto

- El plan aprobado: pasos 1 a 3, DP-04, DP-07, el mapa AUTONOMIA y los riesgos.
- `libs/incoherence_analyzer/README.md`: el uso, las variables de entorno y los códigos de salida.
- `libs/incoherence_analyzer/src/veridicus_incoherence_analyzer/cli/main.py` (`run`, `NOTICE_FILE`, los nombres de salida) y `cli/results_dir.py`.
- `libs/incoherence_analyzer/tests/support.py` y `tests/e2e/test_cli_fake.py`: cómo se arma una entrada C6 y cómo se usa el `FakeTransport` con el `Anonymizer` real.
- `libs/incoherence_analyzer/pyproject.toml`: las dependencias por ruta.
- `contracts/`: el esquema C6 de entrada, para validar el paso 1.
- `.github/workflows/repo-level0.yml` y `scripts/check-no-*.sh`: las guardias del repositorio que deben seguir en 0.

---

## Criterios de aceptación

Se corren desde la raíz del worktree `/workspace/.worktrees/U02-T01`.

- [ ] **CA-1 (paso 1):** las entradas son C6 válidas y sintéticas.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_entrada.py -q
  ```
  Se espera: código 0. La prueba valida cada archivo contra el esquema C6 de entrada de `contracts/`, exige al menos 6 turnos de la compareciente en cada uno, e incluye un control negativo: un turno sin `texto` debe fallar la validación.
- [ ] **CA-2 (paso 2):** el punto de entrada, con el doble del proveedor.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_entrypoint.py --cov=veridicus_demo --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Se espera: código 0 y 100 % de ramas, con al menos estos casos:
  - con un hallazgo guionado sobre `contradiccion.json`, stdout trae su `hecho`, su `tipo` y las dos citas con su turno;
  - con `coherente.json` y respuesta sin hallazgos, stdout dice 0 hallazgos;
  - sin `VERIDICUS_ANTHROPIC_API_KEY`, el código es 3, el transporte registra **0 llamadas** y stdout no trae hallazgos;
  - con el anonimizador forzado a fallar, ninguna llamada sale y el código no es 0;
  - la clave canario `sk-sintetico-canario-7f3a91c2d4e5` y una cadena canario puesta en un turno que no es cita no aparecen en stdout ni en stderr.
- [ ] **CA-3 (paso 3):** el Dockerfile y el `.dockerignore`.
  ```bash
  uv run --frozen --offline --directory deploy pytest tests/test_dockerfile.py -q
  ```
  Se espera: código 0. La prueba lee el Dockerfile y exige:
  - un `@sha256:` en cada `FROM` (o `REEMPLAZAR_DIGEST` marcado como `xfail` estricto con su motivo, si el digest no se pudo obtener);
  - ningún `latest`;
  - el `USER` final numérico y distinto de 0;
  - ningún `COPY` de `.env`, `tests` ni `resultados-locales`;
  - un `.dockerignore` que excluye `.env`, `**/tests`, `**/.venv` y `resultados-locales`.

  Incluye un control negativo por regla: un Dockerfile de prueba en `tmp_path` con `FROM python:3.12-slim` sin digest, y otro con `USER root`, hacen fallar la comprobación.
- [ ] **CA-4:** tipos, *lint* y formato del paquete nuevo.
  ```bash
  uv run --frozen --offline --directory deploy mypy --strict src tests
  ```
  ```bash
  uv run --frozen --offline --directory deploy ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory deploy ruff format --check .
  ```
  Se espera: código 0 en los tres.
- [ ] **CA-5:** nada retrocede y las guardias del repositorio siguen limpias.
  ```bash
  uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli pytest tests/e2e --no-cov -q
  ```
  ```bash
  bash /workspace/.worktrees/U02-T01/scripts/check-no-datos-personales.sh /workspace/.worktrees/U02-T01
  ```
  ```bash
  bash /workspace/.worktrees/U02-T01/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U02-T01
  ```
  ```bash
  bash /workspace/.worktrees/U02-T01/scripts/check-no-insumos.sh /workspace/.worktrees/U02-T01
  ```
  ```bash
  git -C /workspace/.worktrees/U02-T01 diff --stat origin/bolt/b4-demo -- libs contracts
  ```
  Se espera:
  - pytest con código 0;
  - los tres scripts imprimen `0 apariciones`;
  - el `diff --stat` sale vacío;
  - `grep -rnoP "sk-[A-Za-z0-9_-]{6,}"` sobre `deploy/` solo encuentra la clave canario.

---

## Casos sonda obligatorios (ML-11)

El revisor va a atacar estos casos. Cada uno lleva una prueba que lo cubre:

1. **La clave en un mensaje de error:** una excepción inesperada dentro de `run` no debe imprimir el entorno ni la clave. El punto de entrada no puede tener un `except` que haga `print(env)` o `repr` del entorno.
2. **Salida parcial:** si la CLI termina con 4 (un archivo en `error`), el punto de entrada imprime el estado `error` de ese archivo y **cero** hallazgos de ese archivo (AUTONOMIA-05: nunca un resultado parcial).
3. **Un archivo de salida que falta o está corrupto:** con código 0 pero sin `.salida.json`, el punto de entrada termina distinto de 0, con un mensaje fijo en español y sin leer la entrada.
4. **Una cita que no está en la transcripción:** el punto de entrada **no** revalida ni recorta citas: imprime lo que salió de la CLI, que ya las verificó. Una prueba lo deja explícito.
5. **Vocabulario prohibido:** las líneas que añade el punto de entrada (rótulos fijos) pasan `scan` de `veridicus_integrity_policy` sin hallazgos (AUTONOMIA-03).

---

## Plan de pruebas (Testing Contract: custom)

1. **Primero, en rojo:** `tests/test_entrypoint.py` con los casos de AUTONOMIA-04 y 05 de CA-2 y los casos sonda 1 y 2, y `tests/test_entrada.py`. Haz un commit del rojo con el mensaje `test(deploy): rojo del punto de entrada de la demo` y anota su SHA en la bitácora.
2. Implementa el punto de entrada hasta el verde.
3. Escribe el Dockerfile y el `.dockerignore`, y luego `tests/test_dockerfile.py` con sus controles negativos.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** el anonimizador va delante de toda llamada, y con clave ausente o anonimizador caído hay 0 llamadas (CA-2). La clave nunca va en la imagen.
- **AUTONOMIA-05:** sin resultado parcial (caso sonda 2).
- **AUTONOMIA-03:** sin vocabulario de veracidad en los rótulos (caso sonda 5).
- **Solo datos sintéticos.** NEVER nada del piloto ni de `/insumos`.
- **team.md, Deployment:** imagen base fijada por digest, sin root, nunca `latest`.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U02-T01.md`, de una página como máximo. Debe incluir:
  - el SHA del rojo;
  - la tabla de viñetas de los pasos 1 a 3, cada una con su prueba (ML-14);
  - el digest usado, o el aviso de que falta;
  - cualquier supuesto sobre cómo corre la CLI fuera del repositorio.
- **Bash:** un comando simple por llamada, con rutas absolutas y sin `bash -c`, `time`, *pipes* ni redirecciones. Para buscar una comilla invertida usa `grep -P` con `\x60`.
- **Red:** ninguna, salvo `uv lock` y `uv sync`. Si `uv lock --offline` no resuelve por falta de caché, para y repórtalo: el humano lo corre con `!`.
- **Commits:** en Conventional Commits en español, con alcance `deploy`.
- **Plan aprobado:** no lo edites.
- **Al terminar:** haz push de `tarea/U02-T01` y vuelve con tu informe. No fusionas tú.
