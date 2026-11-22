# Reglas de negocio — U7 forensic-report (componente ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02** (y las revisiones 3 de
Inception). Sustituye a la revisión 1 del 2026-10-03.
- Las reglas conservan su ID. Ninguna sale entera; las que siguen y cambian llevan `status: cambia`, las
  que no cambian `status: sigue` y las nuevas `status: nuevo` (regla de `project.md`: sin renumerar).
- **Cambian:** las de finalizar (estados nuevos de la sesión), las precondiciones (modo final, corridas en
  lugar de turnos, sesiones sin modo final posible), el contenido del reporte (FR7.2, sin marco de verdad),
  el escaneo (transcripción como fuente literal y aviso excluido), la lectura y descarga (P5 = A: `/download`
  pasa a ser la lectura de la vista previa y la descarga es la exportación), los roles (tabla de FR1 y
  VE-13: el `admin` lee y exporta; sustituye a P4 = A) y la consola.
- **Entran:** BR2.8–BR2.11 (modo final, sesiones exentas, importadas y hallazgo durante el diálogo), BR5.4
  (integridad de lo descargado), BR8.6–BR8.7 (botón deshabilitado y `admin` en M5), **BR9** (exportación),
  **BR10** (retención) y **BR11** (aviso de VE-01, «páginas», avisos de la sesión y vocabulario de VE-02).

**Alcance.** BR2, BR4, BR6 y BR9 forman el módulo guardia de consolidación y exportación de AUTONOMIA-03,
con 100 % de ramas (team.md). La autorización por rol y dueño la aplica ConsoleApi con el mecanismo de
U3 antes de delegar (ADR-009). Cada regla repite la verificación que exige para que la prueba la cite.
Insumos: `unit-of-work.md`, `unit-of-work-story-map.md`, requirements (FR1, FR3.5, FR7.1–FR7.5, NFR7 y
la adenda 02), components (ReviewReport) y contract-summary (C1, C11, C23, C24).

## Reglas (fuente de verdad)

