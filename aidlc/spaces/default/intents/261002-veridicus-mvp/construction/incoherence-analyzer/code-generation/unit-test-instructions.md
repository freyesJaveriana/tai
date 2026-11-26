# Instrucciones de pruebas unitarias — U11 incoherence-analyzer (Bolt B11a)

Estas instrucciones acompañan a `code-generation-plan.md` (revisión 3) y se aprueban junto con él. Valen solo para el corte B11a (DP-03), que incluye:
- la CLI `veridicus analyze` en modo final;
- el `ModelGateway` con el adaptador `anonymizing`;
- el perfil único `demo-anthropic`;
- la verificación de citas, el filtro, el verificador y la permutación;
- el escáner de vocabulario y el aviso VE-01.

Pasan a B11b el adaptador local, `todo-local`, las ventanas, el modo incremental, `evaluate`, el nivel 2 y ZINE.

## Marco y configuración

- **Paquetes:** `libs/incoherence_analyzer/`, `libs/model_gateway/`, `libs/execution_profiles/` y `libs/integrity_policy/`. Todos usan *src layout* (`src/veridicus_<pkg>/`) y cada uno tiene su propio `pyproject.toml` y su `uv.lock` (PD-1).
- **Herramientas:** `pytest`, `pytest-cov` (con ramas), `pytest-socket`, `hypothesis`, mypy estricto, Ruff con las reglas `S`, `import-linter` y `pip-audit` (team.md, Testing Posture).
- **`[tool.pytest.ini_options]`:**
  - `addopts = "--strict-markers --disable-socket -m 'not manual'"`, **sin** `--cov`; cada comando pide la cobertura que mide;
  - se declaran los marcadores `manual` (proveedor real, lo lanza el humano) y `cli`.
- **`[tool.coverage.run]`:** `branch = true` y `source = ["veridicus_<pkg>"]`.
- **Sin red:** `--disable-socket` hace fallar cualquier prueba que intente abrir una conexión. B11a no abre sockets, ni siquiera a `127.0.0.1`. La única prueba con red real es la marcada `manual`, que no corre por defecto ni en la CI.
- **Instalación:** las únicas llamadas con red son `timeout 600 uv lock --directory libs/<P>`, solo en U11-T01 para crear los lockfiles, y `timeout 600 uv sync --frozen --directory libs/<P>`, una vez por worktree; en `incoherence_analyzer` se agrega `--extra cli`. Todo lo demás corre con `--frozen --offline`.
- **Python 3.12.**

## Cómo correr las pruebas de ESTA unidad

Todos los comandos se corren desde la raíz del worktree de la tarea (`/workspace/.worktrees/U11-TNN`) y solo tocan esta unidad. `<P>` es el directorio del paquete y `<m>`, su módulo.

