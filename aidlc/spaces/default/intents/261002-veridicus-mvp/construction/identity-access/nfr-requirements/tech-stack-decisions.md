# Decisiones de pila — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design vigente
de U3.** Sustituye a la revisión 1 del 2026-10-03. Las decisiones conservan su número; cada fila dice si
**se mantiene**, **cambia** o es **nueva**. Entran D13–D17 y los requisitos NFR13.1 y NFR14.1 (§4).
Ninguna se retira.

**Insumos.** Flujos de `functional-design/functional-spec.md` (functional-spec, revisión 2) y reglas de
`functional-design/rules.md` (rules); restricciones de pila (FastAPI, Python 3.12) y NFR10, NFR13 y
NFR14 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3); C1, C12, C16, C23
y C25 de `inception/contract-design/contract-summary.md` (contract-summary); NFR de U1, revisión 2
(paquete `veridicus-contracts`, cargador YAML seguro, `limits.load`); respuestas P1–P4 de
`nfr-requirements-questions.md`; `security-requirements.md`.

U3 es el primer Bolt que construye `services/session-api` (B2 de `bolt-plan.md`), así que estas
decisiones fijan la base del proceso que después amplían U4–U9, U12 y U13. Lo que ya fijan `team.md` y
requirements no se repite: Python 3.12, FastAPI, `uv`, `pytest` + Hypothesis, mypy estricto, Ruff,
capas `api/ → application/ → domain/` con `adapters/` e import-linter, excepciones de `libs/`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | se mantiene | Servidor ASGI | Uvicorn, 1 proceso por pod | Gunicorn con varios *workers* | Un pod por réplica es más simple de dimensionar; NFR8.1 limita la memoria por proceso | NFR8.1, NFR8.2 |
| D2 | cambia | Modelos y configuración | Pydantic v2 y `pydantic-settings` para los ajustes propios; las cifras de límite salen de C25 con `veridicus_contracts.limits.load` (el entorno solo baja). La configuración inválida o faltante impide arrancar | Variables leídas a mano; duplicar las cifras de sesión como ajustes propios | `team.md` («una configuración faltante impide arrancar el pod») y regla de `project.md` (catálogo único) | NFR10.3, NFR10.13 |
| D3 | se mantiene | Acceso a PostgreSQL | SQLAlchemy 2 (estilo síncrono) con psycopg 3 y `statement_timeout` por conexión | `asyncpg` sin ORM | La transacción compartida `UnitOfWork` de C12, los bloqueos de BR2.6 y BR2.12 y el punto de guardado de NFR10.21 son más simples en síncrono; Argon2id corre igual en el *threadpool* | NFR10.11, NFR10.15, NFR10.21 |
| D4 | se mantiene | Migraciones | Alembic, ejecutado solo por el `Job` de migraciones (nunca al arrancar) | SQL a mano | Prohibición de `project.md`; Alembic da historia y orden; la marca `veridicus-audit` va en el comentario de cada tabla | NFR11.1, NFR11.3 |
| D5 | se mantiene | Redis | `redis-py` con *timeout* de 0,5 s | `aioredis` | Mismo cliente que usarán las colas de U4 | NFR10.5, NFR10.11 |
| D6 | se mantiene | Hash de contraseñas | `argon2-cffi`, Argon2id `m = 65 536 KiB`, `t = 3`, `p = 1` | bcrypt, scrypt | P1 = A | NFR10.1 |
| D7 | cambia | Política de contraseñas | Validador propio en `domain/` con clases Unicode (`unicodedata`) tras NFC; la lista de D15 | Biblioteca externa de fuerza de contraseñas | P2; sin red y determinista; cierra R-04 | NFR10.2 |
| D8 | se mantiene | Tokens | `secrets.token_urlsafe(32)` para sesión y CSRF; en la base solo SHA-256 del token de sesión | JWT | La sesión debe ser revocable al instante (P5 de Contract Design) | NFR10.3, NFR10.4 |
| D9 | se mantiene | Limitador de intentos | Contador en Redis con `INCR` + `EXPIRE` por clave HMAC-SHA256 (clave de un Secret) | Tabla en PostgreSQL | P4 = A; caduca solo y no escribe en la base | NFR10.5 |
| D10 | cambia | Métricas | `prometheus-client` en un puerto interno, métricas propias de `session-api` (no C15) | OpenTelemetry | El clúster ya usa Prometheus; R-05 de la revisión 1 | NFR15.1, NFR10.23 |
| D11 | se mantiene | Pruebas de rendimiento | Marca `perf` de `pytest` en nivel 1, con `time.perf_counter` | Locust o k6 | Pocas peticiones y en proceso; la carga de NFR8 la hace U4 | NFR3.1–NFR3.4 |
| D12 | se mantiene | Reloj | Reloj inyectable en `application/` para probar caducidades | Esperas reales | Las pruebas de NFR10.3 no pueden esperar 12 horas | NFR10.3 |
| D13 | nueva | Validación de cuerpos y parámetros | `jsonschema` (Draft 2020-12) con `veridicus_contracts.registry`; un validador compilado por operación al arrancar, a partir de `contracts/api/console.v2.yaml` | Modelos Pydantic generados del OpenAPI; `openapi-core` | Una sola fuente de verdad (el contrato de U1) y el mismo validador que la suite de U1; no hay segundo esquema que pueda divergir | NFR10.18, NFR3.4 |
| D14 | nueva | Seguridad por ruta | `RouteSecurity` construido al arrancar desde las extensiones `x-veridicus-*` del OpenAPI, leído con el cargador YAML seguro de `veridicus-contracts` | Decoradores por ruta en el código | El contrato decide; el arranque falla ante una declaración mala (BR4.7); el cargador seguro es el único permitido por NFR10.4 de U1 | NFR10.9, NFR10.16 |
| D15 | nueva | Lista de contraseñas comunes | SecLists `Passwords/Common-Credentials/10k-most-common.txt` (licencia MIT), copiada a `services/session-api/` con su SHA-256 en un `SHA256SUMS` | Consultar un servicio en línea; una lista propia | Sin red, reproducible y con licencia compatible con un repositorio público | NFR10.2 |
| D16 | nueva | Contraseñas de los usuarios de base de datos | Roles gestionados por CloudNativePG (`managed.roles` con `passwordSecret`); la migración de U3 solo concede permisos. Si Infrastructure Design no lo adopta, la migración fija la contraseña con un verificador SCRAM-SHA-256 calculado en el `Job` | `ALTER ROLE … PASSWORD '<texto>'` en la migración | El texto nunca llega a una migración ni a los logs de PostgreSQL | NFR10.19 |
| D17 | nueva | Barrido de sesiones web | Tarea en proceso de `session-api` (al arrancar y cada 24 h) con `pg_try_advisory_xact_lock` | `CronJob` aparte | Sin manifiesto nuevo; el bloqueo asesor evita barridos simultáneos con varias réplicas | NFR8.3 |

