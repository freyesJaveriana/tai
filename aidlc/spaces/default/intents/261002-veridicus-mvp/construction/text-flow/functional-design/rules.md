# Reglas de negocio — U4 text-flow

**Insumos.** Los mismos de `entities.md`. Los niveles (N0–N3) siguen team-practices. Las reglas
guardia de AUTONOMIA-05 (BR7.3–BR7.6, BR8.1–BR8.5) viven en `domain/` como código puro y exigen 100 %
de ramas.

```yaml
rules:
  # BR1 — Carga de un escenario
  - id: BR1.1
    statement: Un escenario se acepta solo si mide entre 1 y 1 048 576 bytes, es texto UTF-8 válido y no es un binario disfrazado.
    category: validation
    applies_to: [ScenarioVersion]
    trigger: POST /scenarios
    logic: SI supera 1 048 576 bytes ENTONCES 413 scenario.too_large; SI empieza por una firma binaria conocida (p. ej. %PDF) o contiene bytes NUL ENTONCES 415 scenario.invalid_format; SI no es UTF-8 válido o está vacío ENTONCES 422 scenario.invalid_format; en todos los casos 0 pasajes y 0 versiones.
    violation: Rechazo con el mensaje en español de AC1.1.2.
    source: FR2.1; AC1.1.2
  - id: BR1.2
    statement: Una fuente cuyo SHA-256 ya existe en otra versión se rechaza.
    category: validation
    applies_to: [ScenarioVersion]
    trigger: POST /scenarios
    logic: SI source_sha256 ya existe ENTONCES 409 scenario.duplicate_sha256 y nada se guarda.
    violation: Rechazo.
    source: FR2.4; C1
  - id: BR1.3
    statement: Los documentos de una versión se reconocen por encabezados `# [DOC-…] Título`; sin ninguno, el archivo es DOC-1; un ID repetido rechaza la carga.
    category: validation
    applies_to: [ScenarioDocument]
    trigger: POST /scenarios, antes de crear la versión
    logic: SI hay encabezados de primer nivel con la forma [DOC-…] ENTONCES cada uno abre un documento hasta el siguiente; el texto anterior al primero pertenece al primero; SI no hay ninguno ENTONCES DOC-1; SI dos encabezados usan el mismo ID ENTONCES 422 scenario.invalid_format.
    violation: Rechazo con mensaje en español.
    source: Respuesta P3 = A; FR2.2; PRD S6
  - id: BR1.4
    statement: Una carga válida crea la versión 1 en estado indexing, registra quién y cuándo, y encola su indexación.
    category: policy
    applies_to: [Scenario, ScenarioVersion]
    trigger: POST /scenarios válido
    logic: SI la carga es válida ENTONCES se guardan Scenario y ScenarioVersion (indexing, uploaded_by, uploaded_at) y se publica C4 en la misma operación; responde 202.
    violation: Prueba de nivel 1.
    source: AC1.1.1; FR1.3

  # BR2 — Indexación
  - id: BR2.1
    statement: El escenario se segmenta por párrafo y por encabezado; un párrafo largo se parte en oraciones completas hasta el máximo por pasaje, nunca dentro de una oración.
    category: calculation
    applies_to: [Passage]
    trigger: Indexación de una versión
    logic: SI un bloque separado por línea vacía o por encabezado cabe en el máximo ENTONCES es un pasaje; SI no ENTONCES se agrupan sus oraciones en orden hasta el máximo; una oración más larga que el máximo queda sola en su pasaje; cada pasaje es subcadena literal de la fuente y hereda el document_id de su documento.
    violation: Prueba de propiedad de nivel 0 (literalidad, orden y cobertura del texto).
    source: Respuesta P2 = A; FR2.2; AC1.1.3
  - id: BR2.2
    statement: La indexación de una versión es todo o nada.
    category: constraint
    applies_to: [Passage, ScenarioVersion]
    trigger: Indexación
    logic: SI falla el embedding o el guardado de cualquier pasaje ENTONCES la versión queda error con su code y 0 pasajes; SI todos se guardan ENTONCES pasa a ready con ready_at, en una sola transacción.
    violation: Prueba de nivel 1 con fake de embeddings que falla en el pasaje k > 1.
    source: AC1.1.4; C4
  - id: BR2.3
    statement: Solo una versión ready se puede elegir para una sesión.
    category: validation
    applies_to: [ScenarioVersion, InterviewSessionRecord]
    trigger: POST /sessions y catálogo
    logic: SI la versión está indexing o error ENTONCES 409 scenario.not_ready y la interfaz no la ofrece.
    violation: Rechazo.
    source: AC1.1.4; AC1.1.5; AC1.3.2
  - id: BR2.4
    statement: Cada pasaje expone por la API su texto literal, su posición y su ID de documento.
    category: constraint
    applies_to: [Passage]
    trigger: Consulta de pasajes
    logic: SI se consulta una versión ready ENTONCES cada pasaje trae text, position y document_id.
    violation: Prueba de nivel 1.
    source: AC1.1.3

  # BR3 — Catálogo
  - id: BR3.1
    statement: El catálogo muestra cada escenario con sus versiones y estados, y preselecciona la versión ready más reciente.
    category: policy
    applies_to: [Scenario, ScenarioVersion]
    trigger: Abrir M2 o M3
    logic: SI un escenario tiene versiones ENTONCES se listan con «Indexando…», «Listo» o «Error»; la ready de mayor número se preselecciona y las demás ready se rotulan «versión anterior»; SI no hay ninguna ready ENTONCES «No hay escenarios de control listos» y la acción «Cargar escenario de control».
    violation: Pruebas Vitest y de nivel 1.
    source: AC1.3.1; AC1.3.3
  - id: BR3.2
    statement: Mientras un escenario se indexa, el resto de la consola responde.
    category: policy
    applies_to: [ScenarioVersion]
    trigger: Indexación en curso
    logic: SI una versión está indexing ENTONCES la indexación corre en segundo plano y ninguna pantalla espera por ella.
    violation: Prueba Vitest.
    source: AC1.1.5; FR3.4

  # BR4 — Sesión
  - id: BR4.1
    statement: Al crear una sesión se guardan la versión, su SHA-256, el umbral vigente y top_k, y nunca cambian.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: POST /sessions
    logic: SI la versión está ready ENTONCES se crea la sesión open con esas instantáneas, el dueño y SessionStatusChange (null → open); la cabecera muestra escenario, versión, los primeros 12 caracteres del SHA-256 y el umbral.
    violation: Pruebas de nivel 1 y Vitest.
    source: AC2.1.1; AC2.1.2; ADR-006; Respuesta P4 = A
  - id: BR4.2
    statement: Solo un analista crea sesiones; el admin no ve «Nueva sesión».
    category: authorization
    applies_to: [InterviewSessionRecord]
    trigger: POST /sessions
    logic: SI el principal es admin ENTONCES 403 auth.forbidden y 0 filas; la interfaz oculta la acción.
    violation: Pruebas de nivel 1 y Vitest.
    source: AC2.1.3; FR1.2
  - id: BR4.3
    statement: Solo el dueño envía turnos, reintenta o finaliza su sesión.
    category: authorization
    applies_to: [InterviewSessionRecord, Turn]
    trigger: Rutas owner-only de U4
    logic: SI el principal no es el dueño ENTONCES 403 session.not_owner y 0 filas.
    violation: Prueba de nivel 1.
    source: AC2.1.4; ADR-009

  # BR5 — Turnos
  - id: BR5.1
    statement: Un turno mide entre 1 y 2 000 caracteres tras quitar espacios de los bordes.
    category: validation
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns
    logic: SI está vacío ENTONCES 422 validation.invalid_request y la interfaz deshabilita «Enviar turno»; SI supera 2 000 caracteres ENTONCES 422 turn.too_long con «El turno supera 2 000 caracteres. Divídelo en turnos más cortos».
    violation: Rechazo; 0 filas.
    source: Respuesta P5 = A; AC2.2.5
  - id: BR5.2
    statement: Los turnos se numeran en orden, sin huecos ni duplicados, también con envíos concurrentes.
    category: constraint
    applies_to: [Turn]
    trigger: Creación de un turno
    logic: SI llegan turnos a la vez ENTONCES la numeración se asigna bajo bloqueo de la sesión y (session_id, number) es único.
    violation: Prueba de nivel 1 con 10 envíos concurrentes.
    source: AC2.2.1; FR3.2
  - id: BR5.3
    statement: Un reenvío con el mismo client_request_id devuelve el turno ya creado.
    category: constraint
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns
    logic: SI (session_id, client_request_id) ya existe ENTONCES responde el turno existente sin crear otro ni encolar otra vez.
    violation: Prueba de nivel 1.
    source: C1; AC2.2.1
  - id: BR5.4
    statement: Enviar un turno nunca espera a su evaluación.
    category: policy
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns
    logic: SI el turno es válido ENTONCES se guarda queued con deadline_at, se publica C2 (con umbral, SHA-256, top_k y hasta 3 turnos previos) y responde 202.
    violation: Prueba de nivel 1 con juez bloqueado.
    source: AC2.2.2; FR3.4; C2
  - id: BR5.5
    statement: Una sesión finalizada o consolidada no acepta turnos nuevos.
    category: validation
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns
    logic: SI la sesión no está open ENTONCES 409 session.finalized (o session.not_open si está suspendida) y 0 filas.
    violation: Prueba de nivel 1.
    source: components InterviewSession; C1
  - id: BR5.6
    statement: Cada mensaje de turno cumple C2; uno mal formado se rechaza sin crear filas.
    category: validation
    applies_to: [Turn]
    trigger: Publicar y consumir C2
    logic: SI el mensaje no cumple C2 ENTONCES va a veridicus:turns:failed sin evaluarse ni crear filas.
    violation: Prueba de nivel 0 con el contrato de U1.
    source: AC2.2.3
  - id: BR5.7
    statement: Un turno produce exactamente un resultado por intento aunque un trabajador muera.
    category: constraint
    applies_to: [Turn, TurnEvaluation]
    trigger: Entrega repetida de C2 o de C3
    logic: SI un mensaje se reentrega ENTONCES la evaluación se repite sin efectos y la ingesta de C3 es idempotente por (turn_id, attempt); un resultado de un intento menor que el vigente, o de un turno ya evaluado, se confirma y se descarta.
    violation: Prueba de nivel 1 que mata al trabajador.
    source: AC2.2.4; C3; contract-design P3
  - id: BR5.8
    statement: Un turno queued o processing cuyo plazo vence pasa a error con turn.error.timeout.
    category: policy
    applies_to: [Turn]
    trigger: Revisión periódica de plazos
    logic: SI now > deadline_at Y status en (queued, processing) ENTONCES status error con turn.error.timeout; un resultado que llegue después para ese intento se descarta.
    violation: Prueba de nivel 1.
    source: AC3.2.1; C3
  - id: BR5.9
    statement: Reintentar un turno en error reprocesa el mismo turno con attempt + 1, también en una sesión finalizada.
    category: policy
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns/{n}/retry
    logic: SI el turno está error ENTONCES pasa a queued con attempt + 1 y se publica C2; SI no está error ENTONCES 409 turn.not_in_error.
    violation: Prueba de nivel 1: dos reintentos no duplican alertas.
    source: AC3.2.3; C1

  # BR6 — Umbral y configuración
  - id: BR6.1
    statement: El servicio no arranca sin un umbral válido.
    category: validation
    applies_to: [ThresholdConfig]
    trigger: Arranque de semantic-agent y session-api
    logic: SI VERIDICUS_SIMILARITY_THRESHOLD falta, está vacía, no es un número finito o está fuera del rango ENTONCES el cargador falla, el proceso termina con código ≠ 0, /readyz no pasa y el log nombra el ajuste sin su valor; los extremos del rango se aceptan.
    violation: Pruebas de nivel 0 y 1.
    source: FR5.1; AC4.3.1; AC4.3.2
  - id: BR6.2
    statement: Solo el cargador de configuración fija el umbral; la evaluación usa la instantánea del mensaje.
    category: constraint
    applies_to: [ThresholdConfig, InterviewSessionRecord]
    trigger: Evaluación de un turno
    logic: SI se evalúa un turno ENTONCES el umbral es el de C2 (instantánea de la sesión), nunca el del entorno del trabajador.
    violation: Prueba de nivel 1 de AC2.1.2.
    source: AC2.1.2; FR9.1; ADR-006

  # BR7 — Evaluación por afirmación
  - id: BR7.1
    statement: El turno se divide en afirmaciones por oración y por salto de línea; cada afirmación es subcadena literal del turno.
    category: calculation
    applies_to: [Claim]
    trigger: Evaluación de un turno
    logic: SI aparece `.`, `?`, `!` o `…` seguido de espacio o fin de línea, o un salto de línea, ENTONCES ahí termina una afirmación; se quitan espacios de los bordes y se descartan trozos sin letras; SI no queda ningún corte ENTONCES el turno entero es una afirmación.
    violation: Prueba de propiedad de nivel 0 (mismo texto, mismas afirmaciones; cada una subcadena literal).
    source: Respuesta P1 = A; AC3.1.5
  - id: BR7.2
    statement: Por afirmación se recuperan los 3 pasajes más similares de la versión de la sesión.
    category: calculation
    applies_to: [ClaimEvaluation, Passage]
    trigger: Evaluación de cada afirmación
    logic: SI se evalúa una afirmación ENTONCES se recuperan top_k = 3 pasajes de la versión de la sesión por similitud (1 − distancia coseno) descendente, con el usuario de solo lectura; max_similarity es la del primero.
    violation: Prueba de nivel 1 con vectores sembrados.
    source: Respuesta P4 = A; FR4.1; C9
  - id: BR7.3
    statement: La guardia del umbral decide antes que el juez.
    category: policy
    applies_to: [ClaimEvaluation]
    trigger: Tras recuperar los pasajes de una afirmación
    logic: SI max_similarity < umbral ENTONCES guard below_threshold, grade no documentada y la afirmación no se envía al juez; SI max_similarity ≥ umbral ENTONCES guard at_or_above_threshold y va al juez.
    violation: Prueba de nivel 0 con umbral − δ, umbral y umbral + δ (100 % de ramas) y de nivel 1 con vectores sembrados.
    source: AC4.1.1; AC4.1.2; AUTONOMIA-05; ADR-006
  - id: BR7.4
    statement: Si ninguna afirmación supera la guardia, no se llama al juez.
    category: policy
    applies_to: [TurnEvaluation]
    trigger: Tras la guardia
    logic: SI todas las afirmaciones son below_threshold ENTONCES no hay llamada al juez y el resultado no trae model_digest ni prompt_sha256.
    violation: Prueba de nivel 0 con un juez fake que falla si lo llaman.
    source: AC4.1.2; AUTONOMIA-05
  - id: BR7.5
    statement: Una calificación «no documentada» del juez se trata como por debajo del umbral.
    category: policy
    applies_to: [ClaimEvaluation]
    trigger: Tras validar la salida del juez
    logic: SI el juez califica no documentada ENTONCES la afirmación entra al paquete, sin alerta, y suprime la pregunta sugerida del turno.
    violation: Prueba de nivel 0.
    source: AC4.1.3
  - id: BR7.6
    statement: Solo una afirmación incongruente con guard at_or_above_threshold produce alerta; congruente nunca produce alerta ni paquete.
    category: policy
    applies_to: [ClaimEvaluation, ReviewSuggestion]
    trigger: Armado del resultado
    logic: SI grade incongruente Y guard at_or_above_threshold ENTONCES exactamente una alerta para esa afirmación; SI congruente ENTONCES nada; un turno puede traer a la vez alertas y un paquete.
    violation: Pruebas de nivel 0 de AC4.1.4, AC4.1.5 y AC3.1.3.
    source: FR4.3; AC3.1.3; AC4.1.4; AC4.1.5; project.md Corrections
  - id: BR7.7
    statement: Cada intento evaluado guarda por afirmación su texto, similitud máxima, 3 pasajes más cercanos y calificación.
    category: policy
    applies_to: [TurnEvaluation, ClaimEvaluation]
    trigger: Ingesta de C3 evaluated
    logic: SI el resultado es evaluated ENTONCES se guarda TurnEvaluation con sus ClaimEvaluation; la interfaz no los muestra.
    violation: Prueba de nivel 1.
    source: AC3.1.6

  # BR8 — Validación de la salida del juez y de las alertas
  - id: BR8.1
    statement: La salida del juez se valida contra C6 estricto; cualquier fallo deja el turno entero en error sin alertas.
    category: validation
    applies_to: [TurnEvaluation]
    trigger: Respuesta del juez
    logic: SI no es JSON, falta un campo, sobra un campo, una calificación sale del enum o una afirmación está mal formada ENTONCES outcome error con turn.error.invalid_output y 0 alertas, 0 paquetes y 0 preguntas para todo el turno.
    violation: Pruebas de nivel 0 de los casos (a)–(d) de AC3.2.1.
    source: FR4.2; AC3.2.1; C6
  - id: BR8.2
    statement: Un juez que no responde dentro de su timeout deja el turno en error con turn.error.timeout, distinto del formato inválido.
    category: validation
    applies_to: [TurnEvaluation]
    trigger: Llamada al juez
    logic: SI la llamada supera su timeout ENTONCES outcome error con turn.error.timeout y 0 alertas.
    violation: Prueba de nivel 0 del caso (e) de AC3.2.1.
    source: AC3.2.1; NFR10
  - id: BR8.3
    statement: Cada referencia a pasaje de la CoT debe estar entre los pasajes recuperados para esa afirmación.
    category: validation
    applies_to: [TurnEvaluation]
    trigger: Validación de la salida del juez
    logic: SI un passage_id de una afirmación no está entre sus 3 pasajes recuperados ENTONCES turn.error.invalid_output y 0 alertas.
    violation: Prueba de nivel 0; trazabilidad factual del 100 % en nivel 2.
    source: AC3.1.4; FR4.5
  - id: BR8.4
    statement: Una CoT con vocabulario prohibido fuera de las citas literales es salida inválida.
    category: validation
    applies_to: [TurnEvaluation]
    trigger: Validación de la salida del juez
    logic: SI el escáner de IntegrityPolicy encuentra un término de C8 en la CoT fuera de un tramo «…» literal del turno o de los pasajes recuperados ENTONCES turn.error.invalid_output y 0 alertas.
    violation: Prueba de nivel 0 con «el compareciente miente» (falla) y «falso» dentro de una cita literal (pasa).
    source: AC3.2.4; AC5.5.2; Functional Design de U1 (BR5.3)
  - id: BR8.5
    statement: Una alerta sin fragmento, cita, ID de documento o CoT, o con alguno vacío o solo espacios, o con un documento de otra versión, se rechaza en los tres puntos de validación.
    category: validation
    applies_to: [ReviewSuggestion]
    trigger: Al producir (SemanticEvaluation), al ingerir (InterviewSession) y al guardar (HumanReview)
    logic: SI falta o está en blanco fragment, quote, document_id o cot, o document_id no es de la versión de la sesión ENTONCES la alerta se rechaza; al producir o ingerir, el resultado entero es turn.error.invalid_output; al guardar, la restricción de base de datos lo impide.
    violation: Una prueba por campo y caso en nivel 0 (contrato) y en nivel 1 (restricciones).
    source: FR4.4; AC3.1.1; AC3.1.2; AUTONOMIA-05
  - id: BR8.6
    statement: La alerta usa como fragmento la afirmación literal y como cita el texto literal del pasaje citado.
    category: calculation
    applies_to: [ReviewSuggestion]
    trigger: Armado de la alerta
    logic: SI se arma una alerta ENTONCES fragment es el texto de la afirmación, quote es el texto del primer passage_id que el juez citó para ella, document_id es el de ese pasaje y cot es la CoT validada; el sistema arma estos campos, no el juez.
    violation: Prueba de nivel 0.
    source: FR4.4; AC3.1.1; C7

  # BR9 — Integridad del prompt
  - id: BR9.1
    statement: El testimonio va solo en el bloque delimitado de datos y el prompt del sistema se lee de un archivo montado cuyo SHA-256 coincide con el del repositorio.
    category: constraint
    applies_to: [JudgePrompt]
    trigger: Construcción del prompt y arranque del servicio
    logic: SI el SHA-256 del archivo montado no coincide con el esperado ENTONCES el servicio no arranca; SI se construye el prompt ENTONCES el texto del turno y de los pasajes solo aparece dentro del bloque de datos, nunca en las instrucciones.
    violation: Prueba de nivel 0; nivel 2 con la inyección del Escenario A sin cambio en las alertas.
    source: FR4.6; AC3.3.1; US3.3
  - id: BR9.2
    statement: El prompt del sistema se monta readOnly desde un ConfigMap y el usuario de base de datos del juez solo lee el marco de verdad.
    category: constraint
    applies_to: [JudgePrompt, Passage]
    trigger: Política de manifiestos y prueba de base de datos
    logic: SI el prompt no se monta readOnly desde un ConfigMap ENTONCES la política de nivel 0 falla; SI el usuario del juez logra INSERT, UPDATE, DELETE o un SELECT fuera de la vista del marco de verdad ENTONCES la prueba de nivel 1 falla.
    violation: Pruebas de nivel 0 y 1.
    source: AC3.3.2; C9; NFR10

  # BR10 — Paquete de Contexto de Traspaso
  - id: BR10.1
    statement: Un intento con al menos una afirmación «no documentada» produce exactamente un paquete; uno sin ninguna, ninguno.
    category: policy
    applies_to: [HandoffPackage]
    trigger: Armado del resultado
    logic: SI alguna afirmación es no documentada (por guardia o por el juez) ENTONCES un paquete con fragment = texto del turno, undocumented_claim_indexes y threshold_used; SI ninguna ENTONCES ningún paquete.
    violation: Prueba de nivel 0 y nivel 1 del caso de Hecho No Documentado.
    source: FR5.2; FR5.3; AC4.2.4
  - id: BR10.2
    statement: El paquete trae los turnos previos disponibles, hasta 3.
    category: calculation
    applies_to: [HandoffPackage]
    trigger: Armado del paquete
    logic: SI el turno es el número n ENTONCES previous_turn_numbers son los min(n − 1, 3) anteriores y se muestra «Turnos previos disponibles: N de 3».
    violation: Prueba de nivel 0.
    source: AC4.2.1
  - id: BR10.3
    statement: El paquete trae los 3 pasajes distintos más cercanos de sus afirmaciones no documentadas, por coeficiente descendente (todos si hay menos).
    category: calculation
    applies_to: [HandoffPackage]
    trigger: Armado del paquete
    logic: SI hay pasajes recuperados para las afirmaciones no documentadas ENTONCES se unen sin repetir, se ordenan por similitud descendente y se toman hasta 3.
    violation: Prueba de nivel 0.
    source: AC4.2.1; FR5.3
  - id: BR10.4
    statement: La CoT interrumpida la produce el sistema de forma determinista, sin llamar al LLM.
    category: calculation
    applies_to: [HandoffPackage]
    trigger: Armado del paquete
    logic: SI se arma el paquete ENTONCES interrupted_cot lista, por cada afirmación no documentada, su texto, sus pasajes, su similitud máxima, el umbral de la sesión y el motivo («similitud X < umbral Y» o «el juez la calificó no documentada»), con un formato fijo y números con 4 decimales.
    violation: Prueba de nivel 0 (mismo resultado, mismo texto; el fake del LLM falla si lo llaman).
    source: AC4.2.1; project.md Corrections
  - id: BR10.5
    statement: Un turno con alguna afirmación no documentada no trae pregunta sugerida.
    category: policy
    applies_to: [HandoffPackage]
    trigger: Armado del resultado
    logic: SI hay paquete ENTONCES suggested_question está ausente para todo el turno.
    violation: Prueba de nivel 0.
    source: FR5.2; AC4.1.2; AC4.1.3

  # BR11 — Ingesta y sugerencias
  - id: BR11.1
    statement: La ingesta de un resultado guarda evaluación, paquete y sugerencias en una sola transacción y luego confirma el mensaje.
    category: constraint
    applies_to: [TurnEvaluation, HandoffPackage, ReviewSuggestion]
    trigger: Consumo de C3
    logic: SI el resultado es válido y vigente ENTONCES en una transacción se guarda TurnEvaluation, HandoffPackage (si hay) y se llama SuggestionProposer.propose; el turno pasa a evaluated; solo después XACK.
    violation: Prueba de nivel 1 (un fallo a mitad no deja filas sueltas).
    source: C3; C10; ADR-002
  - id: BR11.2
    statement: Cada sugerencia nace pendiente, es idempotente por (turno, intento, afirmación) y la primera de la sesión abre la ronda 1.
    category: policy
    applies_to: [ReviewSuggestion, ReviewRound]
    trigger: SuggestionProposer.propose
    logic: SI la sesión no tiene ronda ENTONCES se abre la ronda 1 en la misma transacción; SI ya existe la sugerencia de ese (turn_id, attempt, claim_index) ENTONCES no se duplica.
    violation: Prueba de nivel 1 de reintentos sin duplicados.
    source: C10; ADR-007; AC3.2.3
  - id: BR11.3
    statement: Un resultado de error deja el turno en error con su code y sin filas de evaluación, paquete ni sugerencias.
    category: policy
    applies_to: [Turn]
    trigger: Consumo de C3 con outcome error
    logic: SI outcome es error ENTONCES el turno pasa a error con error_code y no se guarda nada más.
    violation: Prueba de nivel 1.
    source: FR4.2; AC3.2.1

  - id: BR11.4
    statement: Los historiales de U4 cumplen la convención de auditoría de U3 y se registran en ella.
    category: constraint
    applies_to: [SessionStatusChange, ScenarioVersion, ReviewSuggestion]
    trigger: Migraciones de U4 y prueba común de nivel 1
    logic: SI U4 crea SessionStatusChange (y las filas de solo inserción ScenarioVersion y ReviewSuggestion) ENTONCES las registra en AuditConvention; un INSERT con actor u hora nulos falla y el usuario de la aplicación no puede hacer UPDATE ni DELETE sobre ellas (la única actualización permitida de ScenarioVersion es la de su estado de indexación, que hace el indexador con su propio permiso).
    violation: Prueba común de nivel 1 de U3.
    source: AC8.4.1; AC8.4.2; ADR-003; US8.4

  # BR12 — Vocabulario prohibido (escáner de IntegrityPolicy)
  - id: BR12.1
    statement: U4 implementa en libs/ el escáner de IntegrityPolicy con la lista y las reglas de C8; U7 y U8 lo reutilizan.
    category: constraint
    applies_to: [TurnEvaluation]
    trigger: Cada texto generado o visible
    logic: SI se escanea un texto ENTONCES se usa scan(text, literal_sources) → lista de coincidencias, con normalización sin mayúsculas ni tildes, palabra completa y exclusión de tramos «…» literales de literal_sources (C8 y Functional Design de U1).
    violation: Suite de nivel 0 con los fixtures de C8 de U1.
    source: AC5.5.1; AC5.5.2; ADR-008; Functional Design de U1
  - id: BR12.2
    statement: El catálogo de mensajes y los rótulos de la consola tienen 0 coincidencias, y la interfaz renderizada también.
    category: validation
    applies_to: [TurnEvaluation]
    trigger: Nivel 0 (catálogo) y nivel 3 (interfaz renderizada)
    logic: SI una cadena del catálogo, un rótulo o el texto renderizado (salvo fragmento, cita y texto del analista) contiene un término ENTONCES la suite falla.
    violation: Pruebas de nivel 0 y 3.
    source: AC5.5.1
  - id: BR12.3
    statement: La salida del juez sobre el Golden Dataset tiene 0 coincidencias.
    category: validation
    applies_to: [TurnEvaluation]
    trigger: Nivel 2
    logic: SI alguna CoT del Golden Dataset tiene una coincidencia fuera de citas literales ENTONCES el reporte de nivel 2 falla.
    violation: Reporte de nivel 2 en rojo.
    source: AC5.5.1
  - id: BR12.4
    statement: Los únicos rótulos de resultado en pantalla vienen del catálogo de rótulos de U1.
    category: constraint
    applies_to: [ReviewSuggestion, HandoffPackage]
    trigger: Renderizado de tarjetas, avisos y estados de turno
    logic: SI la consola muestra un resultado ENTONCES usa «Sugerencia de revisión · Incongruencia semántica» para una alerta y «Hecho No Documentado» para el aviso, leídos del catálogo; no escribe rótulos propios.
    violation: Prueba Vitest.
    source: AC5.5.4; AC3.1.7; Functional Design de U1 (P3)

  # BR13 — Consola
  - id: BR13.1
    statement: Una alerta nueva llega sin modal, sin sonido y sin mover el foco, y se anuncia en una región aria-live polite.
    category: policy
    applies_to: [ReviewSuggestion]
    trigger: Sondeo que trae una sugerencia nueva
    logic: SI llega una sugerencia ENTONCES se agrega al panel, se actualiza el contador de pendientes y la región anuncia el agregado (p. ej. «Turno 4 evaluado · 1 sugerencia nueva · 2 pendientes») sin grados de severidad.
    violation: Prueba Vitest.
    source: AC3.1.7
  - id: BR13.2
    statement: Seleccionar una alerta resalta su fragmento en el turno.
    category: policy
    applies_to: [ReviewSuggestion]
    trigger: Selección de una tarjeta
    logic: SI se selecciona una alerta ENTONCES el fragmento queda resaltado en el turno usando su posición literal.
    violation: Prueba Vitest.
    source: AC3.1.8
  - id: BR13.3
    statement: Un turno en error muestra la causa sin jerga, el code como referencia secundaria y «Reintentar evaluación» al dueño.
    category: policy
    applies_to: [Turn]
    trigger: Turno con status error
    logic: SI el turno está en error ENTONCES se muestra el texto del catálogo para su code y «Código: <code>» en tamaño secundario.
    violation: Prueba Vitest.
    source: AC3.2.2
  - id: BR13.4
    statement: Un turno evaluado sin sugerencias ni paquete muestra «Evaluado · sin sugerencias de revisión».
    category: policy
    applies_to: [Turn]
    trigger: Turno evaluated sin alertas ni paquete
    logic: SI el turno está evaluated sin alertas ni paquete ENTONCES muestra ese texto, distinto de «Procesando» y del aviso de Hecho No Documentado.
    violation: Prueba de nivel 0.
    source: AC3.1.3
  - id: BR13.5
    statement: El aviso de Hecho No Documentado usa el texto exacto, se distingue por texto e icono, no cuenta como pendiente y abre un panel no modal que se cierra con Escape o «Cerrar».
    category: policy
    applies_to: [HandoffPackage]
    trigger: Turno con paquete
    logic: SI hay paquete ENTONCES se muestra «La IA no puede validar este fragmento de forma autónoma. Control manual requerido» sin estilo de error; al pulsarlo se abre el panel lateral sin tapar el turno; Escape o «Cerrar» lo cierran y el foco vuelve al aviso.
    violation: Pruebas Vitest y de nivel 3.
    source: FR5.4; AC4.2.2; AC4.2.3; project.md Corrections
  - id: BR13.6
    statement: Con la sesión recién creada se muestra el estado vacío y «Enviar turno» está deshabilitado mientras el texto esté vacío.
    category: policy
    applies_to: [Turn]
    trigger: Abrir una sesión sin turnos
    logic: SI no hay turnos ENTONCES se ve «Aún no hay turnos. Escribe el primer turno o pega una transcripción completa»; SI el texto está vacío ENTONCES el botón está deshabilitado.
    violation: Prueba Vitest.
    source: AC2.2.5
  - id: BR13.7
    statement: La consola de U4 cumple la base de accesibilidad y entrega la suite axe que usan las demás unidades.
    category: constraint
    applies_to: [Turn, ReviewSuggestion, HandoffPackage]
    trigger: Niveles 0 y 3
    logic: SI axe (WCAG 2.1 AA) encuentra violaciones serious o critical en login, lista, sesión, panel de alertas, paquete o consolidación ENTONCES la suite falla; SI el flujo de texto no se puede recorrer solo con teclado con el foco visible ENTONCES falla; SI un estado se identifica solo por color ENTONCES falla.
    violation: Pruebas de nivel 3 y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3; US5.6
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Carga | BR1.1–BR1.4 | Archivos inválidos, duplicados, documentos sin ID (P3) |
| BR2 Indexación | BR2.1–BR2.4 | Pasajes partidos a mitad de oración (P2), versiones a medio indexar |
| BR3 Catálogo | BR3.1–BR3.2 | Elegir una versión no lista; consola bloqueada |
| BR4 Sesión | BR4.1–BR4.3 | Umbral o escenario que cambian a mitad de sesión; acciones de otro rol o de otro dueño |
| BR5 Turnos | BR5.1–BR5.9 | Turnos enormes (P5), numeración con huecos, duplicados, bloqueo, resultados repetidos, plazos |
| BR6 Umbral | BR6.1–BR6.2 | Arrancar sin umbral; evaluar con un umbral distinto al de la sesión |
| BR7 Evaluación | BR7.1–BR7.7 | AUTONOMIA-05: la guardia decide antes que el juez (P1, P4) |
| BR8 Validación | BR8.1–BR8.6 | Alertas parciales, referencias inventadas, etiquetas de veracidad, alertas sin sus 4 campos |
| BR9 Prompt | BR9.1–BR9.2 | Inyección desde el testimonio; un juez que escribe |
| BR10 Paquete | BR10.1–BR10.5 | Hecho No Documentado sin contexto o con LLM |
| BR11 Ingesta | BR11.1–BR11.3 | Filas sueltas; sugerencias duplicadas |
| BR12 Vocabulario | BR12.1–BR12.4 | AUTONOMIA-03 en salida e interfaz |
| BR13 Consola | BR13.1–BR13.7 | Interrupciones, estados ambiguos, accesibilidad |
