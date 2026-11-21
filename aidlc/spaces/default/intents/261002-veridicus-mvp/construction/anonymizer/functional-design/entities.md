# Entidades — U10 anonymizer

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-02. U10 deja de ser un adaptador COULD de
ModelGateway y pasa a ser el módulo MUST `Anonymizer` de `libs/anonymizer/` (C20), que la CLI usa en el
mismo proceso, más el proceso `anonymizer-proxy` que lo expone en el clúster (C21), con los adaptadores
nativos de Anthropic, Google y OpenAI y sus claves (C22, CD-04). Las entidades conservan su nombre; lo que
sale de cada una queda marcado `status: Retirado` sin borrarlo (regla de `project.md`), y las nuevas van
al final del bloque.
- **Siguen**, con cambios: MaskingRequest (ahora una llamada `generate`), MaskTable (una marca por forma
  exacta, P4 = A; numeración determinista por llamada, P5 = A), MaskCategory (cinco categorías, P3 = A),
  DetectionRuleSet (NER más reglas, sin la lista del escenario) y OutboundDestination (destino externo ya
  resuelto de un proveedor de la lista).
- **Salen**: el atributo `operation` con el valor `embed` (sale `embed` de C13), `scenario_version_id` y
  `scenario_proper_nouns` (el cambio 01 retira los escenarios), y `url` como destino libre (lo sustituye
  la lista de dominios, FR11.4).
- **Entran**: Marker, DetectedSpan, NerModel, AllowedWordList, ProviderDomainList, NativeProviderAdapter,
  ProviderCapabilityTable, RestorationOutcome, ProxyProfileCopy y FakeTransport. Origen de cada una en su
  descripción.

**Insumos.**
- Unidad U10 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) y su mapa
  `unit-of-work-story-map.md` (unit-of-work-story-map): US11.3 y US11.5 propias; US13.3, US13.6, US9.1 y
  US11.6 la cruzan.
- FR11.3, FR11.4, FR12.3, FR12.4, FR14.3, FR15.1–FR15.3, NFR1 y NFR10 de
  `inception/requirements-analysis/requirements.md` (requirements, revisión 3), y VE-14 de
  `requirements-adenda-02.md`.
- Componente Anonymizer de `inception/domain-design/components.md` (components, revisión 3) y ADR-011 y
  ADR-013 de `decisions.md`.
- C13, C16, C18, C20, C21, C22 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3), con CD-01, CD-02, CD-04 y CD-09.
- Lo que U10 importa de U1 (`construction/contracts/functional-design/`, revisión 3): `model_calls` con
  el `Protocol` `AnonymizingProvider` (la regla de U1 sobre ese `Protocol`), `profile-base`, `profiles.validate(kind: base,
  key_prefix="VERIDICUS_")`, `registry` y `model-call.v1.yaml`. Los nombres de módulo siguen las
  precisiones FD-U1-01 a FD-U1-04 de U1 (`veridicus_contracts.model_calls`; si no se aprueban, valen los de
  C13: `contracts.python.model_calls`).
- Respuestas P1–P2 (revisión 1) y P3–P8 = A (segunda pasada) de `functional-design-questions.md`.

**Qué modela este documento.** Ninguna entidad de U10 se persiste: todo vive en memoria del proceso que
seudonimiza (`anonymizer-proxy` o la CLI) y la tabla de correspondencia muere con la llamada. Los tipos de
la llamada (`GenerateRequest`, `GenerateResult`, `ModelCall`, `Destination` y los errores tipados) son de
U1 y aquí solo se nombran; el bloque YAML es la fuente de verdad de lo que U10 añade.

**Frontera AUTONOMIA-04.**

| Componente | Dónde corre | Datos sin seudonimizar que maneja | Qué cruza la frontera del clúster |
|---|---|---|---|
| Módulo `Anonymizer` (`libs/anonymizer/`) | En el pod `anonymizer-proxy` o en el proceso de la CLI | Mensajes con testimonio y la tabla de correspondencia, solo en memoria | Nada por sí mismo; entrega el cuerpo ya seudonimizado al adaptador nativo |
| Adaptadores nativos (`libs/anonymizer/providers/`) | Igual que el módulo | Ninguno: reciben solo el cuerpo seudonimizado y la clave | **Sí**: el cuerpo seudonimizado y el esquema de salida, por HTTPS 443, solo a los tres dominios de la lista (C22) |
| `anonymizer-proxy` (`services/anonymizer-proxy/`) | Dentro del clúster, único pod con salida | Lo que recibe de `semantic-agent` por C21 y la respuesta restaurada | Lo mismo que los adaptadores; la `NetworkPolicy` y el `Secret` son de U2 |
| Transporte *fake* (`libs/anonymizer/testing/`) | Solo en pruebas, sin red | Datos sintéticos | Nada |

