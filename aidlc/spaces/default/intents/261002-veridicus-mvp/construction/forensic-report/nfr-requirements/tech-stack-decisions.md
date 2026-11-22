# Decisiones de pila — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Decisiones.** D1–D12 conservan su número y cada fila dice si **se mantiene** o **cambia**. Entran
  D13 (exportación), D14 (retención) y D15 (tope de tamaño).
- **Requisitos de calidad.** Conservan su ID.
- **Paquete.** Pasa a `review_report` (NFR-U7-08); el directorio de la unidad sigue `forensic-report`.

**Insumos.**
- Flujos F1–F10 de `functional-design/functional-spec.md` (functional-spec, revisión 2), reglas de
  `functional-design/rules.md` (rules) y entidades de `entities.md`.
- NFR2, NFR7, NFR10, NFR11, NFR13 y NFR14 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3), con VE-01, VE-02, VE-12 y VE-13 de la adenda 02.
- C1, C8, C11, C23, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements-questions.md` y `security-requirements.md`.
- Las decisiones de pila ya aprobadas de U3 (base de `session-api`), U4 (consola, escáner) y U5 (bloqueo
  de la ronda), y el Infrastructure Design de U7, revisión 1.

Lo que ya fijan `team.md`, U2, U3, U4 y U5 no se repite:
- **Python y API:** Python 3.12, FastAPI y Uvicorn, Pydantic v2 y `pydantic-settings`.
- **Base de datos:** SQLAlchemy 2 síncrono con psycopg 3 y `statement_timeout`, y Alembic en un `Job`.
- **Pruebas y observabilidad:** `prometheus-client`, la marca `perf` de `pytest`, el reloj inyectable,
  `@axe-core/playwright` y `vitest-axe`.
- **De otras unidades:** TanStack Query, `libs/integrity_policy` con `scan(text, literal_sources)` y la
  carga de C25 de U1. `SELECT … FOR UPDATE` con `lock_timeout` de 2 s, el *engine* con
  `hide_parameters=True` y las pruebas de concurrencia con barrera.
- **Plataforma y calidad:** el perfil `restricted`, Problem Details desde `libs/`, `uv`, mypy estricto,
  Ruff, import-linter, Vitest y Playwright.

U7 no añade dependencias nuevas de terceros.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | cambia | Plantilla del reporte | Render con código Python propio en `review_report/domain/render.py`: funciones puras que escriben las secciones H2 fijas de BR11.1 a partir de `ReportContent`, con los textos fijos del catálogo de U1; el aviso de VE-01 al inicio de cada sección y cada N = 25 turnos o sugerencias (BR11.2); `format_version = "2"` y `notice_version` en la fila | Jinja2; una biblioteca de Markdown | Sin dependencia nueva, determinista y probable con 100 % de casos | NFR10.9, NFR10.22, NFR14.1 |
| D2 | se mantiene | Canonicalización | NFC, saltos `\n`, sin espacios finales, un salto final, orden explícito (turnos por número; sugerencias por turno y creación; decisiones por `at`, `seq`; corridas por inicio), fechas `YYYY-MM-DDTHH:MM:SSZ`; nunca se itera un `dict` o un `set` sin ordenar | Confiar en el orden de la base | BR3.2: los mismos datos dan los mismos bytes | NFR10.22, NFR11.3 |
| D3 | cambia | Escape del Markdown | Todo texto del caso (turnos, citas, `hecho`, `observaciones`, notas, reformulaciones) va en bloques citados `> ` y se escapan los caracteres que abren estructura; los delimitadores «» se conservan. Las líneas del aviso y de la marca usan una forma que el texto escapado no puede producir (NFR10.24) | Emitir el texto tal cual; HTML | Un testimonio no crea encabezados, enlaces, HTML ni marcas falsas | NFR10.4, NFR10.9, NFR10.24 |
| D4 | cambia | Escaneo | `scan(text, literal_sources)` sobre el Markdown completo; `literal_sources` = los textos de todos los turnos, más notas, reformulaciones y la cadena versionada del aviso (A-1); se escanean la plantilla, `hecho`, `observaciones` y los avisos | Escanear cada pieza antes de renderizar | Escanea exactamente lo que se guarda y devuelve la ubicación por sección | NFR10.9 |
| D5 | se mantiene | Puerto de almacenamiento | `ReportStore` con `write_new`, `read`, `delete` y `list_entries`; adaptador `volume_report_store.py` con `O_CREAT \| O_EXCL \| O_WRONLY \| O_NOFOLLOW` (0600), `fsync`, `os.link` + `unlink`, `fsync` del directorio y `chmod 0400` | MinIO dentro del clúster; `bytea` en PostgreSQL | FR7.3 pide el volumen; otro servicio que operar; el archivo es la evidencia independiente | NFR10.15, NFR11.4, NFR10.5 |
| D6 | se mantiene | *Timeout* del volumen | `ThreadPoolExecutor` propio de 2 hilos con `future.result(timeout=…)` | Sin *timeout*; `aiofiles` | Toda E/S lleva *timeout*; el hilo vencido no se cancela y su archivo lo borra el barrido periódico (NFR10.16) | NFR10.17 |
| D7 | se mantiene | Atomicidad | `UnitOfWork` de C11; fila de la sesión primero y después `open_round(..., for_update=True)`; el archivo se escribe dentro de la transacción, con el plazo de 10 s | Fila antes que archivo; `SERIALIZABLE` con reintentos | P2 = A; el bloqueo serializa consolidación y decisiones sin reintentos | NFR10.12–NFR10.14 |
| D8 | cambia | Barrido de huérfanos | `application/orphan_sweep.py`, al arrancar (antes de `/readyz`) y en cada pasada de la medición del volumen (60 s), bajo un candado en proceso; solo nombres `<uuid>.md.tmp` o `<uuid>.md` sin fila y con más de 300 s; 1 réplica con `Recreate` | Solo al arrancar (revisión 1); borrar sin margen | Un pod de larga vida no conserva el archivo de un hilo vencido (R-02, NFR-U7-13) | NFR10.16, NFR8.8 |
| D9 | cambia | Vista previa | Lectura completa del archivo (≤ 8 MiB) en memoria, `hashlib.sha256` sin caché, `hmac.compare_digest` y `Response` con `inline` | `FileResponse` o *streaming*; caché del SHA-256 | La comprobación termina **antes** del primer byte (BR5.1); una caché ocultaría una alteración | NFR3.4, NFR11.3 |
| D10 | cambia | Guardias como código puro | `domain/consolidation_guard.py` (BR2), `domain/correction_policy.py` (BR6), `domain/export_policy.py` (BR9.1, BR9.3, BR9.4, BR9.7: quién exporta, marca y rótulo) y la orquestación en `application/consolidate.py`, `application/export.py` y `application/purge.py` | Reglas repartidas en la ruta | Se prueban celda por celda con 100 % de ramas sin base (AUTONOMIA-03) | NFR13.2 |
| D11 | cambia | Consola | Mutaciones de TanStack Query sin reintento (`retry: false`) y sin actualización optimista para finalizar, consolidar, corregir, descartar y exportar; la exportación es un `POST` con CSRF cuya respuesta se entrega como archivo (`Blob` + `URL.createObjectURL`, liberado al terminar); la vista previa se pide solo al abrirla | `<a href>` a una ruta `GET` (no lleva CSRF ni sirve a un `POST`); reintentos automáticos | Ninguna operación no idempotente se repite sola; la exportación escribe una fila | NFR3.9, NFR3.11, NFR3.15, NFR10.18 |
| D12 | cambia | Arnés de MTTV | `evaluation/mttv/mttv.py` lee los `session_id` del reporte JSON de la corrida, consulta la API con una cuenta de analista sintética y calcula con `mttv_seconds` de `domain/mttv.py` | Consultar la base; cronometrar en el navegador | Solo usa marcas del sistema y la misma función que la métrica | NFR7.1, NFR7.3 |
| D13 | nuevo | Exportación | Se arma en memoria a partir de los bytes verificados: cabecera de marca y rótulo + inserción de la línea de marca en cada punto de página que dejó el render (posiciones conocidas, sin volver a renderizar); `hashlib.sha256` de lo armado; `ReportExport` y `AccessLog.record` en la transacción; `Response` con `attachment` tras el *commit* | Volver a renderizar con la marca; guardar la exportación; firmar el archivo | Lo exportado conserva el texto guardado, su *hash* queda antes de enviar y no hay copias (BR9.5) | NFR10.24–NFR10.26, NFR11.7 |
| D14 | nuevo | Retención | `application/purge.py` implementa `Purgeable` de C24 con una conexión de `veridicus_retention` que le pasa el `Job` de U13; borra filas y archivos con el mismo `ReportStore` y devuelve un `PurgeReceipt` de tipos cerrados (UUID, hex, booleanos, enteros) | Borrado en cascada de la base; borrar archivos desde U13 | El orden y el recibo son de U7; el `Job` solo orquesta | NFR11.8, NFR10.27 |
| D15 | nuevo | Tope de tamaño | `report_max_bytes` de C25, leído con la carga de U1 (una variable de entorno solo puede bajarlo); comprobado sobre los bytes renderizados antes del escaneo y del temporal | Tope por número de turnos o sugerencias; sin tope | Un solo número cubre todas las combinaciones de C25 y acota la memoria de NFR8.1 | NFR8.9, NFR8.5 |

## 2. Configuración (prefijo `VERIDICUS_`)

Siete claves de U7, las mismas de Infrastructure Design de U7 revisión 1.

| Ajuste | Valor por defecto | Validación al arrancar |
|---|---|---|
| `VERIDICUS_REPORTS_DIR` | `/var/lib/veridicus/reports-volume/reports` | Ruta absoluta dentro del montaje; el proceso la crea con `0700` o la exige de su UID y `0700` |
| `VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS` | 5 | Entero entre 1 y 30 |
| `VERIDICUS_REPORT_CONSOLIDATION_TIMEOUT_SECONDS` | 10 | Mayor que `STORAGE_TIMEOUT` + 2 y menor que `idle_in_transaction_session_timeout` (15 s); vale también para la exportación |
| `VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS` | 300 | Mayor que `CONSOLIDATION_TIMEOUT` + 60 |
| `VERIDICUS_REPORT_MIN_FREE_BYTES` | 52428800 (50 MiB) | ≥ 2 × `report_max_bytes` (16 MiB) |
| `VERIDICUS_REPORT_VOLUME_QUOTA_BYTES` | 2147483648 (2 GiB) | Mayor que `MIN_FREE_BYTES` + `report_max_bytes` |
| `VERIDICUS_REPORT_VOLUME_SCAN_INTERVAL_SECONDS` | 60 | Entero entre 10 y 300 |

El plazo de 500 ms de `AccessLog` en la exportación es el de U3 (NFR-U3-05) y no tiene clave propia. Una
configuración faltante o inválida impide arrancar el pod (`team.md`; NFR10.19).

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | se mantiene | Todo U7 se prueba en CPU y sin modelos. | U7 no llama a modelos; los niveles 0 y 1 corren con PostgreSQL real y un directorio real del contenedor como volumen; ninguna prueba exige GPU ni descarga nada. |
| NFR10.22 | cambia | El render y la exportación son deterministas en cualquier proceso (BR3.2, BR11). | Nivel 0: (a) dos renders del caso de 100 turnos dan los mismos bytes; (b) Hypothesis baraja el orden de entrada y obtiene los mismos bytes; (c) dos subprocesos con `PYTHONHASHSEED` distintos dan el mismo SHA-256; (d) `\r\n`, NFD y espacios finales salen NFC, LF y sin espacios; (e) un *golden file* sintético de `format_version` 2 con el aviso al inicio de cada sección y cada 25 elementos coincide byte a byte; (f) un *golden file* de exportación con usuario y hora fijos coincide byte a byte. Cambiar la plantilla exige actualizar los dos en el mismo PR y subir `format_version` si cambia la forma. |
| NFR13.1 | se mantiene | Cobertura de líneas. | ≥ 80 % en `services/session-api` (incluido `review_report`) y en `frontend`, en la CI y bloqueante. |
| NFR13.2 | cambia | 100 % de ramas en los módulos guardia de U7 (BR2, BR4, BR6, BR9, BR10). | En `services/session-api/src/session_api/review_report/`: `domain/consolidation_guard.py`, `domain/correction_policy.py`, `domain/export_policy.py`, `application/consolidate.py`, `application/export.py`, `application/purge.py`, `application/orphan_sweep.py` y `adapters/volume_report_store.py`, con `--cov-branch` y `fail_under = 100`. La guardia se prueba con la tabla completa de estado de sesión (incluidos `paused` y `blocked`), origen, corridas en curso, modo final lanzado o exento, ronda abierta y pendientes. |
| NFR13.3 | cambia | Las fronteras del módulo se respetan. | import-linter: `review_report.domain` no importa `api`, `adapters`, `sqlalchemy` ni otros módulos; ReviewReport solo usa InterviewSession y HumanReview a través de `contracts/python/report_ports.py` (C11 v2) y `AccessLog` por su puerto (C23); `consolidate` solo lo importa la ruta (NFR11.2); `purge` solo lo importan el `Job` de U13 y las pruebas. Control negativo en la CI. |
| NFR14.2 | cambia | Identificadores según el glosario. | `review_report`, `report_version`, `report_export`, `export_watermark`, `purge_receipt`, `consolidation_blocker`, `report_file`, `mttv_sample`, `review_suggestion`; la comprobación de glosario de U1 da 0 hallazgos y 0 apariciones de `forensic_report` en el código (el slug `forensic-report` solo nombra el directorio de AI-DLC). |

## 4. Accesibilidad

BR8.4 reutiliza la base de U4: `vitest-axe` sobre los diálogos de finalizar y consolidar, la vista
previa, la lista de versiones, la exportación y la copia de trabajo, y `@axe-core/playwright` en
`frontend/e2e/report.spec.ts`. Criterios: 0 violaciones `serious` o `critical`; consolidar, copiar el
SHA-256, abrir la vista previa, exportar, corregir y descartar se completan solo con teclado; los
diálogos modales (finalizar, consolidar, descartar) atrapan el foco, se cierran con `Esc` y devuelven el
foco al botón que los abrió; «Descargar reporte» deshabilitado para el analista no dueño usa
`aria-disabled` con su motivo legible (BR8.6); la versión vigente, el rótulo de reemplazo y el estado de
cada sugerencia llevan texto además del color; el SHA-256 se muestra completo en fuente monoespaciada y su
copia se anuncia por `aria-live`.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, render, exportación y guardias (nivel 0) | `uv run --directory services/session-api pytest tests/review_report -m "not integration and not perf"` | Verde; NFR7.3, NFR10.9, NFR10.10, NFR10.22, NFR10.24, NFR14.1 |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest tests/review_report --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1) | `uv run --directory services/session-api pytest tests/review_report -m integration` | Verde; NFR10.1–NFR10.21, NFR10.23–NFR10.27, NFR11.1–NFR11.8, NFR8.4, NFR8.5, NFR8.8–NFR8.10, NFR15.1–NFR15.5 |
| Rendimiento en proceso | `uv run --directory services/session-api pytest tests/review_report -m perf` | NFR3.1–NFR3.8, NFR3.12–NFR3.14, NFR7.2, NFR8.1–NFR8.3 |
| Prueba común de auditoría (U3) | `uv run --directory services/session-api pytest -m integration -k audit_convention` | `ReportVersion` y `ReportExport` registradas; `UPDATE`/`DELETE` de `veridicus_app` fallan |
| Verificación del almacén (la ejecuta el humano) | `kubectl exec deploy/veridicus-session-api -c api -- python -m session_api.review_report.verify_store` | Código 0 (NFR10.20) |
| Políticas de manifiestos (montajes, réplicas, estrategia, *ingress*) | `helm template deploy/veridicus -f deploy/veridicus/values-cpu.yaml`, luego `kubeconform -strict` y `kyverno apply deploy/policies/` sobre el render | 0 violaciones (NFR1.2, NFR1.3, NFR8.6) |
| Reglas de volumen y exportación | `promtool test rules deploy/veridicus/tests/report-rules.yaml` | Verde (NFR15.3, NFR15.5) |
| Consola | `npm --prefix frontend run test -- --coverage src/report` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % (NFR3.9, NFR3.11, NFR3.15, NFR10.4, NFR10.18, NFR10.23) |
| E2E y accesibilidad (nivel 3) | `npx --prefix frontend playwright test e2e/report.spec.ts` | 0 fallos (NFR8.7, NFR3.10, NFR3.11, §4) |
| MTTV (nivel 2, fuera de la CI, tras la revisión humana) | `uv run --directory evaluation python -m mttv.mttv --run out/level2.json --report out/mttv.json` | Media < 600 s (NFR7.1) |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en `services/session-api` | 0 errores (NFR13.3, NFR11.2, NFR1.1) |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El hilo del volumen que vence (D6) no se cancela y su archivo aparece tras el *rollback* | Queda sin fila y el barrido periódico lo borra pasados 300 s (NFR10.16) |
| La consolidación del caso máximo (hasta 8 s) tiene la ronda bloqueada | Una decisión de U5 o una segunda consolidación reciben `503 system.unavailable` en ≤ 2,5 s con 0 filas y la consola conserva lo escrito (NFR10.13); el caso esperado tarda ≤ 1,5 s |
| Una sola réplica de la API por el volumen `ReadWriteOnce` | Declarado en NFR8.6 con su política estática; el MVP tiene un analista |
| Cambiar la plantilla rompe la reproducibilidad de los SHA-256 antiguos | Los archivos no se vuelven a renderizar: vista previa y exportación leen bytes guardados; `format_version` y `notice_version` quedan en cada fila (NFR10.22) |
| La medición de MTTV exige revisar en la consola todas las sesiones guiadas del conjunto (40 hoy) | El arnés falla si falta una versión 1 (NFR7.1); la corrida se repite completa. Es esfuerzo humano que se planifica antes de la entrega etiquetada |
| Sin U13 no hay registro de acceso de la exportación | `ReportExport` conserva quién, cuándo y `export_sha256`; WARN y `access_log: not_configured` (NFR11.7, NFR15.5) |
| El peor caso teórico de 2,4 GiB no cabe en la cuota de 2 GiB | Riesgo aceptado en NFR8.5: el esperado es 18 MB, la regla del 80 % lo muestra y la retención libera espacio |
