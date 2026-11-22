# Reglas de negocio — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02** (y las revisiones 3 de
Inception). Sustituye a la revisión 1 del 2026-10-02.
- Las reglas conservan su ID. Las que salen quedan con `status: Retirado` y no se renumeran (regla de
  `project.md`). Las que siguen y cambian llevan `status: cambia`; las nuevas, `status: nuevo`.
- **Salen:** BR1.1–BR1.6 (segunda lectura del juez con pasajes; la sustituye la permutación del verificador
  que diseñó U11), BR2.1–BR2.6 (pregunta sugerida por el Paquete de Contexto de Traspaso), BR3.1–BR3.3
  (indicio afectivo, US11.1 Retirada) y BR4.3 (rótulos de la pregunta y de la permutación).
- **Cambian:** BR4.1, BR4.2 y BR4.4 (vocabulario, esquema y accesibilidad), reescritas para la aclaración.
- **Entran:** BR4.5–BR4.7 (rótulos, botones deshabilitados y anuncios agregados, que cubren AC5.5.4, AC5.6.4
  y AC5.6.5), BR5.1–BR5.17 (aclaración neutra, US10.3) y BR6.1–BR6.5 (permutación en producción, US10.5).
- Hallazgos de `reviews/review-01.md`: R-01, R-02, R-03 y R-05 caducan con las reglas retiradas; R-04 se
  cierra con BR5.11 y BR5.12, y R-06 con BR5.13.

**Insumos.** Los mismos de `entities.md`. Las reglas de otras unidades se citan por descripción, nunca por
su ID.

**Cómo se prueban.** Salvo que la regla diga otra cosa, en **nivel 0**, sin red, con *fakes* deterministas
del `ModelGateway` y datos sintéticos, cada una con su control negativo. La validación de la aclaración
(BR5.3–BR5.8) es **módulo guardia** de AUTONOMIA-03 y VE-05: código puro en `domain/` de
`libs/incoherence_analyzer/`, con 100 % de ramas, y sus pruebas se escriben primero y se ejecutan en rojo
(team.md, Ordering). La máquina de estados de ConductorObservation (BR5.12) también es guardia (decisión
humana, AUTONOMIA-03). Cada prueba se cita en el plan de tareas por el ID de su regla.

