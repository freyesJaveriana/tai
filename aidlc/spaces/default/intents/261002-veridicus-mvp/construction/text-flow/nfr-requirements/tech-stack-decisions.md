# Decisiones de pila — U4 text-flow

**Revisión 2 (2026-11-22).** Esta revisión sustituye a la revisión 1 del 2026-10-03. Es la segunda pasada,
motivada por el cambio 01 (DT27), la adenda 02 y el Functional Design revisión 2 de U4.

**Qué cambia.**
- Las decisiones sobre el juez, los *embeddings*, el umbral, los vectores, la segmentación y el *prompt*
  quedan «Retiradas». Son D1–D8, D10 y D16.
- Esas decisiones pasan a U11, que es dueña del analizador y del `ModelGateway`, o salen del alcance.
- Lo nuevo empieza en D17.

**Insumos.**
- `functional-design/functional-spec.md` (functional-spec): flujos F3–F15.
- `functional-design/rules.md` (rules): las reglas.
- `inception/requirements-analysis/requirements.md` (requirements): la pila fijada y NFR2, NFR13 y NFR14.
- `inception/contract-design/contract-summary.md` (contract-summary): C1–C3, C6, C10, C15–C18, C21 y C25.
- `nfr-requirements-questions.md`: las respuestas P5 = A, S1 = A (adaptada), P6 = A y P7 = A.
- `security-requirements.md`.
- Las pilas ya aprobadas de U2, U3, U10 y U11.

**Lo que no se repite.** Esto ya lo fijan `team.md`, U2 y U3:
- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 con psycopg 3 (solo en `session-api`) y Alembic en un
  `Job`;
