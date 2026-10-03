# Entidades — U4 text-flow

**Insumos.** Unidad U4 de `inception/units-generation/unit-of-work.md` (unit-of-work) e historias
asignadas en `unit-of-work-story-map.md` (unit-of-work-story-map); FR2–FR5, NFR10, NFR11 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); componentes TruthFrame,
InterviewSession, SemanticEvaluation, HumanReview, ModelGateway, IntegrityPolicy y AnalystConsole de
`inception/domain-design/components.md` (components); contratos C1–C4, C6–C10 y C13–C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P5 de
`functional-design-questions.md`; decisiones de Functional Design de U1 (cita literal «…», lista de 9
términos, catálogo de rótulos, formato de fecha) y de U3 (convención de auditoría).

**Frontera AUTONOMIA-04.** Todas las entidades persistentes viven en PostgreSQL + `pgvector` dentro del
clúster; los mensajes viajan por Redis dentro del clúster; el juez y los *embeddings* son servidores
internos (C14). Ningún dato de esta unidad sale del clúster.

```yaml
entities:
  # TruthFrame
  - name: Scenario
    description: Escenario de control; agrupa sus versiones.
    attributes:
      - { name: scenario_id, type: uuid, required: true, unique: true }
      - { name: name, type: text, required: true, constraints: "1–120 caracteres" }
      - { name: created_by, type: reference, references: User, required: true }
      - { name: created_at, type: UtcTimestamp, required: true }
    relationships:
      - { to: ScenarioVersion, cardinality: "1..*", direction: "Scenario -> ScenarioVersion" }

  - name: ScenarioVersion
    description: Versión inmutable de un escenario, con el SHA-256 de su fuente y su estado de indexación.
    attributes:
      - { name: version_id, type: uuid, required: true, unique: true }
      - { name: scenario_id, type: reference, references: Scenario, required: true }
      - { name: version_number, type: integer, required: true, min: 1 }
      - { name: source_text, type: text, required: true, constraints: "UTF-8, 1 a 1 048 576 bytes" }
      - { name: source_sha256, type: hex64, required: true, unique: true }
      - { name: status, type: enum, required: true, allowed: [indexing, ready, error], default: indexing }
      - { name: error_code, type: text, required: false, description: "code del catálogo; solo si status es error" }
      - { name: uploaded_by, type: reference, references: User, required: true }
      - { name: uploaded_at, type: UtcTimestamp, required: true }
      - { name: ready_at, type: UtcTimestamp, required: false }
    constraints:
      - "(scenario_id, version_number) único."
      - "Una versión ready nunca cambia; no existe operación de modificación ni borrado (FR2.4)."
    relationships:
      - { to: ScenarioDocument, cardinality: "1..*", direction: "ScenarioVersion -> ScenarioDocument" }
      - { to: Passage, cardinality: "0..*", direction: "ScenarioVersion -> Passage (≥ 1 si ready)" }

  - name: ScenarioDocument
    description: >
      Pieza documental dentro de una versión (P3 = A). La abre un encabezado `# [DOC-…] Título`; sin
      ninguno, el archivo entero es DOC-1.
    attributes:
      - { name: version_id, type: reference, references: ScenarioVersion, required: true }
      - { name: document_id, type: text, required: true, constraints: "forma DOC-<letras, dígitos o guiones>, máximo 40 caracteres; único dentro de la versión" }
      - { name: title, type: text, required: false }
      - { name: position, type: integer, required: true, min: 1 }

  - name: Passage
    description: Fragmento literal de un documento con su vector (P2 = A).
    attributes:
      - { name: passage_id, type: uuid, required: true, unique: true }
      - { name: version_id, type: reference, references: ScenarioVersion, required: true }
      - { name: document_id, type: text, required: true, constraints: "existe en ScenarioDocument de la misma versión" }
      - { name: position, type: integer, required: true, min: 1, description: "orden dentro de la versión" }
      - { name: text, type: text, required: true, constraints: "subcadena literal de source_text; oraciones completas; máximo de caracteres por pasaje (lo fija NFR Requirements)" }
      - { name: embedding, type: vector, required: true, description: "dimensión del modelo de embeddings (NFR Requirements)" }

  # InterviewSession
  - name: InterviewSessionRecord
    description: Sesión de entrevista ligada a una versión lista y a la instantánea del umbral.
    attributes:
      - { name: session_id, type: uuid, required: true, unique: true }
      - { name: owner_user_id, type: reference, references: User, required: true }
      - { name: scenario_version_id, type: reference, references: ScenarioVersion, required: true }
      - { name: scenario_sha256, type: hex64, required: true }
      - { name: similarity_threshold, type: decimal, required: true, min: 0, max: 1, description: "instantánea al crear la sesión (ADR-006)" }
      - { name: top_k, type: integer, required: true, default: 3, description: "instantánea, P4 = A" }
      - { name: status, type: enum, required: true, allowed: [open, suspended, finalized, consolidated], default: open }
      - { name: created_at, type: UtcTimestamp, required: true }
      - { name: finalized_at, type: UtcTimestamp, required: false }
      - { name: last_heartbeat_at, type: UtcTimestamp, required: false }
    constraints:
      - "scenario_sha256 es el de la versión al crearla; ninguno de los campos de instantánea cambia después."

  - name: SessionStatusChange
    description: Historial de solo inserción del estado de la sesión (ADR-003, convención de U3).
    attributes:
      - { name: change_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: from_status, type: text, required: false }
      - { name: to_status, type: text, required: true }
      - { name: actor_user_id, type: reference, references: User, required: false, description: "null solo en cambios automáticos del sistema (suspensión por U6), con actor_kind system" }
      - { name: actor_kind, type: enum, required: true, allowed: [user, system] }
      - { name: at, type: UtcTimestamp, required: true }

  - name: Turn
    description: Turno del testimonio, numerado en orden dentro de la sesión.
    attributes:
      - { name: turn_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: number, type: integer, required: true, min: 1 }
      - { name: text, type: text, required: true, constraints: "1 a 2 000 caracteres tras quitar espacios de los bordes (P5 = A)" }
      - { name: origin, type: enum, required: true, allowed: [typed, pasted, voice] }
      - { name: client_request_id, type: uuid, required: true }
      - { name: status, type: enum, required: true, allowed: [queued, processing, evaluated, error] }
      - { name: processing_stage, type: enum, required: false, allowed: [transcribing, retrieving, judging] }
      - { name: error_code, type: text, required: false }
      - { name: attempt, type: integer, required: true, min: 1, default: 1 }
      - { name: submitted_at, type: UtcTimestamp, required: true }
      - { name: deadline_at, type: UtcTimestamp, required: true }
      - { name: evaluated_at, type: UtcTimestamp, required: false }
    constraints:
      - "(session_id, number) único y sin huecos."
      - "(session_id, client_request_id) único: un reenvío del navegador no crea otro turno."

  - name: Claim
    description: Afirmación de un turno según la regla de P1 (valor, no se guarda aparte).
    attributes:
      - { name: claim_index, type: integer, required: true, min: 0 }
      - { name: text, type: text, required: true, constraints: "subcadena literal del turno" }
      - { name: start, type: integer, required: true, description: "posición en el texto del turno" }

  - name: TurnEvaluation
    description: Registro de evaluación de un intento de un turno (AC3.1.6); no visible en la interfaz.
    attributes:
      - { name: evaluation_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: reference, references: Turn, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: threshold_used, type: decimal, required: true }
      - { name: model_digest, type: text, required: false, description: "ausente si ninguna afirmación llegó al juez" }
      - { name: prompt_sha256, type: hex64, required: false }
      - { name: evaluated_at, type: UtcTimestamp, required: true }
    constraints:
      - "(turn_id, attempt) único: la ingesta es idempotente."
    relationships:
      - { to: ClaimEvaluation, cardinality: "1..*", direction: "TurnEvaluation -> ClaimEvaluation" }

  - name: ClaimEvaluation
    description: Resultado por afirmación dentro de una evaluación.
    attributes:
      - { name: claim_index, type: integer, required: true }
      - { name: text, type: text, required: true }
      - { name: max_similarity, type: decimal, required: true, min: 0, max: 1 }
      - { name: nearest_passage_ids, type: list, required: true, constraints: "hasta 3, por similitud descendente" }
      - { name: guard, type: enum, required: true, allowed: [below_threshold, at_or_above_threshold] }
      - { name: grade, type: Grade, required: true }

  - name: HandoffPackage
    description: Paquete de Contexto de Traspaso; uno por intento de turno con alguna afirmación «no documentada».
    attributes:
      - { name: package_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: reference, references: Turn, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: fragment, type: text, required: true, description: "texto literal del turno actual" }
      - { name: previous_turn_numbers, type: list, required: true, constraints: "0 a 3" }
      - { name: nearest_passages, type: list, required: true, constraints: "hasta 3 pasajes distintos, coeficiente descendente" }
      - { name: undocumented_claim_indexes, type: list, required: true, constraints: "≥ 1" }
      - { name: threshold_used, type: decimal, required: true }
      - { name: interrupted_cot, type: text, required: true, description: "determinista, sin LLM" }
      - { name: affective_note, type: text, required: false, description: "solo U8 (COULD)" }

  # HumanReview (tablas que crea U4; las decisiones son de U5)
  - name: ReviewSuggestion
    description: Sugerencia de revisión creada desde una alerta válida (C7, C10).
    attributes:
      - { name: suggestion_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: turn_id, type: reference, references: Turn, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: claim_index, type: integer, required: true }
      - { name: fragment, type: text, required: true, constraints: "no vacío ni solo espacios; subcadena literal del turno" }
      - { name: quote, type: text, required: true, constraints: "no vacío ni solo espacios; subcadena literal del pasaje" }
      - { name: document_id, type: text, required: true, constraints: "pertenece a la versión de la sesión" }
      - { name: passage_id, type: reference, references: Passage, required: true }
      - { name: cot, type: text, required: true, constraints: "no vacío ni solo espacios" }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "(turn_id, attempt, claim_index) único (C10)."
      - "Nace pendiente: sin fila en ReviewDecision (U5)."

  - name: ReviewRound
    description: Ronda de revisión; U4 abre la ronda 1 al proponer la primera sugerencia (C10, ADR-007).
    attributes:
      - { name: round_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: number, type: integer, required: true, min: 1 }
      - { name: status, type: enum, required: true, allowed: [open, locked] }
      - { name: opened_at, type: UtcTimestamp, required: true }

  # Configuración
  - name: ThresholdConfig
    description: Ajuste VERIDICUS_SIMILARITY_THRESHOLD leído por el cargador de configuración (FR5.1).
    attributes:
      - { name: value, type: decimal, required: true, constraints: "número finito dentro del rango que fija NFR Requirements" }

  - name: JudgePrompt
    description: Prompt del sistema del juez, montado de solo lectura (FR4.6).
    attributes:
      - { name: path, type: path, required: true }
      - { name: expected_sha256, type: hex64, required: true, description: "el del archivo en el repositorio" }
```

## Resumen

- **TruthFrame:** `Scenario` → `ScenarioVersion` (inmutable, con SHA-256 y estado) → `ScenarioDocument`
  (nuevo por P3) y `Passage` (segmentado por párrafo y oración, P2).
- **InterviewSession:** la sesión guarda instantáneas de versión, SHA-256, umbral y `top_k` (P4); los
  turnos se numeran sin huecos y miden hasta 2 000 caracteres (P5); cada intento evaluado deja una
  `TurnEvaluation` con una `ClaimEvaluation` por afirmación (P1) y, si hay algo «no documentado», un
  `HandoffPackage`.
- **HumanReview (parte de U4):** `ReviewSuggestion` y la ronda 1; las decisiones son de U5.
- **Configuración:** el umbral y el prompt del juez no se escriben desde la aplicación.
