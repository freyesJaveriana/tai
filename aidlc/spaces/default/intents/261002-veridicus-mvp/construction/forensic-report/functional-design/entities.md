# Entidades — U7 forensic-report (componente ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 y la adenda 02** (y las revisiones 3 de
Inception). Sustituye a la revisión 1 del 2026-10-03. El módulo se llama **ReviewReport** (antes
ForensicReport) y el producto habla de «reporte de revisión» (`review_report`, VE-03); el directorio
conserva el slug `forensic-report` (UG-08).
- **Sigue:** ReportVersion (con cambios), ReportFile, ReportContent (con cambios), ConsolidationBlocker (con
  cambios) y MttvSample (con cambios).
- **Sale (`status: Retirado`, sin renumerar):** los atributos `scenario_version_id`, `scenario_sha256` y
  `similarity_threshold` de ReportVersion; `undocumented_facts` de ReportContent; las referencias a
  ScenarioVersion y HandoffPackage. Motivo: cambio 01 (DT27), que retira el marco de verdad, el umbral de
  similitud y el Hecho No Documentado con su Paquete de Contexto de Traspaso (DD-10).
- **Entra (`status: nuevo`):** ReportExport (tabla de solo inserción), ExportWatermark y PurgeReceipt
  (valores sin tabla) y la interfaz del puerto `AccessLog` que define U7 (C23).

**Insumos.**
- Unidad U7 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3: `service`, MUST, L)
  y su mapa `unit-of-work-story-map.md` (unit-of-work-story-map): US2.4 → US6.1 → US6.2 → US15.8 → US6.3,
  con los cruces de US5.4, US5.5, US5.6, US8.4, US3.7, US15.5 y US15.7.
- FR1 (tabla de roles), FR3.5, FR7.1–FR7.5 y NFR7 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3), y VE-01, VE-02, VE-12, VE-13 con las precisiones A-1, A-2 y A-3 de
  `requirements-adenda-02.md`.
- ReviewReport, InterviewSession, HumanReview, IntegrityPolicy, EthicsGovernance y ConsoleApi de
  `inception/domain-design/components.md` (components, revisión 3).
