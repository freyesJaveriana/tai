# U01-T18: integridad de la suite

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 19 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T15, fusionada. Ola 9, en paralelo con T16 y T17.

---

## Alcance

**Dentro:**

> Seis módulos guardia en `contracts/src/veridicus_contracts/checks/`, más una prueba AST:
>
> - **`loader_usage.py`** (security-design §4.1 y §4.2). Recorre los `.py` de `src/` y `tests/` y falla ante:
>   - `import yaml` (PyYAML);
>   - una llamada `YAML(...)` fuera de `loaders.py`;
>   - un `typ` distinto de `"safe"`;
>   - `load_all` o `Loader=`;
>   - `subprocess`, `multiprocessing` u `os.system` en `checks/`, en `tests/` o en los módulos de `src/veridicus_contracts/`. La única excepción es `tools/check_package.py`, que todavía no existe.
>
>   Se publica como `scan(paths)`. Si `tools/check_red.py` o alguna prueba ya existente importa `subprocess`, para y lo informas con la ruta. No la exceptúes por tu cuenta.
> - **`refs.py`** (§4.2, E36). Falla ante:
>   - un `$ref` entre archivos que no empieza por `/veridicus/contracts/`;
>   - un esquema `http:`, `https:` o `file:`;
>   - una ruta relativa como `contracts/analyzer/v1/salida.schema.json#/$defs/cita`.
>
>   Antes de escribirlo, mira cómo resuelven hoy C1 (T14), C18 y C19 sus `$ref` por `$id` canónico. Si la regla de §4.2 choca con un `$ref` ya fusionado, para y lo informas.
> - **`redos.py`** (§4.5). Hace:
>   - el recorrido completo del árbol con `re._parser`: rechaza una repetición ilimitada dentro de otra, `BRANCH` dentro de una repetición ilimitada, `GROUPREF` y `GROUPREF_EXISTS`;
>   - la comprobación del subconjunto portátil: sin `\d`, `\w`, `\s`, `\b`, grupos con nombre, banderas en línea ni miradas atrás, y todo patrón anclado;
>   - la comprobación de entrada acotada: una repetición ilimitada exige `maxLength` con su `x-veridicus-limit`;
>   - Hypothesis con techo de 1 s sobre una entrada adversaria de 10 000 caracteres;
>   - una prueba que exige `sys.version_info[:2] == (3, 12)`.
>
>   Los controles negativos son los de §4.5: `^(a+)+$`, `^(a|aa)*$`, `^(x|(a+)+)$`, `^(?:a|(?:b+)+)*$`, `^(\w+)\1$`, `^[a-z]+$` sin `maxLength` y `^\d{6}$`. Añade los de K-24: `^(a|a)+$` lo rechaza la regla de `BRANCH`, y varios `[a-z]*` contiguos deben quedar fijados con una prueba, como limitación declarada o como rechazo.
> - **`synthetic.py`** (§4.10). Exige:
>   - cada *fixture* declara `synthetic: true`, `expectation`, `reject_reason` si es `reject`, y `mentions`;
>   - cada mención está en `fixtures/synthetic-names.yaml` y aparece en el texto;
>   - no hay secuencias de 6 a 10 dígitos ni de 23 dígitos, con o sin separadores, en ningún campo de texto ni `example`.
>
>   Se publica como `scan(paths)`. Cierra K-04: se eximen los campos `format: uuid` y las huellas `^[a-f0-9]{64}$`. El alcance de §4.10 incluye las `literal_sources` de `integrity/scan-cases.v1.yaml` y `integrity/testimony-warning-cases.v1.yaml`. Los archivos que §4.10 nombra y que no existen (`transcript/speaker-markers.v1.yaml`, `integrity/clarification-speech.v1.yaml`) se anotan en la bitácora y no se crean.
> - **`fixture_coverage.py`** (§4.10). Exige un `accept` y un `reject` por cada regla de nivel 0 de U1, y falla si un `reject` no falla o falla por otra regla. Quedan fuera BR5.2 a BR5.6, BR1.5, BR1.8 y BR12.2. Si falta un *fixture* para una regla, para y lo informas con la lista. No escribas *fixtures* nuevos de otras tareas sin avisar.
> - **`ci_workflows.py`** (§4.11, AUTONOMIA-01). Falla si un *workflow* de `.github/workflows/` contiene `--write`, `kubectl apply`, `helm install`, `helm upgrade` o credenciales del clúster (`kubeconfig`, `KUBECONFIG`). Corre sobre `repo-level0.yml`, que ya existe.
> - **Prueba AST de E32 (BR12.1).** Ningún módulo importa `contracts.` como nombre de primer nivel.
>
> **Pruebas:** de 5 a 8 por módulo, en `tests/checks/test_loader_usage.py`, `test_refs.py`, `test_redos.py`, `test_synthetic.py`, `test_fixture_coverage.py` y `test_ci_workflows.py`. Cada regla lleva un control negativo, sobre una copia en memoria o un archivo sintético en `tmp_path`, y un control positivo sobre el repositorio real. Deben incluir los controles de §4.1, §4.2, §4.5, §4.10 y §4.11:
> - un C8 con un término repetido;
> - un YAML con `!!python/object`;
> - un módulo sintético con `YAML(typ="unsafe")`;
> - E36;
> - los siete patrones de §4.5;
> - un número de 8 dígitos en un *fixture*;
> - un *workflow* con `kubectl apply`.

