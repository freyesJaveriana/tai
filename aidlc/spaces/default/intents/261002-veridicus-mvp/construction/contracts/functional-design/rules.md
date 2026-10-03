# Reglas de negocio — U1 contracts

**Insumos.** Los mismos de `entities.md`: unit-of-work, contract-summary, requirements, components y
las respuestas P1–P4 de `functional-design-questions.md`. Cada regla se prueba en **nivel 0** con un
*fixture* positivo y uno negativo (control negativo), salvo que diga otra cosa.

```yaml
rules:
  # BR1 — Versión y cambio de contratos
  - id: BR1.1
    statement: Todo contrato tiene versión semántica y todo mensaje de cola declara schema_version.
    category: constraint
    applies_to: [ContractDocument, MessageEnvelope]
    trigger: Al validar un contrato o un mensaje
    logic: SI falta la versión o no tiene la forma MAYOR.MENOR.PARCHE ENTONCES el contrato o el mensaje es inválido.
    violation: La suite de contratos falla; el mensaje se rechaza.
    source: contract-summary P2; NFR10
  - id: BR1.2
    statement: Un mensaje con una versión mayor que el consumidor no conoce se rechaza sin crear filas.
    category: validation
    applies_to: [MessageEnvelope]
    trigger: Al recibir un mensaje de C2–C5
    logic: SI el mayor de schema_version no está entre los mayores conocidos ENTONCES el mensaje va a <cola>:failed y no se procesa.
    violation: Rechazo; ninguna fila nueva.
    source: contract-summary P2 y regla 4; AC2.2.3
  - id: BR1.3
    statement: Un cambio aditivo sube la versión menor; los consumidores ignoran los campos desconocidos en C1–C5.
    category: policy
    applies_to: [ContractDocument, MessageEnvelope]
    trigger: Al cambiar un contrato
    logic: SI el cambio solo añade un campo opcional o una ruta ENTONCES sube el menor y los fixtures anteriores siguen aceptándose.
    violation: La prueba de compatibilidad de fixtures anteriores falla.
    source: contract-summary regla 3
  - id: BR1.4
    statement: En los contratos estrictos C6 y C7 todo cambio es mayor y entra en un solo PR con productor y consumidores.
    category: policy
    applies_to: [JudgeOutput, Alert]
    trigger: Al cambiar C6 o C7
    logic: SI cambia C6 o C7 ENTONCES sube el mayor y cambia el $id (v1 → v2).
    violation: La prueba que compara $id y versión falla.
    source: contract-summary reglas 3 y 4
  - id: BR1.5
    statement: Cada cambio de contrato entra por su propio PR con sus fixtures positivos y negativos.
    category: policy
    applies_to: [ContractDocument, Fixture]
    trigger: Al proponer un cambio
    logic: SI un PR cambia un contrato ENTONCES cambia solo ese contrato, sube su versión y trae al menos un fixture que ejercita el cambio.
    violation: Revisión del PR (comprobación manual del autor con la evidencia de la suite).
    source: unit-of-work U1 Restricciones; team-practices
  - id: BR1.6
    statement: Ningún fixture contiene datos reales.
    category: constraint
    applies_to: [Fixture]
    trigger: En cada PR
    logic: SI un fixture contiene un nombre, testimonio o expediente que no está marcado como sintético ENTONCES la suite falla.
    violation: La comprobación de datos sintéticos de la suite falla.
    source: NFR12; project.md Forbidden

  # BR2 — Mensajes de cola
  - id: BR2.1
    statement: Un mensaje de turno a evaluar sin un campo obligatorio, con un tipo erróneo o con texto vacío se rechaza sin crear filas.
    category: validation
    applies_to: [TurnToEvaluate]
    trigger: Al encolar y al consumir C2
    logic: SI el mensaje no cumple C2 ENTONCES va a veridicus:turns:failed sin evaluarse.
    violation: Rechazo; ninguna fila.
    source: AC2.2.3; FR3
  - id: BR2.2
    statement: El umbral solo viaja como instantánea de lectura entre 0 y 1; ningún mensaje ni ruta lo escribe.
    category: constraint
    applies_to: [TurnToEvaluate]
    trigger: Al validar C2
    logic: SI similarity_threshold falta o está fuera de [0, 1] ENTONCES el mensaje es inválido.
    violation: Rechazo del mensaje.
    source: FR5.1; FR9.1; ADR-006; contract-summary regla 7
  - id: BR2.3
    statement: Un resultado con outcome error no trae alertas, ni paquete de traspaso, ni pregunta sugerida.
    category: validation
    applies_to: [EvaluationResult]
    trigger: Al validar C3
    logic: SI outcome es error ENTONCES alerts está vacío o ausente, y handoff_package y suggested_question están ausentes; además error_code es obligatorio.
    violation: El resultado entero se trata como turn.error.invalid_output.
    source: FR4.2; AC3.2.1
  - id: BR2.4
    statement: Una alerta solo acompaña a una afirmación incongruente con guard at_or_above_threshold.
    category: validation
    applies_to: [EvaluationResult, Alert]
    trigger: Al validar C3
    logic: SI una alerta apunta a un claim_index cuya afirmación no es incongruente o tiene guard below_threshold ENTONCES el resultado es inválido.
    violation: El resultado entero se trata como turn.error.invalid_output.
    source: FR4.3; AUTONOMIA-05
  - id: BR2.5
    statement: Si alguna afirmación es no documentada, el resultado no trae pregunta sugerida y sí paquete de traspaso.
    category: validation
    applies_to: [EvaluationResult]
    trigger: Al validar C3
    logic: SI alguna afirmación tiene grade no documentada ENTONCES suggested_question está ausente y handoff_package está presente.
    violation: El resultado entero se trata como turn.error.invalid_output.
    source: FR5.2; FR5.3; AUTONOMIA-05

  # BR3 — Esquema de la salida del juez (C6)
  - id: BR3.1
    statement: La salida del juez solo acepta los campos de C6; cualquier campo adicional, en cualquier nivel, la invalida.
    category: validation
    applies_to: [JudgeOutput]
    trigger: Al validar la salida del juez
    logic: SI hay una propiedad no declarada, falta claims, claims está vacío o falta un campo obligatorio de una afirmación ENTONCES la salida es inválida.
    violation: turn.error.invalid_output; 0 alertas para todo el turno.
    source: FR4.2; AC3.2.1; AC5.5.3
  - id: BR3.2
    statement: El enum de calificación tiene exactamente congruente, incongruente y no documentada.
    category: constraint
    applies_to: [JudgeOutput, EvaluationResult, Grade]
    trigger: Al validar C6, C3 y C1
    logic: SI el enum de cualquier contrato tiene otro valor, uno menos o uno más ENTONCES la suite falla; SI una afirmación trae otro valor ENTONCES la salida es inválida.
    violation: Suite en rojo; turn.error.invalid_output.
    source: AC5.5.4; FR4.2
  - id: BR3.3
    statement: Ningún esquema de contracts/ declara un campo de veracidad.
    category: constraint
    applies_to: [ContractDocument, JudgeOutput, Alert]
    trigger: Al validar todos los esquemas
    logic: SI algún nombre de propiedad de un esquema coincide con categories_forbidden_in_schemas o con un término de la lista de vocabulario prohibido ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC5.5.3; AUTONOMIA-03
  - id: BR3.4
    statement: El formato inválido y el plazo vencido tienen code distintos y estables.
    category: constraint
    applies_to: [ErrorCodeCatalog]
    trigger: Al validar el catálogo
    logic: SI turn.error.invalid_output, turn.error.timeout y turn.error.system no existen como tres códigos distintos ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC3.2.1; NFR10

  # BR4 — Esquema de la alerta (C7)
  - id: BR4.1
    statement: Una alerta sin fragmento, cita, ID de documento o CoT, o con cualquiera de ellos vacío, se rechaza.
    category: validation
    applies_to: [Alert]
    trigger: Al producir, ingerir y guardar una alerta
    logic: SI falta o está vacío fragment, quote, document_id o cot ENTONCES la alerta es inválida (cuatro fixtures negativos, uno por campo).
    violation: Rechazo; el resultado que la trae es turn.error.invalid_output.
    source: FR4.4; AUTONOMIA-05
  - id: BR4.2
    statement: La alerta rechaza cualquier campo adicional, como is_truthful.
    category: validation
    applies_to: [Alert]
    trigger: Al validar C7
    logic: SI la alerta trae una propiedad no declarada ENTONCES es inválida.
    violation: Rechazo.
    source: AC5.5.3; AUTONOMIA-03

  # BR5 — Vocabulario prohibido (C8)
  - id: BR5.1
    statement: La versión 1.0.0 de la lista tiene exactamente los 9 términos aprobados; cada ampliación entra por su propio PR con su control negativo.
    category: policy
    applies_to: [ForbiddenVocabularyList]
    trigger: Al validar C8
    logic: SI la lista 1.0.0 difiere de mentiroso, mentirosa, miente, mintió, falso, falsa, verdadero, verdadera, engaño ENTONCES la suite falla; SI una versión nueva añade un término sin fixture negativo que lo use ENTONCES la suite falla.
    violation: Suite en rojo.
    source: Respuesta P2 = A; contract-summary C8
  - id: BR5.2
    statement: La coincidencia es por palabra completa, sin distinguir mayúsculas ni tildes.
    category: constraint
    applies_to: [ForbiddenVocabularyList]
    trigger: Al escanear un texto
    logic: SI tras quitar mayúsculas y tildes un término aparece como palabra completa ENTONCES hay coincidencia; SI aparece solo como parte de otra palabra (p. ej. «falsete») ENTONCES no.
    violation: Fixture de control en rojo.
    source: AC5.5.1; components IntegrityPolicy
  - id: BR5.3
    statement: Dentro de una CoT, una cita es el texto entre «…» que aparece literal en el fragmento del turno o en un pasaje recuperado; solo esa cita se excluye del escaneo.
    category: policy
    applies_to: [ForbiddenVocabularyList, JudgeOutput]
    trigger: Al escanear la CoT
    logic: SI un tramo está entre «…» Y su contenido aparece carácter a carácter en el fragmento o en un pasaje recuperado para esa afirmación ENTONCES se excluye; SI no aparece ENTONCES se escanea como texto normal.
    violation: Fixture de control en rojo.
    source: Respuesta P1 = A; AC3.2.4; AC5.5.2
  - id: BR5.4
    statement: Una CoT con vocabulario prohibido fuera de las citas literales es salida inválida del juez.
    category: validation
    applies_to: [JudgeOutput]
    trigger: Al validar la salida del juez
    logic: SI el escaneo de cot encuentra una coincidencia fuera de los tramos excluidos ENTONCES la salida es inválida.
    violation: turn.error.invalid_output; 0 alertas.
    source: AC3.2.4; AUTONOMIA-03
  - id: BR5.5
    statement: Los campos fragment y quote de la alerta y el texto escrito por el analista se excluyen enteros del escaneo.
    category: policy
    applies_to: [Alert, ForbiddenVocabularyList]
    trigger: Al escanear una alerta o un reporte
    logic: SI el texto es fragment, quote o texto del analista ENTONCES no se escanea.
    violation: Fixture de control en rojo.
    source: AC5.5.1; AC5.5.2

  # BR6 — Rótulos de resultado
  - id: BR6.1
    statement: El catálogo de rótulos tiene exactamente tres rótulos de resultado y la consola no define otros.
    category: constraint
    applies_to: [ResultLabelCatalog]
    trigger: Al validar el catálogo
    logic: SI el catálogo no tiene exactamente «Sugerencia de revisión», «Incongruencia semántica» y «Hecho No Documentado» ENTONCES la suite falla.
    violation: Suite en rojo.
    source: Respuesta P3 = A; AC5.5.4
  - id: BR6.2
    statement: Cada calificación se muestra con un rótulo fijo, y congruente no tiene rótulo de resultado.
    category: constraint
    applies_to: [ResultLabelCatalog, Grade]
    trigger: Al validar el catálogo
    logic: SI incongruente no apunta a «Incongruencia semántica», no documentada no apunta a «Hecho No Documentado» o congruente tiene rótulo ENTONCES la suite falla.
    violation: Suite en rojo.
    source: Respuesta P3 = A; AC5.5.4
  - id: BR6.3
    statement: Los rótulos pasan el escaneo de vocabulario prohibido.
    category: validation
    applies_to: [ResultLabelCatalog]
    trigger: Al validar el catálogo
    logic: SI un rótulo contiene un término de C8 ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC5.5.1

  # BR7 — API de la consola (C1) y catálogo de errores
  - id: BR7.1
    statement: El OpenAPI no tiene ninguna operación que escriba el umbral.
    category: constraint
    applies_to: [ContractDocument]
    trigger: Al validar C1
    logic: SI alguna operación POST, PUT, PATCH o DELETE tiene una ruta, un parámetro o una propiedad del cuerpo cuyo nombre contiene threshold o umbral (sin distinguir mayúsculas) ENTONCES la suite falla; el control negativo es una copia del OpenAPI con esa ruta añadida.
    violation: Suite en rojo.
    source: AC8.3.1; FR9.1; AUTONOMIA-03
  - id: BR7.2
    statement: Todo error de C1 es Problem Details con un code del catálogo único y un detail en español.
    category: constraint
    applies_to: [ErrorCodeCatalog, ContractDocument]
    trigger: Al validar C1
    logic: SI una respuesta 4xx o 5xx no referencia el esquema Problem, o un code usado en C1–C5 no está en el catálogo ENTONCES la suite falla.
    violation: Suite en rojo.
    source: NFR10; NFR14; contract-summary regla 6
  - id: BR7.3
    statement: Todo cuerpo de petición de C1 rechaza campos adicionales.
    category: validation
    applies_to: [ContractDocument]
    trigger: Al validar C1
    logic: SI un cuerpo application/json de una petición no declara additionalProperties false ENTONCES la suite falla.
    violation: Suite en rojo.
    source: NFR10

  # BR8 — Fecha y métricas
  - id: BR8.1
    statement: Toda fecha de los contratos es RFC 3339 en UTC con Z, con precisión de segundos y sin fracciones ni desfases.
    category: validation
    applies_to: [UtcTimestamp, MessageEnvelope, ContractDocument]
    trigger: Al validar cualquier campo date-time
    logic: SI la fecha no tiene la forma AAAA-MM-DDTHH:MM:SSZ o no es una fecha real ENTONCES es inválida.
    violation: Rechazo del mensaje o de la respuesta.
    source: Respuesta P4 = A; contract-summary C1
  - id: BR8.2
    statement: Las métricas usan el prefijo veridicus_ y sus etiquetas solo llevan identificadores o valores de enum.
    category: constraint
    applies_to: [MetricDefinition]
    trigger: Al validar C15
    logic: SI una métrica no empieza por veridicus_ o declara una etiqueta de texto libre ENTONCES la suite falla.
    violation: Suite en rojo.
    source: NFR10; NFR15; contract-summary C15
```

