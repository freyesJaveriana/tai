# Reglas de negocio — U1 contracts

**Revisión 2 (2026-11-09), segunda pasada por el cambio 01 (DT27), la adenda 02 y el cambio 03.**
Sustituye a la revisión 1 del 2026-10-03.
- Las reglas conservan su ID. Las que salen quedan con `status: Retirado` y no se renumeran (regla de
  `project.md`).
- Las nuevas siguen la numeración de su grupo (BR1.7 en adelante) o abren los grupos BR9–BR12.

**Insumos.** Los mismos de `entities.md`: unit-of-work, contract-summary, requirements, components, la
copia aprobada del contrato común, el cambio 03 y las respuestas P1–P8 y V-1 = A de
`functional-design-questions.md`.

**Cómo se prueban.** Salvo que la regla diga otra cosa, cada una se prueba en **nivel 0** con un
*fixture* positivo y uno negativo (control negativo).

```yaml
rules:
  # BR1 — Versión y cambio de contratos
  - id: BR1.1
    status: se mantiene
    statement: Todo contrato tiene versión semántica y todo mensaje de cola declara schema_version.
    category: constraint
    applies_to: [ContractDocument, MessageEnvelope]
    trigger: Al validar un contrato o un mensaje
    logic: SI falta la versión o no tiene la forma MAYOR.MENOR.PARCHE ENTONCES el contrato o el mensaje es inválido.
    violation: La suite de contratos falla; el mensaje se rechaza.
    source: contract-summary P2; NFR10
  - id: BR1.2
    status: cambia
    statement: Un mensaje de C2, C3 o C5 con una versión mayor que el consumidor no conoce se rechaza sin crear filas.
    category: validation
    applies_to: [MessageEnvelope, RunRequest, RunResult]
    trigger: Al recibir un mensaje de C2, C3 o C5
    logic: SI el mayor de schema_version no está entre los mayores conocidos ENTONCES el mensaje va a <cola>:failed y no se procesa.
    violation: Rechazo; ninguna fila nueva.
    source: contract-summary P2 y regla 5; AC2.2.3
  - id: BR1.3
    status: se mantiene
    statement: Un cambio aditivo sube la versión menor; los consumidores ignoran los campos desconocidos en los sobres de C2, C3 y C5 y en las respuestas de C1.
    category: policy
    applies_to: [ContractDocument, MessageEnvelope]
    trigger: Al cambiar un contrato no estricto
    logic: SI el cambio solo añade un campo opcional o una ruta ENTONCES sube el menor y los fixtures anteriores siguen aceptándose.
    violation: La prueba de compatibilidad de fixtures anteriores falla.
    source: contract-summary regla 4
  - id: BR1.4
    status: cambia
    statement: En los contratos estrictos (C6, C7, C18 con la configuración efectiva, C19 con el registro de llamadas, C21) todo cambio de forma es mayor y entra en un solo PR con productor y consumidores.
    category: policy
    applies_to: [ContractDocument]
    trigger: Al cambiar un contrato estricto
    logic: SI cambia la forma de un contrato estricto ENTONCES sube el mayor y cambia el $id; en C6 además se aplica BR1.8.
    violation: La prueba que compara $id y versión falla.
    source: contract-summary reglas 4 y 5
  - id: BR1.5
    status: se mantiene
    statement: Cada cambio de contrato entra por su propio PR con sus fixtures positivos y negativos.
    category: policy
    applies_to: [ContractDocument, Fixture]
    trigger: Al proponer un cambio
    logic: SI un PR cambia un contrato ENTONCES cambia solo ese contrato, sube su versión y trae al menos un fixture que ejercita el cambio.
    violation: Revisión del PR (comprobación del autor con la evidencia de la suite).
    source: unit-of-work U1 Restricciones; team.md
  - id: BR1.6
    status: cambia
    statement: Ningún fixture contiene datos reales, y los papeles de prueba son sintéticos.
    category: constraint
    applies_to: [Fixture]
    trigger: En cada PR
    logic: SI un fixture contiene un nombre, testimonio o expediente que no está marcado como sintético, o un nombre de papel o dato de sistema, ENTONCES la suite falla.
    violation: La comprobación de datos sintéticos de la suite falla.
    source: NFR12; project.md Forbidden; cambio 03 §3
  - id: BR1.7
    status: nuevo
    statement: La copia del contrato común en contracts/analyzer/v1/ es idéntica byte a byte a lo aprobado en el principal.
    category: validation
    applies_to: [ApprovedCopyManifest, AnalyzerInput, AnalyzerOutput]
    trigger: En cada PR (nivel 0)
    logic: SI el SHA-256 de entrada.schema.json o de salida.schema.json difiere de su línea en SHA256SUMS, o SHA256SUMS no tiene exactamente esas dos líneas, o contrato no es const "1.0.0" en los dos esquemas ENTONCES la suite falla.
    violation: Suite en rojo. El control negativo es una copia con un byte cambiado en una descripción.
    source: cambio 03 §1; P5 = A; AC3.6.2
  - id: BR1.8
    status: nuevo
    statement: La copia de C6 nunca se edita aquí; un cambio se aprueba en el principal y entra como copia nueva en su propio PR, con su SHA256SUMS.
    category: policy
    applies_to: [ContractDocument, ApprovedCopyManifest]
    trigger: Al cambiar C6
    logic: SI un PR cambia un esquema de contracts/analyzer/ sin cambiar SHA256SUMS a las huellas publicadas por el principal ENTONCES BR1.7 lo rechaza; SI cambia la forma ENTONCES llega como v2/ con contrato "2.0.0" y la v1 se conserva.
    violation: Suite en rojo; revisión del PR.
    source: cambio 03 §1; README del contrato v1.0.0 («Cómo se cambia»); ADR-017
  - id: BR1.9
    status: nuevo
    statement: Todo esquema de contracts/ se carga con un validador estricto que trata como error una palabra clave desconocida.
    category: validation
    applies_to: [ContractDocument]
    trigger: En cada PR (nivel 0)
    logic: SI un esquema no pasa el metaesquema de 2020-12 en modo estricto (jsonschema en Python, ajv strict en TypeScript) ENTONCES la suite falla.
    violation: Suite en rojo.
    source: contract-summary regla 1

  # BR2 — Mensajes de cola
  - id: BR2.1
    status: cambia
    statement: Un mensaje de corrida (C2) sin un campo obligatorio, con un tipo erróneo o con una entrada que no cumple C6 se rechaza sin crear filas.
    category: validation
    applies_to: [RunRequest]
    trigger: Al publicar y al consumir C2
    logic: SI el mensaje no cumple C2 o su entrada no cumple la copia de C6 ENTONCES va a veridicus:runs:failed sin analizarse.
    violation: Rechazo; ninguna fila.
    source: AC2.2.3; contract-summary C2
  - id: BR2.2
    status: Retirado
    statement: "Instantánea del umbral en el mensaje de turno. Sale con el umbral de similitud (cambio 01)."
    source: cambio 01 (DT27)
  - id: BR2.3
    status: cambia
    statement: Un resultado (C3) solo es válido si su salida cumple la copia de C6.
    category: validation
    applies_to: [RunResult, AnalyzerOutput]
    trigger: Al validar C3 en la ingesta
    logic: SI salida no cumple C6 ENTONCES el resultado es inválido.
    violation: La corrida queda en error con analysis.invalid_output (lo aplica U4).
    source: AC3.2.1; contract-summary C3
  - id: BR2.4
    status: Retirado
    statement: "Alerta solo sobre afirmación incongruente sobre el umbral. Sale con el umbral y las calificaciones (cambio 01)."
    source: cambio 01 (DT27)
  - id: BR2.5
    status: Retirado
    statement: "Paquete de traspaso ante una afirmación no documentada. Sale con el Hecho No Documentado (cambio 01)."
    source: cambio 01 (DT27)

  # BR3 — Contrato común (C6)
  - id: BR3.1
    status: cambia
    statement: La salida del analizador solo acepta los campos de C6; un campo adicional en cualquier nivel o un campo obligatorio ausente la invalida.
    category: validation
    applies_to: [AnalyzerOutput, Finding, Quote, CallRecord]
    trigger: Al validar una salida
    logic: SI hay una propiedad no declarada o falta un campo obligatorio ENTONCES la salida es inválida (un fixture negativo por cada campo obligatorio del hallazgo).
    violation: Salida inválida (salida_invalida en U11, analysis.invalid_output en U4).
    source: AC3.6.2; AC3.2.1; AC5.5.3; AUTONOMIA-05
  - id: BR3.2
    status: cambia
    statement: Los enum de C6 tienen exactamente sus valores, y todo contrato de Veridicus que copia uno de ellos usa los mismos valores.
    category: constraint
    applies_to: [AnalyzerOutput, FindingType, CallRecord, CliReport, ContractDocument]
    trigger: Al validar todos los contratos
    logic: SI tipo no tiene los 7 valores, estado los 2, error.codigo los 6, motivo los 8 o papel los 3 de la copia, o si C1 (ModelCall.papel, Run), C19 (error_code, discards, fact_type) o C7 (tipo) difieren de ellos ENTONCES la suite falla.
    violation: Suite en rojo.
    source: contract-summary regla 8; AC5.5.4; AC3.2.1
  - id: BR3.3
    status: se mantiene
    statement: Ningún esquema de contracts/ declara un campo de veracidad.
    category: constraint
    applies_to: [ContractDocument, AnalyzerOutput, ReviewSuggestion]
    trigger: Al validar todos los esquemas
    logic: SI algún nombre de propiedad coincide con categories_forbidden_in_schemas o con un término de C8 ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC5.5.3; AUTONOMIA-03
  - id: BR3.4
    status: cambia
    statement: Cada error.codigo de C6 se traduce a un code distinto y estable del catálogo, y la tabla es uno a uno.
    category: constraint
    applies_to: [ErrorCodeCatalog]
    trigger: Al validar el catálogo
    logic: SI falta la traducción de alguno de los seis error.codigo, dos códigos comparten code, o un code con c6_codigo no existe en C1 ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC3.2.1; contract-summary P8 y tabla de C1
  - id: BR3.5
    status: nuevo
    statement: Una entrada con origen corpus o guiada sin bloque consentimiento se rechaza; con origen sintetico se acepta sin él.
    category: validation
    applies_to: [AnalyzerInput, Consent]
    trigger: Al validar una entrada
    logic: SI origen es corpus o guiada y no hay consentimiento ENTONCES inválida; SI tipo es autoridad sin constancia, o requiere_mandato es true sin constancia_mandato, ENTONCES inválida.
    violation: Rechazo antes de cualquier llamada (lo aplican U11 y U4 con este esquema).
    source: AC15.4.7; A-4; VE-06; contract-summary C6 (fixtures)
  - id: BR3.6
    status: nuevo
    statement: Con estado error la salida trae error y deja vacíos hallazgos y observaciones_conductor; con estado ok no trae error.
    category: validation
    applies_to: [AnalyzerOutput]
    trigger: Al validar una salida
    logic: SI estado es error y falta error, o hay un hallazgo o una observación ENTONCES inválida; SI estado es ok y hay error ENTONCES inválida.
    violation: Salida inválida.
    source: AC3.2.1; FR4.2; AUTONOMIA-05

  # BR4 — Sugerencia de revisión (C7)
  - id: BR4.1
    status: cambia
    statement: Una sugerencia sin hecho, tipo, cita_a, cita_b u observaciones, o con uno de ellos vacío, se rechaza.
    category: validation
    applies_to: [ReviewSuggestion]
    trigger: Al guardar y al mostrar una sugerencia
    logic: SI falta o está vacío alguno de los cinco campos ENTONCES la sugerencia es inválida (cinco fixtures negativos, uno por campo).
    violation: Rechazo.
    source: AUTONOMIA-05; FR4.4
  - id: BR4.2
    status: se mantiene
    statement: La sugerencia rechaza cualquier campo adicional, como is_truthful.
    category: validation
    applies_to: [ReviewSuggestion]
    trigger: Al validar C7
    logic: SI trae una propiedad no declarada ENTONCES es inválida.
    violation: Rechazo.
    source: AC5.5.3; AUTONOMIA-03
  - id: BR4.3
    status: nuevo
    statement: Las citas de C7 referencian la definición de cita de la copia de C6; no hay una segunda definición.
    category: constraint
    applies_to: [ReviewSuggestion, Quote]
    trigger: Al validar C7
    logic: SI cita_a o cita_b de C7 no es un $ref a salida.schema.json#/$defs/cita ENTONCES la suite falla.
    violation: Suite en rojo.
    source: contract-summary C7 y regla 8

  # BR5 — Vocabulario prohibido, aclaraciones y aviso (C8)
  - id: BR5.1
    status: se mantiene
    statement: La lista tiene exactamente los 9 términos aprobados; cada ampliación entra por su propio PR con su control negativo.
    category: policy
    applies_to: [ForbiddenVocabularyList]
    trigger: Al validar C8
    logic: SI la lista difiere de mentiroso, mentirosa, miente, mintió, falso, falsa, verdadero, verdadera, engaño sin un PR que la amplíe ENTONCES la suite falla; SI una versión añade un término sin fixture negativo que lo use ENTONCES la suite falla.
    violation: Suite en rojo.
    source: Respuesta P2 = A; contract-summary C8
  - id: BR5.2
    status: se mantiene
    statement: La coincidencia es por palabra completa, sin distinguir mayúsculas ni tildes.
    category: constraint
    applies_to: [ForbiddenVocabularyList]
    trigger: Al escanear un texto
    logic: SI tras quitar mayúsculas y tildes un término aparece como palabra completa ENTONCES hay coincidencia; SI solo aparece dentro de otra palabra («falsete») ENTONCES no.
    violation: Fixture de control en rojo.
    source: AC5.5.1; components IntegrityPolicy
  - id: BR5.3
    status: cambia
    statement: Dentro de hecho, observaciones y tema, una cita es el texto entre «…» que aparece literal en un turno de la transcripción de entrada; solo esa cita se excluye del escaneo.
    category: policy
    applies_to: [ForbiddenVocabularyList, Finding]
    trigger: Al escanear la salida
    logic: SI un tramo está entre «…» Y su contenido aparece carácter a carácter (salvo espacios, regla del piloto) en un turno de la entrada ENTONCES se excluye; SI no ENTONCES se escanea como texto normal.
    violation: Fixture de control en rojo.
    source: Respuesta P1 = A; AC3.2.4; C8 excluded_spans cita_literal
  - id: BR5.4
    status: cambia
    statement: Una salida con vocabulario prohibido en hecho, observaciones o tema fuera de las citas literales es salida inválida.
    category: validation
    applies_to: [AnalyzerOutput, Finding]
    trigger: Al validar una salida (lo aplica U11 con la lista de U1)
    logic: SI el escaneo encuentra una coincidencia fuera de los tramos excluidos ENTONCES el candidato se descarta con motivo vocabulario_prohibido o la salida es salida_invalida, según la regla de U11.
    violation: Ninguna etiqueta de veracidad llega al analista.
    source: AC3.2.4; AUTONOMIA-03; C6 regla 3
  - id: BR5.5
    status: cambia
    statement: El texto de cita_a y cita_b, el texto del analista (nota y reformulación) y el texto del aviso se excluyen enteros del escaneo.
    category: policy
    applies_to: [Quote, ReviewSuggestion, NoticeText, ForbiddenVocabularyList]
    trigger: Al escanear una salida, una sugerencia o un reporte
    logic: SI el texto es una cita, una nota, una reformulación o el aviso ENTONCES no se escanea.
    violation: Fixture de control en rojo.
    source: AC5.5.1; AC5.5.2; C8 (VE-02)
  - id: BR5.6
    status: nuevo
    statement: El tema de una aclaración neutra no menciona una contradicción, no usa las frases prohibidas y no cita un turno.
    category: validation
    applies_to: [NeutralClarificationRule, AnalyzerOutput]
    trigger: Al validar observaciones_conductor (lo aplica U11; U8 lo muestra)
    logic: SI tema contiene «contradicción», «contradice», «incoherencia», una frase de phrases, «T<n>» o «turno <n>» ENTONCES la aclaración es inválida.
    violation: Fixture de control en rojo.
    source: VE-05; DT23; contract-summary C8
  - id: BR5.7
    status: nuevo
    statement: El aviso de VE-01 tiene versión y contiene la frase base; la consola y el reporte muestran esa misma versión.
    category: constraint
    applies_to: [NoticeText]
    trigger: Al validar C8
    logic: SI notice.v1.yaml no tiene version semántica o su texto no contiene la frase base de VE-01 ENTONCES la suite falla.
    violation: Suite en rojo.
    source: VE-01; contract-summary C8

  # BR6 — Rótulos de resultado
  - id: BR6.1
    status: cambia
    statement: El catálogo tiene exactamente los rótulos «Sugerencia de revisión», «Contradicción en el relato» y los 7 de tipo, y la consola no define otros.
    category: constraint
    applies_to: [ResultLabelCatalog]
    trigger: Al validar el catálogo
    logic: SI el catálogo no tiene exactamente esas nueve filas con «Fecha», «Número», «Lugar», «Persona», «Negación», «Secuencia» y «Otro» ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC5.5.4; respuestas P3 = A y P8 = A
  - id: BR6.2
    status: cambia
    statement: Cada valor de tipo de C6 tiene exactamente un rótulo, y no hay rótulo para un valor que no existe.
    category: constraint
    applies_to: [ResultLabelCatalog, FindingType]
    trigger: Al validar el catálogo
    logic: SI algún valor de FindingType no tiene fila, o una fila type_* apunta a un valor que no está en la copia de C6 ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC5.5.4; respuesta P8 = A
  - id: BR6.3
    status: se mantiene
    statement: Los rótulos pasan el escaneo de vocabulario prohibido.
    category: validation
    applies_to: [ResultLabelCatalog]
    trigger: Al validar el catálogo
    logic: SI un rótulo contiene un término de C8 ENTONCES la suite falla.
    violation: Suite en rojo.
    source: AC5.5.1

  # BR7 — API de la consola (C1) y catálogo de errores
  - id: BR7.1
    status: cambia
    statement: El OpenAPI no tiene ninguna operación que escriba perfiles, proveedores, prompts, la tabla de precios o los límites.
    category: constraint
    applies_to: [ContractDocument]
    trigger: Al validar C1
    logic: SI una operación POST, PUT, PATCH o DELETE tiene una ruta, un parámetro o una propiedad del cuerpo cuyo nombre contiene profile, perfil, provider, proveedor, prompt, price, precio, limit o límite (sin distinguir mayúsculas ni tildes) ENTONCES la suite falla. Lista de excepciones explícita, con su motivo, para los campos que solo eligen un perfil aprobado (profile_name al crear la sesión). Control negativo: una copia del OpenAPI con PUT /profiles.
    violation: Suite en rojo.
    source: AC8.3.1; FR9.2; contract-summary regla 7
  - id: BR7.2
    status: se mantiene
    statement: Todo error de C1 es Problem Details con un code del catálogo único y un detail en español.
    category: constraint
    applies_to: [ErrorCodeCatalog, ContractDocument]
    trigger: Al validar C1
    logic: SI una respuesta 4xx o 5xx no referencia el esquema Problem, o un code usado en C1, C2, C3, C5, C17 o C21 no está en el catálogo ENTONCES la suite falla.
    violation: Suite en rojo.
    source: NFR10; NFR14; contract-summary regla 6
  - id: BR7.3
    status: se mantiene
    statement: Todo cuerpo de petición de C1 rechaza campos adicionales.
    category: validation
    applies_to: [ContractDocument]
    trigger: Al validar C1
    logic: SI un cuerpo application/json de una petición no declara additionalProperties false ENTONCES la suite falla.
    violation: Suite en rojo.
    source: NFR10
  - id: BR7.4
    status: nuevo
    statement: Cada code del catálogo tiene exactamente una clase de excepción sin lógica en libs/, y cada clase tiene su code.
    category: constraint
    applies_to: [ErrorCodeCatalog, ExceptionClass]
    trigger: En cada PR (nivel 0)
    logic: SI un code no tiene clase, una clase no tiene code, dos clases comparten code o una clase define métodos propios ENTONCES la suite falla.
    violation: Suite en rojo.
    source: unit-of-work U1 Límites; R-02 de la revisión 2 de Units Generation

  # BR8 — Fecha y métricas
  - id: BR8.1
    status: cambia
    statement: Toda fecha que emite Veridicus es RFC 3339 en UTC con Z, con precisión de segundos y sin fracciones ni desfases.
    category: validation
    applies_to: [UtcTimestamp, MessageEnvelope, ContractDocument]
    trigger: Al validar un campo date-time de un contrato propio de Veridicus
    logic: SI la fecha no tiene la forma AAAA-MM-DDTHH:MM:SSZ o no es una fecha real ENTONCES es inválida. La copia de C6 no se toca (BR1.8); su format date-time admite esta forma.
    violation: Rechazo del mensaje o de la respuesta.
    source: Respuesta P4 = A; contract-summary C1
  - id: BR8.2
    status: se mantiene
    statement: Las métricas usan el prefijo veridicus_ y sus etiquetas solo llevan identificadores o valores de enum.
    category: constraint
    applies_to: [MetricDefinition]
    trigger: Al validar C15
    logic: SI una métrica no empieza por veridicus_ o declara una etiqueta de texto libre ENTONCES la suite falla.
    violation: Suite en rojo.
    source: NFR10; NFR15; contract-summary C15

  # BR9 — Papeles y perfiles (V-1, opción A)
  - id: BR9.1
    status: nuevo
    statement: El papel de una llamada es una cadena con patrón y no una lista cerrada en model_calls, model-call.v1.yaml y la petición del proxy.
    category: constraint
    applies_to: [RoleName, ModelCall]
    trigger: Al validar C13 (tipos), C19 (registro de llamadas) y C21
    logic: SI alguno de los tres declara un enum de papeles, o acepta un papel que no cumple ^[a-z][a-z0-9_]{0,31}$ ENTONCES la suite falla. Fixtures sintéticos prueba_a y prueba_b se aceptan; «Prueba A» y una cadena de 33 caracteres se rechazan.
    violation: Suite en rojo.
    source: cambio 03 V-1; decisión V-1 = A
  - id: BR9.2
    status: nuevo
    statement: Un perfil genérico declara al menos un papel; cada alias apunta a un papel declarado, sin cadenas y sin pisar un papel.
    category: validation
    applies_to: [ProfileBase]
    trigger: Al validar un archivo de perfiles contra profile-base
    logic: SI roles está vacío, un alias apunta a un papel que no está en roles, el destino de un alias es otro alias, o un alias tiene el mismo nombre que un papel ENTONCES el perfil es inválido. El esquema cubre la forma; la referencia cruzada la comprueba la función de validación que U1 publica junto al esquema.
    violation: El perfil no se carga (el servicio no arranca, la CLI termina antes de llamar).
    source: cambio 03 V-1; AC13.3.1
  - id: BR9.3
    status: nuevo
    statement: Un perfil del analizador tiene exactamente los papeles judge y verifier y el alias verifier_permuted → verifier.
    category: validation
    applies_to: [AnalyzerProfile]
    trigger: Al validar config/profiles.yaml de Veridicus o un perfil que reciba el analizador
    logic: SI faltan judge o verifier, hay otro papel, o role_aliases no es exactamente { verifier_permuted: verifier } ENTONCES el perfil es inválido.
    violation: El perfil no se carga.
    source: cambio 03 V-1 («el analizador sigue exigiendo los suyos»); AC13.3.1
  - id: BR9.4
    status: nuevo
    statement: El esquema solo exige la forma de api_key_ref; el prefijo lo exige quien carga el perfil, y Veridicus usa VERIDICUS_.
    category: constraint
    applies_to: [Destination, KeyPrefix]
    trigger: Al validar un perfil y al cargarlo
    logic: SI api_key_ref no cumple ^[A-Z][A-Z0-9_]{2,63}$ ENTONCES el perfil es inválido. SI el esquema de un perfil fija un prefijo ENTONCES la suite falla, porque el prefijo no va en el archivo. La función de validación de U1 recibe el prefijo como argumento, y el esquema no fija un valor por omisión. Los cargadores de Veridicus (U10, U11) le pasan la constante VERIDICUS_.
    violation: Suite en rojo; el perfil no se carga.
    source: cambio 03 V-1; decisión V-1 = A
  - id: BR9.5
    status: nuevo
    statement: Un perfil tiene como mucho un proveedor alterno, que sirve a cualquier papel.
    category: constraint
    applies_to: [ProfileBase]
    trigger: Al validar un perfil
    logic: SI un papel declara su propio fallback ENTONCES el perfil es inválido.
    violation: El perfil no se carga.
    source: Respuesta P7 = A; FR15.2
  - id: BR9.6
    status: nuevo
    statement: Solo los tres papeles del analizador se traducen a registro.llamadas de C6, con la tabla fija que publica U1.
    category: constraint
    applies_to: [RoleTranslation, CallRecord]
    trigger: Al validar la tabla (nivel 0)
    logic: SI la tabla no tiene exactamente judge → juez, verifier → verificador, verifier_permuted → verificador_permutado ENTONCES la suite falla.
    violation: Suite en rojo. Un papel sin fila no puede aparecer en una salida de C6 (U11 lo prueba).
    source: cambio 03 V-1 (C6 no cambia); contract-summary regla 8
  - id: BR9.7
    status: nuevo
    statement: La configuración efectiva contiene un perfil del analizador y su huella es la del fixture con forma canónica JCS.
    category: calculation
    applies_to: [EffectiveConfig, AnalyzerProfile]
    trigger: Al validar C18 y C2 (nivel 0, Python y TypeScript)
    logic: SI profile no cumple AnalyzerProfile, o el SHA-256 recalculado de la forma canónica del fixture effective-config.valid.json difiere del esperado ENTONCES la suite falla.
    violation: Suite en rojo.
    source: contract-summary C18; FR14.2; AC8.3.3

  # BR10 — Reporte de la CLI (C19)
  - id: BR10.1
    status: nuevo
    statement: El reporte de la CLI no tiene campos de texto libre; toda cadena es enum o tiene pattern sin espacios y con tope de 128 caracteres.
    category: constraint
    applies_to: [CliReport]
    trigger: Al validar C19 (nivel 0)
    logic: SI alguna propiedad de tipo string del esquema no tiene enum, const o pattern acotado sin espacios ENTONCES la suite falla; los fixtures report.testimony-in-model.json y report.testimony-in-price-table.json se rechazan.
    violation: Suite en rojo; la consola rechaza con 422 research.invalid_report (U12).
    source: contract-summary C19 y P12; AC12.6.1 (ver precisión FD-U1-05)
  - id: BR10.2
    status: nuevo
    statement: En el reporte de la CLI el papel de cada llamada es uno de los tres del analizador.
    category: validation
    applies_to: [CliReport, ModelCall]
    trigger: Al validar C19
    logic: SI runs[].calls[].role no es judge, verifier ni verifier_permuted ENTONCES el reporte es inválido (allOf sobre el registro genérico de BR9.1).
    violation: Rechazo.
    source: cambio 03 V-1; decisión V-1 = A

  # BR11 — Catálogo de límites (C25)
  - id: BR11.1
    status: nuevo
    statement: El catálogo de límites tiene un nombre único por cifra, con su unidad, y una variable de entorno solo puede bajarla.
    category: constraint
    applies_to: [LimitsCatalog]
    trigger: Al validar C25 y al leerlo
    logic: SI falta un nombre de C25, un nombre se repite o una cifra no tiene unidad ENTONCES la suite falla; la función de lectura que publica U1 rechaza un valor de entorno mayor que el del catálogo.
    violation: Suite en rojo; el servicio no arranca.
    source: contract-summary C25; regla de project.md (límites)

  # BR12 — Paquete instalable (V-3, P6 = A)
  - id: BR12.1
    status: nuevo
    statement: Los contratos se instalan como la distribución veridicus-contracts y se importan como veridicus_contracts, con sus esquemas como datos del paquete.
    category: constraint
    applies_to: [ContractsPackage]
    trigger: En cada PR (nivel 0)
    logic: SI el paquete construido no se instala en un entorno limpio sin Redis, Kubernetes ni base de datos, o no trae cada esquema y catálogo de contracts/ como dato, o algún módulo se importa como contracts ENTONCES la suite falla.
    violation: Suite en rojo.
    source: cambio 03 V-3; respuesta P6 = A
  - id: BR12.2
    status: nuevo
    statement: Al cerrar B1 se etiqueta una versión vX.Y.Z del repositorio para que sistema la fije.
    category: policy
    applies_to: [ContractsPackage]
    trigger: Al fusionar el PR de B1
    logic: SI B1 cierra sin etiqueta ENTONCES la entrega no está completa.
    violation: Revisión del PR del autor (manual).
    source: cambio 03 V-3
```

