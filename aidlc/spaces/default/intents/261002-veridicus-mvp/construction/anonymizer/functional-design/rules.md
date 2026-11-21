# Reglas de negocio — U10 anonymizer

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-02. Las reglas conservan su ID; las que salen quedan con
`status: Retirado` y nombran a su nuevo dueño, sin renumerar (regla de `project.md`). Las nuevas siguen la
numeración de su grupo o abren los grupos BR4–BR6.
- **Siguen**, con cambios: BR1.1 (seudonimización, ahora con cinco categorías y una marca por forma
  exacta), BR1.2 (NER ∪ reglas, sin la lista del escenario), BR1.3 (restauración solo sobre valores de
  cadena), BR2.1 (fallo cerrado con `AnonymizerUnavailable`, que sustituye a `turn.error.system`), BR2.2
  (arranque con perfiles, claves, NER y listas), BR2.3 (logs solo con IDs) y BR3.1 (ahora la salida la
  restringe el módulo a los dominios de la lista; la `NetworkPolicy` es de U2).
- **Salen**: BR1.4 (`embed`, que sale de C13), BR3.2 (pasa a U11: no arrancar con un destino externo sin
  anonimizador, FR14.3, US13.3), BR3.3 (pasa a U2: verificación manual en el clúster, US9.1) y BR3.4 (pasa
  a U2: tabla de fronteras de Infrastructure Design, AC9.1.3).
- **Entran**: BR1.5–BR1.8, BR2.4–BR2.6, BR3.5–BR3.6, BR4 (marcas alteradas), BR5 (adaptadores nativos,
  C22) y BR6 (`anonymizer-proxy`, C21). Origen en cada regla.

**Insumos.** Los mismos de `entities.md`: unit-of-work y unit-of-work-story-map (U10, US11.3, US11.5 y
las historias que la cruzan), requirements (FR11.3, FR11.4, FR14.3, FR15.1–FR15.3, NFR1, NFR10; VE-14 de
la adenda 02), components (Anonymizer; ADR-011, ADR-013), contract-summary (C13, C16, C18, C20, C21,
C22, C25; CD-01, CD-02, CD-04, CD-09), lo que U10 importa de U1 (el `Protocol` `AnonymizingProvider` y la validación de perfiles) y las respuestas P1–P8 de
`functional-design-questions.md`.

**Cómo se prueban.** Todo el módulo es guardia de AUTONOMIA-04: vive en `domain/` y `application/` como
código puro salvo el transporte, y exige **100 % de ramas** (team.md). Salvo que la regla diga otra cosa,
cada una se prueba en **nivel 0**, sin red, con el `FakeTransport` y un doble del puerto en lugar del
ModelGateway y del analizador (C20), con datos sintéticos y un control negativo.

