# Reglas de negocio — U7 forensic-report

**Alcance.** Las reglas BR2, BR4 y BR6 forman el módulo guardia de consolidación de AUTONOMIA-03, que
exige 100 % de ramas (team-practices). La autorización por dueño la aplica ConsoleApi antes de delegar
(ADR-009). Cada regla repite aquí la verificación que exige, para que la prueba la pueda citar.

```yaml
rules:
  # BR1 — Finalizar la sesión (US2.4)
  - id: BR1.1
    statement: Solo el dueño de la sesión puede finalizarla.
    category: authorization
    applies_to: POST /sessions/{session_id}/finalize
    trigger: Petición de finalizar
    logic: SI el actor no es el dueño, es admin o es una identidad de servicio ENTONCES 403 auth.forbidden y 0 filas.
    violation: 403 Problem Details; no cambia el estado.
    source: FR3.5, ADR-009, AC2.4.2
  - id: BR1.2
    statement: Una sesión se finaliza desde open o desde suspended, una sola vez.
    category: constraint
    applies_to: InterviewSessionRecord.status
    trigger: Petición de finalizar del dueño
    logic: SI la sesión está open o suspended ENTONCES pasa a finalized; SI ya está finalized o consolidated ENTONCES 409 session.finalized y 0 filas.
    violation: 409 session.finalized.
    source: FR3.5, session-lifecycle (finalizar desde suspended lo decide U7)
  - id: BR1.3
    statement: Finalizar guarda en UTC la hora de inicio de MTTV y cierra el ingreso de turnos.
    category: policy
    applies_to: InterviewSessionRecord.finalized_at
    trigger: Transición a finalized
    logic: SI la sesión pasa a finalized ENTONCES se guarda finalized_at (UTC) y un cambio de estado con actor y hora; desde ese momento un turno nuevo responde 409 session.finalized sin crear filas.
    violation: Un turno nuevo tras finalizar responde 409 session.finalized.
    source: FR3.5, NFR7, AC2.4.2
  - id: BR1.4
    statement: Finalizar no detiene los turnos que siguen en cola o procesando; sus resultados se guardan en la sesión.
    category: policy
    applies_to: Turn
    trigger: Resultado de un turno que llega después de finalizar
    logic: SI llega el resultado de un turno que estaba queued o processing al finalizar ENTONCES se guarda como cualquier otro resultado; la sesión sigue finalized.
    violation: Perder un resultado es un defecto; la prueba de nivel 1 lo detecta.
    source: AC2.4.3
  - id: BR1.5
    statement: El diálogo de finalizar avisa la consecuencia e indica cuántos turnos siguen en proceso.
    category: validation
    applies_to: Consola — diálogo «Finalizar sesión»
    trigger: Pulsar «Finalizar sesión»
    logic: SI se pulsa ENTONCES el diálogo dice «Después de finalizar no podrás agregar turnos», muestra el número de turnos queued o processing y ofrece «Finalizar» y «Cancelar»; «Cancelar» no envía nada.
    violation: La prueba Vitest falla.
    source: AC2.4.1
  - id: BR1.6
    statement: Una sesión finalizada muestra cuántas sugerencias quedan pendientes y un acceso a la primera.
    category: validation
    applies_to: Consola — vista de sesión finalizada
    trigger: Ver una sesión finalized
    logic: SI la sesión está finalized ENTONCES se muestra «Quedan N sugerencias pendientes» con enlace a la primera, o «No quedan sugerencias pendientes» si N = 0.
    violation: La prueba Vitest falla.
    source: AC2.4.4

  # BR2 — Precondiciones de la consolidación (guardia AUTONOMIA-03)
  - id: BR2.1
    statement: Solo el dueño de la sesión consolida.
    category: authorization
    applies_to: POST /sessions/{session_id}/reports
    trigger: Petición de consolidar
    logic: SI el actor es otro analista, admin o una identidad de servicio ENTONCES 403 auth.forbidden y no se crea reporte.
    violation: 403 Problem Details; 0 filas y 0 archivos.
    source: FR7.1, AC6.1.7
  - id: BR2.2
    statement: No se consolida una sesión que no está finalizada.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI la sesión está open o suspended ENTONCES 409 report.session_not_finalized y no se crea reporte.
    violation: 409 report.session_not_finalized.
    source: FR7.1, AC6.1.1
  - id: BR2.3
    statement: No se consolida mientras haya turnos en cola o procesando.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI algún turno está queued o processing ENTONCES 409 report.turns_in_progress y no se crea reporte.
    violation: 409 report.turns_in_progress.
    source: AC6.1.1
  - id: BR2.4
    statement: No se consolida mientras la ronda abierta tenga alguna sugerencia pendiente.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI pending_count de la ronda abierta es mayor que 0 ENTONCES 409 report.pending_suggestions y no se crea reporte.
    violation: 409 report.pending_suggestions.
    source: FR7.1, AC6.1.1, AUTONOMIA-03
  - id: BR2.5
    statement: Los bloqueos se evalúan siempre en el mismo orden y la consola los muestra todos con su motivo.
    category: policy
    applies_to: SessionView.consolidation_blockers, botón «Finalizar y Consolidar»
    trigger: Consultar la sesión o intentar consolidar
    logic: SI hay bloqueos ENTONCES la API responde con el primero en el orden session_not_finalized, turns_in_progress, pending_suggestions, y la vista lista todos; el botón queda deshabilitado con «Finaliza la sesión para consolidar», «Hay turnos en proceso» o «Quedan N sugerencias pendientes» con enlace a la primera.
    violation: La prueba de nivel 1 y la de Vitest fallan.
    source: AC6.1.1
  - id: BR2.6
    statement: Los turnos en error no bloquean la consolidación y se rotulan en el reporte.
    category: policy
    applies_to: Turn con estado error
    trigger: Consolidar con turnos en error
    logic: SI un turno está en error ENTONCES no bloquea, y el reporte lo muestra como «turno no evaluado» con su code.
    violation: La prueba de nivel 1 falla.
    source: AC6.1.3, components (ForensicReport)
  - id: BR2.7
    statement: Sin una ronda abierta no hay nada que consolidar.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar una sesión ya consolidada sin copia de corrección abierta
    logic: SI la sesión está consolidated y no hay ronda de corrección abierta ENTONCES 409 report.conflict y no se crea reporte.
    violation: 409 report.conflict.
    source: FR7.5, AC6.1.6

  # BR3 — Contenido, formato y escaneo del reporte
  - id: BR3.1
    statement: El reporte contiene la sesión completa y cada decisión humana, separando lo que dijo la IA de lo que escribió el analista.
    category: policy
    applies_to: ReportContent
    trigger: Generar el reporte
    logic: SI se consolida ENTONCES el Markdown incluye la transcripción por turnos; cada sugerencia de revisión con fragmento, cita, ID de documento, CoT, estado final y notas; si fue editada, «Sugerencia de la IA» con la CoT intacta y «Reformulación del analista» con quién y cuándo (P3 = A); los Hechos No Documentados con su paquete; los turnos en error como «turno no evaluado» con su code; la versión del escenario y su SHA-256; el umbral de la sesión; el número de versión y la versión que reemplaza; y quién consolidó y cuándo.
    violation: La prueba de nivel 1 compara el reporte con un archivo esperado y falla.
    source: FR7.2, AC6.1.3
  - id: BR3.2
    statement: El reporte se renderiza de forma canónica y determinista.
    category: calculation
    applies_to: ReportFile.content
    trigger: Generar el reporte
    logic: SI se renderiza ENTONCES se usa la plantilla de format_version, UTF-8 en NFC, saltos LF, turnos por número, sugerencias por número de turno y orden de creación, fechas ISO 8601 UTC y un salto final; los mismos datos producen los mismos bytes.
    violation: La prueba de nivel 0 renderiza dos veces los mismos datos y compara bytes.
    source: FR7.3, AC6.1.3
  - id: BR3.3
    statement: El reporte se escanea con el vocabulario prohibido antes de guardarse; una coincidencia impide consolidar.
    category: validation
    applies_to: ReportFile.content
    trigger: Antes de calcular el SHA-256
    logic: SI el escaneo de IntegrityPolicy (palabra completa, sin distinguir mayúsculas ni tildes) encuentra un término fuera de los tramos excluidos (fragmentos, citas, notas y reformulaciones) ENTONCES 409 report.forbidden_vocabulary con la ubicación (ID de turno o de sugerencia y sección), sin el texto, y no se crea versión ni archivo final.
    violation: 409 report.forbidden_vocabulary; la ronda sigue abierta.
    source: AC5.5.1, AC5.5.2, AUTONOMIA-03
  - id: BR3.4
    statement: El SHA-256 se calcula sobre los bytes exactos que se guardan.
    category: calculation
    applies_to: ReportVersion.sha256
    trigger: Antes de escribir el archivo
    logic: SI el contenido pasó el escaneo ENTONCES sha256 = SHA-256 de esos bytes; el mismo valor se registra, se muestra y se envía en la descarga.
    violation: La prueba de nivel 1 recalcula el SHA-256 del archivo y falla si no coincide.
    source: FR7.3, AC6.1.3

  # BR4 — Persistencia y concurrencia (guardia AUTONOMIA-03)
  - id: BR4.1
    statement: Primero se guarda el archivo y después se confirma la versión; nunca existe una versión sin archivo.
    category: constraint
    applies_to: ReportFile, ReportVersion
    trigger: Consolidar
    logic: SI el reporte pasó BR3.3 ENTONCES se genera report_version_id, se escribe el archivo temporal, se fuerza a disco y se renombra a su nombre final; solo después, en una sola transacción, se inserta ReportVersion, se bloquea la ronda (lock_round) y, si es la versión 1, la sesión pasa a consolidated.
    violation: Si la escritura del archivo falla, 500 con code de sistema y 0 filas.
    source: FR7.3, P2 = A, C11 (UnitOfWork)
  - id: BR4.2
    statement: De dos consolidaciones simultáneas solo una gana, y la perdedora no deja rastro.
    category: constraint
    applies_to: Consolidación
    trigger: Dos peticiones sobre la misma ronda
    logic: SI lock_round falla porque la ronda ya está bloqueada, o la unicidad (session_id, version_number) rechaza la fila ENTONCES la transacción se revierte, se borra el archivo de la perdedora y responde 409 report.conflict; la ganadora responde 201.
    violation: 409 report.conflict; queda un solo reporte y un solo SHA-256.
    source: AC6.1.6
  - id: BR4.3
    statement: Si la transacción falla después de escribir el archivo, el archivo se borra; un barrido al arrancar elimina los archivos sin versión.
    category: policy
    applies_to: ReportFile
    trigger: Fallo de la transacción o arranque del pod
    logic: SI la transacción se revierte ENTONCES se borra el archivo; SI al arrancar hay archivos temporales o finales sin fila ReportVersion ENTONCES se borran y se registra un WARN con el nombre del archivo y nada del contenido.
    violation: La prueba de nivel 1 simula el fallo y comprueba que no quedan huérfanos.
    source: P2 = A
  - id: BR4.4
    statement: Las versiones del reporte son de solo inserción y siempre llevan actor y hora.
    category: constraint
    applies_to: ReportVersion
    trigger: Cualquier escritura en ReportVersion
    logic: SI se intenta un INSERT con consolidated_by o consolidated_at nulos, o un UPDATE o DELETE con el usuario de la aplicación ENTONCES la base lo rechaza.
    violation: Error de base de datos; la prueba de nivel 1 lo exige.
    source: AC8.4.1, AC8.4.2, ADR-003
  - id: BR4.5
    statement: Tras consolidar, la sesión y sus alertas quedan bloqueadas.
    category: constraint
    applies_to: ReviewDecision en una ronda bloqueada
    trigger: Cambiar una alerta de una sesión consolidada fuera de una copia de corrección
    logic: SI la ronda está locked ENTONCES el cambio responde 409 (review.round_locked, de HumanReview) sin cambios.
    violation: 409 sin filas nuevas.
    source: FR7.5, AC6.1.5

  # BR5 — Lectura, descarga e integridad
  - id: BR5.1
    statement: La descarga recalcula el SHA-256 y solo entrega el archivo si coincide con el registrado.
    category: validation
    applies_to: GET /reports/{report_version_id}/download
    trigger: Petición de descarga
    logic: SI el SHA-256 recalculado coincide ENTONCES 200 text/markdown con la cabecera X-Veridicus-SHA256; SI no coincide o el archivo falta ENTONCES 409 report.integrity_mismatch, no se envían bytes y se registra un ERROR con el report_version_id.
    violation: 409 report.integrity_mismatch.
    source: FR7.3, FR7.4, AC6.2.1
  - id: BR5.2
    statement: Sin una versión consolidada no hay descarga.
    category: constraint
    applies_to: Descarga y consola
    trigger: Pedir la descarga de una sesión sin consolidar
    logic: SI la sesión no tiene ninguna ReportVersion ENTONCES la descarga responde 409 report.not_consolidated (code propuesto, ver Cambios entre unidades) y la consola no ofrece «Descargar reporte».
    violation: 409 report.not_consolidated.
    source: AC6.2.2
  - id: BR5.3
    statement: Leen y descargan reportes el dueño y los demás analistas; admin y las identidades de servicio no.
    category: authorization
    applies_to: GET /sessions/{session_id}/reports, GET /reports/{report_version_id}/download
    trigger: Petición de lectura
    logic: SI el actor tiene rol analista ENTONCES puede listar y descargar (solo lectura si no es el dueño); SI es admin o una identidad de servicio ENTONCES 403 auth.forbidden.
    violation: 403 Problem Details.
    source: P4 = A, AC5.4.2

  # BR6 — Corrección con versión nueva (guardia AUTONOMIA-03)
  - id: BR6.1
    statement: Solo el dueño corrige un reporte o descarta su copia.
    category: authorization
    applies_to: POST /sessions/{session_id}/correction-rounds y su descarte
    trigger: «Corregir reporte» o «Descartar copia»
    logic: SI el actor es otro analista, admin o una identidad de servicio ENTONCES 403 auth.forbidden y 0 filas.
    violation: 403 Problem Details.
    source: FR7.5, AC6.3.5
  - id: BR6.2
    statement: «Corregir reporte» abre o retoma la única copia de trabajo, que parte de la versión vigente.
    category: constraint
    applies_to: ReviewRound de tipo correction
    trigger: «Corregir reporte»
    logic: SI la sesión está consolidated y no hay ronda abierta ENTONCES se abre una ronda de corrección basada en la versión vigente; SI ya hay una abierta ENTONCES se devuelve esa misma; SI la sesión no está consolidated ENTONCES 409 report.not_consolidated.
    violation: Nunca hay dos copias abiertas por sesión.
    source: FR7.5, AC6.3.2, C11
  - id: BR6.3
    statement: En la copia de trabajo solo cambian estados y notas.
    category: validation
    applies_to: Copia de trabajo
    trigger: Intentar cambiar la transcripción o la salida de la IA
    logic: SI la petición intenta cambiar la transcripción, el fragmento, la cita, el documento o la CoT ENTONCES 422 validation.invalid_request y 0 filas; los cambios de estado, nota y reformulación siguen las reglas de HumanReview.
    violation: 422 Problem Details.
    source: AC6.3.1
  - id: BR6.4
    statement: «Descartar copia» cierra la copia sin crear versión y conserva sus decisiones como rastro.
    category: policy
    applies_to: ReviewRound de tipo correction
    trigger: «Descartar copia»
    logic: SI hay una copia abierta ENTONCES la ronda pasa a discarded con quién y cuándo (operación discard_correction_round de C11 v1.1.0, P1 = A); sus decisiones se conservan y no cuentan para ninguna versión; la versión vigente no cambia; SI no hay copia abierta ENTONCES 409 report.conflict.
    violation: 409 report.conflict.
    source: AC6.3.2, P1 = A
  - id: BR6.5
    statement: Consolidar una copia de trabajo crea una versión nueva que referencia a la vigente y deja la anterior intacta.
    category: policy
    applies_to: ReportVersion con version_number > 1
    trigger: Consolidar con una ronda de corrección abierta
    logic: SI la copia no tiene sugerencias pendientes ENTONCES se aplican BR3 y BR4 y se crea la versión N+1 con supersedes_version_id = versión vigente, su SHA-256, quién y cuándo; la sesión sigue consolidated; los bytes de la versión anterior no se tocan y recalculan el mismo SHA-256.
    violation: La prueba de nivel 1 recalcula ambos SHA-256 y falla si cambian.
    source: FR7.5, AC6.3.3
  - id: BR6.6
    statement: Cada versión conserva los estados de su propia ronda, y la lista de versiones marca la vigente.
    category: policy
    applies_to: GET /sessions/{session_id}/reports
    trigger: Consultar versiones
    logic: SI se consultan las versiones ENTONCES cada una muestra SHA-256, quién y cuándo, y la de mayor version_number se marca como vigente; los estados de alertas de cada versión son los de la ronda que bloqueó.
    violation: La prueba de nivel 1 y la de Vitest fallan.
    source: AC6.3.4

  # BR7 — Medición y registros
  - id: BR7.1
    statement: MTTV se calcula con las marcas guardadas, desde finalizar hasta la primera consolidación.
    category: calculation
    applies_to: MttvSample
    trigger: Informe de evaluación
    logic: SI la sesión tiene la versión 1 ENTONCES MTTV = consolidated_at de la versión 1 menos finalized_at, en segundos; las correcciones no cuentan.
    violation: El arnés de evaluación lo calcula y lo compara con NFR7 (< 10 minutos).
    source: NFR7
  - id: BR7.2
    statement: Los registros de ForensicReport solo llevan identificadores.
    category: policy
    applies_to: Logs del módulo
    trigger: Cualquier registro
    logic: SI se registra un evento ENTONCES lleva session_id, report_version_id, round_id, code y duración, nunca texto del testimonio, de la CoT, de notas ni del reporte.
    violation: La prueba de nivel 0 captura los logs de un flujo con un nombre sembrado y falla si aparece.
    source: team-practices (Code Style), AUTONOMIA-04

  # BR8 — Consola y accesibilidad
  - id: BR8.1
    statement: El diálogo de consolidar resume las decisiones y avisa del bloqueo.
    category: validation
    applies_to: Consola — diálogo «Finalizar y Consolidar»
    trigger: Pulsar «Finalizar y Consolidar» sin bloqueos
    logic: SI se pulsa ENTONCES el diálogo muestra cuántas sugerencias quedaron aceptadas, editadas y descartadas, cuántos Hechos No Documentados hay y qué turnos están en «Error», avisa «Después de consolidar, la sesión queda bloqueada; una corrección creará una versión nueva» y ofrece «Consolidar» y «Cancelar».
    violation: La prueba Vitest falla.
    source: AC6.1.2
  - id: BR8.2
    statement: Tras consolidar se muestra quién y cuándo, el SHA-256 completo con acción para copiarlo y «Descargar reporte».
    category: validation
    applies_to: Consola — vista de reporte
    trigger: Respuesta 201 de consolidar
    logic: SI la consolidación termina ENTONCES la vista muestra quién y cuándo (hora de Colombia), los 64 caracteres del SHA-256, «Copiar SHA-256» y «Descargar reporte».
    violation: La prueba Vitest falla.
    source: AC6.1.4
  - id: BR8.3
    statement: La copia de trabajo se rotula y ofrece consolidar o descartar.
    category: validation
    applies_to: Consola — copia de trabajo
    trigger: Abrir o retomar una copia
    logic: SI hay una copia abierta ENTONCES se ve «Copia de trabajo de la versión N. Solo puedes cambiar estados y notas», con «Consolidar» y «Descartar copia»; «Descartar copia» pide confirmación en un diálogo modal porque es irreversible.
    violation: La prueba Vitest falla.
    source: AC6.3.1, AC6.3.2, refined-mockups (solo las confirmaciones irreversibles son modales)
  - id: BR8.4
    statement: Las pantallas de U7 cumplen la accesibilidad común.
    category: validation
    applies_to: Diálogos de finalizar y consolidar, vista de reporte, lista de versiones y copia de trabajo
    trigger: Suite axe y recorrido con teclado
    logic: SI axe encuentra violaciones serious o critical, si consolidar, copiar el SHA-256, descargar, corregir o descartar no se puede hacer solo con teclado, o si un estado se identifica solo por color ENTONCES la prueba falla.
    violation: La prueba de nivel 3 o la de Vitest falla.
    source: AC5.6.1, AC5.6.2, AC5.6.3
  - id: BR8.5
    statement: Quien no es el dueño ve la sesión y sus reportes en solo lectura.
    category: authorization
    applies_to: Consola — sesión de otro analista
    trigger: Abrir una sesión ajena
    logic: SI el usuario no es el dueño ENTONCES no ve «Finalizar sesión», «Finalizar y Consolidar», «Corregir reporte» ni «Descartar copia», y sí la lista de versiones y «Descargar reporte».
    violation: La prueba Vitest falla.
    source: AC5.4.2, P4 = A
```

