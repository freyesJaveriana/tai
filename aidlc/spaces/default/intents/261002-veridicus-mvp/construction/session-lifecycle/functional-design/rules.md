# Reglas de negocio — U6 session-lifecycle

**Insumos.** Los mismos de `entities.md`.

```yaml
rules:
  # BR1 — Versión nueva de un escenario
  - id: BR1.1
    statement: Cargar un documento corregido crea una versión nueva con identificador y SHA-256 propios; la anterior conserva sus pasajes y su SHA-256.
    category: policy
    applies_to: [ScenarioVersion]
    trigger: POST /scenarios/{scenario_id}/versions
    logic: SI el archivo pasa las validaciones de carga de U4 ENTONCES se crea la versión con el número siguiente, en indexing, y se indexa como en U4; ninguna fila de versiones anteriores cambia.
    violation: Prueba de nivel 1.
    source: FR2.4; AC1.2.1
  - id: BR1.2
    statement: No existe ninguna operación que modifique o borre una versión o un pasaje.
    category: constraint
    applies_to: [ScenarioVersion]
    trigger: OpenAPI y permisos de base de datos
    logic: SI se envía PUT, PATCH o DELETE sobre una versión o un pasaje ENTONCES 404 o 405 (la ruta no existe); SI el usuario de la aplicación intenta UPDATE o DELETE directo sobre pasajes ENTONCES falla.
    violation: Pruebas de nivel 0 (OpenAPI) y nivel 1 (permisos).
    source: AC1.2.2; FR2.4
  - id: BR1.3
    statement: Un documento con el mismo SHA-256 que una versión existente se rechaza indicando cuál es.
    category: validation
    applies_to: [ScenarioVersion]
    trigger: POST /scenarios/{scenario_id}/versions
    logic: SI el SHA-256 ya existe ENTONCES 409 scenario.duplicate_sha256 con «Este documento ya está cargado como <escenario> versión <n>» y no se crea ninguna versión.
    violation: Prueba de nivel 1.
    source: AC1.2.3
  - id: BR1.4
    statement: Al listar las versiones de un escenario se ve cada una con su SHA-256 y su fecha de carga.
    category: policy
    applies_to: [ScenarioVersion]
    trigger: GET /scenarios
    logic: SI se listan versiones ENTONCES cada una trae source_sha256 y uploaded_at.
    violation: Prueba de nivel 1.
    source: AC1.2.4

  # BR2 — Transcripción pegada
  - id: BR2.1
    statement: La transcripción se divide en turnos por línea vacía y por marca de hablante, con la misma regla en la consola y en el servidor.
    category: calculation
    applies_to: [TurnPreview]
    trigger: Vista previa y confirmación
    logic: SI una línea empieza por 1–30 caracteres sin dígitos ni ':' seguidos de ': ' ENTONCES abre un turno con ese hablante y la marca no entra en el texto; SI hay una o más líneas vacías ENTONCES cierran el turno en curso; las líneas consecutivas sin marca se unen al turno en curso; se quitan espacios de los bordes y se descartan bloques vacíos.
    violation: Prueba de nivel 0 compartida por la consola y el servidor sobre los mismos ejemplos.
    source: Respuesta P1 = A; FR3.3; requirements §7
  - id: BR2.2
    statement: Los turnos del entrevistador se guardan como contexto y no se evalúan.
    category: policy
    applies_to: [Turn, InterviewerLabels]
    trigger: Confirmación de la transcripción
    logic: SI el hablante coincide (sin mayúsculas ni tildes) con una etiqueta de InterviewerLabels ENTONCES el turno se guarda con role interviewer, sin encolar ni evaluar, y cuenta como turno previo en los paquetes; SI no ENTONCES role testimony y sigue el camino de U4.
    violation: Prueba de nivel 1.
    source: Respuesta P2 = A
  - id: BR2.3
    statement: Una transcripción admite hasta 100 turnos y 100 000 caracteres; un turno de más de 2 000 caracteres impide confirmar.
    category: validation
    applies_to: [TranscriptPaste, TurnPreview]
    trigger: Vista previa y POST /sessions/{id}/transcript
    logic: SI hay más de 100 turnos o más de 100 000 caracteres ENTONCES 422 transcript.too_large; SI algún turno supera 2 000 caracteres ENTONCES la vista previa lo marca y «Crear N turnos» queda deshabilitado, y la API responde 422 turn.too_long sin crear ninguno.
    violation: Pruebas Vitest y de nivel 1.
    source: Respuesta P3 = A; Functional Design de U4 (P5)
  - id: BR2.4
    statement: La vista previa muestra cuántos turnos detectó y cada uno, y cancelar no crea ninguno.
    category: policy
    applies_to: [TurnPreview]
    trigger: «Continuar» en el diálogo
    logic: SI se detectan turnos ENTONCES «Se detectaron N turnos» con la lista; SI no ENTONCES «No se detectaron turnos. Separa los turnos con una línea vacía o con una marca de hablante»; Cancelar o Escape no llaman a la API.
    violation: Prueba Vitest.
    source: AC2.3.1
  - id: BR2.5
    statement: Al confirmar, todos los turnos se crean en orden en una sola transacción y luego se encolan en ese orden.
    category: constraint
    applies_to: [Turn, TranscriptPaste]
    trigger: POST /sessions/{id}/transcript
    logic: SI la transcripción es válida ENTONCES en una transacción se numeran todos los turnos seguidos, se guarda TranscriptPaste y luego se publica C2 de los turnos testimony en orden; un reenvío con el mismo client_request_id devuelve los mismos turnos.
    violation: Prueba de nivel 1.
    source: AC2.3.2; C1
  - id: BR2.6
    statement: Pegar una transcripción produce los mismos resultados que enviarla turno a turno.
    category: constraint
    applies_to: [Turn]
    trigger: Golden Dataset
    logic: SI se procesa la misma transcripción pegada y turno a turno ENTONCES coinciden (número de turno, fragmento, ID de documento, calificación, tipo de resultado).
    violation: Prueba de nivel 1 con el juez fake y de nivel 2 con el modelo real.
    source: AC2.3.3; FR3.3

  # BR3 — Lista de sesiones e historial lateral
  - id: BR3.1
    statement: La lista muestra todas las sesiones con escenario, versión, dueño, fecha y estado, y se puede filtrar por las mías.
    category: policy
    applies_to: [SessionListItem]
    trigger: GET /sessions
    logic: SI un analista o admin abre la lista ENTONCES ve todas las sesiones (FR1.2: leer todas) con esos campos, fechas en hora de Colombia, y el filtro «Solo las mías».
    violation: Pruebas de nivel 1 y Vitest.
    source: AC2.5.1; FR1.2
  - id: BR3.2
    statement: Sin sesiones se ve el estado vacío con la acción «Nueva sesión» (solo para analistas).
    category: policy
    applies_to: [SessionListItem]
    trigger: Lista vacía
    logic: SI no hay sesiones ENTONCES «Aún no hay sesiones» y, para un analista, «Nueva sesión».
    violation: Prueba Vitest.
    source: AC2.5.2
  - id: BR3.3
    statement: El historial lateral muestra mis sesiones anteriores por fecha con su estado (COULD).
    category: policy
    applies_to: [SessionListItem]
    trigger: Abrir el panel lateral en M4
    logic: SI se abre el panel ENTONCES lista las sesiones del usuario ordenadas por created_at descendente con su estado; usa la misma ruta GET /sessions.
    violation: Prueba Vitest.
    source: AC11.2.1

  # BR4 — Suspensión y reanudación
  - id: BR4.1
    statement: Cada consulta del dueño a su sesión abierta cuenta como latido.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: GET /sessions/{id} o POST /sessions/{id}/heartbeat del dueño
    logic: SI el dueño consulta su sesión open ENTONCES last_heartbeat_at = ahora; las consultas de otros usuarios no cuentan.
    violation: Prueba de nivel 1.
    source: AC7.1.1; contract-design P6
  - id: BR4.2
    statement: Una sesión abierta sin latido durante T segundos pasa a suspendida en a lo sumo T más el intervalo de revisión.
    category: policy
    applies_to: [InterviewSessionRecord, SessionStatusChange]
    trigger: Revisión periódica en session-api
    logic: SI status open Y now − last_heartbeat_at > T ENTONCES status suspended, suspended_at y SessionStatusChange (open → suspended, actor sistema); T y el intervalo los fija NFR Requirements.
    violation: Prueba de nivel 1 con reloj controlado.
    source: FR8.2; AC7.1.1
  - id: BR4.3
    statement: La suspensión no detiene el procesamiento de turnos ya encolados.
    category: policy
    applies_to: [Turn]
    trigger: Sesión suspendida con turnos en cola
    logic: SI la sesión está suspended ENTONCES los turnos queued o processing siguen su curso y sus resultados se ingieren normalmente; no se aceptan turnos nuevos.
    violation: Prueba de nivel 1.
    source: AC7.1.4; FR8.1
  - id: BR4.4
    statement: Al volver a entrar a una sesión suspendida propia se ofrece reanudar; «Más tarde» la deja suspendida.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: Abrir una sesión suspended propia o entrar a la consola con una
    logic: SI el dueño abre su sesión suspended ENTONCES ve el diálogo «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?» con «Reanudar» y «Más tarde»; «Más tarde» vuelve a M1 sin cambiar el estado.
    violation: Prueba Vitest.
    source: AC7.1.2; FR8.3
  - id: BR4.5
    statement: Reanudar devuelve la sesión a abierta desde el último turno registrado, sin duplicar turnos, alertas ni filas de historial.
    category: constraint
    applies_to: [InterviewSessionRecord, SessionStatusChange]
    trigger: POST /sessions/{id}/resume
    logic: SI la sesión está suspended ENTONCES pasa a open con SessionStatusChange (suspended → open, actor dueño) y nada más cambia; SI no está suspended ENTONCES 409 session.not_suspended; SI no es el dueño ENTONCES 403.
    violation: Prueba de nivel 1 con conteos antes del corte y tras reanudar.
    source: AC7.1.3; AC7.1.5; FR8.3
  - id: BR4.6
    statement: El historial de estado de la sesión cumple la convención de auditoría.
    category: constraint
    applies_to: [SessionStatusChange]
    trigger: Prueba común de nivel 1
    logic: SI se insertan los cambios de suspensión y reanudación ENTONCES llevan hora y actor (o actor sistema con actor_kind), y no admiten UPDATE ni DELETE.
    violation: Prueba común de nivel 1 de U3.
    source: AC8.4.1; AC8.4.2; ADR-003

  # BR5 — Progreso (SHOULD)
  - id: BR5.1
    statement: Un turno en proceso muestra su etapa y un cronómetro, y cada cambio de etapa se anuncia.
    category: policy
    applies_to: [Turn]
    trigger: Turno queued o processing
    logic: SI el turno está en proceso ENTONCES muestra «Procesando audio…», «Consultando marco de verdad…» o «Evaluando…» según su etapa, con un cronómetro mm:ss, y la región aria-live anuncia el cambio de etapa una vez.
    violation: Prueba Vitest.
    source: FR10.1; AC10.1.1
  - id: BR5.2
    statement: Ningún turno queda en proceso indefinidamente.
    category: policy
    applies_to: [Turn]
    trigger: Plazo vencido
    logic: SI vence el plazo del turno ENTONCES pasa a error con turn.error.timeout y ofrece reintentar (la tarea de plazos de U4).
    violation: Prueba de nivel 1.
    source: AC10.1.2; Functional Design de U4 (tarea de plazos)

  # BR6 — Accesibilidad
  - id: BR6.1
    statement: M1, el diálogo de pegado, el de reanudación y el historial lateral cumplen la base de accesibilidad de U4, y el estado suspendido se ve con texto e icono.
    category: constraint
    applies_to: [SessionListItem, TurnPreview]
    trigger: Niveles 0 y 3
    logic: SI axe encuentra violaciones serious o critical, si un flujo no se puede hacer solo con teclado, o si «Suspendida» u otro estado se distingue solo por color ENTONCES la prueba falla.
    violation: Pruebas de nivel 3 y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3; AC2.5.3
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Versiones | BR1.1–BR1.4 | Que corregir un escenario cambie lo que ya vio una sesión |
| BR2 Pegado | BR2.1–BR2.6 | Divisiones ambiguas (P1), preguntas del analista evaluadas como testimonio (P2), lotes enormes (P3) |
| BR3 Lista | BR3.1–BR3.3 | Encontrar y retomar sesiones |
| BR4 Suspensión | BR4.1–BR4.6 | Perder trabajo o duplicarlo al reconectar |
| BR5 Progreso | BR5.1–BR5.2 | Dudar si el sistema se colgó |
| BR6 Accesibilidad | BR6.1 | Estados solo por color; flujos sin teclado |