```yaml
rules:
  # BR1 — Segunda lectura del juez (Retirado, cambio 01)
  - id: BR1.1
    status: Retirado
    statement: "Segunda lectura del juez con los pasajes en orden inverso. Sale: no hay pasajes; la permutación es la del verificador de U11."
    source: cambio 01 (DT27); iteracion2 P12 = A
  - id: BR1.2
    status: Retirado
    statement: "Alerta solo si las dos lecturas califican incongruente. Sale con las calificaciones."
    source: cambio 01 (DT27)
  - id: BR1.3
    status: Retirado
    statement: "Afirmación no sostenida al invertir el orden como «no documentada». Sale con el Hecho No Documentado."
    source: cambio 01 (DT27)
  - id: BR1.4
    status: Retirado
    statement: "La permutación nunca alerta bajo el umbral. Sale con el umbral de similitud."
    source: cambio 01 (DT27)
  - id: BR1.5
    status: Retirado
    statement: "Validación de la segunda lectura del juez. Sale con la segunda lectura."
    source: cambio 01 (DT27)
  - id: BR1.6
    status: Retirado
    statement: "permutation_applied y las dos calificaciones en C3. Sale: el registro de llamadas de C6 ya muestra las dos llamadas."
    source: cambio 01 (DT27)

  # BR2 — Pregunta sugerida (Retirado, cambio 01)
  - id: BR2.1
    status: Retirado
    statement: "Sin pregunta en un turno con afirmaciones no documentadas. Sale con el Hecho No Documentado."
    source: cambio 01 (DT27)
  - id: BR2.2
    status: Retirado
    statement: "Pregunta generada a partir de los pasajes del turno con un prompt propio. Sale con los pasajes."
    source: cambio 01 (DT27)
  - id: BR2.3
    status: Retirado
    statement: "Pregunta inválida descartada sin afectar el turno. La sustituye BR5.7."
    source: cambio 01 (DT27)
  - id: BR2.4
    status: Retirado
    statement: "Decisión del dueño sobre /questions/{id}/decision. La sustituyen BR5.11 y BR5.12."
    source: cambio 01 (DT27)
  - id: BR2.5
    status: Retirado
    statement: "Sin aprobación no hay audio ni registro como formulada. La sustituye BR5.14."
    source: cambio 01 (DT27)
  - id: BR2.6
    status: Retirado
    statement: "Historial de decisiones de preguntas. Lo sustituye BR5.13."
    source: cambio 01 (DT27)

  # BR3 — Indicio afectivo (Retirado, US11.1)
  - id: BR3.1
    status: Retirado
    statement: "Texto fijo en el paquete ante palabras emocionales. Sale con US11.1 (WON'T por DT15)."
    source: cambio 01 (DT27); US11.1 Retirada
  - id: BR3.2
    status: Retirado
    statement: "Escaneo del texto del indicio y de la lista. Sale con US11.1."
    source: US11.1 Retirada
  - id: BR3.3
    status: Retirado
    statement: "Lista de palabras emocionales versionada. Sale con US11.1."
    source: US11.1 Retirada

  # BR4 — Vocabulario, esquema y accesibilidad en lo que añade U8 (US5.5 y US5.6 cruzan esta unidad)
  - id: BR4.1
    status: cambia
    statement: El tema de cada aclaración y todas las cadenas de la interfaz que añade U8 pasan el escaneo de vocabulario prohibido de C8, con su control negativo.
    category: validation
    applies_to: [ClarificationCandidate, ConductorObservation]
    trigger: Armado de la aclaración (BR5.6), ingesta (BR5.9) y suite de nivel 0 del catálogo de mensajes
    logic: SI el tema contiene un término de la lista vigente de C8 ENTONCES la aclaración se quita en la biblioteca y, si aun así llega a la ingesta, la corrida entera queda en analysis.invalid_output. SI una cadena del panel (rótulo, botones, estados, motivos, mensajes de error) contiene un término ENTONCES la suite falla; el aviso de VE-01 no forma parte de las cadenas de U8.
    violation: Fixture de tema «el compareciente miente» (se quita, con control negativo de un tema limpio que sale); fixture de cadena del catálogo con cada término de la lista, incluida «prueba» fuera del aviso (la suite falla); escaneo de la interfaz renderizada del panel en el E2E de nivel 3.
    source: AC5.5.1; AC5.5.2; AC5.5.5; AC5.5.6; C8 (scanned); VE-02
  - id: BR4.2
    status: cambia
    statement: El esquema de la aclaración es estricto y no tiene campos de veracidad.
    category: constraint
    applies_to: [ClarificationCandidate, ConductorObservation]
    trigger: Validación de la salida en la biblioteca y en la ingesta
    logic: SI un elemento de observaciones_conductor trae un campo distinto de tipo, tema y turnos (p. ej. is_truthful, credibilidad) ENTONCES en la biblioteca se quita con la regla schema, y en la ingesta la salida no cumple C6 y la corrida entera queda en analysis.invalid_output; el modelo de ConductorObservation de C1 tampoco admite campos de veracidad.
    violation: Fixture con is_truthful en un elemento (rechazado en los dos puntos) y prueba de que el esquema de C1 tiene additionalProperties false.
    source: AC5.5.3; AC10.3.1; AUTONOMIA-03
  - id: BR4.3
    status: Retirado
    statement: "Rótulos de la pregunta sugerida y de la permutación. La sustituye BR4.5."
    source: cambio 01 (DT27)
  - id: BR4.4
    status: cambia
    statement: El panel de aclaraciones cumple la base de accesibilidad de U4.
    category: constraint
    applies_to: [ConductorObservation]
    trigger: Suite axe de U4 (nivel 3) y pruebas Vitest (nivel 0)
    logic: SI axe encuentra violaciones serious o critical en M4 con el panel en sus estados (pendiente, aprobada, descartada, solo lectura), SI «Aprobar» o «Descartar» no se activan con Tab y Enter o Espacio con el foco visible, o SI el estado de una aclaración se distingue solo por color ENTONCES la prueba falla. Cada estado se nombra con texto («Pendiente», «Aprobada», «Descartada») e icono.
    violation: El panel entra en la suite axe de U4 con sus cuatro estados; prueba de teclado en el E2E; prueba Vitest que retira el color y exige el texto del estado.
    source: AC5.6.1; AC5.6.2; AC5.6.3
  - id: BR4.5
    status: nuevo
    statement: La aclaración no es un resultado y no añade rótulos de resultado.
    category: constraint
    applies_to: [ConductorObservation]
    trigger: Renderizado del panel
    logic: SI se muestra una aclaración ENTONCES va en un bloque propio al pie del panel de hallazgos, con el rótulo informativo «Aclaración sugerida · requiere tu decisión», fuera de la lista de sugerencias de revisión y sin ninguno de los rótulos de resultado; la lista de rótulos de resultado de la interfaz sigue siendo exactamente la de U1.
    violation: Prueba Vitest que recorre la pantalla con aclaraciones y compara los rótulos de resultado con el catálogo de U1; control negativo con una aclaración rotulada «Sugerencia de revisión».
    source: AC5.5.4; mockups §6.11
  - id: BR4.6
    status: nuevo
    statement: Un botón del panel que no se puede usar queda enfocable y anuncia su motivo.
    category: constraint
    applies_to: [ConductorObservation]
    trigger: Renderizado con una sesión que no admite la decisión (BR5.12)
    logic: SI «Aprobar» o «Descartar» no se pueden usar por el estado de la sesión ENTONCES llevan aria-disabled="true" (no disabled nativo), reciben el foco con Tab y aria-describedby apunta al texto del motivo.
    violation: Prueba Vitest con una sesión con el consentimiento retirado («Aprobar» deshabilitado con motivo, «Descartar» activo) y con una sesión finalizada (los dos deshabilitados).
    source: AC5.6.4
  - id: BR4.7
    status: nuevo
    statement: La llegada de aclaraciones solo se anuncia como un cambio agregado.
    category: constraint
    applies_to: [ConductorObservation]
    trigger: Sondeo de la sesión que trae aclaraciones nuevas o decididas
    logic: 'SI cambia el número de aclaraciones pendientes ENTONCES una región aria-live="polite" anuncia una sola vez el contador («Aclaraciones sugeridas pendientes: N»), sin mover el foco y sin leer el tema; el tema y los turnos se leen al enfocar la aclaración.'
    violation: Prueba Vitest con un sondeo que trae tres aclaraciones (un anuncio, con el contador 3) y con una decisión (un anuncio con el contador nuevo); el foco no cambia.
    source: AC5.6.5; punto 8 de las preguntas

  # BR5 — Aclaración neutra (US10.3)
  - id: BR5.1
    status: nuevo
    statement: Cada hallazgo emitido en una corrida incremental con estado ok da una aclaración armada de forma determinista, sin llamar a ningún modelo.
    category: calculation
    applies_to: [ClarificationCandidate]
    trigger: Consolidación de la salida en la biblioteca, después de numerar los hallazgos y armar el registro, y antes de validar la salida contra C6
    logic: Por cada hallazgo de la salida, tema = su hecho con los espacios normalizados y turnos = los turnos de cita_a y cita_b sin repetir, en orden numérico; tipo = aclaracion_neutra. No hay llamada nueva, ni cambio de prompt ni de contrato. Corre igual en la CLI y en semantic-agent.
    violation: Prueba con un gateway fake que cuenta llamadas (mismas llamadas con y sin el módulo); prueba de equivalencia CLI–trabajador con la misma entrada incremental (mismas observaciones_conductor).
    source: FR10.3; respuesta P4 = A; AC2.2.7 (equivalencia CLI–trabajador)
  - id: BR5.2
    status: nuevo
    statement: Solo una salida incremental con estado ok lleva observaciones_conductor.
    category: constraint
    applies_to: [ClarificationCandidate]
    trigger: Consolidación de la salida
    logic: SI modo es incremental y estado es ok ENTONCES la salida trae observaciones_conductor (vacío si no hay ninguna); SI modo es final ENTONCES el campo no se emite; SI estado es error, también cuando la validación contra C6 de la salida armada falla, ENTONCES el campo no se emite (C6, regla 7).
    violation: Una prueba por caso (incremental ok, final ok, incremental en error por el juez y salida armada que no cumple C6).
    source: FR10.3; C6 (observaciones_conductor y regla 7)
  - id: BR5.3
    status: nuevo
    statement: Primera validación — la aclaración cumple el esquema cerrado de C6.
    category: validation
    applies_to: [ClarificationCandidate]
    trigger: Validación de cada candidata, en el orden BR5.3, BR5.4, BR5.5, BR5.6
    logic: "SI no es exactamente { tipo: aclaracion_neutra, tema con al menos un carácter que no sea espacio, turnos con al menos un elemento ^T[0-9]+$ } ENTONCES se quita con la regla schema."
    violation: Fixtures con tema vacío, turnos vacío, un turno mal formado, otro tipo y un campo extra (los cinco se quitan).
    source: AC10.3.1; C6
  - id: BR5.4
    status: nuevo
    statement: Segunda validación — la aclaración cumple la regla de DT23 de las aclaraciones neutras.
    category: validation
    applies_to: [ClarificationCandidate]
    trigger: Después de BR5.3
    logic: SI el tema menciona la contradicción («contradicción», «contradice», «incoherencia»), contiene «antes dijo» o una de sus variantes (las frases de neutral-clarification de C8, más «antes mencionó» y «había dicho» por AC10.3.4), o cita un turno («T<n>», «turno <n>») ENTONCES se quita con la regla correspondiente (mentions_contradiction, phrases o cites_turn). La comparación usa la forma del escaneo (palabra completa, sin mayúsculas ni tildes) y la regla la lee de contracts/integrity/neutral-clarification de U1 en ejecución.
    violation: Un fixture por término y por frase, cada uno con su control negativo (el mismo tema sin el término sale); «tema sobre el turno 3» y «T3» se quitan, «tercer día» sale.
    source: AC10.3.4; VE-05; DT23; C8 (neutral-clarification); regla de aclaración neutra de U1
  - id: BR5.5
    status: nuevo
    statement: Tercera validación — el tema no contiene el texto de ninguna cita de la salida.
    category: validation
    applies_to: [ClarificationCandidate]
    trigger: Después de BR5.4
    logic: Se normalizan tema y citas (espacios colapsados, sin mayúsculas, sin tildes) y cada cita se parte en sus fragmentos por « […] ». SI el tema contiene, como palabras completas, el texto de un fragmento de cita_a o cita_b de cualquier hallazgo de la misma salida (incluido el de origen), ENTONCES se quita con quote_text; SI comparte 5 o más palabras seguidas con uno de esos fragmentos ENTONCES se quita con quote_overlap.
    violation: Control negativo por caso — tema igual a una cita, tema que contiene una cita corta, tema con 5 palabras seguidas de una cita (se quita), con 4 (sale), con la cita de otro hallazgo (se quita) y con mayúsculas o tildes distintas (se quita).
    source: AC10.3.2 (meta 0 %); VE-05 («nunca contiene una cita»); punto 3 de las preguntas
  - id: BR5.6
    status: nuevo
    statement: Cuarta validación — el tema pasa el escaneo de vocabulario prohibido sin tramos excluidos.
    category: validation
    applies_to: [ClarificationCandidate]
    trigger: Después de BR5.5
    logic: SI el escáner de C8 (de U11) encuentra un término en el tema, llamado sin fuentes literales porque el tema ya no puede contener citas, ENTONCES se quita con forbidden_vocabulary.
    violation: Fixture con «miente» en el tema (se quita) y con «miente» entre «» en el tema (también se quita, porque no hay tramo excluido).
    source: AC5.5.1; AC5.5.2; C8 (scanned salida.observaciones_conductor[].tema)
  - id: BR5.7
    status: nuevo
    statement: Una aclaración que no pasa se quita de la salida sin afectar a los hallazgos y queda registrada como descartada, solo con IDs.
    category: policy
    applies_to: [ClarificationCandidate, ClarificationDiscardEvent]
    trigger: Primera validación que falla
    logic: SI una de BR5.3–BR5.6 falla ENTONCES la candidata no se muestra (no sale en observaciones_conductor), no se evalúan las validaciones siguientes, los hallazgos y el estado de la salida no cambian, y se emite un ClarificationDiscardEvent con run_id, source_finding_id y la regla; nunca con el tema, las citas ni texto de turnos.
    violation: Prueba con una salida de dos hallazgos donde la aclaración de uno falla (sale la otra y los dos hallazgos); captura del log que comprueba campos y ausencia de texto (el tema sembrado no aparece).
    source: AC10.3.4 («no se muestra y se registra como descartada»); VE-05; team.md (logs solo con IDs)
  - id: BR5.8
    status: nuevo
    statement: Dentro de una salida no hay dos aclaraciones con los mismos turnos y el mismo tema normalizado.
    category: constraint
    applies_to: [ClarificationCandidate]
    trigger: Después de validar todas las candidatas
    logic: SI dos aclaraciones válidas tienen los mismos turnos y el mismo tema_key ENTONCES se conserva la del hallazgo de menor id y la otra se omite sin evento (no es un descarte por regla).
    violation: Prueba con dos hallazgos del mismo hecho y los mismos turnos (una aclaración).
    source: punto 5 de las preguntas (deduplicación)
  - id: BR5.9
    status: nuevo
    statement: La ingesta repite las validaciones como segunda línea; una aclaración inválida deja la corrida entera en error.
    category: validation
    applies_to: [ConductorObservation]
    trigger: Ingesta de un resultado (C3) en session-api, después de validar la salida contra C6
    logic: SI algún elemento de observaciones_conductor no pasa BR5.3–BR5.6 (en BR5.5, contra las citas de todos los hallazgos de la salida) ENTONCES la corrida entera queda en error con analysis.invalid_output, sin sugerencias ni ConductorObservation, como ya hace la ingesta ante vocabulario prohibido en un hallazgo; nada se quita en silencio.
    violation: Prueba de nivel 0 por regla y prueba de nivel 1 con un resultado inyectado por caso (0 filas de sugerencia y de aclaración, corrida en error).
    source: AC10.3.1; AC10.3.4; regla de la ingesta de U1 y U4 (vocabulario prohibido invalida la corrida entera); punto 4 de las preguntas
  - id: BR5.10
    status: nuevo
    statement: Las aclaraciones de un resultado válido se guardan en la misma transacción de la ingesta, una sola vez por sesión.
    category: constraint
    applies_to: [ConductorObservation]
    trigger: Ingesta de un resultado con estado ok
    logic: SI la ingesta confirma la corrida ENTONCES, en su misma transacción y con el orden sesión → fila, inserta cada aclaración como ConductorObservation proposed; SI ya existe una con la misma (session_id, turnos, tema_key) ENTONCES no inserta otra ni cambia su estado. Un resultado descartado por la ingesta (intento viejo, corrida cancelada o vencida) no guarda aclaraciones. Si la transacción revierte, no queda ninguna.
    violation: Pruebas de nivel 1 contra PostgreSQL real — dos corridas incrementales con la misma aclaración (una fila), reintento de una corrida (una fila), resultado de una corrida cancelada (0 filas) y fallo forzado a mitad de la ingesta (0 filas).
    source: FR10.3; components (InterviewSession guarda ConductorObservation); punto 5 de las preguntas
  - id: BR5.11
    status: nuevo
    statement: Solo el analista dueño de la sesión decide sobre una aclaración, con CSRF.
    category: authorization
    applies_to: [ConductorObservation, ConductorObservationDecision]
    trigger: POST /conductor-observations/{observation_id}/decision
    logic: La ruta declara x-veridicus-roles [analista] y x-veridicus-owner-only, y U8 registra el resolvedor observation_id → sesión del mecanismo de U3. SI el observation_id no existe ENTONCES 404 conductor_observation.not_found; SI el principal no es el dueño ENTONCES 403 session.not_owner; SI no es analista ENTONCES 403 auth.forbidden; SI falta o no coincide el token CSRF ENTONCES 403 auth.csrf. Ningún rechazo crea filas.
    violation: Pruebas de nivel 1 — otro analista (403), admin (403), sin CSRF (403), identificador inexistente (404); en todos, 0 filas nuevas.
    source: AC10.3.3 («sin mi acción»); C1 (x-veridicus-owner-only); ADR-009; mecanismo de dueño de U3
  - id: BR5.12
    status: nuevo
    statement: Una aclaración se aprueba o se descarta una sola vez, y solo mientras la sesión lo admite.
    category: policy
    applies_to: [ConductorObservation]
    trigger: POST /conductor-observations/{observation_id}/decision autorizado
    logic: SI status no es proposed ENTONCES 409 conductor_observation.already_decided; SI se pide approved y la sesión está finalized, terminated o consolidated o tiene el consentimiento retirado ENTONCES 409 conductor_observation.session_closed; SI se pide discarded y la sesión está finalized, terminated o consolidated ENTONCES 409 conductor_observation.session_closed; SI no ENTONCES status pasa al estado pedido y responde 200 con la ConductorObservation. Una sesión open, paused, suspended o blocked admite las dos decisiones. Antes de escribir, la decisión hace change_cursor.bump sobre la sesión y luego bloquea la fila de la aclaración (orden sesión → fila).
    violation: Pruebas de nivel 1 — doble decisión (409), aprobar con el consentimiento retirado (409) y descartar en la misma sesión (200), decidir en una sesión finalizada (409), decidir en una sesión bloqueada (200), dos decisiones concurrentes (una 200 y otra 409); prueba de nivel 0 de la máquina de estados con 100 % de ramas.
    source: AC10.3.3; VE-10 (consentimiento retirado); punto 7 de las preguntas; regla de orden de bloqueo de NFR Design
  - id: BR5.13
    status: nuevo
    statement: La decisión deja una fila de historial en la misma transacción, y quién y cuándo salen solo de ese historial.
    category: constraint
    applies_to: [ConductorObservationDecision, ConductorObservation]
    trigger: Cada decisión aceptada
    logic: SI cambia status ENTONCES en la misma transacción se inserta ConductorObservationDecision con actor_kind user, actor_user_id y at; decided_by y decided_at no se guardan en ConductorObservation, se derivan de esa fila. Las dos tablas declaran su marca de la convención de auditoría de U3 (mutable con disparador para ConductorObservation, history para el historial) y son purgables con la sesión.
    violation: Prueba de nivel 1 con un fallo forzado en el INSERT del historial (status sin cambiar); prueba común de nivel 1 de U3 con las dos tablas.
    source: ADR-003; NFR11; convención de auditoría de U3; hallazgo R-06 de la revisión 1
  - id: BR5.14
    status: nuevo
    statement: Sin la aprobación del analista, una aclaración no se reproduce ni se registra como formulada, y ninguna entra en el reporte de revisión.
    category: constraint
    applies_to: [ConductorObservation]
    trigger: Petición de audio, consolidación del reporte y renderizado del panel
    logic: SI status no es approved ENTONCES la consola no muestra «Escuchar audio» y la ruta de audio de U9 responde 409 conductor_observation.not_approved; en ningún estado la aclaración entra en el reporte consolidado (P6 = A), y su registro de quién y cuándo queda solo en el historial de la sesión.
    violation: Prueba Vitest (sin «Escuchar audio» en pendiente y descartada); prueba de nivel 1 de que el reporte de una sesión con aclaraciones aprobadas no las lista (lo comprueba el escaneo de contenido del reporte de U7 sobre un fixture).
    source: AC10.3.3; respuesta P6 = A; C1 (/conductor-observations/{id}/audio, de U9)
  - id: BR5.15
    status: nuevo
    statement: La consola presenta cada aclaración como «Aclaración sugerida · requiere tu decisión», con el tema y los turnos y nunca las citas.
    category: policy
    applies_to: [ConductorObservation]
    trigger: Renderizado de M4 con SessionView.conductor_observations
    logic: SI hay aclaraciones ENTONCES se listan al pie de la columna derecha, en orden de creación, cada una con el rótulo, «Tema:» y el tema, los turnos como «Turnos 3 y 7», su estado en texto y, si está pendiente y la sesión lo admite, «Aprobar» y «Descartar»; nunca muestra cita_a, cita_b ni el hallazgo de origen. Una sesión cerrada las muestra en solo lectura.
    violation: Prueba Vitest con una aclaración cuyo hallazgo tiene citas conocidas (las citas no aparecen en el DOM) y con cada estado.
    source: AC10.3.3; AC10.3.2; mockups §6.11; interaction-spec §4.9
  - id: BR5.16
    status: nuevo
    statement: La suite de U8 ejecuta los casos de aclaración neutra que publica U1, con control negativo.
    category: validation
    applies_to: [ClarificationCandidate]
    trigger: Suite de nivel 0 de U8
    logic: Por cada caso de contracts/integrity/scan-cases de tipo aclaración neutra (campo tema con la regla de VE-05), se corre el validador de BR5.3–BR5.6 y se compara el resultado (sale o se quita, y con qué regla) con el esperado; la suite falla si un caso no da lo esperado o si aparece un tipo de caso que no conoce.
    violation: Un caso modificado para esperar lo contrario hace fallar la suite.
    source: AC10.3.4; AC5.5.2; casos de escaneo de U1 (la suite de U11 los lista como de U8)
  - id: BR5.17
    status: nuevo
    statement: En nivel 2, sobre el conjunto sintético, 0 % de las aclaraciones emitidas contiene texto de una cita, y se cuentan las descartadas por regla.
    category: calculation
    applies_to: [ClarificationCandidate]
    trigger: Evaluación de nivel 2 de un PR que toca la aclaración o la IA, y toda entrega etiquetada
    logic: Por cada entrevista del conjunto se corre la CLI en modo incremental con desde_turno el primer turno y hasta_turno el último; una comprobación independiente (búsqueda directa de cada fragmento de cita en cada tema emitido) debe dar 0 coincidencias, y el reporte lleva solo conteos (hallazgos, aclaraciones emitidas y descartadas por regla). La tasa de descarte aceptable la fija NFR Requirements.
    violation: Reporte de la corrida adjunto al PR; control negativo con un tema sembrado en un fixture que contiene una cita (la comprobación lo detecta).
    source: AC10.3.2 [N2]; team.md (nivel 2); precisión FD-U8-09

  # BR6 — Permutación en producción (US10.5)
  - id: BR6.1
    status: nuevo
    statement: Todos los perfiles del archivo de perfiles tienen la permutación activa, también los de demostración y producción y todo-local.
    category: policy
    applies_to: [ExecutionProfile]
    trigger: Validación del archivo de perfiles en nivel 0
    logic: SI un perfil de config/profiles.yaml tiene permutation falso ENTONCES la prueba de U8 falla; apagarla en un perfil (p. ej. todo-local si NFR Requirements muestra que rompe la latencia en CPU) exige cambiar el perfil y esta prueba en el mismo PR. La exigencia de U11 en los perfiles de evaluación no cambia.
    violation: Fixture con un perfil de demostración con permutation falso (la prueba falla).
    source: FR10.5; respuesta P5 = A; exigencia de permutación en evaluación de U11
  - id: BR6.2
    status: nuevo
    statement: Por el camino del producto, un verificador que confirma en un solo orden no deja hallazgo y el registro muestra las dos llamadas.
    category: validation
    applies_to: [ExecutionProfile]
    trigger: Suite de nivel 0 de semantic-agent
    logic: SI semantic-agent corre una entrada con un perfil con permutation verdadero y un gateway fake cuyo verificador confirma en el orden directo y no en el permutado ENTONCES la salida que publica en C3 no trae el hallazgo, el registro trae una llamada verifier y una verifier_permuted por el candidato, y el descarte es rechazado_permutacion; con permutation falso hay una sola llamada verifier.
    violation: Prueba de nivel 0 del trabajador con el gateway fake en los dos perfiles; control negativo con un verificador que confirma en los dos órdenes (el hallazgo sale).
    source: AC10.5.1 [N0]; FR10.5; FR4.5; punto 1 de las preguntas
  - id: BR6.3
    status: nuevo
    statement: La ingesta guarda las dos llamadas y el descarte, y el registro de llamadas de la corrida las muestra sin pantalla propia.
    category: constraint
    applies_to: [ExecutionProfile]
    trigger: Ingesta del resultado de BR6.2 y GET /runs/{run_id}/model-calls
    logic: SI el resultado trae verifier y verifier_permuted ENTONCES quedan dos ModelCall y un DiscardedCandidate con rechazado_permutacion, 0 sugerencias de ese candidato, y la vista de solo lectura del registro (de U4) devuelve las dos llamadas con su papel. U8 no añade pantalla ni rótulo.
    violation: Prueba de nivel 1 con el resultado inyectado (dos filas de llamada, un descarte, 0 sugerencias) y la respuesta de /runs/{run_id}/model-calls.
    source: AC10.5.1; AC12.5.3; mockups (US10.5 sin interfaz propia)
  - id: BR6.4
    status: nuevo
    statement: U8 no cambia la lógica de la permutación de la biblioteca; su medición de nivel 2 es la de la evaluación.
    category: constraint
    applies_to: [ExecutionProfile]
    trigger: PR de B8
    logic: SI el PR de B8 toca el código de la permutación de la biblioteca (orden de las llamadas, descarte, intercambio de las citas) ENTONCES la revisión lo rechaza; la consistencia > 65 % al invertir el orden y la permutación en el 100 % de las consultas offline las mide la evaluación de la CLI de U11 con su reporte.
    violation: Revisión del PR (el diff de B8 no toca esos módulos, comprobado con git diff --stat sobre sus rutas) y reporte de nivel 2 adjunto con los dos umbrales.
    source: AC10.5.1 [N2]; NFR4; punto 1 de las preguntas
  - id: BR6.5
    status: nuevo
    statement: B8 mide el costo de la permutación en los perfiles del producto.
    category: calculation
    applies_to: [ExecutionProfile]
    trigger: Antes de fusionar B8
    logic: Se corre el conjunto sintético con todo-local y con un perfil comercial, con y sin permutación, y se reportan llamadas al verificador, tokens de entrada y salida y duración de la corrida por entrevista; las cifras se comparan con los umbrales de NFR3 y NFR8 que fija NFR Requirements.
    violation: Reporte de la medición adjunto al PR de B8; sin él, el PR no se fusiona.
    source: unit-of-work U8 (restricciones); bolt-plan B8; NFR3; NFR8
```

## Resumen

| Grupo | Reglas | Estado | Qué protege |
|---|---|---|---|
| BR1 Segunda lectura del juez | BR1.1–BR1.6 | Retirado | — |
| BR2 Pregunta sugerida | BR2.1–BR2.6 | Retirado | — |
| BR3 Indicio afectivo | BR3.1–BR3.3 | Retirado | — |
| BR4 Vocabulario, esquema y accesibilidad | BR4.1, BR4.2, BR4.4 (cambia); BR4.3 (Retirado); BR4.5–BR4.7 (nuevo) | Mixto | Etiquetas de veracidad, rótulos de resultado y la base de accesibilidad en el panel |
| BR5 Aclaración neutra | BR5.1–BR5.17 | Nuevo | Que la aclaración revele la contradicción o una cita, que llegue sin decisión humana y que se pierda su auditoría |
| BR6 Permutación en producción | BR6.1–BR6.5 | Nuevo | Falsas alarmas por el orden de las citas, sin tocar la lógica de U11 |

Vigentes: 28 (3 cambian y 25 son nuevas). Retiradas: 16.
