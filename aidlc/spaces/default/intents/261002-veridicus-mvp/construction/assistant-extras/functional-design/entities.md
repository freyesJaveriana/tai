# Entidades — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02** (y las revisiones 3 de
Inception). Sustituye a la revisión 1 del 2026-10-02.
- **Sigue:** nada de la revisión 1 queda igual. La permutación cambia de lugar: ya no es una segunda lectura
  del juez con pasajes, sino la llamada `verifier_permuted` que diseñó U11. U8 solo fija su valor en los
  perfiles que no son de evaluación (`rules.md`, BR6).
- **Sale (`status: Retirado`, sin renumerar):** EvaluationOptions (sus banderas `suggest_question` y
  `affective`; la permutación es el campo `permutation` del perfil de C18), ReadingOrder,
  PermutationOutcome, SuggestedQuestion, QuestionDecision, AffectiveKeywordList y AffectiveNote. Motivo:
  cambio 01 (sin marco de verdad, pasajes ni Paquete de Contexto de Traspaso) y US11.1 Retirada (WON'T por
  DT15).
- **Entra (`status: nuevo`):** ClarificationCandidate y ClarificationDiscardEvent (en memoria, en la
  biblioteca), ConductorObservation y ConductorObservationDecision (en `session-api`).

**Insumos.**
- Unidad U8 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3: `service`, SHOULD,
  S) y su mapa `unit-of-work-story-map.md` (unit-of-work-story-map): US10.3 → US10.5, con los cruces de
  US5.5 (aclaraciones) y US5.6 (accesibilidad).
- FR10.3, FR10.5 y FR4.5 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3), y
  VE-05 de `requirements-adenda-02.md`. AC10.3.1–AC10.3.3, AC10.5.1, US5.5 y US5.6 de `stories.md`, y
  AC10.3.4, AC5.5.5 y AC5.5.6 de `stories-adenda-02.md`.
- InterviewSession (ConductorObservation), IncoherenceAnalyzer, IntegrityPolicy y AnalystConsole de
  `inception/domain-design/components.md` (components, revisión 3).