| Qué | Comando exacto |
|---|---|
| Instalación (con red, una vez) | `timeout 600 uv sync --frozen --directory libs/<P>`; en el analizador, `timeout 600 uv sync --frozen --extra cli --directory libs/incoherence_analyzer` |
| Ejecutor listo (paso 2) | `timeout 300 uv run --frozen --offline --directory libs/<P> pytest tests/test_package.py -q` |
| Rojo del paso 3: recolección | `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts --collect-only -q` |
| Rojo del paso 3: ejecución | `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=line --rojo` y `timeout 300 uv run --frozen --offline --directory libs/execution_profiles pytest tests/contracts -p no:cacheprovider -rfE --tb=line --rojo` |
| Una capa con su cobertura de ramas | `timeout 300 uv run --frozen --offline --directory libs/<P> pytest <archivos> --cov=<módulo> --cov-branch --cov-fail-under=100 --cov-report=term-missing`. El archivo y el módulo exactos de cada capa están en su paso del plan |
| Un archivo, sin cobertura | `timeout 300 uv run --frozen --offline --directory libs/<P> pytest <archivo de prueba> --no-cov` |
| Suite de un paquete, con su mínimo | `timeout 300 uv run --frozen --offline --directory libs/<P> pytest --cov=<m> --cov-branch --cov-report=json --cov-fail-under=80` |
| Ramas de los módulos guardia | `timeout 60 uv run --frozen --offline --directory libs/incoherence_analyzer python -m veridicus_incoherence_analyzer.testing.coverage_gate ../incoherence_analyzer/coverage.json ../model_gateway/coverage.json ../execution_profiles/coverage.json ../integrity_policy/coverage.json` |
| Tipos | `timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src tests` |
| *Lint* y formato | `timeout 120 uv run --frozen --offline --directory libs/<P> ruff check .` y `timeout 120 uv run --frozen --offline --directory libs/<P> ruff format --check .` |
| Fronteras | `timeout 120 uv run --frozen --offline --directory libs/<P> lint-imports` |
| Punta a punta con el doble | `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/e2e --no-cov -q` |
| Corrida manual (solo el humano, con su clave, el viernes después de U11-T05) | `timeout 900 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/manual -m manual --no-cov --force-enable-socket -q`, con `VERIDICUS_ANTHROPIC_API_KEY` y `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300` en el entorno. Cómo se cargan desde el `.env` queda en el README del paquete |
| Rojo del paso 3, comprobando la causa | Los dos comandos de la fila «Rojo del paso 3: ejecución» con `-rfE --tb=line --rojo`. Con `--rojo`, un fallo que no sea `NotImplementedError` cuenta como `ERROR` |
| Regresión del anonimizador (B10a) | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-fail-under=80` |

Nunca se usa un comando de todo el repositorio.

## Volumen y orden (estrategia Standard + orden del equipo)

**Volumen.** Como mínimo, de 5 a 8 pruebas por componente. Las suites AUTONOMIA se suman a ese volumen y ningún paso las recorta.

| Componente | Archivo de pruebas | Mínimo |
|---|---|---|
| Guardias AUTONOMIA-03, 04 y 05, K-84 y contratos de datos | `libs/incoherence_analyzer/tests/guards/`, `tests/contracts/`, `libs/execution_profiles/tests/contracts/` | 35 |
| Errores nuevos de `libs/errors` | `libs/errors/tests/` | 4 (una por clase) |
| Perfiles, validación y pisos | `libs/execution_profiles/tests/` | 10 |
| Escáner y aviso | `libs/integrity_policy/tests/` | 8, con un positivo y un negativo por término |
| `ModelGateway` y adaptador `anonymizing` | `libs/model_gateway/tests/` | 8 |
| Dominio: citas, filtro, estado y salida | `libs/incoherence_analyzer/tests/domain/` | 20 |
| *Prompt*, mensajes y esquemas | `tests/application/test_messages.py` | 8, con 1 propiedad Hypothesis |
| `analyze` (validación previa, juez, verificador, permutación y plazo) | `tests/application/` | 12 |
| CLI | `tests/cli/` | 12, con una por código de salida y una por regla BR11 |
| Fronteras | `tests/boundaries/` | 5 (4 controles negativos y 1 AST) |
| Punta a punta | `tests/e2e/` | 4 |

**Orden según el Testing Contract (`custom`).**
1. **Paso 2.** Deja *stubs* que lanzan `NotImplementedError`, para que el rojo falle en la ejecución y no en la recolección.
2. **Paso 3.** Las pruebas de las guardias AUTONOMIA-03, 04 y 05, de K-84 y de los contratos de datos se escriben primero y se ejecutan en **rojo**:
   - 0 errores de recolección;
   - el 100 % de las pruebas en `FAILED`;
   - van en su propio commit, cuyo SHA se anota como `ROJO_SHA`.
3. **Pasos 4 a 12.** Cada capa se implementa y enseguida se escriben y se corren sus pruebas.
4. **Paso 9.** Las pruebas del paso 3 pasan a verde **sin cambios**. Lo comprueba `git -C /workspace/.worktrees/U11-T04 diff --exit-code <ROJO_SHA> -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts`, que debe terminar con 0. `<ROJO_SHA>` es el SHA de 40 caracteres de la línea `ROJO_SHA:` de `docs/loop/bitacoras/U11-T01.md`, y el orquestador lo escribe literal en el archivo de la tarea U11-T04.

Ninguna prueba de nivel 0 se reintenta para ocultar un fallo.

## Metas de cobertura

- **100 % de ramas** en los módulos guardia:
  - `domain/quotes.py`, `domain/filter.py`, `domain/run_state.py`, `domain/output.py`;
  - `application/preflight.py`, `cli/composition.py`;
  - `model_gateway/adapters/anonymizing.py`, `integrity_policy/scan.py`, `execution_profiles/validate.py`.

  Cada paso mide sus propios módulos, y `testing/coverage_gate.py` lo vuelve a comprobar sobre la suite completa (paso 14).
- **≥ 80 % de líneas** en cada paquete, con `--cov-fail-under=80` en la suite completa y en la CI.
- **Sin exclusiones** en B11a. Si alguna resulta necesaria, se declara en `pyproject.toml` y se justifica en el PR.
- Los umbrales nunca se bajan para que pase una compuerta (team.md).

## Dobles de prueba

- **`FakeTransport` de B10a** (`veridicus_anonymizer.testing.fake_transport`), con respuestas grabadas del juez y del verificador:
  - es el único doble del proveedor en las pruebas compuestas y de punta a punta;
  - captura la petición cruda.
- **Control negativo:** `veridicus_anonymizer.testing.bypass`. La prueba del payload compuesto tiene que fallar con él.
- **Fake determinista del gateway** (`veridicus_model_gateway.testing`), para las pruebas de dominio y de `analyze` que no necesitan el anonimizador (team.md, Dobles de prueba):
  - devuelve un `GenerateResult` fijo por papel y por orden de llamada;
  - puede lanzar cualquier error de `model_calls`;
  - puede devolver un `ModelCall` con `anonymized: false`.
- **Entorno:** `build_anonymizer(env, transport)` y la CLI reciben un diccionario de entorno, nunca variables reales. El valor de la clave es un *canary*.
- **Reloj y plazo:** se inyectan, para probar el plazo agotado y el exceso de 2× sin esperas reales.
- **`caplog` y `capsys`:** capturan logs, stdout y stderr en las pruebas de fugas (BR11.7).
- No se usan los SDK de los proveedores ni ningún servidor HTTP.

## Datos de prueba

- **Solo sintéticos.** Las transcripciones, los nombres, los lugares y los expedientes son inventados y van en `tests/fixtures/`. Nada sale del piloto del TG, de `/insumos` ni de la partición `referencia` (team.md, Forbidden; project.md).
- **Transcripciones** (`tests/fixtures/transcripts/*.json`, objeto `transcripcion` de C6):
  - una con una contradicción sembrada;
  - un relato coherente;
  - una con un turno `ENT` y otra con un turno plegado;
  - una con citas que necesitan « […] »;
  - una con nombres y lugares sembrados para la prueba compuesta;
  - una con origen `corpus` sin consentimiento y otra sin `autoriza_transferencia`, para las pruebas de validación previa;
  - una por encima de cada límite de C25.
- **Respuestas grabadas** (`tests/fixtures/responses/*.json`), con la forma de la Messages API que reproduce el `FakeTransport`:
  - un juez con hallazgos válidos;
  - un juez con una cita alterada, otro con una cita de otro turno y otro con un campo vacío;
  - un juez con vocabulario de C8 en `hecho`, y una respuesta que no valida el esquema;
  - un verificador que confirma y uno que rechaza;
  - un verificador permutado que rechaza;
  - una respuesta con marcas alteradas.
- **Canaries:** una cadena única en el testimonio y otra en el valor de la clave. Las pruebas de fugas las buscan en stderr, en los logs, en las excepciones (con toda su cadena de causas), en la salida C6 fuera de las citas y en los archivos escritos.
- Los datos versionados no deben hacer saltar `scripts/check-no-datos-personales.sh` ni `scripts/check-no-cluster-ids.sh`.
