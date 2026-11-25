# U01-T19: herramientas deterministas (huella de seguridad, generados y compuerta de auditoría)

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 20 y la casilla pendiente del paso 1 (`build/` lo crean `audit_gate` y el paso de `pip-audit` si falta) de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T16, T17, T17b y T18, fusionadas (ola 9). La huella lee las métricas de T17 y las listas de §4.6 de T15. Ola 10, en paralelo con T21.

---

## Alcance

**Dentro:**

> Cuatro herramientas en `contracts/src/veridicus_contracts/tools/`, cada una ejecutable con `python -m veridicus_contracts.tools.<nombre>`. Ya existe `check_red.py`: sigue su estilo.
>
> 1. **`security_surface.py`** (security-design §4.11, DS3).
>    - Genera `contracts/security-surface.json` con las siete secciones de la tabla de §4.11: `operations` (C1 `api/console.v2.yaml`, C16 `health/health.v2.yaml`, C21 `api/anonymizer-proxy.v1.yaml` y la ruta interna de voz `api/speech-internal.v1.yaml`), `schemas`, `cookie`, `servers`, `limits` (C25), `metrics` (todos los archivos de `metrics/`) e `integrity`.
>    - **`integrity`:** la huella de C8 (`integrity/forbidden-vocabulary.v2.yaml`), del catálogo de rótulos (`ui/result-labels.v2.yaml`), de `errors/error-codes.v2.yaml` y de C25 es `canonical.sha256_jcs` del documento **ya cargado** con los cargadores del paquete. La de C6 es el SHA-256 de los bytes de `analyzer/v1/SHA256SUMS` (BR1.7).
>    - **Reproducible en bytes:** las listas sin orden semántico (roles, códigos de respuesta, etiquetas, usos) se ordenan; el archivo se escribe con `json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)` más `\n`, en UTF-8 sin BOM.
>    - Sin argumentos, o con `--check`, compara en memoria y sale con código 1 mostrando la diferencia. Solo `--write` escribe el archivo. La CI nunca corre `--write`.
>    - Reutiliza los recorridos de `checks/_openapi.py` y las constantes de `checks/auth_surface.py` donde existan; no dupliques un recorrido.
> 2. **`gen_ts.py`** (D9, §4.14). Genera en `contracts/ts/generated/` constantes TypeScript `as const` del catálogo de `code`, de los rótulos, de C8 y de las listas de §4.6 (las de `checks/auth_surface.py`). Crea la carpeta si falta; T20 la consume después. `--check` compara sin escribir y sale con código 1 si difiere. La salida es determinista en bytes, con finales de línea LF. No genera los tipos de C1: eso es `openapi-typescript`, en T20.
> 3. **`gen_jcs_vectors.py`** (§4.14). Genera `contracts/fixtures/jcs-vectors.json`: 200 objetos sintéticos con números límite (`1e21`, `-0`, `5e-324`, `0.1`), claves Unicode y anidamiento, cada uno con su SHA-256 esperado de `canonical.sha256_jcs`. Semilla fija de Hypothesis. `--check` igual que arriba.
> 4. **`audit_gate.py`** (§4.13 paso 3, NFRD-U1-11). Lee el JSON de `pip-audit` y `contracts/.pip-audit-ignore.yaml`. Sale con código 0 solo si no queda ninguna vulnerabilidad **con `fix_versions` no vacío** fuera de una excepción vigente. Cada excepción lleva `id`, `motivo` y `caduca` (fecha `AAAA-MM-DD`); una excepción vencida es un fallo, igual que una mal formada o con clave desconocida. Si la carpeta del archivo de entrada es `build/` y no existe, la crea (paso 1). Los mensajes nombran el paquete y el ID, nunca la descripción.
>
> **Archivos versionados nuevos:**
> - `contracts/security-surface.json`, generado con `--write`.
> - `contracts/ts/generated/*`, generados por `gen_ts`.
> - `contracts/fixtures/jcs-vectors.json`, generado por `gen_jcs_vectors`.
> - `contracts/.pip-audit-ignore.yaml`, con una lista vacía de excepciones y un comentario que explica el formato.
> - `.github/pull_request_template.md` en la raíz del repositorio (NFRD-U1-13), en español, con un apartado que pide justificar todo cambio de `contracts/security-surface.json`, más los apartados de evidencia que pide `team.md` (salida del comando de verificación de cada tarea).
>
> **Pruebas** en `contracts/tests/tools/`, cinco por herramienta como mínimo (`test_security_surface.py`, `test_gen_ts.py`, `test_gen_jcs_vectors.py`, `test_audit_gate.py`), y una prueba de la plantilla de PR:
> - **regenerada = versionada:** cada generador, en memoria, coincide con el archivo del repositorio;
> - **idempotencia en bytes:** dos generaciones seguidas dan bytes idénticos;
> - **cambio de seguridad visible:** en una copia en memoria de C1, quitar la seguridad de una operación, añadir un `servers` o cambiar una cifra de C25 cambia la huella en la sección esperada; cambiar solo un comentario o un espacio del YAML no la cambia;
> - **`--check` en rojo tras un cambio:** sobre una copia en `tmp_path`, `--check` sale con código 1;
> - **`audit_gate`:** sin vulnerabilidades, verde; una con `fix_versions`, rojo; una sin `fix_versions`, verde; una con excepción vigente, verde; con excepción vencida, rojo; excepción con clave desconocida, rojo. Los JSON de `pip-audit` de las pruebas son sintéticos y se escriben en `tmp_path`;
> - **vectores JCS:** los 200 vectores recalculados con `canonical.sha256_jcs` coinciden, y están los cuatro números límite;
> - **plantilla de PR:** el archivo existe y conserva el apartado de `security-surface.json`.
>
> Cada decisión de forma que §4.11 o §4.14 no fijen (por ejemplo, la estructura de cada sección de la huella o los nombres de los archivos de `ts/generated/`) se anota en la bitácora como **P-T19-n**, con su fuente.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si `security-surface.json`, `fixtures/jcs-vectors.json` o `.pip-audit-ignore.yaml` obligan a cambiar `pyproject.toml`, `hatch_build.py` o la tabla de rutas de `test_package_map.py` para entrar o quedar fuera de la rueda.
- Si Hypothesis no puede dar los 200 vectores idénticos en bytes de una corrida a otra con semilla fija. Para con las salidas posibles (por ejemplo, `random.Random` con semilla).
- Si una herramienta en `src/` necesita importar una dependencia que solo está en el grupo de desarrollo (Hypothesis), y eso rompe la importación de la rueda o mypy. Para y lo informas.
- Si la huella expone un defecto real en un contrato (por ejemplo, una operación sin seguridad efectiva). Lo informas con la ruta; no edites el contrato.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **El *workflow* de la CI** (`.github/workflows/`, paso 24) y `.pre-commit-config.yaml`.
- **La mitad TypeScript** fuera de `contracts/ts/generated/`: `package.json`, `openapi-typescript`, Vitest (T20).
- **`tools/check_package.py`** (T21).
- **Editar contratos, C25, el catálogo de errores, C8 o los rótulos.**
- **Los módulos guardia** de `checks/` y sus pruebas.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.**
- **Correr `pip-audit` con red** en las pruebas. La suite no tiene red.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: pasos 1 y 20, la tabla de comandos de verificación (V-GEN, V-SURFACE, V-AUDIT) y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.6, §4.11, §4.13, §4.14 y la tabla de §10 (NFRD-U1-11, NFRD-U1-13).
- `contracts/src/veridicus_contracts/canonical.py`, `loaders.py`, `checks/_openapi.py`, `checks/auth_surface.py` y `tools/check_red.py`.
- Los contratos que lee la huella, en solo lectura.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 20.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/tools --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: V-SURFACE y V-GEN.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/tools/test_security_surface.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check
  ```
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_jcs_vectors --check
  ```
  Esperado: verde y código 0, sin diferencias.

