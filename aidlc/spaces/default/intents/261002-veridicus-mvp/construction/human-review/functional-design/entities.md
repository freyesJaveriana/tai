# Entidades — U5 human-review

**Revisión 2 — cambio 01, adenda 02 y revisiones 3 (2026-11-22).** Reemplaza la versión aprobada el
2026-10-02. Las entidades que siguen conservan su nombre; lo que cambia lleva `status: cambia`; lo que
sale queda `status: Retirado` con su reemplazo, sin borrarlo (regla de `project.md`); lo nuevo va al
final de su grupo con `status: nuevo`.

- **Siguen y cambian:** `ReviewRound` (columnas que solo usa la revisión, estado `discarded`, `change_seq`;
  salen las referencias a ReviewReport), `ReviewDecision` (`change_seq`, actor de la convención de
  auditoría, longitud acotada) y `EffectiveState` (orden por `change_seq`; nota y reformulación propias).
- **Se cita sin reescribirla:** `ReviewSuggestion`, la tabla que crea U4 con `propose` (C10). U5 la lee y
  protege sus campos; no cambia su forma.
- **Sale:** `CotView` → `ObservationsView` (nombre de components).
- **Entran:** `ObservationsView` y el valor `PurgeReceipt` (C24).

**Insumos.** Unidad U5 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) y su
mapa `unit-of-work-story-map.md` (unit-of-work-story-map): US5.1–US5.4 y los cruces US5.5, US5.6, US8.4 y
US15.7. FR1.2, FR6, FR7.2, FR7.5 y NFR11 de `inception/requirements-analysis/requirements.md`
(requirements) y A-2 de `requirements-adenda-02.md`. HumanReview, ConsoleApi, la tabla «Propiedad de las
entidades», ADR-003, ADR-007 y ADR-009 de `inception/domain-design/components.md` (components). C1, C7
v2, C10, C11, C15 v2, C23, C24 y C25 de `inception/contract-design/contract-summary.md`
(contract-summary). Functional Design de U3 (convención de auditoría, usuarios de base de datos, orden de
bloqueo) y de U4 (tablas `ReviewSuggestion` y `ReviewRound`, `propose`, `change_cursor`). Respuestas P1,
P2 y P3 de `functional-design-questions.md`.

**Frontera AUTONOMIA-04.** Todo vive en PostgreSQL dentro del clúster (módulo HumanReview de
`session-api`). Nada de U5 sale del clúster: las observaciones, la nota y la reformulación solo viajan
entre `session-api` y el navegador del analista; las métricas de C15 llevan solo un identificador de
sesión y enumeraciones.

## Modelo de entidades (fuente de verdad)

