# Requisitos de seguridad — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02, las revisiones 3 de Inception y
el Functional Design de U7, revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el
historial de Git.
- **IDs.** Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
  Ninguno se retira en este archivo. Lo nuevo toma el número siguiente de su grupo: NFR1.3,
  NFR10.23–NFR10.25 y NFR11.7–NFR11.8.
- **Sin preguntas** en esta pasada (`nfr-requirements-questions.md`, segunda pasada). Lo que precisa
  artefactos aprobados está en §6 (NFR-U7-01 a NFR-U7-13).
- **Revisión 1:** sus hallazgos R-01 a R-05 se cierran en `reliability-requirements.md` (NFR8.8,
  NFR10.13, NFR10.20, §4) y en `traceability.json` (R-03).

**Insumos.**
- Frontera (§1), flujos F1–F10, máquinas de estado, §7 «Errores en la frontera» y tabla FD-U7-01 a
  FD-U7-13 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1–BR11 de `functional-design/rules.md` (rules, revisión 2) y entidades de `entities.md`
  (ReportVersion, ReportExport, ExportWatermark, PurgeReceipt, puerto `AccessLog`).
- FR1, FR6.4, FR7.1–FR7.5 y NFR1, NFR7, NFR10–NFR14 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3), con VE-01, VE-02, VE-12, VE-13 y A-1–A-3 de `requirements-adenda-02.md`.
- C1 (rutas de U7), C8, C11, C16, C23, C24 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3).
- NFR de hoy de U1 (NFR10.3, NFR10.14, NFR-U1-03, NFR-U1-07), U2 (NFR10.7, NFR10.16), U3 (NFR10.17,
  NFR10.18, NFR10.21, NFR-U3-03, NFR-U3-05), U4, U5 y U6 (cifras de C25), y el Infrastructure Design de
  U7, revisión 1.
