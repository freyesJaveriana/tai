# Decisiones de pila — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.** Todo es **nuevo** (D1–D8).

**Insumos.** `functional-design/` de U13 (F1–F10, BR1.1–BR9.2, entidades); NFR10–NFR14 de requirements;
C1, C8, C23, C24 y C25 de contract-summary; las pilas aprobadas de U1 (`veridicus_contracts`: `limits.load`,
cargadores YAML), U3 (manejador de Problem Details, CSRF, `UnitOfWork`, punto de guardado de
`AccessLog`), U4 (pila de `session-api` y de la consola, suite `axe`, escáner de vocabulario), U5 (tope del
cuerpo, `lock_timeout`) y U7 (`verify_store` por `kubectl exec`, `purge_session`); `security-requirements.md`,
`performance-requirements.md` y `reliability-requirements.md` de esta unidad. El insumo `technology-stack` de
Reverse Engineering no aplica: el proyecto es *greenfield* y no hay código previo que analizar.

**Lo que no se repite.** Ya lo fijan `team.md`, U2, U3 y U4:
- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 síncrono con psycopg 3 (solo en `session-api`) y Alembic
  en un `Job`;
- `uv`, `pytest` con Hypothesis, mypy estricto, Ruff e import-linter;
- React con TypeScript estricto, TanStack Query, Vitest, Playwright y `@axe-core/playwright`;
- Problem Details desde `libs/`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | nuevo | Dónde vive | Módulo `session_api.ethics_governance` con `domain/` (estado del reconocimiento, validación del plazo, comparación de testimonio y selección de candidatas, como código puro), `application/` (fachada, `Job`, consulta) y `adapters/` (repositorios y adaptador de `AccessLog`). El `Job` y el comando son `python -m session_api.ethics_governance.retention` y `… .query`, con `argparse` | Un servicio o una imagen aparte para el `Job` | La misma imagen que ya corre (BR5.1); las capas de `team.md` | NFR1.2, NFR10.11 |
| D2 | nuevo | Comparación de testimonio | Función pura `find_literal_overlap(note, turns, min_words)`: normaliza espacios (`\s+` → un espacio, como la regla del piloto), parte por espacios, guarda en un conjunto las secuencias de 8 palabras de la nota (como tuplas, o su *hash* si la medición lo pide) y recorre cada turno con una ventana de 8 palabras; se detiene en la primera coincidencia. La consola tiene su par en TypeScript con la misma especificación y los mismos ejemplos (NFR-U13-10) | Distancia de edición o *embeddings*; pedir la comparación al servidor antes de enviar | Literal y determinista (DD-04, regla del piloto); lineal en el tamaño de la sesión; respuesta inmediata en la consola (como la división de la transcripción de U6) | NFR3.1, NFR3.2, NFR10.6 |
| D3 | nuevo | Plazo del registro de acceso | El adaptador ejecuta `SET LOCAL statement_timeout = <VERIDICUS_ACCESS_LOG_TIMEOUT_MS>`, inserta y restaura con `SET LOCAL statement_timeout` al valor que leyó antes con `current_setting`. Corre dentro del punto de guardado que abre ConsoleApi (U3) o de la transacción de la exportación (U7) | Un hilo con espera; `statement_timeout` por conexión | Corta en el servidor y no deja el plazo corto al resto de la transacción | NFR10.13, NFR3.5 |
| D4 | nuevo | Una ejecución a la vez | `pg_try_advisory_lock` con una clave fija del módulo, tomado en una conexión de `veridicus_retention` durante toda la ejecución | Un archivo de bloqueo en el volumen; un `Lease` de Kubernetes | Sin permisos nuevos en el clúster ni archivos extra; se libera solo si el pod muere | NFR10.19 |
| D5 | nuevo | Acta | `deleted_ids`, `deleted_report_sha256s` y `deleted_audio` en columnas `jsonb`, armadas desde los `PurgeReceipt` con un modelo Pydantic de tipos cerrados (UUID, hex de 64, booleanos) y un `CHECK` de `jsonb_typeof`; el resto en columnas tipadas con `CHECK` de patrón | Tablas hijas por cada lista | El acta es de solo inserción y se lee entera; los tipos cerrados impiden el texto | NFR11.4, NFR3.9 |
| D6 | nuevo | Tope del cuerpo | Se deja de leer el cuerpo JSON de las tres rutas de U13 al pasar `ethics_body_max_bytes`, antes de validar, y se responde `413` `limits.exceeded`, con la misma dependencia que usa U5 (D12 de U5) | Confiar en el límite del Ingress | Corta en la frontera con la cifra del catálogo | NFR10.3 |
| D7 | nuevo | Reloj | Un `Clock` inyectado en la fachada y en el `Job`: el real en producción y uno simulado en las pruebas. Sin argumento ni variable de entorno que lo cambie en el borrado | Leer `datetime.now()` en cada sitio; `freezegun` en todo el módulo | BR5.3 prohíbe cambiar la fecha del borrado; el reloj simulado solo existe en las pruebas | NFR10.11, NFR10.21 |
| D8 | nuevo | Pruebas de rendimiento | Marca `perf` de `pytest` en `services/session-api` (como D15 de U4) y `psutil` para la memoria; Playwright con `performance.now()` en la consola | k6 o Locust | Pocas peticiones; lo que importa es el tamaño de la sesión y del borrado | NFR3.1–NFR3.12 |