- C1, C11, C23 y C24 de `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- Respuestas P1–P4 (primera pasada; P4 superada) y P5–P8 de `functional-design-questions.md`.

## Entidades (fuente de verdad)

```yaml
entities:
  - name: ReportVersion
    owner: ReviewReport
    status: cambia
    description: >
      Versión inmutable y consolidada del reporte de revisión de una sesión. Cada consolidación (la primera
      o la de una corrección) crea una fila nueva; el usuario de la aplicación nunca la actualiza ni la
      borra (ADR-003, FR7.5). Solo el usuario de base del Job de retención la borra (A-2, C24).
    attributes:
      - { name: report_version_id, type: uuid, required: true, unique: true, description: "se genera antes de escribir el archivo; nombra el archivo (BR4.1)" }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: round_id, type: reference, references: ReviewRound, required: true, unique: true, description: "la ronda que esta versión bloquea; una ronda bloquea una sola versión" }
      - { name: version_number, type: integer, required: true, min: 1, description: "1 para la consolidación inicial; +1 por cada corrección consolidada" }
      - { name: supersedes_version_id, type: reference, references: ReportVersion, required: false, description: "obligatorio si version_number > 1; es la versión vigente de la que partió la corrección" }
      - { name: sha256, type: string, required: true, constraints: ["64 caracteres hexadecimales en minúscula", "calculado sobre los bytes exactos del archivo guardado"] }
      - { name: storage_path, type: string, required: true, unique: true, description: "ruta relativa dentro del volumen; derivada del report_version_id, nunca de datos del caso" }
      - { name: byte_size, type: integer, required: true, min: 1 }
      - { name: scenario_version_id, status: Retirado, description: "Sale con el marco de verdad (cambio 01, DD-10)" }
      - { name: scenario_sha256, status: Retirado, description: "Sale con el marco de verdad (cambio 01, DD-10)" }
      - { name: similarity_threshold, status: Retirado, description: "Sale con el umbral de similitud (cambio 01)" }
      - { name: format_version, type: string, required: true, default: "2", status: cambia, description: "versión de la plantilla canónica del Markdown (BR3.2); la 2 trae el contenido de FR7.2 y las secciones de BR11.2; las versiones de formato 1 ya guardadas no se tocan" }
      - { name: notice_version, type: string, required: true, status: nuevo, description: "versión del texto del aviso de VE-01 que lleva el archivo (C1 ReportVersion.notice_version)" }
      - { name: consolidated_by, type: reference, references: User, required: true }
      - { name: consolidated_at, type: UtcTimestamp, required: true }
    constraints:
      - "(session_id, version_number) único: de dos consolidaciones simultáneas solo una puede crear la versión N (AC6.1.6)."
      - "version_number = 1 si y solo si supersedes_version_id es nulo."
      - "supersedes_version_id pertenece a la misma sesión y tiene version_number - 1."
      - "Solo inserción: el usuario de la aplicación no tiene UPDATE ni DELETE; actor u hora nulos hacen fallar el INSERT (AC8.4.1, AC8.4.2)."
      - "Nunca existe una fila sin su archivo (BR4.1)."
      - "Ningún atributo describe la veracidad del compareciente ni una calificación frente a un marco de verdad."
    relationships:
      - { to: InterviewSessionRecord, cardinality: "N:1", direction: "ReportVersion → sesión" }
      - { to: ReviewRound, cardinality: "1:1", direction: "ReportVersion → ronda que bloquea" }
      - { to: ReportVersion, cardinality: "0..1:1", direction: "versión nueva → versión que reemplaza" }
      - { to: User, cardinality: "N:1", direction: "consolidada por" }
      - { to: ScenarioVersion, status: Retirado, description: "Sale con el marco de verdad (cambio 01)" }

  - name: ReportFile
    owner: ReviewReport
    status: sigue
    description: >
      Archivo Markdown del reporte en el volumen persistente del clúster. La fila ReportVersion solo lo
      describe. Las exportaciones se arman a partir de él y no lo modifican.
    attributes:
      - { name: storage_path, type: string, required: true, unique: true, description: "nombre final = report_version_id + extensión .md" }
      - { name: content, type: bytes, required: true, constraints: ["UTF-8 en forma NFC, saltos de línea LF, termina en un salto de línea"] }
      - { name: state, type: enum, required: true, allowed: [temporary, final], description: "temporary mientras se escribe; final tras forzar a disco y enlazar al nombre final" }
    constraints:
      - "Un archivo final sin fila ReportVersion es un huérfano y lo elimina la limpieza inmediata o el barrido con margen (BR4.3)."
      - "Un archivo final nunca se reescribe; solo lo borra la retención (BR10.1)."
    relationships:
      - { to: ReportVersion, cardinality: "1:0..1", direction: "archivo → versión que lo registra" }

  - name: ReportContent
    owner: ReviewReport
    kind: value-object
    status: cambia
    description: >
      Contenido lógico del reporte antes de renderizarlo (no se guarda aparte; vive en el archivo). Sigue
      FR7.2 de la revisión 3 de requirements.
    attributes:
      - { name: header, type: object, required: true, status: cambia, description: "entrevista, sesión, origen (guiada, corpus o sintético), dueño, número de versión, versión que reemplaza, perfil, config_sha256 y aviso de VE-01" }
      - { name: transcript, type: list, required: true, status: cambia, description: "todos los turnos en orden de número, con hablante, página inicial y final y estado plegado; los tramos incrementales en error se rotulan «Tramo no evaluado» con su code" }
      - { name: suggestions, type: list, required: true, status: cambia, description: "todas las sugerencias de revisión con estado final y nota; por cada una hecho, tipo, cita_a y cita_b con turno y página, avisos de la verificación y observaciones; si fue editada, el bloque de la IA y el bloque «Reformulación del analista» con quién y cuándo (P3 = A); «Sin sugerencias de revisión» si no hay" }
      - { name: runs, type: list, required: true, status: nuevo, description: "por cada corrida: perfil, config_sha256, prompt_sha256, versión del analizador, registro de modelos y modo fragmentado con ventana y solapamiento si se usó" }
      - { name: session_notices, type: list, required: true, status: nuevo, description: "avisos de la sesión que aplican: modo fragmentado, misma familia, «Modo final no completado. Revisión manual requerida» con su code, incidente de anonimización, sesión terminada y retirada del consentimiento con su hora (BR11.3)" }
      - { name: consolidation, type: object, required: true, status: nuevo, description: "quién consolidó y cuándo (hora de Colombia y UTC)" }
      - { name: undocumented_facts, status: Retirado, description: "Sale con el Hecho No Documentado y su Paquete de Contexto de Traspaso (cambio 01)" }
      - { name: scan_exclusions, type: list, required: true, status: cambia, description: "tramos que el escaneo no mira: los textos de todos los turnos (literal_sources, que cubren las dos citas), notas, reformulaciones y la cadena versionada del aviso (BR3.3, A-1)" }

  - name: ConsolidationBlocker
    owner: ReviewReport
    kind: value-object
    status: cambia
    description: Motivo por el que una sesión todavía no se puede consolidar; lo muestran la API y la consola.
    attributes:
      - { name: code, type: enum, required: true, status: cambia, allowed: [report.session_not_finalized, report.final_mode_not_launched, report.runs_in_progress, report.pending_suggestions], description: "en este orden (BR2.5); report.final_mode_not_launched es code nuevo (FD-U7-04) y report.runs_in_progress sustituye al report.turns_in_progress de la revisión 1 (C1)" }
      - { name: count, type: integer, required: false, min: 1, description: "corridas en proceso o sugerencias pendientes" }
      - { name: first_target_id, type: uuid, required: false, description: "primera sugerencia pendiente, para el enlace (AC6.1.1, AC2.4.4)" }

  - name: MttvSample
    owner: ReviewReport
    kind: derived
    status: cambia
    description: Medición de MTTV de una sesión guiada, calculada con marcas guardadas; no se almacena (NFR7).
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: finalized_at, type: UtcTimestamp, required: true }
      - { name: first_consolidated_at, type: UtcTimestamp, required: true, description: "consolidated_at de la versión 1; las correcciones no cuentan" }
      - { name: seconds, type: integer, required: true, min: 0 }
    constraints:
      - "Solo sesiones de origen guiada: las importadas (corpus o sintético) se finalizan al consolidar y no tienen momento de finalizar (P7 = A, BR7.1)."

  - name: ReportExport
    owner: ReviewReport
    status: nuevo
    description: >
      Registro de cada exportación del reporte con marca de agua (VE-13, A-3). Cada exportación es un
      artefacto propio; aquí se guarda solo su hash, nunca el archivo exportado (VE-12, BR9.5).
    attributes:
      - { name: export_id, type: uuid, required: true, unique: true }
      - { name: report_version_id, type: reference, references: ReportVersion, required: true }
      - { name: exported_by, type: reference, references: User, required: true }
      - { name: exported_at, type: UtcTimestamp, required: true }
      - { name: export_sha256, type: string, required: true, constraints: ["64 caracteres hexadecimales en minúscula", "SHA-256 de los bytes exactos enviados"] }
      - { name: was_current, type: boolean, required: true, description: "si la versión era la vigente al exportar; si no, la cabecera llevó el rótulo de reemplazo (P8 = A)" }
    constraints:
      - "Solo inserción con actor y hora no nulos (convención de auditoría de U3, AC8.4.1, AC8.4.2)."
      - "exported_by es el dueño de la sesión con rol analista o un usuario admin (BR9.1)."
      - "Se inserta en la misma transacción que la llamada a AccessLog.record (BR9.5)."
    relationships:
      - { to: ReportVersion, cardinality: "N:1", direction: "exportación → versión exportada" }
      - { to: User, cardinality: "N:1", direction: "exportada por" }

  - name: ExportWatermark
    owner: ReviewReport
    kind: value-object
    status: nuevo
    description: Marca visible que lleva cada exportación (VE-13, A-3); no se guarda aparte.
    attributes:
      - { name: username, type: string, required: true, description: "usuario que exporta, tal como lo valida IdentityAccess" }
      - { name: exported_at, type: UtcTimestamp, required: true, description: "se muestra en hora de Colombia y, entre paréntesis, UTC" }
      - { name: version_number, type: integer, required: true }
      - { name: version_sha256, type: string, required: true, description: "SHA-256 de la versión consolidada, solo en la cabecera" }
      - { name: superseded_by, type: object, required: false, description: "número y fecha de la versión vigente cuando se exporta una anterior (P8 = A)" }

  - name: PurgeReceipt
    owner: ReviewReport
    kind: value-object
    status: nuevo
    description: Lo que ReviewReport devuelve al Job de retención (C24); nunca texto.
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: deleted_export_ids, type: list, required: true }
      - { name: deleted_versions, type: list, required: true, description: "por cada versión borrada: report_version_id, sha256 y file_missing (si el archivo ya no estaba)" }