```yaml
entities:
  - name: MaskingRequest
    status: cambia
    description: >
      Una llamada generate del AnonymizingProvider (C20) hacia un destino externo, desde que entra al
      módulo hasta que devuelve un GenerateResult o lanza un error tipado. En el proxy, nace de una
      petición de C21 ya resuelta contra ProxyProfileCopy. Antes era una llamada judge o embed.
    attributes:
      - { name: request, type: reference, references: "GenerateRequest (U1, model_calls)", required: true, description: "papel, ranura, perfil, huella, destino, mensajes, esquema, semilla y timeout_s" }
      - { name: run_id, type: uuid, required: false, description: "solo en el proxy (C21); solo para logs con IDs" }
      - { name: destination, type: reference, references: OutboundDestination, required: true }
      - { name: inbound_messages, type: list, required: true, description: "mensajes originales; nunca se registran, se guardan ni aparecen en un error" }
      - { name: outbound_messages, type: list, required: true, description: "mensajes seudonimizados; con el esquema de salida, lo único que sale del clúster" }
      - { name: deadline, type: datetime, required: true, description: "inicio + request.timeout_s; acota la seudonimización y la llamada (BR2.1, BR6.3)" }
      - { name: operation, type: enum, status: Retirado, allowed: [judge, embed], description: "Retirado: C13 tiene una sola operación generate y sale embed (cambio 01)" }
      - { name: scenario_version_id, type: uuid, status: Retirado, description: "Retirado: el cambio 01 retira los escenarios" }
    constraints:
      - "Produce como mucho una llamada externa (BR2.4)."
      - "request.destination.scope es external y su proveedor es anthropic, google u openai; un destino local nunca se acepta (BR1.6)."
    relationships:
      - { to: MaskTable, cardinality: "1..1", direction: "MaskingRequest -> MaskTable" }
      - { to: OutboundDestination, cardinality: "1..1", direction: "MaskingRequest -> OutboundDestination" }
      - { to: RestorationOutcome, cardinality: "0..1", direction: "MaskingRequest -> RestorationOutcome" }

  - name: MaskTable
    status: cambia
    description: >
      Tabla de correspondencia forma exacta → marca de una sola llamada (P1 = A, P4 = A, P5 = A). Vive solo
      en memoria del módulo durante la llamada; nunca se registra, se guarda, se serializa ni sale del
      proceso.
    attributes:
      - { name: entries, type: list, required: true, description: "pares (forma original exacta, Marker); antes guardaba el valor normalizado sin tildes ni mayúsculas (hallazgo R-05 de la revisión 1)" }
      - { name: counters, type: map, required: true, description: "un contador por MaskCategory, desde 1" }
    constraints:
      - "La clave es la forma exacta del texto, carácter por carácter: «José» y «Jose», o «Ana Pérez» y «Ana», reciben marcas distintas (P4 = A)."
      - "La numeración es determinista: por orden de primera aparición recorriendo los mensajes en su orden y cada mensaje de izquierda a derecha (P5 = A). La misma entrada da siempre la misma tabla."
      - "Biyectiva: una forma tiene una sola marca y una marca una sola forma."
      - "Se vacía y se suelta al terminar la llamada, con éxito o con error (BR1.8). No tiene representación textual que muestre su contenido."
    relationships:
      - { to: Marker, cardinality: "0..*", direction: "MaskTable -> Marker" }

  - name: MaskCategory
    status: cambia
    description: Categoría de lo que se seudonimiza (P3 = A). Antes eran tres.
    attributes:
      - { name: value, type: enum, required: true, allowed: [PERSONA, LUGAR, EXPEDIENTE, IDENTIFICADOR, ENTIDAD] }
      - { name: precedence, type: integer, required: true, description: "orden para resolver solapes: EXPEDIENTE 1, IDENTIFICADOR 2, PERSONA 3, LUGAR 4, ENTIDAD 5" }
    constraints:
      - "PERSONA incluye apodos y alias; IDENTIFICADOR cubre cédula, teléfono, correo, placa y cuenta; ENTIDAD es la red de seguridad (BR1.5)."
      - "No hay categoría para organizaciones e instituciones, fechas ni cifras: no se seudonimizan (P3 = A)."

  - name: DetectionRuleSet
    status: cambia
    description: >
      Reglas de detección versionadas del módulo, en español (P2 = A), que se aplican junto con NerModel
      (unión, BR1.2). Archivo de datos del módulo; solo cambia por PR.
    attributes:
      - { name: schema_version, type: semver, required: true }
      - { name: person_patterns, type: list, required: true, description: "tratamientos («señor», «doña», «don», «sargento»…) seguidos de palabras con mayúscula inicial; secuencias de 2 o más palabras con mayúscula inicial; «alias»/«apodo»/«le dicen» seguidos de una palabra" }
      - { name: place_patterns, type: list, required: true, description: "prefijos de lugar («vereda», «corregimiento», «municipio de», «barrio», «finca»…) seguidos de palabras con mayúscula inicial" }
      - { name: case_number_patterns, type: list, required: true, description: "formatos de radicado y expediente (secuencias de dígitos con guiones o barras de 6 o más caracteres)" }
      - { name: identifier_patterns, type: list, required: true, description: "cédula, teléfono, correo, placa y número de cuenta" }
      - { name: scenario_proper_nouns, type: list, status: Retirado, description: "Retirado: el cambio 01 retira los escenarios" }
    constraints:
      - "Ante una coincidencia ambigua se seudonimiza; nunca queda sin seudonimizar un tramo que alguna regla o el NER marcó (BR1.2)."
      - "El tratamiento («doña», «sargento») queda visible y solo se seudonimiza el nombre que lo sigue."
      - "Cada patrón tiene al menos un ejemplo positivo y uno negativo en la suite (100 % de ramas)."

  - name: OutboundDestination
    status: cambia
    description: >
      Destino externo ya resuelto de una llamada: el Destination de U1 con scope external. En la CLI llega
      dentro del GenerateRequest; en el proxy lo resuelve ProxyProfileCopy y nunca viene de quien llama
      (C21). Antes era una URL libre configurada en el proxy.
    attributes:
      - { name: provider, type: enum, required: true, allowed: [anthropic, google, openai] }
      - { name: model, type: text, required: true }
      - { name: version, type: text, required: false }
      - { name: family, type: text, required: false }
      - { name: parameters, type: map, required: true, description: "effort, temperature y seed del perfil" }
      - { name: api_key_ref, type: secret_ref, required: true, constraints: "empieza por VERIDICUS_ (prefijo de la validación de perfiles de U1); es el nombre de la variable, nunca el valor" }
      - { name: domain, type: hostname, required: true, constraints: "el dominio fijo del proveedor en ProviderDomainList; no lo elige el perfil ni la petición (BR3.5)" }
      - { name: url, type: url, status: Retirado, description: "Retirado: la lista de dominios sustituye al destino libre (FR11.4)" }
      - { name: credential_ref, type: secret_ref, status: Retirado, description: "Retirado: lo sustituye api_key_ref de C13" }
    relationships:
      - { to: ProviderDomainList, cardinality: "1..1", direction: "OutboundDestination -> ProviderDomainList" }
      - { to: NativeProviderAdapter, cardinality: "1..1", direction: "OutboundDestination -> NativeProviderAdapter" }

  - name: Marker
    status: nuevo
    description: >
      Valor de una marca seudonimizada. Forma canónica [CATEGORIA_n], con n entero desde 1 sin ceros a la
      izquierda (P1 = A). Origen: FR11.3, C20.
    attributes:
      - { name: category, type: reference, references: MaskCategory, required: true }
      - { name: number, type: integer, required: true, min: 1 }
      - { name: text, type: text, required: true, description: "p. ej. [PERSONA_3]" }
    constraints:
      - "Una cadena con «forma de marca» es la canónica o cualquier variante que una la palabra de una categoría (sin importar mayúsculas) con un número mediante guion bajo, o que la encierre entre corchetes con cualquier separador: [Persona_3], [PERSONA 3], PERSONA_3], [persona-3]. Se usa para detectar marcas alteradas (BR4.1) y para tratar la entrada que ya trae algo con forma de marca (BR1.7)."

  - name: DetectedSpan
    status: nuevo
    description: Tramo de un valor de texto que un detector marcó, antes de fusionar solapes (origen P2 = A y P3 = A).
    attributes:
      - { name: start, type: integer, required: true, min: 0 }
      - { name: end, type: integer, required: true }
      - { name: category, type: reference, references: MaskCategory, required: true }
      - { name: source, type: enum, required: true, allowed: [ner, rule, safety_net, input_marker, exact_form] }
    constraints:
      - "start < end, dentro del valor de texto."
      - "Los tramos que se solapan se fusionan en su unión, con la categoría de menor precedence (BR1.2)."

  - name: NerModel
    status: nuevo
    description: >
      Modelo NER local, artefacto fijado por sha256 en formato sin código ejecutable y sin
      trust_remote_code (team.md, Deployment). Cuál modelo y su umbral de confianza los fijan NFR
      Requirements e Infrastructure Design. Origen: FR11.3, DT18, components (Anonymizer).
    attributes:
      - { name: artifact_sha256, type: hex64, required: true }
      - { name: confidence_threshold, type: decimal, required: true, min: 0, max: 1, description: "cifra de NFR Requirements" }
      - { name: label_mapping, type: map, required: true, description: "etiqueta del modelo → MaskCategory; las de organización se ignoran (P3 = A)" }
    constraints:
      - "Se carga al arrancar el proxy o al construir el módulo en la CLI, nunca por red en ejecución; un sha256 distinto impide arrancar (BR2.2)."

  - name: AllowedWordList
    status: nuevo
    description: >
      Lista versionada de palabras con mayúscula inicial que la red de seguridad no seudonimiza
      («Fiscalía», «Ejército», meses, días, los valores de enum del contrato común como los rótulos de
      hablante). Archivo de datos del módulo; solo cambia por PR. Origen: P3 = A.
    attributes:
      - { name: schema_version, type: semver, required: true }
      - { name: words, type: list, required: true, description: "formas exactas, sensibles a mayúsculas" }
    constraints:
      - "Ninguna entidad sembrada del conjunto sintético puede estar en la lista (prueba de nivel 0, BR1.5)."

  - name: ProviderDomainList
    status: nuevo
    description: >
      Archivo versionado del módulo con los dominios de los proveedores permitidos (C22): exactamente
      api.anthropic.com, generativelanguage.googleapis.com y api.openai.com, cada uno con su proveedor.
      Lo lee también la comprobación de U2 contra la lista blanca de CoreDNS. Origen: FR11.4, US11.5.
    attributes:
      - { name: schema_version, type: semver, required: true }
      - { name: entries, type: list, required: true, description: "pares (provider, domain); puerto siempre 443" }
    constraints:
      - "Un proveedor tiene exactamente un dominio; un dominio no tiene comodines ni puerto propio."

  - name: NativeProviderAdapter
    status: nuevo
    description: >
      Adaptador de un proveedor comercial en el subpaquete libs/anonymizer/providers/ (C20, CD-04; nombre
      en precisión FD-U10-03). Construye el cuerpo nativo con salida estructurada (P8 = A), lo envía una
      vez por el transporte inyectado, interpreta la respuesta y produce el ModelCall.
    attributes:
      - { name: provider, type: enum, required: true, allowed: [anthropic, google, openai] }
      - { name: operation, type: enum, required: true, allowed: [messages, generate_content, responses], description: "Anthropic Messages API, Google generateContent, OpenAI Responses API (P8 = A)" }
      - { name: structured_mode, type: enum, required: true, allowed: [json_schema_native, forced_tool], description: "forced_tool solo para un modelo de Anthropic sin salida estructurada, según ProviderCapabilityTable" }
      - { name: transport, type: reference, references: "transporte HTTP (real o FakeTransport)", required: true, description: "se inyecta; el código de producción no elige el fake por configuración" }
    constraints:
      - "Nunca sigue redirecciones ni acepta otra URL base que la de su dominio (BR3.5)."
      - "La clave solo va en la cabecera de autenticación del proveedor; nunca en un log, un error ni el ModelCall (BR5.4)."
    relationships:
      - { to: ProviderCapabilityTable, cardinality: "1..1", direction: "NativeProviderAdapter -> ProviderCapabilityTable" }

  - name: ProviderCapabilityTable
    status: nuevo
    description: >
      Tabla versionada del subpaquete de adaptadores que dice, por proveedor y modelo, qué modo de salida
      estructurada admite y cómo se traduce el esfuerzo del perfil. Origen: P8 = A (pregunta abierta de C22).
    attributes:
      - { name: schema_version, type: semver, required: true }
      - { name: entries, type: list, required: true, description: "(provider, model) → structured_mode y parámetro de razonamiento" }
    constraints:
      - "Un modelo que no está en la tabla no se llama: el proxy no pasa /readyz y la CLI falla cerrado antes de enviar (BR5.2)."
      - "Con Anthropic en modo forced_tool, el perfil no puede pedir esfuerzo (el razonamiento extendido no admite una herramienta forzada); la combinación se rechaza al arrancar (BR5.2)."

  - name: RestorationOutcome
    status: nuevo
    description: >
      Resultado de restaurar una respuesta: el contenido JSON con las marcas conocidas restauradas y las
      rutas de las cadenas con marcas alteradas. Se copia a GenerateResult.content y altered_markers
      (C13). Origen: FR11.3, AC11.3.4, P6 = A.
    attributes:
      - { name: content, type: document, required: true, description: "JSON ya parseado; solo cambian valores de cadena" }
      - { name: altered_markers, type: list, required: true, description: "punteros JSON (RFC 6901) a cada cadena con al menos una forma de marca que no está en la tabla, p. ej. /hallazgos/0/cita_a/texto; sin repetidos, en orden de recorrido" }
    constraints:
      - "Una cadena listada en altered_markers conserva sin restaurar la forma de marca que la invalidó; las marcas conocidas de esa misma cadena sí se restauran."

  - name: ProxyProfileCopy
    status: nuevo
    description: >
      Copia validada de config/profiles.yaml que U2 monta en anonymizer-proxy desde el mismo commit que la
      de semantic-agent (C21). De ella salen proveedor, modelo y api_key_ref; quien llama no puede
      elegirlos. Origen: C21, CD-09.
    attributes:
      - { name: profiles, type: list, required: true, description: "validados con profiles.validate(kind: base, key_prefix=\"VERIDICUS_\") de U1" }
      - { name: entry_sha256, type: map, required: true, description: "perfil → SHA-256 de la forma canónica JCS (RFC 8785) de su entrada, el mismo cálculo que C18 y el fixture de U1 (precisión FD-U10-12)" }
    constraints:
      - "Cada api_key_ref de un destino externo de la copia existe en el entorno del proceso al arrancar (AC13.3.1 caso c)."
      - "Inmutable mientras el proceso vive; un cambio de perfiles exige reiniciar el pod con el nuevo commit."

  - name: FakeTransport
    status: nuevo
    description: >
      Transporte HTTP falso de los adaptadores nativos, publicado en libs/anonymizer/testing/ y versionado
      con C20 (R-15 de Contract Design). Captura cada cuerpo saliente, devuelve respuestas grabadas
      sintéticas y nunca abre red. U11 lo reutiliza en su prueba compuesta.
    attributes:
      - { name: captured_requests, type: list, required: true, description: "método, dominio, ruta, cabeceras sin la clave y cuerpo de cada petición" }
      - { name: scripted_responses, type: list, required: true, description: "respuestas grabadas o errores simulados (5xx, bloqueo, timeout, cuerpo no JSON)" }
    constraints:
      - "Ningún módulo fuera de las pruebas lo importa (contrato de import-linter, BR5.5)."
```

