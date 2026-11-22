# Entidades — U6 session-lifecycle

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-02. Conserva los nombres de las entidades que siguen;
las que salen quedan «Retirado» sin renumerar (regla de `project.md`).
- **Salen** (`Retirado`): `ScenarioVersion` (US1.2 sale con el marco documental, cambio 01) e
  `InterviewerLabels` (la marca libre de hablante de P1 y P2 de la primera pasada queda superada por el
  hablante `ENT`/`TEST` de FR3.2 y C1). También salen dos atributos: `InterviewSessionRecord.suspended_at`
  (la hora la guarda `SessionStatusChange`) y `SessionListItem.pending_suggestions` (R-05 de la revisión 1:
  ninguna historia lo pide en la lista).
- **Cambian:** `Turn`, `TranscriptPaste`, `TurnPreview`, `InterviewSessionRecord`, `SessionStatusChange` y
  `SessionListItem`.
- **Entran:** `SpeakerMarkerList` (P4 = A), `ConsentRecord` como ampliación de U4 (retirada y tipo
  `sintetico`, P5 = A), `ImportPreview` e `ImportProblem` (US2.6) y `RunProgress` (US10.1, P7 = B).

**Insumos.** Unidad U6 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) e
historias US2.3, US2.5, US2.6, US2.7, US7.1, US15.2, US10.1 y US11.2 de `unit-of-work-story-map.md`
(unit-of-work-story-map), con los cruces US5.4, US5.6 y US8.4; FR3.2, FR3.3, FR3.6, FR3.7, FR4.9, FR8,
FR10.1 y FR11.2 de `inception/requirements-analysis/requirements.md` (requirements) y VE-10 y A-4 de
`requirements-adenda-02.md`; InterviewSession, ConsoleApi y AnalystConsole de
`inception/domain-design/components.md` (components); C1, C2, C3, C6, C11, C18 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary), con CD-06; respuestas P4–P7 de
`functional-design-questions.md`; entidades de U4 (`InterviewSessionRecord`, `ConsentRecord`, `Turn`,
`AnalysisRun`, `RunStatusChange`, `SessionStatusChange`), que U6 amplía sin redefinir.

**Frontera AUTONOMIA-04.** Todo lo que define U6 vive en PostgreSQL o en memoria de `session-api` y de
`frontend`, dentro del clúster. Nada de U6 sale del clúster: lo único que puede salir es una corrida, por
la tubería de U4 y con el anonimizador delante (U10). La retirada del consentimiento, la pausa y la
terminación impiden además que salga cualquier llamada nueva (clave de cancelación de CD-06).

**Convención de auditoría.** Cada tabla nueva lleva la marca `veridicus-audit` de U3 con su clase
(`history` o `mutable`) y `purgeable`; un actor de sistema usa un valor de la lista `ActorSystem`.