## Resumen

| Grupo | Reglas | De qué protege |
|---|---|---|
| BR1 Versión y cambio | BR1.1–BR1.6 | Que productor y consumidores rompan sin aviso; datos reales en *fixtures* |
| BR2 Mensajes de cola | BR2.1–BR2.5 | Turnos mal formados (AC2.2.3), alertas parciales (FR4.2) y alertas por debajo del umbral (AUTONOMIA-05) |
| BR3 Salida del juez | BR3.1–BR3.4 | Campos extra o de veracidad, enum distinto de tres valores, códigos de error confundidos |
| BR4 Alerta | BR4.1–BR4.2 | Alerta sin sus 4 campos (AUTONOMIA-05) o con `is_truthful` (AUTONOMIA-03) |
| BR5 Vocabulario prohibido | BR5.1–BR5.5 | Etiquetas de veracidad en la CoT; «miente» camuflado entre comillas inventadas (P1) |
| BR6 Rótulos | BR6.1–BR6.3 | Rótulos de resultado distintos de los tres permitidos (P3) |
| BR7 API de la consola | BR7.1–BR7.3 | Una ruta que escriba el umbral (AC8.3.1); errores fuera del catálogo |
| BR8 Fecha y métricas | BR8.1–BR8.2 | Fechas ambiguas en el SHA-256 del reporte (P4); texto sensible en métricas |
