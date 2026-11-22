# Entidades — U13 ethics-governance

**Revisión 1 (2026-11-22), primera pasada.** Es una unidad nueva del cambio 01 (DT27) y de la adenda 02, y
no tiene artefactos previos. Se basa en las respuestas P1 = B, P2 = A, P3 = A, P4 = A, P5 = A, P6 = A y
P7 = A de `functional-design-questions.md` y en los once puntos de su sección 2.

**Insumos.**
- La unidad U13 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3), con UG-01,
  UG-04 y UG-09. Sus historias en `unit-of-work-story-map.md` (unit-of-work-story-map): US15.1, US15.3,
  US15.6, US15.7 y US15.9, y las que cumple con otras unidades, US15.8, US5.6 y US8.4.
- FR1.2, FR1.3, NFR10 y NFR11 de `inception/requirements-analysis/requirements.md` (requirements,
  revisión 3). VE-04, VE-11, VE-12, VE-15, VE-16 y A-2 de `requirements-adenda-02.md`.
- EthicsGovernance, ConsoleApi e InterviewSession de `inception/domain-design/components.md`
  (components, revisión 3), con ADR-003, ADR-009, ADR-016 y DD-01 a DD-05.
- C1, C8, C23, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary,
  revisión 3).
- Mockups §11 de `inception/refined-mockups/mockups.md` y su precisión de la revisión 3 sobre el diálogo
  después de M0. B13 de `inception/delivery-planning/bolt-plan.md`.
- Los diseños de U3 (convención de auditoría, usuario `veridicus_retention`, actor `retention-job`, F11 del
  registro de acceso), U4 (`retention_days` y `retention_until` vacíos, `purge_session`), U5, U6, U7, U8 y
  U9 (sus partes del borrado).

**Frontera AUTONOMIA-04.** Todo corre dentro del clúster. Del lado del servidor están el módulo
EthicsGovernance de `session-api`, sus tablas en PostgreSQL, el `Job` de retención (la misma imagen, con el
usuario `veridicus_retention`) y el comando de consulta. Del lado del navegador del analista están los
diálogos y los avisos. Ningún dato de esta unidad sale del clúster. El único texto libre que guarda U13 es
la nota de un `ProblemReport`, que puede traer testimonio. La nota nunca va a los logs y la retención la
borra (BR3.9, BR5.5, BR5.8).

## Modelo de entidades (fuente de verdad)

