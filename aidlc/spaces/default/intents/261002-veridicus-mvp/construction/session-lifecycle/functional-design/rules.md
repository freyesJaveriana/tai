# Reglas de negocio — U6 session-lifecycle

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-02. Conserva los ID que siguen; los que salen quedan
«Retirado» sin renumerar (regla de `project.md`).
- **Salen** (`Retirado`): BR1.1–BR1.4 (versión nueva de un escenario, US1.2, cambio 01) y BR2.2 (etiquetas
  del entrevistador, superadas por el hablante `ENT`/`TEST` de FR3.2).
- **Cambian:** BR2.1, BR2.3–BR2.6, BR3.1, BR3.2, BR4.1–BR4.6, BR5.1, BR5.2 y BR6.1. BR3.3 se mantiene.
- **Entran:** BR2.7, BR3.4, BR3.5, BR5.3, BR6.2; los grupos nuevos BR7 (importación), BR8 (modo final),
  BR9 (pausa, terminación y retirada del consentimiento) y BR10 (solo el dueño).
- **Hallazgos de `reviews/review-01.md`:** R-01 se resuelve en BR4.2 y BR4.5; R-02 en BR2.5; R-03 queda
  caduco (los codes de C1 revisión 3 sustituyen a `session.not_open` y `turn.too_long`; ver BR2.3 y BR4.3);
  R-04 en BR2.1 y BR2.7; R-05 en BR3.5 (la mitad de `version_number` caduca con `ScenarioVersion`).

**Insumos.** Los mismos de `entities.md`. Las reglas de U4 que U6 reutiliza (rechazo de turnos por
estado, guardia de consentimiento, guardia de encolado, supervisor de plazos, clave de cancelación,
deduplicación por par) se citan por su nombre y no por su ID, para no mezclar ID entre unidades.

