# Preguntas de NFR Design — U7 forensic-report

**Unidad.** U7 `forensic-report` (reporte forense): finalizar la sesión, consolidar el reporte con la
acción explícita del analista dueño (quién, cuándo y SHA-256 de los bytes guardados), versiones y
correcciones que nunca reescriben la anterior, descarga con comprobación de integridad y barrido de
huérfanos del volumen.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D12 de
`nfr-requirements/`: render propio y canónico (`format_version` 1), escape del Markdown, escaneo C8 con
`literal_sources`, puerto `ReportStore` sobre el PVC con `O_EXCL`, `fsync` y renombrado sin reemplazo,
archivo antes que fila dentro de una sola `UnitOfWork`, plazos (volumen 5 s, consolidación 10 s,
`lock_timeout` y `statement_timeout` de 2 s), barrido al arrancar con margen de 300 s, 1 réplica con
`Recreate`, descarga leída entera y comprobada antes del primer byte, nada se reintenta solo, `ReportVersion`
de solo inserción, y la entrada única de `consolidate` desde la ruta de ConsoleApi. También el orden de
bloqueo sesión → ronda de U5: la consolidación empieza con `open_round(for_update=True)`, que hace
`change_cursor.bump` sobre la sesión antes de bloquear la ronda. Quedan dos huecos de diseño.

---

## P1 — Cómo se asegura que el analista consolida exactamente lo que revisó

AUTONOMIA-03 exige una validación explícita del analista. Hoy el diálogo de «Finalizar y Consolidar»
(BR8.1) muestra un resumen calculado con la última `SessionView` del sondeo, pero `POST
/sessions/{id}/reports` no lleva cuerpo: si entre abrir el diálogo y pulsar «Consolidar» cambia una
decisión (por ejemplo, desde otra pestaña del mismo analista) o se abre otra ronda, la guardia solo
comprueba que no haya pendientes y el reporte sellado con su SHA-256 puede contener un estado que el
analista nunca vio en el resumen que confirmó.

A. La petición lleva el cursor de la vista con la que se armó el diálogo (`expected_cursor`, el mismo
   cursor opaco `change_seq` del sondeo de U4). Tras `open_round(for_update=True)`, con la sesión ya
   bloqueada, el servidor lo compara con el `change_seq` vigente; si difiere, responde `409` con un
   `code` nuevo `report.view_outdated` (entra por el PR de U1), 0 filas y 0 archivos, y la consola
   vuelve a pedir la sesión y muestra el resumen actualizado. Prueba de nivel 1: una decisión
   confirmada entre el diálogo y la consolidación da `409` en 50 de 50 repeticiones. (Recomendada)
B. Se mantiene lo aprobado: sin cuerpo y sin comparación. El reporte refleja el estado vigente al
   consolidar; la vista posterior (BR8.2) lo muestra y, si no era lo esperado, se corrige con una
   versión nueva.
C. Consolidación en dos pasos: un `POST` genera una vista previa con su SHA-256 sin guardar nada, y un
   segundo `POST` confirma ese SHA-256 exacto; el servidor vuelve a renderizar y solo consolida si los
   bytes coinciden. El analista confirma los bytes exactos, a costa de renderizar dos veces (≈ 1 s
   más) y de una pantalla de vista previa nueva.
X. Other (please specify)

[Answer]: A **Mode:** guided
## P2 — Qué pasa con el archivo que escribe un hilo del volumen cuando vence su plazo

D6 ejecuta cada escritura en un hilo con espera máxima de 5 s, pero ese hilo no se puede cancelar: si
vence, la consolidación se revierte y responde `503`, y el hilo puede terminar después y dejar en el
volumen un archivo completo del caso sin fila ni dueño. Hoy solo lo borra el barrido del siguiente
arranque; con 1 réplica que casi no se reinicia, puede quedar ahí días, y choca con NFR8.8 (0 huérfanos
de más de 300 s) y con la idea de no dejar copias del caso fuera del registro.

A. Cancelación cooperativa: cada escritura recibe un testigo que la consolidación marca como abandonado
   al vencer el plazo; el hilo lo consulta antes de crear el temporal, después del `fsync` y antes del
   renombrado, y si está marcado borra su propio archivo (temporal o final) y registra `WARNING`
   `report.file_cleaned`. Si el borrado falla, queda `ERROR` `report.cleanup_failed` y el barrido del
   arranque como respaldo. Prueba de nivel 1 con un almacén que tarda 6 s: `503` y 0 archivos a los
   10 s. (Recomendada)
B. Se mantiene lo aprobado: el archivo tardío queda hasta el siguiente arranque y `verify_store` lo
   lista mientras tanto.
C. Barrido periódico en el proceso de la API (cada 10 minutos) con el mismo margen de 300 s, además
   del barrido al arrancar.
X. Other (please specify)

[Answer]: A **Mode:** guided