```yaml
rules:
  # BR1 — Seudonimización
  - id: BR1.1
    status: cambia
    statement: Antes de cualquier llamada externa, el módulo reemplaza cada entidad detectada por su marca, con una marca por forma exacta, coherente en toda la llamada y numerada por primera aparición.
    category: policy
    applies_to: [MaskingRequest, MaskTable, Marker]
    trigger: Cada generate con destino externo, en el paso 2 de C20
    logic: SI un tramo es un DetectedSpan fusionado (BR1.2) ENTONCES se reemplaza por [CATEGORIA_n]; la misma forma exacta recibe la misma marca en todos los mensajes y turnos de la llamada, y además se reemplaza toda otra aparición de esa forma con límites de palabra, aunque ningún detector la marcara allí; n se asigna por orden de primera aparición recorriendo los mensajes en orden y cada uno de izquierda a derecha (P5 = A). SI el contenido de un mensaje es JSON ENTONCES se seudonimizan sus valores de cadena ya decodificados y se vuelve a serializar sin escapar caracteres no ASCII; las claves y los números no se tocan. El esquema de salida (request.schema) no es un mensaje y sale tal cual.
    violation: Prueba del payload saliente sobre el conjunto sintético con entidades sembradas con y sin tilde, también escritas con secuencias de escape Unicode del JSON (barra invertida, u y cuatro dígitos hexadecimales) en la entrada; una sola fuga en un cuerpo capturado por el FakeTransport hace fallar la prueba (AC11.3.1, AC11.3.7 del lado de U10).
    source: FR11.3; AC11.3.1; AC11.3.2; AC11.3.7; C20 paso 2; respuestas P1 = A, P4 = A y P5 = A
  - id: BR1.2
    status: cambia
    statement: La detección es la unión del NER local y de las reglas en español, y ante la duda se seudonimiza.
    category: calculation
    applies_to: [DetectionRuleSet, NerModel, DetectedSpan]
    trigger: Detección en el paso 2 de C20
    logic: SI el NER (con confianza en o por encima de su umbral) o un patrón de DetectionRuleSet marca un tramo ENTONCES es un DetectedSpan. SI dos tramos se solapan o se tocan ENTONCES se fusionan en su unión con la categoría de menor precedencia (EXPEDIENTE, IDENTIFICADOR, PERSONA, LUGAR, ENTIDAD), nunca se recortan. Un tratamiento («doña», «sargento») queda visible y solo se seudonimiza el nombre que lo sigue. Las etiquetas de organización del NER se ignoran. Sale la lista de nombres propios del escenario (cambio 01).
    violation: Prueba con casos ambiguos («San José» como persona y como lugar), solapes NER/regla y un nombre que solo detecta uno de los dos.
    source: FR11.3; DT18; components (Anonymizer); respuesta P2 = A (parte de reglas en español); P3 = A
  - id: BR1.3
    status: cambia
    statement: La respuesta se restaura dentro del proceso con la tabla de la misma llamada, solo sobre los valores de cadena del JSON ya parseado y a la forma original exacta.
    category: policy
    applies_to: [MaskTable, RestorationOutcome]
    trigger: Respuesta del proveedor ya parseada y validada (paso 4 de C20)
    logic: SI un valor de cadena contiene una marca canónica que está en la tabla ENTONCES se reemplaza por su forma original exacta (con tildes y mayúsculas), para que U11 verifique la cita contra el turno original sin casos especiales (FR4.4). Nunca se restaura sobre el texto crudo antes de parsear, ni en claves ni en números. Las formas de marca que no están en la tabla siguen BR4.1.
    violation: Prueba con una cita seudonimizada válida que se restaura byte a byte igual al turno original (AC11.3.4 caso a).
    source: FR11.3; FR4.4; AC11.3.4; C20 paso 4; respuesta P1 = A
  - id: BR1.4
    status: Retirado
    statement: "Retirado (cambio 01): sale la operación embed de C13 y con ella los embeddings externos."
    category: constraint
    applies_to: [MaskingRequest]
    trigger: Ninguno
    logic: Sin efecto. No se entrega.
    violation: No aplica.
    source: C13 revisión 2 (sale embed)
  - id: BR1.5
    status: nuevo
    statement: Se seudonimizan cuatro categorías y una red de seguridad; las organizaciones, las fechas y las cifras no se seudonimizan.
    category: policy
    applies_to: [MaskCategory, AllowedWordList, DetectedSpan]
    trigger: Detección en el paso 2 de C20, en mensajes user y assistant
    logic: SE seudonimizan PERSONA (con apodos y alias), LUGAR, EXPEDIENTE e IDENTIFICADOR (cédula, teléfono, correo, placa, cuenta). Red de seguridad SI una palabra con mayúscula inicial no abre oración (inicio de un valor de texto, o tras «.», «?», «!», «¿», «¡», «:» o salto de línea), ningún detector la clasificó y no está en AllowedWordList ENTONCES se seudonimiza como [ENTIDAD_n]. Las fechas y las cifras quedan visibles salvo que formen un EXPEDIENTE o un IDENTIFICADOR, porque son hechos centrales que el juez compara. La red de seguridad no se aplica a los mensajes system, que son configuración versionada sin testimonio (FR4.6); el NER y las reglas sí.
    violation: Prueba con un nombre suelto y un apodo que no detecta ninguna regla (hallazgo R-02 de la revisión 1); prueba de que «Fiscalía» y los meses quedan visibles; prueba de que ninguna entidad sembrada del conjunto sintético está en AllowedWordList.
    source: FR11.3; AUTONOMIA-04 («identificadores reales del proceso»); respuesta P3 = A (ver precisión FD-U10-02)
  - id: BR1.6
    status: nuevo
    statement: El módulo solo atiende destinos externos de un proveedor comercial; un destino local se rechaza sin hacer nada.
    category: validation
    applies_to: [MaskingRequest, OutboundDestination]
    trigger: Paso 1 de C20
    logic: SI request.destination.scope no es external, o su proveedor es local o no es anthropic, google ni openai ENTONCES lanza AnonymizerUnavailable antes de seudonimizar, y el transporte no recibe nada. Con un perfil todo local el ModelGateway nunca llama al módulo (U11).
    violation: Prueba con un destino local y con un proveedor desconocido; el FakeTransport registra 0 peticiones (AC11.3.6 del lado de U10).
    source: C20 paso 1; AC11.3.6; FR11.3 («con un perfil todo local no interviene»)
  - id: BR1.7
    status: nuevo
    statement: Un texto de entrada que ya trae algo con forma de marca se trata como un valor más de la tabla y vuelve intacto.
    category: constraint
    applies_to: [MaskTable, Marker, DetectedSpan]
    trigger: Detección en el paso 2 de C20
    logic: SI un valor de texto de entrada contiene una cadena con forma de marca (Marker) ENTONCES es un DetectedSpan con source input_marker y categoría ENTIDAD, recibe su propia marca nueva y se restaura a su forma exacta; así una marca literal del testimonio nunca choca con una de la tabla ni se toma por alterada.
    violation: Prueba con un testimonio sintético que contiene «[PERSONA_1]» y «Ana Pérez»; la respuesta restaurada devuelve las dos formas originales.
    source: Hallazgo R-05 de la revisión 1; C20 paso 4 (ver precisión FD-U10-07)
  - id: BR1.8
    status: nuevo
    statement: La tabla de correspondencia vive solo en memoria del módulo durante la llamada y nunca se registra, se guarda ni aparece en un error.
    category: constraint
    applies_to: [MaskTable, MaskingRequest]
    trigger: Toda la vida de la llamada
    logic: SI la llamada termina, con éxito o con cualquier error ENTONCES la tabla se vacía y se suelta; no tiene representación textual, no se serializa, no se pasa a ningún log, mensaje de excepción ni GenerateResult, y no se escribe en disco. Los mensajes de error nombran el paso que falló, nunca un valor.
    violation: Prueba con un canary sembrado como nombre que recorre el éxito y cada rama de error y comprueba que no aparece en ningún log capturado, en ningún archivo escrito ni en el texto de ninguna excepción (AC11.3.5 del lado de U10, nivel 0; AC11.6.3 en nivel 1).
    source: FR11.3; NFR10; AC11.3.5; AC11.6.3; C20

  # BR2 — Fallo cerrado y registro
  - id: BR2.1
    status: cambia
    statement: Si cualquier paso anterior al envío falla, no sale ninguna llamada y el módulo lanza AnonymizerUnavailable.
    category: constraint
    applies_to: [MaskingRequest]
    trigger: Pasos 1 y 2 de C20 y la preparación del cuerpo nativo
    logic: SI falla la validación del destino o del dominio, el NER, una regla, la construcción de la tabla, la serialización, la clave referenciada no existe, el adaptador no puede construir el cuerpo, se lanza cualquier excepción inesperada, o la seudonimización consumió su presupuesto del plazo (fracción de timeout_s, cifra de NFR Requirements) ENTONCES lanza AnonymizerUnavailable sin ModelCall y el transporte no recibe nada. El núcleo (U11) termina el tramo con codigo anonimizador_no_disponible (CD-01, CD-02). Sale turn.error.system de la revisión 1.
    violation: Una prueba por rama de fallo, cada una con el FakeTransport en 0 peticiones (AC11.3.3 del lado de U10, con el módulo caído, con excepción y sin responder a tiempo).
    source: FR11.3; AC11.3.3; C20 («si cualquier paso antes del 3 falla»); CD-01; CD-02
  - id: BR2.2
    status: cambia
    statement: El proxy no arranca, y el módulo no se construye, sin todo lo que necesita para seudonimizar y llamar.
    category: validation
    applies_to: [ProxyProfileCopy, NerModel, DetectionRuleSet, AllowedWordList, ProviderDomainList, ProviderCapabilityTable]
    trigger: Arranque de anonymizer-proxy; construcción del módulo en la raíz de composición de la CLI
    logic: SI el NER falta o su sha256 no coincide, alguna lista o tabla del módulo es inválida, o (solo en el proxy) el archivo de perfiles no pasa profiles.validate(kind base, key_prefix VERIDICUS_) de U1, o falta en el entorno alguna api_key_ref de un destino externo de la copia, o un modelo externo de la copia no está en ProviderCapabilityTable ENTONCES el proxy termina con código distinto de 0 y /readyz no pasa, y en la CLI la construcción lanza el error de configuración antes de cualquier llamada. El log nombra el ajuste, nunca su valor.
    violation: Una prueba por caso con control positivo (el mismo archivo corregido arranca y pasa /readyz), y un canary como valor de clave que no aparece en el log (AC13.3.1 caso c y su variante a en el proxy, AC13.3.2 del lado del módulo).
    source: FR14.3; NFR10; AC13.3.1; AC13.3.2; C16; C21; U1 F8 (función profiles.validate)
  - id: BR2.3
    status: cambia
    statement: Los logs del módulo y del proxy llevan solo identificadores y cifras, nunca texto.
    category: constraint
    applies_to: [MaskingRequest, MaskTable]
    trigger: Cualquier línea de log del módulo o del proxy
    logic: SI se registra algo ENTONCES solo run_id, perfil, papel, ranura, proveedor, modelo, código de resultado o de error, número de reemplazos por categoría, tokens y duración; nunca mensajes, respuesta, formas originales, marcas con su valor, la tabla ni el valor de una clave.
    violation: Prueba de nivel 0 con canary en el testimonio y en una clave; en nivel 1, el canary no aparece en los logs de anonymizer-proxy (lado de U10 de AC9.1.4 y AC11.6.3).
    source: NFR10; AC9.1.4; AC11.3.5; AC11.6.3; C21 (ver precisión FD-U10-14)
  - id: BR2.4
    status: nuevo
    statement: Cada generate produce como mucho una llamada externa; ni el módulo ni el proxy reintentan hacia el proveedor.
    category: constraint
    applies_to: [MaskingRequest, NativeProviderAdapter]
    trigger: Paso 3 de C20
    logic: SI el envío falla por cualquier causa ENTONCES se traduce al error tipado (BR5.3) sin repetir; el proveedor alterno es una llamada nueva que decide el núcleo (FR15.2), no el módulo.
    violation: Prueba con el FakeTransport devolviendo 503 y luego 200; registra exactamente 1 petición.
    source: C13 (tabla de reintentos y «cada petición produce como mucho una llamada externa»); C21; C20 paso 3
  - id: BR2.5
    status: nuevo
    statement: Toda llamada que sale por el módulo se registra con anonymized verdadero, y el módulo no puede producir un registro con anonymized falso.
    category: constraint
    applies_to: [MaskingRequest, NativeProviderAdapter]
    trigger: Después del paso 3 de C20
    logic: SI el adaptador nativo envió el cuerpo ENTONCES el ModelCall lleva role, provider, model, version si el proveedor la informa, effort_or_quantization, engine nulo, seed solo si el proveedor la admite, input_tokens y output_tokens del proveedor (0 si no los informa), fallback_provider verdadero cuando destination_slot es fallback, anonymized verdadero y at con la hora del envío en UTC. El adaptador nativo no es alcanzable sin pasar por el paso 2. Detectar un registro con anonymized falso y bloquear la sesión es de U11 y U4 (ADR-013).
    violation: Prueba de que el ModelCall cumple model-call.v1.yaml de U1 y lleva anonymized verdadero; prueba de import-linter de que nada fuera del módulo importa los adaptadores para enviar (BR5.1).
    source: C20 paso 5; FR15.3; VE-14; ADR-013; AC11.3.8 (lado de U10)
  - id: BR2.6
    status: nuevo
    statement: Todo error lanzado después de enviar lleva el ModelCall de la llamada, para que la llamada fallida cuente en el registro y en el costo.
    category: policy
    applies_to: [MaskingRequest, NativeProviderAdapter]
    trigger: ContentBlocked, Timeout, ProviderError o InvalidOutput después del paso 3
    logic: SI la llamada ya salió y termina en error ENTONCES el error tipado lleva el ModelCall con los tokens que informe el proveedor (0 si no los informa), y el proxy lo incluye en el cuerpo de error (BR6.3). AnonymizerUnavailable nunca lleva ModelCall, porque no salió nada.
    violation: Una prueba por error tipado después del envío que comprueba el ModelCall adjunto, y otra de que AnonymizerUnavailable no lo lleva.
    source: FR15.3; FR15.4; respuesta P7 = A (ver precisión FD-U10-04)

  # BR3 — Red y destinos
  - id: BR3.1
    status: cambia
    statement: El módulo solo abre conexiones hacia los dominios de la lista, por HTTPS y el puerto 443; cualquier otro destino se rechaza sin abrir conexión.
    category: constraint
    applies_to: [OutboundDestination, ProviderDomainList, NativeProviderAdapter]
    trigger: Paso 1 de C20 y cada envío del adaptador nativo
    logic: SI el dominio del proveedor del destino no está en ProviderDomainList, o el envío apunta a otro esquema, host o puerto ENTONCES lanza AnonymizerUnavailable y el transporte no recibe nada. Complementa la NetworkPolicy y la lista blanca de CoreDNS, que son de U2 (FR12.3, US11.6); antes esta regla era la política de manifiestos.
    violation: Prueba con un dominio fuera de la lista y con un puerto distinto de 443; el FakeTransport registra 0 peticiones (AC11.5.1).
    source: FR11.4; AC11.5.1; C22 (reglas); AUTONOMIA-04
  - id: BR3.2
    status: Retirado
    statement: "Retirado: que un servicio o la CLI no arranque con un destino externo sin anonimizador pasa a U11 (ModelGateway y ExecutionProfiles, FR14.3, US13.3)."
    category: constraint
    applies_to: [OutboundDestination]
    trigger: Ninguno en U10
    logic: Sin efecto en U10.
    violation: No aplica.
    source: unit-of-work revisión 3 (U11, Restricciones); C13 (Arranque)
  - id: BR3.3
    status: Retirado
    statement: "Retirado: la verificación manual en el clúster de que solo anonymizer-proxy sale pasa a U2 (US9.1, AC9.1.2)."
    category: policy
    applies_to: [OutboundDestination]
    trigger: Ninguno en U10
    logic: Sin efecto en U10.
    violation: No aplica.
    source: unit-of-work revisión 3 (U10, Límites; U2)
  - id: BR3.4
    status: Retirado
    statement: "Retirado: la tabla de fronteras de Infrastructure Design pasa a U2 (AC9.1.3)."
    category: policy
    applies_to: [OutboundDestination]
    trigger: Ninguno en U10
    logic: Sin efecto en U10.
    violation: No aplica.
    source: unit-of-work revisión 3 (U2)
  - id: BR3.5
    status: nuevo
    statement: Ningún adaptador nativo sigue redirecciones ni acepta otra URL base que la de su dominio, y siempre verifica TLS.
    category: constraint
    applies_to: [NativeProviderAdapter, OutboundDestination]
    trigger: Cada envío del adaptador nativo
    logic: SI el proveedor responde con una redirección ENTONCES no se sigue y la llamada termina en ProviderError con su ModelCall (ya salió una petición). La URL base es una constante del adaptador; ni el perfil ni la petición de C21 pueden cambiarla, y no existe ajuste para desactivar la verificación del certificado.
    violation: Prueba con el FakeTransport devolviendo 307 hacia otro host; registra 1 sola petición y ninguna al host de la redirección.
    source: FR11.4; AUTONOMIA-04; C22 (ver precisión FD-U10-05)
  - id: BR3.6
    status: nuevo
    statement: La lista de dominios es un archivo versionado del módulo, y una comprobación estática la compara con la lista blanca de CoreDNS.
    category: validation
    applies_to: [ProviderDomainList]
    trigger: Cada PR (nivel 0)
    logic: SI ProviderDomainList no tiene exactamente los tres dominios de C22, o la función de comparación publicada por el módulo encuentra un dominio en una lista y no en la otra ENTONCES la comprobación falla. U10 la prueba con un Corefile sintético coherente y otro con un dominio de más (control negativo); U2 la ejecuta sobre su Corefile renderizado.
    violation: Comprobación de nivel 0 en rojo (AC11.5.2).
    source: FR11.4; FR12.3; AC11.5.2; C22 (ver precisión FD-U10-06)

  # BR4 — Marcas alteradas
  - id: BR4.1
    status: nuevo
    statement: Toda cadena de la respuesta con una forma de marca que no coincide exactamente con una de la tabla se deja sin restaurar y su ruta va a altered_markers.
    category: validation
    applies_to: [RestorationOutcome, Marker, MaskTable]
    trigger: Paso 4 de C20, sobre todas las cadenas de la respuesta
    logic: SI una cadena contiene una forma de marca (alterada como [Persona_3] o [PERSONA 3], inventada como [PERSONA_9], mal escrita como PERSONA_3]) que no es exactamente una marca de la tabla ENTONCES esa forma queda sin restaurar y el puntero JSON de la cadena entra en altered_markers, esté en una cita, en hecho o en observaciones. Las marcas conocidas de la misma cadena sí se restauran. No hay tolerancia a variantes triviales.
    violation: Pruebas con una marca alterada y una inventada (AC11.3.4 casos b y c) en cita_a, en hecho y en observaciones.
    source: FR11.3; AC11.3.4; C13 (altered_markers); respuesta P6 = A
  - id: BR4.2
    status: nuevo
    statement: El módulo no conoce la forma del hallazgo; solo informa rutas, y el núcleo descarta el hallazgo que las contiene.
    category: policy
    applies_to: [RestorationOutcome]
    trigger: Al devolver el GenerateResult
    logic: SI una cadena entra en altered_markers ENTONCES se informa su puntero JSON (RFC 6901) y nada más; U11 descarta el hallazgo que contiene esa ruta con motivo marca_alterada. Una cita que perdió una marca (AC11.3.4 caso d) no la ve el módulo, porque no tiene forma de marca; la rechaza la verificación de U11 contra el turno original.
    violation: Prueba de que altered_markers solo trae punteros válidos al contenido devuelto, sin repetidos y en orden de recorrido; prueba de que el módulo no importa nada del esquema de C6.
    source: C13; C20 paso 4; respuesta P6 = A (ver precisión FD-U10-08)

  # BR5 — Adaptadores nativos (C22)
  - id: BR5.1
    status: nuevo
    statement: Los adaptadores nativos viven en el subpaquete libs/anonymizer/providers/, separado de la seudonimización, y solo los importa la orquestación del módulo.
    category: constraint
    applies_to: [NativeProviderAdapter]
    trigger: Cada PR (nivel 0, import-linter)
    logic: SI libs.anonymizer.providers importa la seudonimización, la seudonimización importa libs.anonymizer.providers, o algo fuera de libs.anonymizer (salvo sus pruebas) importa libs.anonymizer.providers ENTONCES el contrato de import-linter anonymizer-layers falla. El contrato anonymizer-independent de C20 sigue vigente. La exclusión de semantic-agent (semantic-agent-no-anonymizer, AC11.6.4) la configura U4.
    violation: import-linter en rojo, con un módulo de prueba que viola cada contrato (control negativo).
    source: C20 (subpaquete propio, pregunta abierta); CD-04; AC11.6.4; unit-of-work revisión 3 (R-02) (ver precisión FD-U10-03)
  - id: BR5.2
    status: nuevo
    statement: Cada adaptador fuerza la salida JSON con el modo estructurado nativo del proveedor y el esquema de la petición, y traduce el esfuerzo del perfil al parámetro de razonamiento del proveedor.
    category: policy
    applies_to: [NativeProviderAdapter, ProviderCapabilityTable]
    trigger: Construcción del cuerpo nativo, antes del paso 3
    logic: Google usa generateContent con salida JSON y responseSchema; OpenAI usa la Responses API con json_schema estricto; Anthropic usa la Messages API con su salida estructurada por esquema JSON o, SI el modelo no la admite según ProviderCapabilityTable, una herramienta forzada cuyo esquema de entrada es el de la respuesta. El esfuerzo va al parámetro de razonamiento de cada proveedor. SI el modelo no está en la tabla, o la combinación no la admite el proveedor (Anthropic con herramienta forzada y esfuerzo) ENTONCES no se envía; el proxy no arranca (BR2.2) y en la CLI lanza AnonymizerUnavailable. Una prueba de contrato por adaptador, con respuestas grabadas sintéticas y sin red, comprueba que devuelve la misma estructura validada contra el esquema, y otra que el esquema de C6 es compatible con el modo estructurado de cada proveedor.
    violation: Prueba de contrato en rojo (AC13.6.1).
    source: FR15.1; AC13.6.1; C22 (pregunta abierta); respuesta P8 = A (ver precisión FD-U10-09)
  - id: BR5.3
    status: nuevo
    statement: Cada adaptador traduce la respuesta del proveedor a un GenerateResult o a un error tipado de U1.
    category: validation
    applies_to: [NativeProviderAdapter]
    trigger: Respuesta del proveedor (paso 3 de C20)
    logic: SI la respuesta es 2xx y su salida es JSON estricto (sin claves repetidas ni valores no estándar) que valida contra request.schema ENTONCES sigue a la restauración (BR1.3, BR4.1). SI no es JSON o no valida ENTONCES InvalidOutput. SI el proveedor señala bloqueo o filtro de contenido ENTONCES ContentBlocked. SI se agota el plazo de la llamada ENTONCES Timeout. SI responde con otro error, una redirección o se corta la conexión después de enviar ENTONCES ProviderError. Todos llevan su ModelCall (BR2.6).
    violation: Una prueba por rama con respuestas grabadas sintéticas en el FakeTransport (AC13.6.2).
    source: FR15.2; AC13.6.2; C13 (errores tipados) (ver precisión FD-U10-10)
  - id: BR5.4
    status: nuevo
    statement: La clave de API se lee del entorno por su api_key_ref y solo viaja en la cabecera de autenticación del proveedor.
    category: constraint
    applies_to: [NativeProviderAdapter, OutboundDestination]
    trigger: Construcción del módulo o del proxy y cada envío
    logic: SI se necesita la clave ENTONCES se toma del entorno que recibe el módulo al construirse (en el proxy, el Secret que monta U2; en la CLI, variables de la máquina) por el nombre api_key_ref; nunca entra en un log, un error, el ModelCall, la respuesta del proxy ni el repositorio. Las cabeceras capturadas por el FakeTransport ocultan la clave.
    violation: Prueba con un canary como valor de clave que no aparece en logs, errores, ModelCall ni respuesta.
    source: FR12.4; NFR10; C22 (reglas); CD-04
  - id: BR5.5
    status: nuevo
    statement: El transporte HTTP falso es una utilería de pruebas de libs/anonymizer/testing/ que captura cada cuerpo saliente sin red, y el código de producción no puede seleccionarlo.
    category: constraint
    applies_to: [FakeTransport, NativeProviderAdapter]
    trigger: Pruebas de U10 y prueba compuesta de U11
    logic: SI una prueba inyecta el FakeTransport ENTONCES cada petición queda capturada con su cuerpo y ninguna abre red; las pruebas del payload comprueban que ningún cuerpo contiene una entidad sembrada y que todos llevan marcas [PERSONA_n]. El fixture de control negativo que puentea el paso 2 vive en libs/anonymizer/testing/ y no es alcanzable desde producción. SI un módulo fuera de las pruebas importa libs.anonymizer.testing ENTONCES el contrato de import-linter falla.
    violation: Prueba del payload en rojo con el paso de seudonimización puenteado (control negativo de AC11.3.7); import-linter en rojo.
    source: C20 (transporte fake, R-15); AC11.3.3; AC11.3.7

  # BR6 — anonymizer-proxy (C21)
  - id: BR6.1
    status: nuevo
    statement: El proxy valida cada petición contra C21 antes de tocar su contenido.
    category: validation
    applies_to: [MaskingRequest]
    trigger: Cada POST /v1/generate
    logic: SI el cuerpo no cumple el esquema de C21 (additionalProperties false; un campo destination o api_key_ref da 422), su schema_version tiene un mayor desconocido, o supera el tamaño máximo del catálogo de límites (C25) ENTONCES responde 422 anonymizer.destination_rejected y no sale ninguna llamada.
    violation: Pruebas negativas de C21 con el doble del adaptador nativo en 0 peticiones.
    source: C21 (pruebas negativas); NFR10; C25 (ver precisión FD-U10-13)
  - id: BR6.2
    status: nuevo
    statement: El proxy resuelve proveedor, modelo y clave en su propia copia de los perfiles y no confía en el destino de quien llama.
    category: authorization
    applies_to: [ProxyProfileCopy, OutboundDestination]
    trigger: Cada petición válida
    logic: SI profile_sha256 no es el de la entrada en ProxyProfileCopy ENTONCES 409 anonymizer.profile_mismatch. SI el perfil o el papel (o su alias) no existe, el papel es local, o la ranura es fallback y el perfil no tiene fallback_provider o este es local ENTONCES 422 anonymizer.destination_rejected. SI la ranura es fallback y el alterno es externo ENTONCES el destino es el alterno y no el del papel. En todos los rechazos no sale ninguna llamada.
    violation: Las seis pruebas negativas y la positiva de fallback de C21, con el doble del adaptador nativo.
    source: C21; FR15.2; respuesta P7 = A de Contract Design (proveedor alterno único)
  - id: BR6.3
    status: nuevo
    statement: Cada resultado del módulo tiene una sola respuesta HTTP del proxy, y las de después del envío llevan el registro de la llamada.
    category: policy
    applies_to: [MaskingRequest, RestorationOutcome]
    trigger: Fin de cada petición
    logic: GenerateResult → 200 con content, altered_markers y call; AnonymizerUnavailable → 503 analysis.anonymizer_unavailable; ContentBlocked → 451 analysis.content_blocked; ProviderError → 502 analysis.provider; InvalidOutput → 502 analysis.invalid_output; Timeout después de enviar → 504 analysis.timeout. Los cuerpos de 451, 502 y 504 incluyen call (BR2.6). SI el plazo se agota antes de enviar ENTONCES es AnonymizerUnavailable (503), nunca 504.
    violation: Una prueba por fila, con el cuerpo validado contra C21 y model-call.v1.yaml.
    source: C21 (respuestas); C13 (tabla de reintentos); respuesta P7 = A (ver precisión FD-U10-04)
  - id: BR6.4
    status: nuevo
    statement: El proxy solo está listo cuando todo lo de BR2.2 está cargado, y su sonda nunca llama a un proveedor.
    category: validation
    applies_to: [ProxyProfileCopy, NerModel, ProviderDomainList]
    trigger: GET /readyz y /healthz (C16)
    logic: /healthz responde 200 mientras el proceso vive. /readyz responde 200 solo si los perfiles, las claves, el NER, las listas y la tabla de capacidades se cargaron y validaron; si no, 503 con los checks que fallan, sin datos sensibles. Ninguna sonda abre conexión fuera del clúster.
    violation: Prueba de cada check en rojo; el FakeTransport registra 0 peticiones durante las sondas.
    source: C16; FR12.5; AC13.3.1 (no pasa la sonda de salud) (ver precisión FD-U10-11)
  - id: BR6.5
    status: nuevo
    statement: Cada petición del proxy tiene su propia tabla y su propio estado; el proxy no comparte nada entre peticiones ni entre réplicas.
    category: constraint
    applies_to: [MaskTable, MaskingRequest]
    trigger: Peticiones concurrentes
    logic: SI llegan dos peticiones a la vez ENTONCES cada una construye y suelta su MaskTable; ninguna ve las marcas de la otra. Como la tabla vive solo durante la llamada (P5 = A), el proxy puede tener varias réplicas sin estado compartido.
    violation: Prueba concurrente con dos transcripciones sintéticas distintas; cada respuesta se restaura solo con sus propias formas.
    source: C20 («la tabla vive solo durante la llamada»); respuesta P5 = A
```

