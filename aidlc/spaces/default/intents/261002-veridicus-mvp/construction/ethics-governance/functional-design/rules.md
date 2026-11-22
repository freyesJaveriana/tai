# Reglas de negocio — U13 ethics-governance

**Revisión 1 (2026-11-22), primera pasada.** Es una unidad nueva del cambio 01 (DT27) y de la adenda 02, y no
tiene reglas previas. Se basa en las respuestas de `functional-design-questions.md` y en los once puntos de
su sección 2:
- P1 = B: «Más tarde» y franja persistente;
- P2 = A: plazo por defecto igual al máximo;
- P3 = A: el plazo cuenta desde la creación;
- P4 = A: reducen el plazo el dueño y el `admin`, desde M4;
- P5 = A: el Job borra con el reloj real, y `--as-of` solo vale con `--dry-run`;
- P6 = A: un reporte sin sesión se borra por antigüedad;
- P7 = A: lo registrado se consulta con un comando de solo lectura.

**Insumos.** Son los mismos de `entities.md`:
- `inception/units-generation/unit-of-work.md` (unit-of-work) y `unit-of-work-story-map.md`
  (unit-of-work-story-map);
- `inception/requirements-analysis/requirements.md` (requirements) y `requirements-adenda-02.md`;
- `inception/domain-design/components.md` (components);
- `inception/contract-design/contract-summary.md` (contract-summary);
- mockups §11 y los diseños de U3 a U9.

**Demostración sin compuertas (ADR-016, DD-01 a DD-05, punto 4 de B13).** Ninguna regla de este archivo
rechaza abrir ni crear una sesión, ni deja la consola inutilizable. Los únicos rechazos están en las rutas
propias de U13: un valor de plazo fuera de rango, una petición mal formada o un rol sin permiso.

Los niveles de prueba (N0 a N3) siguen `team.md` (Testing Posture). Los `code`, los mensajes y las cifras
que aún no están en C1, C25 ni `interaction-spec.md` se proponen en la tabla de precisiones de
`functional-spec.md` (§10). Las pruebas que protegen datos sensibles se escriben primero y en rojo, como
las de los contratos de datos (Testing Posture, Ordering): son las de BR3.6, BR3.9, BR5.2, BR5.3, BR5.5,
BR5.6 y BR5.8.

## Reglas (fuente de verdad)

