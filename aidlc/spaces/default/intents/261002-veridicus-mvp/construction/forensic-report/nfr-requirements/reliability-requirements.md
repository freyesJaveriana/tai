# Requisitos de fiabilidad — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
  Entran NFR10.26 (exportación) y NFR10.27 (retención). Ninguno se retira.
- **Hallazgos de la revisión 1.** Se cierran R-01 (NFR10.20), R-02 (NFR8.8, NFR10.16), R-04 (NFR10.13)
  y R-05 (§4).

**Insumos.**
- Flujos F1–F10, máquinas de estado, §7 «Errores en la frontera» y §12 de
  `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1.2–BR1.4, BR2, BR4.1–BR4.4, BR5.1, BR6.2–BR6.5, BR9.2–BR9.6 y BR10.1–BR10.3 de
  `functional-design/rules.md` (rules), y entidades de `entities.md`.
- FR7, NFR8, NFR10 y NFR11 de `inception/requirements-analysis/requirements.md` (requirements,
  revisión 3), con A-2 y A-3 de la adenda 02.
- C1, C11, C16, C23 y C24 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements-questions.md`, segunda pasada, sin preguntas.

U7 no usa colas ni modelos: su fiabilidad descansa en una transacción de PostgreSQL y en el orden
«archivo antes que fila» sobre el volumen (P2 = A). Se reutilizan los *timeouts* de base (2 s por
sentencia, U3), el `lock_timeout` de 2 s (U5), el orden de bloqueo sesión → ronda con
`change_cursor.bump` (`project.md`) y los errores de sistema de NFR10.17 de U3: `500 system.internal` y
`503 system.unavailable`.

## 1. Objetivos

El MVP no tiene SLA ni objetivo de disponibilidad propio: U7 vive en la API de `session-api` y comparte su
disponibilidad (1 réplica, NFR8.6). Sus objetivos medibles son de corrección: ninguna versión sin
archivo, ninguna consolidación doble, ninguna vista previa ni exportación alterada y ninguna exportación
sin registrar.

| ID | Estado | Objetivo | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.7 | cambia | El flujo del reporte funciona de punta a punta. | `frontend/e2e/report.spec.ts`: finalizar con 2 corridas en curso, esperar, decidir la última pendiente, consolidar, copiar el SHA-256, abrir la vista previa (aviso en cada página), exportar y comparar `export_sha256` con el archivo bajado, corregir, consolidar la versión 2, exportar la versión 1 con su rótulo de reemplazo, abrir y descartar otra copia, ver la sesión como otro analista en solo lectura y exportarla como `admin`. 0 fallos en cada corrida de nivel 3 antes de etiquetar una entrega. | Nivel 3 |
| NFR8.8 | cambia | Ninguna `ReportVersion` queda sin su archivo íntegro y ningún huérfano sobrevive al barrido. | Tras toda la suite de nivel 1 (incluidos los fallos inyectados de §2 y el hilo del volumen que vence) y una pasada del barrido de NFR10.16 con el reloj inyectado 301 s después, `verify_store` (NFR10.20) informa 0 versiones sin archivo, 0 SHA-256 distintos y 0 huérfanos. La prueba no reinicia la API: el barrido periódico lo cubre (cierra R-02). | Nivel 1 |

