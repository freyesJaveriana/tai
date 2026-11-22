# Decisiones de pila — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.** Todo es **nuevo** (D1–D7).

**Insumos.** `functional-design/` de U12 (F1–F6, BR1.1–BR8.4, entidades); FR13.5, NFR10, NFR12, NFR13 y NFR14
de requirements; C1, C19 y C25 de contract-summary; las pilas aprobadas de U1 (`veridicus_contracts`:
`registry`, `limits.load`, cargadores YAML), U3 (manejador de Problem Details, CSRF) y U4 (D9, D11, D13,
D14); `security-requirements.md`, `performance-requirements.md` y `reliability-requirements.md` de esta
unidad.

**Lo que no se repite.** Ya lo fijan `team.md`, U2, U3 y U4:
- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 con psycopg 3 (solo en `session-api`) y Alembic en un
  `Job`;
- `uv`, `pytest` con Hypothesis, mypy estricto, Ruff e import-linter;
- React con TypeScript estricto, TanStack Query, Vitest, Playwright y `@axe-core/playwright`;
- Problem Details desde `libs/`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | nuevo | Lectura del cuerpo | La ruta lee `request.stream()` de Starlette y corta al pasar `research_report_max_bytes` + 64 KiB; rechaza antes de leer si `Content-Length` ya lo supera | `UploadFile` de FastAPI, que analiza todo el cuerpo antes de entrar a la ruta | Cortar mientras se lee (BR2.2) y no confiar en `Content-Length` | NFR10.3, NFR3.3 |
| D2 | nuevo | Análisis del `multipart` | `python-multipart` en modo de bajo nivel (`MultipartParser` con *callbacks*), que copia la parte `file` a un `bytearray` acotado y descarta el `filename` sin guardarlo | `request.form()`, que usa `SpooledTemporaryFile` y escribe en disco por encima de 1 MiB | El archivo no toca el disco (BR5.1) y el nombre no se conserva (BR4.2) | NFR10.4, NFR10.8 |
| D3 | nuevo | JSON estricto y esquema | Un recorrido lineal de los bytes mide la profundidad antes de `json.loads`. `json.loads` lleva `object_pairs_hook` que rechaza claves repetidas, `parse_constant` que rechaza `NaN` e `Infinity` y `parse_float` que rechaza lo que da infinito. El `ValueError` de enteros enormes se traduce a `out_of_range`. El esquema C19 vigente se valida con `jsonschema` (Draft 2020-12) desde `veridicus_contracts.registry`, con el validador compilado una sola vez al arrancar y `iter_errors` para contar todos los problemas | `orjson` (no detecta claves repetidas); validar con modelos Pydantic escritos a mano | Un solo origen de verdad (los esquemas de U1, como D9 de U4) y control de cada caso de BR2.3 | NFR10.5, NFR10.6, NFR3.2 |
| D4 | nuevo | Almacenamiento | Tabla `research_report` y tablas hijas `research_report_model_call`, `research_report_metric` y `research_report_bias_count`, con columnas tipadas y `CHECK` por patrón; `run_summary` en columnas de la fila (los mapas como `jsonb` con claves y valores comprobados por `CHECK` contra sus enum). Inserción en bloque con `insert()` de SQLAlchemy Core (`insertmanyvalues`) dentro de la `UnitOfWork` | Todo en una columna `jsonb` | Los `CHECK` por columna son la defensa en profundidad de NFR12.4; Code Generation confirma la forma (NFR-U12-07) | NFR12.4, NFR11.1, NFR11.4, NFR3.11 |
| D5 | nuevo | Catálogo de referencia | `ReferenceCatalog` inmutable (`dataclass(frozen=True)`) armado por el cargador de configuración de ConsoleApi al arrancar, con los cargadores YAML de `veridicus_contracts` y `profiles.validate` de U1 | Leer los archivos en cada subida | Cargar una vez, fallar al arrancar (BR3.6) y no abrir archivos en ResearchReports | NFR10.9, NFR10.15, NFR10.18 |
| D6 | nuevo | Rechazos sin eco | Una clase `ValidationProblem` con solo `rule`, `path`, `line` y `column`; el `detail` se arma con plantillas del catálogo de mensajes. Las excepciones de `json` y `jsonschema` se capturan en el borde del validador y se descartan después de extraer la regla y la ruta | Pasar `str(exc)` al `detail` | BR4.1: nunca el valor ni el mensaje del validador | NFR10.7, NFR10.8, NFR14.1 |
| D7 | nuevo | Pruebas de rendimiento | Marca `perf` de `pytest` en `services/session-api` (como D15 de U4) y `psutil` para el pico de memoria | k6 o Locust | Pocas peticiones en proceso; lo que importa es el tamaño del archivo | NFR3.1–NFR3.8 |