```yaml
entities:
  - name: UsageRulesText
    description: >
      Texto versionado de las reglas de uso que el analista reconoce (VE-04, DT23). No es una tabla: es
      un archivo de IntegrityPolicy, junto al aviso de VE-01, que solo cambia por PR (FD-U13-02).
      ConsoleApi lo sirve con su versión.
    storage: { kind: versioned_file, source: "contracts/integrity/usage-rules.v1.yaml (U1, C8)" }
    attributes:
      - { name: version, type: text, required: true, constraints: "^[0-9]+\\.[0-9]+\\.[0-9]+$; cambiarla obliga a reconocer de nuevo (AC15.1.4)" }
      - { name: points, type: list, required: true, min: 3, max: 3, description: "los tres puntos de AC15.1.1, en este orden: «Los hallazgos no son prueba», «Una contradicción puede venir del trauma», «No se confronta a la persona con sus contradicciones»" }
    constraints:
      - "Una prueba de nivel 0 falla si el archivo no tiene exactamente los tres puntos de AC15.1.1."
      - "El texto pasa por el escaneo de vocabulario de la interfaz y está excluido como notice_text, igual que el aviso de VE-01, porque contiene «prueba» (AC5.5.6)."
      - "Si falta el archivo o no es válido, session-api no arranca (configuración faltante)."

  - name: AnalystAcknowledgement
    description: >
      Un reconocimiento de las reglas de uso por un analista. Es de solo inserción. La vigencia no se
      guarda: se calcula (AcknowledgementState).
    storage: { kind: history, purgeable: false, owner_unit: U13, actor_columns: { actor_user_id: actor_user_id, at: at } }
    attributes:
      - { name: acknowledgement_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: actor_user_id, type: reference, references: User, required: true, description: "el analista que reconoce (FR1.3)" }
      - { name: text_version, type: text, required: true, constraints: "igual a UsageRulesText.version vigente al registrar (BR1.3)" }
      - { name: at, type: UtcTimestamp, required: true, description: "la pone el servidor" }
      - { name: actor_kind, type: enum, required: true, allowed: [person], default: person }
      - { name: actor_system, type: text, required: false, description: "siempre nulo" }
    constraints:
      - "Sin UPDATE ni DELETE para ningún usuario de base de datos, tampoco para veridicus_retention (no es purgable)."
      - "El actor y la hora no son nulos (AC8.4.1)."
    relationships:
      - { to: User, cardinality: "N..1", direction: "AnalystAcknowledgement -> User (owned_by IdentityAccess)" }

  - name: AcknowledgementState
    description: >
      Estado calculado del reconocimiento de un usuario. Es un valor sin almacenamiento que viaja como
      AcknowledgementStatus en GET /auth/me (C1).
    storage: { kind: value }
    attributes:
      - { name: status, type: enum, required: true, allowed: [valid, missing, expired, text_changed] }
      - { name: text_version, type: text, required: false, description: "la versión del último reconocimiento; nula con missing" }
      - { name: at, type: UtcTimestamp, required: false, description: "la hora del último reconocimiento; nula con missing" }
      - { name: current_text_version, type: text, required: true, description: "la versión vigente de UsageRulesText (FD-U13-04)" }
    constraints:
      - "Se calcula con el último AnalystAcknowledgement del usuario y con el reloj inyectado (BR1.2)."
      - "Solo los usuarios analista tienen estado; para admin e investigador el campo no viaja (BR1.7)."

  - name: AccessLogEntry
    description: >
      Una lectura o una exportación registrada por el puerto AccessLog (C23). Es de solo inserción y no
      tiene texto. Sobrevive a la retención y guarda los IDs sin clave foránea.
    storage: { kind: history, purgeable: false, owner_unit: U13, actor_columns: { actor_user_id: actor_user_id, at: at } }
    attributes:
      - { name: entry_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: actor_user_id, type: uuid, required: true, description: "ID del usuario; sin clave foránea, para no acoplar el registro al ciclo de vida de User" }
      - { name: resource_type, type: enum, required: true, allowed: [session, suggestion, report_version, report_export] }
      - { name: resource_id, type: uuid, required: true, description: "sin clave foránea (sobrevive a la retención)" }
      - { name: export_sha256, type: text, required: false, constraints: "^[a-f0-9]{64}$; obligatorio si resource_type es report_export y nulo en los demás (A-3)" }
      - { name: at, type: UtcTimestamp, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [person], default: person }
      - { name: actor_system, type: text, required: false, description: "siempre nulo" }
    constraints:
      - "No tiene ninguna columna de texto libre (VE-11, NFR10)."
      - "El usuario de la aplicación no puede hacer UPDATE ni DELETE (AC15.6.2), y veridicus_retention tampoco puede borrar (no es purgable)."
      - "Una restricción CHECK une export_sha256 con resource_type report_export."

  - name: ProblemReport
    description: >
      Un problema reportado desde la consola (VE-15). Puede referirse a una sesión, a un hallazgo de esa
      sesión o a ninguna sesión (P6 = A). Su nota puede traer testimonio, así que se borra con la sesión
      o, si no tiene sesión, al cumplir el máximo de retención.
    storage: { kind: mutable, purgeable: true, owner_unit: U13, app_permissions: [SELECT, INSERT] }
    attributes:
      - { name: problem_report_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: category, type: enum, required: true, allowed: [harmful_finding, improper_vocabulary, mismatched_quote, interviewee_distress, anonymization_failure, misuse], description: "los seis rótulos de AC15.3.1, en ese orden" }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: false, description: "nulo solo en un reporte sin sesión (P6 = A); si viene suggestion_id, se deriva de la sugerencia (UG-01)" }
      - { name: suggestion_id, type: reference, references: ReviewSuggestion, required: false }
      - { name: note, type: text, required: false, max: "problem_report_note_max_chars de C25", description: "opcional (AC15.3.1, FD-U13-06); nunca va a los logs" }
      - { name: testimony_warning, type: boolean, required: true, default: false, description: "verdadero si la nota trae testimony_warning_words o más palabras seguidas de un turno de la sesión (BR3.6)" }
      - { name: reported_by, type: reference, references: User, required: true }
      - { name: reported_at, type: UtcTimestamp, required: true }
    constraints:
      - "Si suggestion_id no es nulo, session_id no es nulo y es la sesión de esa sugerencia (BR3.4)."
      - "Sin sesión, testimony_warning es siempre falso, porque no hay turnos con qué comparar (BR3.8)."
      - "Ninguna ruta lo modifica ni lo borra; solo veridicus_retention lo borra (BR5.5, BR5.8)."
    relationships:
      - { to: InterviewSessionRecord, cardinality: "N..0..1", direction: "ProblemReport -> InterviewSessionRecord (owned_by InterviewSession)" }
      - { to: ReviewSuggestion, cardinality: "N..0..1", direction: "ProblemReport -> ReviewSuggestion (owned_by HumanReview)" }
      - { to: User, cardinality: "N..1", direction: "ProblemReport -> User (owned_by IdentityAccess)" }

  - name: RetentionTerm
    description: >
      El plazo de retención de una sesión. No es una tabla de U13: son las columnas retention_days y
      retention_until de InterviewSessionRecord, que creó U4. EthicsGovernance decide los valores, y
      InterviewSession los guarda por el puerto EthicsSessionPort (FD-U13-08).
    storage: { kind: columns_of, table: InterviewSessionRecord, owner_unit: U4 }
    attributes:
      - { name: retention_days, type: integer, required: false, min: "retention_min_days de C25 (1)", max: "retention_max_days de C25 (90)", description: "nulo solo en sesiones creadas antes de U13 (BR4.5)" }
      - { name: retention_until, type: UtcTimestamp, required: false, description: "creación + retention_days × 24 h (P3 = A); se recalcula al reducir" }
    constraints:
      - "retention_until solo puede bajar; nunca sube (BR4.4)."
      - "Un plazo vacío se lee como creación + retention_max_days, sin escribirlo (P2 = A, BR4.5)."

  - name: RetentionChange
    description: >
      Una reducción del plazo de una sesión, con quién y cuándo (AC15.7.3, P4 = A). Es de solo
      inserción. Se borra con la sesión, porque solo tiene sentido mientras la sesión existe.
    storage: { kind: history, purgeable: true, owner_unit: U13, actor_columns: { actor_user_id: actor_user_id, at: at } }
    attributes:
      - { name: change_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: from_days, type: integer, required: false, description: "nulo si la sesión tenía el plazo vacío" }
      - { name: to_days, type: integer, required: true, constraints: "menor que el plazo efectivo anterior" }
      - { name: from_until, type: UtcTimestamp, required: true, description: "el plazo efectivo anterior" }
      - { name: to_until, type: UtcTimestamp, required: true }
      - { name: actor_user_id, type: reference, references: User, required: true, description: "el dueño o un admin (BR4.4)" }
      - { name: at, type: UtcTimestamp, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [person], default: person }
      - { name: actor_system, type: text, required: false, description: "siempre nulo" }
    constraints:
      - "to_until < from_until."
      - "Sin UPDATE ni DELETE para el usuario de la aplicación; veridicus_retention la borra en el paso 1 del Job (BR5.5)."
    relationships:
      - { to: InterviewSessionRecord, cardinality: "N..1", direction: "RetentionChange -> InterviewSessionRecord (owned_by InterviewSession)" }

  - name: RetentionAct
    description: >
      El acta de un borrado de retención (VE-12, A-2). Hay una por sesión borrada y una por cada tanda de
      reportes de problemas sin sesión (P6 = A). Es de solo inserción, sin texto. Sobrevive a la
      retención y guarda los IDs sin clave foránea.
    storage: { kind: history, purgeable: false, owner_unit: U13, actor_columns: { actor_user_id: null, at: executed_at }, actor_system: retention-job }
    attributes:
      - { name: act_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: job_run_id, type: uuid, required: true, description: "agrupa las actas de una misma ejecución del Job" }
      - { name: deleted_session_id, type: uuid, required: false, description: "sin clave foránea; nulo en el acta de reportes sin sesión (FD-U13-07)" }
      - { name: rule, type: enum, required: true, allowed: [session_term_expired, session_default_term_expired, sessionless_problem_report_expired], description: "por qué regla se borró (BR5.7)" }
      - { name: retention_days, type: integer, required: true, description: "el plazo aplicado: el de la sesión, o retention_max_days si el plazo estaba vacío o no hay sesión" }
      - { name: retention_until, type: UtcTimestamp, required: true, description: "el vencimiento aplicado" }
      - { name: deleted_ids, type: map, required: true, description: "por tabla, la lista de IDs borrados; viene de los PurgeReceipt (C24) y de las tablas propias" }
      - { name: deleted_report_sha256s, type: list, required: true, description: "por cada ReportVersion borrada, report_version_id, sha256 y file_missing" }
      - { name: deleted_audio, type: list, required: true, description: "por cada TurnAudio borrado, audio_id, sha256 y file_missing; vacía si no había audio" }
      - { name: executed_at, type: UtcTimestamp, required: true, description: "hora real del borrado (BR5.3)" }
      - { name: actor_kind, type: enum, required: true, allowed: [system], default: system }
      - { name: actor_system, type: text, required: true, constraints: "retention-job" }
    constraints:
      - "Solo veridicus_retention hace INSERT; nadie hace UPDATE ni DELETE (A-2)."
      - "No tiene texto: solo IDs, hashes, números, la regla y las horas."
      - "deleted_session_id nulo ⇔ rule sessionless_problem_report_expired."

  - name: RetentionJobRun
    description: >
      Una ejecución del Job de retención. Es un valor sin almacenamiento: queda en la salida del Job y en
      sus actas por job_run_id.
    storage: { kind: value }
    attributes:
      - { name: job_run_id, type: uuid, required: true }
      - { name: mode, type: enum, required: true, allowed: [purge, dry_run] }
      - { name: as_of, type: UtcTimestamp, required: true, description: "en purge, siempre el reloj real; en dry_run, el --as-of o el reloj real (BR5.3)" }
      - { name: outcomes, type: list, required: true, description: "por sesión o tanda: ID, regla, conteos por tabla y estado purged, would_purge o failed con su code" }
      - { name: exit_code, type: integer, required: true, description: "0 si no hubo ningún failed; 1 si hubo alguno; 2 si los argumentos no valen" }

  - name: RetentionCandidate
    description: Una sesión o una tanda de reportes sin sesión que vence en as_of. Es un valor que arma el Job.
    storage: { kind: value }
    attributes:
      - { name: session_id, type: uuid, required: false, description: "nulo en la tanda de reportes sin sesión" }
      - { name: effective_days, type: integer, required: true }
      - { name: effective_until, type: UtcTimestamp, required: true }
      - { name: rule, type: enum, required: true, allowed: [session_term_expired, session_default_term_expired, sessionless_problem_report_expired] }

  - name: AccessQuery
    description: >
      Una consulta del comando de solo lectura (P7 = A). Es un valor y no se guarda. Lista accesos,
      reportes de problemas o actas en texto o en JSON.
    storage: { kind: value }
    attributes:
      - { name: subject, type: enum, required: true, allowed: [access_log, problem_reports, retention_acts] }
      - { name: session_id, type: uuid, required: false }
      - { name: user_id, type: uuid, required: false }
      - { name: since, type: UtcTimestamp, required: false }
      - { name: format, type: enum, required: true, allowed: [text, json], default: text }
```