## Resumen

| Grupo | Reglas vigentes | Retiradas | De qué protege |
|---|---|---|---|
| BR1 Versión y cambio | BR1.1–BR1.9 | — | Contratos que cambian sin aviso, datos reales en *fixtures*, una copia de C6 editada aquí (P5) |
| BR2 Mensajes de cola | BR2.1, BR2.3 | BR2.2, BR2.4, BR2.5 | Corridas mal formadas (AC2.2.3) y resultados que no cumplen C6 |
| BR3 Contrato común | BR3.1–BR3.6 | — | Campos extra o de veracidad, enum distintos entre contratos, error con hallazgos, entradas sin consentimiento (AC15.4.7) |
| BR4 Sugerencia | BR4.1–BR4.3 | — | Sugerencia sin sus cinco campos (AUTONOMIA-05) o con `is_truthful` (AUTONOMIA-03) |
| BR5 Vocabulario, aclaraciones y aviso | BR5.1–BR5.7 | — | Etiquetas de veracidad en la salida, aclaraciones que delatan la contradicción (VE-05), aviso sin versión (VE-01) |
| BR6 Rótulos | BR6.1–BR6.3 | — | Rótulos distintos de los nueve permitidos (AC5.5.4, P8) |
| BR7 API y errores | BR7.1–BR7.4 | — | Una ruta que escriba configuración (AC8.3.1), errores fuera del catálogo, códigos sin excepción |
| BR8 Fecha y métricas | BR8.1–BR8.2 | — | Fechas ambiguas en las huellas, texto sensible en métricas |
| BR9 Papeles y perfiles | BR9.1–BR9.7 | — | Papeles cerrados que impiden reutilizar a `sistema`, perfiles del analizador incompletos, claves fuera del prefijo |
| BR10 Reporte de la CLI | BR10.1–BR10.2 | — | Testimonio dentro del reporte (P12) |
| BR11 Límites | BR11.1 | — | Cifras sueltas o subidas por entorno |
| BR12 Paquete | BR12.1–BR12.2 | — | Choque de nombres en `sistema` y una entrega sin etiqueta (V-3) |
