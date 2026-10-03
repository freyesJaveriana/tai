# Decisiones de pila — U4 text-flow

**Insumos.** Flujos F1–F10 de `functional-design/functional-spec.md` (functional-spec) y reglas de
`functional-design/rules.md` (rules); pila fijada y NFR2, NFR4, NFR5, NFR9, NFR13 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); C2–C4, C6–C9, C13, C14 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P5 y S1–S3 de
`nfr-requirements-questions.md`; `security-requirements.md`; las decisiones de pila ya aprobadas de U2
(servidores `llama.cpp`, chart, `models.lock`) y de U3 (base de `session-api`).

Lo que ya fijan `team.md`, U2 y U3 no se repite: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 con
psycopg 3, Alembic en un `Job`, `redis-py`, `uv`, `pytest` + Hypothesis, mypy estricto, Ruff,
import-linter, React con TypeScript estricto, Vitest, Playwright, Problem Details desde `libs/`.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Modelo del juez | **Qwen2.5-7B-Instruct** en GGUF **Q4_K_M** (≈ 4,7 GB, Apache 2.0) | Llama-3.1-8B Q4_K_M; Qwen2.5-3B Q4_K_M | P1 = A: buen español y buena obediencia al esquema JSON; familia distinta a la del generador del Golden Dataset (NFR5.2) | NFR3.1, NFR4.4, NFR5.2 |
| D2 | Servidor del juez | `llama-server` de U2 con `--ctx-size 12288`, `--parallel 1`, hilos = núcleos físicos, caché del *prompt* activa, sin modo detallado ni registro de peticiones | Varias ranuras en paralelo | Una ranura hace repetible la salida con semilla fija (NFR4.2); la caché reutiliza las instrucciones entre turnos | NFR3.11, NFR4.2, NFR8.7, NFR10.8 |
| D3 | Modelo de *embeddings* | **`intfloat/multilingual-e5-base`** (768 dimensiones) en GGUF f16, en `llama-server --embedding --pooling mean`; prefijo `query: ` para afirmaciones y `passage: ` para pasajes; vectores normalizados (L2) | `bge-m3`; `multilingual-e5-small` | P2 = A: equilibrio entre calidad en español y velocidad en CPU; un solo tipo de servidor (U2 D1) | NFR9.1, NFR9.3, NFR3.4 |
| D4 | Umbral y calibración | `VERIDICUS_SIMILARITY_THRESHOLD = 0.80` en `values-cpu.yaml` y `values-gpu.yaml`; barrido de nivel 2 con `evaluation/threshold_sweep.py` y la regla de NFR4.1; el valor nuevo entra por PR con el reporte | Fijo sin calibrar; percentil de las alineadas | P3 = A; el cambio queda revisable (AUTONOMIA-01, FR9.2) | NFR4.1, NFR11.3 |
| D5 | Almacenamiento de vectores | Columna `vector(768)` de `pgvector`, distancia coseno (`<=>`), búsqueda **exacta** filtrada por `version_id` con índice B-tree; similitud = 1 − distancia | Índice HNSW o IVFFlat | Con ≈ 1 100 pasajes por versión la búsqueda exacta cumple NFR3.4, y un índice aproximado con filtro por versión puede devolver menos de 3 pasajes | NFR3.4, NFR8.9 |
| D6 | Segmentación | Pasajes de hasta **1 000 caracteres** con BR2.1 | 1 600 o 600 caracteres | S2 = A: holgura en la ventana de 512 *tokens* y *prompt* corto | NFR9.2 |
| D7 | Límite del *prompt* | Bloque de datos ≤ 6 000 *tokens* contados con `/tokenize` del servidor del juez; si se supera, `turn.error.system` sin llamar al juez | Recortar afirmaciones; ventana de 32 768 | S3 = A | NFR3.11, NFR3.12 |
| D8 | Formato del bloque de datos | JSON serializado en el mensaje `user` (afirmaciones con su índice y pasajes con su `passage_id`, cada pasaje una vez); instrucciones solas en `system` | Delimitadores de texto (`<datos>…</datos>`) | Un testimonio no puede «cerrar» un JSON bien serializado (T1) | NFR10.2, NFR5.1 |
| D9 | Validación de esquemas | `jsonschema` (Draft 2020-12, validador de formatos) con C2, C3, C4, C6 y C7 cargados de `contracts/` | Modelos Pydantic escritos a mano | Un solo origen: los esquemas de U1 y sus *fixtures* | NFR10.1, NFR10.4 |
| D10 | Cliente HTTP de ModelGateway | `httpx` síncrono con *timeouts* separados (conexión 2 s; lectura según el método) y verificación de URL interna al construir | `openai` SDK | Control explícito de *timeouts* y de destino; sin dependencia de un SDK externo | NFR1.1, NFR10.14 |
| D11 | Procesos de `session-api` | Dos procesos de la misma imagen: la API (solo HTTP) y un **trabajador** con tres hilos: ingesta de C3, indexador de C4 y revisión de plazos cada 15 s | Todo en el proceso de la API | La indexación y la ingesta no frenan las respuestas de la consola (NFR3.2) | NFR3.2, NFR3.6, NFR9.1 |
| D12 | `semantic-agent` | Un proceso con el bucle consumidor de C2 (un turno a la vez) y un servidor HTTP mínimo (FastAPI + Uvicorn en un hilo) solo para `/healthz`, `/readyz` y `/metrics` en un puerto interno | Servicio asíncrono con varios turnos a la vez | El juez atiende uno a la vez (D2); más concurrencia solo agrega espera | NFR8.7, NFR10.19 |
| D13 | Sondeo de la consola | TanStack Query v5 con `refetchInterval` de 2 000 ms o 15 000 ms según haya turnos en curso, y reintento con espera creciente hasta 30 s | Intervalo fijo con `setInterval` | P5 = A; NFR10.20 sin código propio de temporizadores | NFR3.7, NFR10.20 |
| D14 | Accesibilidad | `@axe-core/playwright` en nivel 3 y `vitest-axe` en componentes | Revisión manual sola | BR13.7 (WCAG 2.1 AA) | NFR14.1 |
| D15 | Pruebas de rendimiento y carga | Marca `perf` de `pytest` (nivel 1) para NFR3.2–NFR3.4; arnés de nivel 2 en `evaluation/` para NFR3.1, NFR9.1 y NFR4; `evaluation/load/run_batches.py` para NFR8 | k6 o Locust | Pocas peticiones en proceso; la carga real la limita el juez | NFR3, NFR8, NFR9 |
| D16 | Paridad de los *embeddings* | Al aprovisionar, 20 frases de control: el coseno entre el vector de `llama-server` y el de referencia guardado en el repositorio debe ser ≥ 0,99 | Confiar en la conversión a GGUF | Detecta una conversión defectuosa antes de calibrar el umbral | NFR4.1 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_SIMILARITY_THRESHOLD` | 0.80 (en los *values*, sin valor en el código) | Obligatorio; número finito entre 0,50 y 0,99, extremos incluidos (BR6.1) | `session-api`, `semantic-agent` |
| `VERIDICUS_TOP_K` | 3 | Entero igual a 3 en el MVP (C9, P4 de Functional Design) | `session-api` |
| `VERIDICUS_TURN_DEADLINE_BASE_SECONDS`, `_MAX_SECONDS` | 300, 3600 | Enteros; base ≥ 60 y máximo ≥ base | `session-api` |
| `VERIDICUS_DEADLINE_SWEEP_SECONDS` | 15 | Entero entre 5 y 60 | trabajador de `session-api` |
| `VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS`, `VERIDICUS_QUEUE_MAX_DELIVERIES` | 240, 3 | Reclamo > *timeout* del juez + *timeout* de *embeddings* | ambos |
| `VERIDICUS_JUDGE_URL`, `VERIDICUS_EMBEDDINGS_URL` | — | Obligatorias; solo URL internas (NFR1.1) | según el servicio |
| `VERIDICUS_JUDGE_PROMPT_SHA256` | — | Obligatorio; 64 hexadecimales; igual al del archivo montado | `semantic-agent` |
| `VERIDICUS_JUDGE_SEED` | 20261002 | Entero ≥ 0 | `semantic-agent` |
| `VERIDICUS_JUDGE_TIMEOUT_SECONDS`, `VERIDICUS_EMBEDDINGS_TIMEOUT_SECONDS` | 180, 30 | Juez < plazo base | ambos |
| `VERIDICUS_JUDGE_MAX_DATA_TOKENS` | 6000 | Entero ≤ ventana − 1 000 − 4 096 | `semantic-agent` |
| `VERIDICUS_PASSAGE_MAX_CHARS`, `VERIDICUS_EMBEDDINGS_BATCH` | 1000, 32 | Enteros positivos | trabajador de `session-api` |

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U4 se prueba en CPU sin modelos reales en los niveles 0 y 1. | El juez, los *embeddings* y el tokenizador se sustituyen por *fakes* deterministas que implementan el `Protocol` de C13; PostgreSQL + `pgvector` y Redis son reales en contenedor. Ninguna prueba de los niveles 0 y 1 descarga un modelo ni exige GPU. |
| NFR2.2 | Las metas de U4 se cumplen en el perfil CPU. | NFR3.1, NFR3.10, NFR9.1 y NFR8.5 se miden con `values-cpu.yaml`; el perfil GPU es opcional y su etapa corre a demanda. |
| NFR13.1 | Cobertura de líneas por servicio. | ≥ 80 % en `services/session-api`, `services/semantic-agent`, `libs/model_gateway`, `libs/integrity_policy` y `frontend`, medido en la CI y bloqueante. |
| NFR13.2 | 100 % de ramas en los módulos guardia de U4. | `services/semantic-agent/.../domain/threshold_guard.py` (BR7.3–BR7.6), `domain/alert_assembly.py` y `domain/judge_output_validation.py` (BR8.1–BR8.6), la validación de C7 al ingerir en `session-api` y `libs/integrity_policy/scanner.py` (BR12.1): `--cov-branch` con `fail_under = 100` sobre esos módulos. |
| NFR14.1 | Textos visibles en español y del catálogo. | M2–M4 solo usan cadenas del catálogo de mensajes y rótulos de U1 (BR12.4); una prueba de nivel 0 falla si un componente de U4 tiene un literal visible fuera del catálogo; identificadores en inglés según el glosario (`undocumented_fact`, `review_suggestion`, `handoff_package`). |
| NFR14.2 | La CoT está en español. | Las instrucciones lo exigen; el reporte de nivel 2 marca toda CoT con menos de un 20 % de palabras vacías del español y la meta es 0 marcadas. |

## 4. Dependencias nuevas de U4

- `services/semantic-agent`: `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`,
  `redis`, `httpx`, `jsonschema`, `prometheus-client`; las de desarrollo de U3.
- `services/session-api`: añade `jsonschema` y `pgvector` (adaptador de SQLAlchemy).
- `libs/model_gateway` y `libs/integrity_policy`: `httpx`; sin otras dependencias.
- `frontend`: `@tanstack/react-query`; en desarrollo `@axe-core/playwright` y `vitest-axe`.

Todas fijadas en el lockfile de cada servicio; `pip-audit` y `npm audit` en la CI (team-practices).

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y guardias (nivel 0) | `uv run --directory services/semantic-agent pytest -m "not integration and not perf"` y lo mismo en `services/session-api` y `libs/` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/semantic-agent pytest --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1) | `uv run --directory services/session-api pytest -m integration` y lo mismo en `services/semantic-agent` | Verde |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf` | NFR3.2–NFR3.4 |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| Evaluación de IA (nivel 2, fuera de la CI) | `uv run --directory evaluation python -m golden.run --profile cpu --report out/level2.json` | NFR3.1, NFR4.1–NFR4.5, NFR5.1, NFR5.2, NFR9.1, NFR14.2 |
| Barrido del umbral (nivel 2) | `uv run --directory evaluation python -m golden.threshold_sweep --from 0.70 --to 0.95 --step 0.01 --report out/sweep.json` | Regla de NFR4.1 |
| Carga (a demanda) | `uv run --directory evaluation python -m load.run_batches --sessions 50 --concurrency 3 --report out/nfr8.json` | NFR8.5 |
| Humo (nivel 3) | `scripts/smoke.sh <url-base>` | Código 0 en ≤ 120 s por caso (NFR3.10) |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en cada servicio | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El juez de 7B en CPU no llega al p95 de 60 s (el *prompt* y la generación son lentos en CPU) | Caché de las instrucciones, CoT de 20–80 palabras, límite de 6 000 *tokens*; si aun así falla, es un hallazgo que se resuelve por PR (hilos, perfil GPU para la demostración), nunca subiendo la meta |
| El esquema JSON por gramática de `llama-server` no garantiza todo C6 | La validación de C6 en U4 es la que manda (BR8.1) |
| La conversión de `multilingual-e5-base` a GGUF da vectores distintos | Comprobación de paridad D16 antes de calibrar |
| El umbral calibrado sobre un solo escenario no generaliza | Es el alcance del PRD (un escenario); el valor y su reporte quedan versionados para recalibrar por PR |
