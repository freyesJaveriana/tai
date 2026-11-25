# Instrucciones de pruebas unitarias — U10 anonymizer (Bolt B10a)

Acompañan a `code-generation-plan.md` (revisión 1), que se aprueba junto con ellas. Valen solo para el corte B10a (DP-03):
- la seudonimización con reglas y listas;
- la restauración;
- el fallo cerrado;
- el adaptador de Anthropic (`claude-sonnet-5-5`);
- el `FakeTransport`.

El NER, el proxy, los adaptadores de OpenAI y Google y el Corefile son de B10b.

## Marco y configuración

- **Paquete:** `libs/anonymizer/`, con *src layout* (`src/veridicus_anonymizer/`) y sus propios `pyproject.toml` y `uv.lock` (PD-3).
- **Herramientas:** `pytest`, `pytest-cov` (ramas), `pytest-socket`, `hypothesis`, mypy estricto, Ruff (con las reglas `S`), `import-linter` y `pip-audit` (team.md, Testing Posture).
- **`[tool.pytest.ini_options]`:** `addopts = "--strict-markers --disable-socket"`, **sin** `--cov`. Cada comando pide la cobertura que mide (R-01).
- **`[tool.coverage.run]`:** `branch = true` y `source = ["veridicus_anonymizer"]`.
- **Sin red en las pruebas:** `--disable-socket` hace fallar toda prueba que intente abrir una conexión. En B10a no existe ningún marcador para permitirla.
- **Instalación:** la única llamada con red es `timeout 600 uv sync --frozen --directory libs/anonymizer`, una vez por worktree. Instala lo que fija el lockfile, con sus hashes. Todo lo demás corre con `--frozen --offline`.
- **Python 3.12.**

## Cómo correr las pruebas de ESTA unidad

Todos los comandos se corren desde la raíz del worktree de la tarea (`/workspace/.worktrees/U10-TNN`) y solo tocan esta unidad.

| Qué | Comando exacto |
|---|---|
| Instalación (con red, una vez) | `timeout 600 uv sync --frozen --directory libs/anonymizer` |
| Ejecutor listo (paso 3, antes de la primera prueba en rojo) | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/test_package.py -q` |
| Rojo del paso 4: recolección | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts --collect-only -q` |
| Rojo del paso 4: ejecución | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts -p no:cacheprovider -rf` |
| Una capa con su cobertura de ramas | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest <archivos> --cov=<módulo> --cov-branch --cov-fail-under=100 --cov-report=term-missing`. El archivo y el módulo exactos de cada capa están en su paso del plan |
| Un archivo, sin cobertura | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest <archivo de prueba> --no-cov` |
| Suite de la unidad, con su mínimo | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-report=json --cov-fail-under=80` |
| Ramas de los módulos guardia | `timeout 60 uv run --frozen --offline --directory libs/anonymizer python -m veridicus_anonymizer.testing.coverage_gate coverage.json` |
| Tipos | `timeout 300 uv run --frozen --offline --directory libs/anonymizer mypy --strict src tests` |
| *Lint* y formato | `timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff check .` y `timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff format --check .` |
| Fronteras | `timeout 120 uv run --frozen --offline --directory libs/anonymizer lint-imports` |
| Contratos de U1, tocados en el paso 1 | `timeout 60 uv run --frozen --offline --directory contracts pytest` |
| Autoprueba de las guardias del repositorio (paso 13) | `bash scripts/tests/autoprueba-guardias.sh` |

Nunca se usa un comando de todo el repositorio.

## Volumen y orden (estrategia Standard + orden del equipo)

**Volumen:** como mínimo, de 5 a 8 pruebas por componente. Las suites AUTONOMIA se suman a ese volumen y ningún paso las recorta.

| Componente | Archivo de pruebas | Mínimo |
|---|---|---|
| Validador de `contracts` (K-56) | `contracts/tests/test_validators.py` (pruebas `k56`) | 6, de ellas 4 controles negativos |
| Guardias AUTONOMIA-04 y 05 y contratos de datos del módulo | `tests/guards/`, `tests/contracts/` | 30 |
| `FakeTransport` | `tests/testing/test_fake_transport.py` | 6 |
| Listas y tablas (`catalogs`) | `tests/domain/test_catalogs.py` | 2 por patrón |
| Seudonimización (oración, detección y enmascarado) | `tests/domain/test_sentence.py`, `tests/domain/test_detection.py`, `tests/domain/test_masking.py` | 15 |
| Restauración y marcas alteradas | `tests/domain/test_restoration.py` | 6, más las del paso 4 |
| Adaptador de Anthropic y transporte de producción | `tests/providers/` | 10 |
| Orquestación `generate` y `build_anonymizer` | `tests/application/` | 8 |
| Fronteras y logs | `tests/boundaries/` | 4 (3 controles negativos y 1 de logs) |