- `nfr-requirements-questions.md` y las reglas de `team.md` y `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de `team.md`: nivel 0 (unitarias,
contratos y políticas, cada PR), nivel 1 (integración con PostgreSQL real y el volumen real en
contenedor, cada PR), nivel 3 (E2E) y manual. Los comandos están en `tech-stack-decisions.md` §5.
La autenticación, la sesión web, el anti-CSRF, la matriz de roles (incluido
`x-veridicus-owner-only-for-role`), el manejador de Problem Details y `AuditConvention` son de U3; el
escáner `scan(text, literal_sources)` y el aviso son de IntegrityPolicy (C8); las rondas son de U5 (C11);
las transiciones de la sesión son de U4 y U6; el adaptador real de `AccessLog` y el `Job` de retención son
de U13. Aquí se exige que U7 los use y se fijan sus pruebas.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera | Clasificación |
|---|---|---|---|
| Rutas de U7 en ConsoleApi (`/finalize`, `/reports`, `/correction-rounds`, descarte, `/download`, `/exports`) | API de `session-api`, dentro del clúster, bajo la `NetworkPolicy` de salida denegada de U2 | Peticiones del navegador; `ReportVersion`, la vista previa y la exportación hacia el navegador de un usuario autorizado (C1). Es la entrega prevista dentro del clúster, no una salida a internet | Restringido |
| ReviewReport (guardia, render, escaneo, persistencia, exportación, barrido, retención) | Módulo `review_report` de la API de `session-api`, dentro | Llamadas en proceso a InterviewSession y HumanReview (C11), IntegrityPolicy (C8); filas en PostgreSQL interno | Restringido |
| Volumen de reportes (PVC `veridicus-reports`, subdirectorio `reports/`) | Dentro, montado en escritura en el contenedor de la API y en el `Job` de retención (U2) | Archivos Markdown completos del caso; **nunca** una exportación | Restringido |
| PostgreSQL (CloudNativePG) | Dentro | `ReportVersion` y `ReportExport`: IDs, SHA-256, tamaños, actor y hora; **sin texto del caso** | Interna |
| Puerto `AccessLog` (adaptador por defecto o el de U13) | Dentro de `session-api` | `user_id`, tipo y ID de recurso, `export_sha256` | Interna |
| `ingress-nginx` | Dentro (termina TLS) | Ve la vista previa y la exportación en tránsito; no las escribe en disco (NFR1.3) | Restringido en tránsito |
| Métricas de U7 | `/metrics` del puerto interno 8081 de `session-api` | Solo contadores, histogramas y *gauges* sin texto (NFR10.10) | Interna |
| AnalystConsole (diálogos, M5, vista previa, exportación) | Navegador del usuario, servida por `frontend` | Solo habla con ConsoleApi (ADR-004); la exportación queda en el equipo del usuario | Restringido |
| `Job` de retención (U13) | Dentro, imagen de `session-api` | Llama `purge_session` de ReviewReport; recibe IDs y SHA-256, nunca texto | Interna |
| Arnés de MTTV | Máquina de desarrollo, contra la API | Solo `finalized_at`, `consolidated_at`, origen e identificadores; nunca pide reportes | Interna |

**Ningún componente de U7 hace una llamada fuera del clúster ni a un modelo.** El reporte junta en un solo
archivo todo el caso; aunque en el MVP los datos son sintéticos (NFR12), se trata como si fueran reales.

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Otro analista, un `admin`, un `investigador` o una identidad de servicio finaliza, consolida, corrige o descarta | Elevation of privilege | Alto | NFR10.1 |
| T2 | Un `investigador` o una identidad de servicio lee versiones o la vista previa (VE-09) | Information disclosure | Alto | NFR10.2 |
| T3 | Petición falsificada desde otro sitio que finaliza, consolida, descarta o exporta | Tampering | Medio | NFR10.3 |
| T4 | Consolidación automática sin acción explícita del analista (AUTONOMIA-03) | Elevation of privilege | Alto | NFR11.2 |
| T5 | Consolidar con pendientes o corridas en curso por una carrera entre la guardia y el bloqueo | Tampering | Alto | NFR10.13, NFR10.14 (reliability) |
| T6 | Alterar el archivo del reporte en el volumen después de consolidar | Tampering | Alto | NFR11.3, NFR11.4 |
| T7 | Reescribir o borrar una `ReportVersion` o una `ReportExport` | Repudiation | Alto | NFR11.1 |
| T8 | Una corrección reescribe la versión anterior | Tampering | Alto | NFR11.5 |
| T9 | Recorrido de rutas o lectura de otro archivo del volumen desde `/download` o `/exports` | Information disclosure | Medio | NFR10.5 |
| T10 | Otro pod o proceso lee el volumen de reportes | Information disclosure | Alto | NFR1.2, NFR10.6 |
| T11 | Texto del reporte o nombre de usuario de la marca en logs, métricas, errores o rechazos | Information disclosure | Alto | NFR10.7, NFR10.8, NFR10.10 |
| T12 | Una etiqueta de veracidad o una palabra de VE-02 en el reporte consolidado | Tampering | Alto | NFR10.9 |
| T13 | El navegador interpreta el Markdown como HTML o lo guarda en caché | Information disclosure | Medio | NFR10.4 |
| T14 | Cambiar la transcripción o la salida de la IA desde la copia de trabajo | Tampering | Alto | NFR10.11 |
| T15 | Suplantar al actor o la hora enviándolos en el cuerpo | Spoofing | Medio | NFR10.1, NFR7.3 |
| T16 | Un analista que no es el dueño, o un `investigador`, exporta (VE-13) | Elevation of privilege | Alto | NFR10.23 |
| T17 | Una exportación sin marca, con la marca de otro usuario o sin el rótulo de reemplazo | Repudiation | Alto | NFR10.24 |
| T18 | Una exportación sale sin quedar registrada, o su *hash* registrado no es el de lo enviado (A-3) | Repudiation | Alto | NFR11.7 |
| T19 | Copias del testimonio fuera del volumen controlado: bytes exportados guardados, temporales del *ingress* | Information disclosure | Medio | NFR10.25, NFR1.3 |
| T20 | La retención borra lo de otra sesión, deja texto en el acta o el usuario de la aplicación borra | Tampering, Information disclosure | Alto | NFR11.8, NFR11.1 |

## 3. Requisitos

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | cambia | U7 no abre conexiones salvo a PostgreSQL y al volumen local. | El paquete `review_report` no importa clientes HTTP (`httpx`, `requests`, `urllib`), Redis, `libs.model_gateway` ni `libs.anonymizer` (contrato de import-linter con control negativo: un módulo de prueba que importa `httpx` lo hace fallar); `session-api` queda bajo la `NetworkPolicy` de salida denegada de U2, que es la defensa de fondo. | Nivel 0 |
| NFR1.2 | cambia | El volumen de reportes no sale del clúster y solo lo montan sus dos usuarios. | El PVC `veridicus-reports` usa la `StorageClass` local del nodo (Infrastructure Design de U7). Lo montan en escritura solo el contenedor `api` del `Deployment` `session-api` y el `Job` de retención de `deploy/jobs/` (NFR10.16 de U2); ningún otro *workload* lo monta, ni siquiera en lectura (la verificación corre dentro del contenedor de la API, NFR10.20). Política Kyverno `veridicus-reports-mounts` sobre el render de `helm template` con controles negativos: otro `Deployment` que lo monte, y un `CronJob` que lo monte, fallan (NFR-U7-05, NFR-U7-06). | Nivel 0 |
| NFR1.3 | nuevo | El *ingress* no escribe en disco las respuestas que llevan el reporte (T19). | Las respuestas de `GET /reports/{id}/download` y `POST /reports/{id}/exports` pasan por `ingress-nginx` sin archivo temporal: la ruta que las sirve declara `proxy-buffering: "off"` o `proxy-max-temp-file-size: "0"` (lo concreta NFR Design). Política estática de nivel 0 sobre el render con control negativo (la ruta de reportes sin la anotación falla) y comprobación manual antes de la sustentación: tras exportar un reporte de 8 MiB, el directorio de temporales de `ingress-nginx` no contiene archivos `proxy_temp` nuevos. Es la misma regla que ya aplicó el *Ingress* de voz (`project.md`) y NFR-U6-06 (NFR-U7-07). | Nivel 0 y manual |

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | cambia | Solo el analista dueño finaliza, consolida, corrige y descarta (BR1.1, BR2.1, BR6.1, ADR-009). | Las cuatro rutas declaran `x-veridicus-roles: [analista]` y `x-veridicus-owner-only: true`; ConsoleApi obtiene el dueño en el servidor antes de delegar. Pruebas por ruta: otro analista, `admin`, `investigador` e identidad de servicio → `403` `auth.forbidden` (§7 de functional-spec); sin sesión web → `401`; en cada caso 0 filas en `ReportVersion`, 0 cambios de sesión o ronda y 0 archivos en el volumen. Actor y hora son del servidor: un cuerpo con `consolidated_by`, `consolidated_at`, `finalized_at`, `actor_user_id` u otro campo no declarado responde `422` `validation.invalid_request` (`additionalProperties: false`), y la misma petición de un rol sin permiso responde `403`, no `422` (NFR10.18 de U3). | Nivel 1 |
| NFR10.2 | cambia | Leen versiones y vista previa todos los analistas y el `admin`; el `investigador` y las identidades de servicio no (BR5.3, FR1, VE-09). | `GET /sessions/{id}/reports` y `GET /reports/{id}/download` declaran `x-veridicus-roles: [analista, admin]` sin marca de dueño. Pruebas: dueño, otro analista y `admin` → `200`; `investigador` → `403` `auth.forbidden`; identidad de servicio → `403`; sin sesión web → `401`. Ningún `403` envía bytes ni la cabecera `X-Veridicus-SHA256` y ninguno llama a `AccessLog` (NFR10.21 de U3). | Nivel 1 |
| NFR10.3 | cambia | Las rutas que escriben exigen el anti-CSRF de U3. | `POST /finalize`, `POST /reports`, `POST /correction-rounds`, `POST …/correction-rounds/current/discard` y `POST /reports/{id}/exports`: sin `X-CSRF-Token` o con uno distinto → `403` `auth.csrf`, 0 filas (ni `ReportExport`), 0 archivos, 0 bytes y 0 llamadas a `AccessLog`. `GET` de lista y vista previa no cambian estado (prueba que compara filas antes y después). | Nivel 1 |
| NFR10.4 | cambia | Ni la vista previa ni la exportación se interpretan como HTML ni se guardan en caché. | **Vista previa** (`/download`): `200` con `Content-Type: text/markdown; charset=utf-8`, `Content-Disposition: inline`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store` y `X-Veridicus-SHA256` de 64 caracteres. **Exportación**: `201` con el mismo `Content-Type`, `Content-Disposition: attachment; filename="veridicus-reporte-<report_version_id>-<export_id>.md"` (solo UUID), `nosniff`, `no-store` y `X-Veridicus-Export-SHA256`. La consola muestra la vista previa como Markdown **sin HTML crudo** (`skipHtml`, sin enlaces navegables) y nunca con `dangerouslySetInnerHTML` (`react/no-danger` en error, `team.md`); una prueba Vitest con `<script>`, `<img onerror>` y `[x](javascript:…)` sembrados en una nota comprueba que no se ejecutan ni crean enlaces. | Nivel 1 y Vitest |
| NFR10.5 | cambia | `/download` y `/exports` solo leen el archivo registrado de esa versión (T9). | `report_version_id` se valida como UUID en la ruta (`422` si no lo es); la ruta del archivo es `<VERIDICUS_REPORTS_DIR>/<report_version_id>.md` y se compara con `storage_path` de la fila; el valor de la petición nunca se concatena a una ruta. Sin fila: `/download` responde `409` `report.not_consolidated` (BR5.2) y `/exports` `404` `report.not_found` (BR9.2, FD-U7-05). Pruebas con `..%2F`, rutas absolutas y un enlace simbólico plantado en el volumen: `422`, `404` o `409 report.integrity_mismatch`, nunca el contenido de otro archivo (la apertura usa `O_NOFOLLOW`). | Nivel 1 |
| NFR10.6 | cambia | El volumen solo lo lee el proceso de la API (T10). | El contenedor corre sin root (UID 10001, perfil `restricted` de U2). `VERIDICUS_REPORTS_DIR` es el subdirectorio `reports/` del montaje, que el proceso crea con `0700` si no existe; si existe, debe ser del UID del proceso y `0700`, o el pod no pasa `/readyz`. Cada archivo final queda `0400` y cada temporal `0600`; el proceso fija `umask 077`. No se confía en `fsGroup`, que el aprovisionador hostPath ignora (Infrastructure Design de U7). Prueba de nivel 1 que consolida y lee `stat()` del archivo y del directorio; política de NFR1.2 sobre los montajes. | Nivel 0 y nivel 1 |
| NFR10.7 | cambia | Los logs de U7 solo llevan identificadores (BR7.2). | Campos permitidos: `session_id`, `report_version_id`, `export_id`, `round_id`, `user_id`, `version_number`, `byte_size`, `sha256`, `export_sha256`, `was_current`, `code`, nombre de archivo (siempre `<uuid>.md` o `<uuid>.md.tmp`), duraciones y conteos. Nunca el nombre de usuario que va en la marca. Prueba de nivel 1: con una cadena centinela en un turno, un hecho, unas observaciones, una nota, una reformulación y el nombre de usuario, 0 coincidencias en los logs capturados de `session-api` en los caminos `200`, `201`, `204`, `403`, `404`, `409` (todos los `code` de U7), `413`, `422`, `500`, `503`, en el barrido, en `purge_session` y en una violación de restricción (*engine* con `hide_parameters=True`, D5 de U5). | Nivel 1 |
| NFR10.8 | cambia | Los errores no devuelven texto del caso. | Cada rechazo es Problem Details (`application/problem+json`) con un `code` de C1 y el `detail` en español del catálogo; `report.forbidden_vocabulary` trae la ubicación (sección e ID de turno o de sugerencia, BR3.3) y **nunca** el término ni su entorno. Con la cadena centinela de NFR10.7, 0 coincidencias en los cuerpos de error. | Nivel 1 |
| NFR10.9 | cambia | El reporte consolidado no lleva etiquetas de veracidad ni el vocabulario de VE-02 (AUTONOMIA-03, BR3.3, BR11.4). | Antes del SHA-256, el Markdown completo pasa por `scan(text, literal_sources)` con la lista de C8 que suma los términos de VE-02. `literal_sources` son los textos de **todos** los turnos (cubren las dos citas); se excluyen además notas, reformulaciones y la cadena versionada del aviso (A-1, FD-U7-07). Se escanean los rótulos y textos de la plantilla de `format_version` 2, `hecho`, `observaciones`, los avisos de la sesión y los textos del sistema. Controles de nivel 0: «miente» en un texto del sistema o en unas observaciones hace fallar la consolidación con su ubicación; «falso» o «prueba» dentro de un turno o una cita no; «miente» en una reformulación no; la plantilla vacía da 0 coincidencias; «prueba» en el aviso no falla y en cualquier otra cadena fija sí. Prueba de nivel 1: tras el rechazo, 0 filas, 0 archivos y la ronda sigue abierta. | Nivel 0 y nivel 1 |
| NFR10.10 | se mantiene | Las métricas de U7 no llevan texto. | Las etiquetas de NFR15.1 solo toman valores de su enum (`result`); no hay etiqueta `session_id`, `report_version_id` ni `user_id`. Prueba de nivel 0 que recorre las series y valida cada etiqueta contra su patrón, y de nivel 1 con la cadena centinela: 0 coincidencias en `/metrics`. | Nivel 0 y nivel 1 |
| NFR10.11 | cambia | La copia de trabajo solo cambia estados, notas y reformulaciones (BR6.3). | Una petición que intenta cambiar transcripción, hecho, tipo, citas, avisos u observaciones responde `422` `validation.invalid_request` con 0 filas; el SHA-256 de esos campos y el de los bytes de la versión vigente son iguales antes y después de corregir y de consolidar la versión N+1 (NFR11.5). | Nivel 1 |
| NFR10.23 | nuevo | Solo exportan el analista dueño y el `admin` (BR9.1, VE-13, A-3). | `POST /reports/{id}/exports` declara `x-veridicus-roles: [analista, admin]` y `x-veridicus-owner-only-for-role: analista`. Pruebas: dueño → `201`; `admin` → `201`; otro analista → `403` `auth.forbidden`; `investigador` → `403`; identidad de servicio → `403`; sin sesión → `401`. En cada rechazo: 0 `ReportExport`, 0 llamadas a `AccessLog` y 0 bytes. La consola deja «Descargar reporte» `aria-disabled` con su motivo para el analista no dueño (BR8.6), pero la prueba exige el `403` de la API. | Nivel 1 y Vitest |
| NFR10.24 | nuevo | Cada exportación lleva la marca de quien la pide, el SHA-256 de la versión y, si no es la vigente, el rótulo de reemplazo (BR9.3, BR9.4, BR9.7, VE-01, VE-13). | La cabecera lleva «Exportado por <usuario> el <fecha Colombia> (<UTC>)», «Versión N · SHA-256 de la versión <64 caracteres>» y, si la versión no es la vigente, «Reemplazada por la versión M el …»; la línea de marca se repite en **cada** punto de página de BR11.2, junto al aviso. Los puntos de página tienen una forma de línea que el texto del caso, ya escapado (D3), no puede producir: una prueba de nivel 1 con un turno que contiene el texto exacto del aviso y la frase de la marca da tantas marcas como puntos de página, ni una más. El nombre de usuario se escapa como texto del caso. Las cadenas fijas de la marca y del rótulo dan 0 coincidencias con C8 (nivel 0). Mismas entradas (versión, usuario, hora) → mismos bytes (nivel 0). | Nivel 0 y nivel 1 |
| NFR10.25 | nuevo | Los bytes exportados nunca se guardan (BR9.5, VE-12). | Tras 20 exportaciones, el listado y los SHA-256 de `reports/` son iguales a los de antes; no hay archivos nuevos en `/tmp` del contenedor ni columnas `bytea` o de texto con el contenido (prueba sobre el esquema); el log no lleva los bytes. Solo queda `export_sha256` en `ReportExport` y, con U13, en el registro de acceso. | Nivel 1 |

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia | `ReportVersion` y `ReportExport` solo admiten inserciones para la aplicación (BR4.4, A-2). | Las dos tablas registradas en `AuditConvention` de U3 con la marca `purgeable: true`; `veridicus_app` tiene solo `INSERT` y `SELECT`: `UPDATE`, `DELETE` y `TRUNCATE` fallan por permisos; `veridicus_retention` puede `DELETE` y no `UPDATE`. `consolidated_by`, `consolidated_at`, `exported_by` y `exported_at` `NOT NULL`. Restricciones como segunda barrera: `UNIQUE (session_id, version_number)`, `UNIQUE (round_id)`, `UNIQUE (storage_path)`, `CHECK ((version_number = 1) = (supersedes_version_id IS NULL))`, `CHECK (sha256 ~ '^[a-f0-9]{64}$')`, `CHECK (export_sha256 ~ '^[a-f0-9]{64}$')`, `CHECK (byte_size > 0)` y claves foráneas a sesión, ronda, usuario y versión. Salen las columnas y la clave foránea del escenario (cambio 01). Una prueba por restricción y la prueba común de U3 (NFR11.1 y NFR11.3 de U3). | Nivel 1 |
| NFR11.2 | cambia | Ninguna consolidación ocurre sin la acción explícita del analista dueño (AUTONOMIA-03, FR7.1). | La única entrada que llama `consolidate` es la ruta `POST /sessions/{id}/reports`: contrato de import-linter que prohíbe importar `review_report.application.consolidate` desde el trabajador de `session-api`, `semantic-agent`, `evaluation/`, el `Job` de retención y cualquier módulo distinto de la ruta (control negativo en la CI). La importada se finaliza dentro de esa misma acción (BR2.10), nunca sola. Cada versión registra quién (principal autenticado) y cuándo (reloj del servidor), y M5 los muestra (BR8.2). | Nivel 0 y nivel 1 |
| NFR11.3 | cambia | El SHA-256 registrado es el de los bytes guardados y se comprueba en cada vista previa y en cada exportación (BR3.4, BR5.1, BR9.2). | Tras consolidar, `sha256sum` del archivo coincide con la fila y con la respuesta `201`. Se altera 1 byte del archivo, se trunca y se borra: las tres vistas previas y las tres exportaciones responden `409` `report.integrity_mismatch` sin bytes y sin `ReportExport`, con un `ERROR` que solo lleva el `report_version_id` y `+1` en el contador de NFR15.1. El recálculo no se guarda en caché. | Nivel 1 |
| NFR11.4 | cambia | Un archivo final nunca se reescribe. | El temporal se crea con `O_CREAT \| O_EXCL` y el nombre final con `os.link` + `unlink` del temporal (falla si el destino existe); el final queda `0400`. Prueba de nivel 1: un archivo plantado con el nombre del `report_version_id` siguiente hace fallar la consolidación con `500` `system.internal` (NFR-U7-03) sin tocar el archivo plantado. Solo la retención borra un final (NFR11.8). | Nivel 1 |
| NFR11.5 | se mantiene | Corregir crea una versión nueva y deja la anterior intacta (BR6.5). | Tras consolidar la versión 2: la fila y el archivo de la versión 1 no cambian (mismo `st_mtime`, mismo SHA-256, misma fila), la 2 tiene `supersedes_version_id` = 1 y la lista marca la 2 como vigente. | Nivel 1 |
| NFR11.6 | cambia | Una copia descartada deja rastro y no cuenta (BR6.4). | La ronda pasa a `discarded` con quién y cuándo por `discard_correction_round` (FD-U5-04, FD-U7-09); sus decisiones siguen en `ReviewDecision` y ninguna `ReportVersion` la referencia. Sin copia abierta, el descarte responde `409` `report.conflict`. | Nivel 1 |
| NFR11.7 | nuevo | Toda exportación queda registrada con el SHA-256 de lo que se envía, antes de enviarlo (BR9.5, BR9.6, A-3). | En una transacción: inserción de `ReportExport` y `AccessLog.record(report_export, report_version_id, export_sha256)` desde la ruta; solo tras el *commit* se envían los bytes. `sha256sum` de lo recibido = `X-Veridicus-Export-SHA256` = `ReportExport.export_sha256` = el valor que recibe el doble del puerto (nivel 0 y 1). Con el adaptador real que falla o tarda más de 500 ms: *rollback*, `503` `report.export_not_recorded`, 0 `ReportExport`, 0 bytes. Con el adaptador por defecto: `201`, WARN «registro de acceso no configurado» solo con IDs, y `/readyz` `200` con `access_log: not_configured` (C23). | Nivel 0 y nivel 1 |
| NFR11.8 | nuevo | La retención borra solo lo de la sesión pedida, con el usuario de retención, y devuelve IDs y SHA-256 sin texto (BR10.1, BR10.2, C24, A-2). | `purge_session` borra las `ReportExport` de la sesión y después cada `ReportVersion` de la más nueva a la más antigua, archivo antes que fila. `PurgeReceipt` lleva `session_id`, los `export_id` y, por versión, `report_version_id`, `sha256` y `file_missing`; una prueba de propiedades comprueba que el recibo serializado solo contiene UUID, hex de 64, booleanos y enteros. Pruebas de nivel 1 con dos sesiones: tras purgar una, la otra conserva filas y archivos; con `veridicus_app` el mismo borrado falla por permisos. | Nivel 1 |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | cambia | Los *fixtures*, los reportes esperados y los informes del arnés de U7 son sintéticos. | Los casos de 100 turnos y máximo, los archivos dorados de `services/session-api/tests/review_report/` y los informes del arnés de MTTV usan el catálogo de nombres de U1 (`contracts/fixtures/synthetic-names.yaml`); la comprobación de U1 sobre esas rutas da 0 hallazgos. Ningún reporte ni exportación de una corrida real se versiona: `evaluation/out/` y `backups/` están en `.gitignore`. | Nivel 0 |

