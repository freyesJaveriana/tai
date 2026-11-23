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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Sin preguntas: todo lo fijan las fuentes.** Ninguna decisión de esta pasada enfrenta dos fuentes
aprobadas sin una salida que cumpla las dos. Tampoco cambia el alcance, el riesgo aceptado ni un dato que
sale del clúster (regla de `project.md` del 2026-11-22). Lo que se aplica sin preguntar queda en la tabla
NFRD-U7-xx de `security-design.md` §14 y se presenta en la aprobación.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| Módulo y paquete | ReviewReport, paquete `review_report`; el directorio sigue `forensic-report` | NFR-U7-08; `team.md` (glosario) |
| Roles | Leen los analistas y el `admin`; exportan el dueño y el `admin`; consolidan, corrigen y descartan solo el dueño | FR1; VE-13; NFR10.1, NFR10.2, NFR10.23 |
| Exportación | Marca por página, `export_sha256`, `ReportExport` de solo inserción, sin guardar bytes, `AccessLog` en 500 ms con falla cerrada | BR9; A-3; NFR10.24–NFR10.26, NFR11.7; NFR-U7-09; U3 (`record_access_strict`) |
| Retención | `purge_session` con `veridicus_retention`; archivo antes que fila; recibo sin texto | C24; VE-12; NFR11.8, NFR10.27 |
| Cifras | `report_max_bytes` = 8 MiB; PVC de 2 GiB con cuota; 768 MiB de memoria; almacén 5 s; consolidación y exportación 10 s; 15 s de inactividad | NFR-U7-01, NFR-U7-11; NFR10.17; tech-stack §2 |
| Errores | `500 system.internal` y `503 system.unavailable`; sale `report.storage_failed` | NFR-U7-03; NFR10.17 de U3 |
| Métricas | Internas de `session-api`, fuera de C15 | NFR-U7-04; NFR Design de U1 |
| Verificación del almacén | `verify_store` por `kubectl exec`, sin `Job` ni rol | NFR-U7-05; lista de `exec` de U2 |
| `Ingress` | Sin buffering ni temporales en todo `/api/` | NFR1.3; NFR Design de U2 §3 |
| Barrido | Al arrancar y cada 60 s, con margen de 300 s | NFR-U7-13; NFR10.16 |
| Respuestas de la primera pasada | **Siguen** P1 = A (cursor de lo revisado) y P2 = A (cancelación cooperativa); ninguna fuente aprobada las retiró | Respuestas del humano (revisión 1) |
| Cursor | Es el de la sesión, `v1.<session_id>.<n>` con `n` = `change_cursor` | NFRD-U4-05 |

## Cómo se registra la revisión

- Los seis documentos llevan la cabecera «Revisión 2 (2026-11-22)…», que sustituye a la revisión 1 y dice
  qué cambia. Las secciones conservan su número; lo que sale queda «Retirado» y lo nuevo toma el número
  siguiente.
- Las tablas de precisiones de la revisión 1 que estaban repartidas por varios documentos se reúnen en una
  sola tabla, **NFRD-U7-01…** (`security-design.md` §14). Las demás tablas quedan «Retirado».
- Las amenazas T16 y T17 de la revisión 1 pasan a T21 y T22, porque NFR Requirements revisión 2 usó
  T16–T20.
- Las decisiones de diseño se recogen en una tabla DSn (`security-design.md` §12).
- `traceability.json` lleva `"revision": 2` y los 78 IDs de NFR Requirements revisión 2.
- Se cierran los hallazgos R-01 a R-04 de `reviews/review-01.md` en las secciones que los citan.

## Lo que el diseño resolverá sin preguntar

1. **Plazo de inactividad: 5 s en U6 frente a 15 s en U7 (pendiente de U12).** Las fuentes aprobadas lo
   deciden, así que no es una pregunta:
   - el NFR Design de U4 y U6 fija los 5 s con `SET LOCAL` en sus propias transacciones;
   - NFR10.17 de U7 fija 15 s para consolidar y exportar.

   Son alcances distintos, no valores en conflicto. Solo los dos Infrastructure Design lo escribieron sin
   alcance. Se aplica `SET LOCAL` de 15 s como primera sentencia de los manejadores de U7, sin valor por
   conexión ni por rol (DS3). Se registran tres entradas:
   - la precisión a los Infrastructure Design de U6 y U7 (NFRD-U7-01, que cierra R-02 de la revisión de
     Infrastructure Design de U7);
   - la nota para U12 (NFRD-U7-02);
   - la petición del parámetro en `db.py` (NFRD-U7-03).
2. **COMMIT con resultado desconocido (R-01).** La limpieza corre solo tras un *rollback* cierto. Si el
   `COMMIT` falla, el archivo se queda y el barrido lo borra solo si no hay fila (DS4; petición a U3,
   NFRD-U7-05).
3. **Exportación frente a purga.** `FOR KEY SHARE` sobre la versión al exportar y `FOR UPDATE` sobre las
   versiones al purgar (DS5, NFRD-U7-06).
4. **P1 = A frente a C1 revisión 3.** C1 no llevó el cuerpo `{ expected_cursor }`, así que se vuelve a pedir
   a U1 con su límite (NFRD-U7-04). La métrica recupera `outdated` (NFRD-U7-08).
5. **P2 = A frente al texto de D6.** Se precisa que el hilo se cancela de forma cooperativa (NFRD-U7-07).
6. **Presupuesto del bloqueo (R-02), cursor de la sesión (R-03) y *executor* colgado (R-04).** Se tratan en
   `performance-design.md` §1, en `security-design.md` §3 y en `reliability-design.md` §3.