```yaml
entities:
  - name: ReviewSuggestion
    status: cambia
    description: >
      Hallazgo de C6 guardado como sugerencia de revisión (C7 v2). La tabla y propose son de U4 (C10);
      el dominio es de HumanReview. U5 la lee y protege sus campos: nunca la modifica.
      Marca veridicus-audit: kind history, purgeable true, owner_unit U5.
    attributes:
      - { name: suggestion_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: first_run_id, type: reference, references: AnalysisRun, required: true }
      - { name: hecho, type: text, required: true, protected: true }
      - { name: tipo, type: enum, required: true, protected: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      - { name: cita_a, type: json, required: true, protected: true, description: "cita de C6: texto, turno, página si la hay, avisos" }
      - { name: cita_b, type: json, required: true, protected: true }
      - { name: observaciones, type: text, required: true, protected: true }
      - { name: actos, type: list, required: false }
      - { name: pair_key, type: hex64, required: true, description: "interno; no sale en C7" }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "Los campos protected (hecho, tipo, cita_a, cita_b, observaciones) no cambian nunca: la tabla es history y veridicus_app no tiene UPDATE."
      - "No tiene columna de estado: el estado es EffectiveState."
      - "Sin campos de veracidad ni puntaje (C7 v2, additionalProperties false)."

  - name: ReviewRound
    status: cambia
    description: >
      Ronda de revisión de una sesión (ADR-007). La 1 (initial) la abre propose o, sin sugerencias, la
      consolidación; cada «Corregir reporte» abre una de corrección. U4 crea la tabla con round_id,
      session_id, number, status y opened_at; U5 añade el resto en su migración.
      Marca veridicus-audit: kind mutable, purgeable true, owner_unit U5.
    attributes:
      - { name: round_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: number, type: integer, required: true, min: 1 }
      - { name: kind, type: enum, required: true, allowed: [initial, correction], default: initial, status: nuevo }
      - { name: status, type: enum, required: true, allowed: [open, locked, discarded], status: cambia, description: "discarded es nuevo (copia de trabajo descartada, AC6.3.2)" }
      - { name: based_on_round_id, type: reference, references: ReviewRound, required: false, status: nuevo, description: "obligatorio si kind es correction: la última ronda locked de la sesión" }
      - { name: opened_by, type: reference, references: User, required: false, status: nuevo, description: "nulo solo en la ronda 1 que abre el sistema" }
      - { name: opened_actor_kind, type: enum, required: true, allowed: [user, system], status: nuevo }
      - { name: opened_actor_system, type: ActorSystem, required: false, status: nuevo, description: "analysis-worker si la abre propose en la ingesta" }
      - { name: opened_at, type: UtcTimestamp, required: true }
      - { name: locked_at, type: UtcTimestamp, required: false, status: nuevo }
      - { name: discarded_by, type: reference, references: User, required: false, status: nuevo }
      - { name: discarded_at, type: UtcTimestamp, required: false, status: nuevo }
      - { name: change_seq, type: bigint, required: true, status: nuevo, description: "valor de change_cursor de la sesión en la última escritura de la ronda" }
      - { name: based_on_report_version_id, status: Retirado, description: "Sale: HumanReview no referencia ReviewReport (R-01 de Domain Design, ADR-007 revisada); ReviewReport deduce la versión de la ronda bloqueada anterior" }
      - { name: locked_by_report_version_id, status: Retirado, description: "Sale por lo mismo: la relación ronda ↔ versión la guarda ReportVersion.round_id (U7)" }
    constraints:
      - "(session_id, number) único."
      - "Como mucho una ronda open por sesión (índice único parcial)."
      - "kind initial solo para number 1; kind correction exige based_on_round_id con status locked."
      - "Disparador de la marca mutable: status solo pasa de open a locked (fija locked_at) o de open a discarded (fija discarded_by y discarded_at); una ronda initial nunca pasa a discarded; las demás columnas no cambian; change_seq solo sube."
      - "Sin DELETE para veridicus_app; solo veridicus_retention borra (C24)."

  - name: ReviewDecision
    status: cambia
    description: >
      Decisión humana sobre una sugerencia dentro de una ronda; solo inserción (ADR-003).
      Marca veridicus-audit: kind history, purgeable true, owner_unit U5, actor actor_user_id, hora at.
    attributes:
      - { name: decision_id, type: uuid, required: true, unique: true }
      - { name: round_id, type: reference, references: ReviewRound, required: true }
      - { name: suggestion_id, type: reference, references: ReviewSuggestion, required: true }
      - { name: previous_state, type: enum, required: true, allowed: [pending, accepted, edited, dismissed] }
      - { name: state, type: enum, required: true, allowed: [accepted, edited, dismissed] }
      - { name: note, type: text, required: false, max: review_text_max_chars, constraints: "obligatoria y no en blanco si state es dismissed" }
      - { name: reformulation, type: text, required: false, max: review_text_max_chars, constraints: "obligatoria y no en blanco si state es edited; ausente en otro caso" }
      - { name: actor_kind, type: enum, required: true, allowed: [user], status: nuevo }
      - { name: actor_system, type: ActorSystem, required: false, status: nuevo, description: "siempre nulo: solo una persona decide" }
      - { name: actor_user_id, type: reference, references: User, required: true }
      - { name: at, type: UtcTimestamp, required: true }
      - { name: change_seq, type: bigint, required: true, status: nuevo, description: "change_cursor de la sesión tras el bump de la decisión; ordena las decisiones" }
    constraints:
      - "(round_id, suggestion_id, change_seq) único; change_seq es estrictamente creciente por sesión."
      - "actor_user_id y at no nulos (CHECK y NOT NULL); sin UPDATE ni DELETE para veridicus_app."
      - "En blanco = vacío tras quitar espacios, incluidos los Unicode; la base añade un CHECK con btrim como segunda barrera."

  - name: CotView
    status: Retirado
    description: "Sale con la CoT (cambio 01). La sustituye ObservationsView."

  - name: EffectiveState
    status: cambia
    description: >
      Estado vigente de una sugerencia en una ronda (valor calculado, nunca guardado): la decisión de
      mayor change_seq de esa ronda; si no hay, el estado vigente en based_on_round_id; si no hereda,
      pending. Nota y reformulación son las de esa misma decisión.
    attributes:
      - { name: suggestion_id, type: uuid, required: true }
      - { name: round_id, type: uuid, required: true }
      - { name: state, type: enum, required: true, allowed: [pending, accepted, edited, dismissed] }
      - { name: note, type: text, required: false }
      - { name: reformulation, type: text, required: false, description: "solo si state es edited" }
      - { name: decided_by, type: uuid, required: false }
      - { name: decided_at, type: UtcTimestamp, required: false }
      - { name: last_decision_id, type: uuid, required: false }
    constraints:
      - "Una ronda discarded nunca es base de otra: la herencia salta a la última ronda locked."

  - name: ObservationsView
    status: nuevo
    description: >
      Evento «Observaciones consultadas» de un usuario sobre una sugerencia; solo inserción. Vale por
      usuario y sugerencia en todas las rondas (P1 = A). Se guarda solo el primero; cada apertura queda
      además en el registro de acceso (C23), que no es de U5.
      Marca veridicus-audit: kind history, purgeable true, owner_unit U5, actor user_id, hora viewed_at.
    attributes:
      - { name: view_id, type: uuid, required: true, unique: true }
      - { name: suggestion_id, type: reference, references: ReviewSuggestion, required: true }
      - { name: user_id, type: reference, references: User, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [user] }
      - { name: actor_system, type: ActorSystem, required: false }
      - { name: viewed_at, type: UtcTimestamp, required: true }
    constraints:
      - "(suggestion_id, user_id) único: la segunda apertura no inserta (ON CONFLICT DO NOTHING)."
      - "user_id y viewed_at no nulos; sin UPDATE ni DELETE para veridicus_app."

  - name: PurgeReceipt
    status: nuevo
    description: "Valor que devuelve Purgeable.purge_session (C24): solo IDs, nunca texto."
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: observations_view_ids, type: list, required: true }
      - { name: decision_ids, type: list, required: true }
      - { name: suggestion_ids, type: list, required: true }
      - { name: round_ids, type: list, required: true }

relationships:
  - { from: InterviewSessionRecord, to: ReviewRound, cardinality: "1:N", direction: "la sesión tiene rondas" }
  - { from: InterviewSessionRecord, to: ReviewSuggestion, cardinality: "1:N", direction: "la sesión recibe sugerencias" }
  - { from: ReviewRound, to: ReviewDecision, cardinality: "1:N", direction: "la ronda contiene decisiones" }
  - { from: ReviewSuggestion, to: ReviewDecision, cardinality: "1:N", direction: "la sugerencia recibe decisiones" }
  - { from: ReviewSuggestion, to: ObservationsView, cardinality: "1:N", direction: "una por usuario" }
  - { from: ReviewRound, to: ReviewRound, cardinality: "0..1:0..N", direction: "la corrección hereda de una ronda locked" }
```

## Resumen

- **ReviewSuggestion** es la tabla de U4: U5 solo la lee, y sus cinco campos protegidos no cambian nunca
  porque la tabla es `history`.
- **ReviewRound** organiza las decisiones: una ronda `open` como mucho por sesión; la corrección hereda
  de la última ronda `locked`; una copia descartada queda `discarded` con quién y cuándo. Ya no guarda
  ninguna referencia a ReviewReport.
- **ReviewDecision** y **ObservationsView** son historiales de solo inserción con actor y hora; el
  orden de las decisiones lo da `change_seq`, el cursor de la sesión.
- **EffectiveState** es la regla de herencia de ADR-007: la sugerencia no guarda un campo «estado».
- **PurgeReceipt** es lo único que sale de la retención: IDs.
