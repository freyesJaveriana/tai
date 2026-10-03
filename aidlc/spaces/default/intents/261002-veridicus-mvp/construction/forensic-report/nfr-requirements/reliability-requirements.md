# Requisitos de fiabilidad — U7 forensic-report

**Insumos.** Flujos F1–F7, máquinas de estado de §3 y §7 «Errores en la frontera» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1.2, BR1.4, BR2, BR4.1–BR4.4,
BR5.1 y BR6.2–BR6.5 de `functional-design/rules.md` (rules) y entidades de `entities.md`; FR7, NFR8,
NFR10 y NFR11 de `inception/requirements-analysis/requirements.md` (requirements); C1 y C11 y las
reglas de propiedad de `inception/contract-design/contract-summary.md` (contract-summary);
`nfr-requirements-questions.md` (sin preguntas nuevas).

U7 no usa colas ni modelos: su fiabilidad descansa en una transacción de PostgreSQL y en el orden
«archivo antes que fila» sobre el volumen (P2 = A). Los *timeouts* de base (2 s por sentencia, U3), el
`lock_timeout` de 2 s (D3 de U5) y el error `503` `system.unavailable` (U3) se reutilizan; aquí se
fijan los propios de U7.

## 1. Objetivos

El MVP no tiene SLA ni objetivo de disponibilidad propio: U7 vive en la API de `session-api` y comparte
su disponibilidad (1 réplica, NFR8.6). Sus objetivos medibles son de corrección: ninguna versión sin
archivo, ninguna consolidación doble y ninguna descarga alterada.

| ID | Objetivo | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.7 | El flujo del reporte funciona de punta a punta. | `frontend/e2e/report.spec.ts` (finalizar con 2 turnos en curso, esperar, decidir la última pendiente, consolidar, copiar el SHA-256, descargar y comparar el SHA-256 del archivo, corregir, consolidar la versión 2, abrir y descartar otra copia, y ver la sesión como otro analista en solo lectura) pasa con 0 fallos en cada corrida de nivel 3 antes de etiquetar una entrega. | Nivel 3 |
| NFR8.8 | Ninguna `ReportVersion` queda sin su archivo íntegro. | Tras toda la suite de nivel 1 (incluidas las pruebas de fallos inyectados de §2), el comando de NFR10.20 informa 0 versiones sin archivo, 0 SHA-256 distintos y 0 archivos huérfanos de más de 300 s. | Nivel 1 |

