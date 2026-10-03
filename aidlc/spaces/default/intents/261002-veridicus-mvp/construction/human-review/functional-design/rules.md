# Reglas de negocio — U5 human-review

**Insumos.** Los mismos de `entities.md`. La máquina de estados (BR2) es un módulo guardia de
AUTONOMIA-03 en `domain/`, con 100 % de ramas.

```yaml
rules:
  # BR1 — Autorización
  - id: BR1.1
    statement: Solo el analista dueño de la sesión decide sobre sus sugerencias; el admin, otro analista o una identidad de servicio reciben 403 sin filas nuevas.
    category: authorization
    applies_to: [ReviewDecision]
    trigger: POST /suggestions/{id}/decisions
    logic: SI el principal no es analista o no es el dueño de la sesión de la sugerencia ENTONCES 403 (auth.forbidden o session.not_owner) y 0 filas; la comprobación la hace ConsoleApi antes de delegar.
    violation: Pruebas de nivel 1 por cada celda.
    source: FR1.2; FR6.1; AC5.4.1; AC5.4.3; ADR-009
  - id: BR1.2
    statement: Una sesión ajena se ve en solo lectura, sin botones de decisión ni de consolidación.
    category: authorization
    applies_to: [ReviewDecision]
    trigger: Abrir una sesión de otro analista o con rol admin
    logic: SI el usuario no es el dueño ENTONCES la consola muestra «Sesión de <usuario>. Solo lectura» y oculta las acciones; puede leer alertas, CoT y reporte.
    violation: Pruebas de nivel 1 y Vitest.
    source: AC5.4.2
  - id: BR1.3
    statement: Registrar «CoT consultada» lo puede hacer cualquier usuario que lee la sesión, y queda a su nombre.
    category: policy
    applies_to: [CotView]
    trigger: POST /suggestions/{id}/cot-views al desplegar la CoT
    logic: SI un usuario despliega la CoT ENTONCES se inserta CotView con su user_id y la hora; repetirlo no cambia nada (basta un evento).
    violation: Prueba de nivel 1.
    source: AC5.1.2; C1

  # BR2 — Máquina de estados (guardia AUTONOMIA-03)
  - id: BR2.1
    statement: Las únicas transiciones válidas son de pending a accepted, edited o dismissed, y entre accepted, edited y dismissed; nunca hacia pending.
    category: constraint
    applies_to: [ReviewDecision, EffectiveState]
    trigger: Cada decisión
    logic: SI el estado pedido es pending ENTONCES 409 review.invalid_transition; SI el estado pedido es igual al vigente y no cambia la nota ni la reformulación ENTONCES 409 review.invalid_transition; en otro caso se inserta la decisión con previous_state = estado vigente.
    violation: Prueba de nivel 0 de la tabla completa (100 % de ramas) y de nivel 1.
    source: AC5.1.4; FR6.1; ADR-007
  - id: BR2.2
    statement: Aceptar o editar exige que el mismo usuario haya consultado la CoT de esa sugerencia, en cualquier ronda.
    category: validation
    applies_to: [ReviewDecision, CotView]
    trigger: Decisión accepted o edited
    logic: SI no existe CotView del actor para la sugerencia ENTONCES 409 review.cot_not_viewed; descartar no lo exige.
    violation: Prueba de nivel 1 (409 antes, 201 después).
    source: FR6.2; AC5.1.2; Respuesta P1 = A
  - id: BR2.3
    statement: Descartar exige una nota que no esté vacía ni sea solo espacios.
    category: validation
    applies_to: [ReviewDecision]
    trigger: Decisión dismissed
    logic: SI la nota falta o está en blanco ENTONCES 422 review.note_required y la sugerencia no cambia.
    violation: Pruebas de nivel 0 y 1.
    source: FR6.3; AC5.3.1; AC5.3.2
  - id: BR2.4
    statement: Editar exige una reformulación no en blanco y nunca cambia fragmento, cita, documento ni CoT.
    category: validation
    applies_to: [ReviewDecision]
    trigger: Decisión edited
    logic: SI la reformulación falta o está en blanco ENTONCES 422 validation.invalid_request; SI la petición trae fragmento, cita, documento o CoT ENTONCES 422 sin cambios (el cuerpo de C1 no los admite); el SHA-256 de (fragmento, cita, document_id, CoT) es el mismo antes y después.
    violation: Prueba de nivel 1 con el SHA-256.
    source: AC5.2.1; AC5.2.2; FR7.2
  - id: BR2.5
    statement: Aceptar admite una nota opcional; la nota se guarda con la decisión.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Decisión accepted
    logic: SI se acepta con nota ENTONCES se guarda y la lista muestra «Aceptada · con nota» con la nota visible.
    violation: Pruebas de nivel 1 y Vitest.
    source: FR6.3; AC5.1.3
  - id: BR2.6
    statement: Cada decisión guarda actor, hora, estado anterior y nuevo, y nunca se modifica ni se borra.
    category: constraint
    applies_to: [ReviewDecision]
    trigger: Cada decisión
    logic: SI se registra una decisión ENTONCES es una fila nueva con actor_user_id, at, previous_state y state; la tabla está en la convención de auditoría de U3.
    violation: Prueba común de nivel 1.
    source: FR6.1; NFR11; AC8.4.1; AC8.4.2; ADR-003

  # BR3 — Rondas
  - id: BR3.1
    statement: Una decisión solo entra en la ronda abierta de la sesión; con la ronda bloqueada y sin corrección abierta, se rechaza.
    category: constraint
    applies_to: [ReviewRound, ReviewDecision]
    trigger: Cada decisión
    logic: SI la sesión no tiene ronda open ENTONCES 409 review.round_locked y 0 filas.
    violation: Prueba de nivel 1.
    source: ADR-007; C10
  - id: BR3.2
    statement: El estado vigente en una ronda es su última decisión; sin decisiones, el vigente en la ronda de la que hereda; sin herencia, pending.
    category: calculation
    applies_to: [EffectiveState]
    trigger: Cualquier lectura del estado de una sugerencia
    logic: SI la ronda tiene decisiones para la sugerencia ENTONCES la de mayor at (y, a igual hora, mayor orden de inserción); SI no ENTONCES el estado vigente en based_on_round_id; SI no hay ronda base ENTONCES pending.
    violation: Prueba de nivel 0 y de nivel 1.
    source: ADR-007 («Functional Design fija cómo hereda una ronda de corrección»)
  - id: BR3.3
    statement: Abrir una ronda de corrección la crea a partir de la versión vigente del reporte, o retoma la ya abierta.
    category: policy
    applies_to: [ReviewRound]
    trigger: ReviewRounds.open_correction_round (lo pide U7)
    logic: SI ya existe una ronda correction open ENTONCES la devuelve; SI no ENTONCES crea la ronda number + 1, kind correction, con based_on_report_version_id y based_on_round_id = la ronda que esa versión bloqueó.
    violation: Prueba de nivel 1.
    source: C11; ADR-007; AC6.3.2
  - id: BR3.4
    statement: Bloquear una ronda es atómico: de dos consolidaciones simultáneas solo una gana.
    category: constraint
    applies_to: [ReviewRound]
    trigger: ReviewRounds.lock_round (lo pide U7 en su transacción)
    logic: SI la ronda ya está locked ENTONCES report.conflict; SI no ENTONCES pasa a locked con el report_version_id y la hora.
    violation: Prueba de nivel 1 con dos consolidaciones simultáneas.
    source: C11; AC6.1.6
  - id: BR3.5
    statement: Una sugerencia nueva solo se propone en una ronda abierta.
    category: constraint
    applies_to: [ReviewRound]
    trigger: SuggestionProposer.propose (U4)
    logic: SI la sesión no tiene rondas ENTONCES se abre la ronda 1; SI tiene una ronda open ENTONCES la sugerencia nace pending en ella; SI todas sus rondas están locked ENTONCES la propuesta se rechaza con review.round_locked y no se crea ninguna sugerencia.
    violation: Prueba de nivel 1.
    source: C10; ADR-007; AUTONOMIA-03
  - id: BR3.6
    statement: ReviewRounds informa cuántas sugerencias siguen pending en una ronda y las decisiones vigentes para el reporte.
    category: calculation
    applies_to: [ReviewRound, EffectiveState]
    trigger: pending_count y decisions (C11)
    logic: SI U7 lo pide ENTONCES pending_count cuenta sugerencias con estado vigente pending y decisions devuelve, por sugerencia, su estado vigente, nota, reformulación, actor y hora.
    violation: Prueba de nivel 1.
    source: C11; AC5.2.4

  # BR4 — Métricas (C15, SHOULD)
  - id: BR4.1
    statement: Cada decisión suma al contador veridicus_review_decisions_total por estado y actualiza la razón de descarte de la sesión.
    category: calculation
    applies_to: [ReviewDecision]
    trigger: Cada decisión registrada
    logic: SI se registra una decisión ENTONCES el contador suma 1 en su etiqueta de estado y veridicus_session_dismissal_ratio se recalcula sobre las últimas W decididas (W de NFR Requirements); las etiquetas solo llevan identificadores.
    violation: Prueba de nivel 1.
    source: C15; FR9.3; NFR10

  # BR5 — Consola
  - id: BR5.1
    statement: Con la CoT plegada, «Aceptar» y «Editar» están deshabilitados con su motivo visible.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Tarjeta sin CotView del usuario
    logic: SI el usuario no ha desplegado la CoT ENTONCES «Aceptar» y «Editar» están deshabilitados con «Despliega y lee la justificación (CoT) para habilitar esta acción».
    violation: Prueba Vitest.
    source: AC5.1.1
  - id: BR5.2
    statement: Junto a los botones de decisión, sin hover, siempre está el recordatorio de criterio.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Renderizado de la tarjeta
    logic: SI se muestra una tarjeta con acciones ENTONCES aparece «La IA es un asistente de soporte. Su criterio como analista prevalece».
    violation: Prueba Vitest.
    source: FR6.5; AC5.1.5
  - id: BR5.3
    statement: El editor muestra el hallazgo original en solo lectura junto a la reformulación, y «Guardar» se deshabilita con la reformulación en blanco.
    category: policy
    applies_to: [ReviewDecision]
    trigger: Edición
    logic: SI se edita ENTONCES dos columnas (original en solo lectura / reformulación); SI la reformulación está en blanco ENTONCES «Guardar» deshabilitado con su motivo.
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
    statement: La tarjeta y sus formularios cumplen la base de accesibilidad de U4.
    category: constraint
    applies_to: [ReviewDecision]
    trigger: Niveles 0 y 3
    logic: SI axe encuentra violaciones serious o critical en la tarjeta o sus formularios, si aceptar, editar o descartar no se puede hacer solo con teclado, o si un estado se identifica solo por color ENTONCES la prueba falla.
    violation: Pruebas de nivel 3 y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Autorización | BR1.1–BR1.3 | Que otro decida por el dueño (US5.4) |
| BR2 Máquina de estados | BR2.1–BR2.6 | AUTONOMIA-03: decisiones a ciegas, sin nota o que reescriben a la IA |
| BR3 Rondas | BR3.1–BR3.6 | Cambios después de consolidar; herencia ambigua entre rondas |
| BR4 Métricas | BR4.1 | Señal AIR sin texto sensible |
| BR5 Consola | BR5.1–BR5.5 | Acciones sin motivo visible; accesibilidad |
