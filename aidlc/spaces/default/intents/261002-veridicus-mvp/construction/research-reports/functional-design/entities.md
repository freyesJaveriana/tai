# Entidades — U12 research-reports

**Revisión 1 (2026-11-22), primera pasada.** Unidad nueva del cambio 01 (DT27); no hay artefactos previos.
Respuestas P1 = A, P2 = A y P3 = A de `functional-design-questions.md`, y los doce puntos de su sección 2.

**Insumos.**
- Unidad U12 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) e historias
  US12.6, US12.7 y US5.6 (en M8) de `unit-of-work-story-map.md` (unit-of-work-story-map, revisión 3).
- FR1.2, FR1.3, FR13.5 y NFR12 de `inception/requirements-analysis/requirements.md` (requirements,
  revisión 3).
- ResearchReports, ConsoleApi e IntegrityPolicy de `inception/domain-design/components.md` (components,
  revisión 3), con CD-03 y ADR-014.
- C1 (`/research-reports*`, `ResearchReportSummary`, `ResearchReportDetail`), C18 (perfiles y tabla de
  precios), C19 (reporte de la CLI y registro de llamadas) y C25 (`research_report_max_bytes`) de
  `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- M8 (§10.1–§10.3) de `inception/refined-mockups/mockups.md` y el catálogo `research.*` de
  `interaction-spec.md`; B12 y DP-01 de `inception/delivery-planning/bolt-plan.md`.
- Diseños de U1 (BR10.1, FD-U1-03, FD-U1-05), U3 (convención de auditoría, rol `investigador`, destino M8),
  U4 (suite `axe`) y U11 (`CliReport`, BR12.7, BR13.3, FD-U11-07, FD-U11-09).

**Frontera AUTONOMIA-04.** Todo corre dentro del clúster: el módulo ResearchReports de `session-api` y su
tabla en PostgreSQL, y la pantalla M8 servida por `frontend`. El archivo llega desde el navegador del
investigador, que lo trae de su máquina o de ZINE. Ningún dato de esta unidad sale del clúster, y ninguno
es testimonio: solo enums, números, hashes, versiones y nombres que coinciden con archivos versionados
(BR3.1–BR3.5).

## Modelo de entidades (fuente de verdad)

```yaml
entities:
  - name: ResearchReport
    description: >
      Metadatos y cifras de un reporte de la CLI (C19) que subió un investigador. Agregado raíz de
      ResearchReports. Nunca cambia después de guardarse: no hay rutas de edición ni de borrado, y la
      retención no lo toca.
    storage: { kind: history, purgeable: false, owner_unit: U12, actor_columns: { actor_user_id: uploaded_by, at: uploaded_at } }
    attributes:
      - { name: research_report_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: source_sha256, type: text, required: true, unique: true, constraints: "^[a-f0-9]{64}$; SHA-256 de los bytes del archivo subido; la unicidad la impone la base (BR2.8)" }
      - { name: source_bytes, type: integer, required: true, min: 1, description: "tamaño del archivo; su tope es research_report_max_bytes de C25" }
      - { name: schema_version, type: text, required: true, description: "la versión de C19 vigente que publica veridicus_contracts (BR2.4)" }
      - { name: kind, type: enum, required: true, allowed: [run, evaluation] }
      - { name: origin, type: enum, required: false, allowed: [local, zine], description: "campo origin de C19 v2 (P3 = A, FD-U12-07); nulo con C19 v1, y M8 muestra «No informado»" }
      - { name: analyzer_version, type: text, required: true, constraints: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
      - { name: contract_version, type: text, required: true, constraints: "const de C19" }
      - { name: profile_name, type: text, required: true, constraints: "^[a-z0-9-]{1,48}$ y existe en el catálogo de perfiles aprobado (BR3.1)" }
      - { name: config_sha256, type: text, required: true, constraints: "^[a-f0-9]{64}$" }
      - { name: prompt_sha256, type: text, required: true, constraints: "^[a-f0-9]{64}$" }
      - { name: dataset_version, type: text, required: false, constraints: "^[0-9]+\\.[0-9]+\\.[0-9]+$; obligatorio en evaluation y ausente en run (BR2.5)" }
      - { name: dataset_sha256, type: text, required: false, constraints: "^[a-f0-9]{64}$; solo con C19 v2 y solo en evaluation" }
      - { name: report_created_at, type: UtcTimestamp, required: true, description: "created_at del reporte, la hora en que la CLI lo escribió" }
      - { name: input_tokens_total, type: integer, required: true, min: 0 }
      - { name: output_tokens_total, type: integer, required: true, min: 0 }
      - { name: estimated_cost, type: decimal, required: false, min: 0, description: "nulo = «sin precio» (FD-U11-14)" }
      - { name: price_table_version, type: text, required: false, constraints: "igual a la versión de la tabla de precios vigente (BR3.4)" }
      - { name: measurement_valid, type: boolean, required: true, description: "falso si una llamada local declara una cuantización distinta de Q8_0 y BF16 (BR2.7)" }
      - { name: overall_passes, type: boolean, required: false, description: "passes global de C19 v2 en evaluation; nulo si el reporte no lo trae" }
      - { name: run_summary, type: RunSummary, required: true }
      - { name: model_calls, type: list, required: true, description: "lista de ModelCallRecord, en el orden del archivo, sin enlace a ninguna entrevista" }
      - { name: metrics, type: list, required: false, description: "lista de MetricValue; solo evaluation; una métrica ausente no tiene elemento" }
      - { name: bias_counts, type: list, required: false, description: "lista de BiasCount; solo evaluation" }
      - { name: uploaded_by, type: reference, references: User, required: true, description: "el investigador que lo subió (FR1.3)" }
      - { name: uploaded_at, type: UtcTimestamp, required: true }
      - { name: actor_kind, type: enum, required: true, allowed: [user], default: user, description: "convención de auditoría de U3; ResearchReports no tiene actores de sistema" }
      - { name: actor_system, type: text, required: false, description: "siempre nulo (convención de auditoría de U3)" }
    constraints:
      - "No hay ninguna columna para texto de transcripciones, hallazgos, citas, observaciones ni hechos, ni para el nombre del archivo subido (NFR12, BR4.2, BR5.1)."
      - "Toda cadena guardada es un enum, un hash hexadecimal, una versión semántica o un nombre que coincide con un archivo versionado (BR3.1–BR3.5)."
      - "El usuario veridicus_app solo tiene SELECT e INSERT sobre la tabla (history); nadie la modifica ni la borra (BR1.4)."
      - "La fila y sus listas se escriben en una sola transacción; nunca queda un reporte a medias (BR2.1)."
    relationships:
      - { to: User, cardinality: "N..1", direction: "ResearchReport -> User (owned_by IdentityAccess)" }
      - { to: ModelCallRecord, cardinality: "0..*", direction: "ResearchReport -> ModelCallRecord (composición)" }
      - { to: MetricValue, cardinality: "0..*", direction: "ResearchReport -> MetricValue (composición)" }
      - { to: BiasCount, cardinality: "0..*", direction: "ResearchReport -> BiasCount (composición)" }
      - { to: RunSummary, cardinality: "1..1", direction: "ResearchReport -> RunSummary (valor)" }

  - name: ModelCallRecord
    description: >
      Copia de una llamada del registro de C19 (model-call.v1.yaml). Valor dentro de ResearchReport. No
      dice a qué entrevista pertenece: las llamadas de todas las corridas se guardan en una sola lista.
    attributes:
      - { name: role, type: enum, required: true, allowed: [judge, verifier, verifier_permuted], description: "los tres papeles del analizador (FD-U1-03, BR10.2 de U1)" }
      - { name: provider, type: enum, required: true, allowed: [anthropic, google, openai, local] }
      - { name: model, type: text, required: true, constraints: "igual al model del destino del perfil para ese papel o su alterno (BR3.2)" }
      - { name: version, type: text, required: false, constraints: "obligatorio si provider es local (BR2.6); igual al declarado en el perfil o, en un comercial sin version declarada, con la forma de BR3.3" }
      - { name: effort_or_quantization, type: text, required: false, constraints: "obligatorio si provider es local (BR2.6); igual a parameters.effort o parameters.quantization del destino (BR3.2)" }
      - { name: engine, type: text, required: false, constraints: "obligatorio si provider es local (BR2.6); igual a parameters.engine del destino (BR3.2)" }
      - { name: seed, type: integer, required: false }
      - { name: input_tokens, type: integer, required: true, min: 0 }
      - { name: output_tokens, type: integer, required: true, min: 0 }
      - { name: fallback_provider, type: boolean, required: true }
      - { name: anonymized, type: boolean, required: true }
      - { name: at, type: UtcTimestamp, required: true }

  - name: RunSummary
    description: >
      Agregados de runs[] de C19 (P2 = A). Valor dentro de ResearchReport. No guarda ningún
      interview_sha256 individual.
    attributes:
      - { name: run_count, type: integer, required: true, min: 0 }
      - { name: status_counts, type: map, required: true, description: "clave en [ok, error] → entero ≥ 0; las dos claves siempre presentes" }
      - { name: error_code_counts, type: map, required: true, description: "clave en los 6 valores de error_code de C19 → entero ≥ 0; solo las claves con conteo > 0" }
      - { name: findings_total, type: integer, required: true, min: 0, description: "suma de runs[].findings" }
      - { name: discard_counts, type: map, required: true, description: "clave en los 8 motivos de discards de C19 → suma por motivo; solo claves con conteo > 0" }
      - { name: inputs_fingerprint, type: text, required: true, constraints: "^[a-f0-9]{64}$; huella del conjunto de entradas (BR5.2)" }
    constraints:
      - "La suma de status_counts es igual a run_count; la suma de error_code_counts es igual a status_counts.error."

  - name: MetricValue
    description: Una métrica de C19 (v1 o v2) con lo que el reporte trae de ella. Valor dentro de ResearchReport.
    attributes:
      - { name: name, type: enum, required: true, allowed: [precision, recall, verified_quotes, json_format_errors, reversed_order_consistency, three_run_agreement, anonymizer_leaks, permutation_coverage, completed_runs, type_agreement], description: "los 7 de C19 v1; los 3 últimos solo con C19 v2 (FD-U11-09)" }
      - { name: value, type: decimal, required: true, description: "el agregado del reporte; en anonymizer_leaks es un entero" }
      - { name: per_run, type: list, required: false, description: "valores por corrida de C19 v2; se guardan y no se muestran en M8" }
      - { name: threshold, type: decimal, required: false, description: "el umbral que trae el reporte (el que se aplicó al correr); nunca el de thresholds.v1.yaml actual (BR6.2)" }
      - { name: passes, type: boolean, required: false, description: "el passes que trae el reporte" }
    constraints:
      - "threshold y passes vienen juntos o no vienen (BR2.5)."
      - "Una métrica que el reporte no trae no tiene MetricValue; M8 la muestra como «No informado» (BR6.1)."

  - name: BiasCount
    description: Una fila de bias_table de C19 (VE-17). Valor dentro de ResearchReport.
    attributes:
      - { name: fact_type, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      - { name: story_fact_type, type: text, required: true, description: "primera parte de synthetic_set (<tipo_hecho>), de evaluation/labels/tipo-hecho.v1.yaml (BR3.5)" }
      - { name: persona_profile, type: text, required: true, description: "segunda parte de synthetic_set (<perfil_persona>), de evaluation/labels/perfil-persona.v1.yaml (BR3.5)" }
      - { name: expected, type: integer, required: true, min: 0 }
      - { name: found, type: integer, required: true, min: 0 }

  - name: ReferenceCatalog
    description: >
      Lo versionado contra lo que se contrastan las cadenas de un reporte (P1 = A). Valor en memoria que
      ConsoleApi carga al arrancar y pasa a ResearchReports en cada subida. ResearchReports no lee archivos.
    attributes:
      - { name: profiles, type: map, required: true, description: "config/profiles.yaml validado por ExecutionProfiles: nombre → destinos judge, verifier y fallback_provider con provider, model, version y parameters" }
      - { name: price_table_version, type: text, required: true, description: "version de config/prices.yaml" }
      - { name: currency, type: text, required: true, description: "currency de config/prices.yaml, para mostrar el costo" }
      - { name: story_fact_types, type: list, required: true, description: "valores de evaluation/labels/tipo-hecho.v1.yaml" }
      - { name: persona_profiles, type: list, required: true, description: "valores de evaluation/labels/perfil-persona.v1.yaml" }
      - { name: catalog_sha256, type: text, required: true, description: "huella de los cuatro archivos, para el log de arranque" }
    constraints:
      - "Si falta o no valida alguno de los cuatro archivos, session-api no arranca (BR3.6)."

  - name: UploadOutcome
    description: >
      Resultado de una subida. Valor sin almacenamiento. En un rechazo nunca lleva valores del archivo ni
      nombres de campos que el esquema no conoce (BR4.1).
    attributes:
      - { name: status, type: enum, required: true, allowed: [accepted, rejected] }
      - { name: http_status, type: integer, required: true, allowed: [201, 409, 413, 422] }
      - { name: code, type: enum, required: false, allowed: [research.invalid_report, research.duplicate, limits.exceeded, auth.csrf] }
      - { name: source_sha256, type: text, required: false, description: "nulo solo cuando el archivo supera el tope y no se lee entero" }
      - { name: first_problem, type: ValidationProblem, required: false }
      - { name: problem_count, type: integer, required: false, min: 1 }

  - name: ValidationProblem
    description: Un problema de validación descrito solo con datos del esquema. Valor sin almacenamiento.
    attributes:
      - { name: rule, type: enum, required: true, allowed: [encoding, json_syntax, json_duplicate_key, json_non_finite, json_depth, schema_version, not_allowed_field, missing_field, type_mismatch, out_of_range, pattern_mismatch, kind_mismatch, value_not_recognized, inconsistent_counts, inconsistent_validity] }
      - { name: path, type: text, required: false, description: "ruta con nombres de campo del esquema e índices, p. ej. runs[3].calls[0].model; un campo desconocido se describe en su objeto padre" }
      - { name: line, type: integer, required: false, description: "solo en json_syntax" }
      - { name: column, type: integer, required: false, description: "solo en json_syntax" }

  - name: ComparisonView
    description: >
      La comparación de dos reportes del mismo tipo que arma la consola con las dos respuestas de
      GET /research-reports/compare. Valor sin almacenamiento.
    attributes:
      - { name: comparable_figures, type: boolean, required: true, description: "verdadero si el conjunto coincide (BR7.3)" }
      - { name: rows, type: list, required: true, description: "ComparisonRow: label, value_a, value_b, mark (= | ≠), difference (con signo o «—»)" }
      - { name: notice, type: enum, required: false, allowed: [research.not_comparable] }
```

## Resumen

| Entidad | Qué es | Almacenamiento |
|---|---|---|
| `ResearchReport` | Agregado raíz: metadatos y cifras de un reporte de la CLI, con quién y cuándo lo subió | PostgreSQL, `history`, no purgable |
| `ModelCallRecord` | Una llamada del registro de C19, sin enlace a ninguna entrevista | Dentro de `ResearchReport` |
| `RunSummary` | Agregados de `runs[]`: conteos y la huella del conjunto de entradas (P2 = A) | Dentro de `ResearchReport` |
| `MetricValue` | Una métrica con el umbral y el `passes` que trae el reporte | Dentro de `ResearchReport` |
| `BiasCount` | Una fila de la tabla de sesgo, con `synthetic_set` partido en sus dos etiquetas | Dentro de `ResearchReport` |
| `ReferenceCatalog` | Perfiles, tabla de precios y listas de etiquetas que contrastan las cadenas (P1 = A) | Memoria de ConsoleApi |
| `UploadOutcome`, `ValidationProblem` | Resultado de una subida, sin eco del archivo | Sin almacenamiento |
| `ComparisonView` | Comparación de dos reportes que arma la consola | Sin almacenamiento |

Un reporte guardado nunca cambia. Por eso `ResearchReport` no tiene máquina de estados: existe o no
existe. Las listas (`model_calls`, `metrics`, `bias_counts`) y `run_summary` son valores del agregado.
Viven en su misma fila o en tablas hijas escritas en la misma transacción; lo decide Code Generation. Si
son tablas hijas, cada una lleva la misma marca `history` y no purgable, con sus propias columnas de
actor y hora (copia de `uploaded_by` y `uploaded_at`), porque la prueba común de U3 las recorre todas.
