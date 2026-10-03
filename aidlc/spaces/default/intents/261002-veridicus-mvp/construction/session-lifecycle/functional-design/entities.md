# Entidades — U6 session-lifecycle

**Insumos.** Unidad U6 de `inception/units-generation/unit-of-work.md` (unit-of-work) e historias
US1.2, US2.3, US2.5, US7.1, US10.1 y US11.2 (`unit-of-work-story-map.md`); FR2.4, FR3.3, FR8 y FR10.1 de
`inception/requirements-analysis/requirements.md` (requirements); TruthFrame e InterviewSession de
`inception/domain-design/components.md` (components); C1 y C2 de
`inception/contract-design/contract-summary.md` (contract-summary); PasteTranscriptDialog y F3 de
`refined-mockups/interaction-spec.md`; respuestas P1–P3 de `functional-design-questions.md`; entidades de
U4 (`Scenario`, `ScenarioVersion`, `InterviewSessionRecord`, `Turn`), que U6 amplía.

**Frontera AUTONOMIA-04.** Todo vive en PostgreSQL dentro del clúster (`session-api`); ninguna entidad
de U6 sale del clúster.

```yaml
entities:
  - name: ScenarioVersion
    description: Ampliación de U4. Una versión nueva de un escenario existente (FR2.4).
    attributes:
      - { name: version_number, type: integer, required: true, min: 2, description: "número siguiente al mayor existente del escenario" }
      - { name: supersedes_version_id, type: reference, references: ScenarioVersion, required: false, description: "la versión anterior más reciente al cargar" }
    constraints:
      - "Las versiones anteriores conservan sus pasajes y su SHA-256; no existe operación de modificación ni borrado."

  - name: Turn
    description: Ampliación de U4 para la transcripción pegada (P1, P2).
    attributes:
      - { name: speaker, type: text, required: false, constraints: "1–30 caracteres sin dígitos ni ':'; la marca de hablante sin los dos puntos" }
      - { name: role, type: enum, required: true, allowed: [testimony, interviewer], default: testimony }
      - { name: paste_batch_id, type: uuid, required: false, description: "identifica la transcripción pegada de la que salió" }
    constraints:
      - "Un turno interviewer se guarda evaluated sin evaluación: no se encola ni se califica (P2 = A)."

  - name: TranscriptPaste
    description: Transcripción pegada y confirmada (US2.3); solo existe como identificador del lote.
    attributes:
      - { name: paste_batch_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: client_request_id, type: uuid, required: true }
      - { name: turn_count, type: integer, required: true, min: 1, max: 100 }
      - { name: char_count, type: integer, required: true, min: 1, max: 100000 }
      - { name: created_by, type: reference, references: User, required: true }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "(session_id, client_request_id) único."

  - name: TurnPreview
    description: Resultado de dividir una transcripción antes de confirmar (valor; no se guarda).
    attributes:
      - { name: index, type: integer, required: true }
      - { name: speaker, type: text, required: false }
      - { name: role, type: enum, required: true, allowed: [testimony, interviewer] }
      - { name: text, type: text, required: true }
      - { name: too_long, type: boolean, required: true, description: "más de 2 000 caracteres" }

  - name: InterviewerLabels
    description: Lista configurable de marcas que identifican al entrevistador (P2 = A).
    attributes:
      - { name: labels, type: list, required: true, default: [Analista, Entrevistador], constraints: "comparación sin mayúsculas ni tildes" }

  - name: InterviewSessionRecord
    description: Ampliación de U4 con el estado suspendido (FR8).
    attributes:
      - { name: status, type: enum, required: true, allowed: [open, suspended, finalized, consolidated] }
      - { name: last_heartbeat_at, type: UtcTimestamp, required: false }
      - { name: suspended_at, type: UtcTimestamp, required: false }

  - name: SessionStatusChange
    description: Historial de U4; U6 añade las transiciones open → suspended (actor sistema) y suspended → open (actor dueño).
    attributes:
      - { name: from_status, type: text, required: false }
      - { name: to_status, type: text, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [user, system] }
      - { name: at, type: UtcTimestamp, required: true }

  - name: SessionListItem
    description: Fila de la lista de sesiones y del historial lateral (valor).
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: scenario_name, type: text, required: true }
      - { name: version_number, type: integer, required: true }
      - { name: owner_username, type: text, required: true }
      - { name: created_at, type: UtcTimestamp, required: true }
      - { name: status, type: enum, required: true, allowed: [open, suspended, finalized, consolidated] }
      - { name: pending_suggestions, type: integer, required: true, min: 0 }
```

## Resumen

- U6 amplía entidades de U4: versiones nuevas de un escenario, turnos con hablante y rol, y el estado
  `suspended` de la sesión.
- **TranscriptPaste** y **TurnPreview** sostienen el pegado en dos pasos (vista previa y confirmación).
- **InterviewerLabels** decide qué turnos son preguntas del entrevistador (se guardan como contexto y no se
  evalúan, P2).
- **SessionListItem** alimenta la lista de sesiones (M1) y el historial lateral (COULD).
