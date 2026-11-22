# Entidades — U4 text-flow

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-03. Las entidades que siguen conservan su nombre. Las
que salen quedan con `status: Retirado` y nombran a su reemplazo, sin borrarlas (regla de `project.md`).
Las nuevas van al final de su grupo.

- **Se mantienen** (cambian de forma): `InterviewSessionRecord` (perfil y huella en lugar de escenario y
  umbral; consentimiento y bloqueo), `SessionStatusChange` y `Turn` (hablante, página y estado plegado;
  sin estado de evaluación, que ahora se deriva de las corridas). Origen: cambio 01, C1 y components.
- **Salen** (`Retirado`): `Scenario`, `ScenarioVersion`, `ScenarioDocument`, `Passage`, `Claim`,
  `TurnEvaluation`, `ClaimEvaluation`, `HandoffPackage`, `ThresholdConfig` y `JudgePrompt`. Origen:
  cambio 01 (sale el marco documental, el umbral, el Hecho No Documentado y el paquete) y unit-of-work
  (el *prompt* y ModelGateway pasan a U11).
- **Pasan a citarse como entidades de HumanReview** (U5): `ReviewSuggestion` y `ReviewRound`. U4 crea
  sus tablas y la implementación de `SuggestionProposer.propose` (C10) porque B3 va antes que B5; las
  decisiones son de U5.
- **Entran:** `ConsentRecord` (VE-06, A-4), `AnalysisRun`, `RunAttempt` y `RunStatusChange` (corridas,
  FD-U3-10, P9 = A), `ModelCall` (US12.5), `DiscardedCandidate` (C6 `registro.descartes`),
  `AnonymizationIncident` (VE-14, P7 = A, P8 = A) y los mensajes `RunStarted` (P9 = A) y
  `CancellationKey` (CD-06).

**Insumos.**
- Unidad U4 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) y su mapa
  `unit-of-work-story-map.md` (unit-of-work-story-map), con las historias US2.1, US2.2, US3.1, US5.5,
  US5.6, US13.1, US15.4 y US15.5 y los cruces US3.2, US3.6, US3.7, US8.4, US12.5, US13.3, US15.2 y US15.7.
- FR3, FR4, FR14, FR15 y la adenda 02 (VE-01, VE-06, VE-10, VE-14) de
  `inception/requirements-analysis/requirements.md` (requirements) y `requirements-adenda-02.md`.
- Componentes InterviewSession, AnalysisWorker, HumanReview, ConsoleApi, IntegrityPolicy y AnalystConsole
  de `inception/domain-design/components.md` (components), con ADR-002, ADR-003, ADR-006 y ADR-013.
- Contratos C1, C2, C3, C6, C7, C8, C10, C11, C17, C18, C21, C24 y C25 de
  `inception/contract-design/contract-summary.md` (contract-summary, revisión 3), con CD-01, CD-02, CD-06
  y CD-11.
- Respuestas P6–P11 de la segunda pasada de `functional-design-questions.md`. P1–P4 de la primera pasada
  quedan retiradas y P5 (largo del turno) pasa al catálogo C25 y a NFR Requirements.
- Functional Design de U1 (F3, fixtures de C6), de U3 (FD-U3-04, FD-U3-07, FD-U3-08, FD-U3-10,
  FD-U3-13), de U10 (FD-U10-03, FD-U10-16) y de U11 (FD-U11-01 a FD-U11-20).

**Frontera AUTONOMIA-04.** Todas las entidades persistentes viven en PostgreSQL dentro del clúster; los
mensajes y la clave de cancelación viajan por Redis dentro del clúster. Ninguna entidad de esta unidad
sale del clúster. Lo único que cruza la frontera lo hace dentro de una llamada de U11 a través de
`anonymizer-proxy` (C21); U4 solo guarda su registro (`ModelCall`), que no tiene texto.

**Convención de auditoría (FD-U3-07).** Cada tabla declara en su comentario `veridicus-audit` con
`kind`, `purgeable` y `owner_unit`. Las `history` suman `actor_kind` (`person` | `system`) y
`actor_system`; el usuario `veridicus_app` no tiene `UPDATE` ni `DELETE` sobre ellas, y solo
`veridicus_retention` (U13) borra.