## 2. Transacción y concurrencia

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.12 | cambia | La consolidación es todo o nada (BR4.1, ADR-001). | Una sola `UnitOfWork` cubre la guardia, la inserción de `ReportVersion`, `lock_round` y, en la versión 1, la transición de la sesión (con la finalización de una importada, BR2.10). Fallo inyectado después de la guardia, del render, del escaneo, de escribir el temporal, del enlace, de insertar, dentro de `lock_round`, dentro de la transición y en el *commit*: 0 filas nuevas, ronda `open`, sesión en su estado, **0 archivos** tras la limpieza y la respuesta `409 report.conflict` (carrera), `413 limits.exceeded` (NFR8.9), `500 system.internal` (volumen, NFR-U7-03) o `503 system.unavailable` (*timeout*). Las métricas cambian solo después del *commit*. | Nivel 1 |
| NFR10.13 | cambia | De dos consolidaciones simultáneas gana una (BR4.2). | Se toma primero la fila de la sesión (`change_cursor.bump`) y después `open_round(..., for_update=True)` (C11 v2); la segunda espera y, al obtener el bloqueo, ya no hay ronda abierta → `409 report.conflict`. Dos hilos, barrera y dos conexiones reales, 50 repeticiones sobre la versión 1 y 50 sobre una corrección: un `201` y un `409`, 1 fila y **1 archivo** por repetición. **Resultado esperado cuando la ganadora tarda más que el `lock_timeout`** (caso máximo, NFR3.13, o prueba con una ganadora frenada 3 s): la perdedora responde `503 system.unavailable` en ≤ 2,5 s con 0 filas y 0 archivos, y la consola muestra el mensaje de `system.unavailable` del catálogo de U1 y vuelve a pedir la sesión, que ya aparece consolidada; el analista no reintenta solo (cierra R-04). `UNIQUE (session_id, version_number)` es la segunda barrera. | Nivel 1 |
| NFR10.14 | cambia | Una decisión o una corrida simultánea a la consolidación no queda fuera del reporte. | Decisión de U5 a la vez que la consolidación (barrera, 50 repeticiones): o aparece en el reporte y en `decisions` de la ronda, o recibe `409 review.round_locked`; nunca hay una `ReviewDecision` posterior al `locked_at` de su ronda, y el estado de cada sugerencia en el Markdown es el vigente de la ronda bloqueada. Una corrida que termina durante la consolidación: o la guardia la ve en curso y responde `409 report.runs_in_progress`, o su resultado entra antes del bloqueo. | Nivel 1 |
| NFR10.15 | cambia | Archivo antes que fila, y limpieza si la transacción falla (BR4.1, BR4.3, P2 = A). | Orden fijo: render → comprobación de `report_max_bytes` → escaneo → SHA-256 → `<report_version_id>.md.tmp` con `O_EXCL` → `write` → `fsync` → enlace sin reemplazo → `fsync` del directorio → inserción y bloqueo → *commit*. Si algo falla después de crear el temporal, se borra el temporal o el final con `WARNING report.file_cleaned`; si el borrado falla, `ERROR report.cleanup_failed` y el archivo queda para el barrido. Pruebas con `ENOSPC` (sistema de archivos pequeño), sin permiso de escritura y con fallo del *commit*: 0 filas y, tras el barrido, 0 archivos. | Nivel 1 |
| NFR10.16 | cambia | El barrido de huérfanos no borra consolidaciones en vuelo y también corre en un pod de larga vida. | Corre al arrancar, antes de que `/readyz` responda `200`, **y en cada pasada de la medición del volumen** (`VERIDICUS_REPORT_VOLUME_SCAN_INTERVAL_SECONDS` = 60, Infrastructure Design; NFR-U7-13). Borra los `*.md.tmp` y los `*.md` sin fila con **más de 300 s** (`VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS`); cada borrado deja `WARNING report.orphan_removed` con el nombre del archivo y `+1` en `veridicus_report_orphans_removed_total`. Cualquier otro nombre queda con `WARNING report.unexpected_file` sin borrarse. Las dos ejecuciones nunca se solapan (un candado en proceso; 1 réplica, NFR8.6). Pruebas: huérfanos viejos borrados; un archivo de 10 s en vuelo **no** se borra y su consolidación termina con `201`; un final con fila nunca se toca; el archivo del hilo vencido de NFR10.17 se borra en la pasada siguiente a sus 300 s; con 1 000 archivos el barrido termina en ≤ 5 s. | Nivel 1 |
| NFR10.21 | cambia | Finalizar es una sola vez y no compite con el ingreso de turnos (BR1.2, BR1.3). | La transición es un `UPDATE … WHERE status IN ('open', 'paused', 'suspended', 'blocked')` con la fila de la sesión bloqueada. Dos finalizaciones simultáneas (50 repeticiones): un `200` y un `409 session.finalized`, 1 fila de historial. Un turno nuevo simultáneo: o entra antes (y la guardia lo ve en curso) o recibe `409 session.finalized`. Las corridas en cola terminan y sus resultados se guardan (BR1.4); una corrida colgada la cierra el supervisor de U4 por su plazo, así que la guardia nunca bloquea para siempre. | Nivel 1 |
| NFR10.26 | nuevo | La exportación es todo o nada y nunca envía bytes sin registro (BR9.5, BR9.6, A-3). | Una transacción: lectura y verificación del SHA-256 de la versión, armado de la marca, `export_sha256`, inserción de `ReportExport` y `AccessLog.record` (500 ms, NFR-U7-09); los bytes salen solo tras el *commit*. Fallo inyectado en cada paso (lectura, verificación, inserción, `AccessLog` que falla, `AccessLog` que tarda 600 ms, *commit*): 0 `ReportExport`, 0 bytes y `409 report.integrity_mismatch`, `503 report.export_not_recorded` o `503 system.unavailable` según el paso. Si el cliente corta la conexión después del *commit*, la fila queda (la exportación se registró aunque no llegara) y se ve en el log `INFO report.exported`. Dos exportaciones simultáneas de la misma versión dan dos filas con su `export_id`. | Nivel 1 |
| NFR10.27 | nuevo | `purge_session` es completa o se repite sin daño (BR10.1–BR10.3, C24). | Corre dentro de la transacción por sesión del `Job` de U13. Orden: `ReportExport` → `ReportVersion` de la más nueva a la más antigua, archivo antes que fila. Un archivo que ya falta da `file_missing: true` y un `WARNING` con IDs, y el borrado sigue. Fallo inyectado tras borrar el archivo de la versión 2 de 3: la transacción se revierte, las filas quedan y la vista previa de esa versión responde `409 report.integrity_mismatch`; la siguiente ejecución termina el borrado con `file_missing: true` para esa versión. Cada borrado de archivo dentro de 5 s; p95 de NFR3.14. Nunca se reintenta dentro de la misma ejecución. | Nivel 1 |