## 2. Configuración

### Cifras de C25 (`contracts/limits.v1.yaml`, NFR-U3-01)

| Cifra | Valor | Variable que solo puede bajarla | Validación propia al arrancar |
|---|---|---|---|
| `web_session_max_s` | 43 200 s | `VERIDICUS_LIMIT_WEB_SESSION_MAX_S` | ≥ 3 600 y mayor que la inactividad |
| `web_session_idle_s` | 1 800 s | `VERIDICUS_LIMIT_WEB_SESSION_IDLE_S` | ≥ 300 |
| `username_max_chars` | 32 chars | `VERIDICUS_LIMIT_USERNAME_MAX_CHARS` | ≥ 3 |
| `password_max_chars` | 128 chars | `VERIDICUS_LIMIT_PASSWORD_MAX_CHARS` | ≥ 64 |

### Ajustes propios (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar |
|---|---|---|
| `VERIDICUS_ARGON2_MEMORY_KIB`, `_TIME_COST`, `_PARALLELISM` | 65536, 3, 1 | Mínimos 19 456, 2, 1 (recomendación de OWASP) |
| `VERIDICUS_ARGON2_MAX_CONCURRENT`, `VERIDICUS_ARGON2_QUEUE_TIMEOUT_S` | 2, 5 | Enteros positivos |
| `VERIDICUS_LOGIN_MAX_FAILURES`, `VERIDICUS_LOGIN_WINDOW_SECONDS` | 5, 900 | Enteros positivos. No van a C25: son política de seguridad y su unidad (intentos) no está en la lista cerrada de U1 |
| `VERIDICUS_TRUSTED_PROXY` | vacío | Lista de direcciones o redes; vacío solo en pruebas. El chart fija el pod CIDR y no lo deja vacío (`project.md`) |
| `VERIDICUS_RATE_LIMIT_HMAC_KEY` | — (Secret) | Obligatorio, ≥ 32 bytes |
| `VERIDICUS_DB_STATEMENT_TIMEOUT_MS`, `VERIDICUS_REDIS_TIMEOUT_MS` | 2000, 500 | Enteros positivos |
| `VERIDICUS_ACCESS_LOG_TIMEOUT_MS` | 500 | Entero entre 100 y 2 000 |
| `VERIDICUS_WEB_SESSION_PURGE_DAYS` | 7 | Entero ≥ 1 |