```yaml
rules:
  # BR1 — Finalizar la sesión (US2.4)
  - id: BR1.1
    status: sigue
    statement: Solo el dueño de la sesión puede finalizarla.
    category: authorization
    applies_to: POST /sessions/{session_id}/finalize
    trigger: Petición de finalizar
    logic: SI el actor no es el dueño, es admin, investigador o una identidad de servicio ENTONCES 403 auth.forbidden y 0 filas.
    violation: 403 Problem Details; no cambia el estado.
    source: FR3.5, ADR-009, AC2.4.2
  - id: BR1.2
    status: cambia
    statement: Una sesión se finaliza desde open, paused, suspended o blocked, una sola vez.
    category: constraint
    applies_to: InterviewSessionRecord.status
    trigger: Petición de finalizar del dueño
    logic: SI la sesión está open, paused, suspended o blocked ENTONCES pasa a finalized (blocked conserva su blocked_code); SI está finalized o consolidated ENTONCES 409 session.finalized; SI está terminated ENTONCES 409 session.terminated; en ambos casos 0 filas.
    violation: 409 session.finalized o session.terminated.
    source: FR3.5; máquina de la sesión del Functional Design de U6 (finalizar es la ruta de U7, también desde pausada, suspendida y bloqueada)
  - id: BR1.3
    status: sigue
    statement: Finalizar guarda en UTC la hora de inicio de MTTV y cierra el ingreso de turnos.
    category: policy
    applies_to: InterviewSessionRecord.finalized_at
    trigger: Transición a finalized
    logic: SI la sesión pasa a finalized ENTONCES se guarda finalized_at (UTC) y un cambio de estado con actor y hora; desde ese momento un turno nuevo responde 409 session.finalized sin crear filas.
    violation: Un turno nuevo tras finalizar responde 409 session.finalized.
    source: FR3.5, NFR7, AC2.4.2
  - id: BR1.4
    status: cambia
    statement: Finalizar no detiene las corridas que siguen en cola o procesando; sus hallazgos se guardan en la sesión.
    category: policy
    applies_to: AnalysisRun
    trigger: Resultado de una corrida que llega después de finalizar
    logic: SI llega el resultado de una corrida que estaba queued o processing al finalizar ENTONCES se guarda como cualquier otro resultado; la sesión sigue finalized. Una corrida colgada la vence el supervisor de corridas de InterviewSession al pasar su plazo.
    violation: Perder un resultado es un defecto; la prueba de nivel 1 lo detecta.
    source: AC2.4.3; plazos de corrida del catálogo C25
  - id: BR1.5
    status: cambia
    statement: El diálogo de finalizar avisa la consecuencia e indica cuántas corridas siguen en proceso.
    category: validation
    applies_to: Consola — diálogo «Finalizar sesión» (solo sesiones guiadas)
    trigger: Pulsar «Finalizar sesión»
    logic: SI se pulsa ENTONCES el diálogo dice «Después de finalizar no podrás agregar turnos», muestra cuántas corridas siguen queued o processing y ofrece «Finalizar» y «Cancelar»; «Cancelar» no envía nada.
    violation: La prueba Vitest falla.
    source: AC2.4.1; mockups §6.7
  - id: BR1.6
    status: cambia
    statement: Una sesión finalizada ofrece lanzar el modo final y muestra cuántas sugerencias quedan pendientes con un acceso a la primera.
    category: validation
    applies_to: Consola — vista de sesión finalizada
    trigger: Ver una sesión finalized
    logic: SI la sesión está finalized ENTONCES se muestran «Lanzar modo final» (acción de U6), «Quedan N sugerencias pendientes» con enlace a la primera, o «No quedan sugerencias pendientes» si N = 0.
    violation: La prueba Vitest falla.
    source: AC2.4.4

  # BR2 — Precondiciones de la consolidación (guardia AUTONOMIA-03)
  - id: BR2.1
    status: sigue
    statement: Solo el dueño de la sesión consolida.
    category: authorization
    applies_to: POST /sessions/{session_id}/reports
    trigger: Petición de consolidar
    logic: SI el actor es otro analista, admin, investigador o una identidad de servicio ENTONCES 403 auth.forbidden y no se crea reporte.
    violation: 403 Problem Details; 0 filas y 0 archivos.
    source: FR7.1, AC6.1.7, AC5.4.3
  - id: BR2.2
    status: cambia
    statement: No se consolida una sesión guiada que no está finalizada ni terminada.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI la sesión es guiada y está open, paused, suspended o blocked ENTONCES report.session_not_finalized y no se crea reporte. Una sesión finalized o terminated cumple. Las importadas siguen BR2.10.
    violation: 409 report.session_not_finalized.
    source: FR7.1, AC6.1.1; components (ReviewReport consolida una sesión finalizada o terminada)
  - id: BR2.3
    status: cambia
    statement: No se consolida mientras haya corridas en cola o procesando.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI alguna corrida incremental o final de la sesión está queued o processing ENTONCES report.runs_in_progress y no se crea reporte.
    violation: 409 report.runs_in_progress.
    source: FR7.1, AC6.1.1; C1 (code report.runs_in_progress)
  - id: BR2.4
    status: sigue
    statement: No se consolida mientras la ronda abierta tenga alguna sugerencia pendiente.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI pending_count de la ronda abierta, leído con la ronda bloqueada (open_round con for_update), es mayor que 0 ENTONCES report.pending_suggestions y no se crea reporte.
    violation: 409 report.pending_suggestions.
    source: FR7.1, AC6.1.1, AUTONOMIA-03
  - id: BR2.5
    status: cambia
    statement: Los bloqueos se evalúan siempre en el mismo orden y la consola los muestra todos con su motivo.
    category: policy
    applies_to: SessionView.consolidation_blockers y can_consolidate, botón «Consolidar reporte»
    trigger: Consultar la sesión o intentar consolidar
    logic: SI hay bloqueos ENTONCES la API responde 409 con el primero en el orden session_not_finalized, final_mode_not_launched, runs_in_progress, pending_suggestions, y SessionView los lista todos; el botón queda aria-disabled y enfocable con «Finaliza la sesión para consolidar», «Lanza el modo final para consolidar», «Hay análisis en proceso» y «Quedan N sugerencias pendientes» con enlace a la primera, en ese orden.
    violation: La prueba de nivel 1 (una por motivo) y la de Vitest fallan.
    source: AC6.1.1, AC5.6.4; mockups §6.9
  - id: BR2.6
    status: cambia
    statement: Las corridas en error no bloquean la consolidación y se declaran en el reporte.
    category: policy
    applies_to: AnalysisRun con estado error
    trigger: Consolidar con corridas en error
    logic: SI un tramo incremental terminó en error ENTONCES no bloquea y el reporte lo muestra como «Tramo no evaluado» con su code; SI el último modo final lanzado terminó en error ENTONCES no bloquea y el reporte dice «Modo final no completado. Revisión manual requerida» con su code; los intentos anteriores en error quedan solo en el registro de corridas.
    violation: La prueba de nivel 1 falla.
    source: FR7.1, FR7.2, AC6.1.2, AC6.1.3
  - id: BR2.7
    status: sigue
    statement: Sin una ronda abierta en una sesión consolidada no hay nada que consolidar.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar una sesión ya consolidada sin copia de corrección abierta
    logic: SI la sesión está consolidated y no hay ronda de corrección abierta ENTONCES 409 report.conflict y no se crea reporte. Una sesión sin consolidar y sin ninguna ronda obtiene la ronda 1 de open_round con for_update (0 sugerencias).
    violation: 409 report.conflict.
    source: FR7.5, AC6.1.6, AC6.1.8
  - id: BR2.8
    status: nuevo
    statement: No se consolida una sesión cuyo modo final no se lanzó nunca, salvo las de BR2.9.
    category: constraint
    applies_to: Consolidación
    trigger: Petición de consolidar
    logic: SI la sesión no tiene ninguna corrida final y no está en un caso de BR2.9 ENTONCES 409 report.final_mode_not_launched y no se crea reporte. Un modo final en curso cae en BR2.3; uno terminado en ok o en error cumple.
    violation: 409 report.final_mode_not_launched (code nuevo, FD-U7-04).
    source: FR7.1, AC6.1.1
  - id: BR2.9
    status: nuevo
    statement: Una sesión que ya no puede lanzar el modo final se consolida sin exigirlo.
    category: policy
    applies_to: Consolidación
    trigger: Consolidar una sesión bloqueada por incidente, terminada o con la retirada del consentimiento sin modo final
    logic: SI blocked_code no es nulo, o la sesión está terminated, o tiene la retirada del consentimiento registrada ENTONCES BR2.8 no aplica; el resto de la guardia sí, y el reporte declara el incidente, la terminación o la retirada con su hora y los tramos sin evaluar (BR11.3).
    violation: La prueba de nivel 1 (una por caso) falla.
    source: Precisiones de los Functional Design de U4 (sesión bloqueada) y U6 (terminada o con retirada); AC6.1.1; VE-10, VE-14
  - id: BR2.10
    status: nuevo
    statement: Una sesión importada se finaliza dentro de la misma consolidación.
    category: policy
    applies_to: Consolidación de una sesión de origen corpus o sintético
    trigger: Consolidar una sesión importada no finalizada
    logic: SI la sesión es importada y está open, paused, suspended o blocked ENTONCES BR2.2 no aplica; la transacción de consolidar registra la transición a finalized y después a consolidated, con dos filas del historial de la sesión, actor el dueño y la misma hora; la guardia no muestra «Finaliza la sesión para consolidar». La sesión queda fuera de MTTV (BR7.1).
    violation: La prueba de nivel 1 comprueba las dos filas y el orden; la de Vitest, que el motivo no aparece.
    source: P7 = A; mockups §6.2 (importada sin «Finalizar sesión»); AC6.1.1
  - id: BR2.11
    status: nuevo
    statement: Un hallazgo que llega con el diálogo de consolidar abierto impide la consolidación.
    category: constraint
    applies_to: Consolidación
    trigger: Confirmar «Consolidar» después de que llegó una sugerencia nueva
    logic: SI al confirmar la ronda abierta tiene pendientes que no había al abrir el diálogo ENTONCES 409 report.pending_suggestions y el diálogo muestra «Quedan N sugerencias pendientes» con enlace a la primera.
    violation: La prueba de nivel 1 inserta una sugerencia entre la vista y la confirmación y exige 409 con 0 filas.
    source: AC6.1.9

  # BR3 — Contenido, formato y escaneo del reporte
  - id: BR3.1
    status: cambia
    statement: El reporte contiene la sesión completa y cada decisión humana, separando lo que dijo la IA de lo que escribió el analista.
    category: policy
    applies_to: ReportContent
    trigger: Generar el reporte
    logic: SI se consolida ENTONCES el Markdown incluye la transcripción por turnos con hablante y página; todas las sugerencias con estado final y nota y, por cada una, hecho, tipo, las dos citas con turno y página, sus avisos y las observaciones; si fue editada, el bloque «Sugerencia de la IA» intacto y «Reformulación del analista» con quién y cuándo (P3 = A); por cada corrida, perfil, config_sha256, prompt_sha256, versión del analizador, registro de modelos y modo fragmentado con su ventana; los avisos de BR2.6 y BR11.3; el número de versión y la versión que reemplaza; quién consolidó y cuándo; y «Sin sugerencias de revisión» si no hay. No incluye escenario, umbral, calificaciones frente a un marco de verdad ni aclaraciones neutras.
    violation: La prueba de nivel 1 compara el reporte con un archivo dorado de una sesión fixture con reloj fijo y falla.
    source: FR7.2, AC6.1.3, AC6.1.8, AC3.7.1; cambio 01 (sin marco de verdad)
  - id: BR3.2
    status: cambia
    statement: El reporte se renderiza de forma canónica y determinista.
    category: calculation
    applies_to: ReportFile.content
    trigger: Generar el reporte
    logic: SI se renderiza ENTONCES se usa la plantilla de format_version 2 con las secciones H2 fijas de BR11.2, UTF-8 en NFC, saltos LF, turnos por número, sugerencias por número de turno y orden de creación, fechas ISO 8601 UTC con la hora de Colombia entre paréntesis donde se muestra a personas y un salto final; los mismos datos producen los mismos bytes.
    violation: La prueba de nivel 0 renderiza dos veces los mismos datos y compara bytes.
    source: FR7.3, AC6.1.3
  - id: BR3.3
    status: cambia
    statement: El reporte se escanea con el vocabulario prohibido antes de guardarse; una coincidencia impide consolidar.
    category: validation
    applies_to: ReportFile.content
    trigger: Antes de calcular el SHA-256
    logic: SI scan(text, literal_sources) de IntegrityPolicy, con literal_sources = los textos de todos los turnos de la sesión, encuentra un término de la lista versionada fuera de los tramos excluidos (turnos y citas, notas, reformulaciones y la cadena versionada del aviso) ENTONCES 409 report.forbidden_vocabulary con la ubicación (sección e ID de turno o de sugerencia), sin el texto, y no se crea versión ni archivo final.
    violation: 409 report.forbidden_vocabulary; la ronda sigue abierta. Controles de nivel 0 — «miente» en un texto del sistema del reporte lo hace fallar; «falso» o «prueba» dentro de un turno o de una cita no; «miente» en una reformulación no.
    source: AC5.5.1, AC5.5.2, AUTONOMIA-03; A-1
  - id: BR3.4
    status: sigue
    statement: El SHA-256 se calcula sobre los bytes exactos que se guardan.
    category: calculation
    applies_to: ReportVersion.sha256
    trigger: Antes de escribir el archivo
    logic: SI el contenido pasó el escaneo ENTONCES sha256 = SHA-256 de esos bytes; el mismo valor se registra, se muestra y va en la cabecera de cada exportación.
    violation: La prueba de nivel 1 recalcula el SHA-256 del archivo y falla si no coincide.
    source: FR7.3, AC6.1.3

  # BR4 — Persistencia y concurrencia (guardia AUTONOMIA-03)
  - id: BR4.1
    status: cambia
    statement: Primero se guarda el archivo y después se confirma la versión; nunca existe una versión sin archivo.
    category: constraint
    applies_to: ReportFile, ReportVersion
    trigger: Consolidar
    logic: SI el reporte pasó BR3.3 ENTONCES se genera report_version_id, se escribe el archivo temporal, se fuerza a disco y se enlaza a su nombre final; solo después, en la misma transacción, se inserta ReportVersion, se bloquea la ronda (lock_round) y, si es la versión 1, la sesión pasa a consolidated (desde finalized o terminated, o con la finalización de BR2.10).
    violation: Si la escritura del archivo falla, 500 con code de sistema y 0 filas.
    source: FR7.3, P2 = A, C11 (UnitOfWork)
  - id: BR4.2
    status: cambia
    statement: De dos consolidaciones simultáneas solo una gana, y la perdedora no deja rastro.
    category: constraint
    applies_to: Consolidación
    trigger: Dos peticiones sobre la misma ronda
    logic: SI la segunda petición espera el bloqueo de la sesión y luego de la ronda (orden sesión → ronda, open_round con for_update) y encuentra la ronda bloqueada, o lock_round falla, o la unicidad (session_id, version_number) rechaza la fila ENTONCES la transacción se revierte, se borra el archivo de la perdedora y responde 409 report.conflict; la ganadora responde 201.
    violation: 409 report.conflict; queda un solo reporte y un solo SHA-256.
    source: AC6.1.6; NFR Design de U7 (bloqueos y orden)
  - id: BR4.3
    status: sigue
    statement: Si la transacción falla después de escribir el archivo, el archivo se borra; un barrido con margen elimina los que queden sin versión.
    category: policy
    applies_to: ReportFile
    trigger: Fallo de la transacción o arranque del pod
    logic: SI la transacción se revierte ENTONCES se borra el archivo en el acto; SI al arrancar hay archivos temporales o finales sin fila ReportVersion más viejos que el margen ENTONCES se borran y se registra un WARN con el nombre del archivo y nada del contenido.
    violation: La prueba de nivel 1 simula el fallo y comprueba que no quedan huérfanos.
    source: P2 = A; NFR Design de U7 (margen del barrido, 1 réplica)
  - id: BR4.4
    status: sigue
    statement: Las versiones y exportaciones del reporte son de solo inserción y siempre llevan actor y hora.
    category: constraint
    applies_to: ReportVersion, ReportExport
    trigger: Cualquier escritura
    logic: SI se intenta un INSERT con actor u hora nulos, o un UPDATE o DELETE con el usuario de la aplicación ENTONCES la base lo rechaza; solo el usuario de base de la retención borra (BR10.1).
    violation: Error de base de datos; la prueba de nivel 1 lo exige para las dos tablas.
    source: AC8.4.1, AC8.4.2, ADR-003, A-2
  - id: BR4.5
    status: sigue
    statement: Tras consolidar, la sesión y sus hallazgos quedan bloqueados.
    category: constraint
    applies_to: ReviewDecision en una ronda bloqueada
    trigger: Cambiar un hallazgo de una sesión consolidada fuera de una copia de corrección
    logic: SI la ronda está locked ENTONCES el cambio responde 409 (review.round_locked, de HumanReview) sin cambios.
    violation: 409 sin filas nuevas.
    source: FR7.5, AC6.1.5

  # BR5 — Lectura y descarga
  - id: BR5.1
    status: cambia
    statement: La lectura de una versión para la vista previa recalcula el SHA-256 y solo la entrega si coincide.
    category: validation
    applies_to: GET /reports/{report_version_id}/download (lectura de la vista previa de M5)
    trigger: Abrir M5 o cambiar de versión en la lista
    logic: SI el SHA-256 recalculado coincide ENTONCES 200 text/markdown con X-Veridicus-SHA256 y Content-Disposition inline, y la consola lo muestra en la página sin ofrecer guardar el archivo; el acceso se registra como report_version por la marca de la ruta; SI no coincide o el archivo falta ENTONCES 409 report.integrity_mismatch, no se envían bytes y se registra un ERROR con el report_version_id.
    violation: 409 report.integrity_mismatch.
    source: P5 = A; FR7.3; AC5.4.2
  - id: BR5.2
    status: sigue
    statement: Sin una versión consolidada no hay lectura, exportación ni corrección.
    category: constraint
    applies_to: Lectura, exportación, corrección y consola
    trigger: Pedirlas sobre una sesión sin consolidar
    logic: SI la sesión no tiene ninguna ReportVersion ENTONCES responde 409 report.not_consolidated y la consola no ofrece «Descargar reporte».
    violation: 409 report.not_consolidated.
    source: AC6.2.2; C1
  - id: BR5.3
    status: cambia
    statement: Leen las versiones y su vista previa todos los analistas y el admin; el investigador y las identidades de servicio no.
    category: authorization
    applies_to: GET /sessions/{session_id}/reports, GET /reports/{report_version_id}/download
    trigger: Petición de lectura
    logic: SI el actor tiene rol analista (sea o no el dueño) o admin ENTONCES puede listar y leer en solo lectura si no es el dueño; SI es investigador o una identidad de servicio ENTONCES 403 auth.forbidden.
    violation: 403 Problem Details.
    source: FR1 (tabla de roles, «Leer sesiones y reportes»); AC5.4.2; sustituye a P4 = A de la primera pasada
  - id: BR5.4
    status: nuevo
    statement: Lo que el analista descarga es una exportación y su SHA-256 se comprueba contra el registrado para esa exportación.
    category: validation
    applies_to: «Descargar reporte» en M5
    trigger: Descargar
    logic: SI se pulsa «Descargar reporte» ENTONCES la consola llama a la exportación (BR9) y muestra junto a la descarga el export_sha256 de X-Veridicus-Export-SHA256; la cabecera del archivo lleva el SHA-256 de la versión consolidada; sha256sum del archivo descargado coincide con el export_sha256 registrado.
    violation: La prueba de nivel 1 recalcula el SHA-256 de los bytes recibidos y lo compara con ReportExport; la de nivel 3 lo comprueba en el navegador.
    source: P5 = A; FR7.3 (coincide con el registrado para esa exportación); AC6.2.1, AC15.8.2

  # BR6 — Corrección con versión nueva (guardia AUTONOMIA-03)
  - id: BR6.1
    status: sigue
    statement: Solo el dueño corrige un reporte o descarta su copia.
    category: authorization
    applies_to: POST /sessions/{session_id}/correction-rounds y su descarte
    trigger: «Corregir reporte» o «Descartar copia»
    logic: SI el actor es otro analista, admin, investigador o una identidad de servicio ENTONCES 403 auth.forbidden y 0 filas.
    violation: 403 Problem Details.
    source: FR7.5, AC6.3.5, AC5.4.3
  - id: BR6.2
    status: sigue
    statement: «Corregir reporte» abre o retoma la única copia de trabajo, que parte de la versión vigente.
    category: constraint
    applies_to: ReviewRound de tipo correction
    trigger: «Corregir reporte»
    logic: SI la sesión está consolidated y no hay ronda abierta ENTONCES se abre una ronda de corrección basada en la ronda bloqueada por la versión vigente; SI ya hay una abierta ENTONCES se devuelve esa misma; SI la sesión no está consolidated ENTONCES 409 report.not_consolidated.
    violation: Nunca hay dos copias abiertas por sesión.
    source: FR7.5, AC6.3.2, C11
  - id: BR6.3
    status: cambia
    statement: En la copia de trabajo solo cambian estados y notas.
    category: validation
    applies_to: Copia de trabajo
    trigger: Intentar cambiar la transcripción o la salida de la IA
    logic: SI la petición intenta cambiar la transcripción, el hecho, el tipo, las citas, los avisos o las observaciones ENTONCES 422 validation.invalid_request y 0 filas; los cambios de estado, nota y reformulación siguen las reglas de HumanReview.
    violation: 422 Problem Details.
    source: AC6.3.1
  - id: BR6.4
    status: cambia
    statement: «Descartar copia» cierra la copia sin crear versión y conserva sus decisiones como rastro.
    category: policy
    applies_to: ReviewRound de tipo correction
    trigger: «Descartar copia»
    logic: SI hay una copia abierta ENTONCES la ronda pasa a discarded con quién y cuándo (operación discard_correction_round, precisión de C11 que recoge el Functional Design de U5, P1 = A); sus decisiones se conservan y no cuentan para ninguna versión; la versión vigente no cambia; SI no hay copia abierta ENTONCES 409 report.conflict.
    violation: 409 report.conflict.
    source: AC6.3.2, P1 = A
  - id: BR6.5
    status: sigue
    statement: Consolidar una copia de trabajo crea una versión nueva que referencia a la vigente y deja la anterior intacta.
    category: policy
    applies_to: ReportVersion con version_number > 1
    trigger: Consolidar con una ronda de corrección abierta
    logic: SI la copia no tiene sugerencias pendientes ENTONCES se aplican BR3 y BR4 y se crea la versión N+1 con supersedes_version_id = versión vigente, su SHA-256, quién y cuándo; la sesión sigue consolidated; los bytes de la versión anterior no se tocan y recalculan el mismo SHA-256.
    violation: La prueba de nivel 1 recalcula ambos SHA-256 y falla si cambian.
    source: FR7.5, AC6.3.3
  - id: BR6.6
    status: sigue
    statement: Cada versión conserva los estados de su propia ronda, y la lista de versiones marca la vigente.
    category: policy
    applies_to: GET /sessions/{session_id}/reports
    trigger: Consultar versiones
    logic: SI se consultan las versiones ENTONCES cada una muestra SHA-256, quién y cuándo, y la de mayor version_number lleva el texto «vigente»; los estados de los hallazgos de cada versión son los de la ronda que bloqueó.
    violation: La prueba de nivel 1 y la de Vitest fallan.
    source: AC6.3.4

  # BR7 — Medición y registros
  - id: BR7.1
    status: cambia
    statement: MTTV se calcula con las marcas guardadas, desde finalizar hasta la primera consolidación, solo en sesiones guiadas.
    category: calculation
    applies_to: MttvSample
    trigger: Informe de evaluación
    logic: SI la sesión es guiada y tiene la versión 1 ENTONCES MTTV = consolidated_at de la versión 1 menos finalized_at, en segundos; las correcciones no cuentan; las importadas no producen muestra (BR2.10).
    violation: El arnés de evaluación lo calcula y lo compara con NFR7.
    source: NFR7, P7 = A
  - id: BR7.2
    status: sigue
    statement: Los registros de ReviewReport y de la ruta de exportación solo llevan identificadores.
    category: policy
    applies_to: Logs del módulo y de la exportación
    trigger: Cualquier registro
    logic: SI se registra un evento ENTONCES lleva session_id, report_version_id, export_id, round_id, user_id, code y duración, nunca texto del testimonio, de las observaciones, de notas, del reporte ni el nombre de usuario de la marca.
    violation: La prueba de nivel 0 captura los logs de un flujo con un nombre sembrado y falla si aparece.
    source: team.md (Code Style), AUTONOMIA-04

  # BR8 — Consola y accesibilidad
  - id: BR8.1
    status: cambia
    statement: El diálogo de consolidar resume las decisiones, declara lo no evaluado y avisa del bloqueo.
    category: validation
    applies_to: Consola — diálogo «Consolidar el reporte»
    trigger: Pulsar «Consolidar reporte» sin bloqueos
    logic: SI se pulsa ENTONCES el diálogo abre con el foco en «Cancelar», resume cuántas sugerencias quedaron aceptadas, editadas y descartadas, lista los tramos no evaluados; SI el último modo final terminó en error lo dice con su code, ofrece «Volver y relanzar el modo final» y explica «El reporte no incluirá contradicciones entre pasajes distantes»; SI se usó el modo fragmentado repite la limitación; y avisa «Después de consolidar, la sesión queda bloqueada; una corrección creará una versión nueva», con «Consolidar» y «Cancelar».
    violation: La prueba Vitest falla.
    source: AC6.1.2; mockups §6.9
  - id: BR8.2
    status: cambia
    statement: Tras consolidar se abre M5 con quién y cuándo, el SHA-256 completo con acción para copiarlo y «Descargar reporte».
    category: validation
    applies_to: Consola — M5
    trigger: Respuesta 201 de consolidar
    logic: SI la consolidación termina ENTONCES se abre M5 con «Consolidado por <usuario> el <fecha Colombia> (<UTC>)», los 64 caracteres del SHA-256, «Copiar SHA-256» y «Descargar reporte», que exporta (BR5.4).
    violation: La prueba Vitest falla.
    source: AC6.1.4; mockups §7
  - id: BR8.3
    status: sigue
    statement: La copia de trabajo se rotula y ofrece consolidar o descartar.
    category: validation
    applies_to: Consola — copia de trabajo
    trigger: Abrir o retomar una copia
    logic: SI hay una copia abierta ENTONCES se ve «Copia de trabajo de la versión N. Solo puedes cambiar estados y notas», con «Consolidar reporte» y «Descartar copia»; «Descartar copia» pide confirmación en un diálogo modal porque es irreversible.
    violation: La prueba Vitest falla.
    source: AC6.3.1, AC6.3.2; refined-mockups (solo las confirmaciones irreversibles son modales)
  - id: BR8.4
    status: cambia
    statement: Las pantallas de U7 cumplen la accesibilidad común.
    category: validation
    applies_to: Diálogos de finalizar, consolidar y descartar, M5, lista de versiones, vista previa y copia de trabajo
    trigger: Suite axe y recorrido con teclado
    logic: SI axe encuentra violaciones serious o critical, si consolidar, copiar el SHA-256, descargar, corregir o descartar no se puede hacer solo con teclado, si un estado se identifica solo por color o si un botón deshabilitado no recibe el foco con su motivo por aria-describedby ENTONCES la prueba falla.
    violation: La prueba de nivel 3 o la de Vitest falla.
    source: AC5.6.1, AC5.6.2, AC5.6.3, AC5.6.4
  - id: BR8.5
    status: cambia
    statement: Quien no es el dueño ve la sesión y sus reportes en solo lectura.
    category: authorization
    applies_to: Consola — sesión y M5 de otro analista
    trigger: Abrir una sesión ajena
    logic: SI el usuario no es el dueño ENTONCES ve «Sesión de <usuario>. Solo lectura», la lista de versiones y la vista previa, y no ve «Finalizar sesión», «Consolidar reporte», «Corregir reporte» ni «Descartar copia»; «Descargar reporte» sigue BR8.6.
    violation: La prueba Vitest falla.
    source: AC5.4.2; FR1 (tabla de roles)
  - id: BR8.6
    status: nuevo
    statement: «Descargar reporte» queda deshabilitado con su motivo para quien no puede exportar.
    category: validation
    applies_to: Consola — M5
    trigger: Abrir M5 como analista que no es el dueño
    logic: SI el usuario es analista y no es el dueño ENTONCES «Descargar reporte» está aria-disabled, recibe el foco y anuncia «Solo el dueño de la sesión o un administrador pueden exportar el reporte» por aria-describedby; la API mantiene el 403 de BR9.1.
    violation: La prueba Vitest falla.
    source: AC15.8.1, AC5.6.4; mockups §11 (US15.8 deja la forma a esta etapa)
  - id: BR8.7
    status: nuevo
    statement: El admin abre M5 en solo lectura y puede exportar.
    category: authorization
    applies_to: Consola — M5 para el rol admin
    trigger: Abrir M5 como admin
    logic: SI el usuario es admin ENTONCES ve el banner de solo lectura, la lista de versiones, la vista previa y «Descargar reporte» habilitado; no ve «Corregir reporte», «Descartar copia» ni «Consolidar reporte».
    violation: La prueba Vitest falla.
    source: FR1 (tabla de roles), VE-13, AC15.8.1

  # BR9 — Exportación con marca de agua (guardia AUTONOMIA-03, US15.8)
  - id: BR9.1
    status: nuevo
    statement: Solo exportan el analista dueño de la sesión y el admin.
    category: authorization
    applies_to: POST /reports/{report_version_id}/exports
    trigger: Petición de exportar
    logic: SI el actor es un analista que no es el dueño, un investigador o una identidad de servicio ENTONCES 403 auth.forbidden, sin ReportExport, sin llamada al puerto y sin bytes; SI es el analista dueño o un admin ENTONCES sigue BR9.2.
    violation: 403 Problem Details; prueba de nivel 1 (dueño 201, analista no dueño 403, admin 201, investigador 403).
    source: VE-13, A-3, AC15.8.1; C1 (x-veridicus-owner-only-for-role analista)
  - id: BR9.2
    status: nuevo
    statement: Antes de exportar se comprueba que la versión existe y que su archivo no cambió.
    category: validation
    applies_to: Exportación
    trigger: Después de BR9.1
    logic: SI el report_version_id no existe ENTONCES 404 report.not_found (code nuevo, FD-U7-05); SI el SHA-256 recalculado del archivo no coincide con ReportVersion.sha256 o el archivo falta ENTONCES 409 report.integrity_mismatch, sin ReportExport ni bytes.
    violation: 404 o 409 Problem Details.
    source: FR7.3, A-3
  - id: BR9.3
    status: nuevo
    statement: Cada exportación lleva una marca visible con el usuario y la hora, y en la cabecera el SHA-256 de la versión.
    category: calculation
    applies_to: ExportWatermark, bytes exportados
    trigger: Armar la exportación
    logic: SI se arma ENTONCES los bytes son los del archivo de la versión con, en la cabecera, «Exportado por <usuario> el <fecha Colombia> (<UTC>)», «Versión N · SHA-256 de la versión <64 caracteres>», y la línea de marca «Exportado por <usuario> el <fecha>» repetida en cada punto de página de BR11.2 junto al aviso; las mismas entradas (versión, usuario, hora) producen los mismos bytes.
    violation: La prueba de nivel 1 busca la marca en la cabecera y en cada punto de página y el SHA-256 de la versión en la cabecera.
    source: VE-13, A-3, FR7.4, AC15.8.2; P6 = A
  - id: BR9.4
    status: nuevo
    statement: Una versión que ya no es la vigente se exporta con el rótulo de reemplazo.
    category: policy
    applies_to: Exportación de una versión con version_number menor que el de la vigente
    trigger: Exportar una versión anterior
    logic: SI la versión no es la vigente ENTONCES la cabecera dice «Reemplazada por la versión M el <fecha Colombia> (<UTC>)» junto a la marca, y ReportExport.was_current es false; la vigente no lleva el rótulo.
    violation: La prueba de nivel 1 exporta v1 con v2 vigente y busca el rótulo; exporta v2 y exige que no esté.
    source: P8 = A; FR7.5
  - id: BR9.5
    status: nuevo
    statement: El SHA-256 de cada exportación se registra antes de enviar los bytes, y el archivo exportado no se guarda.
    category: constraint
    applies_to: ReportExport, AccessLog
    trigger: Después de armar los bytes
    logic: SI los bytes están armados ENTONCES export_sha256 = SHA-256 de esos bytes; en una transacción se inserta ReportExport y la ruta de exportación llama a AccessLog.record con resource_type report_export, el report_version_id y export_sha256; tras el commit responde 201 con X-Veridicus-Export-SHA256 y los bytes; los bytes no se escriben en el volumen ni en la base.
    violation: La prueba de nivel 1 recalcula el SHA-256 de lo recibido y lo compara con ReportExport; la de nivel 0 comprueba con un doble que el puerto recibió usuario, versión y ese SHA-256; otra comprueba que el volumen no cambió.
    source: A-3, VE-12, AC15.8.2, UG-09
  - id: BR9.6
    status: nuevo
    statement: Si el registro de acceso real falla, no sale la exportación; sin registro construido, exporta igual y avisa.
    category: policy
    applies_to: Exportación y adaptador del puerto AccessLog
    trigger: Llamada a AccessLog.record
    logic: SI el adaptador real lanza un error o vence su plazo ENTONCES la transacción se revierte, no se envía ningún byte y responde 503 report.export_not_recorded (code nuevo, FD-U7-05); SI está cableado el adaptador por defecto ENTONCES la exportación responde 201, el log lleva un WARN «registro de acceso no configurado» solo con IDs y /readyz sigue en 200 con access_log not_configured.
    violation: Prueba de nivel 0 con el adaptador por defecto (201, WARN con IDs y /readyz 200) y con un doble que falla (503, 0 filas, 0 bytes).
    source: VE-13, AC15.8.2, UG-09; C23
  - id: BR9.7
    status: nuevo
    statement: Las cadenas fijas de la marca pasan el escaneo de vocabulario.
    category: validation
    applies_to: Plantilla de la marca y del rótulo de reemplazo
    trigger: Prueba de nivel 0
    logic: SI se escanean las cadenas fijas de la marca, del rótulo de reemplazo y de los encabezados de la exportación ENTONCES hay 0 coincidencias; el nombre de usuario es dato de IdentityAccess y no se escanea.
    violation: La prueba de nivel 0 falla.
    source: AC5.5.1, AC5.5.5

  # BR10 — Retención (C24)
  - id: BR10.1
    status: nuevo
    statement: ReviewReport borra lo suyo de una sesión vencida cuando se lo pide la retención, y devuelve IDs y SHA-256.
    category: policy
    applies_to: ReportExport, ReportVersion, ReportFile, PurgeReceipt
    trigger: Purgeable.purge_session llamado por el Job de retención (lo lanza el humano)
    logic: SI el Job llama purge_session ENTONCES, con el usuario de base de la retención, se borran las ReportExport de la sesión y después cada ReportVersion de la más nueva a la más antigua, borrando su archivo antes de su fila; devuelve PurgeReceipt con los IDs y el SHA-256 de cada versión borrada, nunca texto.
    violation: Prueba de nivel 1 con reloj simulado y el usuario de retención; otra comprueba que el usuario de la aplicación no puede borrar.
    source: C24, VE-12, A-2, AC15.7.2
  - id: BR10.2
    status: nuevo
    statement: Un archivo que ya no está no detiene el borrado.
    category: policy
    applies_to: ReportFile durante la retención
    trigger: Borrar el archivo de una versión
    logic: SI el archivo no existe ENTONCES se registra un WARN con el report_version_id, se marca file_missing en el recibo y se borra la fila; SI el borrado del archivo falla por otro motivo ENTONCES la transacción se revierte y purge_session falla sin borrar filas.
    violation: La prueba de nivel 1 cubre el archivo ausente y el fallo de borrado.
    source: C24, AC15.7.2

  # BR11 — Aviso de VE-01, páginas, avisos de la sesión y vocabulario de VE-02
  - id: BR11.1
    status: nuevo
    statement: El reporte lleva el aviso de VE-01 leído del archivo versionado.
    category: policy
    applies_to: ReportContent.header, ReportVersion.notice_version
    trigger: Generar el reporte
    logic: SI se genera ENTONCES el texto del aviso y su versión se leen de IntegrityPolicy; el aviso va en la cabecera y en cada punto de página de BR11.2; notice_version se guarda en la versión.
    violation: La prueba de nivel 1 cuenta las apariciones del aviso en el archivo dorado y compara notice_version.
    source: VE-01, AC15.5.2, A-1; C1 (notice_version)
  - id: BR11.2
    status: nuevo
    statement: Una «página» del reporte es una sección H2 fija o un bloque fijo de turnos o sugerencias.
    category: calculation
    applies_to: Plantilla de format_version 2
    trigger: Renderizar el reporte o la exportación
    logic: SI se renderiza ENTONCES las secciones H2 son, en orden, «Datos de la sesión y de las corridas», «Transcripción», «Sugerencias de revisión», «Avisos de la sesión» y «Consolidación»; el aviso (y en una exportación también la marca) cierra cada sección H2 y se repite dentro de «Transcripción» cada N turnos y dentro de «Sugerencias de revisión» cada N sugerencias, con N = 25 (propuesta FD-U7-06).
    violation: La prueba de nivel 1 recorre el archivo y falla si un tramo entre dos puntos de página supera N elementos o una sección H2 cierra sin aviso.
    source: P6 = A; AC15.5.2, AC15.8.2
  - id: BR11.3
    status: nuevo
    statement: El reporte declara los avisos de la sesión que aplican.
    category: policy
    applies_to: ReportContent.session_notices
    trigger: Generar el reporte
    logic: SI se usó el modo fragmentado ENTONCES «Análisis por ventanas de N turnos (solapamiento de M). No se buscaron contradicciones entre turnos separados por más de N turnos»; SI el perfil declara misma familia ENTONCES el aviso de AC13.1.2; SI hay blocked_code ENTONCES el incidente de anonimización con su code y hora; SI la sesión está terminated ENTONCES la terminación con su hora; SI hay retirada del consentimiento ENTONCES la retirada con su hora; más los rótulos de BR2.6.
    violation: La prueba de nivel 1 genera una sesión fixture por caso y busca cada texto.
    source: AC3.7.1, AC13.1.2, AC6.1.3; VE-10, VE-14
  - id: BR11.4
    status: nuevo
    statement: La plantilla del reporte pasa el vocabulario de VE-02 y solo el aviso exacto queda excluido.
    category: validation
    applies_to: Plantilla de format_version 2 y textos fijos del reporte
    trigger: Prueba de nivel 0
    logic: SI se escanean las plantillas y textos fijos del reporte con la lista versionada que suma «prueba», «probatorio», «pliego», «inculpa», «miente», «engaño» y «falso» ENTONCES hay 0 coincidencias; un fixture con cada término nuevo lo hace fallar; «prueba» dentro de la cadena versionada del aviso no lo hace fallar y en cualquier otra cadena sí.
    violation: La prueba de nivel 0 falla.
    source: VE-02, A-1, AC5.5.5, AC5.5.6
  - id: BR11.5
    status: nuevo
    statement: Las aclaraciones neutras no entran en el reporte.
    category: policy
    applies_to: ReportContent
    trigger: Generar el reporte de una sesión con aclaraciones
    logic: SI la sesión tiene aclaraciones propuestas, aprobadas o descartadas ENTONCES ninguna aparece en el reporte; quedan en la consola y en su historial.
    violation: La prueba de nivel 1 genera el reporte de una sesión fixture con aclaraciones aprobadas y falla si aparece su tema.
    source: Respuesta P6 = A del Functional Design de U8; AC10.3.3
```

