# Reglas de negocio — U5 human-review

**Revisión 2 — cambio 01, adenda 02 y revisiones 3 (2026-11-22).** Reemplaza la versión aprobada el
2026-10-02. Se conservan los ID BR1.1–BR5.5; lo que cambia lleva `status: cambia`; lo nuevo toma el
número siguiente de su grupo (`status: nuevo`). Ninguna regla sale en esta revisión.

- **Cambian:** CoT → observaciones (BR1.3, BR2.2, BR5.1), campos protegidos de C7 v2 (BR2.4), convención
  de auditoría (BR2.6), orden de bloqueo y `change_seq` (BR3.1, BR3.2), rondas sin referencia a
  ReviewReport (BR3.3, BR3.4), `propose` implementado por U4 (BR3.5), texto vigente tras `edited` (BR3.6),
  métricas C15 v2 (BR4.1), accesibilidad y textos (BR5.3, BR5.5).
- **Entran:** BR1.4 (404), BR2.7 (longitudes), BR2.8 (texto del analista fuera del escáner), BR3.7–BR3.11
  (ronda 1 al consolidar, concurrencia, copia descartada, estados de la sesión, corrección), BR5.6–BR5.8
  (`aria-disabled`, tarjeta decidida, catálogo de textos) y el grupo BR6 de retención.
- **Cierran la revisión 1:** R-01 → BR3.5; R-02 → BR3.1, BR3.2 y BR3.8; R-03 → BR3.6; R-04 → BR3.7;
  R-05 → BR1.4 y BR4.1.

**Insumos.** Los mismos de `entities.md`: unit-of-work, unit-of-work-story-map, requirements, components y
contract-summary. La máquina de estados (BR2.1–BR2.4) y la herencia (BR3.2) son módulos guardia de
AUTONOMIA-03 en `domain/`, con 100 % de ramas.

## Reglas (fuente de verdad)