- C1 (`ConductorObservation`, `SessionView.conductor_observations`, `/conductor-observations/{id}/decision`),
  C3, C6 (`observaciones_conductor` y su regla 7), C8 (`neutral-clarification.v1.yaml` y `scanned`) y C18
  (`permutation`) de `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- Respuestas P4 = A, P5 = A y P6 = A de `functional-design-questions.md` y su lista «Lo que el diseño
  resolverá sin preguntar» (puntos 1–10). Diseños de U11, U4, U3 y U1 citados por descripción.

**Glosario de identificadores** (team.md, Code Style): aclaración neutra → `NeutralClarification` (el
elemento de `observaciones_conductor`); aclaración guardada → `ConductorObservation`; su decisión →
`ConductorObservationDecision`. Los campos del contrato común conservan su nombre en español (`tipo`,
`tema`, `turnos`; CD-05).

```yaml
entities:
  # --- Revisión 1: Retirado (cambio 01, US11.1 Retirada) ---------------------------------------
  - name: EvaluationOptions
    status: Retirado
    description: "Banderas permutation, suggest_question y affective en C2. Sale: la permutación es el campo permutation del perfil (C18) y los otros dos extras salen con el cambio 01."
  - name: ReadingOrder
    status: Retirado
    description: "Orden de lectura de los pasajes ante el juez. Sale: ya no hay pasajes; la permutación es la del verificador de U11."
  - name: PermutationOutcome
    status: Retirado
    description: "Comparación de dos lecturas del juez. Sale: el resultado de la permutación es el descarte rechazado_permutacion de U11."
  - name: SuggestedQuestion
    status: Retirado
    description: "Pregunta sugerida a partir de los pasajes del Paquete de Contexto de Traspaso. La sustituye ConductorObservation."
  - name: QuestionDecision
    status: Retirado
    description: "Historial de la decisión sobre una pregunta. Lo sustituye ConductorObservationDecision."
  - name: AffectiveKeywordList
    status: Retirado
    description: "Lista de palabras emocionales del indicio afectivo. Sale con US11.1 (WON'T por DT15)."
  - name: AffectiveNote
    status: Retirado
    description: "Texto fijo del indicio afectivo. Sale con US11.1."

  # --- Biblioteca (libs/incoherence_analyzer/, en memoria) -------------------------------------
  - name: ClarificationCandidate
    status: nuevo
    description: >
      Aclaración que la biblioteca arma de forma determinista a partir de un hallazgo ya consolidado de una
      corrida incremental con estado ok (P4 = A). Vive solo en memoria. Si pasa las cuatro validaciones,
      sale como un elemento de observaciones_conductor (NeutralClarification de C6); si no, se quita y deja
      un ClarificationDiscardEvent.
    attributes:
      - { name: source_finding_id, type: string, required: true, description: "id del hallazgo de origen (<entrevista>-Cnn); no sale en C6" }
      - { name: tipo, type: enum, required: true, allowed: [aclaracion_neutra], default: aclaracion_neutra }
      - { name: tema, type: text, required: true, min: 1, constraints: "hecho del hallazgo con los espacios normalizados (sin espacios al inicio ni al final, uno solo entre palabras)" }
      - { name: turnos, type: list, required: true, min: 1, constraints: "identificadores de turno de cita_a y cita_b, sin repetir, en orden numérico; cada uno cumple ^T[0-9]+$" }
      - { name: tema_key, type: text, required: true, description: "tema en minúsculas, sin tildes y con espacios normalizados; solo para deduplicar" }
    constraints:
      - "Una por hallazgo emitido; dos candidatas con los mismos turnos y el mismo tema_key en una salida se unen en una."
      - "Nunca se arma en modo final ni con estado error (C6, regla 7)."

  - name: ClarificationDiscardEvent
    status: nuevo
    description: >
      Registro de una aclaración que no pasó la validación (AC10.3.4: «se registra como descartada»). Es un
      evento de log estructurado de la biblioteca, no una fila: nunca lleva el tema, las citas ni texto de
      turnos.
    attributes:
      - { name: run_id, type: uuid, required: false, description: "presente en el trabajador; en la CLI, el identificador de la corrida de la CLI" }
      - { name: source_finding_id, type: string, required: true }
      - { name: rule, type: enum, required: true, allowed: [schema, mentions_contradiction, phrases, cites_turn, quote_text, quote_overlap, forbidden_vocabulary] }
      - { name: at, type: UtcTimestamp, required: true }

  # --- InterviewSession (services/session-api) -------------------------------------------------
  - name: ConductorObservation
    status: nuevo
    description: >
      Aclaración neutra guardada al ingerir un resultado (C3). Es la entidad ConductorObservation de
      InterviewSession (components) con los nombres de C1. Tabla de clase mutable de la convención de
      auditoría de U3: solo cambia status, una vez, de proposed a un estado final.
    attributes:
      - { name: observation_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: run_id, type: reference, references: AnalysisRun, required: true, description: "corrida que la propuso por primera vez" }
      - { name: tema, type: text, required: true, min: 1 }
      - { name: turnos, type: list, required: true, min: 1, constraints: "^T[0-9]+$; en orden numérico" }
      - { name: tema_key, type: text, required: true, description: "igual que en ClarificationCandidate; no sale en C1" }
      - { name: status, type: enum, required: true, allowed: [proposed, approved, discarded], default: proposed }
      - { name: created_at, type: UtcTimestamp, required: true }
    derived:
      - { name: decided_by, from: "actor_user_id de la última ConductorObservationDecision" }
      - { name: decided_at, from: "at de la última ConductorObservationDecision" }
    constraints:
      - "Único (session_id, turnos, tema_key): una corrida nueva o un reintento que repite la aclaración no la duplica."
      - "status solo pasa de proposed a approved o a discarded, y nunca vuelve; un disparador de la base rechaza cualquier otro cambio de columna."
      - "Se guarda en la misma transacción que la ingesta de su corrida y solo si la salida tiene estado ok."
      - "Purgable con su sesión por la retención (U13)."

  - name: ConductorObservationDecision
    status: nuevo
    description: Historial de solo inserción de la decisión del analista (tabla history de la convención de U3).
    attributes:
      - { name: decision_id, type: uuid, required: true, unique: true }
      - { name: observation_id, type: reference, references: ConductorObservation, required: true }
      - { name: status, type: enum, required: true, allowed: [approved, discarded] }
      - { name: actor_kind, type: enum, required: true, allowed: [user] }
      - { name: actor_user_id, type: reference, references: User, required: true }
      - { name: at, type: UtcTimestamp, required: true }
    constraints:
      - "Como mucho una fila por observación, porque los dos estados son finales."
      - "Se inserta en la misma transacción que cambia ConductorObservation.status."
      - "Sin UPDATE ni DELETE del usuario de la aplicación; purgable solo por el usuario de retención."

relationships:
  - { from: InterviewSessionRecord, to: ConductorObservation, cardinality: "1 a 0..n", direction: "la sesión tiene sus aclaraciones" }
  - { from: AnalysisRun, to: ConductorObservation, cardinality: "1 a 0..n", direction: "la corrida que la propuso" }
  - { from: ConductorObservation, to: ConductorObservationDecision, cardinality: "1 a 0..1", direction: "la decisión registra quién y cuándo" }
  - { from: ClarificationCandidate, to: ClarificationDiscardEvent, cardinality: "1 a 0..1", direction: "una candidata rechazada deja un evento" }
```

## Resumen

- **ClarificationCandidate** es la aclaración que arma la biblioteca sin llamar a ningún modelo: `tema` =
  el `hecho` del hallazgo y `turnos` = los turnos de sus dos citas (P4 = A). Solo en modo incremental y con
  `estado: ok`.
- **ClarificationDiscardEvent** deja constancia de la aclaración que no pasa la validación, solo con IDs y
  la regla que falló.
- **ConductorObservation** es la aclaración guardada en `session-api`, deduplicada por sesión, con estado
  `proposed → approved | discarded`. `decided_by` y `decided_at` salen de **ConductorObservationDecision**,
  el historial auditado (cierra R-06).
- La permutación no tiene entidad propia en U8: es el campo `permutation` de cada perfil (C18), y su
  resultado es el descarte `rechazado_permutacion` del registro de la corrida, que ya modela U11.
- No hay frontera nueva con el exterior (AUTONOMIA-04): la aclaración se arma en el proceso que ya tiene el
  hallazgo restaurado, y ConductorObservation solo viaja de `session-api` al navegador dentro del clúster
  (`functional-spec.md` §1).