**Cuándo parar y avisar:** si una guardia nueva encuentra un defecto en un contrato, *fixture* o prueba ya fusionados, para y lo informas con la ruta y la regla. Por ejemplo, un `pattern` con `\d`, un `$ref` relativo o un número largo en un *fixture*. No edites el archivo ajeno.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **El *workflow* de CI** (paso 24) y `tools/security_surface.py` (paso 20).
- **Editar contratos, *fixtures* o pruebas de otras tareas.**
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.**
- **Los módulos de T15 y T17.**

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 19 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.1, §4.2, §4.5, §4.10 y §4.11.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.6 y BR12.1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E32 y E36.
- `docs/loop/CANDIDATAS.md`: K-04 y K-24.
- `contracts/src/veridicus_contracts/loaders.py`, `contracts/fixtures/synthetic-names.yaml` y `.github/workflows/repo-level0.yml`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 19.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_loader_usage.py tests/checks/test_refs.py tests/checks/test_redos.py tests/checks/test_synthetic.py tests/checks/test_fixture_coverage.py tests/checks/test_ci_workflows.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: 100 % de ramas en los seis módulos guardia.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/loader_usage.py,src/veridicus_contracts/checks/refs.py,src/veridicus_contracts/checks/redos.py,src/veridicus_contracts/checks/synthetic.py,src/veridicus_contracts/checks/fixture_coverage.py,src/veridicus_contracts/checks/ci_workflows.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, con el 100 % de líneas y de ramas.

- [ ] **CA-3**: la suite del Bolt sigue en verde.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde.

- [ ] **CA-4**: rueda, tipos y *lint*.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: todo verde y sin hallazgos.

- [ ] **CA-5**: sin cambios al clúster.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero las seis pruebas y la prueba de E32.
2. Haz el commit de las pruebas, corre el rojo contra `feat/b1-contratos` y pega la salida literal en `docs/loop/bitacoras/U01-T18.md`.
3. Escribe los módulos hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con el archivo del commit final y pega esa salida.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** ningún *workflow* aplica cambios al clúster ni tiene sus credenciales (`ci_workflows.py`).
- **Solo datos sintéticos** (`project.md`, NFR12.1): `synthetic.py` es la evidencia. Nunca copies texto del piloto ni de `/insumos`.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- Los mensajes de las guardias nombran el archivo, el puntero y la regla, nunca el valor (un número sospechoso no se repite en el mensaje).
- `redos.py` depende de una API privada de Python 3.12. La prueba de versión es obligatoria.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`. Para añadir a la bitácora, usa `cat >> RUTA <<'FIN'`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): integridad de la suite (U01-T18)`.