## 3. Tiempos de espera, reintentos y arranque

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.17 | cambia | Toda E/S de U7 tiene *timeout* explícito, leído de la configuración validada al arrancar. | PostgreSQL: `statement_timeout` y `lock_timeout` de 2 s. Volumen: cada operación (escritura + `fsync` + enlace; lectura completa; borrado) en un hilo con espera máxima de **5 s** (`VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS`). Consolidación y exportación completas: plazo de **10 s** (`VERIDICUS_REPORT_CONSOLIDATION_TIMEOUT_SECONDS`, el mismo para las dos) comprobado antes del *commit*, con `idle_in_transaction_session_timeout` de 15 s. `AccessLog.record` en la exportación: **500 ms** (NFR-U7-09). Al vencer: *rollback*, limpieza de NFR10.15, `503 system.unavailable` (o `503 report.export_not_recorded` si venció `AccessLog`), 0 filas y `WARNING` con `code`. Pruebas con un almacén que tarda 6 s, una base retenida 3 s, una consolidación de más de 10 s y un `AccessLog` de 600 ms: `503` en ≤ 6,5 s, ≤ 2,5 s, ≤ 10,5 s y ≤ 1 s. | Nivel 0 (configuración) y nivel 1 |
| NFR10.18 | cambia | Nada de U7 se reintenta solo. | Consolidar, finalizar, corregir, descartar y exportar no son idempotentes (cada exportación crea su `ReportExport`): ni el servidor ni la consola los reintentan. Ante red, `500` o `503`, la consola muestra el mensaje del catálogo y vuelve a pedir la sesión; si la consolidación sí se guardó, aparece `consolidated` y un reenvío manual recibe `409 report.conflict`. La vista previa se puede repetir, solo a mano. Vitest con un *fake* que falla, que responde `503` y que responde `409`. | Vitest |
| NFR10.19 | cambia | `/readyz` refleja lo que U7 necesita (C16). | `503` mientras falte o sea inválida la configuración de U7 (`tech-stack-decisions.md` §2), si `VERIDICUS_REPORTS_DIR` no existe y no se puede crear con `0700`, si existe con otro dueño o modo, si no es escribible, si quedan menos de `VERIDICUS_REPORT_MIN_FREE_BYTES` libres o si el uso supera `VERIDICUS_REPORT_VOLUME_QUOTA_BYTES`, o si el barrido de arranque no terminó. Con el adaptador por defecto de `AccessLog`, `200` con `access_log: not_configured` (C23). Configuración inválida → el proceso termina con código distinto de 0 y un log que nombra el ajuste. Una prueba de nivel 0 por regla y pruebas de nivel 1 con el volumen sin montar, de solo lectura, con el subdirectorio en `0755` y casi lleno. | Nivel 0 y nivel 1 |