## Resumen

| Entidad | Estado | Qué es |
|---|---|---|
| MaskingRequest | cambia | Una llamada `generate` hacia un destino externo; solo su cuerpo seudonimizado sale del clúster |
| MaskTable | cambia | Forma exacta → marca, numerada por primera aparición, solo en memoria durante la llamada |
| MaskCategory | cambia | `PERSONA`, `LUGAR`, `EXPEDIENTE`, `IDENTIFICADOR` y la red de seguridad `ENTIDAD` |
| DetectionRuleSet | cambia | Reglas en español que se suman al NER; pierde la lista del escenario |
| OutboundDestination | cambia | Destino externo resuelto, con dominio fijo de la lista y clave por referencia |
| Marker | nuevo | `[CATEGORIA_n]` y la definición de «forma de marca» |
| DetectedSpan | nuevo | Tramo marcado por NER, reglas, red de seguridad, forma exacta o marca de entrada |
| NerModel | nuevo | Modelo local fijado por `sha256`, cargado al arrancar |
| AllowedWordList | nuevo | Palabras con mayúscula que la red de seguridad deja pasar |
| ProviderDomainList | nuevo | Los tres dominios de C22, archivo que también lee U2 |
| NativeProviderAdapter | nuevo | Anthropic, Google y OpenAI con salida estructurada (P8 = A) |
| ProviderCapabilityTable | nuevo | Modo estructurado y esfuerzo por modelo |
| RestorationOutcome | nuevo | Contenido restaurado y punteros JSON de marcas alteradas |
| ProxyProfileCopy | nuevo | Perfiles del proxy y huella de cada entrada |
| FakeTransport | nuevo | Utilería de pruebas sin red que captura los cuerpos salientes |