## 3. Dependencias

`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `alembic`,
`redis`, `argon2-cffi`, `prometheus-client`, `jsonschema` y `veridicus-contracts` (paquete de U1, como
dependencia de ruta del monorepo); en desarrollo `pytest`, `pytest-cov`, `pytest-asyncio`, `hypothesis`,
`httpx`, `mypy`, `ruff`, `import-linter`, `pip-audit`. Todas fijadas en `services/session-api/uv.lock`.

## 4. Calidad e idioma

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR13.1 | nuevo | `session-api` cumple la meta de cobertura desde B2. | ≥ 80 % de líneas en `services/session-api`, medido en CI y bloqueante (`team.md`). U3 no tiene módulos guardia de la lista de NFR13; las exclusiones (migraciones, código generado) van en la configuración y se justifican en el PR. | `pytest --cov-fail-under=80` |
| NFR14.1 | nuevo | Todo error y todo texto de M0 y M6 está en español, con identificadores en inglés. | Cada `code` del catálogo tiene un `detail` en español en el catálogo de mensajes (BR8.1, comprobado al arrancar por NFR10.16). Los textos de M0, M6 y el aviso de M8 salen de ese catálogo y pasan el escaneo de vocabulario prohibido. Los nombres de código y de métrica van en inglés según el glosario de `team.md`. | Nivel 0 |

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, estáticas y nivel 0 | `uv run --directory services/session-api pytest -m "not integration and not perf"` | Verde |
| Integración (nivel 1) con PostgreSQL y Redis reales | `uv run --directory services/session-api pytest -m integration` | Verde |
| Prueba común de la convención de auditoría | `uv run --directory services/session-api pytest -m audit_convention` | Verde (NFR11.1, NFR11.3) |
| Rendimiento de U3 | `uv run --directory services/session-api pytest -m perf` | NFR3.1–NFR3.4, NFR8.1, NFR8.4 |
| Cobertura del servicio | `--cov=services/session-api --cov-fail-under=80` en la configuración de `pytest` | ≥ 80 % de líneas (NFR13.1) |
| Tipos, *lint* y fronteras | `uv run --directory services/session-api mypy --strict .`, `ruff check`, `lint-imports` | 0 errores |
| Secretos | `gitleaks detect` en pre-commit y en la CI | 0 hallazgos (NFR10.19) |
| Humo sobre HTTPS | `scripts/smoke.sh <url-base>` | Código 0 (NFR10.22, NFR10.23) |