```yaml
entities:
  # Salen
  - name: ScenarioVersion
    status: Retirado
    replaced_by: "ninguno"
    description: "Versión nueva de un escenario (US1.2). Sale con TruthFrame (cambio 01)."
  - name: InterviewerLabels
    status: Retirado
    replaced_by: SpeakerMarkerList
    description: "Lista de etiquetas del entrevistador (P2 de la primera pasada). La sustituye el hablante ENT/TEST de C1."

  # Ampliaciones de entidades de U4
  - name: InterviewSessionRecord
    status: cambia
    description: >
      Entidad de U4. U6 escribe las transiciones de pausa, suspensión, reanudación y terminación, crea
      las sesiones importadas y usa last_heartbeat_at y closed_to_new_turns. audit: kind mutable,
      purgeable, owner_unit U4.
    attributes:
      - { name: status, type: SessionStatus, required: true, allowed: [open, paused, suspended, finalized, terminated, blocked, consolidated], description: "enum único de C1; U6 escribe paused, suspended, terminated y la vuelta a open" }
      - { name: origin, type: enum, required: true, allowed: [guiada, corpus, sintetico], description: "U6 crea corpus y sintetico al importar" }
      - { name: closed_to_new_turns, type: boolean, required: true, default: false, description: "true al importar, al terminar y al retirar el consentimiento; nunca vuelve a false" }
      - { name: last_heartbeat_at, type: UtcTimestamp, required: false, description: "último latido del dueño; nulo se lee como created_at (R-01); la importación y la reanudación lo fijan a la hora del servidor" }
      - { name: suspended_at, status: Retirado, description: "la hora de la suspensión la guarda SessionStatusChange.at" }
    constraints:
      - "closed_to_new_turns solo pasa de false a true (disparador)."
      - "Una sesión importada nace open con closed_to_new_turns true y sin corridas."

  - name: ConsentRecord
    status: cambia
    description: >
      Entidad de U4. U6 escribe la retirada (VE-10) y crea el registro de una sesión importada, leído
      del bloque consentimiento del archivo o, en una importación sintética sin bloque, del tipo
      sintetico (P5 = A, precisión FD-U6-05). audit: kind mutable (solo la retirada), purgeable.
    attributes:
      - { name: kind, type: enum, required: true, allowed: [persona, autoridad, sintetico], description: "sintetico es nuevo: transcripción que no corresponde a una persona real" }
      - { name: authorizes_commercial_transfer, type: boolean, required: true, description: "true fijo con kind sintetico" }
      - { name: authorizes_voice, type: boolean, required: true, description: "false fijo con kind sintetico" }
      - { name: authorizes_audio_retention, type: boolean, required: true, description: "false fijo con kind sintetico" }
      - { name: requires_mandate, type: boolean, required: true, description: "false fijo con kind sintetico" }
      - { name: text_version, type: text, required: true, description: "con kind sintetico, el valor fijo «no-aplica-sintetico»" }
      - { name: recorded_by, type: reference, references: User, required: true, description: "el analista que importa" }
      - { name: recorded_at, type: UtcTimestamp, required: true, description: "hora del servidor; registrado_en del archivo se ignora" }
      - { name: withdrawn_at, type: UtcTimestamp, required: false, description: "hora del servidor al registrar la retirada (la ruta no lleva cuerpo)" }
      - { name: withdrawn_by, type: reference, references: User, required: false, description: "el dueño que registra la retirada" }
    constraints:
      - "withdrawn_at y withdrawn_by solo pasan de nulo a un valor, juntos (disparador de U4)."
      - "kind sintetico solo con InterviewSessionRecord.origin sintetico."

  - name: Turn
    status: cambia
    description: >
      Entidad de U4 (C1 Turn, C6 turnos). U6 crea turnos pegados (origin pasted) e importados (origin
      imported). Los atributos speaker y role de la revisión 1 salen: el hablante es ENT o TEST (C1).
      audit: kind history, purgeable.
    attributes:
      - { name: speaker, type: enum, required: true, allowed: [ENT, TEST], description: "pegado: de la marca o heredado (BR2.1); importado: hablante del archivo" }
      - { name: text, type: text, required: true, description: "pegado: sin la marca y sin espacios en los bordes; importado: el texto del archivo tal cual" }
      - { name: page, type: integer, required: false, min: 1, description: "solo importados (C6 pagina)" }
      - { name: page_end, type: integer, required: false, min: 1, description: "solo importados (C6 pagina_fin); page_end >= page" }
      - { name: fold_state, type: enum, required: true, allowed: [visible, plegado], description: "importado: C6 estado; pegado: visible" }
      - { name: origin, type: enum, required: true, allowed: [typed, pasted, voice, imported] }
      - { name: paste_batch_id, type: reference, references: TranscriptPaste, required: false, description: "solo turnos pegados" }
    constraints:
      - "En una sesión guiada, (session_id, n) es único y sin huecos (U4). En una importada, n es el número del archivo: único y en orden, con huecos posibles (precisión FD-U6-06)."

  - name: SessionStatusChange
    status: cambia
    description: >
      Historial de U4. U6 añade las transiciones de su máquina (functional-spec §3) con actor y hora.
      audit: kind history, purgeable.
    attributes:
      - { name: from_status, type: SessionStatus, required: false }
      - { name: to_status, type: SessionStatus, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [person, system] }
      - { name: actor_user_id, type: reference, references: User, required: false, description: "el dueño en pausa, reanudación del análisis, reanudación y terminación; el analista al importar" }
      - { name: actor_system, type: ActorSystem, required: false, allowed: [session-supervisor], description: "session-supervisor al suspender por falta de latido (valor nuevo, precisión FD-U6-13)" }
      - { name: at, type: UtcTimestamp, required: true }
    constraints:
      - "actor_user_id no nulo si y solo si actor_kind es person; actor_system no nulo si y solo si es system (convención de U3)."

  # Pegado
  - name: TranscriptPaste
    status: cambia
    description: >
      Bloque pegado y confirmado (US2.3). Agrupa sus turnos y su corrida, y hace idempotente el reenvío.
      audit: kind history, purgeable.
    attributes:
      - { name: paste_batch_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: client_request_id, type: uuid, required: true }
      - { name: first_turn, type: integer, required: true, min: 1, description: "n del primer turno del bloque" }
      - { name: turn_count, type: integer, required: true, min: 1, description: "a lo sumo transcript_max_turns (C25); el tope fijo de 100 de la revisión 1 sale" }
      - { name: char_count, type: integer, required: true, min: 1, description: "longitud de text en puntos de código; a lo sumo transcript_max_chars (C25)" }
      - { name: run_id, type: reference, references: AnalysisRun, required: false, description: "nulo si el bloque no tiene turnos TEST o la sesión está en pausa" }
      - { name: created_by, type: reference, references: User, required: true }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "(session_id, client_request_id) único."
    relationships:
      - { to: Turn, cardinality: "1..*", direction: "TranscriptPaste -> Turn" }
      - { to: AnalysisRun, cardinality: "0..1", direction: "TranscriptPaste -> AnalysisRun" }

  - name: TurnPreview
    status: cambia
    description: Un turno de la vista previa del pegado (valor; no se guarda). La consola y el servidor lo calculan con la misma regla.
    attributes:
      - { name: index, type: integer, required: true, min: 1, description: "posición en el bloque" }
      - { name: speaker, type: enum, required: true, allowed: [ENT, TEST] }
      - { name: speaker_source, type: enum, required: true, allowed: [marker, alias, inherited, default], description: "marca literal, alias de la lista, heredado del turno anterior o TEST por ser el primero" }
      - { name: text, type: text, required: true }
      - { name: char_count, type: integer, required: true, min: 1 }
      - { name: over_limit, type: boolean, required: true, description: "char_count > turn_max_chars (C25)" }

  - name: SpeakerMarkerList
    status: nuevo
    description: >
      Lista versionada de marcas de hablante en contracts/ (precisión FD-U6-08), que leen la consola y el
      servidor. Solo cambia por PR (FR9.2).
    attributes:
      - { name: version, type: semver, required: true }
      - { name: literal_markers, type: map, required: true, default: { "ENT": ENT, "TEST": TEST } }
      - { name: aliases, type: map, required: true, default: { "Entrevistador": ENT, "Analista": ENT, "Testimonio": TEST, "Compareciente": TEST } }
      - { name: examples, type: list, required: true, description: "ejemplos versionados de división (texto de entrada y turnos esperados), todos sintéticos (AC2.3.2)" }
    constraints:
      - "La comparación ignora mayúsculas y tildes; un alias no puede repetirse con dos hablantes."

  # Importación
  - name: ImportPreview
    status: nuevo
    description: Resumen de un archivo de importación válido antes de crear nada (valor; no se guarda, AC2.6.5).
    attributes:
      - { name: entrevista, type: text, required: true }
      - { name: origen, type: enum, required: true, allowed: [corpus, sintetico] }
      - { name: turn_count, type: integer, required: true, min: 1 }
      - { name: interviewer_turns, type: integer, required: true, min: 0, description: "turnos ENT (K)" }
      - { name: folded_turns, type: integer, required: true, min: 0, description: "turnos plegados (P)" }
      - { name: first_page, type: integer, required: false }
      - { name: last_page, type: integer, required: false, description: "máximo de pagina_fin o pagina" }
      - { name: has_consent_block, type: boolean, required: true }

  - name: ImportProblem
    status: nuevo
    description: Un problema de un archivo de importación (valor). La respuesta 422 nombra el primero y el total.
    attributes:
      - { name: position, type: integer, required: false, description: "posición del turno en el archivo; nula si el problema es de la cabecera" }
      - { name: turn_n, type: integer, required: false, description: "n del turno si lo trae" }
      - { name: field, type: text, required: true, description: "ruta del campo (p. ej. turnos[36].hablante)" }
      - { name: message, type: text, required: true, description: "en español, sin texto del testimonio (p. ej. «Turno 37: falta el hablante»)" }
    constraints:
      - "Los problemas se ordenan por posición en el archivo; los de la cabecera van primero."

  # Lista e historial
  - name: SessionListItem
    status: cambia
    description: Fila de la lista de sesiones (M1) y del historial lateral (valor), armada desde C1 SessionSummary.
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: entrevista, type: text, required: true }
      - { name: origin_label, type: enum, required: true, allowed: [Importada, Guiada], description: "Importada para corpus y sintetico" }
      - { name: profile_name, type: text, required: true }
      - { name: owner_username, type: text, required: true }
      - { name: created_at, type: UtcTimestamp, required: true, description: "se muestra en hora de Colombia" }
      - { name: status, type: SessionStatus, required: true }
      - { name: consent_withdrawn, type: boolean, required: true, description: "añade «· consentimiento retirado» al estado" }
      - { name: scenario_name, status: Retirado, description: "sale TruthFrame; lo sustituye entrevista" }
      - { name: version_number, status: Retirado, description: "sale ScenarioVersion" }
      - { name: pending_suggestions, status: Retirado, description: "R-05: la lista no lo muestra; el campo de C1 SessionSummary se sigue llenando (BR3.5)" }

  # Progreso
  - name: RunProgress
    status: nuevo
    description: Lo que la consola muestra de una corrida en proceso (valor, P7 = B). No hay «van N».
    attributes:
      - { name: run_id, type: uuid, required: true }
      - { name: stage_label, type: enum, required: true, allowed: ["En cola", "Procesando audio…", "Analizando contradicciones…"] }
      - { name: stage_started_at, type: UtcTimestamp, required: true, description: "hora de la última transición de la corrida; el cronómetro mm:ss cuenta desde aquí" }
      - { name: planned_windows, type: integer, required: false, min: 1, description: "solo modo final con chunking activo en effective_config (BR5.3)" }
```

## Resumen

- U6 no crea un agregado propio: amplía la sesión de U4 (`InterviewSessionRecord`, `ConsentRecord`,
  `Turn`, `SessionStatusChange`) con las transiciones del ciclo de vida, las sesiones importadas y la
  retirada del consentimiento, que no es un estado sino un dato del consentimiento con quién y cuándo.
- **TranscriptPaste**, **TurnPreview** y **SpeakerMarkerList** sostienen el pegado en dos pasos con la
  misma regla en la consola y en el servidor; el hablante es `ENT` o `TEST` (P4 = A).
- **ImportPreview** e **ImportProblem** sostienen la importación: vista previa antes de crear nada y
  rechazo completo con el primer problema y el total.
- **SessionListItem** alimenta la lista de sesiones (M1) y el historial lateral (COULD).
- **RunProgress** es el progreso sin cambio de contrato de P7 = B: etapa, cronómetro y, en el modo final
  por ventanas, el total de ventanas.
- Salen `ScenarioVersion` e `InterviewerLabels`, y los atributos `suspended_at` y `pending_suggestions` de
  la lista.