### NFR14 — Idioma

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR14.1 | cambia | El reporte, la exportación y las pantallas de U7 están en español. | Encabezados, rótulos y textos de la plantilla de `format_version` 2, de la marca y del rótulo de reemplazo, y los textos de los diálogos y de M5 (BR1.5, BR8.1–BR8.7) salen del catálogo de U1; una prueba de nivel 0 recorre la plantilla y comprueba que cada texto fijo está en el catálogo. Fechas del reporte en ISO 8601 UTC con la hora de Colombia entre paréntesis donde se muestran a personas (BR3.2); en la consola, hora de Colombia y UTC entre paréntesis. | Nivel 0 |

## 4. Trazabilidad de AUTONOMIA

| Regla | Requisitos de U7 |
|---|---|
| AUTONOMIA-01 | U7 no aplica nada al clúster: sus tablas y permisos entran por la migración de su PR (`Job` aparte), el PVC y sus montajes por el chart (PR), y `verify_store`, `export_store` e `import_store` los ejecuta el humano. La retención la lanza el humano (U13) |
| AUTONOMIA-02 | Cada requisito tiene su criterio y su comando (`tech-stack-decisions.md` §5) |
| AUTONOMIA-03 | NFR10.9, NFR10.11, NFR11.1–NFR11.6; guardias de consolidación, persistencia, corrección y exportación con 100 % de ramas (NFR13.2); atomicidad (NFR10.12–NFR10.14) |
| AUTONOMIA-04 | §1, NFR1.1–NFR1.3, NFR10.6, NFR10.7, NFR10.8, NFR10.10, NFR10.25 |
| AUTONOMIA-05 | No aplica directamente: U7 solo consolida hallazgos que ya salieron verificados del analizador (U11, U4); el reporte copia las dos citas con su turno y sus avisos sin reescribirlas (BR3.1) |