## Resumen

| Entidad | Almacenamiento | Purgable | Qué guarda |
|---|---|---|---|
| UsageRulesText | Archivo versionado (C8) | — | Los tres puntos de las reglas de uso y su versión |
| AnalystAcknowledgement | `history` | No | Quién reconoció, cuándo y qué versión |
| AcknowledgementState | Valor | — | `valid`, `missing`, `expired` o `text_changed`, calculado |
| AccessLogEntry | `history` | No | Usuario, tipo y ID de recurso, hora y `export_sha256`; sin texto ni claves foráneas |
| ProblemReport | `mutable` (solo `INSERT` para la aplicación) | Sí | Categoría, IDs, nota opcional y `testimony_warning` |
| RetentionTerm | Columnas de `InterviewSessionRecord` (U4) | Con la sesión | Plazo en días y su vencimiento |
| RetentionChange | `history` | Sí | Cada reducción del plazo, con quién y cuándo |
| RetentionAct | `history` | No | El acta de cada borrado: IDs, SHA-256, regla y horas |
| RetentionJobRun, RetentionCandidate, AccessQuery | Valores | — | Una ejecución del Job, lo que vence y una consulta del comando |

U13 es dueña de cinco tablas: `AnalystAcknowledgement`, `AccessLogEntry`, `ProblemReport`, `RetentionChange` y
`RetentionAct`. Las cuatro de solo inserción siguen la convención de auditoría (ADR-003). El plazo vive en
la tabla de U4, y U13 lo cambia por un puerto, sin escribir en tablas ajenas. De una sesión borrada solo
quedan `AccessLogEntry`, `RetentionAct` y el incidente de anonimización de U4, todos sin clave foránea.