```yaml
rules:
  # BR1 — Autorización
  - id: BR1.1
    status: cambia
    statement: Solo el analista dueño de la sesión decide sobre sus sugerencias; el admin, el investigador, otro analista o una identidad de servicio reciben 403 sin filas nuevas.
    category: authorization
    applies_to: [ReviewDecision]
    trigger: POST /suggestions/{id}/decisions
    logic: SI el rol no es analista ENTONCES 403 auth.forbidden; SI es analista y no es el dueño de la sesión de la sugerencia ENTONCES 403 session.not_owner; en ambos casos 0 filas y ConsoleApi decide antes de delegar (x-veridicus-roles analista, x-veridicus-owner-only); HumanReview recibe el actor ya autorizado.
    violation: Prueba de nivel 1 por celda (dueño 201, otro analista 403, admin 403, investigador 403, sin sesión web 401).
    source: FR1.2; FR6.1; AC5.4.1; AC5.4.3; ADR-009
  - id: BR1.2
    status: cambia
    statement: Una sesión ajena se ve en solo lectura, sin botones de decisión ni de consolidación; el investigador no ve hallazgos.
    category: authorization
    applies_to: [ReviewSuggestion, ReviewDecision]
    trigger: Abrir una sesión de otro analista o con rol admin
    logic: SI el usuario es analista no dueño o admin ENTONCES la tarjeta muestra el banner «Sesión de <usuario>. Solo lectura», estados, notas, reformulaciones y observaciones, sin acciones; SI es investigador ENTONCES 403 auth.forbidden y ninguna tarjeta.
    violation: Pruebas de nivel 1 (403 del investigador) y Vitest (canDecide falso oculta las acciones).
    source: AC5.4.2; FR1.2
  - id: BR1.3
    status: cambia
    statement: Registrar «Observaciones consultadas» lo pueden hacer el analista y el admin que leen la sesión; queda a su nombre una sola vez y cada apertura pasa por el registro de acceso.
    category: policy
    applies_to: [ObservationsView]
    trigger: POST /suggestions/{id}/observation-views al desplegar las observaciones
    logic: SI el rol es analista o admin ENTONCES se inserta ObservationsView con su user_id y la hora si no existía (la repetición no inserta) y responde 204; tras el 2xx ConsoleApi registra la apertura con resource_type suggestion (x-veridicus-access-log); SI es investigador ENTONCES 403 auth.forbidden sin filas ni registro.
    violation: Prueba de nivel 1 (primera apertura 1 fila, segunda 0 filas nuevas y 2 entradas de acceso; investigador 403).
    source: AC5.1.2; C1; C23
  - id: BR1.4
    status: nuevo
    statement: Una sugerencia que no existe responde 404 sin filas ni registro de acceso.
    category: validation
    applies_to: [ReviewSuggestion]
    trigger: Las dos rutas /suggestions/{id}/*
    logic: HumanReview aporta el resolvedor del dueño sugerencia → sesión que usa el mecanismo de dueño de ConsoleApi; SI el suggestion_id no existe ENTONCES 404 suggestion.not_found (code nuevo, FD-U5-01), 0 filas y sin entrada de acceso; SI existe, el dueño es el de su sesión.
    violation: Prueba de nivel 1 con un UUID inexistente en cada ruta; prueba de nivel 0 de que ConsoleApi no arranca sin el resolvedor.
    source: revisión 1 R-05; C1

  # BR2 — Máquina de estados (guardia AUTONOMIA-03)
  - id: BR2.1
    status: cambia
    statement: Las únicas transiciones válidas son de pending a accepted, edited o dismissed, y entre accepted, edited y dismissed; nunca hacia pending.
    category: constraint
    applies_to: [ReviewDecision, EffectiveState]
    trigger: Cada decisión
    logic: SI la petición HTTP pide pending ENTONCES 422 validation.invalid_request, porque el enum del cuerpo de C1 no lo admite (precisión FD-U5-09 a AC5.1.4); SI el dominio recibe pending por cualquier otra vía ENTONCES rechaza con review.invalid_transition; SI el estado pedido es igual al vigente y no cambia la nota ni la reformulación ENTONCES 409 review.invalid_transition; en otro caso se inserta la decisión con previous_state = estado vigente.
    violation: Prueba de nivel 0 de la tabla completa del dominio (100 % de ramas) y de nivel 1 (pending 422, repetición sin cambios 409).
    source: AC5.1.4; FR6.1; ADR-007
  - id: BR2.2
    status: cambia
    statement: Aceptar o editar exige que el mismo usuario haya desplegado las observaciones de esa sugerencia, en cualquier ronda.
    category: validation
    applies_to: [ReviewDecision, ObservationsView]
    trigger: Decisión accepted o edited
    logic: SI no existe ObservationsView del actor para la sugerencia ENTONCES 409 review.observations_not_viewed y 0 filas; descartar no lo exige; un evento de la ronda 1 vale en las correcciones (P1 = A).
    violation: Prueba de nivel 1 (409 antes, 201 después; descartar sin evento 201).
    source: FR6.2; AC5.1.2; Respuesta P1 = A
  - id: BR2.3
    status: cambia
    statement: Descartar exige una nota que no esté vacía ni sea solo espacios.
    category: validation
    applies_to: [ReviewDecision]
    trigger: Decisión dismissed
    logic: SI la nota falta o queda vacía tras quitar los espacios (incluidos los Unicode) ENTONCES 422 review.note_required y la sugerencia no cambia.
    violation: Pruebas de nivel 0 (propiedad con cadenas de solo espacios Unicode) y de nivel 1.
    source: FR6.3; AC5.3.1; AC5.3.2
  - id: BR2.4
    status: cambia
    statement: Editar exige una reformulación no en blanco y nunca cambia hecho, tipo, cita_a, cita_b ni observaciones.
    category: validation
    applies_to: [ReviewDecision, ReviewSuggestion]
    trigger: Decisión edited y toda decisión
    logic: SI state es edited y la reformulación falta o está en blanco ENTONCES 422 validation.invalid_request; SI la reformulación viene con otro estado ENTONCES 422 validation.invalid_request; SI el cuerpo trae hecho, tipo, cita_a, cita_b, observaciones u otro campo ENTONCES 422 validation.invalid_request (additionalProperties false en C1) y 0 filas; el SHA-256 de (hecho, tipo, cita_a, cita_b, observaciones) es el mismo antes y después de cada decisión; un UPDATE de veridicus_app sobre ReviewSuggestion falla.
    violation: Prueba de nivel 1 con el SHA-256 antes y después y con el UPDATE directo que falla.
    source: AC5.2.1; AC5.2.2; FR6.1; FR7.2
  - id: BR2.5
    statement: Aceptar admite una nota opcional; la nota se guarda con la decisión.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Decisión accepted o edited
    logic: SI se acepta o edita con nota ENTONCES se guarda en la misma fila y la tarjeta muestra «Aceptada · con nota» (o la nota bajo la reformulación) con la nota visible.
    violation: Pruebas de nivel 1 y Vitest.
    source: FR6.3; AC5.1.3
  - id: BR2.6
    status: cambia
    statement: Cada decisión y cada evento de observaciones guardan actor y hora, nunca se modifican ni se borran con el usuario de la aplicación.
    category: constraint
    applies_to: [ReviewDecision, ObservationsView]
    trigger: Cada decisión o evento; prueba común de la convención de auditoría
    logic: SI se registra una decisión ENTONCES es una fila nueva con actor_kind user, actor_user_id, at, previous_state, state y change_seq; SI un INSERT trae actor u hora nulos ENTONCES falla; SI veridicus_app intenta UPDATE o DELETE en ReviewDecision u ObservationsView ENTONCES falla.
    violation: Prueba común de nivel 1 de la convención de auditoría de U3, que recorre las tablas history de U5.
    source: FR6.1; NFR11; AC8.4.1; AC8.4.2; ADR-003
  - id: BR2.7
    status: nuevo
    statement: La nota y la reformulación tienen una longitud máxima del catálogo de límites, y el cuerpo de la petición también.
    category: validation
    applies_to: [ReviewDecision]
    trigger: POST /suggestions/{id}/decisions
    logic: SI note o reformulation pasan de review_text_max_chars, o el cuerpo pasa de review_body_max_bytes (C25, entradas nuevas FD-U5-02) ENTONCES 422 limits.exceeded y 0 filas; una variable de entorno solo puede bajar esas cifras.
    violation: Prueba de nivel 0 de límites (máximo y máximo + 1) y de nivel 1 del cuerpo grande.
    source: NFR10; C25
  - id: BR2.8
    status: nuevo
    statement: La nota y la reformulación son texto del analista; el escáner de vocabulario prohibido no las rechaza y se guardan tal cual.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Decisión con nota o reformulación
    logic: SI la reformulación o la nota contienen un término de la lista (p. ej. «miente») ENTONCES la decisión se registra igual (201) y el texto queda marcado como del analista para que el reporte lo muestre en el bloque del analista; HumanReview no llama al escáner sobre ese texto.
    violation: Prueba de nivel 0 (control (d) de AC5.5.2) y de nivel 1 (201 con «miente» en la reformulación).
    source: FR6.4; AC5.5.1; AC5.5.2

  # BR3 — Rondas
  - id: BR3.1
    status: cambia
    statement: Una decisión solo entra en la ronda abierta de la sesión, tomada con bloqueo; sin ronda abierta se rechaza.
    category: constraint
    applies_to: [ReviewRound, ReviewDecision]
    trigger: Cada decisión
    logic: Dentro de la transacción de la petición, tras el bloqueo compartido del usuario, HumanReview hace change_cursor.bump sobre la fila de la sesión y luego toma la ronda open con FOR UPDATE; SI no hay ronda open ENTONCES 409 review.round_locked y 0 filas.
    violation: Prueba de nivel 1 (ronda locked 409) y la de concurrencia de BR3.8.
    source: ADR-007; C10; C11
  - id: BR3.2
    status: cambia
    statement: El estado vigente en una ronda es su decisión de mayor change_seq; sin decisiones, el vigente en la ronda de la que hereda; sin herencia, pending.
    category: calculation
    applies_to: [EffectiveState]
    trigger: Cualquier lectura del estado de una sugerencia
    logic: SI la ronda tiene decisiones para la sugerencia ENTONCES la de mayor change_seq, con su nota y su reformulación; SI no ENTONCES el estado vigente en based_on_round_id; SI no hay ronda base ENTONCES pending; las rondas discarded no son base de ninguna.
    violation: Prueba de nivel 0 (cadena de tres rondas, una descartada) y de nivel 1.
    source: ADR-007 («Functional Design fija cómo hereda una ronda de corrección»); revisión 1 R-02
  - id: BR3.3
    status: cambia
    statement: Abrir una ronda de corrección la crea a partir de la última ronda bloqueada, o retoma la ya abierta, sin guardar la versión del reporte.
    category: policy
    applies_to: [ReviewRound]
    trigger: ReviewRounds.open_correction_round (lo pide U7)
    logic: Tras bump de la sesión; SI ya existe una ronda correction open ENTONCES la devuelve; SI no ENTONCES crea number + 1, kind correction, opened_by el actor, based_on_round_id la última ronda locked; SI la sesión no tiene ninguna ronda locked ENTONCES report.conflict y 0 filas.
    violation: Prueba de nivel 1 (dos llamadas devuelven la misma ronda; sin ronda locked report.conflict).
    source: C11; ADR-007; AC6.3.2
  - id: BR3.4
    status: cambia
    statement: Bloquear una ronda es atómico y no guarda la versión del reporte; de dos consolidaciones simultáneas solo una gana.
    category: constraint
    applies_to: [ReviewRound]
    trigger: ReviewRounds.lock_round (lo pide U7 en su transacción, tras open_round con for_update)
    logic: SI la ronda no está open ENTONCES report.conflict; SI no ENTONCES pasa a locked con locked_at y change_seq; recibe el report_version_id pero no lo guarda (la relación la guarda ReportVersion.round_id); tras el commit retira la serie de la razón de descartes de la sesión.
    violation: Prueba de nivel 1 con dos consolidaciones simultáneas (una gana, la otra report.conflict).
    source: C11; ADR-007; AC6.1.6
  - id: BR3.5
    status: cambia
    statement: Una sugerencia nueva solo se propone en una ronda abierta; propose lo implementa U4 sobre este contrato.
    category: constraint
    applies_to: [ReviewRound, ReviewSuggestion]
    trigger: SuggestionProposer.propose (implementación de U4, C10)
    logic: SI la sesión no tiene rondas ENTONCES se abre la ronda 1 (kind initial, opened_by nulo, opened_actor_kind system, opened_actor_system analysis-worker); SI tiene una ronda open ENTONCES la sugerencia nace pending en ella; SI todas sus rondas están locked o discarded ENTONCES rechaza con review.round_locked sin crear sugerencias, y la ingesta deja la corrida en error con analysis.system y confirma el mensaje (diseño de U4).
    violation: Prueba de nivel 1 de U4 contra este contrato; U5 suma la prueba de las columnas de la ronda 1.
    source: C10; ADR-007; AUTONOMIA-03; revisión 1 R-01
  - id: BR3.6
    status: cambia
    statement: ReviewRounds informa cuántas sugerencias siguen pending en una ronda y, por sugerencia, su estado vigente con su propia nota y reformulación.
    category: calculation
    applies_to: [ReviewRound, EffectiveState]
    trigger: pending_count y decisions (C11)
    logic: pending_count cuenta las sugerencias de la sesión con estado vigente pending en la ronda; decisions devuelve por sugerencia sus campos protegidos, el estado vigente, la nota, la reformulación (solo si el vigente es edited), quién y cuándo; SI una edited pasó luego a accepted ENTONCES se consolida el hallazgo de la IA sin reformulación; SI pasó a dismissed ENTONCES se consolida la nota del descarte; la reformulación anterior queda solo en el historial.
    violation: Prueba de nivel 1 (edited → accepted y edited → dismissed devuelven reformulación nula).
    source: C11; AC5.2.4; FR7.2; revisión 1 R-03
  - id: BR3.7
    status: nuevo
    statement: Consolidar una sesión sin sugerencias también bloquea una ronda, porque open_round con for_update abre la ronda 1 si la sesión no tiene ninguna.
    category: policy
    applies_to: [ReviewRound]
    trigger: ReviewRounds.open_round(for_update=True)
    logic: SI la sesión no tiene ninguna ronda ENTONCES crea la ronda 1 (kind initial, opened_by el actor de la consolidación) y la devuelve bloqueada; SI tiene una open ENTONCES la devuelve con FOR UPDATE; SI todas están locked o discarded ENTONCES devuelve nada; con for_update false nunca crea filas.
    violation: Prueba de nivel 1 (sesión con 0 hallazgos, pending_count 0 y lock_round bloquea la ronda 1).
    source: C11; revisión 1 R-04
  - id: BR3.8
    status: nuevo
    statement: Toda escritura de HumanReview que cambia una sesión toma los bloqueos en el orden usuario → sesión → ronda y marca sus filas con el change_seq de la sesión.
    category: constraint
    applies_to: [ReviewRound, ReviewDecision]
    trigger: decide, open_round con for_update, lock_round, open_correction_round, discard_correction_round
    logic: SI la operación cambia la sesión ENTONCES bloqueo compartido del usuario (lo toma ConsoleApi), luego change_cursor.bump con bloqueo exclusivo de la sesión, luego FOR UPDATE de la ronda; la fila escrita lleva ese change_seq; record_observations_view no cambia el estado y no hace bump.
    violation: Prueba de nivel 1 con una decisión y una consolidación simultáneas (sin interbloqueo; la decisión entra antes y cuenta, o después y recibe 409 review.round_locked) y con decisión e ingesta simultáneas.
    source: C11; revisión 1 R-02
  - id: BR3.9
    status: nuevo
    statement: Descartar la copia de trabajo deja su ronda de corrección en discarded con quién y cuándo; sus decisiones quedan como rastro y no cuentan.
    category: policy
    applies_to: [ReviewRound]
    trigger: ReviewRounds.discard_correction_round (lo pide U7; operación nueva, FD-U5-04)
    logic: Tras bump de la sesión; SI hay una ronda correction open ENTONCES pasa a discarded con discarded_by y discarded_at; SI no la hay ENTONCES report.conflict; la ronda initial nunca se descarta; la siguiente corrección hereda de la última locked.
    violation: Prueba de nivel 1 (descartar y volver a corregir; el estado vigente es el de la versión vigente).
    source: AC6.3.2; ADR-007
  - id: BR3.10
    status: nuevo
    statement: Las decisiones siguen en las sesiones pausadas, suspendidas, finalizadas, terminadas, bloqueadas o con el consentimiento retirado; solo la ronda manda.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Cada decisión
    logic: SI hay una ronda open ENTONCES la decisión se registra sea cual sea el estado de la sesión; ni HumanReview ni la ruta de U5 consultan el estado de la sesión; solo el análisis nuevo se detiene en esos estados (U4, U6).
    violation: Prueba de nivel 1 con una sesión en cada estado (201 en todos mientras la ronda está open).
    source: Respuesta P3 = A; VE-10
  - id: BR3.11
    status: nuevo
    statement: En una ronda de corrección valen las mismas reglas que en la inicial, reformulación incluida.
    category: policy
    applies_to: [ReviewDecision, ReviewRound]
    trigger: Decisión en una ronda kind correction
    logic: SI la ronda open es de corrección ENTONCES se pueden cambiar estados, notas y reformulaciones con las exigencias de BR2.1–BR2.8; los campos protegidos y la transcripción siguen sin cambio.
    violation: Prueba de nivel 1 (en la corrección, pasar a edited con reformulación nueva da 201).
    source: Respuesta P2 = A; FR7.5

  # BR4 — Métricas (C15 v2, SHOULD)
  - id: BR4.1
    status: cambia
    statement: Cada decisión suma al contador por estado y actualiza la razón de descartes de la sesión, con cardinalidad acotada.
    category: calculation
    applies_to: [ReviewDecision]
    trigger: Cada decisión registrada (tras el commit)
    logic: SI se registra una decisión ENTONCES veridicus_review_decisions_total suma 1 en su etiqueta state y veridicus_session_dismissal_ratio se recalcula sobre las últimas dismissal_window_w decididas de la sesión (C25); la única etiqueta de la razón es session_id y su serie existe solo mientras la sesión tiene una ronda open con ventana completa (se retira al bloquear o descartar la ronda y al purgar); el umbral 0.25 vive en la regla de U2; las emite U5 desde session-api.
    violation: Prueba de nivel 1 (contador por estado; series acotadas con sesiones consolidadas).
    source: C15; FR9.3; NFR10; revisión 1 R-05

  # BR5 — Consola (tarjeta de ReviewSuggestionCard)
  - id: BR5.1
    status: cambia
    statement: Con las observaciones plegadas y sin evento del usuario, «Aceptar» y «Editar» están deshabilitados con su motivo visible.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Tarjeta con observationsViewed falso
    logic: SI el usuario no ha desplegado las observaciones ENTONCES «Aceptar» y «Editar» llevan aria-disabled true con «Despliega y lee las observaciones para habilitar esta acción»; «Descartar» sigue habilitado; plegarlas de nuevo no vuelve a deshabilitar.
    violation: Prueba Vitest.
    source: AC5.1.1
  - id: BR5.2
    statement: Junto a los botones de decisión, sin hover, siempre está el recordatorio de criterio.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Renderizado de la tarjeta con acciones
    logic: SI se muestra una tarjeta con acciones ENTONCES aparece «La IA es un asistente de soporte. Su criterio como analista prevalece».
    violation: Prueba Vitest.
    source: FR6.5; AC5.1.5
  - id: BR5.3
    status: cambia
    statement: El editor muestra el hallazgo de la IA en solo lectura junto a la reformulación, y «Guardar» queda deshabilitado con la reformulación en blanco.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Edición
    logic: SI se edita ENTONCES dos columnas (hecho, tipo, citas y observaciones como texto en solo lectura / «Tu reformulación» y «Nota (opcional)»); SI la reformulación está en blanco ENTONCES «Guardar» lleva aria-disabled true con «Escribe tu reformulación para guardar».
    violation: Prueba Vitest.
    source: AC5.2.1; AC5.2.3
  - id: BR5.4
    statement: Descartar sin nota muestra el error junto al campo.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Descartar con nota en blanco
    logic: SI la nota está en blanco ENTONCES aparece «Escribe por qué descartas esta sugerencia» junto al campo y no se envía.
    violation: Prueba Vitest.
    source: AC5.3.1
  - id: BR5.5
    status: cambia
    statement: La tarjeta y sus formularios entran en la suite de accesibilidad de la consola y se usan solo con teclado.
    category: constraint
    applies_to: [ReviewDecision]
    trigger: Niveles 0 y 3
    logic: SI axe (WCAG 2.1 AA) encuentra violaciones serious o critical en la tarjeta o sus formularios, si desplegar las observaciones, aceptar, editar, descartar o cambiar la decisión no se puede hacer con Tab, Enter, Espacio y Escape con el foco visible, o si un estado se identifica solo por color ENTONCES la prueba falla.
    violation: Pruebas de nivel 3 (suite axe y recorrido con teclado de U4, ampliados por U5) y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3
  - id: BR5.6
    status: nuevo
    statement: Un botón deshabilitado con motivo recibe el foco y anuncia su motivo.
    category: constraint
    applies_to: [ReviewDecision]
    trigger: Aceptar, Editar y Guardar deshabilitados
    logic: SI un botón está deshabilitado con motivo ENTONCES usa aria-disabled true (no disabled nativo), sigue en el orden de Tab y el motivo se asocia con aria-describedby; activarlo no envía nada.
    violation: Prueba Vitest.
    source: AC5.6.4
  - id: BR5.7
    status: nuevo
    statement: Cada estado de la tarjeta se ve con icono y texto, y la editada muestra la IA y al analista por separado.
    category: policy
    applies_to: [EffectiveState]
    trigger: Renderizado de una tarjeta decidida, bloqueada o en error
    logic: SI el estado vigente es accepted ENTONCES «✓ Aceptada» o «✓ Aceptada · con nota» y la nota; SI edited ENTONCES «✎ Editada» con el hallazgo de la IA y la reformulación con quién y cuándo; SI dismissed ENTONCES «✕ Descartada» con la nota, quién y cuándo; SI la ronda está cerrada ENTONCES 🔒 y sin acciones; antes de consolidar, «Cambiar decisión» nunca ofrece «Pendiente»; SI la API responde con error ENTONCES el formulario conserva el texto y muestra el mensaje de su code.
    violation: Prueba Vitest por estado y por code.
    source: AC5.1.3; AC5.1.4; AC5.6.3
  - id: BR5.8
    status: nuevo
    statement: Los textos de la tarjeta viven en el catálogo de mensajes de la consola y pasan el escaneo de vocabulario prohibido.
    category: constraint
    applies_to: [ReviewDecision]
    trigger: Nivel 0 (escaneo de las cadenas de la interfaz)
    logic: SI una cadena de U5 del catálogo contiene un término de la lista ENTONCES el escaneo de la interfaz falla; el texto que escribe el analista no está en el catálogo y no se escanea (BR2.8).
    violation: Prueba de nivel 0 del escaneo de cadenas con un control que siembra un término.
    source: AC5.5.1; AC5.5.5; FR6.4

  # BR6 — Retención (C24, A-2)
  - id: BR6.1
    status: nuevo
    statement: HumanReview implementa Purgeable.purge_session y borra lo suyo de la sesión en el orden inverso de las referencias, devolviendo solo IDs.
    category: constraint
    applies_to: [ObservationsView, ReviewDecision, ReviewSuggestion, ReviewRound, PurgeReceipt]
    trigger: Job de retención de U13 (lo lanza el humano), después de que ReviewReport borró lo suyo
    logic: SI el Job llama purge_session ENTONCES, con el usuario veridicus_retention y en la transacción del Job, borra ObservationsView, ReviewDecision, ReviewSuggestion y ReviewRound de la sesión, en ese orden, retira la serie de la razón de descartes y devuelve PurgeReceipt; SI la sesión no tiene filas ENTONCES devuelve listas vacías sin error.
    violation: Prueba de nivel 1 con el usuario de retención (0 filas de la sesión después; las de otra sesión intactas; el recibo sin texto).
    source: C24; AC15.7.2; A-2
  - id: BR6.2
    status: nuevo
    statement: Solo el usuario de retención puede borrar en las tablas de U5.
    category: authorization
    applies_to: [ObservationsView, ReviewDecision, ReviewSuggestion, ReviewRound]
    trigger: Cualquier DELETE
    logic: SI veridicus_app intenta DELETE en cualquiera de las cuatro tablas ENTONCES falla por permisos; veridicus_retention tiene DELETE y nunca UPDATE.
    violation: Prueba de nivel 1 con los dos usuarios.
    source: AC8.4.2; A-2; NFR11
  - id: BR6.3
    status: nuevo
    statement: Las cuatro tablas de HumanReview declaran la marca de auditoría con su tipo, purgeable y owner_unit U5.
    category: constraint
    applies_to: [ObservationsView, ReviewDecision, ReviewSuggestion, ReviewRound]
    trigger: Migraciones de U4 y U5; prueba común de la convención
    logic: ReviewDecision, ObservationsView y ReviewSuggestion son history con sus columnas de actor y hora; ReviewRound es mutable con el disparador de entities.md; las cuatro son purgeable true y owner_unit U5; SI falta la marca ENTONCES la prueba común falla.
    violation: Prueba común de nivel 1 de la convención de auditoría.
    source: AC8.4.1; ADR-003
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Autorización | BR1.1–BR1.4 | Que otro decida por el dueño (US5.4); el investigador sin hallazgos; 404 estable |
| BR2 Máquina de estados | BR2.1–BR2.8 | AUTONOMIA-03: decisiones a ciegas, sin nota, que reescriben a la IA o sin rastro; texto del analista fuera del escáner |
| BR3 Rondas | BR3.1–BR3.11 | Cambios después de consolidar, herencia ambigua, consolidación sin ronda, carreras entre decidir y consolidar, copia descartada, estados de la sesión |
| BR4 Métricas | BR4.1 | Señal de descartes sin texto y con series acotadas |
| BR5 Consola | BR5.1–BR5.8 | Acciones sin motivo visible, accesibilidad, IA y analista separados, textos sin vocabulario prohibido |
| BR6 Retención | BR6.1–BR6.3 | Borrado solo por el Job, en orden y sin texto |