## 5. Riesgos aceptados

| Riesgo | Por qué queda | Tratamiento |
|---|---|---|
| El volumen no está cifrado por la aplicación | El reporte se guarda en claro en un PVC local del nodo; la protección es el acceso al nodo, los permisos de NFR10.6 y la `NetworkPolicy` | En el MVP los datos son sintéticos (NFR12). Cifrar el disco queda fuera del MVP; si entraran datos reales, el dueño es Infrastructure Design de U2 (cierra R-05 junto con §4 de reliability) |
| El SHA-256 detecta alteraciones, no las impide | Quien tenga escritura en el nodo y credenciales de administración de la base puede cambiar archivo y fila | La fila es de solo inserción para la aplicación (NFR11.1); `verify_store` lo detecta si cambia solo uno de los dos |
| La exportación queda en el equipo del usuario | Es la entrega prevista por FR7.4 y VE-13 | Lleva la marca de quien la pidió (NFR10.24) y su *hash* queda registrado (NFR11.7) |
| Sin U13, el registro de acceso de la exportación no existe | C23 permite el adaptador por defecto mientras U13 no se construya | `ReportExport` conserva quién, cuándo y `export_sha256` (A-3 se cumple con esa fila); WARN por exportación y `access_log: not_configured` en `/readyz` |
| Una purga revertida tras borrar un archivo deja una fila sin archivo | Archivo antes que fila en el borrado (BR10.1) y transacción por sesión (U13) | La vista previa y la exportación responden `409 report.integrity_mismatch`; `verify_store` lo lista; la siguiente ejecución del `Job` termina el borrado con `file_missing` (NFR10.27) |

