# Entidades — U1 contracts

**Insumos.** Unidad U1 de `inception/units-generation/unit-of-work.md` (unit-of-work); contratos C1–C16
de `inception/contract-design/contract-summary.md` (contract-summary); requisitos FR4, FR5, FR9, NFR10,
NFR11 y NFR14 de `inception/requirements-analysis/requirements.md` (requirements); componente
IntegrityPolicy de `inception/domain-design/components.md` (components); respuestas P1–P4 de
`functional-design-questions.md`.

**Qué modela este documento.** U1 no tiene comportamiento en ejecución: sus «entidades» son los
documentos de contrato que guarda `contracts/` y los datos que esos documentos describen. El bloque YAML
es la fuente de verdad; las formas campo a campo de cada contrato siguen en `contract-summary.md` y no
se repiten aquí, salvo las entidades nuevas de esta etapa (catálogo de rótulos, P3) y las precisiones de
P1, P2 y P4.

```yaml
entities:
  - name: ContractDocument
    description: >
      Un contrato versionado de contracts/ (C1–C16). Es la unidad de versión, de propiedad y de PR.
    attributes:
      - { name: contract_id, type: identifier, required: true, unique: true, constraints: "C1..C16 o un id nuevo aprobado por PR" }
      - { name: kind, type: enum, required: true, allowed: [openapi, asyncapi, json_schema, vocabulary_list, db_view, python_protocol, metrics, label_catalog, error_catalog, datetime_format] }
      - { name: path, type: path, required: true, unique: true, constraints: "bajo contracts/ (C13 bajo libs/model_gateway/)" }
      - { name: version, type: semver, required: true, constraints: "MAYOR.MENOR.PARCHE" }
      - { name: owner_unit, type: identifier, required: true, description: "Unidad que decide los cambios (columna Owner de contract-summary)" }
      - { name: strict, type: boolean, required: true, default: false, description: "true en C6 y C7: todo cambio es mayor" }
    constraints:
      - "Cada ContractDocument tiene al menos un Fixture válido y uno inválido (salvo python_protocol, que se verifica con tipos)."
    relationships:
      - { to: Fixture, cardinality: "1..*", direction: "ContractDocument -> Fixture" }

  - name: Fixture
    description: Ejemplo sintético que el contrato debe aceptar o rechazar.
    attributes:
      - { name: fixture_id, type: identifier, required: true, unique: true }
      - { name: contract_id, type: reference, references: ContractDocument, required: true }
      - { name: expectation, type: enum, required: true, allowed: [accept, reject] }
      - { name: reject_reason, type: text, required: false, description: "Obligatorio si expectation es reject; nombra la regla BR que lo rechaza" }
      - { name: payload, type: document, required: true, constraints: "Solo datos sintéticos (NFR12); ningún nombre, testimonio ni expediente real" }
    relationships:
      - { to: ContractDocument, cardinality: "*..1", direction: "Fixture -> ContractDocument" }

  - name: MessageEnvelope
    description: Campos comunes de todo mensaje de cola (C2, C3, C4, C5).
    attributes:
      - { name: schema_version, type: semver, required: true, constraints: "mayor conocido por el consumidor" }
      - { name: message_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true, min: 1 }
    constraints:
      - "Los mensajes admiten campos desconocidos (cambio aditivo); un campo obligatorio ausente o mal tipado rechaza el mensaje."

  - name: TurnToEvaluate
    description: Mensaje C2. Turno a evaluar con la instantánea del umbral y de la versión de escenario.
    attributes:
      - { name: envelope, type: MessageEnvelope, required: true }
      - { name: similarity_threshold, type: decimal, required: true, min: 0, max: 1, description: "Instantánea de solo lectura tomada al crear la sesión (ADR-006)" }
      - { name: scenario_sha256, type: hex64, required: true }
      - { name: text, type: text, required: true, constraints: "no vacío" }
      - { name: previous_turns, type: list, required: true, constraints: "máximo 3" }
      - { name: deadline_at, type: UtcTimestamp, required: true }

  - name: EvaluationResult
    description: Mensaje C3. Resultado de evaluar un intento de un turno.
    attributes:
      - { name: envelope, type: MessageEnvelope, required: true }
      - { name: outcome, type: enum, required: true, allowed: [evaluated, error] }
      - { name: error_code, type: enum, required: false, allowed: [turn.error.invalid_output, turn.error.system] }
      - { name: claims, type: list, required: false, description: "Cada afirmación con grade, max_similarity y guard" }
      - { name: alerts, type: list, required: false, description: "Cada elemento es un Alert" }
      - { name: handoff_package, type: document, required: false }
      - { name: suggested_question, type: document, required: false }
    relationships:
      - { to: Alert, cardinality: "1..*", direction: "EvaluationResult -> Alert (0..* en la práctica)" }

  - name: JudgeOutput
    description: Esquema estricto C6 de la salida del juez (judge-output.v1).
    attributes:
      - { name: claims, type: list, required: true, min: 1 }
      - { name: claims[].claim_index, type: integer, required: true, min: 0 }
      - { name: claims[].grade, type: Grade, required: true }
      - { name: claims[].passage_ids, type: list, required: true }
      - { name: claims[].cot, type: text, required: true, constraints: "no vacío; pasa el escaneo de ForbiddenVocabularyList" }
    constraints:
      - "Sin propiedades adicionales en ningún nivel."

  - name: Alert
    description: Esquema estricto C7 de la alerta de incongruencia (sugerencia de revisión, alert.v1).
    attributes:
      - { name: turn_id, type: uuid, required: true }
      - { name: claim_index, type: integer, required: true, min: 0 }
      - { name: fragment, type: text, required: true, constraints: "no vacío; fragmento literal de la transcripción" }
      - { name: quote, type: text, required: true, constraints: "no vacío; cita literal del pasaje" }
      - { name: document_id, type: text, required: true, constraints: "no vacío" }
      - { name: passage_id, type: uuid, required: true }
      - { name: cot, type: text, required: true, constraints: "no vacío" }
    constraints:
      - "Sin propiedades adicionales; ningún campo de veracidad."

  - name: Grade
    description: Calificación de una afirmación frente al marco de verdad (valor).
    attributes:
      - { name: value, type: enum, required: true, allowed: [congruente, incongruente, no documentada] }

  - name: ForbiddenVocabularyList
    description: Lista versionada C8 (forbidden-vocabulary.v1.yaml).
    attributes:
      - { name: schema_version, type: semver, required: true, default: "1.0.0" }
      - { name: terms, type: list, required: true, constraints: "v1.0.0 = los 9 términos aprobados (P2 = A)" }
      - { name: match.whole_word, type: boolean, required: true, default: true }
      - { name: match.case_insensitive, type: boolean, required: true, default: true }
      - { name: match.accent_insensitive, type: boolean, required: true, default: true }
      - { name: excluded_spans, type: list, required: true, allowed: [literal_testimony_quote, literal_scenario_quote, analyst_text] }
      - { name: quote_delimiters, type: pair, required: true, default: ["«", "»"], description: "Nuevo en esta etapa (P1 = A)" }
      - { name: categories_forbidden_in_schemas, type: list, required: true, default: [veracity_score, is_lying, truthfulness] }

  - name: ErrorCodeCatalog
    description: Catálogo único de code estables (ErrorCode de C1), compartido por la API y las colas.
    attributes:
      - { name: code, type: identifier, required: true, unique: true, constraints: "forma <dominio>.<motivo>[.<detalle>]" }
      - { name: http_status, type: integer, required: false, description: "Estado HTTP con que viaja en C1" }

  - name: ResultLabelCatalog
    description: >
      Nuevo en esta etapa (P3 = A). Asocia cada tipo de resultado visible con su único rótulo en la
      consola. La consola lo importa; no hay otro lugar donde se escriban rótulos de resultado.
    attributes:
      - { name: result_kind, type: enum, required: true, unique: true, allowed: [review_suggestion, semantic_incongruence, undocumented_fact] }
      - { name: label, type: text, required: true, unique: true, allowed: ["Sugerencia de revisión", "Incongruencia semántica", "Hecho No Documentado"] }
      - { name: applies_to_grade, type: Grade, required: false, description: "incongruente → semantic_incongruence; no documentada → undocumented_fact; congruente no tiene rótulo" }
    constraints:
      - "Exactamente tres filas."

  - name: UtcTimestamp
    description: Formato de fecha compartido (P4 = A), valor.
    attributes:
      - { name: value, type: text, required: true, constraints: "AAAA-MM-DDTHH:MM:SSZ; UTC con Z; sin fracciones ni desfases" }

  - name: MetricDefinition
    description: Nombre, tipo y etiquetas de una métrica de C15.
    attributes:
      - { name: name, type: identifier, required: true, unique: true, constraints: "prefijo veridicus_" }
      - { name: type, type: enum, required: true, allowed: [counter, gauge, histogram] }
      - { name: labels, type: list, required: true, constraints: "solo identificadores o valores de enum, nunca texto (NFR10)" }
```

## Resumen

- **ContractDocument** y **Fixture** son la pareja central: cada contrato vive con su versión, su dueño
  y sus ejemplos que se aceptan o se rechazan.
- **MessageEnvelope**, **TurnToEvaluate** y **EvaluationResult** son los mensajes de cola; **JudgeOutput**
  y **Alert** son los dos esquemas estrictos; **Grade** es el enum de tres calificaciones.
- **ForbiddenVocabularyList** gana el par de delimitadores de cita «» (P1); su lista arranca con los 9
  términos aprobados (P2).
- **ResultLabelCatalog** es nuevo (P3): la consola no escribe rótulos de resultado propios.
- **UtcTimestamp** fija una sola forma de fecha para colas, API y reporte (P4).