```yaml
entities:
  # Retiradas (cambio 01)
  - name: Scenario
    status: Retirado
    replaced_by: "ninguno (sale el marco documental)"
    description: "Escenario de control de la revisión 1. Sale con TruthFrame (cambio 01, DD-10)."
  - name: ScenarioVersion
    status: Retirado
    replaced_by: "ninguno"
    description: "Versión indexada de un escenario. Sale con TruthFrame."
  - name: ScenarioDocument
    status: Retirado
    replaced_by: "ninguno"
    description: "Documento de una versión (respuesta P3 de la primera pasada, retirada)."
  - name: Passage
    status: Retirado
    replaced_by: "ninguno"
    description: "Pasaje con embedding. Salen los embeddings (cambio 01)."
  - name: Claim
    status: Retirado
    replaced_by: "Hallazgo de C6 (U11)"
    description: "Afirmación por oración (P1 de la primera pasada, retirada)."
  - name: TurnEvaluation
    status: Retirado
    replaced_by: AnalysisRun
    description: "Evaluación de un intento de turno. La sustituye la corrida del contrato común."
  - name: ClaimEvaluation
    status: Retirado
    replaced_by: "ninguno (salen las tres calificaciones)"
    description: "Calificación por afirmación frente al marco de verdad."
  - name: HandoffPackage
    status: Retirado
    replaced_by: "ninguno (sale el Hecho No Documentado)"
    description: "Paquete de Contexto de Traspaso."
  - name: ThresholdConfig
    status: Retirado
    replaced_by: "ninguno (sale el umbral)"
    description: "Ajuste VERIDICUS_SIMILARITY_THRESHOLD."
  - name: JudgePrompt
    status: Retirado
    replaced_by: "prompt de la biblioteca de U11 (C17); la corrida guarda su prompt_sha256"
    description: "Prompt del juez montado por U4."

  # InterviewSession — sesión
  - name: InterviewSessionRecord
    status: cambia
    description: >
      Sesión guiada o importada, ligada para siempre a su perfil y a su configuración efectiva (ADR-006).
      audit: kind mutable, purgeable, owner_unit U4.
    attributes:
      - { name: session_id, type: uuid, required: true, unique: true }
      - { name: owner_user_id, type: reference, references: User, required: true }
      - { name: entrevista, type: text, required: true, constraints: "1 a 120 caracteres; identificador, nunca un nombre real" }
      - { name: origin, type: enum, required: true, allowed: [guiada, corpus, sintetico], description: "guiada al crear desde M3; corpus o sintetico al importar (U6)" }
      - { name: profile_name, type: text, required: true, description: "perfil aprobado de C18 al crear" }
      - { name: effective_config, type: json, required: true, description: "instantánea de effective-config.v1 (C18); nunca cambia" }
      - { name: config_sha256, type: hex64, required: true, description: "nunca cambia" }
      - { name: status, type: SessionStatus, required: true, allowed: [open, paused, suspended, finalized, terminated, blocked, consolidated] }
      - { name: closed_to_new_turns, type: boolean, required: true, default: false }
      - { name: blocked_code, type: ErrorCode, required: false, allowed: [anonymizer.incident], description: "una vez fijado no se borra (P7 = A)" }
      - { name: change_cursor, type: bigint, required: true, description: "sube en cada escritura que cambia la sesión (BR19.2)" }
      - { name: retention_days, type: integer, required: false, description: "vacío en U4; el campo y su validación llegan con U13" }
      - { name: retention_until, type: UtcTimestamp, required: false, description: "vacío en U4" }
      - { name: created_at, type: UtcTimestamp, required: true }
      - { name: finalized_at, type: UtcTimestamp, required: false }
      - { name: last_heartbeat_at, type: UtcTimestamp, required: false }
    constraints:
      - "profile_name, effective_config y config_sha256 no admiten UPDATE (disparador)."
      - "blocked_code solo pasa de nulo a anonymizer.incident (disparador)."
    relationships:
      - { to: ConsentRecord, cardinality: "1..1", direction: "InterviewSessionRecord -> ConsentRecord" }
      - { to: Turn, cardinality: "0..*", direction: "InterviewSessionRecord -> Turn" }
      - { to: AnalysisRun, cardinality: "0..*", direction: "InterviewSessionRecord -> AnalysisRun" }
      - { to: SessionStatusChange, cardinality: "1..*", direction: "InterviewSessionRecord -> SessionStatusChange" }
      - { to: AnonymizationIncident, cardinality: "0..*", direction: "InterviewSessionRecord -> AnonymizationIncident" }

  - name: ConsentRecord
    description: >
      Bloque consentimiento de C6 registrado al crear la sesión (VE-06, A-4). Sin datos personales:
      las constancias son identificadores. audit: kind mutable (solo la retirada, de U6), purgeable.
    attributes:
      - { name: consent_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true, unique: true }
      - { name: kind, type: enum, required: true, allowed: [persona, autoridad], description: "C6 tipo" }
      - { name: text_version, type: text, required: true, description: "C6 version_texto" }
      - { name: authorizes_commercial_transfer, type: boolean, required: true, description: "C6 autoriza_transferencia" }
      - { name: authorizes_voice, type: boolean, required: true, description: "C6 autoriza_voz" }
      - { name: authorizes_audio_retention, type: boolean, required: true, description: "C6 autoriza_conservar_audio" }
      - { name: authority_evidence, type: text, required: false, description: "C6 constancia; obligatoria si kind es autoridad" }
      - { name: requires_mandate, type: boolean, required: true, description: "C6 requiere_mandato" }
      - { name: mandate_evidence, type: text, required: false, description: "C6 constancia_mandato; obligatoria si requires_mandate" }
      - { name: recorded_by, type: reference, references: User, required: true }
      - { name: recorded_at, type: UtcTimestamp, required: true, description: "C6 registrado_en; lo fija el servidor" }
      - { name: withdrawn_at, type: UtcTimestamp, required: false, description: "lo escribe U6 (VE-10)" }
      - { name: withdrawn_by, type: reference, references: User, required: false }
    constraints:
      - "Ninguna columna cambia salvo withdrawn_at y withdrawn_by, y solo de nulo a un valor (disparador)."
      - "Las constancias cumplen ^[A-Za-z0-9._:-]{1,64}$: un identificador, nunca un nombre."

  - name: SessionStatusChange
    status: cambia
    description: "Historial de estados de la sesión. audit: kind history, purgeable."
    attributes:
      - { name: change_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: from_status, type: SessionStatus, required: false }
      - { name: to_status, type: SessionStatus, required: true }
      - { name: code, type: ErrorCode, required: false, description: "anonymizer.incident al bloquear" }
      - { name: actor_user_id, type: reference, references: User, required: false }
      - { name: actor_kind, type: enum, required: true, allowed: [person, system] }
      - { name: actor_system, type: ActorSystem, required: false, description: "analysis-worker al bloquear por la ingesta (FD-U3-08)" }
      - { name: at, type: UtcTimestamp, required: true }

  - name: Turn
    status: cambia
    description: >
      Turno de la transcripción (C1 Turn, C6 turnos). Inmutable: su estado en pantalla se deriva de las
      corridas (BR17.1). audit: kind history, purgeable.
    attributes:
      - { name: turn_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: n, type: integer, required: true, min: 1 }
      - { name: speaker, type: enum, required: true, allowed: [ENT, TEST], description: "C6 hablante" }
      - { name: text, type: text, required: true, constraints: "1 a turn_max_chars (C25) tras quitar espacios de los bordes" }
      - { name: page, type: integer, required: false, min: 1, description: "ausente en turnos guiados" }
      - { name: page_end, type: integer, required: false, min: 1 }
      - { name: fold_state, type: enum, required: true, allowed: [visible, plegado], default: visible }
      - { name: origin, type: enum, required: true, allowed: [typed, pasted, voice, imported] }
      - { name: client_request_id, type: uuid, required: false, description: "obligatorio en typed" }
      - { name: submitted_by, type: reference, references: User, required: true }
      - { name: submitted_at, type: UtcTimestamp, required: true }
    constraints:
      - "(session_id, n) único y sin huecos."
      - "(session_id, client_request_id) único cuando no es nulo."

  # InterviewSession — corridas
  - name: AnalysisRun
    description: >
      Una corrida del contrato común sobre un tramo de la sesión (C1 Run, C2). Solo datos de la petición,
      que no cambian; el estado vive en RunStatusChange y el resultado en RunAttempt (FD-U3-10).
      audit: kind history, purgeable.
    attributes:
      - { name: run_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: mode, type: enum, required: true, allowed: [incremental, final] }
      - { name: from_turn, type: integer, required: true, min: 1, description: "C6 desde_turno" }
      - { name: to_turn, type: integer, required: true, min: 1, description: "C6 hasta_turno" }
      - { name: profile_name, type: text, required: true, description: "copia de la sesión" }
      - { name: config_sha256, type: hex64, required: true, description: "copia de la sesión (AC2.1.2)" }
      - { name: requested_by, type: reference, references: User, required: true }
      - { name: requested_at, type: UtcTimestamp, required: true }
    constraints:
      - "from_turn <= to_turn; en incremental to_turn es un turno TEST."
    relationships:
      - { to: RunStatusChange, cardinality: "1..*", direction: "AnalysisRun -> RunStatusChange" }
      - { to: RunAttempt, cardinality: "0..*", direction: "AnalysisRun -> RunAttempt" }

  - name: RunStatusChange
    description: >
      Historial de estados de la corrida, con actor y hora. El estado vigente y el intento vigente son
      los de la última fila. audit: kind history, purgeable.
    attributes:
      - { name: change_id, type: uuid, required: true, unique: true }
      - { name: run_id, type: reference, references: AnalysisRun, required: true }
      - { name: attempt, type: integer, required: true, min: 1 }
      - { name: from_status, type: enum, required: false, allowed: [queued, processing, done, error, cancelled] }
      - { name: to_status, type: enum, required: true, allowed: [queued, processing, done, error, cancelled] }
      - { name: error_code, type: ErrorCode, required: false, description: "solo con to_status error" }
      - { name: deadline_at, type: UtcTimestamp, required: false, description: "solo con to_status queued (C25)" }
      - { name: actor_user_id, type: reference, references: User, required: false }
      - { name: actor_kind, type: enum, required: true, allowed: [person, system] }
      - { name: actor_system, type: ActorSystem, required: false, allowed: [analysis-worker, run-supervisor] }
      - { name: at, type: UtcTimestamp, required: true }
    constraints:
      - "(run_id, attempt, to_status) único: una transición por intento."

  - name: RunAttempt
    description: >
      Resultado de un intento ingerido (C3 salida). Una fila por (run_id, attempt) con resultado; los
      intentos descartados no dejan fila. audit: kind history, purgeable.
    attributes:
      - { name: run_id, type: reference, references: AnalysisRun, required: true }
      - { name: attempt, type: integer, required: true, min: 1 }
      - { name: outcome, type: enum, required: true, allowed: [ok, error] }
      - { name: error_code, type: ErrorCode, required: false }
      - { name: prompt_sha256, type: hex64, required: false, description: "C6 prompt_sha256; ausente si la salida no cumplió C6" }
      - { name: analyzer_version, type: text, required: false, description: "C6 version" }
      - { name: fragmented, type: boolean, required: false, description: "C6 registro.fragmentado.activo" }
      - { name: window, type: integer, required: false }
      - { name: overlap, type: integer, required: false }
      - { name: anonymized, type: boolean, required: false, description: "true si todas las llamadas externas pasaron por el anonimizador; nulo si no hubo ninguna externa (BR16.3)" }
      - { name: tokens_in, type: integer, required: false, min: 0 }
      - { name: tokens_out, type: integer, required: false, min: 0 }
      - { name: estimated_cost, type: decimal, required: false, min: 0 }
      - { name: price_table, type: text, required: false, description: "C6 tabla_precios" }
      - { name: message_id, type: uuid, required: true, description: "C3 message_id" }
      - { name: finished_at, type: UtcTimestamp, required: true }
    constraints:
      - "(run_id, attempt) único: la ingesta es idempotente (AC2.2.4)."

  - name: ModelCall
    description: >
      Una fila de registro.llamadas de C6, copiada tal cual (C1 ModelCall). Sin texto enviado ni recibido.
      audit: kind history, purgeable, actor analysis-worker.
    attributes:
      - { name: call_id, type: uuid, required: true, unique: true }
      - { name: run_id, type: reference, references: AnalysisRun, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: role, type: enum, required: true, allowed: [juez, verificador, verificador_permutado], description: "C6 papel" }
      - { name: provider, type: text, required: true }
      - { name: model, type: text, required: true }
      - { name: version, type: text, required: false }
      - { name: effort_or_quantization, type: text, required: false }
      - { name: engine, type: text, required: false }
      - { name: seed, type: integer, required: false }
      - { name: tokens_in, type: integer, required: true, min: 0 }
      - { name: tokens_out, type: integer, required: true, min: 0 }
      - { name: used_fallback, type: boolean, required: true, description: "C6 proveedor_alterno" }
      - { name: external, type: boolean, required: true, description: "derivado de effective_config para ese papel: commercial" }
      - { name: anonymized, type: boolean, required: true, description: "C6 anonimizado" }
      - { name: at, type: UtcTimestamp, required: true, description: "C6 fecha" }

  - name: DiscardedCandidate
    description: "Una fila de registro.descartes de C6: motivo y turnos, sin texto de citas. audit: kind history, purgeable."
    attributes:
      - { name: run_id, type: reference, references: AnalysisRun, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: reason, type: enum, required: true, allowed: [cita_no_verificada, cita_en_otro_turno, marca_alterada, campo_faltante, rechazado_verificador, rechazado_permutacion, fuera_de_tramo, vocabulario_prohibido] }
      - { name: turn_a, type: text, required: false, constraints: "^T[0-9]+$" }
      - { name: turn_b, type: text, required: false, constraints: "^T[0-9]+$" }

  - name: AnonymizationIncident
    description: >
      Incidente de VE-14: una llamada a un destino externo sin anonimizar, o error.codigo
      incidente_anonimizacion. Solo IDs (ADR-013). audit: kind history; sobrevive a la retención sin
      clave foránea, como RetentionAct (propuesta FD-U4-12).
    attributes:
      - { name: incident_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: uuid, required: true, description: "sin clave foránea" }
      - { name: run_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true }
      - { name: call_id, type: uuid, required: false, description: "la llamada con anonimizado false, si la hay" }
      - { name: code, type: enum, required: true, allowed: [incidente_anonimizacion, llamada_externa_sin_anonimizar] }
      - { name: detected_at, type: UtcTimestamp, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [system] }
      - { name: actor_system, type: ActorSystem, required: true, allowed: [analysis-worker] }

  # HumanReview — tablas que crea U4 (dueño del dominio: U5)
  - name: ReviewSuggestion
    status: cambia
    description: >
      Hallazgo de C6 guardado como sugerencia de revisión (C7, C10). Nace pendiente. Entidad de
      HumanReview; U4 crea la tabla y propose. audit: kind history, purgeable, owner_unit U5.
    attributes:
      - { name: suggestion_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: first_run_id, type: reference, references: AnalysisRun, required: true }
      - { name: hecho, type: text, required: true, constraints: "no vacío ni solo espacios" }
      - { name: tipo, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      - { name: cita_a, type: json, required: true, description: "C6 cita: cita, turno, pagina, avisos" }
      - { name: cita_b, type: json, required: true }
      - { name: observaciones, type: text, required: true, constraints: "no vacío ni solo espacios" }
      - { name: actos, type: list, required: false }
      - { name: pair_key, type: hex64, required: true, description: "SHA-256 del par no ordenado (turno, cita normalizada en espacios)" }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "(session_id, pair_key) único (AC3.6.3)."
      - "Sin campos de veracidad ni puntaje (AC5.5.3)."

  - name: ReviewRound
    status: cambia
    description: "Ronda de revisión (ADR-007). propose abre la ronda 1. Entidad de HumanReview."
    attributes:
      - { name: round_id, type: uuid, required: true, unique: true }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: number, type: integer, required: true, min: 1 }
      - { name: status, type: enum, required: true, allowed: [open, locked] }
      - { name: opened_at, type: UtcTimestamp, required: true }

  # Mensajes y claves (no persisten en PostgreSQL)
  - name: RunStarted
    description: >
      Mensaje que AnalysisWorker publica en veridicus:results al tomar una corrida (P9 = A, cambio menor
      de C3, FD-U4-02).
    attributes:
      - { name: schema_version, type: text, required: true, constraints: "^2\\.[0-9]+\\.[0-9]+$" }
      - { name: kind, type: enum, required: true, allowed: [run_started] }
      - { name: message_id, type: uuid, required: true }
      - { name: run_id, type: uuid, required: true }
      - { name: attempt, type: integer, required: true, min: 1 }
      - { name: started_at, type: UtcTimestamp, required: true }

  - name: CancellationKey
    description: "Clave de Redis veridicus:run-cancelled:{run_id} (C2, CD-06); la escribe InterviewSession y el trabajador solo la lee."
    attributes:
      - { name: run_id, type: uuid, required: true }
      - { name: expires_at, type: UtcTimestamp, required: true, description: "deadline_at + cancel_key_margin_s (C25)" }
```

## Resumen

- **InterviewSession:** la sesión queda ligada a su perfil, su configuración efectiva y su huella, y a un
  único `ConsentRecord`. Los turnos son inmutables, con hablante y, si vienen del corpus, página y estado
  plegado. El bloqueo por incidente se guarda en `blocked_code`, que nunca se borra.
- **Corridas:** `AnalysisRun` guarda lo que se pidió; `RunStatusChange` guarda cada cambio de estado con
  su actor; `RunAttempt`, `ModelCall` y `DiscardedCandidate` guardan lo que devolvió cada intento
  ingerido. Así ninguna fila de corridas ni del registro de modelos necesita `UPDATE` (AC8.4.2).
- **HumanReview:** U4 crea `ReviewSuggestion` y `ReviewRound` por C10; las decisiones son de U5.
- **Salen** el marco documental, el umbral, las calificaciones y el paquete de traspaso (cambio 01).
