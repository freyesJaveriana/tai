# Entidades — U1 contracts

**Revisión 2 (2026-11-09), segunda pasada por el cambio 01 (DT27), la adenda 02 y el cambio 03.**
Sustituye a la revisión 1 del 2026-10-03. Las entidades que siguen conservan su nombre. Las que salen
quedan con `status: Retirado` y nombran a su reemplazo, sin borrarlas (regla de `project.md`). Las nuevas
van al final del bloque.

**Insumos.**
- Unidad U1 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 2) y su mapa
  `unit-of-work-story-map.md` (unit-of-work-story-map).
- Contratos C1–C25 de `inception/contract-design/contract-summary.md` (contract-summary, revisión 2).
- Requisitos de `inception/requirements-analysis/requirements.md` (requirements, revisión 2).
- Componentes IntegrityPolicy, ExecutionProfiles y ModelGateway de `inception/domain-design/components.md`
  (components).
- Contrato común v1.0.0 aprobado en el repositorio principal del TG (`/insumos/app/contratos/analizador/v1/`)
  y cambio 03 (`/insumos/app/cambios/veridicus-03_reutilizacion_en_sistema.md`): V-1 y V-3.
- Respuestas P1–P4 (primera pasada), P5–P8 (segunda pasada), la opción A de V-1 y P9–P11 (hallazgos
  R-01 a R-09 de la revisión asesora), que el autor eligió el 2026-11-09. Todo está en
  `functional-design-questions.md`.

**Qué modela este documento.** U1 no tiene comportamiento en ejecución, salvo tres funciones puras que
publica en el paquete (P9 = A, precisión FD-U1-10): la validación de perfiles, la carga de límites y el
registro que resuelve las referencias entre esquemas. Sus «entidades» son los
documentos de contrato que guarda `contracts/` y los datos que esos documentos describen. El bloque YAML
es la fuente de verdad. La forma campo a campo de cada contrato sigue en `contract-summary.md` (y, para
C6, en la copia aprobada), y aquí solo se repite lo que esta etapa decide o precisa.