## 2. Transacción y concurrencia

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.12 | La consolidación es todo o nada (BR4.1, ADR-001). | Una sola `UnitOfWork` cubre la guardia, la inserción de `ReportVersion`, `lock_round` y, en la versión 1, `mark_consolidated`. Pruebas con fallo inyectado en cada paso (después de la guardia, después del render, después de escribir el temporal, después del renombrado, después de insertar, dentro de `lock_round`, dentro de `mark_consolidated` y en el *commit*): en todos los casos 0 filas nuevas, la ronda sigue `open`, la sesión sigue en su estado, **0 archivos** (temporal o final) tras la limpieza y la respuesta es `409` `report.conflict` (si perdió la carrera), `500` `report.storage_failed` (volumen) o `503` `system.unavailable` (*timeout*). Las métricas cambian solo después del *commit*. | Nivel 1 |
| NFR10.13 | De dos consolidaciones simultáneas gana una (BR4.2). | La consolidación toma `open_round(..., for_update=True)` (precisión en `security-requirements.md` §6) al empezar; la segunda espera el bloqueo y, al obtenerlo, ya no hay ronda abierta (BR2.7) → `409` `report.conflict`. Con dos hilos, una barrera y dos conexiones a PostgreSQL real, 50 repeticiones sobre la versión 1 y 50 sobre una corrección: exactamente un `201` y un `409` `report.conflict`, 1 fila nueva y **1 solo archivo** en el volumen por repetición. Si la ganadora tarda más que el `lock_timeout` (prueba aparte con una consolidación frenada 3 s), la perdedora responde `503` `system.unavailable` en ≤ 2,5 s, con 0 filas y 0 archivos. La restricción `UNIQUE (session_id, version_number)` es la segunda barrera (prueba que la viola directamente). | Nivel 1 |
| NFR10.14 | Una decisión simultánea a la consolidación no queda fuera del reporte. | Con una decisión de U5 lanzada a la vez que la consolidación (dos hilos, barrera, 50 repeticiones): o la decisión aparece en el reporte consolidado y en `decisions` de la ronda, o recibe `409` `review.round_locked`; nunca hay una `ReviewDecision` con `at` posterior al `locked_at` de su ronda, y el estado de cada sugerencia en el Markdown es igual al estado vigente de la ronda bloqueada (BR6.6). Lo mismo con un turno que termina (C3) durante la consolidación: o la guardia lo ve en curso y responde `409` `report.turns_in_progress`, o su resultado entra antes del bloqueo. | Nivel 1 |
| NFR10.15 | Archivo antes que fila, y limpieza si la transacción falla (BR4.1, BR4.3, P2 = A). | Orden fijo: render → escaneo → SHA-256 → `<report_version_id>.md.tmp` con `O_EXCL` → `write` → `fsync` del archivo → renombrado sin reemplazo → `fsync` del directorio → inserción y bloqueo → *commit*. Si algo falla después de crear el temporal, se borra el temporal o el final y se registra `WARNING` `report.file_cleaned`; si el borrado también falla, se registra `ERROR` `report.cleanup_failed` y el archivo queda para el barrido (NFR10.16). Prueba con el volumen lleno (`ENOSPC` simulado con un sistema de archivos pequeño), sin permiso de escritura y con fallo del *commit*: 0 filas y, tras el barrido, 0 archivos. | Nivel 1 |
| NFR10.16 | El barrido de huérfanos no borra consolidaciones en vuelo. | Al arrancar, antes de que `/readyz` responda `200`, ForensicReport lista el directorio y borra los `*.md.tmp` y los `*.md` sin fila en `ReportVersion` **con más de 300 s** (`VERIDICUS_REPORT_ORPHAN_MIN_AGE_SECONDS`); cada borrado deja un `WARNING` `report.orphan_removed` con el nombre del archivo y `+1` en `veridicus_report_orphans_removed_total`. Ignora cualquier otro nombre (lo registra como `WARNING` `report.unexpected_file` sin borrarlo). Pruebas de nivel 1: huérfanos viejos borrados, un archivo de 10 s de una consolidación en vuelo **no** se borra y su consolidación termina con `201` y descarga íntegra (hallazgo R-02 del Functional Design), un final con fila nunca se toca. Con 1 000 archivos el barrido termina en ≤ 5 s. | Nivel 1 |
| NFR10.21 | Finalizar es una sola vez y no compite con el ingreso de turnos (BR1.2, BR1.3). | La transición a `finalized` es un `UPDATE … WHERE status IN ('open', 'suspended')` con la fila de la sesión bloqueada (como BR5.2 de U4). Dos finalizaciones simultáneas (50 repeticiones): un `200` y un `409` `session.finalized`, 1 fila de historial. Un turno nuevo simultáneo a finalizar: o entra antes (y la guardia lo ve en curso) o recibe `409` `session.finalized` con 0 filas. Los turnos que estaban en cola terminan y sus resultados se guardan (BR1.4); si un turno queda colgado, la revisión de plazos de U4 lo pasa a `error` antes de `deadline_at` + 30 s (NFR10.17 de U4), así que la guardia BR2.3 nunca bloquea para siempre (hallazgo R-04 del Functional Design). | Nivel 1 |

