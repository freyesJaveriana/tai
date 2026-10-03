# Decisiones de pila — U3 identity-access

**Insumos.** Flujos de `functional-design/functional-spec.md` (functional-spec) y reglas de
`functional-design/rules.md` (rules); restricciones de pila (FastAPI, Python 3.12) y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C12 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P4 de
`nfr-requirements-questions.md`; `security-requirements.md`.

U3 es el primer Bolt que construye `services/session-api` (B2 de `bolt-plan.md`), así que D1–D6 fijan
la base del proceso que después amplían U4–U7. Lo que ya fijan `team.md` y requirements no se repite:
Python 3.12, FastAPI, `uv`, `pytest` + Hypothesis, mypy estricto, Ruff, capas
`api/ → application/ → domain/` con `adapters/` e import-linter, Problem Details desde `libs/`.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Servidor ASGI | Uvicorn, 1 proceso por pod | Gunicorn con varios *workers* | Un pod por réplica es más simple de dimensionar; NFR8.1 limita la memoria por proceso | NFR8.1, NFR8.2 |
| D2 | Modelos y configuración | Pydantic v2 y `pydantic-settings`; la configuración inválida o faltante impide arrancar | Variables leídas a mano | Regla de team-practices «una configuración faltante impide arrancar el pod» | NFR10.13 |
| D3 | Acceso a PostgreSQL | SQLAlchemy 2 (estilo síncrono) con psycopg 3 y `statement_timeout` por conexión | `asyncpg` sin ORM | La transacción compartida `UnitOfWork` de C11 y el bloqueo de BR2.6 son más simples en síncrono; Argon2id corre igual en el *threadpool* | NFR10.11, NFR10.15 |
| D4 | Migraciones | Alembic, ejecutado solo por el `Job` de migraciones (nunca al arrancar) | SQL a mano | Prohibición de `project.md`; Alembic da historia y orden | NFR11.1 |
| D5 | Redis | `redis-py` con *timeout* de 0,5 s | `aioredis` | Mismo cliente que usarán las colas de U4 | NFR10.5, NFR10.11 |
| D6 | Hash de contraseñas | `argon2-cffi`, Argon2id `m = 65 536 KiB`, `t = 3`, `p = 1` | bcrypt, scrypt | P1 = A | NFR10.1 |
| D7 | Política de contraseñas | Validador propio en `domain/` y lista de contraseñas comunes en un archivo con su SHA-256 | Biblioteca externa de fuerza de contraseñas | P2; sin red y determinista | NFR10.2 |
| D8 | Tokens | `secrets.token_urlsafe(32)` para sesión y CSRF; en la base solo SHA-256 del token de sesión | JWT | La sesión debe ser revocable al instante (P5 de Contract Design) | NFR10.3, NFR10.4 |
| D9 | Limitador de intentos | Contador en Redis con `INCR` + `EXPIRE` por clave HMAC-SHA256 (clave de un Secret) | Tabla en PostgreSQL | P4 = A; caduca solo y no escribe en la base | NFR10.5 |
| D10 | Métricas | `prometheus-client` en `/metrics` (puerto interno) | OpenTelemetry | C15 ya es Prometheus | NFR15.1 |
| D11 | Pruebas de rendimiento | Marca `perf` de `pytest` en nivel 1, con `time.perf_counter` | Locust o k6 | Pocas peticiones y en proceso; la carga de NFR8 la hace U4 | NFR3.1–NFR3.3 |
| D12 | Reloj | Reloj inyectable en `application/` para probar caducidades | Esperas reales | Las pruebas de NFR10.3 no pueden esperar 12 horas | NFR10.3 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar |
|---|---|---|
| `VERIDICUS_SESSION_IDLE_SECONDS` | 1800 | Entero entre 300 y 3 600 |
| `VERIDICUS_SESSION_MAX_SECONDS` | 43200 | Entero entre 3 600 y 86 400, mayor que el anterior |
| `VERIDICUS_ARGON2_MEMORY_KIB`, `_TIME_COST`, `_PARALLELISM` | 65536, 3, 1 | Mínimos 19 456, 2, 1 (recomendación de OWASP) |
| `VERIDICUS_LOGIN_MAX_FAILURES`, `VERIDICUS_LOGIN_WINDOW_SECONDS` | 5, 900 | Enteros positivos |
| `VERIDICUS_TRUSTED_PROXY` | vacío | Lista de direcciones o redes; vacío = usar la dirección de la conexión |
| `VERIDICUS_RATE_LIMIT_HMAC_KEY` | — (Secret) | Obligatorio, ≥ 32 bytes |

## 3. Dependencias

`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `alembic`,
`redis`, `argon2-cffi`, `prometheus-client`; en desarrollo `pytest`, `pytest-cov`, `hypothesis`,
`httpx`, `mypy`, `ruff`, `import-linter`, `pip-audit`. Todas fijadas en `services/session-api/uv.lock`.

## 4. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias y nivel 0 | `uv run --directory services/session-api pytest -m "not integration and not perf"` | Verde |
| Integración (nivel 1) con PostgreSQL y Redis reales | `uv run --directory services/session-api pytest -m integration` | Verde |
| Rendimiento de U3 | `uv run --directory services/session-api pytest -m perf` | NFR3.1–NFR3.3 |
| Cobertura del servicio | `--cov=services/session-api --cov-fail-under=80` en la configuración de `pytest` | ≥ 80 % de líneas |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` | 0 errores |
