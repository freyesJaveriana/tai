# Decisiones de pila — U7 forensic-report

**Insumos.** Flujos F1–F7 de `functional-design/functional-spec.md` (functional-spec), reglas de
`functional-design/rules.md` (rules) y entidades de `entities.md`; NFR2, NFR7, NFR10, NFR11, NFR13 y
NFR14 de `inception/requirements-analysis/requirements.md` (requirements); C1, C8, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); `nfr-requirements-questions.md`
(sin preguntas nuevas); `security-requirements.md`; las decisiones de pila ya aprobadas de U3 (base de
`session-api`), U4 (consola, escáner) y U5 (bloqueo de la ronda).

Lo que ya fijan `team.md`, U2, U3, U4 y U5 no se repite: Python 3.12, FastAPI y Uvicorn (U3 D1),
Pydantic v2 y `pydantic-settings` (U3 D2), SQLAlchemy 2 síncrono con psycopg 3 y `statement_timeout`
(U3 D3), Alembic en un `Job` (U3 D4), `prometheus-client` (U3 D10), marca `perf` de `pytest` (U3 D11),
reloj inyectable (U3 D12), TanStack Query (U4 D13), `@axe-core/playwright` y `vitest-axe` (U4 D14),
`libs/integrity_policy` con `scan(text, literal_sources)` (U4), `SELECT … FOR UPDATE` y `lock_timeout`
de 2 s (U5 D3), *engine* con `hide_parameters=True` (U5 D5), pruebas de concurrencia con barrera y
PostgreSQL real (U5 D9), perfil `restricted` (U2 NFR10.2), Problem Details desde `libs/`, `uv`, mypy
estricto, Ruff, import-linter, Vitest y Playwright. U7 no añade dependencias nuevas de terceros.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Plantilla del reporte | Render con código Python propio en `forensic_report/domain/render.py`: funciones puras que escriben secciones fijas a partir de `ReportContent`, con los textos fijos tomados del catálogo de U1; `format_version = "1"` | Jinja2; generar el Markdown con una biblioteca de Markdown | Sin dependencia nueva, determinista y probable con 100 % de casos; una plantilla de texto libre mezcla espacios y saltos difíciles de fijar | NFR10.9, NFR14.1, BR3.2 |
| D2 | Canonicalización | `unicodedata.normalize("NFC")` de cada texto, saltos `\n` (se convierten `\r\n` y `\r`), sin espacios al final de línea, un salto final, orden explícito (turnos por número; sugerencias por número de turno y orden de creación; paquetes por turno; decisiones por `at`, `seq`), fechas `YYYY-MM-DDTHH:MM:SSZ` y números con formato fijo; nunca se itera un `dict` o un `set` sin ordenar | Confiar en el orden de la base | BR3.2: los mismos datos dan los mismos bytes, en cualquier proceso | NFR10.9, NFR11.3 |
| D3 | Escape del Markdown | Todo texto del caso (turnos, CoT, notas, reformulaciones, citas) se emite dentro de bloques citados con prefijo `> ` por línea y se escapan los caracteres que abren estructura (`#`, `` ` ``, `<`, `[`, `|`, `*`, `_` al inicio) con barra invertida; los delimitadores «» de cita literal se conservan | Emitir el texto tal cual; HTML | Un testimonio no puede crear encabezados, enlaces ni HTML en el reporte, y el escaneo sabe qué tramos son literales | NFR10.4, NFR10.9 |
| D4 | Escaneo | `scan(text, literal_sources)` de U4 sobre el Markdown completo; `literal_sources` se arma con los tramos de turnos, fragmentos, citas, pasajes, notas y reformulaciones a medida que se renderizan (el render devuelve los bytes y la lista de tramos) | Escanear cada pieza por separado antes de renderizar | Escanea exactamente lo que se guarda, incluidos los textos de la plantilla, y devuelve la ubicación por sección | NFR10.9 |
| D5 | Puerto de almacenamiento | `ReportStore` en `application/ports.py` con `write_new(report_version_id, data, deadline)`, `read(report_version_id, deadline)`, `delete(...)` y `list_entries()`; adaptador `adapters/volume_report_store.py` sobre el sistema de archivos con `os.open(O_CREAT \| O_EXCL \| O_WRONLY \| O_NOFOLLOW, 0o600)`, `os.fsync`, `os.link` + `os.unlink` (sin reemplazo) y `fsync` del directorio, y `os.chmod(0o400)` al terminar | Almacén de objetos (MinIO) dentro del clúster; guardar el Markdown en PostgreSQL (`bytea`) | FR7.3 pide el volumen persistente; un almacén de objetos es otro servicio que operar; en la base, el archivo dejaría de ser la evidencia descargable independiente y crecería el respaldo de la base | NFR10.15, NFR11.4, NFR10.5 |
| D6 | *Timeout* del volumen | Cada operación del adaptador corre en un `ThreadPoolExecutor` propio de 2 hilos con `future.result(timeout=VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS)` | Sin *timeout* (las llamadas al sistema de archivos bloquean); `asyncio` con `aiofiles` | team-practices exige *timeout* en toda E/S; en una API síncrona (U3 D3) un hilo con espera acotada es lo más simple. Límite: el hilo no se puede cancelar; si vence, su archivo queda como huérfano para el barrido | NFR10.17 |
| D7 | Atomicidad | La consolidación usa la `UnitOfWork` de C11 y empieza con `open_round(..., for_update=True)`; el archivo se escribe **dentro** de la transacción (después de la guardia y antes de insertar), con el plazo total de 10 s y `idle_in_transaction_session_timeout` de 15 s | Escribir el archivo después del *commit* (fila antes que archivo); aislamiento `SERIALIZABLE` con reintentos | P2 = A (archivo antes que fila: nunca hay versión sin archivo); el bloqueo de la ronda serializa a la vez la consolidación y las decisiones de U5 sin reintentar operaciones no idempotentes | NFR10.12–NFR10.14 |
| D8 | Barrido de huérfanos | Función de arranque en `application/orphan_sweep.py`, llamada antes de marcar el proceso listo; solo borra nombres `<uuid>.md.tmp` o `<uuid>.md` sin fila y con `st_mtime` de más de 300 s; 1 réplica con `Recreate` | Barrido periódico; borrar sin margen | P2 = A pide el barrido al arrancar; el margen y la réplica única cierran la carrera con una consolidación en vuelo (hallazgo R-02 del Functional Design) | NFR10.16, NFR8.6 |
| D9 | Descarga | Lectura completa del archivo (≤ 2 MiB, NFR8.5) en memoria, `hashlib.sha256`, comparación con `hmac.compare_digest` y respuesta `Response` con las cabeceras de NFR10.4 | `FileResponse` o *streaming* | La comprobación debe terminar **antes** de enviar el primer byte (BR5.1); con ≤ 2 MiB cabe en memoria (NFR8.1) | NFR3.4, NFR11.3 |
| D10 | Guardias como código puro | `domain/consolidation_guard.py` (BR2.1–BR2.7: recibe el `snapshot`, la ronda y el conteo y devuelve `Allowed` o el primer bloqueo en el orden fijo, más la lista completa para la vista) y `domain/correction_policy.py` (BR6.1–BR6.5); la orquestación de BR4 en `application/consolidate.py` | Reglas repartidas en la ruta | Se prueban celda por celda con 100 % de ramas sin base (AUTONOMIA-03); la orquestación se prueba con fallos inyectados en el puerto `ReportStore` y en C11 | NFR13.2 |
| D11 | Consola | Mutación de TanStack Query sin reintento (`retry: false`) y sin actualización optimista para finalizar, consolidar, corregir y descartar; el botón se deshabilita mientras la mutación está pendiente; la descarga es un `<a href>` a la ruta de C1, y «Copiar SHA-256» usa `navigator.clipboard.writeText` con un anuncio `aria-live="polite"` | Reintentos automáticos; descarga con `fetch` + `Blob` | Ninguna operación no idempotente se repite sola (NFR10.18); el enlace deja la descarga al navegador (NFR3.11) | NFR3.9, NFR3.11, NFR10.18 |
| D12 | Arnés de MTTV | `evaluation/golden/mttv.py` lee los `session_id` del reporte JSON de la corrida de nivel 2, consulta la API con una cuenta de analista sintética y calcula con `mttv_seconds` de `domain/mttv.py` (paquete instalado en el arnés) | Consultar la base directamente; cronometrar en el navegador | Solo usa marcas que guarda el sistema (NFR7) y la misma función que la métrica; no necesita credenciales de la base | NFR7.1, NFR7.3 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_REPORTS_DIR` | `/var/lib/veridicus/reports` (punto de montaje del PVC) | Obligatorio; ruta absoluta; existe, es un directorio, escribible y con modo `0700` | API de `session-api` |
| `VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS` | 5 | Entero entre 1 y 30 | API de `session-api` |
| `VERIDICUS_REPORT_CONSOLIDATION_TIMEOUT_SECONDS` | 10 | Entero mayor que `STORAGE_TIMEOUT` + 2 y menor que `idle_in_transaction_session_timeout` (15 s) | API de `session-api` |
| `VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS` | 300 | Entero mayor que `CONSOLIDATION_TIMEOUT` + 60 | API de `session-api` |
| `VERIDICUS_REPORT_MIN_FREE_BYTES` | 52428800 (50 MiB) | Entero ≥ 2 × 2 MiB | API de `session-api` |

Una configuración faltante o inválida impide arrancar el pod (team-practices; NFR10.19).

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U7 se prueba en CPU y sin modelos. | U7 no llama a modelos; los niveles 0 y 1 corren con PostgreSQL real y un directorio real del contenedor como volumen; ninguna prueba exige GPU ni descarga nada. |
| NFR10.22 | El render es determinista en cualquier proceso (BR3.2). | Pruebas de nivel 0: (a) renderizar dos veces el caso de 100 turnos da los mismos bytes; (b) propiedad (Hypothesis) que baraja el orden de turnos, sugerencias, decisiones y paquetes de entrada y obtiene los mismos bytes; (c) dos subprocesos con `PYTHONHASHSEED` distintos dan el mismo SHA-256; (d) textos con `\r\n`, NFD y espacios finales producen NFC, LF y sin espacios finales; (e) un *golden file* sintético de `format_version` 1 coincide byte a byte (cambiar la plantilla exige actualizarlo en el mismo PR y subir `format_version` si cambia la forma). |
| NFR13.1 | Cobertura de líneas. | ≥ 80 % en `services/session-api` (incluido el módulo `forensic_report`) y en `frontend`, medido en la CI y bloqueante. |
| NFR13.2 | 100 % de ramas en los módulos guardia de U7 (BR2, BR4, BR6). | `services/session-api/src/session_api/forensic_report/domain/consolidation_guard.py` (BR2.1–BR2.7), `application/consolidate.py` (orquestación de BR4.1–BR4.3 con cada rama de fallo y limpieza), `application/orphan_sweep.py` (BR4.3), `adapters/volume_report_store.py` (BR4.1, BR4.3, BR5.1) y `domain/correction_policy.py` (BR6.1–BR6.5): `--cov-branch` con `fail_under = 100` sobre esos módulos. La guardia se prueba con la tabla completa de combinaciones de estado de sesión, turnos en curso, ronda abierta y pendientes, incluido el orden de BR2.5. |
| NFR13.3 | Las fronteras del módulo se respetan. | import-linter: `forensic_report.domain` no importa `api`, `adapters`, `sqlalchemy` ni otros módulos; ForensicReport solo usa InterviewSession, HumanReview y TruthFrame a través de `contracts/python/forensic_ports.py` (C11); `consolidate` solo lo importa la ruta (NFR11.2). Control negativo en la CI. |
| NFR14.2 | Identificadores según el glosario. | `report_version`, `forensic_report`, `consolidation_blocker`, `report_file`, `mttv_sample`, `undocumented_fact`, `review_suggestion`; la comprobación de glosario de U1 da 0 hallazgos en el módulo. |

## 4. Accesibilidad

BR8.4 reutiliza la base de U4 (D14 de U4): `vitest-axe` sobre los diálogos de finalizar y consolidar,
la vista del reporte, la lista de versiones y la copia de trabajo, y `@axe-core/playwright` en
`frontend/e2e/report.spec.ts`. Criterios: 0 violaciones `serious` o `critical`; consolidar, copiar el
SHA-256, descargar, corregir y descartar se completan solo con teclado; los diálogos modales (finalizar,
consolidar, descartar) atrapan el foco, se cierran con `Esc` como «Cancelar» y devuelven el foco al botón
que los abrió; la versión vigente y el estado de cada sugerencia llevan texto además del color; el
SHA-256 se muestra completo en fuente monoespaciada y «SHA-256 copiado» se anuncia por `aria-live`.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, render y guardias (nivel 0) | `uv run --directory services/session-api pytest tests/forensic_report -m "not integration and not perf"` | Verde; NFR7.3, NFR10.9, NFR10.10, NFR10.22, NFR14.1 |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest tests/forensic_report --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1): permisos, CSRF, atomicidad, carreras, fallos inyectados, barrido, integridad, logs y métricas | `uv run --directory services/session-api pytest tests/forensic_report -m integration` | Verde; NFR10.1–NFR10.21, NFR11.1–NFR11.6, NFR8.4, NFR8.5, NFR8.8, NFR15.1–NFR15.4 |
| Rendimiento en proceso | `uv run --directory services/session-api pytest tests/forensic_report -m perf` | NFR3.1–NFR3.8, NFR7.2, NFR8.1–NFR8.3 |
| Prueba común de auditoría (U3) | `uv run --directory services/session-api pytest -m integration -k audit_convention` | `ReportVersion` registrada; `UPDATE`/`DELETE` fallan |
| Verificación del almacén | `uv run --directory services/session-api python -m session_api.forensic_report.verify_store` | Código 0 (NFR10.20) |
| Políticas de manifiestos (montajes, réplicas, estrategia) | `helm template deploy/charts/veridicus -f deploy/values-cpu.yaml \| kubeconform -strict - && kyverno apply deploy/policies/ --resource -` | 0 violaciones (NFR1.2, NFR8.6) |
| Regla de volumen | `promtool test rules deploy/prometheus/tests/volume.yaml` | Verde (NFR15.3) |
| Consola | `npm --prefix frontend run test -- --coverage src/report` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas (NFR3.9, NFR10.4, NFR10.18) |
| E2E y accesibilidad (nivel 3) | `npx --prefix frontend playwright test e2e/report.spec.ts` | 0 fallos (NFR8.7, NFR3.10, NFR3.11, §4) |
| MTTV (nivel 2, fuera de la CI, tras la revisión humana del Golden Dataset) | `uv run --directory evaluation python -m golden.mttv --run out/level2.json --report out/mttv.json` | Media < 600 s (NFR7.1) |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en `services/session-api` | 0 errores (NFR13.3, NFR11.2, NFR1.1) |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El hilo del volumen que vence (D6) no se puede cancelar y su archivo puede aparecer después del *rollback* | Queda sin fila y el barrido lo borra en el siguiente arranque (NFR10.16); `verify_store` lo lista mientras tanto (NFR10.20) |
| El archivo se escribe con la ronda bloqueada y una decisión de U5 espera hasta que termine | La consolidación mide p95 ≤ 1,5 s, por debajo del `lock_timeout` de 2 s (NFR3.2); si se supera, la decisión recibe `503` claro (NFR10.15 de U5) y la consola conserva lo escrito |
| Una sola réplica de la API por el volumen `ReadWriteOnce` | Declarado en NFR8.6 con su política estática; el MVP tiene un analista |
| Cambiar la plantilla rompe la reproducibilidad de los SHA-256 antiguos | Los archivos antiguos no se vuelven a renderizar nunca: la descarga lee bytes guardados; `format_version` queda en cada fila y el *golden file* obliga a declararlo (NFR10.22) |
| La medición de MTTV depende de que el analista revise las 11 sesiones de una corrida | El arnés falla si falta una versión 1 (NFR7.1); la corrida se repite completa, nunca con casos sueltos |
| U5 o C11 no adoptan `open_round(for_update=True)` | Precisión registrada en U5 y en U7; la prueba de NFR10.14 falla sin ella |