## 3. Tiempos de espera, reintentos y arranque

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.17 | Toda E/S de U7 tiene *timeout* explícito, leído de la configuración validada al arrancar. | PostgreSQL: `statement_timeout` de 2 s (U3) y `lock_timeout` de 2 s (U5) por sentencia. Volumen: cada operación (escritura + `fsync` + renombrado al consolidar; lectura completa al descargar) corre en un hilo con espera máxima de **5 s** (`VERIDICUS_REPORT_STORAGE_TIMEOUT_SECONDS`). Consolidación completa: plazo de **10 s** (`VERIDICUS_REPORT_CONSOLIDATION_TIMEOUT_SECONDS`) comprobado antes del *commit*, con `idle_in_transaction_session_timeout` de 15 s en la conexión como respaldo. Al vencer cualquiera: *rollback*, limpieza de NFR10.15, `503` `system.unavailable`, 0 filas y `WARNING` con `code`. Pruebas con un almacén que tarda 6 s, una base retenida 3 s y una consolidación que supera 10 s: `503` en ≤ 6,5 s, ≤ 2,5 s y ≤ 10,5 s. | Nivel 0 (configuración) y nivel 1 |
| NFR10.18 | Nada de U7 se reintenta solo. | Consolidar, finalizar, corregir y descartar no son idempotentes: ni el servidor ni la consola los reintentan. Si la petición falla por red, `500` o `503`, la consola muestra el mensaje del catálogo y vuelve a pedir la sesión; si la consolidación sí se guardó, la sesión aparece `consolidated` con su versión y un reenvío manual recibe `409` `report.conflict`. La descarga sí se puede repetir (es de lectura) pero solo a mano. Vitest con un servidor *fake* que falla, que responde `503` y que responde `409`. | Vitest |
| NFR10.19 | `/readyz` refleja lo que U7 necesita (C16). | `503` mientras falte o sea inválida la configuración de U7 (`tech-stack-decisions.md` §2), si el directorio de reportes no existe, no es escribible o no tiene modo `0700`, si quedan menos de 50 MiB libres en el volumen, o si el barrido de NFR10.16 no terminó. Configuración inválida → el proceso termina con código distinto de 0 y un log que nombra el ajuste. Una prueba de nivel 0 por regla de configuración y pruebas de nivel 1 con el volumen sin montar, de solo lectura y casi lleno. | Nivel 0 y nivel 1 |

## 4. Respaldo y verificación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.20 | Se puede comprobar en cualquier momento que cada versión tiene su archivo íntegro. | Comando de solo lectura `python -m session_api.forensic_report.verify_store` (también empaquetado como `Job` revisable que monta el volumen en solo lectura, AUTONOMIA-01): recorre todas las `ReportVersion`, recalcula el SHA-256 de cada archivo y lista huérfanos; imprime solo identificadores y conteos y termina con código 0 solo si hay 0 versiones sin archivo y 0 SHA-256 distintos. Se ejecuta tras cada restauración y antes de la sustentación. Prueba de nivel 1 con un archivo alterado y otro borrado: código 1 y los dos `report_version_id`. | Nivel 1 y manual (tras restaurar) |

El RPO y el RTO de los reportes son los del respaldo conjunto de CloudNativePG y del PVC que fije
Infrastructure Design (precisión en `security-requirements.md` §6). Si una restauración deja la base
más nueva que el volumen, las versiones afectadas responden `409` `report.integrity_mismatch` y
NFR10.20 las lista; nunca se entrega un archivo distinto del registrado.

## 5. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de la API a mitad de una consolidación | Nada confirmado: la transacción se revierte | Si quedó un archivo, el barrido lo borra en el siguiente arranque pasado su margen (NFR10.16); el analista vuelve a consolidar |
| Volumen lleno o sin escritura | Nada | `500` `report.storage_failed`, 0 filas; `/readyz` pasa a `503` bajo 50 MiB libres (NFR10.19) y la alerta de NFR15.3 avisa antes |
| PostgreSQL no responde | Nada guardado | `503` `system.unavailable`; el archivo escrito se limpia (NFR10.15) |
| Archivo alterado o borrado en el volumen | La descarga de esa versión | `409` `report.integrity_mismatch` y `ERROR`; se restaura el archivo del respaldo y NFR10.20 confirma el SHA-256 |
| Pérdida del PVC | Los archivos de los reportes | Restauración del respaldo conjunto (Infrastructure Design); las filas se conservan y NFR10.20 lista lo que falte |

## 6. Degradación

Si el juez, Redis o el trabajador de `session-api` no están disponibles, U7 sigue funcionando para lo
ya evaluado: se puede finalizar, consolidar (si no hay turnos en curso), descargar y corregir, porque U7
solo necesita PostgreSQL y el volumen. Los turnos que quedaron en curso terminan en `error` por la
revisión de plazos de U4 cuando el trabajador vuelve, y entonces dejan de bloquear (BR2.6). Si
Prometheus no está, no hay métricas, pero ninguna operación depende de ellas.