- `redis-py`, `uv`, `pytest` con Hypothesis, mypy estricto, Ruff e import-linter;
- React con TypeScript estricto, Vitest y Playwright;
- Problem Details desde `libs/`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | Retirado | Modelo del juez | Pasa a U11 (perfiles de C18) | — | Cambio 01 | — |
| D2 | Retirado | Servidor del juez | Pasa a U2 y U11 | — | Cambio 01 | — |
| D3 | Retirado | Modelo de *embeddings* | Sale | — | Cambio 01 | — |
| D4 | Retirado | Umbral | Sale | — | Cambio 01 | — |
| D5 | Retirado | Vectores con `pgvector` | Sale | — | Cambio 01 | — |
| D6 | Retirado | Segmentación | Sale | — | Cambio 01 | — |
| D7 | Retirado | Límite del *prompt* | Pasa a U11 | — | Cambio 01 | — |
| D8 | Retirado | Formato del bloque de datos | Pasa a U11 | — | Cambio 01 | — |
| D9 | cambia | Validación de esquemas | `jsonschema` (Draft 2020-12, con validador de formatos) con C2, C3 y C6 cargados de `contracts/` | Modelos Pydantic escritos a mano | Un solo origen: los esquemas de U1 y sus *fixtures* | NFR10.1, NFR10.4 |
| D10 | Retirado | Cliente HTTP del `ModelGateway` | Pasa a U11 | — | Cambio 01 | — |
| D11 | cambia | Procesos de `session-api` | Dos procesos de la misma imagen: la API (solo HTTP) y un **trabajador** con tres hilos (ingesta de C3, supervisor de plazos cada 15 s y liberación de las corridas en espera) | Todo en el proceso de la API | La ingesta no frena las respuestas de la consola | NFR3.2, NFR3.6, NFR3.13 |
| D12 | cambia | `semantic-agent` | Un proceso con el bucle consumidor de C2 (una corrida a la vez, que llama `analyze` de U11 en proceso), un hilo que renueva el reclamo y un servidor HTTP mínimo (FastAPI con Uvicorn en un hilo) solo para `/healthz`, `/readyz` y `/metrics` | Servicio asíncrono con varias corridas a la vez | Una corrida a la vez (FD-U4-09) | NFR8.7, NFR10.19 |
| D13 | cambia | Sondeo de la consola | TanStack Query v5 con `refetchInterval` de `poll_interval_active_s` o `poll_interval_s`, leídos del catálogo de C25 que se genera en *build* desde `contracts/limits.v1.yaml`, y reintento con espera creciente hasta 30 s | Intervalo fijo con `setInterval` | P5 = A; NFR10.20 sin código propio de temporizadores | NFR3.7, NFR10.20 |
| D14 | se mantiene | Accesibilidad | `@axe-core/playwright` en nivel 3 y `vitest-axe` en los componentes | Revisión manual sola | WCAG 2.1 AA | NFR14.1 |
| D15 | cambia | Pruebas de rendimiento y carga | Marca `perf` de `pytest` (nivel 1) para NFR3.1–NFR3.3 y NFR3.13; `evaluation/load/run_batches.py` para NFR8 | k6 o Locust | Pocas peticiones en proceso; la carga real la limita el modelo | NFR3, NFR8 |
| D16 | Retirado | Paridad de los *embeddings* | Sale | — | Cambio 01 | — |
| D17 | nuevo | Renovación del reclamo | `XCLAIM <stream> <grupo> <consumidor> 0 <id> JUSTID` cada 15 s desde un hilo del trabajador, mientras dura la corrida; `claim_idle_ms` = 60 000 | `claim_idle_ms` mayor que el modo final más largo (más de 1 h) | Un trabajador caído se detecta en 1 min, aunque un modo final dure horas | NFR10.15 (NFR-U4-06) |
| D18 | nuevo | Fronteras de `semantic-agent` | Contratos de import-linter: `semantic-agent-no-anonymizer` (prohíbe `libs.anonymizer`) y `semantic-agent-no-db` (prohíbe `psycopg`, `sqlalchemy` y `asyncpg`); además, una comprobación del lockfile | Revisión manual del PR | Hace falta un control negativo automático | NFR1.3, NFR10.6 |
| D19 | nuevo | Cancelación | `SET veridicus:run-cancelled:{run_id} 1 EX <plazo restante + 120>`, que escribe `session-api`; el trabajador solo hace `EXISTS` | Una columna en la base, consultada por el trabajador | El trabajador no tiene base de datos (ADR-002, CD-06) | NFR1.6, NFR10.21 |
| D20 | nuevo | Límites | `veridicus_contracts.limits.load()` de U1 en los dos servicios; las variables `VERIDICUS_LIMIT_<NOMBRE>` solo bajan una cifra | Constantes en el código de U4 | Un solo catálogo (C25) | NFR10.1, NFR10.25 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_PROFILES_PATH` | — | Obligatorio. Archivo de perfiles válido contra C18 | ambos |
| `VERIDICUS_LIMITS_PATH` | `contracts/limits.v1.yaml` en la imagen | Obligatorio. Catálogo válido y sin nulos | ambos |
| `VERIDICUS_LIMIT_<NOMBRE>` | — | Opcional. Solo puede bajar la cifra de C25: si la sube, el proceso no arranca | ambos |
| `VERIDICUS_ANONYMIZER_PROXY_URL` | — | Obligatorio si algún perfil habilitado tiene destino externo. Solo admite una dirección interna (NFR1.1) | `semantic-agent` |
| `VERIDICUS_DEADLINE_SWEEP_SECONDS` | 15 | Entero entre 5 y 60 | trabajador de `session-api` |
| `VERIDICUS_CLAIM_RENEW_SECONDS` | 15 | Entero ≥ 5 y < `claim_idle_ms` / 3 000 | `semantic-agent` |
| `VERIDICUS_FAILED_STREAM_MAXLEN` | 1000 | Entero entre 100 y 10 000 | ambos |

**Ajustes retirados de la revisión 1:**
- `VERIDICUS_SIMILARITY_THRESHOLD`, `VERIDICUS_TOP_K` y `VERIDICUS_TURN_DEADLINE_*`;
- `VERIDICUS_QUEUE_*`, `VERIDICUS_JUDGE_*`, `VERIDICUS_EMBEDDINGS_*` y `VERIDICUS_PASSAGE_MAX_CHARS`.

Las cifras de la cola y del plazo de esos ajustes salen ahora de C25 (NFR-U4-01, NFR-U4-04).

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | cambia | Todo U4 se prueba en CPU sin modelos reales en los niveles 0 y 1. | `analyze` (C17) y el `ModelGateway` de U11 se sustituyen por *fakes* deterministas. PostgreSQL y Redis son reales, en contenedor. Ninguna prueba de los niveles 0 y 1 descarga un modelo, llama a un proveedor ni exige GPU |
| NFR2.2 | cambia | Las metas de U4 se cumplen en la máquina de desarrollo con CPU. | NFR3.1–NFR3.3, NFR3.13 y NFR8.12 se miden en CPU. NFR3.10 y NFR8.5 usan `comercial-piloto`. Los perfiles locales grandes van en la etapa GPU, a demanda |
| NFR13.1 | cambia | Cobertura de líneas por servicio. | ≥ 80 % en `services/session-api`, `services/semantic-agent` y `frontend`, medido en la CI y bloqueante. `libs/incoherence_analyzer` y `libs/integrity_policy` las mide U11 |
| NFR13.2 | cambia | 100 % de ramas en los módulos guardia de U4. | La segunda línea de C6 en la ingesta (BR8.1–BR8.6), la decisión de incidente y bloqueo (BR16.1–BR16.5) y el cálculo del plazo (NFR3.5): `--cov-branch` con `fail_under = 100` sobre esos módulos |
| NFR14.1 | se mantiene | Los textos visibles están en español y salen del catálogo. | M3 y M4 y el aviso solo usan cadenas del catálogo de mensajes y rótulos de U1. Una prueba de nivel 0 falla si un componente de U4 tiene un literal visible fuera del catálogo. Los identificadores van en inglés, según el glosario |
| NFR14.2 | Retirado | La CoT está en español. | Pasa a U11 (`observaciones`) |

## 4. Dependencias nuevas de U4

- `services/semantic-agent`: `fastapi`, `uvicorn`, `pydantic-settings`, `redis`, `jsonschema`,
  `prometheus-client` y `libs-incoherence-analyzer` (U11). **No lleva** `sqlalchemy`, `psycopg` ni
  `libs-anonymizer` (D18).
- `services/session-api`: añade `jsonschema`. Sale `pgvector`.
- `frontend`: `@tanstack/react-query`; en desarrollo, `@axe-core/playwright` y `vitest-axe`.

Todas van fijadas en el lockfile de cada servicio, con `pip-audit` y `npm audit` en la CI.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y guardias (nivel 0) | `uv run --directory services/semantic-agent pytest -m "not integration and not perf"`, y lo mismo en `services/session-api` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1) | `uv run --directory services/session-api pytest -m integration`, y lo mismo en `services/semantic-agent` | Verde |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf` | NFR3.1–NFR3.3, NFR3.13 |
| Fronteras de `semantic-agent` | `uv run --directory services/semantic-agent lint-imports` y `uv run --directory services/semantic-agent python -m scripts.check_lock_no_anonymizer` | 0 violaciones, y el control negativo falla (NFR1.3) |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| Carga (a demanda) | `uv run --directory evaluation python -m load.run_batches --profile comercial-piloto --sessions 50 --concurrency 3 --report out/nfr8.json` | NFR8.5 |
| Humo (nivel 3) | `scripts/smoke.sh <url-base>` | Código 0, con ≤ 300 s por caso (NFR3.10) |
| Límites del piloto (P7 = A, fuera de Git) | `python scripts/count-transcript-limits.py <ruta-del-corpus-fuera-de-git>` (lo corre el humano) | Imprime 2 cifras. Cada una debe caber con un 25 % de margen (NFR-U4-03) |
| Tipos y *lint* | `mypy --strict` y `ruff check` en cada servicio | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Una transcripción de 250 000 caracteres no cabe en el presupuesto de U10 o en la latencia de U11 | NFR-U4-02: U10 y U11 repiten sus comprobaciones con 250 000 en sus PR y `model_call_timeout_s` ≥ 270 s. Si una falla, falla ese PR; los umbrales no se bajan |
| El piloto tiene un turno de más de 16 000 caracteres o más de 1 600 turnos | NFR-U4-03: la cifra se sube por el PR de U1 antes del código |
| Un modo final largo deja la cola parada para las demás sesiones | El plazo suma la cola con un tope (NFR3.5), y la profundidad se vigila (`observability-requirements.md`) |
| La renovación del reclamo falla sin aviso | El trabajador termina la corrida si una renovación falla dos veces seguidas. El mensaje vuelve por `XAUTOCLAIM` y se registra `WARNING` |