**Orden según el Testing Contract (`custom`):**
1. **Paso 1.** La prueba `k56` se ejecuta en rojo contra `contracts` 0.1.0 y luego se arregla el validador.
2. **Paso 2.** Deja *stubs* que lanzan `NotImplementedError`, para que el rojo falle en la ejecución y no en la recolección.
3. **Paso 4.** Las pruebas de las guardias AUTONOMIA-04 y 05 y de los contratos de datos del módulo se escriben primero y se ejecutan en **rojo**:
   - 0 errores de recolección;
   - el 100 % en `FAILED`;
   - van en su propio commit, cuyo SHA se anota como `ROJO_SHA`.
4. **Pasos 5 a 11.** Cada capa se implementa y enseguida se escriben y ejecutan sus pruebas.
5. **Paso 10.** Las pruebas del paso 4 pasan a verde **sin cambios**: `git -C /workspace/.worktrees/U10-T04 diff --exit-code ROJO_SHA -- libs/anonymizer/tests/guards libs/anonymizer/tests/contracts` termina con 0.

Ninguna prueba de nivel 0 se reintenta para ocultar un fallo.

## Metas de cobertura

- **100 % de ramas** en los módulos guardia: `domain/`, `application/`, `api.py`, `providers/` y `testing/fake_transport.py`. Cada paso mide sus propios módulos, y `testing/coverage_gate.py` lo vuelve a comprobar sobre la suite completa (paso 14).
- **≥ 80 % de líneas** en todo el paquete, con `--cov-fail-under=80` en la suite completa y en la CI.
- **Sin exclusiones** en B10a. Si alguna resulta necesaria, se declara en `pyproject.toml` y se justifica en el PR.
- Los umbrales nunca se bajan para que pase una compuerta (team.md).

## Dobles de prueba

- **`FakeTransport`** (`testing/fake_transport.py`, sobre `httpx.MockTransport`).
  - Es el único doble del proveedor.
  - Guarda la petición **cruda**: método, dominio, puerto, ruta, cabeceras y cuerpo. Oculta la clave solo al representarla.
  - Devuelve respuestas grabadas sintéticas o errores simulados: 5xx, bloqueo, *timeout*, cuerpo que no es JSON y `307`.
  - Cada prueba de fallo cerrado afirma que quedó con **0 peticiones**, y su control positivo, con 1.
- **Control negativo `testing/bypass.py`.** Reemplaza con `monkeypatch` la función interna de seudonimización, y la prueba del payload tiene que fallar con él. Solo lo importan las pruebas (lo comprueba import-linter), y `build_anonymizer` no tiene ningún parámetro equivalente.
- **Entorno y catálogos.** `build_anonymizer(env, transport)` recibe un diccionario de entorno, y las pruebas le pasan un *canary* como valor de clave; no se leen variables reales. Los casos de dominio o puerto fuera de la lista inyectan un catálogo alterado.
- **Reloj y presupuesto.** El plazo se inyecta, para probar el presupuesto agotado sin esperas reales.
- **`caplog`** captura todos los logs de las pruebas de fugas y de BR2.3.
- No se usan los SDK de los proveedores ni ningún servidor HTTP. El servidor HTTPS local con `trustme` (nivel 1) es de B10b.

## Datos de prueba

- **Solo sintéticos.** Los nombres, lugares, expedientes e identificadores son inventados y van en `tests/fixtures/`. Nada sale del piloto del TG, de `/insumos` ni de la partición `referencia` (team.md, Forbidden; project.md).
- **Conjunto sembrado** (`tests/fixtures/transcripts/*.json`):
  - nombres con mayúscula en **cada** posición de apertura de oración de PD-2 y a mitad de oración, con tilde y sin tilde;
  - nombres escritos con secuencias de escape Unicode del JSON;
  - apodos con mayúscula y tratamientos («doña», «sargento»);
  - una cadena con forma de marca dentro del testimonio;
  - instituciones y meses que deben quedar visibles;
  - nombres de la lista sintética de nombres que también son palabras comunes («Paz», «Esperanza»…) al comienzo de una oración.
- **Límite declarado:** el apodo todo en minúscula va en su propio *fixture*, y una prueba documenta que no se detecta. No forma parte del conjunto de fuga cero.
- **Respuestas grabadas de Anthropic** (`tests/fixtures/anthropic/*.json`): éxito, salida que no es JSON, salida que no valida, rechazo de contenido, 503, 307 hacia otro host y una respuesta con marcas alteradas e inventadas. Se escriben a mano, con la forma documentada de la Messages API, que se cita en la bitácora, y no traen ningún dato real.
- **Canaries:** una cadena única en el testimonio y otra en el valor de la clave. Las pruebas de fugas los buscan en logs, en excepciones (con toda su cadena de causas), en el `ModelCall` y en la petición cruda, fuera de la cabecera de autenticación.
- Los datos versionados no deben hacer saltar `scripts/check-no-datos-personales.sh` ni `scripts/check-no-cluster-ids.sh`. Las sondas de la autoprueba se arman en tiempo de ejecución.
