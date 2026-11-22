# Reglas de negocio — U4 text-flow

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-03.
- Las reglas conservan su ID. Las que salen quedan con `status: Retirado` y no se renumeran (regla de
  `project.md`). Las que siguen y cambian llevan `status: cambia`.
- **Salen:** BR1.x (carga), BR2.x (indexación), BR3.x (catálogo de escenarios), BR6.x (umbral), BR7.x
  (evaluación por afirmación), BR8.3 (pasajes de la CoT), BR9.2 (usuario de solo lectura del juez),
  BR10.x (paquete de traspaso) y BR13.5 (aviso de Hecho No Documentado). Origen: cambio 01 e
  `docs/iteracion2.md` §2.8.
- **Cambian:** BR4.x, BR5.x, BR8.1, BR8.2, BR8.4–BR8.6, BR9.1, BR11.x, BR12.x y BR13.x (salvo BR13.5).
  Origen: C1–C3, C6, C10 y C17 de la revisión 3 de contract-summary.
- **Entran:** BR14 (consentimiento y perfil), BR15 (corridas y AnalysisWorker), BR16 (errores, incidente
  y bloqueo), BR17 (estado en pantalla, modo final y registro de modelos), BR18 (aviso de propósito
  limitado) y BR19 (puertos hacia otras unidades). Origen: respuestas P6–P11, adenda 02 y lo que U3,
  U10 y U11 dejaron a U4.

**Insumos.** Los mismos de `entities.md`: unit-of-work y unit-of-work-story-map (U4, revisión 3),
requirements (FR3, FR4, FR14, FR15 y adenda 02), components (InterviewSession, AnalysisWorker,
HumanReview, ConsoleApi, IntegrityPolicy, AnalystConsole), contract-summary (C1–C3, C6–C8, C10, C11, C17,
C18, C21, C24, C25; CD-01, CD-02, CD-06, CD-11) y las respuestas P6–P11 de
`functional-design-questions.md`.

**Bloqueantes.** Las reglas que realizan AUTONOMIA-03, AUTONOMIA-04 y AUTONOMIA-05 viven en `domain/`
como código puro y piden 100 % de ramas: BR8.1, BR8.4, BR8.5, BR12.x, BR16.3, BR16.4 y BR16.5. Cada una
cita su prueba.