```yaml
rules:
  # BR1 — Reconocimiento de las reglas de uso (US15.1, VE-04, DD-01)
  - id: BR1.1
    statement: El texto de las reglas de uso es un archivo versionado de IntegrityPolicy que ConsoleApi sirve con su versión.
    category: policy
    applies_to: [UsageRulesText]
    trigger: Al arrancar session-api y al pedir el texto la consola
    logic: SI el archivo usage-rules.v1.yaml existe, cumple su esquema y trae exactamente los tres puntos de AC15.1.1 ENTONCES ConsoleApi lo entrega con su versión y la consola los muestra en ese orden; SI falta o no es válido ENTONCES session-api no arranca y el log nombra el archivo.
    violation: Prueba de nivel 0 del esquema y de los tres puntos; prueba de arranque con el archivo ausente.
    source: AC15.1.1; VE-04; C8 (FD-U13-02); configuración faltante impide arrancar (team.md, Code Style)
  - id: BR1.2
    statement: El estado del reconocimiento se calcula con el último reconocimiento del usuario, la versión vigente y el reloj inyectado.
    category: calculation
    applies_to: [AcknowledgementState, AnalystAcknowledgement]
    trigger: GET /auth/me y la apertura de una sesión en la consola
    logic: SI el usuario no tiene reconocimientos ENTONCES missing; SI la versión del último es distinta de la vigente ENTONCES text_changed (aunque no hayan pasado 90 días); SI no, y ahora − at ≤ acknowledgement_validity_days × 24 h ENTONCES valid; SI no ENTONCES expired. El día 90 sigue vigente y el día 91 no.
    violation: Prueba de nivel 1 con reloj simulado en el día 90 (valid) y en el 91 (expired), y con la versión 2 a los 10 días (text_changed).
    source: AC15.1.3; AC15.1.4; VE-04; C1 (AcknowledgementStatus); C25 (FD-U13-03)
  - id: BR1.3
    statement: «Reconozco estas reglas» registra una fila de solo inserción con usuario, hora UTC del servidor y versión del texto.
    category: validation
    applies_to: [AnalystAcknowledgement]
    trigger: POST /acknowledgements
    logic: SI el principal es analista, trae el token CSRF y text_version es la versión vigente ENTONCES se inserta la fila y se responde 201 con el estado valid; SI text_version no es la vigente (el texto cambió mientras el diálogo estaba abierto) ENTONCES 422 ethics.text_version_outdated sin filas, y la consola vuelve a pedir el texto; varios reconocimientos del mismo usuario son filas distintas.
    violation: Prueba de nivel 1 que lee la fila (usuario, hora, versión) y prueba con una versión vieja.
    source: AC15.1.2; VE-04; C1 (/acknowledgements); FR1.3
  - id: BR1.4
    statement: El diálogo modal aparece al entrar a la consola y al abrir una sesión cuando el estado no es valid.
    category: policy
    applies_to: [AcknowledgementState]
    trigger: Tras iniciar sesión (M0), antes de la pantalla de destino, y al abrir M4
    logic: SI el usuario es analista y el estado es missing, expired o text_changed ENTONCES se abre el diálogo con los tres puntos y la versión; con expired lleva arriba el aviso «Tu reconocimiento venció. Vuelve a leer las reglas de uso»; con text_changed, «Las reglas de uso cambiaron»; SI el estado es valid ENTONCES no aparece.
    violation: Prueba Vitest por cada estado y en los dos momentos.
    source: AC15.1.1; AC15.1.3; AC15.1.4; mockups (precisión de la revisión 3, diálogo después de M0)
  - id: BR1.5
    statement: «Más tarde» cierra el diálogo y deja una franja persistente con «Reconocer»; la consola sigue usable (P1 = B).
    category: policy
    applies_to: [AcknowledgementState]
    trigger: El analista pulsa «Más tarde» o Escape en el diálogo
    logic: SI el analista cierra el diálogo sin reconocer ENTONCES la consola muestra bajo el aviso de VE-01 la franja «No has reconocido las reglas de uso» con el botón «Reconocer», que reabre el diálogo; la franja sigue en todas las pantallas hasta que el estado sea valid; el diálogo vuelve a abrirse solo en el siguiente inicio de sesión o en la siguiente apertura de sesión.
    violation: Prueba Vitest de la franja y de que la lista de sesiones y M4 siguen operables tras «Más tarde».
    source: AC15.1.1 (FD-U13-01); DD-01; respuesta P1 = B
  - id: BR1.6
    statement: Ningún estado del reconocimiento rechaza abrir ni crear sesiones.
    category: policy
    applies_to: [AcknowledgementState]
    trigger: Cualquier ruta de sesión con un reconocimiento missing, expired o text_changed
    logic: SI el estado no es valid ENTONCES la ruta responde igual que con valid (sin 403 ni código ethics.acknowledgement_required) y la consola solo muestra el diálogo o la franja.
    violation: Prueba de nivel 1 que crea y abre una sesión con el reconocimiento vencido (reloj simulado, día 91) y sin reconocimiento.
    source: AC15.1.1; AC15.1.3; DD-01; ADR-016
  - id: BR1.7
    statement: Solo el rol analista reconoce y ve el diálogo; admin e investigador no.
    category: authorization
    applies_to: [AnalystAcknowledgement, AcknowledgementState]
    trigger: POST /acknowledgements y GET /auth/me
    logic: SI el principal es admin o investigador ENTONCES POST /acknowledgements responde 403 auth.forbidden sin filas, /auth/me no trae acknowledgement y la consola no muestra ni el diálogo ni la franja.
    violation: Prueba de nivel 1 con los dos roles y prueba Vitest.
    source: C1 (x-veridicus-roles de /acknowledgements); FR1.2

  # BR2 — Registro de acceso (US15.6, VE-11, DD-02; puerto AccessLog de C23)
  - id: BR2.1
    statement: El adaptador real de AccessLog lo aporta EthicsGovernance, y ConsoleApi lo cablea al arrancar en lugar del adaptador por defecto.
    category: policy
    applies_to: [AccessLogEntry]
    trigger: Arranque de session-api
    logic: SI el módulo EthicsGovernance está presente ENTONCES ConsoleApi cablea su adaptador, deja de escribir el aviso «registro de acceso no configurado» y /readyz deja de informar access_log not_configured; SI el adaptador no puede comprobar su tabla al arrancar ENTONCES session-api no arranca. EthicsGovernance no importa nada de ConsoleApi.
    violation: Prueba de nivel 1 de que el adaptador cableado es el real y /readyz no trae not_configured; import-linter prohíbe ethics_governance → console_api.
    source: AC15.8.2; C23; UG-09; ADR-016
  - id: BR2.2
    statement: Cada registro es una fila sin texto con usuario, tipo de recurso, ID, hora UTC y, solo en una exportación, su SHA-256.
    category: validation
    applies_to: [AccessLogEntry]
    trigger: AccessLog.record
    logic: SI resource_type es session, suggestion o report_version ENTONCES export_sha256 debe ser nulo; SI es report_export ENTONCES export_sha256 es obligatorio y tiene 64 hexadecimales; SI no se cumple ENTONCES se lanza un error de programación (nunca se guarda una fila incoherente); la hora la pone el servidor.
    violation: Prueba de nivel 1 que abre una sesión, una sugerencia y un reporte, exporta, y consulta las cuatro filas.
    source: AC15.6.1; AC15.8.2; VE-11; A-3; NFR10
  - id: BR2.3
    statement: El registro se escribe dentro de la transacción de quien llama, con su timeout, y un fallo se propaga como error para que quien llama decida.
    category: constraint
    applies_to: [AccessLogEntry]
    trigger: AccessLog.record dentro de una petición
    logic: SI la inserción falla o vence su plazo ENTONCES el adaptador lanza la excepción de registro de acceso de la jerarquía común, sin reintentar; en una lectura, ConsoleApi responde igual y lo avisa con IDs (contrato de C23 y F11 de U3); en la exportación, la ruta revierte y responde 503 report.export_not_recorded (diseño de U7). U13 no decide esas respuestas.
    violation: Prueba de nivel 1 con la tabla bloqueada; la lectura responde 200 y la exportación 503 sin bytes.
    source: AC15.8.2; C23; UG-09
  - id: BR2.4
    statement: El registro de acceso es de solo inserción, sin claves foráneas, y sobrevive a la retención.
    category: constraint
    applies_to: [AccessLogEntry]
    trigger: UPDATE o DELETE sobre la tabla
    logic: SI veridicus_app o veridicus_retention intentan UPDATE o DELETE ENTONCES la base lo rechaza; los IDs no tienen clave foránea, así que borrar la sesión no toca el registro.
    violation: Prueba de nivel 1 con los dos usuarios y prueba de que, tras el Job, las filas de la sesión borrada siguen.
    source: AC15.6.2; VE-11; NFR11; A-2; C24
  - id: BR2.5
    statement: El adaptador nunca escribe texto en el log, solo IDs y el tipo de recurso.
    category: constraint
    applies_to: [AccessLogEntry]
    trigger: Cualquier log del adaptador
    logic: SI el adaptador registra un aviso o un error ENTONCES el log lleva solo resource_type, resource_id, user_id y el code; nunca contenido del recurso.
    violation: Prueba de nivel 1 que captura los logs del fallo de BR2.3 y busca un turno sintético con canario.
    source: NFR10; team.md (Code Style, logs sin datos sensibles)

  # BR3 — Reporte de problemas (US15.3, VE-15, DD-04)
  - id: BR3.1
    statement: El formulario ofrece exactamente las seis categorías de AC15.3.1 y una nota opcional.
    category: validation
    applies_to: [ProblemReport]
    trigger: Abrir el formulario y POST /problem-reports
    logic: SI la categoría no es una de harmful_finding («Hallazgo dañino»), improper_vocabulary («Vocabulario indebido»), mismatched_quote («Cita que no corresponde»), interviewee_distress («Malestar de la persona entrevistada»), anonymization_failure («Falla de anonimización») o misuse («Uso indebido») ENTONCES 422 validation.invalid_request sin filas; la consola las muestra en ese orden y nada más.
    violation: Prueba Vitest de los seis rótulos y prueba de nivel 1 con una categoría desconocida.
    source: AC15.3.1; VE-15; C1 (/problem-reports)
  - id: BR3.2
    statement: El formulario es un panel no modal que se abre desde la cabecera de todas las pantallas o desde el menú de una tarjeta, que precarga el ID.
    category: policy
    applies_to: [ProblemReport]
    trigger: «Reportar un problema» en la cabecera o en el menú de una tarjeta de M4
    logic: SI se abre desde una tarjeta ENTONCES suggestion_id y session_id quedan precargados y visibles como «Hallazgo de la sesión <ID corto>»; SI se abre desde M4 o M5 sin tarjeta ENTONCES se precarga session_id; SI se abre desde otra pantalla ENTONCES no hay sesión; el panel no atrapa el foco y deja leer la transcripción.
    violation: Prueba Vitest de los tres orígenes y de que el foco no queda atrapado.
    source: AC15.3.1; mockups §11 (US15.3); regla de project.md (panel no modal)
  - id: BR3.3
    statement: Envían reportes el analista y el admin, con el token CSRF; el investigador no.
    category: authorization
    applies_to: [ProblemReport]
    trigger: POST /problem-reports
    logic: SI el principal es investigador ENTONCES 403 auth.forbidden y la consola no muestra el enlace; SI falta el token CSRF ENTONCES 403 auth.csrf; SI no ENTONCES se guarda con reported_by y reported_at del servidor.
    violation: Prueba de nivel 1 por rol y sin token.
    source: AC15.3.2; C1 (x-veridicus-roles); FR1.2; FR1.3
  - id: BR3.4
    statement: Si llega suggestion_id, session_id se deriva de la sugerencia; los dos deben coincidir y el usuario debe poder ver esa sesión.
    category: validation
    applies_to: [ProblemReport]
    trigger: POST /problem-reports con session_id o suggestion_id
    logic: SI llega suggestion_id ENTONCES session_id = la sesión de la sugerencia; SI también llegó session_id y no coincide ENTONCES 422 problem_report.ids_mismatch sin filas; SI la sesión o la sugerencia no existen ENTONCES 404 con el mismo code que la ruta de la sesión; SI el principal no es el dueño ni admin ENTONCES 403 igual que la ruta de la sesión. ConsoleApi hace la verificación de dueño (ADR-009).
    violation: Prueba de nivel 1 de la derivación, del desacuerdo, del 404 y del analista ajeno.
    source: AC15.3.2; UG-01; ADR-009; C1 (FD-U13-06)
  - id: BR3.5
    statement: La nota es opcional y tiene un tope de caracteres del catálogo de límites.
    category: validation
    applies_to: [ProblemReport]
    trigger: POST /problem-reports
    logic: SI note falta o está vacía tras quitar espacios ENTONCES se guarda nula; SI supera problem_report_note_max_chars ENTONCES 422 limits.exceeded sin filas; la consola cuenta los caracteres y deshabilita «Enviar» con su motivo al pasar el tope.
    violation: Prueba de nivel 1 sin nota, con nota vacía y con el tope + 1.
    source: AC15.3.1 (FD-U13-06); C25 (FD-U13-03)
  - id: BR3.6
    statement: El servidor marca testimony_warning si la nota trae testimony_warning_words o más palabras seguidas de un turno de la sesión, y guarda la fila igual.
    category: calculation
    applies_to: [ProblemReport]
    trigger: POST /problem-reports con nota y con sesión
    logic: SI hay sesión y nota ENTONCES se normalizan espacios en la nota y en cada turno de la sesión (los dos papeles), se parten en palabras por espacios y se busca una secuencia de testimony_warning_words (8) o más palabras idénticas y seguidas en algún turno; SI aparece ENTONCES testimony_warning = true; SI no ENTONCES false; en ningún caso se responde 422 ni se cambia la nota. Los turnos se leen por el puerto EthicsSessionPort de InterviewSession, sin copiar su texto fuera de la petición.
    violation: Prueba de nivel 1 con 8 palabras seguidas de un turno sintético (true), con 7 (false), con 8 de dos turnos distintos (false) y con espacios distintos (true); el mismo conjunto de ejemplos lo usa la prueba de la consola (BR3.7).
    source: AC15.3.2; AC15.3.3; VE-15; DD-04; C25 (testimony_warning_words); regla de verificación de citas del piloto (solo espacios)
  - id: BR3.7
    statement: La consola avisa antes de enviar con la misma especificación, y permite enviar igual.
    category: policy
    applies_to: [ProblemReport]
    trigger: «Enviar» en el panel, con la sesión abierta en M4
    logic: SI la comprobación local con los turnos ya cargados encuentra la coincidencia ENTONCES el panel muestra «Quita el texto del testimonio de la nota», marca el tramo coincidente de la nota y cambia el botón a «Enviar igual»; SI el analista envía igual ENTONCES la fila se guarda con testimony_warning = true y el panel muestra «Reporte enviado»; fuera de M4 no hay comprobación local y manda el servidor; si el servidor marca true y la consola no avisó, se muestra el aviso tras guardar.
    violation: Prueba Vitest con los mismos ejemplos de BR3.6 y prueba de nivel 1 de «Enviar igual».
    source: AC15.3.3; DD-04; punto 5 de la sección 2
  - id: BR3.8
    statement: Un reporte sin sesión se guarda con su nota y con el aviso fijo, sin compararla con turnos.
    category: policy
    applies_to: [ProblemReport]
    trigger: POST /problem-reports sin session_id ni suggestion_id
    logic: SI no hay sesión ENTONCES el panel muestra siempre «No incluyas texto del testimonio en la nota», la fila se guarda con session_id nulo y testimony_warning = false, y queda sujeta al borrado por antigüedad (BR5.8).
    violation: Prueba de nivel 1 desde M1 y prueba Vitest del aviso fijo.
    source: AC15.3.2; respuesta P6 = A (FD-U13-07); VE-15
  - id: BR3.9
    statement: La nota nunca aparece en los logs, en las métricas ni en un Problem Details.
    category: constraint
    applies_to: [ProblemReport]
    trigger: Cualquier log o error de POST /problem-reports
    logic: SI se registra un log o se responde un error ENTONCES solo llevan el code, problem_report_id, session_id, suggestion_id, la categoría y testimony_warning; nunca la nota ni un fragmento de turno.
    violation: Prueba de nivel 1 con una nota con canario que captura logs y respuestas de error y busca el canario.
    source: NFR10; DD-04; team.md (Code Style, logs sin datos sensibles)

  # BR4 — Plazo de retención (US15.7, VE-12, DD-03)
  - id: BR4.1
    statement: El plazo es un entero de días entre retention_min_days y retention_max_days del catálogo; fuera de ese rango se rechaza sin filas.
    category: validation
    applies_to: [RetentionTerm]
    trigger: POST /sessions, POST /sessions/import y PATCH /sessions/{id}/retention
    logic: SI retention_days > retention_max_days (90) ENTONCES 422 retention.above_maximum; SI < retention_min_days (1) ENTONCES 422 retention.below_minimum; SI no es un entero ENTONCES 422 validation.invalid_request; en todos los casos no se crean filas. ConsoleApi valida con EthicsGovernance antes de delegar en InterviewSession.
    violation: Prueba de nivel 1 con 30 (se acepta), 120 (above_maximum, 0 filas), 0 (below_minimum) y 90 (se acepta).
    source: AC15.7.1; VE-12; C25 (FD-U13-03); C1 (FD-U13-04)
  - id: BR4.2
    statement: Si no llega plazo, se usa el máximo del catálogo; la consola lo muestra relleno (P2 = A).
    category: calculation
    applies_to: [RetentionTerm]
    trigger: Crear o importar una sesión sin retention_days
    logic: SI falta retention_days ENTONCES se guarda retention_max_days; M3 y M7 muestran el campo «Plazo de retención (días)» relleno con el máximo y la ayuda «Máximo <N> días. Después solo se puede reducir».
    violation: Prueba de nivel 1 sin el campo (se guarda 90) y prueba Vitest del campo relleno.
    source: AC15.7.1; VE-12 («90 días como máximo por defecto»); respuesta P2 = A
  - id: BR4.3
    statement: El plazo cuenta desde la creación de la sesión (P3 = A).
    category: calculation
    applies_to: [RetentionTerm]
    trigger: Crear, importar o reducir
    logic: SI se fija o se reduce el plazo ENTONCES retention_until = created_at de la sesión + retention_days × 24 h, sea cual sea el estado de la sesión; no se recalcula al finalizar, terminar, consolidar ni al retirar el consentimiento.
    violation: Prueba de nivel 1 de que finalizar o terminar no cambia retention_until.
    source: AC15.7.2; VE-12; respuesta P3 = A
  - id: BR4.4
    statement: Un plazo fijado solo se reduce, y lo reducen el dueño de la sesión o un admin, que quedan registrados (P4 = A).
    category: authorization
    applies_to: [RetentionTerm, RetentionChange]
    trigger: PATCH /sessions/{id}/retention
    logic: SI el principal no es el analista dueño ni admin ENTONCES 403 igual que la ruta de la sesión; SI falta el token CSRF ENTONCES 403 auth.csrf; SI el nuevo vencimiento es mayor o igual que el efectivo ENTONCES 422 retention.cannot_extend sin filas; SI es menor ENTONCES, en una transacción con el orden sesión primero, InterviewSession guarda retention_days y retention_until por el puerto EthicsSessionPort, sube el change_cursor y EthicsGovernance inserta RetentionChange con el antes, el después, el actor y la hora. Un vencimiento ya pasado es válido, y la sesión queda vencida para el próximo Job.
    violation: Prueba de nivel 1 de ampliar (422), igualar (422), reducir (fila con quién y cuándo), un analista ajeno (403) y un admin (200).
    source: AC15.7.3; VE-12; respuesta P4 = A; ADR-009 (C1, FD-U13-05)
  - id: BR4.5
    statement: Una sesión con el plazo vacío se lee como creación más el máximo del catálogo, sin escribirlo (P2 = A).
    category: calculation
    applies_to: [RetentionTerm, RetentionCandidate]
    trigger: El Job, la cabecera de M4 y PATCH /sessions/{id}/retention sobre una sesión creada antes de U13
    logic: SI retention_days es nulo ENTONCES el plazo efectivo es retention_max_days y el vencimiento created_at + máximo; la cabecera dice «Plazo de retención <N> días (por defecto)»; el acta usa la regla session_default_term_expired; una reducción escribe los dos campos por primera vez.
    violation: Prueba de nivel 1 con una sesión de plazo nulo vencida (reloj simulado) que se borra con esa regla.
    source: respuesta P2 = A; FD-U4-22 (campos vacíos hasta U13)
  - id: BR4.6
    statement: La cabecera de M4 muestra el plazo y su vencimiento; «Reducir plazo» solo aparece para el dueño y el admin.
    category: policy
    applies_to: [RetentionTerm]
    trigger: Dibujar la cabecera de M4
    logic: SI el usuario es el dueño o admin ENTONCES ve «Plazo de retención <N> días (hasta DD/MM/AAAA)» y el botón «Reducir plazo», que abre un diálogo modal con el número de días, la ayuda «Solo puedes reducirlo. No se puede deshacer» y «Cancelar»/«Reducir»; SI es otro analista en solo lectura ENTONCES ve el plazo sin el botón.
    violation: Prueba Vitest por rol y del diálogo.
    source: AC15.7.3; respuesta P4 = A; mockups §11 (US15.7) (FD-U13-05)

  # BR5 — Job de retención (US15.7, VE-12, A-2, DD-03; C24)
  - id: BR5.1
    statement: El Job es un artefacto revisable que lanza el humano, con el usuario veridicus_retention y el actor retention-job; el sistema nunca lo programa.
    category: policy
    applies_to: [RetentionJobRun, RetentionAct]
    trigger: Ejecución del Job
    logic: SI el Job corre ENTONCES usa la imagen de session-api con el comando de retención, la conexión de veridicus_retention desde un Secret que crea el humano y el actor de sistema retention-job; el manifiesto es un Job en deploy/ que entra por PR, nunca un CronJob; ningún workflow ni script lo aplica.
    violation: Comprobación estática de nivel 0 (sin CronJob de retención y sin kubectl apply en scripts ni workflows) y prueba de nivel 1 de que la conexión del Job es veridicus_retention.
    source: VE-12; A-2; DD-03; AUTONOMIA-01; FR1.3
  - id: BR5.2
    statement: El Job selecciona toda sesión cuyo vencimiento efectivo es menor o igual que as_of, sea cual sea su estado (P3 = A).
    category: calculation
    applies_to: [RetentionCandidate]
    trigger: Inicio del Job
    logic: SI retention_until (o created_at + máximo si es nulo) ≤ as_of ENTONCES la sesión es candidata, aunque esté abierta, pausada, suspendida, bloqueada, finalizada, terminada o consolidada; SI no ENTONCES no se toca.
    violation: Prueba de nivel 1 con reloj simulado y sesiones en cada estado, vencidas y no vencidas.
    source: AC15.7.2; VE-12; respuesta P3 = A
  - id: BR5.3
    statement: Para borrar, as_of es siempre el reloj real; --as-of solo se admite con --dry-run, que no borra ni escribe actas (P5 = A).
    category: constraint
    applies_to: [RetentionJobRun]
    trigger: Argumentos del Job
    logic: SI llega --as-of sin --dry-run ENTONCES el Job termina con código 2 antes de abrir la base; SI llega --dry-run ENTONCES lista por candidato el ID, la regla y los conteos por tabla (would_purge), sin cancelar corridas, sin borrar y sin escribir actas; SI no ENTONCES as_of = ahora real y borra. El reloj simulado de las pruebas se inyecta en el código, nunca por un argumento.
    violation: Prueba de nivel 0 de los argumentos y prueba de nivel 1 de que --dry-run deja 0 filas borradas y 0 actas.
    source: respuesta P5 = A; AUTONOMIA-01
  - id: BR5.4
    statement: Antes de borrar una sesión, el Job cancela sus corridas en cola; un resultado que llegue después se descarta.
    category: constraint
    applies_to: [RetentionCandidate]
    trigger: Borrado de una sesión candidata
    logic: SI la sesión tiene corridas en cola o en curso ENTONCES el Job pide a InterviewSession que escriba su clave de cancelación de Redis (CD-06) antes de borrar; un resultado que llegue después no encuentra la sesión y la ingesta lo descarta sin filas (FD-U13-13).
    violation: Prueba de nivel 1 con una corrida en cola; el fake registra 0 llamadas nuevas y un resultado tardío no crea filas.
    source: VE-12; CD-06; respuesta P3 = A
  - id: BR5.5
    statement: El borrado sigue el orden inverso de las referencias de C24, empezando por lo propio de EthicsGovernance.
    category: constraint
    applies_to: [ProblemReport, RetentionChange, RetentionAct]
    trigger: Borrado de una sesión candidata
    logic: ENTONCES, en este orden, (1) EthicsGovernance borra los ProblemReport de la sesión, incluidos los ligados por una sugerencia de la sesión, y sus RetentionChange; (2) ReviewReport.purge_session; (3) HumanReview.purge_session; (4) InterviewSession.purge_session, que incluye lo de U6, U8 y U9 y termina en InterviewSessionRecord. Cada PurgeReceipt aporta IDs y SHA-256 al acta; nunca texto.
    violation: Prueba de nivel 1 con reloj simulado que, tras el Job, no encuentra ninguna fila de la sesión fuera de RetentionAct, AccessLogEntry y el incidente de anonimización, incluidos los ProblemReport.
    source: AC15.7.2; VE-12; A-2; C24; UG-01
  - id: BR5.6
    statement: Cada sesión se borra en su propia transacción; si falla, se revierte esa sesión y el Job sigue con las demás.
    category: constraint
    applies_to: [RetentionJobRun, RetentionAct]
    trigger: Borrado de cada candidata
    logic: SI todo el borrado de la sesión y su acta salen bien ENTONCES se confirma la transacción y el resultado es purged; SI algo falla ENTONCES se revierte (la sesión y su acta quedan como estaban; un archivo ya borrado se verá como file_missing en el siguiente intento), el resultado es failed con su code y el Job sigue; al final, el código de salida es 1 si hubo algún failed y 0 si no.
    violation: Prueba de nivel 1 con un fallo inyectado en la segunda de tres sesiones; la 1 y la 3 se borran, la 2 queda entera y la salida es 1.
    source: AC15.7.2; A-2; team.md (Code Style, errores en fronteras)
  - id: BR5.7
    statement: Cada borrado deja un acta sin texto con los IDs, el SHA-256 de cada reporte y audio borrados, la regla aplicada y la hora.
    category: policy
    applies_to: [RetentionAct]
    trigger: Fin del borrado de una sesión o de una tanda de reportes sin sesión
    logic: ENTONCES se inserta RetentionAct con job_run_id, deleted_session_id, la regla (session_term_expired, session_default_term_expired o sessionless_problem_report_expired), el plazo y el vencimiento aplicados, deleted_ids por tabla, deleted_report_sha256s y deleted_audio con file_missing, executed_at y el actor retention-job, en la misma transacción del borrado.
    violation: Prueba de nivel 1 que compara el acta con los IDs y SHA-256 sembrados.
    source: AC15.7.2; VE-12; A-2; C24
  - id: BR5.8
    statement: Los reportes de problemas sin sesión se borran cuando su reported_at más el máximo del catálogo es menor o igual que as_of (P6 = A).
    category: policy
    applies_to: [ProblemReport, RetentionAct]
    trigger: Job, después de las sesiones
    logic: SI hay ProblemReport con session_id nulo y reported_at + retention_max_days ≤ as_of ENTONCES se borran todos en una transacción y se escribe un acta con deleted_session_id nulo y la regla sessionless_problem_report_expired; SI no hay ninguno ENTONCES no se escribe acta.
    violation: Prueba de nivel 1 con reloj simulado; uno de 91 días se borra con su acta, uno de 89 queda.
    source: respuesta P6 = A (FD-U13-07); VE-12; VE-15
  - id: BR5.9
    statement: La salida y los logs del Job solo llevan IDs, reglas, conteos y codes.
    category: constraint
    applies_to: [RetentionJobRun]
    trigger: Cualquier salida o log del Job
    logic: SI el Job escribe ENTONCES escribe una línea por candidato (ID, regla, conteos por tabla, estado) y un resumen final; nunca texto de turnos, hallazgos, notas ni rutas de archivo con nombres de persona.
    violation: Prueba de nivel 1 con datos sintéticos con canario que busca el canario en la salida y en los logs.
    source: NFR10; AUTONOMIA-04; team.md (Code Style, logs sin datos sensibles)
  - id: BR5.10
    statement: De una sesión borrada solo sobreviven RetentionAct, AccessLogEntry y el incidente de anonimización, todos sin clave foránea.
    category: constraint
    applies_to: [RetentionAct, AccessLogEntry]
    trigger: Fin del Job
    logic: SI una sesión se borró ENTONCES sus filas en esas tres tablas siguen, con sus IDs, y ninguna otra tabla tiene filas con ese session_id.
    violation: La misma prueba de BR5.5, que recorre todas las tablas marcadas con la convención de auditoría.
    source: AC15.7.2; C24; A-2

  # BR6 — Avisos de bienestar (US15.9, VE-16, DD-05)
  - id: BR6.1
    statement: Al abrir M4 aparece el aviso de contenido antes de la transcripción, con «Continuar».
    category: policy
    applies_to: [AnalystConsole]
    trigger: Cada apertura de M4, guiada o importada, por el dueño o en solo lectura
    logic: SI se abre M4 ENTONCES, antes de mostrar los turnos, se ve «Esta sesión contiene relatos de violencia. Puedes pausar cuando lo necesites» con «Continuar»; al pulsarlo aparece la transcripción; si además corresponde el diálogo de reconocimiento (BR1.4), va primero el reconocimiento.
    violation: Prueba Vitest de que la transcripción no está en el DOM visible hasta «Continuar».
    source: AC15.9.1; VE-16; DD-05
  - id: BR6.2
    statement: Al cumplirse wellness_reminder_interval_s con M4 abierta aparece un recordatorio no modal que se cierra sin perder el trabajo.
    category: policy
    applies_to: [AnalystConsole]
    trigger: Reloj de la consola desde «Continuar»
    logic: SI pasa el intervalo con M4 abierta ENTONCES aparece «Llevas un rato revisando. Considera una pausa» con «Cerrar», sin quitar el foco ni bloquear la entrada de turnos ni las tarjetas; al cerrarlo, el reloj vuelve a empezar; al salir de M4, se detiene.
    violation: Prueba Vitest con reloj simulado; aparece en el intervalo, no antes, y el texto escrito en la entrada de turnos sigue tras cerrarlo.
    source: AC15.9.2; VE-16; C25 (FD-U13-03)
  - id: BR6.3
    statement: Los avisos de bienestar no llaman a la API ni guardan nada.
    category: constraint
    applies_to: [AnalystConsole]
    trigger: Mostrar o cerrar un aviso de bienestar
    logic: SI se muestra o se cierra un aviso ENTONCES no hay petición ni fila; el intervalo llega a la consola con el catálogo de límites que ya sirve ConsoleApi.
    violation: Prueba Vitest que comprueba 0 peticiones al cerrar el aviso.
    source: VE-16; DD-05 (avisos que no bloquean); punto 10 de la sección 2

  # BR7 — Consulta de lo registrado (P7 = A)
  - id: BR7.1
    statement: Un comando de solo lectura de la imagen de session-api, que ejecuta el humano, lista accesos, reportes de problemas y actas.
    category: policy
    applies_to: [AccessQuery, AccessLogEntry, ProblemReport, RetentionAct]
    trigger: El humano ejecuta el comando de consulta dentro del pod de session-api
    logic: SI el subject es access_log ENTONCES lista las filas por session_id o user_id y since, solo con IDs, tipo y hora; SI es problem_reports ENTONCES lista categoría, IDs, quién, cuándo, testimony_warning y la nota; SI es retention_acts ENTONCES lista las actas; la salida es texto o JSON; usa una transacción de solo lectura y nunca escribe.
    violation: Prueba de nivel 1 que siembra filas y compara la salida JSON; prueba de que la transacción es READ ONLY.
    source: AC15.6.1 («consulto el registro de acceso»); respuesta P7 = A; VE-11; VE-15
  - id: BR7.2
    statement: El comando no expone ruta HTTP ni corre en la CI contra el clúster.
    category: constraint
    applies_to: [AccessQuery]
    trigger: Construcción de la imagen y de la API
    logic: SI se revisa el OpenAPI ENTONCES no hay rutas de lectura del registro, de los reportes de problemas ni de las actas; el comando se documenta en el runbook como una acción del humano.
    violation: Prueba de nivel 0 sobre el OpenAPI y la comprobación estática de AUTONOMIA-01.
    source: respuesta P7 = A; mockups §11 (US15.6 sin interfaz); AUTONOMIA-01

  # BR8 — Accesibilidad de lo que agrega U13 (US5.6)
  - id: BR8.1
    statement: El diálogo de reconocimiento, la franja, el panel de reporte, el diálogo de reducir el plazo y los avisos de bienestar entran en la suite axe de U4.
    category: policy
    applies_to: [ProblemReport, AcknowledgementState, RetentionTerm]
    trigger: Suite axe de nivel 3
    logic: SI corre la suite ENTONCES recorre cada uno de esos elementos abierto y cerrado con 0 violaciones serious o critical.
    violation: Casos nuevos en la suite axe.
    source: AC5.6.1; US5.6
  - id: BR8.2
    statement: Todo se usa con teclado; los diálogos modales atrapan y devuelven el foco, y el panel no modal no lo atrapa.
    category: policy
    applies_to: [ProblemReport, AcknowledgementState, RetentionTerm]
    trigger: Recorrido con teclado
    logic: SI se abre un diálogo modal ENTONCES el foco va al primer control y vuelve al botón que lo abrió al cerrar; Escape equivale a «Más tarde» o «Cancelar»; el panel de reporte y el recordatorio no atrapan el foco y se cierran con Escape cuando tienen el foco.
    violation: Casos nuevos del recorrido con teclado de nivel 3.
    source: AC5.6.2; US5.6
  - id: BR8.3
    statement: El aviso de testimonio, la franja y el plazo se leen por texto e icono, no solo por color.
    category: policy
    applies_to: [ProblemReport, AcknowledgementState, RetentionTerm]
    trigger: Dibujar esos estados
    logic: SI se muestra un aviso ENTONCES lleva icono y texto.
    violation: Prueba Vitest.
    source: AC5.6.3; US5.6
  - id: BR8.4
    statement: «Enviar» sin categoría o con la nota sobre el tope, y «Reducir» con un valor no válido, quedan deshabilitados y enfocables con su motivo.
    category: policy
    applies_to: [ProblemReport, RetentionTerm]
    trigger: Estado del formulario
    logic: SI falta la categoría ENTONCES «Enviar» tiene aria-disabled y el motivo «Elige una categoría»; SI la nota supera el tope ENTONCES el motivo es «La nota supera <N> caracteres»; SI el valor del diálogo no es menor que el plazo efectivo ni está en el rango ENTONCES «Reducir» queda deshabilitado con «Escribe un número de días menor que el actual».
    violation: Prueba Vitest con aria-disabled y aria-describedby.
    source: AC5.6.4; US5.6
  - id: BR8.5
    statement: aria-live anuncia una vez el resultado de reconocer, de enviar un reporte, de reducir el plazo y el recordatorio de bienestar.
    category: policy
    applies_to: [ProblemReport, AcknowledgementState, RetentionTerm]
    trigger: Fin de esas acciones y aparición del recordatorio
    logic: SI ocurre una de esas acciones ENTONCES se anuncia una sola vez su resultado («Reglas reconocidas», «Reporte enviado», «Aviso de testimonio», «Plazo reducido a <N> días») o el recordatorio, con cortesía polite; nada más se anuncia.
    violation: Prueba Vitest que cuenta los anuncios.
    source: AC5.6.5; regla única de anuncios de mockups (revisión 02, R-09)

  # BR9 — Convención de auditoría en las tablas de U13 (US8.4)
  - id: BR9.1
    statement: Las cinco tablas de U13 llevan la marca de la convención; las de solo inserción exigen actor y hora y el usuario de la aplicación no puede modificarlas ni borrarlas.
    category: constraint
    applies_to: [AnalystAcknowledgement, AccessLogEntry, RetentionChange, RetentionAct, ProblemReport]
    trigger: Migración de U13 y prueba común de auditoría
    logic: SI se crean las tablas ENTONCES AnalystAcknowledgement, AccessLogEntry, RetentionChange y RetentionAct se marcan history (purgable solo RetentionChange) y ProblemReport mutable purgable con solo SELECT e INSERT para veridicus_app; un INSERT con actor u hora nulos en una history falla y un UPDATE o DELETE de veridicus_app falla. La migración entra por su propio PR y corre como Job aparte.
    violation: La prueba común de auditoría recorre las cinco tablas; prueba de nivel 1 de INSERT con actor nulo.
    source: AC8.4.1; AC8.4.2; AC15.6.2; NFR11; ADR-003; project.md (migraciones como Job aparte)
  - id: BR9.2
    statement: veridicus_retention solo borra las tablas purgables de U13 y solo inserta en RetentionAct.
    category: authorization
    applies_to: [ProblemReport, RetentionChange, RetentionAct, AccessLogEntry, AnalystAcknowledgement]
    trigger: Operaciones del Job
    logic: SI veridicus_retention borra ProblemReport o RetentionChange ENTONCES funciona; SI intenta borrar AnalystAcknowledgement, AccessLogEntry o RetentionAct, o cualquier UPDATE ENTONCES la base lo rechaza; su único INSERT es en RetentionAct. Los permisos los define la migración de la convención de U3; U13 solo declara sus tablas.
    violation: Prueba de nivel 1 con el usuario de retención sobre cada tabla de U13.
    source: A-2; NFR11; usuario de retención de la convención de auditoría (diseño de U3)
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Reconocimiento | BR1.1–BR1.7 | El texto versionado; el estado calculado (90 días y versión); la fila de solo inserción; el diálogo y la franja (P1 = B); sin `403` |
| BR2 Registro de acceso | BR2.1–BR2.5 | El adaptador real de C23; filas sin texto; el registro en la transacción; solo inserción y sin claves foráneas; logs solo con IDs |
| BR3 Reporte de problemas | BR3.1–BR3.9 | Seis categorías; panel no modal; roles; derivación por sugerencia; nota opcional; testimonio avisado y no rechazado; sin sesión (P6 = A); nota fuera de los logs |
| BR4 Plazo de retención | BR4.1–BR4.6 | De 1 a 90 días; el máximo por defecto (P2 = A); desde la creación (P3 = A); solo reducir, por el dueño o un admin (P4 = A); plazo vacío; la cabecera de M4 |
| BR5 Job de retención | BR5.1–BR5.10 | Lo lanza el humano; selección por vencimiento; reloj real y `--dry-run` (P5 = A); cancelación previa; orden de C24; una transacción por sesión; acta; reportes sin sesión; salida sin texto; lo que sobrevive |
| BR6 Bienestar | BR6.1–BR6.3 | El aviso al abrir; el recordatorio no modal; sin API |
| BR7 Consulta | BR7.1–BR7.2 | El comando de solo lectura (P7 = A); sin rutas nuevas de lectura |
| BR8 Accesibilidad | BR8.1–BR8.5 | `axe`, teclado y foco, texto además del color, botones deshabilitados con motivo, anuncios |
| BR9 Auditoría | BR9.1–BR9.2 | Las marcas de la convención y los permisos de los dos usuarios sobre las tablas de U13 |
