# Entidades — U7 forensic-report

**Alcance.** ForensicReport es dueño de `ReportVersion` y del archivo del reporte en el volumen
persistente (components, ADR-001). Lee la sesión y sus turnos de InterviewSession, las rondas y
decisiones de HumanReview y la versión del escenario de TruthFrame por las interfaces en proceso de C11;
no guarda copias de esos datos fuera del propio reporte. Las entidades de otros componentes aparecen
solo como referencias.

```yaml
entities:
  - name: ReportVersion
    owner: ForensicReport
    description: >
      Versión inmutable y consolidada del reporte forense de una sesión. Cada consolidación (la primera o
      la de una corrección) crea una fila nueva; nunca se actualiza ni se borra (ADR-003, FR7.5).
    attributes:
      - { name: report_version_id, type: uuid, required: true, unique: true, description: "se genera antes de escribir el archivo; nombra el archivo (BR4.1)" }
      - { name: session_id, type: reference, references: InterviewSessionRecord, required: true }
      - { name: round_id, type: reference, references: ReviewRound, required: true, unique: true, description: "la ronda que esta versión bloquea; una ronda bloquea una sola versión" }
      - { name: version_number, type: integer, required: true, min: 1, description: "1 para la consolidación inicial; +1 por cada corrección consolidada" }
      - { name: supersedes_version_id, type: reference, references: ReportVersion, required: false, description: "obligatorio si version_number > 1; es la versión vigente de la que partió la corrección" }
      - { name: sha256, type: string, required: true, constraints: ["64 caracteres hexadecimales en minúscula", "calculado sobre los bytes exactos del archivo guardado"] }
      - { name: storage_path, type: string, required: true, unique: true, description: "ruta relativa dentro del volumen; derivada del report_version_id, nunca de datos del caso" }
      - { name: byte_size, type: integer, required: true, min: 1 }
      - { name: scenario_version_id, type: reference, references: ScenarioVersion, required: true }
      - { name: scenario_sha256, type: string, required: true, constraints: ["64 caracteres hexadecimales en minúscula"] }
      - { name: similarity_threshold, type: decimal, required: true, min: 0, max: 1, description: "umbral vigente de la sesión al consolidar (AC6.1.3)" }
      - { name: format_version, type: string, required: true, default: "1", description: "versión de la plantilla canónica del Markdown (BR3.2)" }
      - { name: consolidated_by, type: reference, references: User, required: true }
      - { name: consolidated_at, type: UtcTimestamp, required: true }
    constraints:
      - "(session_id, version_number) único: de dos consolidaciones simultáneas solo una puede crear la versión N (AC6.1.6)."
      - "version_number = 1 si y solo si supersedes_version_id es nulo."
      - "supersedes_version_id pertenece a la misma sesión y tiene version_number - 1."
      - "Solo inserción: el usuario de la aplicación no tiene UPDATE ni DELETE; actor u hora nulos hacen fallar el INSERT (AC8.4.1, AC8.4.2)."
      - "Nunca existe una fila sin su archivo (BR4.1)."
    relationships:
      - { to: InterviewSessionRecord, cardinality: "N:1", direction: "ReportVersion → sesión" }
      - { to: ReviewRound, cardinality: "1:1", direction: "ReportVersion → ronda que bloquea" }
      - { to: ReportVersion, cardinality: "0..1:1", direction: "versión nueva → versión que reemplaza" }
      - { to: User, cardinality: "N:1", direction: "consolidada por" }
      - { to: ScenarioVersion, cardinality: "N:1", direction: "escenario usado por la sesión" }

  - name: ReportFile
    owner: ForensicReport
    description: >
      Archivo Markdown del reporte en el volumen persistente del clúster. Es la evidencia que se descarga;
      la fila ReportVersion solo lo describe.
    attributes:
      - { name: storage_path, type: string, required: true, unique: true, description: "nombre final = report_version_id + extensión .md" }
      - { name: content, type: bytes, required: true, constraints: ["UTF-8 en forma NFC, saltos de línea LF, termina en un salto de línea"] }
      - { name: state, type: enum, required: true, allowed: [temporary, final], description: "temporary mientras se escribe; final tras forzar a disco y renombrar" }
    constraints:
      - "Un archivo final sin fila ReportVersion es un huérfano y lo elimina el barrido al arrancar (BR4.3)."
      - "Un archivo final nunca se reescribe."
    relationships:
      - { to: ReportVersion, cardinality: "1:0..1", direction: "archivo → versión que lo registra" }

  - name: ReportContent
    owner: ForensicReport
    kind: value-object
    description: >
      Contenido lógico del reporte antes de renderizarlo (no se guarda aparte; vive en el archivo).
    attributes:
      - { name: header, type: object, required: true, description: "sesión, dueño, versión del escenario y su SHA-256, umbral de la sesión, número de versión, versión que reemplaza, quién consolidó y cuándo" }
      - { name: transcript, type: list, required: true, description: "todos los turnos en orden de número, con hablante, texto y estado; los turnos en error rotulados «turno no evaluado» con su code" }
      - { name: suggestions, type: list, required: true, description: "cada sugerencia de revisión con fragmento, cita, ID de documento, CoT, estado final, notas y, si fue editada, la reformulación del analista con quién y cuándo (BR3.1)" }
      - { name: undocumented_facts, type: list, required: true, description: "cada Hecho No Documentado con su Paquete de Contexto de Traspaso" }
      - { name: scan_exclusions, type: list, required: true, description: "tramos excluidos del escaneo de vocabulario: fragmentos, citas, notas y reformulaciones" }

  - name: ConsolidationBlocker
    owner: ForensicReport
    kind: value-object
    description: Motivo por el que una sesión todavía no se puede consolidar; lo muestran la API y la consola.
    attributes:
      - { name: code, type: enum, required: true, allowed: [report.session_not_finalized, report.turns_in_progress, report.pending_suggestions] }
      - { name: count, type: integer, required: false, min: 1, description: "turnos en proceso o sugerencias pendientes" }
      - { name: first_target_id, type: uuid, required: false, description: "primera sugerencia pendiente, para el enlace (AC6.1.1, AC2.4.4)" }

  - name: MttvSample
    owner: ForensicReport
    kind: derived
    description: Medición de MTTV de una sesión, calculada a partir de marcas guardadas; no se almacena (NFR7).
    attributes:
      - { name: session_id, type: uuid, required: true }
      - { name: finalized_at, type: UtcTimestamp, required: true }
      - { name: first_consolidated_at, type: UtcTimestamp, required: true, description: "consolidated_at de la versión 1; las correcciones no cuentan" }
      - { name: seconds, type: integer, required: true, min: 0 }

references:
  - { name: InterviewSessionRecord, owner: InterviewSession, used_for: "estado (open, suspended, finalized, consolidated), dueño, finalized_at, umbral vigente, turnos y paquetes de traspaso (C11 SessionReader)" }
  - { name: Turn, owner: InterviewSession, used_for: "texto, hablante, número, estado (queued, processing, evaluated, error) y code de error" }
  - { name: HandoffPackage, owner: InterviewSession, used_for: "Paquete de Contexto de Traspaso de cada Hecho No Documentado" }
  - { name: ReviewRound, owner: HumanReview, used_for: "ronda abierta, pendientes, bloqueo y corrección (C11 ReviewRounds)" }
  - { name: ReviewDecision, owner: HumanReview, used_for: "estado vigente, nota, reformulación, actor y hora por sugerencia y ronda" }
  - { name: ScenarioVersion, owner: TruthFrame, used_for: "identificador y SHA-256 del escenario (C11 ScenarioReader)" }
  - { name: User, owner: IdentityAccess, used_for: "quién finaliza, consolida, corrige o descarta" }
```

## Resumen

- **ReportVersion** es la única tabla de ForensicReport y es de solo inserción. Cada versión bloquea su
  ronda y, si es una corrección, apunta a la versión que reemplaza. La versión vigente es la de mayor
  `version_number`. No hay campo de «vigente» que haya que actualizar.
- **ReportFile** es el archivo en el volumen. Se nombra por el `report_version_id` y se escribe antes de
  confirmar la fila (P2 = A). Así nunca hay una versión sin archivo, y un archivo sin versión es un huérfano
  que el barrido elimina.
- **ReportContent**, **ConsolidationBlocker** y **MttvSample** son valores sin tabla propia. El
  contenido se guarda solo dentro del archivo. Los bloqueos se calculan en cada consulta. MTTV se calcula
  con `finalized_at` y la primera `consolidated_at`.
- Ninguna entidad tiene campos de veracidad. La calificación de cada afirmación viene de HumanReview e
  IntegrityPolicy con sus tres valores («congruente», «incongruente», «no documentada»).