## 4. Respaldo y verificación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.20 | cambia | Se puede comprobar en cualquier momento que cada versión tiene su archivo íntegro. | `python -m session_api.review_report.verify_store`, que el humano ejecuta con `kubectl exec` dentro del contenedor `api` (mismo UID que escribió los archivos, sin otro pod sobre el PVC RWO; cierra R-01, NFR-U7-05). Abre la base en una transacción `READ ONLY` y los archivos con `O_RDONLY`; recorre todas las `ReportVersion`, recalcula cada SHA-256 y lista huérfanos; imprime solo IDs y conteos y termina con código 0 solo si hay 0 versiones sin archivo y 0 SHA-256 distintos. Se ejecuta tras cada restauración y antes de la sustentación. Nivel 1 con un archivo alterado y otro borrado: código 1 y los dos `report_version_id`; prueba de que no escribe (fila y `st_mtime` iguales). | Nivel 1 y manual |

**RPO y RTO (cierra R-05).** El respaldo es conjunto y a pedido (P2 = A de Infrastructure Design):
`scripts/backup-db.sh` más `export_store`, que el humano ejecuta antes de la sustentación y antes de
cada PR que trae una migración de U7. **RPO** = el último respaldo conjunto; nada posterior está
protegido, y es aceptable porque los datos son sintéticos (NFR12). **RTO**: restaurar base y volumen y
obtener `verify_store` con código 0 en **≤ 30 min**, medido una vez en un ensayo manual antes de la
sustentación con el caso de 100 turnos y 10 versiones. Si una restauración deja la base más nueva que el
volumen, las versiones afectadas responden `409 report.integrity_mismatch` y `verify_store` las lista;
nunca se entrega un archivo distinto del registrado.

## 5. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de la API a mitad de una consolidación o una exportación | Nada confirmado | Un archivo de consolidación que quedó lo borra el barrido pasado su margen (NFR10.16); la exportación no deja archivos. El analista repite la acción |
| Volumen lleno o sin escritura | Nada | `500 system.internal`, 0 filas; `/readyz` pasa a `503` bajo el mínimo libre o sobre la cuota (NFR10.19) y la regla de NFR15.3 lo muestra antes |
| PostgreSQL no responde | Nada guardado | `503 system.unavailable`; el archivo escrito se limpia (NFR10.15) |
| Adaptador real de `AccessLog` caído | Las exportaciones mientras dure | `503 report.export_not_recorded`; la vista previa sigue (su registro es en punto de guardado, U3); `veridicus_report_exports_total{result="not_recorded"}` lo muestra |
| Archivo alterado o borrado | La vista previa y la exportación de esa versión | `409 report.integrity_mismatch` y `ERROR`; se restaura del respaldo y `verify_store` confirma el SHA-256 |
| Pérdida del PVC | Los archivos de los reportes | Restauración del respaldo conjunto; las filas se conservan y `verify_store` lista lo que falte |
| Purga interrumpida | Nada confirmado | La siguiente ejecución del `Job` termina el borrado (NFR10.27) |

## 6. Degradación

Si el juez, Redis o el trabajador de `session-api` no están disponibles, U7 sigue funcionando para lo ya
evaluado: se puede finalizar, consolidar (si no hay corridas en curso), ver la vista previa, exportar y
corregir, porque U7 solo necesita PostgreSQL, el volumen y, para exportar con U13, el registro de acceso.
Las corridas que quedaron en curso las cierra el supervisor de U4 por su plazo y dejan de bloquear. Si
Prometheus no está, no hay métricas, pero ninguna operación depende de ellas.