## Resumen

| Grupo | Reglas | Estado | Qué protege |
|---|---|---|---|
| BR1 Seudonimización | BR1.1–BR1.3, BR1.5–BR1.8 | BR1.1–BR1.3 cambian; BR1.5–BR1.8 nuevas | Que un nombre, lugar, expediente o identificador real salga del clúster; que la tabla quede en algún lado |
| | BR1.4 | Retirado | (`embed` sale de C13) |
| BR2 Fallo cerrado y registro | BR2.1–BR2.6 | BR2.1–BR2.3 cambian; BR2.4–BR2.6 nuevas | Que un error deje pasar el cuerpo original, que se reintente hacia fuera o que una llamada fallida no se registre |
| BR3 Red y destinos | BR3.1, BR3.5, BR3.6 | BR3.1 cambia; BR3.5–BR3.6 nuevas | Otra salida que no sea un dominio de la lista |
| | BR3.2–BR3.4 | Retirado | (pasan a U11 y U2) |
| BR4 Marcas alteradas | BR4.1–BR4.2 | nuevas | Un hallazgo cuya marca alteró o inventó el modelo |
| BR5 Adaptadores nativos | BR5.1–BR5.5 | nuevas | Claves y adaptadores fuera de su subpaquete, salida JSON sin forzar, transporte *fake* en producción |
| BR6 `anonymizer-proxy` | BR6.1–BR6.5 | nuevas | Que quien llama elija proveedor o clave, respuestas ambiguas, sondas que salen del clúster |

Son 32 ID: 28 vigentes y 4 retirados.