## 2. Configuración

U12 no añade variables `VERIDICUS_*` propias. Usa las de `session-api`:

| Ajuste | De quién | Qué usa U12 |
|---|---|---|
| `VERIDICUS_PROFILES_PATH` | U4 | El archivo de perfiles del catálogo de referencia |
| `VERIDICUS_LIMITS_PATH` y `VERIDICUS_LIMIT_<NOMBRE>` | U4 (D20) | `research_report_max_bytes`, `research_report_max_json_depth` y `research_report_write_timeout_s`; el entorno solo puede bajarlas |
| `VERIDICUS_PRICES_PATH` y `VERIDICUS_LABELS_DIR` | Nuevas en `session-api` si Infrastructure Design no monta los archivos en la ruta por defecto | Precios y listas de etiquetas. Obligatorias si se declaran; un archivo ausente impide arrancar (NFR10.15) |

## 3. Calidad del código (NFR13)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR13.1 | nuevo | Cobertura de líneas. | ≥ 80 % en `services/session-api` y en `frontend` con M8 incluida, medido en la CI y bloqueante (`team.md`) |
| NFR13.2 | nuevo | 100 % de ramas en los módulos que protegen NFR12. | La validación (BR2.1–BR2.8), el contraste con lo versionado (BR3.1–BR3.5) y el armado de rechazos sin eco (BR4.1–BR4.2) se tratan como módulos guardia: `--cov-branch` con `fail_under = 100` sobre ellos, en el mismo `.coveragerc-guards` de U4. Sus pruebas se escriben primero y en rojo (Testing Posture, Ordering) |

## 4. Dependencias nuevas de U12

- `services/session-api`: `python-multipart` (ya la trae FastAPI para formularios; se fija su versión), y en
  desarrollo `psutil`.
- `frontend`: ninguna.

Todas van fijadas en el lockfile de cada servicio, con `pip-audit` y `npm audit` en la CI (NFR10.13).

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y guardias (nivel 0) | `uv run --directory services/session-api pytest -m "not integration and not perf" tests/research_reports` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1), con el *canary* | `uv run --directory services/session-api pytest -m integration tests/research_reports` | Verde; 0 coincidencias del *canary* (NFR12.1) |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf tests/research_reports` | NFR3.1–NFR3.6, NFR3.8, NFR3.10, NFR3.11 |
| Fronteras | `uv run --directory services/session-api lint-imports` | 0 violaciones, y el módulo de control negativo falla (NFR1.2, NFR15.1) |
| Consola (M8) | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| Accesibilidad y teclado (nivel 3) | `npx --prefix frontend playwright test e2e/research-reports.spec.ts` | 0 violaciones `serious` o `critical` (BR8.1); NFR3.7 |
| Tipos y *lint* | `uv run --directory services/session-api mypy --strict .` y `uv run --directory services/session-api ruff check .` | 0 errores |
| Dependencias | `uv run --directory services/session-api pip-audit` y `npm --prefix frontend audit --audit-level=high` | Sin `HIGH` o `CRITICAL` con corrección |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| `python-multipart` cambia su API de bajo nivel | Versión fijada en el lockfile; la prueba de NFR10.4 falla si vuelve a escribir en disco |
| `jsonschema` no cabe en su tramo de NFR3.2 con el archivo máximo | Validador compilado al arrancar (D3); si aun así no cabe, se mide con `fastjsonschema` en un PR aparte, sin cambiar el esquema ni el umbral |