```yaml
rules:
  # BR1–BR3 — Escenarios (Retirado, cambio 01)
  - id: BR1.1
    status: Retirado
    statement: "Validación del archivo de escenario. Sale con TruthFrame (cambio 01)."
    source: cambio 01 (DT27)
  - id: BR1.2
    status: Retirado
    statement: "SHA-256 único por versión de escenario. Sale con TruthFrame."
    source: cambio 01 (DT27)
  - id: BR1.3
    status: Retirado
    statement: "Documentos del escenario por encabezado (P3 de la primera pasada)."
    source: cambio 01 (DT27)
  - id: BR1.4
    status: Retirado
    statement: "Indexación en segundo plano al cargar. Sale con los embeddings."
    source: cambio 01 (DT27)
  - id: BR2.1
    status: Retirado
    statement: "Segmentación en pasajes (P2 de la primera pasada)."
    source: cambio 01 (DT27)
  - id: BR2.2
    status: Retirado
    statement: "Indexación atómica de una versión."
    source: cambio 01 (DT27)
  - id: BR2.3
    status: Retirado
    statement: "Versión no lista no elegible."
    source: cambio 01 (DT27)
  - id: BR2.4
    status: Retirado
    statement: "Indexación sin bloquear la consola."
    source: cambio 01 (DT27)
  - id: BR3.1
    status: Retirado
    statement: "Versión más reciente preseleccionada en el catálogo."
    source: cambio 01 (DT27)
  - id: BR3.2
    status: Retirado
    statement: "Catálogo usable durante la indexación."
    source: cambio 01 (DT27)

  # BR4 — Sesión
  - id: BR4.1
    status: cambia
    statement: Al crear una sesión se guardan el perfil, su configuración efectiva y su config_sha256, y nunca cambian; todas sus corridas usan esa instantánea.
    category: policy
    applies_to: [InterviewSessionRecord, AnalysisRun]
    trigger: POST /sessions
    logic: SI el perfil está aprobado y el consentimiento es válido ENTONCES en una transacción se crean InterviewSessionRecord open con profile_name, effective_config y config_sha256 resueltos en ese momento, ConsentRecord y SessionStatusChange (null → open, actor el analista); cada corrida copia config_sha256 de la sesión y C2 lleva effective_config de la sesión, nunca la del archivo vigente; un disparador impide cambiar esas tres columnas.
    violation: Prueba de nivel 1 de AC2.1.2 (PR que cambia el perfil X y reinicio; S1 conserva su huella, S2 guarda la nueva) y Vitest de la cabecera.
    source: AC2.1.1; AC2.1.2; ADR-006; C1 POST /sessions
  - id: BR4.2
    status: cambia
    statement: Solo un analista crea sesiones y envía turnos; admin e investigador reciben 403 y no ven «Nueva sesión».
    category: authorization
    applies_to: [InterviewSessionRecord, Turn]
    trigger: POST /sessions y POST /sessions/{id}/turns
    logic: SI el rol no es analista ENTONCES 403 auth.forbidden y 0 filas; la interfaz oculta «Nueva sesión» y la entrada de turnos.
    violation: Pruebas de nivel 1 por rol y Vitest.
    source: AC2.1.4; FR1.2; C1 x-veridicus-roles
  - id: BR4.3
    status: cambia
    statement: Solo el dueño envía turnos, reintenta corridas y consulta su sesión como dueño; la verificación la hace ConsoleApi antes de delegar.
    category: authorization
    applies_to: [InterviewSessionRecord, Turn, AnalysisRun]
    trigger: Rutas x-veridicus-owner-only de U4
    logic: SI el principal no es el dueño ENTONCES 403 session.not_owner y 0 filas; el resolvedor del dueño lee owner_user_id con el mismo bloqueo compartido de la sesión.
    violation: Prueba de nivel 1 por ruta.
    source: AC2.1.5; ADR-009

  # BR5 — Turnos y encolado
  - id: BR5.1
    status: cambia
    statement: Un turno mide entre 1 y turn_max_chars caracteres (C25) tras quitar espacios de los bordes; en el límite exacto se acepta.
    category: validation
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns
    logic: SI está vacío ENTONCES 422 validation.invalid_request; SI supera turn_max_chars ENTONCES 413 limits.exceeded y 0 filas; la consola muestra «X / M caracteres» y deshabilita «Enviar turno» con su motivo. La cifra se lee de contracts/limits.v1.yaml; una variable de entorno solo puede bajarla.
    violation: Prueba de nivel 1 en M, M + 1 y 0; Vitest del contador.
    source: AC2.2.6; AC2.2.5; C25; P5 de la primera pasada pasa a NFR Requirements
  - id: BR5.2
    statement: Los turnos se numeran en orden, sin huecos ni duplicados, también con envíos concurrentes.
    category: constraint
    applies_to: [Turn]
    trigger: Creación de un turno
    logic: SI llegan turnos a la vez ENTONCES n se asigna bajo el bloqueo exclusivo de la fila de la sesión (después del bloqueo compartido del usuario, BR19.2) y (session_id, n) es único.
    violation: Prueba de nivel 1 con 10 envíos concurrentes (turnos 1..10).
    source: AC2.2.1; FR3.2
  - id: BR5.3
    statement: Un reenvío con el mismo client_request_id devuelve el turno ya creado y su corrida, sin crear otro ni encolar otra vez.
    category: constraint
    applies_to: [Turn, AnalysisRun]
    trigger: POST /sessions/{id}/turns
    logic: SI (session_id, client_request_id) ya existe ENTONCES responde 202 con el turno y la corrida existentes.
    violation: Prueba de nivel 1.
    source: C1 client_request_id; AC2.2.1
  - id: BR5.4
    status: cambia
    statement: Un turno TEST encola una sola corrida incremental con desde_turno = hasta_turno = n y responde 202 sin esperar el análisis.
    category: policy
    applies_to: [Turn, AnalysisRun]
    trigger: POST /sessions/{id}/turns con hablante TEST
    logic: SI el turno es TEST y la sesión admite corridas (BR15.2) ENTONCES en la misma transacción se guardan Turn, AnalysisRun incremental (desde = hasta = n) y RunStatusChange (null → queued, attempt 1, deadline_at); tras confirmar se publica C2 y responde 202 con turn y run. Un turno ENT sigue BR15.1.
    violation: Prueba de nivel 1 de AC2.2.2 con un fake que bloquea hasta que la prueba lo libera (POST 202 y GET 200 antes de liberar).
    source: AC2.2.2; AC2.2.3; FR4.9; C1; P10 = B
  - id: BR5.5
    status: cambia
    statement: Una sesión que no está abierta a turnos los rechaza con un code por situación y sin crear filas; en pausa el turno se guarda sin encolar.
    category: validation
    applies_to: [Turn]
    trigger: POST /sessions/{id}/turns
    logic: SI blocked_code no es nulo ENTONCES 409 session.blocked; SI el consentimiento está retirado ENTONCES 409 session.consent_withdrawn; SI status terminated ENTONCES 409 session.terminated; SI finalized o consolidated ENTONCES 409 session.finalized; SI closed_to_new_turns (importada) ENTONCES 409 session.closed_to_new_turns; SI suspended ENTONCES 409 session.suspended (code nuevo, FD-U4-07), y se reanuda primero con U6; SI paused ENTONCES 202 con el turno y sin run. El orden de las comprobaciones es el de esta lista. En el rechazo, 0 filas.
    violation: Prueba de nivel 1 por estado.
    source: C1 ErrorCode; AC15.2.1; AC15.2.2; AC15.2.3; P7 = A
  - id: BR5.6
    status: cambia
    statement: Cada mensaje de corrida cumple C2; uno mal formado o de versión mayor desconocida va a veridicus:runs:failed sin analizarse ni crear filas.
    category: validation
    applies_to: [AnalysisRun]
    trigger: Publicar y consumir C2
    logic: SI InterviewSession arma un mensaje ENTONCES lo valida contra C2 antes de publicar; SI AnalysisWorker recibe uno que no cumple C2 ENTONCES lo pasa a veridicus:runs:failed, hace XACK y no llama a C17; la corrida termina en analysis.system por plazo (BR5.8).
    violation: Prueba de nivel 0 con los fixtures de C2 de U1 y de nivel 1 con un mensaje inválido inyectado.
    source: AC2.2.3; C2
  - id: BR5.7
    status: cambia
    statement: Una corrida produce exactamente un resultado por intento aunque un trabajador muera.
    category: constraint
    applies_to: [AnalysisRun, RunAttempt]
    trigger: Reentrega de C2 o de C3
    logic: SI un mensaje de C2 queda pendiente ENTONCES otro trabajador lo reclama con XAUTOCLAIM tras claim_idle_ms y repite la corrida entera; la ingesta de C3 es idempotente por (run_id, attempt), y un segundo resultado del mismo intento se confirma y se descarta.
    violation: Prueba de nivel 1 que mata al trabajador a mitad de la corrida.
    source: AC2.2.4; C2; C3
  - id: BR5.8
    status: cambia
    statement: Una corrida queued o processing cuyo plazo vence, o que agota sus entregas, pasa a error con analysis.system.
    category: policy
    applies_to: [AnalysisRun, RunStatusChange]
    trigger: Supervisor periódico de plazos en session-api; paso a veridicus:runs:failed
    logic: SI now > deadline_at Y el estado vigente es queued o processing ENTONCES RunStatusChange → error con analysis.system, actor system run-supervisor, y se escribe la clave de cancelación (BR15.4); SI el mensaje llega a run_max_deliveries ENTONCES va a veridicus:runs:failed y la corrida queda igual en error con analysis.system. Un resultado que llegue después se descarta (BR16.1).
    violation: Prueba de nivel 1 con reloj simulado.
    source: C2; C25 run_deadline_incremental_s y run_deadline_final_s
  - id: BR5.9
    status: cambia
    statement: Reintentar una corrida en error repite el mismo tramo con attempt + 1, también en una sesión finalizada, si la sesión admite corridas.
    category: policy
    applies_to: [AnalysisRun, RunStatusChange]
    trigger: POST /sessions/{id}/runs/{run_id}/retry
    logic: SI el estado vigente no es error ENTONCES 409 run.not_in_error; SI la sesión no admite corridas ENTONCES 409 con el code de BR15.2; SI no ENTONCES RunStatusChange (error → queued, attempt + 1, deadline_at nuevo, actor el dueño) y se publica C2 con el mismo desde_turno y hasta_turno.
    violation: Prueba de nivel 1 de AC3.2.3 (dos reintentos, sin hallazgos duplicados).
    source: AC3.2.3; C1 retry

  # BR6 — Umbral (Retirado)
  - id: BR6.1
    status: Retirado
    statement: "Arranque rechazado sin umbral válido. Sale el umbral (cambio 01)."
    source: cambio 01 (DT27)
  - id: BR6.2
    status: Retirado
    statement: "Umbral de la instantánea de la sesión. Sale el umbral."
    source: cambio 01 (DT27)

  # BR7 — Evaluación por afirmación (Retirado)
  - id: BR7.1
    status: Retirado
    statement: "División del turno en afirmaciones (P1 de la primera pasada)."
    source: cambio 01 (DT27)
  - id: BR7.2
    status: Retirado
    statement: "Recuperación de 3 pasajes por afirmación."
    source: cambio 01 (DT27)
  - id: BR7.3
    status: Retirado
    statement: "Guardia del umbral antes del juez."
    source: cambio 01 (DT27)
  - id: BR7.4
    status: Retirado
    statement: "Sin llamada al juez bajo el umbral."
    source: cambio 01 (DT27)
  - id: BR7.5
    status: Retirado
    statement: "«No documentada» como bajo el umbral."
    source: cambio 01 (DT27)
  - id: BR7.6
    status: Retirado
    statement: "Alerta solo con «incongruente» sobre el umbral."
    source: cambio 01 (DT27)
  - id: BR7.7
    status: Retirado
    statement: "Registro de evaluación por afirmación."
    source: cambio 01 (DT27)

  # BR8 — Validación en la ingesta
  - id: BR8.1
    status: cambia
    statement: La salida de cada resultado se valida contra C6 estricto en la ingesta; cualquier fallo deja la corrida entera en error con analysis.invalid_output y sin sugerencias.
    category: validation
    applies_to: [RunAttempt, ReviewSuggestion]
    trigger: Consumo de C3 RunResult
    logic: SI la salida no cumple el esquema de C6 (campo faltante o extra, tipo fuera del enum, estado error con hallazgos) o rompe la regla 2 de C6 (una cita en un turno que no está en la entrada; en incremental, ninguna cita en un turno >= desde_turno) ENTONCES RunAttempt outcome error con analysis.invalid_output, 0 ReviewSuggestion y XACK.
    violation: Pruebas de nivel 0 con los fixtures inválidos de C6 de U1 y de nivel 1 con un resultado inyectado por caso.
    source: AC3.2.1; AC3.6.1; AC3.6.2; FR4.2; AUTONOMIA-05
  - id: BR8.2
    status: cambia
    statement: Cada error.codigo de C6 se traduce a un solo code de C1, distinto para cada causa.
    category: calculation
    applies_to: [RunAttempt, RunStatusChange]
    trigger: Ingesta de una salida con estado error
    logic: salida_invalida → analysis.invalid_output; bloqueo_contenido → analysis.content_blocked; tiempo_agotado → analysis.timeout; proveedor → analysis.provider; anonimizador_no_disponible → analysis.anonymizer_unavailable; incidente_anonimizacion → anonymizer.incident (BR16.4). analysis.system solo lo fija InterviewSession (BR5.8, BR16.8, BR15.5). La tabla vive en un único módulo de domain/.
    violation: Prueba de nivel 0 con una salida fixture por código (casos (a)–(i) de AC3.2.1) y prueba de nivel 1 de extremo a extremo con un fake del ModelGateway por código.
    source: AC3.2.1; C1 ErrorCode; CD-01; CD-02
  - id: BR8.3
    status: Retirado
    statement: "Referencias de la CoT a pasajes recuperados. Sale el marco documental (cambio 01)."
    source: cambio 01 (DT27)
  - id: BR8.4
    status: cambia
    statement: Un hallazgo cuyo hecho u observaciones contienen vocabulario prohibido fuera de las dos citas deja la corrida entera en analysis.invalid_output; no se quita en silencio.
    category: validation
    applies_to: [RunAttempt, ReviewSuggestion]
    trigger: Ingesta de una salida ok
    logic: SI el escáner de C8 (de U11) encuentra un término en hecho u observaciones de cualquier hallazgo, excluidas cita_a.cita y cita_b.cita, ENTONCES RunAttempt outcome error con analysis.invalid_output y 0 sugerencias. Es la segunda línea, porque U11 ya descarta el candidato (motivo vocabulario_prohibido) antes de emitir.
    violation: Prueba de nivel 0 de AC5.5.2 (a) «el compareciente miente» en observaciones falla, (b) «falso» dentro de una cita pasa, (c) «miente» entre «» en observaciones que no es ninguna de las citas falla; prueba de nivel 1 con una salida inyectada.
    source: AC3.2.4; AC5.5.2; Functional Design de U1 (F3, R-09); FD-U11-02
  - id: BR8.5
    status: cambia
    statement: Un hallazgo sin hecho, tipo, cita_a, cita_b u observaciones, o con alguno vacío o solo espacios, se rechaza en los tres puntos de validación.
    category: validation
    applies_to: [ReviewSuggestion]
    trigger: Al producir (U11 por C17), al ingerir (InterviewSession) y al guardar (HumanReview)
    logic: SI falta o está en blanco hecho, tipo, cita_a.cita, cita_a.turno, cita_b.cita, cita_b.turno u observaciones ENTONCES al ingerir la corrida entera es analysis.invalid_output (BR8.1); al guardar, una restricción CHECK de la base y propose lo impiden.
    violation: Una prueba por campo y caso en nivel 0 (contrato) y en nivel 1 (restricciones de la base).
    source: AC3.1.1; AUTONOMIA-05; C7; C10
  - id: BR8.6
    status: cambia
    statement: La sugerencia copia tal cual hecho, tipo, cita_a, cita_b, observaciones y actos del hallazgo; U4 no arma ni reescribe ningún campo.
    category: calculation
    applies_to: [ReviewSuggestion]
    trigger: SuggestionProposer.propose
    logic: SI se guarda una sugerencia ENTONCES sus campos son los del hallazgo de C6, con los avisos de cada cita; solo se calculan pair_key, first_run_id y created_at.
    violation: Prueba de nivel 0 (ida y vuelta del fixture de C6 sin cambios).
    source: AC3.1.1; C7; C10

  # BR9 — Configuración de la corrida
  - id: BR9.1
    status: cambia
    statement: AnalysisWorker no construye el prompt ni lee el archivo de perfiles vigente; llama a C17 con la entrada y la configuración efectiva del mensaje, y la corrida guarda el prompt_sha256 y la versión del analizador que devuelve la salida.
    category: constraint
    applies_to: [AnalysisRun, RunAttempt]
    trigger: Corrida en AnalysisWorker
    logic: SI se procesa una corrida ENTONCES config = effective_config de C2 y entrada = entrada de C2; RunAttempt guarda prompt_sha256 y analyzer_version de la salida.
    violation: Prueba de nivel 1 de AC2.1.2 y prueba de equivalencia de AC2.2.7 (BR15.9).
    source: AC2.1.2; FR14.2; C17; unit-of-work (el prompt y ModelGateway pasan a U11)
  - id: BR9.2
    status: Retirado
    statement: "Prompt montado desde un ConfigMap y usuario de solo lectura del juez. El prompt pasa a U11 y sale el marco documental."
    source: cambio 01 (DT27); unit-of-work

  # BR10 — Paquete de Contexto de Traspaso (Retirado)
  - id: BR10.1
    status: Retirado
    statement: "Un paquete por intento con afirmación no documentada."
    source: cambio 01 (DT27)
  - id: BR10.2
    status: Retirado
    statement: "Turnos previos del paquete."
    source: cambio 01 (DT27)
  - id: BR10.3
    status: Retirado
    statement: "Pasajes más cercanos del paquete."
    source: cambio 01 (DT27)
  - id: BR10.4
    status: Retirado
    statement: "CoT interrumpida determinista."
    source: cambio 01 (DT27)
  - id: BR10.5
    status: Retirado
    statement: "Sin pregunta sugerida con paquete."
    source: cambio 01 (DT27)

  # BR11 — Ingesta y sugerencias
  - id: BR11.1
    status: cambia
    statement: La ingesta de un resultado vigente guarda intento, registro de modelos, descartes, estado y sugerencias en una sola transacción, y solo después confirma el mensaje.
    category: constraint
    applies_to: [RunAttempt, ModelCall, DiscardedCandidate, RunStatusChange, ReviewSuggestion]
    trigger: Consumo de C3 RunResult
    logic: SI el resultado es vigente (BR16.1) ENTONCES en una transacción, con el orden de bloqueo sesión → ronda (BR19.2), se guardan RunAttempt, cada ModelCall, cada DiscardedCandidate, RunStatusChange (→ done o → error, actor system analysis-worker) y, con estado ok, se llama a propose; solo después XACK. Un fallo a mitad revierte todo y el mensaje queda pendiente.
    violation: Prueba de nivel 1 que hace fallar la transacción a mitad (0 filas sueltas, el mensaje se reentrega).
    source: C3; C10; ADR-002; AC12.5.1
  - id: BR11.2
    status: cambia
    statement: Cada hallazgo se une sin duplicar por el par no ordenado de (turno, cita normalizada en espacios); un hallazgo ya decidido conserva su estado, y la primera sugerencia de la sesión abre la ronda 1.
    category: policy
    applies_to: [ReviewSuggestion, ReviewRound]
    trigger: SuggestionProposer.propose
    logic: pair_key = SHA-256 de los dos pares (turno, cita con espacios normalizados) ordenados; SI (session_id, pair_key) ya existe ENTONCES no se crea otra fila ni cambia la existente ni su decisión; SI la sesión no tiene ronda ENTONCES se abre la ronda 1 en la misma transacción.
    violation: Prueba de nivel 1 de AC3.6.3 (dos corridas con el mismo par, una ya decidida) y de AC3.2.3.
    source: AC3.6.3; AC2.7.2; C10; ADR-007; FR4.9
  - id: BR11.3
    status: cambia
    statement: Una salida con estado error deja la corrida en error con su code y guarda su registro, sin sugerencias.
    category: policy
    applies_to: [RunAttempt, ModelCall, RunStatusChange]
    trigger: Consumo de C3 con estado error
    logic: SI estado es error ENTONCES RunAttempt outcome error con el code de BR8.2, ModelCall y DiscardedCandidate de lo que alcanzó a llamar, RunStatusChange → error y 0 sugerencias; una salida error con hallazgos no cumple C6 (BR8.1).
    violation: Prueba de nivel 1 por código.
    source: AC3.2.1; FR4.2; C3
  - id: BR11.4
    status: cambia
    statement: Las tablas de U4 cumplen la convención de auditoría de U3; las de solo inserción rechazan actor u hora nulos y no admiten UPDATE ni DELETE del usuario de la aplicación.
    category: constraint
    applies_to: [SessionStatusChange, RunStatusChange, AnalysisRun, RunAttempt, ModelCall, DiscardedCandidate, AnonymizationIncident, Turn, ReviewSuggestion]
    trigger: Migraciones de U4 y prueba común de nivel 1 de U3
    logic: SI U4 crea una tabla ENTONCES declara veridicus-audit; las history (todas las de applies_to) llevan actor_kind y actor_system; InterviewSessionRecord y ConsentRecord son mutable con disparadores que limitan qué columnas cambian (entities.md). Las corridas no cambian de fila; su estado es la última RunStatusChange.
    violation: Prueba común de nivel 1 de U3, que entra completa con el PR de U4.
    source: AC8.4.1; AC8.4.2; ADR-003; FD-U3-07; FD-U3-10

  # BR12 — Vocabulario prohibido (escáner de U11)
  - id: BR12.1
    status: cambia
    statement: U4 no implementa el escáner; usa el de U11 con la lista de C8 en la ingesta y en las suites de la interfaz.
    category: constraint
    applies_to: [ReviewSuggestion]
    trigger: Ingesta (BR8.4) y suites de nivel 0 y 3 (BR12.2)
    logic: SI U4 escanea un texto ENTONCES llama al escáner publicado por U11 con la lista versionada de C8 y sus fuentes literales (las dos citas, el texto del analista y la cadena del aviso); no copia la lista ni las reglas.
    violation: Prueba de nivel 0 de import-linter (session-api y frontend no definen otra lista) y la suite de BR12.2.
    source: AC5.5.1; Functional Design de U1 (FD-U1-09); unit-of-work (la propiedad del escáner pasa a U11)
  - id: BR12.2
    status: cambia
    statement: Las cadenas de la interfaz, los rótulos y la interfaz renderizada tienen 0 coincidencias, salvo las dos citas, el texto del analista y la cadena versionada del aviso.
    category: validation
    applies_to: [ReviewSuggestion]
    trigger: Nivel 0 (catálogo de mensajes y plantillas) y nivel 3 (interfaz renderizada)
    logic: SI una cadena del catálogo, un rótulo, una plantilla o el texto renderizado contiene un término de C8 fuera de esas exclusiones ENTONCES la suite falla; un fixture con cada término de la lista (incluidos «prueba», «probatorio», «pliego», «inculpa», «miente», «engaño» y «falso») la hace fallar; «prueba» dentro del aviso no.
    violation: Pruebas de nivel 0 y 3 con control negativo por término.
    source: AC5.5.1; AC5.5.5; AC5.5.6; A-1
  - id: BR12.3
    status: cambia
    statement: El nivel 2 del vocabulario lo mide la CLI de U11 sobre el conjunto sintético; vale para el trabajador porque los dos dan la misma salida.
    category: policy
    applies_to: [RunAttempt]
    trigger: Nivel 2
    logic: SI el reporte de nivel 2 de la CLI tiene 0 coincidencias Y la prueba de equivalencia (BR15.9) pasa ENTONCES el trabajador no necesita una corrida de nivel 2 propia.
    violation: Reporte de nivel 2 de U11 en rojo, o prueba de equivalencia en rojo.
    source: AC5.5.1; AC2.2.7
  - id: BR12.4
    status: cambia
    statement: Los únicos rótulos de resultado en pantalla son «Sugerencia de revisión», «Contradicción en el relato» y los 7 rótulos de tipo, leídos del catálogo de rótulos.
    category: constraint
    applies_to: [ReviewSuggestion]
    trigger: Renderizado de tarjetas y estados
    logic: SI la consola muestra un hallazgo ENTONCES su rótulo es «Sugerencia de revisión · Contradicción en el relato» y el tipo uno de Fecha, Número, Lugar, Persona, Negación, Secuencia u Otro, del catálogo de U1; sin grados de severidad ni puntajes.
    violation: Prueba Vitest que recorre los rótulos renderizados.
    source: AC5.5.4; AC3.1.3; AC5.5.3; Functional Design de U1 (FD-U1-08)

  # BR13 — Consola
  - id: BR13.1
    status: cambia
    statement: Un hallazgo nuevo llega sin modal, sin sonido y sin mover el foco; la región aria-live polite anuncia por corrida, nunca por turno.
    category: policy
    applies_to: [ReviewSuggestion, AnalysisRun]
    trigger: Sondeo que trae cambios
    logic: SI el sondeo trae sugerencias nuevas o una corrida que empieza, termina o falla ENTONCES se actualiza el panel y el contador, y la región publica un solo mensaje agregado por corrida (p. ej. «Corrida del turno 4 terminada · 1 sugerencia nueva · 2 pendientes»); los estados de cada turno se leen al enfocarlo.
    violation: Prueba Vitest con un bloque de 200 turnos que cambian a la vez (un anuncio por corrida).
    source: AC3.1.3; AC5.6.5; mockups §6.4
  - id: BR13.2
    status: cambia
    statement: Seleccionar un hallazgo marca sus dos citas en la transcripción con «A» y «B» además del color, anuncia «Cita A, turno N» y permite saltar de una a otra.
    category: policy
    applies_to: [ReviewSuggestion]
    trigger: Selección de una tarjeta o «Ir a la cita A/B»
    logic: SI se selecciona un hallazgo ENTONCES las dos citas quedan marcadas (A con barra continua, B con barra discontinua); «Ir a la cita» desplaza y mueve el foco al turno; «Volver al hallazgo» devuelve el foco a la tarjeta. Una cita con « […] » marca sus fragmentos en orden.
    violation: Prueba Vitest.
    source: AC3.1.2; AC5.6.3
  - id: BR13.3
    status: cambia
    statement: Un tramo en error muestra su causa en español, el mensaje de FR4.2, el code como referencia secundaria y «Reintentar tramo» al dueño.
    category: policy
    applies_to: [AnalysisRun]
    trigger: Corrida con estado vigente error
    logic: 'SI la corrida está en error y no la cubre el modo final (BR17.2) ENTONCES sobre el grupo de turnos se ve «⚠ Tramo no evaluado», la causa del catálogo para su code (AC3.2.5 o la propuesta de analysis.system), «El analizador no pudo procesar este tramo. Revisión manual requerida» y «Código: <code>»; «Reintentar tramo» solo para el dueño, deshabilitado (enfocable) con su motivo si la sesión no admite corridas.'
    violation: Prueba Vitest por code.
    source: AC3.2.2; AC3.2.5; AC5.6.4
  - id: BR13.4
    status: cambia
    statement: Los turnos TEST de una corrida terminada sin hallazgos muestran «Analizado · sin sugerencias de revisión», distinto de «Procesando» y de «Tramo no evaluado».
    category: policy
    applies_to: [Turn]
    trigger: Corrida done sin sugerencias nuevas
    logic: SI el estado derivado del turno (BR17.1) es done sin hallazgos ENTONCES se muestra ese texto con icono ✓; con hallazgos, «Analizado» y el enlace «N hallazgos».
    violation: Prueba de nivel 0 de la función de estado derivado y Vitest.
    source: AC3.1.5
  - id: BR13.5
    status: Retirado
    statement: "Aviso de Hecho No Documentado y panel del paquete. Sale el paquete (cambio 01)."
    source: cambio 01 (DT27)
  - id: BR13.6
    status: cambia
    statement: Una sesión guiada sin turnos muestra el estado vacío, y «Enviar turno» queda deshabilitado pero enfocable con su motivo mientras el texto esté vacío.
    category: policy
    applies_to: [Turn]
    trigger: Abrir una sesión sin turnos; texto vacío
    logic: SI no hay turnos ENTONCES «Aún no hay turnos. Escribe el primer turno o pega un bloque de turnos»; SI el texto está vacío ENTONCES el botón lleva aria-disabled="true" y «Escribe el turno para enviarlo».
    violation: Prueba Vitest.
    source: AC2.2.5; AC5.6.4
  - id: BR13.7
    status: cambia
    statement: La consola de U4 cumple la base de accesibilidad y entrega la suite axe que amplían las demás unidades.
    category: constraint
    applies_to: [Turn, ReviewSuggestion, AnalysisRun]
    trigger: Niveles 0 y 3
    logic: SI axe (WCAG 2.1 AA) encuentra violaciones serious o critical en las pantallas de U4 (M3, M4 y el aviso) ENTONCES la suite falla; SI el flujo de U4 (crear sesión eligiendo perfil y consentimiento, enviar un turno, ver el hallazgo, ir a sus citas) no se recorre solo con teclado con el foco visible ENTONCES falla; SI un estado de turno, corrida, hallazgo o sesión se distingue solo por color ENTONCES falla.
    violation: Pruebas de nivel 3 (Playwright con @axe-core/playwright) y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3; US5.6

  # BR14 — Consentimiento y perfil (nuevo)
  - id: BR14.1
    statement: Crear una sesión exige el bloque de consentimiento completo; sin él, o con una constancia que falta, 422 y 0 filas.
    category: validation
    applies_to: [ConsentRecord, InterviewSessionRecord]
    trigger: POST /sessions
    logic: SI falta consentimiento, tipo o version_texto, o tipo es autoridad sin constancia, o requiere_mandato es true sin constancia_mandato, o una constancia no cumple el patrón de identificador ENTONCES 422 validation.invalid_request y 0 filas.
    violation: Prueba de nivel 1 por caso y Vitest del formulario.
    source: AC15.4.1; AC15.4.4; VE-06; C1 Consent
  - id: BR14.2
    statement: registrado_en lo fija el servidor; el valor que traiga la petición se ignora.
    category: constraint
    applies_to: [ConsentRecord]
    trigger: POST /sessions
    logic: SI la petición trae registrado_en ENTONCES se ignora; recorded_at = hora del servidor y recorded_by = el analista.
    violation: Prueba de nivel 1.
    source: C1 Consent (readOnly); VE-06
  - id: BR14.3
    statement: Sin un ConsentRecord, los turnos y las corridas se rechazan con 409 session.consent_missing y sin filas.
    category: validation
    applies_to: [Turn, AnalysisRun]
    trigger: POST turnos, transcripción, voz y corridas
    logic: SI la sesión no tiene ConsentRecord ENTONCES 409 session.consent_missing y 0 filas. Es una guardia defensiva (BR14.1 ya impide crear la sesión sin él) que se prueba con un fixture de sesión sin consentimiento; U6 y U9 reutilizan la misma guardia.
    violation: Prueba de nivel 1 con el fixture.
    source: AC15.4.2; VE-06
  - id: BR14.4
    statement: Solo se crea una sesión con un perfil aprobado del archivo de perfiles.
    category: validation
    applies_to: [InterviewSessionRecord]
    trigger: POST /sessions
    logic: SI profile_name no está en el archivo aprobado ENTONCES 422 profile.not_approved y 0 filas.
    violation: Prueba de nivel 1.
    source: AC2.1.3; C18
  - id: BR14.5
    statement: Un consentimiento que no autoriza la transferencia solo admite perfiles sin destino externo.
    category: validation
    applies_to: [InterviewSessionRecord, ConsentRecord]
    trigger: Elegir perfil en M3 y POST /sessions
    logic: SI autoriza_transferencia es false ENTONCES M3 solo ofrece perfiles sin papel commercial y la API rechaza otro con 422 profile.transfer_not_authorized antes de crear filas.
    violation: Prueba de nivel 1 y Vitest.
    source: AC15.4.5; VE-07; C1 POST /sessions
  - id: BR14.6
    statement: El perfil de una sesión no se puede cambiar, y la consola no ofrece ningún control para cambiar perfiles, proveedores, prompts ni límites.
    category: constraint
    applies_to: [InterviewSessionRecord]
    trigger: Cualquier ruta de U4
    logic: SI se intenta cambiar profile_name ENTONCES no existe ruta (C1) y el disparador de BR4.1 lo impide; M3 dice «El perfil no se puede cambiar después de crear la sesión».
    violation: Prueba de nivel 0 sobre el OpenAPI (ninguna ruta escribe perfiles) y Vitest.
    source: AC13.1.4; FR9.2; AC2.1.2
  - id: BR14.7
    statement: M3 lista solo los perfiles aprobados, ninguno preseleccionado, cada uno con su línea en lenguaje llano y sus modelos por papel en un desplegable.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: GET /profiles y M3
    logic: 'SI se abre M3 ENTONCES por perfil se muestra «Comercial: el texto sale seudonimizado del clúster» si algún papel es commercial o «Local: nada sale del clúster» si no; con chunking_enabled, «Análisis por ventanas: no busca contradicciones entre turnos separados por más de N turnos»; con same_family_warning, «El modelo que propone cada contradicción y el que la confirma son de la misma familia: la confirmación es menos independiente»; «Crear sesión» queda deshabilitado (enfocable) con «Elige un perfil para crear la sesión».'
    violation: Prueba Vitest y prueba de nivel 1 de GET /profiles.
    source: AC13.1.1; AC13.1.2; AC13.1.3; AC13.1.4
  - id: BR14.8
    statement: La cabecera de la sesión muestra perfil, los primeros 12 caracteres de config_sha256 y, por papel, si es comercial o local, con los avisos de su perfil.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: GET /sessions/{id}
    logic: SI se abre M4 ENTONCES la cabecera muestra esos datos; con perfil fragmentado, la franja de BR17.3; con misma familia, su aviso.
    violation: Prueba Vitest.
    source: AC2.1.1; AC13.1.2; AC13.1.3
  - id: BR14.9
    statement: Un servicio con un perfil inválido, o con destino externo sin anonimizador, no arranca y lo dice sin mostrar valores.
    category: validation
    applies_to: [InterviewSessionRecord]
    trigger: Arranque de session-api y de semantic-agent
    logic: SI el archivo de perfiles no cumple C18 ENTONCES session-api y semantic-agent terminan con código ≠ 0 y no pasan /readyz; SI semantic-agent tiene un perfil con destino externo y no tiene la dirección de anonymizer-proxy ENTONCES termina igual; el log nombra el ajuste sin su valor (un canary no aparece); el mismo archivo corregido arranca.
    violation: Pruebas de nivel 0 y 1 con control positivo por caso.
    source: AC13.3.1; AC11.6.1; FR14.5

  # BR15 — Corridas y AnalysisWorker (nuevo)
  - id: BR15.1
    statement: Un turno ENT se guarda sin corrida y se muestra sin estado; solo un turno TEST encola su corrida, que lleva como contexto los turnos ENT anteriores.
    category: policy
    applies_to: [Turn, AnalysisRun]
    trigger: POST /sessions/{id}/turns
    logic: SI hablante es ENT ENTONCES 202 con turn y sin run; SI es TEST ENTONCES BR5.4, y la entrada de C2 lleva todos los turnos 1..n (ENT y TEST) con su hablante.
    violation: Prueba de nivel 1 (un ENT no publica C2; el TEST siguiente lleva el ENT en entrada).
    source: P10 = B; AC2.2.3 (precisión FD-U4-01)
  - id: BR15.2
    statement: InterviewSession nunca encola una corrida de una sesión en pausa, terminada, bloqueada, con el consentimiento retirado o consolidada, ni con turnos posteriores a la retirada.
    category: policy
    applies_to: [AnalysisRun]
    trigger: Todo encolado (turno, reintento, bloque pegado, modo final)
    logic: SI blocked_code ENTONCES 409 session.blocked; SI consentimiento retirado ENTONCES 409 session.consent_withdrawn; SI terminated ENTONCES 409 session.terminated; SI consolidated ENTONCES 409 session.consolidated; SI paused ENTONCES 409 session.paused (en el turno, BR5.5 guarda sin encolar); la entrada nunca incluye un turno con submitted_at posterior a withdrawn_at.
    violation: Prueba de nivel 1 por estado (el fake registra 0 llamadas nuevas).
    source: C2; AC15.2.1; AC15.2.2; AC15.2.3; VE-10 (a); P7 = A
  - id: BR15.3
    statement: AnalysisWorker publica RunStarted al tomar una corrida, e InterviewSession la pasa a processing con actor analysis-worker.
    category: policy
    applies_to: [AnalysisRun, RunStatusChange]
    trigger: Consumo de C2; ingesta de RunStarted en veridicus:results
    logic: SI el trabajador toma un mensaje válido y vigente ENTONCES publica RunStarted (run_id, attempt, started_at) antes de la primera llamada; SI InterviewSession lo recibe y el estado vigente es queued con el mismo attempt ENTONCES RunStatusChange queued → processing, actor system analysis-worker; SI no (intento viejo, cancelada, vencida, ya processing) ENTONCES XACK sin filas.
    violation: Prueba de contrato de nivel 0 del mensaje y prueba de nivel 1 (RunStarted repetido no duplica la transición).
    source: P9 = A; C3 (precisión FD-U4-02); revisión 1 R-01 (b)
  - id: BR15.4
    statement: Al cancelar una corrida, InterviewSession la marca cancelled y escribe la clave de cancelación; el trabajador la consulta, con el plazo, antes de empezar y antes de cada llamada.
    category: policy
    applies_to: [AnalysisRun, CancellationKey]
    trigger: Pausa, terminación o retirada (U6), bloqueo (BR16.5) o plazo (BR5.8); antes de cada llamada en el trabajador
    logic: SI se cancela ENTONCES RunStatusChange → cancelled (salvo plazo, que deja error) y SET veridicus:run-cancelled:{run_id} con vencimiento deadline_at + cancel_key_margin_s; SI el trabajador ve la clave o now > deadline_at ENTONCES no llama a nada más, no publica y hace XACK. Al reconectar tras un reinicio de Redis se reescriben las claves de corridas cancelled con plazo vigente.
    violation: Prueba de nivel 1 de AC15.2.1 (fake con 0 llamadas nuevas tras pausar) y de la clave después de un reinicio de Redis.
    source: C2; CD-06; VE-10 (a); AC15.2.1; AC15.2.3
  - id: BR15.5
    statement: AnalysisWorker llama a C17 y respeta sus dos excepciones; Cancelled no publica nada e InputRejected manda el mensaje a fallidos.
    category: policy
    applies_to: [AnalysisRun]
    trigger: Corrida en AnalysisWorker
    logic: analyze(entrada, config, gateway, cancelled) con cancelled = BR15.4; SI devuelve Salida ENTONCES publica C3 RunResult; SI lanza Cancelled ENTONCES XACK sin publicar; SI lanza InputRejected ENTONCES el mensaje va a veridicus:runs:failed y la corrida termina en error analysis.system (BR5.8).
    violation: Prueba de nivel 1 por rama con fakes.
    source: C17
  - id: BR15.6
    statement: AnalysisWorker no escribe en la base, no reintenta por su cuenta y confirma el mensaje de C2 solo después de publicar el resultado.
    category: constraint
    applies_to: [AnalysisRun]
    trigger: Corrida en AnalysisWorker
    logic: SI termina una corrida ENTONCES XADD a veridicus:results y después XACK en veridicus:runs; semantic-agent no tiene credenciales de PostgreSQL; un fallo de publicación deja el mensaje pendiente para XAUTOCLAIM.
    violation: Prueba de nivel 0 de import-linter (semantic-agent no importa controladores de base) y prueba de nivel 1 que corta Redis entre XADD y XACK.
    source: ADR-002; C2; AC3.2.1
  - id: BR15.7
    statement: La raíz de composición de semantic-agent llama a check_ready() del cliente de anonymizer-proxy antes de construir el gateway cuando el perfil tiene un destino externo.
    category: validation
    applies_to: [AnalysisRun]
    trigger: Arranque de semantic-agent
    logic: SI algún perfil aprobado tiene un papel commercial ENTONCES check_ready() de C21 antes del gateway; SI falla ENTONCES el proceso no pasa /readyz y no consume la cola; con solo perfiles locales no se llama.
    violation: Prueba de nivel 1 con el proxy detenido.
    source: C21; AC11.6.1; B3 (definición de terminado, punto 5)
  - id: BR15.8
    statement: semantic-agent no puede importar ni instalar libs-anonymizer ni sus adaptadores nativos comerciales.
    category: constraint
    applies_to: [AnalysisRun]
    trigger: Nivel 0 en cada PR
    logic: SI el contrato semantic-agent-no-anonymizer de import-linter encuentra un import de libs.anonymizer o libs.anonymizer.providers, o el lockfile de semantic-agent incluye libs-anonymizer, o en la imagen construida import libs.anonymizer no termina en ModuleNotFoundError, o tras arrancar sys.modules contiene libs.anonymizer ENTONCES la CI falla; control negativo con un import sembrado.
    violation: Pruebas de nivel 0 (import-linter, lockfile, imagen y sys.modules).
    source: AC11.6.4 (mitad de U4); CD-04; C13; FD-U10-03; unit-of-work (revisión 07, R-02)
  - id: BR15.9
    statement: La CLI y el trabajador producen la misma salida para la misma transcripción y el mismo fake.
    category: constraint
    applies_to: [RunAttempt]
    trigger: Nivel 1
    logic: SI la CLI de U11 y AnalysisWorker analizan la misma entrada con el mismo fake del ModelGateway ENTONCES las salidas coinciden salvo fecha y las fechas del registro.
    violation: Prueba de nivel 1 de equivalencia.
    source: AC2.2.7; FR13.1
  - id: BR15.10
    statement: Una sola cola FIFO lleva las corridas incrementales y finales.
    category: policy
    applies_to: [AnalysisRun]
    trigger: Publicar C2
    logic: SI se encola cualquier corrida ENTONCES va a veridicus:runs en orden de llegada; no hay prioridad por modo.
    violation: Prueba de nivel 1 (una final encolada después de una incremental se procesa después).
    source: Propuesta de esta etapa (FD-U4-09); C2
  - id: BR15.11
    statement: Tras la muerte de un trabajador la corrida se repite entera, y el registro guarda solo las llamadas de la entrega que publica.
    category: policy
    applies_to: [ModelCall, RunAttempt]
    trigger: XAUTOCLAIM de un mensaje pendiente
    logic: SI otro trabajador reclama el mensaje ENTONCES vuelve a llamar desde el principio; las llamadas de la entrega muerta no llegan a C3 y no quedan en ModelCall. Es una limitación declarada del costo registrado.
    violation: Prueba de nivel 1 que mata al trabajador y cuenta las filas de ModelCall.
    source: Propuesta de esta etapa (FD-U4-10); AC2.2.4

  # BR16 — Errores, incidente y bloqueo (nuevo)
  - id: BR16.1
    statement: Un resultado de un intento viejo, de una corrida cancelled o de una ya en error por plazo se confirma y se descarta sin filas, salvo el incidente.
    category: policy
    applies_to: [RunAttempt]
    trigger: Consumo de C3
    logic: SI attempt < intento vigente, o el estado vigente es cancelled, o es error con analysis.system, o ya existe RunAttempt (run_id, attempt) ENTONCES XACK y 0 filas de resultado; ANTES de descartar se aplica BR16.4 al registro.
    violation: Prueba de nivel 1 por caso, incluido un resultado descartado con una llamada externa sin anonimizar.
    source: C3; BR16.4 (propuesta FD-U4-11)
  - id: BR16.2
    statement: Cada intento ingerido guarda su registro completo de C6, sin texto.
    category: constraint
    applies_to: [RunAttempt, ModelCall, DiscardedCandidate]
    trigger: Ingesta de C3
    logic: SI la salida cumple C6 ENTONCES RunAttempt guarda prompt_sha256, analyzer_version, fragmentado (activo, ventana, solapamiento), tokens, costo_estimado y tabla_precios; una ModelCall por llamada, con external derivado de effective_config del papel; un DiscardedCandidate por descarte.
    violation: Prueba de nivel 1 de AC12.5.1 y AC3.7.1 con un fake que registra cada llamada.
    source: AC12.5.1; AC12.5.2; AC3.7.1; FR15.3; VE-14
  - id: BR16.3
    statement: Cada intento guarda si pasó por el anonimizador; true solo si todas sus llamadas externas lo hicieron, nulo si no tuvo ninguna externa.
    category: calculation
    applies_to: [RunAttempt]
    trigger: Ingesta de C3
    logic: anonymized = nulo SI no hay ModelCall con external; true SI todas las externas tienen anonymized true; false en otro caso (y BR16.4 bloquea).
    violation: Prueba de nivel 0 con 100 % de ramas.
    source: AC11.3.8; VE-14; AUTONOMIA-04
  - id: BR16.4
    statement: Un incidente de anonimización bloquea la sesión con anonymizer.incident, registra el incidente solo con IDs y no guarda ninguna sugerencia de esa corrida.
    category: policy
    applies_to: [InterviewSessionRecord, AnonymizationIncident, SessionStatusChange, RunAttempt]
    trigger: Ingesta de C3 (vigente o descartado) o de un registro inyectado en la prueba
    logic: SI error.codigo es incidente_anonimizacion O alguna llamada tiene external true y anonimizado false ENTONCES en una transacción, AnonymizationIncident, blocked_code = anonymizer.incident, status → blocked si estaba open, paused o suspended (si ya estaba finalized o terminated, conserva su status y solo fija blocked_code), SessionStatusChange con code anonymizer.incident y actor system analysis-worker, la corrida en error con anonymizer.incident y 0 sugerencias aunque la salida traiga hallazgos; luego BR16.5.
    violation: Prueba de nivel 0 de la decisión (100 % de ramas) y de nivel 1 de AC11.3.8 y del caso (i) de AC3.2.1 con un registro inyectado.
    source: AC11.3.8; AC3.2.1; VE-14; CD-01; CD-11; P7 = A; AUTONOMIA-04
  - id: BR16.5
    statement: Una sesión bloqueada no lanza ni encola ninguna corrida nunca más, cancela las que tenía en cola o en proceso y sigue siendo legible, decidible, finalizable y consolidable.
    category: policy
    applies_to: [InterviewSessionRecord, AnalysisRun]
    trigger: Fijar blocked_code; toda petición posterior
    logic: SI blocked_code se fija ENTONCES las corridas queued o processing de la sesión pasan a cancelled con la clave de BR15.4; turnos nuevos, reintentos, bloques pegados y modo final responden 409 session.blocked; GET de la sesión, decisiones de U5, finalizar (U6) y consolidar (U7) siguen; no hay ruta para desbloquear en el MVP.
    violation: Prueba de nivel 1 (después del bloqueo, el fake registra 0 llamadas; las rutas de lectura y decisión responden 200).
    source: P7 = A; AC11.3.8; CD-11; AUTONOMIA-04
  - id: BR16.6
    statement: Solo se bloquea la sesión del incidente.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: Incidente
    logic: SI hay un incidente en la sesión S ENTONCES solo S se bloquea; otras sesiones del mismo perfil o del mismo analista siguen.
    violation: Prueba de nivel 1 con dos sesiones del mismo perfil.
    source: P8 = A
  - id: BR16.7
    statement: Con el anonimizador caído o un rechazo del proxy, solo falla la corrida; la sesión conserva su estado y el dueño puede reintentar.
    category: policy
    applies_to: [AnalysisRun, InterviewSessionRecord]
    trigger: Salida error con anonimizador_no_disponible
    logic: SI error.codigo es anonimizador_no_disponible (incluidos los 409 anonymizer.profile_mismatch y 422 anonymizer.destination_rejected de C21) ENTONCES la corrida en error con analysis.anonymizer_unavailable y la sesión sin cambios; el reintento sigue BR5.9.
    violation: Prueba de nivel 1 con el proxy detenido y con cada rechazo.
    source: P6 = A; AC3.2.5; CD-02; UG-02
  - id: BR16.8
    statement: Si propose rechaza durante la ingesta, la corrida pasa a error con analysis.system, el mensaje se confirma y no se guarda ninguna sugerencia.
    category: policy
    applies_to: [AnalysisRun, ReviewSuggestion]
    trigger: SuggestionProposer.propose lanza review.round_locked u otro rechazo
    logic: SI propose rechaza ENTONCES se revierte la parte de sugerencias, la corrida queda en error con analysis.system (actor system analysis-worker) con su RunAttempt y su registro, y XACK.
    violation: Prueba de nivel 1 con todas las rondas bloqueadas.
    source: Propuesta de esta etapa (FD-U4-06); C10; revisión 1 R-02
  - id: BR16.9
    statement: Reintentar una corrida de una sesión consolidada responde 409 session.consolidated.
    category: validation
    applies_to: [AnalysisRun]
    trigger: POST /sessions/{id}/runs/{run_id}/retry
    logic: SI la sesión está consolidated ENTONCES 409 session.consolidated y 0 filas; una corrección (U7) abre su propia ronda y no reintenta corridas.
    violation: Prueba de nivel 1.
    source: Propuesta de esta etapa (FD-U4-05); revisión 1 R-02

  # BR17 — Estado en pantalla, modo final y registro (nuevo)
  - id: BR17.1
    statement: El estado de un turno no se guarda; se deriva del último intento de la última corrida incremental que lo cubre o, en una sesión importada, de la corrida final.
    category: calculation
    applies_to: [Turn, AnalysisRun]
    trigger: GET /sessions/{id} y consola
    logic: SI el turno es ENT ENTONCES sin estado; SI es TEST ENTONCES estado = estado vigente de la última corrida incremental con desde_turno <= n <= hasta_turno (queued «En cola», processing «Procesando», done «Analizado», error «Tramo no evaluado», cancelled «Análisis cancelado»); SI la sesión es importada ENTONCES el de la última corrida final; el modo final de una guiada se muestra en su franja, no en cada turno.
    violation: Prueba de nivel 0 de la función (todas las combinaciones) y Vitest.
    source: AC2.2.1; AC3.1.5; propuesta de esta etapa (FD-U4-04)
  - id: BR17.2
    statement: Si el último modo final lanzado termina bien, un tramo incremental en error ya no cuenta como «Tramo no evaluado».
    category: policy
    applies_to: [AnalysisRun]
    trigger: Corrida final done; consola y SessionReader
    logic: SI la última corrida final por requested_at está done ENTONCES cada corrida incremental en error se muestra solo en «Corridas» con su error y «Cubierto por el modo final», sin «Tramo no evaluado» ni «Reintentar tramo», y SessionReader.snapshot la marca covered_by_final; SI se lanza otra final, o la última termina en error o cancelada, la cobertura se pierde.
    violation: Prueba de nivel 0 de la función y de nivel 1 del snapshot.
    source: P11 = A; AC3.2.2; C11
  - id: BR17.3
    statement: Una corrida en modo fragmentado muestra su limitación con la ventana y el solapamiento registrados.
    category: policy
    applies_to: [RunAttempt]
    trigger: RunAttempt con fragmented true
    logic: SI la última corrida terminada tiene fragmented ENTONCES la franja informativa de M4 dice «Análisis por ventanas de N turnos (solapamiento de M). No se buscaron contradicciones entre turnos separados por más de N turnos» con N = window y M = overlap; siempre visible y sin cerrar.
    violation: Prueba de nivel 1 del registro y Vitest de la franja.
    source: AC3.7.1; AC13.1.3
  - id: BR17.4
    statement: El registro de modelos de una corrida se consulta en solo lectura, sin texto, con sus totales y «sin precio» para un modelo sin precio.
    category: policy
    applies_to: [ModelCall, RunAttempt]
    trigger: GET /sessions/{id}/runs/{run_id}/model-calls
    logic: SI se abre una corrida ENTONCES se listan papel, proveedor, modelo, versión, esfuerzo o cuantización, motor, llamadas, tokens y costo estimado con su total; una corrida sin llamadas dice «Aún no hay llamadas registradas»; un modelo sin precio dice «sin precio»; la respuesta nunca trae texto enviado ni recibido.
    violation: Prueba de nivel 1 de la ruta (esquema C1 ModelCall sin campos de texto) y Vitest.
    source: AC12.5.3; AC12.5.2
  - id: BR17.5
    statement: Una cita en un turno ENT o plegado lleva su aviso con texto e icono.
    category: policy
    applies_to: [ReviewSuggestion]
    trigger: Renderizado de cita_a o cita_b con avisos
    logic: 'SI avisos contiene turno_entrevistador ENTONCES «ⓘ Cita en un turno del entrevistador»; SI contiene turno_plegado ENTONCES «ⓘ Cita en un turno plegado: en la versión analizada, las partes de este turno que no tratan los hechos centrales se resumieron como [pasaje plegado: N palabras]. La cita está en la parte visible del turno».'
    violation: Prueba Vitest y de nivel 1 (los avisos se guardan con la sugerencia).
    source: AC3.1.4; propuesta de esta etapa (FD-U4-15)

  # BR18 — Aviso de propósito limitado (nuevo)
  - id: BR18.1
    statement: Toda pantalla de la consola, incluido el inicio de sesión, muestra el aviso de VE-01 leído de C8 en ejecución.
    category: policy
    applies_to: [InterviewSessionRecord]
    trigger: Cualquier pantalla
    logic: GET /notice es pública (security vacía) y devuelve text y version de notice.v1; la consola muestra una franja fija bajo la cabecera con ese texto y no guarda copia; si GET /notice falla, se muestra el error del sistema en la franja y no se inventa el texto.
    violation: Prueba Vitest por pantalla y de nivel 3.
    source: AC15.5.1; VE-01; propuesta de esta etapa (FD-U4-08)
  - id: BR18.2
    statement: Un cambio del texto del aviso que pierde la frase base hace fallar la prueba.
    category: validation
    applies_to: [InterviewSessionRecord]
    trigger: Nivel 0
    logic: SI el texto servido por GET /notice no contiene la frase base completa de AC15.5.1 ENTONCES la prueba falla.
    violation: Prueba de nivel 0 con un fixture que recorta la frase.
    source: AC15.5.3; C8

  # BR19 — Puertos hacia otras unidades (nuevo)
  - id: BR19.1
    statement: InterviewSession implementa PendingSessions.count_pending, que cuenta las sesiones del usuario en cualquier estado distinto de consolidated.
    category: calculation
    applies_to: [InterviewSessionRecord]
    trigger: Cambio de rol en U3
    logic: count_pending(uow, owner_user_id) = número de InterviewSessionRecord del dueño con status distinto de consolidated; reemplaza el adaptador por defecto que devolvía 0.
    violation: Prueba de nivel 1 con sesiones reales en cada estado (entra con el PR de U4, como pidió U3).
    source: FD-U3-04
  - id: BR19.2
    statement: Toda escritura que cambia una sesión toma los bloqueos en el orden usuario → sesión → ronda y sube change_cursor de la sesión antes de bloquear la ronda.
    category: constraint
    applies_to: [InterviewSessionRecord, ReviewRound]
    trigger: Toda petición o ingesta que cambia estado
    logic: SI una operación cambia la sesión ENTONCES bloqueo compartido del usuario (en peticiones), luego change_cursor.bump con bloqueo exclusivo de la fila de la sesión, luego, si hace falta, open_round(for_update=True); la ingesta no tiene usuario y empieza por la sesión.
    violation: Prueba de nivel 1 con ingesta y decisión concurrentes (sin interbloqueo y sin cambios perdidos en el sondeo).
    source: FD-U3-13; regla aprendida de NFR Design en project.md; C11 open_round
  - id: BR19.3
    statement: InterviewSession implementa Purgeable.purge_session y borra solo lo suyo, devolviendo IDs y nunca texto.
    category: constraint
    applies_to: [InterviewSessionRecord, Turn, AnalysisRun, ModelCall, ConsentRecord]
    trigger: Job de retención de U13 (lo lanza el humano)
    logic: SI el Job llama purge_session ENTONCES con el usuario veridicus_retention se borran ModelCall, DiscardedCandidate, RunAttempt, RunStatusChange, AnalysisRun, Turn, ConsentRecord, SessionStatusChange y por último InterviewSessionRecord; AnonymizationIncident sobrevive sin clave foránea; devuelve los IDs borrados. U4 crea retention_days y retention_until vacíos.
    violation: Prueba de nivel 1 con el usuario de retención y otra que comprueba que veridicus_app no puede borrar.
    source: C24; AC15.7.2 (parte de U4); propuesta FD-U4-12
  - id: BR19.4
    statement: InterviewSession implementa SessionReader.snapshot con corridas, registro de modelos, modo fragmentado, cobertura del modo final y bloqueo.
    category: constraint
    applies_to: [InterviewSessionRecord, AnalysisRun, ModelCall]
    trigger: ReviewReport (U7)
    logic: snapshot devuelve estado, dueño, perfil y config_sha256, finalized_at, turnos con hablante, página y estado plegado, corridas con su estado vigente, intento, registro y covered_by_final (BR17.2), cuántas siguen queued o processing y blocked_code; sin datos del consentimiento.
    violation: Prueba de contrato de nivel 0 contra C11 y de nivel 1.
    source: C11; P11 = A
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1–BR3 Escenarios | Retirado | — (cambio 01) |
| BR4 Sesión | BR4.1–BR4.3 | Perfil o huella que cambian a mitad de sesión; acciones de otro rol o dueño |
| BR5 Turnos y encolado | BR5.1–BR5.9 | Turnos fuera del límite, numeración con huecos, duplicados, mensajes mal formados, plazos, reintentos |
| BR6–BR7 Umbral y evaluación | Retirado | — (cambio 01) |
| BR8 Validación en la ingesta | BR8.1, BR8.2, BR8.4–BR8.6 (BR8.3 Retirado) | AUTONOMIA-05 y AUTONOMIA-03 en la segunda línea: nada parcial, nada sin sus campos, nada con vocabulario prohibido |
| BR9 Configuración | BR9.1 (BR9.2 Retirado) | El trabajador usa la configuración de la sesión |
| BR10 Paquete | Retirado | — (cambio 01) |
| BR11 Ingesta y sugerencias | BR11.1–BR11.4 | Filas sueltas, duplicados por par, auditoría |
| BR12 Vocabulario | BR12.1–BR12.4 | AUTONOMIA-03 en salida e interfaz con el escáner de U11 |
| BR13 Consola | BR13.1–BR13.4, BR13.6, BR13.7 (BR13.5 Retirado) | Interrupciones, estados ambiguos, accesibilidad |
| BR14 Consentimiento y perfil | BR14.1–BR14.9 | VE-06, VE-07; perfiles no aprobados o sin anonimizador |
| BR15 Corridas y trabajador | BR15.1–BR15.11 | P9, P10, VE-10 (a), CD-04 |
| BR16 Errores e incidente | BR16.1–BR16.9 | AUTONOMIA-04, VE-14, P6–P8 |
| BR17 Estado y registro | BR17.1–BR17.5 | P11, US3.7, US12.5, AC3.1.4 |
| BR18 Aviso | BR18.1–BR18.2 | VE-01 |
| BR19 Puertos | BR19.1–BR19.4 | Lo que piden U3, U7 y U13 |

Reglas vigentes: 72 (32 que siguen, de ellas 30 con cambios, y 40 nuevas). Retiradas: 27.
