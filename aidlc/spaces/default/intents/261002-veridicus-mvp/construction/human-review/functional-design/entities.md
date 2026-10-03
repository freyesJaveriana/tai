# Entidades — U5 human-review

**Insumos.** Unidad U5 de `inception/units-generation/unit-of-work.md` (unit-of-work) e historias
US5.1–US5.4 (`unit-of-work-story-map.md`); FR6, FR1.2 y NFR11 de
`inception/requirements-analysis/requirements.md` (requirements); HumanReview, ADR-003, ADR-007 y
ADR-009 de `inception/domain-design/components.md` (components); C1, C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); ReviewSuggestionCard de
`refined-mockups/interaction-spec.md`; respuesta P1 de `functional-design-questions.md`.

**Frontera AUTONOMIA-04.** Todo vive en PostgreSQL dentro del clúster (módulo HumanReview de
`session-api`); las métricas de C15 solo llevan identificadores y contadores.

U4 crea `ReviewSuggestion` y abre la ronda 1 (C10); U5 es dueño de la máquina de estados, de
`ReviewDecision`, de `CotView` y del ciclo de las rondas.

```yaml
entities:
  - name: ReviewRound
    description: Ronda de revisión de una sesión (ADR-007). La 1 es la revisión inicial; cada corrección del reporte abre otra.
    attributes:
      - { name: round_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: number, type: integer, required: true, min: 1 }
      - { name: kind, type: enum, required: true, allowed: [initial, correction] }
      - { name: status, type: enum, required: true, allowed: [open, locked] }
      - { name: based_on_report_version_id, type: reference, references: ReportVersion, required: false, description: "obligatorio si kind es correction" }
      - { name: based_on_round_id, type: reference, references: ReviewRound, required: false, description: "ronda de la que hereda (la bloqueada por esa versión del reporte)" }
      - { name: opened_by, type: reference, references: User, required: false, description: "null solo en la ronda 1, que abre el sistema al proponer" }
      - { name: opened_at, type: UtcTimestamp, required: true }
      - { name: locked_by_report_version_id, type: reference, references: ReportVersion, required: false }
      - { name: locked_at, type: UtcTimestamp, required: false }
    constraints:
      - "(session_id, number) único."
      - "Como mucho una ronda open por sesión."
      - "Una ronda locked nunca vuelve a open."

  - name: ReviewDecision
    description: Decisión humana sobre una sugerencia dentro de una ronda; solo inserción (ADR-003).
    attributes:
      - { name: decision_id, type: uuid, required: true, unique: true }
      - { name: round_id, type: reference, references: ReviewRound, required: true }
      - { name: suggestion_id, type: reference, references: ReviewSuggestion, required: true }
      - { name: previous_state, type: enum, required: true, allowed: [pending, accepted, edited, dismissed] }
      - { name: state, type: enum, required: true, allowed: [accepted, edited, dismissed] }
      - { name: note, type: text, required: false, constraints: "obligatoria y no en blanco si state es dismissed" }
      - { name: reformulation, type: text, required: false, constraints: "obligatoria y no en blanco si state es edited; ausente en otro caso" }
      - { name: actor_user_id, type: reference, references: User, required: true }
      - { name: at, type: UtcTimestamp, required: true }
    constraints:
      - "Registrada en la convención de auditoría: sin UPDATE ni DELETE."

  - name: CotView
    description: Evento «CoT consultada» de un usuario sobre una sugerencia; solo inserción.
    attributes:
      - { name: view_id, type: uuid, required: true, unique: true }
      - { name: suggestion_id, type: reference, references: ReviewSuggestion, required: true }
      - { name: user_id, type: reference, references: User, required: true }
      - { name: viewed_at, type: UtcTimestamp, required: true }
    constraints:
      - "Vale por usuario y sugerencia en todas las rondas (P1 = A)."

  - name: EffectiveState
    description: >
      Estado vigente de una sugerencia en una ronda (valor calculado, no guardado): la última decisión de
      esa ronda; si no hay, el estado vigente en la ronda de la que hereda; si no hereda, pending.
    attributes:
      - { name: suggestion_id, type: uuid, required: true }
      - { name: round_id, type: uuid, required: true }
      - { name: state, type: enum, required: true, allowed: [pending, accepted, edited, dismissed] }
      - { name: last_decision_id, type: uuid, required: false }
```

## Resumen

- **ReviewRound** organiza las decisiones: una ronda abierta como mucho por sesión; la corrección hereda
  de la ronda que bloqueó la versión del reporte de la que parte.
- **ReviewDecision** y **CotView** son historiales de solo inserción.
- **EffectiveState** es la regla de herencia que ADR-007 dejó a esta etapa: la sugerencia no guarda un
  campo «estado».