## Resumen de reglas

| Grupo | Reglas | Qué protegen |
|---|---|---|
| BR1 Finalizar | BR1.1–BR1.6 | Solo el dueño finaliza, una vez, desde `open` o `suspended`; se fija el inicio de MTTV; los turnos en curso terminan |
| BR2 Precondiciones | BR2.1–BR2.7 | Dueño, sesión finalizada, 0 turnos en curso, 0 pendientes y una ronda abierta (AUTONOMIA-03) |
| BR3 Contenido | BR3.1–BR3.4 | Contenido completo, IA y analista separados, render determinista, escaneo de vocabulario y SHA-256 sobre los bytes guardados |
| BR4 Persistencia | BR4.1–BR4.5 | Archivo antes que fila, una sola consolidación gana, sin huérfanos, solo inserción y bloqueo de la sesión |
| BR5 Descarga | BR5.1–BR5.3 | Integridad verificada en cada descarga, sin descarga antes de consolidar, lectura solo para analistas |
| BR6 Corrección | BR6.1–BR6.6 | Solo el dueño, una copia por sesión, solo estados y notas, descarte sin versión, versión nueva que conserva la anterior |
| BR7 Medición | BR7.1–BR7.2 | MTTV con marcas guardadas; registros solo con identificadores |
| BR8 Consola | BR8.1–BR8.5 | Diálogos, vista del reporte, copia de trabajo, accesibilidad y solo lectura |