## 6. Precisiones a artefactos ya aprobados (NFR-U7-xx)

No edité ningún artefacto aprobado (regla de `project.md`). Decides en la aprobación cuáles se llevan al
original, cada una en su propio commit. Todas se aplicaron sin preguntar porque salen de fuentes aprobadas.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U7-01 | `contract-design/contract-summary.md` (C25) | Entra `report_max_bytes: { value: 8388608, unit: bytes }`. Una consolidación cuyo Markdown la supera responde `413` `limits.exceeded` antes de escribir, con 0 filas y 0 archivos (NFR8.9). La exportación cabe en esa cifra más 64 KiB (marca por página) | §12 pregunta 1 de functional-spec; NFR10.14 y NFR-U1-07 de U1; P7 = A de U1 |
| NFR-U7-02 | C1 (rutas de U7) | `POST /reports` suma `403`, `413`, `422` y `503`; `/finalize`, `/correction-rounds` y el descarte declaran `403`, `409`, `422` y `503`; `/download` declara `Content-Disposition: inline`, `403`, `422` y `503`; `/exports` suma `422` y las cabeceras de NFR10.4 (sus `403`, `404`, `409` y `503` ya están en FD-U7-05). Cambio menor en el PR de U1 que precede a B7 | NFR10.1–NFR10.5, NFR10.17 |
| NFR-U7-03 | §6 de la revisión 1 de este archivo (`report.storage_failed`) y §7 de functional-spec | Se retira el `code` propuesto `report.storage_failed`: el fallo de escritura o enlace en el volumen responde `500` `system.internal` y un *timeout* de base o de volumen `503` `system.unavailable`, como fija NFR10.17 de U3 y como pide §7 («code de sistema de la jerarquía de `libs/`») | NFR10.17 de U3; FD rev. 2 §7 |
| NFR-U7-04 | §6 de la revisión 1 (C15) e Infrastructure Design de U7 rev. 1 §6 (dos *gauges* en C15) | Las métricas de U7 son internas de `session-api` y **no** van a C15, que es el contrato de AIR de U5; se documentan en `observability-requirements.md` | NFR-U3-03 |
| NFR-U7-05 | Infrastructure Design de U7 rev. 1 (§2.1 rol `veridicus_report_ro`, §2.3 `Job` `veridicus-verify-store`, §3 su `NetworkPolicy`) | `verify_store` corre dentro del contenedor `api` (`kubectl exec … python -m session_api.review_report.verify_store`, lo ejecuta el humano), abre la base en una transacción `READ ONLY` y los archivos con `O_RDONLY`. Salen el `Job`, el rol y su regla de red: así se cumplen los tres usuarios de base de datos de U2 (NFR10.7 de U2) y el *exec* que ya usa `export_store`. Cierra R-01 de la revisión 1 | NFR10.7 y NFR10.13 de U2; R-01 |
| NFR-U7-06 | Infrastructure Design de U7 rev. 1 §2.2 (política `veridicus-reports-mounts`) | La política admite también el `Job` de retención de `deploy/jobs/`, en escritura, y ya no el de verificación | NFR10.16 de U2; C24 |
| NFR-U7-07 | Infrastructure Design de U2 y de U3 (`Ingress` de `/api/`) | Las respuestas de vista previa y exportación no se escriben en disco en `ingress-nginx` (NFR1.3) | `project.md` (*Ingress* de voz); NFR-U6-06 |
| NFR-U7-08 | Revisión 1 de este NFR, NFR Design e Infrastructure Design de U7 rev. 1 (paquete `forensic_report`, comandos `session_api.forensic_report.*`) | El paquete se llama `review_report` (glosario de `team.md`: «reporte de revisión» → `review_report`, VE-03); los comandos pasan a `session_api.review_report.*`. El slug del directorio sigue `forensic-report` (UG-08) | `team.md` (Code Style, Idioma); FD rev. 2 |
| NFR-U7-09 | C23 y functional-spec §12 pregunta 3 | El adaptador real de `AccessLog` tiene 500 ms en la exportación, el mismo plazo de NFR10.21 de U3; aquí un fallo o un vencimiento revierte toda la transacción y responde `503 report.export_not_recorded` (no un punto de guardado) | NFR-U3-05; BR9.6; FD-U13-11 |
| NFR-U7-10 | `requirements.md` (NFR7) y functional-spec §12 pregunta 6 | MTTV se mide sobre todas las transcripciones del conjunto sintético versionado de `evaluation/` (40 muestras hoy), cada una cargada como sesión **guiada** con un bloque pegado; las importadas no dan muestra (BR7.1, FD-U7-08) | NFR7; P7 = A; conjunto de U11 |
| NFR-U7-11 | Infrastructure Design de U7 rev. 1 §1.1 (memoria de la API) | Con `report_max_bytes` = 8 MiB, tres consolidaciones simultáneas del caso máximo suman ≤ 192 MiB y caben bajo el tope de 640 MiB (768 / 1,2) junto con los ≈ 410 MiB previos y una exportación del caso máximo (≤ 32 MiB) (NFR8.1) | NFR-U7-01 |
| NFR-U7-13 | functional-spec (barrido al arrancar, BR4.3) y tech-stack de la revisión 1 (D8 descartaba el barrido periódico) | El barrido de huérfanos corre también en cada pasada de la medición del volumen (60 s, Infrastructure Design de U7), con el mismo margen de 300 s, para que un pod de larga vida no conserve el archivo de un hilo vencido (NFR10.16, NFR8.8) | R-02 de la revisión 1 |
| NFR-U7-12 | §6 de la revisión 1 de este archivo | Se cierran sin cambios: `open_round(for_update=True)` (ya en C11 v2), `report.not_consolidated` (ya en C1), exclusiones del escaneo (FD-U7-07), roles de lectura (C1 con `[analista, admin]`), margen del barrido y `Recreate` (NFR Design e Infrastructure Design de U7), PVC de 2 GiB en lugar de 1 GiB (Infrastructure Design de U7) | Revisión 1 |