```yaml
rules:
  # BR1 — Versión nueva de un escenario (Retirado)
  - id: BR1.1
    status: Retirado
    statement: 'Versión nueva con SHA-256 propio. Sale US1.2 con TruthFrame (cambio 01).'
    source: cambio 01 (DT27); unit-of-work revisión 3
  - id: BR1.2
    status: Retirado
    statement: 'Sin operaciones de modificación ni borrado de versiones. Sale con US1.2.'
    source: cambio 01 (DT27)
  - id: BR1.3
    status: Retirado
    statement: 'Documento con un SHA-256 ya cargado. Sale con US1.2.'
    source: cambio 01 (DT27)
  - id: BR1.4
    status: Retirado
    statement: 'Lista de versiones con su SHA-256. Sale con US1.2.'
    source: cambio 01 (DT27)

  # BR2 — Bloque pegado
  - id: BR2.1
    status: cambia
    statement: 'El bloque pegado se divide en turnos por línea vacía y por marca de hablante ENT o TEST (literal o alias de la lista versionada), con la misma regla y los mismos ejemplos en la consola y en el servidor.'
    category: calculation
    applies_to: [TurnPreview, SpeakerMarkerList]
    trigger: Vista previa en la consola y POST /sessions/{id}/transcript
    logic: 'SI una línea, sin los espacios del inicio, empieza por una marca literal (ENT o TEST) o por un alias de SpeakerMarkerList seguido de dos puntos, sin distinguir mayúsculas ni tildes, ENTONCES cierra el turno en curso y abre uno con ese hablante; la marca y los dos puntos no entran en el texto. Cualquier otra «Palabra:» (p. ej. «Entonces dijo:», «Nota:», «Hora: 14:30») queda en el texto. Una o más líneas vacías cierran el turno en curso. Un turno sin marca hereda el hablante del turno anterior del bloque; el primero sin marca es TEST. Se quitan los espacios de los bordes de cada turno y se descartan los turnos vacíos. Para corregir un hablante, el analista usa «Volver a editar» y escribe la marca; el cuerpo de C1 no cambia.'
    violation: Prueba de nivel 0 compartida (Vitest y pytest) sobre los ejemplos versionados de SpeakerMarkerList; falla si las dos implementaciones dan turnos distintos en algún ejemplo.
    source: P4 = A; FR3.2; FR3.3; AC2.3.1; AC2.3.2; R-04 de la revisión 1
  - id: BR2.2
    status: Retirado
    statement: 'Etiquetas configurables del entrevistador (P2 de la primera pasada). Las sustituye el hablante ENT/TEST: un turno ENT se guarda como contexto sin corrida, como en U4.'
    source: cambio 01; FR3.2; C1 Turn.hablante
  - id: BR2.3
    status: cambia
    statement: 'Un bloque que supera un límite del catálogo (turnos, caracteres del bloque o caracteres por turno) no se confirma y la API responde 413 sin crear filas; en el límite exacto se acepta.'
    category: validation
    applies_to: [TranscriptPaste, TurnPreview]
    trigger: Vista previa y POST /sessions/{id}/transcript
    logic: 'SI el número de turnos supera transcript_max_turns, o la longitud de text supera transcript_max_chars, o algún turno supera turn_max_chars (C25) ENTONCES la vista previa muestra «El bloque tiene N turnos; el máximo es M» (o «El bloque tiene N caracteres; el máximo es M», o «El turno K tiene N caracteres; el máximo es M»), marca los turnos que lo superan, «Confirmar» queda deshabilitado (enfocable) con ese motivo, y la API responde 413 limits.exceeded con 0 filas. Las cifras se leen de contracts/limits.v1.yaml; los caracteres se cuentan en puntos de código.'
    violation: Prueba de nivel 1 en el límite exacto y en el límite + 1 para cada una de las tres cifras; Vitest del mensaje y del botón.
    source: AC2.3.4; FR3.7; C25; R-03 de la revisión 1 (turn.too_long y transcript.too_large salen)
  - id: BR2.4
    status: cambia
    statement: 'La vista previa muestra cuántos turnos detectó y cada uno con su hablante; cancelar no crea ningún turno.'
    category: policy
    applies_to: [TurnPreview]
    trigger: «Continuar» en el diálogo «Pegar transcripción»
    logic: 'SI se detectan turnos ENTONCES «Se detectaron N turnos» y la lista con número, hablante y primeras líneas; SI no ENTONCES «No se detectaron turnos. Separa los turnos con una línea vacía o empieza cada uno con ENT: o TEST:». «Volver a editar» regresa al texto sin perderlo; «Cancelar» o Escape cierran sin llamar a la API.'
    violation: Prueba Vitest (0 llamadas a la API al cancelar).
    source: AC2.3.1
  - id: BR2.5
    status: cambia
    statement: 'Al confirmar, los turnos del bloque se crean seguidos en una transacción y se encola una sola corrida incremental para todo el bloque; el reenvío devuelve lo mismo.'
    category: constraint
    applies_to: [Turn, TranscriptPaste]
    trigger: POST /sessions/{id}/transcript
    logic: 'SI el bloque es válido ENTONCES el servidor vuelve a dividirlo con BR2.1 (nunca confía en la vista previa) y, con el orden de bloqueo usuario → sesión, en una transacción numera los k turnos n..n+k−1, guarda TranscriptPaste y, si el bloque tiene algún turno TEST y la sesión admite corridas, crea una corrida incremental con desde_turno = n y hasta_turno = el último turno TEST del bloque (precisión FD-U6-07) con su primer cambio de estado; tras confirmar publica C2 y responde 202 con turns y run. SI (session_id, client_request_id) ya existe ENTONCES responde 202 con los mismos turnos y la misma corrida, sin publicar otra vez. SI la publicación falla tras confirmar ENTONCES no hay outbox: el supervisor de plazos de U4 deja la corrida en error con analysis.system y M4 ofrece «Reintentar tramo».'
    violation: Prueba de nivel 1 (k turnos, una sola corrida con su tramo; reenvío sin duplicados; corte entre la confirmación y la publicación termina en error por plazo con reloj simulado).
    source: AC2.3.3; FR4.9; C1 /transcript; R-02 de la revisión 1
  - id: BR2.6
    status: cambia
    statement: 'Pegar un bloque o importar una transcripción produce los mismos turnos que escribirlos uno a uno.'
    category: constraint
    applies_to: [Turn]
    trigger: Nivel 1 sobre una transcripción sintética
    logic: 'SI la misma transcripción sintética entra escrita turno a turno, pegada y como archivo de importación ENTONCES las tres secuencias de turnos coinciden en n, hablante y texto (el origen y la página difieren por definición). La igualdad de hallazgos ya no se exige: un bloque da una sola corrida incremental y un turno escrito da una por turno.'
    violation: Prueba de nivel 1 de las tres entradas.
    source: bolt-plan B7 (definición de terminado 2); FR3.3; FR3.6; docs/iteracion2.md C10
  - id: BR2.7
    status: nuevo
    statement: 'Un bloque sobre una sesión que no admite turnos se rechaza con el mismo code y el mismo orden que un turno escrito; en pausa los turnos se guardan sin corrida.'
    category: validation
    applies_to: [TranscriptPaste, Turn]
    trigger: POST /sessions/{id}/transcript
    logic: 'SI la sesión no tiene ConsentRecord ENTONCES 409 session.consent_missing; luego, en el orden del rechazo de turnos de U4, session.blocked, session.consent_withdrawn, session.terminated, session.finalized (también consolidada), session.closed_to_new_turns (importada) y session.suspended (FD-U4-07), con 0 filas. SI la sesión está paused ENTONCES se guardan los turnos y TranscriptPaste sin corrida y responde 202 sin run. Un bloque se numera después del último turno de la sesión aunque haya corridas en cola.'
    violation: Prueba de nivel 1 por estado (0 filas en cada rechazo; en pausa, turnos sin corrida y el fake con 0 llamadas).
    source: C1 ErrorCode; AC15.2.1; FD-U4-07; R-04 de la revisión 1

  # BR3 — Lista de sesiones e historial lateral
  - id: BR3.1
    status: cambia
    statement: 'La lista muestra todas las sesiones con entrevista, origen, perfil, dueño, fecha y estado, y se puede filtrar por las mías.'
    category: policy
    applies_to: [SessionListItem]
    trigger: GET /sessions y M1
    logic: 'SI un analista o un admin abre M1 ENTONCES ve todas las sesiones (FR1.2: leer todas) ordenadas por created_at descendente, con entrevista, origen («Importada» para corpus y sintetico, «Guiada»), perfil, dueño, fecha en hora de Colombia y estado con texto e icono decorativo; «Solo las mías» filtra por owner_user_id en la consola. Cada fila abre M4, o M5 si está consolidada; la de otro analista se abre en solo lectura.'
    violation: Prueba de nivel 1 con sesiones de dos analistas y Vitest de las columnas y del filtro.
    source: AC2.5.1; FR1.2; M1
  - id: BR3.2
    status: cambia
    statement: 'Sin sesiones se ve el estado vacío con «Nueva sesión» e «Importar transcripción» para el analista.'
    category: policy
    applies_to: [SessionListItem]
    trigger: Lista vacía
    logic: 'SI no hay sesiones ENTONCES «Aún no hay sesiones» y, para un analista, «Nueva sesión» e «Importar transcripción»; el admin no ve esas acciones. SI hay sesiones pero el filtro no deja ninguna ENTONCES «No hay sesiones con este filtro» y «Quitar filtros».'
    violation: Prueba Vitest por rol.
    source: AC2.5.2; M1
  - id: BR3.3
    statement: 'El historial lateral muestra mis sesiones anteriores ordenadas por fecha con su estado (COULD).'
    category: policy
    applies_to: [SessionListItem]
    trigger: «Mis sesiones» en M4
    logic: 'SI se abre el panel ENTONCES lista las sesiones del usuario por created_at descendente con su estado (texto e icono), con la misma ruta GET /sessions filtrada en la consola; no sustituye a M1 y no atrapa el foco.'
    violation: Prueba Vitest.
    source: AC11.2.1; FR11.2
  - id: BR3.4
    status: nuevo
    statement: 'La lista se filtra por estado con el enum de C1, pagina de 25 en 25, y solo la ven el analista y el admin.'
    category: authorization
    applies_to: [SessionListItem]
    trigger: GET /sessions y M1
    logic: 'SI se elige un estado ENTONCES se pide GET /sessions?status=<SessionStatus>; SI hay más de 25 filas ENTONCES «Mostrando 1–25 de N» con paginación en la consola. SI el rol es investigador ENTONCES 403 auth.forbidden. GET /sessions no registra acceso en C23 porque no devuelve testimonio, solo identificadores.'
    violation: Prueba de nivel 1 (filtro por estado y 403 del investigador) y Vitest de la paginación.
    source: AC2.5.1; C1 GET /sessions (x-veridicus-roles); M1
  - id: BR3.5
    status: nuevo
    statement: 'Cada SessionSummary de la lista lleva pending_suggestions, que C1 exige, aunque M1 no lo muestre.'
    category: calculation
    applies_to: [SessionListItem]
    trigger: GET /sessions
    logic: 'SI ConsoleApi arma la lista ENTONCES pending_suggestions = ReviewRounds.pending_count de la ronda abierta de la sesión (C11), o 0 si la sesión no tiene ronda; M1 no lo muestra como columna (R-05).'
    violation: Prueba de nivel 1 (sesión sin ronda da 0; con dos pendientes da 2).
    source: C1 SessionSummary (campo requerido); C11 ReviewRounds; R-05 de la revisión 1; precisión FD-U6-20

  # BR4 — Latido, suspensión y reanudación
  - id: BR4.1
    status: cambia
    statement: 'Cada consulta del dueño a su sesión abierta, o su latido explícito, cuenta como latido.'
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: GET /sessions/{id} o POST /sessions/{id}/heartbeat del dueño
    logic: 'SI el dueño consulta su sesión con status open ENTONCES last_heartbeat_at = hora del servidor, sin subir change_cursor; SI la sesión no está open, o quien consulta no es el dueño, ENTONCES el latido no cuenta y POST /heartbeat responde 204 sin cambios. Sin corridas en proceso, M4 mantiene el sondeo lento o POST /heartbeat (poll_interval_s, C25).'
    violation: Prueba de nivel 1 (la consulta de otro usuario no mueve last_heartbeat_at).
    source: AC7.1.1; C1 GET /sessions/{id} y /heartbeat; contract-design P6
  - id: BR4.2
    status: cambia
    statement: 'Una sesión abierta, guiada o importada, sin latido durante T pasa a suspendida en a lo sumo T más el intervalo de revisión.'
    category: policy
    applies_to: [InterviewSessionRecord, SessionStatusChange]
    trigger: Revisión periódica de session-api (actor session-supervisor)
    logic: 'SI status es open Y ahora − coalesce(last_heartbeat_at, created_at) > heartbeat_timeout_s (C25) ENTONCES, bajo el bloqueo de la fila de la sesión y con change_cursor.bump, status → suspended y SessionStatusChange (open → suspended, actor_kind system, actor_system session-supervisor, at). La tarea es idempotente: solo toca filas open en la misma transacción, y una sesión ya suspended no genera otra fila. Una sesión paused no se suspende (ya no analiza). El intervalo de revisión lo fija NFR Requirements.'
    violation: Prueba de nivel 1 con reloj simulado (también con last_heartbeat_at nulo, con una importada y con una pausada que no se suspende).
    source: AC7.1.1; FR8.2; R-01 de la revisión 1; precisión FD-U6-13
  - id: BR4.3
    status: cambia
    statement: 'La suspensión no detiene las corridas ya encoladas, pero la sesión no admite turnos, bloques, modo final ni pausa hasta reanudarla.'
    category: policy
    applies_to: [InterviewSessionRecord, AnalysisRun]
    trigger: Sesión suspended
    logic: 'SI la sesión está suspended ENTONCES las corridas queued o processing siguen y sus resultados se ingieren normalmente; un turno o un bloque responden 409 session.suspended (FD-U4-07), el modo final y la pausa también, con 0 filas. Terminar y registrar la retirada sí se admiten.'
    violation: Prueba de nivel 1 (corrida en cola que termina durante la suspensión; turno, bloque y modo final con 409).
    source: AC7.1.4; FR8.1; FD-U4-07; R-03 de la revisión 1 (session.not_open sale)
  - id: BR4.4
    status: cambia
    statement: 'Al entrar a la consola, o al abrir una sesión suspendida propia, se ofrece reanudarla; «Más tarde» la deja suspendida.'
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: Entrada a M1 o apertura de M4 de una sesión suspended del dueño
    logic: 'SI el dueño tiene sesiones suspended ENTONCES M1 abre el diálogo modal «Se detectó una interrupción inesperada en la sesión. ¿Desea reanudar desde el último turno registrado?» con la más reciente (entrevista, perfil, fecha y número de turnos) y «Más tarde» y «Reanudar»; las demás se reanudan desde su fila. «Más tarde» cierra el diálogo sin cambiar el estado. SI abre M4 de una sesión suspended propia ENTONCES el mismo diálogo. Un admin u otro analista no ven el diálogo.'
    violation: Prueba Vitest (con dos sesiones suspendidas, el diálogo muestra la más reciente).
    source: AC7.1.2; FR8.3; M1
  - id: BR4.5
    status: cambia
    statement: 'Reanudar devuelve la sesión a abierta desde el último turno registrado, reinicia el latido y no duplica turnos, corridas, hallazgos ni decisiones.'
    category: constraint
    applies_to: [InterviewSessionRecord, SessionStatusChange]
    trigger: POST /sessions/{id}/resume
    logic: 'SI quien llama no es el dueño ENTONCES 403 session.not_owner y 0 filas; SI la sesión no está suspended ENTONCES 409 session.not_suspended; SI no ENTONCES status → open, last_heartbeat_at = hora del servidor, change_cursor.bump y SessionStatusChange (suspended → open, actor el dueño); no se reencola, reenvía ni crea nada más. Los turnos que terminaron mientras tanto se ven «Analizado» o con su error.'
    violation: 'Prueba de nivel 1 que corta el latido a mitad de una transcripción: los conteos de turnos, corridas, sugerencias y decisiones son iguales antes del corte y tras reanudar, y SessionStatusChange crece exactamente en 2 (precisión FD-U6-14); la siguiente revisión del supervisor tras reanudar no vuelve a suspender.'
    source: AC7.1.3; AC7.1.5; FR8.3; R-01 de la revisión 1
  - id: BR4.6
    status: cambia
    statement: 'Todo lo que U6 escribe cumple la convención de auditoría de U3.'
    category: constraint
    applies_to: [SessionStatusChange, TranscriptPaste, ConsentRecord, InterviewSessionRecord]
    trigger: Prueba común de nivel 1 de U3
    logic: 'SI se inserta una fila de SessionStatusChange (suspensión, reanudación, pausa, reanudación del análisis, terminación, importación), de TranscriptPaste o una corrida final ENTONCES lleva hora y actor (persona o session-supervisor) y un INSERT con actor u hora nulos falla; esas tablas son history y no admiten UPDATE ni DELETE con el usuario de la aplicación. ConsentRecord es mutable solo en withdrawn_at y withdrawn_by, de nulo a valor. TranscriptPaste lleva la marca veridicus-audit.'
    violation: Prueba común de nivel 1 de U3 sobre las tablas de U6.
    source: AC8.4.1; AC8.4.2; ADR-003

  # BR5 — Progreso (SHOULD)
  - id: BR5.1
    status: cambia
    statement: 'Una corrida en proceso muestra su etapa y un cronómetro, y cada cambio de la corrida se anuncia una vez.'
    category: policy
    applies_to: [RunProgress]
    trigger: Corrida queued o processing en M4
    logic: 'SI la corrida está queued ENTONCES «En cola»; SI está processing ENTONCES «Analizando contradicciones…» (o «Procesando audio…» si el turno de voz está transcribing, U9), con un cronómetro mm:ss desde la última transición. En el modo final con chunking activo se añade «N ventanas» (BR5.3); no hay «ventana N de M» (P7 = B, precisión FD-U6-09). La región aria-live polite anuncia una vez el inicio, el cambio de etapa, el fin y el error de cada corrida; nunca el cronómetro.'
    violation: Prueba Vitest.
    source: AC10.1.1; FR10.1; P7 = B
  - id: BR5.2
    status: cambia
    statement: 'Ninguna corrida queda en proceso indefinidamente.'
    category: policy
    applies_to: [AnalysisRun]
    trigger: Plazo vencido
    logic: 'SI la biblioteca agota su plazo ENTONCES la corrida termina en error con analysis.timeout (tiempo_agotado); SI vence deadline_at sin resultado ENTONCES el supervisor de plazos de U4 la deja en error con analysis.system. En los dos casos M4 muestra la causa y ofrece «Reintentar tramo» (incremental) o «Relanzar modo final» (final).'
    violation: Prueba de nivel 1 con reloj simulado para una incremental y una final.
    source: AC10.1.2; C2 (plazo vencido); C25 run_deadline_incremental_s y run_deadline_final_s
  - id: BR5.3
    status: nuevo
    statement: 'El total de ventanas del modo final lo calcula session-api con la ventana y el solapamiento de la configuración efectiva de la sesión.'
    category: calculation
    applies_to: [RunProgress]
    trigger: Corrida final con chunking.enabled en effective_config
    logic: 'Con N turnos hasta hasta_turno, ventana W y solapamiento O de effective_config: SI N <= W ENTONCES 1; SI no ENTONCES 1 + techo((N − W) / (W − O)). Es la misma cuenta que el armado de ventanas por posición de U11, con los mismos ejemplos; sin chunking no se muestra total.'
    violation: Prueba de nivel 0 de la función sobre los ejemplos de ventanas de U11 (N <= W, N = W + 1, N = 312 con W = 40 y O = 8 da 10).
    source: P7 = B; AC10.1.1; C18 chunking; FD-U11-26

  # BR6 — Accesibilidad
  - id: BR6.1
    status: cambia
    statement: 'Las pantallas y diálogos de U6 cumplen la base de accesibilidad de U4, y todo estado se lee con texto además del color.'
    category: constraint
    applies_to: [SessionListItem, TurnPreview, ImportPreview, RunProgress]
    trigger: Niveles 0 y 3
    logic: 'SI axe (WCAG 2.1 AA) encuentra violaciones serious o critical en M1, M7, el diálogo de pegado, el de reanudación, los de terminar y de registrar la retirada, la franja del modo final o el historial lateral ENTONCES la suite falla; SI importar y confirmar la vista previa, lanzar y relanzar el modo final o responder al aviso de reanudación no se recorren solo con teclado con el foco visible ENTONCES falla; SI un estado de sesión, de corrida o del modo final se distingue solo por color ENTONCES falla.'
    violation: Pruebas de nivel 3 (Playwright con @axe-core/playwright, en la suite de U4) y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3; AC2.5.3
  - id: BR6.2
    status: nuevo
    statement: 'Los botones deshabilitados de U6 son enfocables y anuncian su motivo, y los cambios de muchos turnos se anuncian solo agregados.'
    category: constraint
    applies_to: [TurnPreview, ImportPreview, RunProgress]
    trigger: Nivel 0
    logic: 'SI «Confirmar» del pegado, «Importar», «Lanzar modo final», «Relanzar modo final», «Pausar análisis» o «Terminar sesión» están deshabilitados ENTONCES usan aria-disabled="true" (no disabled nativo) y aria-describedby con su motivo; SI un bloque pegado o una importación de cientos de turnos cambia de estado ENTONCES aria-live solo anuncia el contador, el inicio, el fin o el error del modo final y la sesión suspendida; el estado de cada turno se lee al enfocarlo.'
    violation: Prueba Vitest.
    source: AC5.6.4; AC5.6.5

  # BR7 — Importación
  - id: BR7.1
    status: nuevo
    statement: 'Un archivo que no es JSON se rechaza con 415.'
    category: validation
    applies_to: [ImportPreview]
    trigger: POST /sessions/import y selección del archivo en M7
    logic: 'SI la parte file no es application/json (o el archivo no se puede leer como JSON en UTF-8) ENTONCES 415 import.invalid_type con «El archivo debe ser JSON con el formato del contrato común» y 0 filas. El YAML que menciona la descripción de C1 no se admite (precisión FD-U6-03).'
    violation: Prueba de nivel 1 con un archivo de texto y Vitest del mensaje.
    source: AC2.6.2; M7; C1 /sessions/import
  - id: BR7.2
    status: nuevo
    statement: 'Un archivo que supera un límite del catálogo se rechaza con 413 antes de crear o encolar nada; en el límite exacto se acepta.'
    category: validation
    applies_to: [ImportPreview]
    trigger: POST /sessions/import y vista previa en M7
    logic: 'SI el tamaño supera import_file_max_bytes ENTONCES 413 limits.exceeded antes de leerlo; SI el número de turnos supera transcript_max_turns, la suma de caracteres de texto supera transcript_max_chars o algún texto supera turn_max_chars ENTONCES 413 limits.exceeded con «La transcripción tiene N turnos; el máximo es M» (o su equivalente) y 0 filas; M7 deja «Importar» deshabilitado con ese motivo.'
    violation: Prueba de nivel 1 en el límite exacto y en el límite + 1 para cada cifra.
    source: AC2.6.3; FR3.7; C25
  - id: BR7.3
    status: nuevo
    statement: 'Un archivo fuera del esquema de entrada de C6 se rechaza completo con el primer problema y el total.'
    category: validation
    applies_to: [ImportProblem]
    trigger: POST /sessions/import y vista previa en M7
    logic: 'SI el JSON está mal formado, falta un campo obligatorio, turnos está vacío, hay números de turno repetidos, pagina_fin < pagina, estado está fuera del enum, hablante no es ENT ni TEST, un texto está vacío tras quitar espacios o modo no es final ENTONCES 422 import.invalid_transcript con «<primer problema>. Hay N problemas más» (p. ej. «Turno 37: falta el hablante. Hay 3 problemas más»), sin texto del testimonio, y 0 sesiones y 0 turnos. Los problemas se ordenan por posición; desde_turno y hasta_turno, si vienen, se ignoran. M7 valida con el mismo esquema versionado y el servidor es la autoridad.'
    violation: Prueba de nivel 0 del esquema (un caso por problema) y de nivel 1 del conteo con un archivo de 4 problemas.
    source: AC2.6.2; FR3.6; C1 /sessions/import; C6 entrada
  - id: BR7.4
    status: nuevo
    statement: 'Se importan transcripciones corpus con su bloque de consentimiento y sintéticas con o sin él; sin bloque, la sesión guarda un consentimiento de tipo sintetico.'
    category: validation
    applies_to: [ConsentRecord, ImportPreview]
    trigger: POST /sessions/import
    logic: 'SI origen no es corpus ni sintetico ENTONCES 422 import.invalid_transcript (precisión FD-U6-04); SI origen es corpus sin bloque consentimiento ENTONCES 422 import.invalid_transcript con «Falta el bloque de consentimiento»; SI el bloque viene ENTONCES se valida como al crear una sesión guiada (tipo, versión, constancias con patrón de identificador, mandato) y se guarda en ConsentRecord; SI origen es sintetico sin bloque ENTONCES ConsentRecord kind sintetico con transferencia autorizada y voz, audio y mandato en false (precisión FD-U6-05), y M7 dice «Transcripción sintética: no corresponde a una persona real; no se registra consentimiento». Un bloque de tipo sintetico dentro de un archivo corpus es inválido.'
    violation: Prueba de nivel 1 (corpus sin bloque 422; sintetico sin bloque crea kind sintetico; corpus con bloque inválido 422) y Vitest del texto.
    source: P5 = A; A-4; FR3.6; C1 /sessions/import; AC2.6.2
  - id: BR7.5
    status: nuevo
    statement: 'La importación exige un perfil aprobado, igual al del archivo y compatible con el consentimiento.'
    category: validation
    applies_to: [InterviewSessionRecord]
    trigger: POST /sessions/import
    logic: 'SI profile_name no es un perfil aprobado ENTONCES 422 profile.not_approved; SI perfil del archivo es distinto de profile_name ENTONCES 422 import.profile_mismatch; SI el bloque no autoriza la transferencia y el perfil tiene un papel commercial ENTONCES 422 profile.transfer_not_authorized; en todos, 0 filas. El selector de M7 es el de M3, sin perfil preseleccionado.'
    violation: Prueba de nivel 1 por caso.
    source: C1 /sessions/import; FR3.1; VE-07
  - id: BR7.6
    status: nuevo
    statement: 'Una importación válida crea la sesión abierta, cerrada a turnos nuevos y sin corridas, con los turnos iguales campo a campo a los del archivo.'
    category: constraint
    applies_to: [InterviewSessionRecord, Turn, ConsentRecord, SessionStatusChange]
    trigger: «Importar» en M7 (POST /sessions/import)
    logic: 'SI el archivo pasa BR7.1–BR7.5 ENTONCES en una transacción se crean InterviewSessionRecord (status open, origin corpus o sintetico, closed_to_new_turns true, perfil, effective_config y config_sha256 fijados, last_heartbeat_at = ahora), ConsentRecord (recorded_by el analista, recorded_at la hora del servidor), los turnos con origin imported y n, hablante, pagina, pagina_fin, texto y estado tal cual, y SessionStatusChange (null → open, actor el analista); no se crea ninguna corrida y responde 201 con SessionView, con «Lanzar modo final» disponible.'
    violation: Prueba de nivel 1 que compara los turnos leídos por la API con los del archivo, campo a campo, y cuenta 0 corridas.
    source: AC2.6.1; FR3.6
  - id: BR7.7
    status: nuevo
    statement: 'Antes de crear nada, M7 muestra el resumen del archivo y cancelar no crea filas.'
    category: policy
    applies_to: [ImportPreview]
    trigger: Selección de un archivo válido en M7
    logic: 'SI el archivo es válido ENTONCES «Se importarán N turnos (páginas X–Y), de ellos K del entrevistador y P plegados. La sesión no admitirá turnos nuevos», los primeros turnos y «Importar» y «Cancelar»; sin páginas, se omite «(páginas X–Y)». «Importar» queda deshabilitado con «Elige un perfil para crear la sesión» hasta elegir perfil y muestra «Importando N turnos…» mientras crea. «Cancelar» no llama a la API.'
    violation: Prueba Vitest y de nivel 1 (0 filas tras cancelar).
    source: AC2.6.5; M7
  - id: BR7.8
    status: nuevo
    statement: 'Una sesión importada no admite turnos ni bloques, y la consola no ofrece esas acciones.'
    category: validation
    applies_to: [InterviewSessionRecord, Turn]
    trigger: POST /turns o /transcript sobre una importada; M4 de una importada
    logic: 'SI closed_to_new_turns es true por importación ENTONCES un turno o un bloque responden 409 session.closed_to_new_turns con 0 filas, y M4 no muestra la entrada de turnos, «Pegar transcripción» ni «Finalizar sesión».'
    violation: Prueba de nivel 1 y Vitest.
    source: AC2.6.4; M4 §6.2
  - id: BR7.9
    status: nuevo
    statement: 'El archivo importado no se guarda tal cual ni aparece en los logs, y las pruebas solo usan transcripciones sintéticas.'
    category: policy
    applies_to: [ImportPreview, ImportProblem]
    trigger: Toda importación
    logic: 'SI se importa un archivo ENTONCES se guardan solo los turnos y el consentimiento, nunca el archivo; los logs llevan solo session_id, el tamaño y el code, nunca texto del archivo ni mensajes de ImportProblem con texto. Los fixtures son sintéticos aunque declaren origen corpus; las entrevistas del piloto solo se importan en el Minikube local, nunca en Git ni en la CI.'
    violation: Prueba de nivel 1 con un canary en un turno (no aparece en los logs capturados) y la comprobación de nivel 0 de gitleaks y de la lista de fixtures.
    source: M7; project.md (Forbidden, datos reales); docs/iteracion2.md P7 = A; NFR10

  # BR8 — Modo final
  - id: BR8.1
    status: nuevo
    statement: 'El modo final se lanza en una sesión guiada finalizada o en una importada; en los demás casos se rechaza con un code por situación.'
    category: validation
    applies_to: [AnalysisRun, InterviewSessionRecord]
    trigger: POST /sessions/{id}/final-runs
    logic: 'Bajo el bloqueo de la sesión, en este orden: SI no hay ConsentRecord ENTONCES 409 session.consent_missing; SI blocked_code ENTONCES 409 session.blocked; SI hay retirada ENTONCES 409 session.consent_withdrawn; SI terminated ENTONCES 409 session.terminated; SI consolidated ENTONCES 409 session.consolidated (FD-U4-05); SI paused ENTONCES 409 session.paused; SI suspended ENTONCES 409 session.suspended; SI es guiada y no está finalized ENTONCES 409 session.not_finalized (precisión FD-U6-02); en todos, 0 filas. SI no ENTONCES sigue BR8.2.'
    violation: Prueba de nivel 1 por estado.
    source: AC2.7.1; AC2.7.5; FR4.9; C1 /final-runs
  - id: BR8.2
    status: nuevo
    statement: 'De dos lanzamientos simultáneos del modo final, uno crea la corrida y el otro recibe 409.'
    category: constraint
    applies_to: [AnalysisRun]
    trigger: POST /sessions/{id}/final-runs
    logic: 'SI, bajo el bloqueo exclusivo de la fila de la sesión, la última corrida final está queued o processing ENTONCES 409 run.final_in_progress y 0 filas; SI no ENTONCES BR8.3 y 202. M4 deja «Relanzar modo final» deshabilitado con «El modo final ya está en proceso» mientras la última corrida final está en cola o en proceso.'
    violation: Prueba de nivel 1 con dos POST simultáneos (un 202, un 409, una sola corrida nueva) y Vitest del botón.
    source: AC2.7.6; C1 /final-runs
  - id: BR8.3
    status: nuevo
    statement: 'Lanzar el modo final encola una corrida final sobre toda la transcripción y registra quién y cuándo.'
    category: policy
    applies_to: [AnalysisRun, RunStatusChange]
    trigger: POST /sessions/{id}/final-runs aceptado
    logic: 'SI se acepta ENTONCES en una transacción AnalysisRun (mode final, desde_turno el primer turno, hasta_turno el último, requested_by el dueño, requested_at) y su primer cambio de estado (null → queued, attempt 1, deadline_at con run_deadline_final_s, actor el dueño); tras confirmar se publica C2 con la entrada de C6 completa y modo final por la tubería de U4 y responde 202 con Run. Relanzar crea siempre una corrida nueva; cuenta la última por requested_at.'
    violation: Prueba de nivel 1 (actor y hora no nulos; la corrida anterior sigue en el registro).
    source: AC2.7.1; FR4.9; C1 Run; C2
  - id: BR8.4
    status: nuevo
    statement: 'Los hallazgos del modo final se unen a los de la sesión sin duplicar, y un hallazgo ya decidido conserva su estado y su historial.'
    category: constraint
    applies_to: [AnalysisRun]
    trigger: Ingesta del resultado de una corrida final
    logic: 'SI termina el modo final ENTONCES sus hallazgos pasan por la misma ingesta y la misma deduplicación por par no ordenado de (turno, cita normalizada en espacios) que los incrementales (U4 y propose de U5): un par ya presente, pendiente o decidido, no se repite ni vuelve a pendiente; dos citas casi iguales del mismo par de turnos cuentan como hallazgos distintos (límite declarado).'
    violation: Prueba de nivel 1 con un hallazgo incremental aceptado que el modo final repite (una sola sugerencia, aceptada, con su historial).
    source: AC2.7.2; FR4.9; C10 propose
  - id: BR8.5
    status: nuevo
    statement: 'Mientras el modo final procesa, la sesión se lee y se decide con normalidad.'
    category: policy
    applies_to: [AnalysisRun]
    trigger: Corrida final queued o processing
    logic: 'SI el modo final está en proceso ENTONCES GET de la sesión y la decisión sobre un hallazgo existente responden 200 sin esperar a la corrida; la franja muestra «Modo final en proceso», distinto de «Modo final terminado» y de «Modo final con error».'
    violation: Prueba de nivel 1 con un fake del ModelGateway que bloquea hasta que la prueba lo libera, y Vitest de los tres textos.
    source: AC2.7.3; FR3.4
  - id: BR8.6
    status: nuevo
    statement: 'Un modo final en error muestra su causa y se puede relanzar; la corrida anterior queda en el registro.'
    category: policy
    applies_to: [AnalysisRun]
    trigger: Última corrida final en error
    logic: 'SI la última corrida final termina en error ENTONCES la franja muestra «Modo final con error», la causa del code (catálogo de AC3.2.5) y «El analizador no pudo procesar la transcripción completa. Revisión manual requerida», con «Relanzar modo final»; relanzar sigue BR8.1–BR8.3 y crea una corrida nueva.'
    violation: Prueba de nivel 1 (dos corridas finales en el registro) y Vitest.
    source: AC2.7.4; CD-08
  - id: BR8.7
    status: nuevo
    statement: 'La franja del modo final muestra un estado con texto por situación, con la acción o el motivo de que no la haya.'
    category: policy
    applies_to: [RunProgress, AnalysisRun]
    trigger: M4, franja del modo final
    logic: 'Guiada sin finalizar: «No lanzado · disponible al finalizar la sesión». Sin corridas finales: «No lanzado» y «Lanzar modo final». En cola o en proceso: «Modo final en cola» o «Modo final en proceso» con BR5.1, y «Lanzado por <usuario> el <fecha>». Terminado: «Modo final terminado» y N hallazgos nuevos. Con error: BR8.6. Cancelado: «Modo final cancelado» y «Relanzar modo final» si la sesión lo admite. Pausada, suspendida, terminada, bloqueada o con la retirada registrada: el botón deshabilitado (enfocable) con el motivo («Análisis en pausa: reanuda el análisis para lanzar el modo final», «Sesión suspendida: reanúdala para lanzar el modo final», «Sesión terminada», el de U4 para la bloqueada, «Consentimiento retirado: no se analiza nada más en esta sesión»). Consolidada: el último estado, sin acciones.'
    violation: Prueba Vitest por estado.
    source: AC2.7.3; AC2.7.5; M4 §6.8; precisión FD-U6-16

  # BR9 — Pausa, terminación y retirada del consentimiento
  - id: BR9.1
    status: nuevo
    statement: 'Pausar el análisis pasa la sesión de abierta a en pausa y cancela lo encolado sin llamar a ningún modelo.'
    category: policy
    applies_to: [InterviewSessionRecord, SessionStatusChange, AnalysisRun]
    trigger: PATCH /sessions/{id}/analysis con paused true («Pausar análisis»)
    logic: 'SI la sesión está open y sin retirada ENTONCES, con el orden usuario → sesión y change_cursor.bump, status → paused, SessionStatusChange (open → paused, actor el dueño) y BR9.6 sobre sus corridas queued o processing, y responde 200 con SessionView. SI no está open ENTONCES 409 con el code de su situación (session.paused, session.suspended, session.finalized, session.terminated, session.consolidated, session.blocked; session.consent_withdrawn con retirada) y 0 filas.'
    violation: Prueba de nivel 1 con corridas en cola (el fake registra 0 llamadas nuevas tras pausar).
    source: AC15.2.1; VE-10; DD-06 (b); C1 PATCH /analysis
  - id: BR9.2
    status: nuevo
    statement: 'En pausa los turnos se guardan sin encolar; al reanudar el análisis se encola una sola corrida que cubre lo que quedó sin analizar.'
    category: policy
    applies_to: [InterviewSessionRecord, AnalysisRun, Turn]
    trigger: Turnos y bloques en pausa; PATCH /sessions/{id}/analysis con paused false («Reanudar análisis»)
    logic: 'SI la sesión está paused ENTONCES un turno o un bloque se guardan y responden 202 sin run. SI llega paused false y la sesión no está paused ENTONCES 409 session.not_paused (precisión FD-U6-01), o session.consent_withdrawn con retirada; SI está paused ENTONCES status → open con SessionStatusChange (paused → open, actor el dueño) y, en una guiada, si hay algún turno TEST cuya última corrida incremental que lo cubre está cancelled o que no tiene ninguna, una sola corrida incremental con desde_turno = el primero de esos turnos y hasta_turno = el último turno TEST de la sesión (precisión FD-U6-15). Un tramo en error conserva su «Reintentar tramo» y no entra. En una importada no se encola nada: el analista relanza el modo final.'
    violation: Prueba de nivel 1 (dos turnos en pausa, reanudar, una sola corrida con su tramo; un tramo en error no se reencola).
    source: AC15.2.1; C1 PATCH /analysis; FR4.9
  - id: BR9.3
    status: nuevo
    statement: 'Terminar la sesión la cierra a turnos nuevos y cancela lo encolado; después se puede consolidar.'
    category: policy
    applies_to: [InterviewSessionRecord, SessionStatusChange, AnalysisRun]
    trigger: POST /sessions/{id}/terminate tras el diálogo de confirmación
    logic: 'SI la sesión está open, paused, suspended o blocked ENTONCES status → terminated, closed_to_new_turns true, SessionStatusChange (→ terminated, actor el dueño) y BR9.6; blocked_code se conserva; responde 200. SI está finalized ENTONCES 409 session.finalized; SI terminated ENTONCES 409 session.terminated; SI consolidated ENTONCES 409 session.consolidated; 0 filas. Después, un turno, un bloque, el modo final y el reintento responden 409 session.terminated.'
    violation: Prueba de nivel 1 (turno tras terminar 409 sin filas; el fake con 0 llamadas nuevas).
    source: AC15.2.2; VE-10; DD-06 (b); C1 /terminate
  - id: BR9.4
    status: nuevo
    statement: 'Registrar la retirada del consentimiento guarda quién y cuándo, cierra la sesión a turnos nuevos y cancela lo encolado; no cambia el estado.'
    category: policy
    applies_to: [ConsentRecord, InterviewSessionRecord, AnalysisRun]
    trigger: POST /sessions/{id}/consent-withdrawal tras el diálogo de confirmación
    logic: 'SI la sesión no está consolidated y no tiene retirada ENTONCES, con change_cursor.bump, ConsentRecord.withdrawn_at = hora del servidor y withdrawn_by = el dueño, closed_to_new_turns true y BR9.6 sobre las corridas queued o processing, incluida la final; el status no cambia y responde 200 con consent_withdrawn_at. SI ya hay retirada ENTONCES 409 session.consent_withdrawn y 0 filas; SI está consolidated ENTONCES 409 session.consolidated. Lo ya analizado se conserva; solo lo borra la retención (U13).'
    violation: Prueba de nivel 1 (una sola retirada; la segunda 409 sin filas; la corrida final en cola queda cancelled).
    source: AC15.2.3; VE-10 (a); DD-06 (a); A-4; C1 /consent-withdrawal; UG-03
  - id: BR9.5
    status: nuevo
    statement: 'Después de la retirada no se encola ni se analiza ninguna corrida, tampoco el modo final ni un reintento.'
    category: policy
    applies_to: [AnalysisRun]
    trigger: Todo encolado posterior a la retirada
    logic: 'SI withdrawn_at no es nulo ENTONCES un turno o un bloque responden 409 session.consent_withdrawn, y el modo final, el reintento y la reanudación del análisis también, con 0 filas; ningún turno posterior entra en una corrida porque no se aceptan. La sesión se puede terminar, finalizar y consolidar (U7); el reporte declara la retirada con su hora y los tramos sin evaluar (precisión FD-U6-11).'
    violation: Prueba de nivel 1 con el fake (0 llamadas nuevas tras la retirada; modo final y reintento 409).
    source: P6 = A; AC15.2.3; VE-10 (a); C1 /consent-withdrawal; precisión FD-U6-10
  - id: BR9.6
    status: nuevo
    statement: 'Pausar, terminar y retirar el consentimiento cancelan las corridas en cola o en proceso con la clave de Redis de CD-06.'
    category: policy
    applies_to: [AnalysisRun]
    trigger: BR9.1, BR9.3 y BR9.4
    logic: 'SI se cancela ENTONCES, en la misma transacción, cada corrida queued o processing de la sesión recibe su cambio a cancelled (actor el dueño) y, tras confirmar, se escribe veridicus:run-cancelled:{run_id} con vencimiento deadline_at + cancel_key_margin_s, con el mecanismo de cancelación de U4; el trabajador no llama a nada más y un resultado que llegue se descarta. SI la escritura de la clave falla ENTONCES la transición ya confirmada se mantiene y la clave se reintenta en la reconexión, como tras un reinicio de Redis; la regla del plazo vencido cubre el resto.'
    violation: Prueba de nivel 1 de cada acción con el fake (0 llamadas nuevas) y con Redis cortado al escribir la clave.
    source: CD-06; C2 (cancelación); AC15.2.1; AC15.2.2; unit-of-work U6 (Restricciones)
  - id: BR9.7
    status: nuevo
    statement: 'Los estados del ciclo de vida se leen con texto en la cabecera de M4 y en la fila de M1.'
    category: policy
    applies_to: [SessionListItem, InterviewSessionRecord]
    trigger: M4 y M1
    logic: 'open «Abierta», paused «Análisis en pausa», suspended «Suspendida», finalized «Finalizada», terminated «Sesión terminada», blocked «Bloqueada», consolidated «Consolidada»; con retirada se añade «· consentimiento retirado» y la cabecera de M4 dice «Consentimiento retirado el <fecha y hora>. No se analiza nada más en esta sesión». Cada estado lleva icono decorativo y nunca se distingue solo por color.'
    violation: Prueba Vitest por estado.
    source: AC15.2.4; AC2.5.3; AC5.6.3; mockups revisión 3 (estado en M1); precisión FD-U6-16
  - id: BR9.8
    status: nuevo
    statement: 'La máquina de la sesión admite solo las transiciones de functional-spec §3; finalizar y consolidar las ejecuta U7.'
    category: constraint
    applies_to: [InterviewSessionRecord, SessionStatusChange]
    trigger: Toda escritura de status
    logic: 'SI una escritura pide una transición que no está en la tabla de functional-spec §3 ENTONCES se rechaza con el code de la situación y 0 filas. U6 deja permitidas open, paused, suspended y blocked → finalized (ruta de U7), y finalized y terminated → consolidated (U7); terminated no es final (precisión FD-U6-12). blocked_code nunca vuelve a nulo.'
    violation: Prueba de nivel 0 de la tabla de transiciones con 100 % de ramas.
    source: C1 SessionStatus y /terminate («se puede consolidar después»); FD-U4-18; unit-of-work U6 (Límites)

  # BR10 — Solo el dueño
  - id: BR10.1
    status: nuevo
    statement: 'Solo el dueño de la sesión pega, lanza el modo final, late, reanuda, pausa, termina o registra la retirada.'
    category: authorization
    applies_to: [InterviewSessionRecord]
    trigger: Rutas /transcript, /final-runs, /heartbeat, /resume, /analysis, /terminate y /consent-withdrawal
    logic: 'SI quien llama es otro analista ENTONCES ConsoleApi responde 403 session.not_owner antes de delegar; SI es admin o investigador ENTONCES 403 auth.forbidden; en todos, 0 filas. La importación exige el rol analista y su autor queda como dueño.'
    violation: Prueba de nivel 1 por ruta con otro analista y con el admin.
    source: AC5.4.1; AC5.4.3; AC7.1.5; ADR-009; C1 x-veridicus-owner-only
  - id: BR10.2
    status: nuevo
    statement: 'Una sesión ajena se ve en solo lectura, sin acciones del ciclo de vida.'
    category: authorization
    applies_to: [InterviewSessionRecord]
    trigger: M4 de una sesión de otro usuario
    logic: 'SI el usuario no es el dueño ENTONCES M4 muestra «Sesión de <usuario>. Solo lectura» y no ofrece «Pegar transcripción», «Lanzar modo final», «Relanzar modo final», «Pausar análisis», «Reanudar análisis», «Terminar sesión» ni «Registrar retirada del consentimiento», ni el diálogo de reanudación.'
    violation: Prueba Vitest y de nivel 1.
    source: AC5.4.2; M1; M4
```