```yaml
entities:
  - name: ContractDocument
    status: cambia
    description: >
      Un contrato versionado de contracts/ (C1–C25; C4 y C9 Retirado). Es la unidad de versión, de
      propiedad y de PR.
    attributes:
      - { name: contract_id, type: identifier, required: true, unique: true, constraints: "C1..C25 salvo C4 y C9, o un catálogo propio de U1 (rótulos, fecha, excepciones)" }
      - { name: kind, type: enum, required: true, allowed: [openapi, asyncapi, json_schema, yaml_schema, vocabulary_list, rule_list, notice_text, python_types, python_protocol, metrics, label_catalog, error_catalog, limits_catalog, datetime_format] }
      - { name: origin, type: enum, required: true, allowed: [internal, external_copy], default: internal, description: "external_copy solo para C6 (ADR-017, cambio 03 §1)" }
      - { name: path, type: path, required: true, unique: true, constraints: "bajo contracts/; los Protocol de C13, C17 y C20 que viven en libs/ no son de U1, salvo sus tipos compartidos" }
      - { name: version, type: semver, required: true, constraints: "MAYOR.MENOR.PARCHE" }
      - { name: owner_unit, type: identifier, required: true, description: "Columna Owner de contract-summary" }
      - { name: strict, type: boolean, required: true, default: false, description: "true en C6, C7, C18 (con la configuración efectiva), C19 (con el registro de llamadas) y C21: todo cambio de forma es mayor" }
    constraints:
      - "Cada ContractDocument tiene al menos un Fixture válido y uno inválido, salvo python_types y python_protocol, que se verifican con tipos."
    relationships:
      - { to: Fixture, cardinality: "1..*", direction: "ContractDocument -> Fixture" }
      - { to: ApprovedCopyManifest, cardinality: "0..1", direction: "ContractDocument (origin external_copy) -> ApprovedCopyManifest" }

  - name: Fixture
    status: se mantiene
    description: Ejemplo sintético que el contrato debe aceptar o rechazar.
    attributes:
      - { name: fixture_id, type: identifier, required: true, unique: true }
      - { name: contract_id, type: reference, references: ContractDocument, required: true }
      - { name: expectation, type: enum, required: true, allowed: [accept, reject, scan_case] }
      - { name: reject_reason, type: text, required: false, description: "Obligatorio si expectation es reject; nombra la regla BR que lo rechaza" }
      - { name: executed_by, type: identifier, required: false, description: "Solo con scan_case: U11 (B11). U1 valida su forma (BR5.8, P10 = A)" }
      - { name: payload, type: document, required: true, constraints: "Solo datos sintéticos (NFR12); ningún nombre, testimonio ni expediente real; papeles de prueba como prueba_a, sin nombres de sistema (cambio 03)" }
    constraints:
      - "Los fixtures de C6 viven en contracts/analyzer/v1/fixtures/, fuera de la lista de SHA256SUMS: la copia sin editar son solo los dos esquemas."
    relationships:
      - { to: ContractDocument, cardinality: "*..1", direction: "Fixture -> ContractDocument" }

  - name: MessageEnvelope
    status: cambia
    description: Campos comunes de los mensajes de cola de Veridicus (C2, C3, C5; C4 Retirado).
    attributes:
      - { name: schema_version, type: semver, required: true, constraints: "C2 y C3 en 2.x; mayor conocido por el consumidor" }
      - { name: message_id, type: uuid, required: true }
      - { name: run_id, type: uuid, required: true, description: "C2 y C3" }
      - { name: attempt, type: integer, required: true, min: 1 }
    constraints:
      - "Los sobres admiten campos desconocidos (cambio aditivo). Un campo obligatorio ausente o mal tipado rechaza el mensaje. Lo que va dentro (entrada, salida) es estricto porque es C6."

  - name: TurnToEvaluate
    status: Retirado
    replaced_by: RunRequest
    description: "Mensaje C2 de la revisión 1 (turno con umbral y escenario). Sale con el marco documental (cambio 01)."

  - name: EvaluationResult
    status: Retirado
    replaced_by: RunResult
    description: "Mensaje C3 de la revisión 1 (calificaciones y alertas). Sale con el marco documental."

  - name: JudgeOutput
    status: Retirado
    replaced_by: AnalyzerOutput
    description: "Salida del juez con tres calificaciones (C6 de la revisión 1). La sustituye el contrato común."

  - name: Alert
    status: Retirado
    replaced_by: ReviewSuggestion
    description: "Alerta de incongruencia con fragmento, cita del documento, pasaje y CoT (C7 de la revisión 1)."

  - name: Grade
    status: Retirado
    replaced_by: FindingType
    description: "Enum congruente / incongruente / no documentada. Sale con el marco documental."

  - name: ForbiddenVocabularyList
    status: cambia
    description: Lista versionada C8 (forbidden-vocabulary.v2.yaml).
    attributes:
      - { name: schema_version, type: semver, required: true, default: "2.0.0" }
      - { name: terms, type: list, required: true, constraints: "los mismos 9 términos de la 1.0.0 (P2 = A); cada ampliación por su PR" }
      - { name: match.whole_word, type: boolean, required: true, default: true }
      - { name: match.case_insensitive, type: boolean, required: true, default: true }
      - { name: match.accent_insensitive, type: boolean, required: true, default: true }
      - { name: excluded_spans, type: list, required: true, allowed: [cita_literal, analyst_text, notice_text] }
      - { name: quote_delimiters, type: pair, required: true, default: ["«", "»"], description: "P1 = A; ahora dentro de hecho, observaciones y tema" }
      - { name: scanned, type: list, required: true, default: ["salida.hallazgos[].hecho", "salida.hallazgos[].observaciones", "salida.observaciones_conductor[].tema", "reporte consolidado", "catálogo de mensajes de la consola"] }
      - { name: categories_forbidden_in_schemas, type: list, required: true, default: [veracity_score, is_lying, truthfulness, veracidad, credibilidad] }

  - name: ErrorCodeCatalog
    status: cambia
    description: >
      Catálogo único de code (ErrorCode de C1), compartido por la API, las colas, la biblioteca y el
      proxy. Ahora trae también la traducción uno a uno desde error.codigo de C6.
    attributes:
      - { name: code, type: identifier, required: true, unique: true, constraints: "forma <dominio>.<motivo>; los valores de C1 revisión 2" }
      - { name: http_status, type: integer, required: false }
      - { name: c6_codigo, type: enum, required: false, unique: true, allowed: [salida_invalida, bloqueo_contenido, tiempo_agotado, proveedor, anonimizador_no_disponible, incidente_anonimizacion], description: "Solo en los seis code que traducen un error.codigo de C6" }
    relationships:
      - { to: ExceptionClass, cardinality: "1..1", direction: "ErrorCodeCatalog.code <-> ExceptionClass" }

  - name: ResultLabelCatalog
    status: cambia
    description: >
      Asocia cada resultado visible con su único rótulo en la consola (P3 = A). La revisión 2 cambia las
      filas por AC5.5.4 y P8 = A. La consola lo importa y no escribe otros rótulos de resultado.
    attributes:
      - { name: result_kind, type: enum, required: true, unique: true, allowed: [review_suggestion, contradiction, type_fecha, type_numero, type_lugar, type_persona, type_negacion, type_secuencia, type_otro] }
      - { name: label, type: text, required: true, unique: true, allowed: ["Sugerencia de revisión", "Contradicción en el relato", "Fecha", "Número", "Lugar", "Persona", "Negación", "Secuencia", "Otro"] }
      - { name: applies_to_type, type: FindingType, required: false, description: "Solo en las 7 filas type_*" }
    constraints:
      - "Exactamente nueve filas: dos de resultado y una por cada valor de FindingType."

  - name: UtcTimestamp
    status: se mantiene
    description: >
      Formato de fecha de lo que Veridicus emite (P4 = A). La copia de C6 conserva su format date-time
      sin editar; U11 emite sus fechas en esta forma, que cabe en ese formato.
    attributes:
      - { name: value, type: text, required: true, constraints: "AAAA-MM-DDTHH:MM:SSZ; UTC con Z; sin fracciones ni desfases" }

  - name: MetricDefinition
    status: cambia
    description: Nombre, tipo y etiquetas de una métrica de C15 (review.v2.yaml; sale la razón AIR).
    attributes:
      - { name: name, type: identifier, required: true, unique: true, constraints: "prefijo veridicus_" }
      - { name: type, type: enum, required: true, allowed: [counter, gauge, histogram] }
      - { name: labels, type: list, required: true, constraints: "solo identificadores o valores de enum, nunca texto (NFR10)" }

  # ---- Nuevas en la revisión 2 ----

  - name: ApprovedCopyManifest
    status: nuevo
    description: >
      contracts/analyzer/v1/SHA256SUMS (P5 = A). Registra las huellas de los dos esquemas tal como llegan
      del principal. Es la referencia versionada con la que la CI compara la copia, porque la CI no ve
      /insumos.
    attributes:
      - { name: entries, type: list, required: true, constraints: "exactamente dos: entrada.schema.json y salida.schema.json" }
      - { name: entries[].sha256, type: hex64, required: true }
      - { name: entries[].file, type: path, required: true }
      - { name: contract_version, type: semver, required: true, default: "1.0.0" }
    constraints:
      - "v1.0.0: entrada 28606016b51dd19d873e7ee8fae7d959f0a98c225ab2690d0fd935296c3c41a8; salida e1528b7de1db9b5a3ca8c6f3e8eacb0eeec92522423014d6644ab39918bedeaf."
      - "No se copia el README.md del principal."

  - name: AnalyzerInput
    status: nuevo
    description: Entrada del contrato común (C6, entrada.schema.json); copia sin editar.
    attributes:
      - { name: contrato, type: const, required: true, default: "1.0.0" }
      - { name: transcripcion, type: document, required: true, description: "entrevista, origen (corpus | guiada | sintetico), consentimiento y turnos" }
      - { name: modo, type: enum, required: true, allowed: [final, incremental] }
      - { name: hasta_turno, type: integer, required: false, min: 1, description: "Obligatorio en incremental" }
      - { name: desde_turno, type: integer, required: false, min: 1, description: "Obligatorio en incremental" }
      - { name: perfil, type: text, required: true, description: "Nombre de un perfil aprobado (C18)" }
    relationships:
      - { to: Consent, cardinality: "0..1", direction: "AnalyzerInput -> Consent" }

  - name: Consent
    status: nuevo
    description: Bloque consentimiento de C6 (A-4, VE-06); sin datos personales.
    attributes:
      - { name: tipo, type: enum, required: true, allowed: [persona, autoridad] }
      - { name: version_texto, type: text, required: true }
      - { name: autoriza_transferencia, type: boolean, required: true }
      - { name: autoriza_voz, type: boolean, required: true }
      - { name: autoriza_conservar_audio, type: boolean, required: true }
      - { name: requiere_mandato, type: boolean, required: true }
      - { name: constancia, type: text, required: false, description: "Obligatoria con tipo autoridad; un identificador, nunca un nombre" }
      - { name: constancia_mandato, type: text, required: false, description: "Obligatoria con requiere_mandato true" }
      - { name: registrado_en, type: date-time, required: true }
    constraints:
      - "Obligatorio con origen corpus o guiada; origen sintetico queda exento."

  - name: AnalyzerOutput
    status: nuevo
    description: Salida del contrato común (C6, salida.schema.json); copia sin editar.
    attributes:
      - { name: estado, type: enum, required: true, allowed: [ok, error] }
      - { name: error.codigo, type: enum, required: false, allowed: [salida_invalida, bloqueo_contenido, tiempo_agotado, proveedor, anonimizador_no_disponible, incidente_anonimizacion] }
      - { name: hallazgos, type: list, required: true, description: "Cada elemento es un Finding" }
      - { name: observaciones_conductor, type: list, required: false, description: "aclaracion_neutra con tema y turnos" }
      - { name: registro, type: document, required: true, description: "llamadas (CallRecord), descartes, fragmentado, tokens, costo" }
      - { name: prompt_sha256, type: hex64, required: true }
      - { name: config_sha256, type: hex64, required: true }
    constraints:
      - "estado error: error obligatorio, hallazgos y observaciones_conductor vacíos. estado ok: sin error."
    relationships:
      - { to: Finding, cardinality: "0..*", direction: "AnalyzerOutput -> Finding" }
      - { to: CallRecord, cardinality: "0..*", direction: "AnalyzerOutput -> CallRecord" }

  - name: Finding
    status: nuevo
    description: Hallazgo de contradicción de C6 (AUTONOMIA-05).
    attributes:
      - { name: id, type: text, required: true, constraints: "<entrevista>-C<nn>" }
      - { name: hecho, type: text, required: true, constraints: "no vacío; pasa el escaneo de C8" }
      - { name: tipo, type: FindingType, required: true }
      - { name: cita_a, type: Quote, required: true }
      - { name: cita_b, type: Quote, required: true }
      - { name: observaciones, type: text, required: true, constraints: "no vacío; pasa el escaneo de C8" }
      - { name: actos, type: list, required: false }

  - name: FindingType
    status: nuevo
    description: Valor; los 7 tipos de hallazgo de C6.
    attributes:
      - { name: value, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }

  - name: Quote
    status: nuevo
    description: Cita de C6 ($defs/cita); la única definición, que C7 referencia.
    attributes:
      - { name: cita, type: text, required: true, constraints: "texto literal; « […] » separa fragmentos del mismo turno" }
      - { name: turno, type: text, required: true, constraints: "T<n>" }
      - { name: pagina, type: integer, required: false, min: 1 }
      - { name: avisos, type: list, required: false, allowed: [turno_entrevistador, turno_plegado] }

  - name: CallRecord
    status: nuevo
    description: Fila de registro.llamadas de C6. Su papel sigue cerrado en tres valores (cambio 03, V-1).
    attributes:
      - { name: papel, type: enum, required: true, allowed: [juez, verificador, verificador_permutado] }
      - { name: proveedor, type: text, required: true }
      - { name: modelo, type: text, required: true }
      - { name: anonimizado, type: boolean, required: true }
      - { name: proveedor_alterno, type: boolean, required: true }
      - { name: tokens_entrada, type: integer, required: true, min: 0 }
      - { name: tokens_salida, type: integer, required: true, min: 0 }
      - { name: fecha, type: date-time, required: true }
      - { name: version, type: text, required: false }
      - { name: esfuerzo_o_cuantizacion, type: text, required: false }
      - { name: motor, type: text, required: false }
      - { name: semilla, type: integer, required: false }

  - name: RunRequest
    status: nuevo
    description: Mensaje C2 RunRequested (veridicus:runs, 2.x).
    attributes:
      - { name: envelope, type: MessageEnvelope, required: true }
      - { name: session_id, type: uuid, required: true }
      - { name: effective_config, type: EffectiveConfig, required: true }
      - { name: config_sha256, type: hex64, required: true }
      - { name: entrada, type: AnalyzerInput, required: true }
      - { name: enqueued_at, type: UtcTimestamp, required: true }
      - { name: deadline_at, type: UtcTimestamp, required: true }

  - name: RunResult
    status: nuevo
    description: Mensaje C3 RunResult (veridicus:results, 2.x).
    attributes:
      - { name: envelope, type: MessageEnvelope, required: true }
      - { name: salida, type: AnalyzerOutput, required: true }
      - { name: finished_at, type: UtcTimestamp, required: true }

  - name: ReviewSuggestion
    status: nuevo
    description: >
      C7 v2 (review-suggestion.v2.json): el hallazgo convertido en sugerencia de revisión con su estado
      (AUTONOMIA-03). Estricto y sin campos de veracidad.
    attributes:
      - { name: suggestion_id, type: uuid, required: true }
      - { name: session_id, type: uuid, required: true }
      - { name: first_run_id, type: uuid, required: true }
      - { name: hallazgo_id, type: identifier, required: false, description: "id del hallazgo en C6 de la corrida que lo propuso" }
      - { name: hecho, type: text, required: true }
      - { name: tipo, type: FindingType, required: true }
      - { name: actos, type: list, required: false }
      - { name: cita_a, type: Quote, required: true, description: "$ref '/veridicus/contracts/analyzer/v1/salida#/$defs/cita' (BR4.3, BR12.3)" }
      - { name: cita_b, type: Quote, required: true, description: "La misma referencia que cita_a" }
      - { name: observaciones, type: text, required: true }
      - { name: state, type: enum, required: true, allowed: [pending, accepted, edited, dismissed] }
      - { name: observations_viewed, type: boolean, required: true }
      - { name: note, type: text, required: false, description: "Obligatoria y no vacía si state es dismissed (BR4.4)" }
      - { name: reformulation, type: text, required: false, description: "Obligatoria y no vacía si state es edited (BR4.4)" }
      - { name: decided_by, type: uuid, required: false, description: "Obligatorio si state no es pending; ausente si es pending (BR4.4)" }
      - { name: decided_at, type: UtcTimestamp, required: false, description: "Obligatorio si state no es pending; ausente si es pending (BR4.4)" }

  - name: RoleName
    status: nuevo
    description: >
      Nombre de papel de una llamada a un modelo (V-1, opción A). Deja de ser una lista cerrada en
      model_calls (C13), en model-call.v1.yaml (C19) y en la petición del proxy (C21). Cada perfil
      declara los suyos.
    attributes:
      - { name: value, type: text, required: true, constraints: "patrón ^[a-z][a-z0-9_]{0,31}$" }

  - name: Destination
    status: nuevo
    description: Destino de un papel en un perfil (C18 $defs/destination, C13 Destination).
    attributes:
      - { name: provider, type: enum, required: true, allowed: [anthropic, google, openai, local] }
      - { name: model, type: token, required: true }
      - { name: scope, type: enum, required: true, allowed: [local, external] }
      - { name: version, type: token, required: false }
      - { name: family, type: token, required: false }
      - { name: base_url, type: uri, required: false, description: "Solo local" }
      - { name: api_key_ref, type: text, required: false, constraints: "patrón genérico ^[A-Z][A-Z0-9_]{2,63}$; el prefijo lo exige quien carga el perfil (KeyPrefix)" }
      - { name: parameters, type: document, required: false, description: "effort, temperature, quantization, engine, seed" }

  - name: ProfileBase
    status: nuevo
    description: >
      Esquema genérico de perfil (V-1, opción A): contracts/profiles/profile-base.schema.v1.yaml. Lo usan
      el analizador y sistema; el anonimizador y su proxy validan contra él. Es abierto: no declara
      additionalProperties false, para que una especialización añada sus campos; cada especialización se
      cierra con unevaluatedProperties false (R-08).
    attributes:
      - { name: purpose, type: text, required: true, constraints: "patrón ^[a-z][a-z0-9_]{0,31}$; cada especialización fija su enum (el analizador: evaluation, demonstration, production)" }
      - { name: roles, type: map, required: true, constraints: "clave RoleName -> Destination; al menos un papel" }
      - { name: role_aliases, type: map, required: false, constraints: "clave RoleName -> RoleName existente en roles; sin cadenas ni alias que pisen un papel" }
      - { name: fallback_provider, type: Destination, required: false, description: "Uno por perfil y sirve a cualquier papel (P7 = A)" }

  - name: AnalyzerProfile
    status: nuevo
    description: >
      Especialización del analizador (contracts/profiles/profiles.schema.v1.yaml, que sustituye la forma
      de campos fijos judge y verifier de C18). Extiende ProfileBase con unevaluatedProperties false.
    attributes:
      - { name: purpose, type: enum, required: true, allowed: [evaluation, demonstration, production] }
      - { name: roles, type: map, required: true, constraints: "exactamente judge y verifier" }
      - { name: role_aliases, type: map, required: true, constraints: "exactamente { verifier_permuted: verifier }" }
      - { name: permutation, type: boolean, required: true }
      - { name: chunking, type: document, required: false, description: "enabled, window, overlap (C25 es su tope)" }
      - { name: same_family_declared, type: boolean, required: false, default: false }
      - { name: batch_only, type: boolean, required: false }
    relationships:
      - { to: ProfileBase, cardinality: "1..1", direction: "AnalyzerProfile extends ProfileBase" }

  - name: KeyPrefix
    status: nuevo
    description: >
      Prefijo obligatorio de api_key_ref (V-1). Es un parámetro del código que carga perfiles (U11
      ExecutionProfiles, U10 proxy), no un campo del archivo: un perfil no puede elegir qué variables lee.
      U1 publica la constante de Veridicus.
    attributes:
      - { name: value, type: text, required: true, default: "VERIDICUS_", constraints: "patrón ^[A-Z][A-Z0-9]*_$" }

  - name: PriceTable
    status: nuevo
    description: Esquema de config/prices.yaml (C18 prices.schema.v1.yaml).
    attributes:
      - { name: version, type: text, required: true }
      - { name: currency, type: const, required: true, default: USD }
      - { name: prices, type: list, required: true, description: "provider, model, input_per_million, output_per_million" }

  - name: EffectiveConfig
    status: nuevo
    description: Configuración efectiva (C18 effective-config.v1.yaml) que viaja en C2; de ella salen profile_sha256 y config_sha256 (JCS, RFC 8785).
    attributes:
      - { name: analyzer_version, type: semver, required: true }
      - { name: profile_name, type: text, required: true }
      - { name: profile, type: AnalyzerProfile, required: true }
      - { name: profile_sha256, type: hex64, required: true }
      - { name: prompt_sha256, type: hex64, required: true }
      - { name: limits, type: document, required: true, description: "las cifras de C25 que cambian el resultado" }

  - name: ModelCall
    status: nuevo
    description: Registro de una llamada (contracts/model_calls/model-call.v1.yaml), compartido por C13, C19 y C21.
    attributes:
      - { name: role, type: RoleName, required: true }
      - { name: provider, type: enum, required: true, allowed: [anthropic, google, openai, local] }
      - { name: model, type: token, required: true }
      - { name: input_tokens, type: integer, required: true, min: 0 }
      - { name: output_tokens, type: integer, required: true, min: 0 }
      - { name: fallback_provider, type: boolean, required: true }
      - { name: anonymized, type: boolean, required: true }
      - { name: at, type: UtcTimestamp, required: true }
      - { name: version, type: token, required: false }
      - { name: effort_or_quantization, type: token, required: false }
      - { name: engine, type: token, required: false }
      - { name: seed, type: integer, required: false }

  - name: RoleTranslation
    status: nuevo
    description: >
      Tabla fija ModelCall.role -> CallRecord.papel (regla 8 de contract-summary). Publicada como dato
      para que U11 no la reescriba.
    attributes:
      - { name: role, type: RoleName, required: true, unique: true, allowed: [judge, verifier, verifier_permuted] }
      - { name: papel, type: enum, required: true, unique: true, allowed: [juez, verificador, verificador_permutado] }
    constraints:
      - "Exactamente tres filas; otro papel no tiene traducción a C6."

  - name: CliReport
    status: nuevo
    description: Reporte de corrida o de evaluación de la CLI (C19 report.schema.v1.yaml); sin campos de texto libre (P12).
    attributes:
      - { name: kind, type: enum, required: true, allowed: [run, evaluation] }
      - { name: runs, type: list, required: true, description: "interview_sha256, status, error_code, findings, discards, calls" }
      - { name: runs[].calls[].role, type: enum, required: true, allowed: [judge, verifier, verifier_permuted], description: "El reporte es del analizador: restringe RoleName a sus tres papeles" }
      - { name: totals, type: document, required: true }
      - { name: metrics, type: document, required: false }
      - { name: bias_table, type: list, required: false }

  - name: LimitsCatalog
    status: nuevo
    description: Catálogo único de límites (C25 limits.v1.yaml); las cifras las fija NFR Requirements.
    attributes:
      - { name: limits, type: map, required: true, constraints: "nombre -> { value, unit }; los nombres de C25" }

  - name: NeutralClarificationRule
    status: nuevo
    description: Regla de las aclaraciones neutras (C8 neutral-clarification.v1.yaml; VE-05, DT23).
    attributes:
      - { name: mentions_contradiction, type: boolean, required: true, default: true }
      - { name: phrases, type: list, required: true, default: ["antes dijo", "dijo antes", "se contradice"] }
      - { name: cites_turn, type: boolean, required: true, default: true }

  - name: NoticeText
    status: nuevo
    description: Aviso de propósito limitado (C8 notice.v1.yaml; VE-01). El texto exacto lo fija el autor en el PR de B1.
    attributes:
      - { name: version, type: semver, required: true }
      - { name: text, type: text, required: true, constraints: "contiene la frase base de VE-01" }

  - name: ExceptionClass
    status: nuevo
    description: >
      Clase de excepción de libs/ (jerarquía declarativa), una por code del catálogo y sin lógica
      (unit-of-work U1, R-02 de la revisión 2 de Units Generation).
    attributes:
      - { name: class_name, type: identifier, required: true, unique: true }
      - { name: code, type: reference, references: ErrorCodeCatalog, required: true, unique: true }

  - name: ContractsPackage
    status: nuevo
    description: >
      Paquete instalable de los contratos (V-3, P6 = A): distribución veridicus-contracts, paquete de
      importación veridicus_contracts. La carpeta del repositorio sigue siendo contracts/.
    attributes:
      - { name: distribution, type: text, required: true, default: veridicus-contracts }
      - { name: import_name, type: identifier, required: true, default: veridicus_contracts }
      - { name: version, type: semver, required: true, description: "Etiqueta vX.Y.Z al cerrar B1 (cambio 03, V-3)" }
      - { name: package_data, type: list, required: true, description: "todos los esquemas y catálogos de contracts/, para que se lean sin el repositorio" }
      - { name: path_map, type: map, required: true, description: "ruta en contracts/ -> módulo o dato en veridicus_contracts; la fija functional-spec.md §1 (R-03)" }
    constraints:
      - "No depende de Redis, Kubernetes, bases de datos ni de la consola."

  - name: ProfilesFile
    status: nuevo
    description: >
      Sobre del archivo de perfiles (config/profiles.yaml en Veridicus; el de sistema tiene la misma
      forma). Lo valida ProfileValidator (R-08).
    attributes:
      - { name: schema_version, type: semver, required: true, constraints: "const 1.0.0" }
      - { name: profiles, type: map, required: true, constraints: "nombre con patrón ^[a-z0-9-]{1,48}$ -> ProfileBase o AnalyzerProfile, según kind" }
    relationships:
      - { to: ProfileBase, cardinality: "1..*", direction: "ProfilesFile -> ProfileBase" }

  - name: ProfileValidator
    status: nuevo
    description: >
      Función pura veridicus_contracts.profiles.validate (P9 = A, BR9.8). La llaman U10 (módulo y proxy),
      U11 (ExecutionProfiles) y sistema, cada uno con su prefijo.
    attributes:
      - { name: signature, type: text, required: true, default: "validate(data: Mapping[str, object], *, key_prefix: str, kind: Literal['base', 'analyzer']) -> Mapping[str, Profile]" }
      - { name: error, type: identifier, required: true, default: "ProfileValidationError (code config.invalid_profile)" }
    constraints:
      - "No lee archivos, entorno ni red; key_prefix no tiene valor por omisión y debe cumplir ^[A-Z][A-Z0-9_]{1,31}_$."
      - "El mensaje de error nombra el perfil, el papel y el ajuste, nunca un valor."

  - name: LimitsLoader
    status: nuevo
    description: Función pura veridicus_contracts.limits.load (P9 = A, BR11.1).
    attributes:
      - { name: signature, type: text, required: true, default: "load(environ: Mapping[str, str]) -> Limits" }
      - { name: env_name, type: text, required: true, default: "VERIDICUS_LIMIT_<NOMBRE en mayúsculas>" }
      - { name: error, type: identifier, required: true, default: "LimitsConfigError (code config.invalid_limit)" }
    constraints:
      - "Solo baja una cifra del catálogo; un valor mayor, no entero o de un límite inexistente falla."

  - name: SchemaRegistry
    status: nuevo
    description: >
      Registro veridicus_contracts.registry que resuelve las referencias entre esquemas sin red (BR12.3,
      R-03). Carga cada esquema del paquete bajo https://veridicus.invalid/ más su $id, sin modificar el
      archivo (la copia de C6 queda intacta).
    attributes:
      - { name: base_uri, type: uri, required: true, default: "https://veridicus.invalid/" }
      - { name: ref_form, type: text, required: true, default: "ruta absoluta del $id de destino más el puntero, p. ej. /veridicus/contracts/analyzer/v1/salida#/$defs/cita" }
    constraints:
      - "Es el único resolvedor; ningún servicio resuelve una referencia por ruta de archivo."
      - "En TypeScript se usa el mismo base_uri con addSchema de ajv."

  - name: ScanCase
    status: nuevo
    description: >
      Caso de escaneo de vocabulario o de aclaración neutra (integrity/scan-cases.v1.yaml, BR5.8,
      P10 = A). U1 valida su forma; U11 lo ejecuta en B11 con scan(text, literal_sources).
    attributes:
      - { name: case_id, type: identifier, required: true, unique: true, constraints: "E<n> del escenario de functional-spec.md o un id propio" }
      - { name: field, type: enum, required: true, allowed: [hecho, observaciones, tema, cita, note, reformulation, notice] }
      - { name: text, type: text, required: true, constraints: "sintético" }
      - { name: literal_sources, type: list, required: true, description: "turnos sintéticos de la entrada; puede ir vacía" }
      - { name: expected_matches, type: list, required: true, description: "términos o frases que deben coincidir; vacía si no debe haber coincidencia" }
      - { name: expected_excluded_spans, type: list, required: false, description: "tramos entre «…» que deben quedar fuera del escaneo" }
      - { name: rule, type: reference, required: true, description: "BR5.2, BR5.3, BR5.5 o BR5.6" }
```

