# Entidades — U8 assistant-extras

**Insumos.** Unidad U8 de `inception/units-generation/unit-of-work.md` (unit-of-work) e historias US10.3,
US10.5 y US11.1 (`unit-of-work-story-map.md`); FR10.3, FR10.5, FR11.1, FR5.2 y NFR4 de
`inception/requirements-analysis/requirements.md` (requirements); SemanticEvaluation e InterviewSession
de `inception/domain-design/components.md` (components); C1, C2, C3 y C8 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P3 de
`functional-design-questions.md`; Functional Design de U4 (flujo de evaluación, paquete y escáner).

**Frontera AUTONOMIA-04.** Todo corre en `semantic-agent` y `session-api` dentro del clúster; las dos
lecturas del juez y la pregunta sugerida usan el juez interno (C14). Ningún dato sale del clúster.

```yaml
entities:
  - name: EvaluationOptions
    description: Opciones de la sesión que viajan en C2 (options).
    attributes:
      - { name: permutation, type: boolean, required: true, default: false, description: "SHOULD; activa la segunda lectura" }
      - { name: suggest_question, type: boolean, required: true, default: false, description: "SHOULD" }
      - { name: affective, type: boolean, required: true, default: false, description: "COULD" }
    constraints:
      - "Se fijan por configuración del despliegue y se copian a la sesión al crearla; la consola no las cambia."

  - name: ReadingOrder
    description: Orden de lectura de una evaluación del juez (P1 = A), valor.
    attributes:
      - { name: order, type: enum, required: true, allowed: [forward, reversed] }
      - { name: passages_order, type: enum, required: true, allowed: [similarity_desc, similarity_asc] }
      - { name: claim_position, type: enum, required: true, allowed: [after_passages, before_passages] }
    constraints:
      - "forward = similarity_desc + after_passages; reversed = similarity_asc + before_passages; mismo prompt del sistema y misma semilla."

  - name: PermutationOutcome
    description: Resultado de comparar las dos lecturas para una afirmación candidata (valor; queda en la evaluación).
    attributes:
      - { name: claim_index, type: integer, required: true }
      - { name: forward_grade, type: Grade, required: true }
      - { name: reversed_grade, type: Grade, required: true }
      - { name: sustained, type: boolean, required: true, description: "true solo si las dos lecturas califican incongruente" }

  - name: SuggestedQuestion
    description: Pregunta sugerida al analista para un turno (C1, C3); nunca llega al compareciente sin aprobación.
    attributes:
      - { name: question_id, type: uuid, required: true, unique: true }
      - { name: turn_id, type: reference, references: Turn, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: text, type: text, required: true, constraints: "1–300 caracteres; pasa el escaneo de vocabulario prohibido" }
      - { name: source_passage_ids, type: list, required: true, constraints: "solo pasajes recuperados para el turno" }
      - { name: status, type: enum, required: true, allowed: [proposed, approved, discarded], default: proposed }
      - { name: decided_by, type: reference, references: User, required: false }
      - { name: decided_at, type: UtcTimestamp, required: false }
    constraints:
      - "Como mucho una por intento de turno."
      - "Una pregunta approved o discarded no cambia de nuevo."

  - name: QuestionDecision
    description: Historial de solo inserción de la decisión sobre una pregunta (convención de auditoría).
    attributes:
      - { name: question_id, type: reference, references: SuggestedQuestion, required: true }
      - { name: status, type: enum, required: true, allowed: [approved, discarded] }
      - { name: actor_user_id, type: reference, references: User, required: true }
      - { name: at, type: UtcTimestamp, required: true }

  - name: AffectiveKeywordList
    description: Lista versionada de palabras clave emocionales en español (P3 = A), en contracts/.
    attributes:
      - { name: schema_version, type: semver, required: true }
      - { name: keywords, type: list, required: true, constraints: "solo términos de estado emocional (p. ej. miedo, llanto, angustia); ninguno de la lista de vocabulario prohibido" }
      - { name: match, type: document, required: true, description: "palabra completa, sin mayúsculas ni tildes (las reglas de C8)" }

  - name: AffectiveNote
    description: Texto fijo que se añade al paquete si hay indicio (AC11.1.1), valor.
    attributes:
      - { name: text, type: text, required: true, default: "Fluctuación afectiva por posible estrés/trauma en este fragmento. Se recomienda moderar el ritmo" }
```

## Resumen

- **EvaluationOptions** activa cada extra por despliegue; todos están apagados por defecto, porque ningún
  MUST depende de ellos.
- **ReadingOrder** y **PermutationOutcome** fijan qué se invierte (P1) y qué se registra cuando las
  lecturas no coinciden (P2: queda «no documentada»).
- **SuggestedQuestion** y **QuestionDecision** sostienen la aprobación del analista.
- **AffectiveKeywordList** es una lista versionada sin LLM (P3).
