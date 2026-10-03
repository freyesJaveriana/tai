# Reglas de negocio — U8 assistant-extras

**Insumos.** Los mismos de `entities.md`. La regla de permutación (BR1) forma parte de la guardia de
alertas de AUTONOMIA-05: vive en `domain/` y exige 100 % de ramas.

```yaml
rules:
  # BR1 — Permutación del orden de lectura (US10.5)
  - id: BR1.1
    statement: Con la permutación activa, cada afirmación candidata a alerta se evalúa también en orden inverso.
    category: policy
    applies_to: [ReadingOrder, PermutationOutcome]
    trigger: Tras la primera lectura del juez, si options.permutation es true
    logic: SI una afirmación pasó la guardia y la primera lectura la calificó incongruente ENTONCES se hace una segunda lectura con los pasajes en orden de similitud ascendente y la afirmación antes de los pasajes, con el mismo prompt del sistema y la misma semilla; las demás afirmaciones no se releen.
    violation: Prueba de nivel 0 con un juez fake que registra el orden recibido.
    source: FR10.5; Respuesta P1 = A
  - id: BR1.2
    statement: Solo se registra la alerta si las dos lecturas califican incongruente.
    category: policy
    applies_to: [PermutationOutcome]
    trigger: Tras la segunda lectura
    logic: SI las dos lecturas son incongruente ENTONCES sustained true y la alerta sigue el camino de U4; SI no ENTONCES no hay alerta.
    violation: Prueba de nivel 0 con un juez fake que discrepa solo en un orden; consistencia > 65 % en nivel 2.
    source: AC10.5.1; NFR4
  - id: BR1.3
    statement: Una afirmación que no se sostiene al invertir el orden queda «no documentada» y va al paquete.
    category: policy
    applies_to: [PermutationOutcome]
    trigger: sustained false
    logic: SI las lecturas no coinciden ENTONCES la afirmación es no documentada, entra al Paquete de Contexto de Traspaso con el motivo «el juez no sostuvo la incongruencia al invertir el orden» y suprime la pregunta sugerida del turno.
    violation: Prueba de nivel 0.
    source: Respuesta P2 = A; FR5.2
  - id: BR1.4
    statement: La permutación nunca produce una alerta por debajo del umbral.
    category: constraint
    applies_to: [PermutationOutcome]
    trigger: Evaluación con permutación
    logic: SI una afirmación no pasó la guardia ENTONCES no tiene segunda lectura y nunca alerta.
    violation: Prueba de nivel 0.
    source: AC10.5.1; AUTONOMIA-05
  - id: BR1.5
    statement: La segunda lectura se valida igual que la primera; si falla, el turno entero queda en error.
    category: validation
    applies_to: [PermutationOutcome]
    trigger: Respuesta de la segunda lectura
    logic: SI la segunda salida no cumple C6, cita pasajes no recuperados o tiene vocabulario prohibido fuera de citas literales ENTONCES turn.error.invalid_output y 0 alertas.
    violation: Prueba de nivel 0.
    source: FR4.2; AC3.2.1
  - id: BR1.6
    statement: El resultado registra si se aplicó la permutación.
    category: policy
    applies_to: [PermutationOutcome]
    trigger: Publicación de C3
    logic: SI options.permutation es true ENTONCES permutation_applied es true y cada afirmación releída guarda las dos calificaciones en su evaluación.
    violation: Prueba de nivel 1.
    source: C3

  # BR2 — Pregunta sugerida (US10.3)
  - id: BR2.1
    statement: Un turno con alguna afirmación «no documentada» nunca tiene pregunta sugerida.
    category: constraint
    applies_to: [SuggestedQuestion]
    trigger: Armado del resultado
    logic: SI alguna afirmación del turno es no documentada (por guardia, por el juez o por la permutación) ENTONCES no se genera pregunta, aunque suggest_question esté activo.
    violation: Prueba de nivel 0.
    source: AC10.3.2; FR5.2; AUTONOMIA-05
  - id: BR2.2
    statement: La pregunta se genera solo a partir de pasajes del marco de verdad recuperados para el turno.
    category: constraint
    applies_to: [SuggestedQuestion]
    trigger: Generación con suggest_question activo y sin afirmaciones no documentadas
    logic: SI se genera la pregunta ENTONCES el bloque de datos del prompt solo lleva los pasajes recuperados del turno (y el turno como dato), nunca instrucciones del testimonio; la salida se valida contra su esquema (texto de 1–300 caracteres) y se escanea con C8.
    violation: Prueba de nivel 0 que inspecciona el bloque de datos del prompt.
    source: AC10.3.1; FR10.3; FR4.6
  - id: BR2.3
    statement: Una pregunta inválida o con vocabulario prohibido se descarta sin afectar al resto del turno.
    category: validation
    applies_to: [SuggestedQuestion]
    trigger: Validación de la pregunta
    logic: SI la pregunta no cumple su esquema o el escaneo encuentra un término ENTONCES no se publica pregunta y el turno sigue evaluated con sus alertas y paquete.
    violation: Prueba de nivel 0.
    source: AC5.5.1; FR10.3
  - id: BR2.4
    statement: La pregunta se muestra como sugerencia que requiere aprobación, y solo el dueño la aprueba o descarta.
    category: authorization
    applies_to: [SuggestedQuestion, QuestionDecision]
    trigger: POST /questions/{id}/decision
    logic: SI el principal no es el analista dueño ENTONCES 403; SI la pregunta ya fue decidida ENTONCES 409; SI no ENTONCES pasa a approved o discarded e inserta QuestionDecision; la consola muestra «Pregunta sugerida · requiere tu aprobación» con «Aprobar» y «Descartar».
    violation: Pruebas de nivel 1 y Vitest.
    source: AC10.3.1; FR10.3; ADR-009
  - id: BR2.5
    statement: Una pregunta que no se aprueba no se reproduce ni se registra como formulada.
    category: constraint
    applies_to: [SuggestedQuestion]
    trigger: Audio o reporte
    logic: SI la pregunta no está approved ENTONCES GET /questions/{id}/audio responde 409 y el reporte no la lista como formulada.
    violation: Prueba de nivel 0.
    source: AC10.3.3; FR10.4
  - id: BR2.6
    statement: El historial de decisiones de preguntas cumple la convención de auditoría.
    category: constraint
    applies_to: [QuestionDecision]
    trigger: Prueba común de nivel 1
    logic: SI se registra una decisión ENTONCES lleva actor y hora y no admite UPDATE ni DELETE.
    violation: Prueba común de nivel 1 de U3.
    source: ADR-003; NFR11

  # BR3 — Indicio afectivo (US11.1, COULD)
  - id: BR3.1
    statement: Con el indicio activo, un paquete lleva el texto fijo si el fragmento contiene al menos una palabra clave emocional.
    category: calculation
    applies_to: [AffectiveKeywordList, AffectiveNote]
    trigger: Armado del paquete con options.affective true
    logic: SI el texto del turno contiene una palabra de la lista (palabra completa, sin mayúsculas ni tildes) ENTONCES el paquete lleva affective_note con el texto fijo; SI no hay coincidencia o el indicio está apagado ENTONCES no lo lleva; nunca se llama al LLM.
    violation: Prueba de nivel 0 (activo con coincidencia, activo sin coincidencia, apagado).
    source: AC11.1.1; FR11.1; Respuesta P3 = A
  - id: BR3.2
    statement: El texto del indicio y la lista de palabras pasan el escaneo de vocabulario prohibido.
    category: validation
    applies_to: [AffectiveKeywordList, AffectiveNote]
    trigger: Suite de nivel 0
    logic: SI el texto fijo o una palabra de la lista contiene un término de C8 ENTONCES la suite falla.
    violation: Prueba de nivel 0.
    source: AC11.1.1; AC5.5.1
  - id: BR3.3
    statement: La lista de palabras emocionales es un contrato versionado que cambia solo por PR.
    category: policy
    applies_to: [AffectiveKeywordList]
    trigger: Cambio de la lista
    logic: SI se cambia la lista ENTONCES entra por su propio PR con versión nueva y un fixture que ejercita el cambio.
    violation: Revisión del PR.
    source: Respuesta P3 = A; Functional Design de U1 (versión de contratos)

  # BR4 — Vocabulario y accesibilidad en lo que añade U8 (US5.5 y US5.6 cruzan esta unidad)
  - id: BR4.1
    statement: La pregunta sugerida y el indicio afectivo pasan el escaneo de vocabulario prohibido con su control negativo.
    category: validation
    applies_to: [SuggestedQuestion, AffectiveNote]
    trigger: Generación y suite de nivel 0
    logic: SI la pregunta o el indicio contienen un término de C8 fuera de citas literales ENTONCES se omiten (pregunta) o la suite falla (texto fijo); el fixture «¿Por qué miente?» hace fallar el escaneo de la pregunta.
    violation: Prueba de nivel 0.
    source: AC5.5.1; AC5.5.2
  - id: BR4.2
    statement: El esquema de la salida de la pregunta es estricto y no tiene campos de veracidad.
    category: constraint
    applies_to: [SuggestedQuestion]
    trigger: Validación de la pregunta
    logic: SI la salida del juez para la pregunta trae un campo distinto de text (p. ej. is_truthful) ENTONCES se rechaza y no hay pregunta.
    violation: Prueba de nivel 0.
    source: AC5.5.3; AUTONOMIA-03
  - id: BR4.3
    statement: U8 no añade rótulos de resultado: la permutación usa los de U1 y la pregunta usa el rótulo informativo «Pregunta sugerida · requiere tu aprobación».
    category: constraint
    applies_to: [SuggestedQuestion, PermutationOutcome]
    trigger: Renderizado
    logic: SI se muestra un resultado de afirmación ENTONCES el rótulo sale del catálogo de U1; la pregunta no se presenta como un resultado de afirmación.
    violation: Prueba Vitest.
    source: AC5.5.4
  - id: BR4.4
    statement: La tarjeta de la pregunta sugerida cumple la base de accesibilidad de U4.
    category: constraint
    applies_to: [SuggestedQuestion]
    trigger: Niveles 0 y 3
    logic: SI axe encuentra violaciones serious o critical en la tarjeta, si «Aprobar» o «Descartar» no se activan con teclado, o si su estado se distingue solo por color ENTONCES la prueba falla.
    violation: Pruebas de nivel 3 y Vitest.
    source: AC5.6.1; AC5.6.2; AC5.6.3
```

## Resumen

| Grupo | Reglas | Qué protege |
|---|---|---|
| BR1 Permutación | BR1.1–BR1.6 | Falsas alarmas por sesgo de posición; alertas bajo el umbral |
| BR2 Pregunta | BR2.1–BR2.6 | Preguntas con conjeturas, sin aprobación o con etiquetas de veracidad |
| BR3 Indicio afectivo | BR3.1–BR3.3 | Un juicio afectivo opaco del LLM; vocabulario prohibido |