## Resumen

| Grupo | Reglas | Estado | Qué protege |
|---|---|---|---|
| BR1 Versiones | BR1.1–BR1.4 | Retirado | — (cambio 01) |
| BR2 Bloque pegado | BR2.1, BR2.3–BR2.7 (BR2.2 Retirado) | cambia / nuevo | Divisiones ambiguas, bloques que superan el catálogo, corridas duplicadas o perdidas, bloques sobre sesiones cerradas |
| BR3 Lista | BR3.1–BR3.5 | cambia / nuevo | Encontrar y retomar sesiones; roles; contrato C1 |
| BR4 Latido y reanudación | BR4.1–BR4.6 | cambia | Re-suspensión tras reanudar (R-01), trabajo perdido o duplicado, auditoría |
| BR5 Progreso (SHOULD) | BR5.1–BR5.3 | cambia / nuevo | Dudar si el sistema se colgó, sin cambiar contratos (P7 = B) |
| BR6 Accesibilidad | BR6.1–BR6.2 | cambia / nuevo | Estados solo por color, flujos sin teclado, anuncios en exceso |
| BR7 Importación | BR7.1–BR7.9 | nuevo | Archivos fuera del contrato, límites, consentimiento (P5 = A), perfiles, datos reales |
| BR8 Modo final | BR8.1–BR8.7 | nuevo | Lanzamientos fuera de estado o duplicados, hallazgos repetidos, sesión bloqueada mientras analiza |
| BR9 Pausa, terminación y retirada | BR9.1–BR9.8 | nuevo | VE-10: nada se analiza tras la retirada (P6 = A); cancelación sin llamadas |
| BR10 Solo el dueño | BR10.1–BR10.2 | nuevo | Acciones de otro analista, del admin o del investigador |

Cuenta: 53 reglas en el bloque; 5 retiradas (BR1.1–BR1.4, BR2.2), 17 que cambian o siguen (BR3.3 sin
cambios) y 31 nuevas.