- [ ] **CA-3**: la compuerta de auditoría lee la lista de excepciones real (lectura de vuelta con la herramienta).
  ```bash
  uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.audit_gate tests/data/pip-audit-vacio.json --ignore .pip-audit-ignore.yaml
  ```
  Esperado: código 0. `tests/data/pip-audit-vacio.json` es un JSON sintético sin vulnerabilidades que añade esta tarea.

- [ ] **CA-4**: la suite del Bolt sigue en verde.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde.

- [ ] **CA-5**: rueda, tipos y *lint*.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: verde, `Success: no issues found` y `All checks passed!`.

- [ ] **CA-6**: sin cambios al clúster y ningún *workflow* con `--write`.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  Esperado: `0 apariciones` con código 0, y verde.

---

## Plan de pruebas

1. Escribe primero las pruebas de `tests/tools/` y la de la plantilla.
2. Haz el commit de las pruebas, corre el rojo contra `feat/b1-contratos` y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T19.md`.
3. Escribe las herramientas y genera los archivos versionados hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada. Si el rojo de una herramienta que no existe solo puede fallar por módulo ausente, dilo en la bitácora y muestra en el verde que cada control negativo falla por su regla.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** regenerar la huella es un acto explícito (`--write`) que la CI nunca ejecuta.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`): los vectores JCS y los JSON de `pip-audit` de prueba son sintéticos.
- **NEVER versionar secretos:** la huella registra cómo se nombra cada `Secret` o clave, nunca un valor.

---

## Notas

- **Edita solo con Edit o Write**, también las pruebas. Los archivos generados se escriben corriendo la herramienta con `--write` o sin `--check`, nunca a mano. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write. No uses `ruff --fix` ni `git stash`.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`.
- Los mensajes de error nombran el archivo, el puntero y la regla, nunca el valor.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): herramientas deterministas de huella, generados y auditoria (U01-T19)`. Sin signo de dólar en el mensaje.