## Resumen de reglas

| Grupo | Reglas | Estado | Qué protegen |
|---|---|---|---|
| BR1 Finalizar | BR1.1–BR1.6 | 1.1 y 1.3 siguen; el resto cambia | Solo el dueño, una vez, desde `open`, `paused`, `suspended` o `blocked`; inicio de MTTV; las corridas en curso terminan |
| BR2 Precondiciones | BR2.1–BR2.11 | 2.8–2.11 nuevas | Dueño, sesión finalizada o terminada, modo final lanzado, 0 corridas en curso, 0 pendientes y una ronda abierta; exentas e importadas |
| BR3 Contenido | BR3.1–BR3.4 | 3.4 sigue | Contenido de FR7.2 sin marco de verdad, IA y analista separados, render determinista, escaneo con los turnos como fuente literal y SHA-256 |
| BR4 Persistencia | BR4.1–BR4.5 | 4.3–4.5 siguen | Archivo antes que fila, una sola consolidación gana, sin huérfanos, solo inserción y bloqueo |
| BR5 Lectura y descarga | BR5.1–BR5.4 | 5.4 nueva | Vista previa con integridad, nada antes de consolidar, lectura para analistas y `admin`, descarga = exportación |
| BR6 Corrección | BR6.1–BR6.6 | 6.3 y 6.4 cambian | Solo el dueño, una copia por sesión, solo estados y notas, descarte sin versión, versión nueva que conserva la anterior |
| BR7 Medición | BR7.1–BR7.2 | 7.1 cambia | MTTV solo en guiadas; registros solo con identificadores |
| BR8 Consola | BR8.1–BR8.7 | 8.6 y 8.7 nuevas | Diálogos, M5, copia rotulada, accesibilidad, solo lectura, botón deshabilitado con motivo y `admin` |
| BR9 Exportación | BR9.1–BR9.7 | nuevas | Roles, integridad, marca, rótulo de reemplazo, *hash* registrado antes de enviar, registro de acceso y vocabulario de la marca |
| BR10 Retención | BR10.1–BR10.2 | nuevas | Borrado propio en orden, IDs y SHA-256 para el acta, archivo ausente |
| BR11 Aviso y avisos | BR11.1–BR11.5 | nuevas | Aviso versionado, «páginas», avisos de la sesión, vocabulario de VE-02, sin aclaraciones |

Reglas vigentes: 59 (16 que siguen, 22 que cambian y 21 nuevas). Retiradas: 0 (salen solo atributos y
referencias; ver `entities.md`).