## Resumen

- **ContractDocument** y **Fixture** siguen siendo la pareja central. ContractDocument ahora distingue
  la copia externa de C6 (`origin: external_copy`) y amplía la lista de contratos estrictos.
- **Salen** TurnToEvaluate, EvaluationResult, JudgeOutput, Alert y Grade con el marco documental. Los
  sustituyen RunRequest, RunResult, AnalyzerOutput, ReviewSuggestion y FindingType.
- **El contrato común** se modela con AnalyzerInput, Consent, AnalyzerOutput, Finding, Quote y
  CallRecord. Todos salen de una copia sin editar que **ApprovedCopyManifest** protege con sus huellas
  (P5).
- **Los papeles abiertos (V-1):** RoleName es una cadena con patrón. **ProfileBase** es el perfil genérico
  y **AnalyzerProfile** la especialización que exige `judge` y `verifier`. **KeyPrefix** saca el prefijo
  de la clave del archivo y lo pasa al código. **RoleTranslation** deja fija la traducción de los tres
  papeles del analizador a C6, que no cambia.
- **Correcciones de la revisión asesora (P9–P11):** **ProfileValidator**, **LimitsLoader** y
  **SchemaRegistry** son las tres funciones puras que U1 publica; **ProfilesFile** modela el sobre del
  archivo; **ScanCase** convierte los escenarios del escaneo en datos que ejecuta U11. ReviewSuggestion,
  CallRecord y ModelCall quedan completos.
- **ResultLabelCatalog** pasa a nueve rótulos: dos de resultado y los 7 tipos (P8). **ContractsPackage**
  hace instalables los contratos con un nombre que no choca en `sistema` (P6).