## 2. Configuración

| Ajuste | De quién | Qué usa U13 |
|---|---|---|
| `VERIDICUS_LIMITS_PATH` y `VERIDICUS_LIMIT_<NOMBRE>` | U4 (D20) | Las siete cifras de NFR-U13-01; el entorno solo puede bajarlas |
| `VERIDICUS_ACCESS_LOG_TIMEOUT_MS` | U3 (500, entre 100 y 2 000) | El plazo del adaptador (D3) |
| `VERIDICUS_DB_LOCK_TIMEOUT_MS` | U5 | La `PATCH` del plazo |
| `VERIDICUS_RETENTION_SESSION_TIMEOUT_S` | **Nueva**, solo en el `Job` (60, entero entre 10 y 300) | El plazo de cada sesión (NFR10.15). Si falta o no vale, el `Job` termina con código 2 antes de abrir la base |
| Conexión de `veridicus_retention` | U2 (Secret que crea el humano, por `secretKeyRef`) | Solo en el `Job` |

## 3. Calidad del código (NFR13)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR13.1 | nuevo | Cobertura de líneas. | ≥ 80 % en `services/session-api` y en `frontend` con lo de U13 incluido, medido en la CI y bloqueante (`team.md`) |
| NFR13.2 | nuevo | 100 % de ramas en los módulos que protegen el borrado y la nota. | La selección de candidatas y los argumentos del `Job` (BR5.2, BR5.3), la orquestación del borrado por sesión con su acta (BR5.4–BR5.8), la comparación de testimonio del servidor y de la consola (BR3.6, BR3.7) y el armado de logs y rechazos sin la nota (BR3.9) se tratan como módulos guardia: `--cov-branch` con `fail_under = 100` en el `.coveragerc-guards` de U4, y Vitest con `branches: 100` sobre la función de la consola. Sus pruebas se escriben primero y en rojo (Testing Posture, Ordering; rules.md lo pide para BR3.6, BR3.9, BR5.2, BR5.3, BR5.5, BR5.6 y BR5.8) |
| NFR13.3 | nuevo | Las fronteras del módulo se respetan. | import-linter: `ethics_governance.domain` no importa `adapters`, `sqlalchemy` ni otros módulos; `ethics_governance` no importa `console_api` (BR2.1) y solo usa InterviewSession por `EthicsSessionPort`, HumanReview por su resolvedor y cada unidad por `Purgeable` (C24). Control negativo en la CI |

## 4. Dependencias nuevas de U13

- `services/session-api`: ninguna en ejecución (`argparse` y `hashlib` son de la biblioteca estándar). En
  desarrollo, `psutil` (ya la usa U12).
- `frontend`: ninguna.

Todas van fijadas en el lockfile de cada servicio, con `pip-audit` y `npm audit` en la CI (NFR10.9).

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y guardias (nivel 0) | `uv run --directory services/session-api pytest -m "not integration and not perf" tests/ethics_governance` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1), con el *canary* | `uv run --directory services/session-api pytest -m integration tests/ethics_governance` | Verde; 0 coincidencias del *canary* (NFR10.5, NFR10.22) |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf tests/ethics_governance` | NFR3.1, NFR3.3–NFR3.7, NFR3.9–NFR3.12 |
| Fronteras | `uv run --directory services/session-api lint-imports` | 0 violaciones, y el módulo de control negativo falla (NFR1.2, NFR13.3, NFR15.1) |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas; 100 % de ramas en la comparación (NFR13.2) |
| Accesibilidad, teclado y latencia de la consola (nivel 3) | `npx --prefix frontend playwright test e2e/ethics-governance.spec.ts` | 0 violaciones `serious` o `critical` (BR8.1); NFR3.2, NFR3.8 |
| Manifiesto del `Job` | `helm template deploy/jobs` → `kubeconform` → Kyverno CLI (política de U2) | Sin `CronJob`, `backoffLimit: 0`, salida solo a PostgreSQL y Redis (NFR1.3, NFR10.11) |
| Tipos y *lint* | `uv run --directory services/session-api mypy --strict .` y `uv run --directory services/session-api ruff check .` | 0 errores |
| Dependencias | `uv run --directory services/session-api pip-audit` y `npm --prefix frontend audit --audit-level=high` | Sin `HIGH` o `CRITICAL` con corrección |
| Borrado en el clúster (solo el humano, tras fusionar el PR del manifiesto; AUTONOMIA-01) | El humano lanza el `Job` ya fusionado de `deploy/jobs/`, primero con `--dry-run` y después sin él. Ningún plan de tareas ni *script* lo lanza | Código 0 y actas visibles con `kubectl exec deploy/veridicus-session-api -c session-api -- python -m session_api.ethics_governance.query retention-acts` |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| La comparación en Python no cabe en su tramo con la sesión máxima | Pasar a *hashes* enteros de las palabras (D2); el umbral no se cambia |
| Las dos implementaciones de la comparación divergen | Los mismos ejemplos versionados (NFR-U13-10) en las dos suites, y 100 % de ramas en las dos (NFR13.2) |
| `SET LOCAL` dentro del punto de guardado no se restaura si la inserción falla | Al fallar, ConsoleApi revierte el punto de guardado y con él el `SET LOCAL`; la prueba de NFR10.13 cubre los dos caminos |