interfaces:
  - name: AccessLog
    defined_by: ReviewReport (U7)
    implemented_by: "EthicsGovernance (U13); adaptador por defecto en ConsoleApi mientras U13 no exista"
    status: nuevo
    description: >
      Puerto de C23 con record(uow, user_id, resource_type, resource_id, export_sha256). La ruta de
      exportación lo llama con resource_type report_export y export_sha256; ReviewReport no lo conoce
      (ADR-016): lo llama la ruta de ConsoleApi después de recibir los bytes.

references:
  - { name: InterviewSessionRecord, owner: InterviewSession, used_for: "estado (open, paused, suspended, blocked, finalized, terminated, consolidated), origen, dueño, perfil y config_sha256, finalized_at, blocked_code, retirada del consentimiento y transiciones (C11 SessionReader y puerto de transiciones, FD-U7-02)" }
  - { name: Turn, owner: InterviewSession, used_for: "número, hablante, texto, páginas y estado plegado" }
  - { name: AnalysisRun, owner: InterviewSession, used_for: "tipo (incremental o final), estado vigente, code de error, covered_by_final y modo fragmentado" }
  - { name: ModelCall, owner: InterviewSession, used_for: "registro de modelos de cada corrida" }
  - { name: HandoffPackage, status: Retirado, used_for: "Sale con el Paquete de Contexto de Traspaso (cambio 01)" }
  - { name: ReviewRound, owner: HumanReview, used_for: "ronda abierta, pendientes, bloqueo, corrección y descarte (C11 ReviewRounds)" }
  - { name: ReviewSuggestion, owner: HumanReview, used_for: "hecho, tipo, citas, avisos y observaciones" }
  - { name: ReviewDecision, owner: HumanReview, used_for: "estado vigente, nota, reformulación, actor y hora por sugerencia y ronda" }
  - { name: ScenarioVersion, status: Retirado, used_for: "Sale con el marco de verdad (cambio 01, C11 sin ScenarioReader)" }
  - { name: User, owner: IdentityAccess, used_for: "quién finaliza, consolida, corrige, descarta o exporta, y su rol" }
  - { name: ForbiddenVocabularyList, owner: IntegrityPolicy, used_for: "lista versionada de C8 con los términos de VE-02 y el escáner scan(text, literal_sources)" }
  - { name: NoticeText, owner: IntegrityPolicy, used_for: "texto versionado del aviso de VE-01 y su versión" }
```

## Resumen

- **ReportVersion** sigue siendo de solo inserción. Pierde todo lo del marco de verdad (escenario y
  umbral) y gana `notice_version`. Su plantilla pasa a `format_version` 2. La versión vigente es la de
  mayor `version_number`; no hay campo «vigente» que actualizar.
- **ReportFile** no cambia: se escribe antes de confirmar la fila (P2 = A). Ahora solo la retención lo
  borra.
- **ReportContent** sigue FR7.2: hecho, tipo, dos citas con turno y página, observaciones, corridas con su
  perfil, huellas y registro de modelos, y avisos de la sesión. Ya no tiene Hechos No Documentados.
- **ReportExport** registra cada exportación con su `export_sha256`; el archivo exportado no se guarda.
  **ExportWatermark** y **PurgeReceipt** son valores sin tabla.
- U7 **define** el puerto `AccessLog` (C23), pero ReviewReport no lo llama: lo llama la ruta de
  exportación de ConsoleApi.
- Ninguna entidad tiene campos de veracidad ni calificaciones (AUTONOMIA-03).
