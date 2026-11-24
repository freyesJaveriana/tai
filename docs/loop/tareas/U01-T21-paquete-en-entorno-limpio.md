# U01-T21: paso del paquete en entorno limpio (F9)

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 22 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T16, T17, T17b y T18, fusionadas (ola 9). T18 trae la lista de excepciones de `loader_usage` con `tools/check_package.py` (E-19). Ola 10, en paralelo con T19.

---

## Alcance

**Dentro:**

> **`contracts/src/veridicus_contracts/tools/check_package.py`** (security-design §4.16, functional-spec F9), ejecutable con `python -m veridicus_contracts.tools.check_package`. Hace, en este orden, y para en el primer fallo con un mensaje que nombra el paso y la ruta:
>
> 1. **Construye** con `uv build` la rueda y el `sdist` en un directorio temporal (D15).
> 2. **Compara la lista de la rueda con la tabla de rutas** de functional-spec §1. Falla si falta un esquema o catálogo de la tabla, o si aparece una ruta con `fixtures/`, `tests/`, `.env*`, `*.pem` o `*.key`.
>    - La tabla de rutas no se escribe dos veces: `check_package` la deriva de la configuración de la rueda en `contracts/pyproject.toml` (`include`, `sources` y `force-include`), que `tests/test_package_map.py` ya fija contra el árbol. Si no se puede derivar de ahí sin tocar `pyproject.toml`, para y lo informas.
> 3. **Crea un entorno nuevo** con `uv venv`, sin Redis, Kubernetes ni base de datos, e instala la rueda. Aquí hay red, solo para las dependencias.
> 4. **Ejecuta en ese entorno** un guion con `python -I` y con `socket.socket` sustituido por una función que falla. El guion:
>    - importa `veridicus_contracts`;
>    - lee cada dato de la tabla de rutas con `importlib.resources`;
>    - valida sin red, con `veridicus_contracts.registry`, los *fixtures* de C7, C1 y C19, que recibe por ruta (los *fixtures* no van en la rueda), y compara cada resultado con su `expectation`;
>    - comprueba que la forma antigua de referencia (`contracts/analyzer/v1/salida.schema.json#/$defs/cita`) no se resuelve (BR12.3, E36).
>
> El guion vive como dato del módulo o como función que se pasa por archivo temporal; no como un archivo suelto fuera de `src/`. `subprocess` está admitido en `tools/check_package.py` por E-19 y §4.2; úsalo con listas de argumentos fijas, nunca con `shell=True`, y con `# noqa: S603` más su motivo.
>
> **Pruebas** en `contracts/tests/tools/test_check_package.py`, de 5 a 8, **sin red y sin construir de verdad**. Prueban las piezas puras con datos sintéticos:
> - una lista de rueda completa pasa;
> - una lista sin un esquema de la tabla falla y nombra la ruta;
> - una lista con `fixtures/`, otra con `tests/`, otra con `.env` y otra con un `.pem` fallan;
> - la tabla derivada de `pyproject.toml` coincide con `DIRECTORIOS_DE_DATOS` y `ARCHIVOS_DE_DATOS` de `tests/test_package_map.py`;
> - el guion, corrido en el entorno de la suite con el socket bloqueado, importa el paquete, valida los *fixtures* de C7, C1 y C19 y rechaza la forma antigua;
> - un guion que intenta abrir un socket falla con el error del bloqueo.
>
> La corrida completa (construir, crear el entorno, instalar) se comprueba con el criterio CA-2, no dentro de la suite.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si la corrida completa necesita red y el entorno no la tiene. Pega la salida literal del fallo y para; no la sustituyas por una instalación `--offline` sin decirlo.
- Si un *fixture* de C7, C1 o C19 no valida desde el paquete instalado, o si la forma antigua de referencia sí se resuelve. Es un defecto de un contrato o del registro: lo informas con la ruta y no lo corriges.
- Si hace falta tocar `pyproject.toml`, `hatch_build.py` o `registry.py`.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **La etiqueta `vX.Y.Z`** (BR12.2, paso 25): la pone el humano al cerrar B1.
- **La prueba AST de E32**, que ya entrega T18.
- **El *workflow* de la CI** (paso 24).
- **Las herramientas de T19** y la mitad TypeScript (T20).
- **Editar contratos, *fixtures*, `tests/test_package_map.py` u otras pruebas existentes.**
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.**

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 22, la tabla de comandos (V-PKG) y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-19 y P-T18-1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.2 y §4.16.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: §1 (tabla de rutas), F9 y E36.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR12.1 a BR12.3.
- `contracts/pyproject.toml`, `contracts/tests/test_package_map.py`, `contracts/src/veridicus_contracts/registry.py` y `tools/check_red.py` (solo lectura).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: pruebas de la herramienta, sin red.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/tools/test_check_package.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: V-PKG, la corrida completa (con red, solo para instalar).
  ```bash
  timeout 180 uv run --frozen --directory contracts python -m veridicus_contracts.tools.check_package
  ```
  Esperado: código 0 en 180 s o menos. Pega en la bitácora la salida completa y el tiempo.

- [ ] **CA-3**: la herramienta falla de verdad ante una rueda contaminada (lectura de vuelta sobre una rueda real).
  ```bash
  timeout 180 uv run --frozen --offline --directory contracts pytest tests/tools/test_check_package.py -k rueda_contaminada --no-cov
  ```
  Esperado: verde. La prueba `test_rueda_contaminada_...` construye con `uv build --offline` una copia de `contracts/` en `tmp_path` cuya configuración fuerza la entrada de un `api/fixtures/sintetico.yaml` sintético, y exige que la función de comparación de `check_package`, aplicada a la lista real de esa rueda, falle y nombre la ruta. Es la única prueba de este archivo que construye, y no instala nada.

- [ ] **CA-4**: la suite del Bolt sigue en verde.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde.

- [ ] **CA-5**: rueda, tipos, *lint* y la regla de §4.2.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py tests/checks/test_loader_usage.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: verde, `Success: no issues found` y `All checks passed!`.

- [ ] **CA-6**: sin cambios al clúster.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero `test_check_package.py`.
2. Haz el commit de las pruebas, corre el rojo contra `feat/b1-contratos` y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T21.md`.
3. Escribe la herramienta hasta el verde, y luego corre CA-2.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada. Si el rojo solo puede fallar por módulo ausente, dilo en la bitácora y muestra en el verde que cada control negativo falla por su regla.

---

## Reglas de la app que aplican

- **NEVER versionar secretos:** la rueda no lleva `.env*`, `*.pem` ni `*.key`, y la herramienta lo comprueba.
- **Solo datos sintéticos** (`project.md`): los *fixtures* que valida el guion son los sintéticos del repositorio.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Los directorios temporales van bajo `tempfile` y se borran al terminar, también si falla.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): paso del paquete en entorno limpio (U01-T21)`. Sin signo de dólar en el mensaje.
