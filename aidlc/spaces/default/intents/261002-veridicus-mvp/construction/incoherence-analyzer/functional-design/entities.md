# Entidades — U11 incoherence-analyzer

**Revisión 1 (2026-11-21).** Primera pasada de una unidad nueva del cambio 01 (DT27) y de la adenda 02.
No sustituye a nada. Origen: las respuestas P1–P8 = A de `functional-design-questions.md` y lo que esa
misma página da por decidido o deja a este diseño («Lo que el diseño resolverá sin preguntar», puntos 1–9).

**Insumos.**
- Unidad U11 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3: `library`, MUST,
  XL) y su mapa `unit-of-work-story-map.md` (unit-of-work-story-map, revisión 3): US12.2 → US13.3 → US13.2
  → US3.3 → US3.4 → US3.5 → US3.2 → US3.6 → US3.7 → US13.4 → US13.5 → US12.1 → US12.5 → US13.6 → US12.3 →
  US15.10 → US12.4 → US13.7 → US14.2 → US14.3, y las historias que la cruzan (US5.5, US8.3, US10.5,
  US13.3, US15.5, US11.3, US15.4).
- FR4.1–FR4.9, FR10.5, FR13.1–FR13.4, FR14.1–FR14.4, FR15.1–FR15.4, FR16.1–FR16.2, NFR1, NFR4, NFR5,
  NFR10, NFR12 y NFR13 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3), y
  VE-01, VE-02, VE-14, VE-17 y A-4 de `requirements-adenda-02.md`.
- Componentes IncoherenceAnalyzer, AnalyzerCli, ModelGateway, ExecutionProfiles e IntegrityPolicy de
  `inception/domain-design/components.md` (components, revisión 3); ADR-005, ADR-010, ADR-012, ADR-013,
  ADR-016 y ADR-017 de `decisions.md`.
- C6, C8, C13, C14, C17, C18, C19, C20, C21 y C25 de `inception/contract-design/contract-summary.md`
  (contract-summary, revisión 3), con CD-01, CD-02, CD-04 y CD-09.
- Historias de `inception/user-stories/stories.md` (revisión 3) y US15.10, AC15.4.7 de
  `stories-adenda-02.md`; B11 y los riesgos R8, R10, R11 y R13 de `inception/delivery-planning/bolt-plan.md`.
- Puntos de integración: U1 (`construction/contracts/functional-design/`, revisión 3: §1, §2 F3 y F8, §6,
  §7 y FD-U1-01 a FD-U1-14) y U10 (`construction/anonymizer/functional-design/functional-spec.md`, revisión
  2: §2 F1, F3b, F6, F7, §7 y FD-U10-xx). Las reglas de otras unidades se citan por descripción.

**Qué modela este documento.** U11 no persiste nada: todo vive en memoria del proceso que analiza (la
CLI en la máquina local o en ZINE, o `semantic-agent`) salvo los archivos que escribe la CLI y los datos
versionados de `evaluation/`. Los esquemas que U11 usa son de U1 (C6 entrada y salida, C18, C19,
`model-call.v1.yaml`, C8, C25) y aquí solo se nombran; los tipos de la llamada (`GenerateRequest`,
`GenerateResult`, `ModelCall`, `Destination`, errores tipados y el `Protocol` `AnonymizingProvider`) son de
U1 (`veridicus_contracts.model_calls`, o `contracts.python.model_calls` si no se aprueban FD-U1-01 a
FD-U1-04). El bloque YAML es la fuente de verdad de lo que U11 añade.

**Glosario de identificadores** (team.md, Code Style): corrida → `AnalysisRun`; candidato del juez →
`JudgeCandidate`; descarte → `DiscardRecord`; ventana → `TranscriptWindow`; conjunto sintético →
`SyntheticDataset`; reporte de la CLI → `CliReport`; paquete de ZINE → `ZinePackage`. Los campos de C6
conservan su nombre en español (CD-05).

```yaml
entities:
  # --- Núcleo: IncoherenceAnalyzer ---------------------------------------------------------------
  - name: AnalysisRun
    status: nuevo
    description: >
      Una llamada a IncoherenceAnalyzer.analyze (C17): desde que recibe la entrada de C6, la
      configuración efectiva, el gateway y la comprobación de cancelación, hasta que devuelve una Salida
      de C6, lanza InputRejected (antes de cualquier llamada) o lanza Cancelled. Su ciclo de vida está en
      functional-spec.md §3.1. Vive solo en memoria y no se guarda: en el producto la persiste
      InterviewSession (U4, ADR-013) a partir de la Salida.
    attributes:
      - { name: entrada, type: reference, references: "Entrada de C6 (U1)", required: true }
      - { name: config, type: reference, references: EffectiveConfig, required: true }
      - { name: mode, type: enum, allowed: [final, incremental], required: true, description: "entrada.modo" }
      - { name: from_turn, type: integer, required: false, min: 1, description: "entrada.desde_turno; solo incremental" }
      - { name: to_turn, type: integer, required: false, min: 1, description: "entrada.hasta_turno; solo incremental" }
      - { name: started_at, type: datetime, required: true, description: "UTC; marca el inicio del plazo" }
      - { name: deadline, type: datetime, required: true, description: "started_at + run_deadline_final_s o run_deadline_incremental_s de config.limits (C25)" }
      - { name: state, type: enum, required: true, allowed: [received, validating, rejected, judging, filtering, verifying, finalizing, succeeded, failed, aborted_incident, cancelled], default: received }
      - { name: windows, type: list, required: true, description: "TranscriptWindow en orden; una sola si no hay modo fragmentado" }
      - { name: candidates, type: list, required: true, description: "JudgeCandidate de todas las ventanas" }
      - { name: calls, type: list, required: true, description: "ModelCall (U1) en orden cronológico, incluidas las de llamadas que fallaron con su registro" }
      - { name: discards, type: list, required: true, description: "DiscardRecord; se vacía si la corrida termina en error" }
      - { name: findings, type: list, required: true, description: "Finding; vacía salvo en succeeded" }
      - { name: error_code, type: enum, required: false, allowed: [salida_invalida, bloqueo_contenido, tiempo_agotado, proveedor, anonimizador_no_disponible, incidente_anonimizacion], description: "solo en failed y aborted_incident" }
    constraints:
      - "Ninguna llamada al gateway antes de terminar validating sin rechazo."
      - "En failed y aborted_incident: findings vacía, discards vacía, observaciones_conductor ausente y error_code presente; calls se conserva."
      - "Después de aborted_incident o cancelled no se hace ninguna llamada más."
      - "Ninguna llamada empieza con el plazo agotado ni con cancelled() verdadero."
    relationships:
      - { to: EffectiveConfig, cardinality: "1..1", direction: "AnalysisRun -> EffectiveConfig" }
      - { to: TranscriptWindow, cardinality: "1..*", direction: "AnalysisRun -> TranscriptWindow" }
      - { to: JudgeCandidate, cardinality: "0..*", direction: "AnalysisRun -> JudgeCandidate" }
      - { to: DiscardRecord, cardinality: "0..*", direction: "AnalysisRun -> DiscardRecord" }
      - { to: Finding, cardinality: "0..*", direction: "AnalysisRun -> Finding" }
      - { to: PromptBundle, cardinality: "1..1", direction: "AnalysisRun -> PromptBundle" }

  - name: TranscriptWindow
    status: nuevo
    description: >
      Tramo contiguo de turnos que el juez recibe en una llamada. Sin modo fragmentado hay una sola, con
      todos los turnos hasta to_turn (o todos en el modo final). Con modo fragmentado se arman por
      posición en la lista ordenada de turnos, con paso window − overlap (respuesta del punto 3).
    attributes:
      - { name: index, type: integer, required: true, min: 0, unique: true }
      - { name: first_position, type: integer, required: true, min: 0, description: "posición (no número n) del primer turno" }
      - { name: last_position, type: integer, required: true, min: 0 }
      - { name: turn_numbers, type: list, required: true, description: "números n de los turnos que contiene, en orden" }
      - { name: relevant, type: boolean, required: true, description: "en incremental, verdadero si contiene algún turno >= from_turn; las no relevantes no se envían" }
    constraints:
      - "last_position − first_position + 1 <= window (AC3.7.2)."
      - "La última ventana termina en el último turno enviado; si quedaría más corta que window se desplaza hacia atrás hasta tener window turnos (o todos, si hay menos)."
      - "Dos ventanas consecutivas comparten exactamente overlap turnos, salvo la última desplazada, que comparte overlap o más."
    relationships:
      - { to: AnalysisRun, cardinality: "1..1", direction: "TranscriptWindow -> AnalysisRun" }

  - name: JudgeCandidate
    status: nuevo
    description: >
      Una contradicción propuesta por el juez en una ventana, ya restaurada por el anonimizador si el
      destino era externo. El juez responde sin id, pagina, avisos ni actos (punto 2; precisión
      FD-U11-12): esos campos los pone el núcleo. Recorre el filtro determinista y luego el verificador
      (P1 = A).
    attributes:
      - { name: window_index, type: integer, required: true }
      - { name: ordinal, type: integer, required: true, description: "posición en la respuesta del juez; sirve para el puntero JSON" }
      - { name: json_pointer, type: text, required: true, description: "puntero RFC 6901 al candidato en la respuesta (p. ej. /hallazgos/2), para cruzarlo con altered_markers" }
      - { name: hecho, type: text, required: true }
      - { name: tipo, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      - { name: cita_a, type: reference, references: QuoteClaim, required: true }
      - { name: cita_b, type: reference, references: QuoteClaim, required: true }
      - { name: observaciones, type: text, required: true }
      - { name: outcome, type: enum, required: true, allowed: [pending, discarded, kept], default: pending }
      - { name: verdict_direct, type: boolean, required: false, description: "respuesta del verificador con las citas en su orden" }
      - { name: verdict_permuted, type: boolean, required: false, description: "respuesta con las citas invertidas; solo con permutation" }
    constraints:
      - "Un candidato se descarta una sola vez, con el motivo del primer filtro que falla (orden de functional-spec.md F5)."
      - "Solo los candidatos que pasan el filtro determinista llegan al verificador (P1 = A)."
    relationships:
      - { to: QuoteClaim, cardinality: "2..2", direction: "JudgeCandidate -> QuoteClaim" }
      - { to: DiscardRecord, cardinality: "0..1", direction: "JudgeCandidate -> DiscardRecord" }
      - { to: Finding, cardinality: "0..1", direction: "JudgeCandidate -> Finding" }

  - name: QuoteClaim
    status: nuevo
    description: Una cita tal como la propone el juez (texto y turno) y el resultado de verificarla.
    attributes:
      - { name: text, type: text, required: true, description: "cita restaurada; « […] » separa fragmentos" }
      - { name: turn_ref, type: text, required: true, constraints: "patrón ^T[0-9]+$" }
      - { name: fragments, type: list, required: true, description: "fragmentos ya normalizados en espacios" }
      - { name: normalized, type: text, required: true, description: "texto con los espacios normalizados; clave de deduplicación (FR4.9)" }
      - { name: verification, type: enum, required: true, allowed: [pending, verified, not_found, other_turn, unknown_turn, out_of_range], default: pending }
      - { name: notices, type: list, required: true, allowed: [turno_entrevistador, turno_plegado], description: "se derivan del turno, no del modelo" }
      - { name: page, type: integer, required: false, min: 1, description: "pagina del turno citado; ausente si el turno no la tiene" }
    constraints:
      - "Se verifica contra el texto original del turno de la entrada, nunca contra el texto seudonimizado."

  - name: DiscardRecord
    status: nuevo
    description: Candidato que no salió, sin texto (registro.descartes de C6).
    attributes:
      - { name: motivo, type: enum, required: true, allowed: [cita_no_verificada, cita_en_otro_turno, marca_alterada, campo_faltante, rechazado_verificador, rechazado_permutacion, fuera_de_tramo, vocabulario_prohibido] }
      - { name: turno_a, type: text, required: false, constraints: "^T[0-9]+$; el turno que nombró el juez, aunque no exista" }
      - { name: turno_b, type: text, required: false, constraints: "^T[0-9]+$" }
    constraints:
      - "Nunca lleva texto de citas, hecho ni observaciones."
      - "Los duplicados entre ventanas no generan DiscardRecord: se unen (FD-U11-24)."

  - name: Finding
    status: nuevo
    description: >
      Hallazgo emitido: un JudgeCandidate kept con id, pagina y avisos puestos por el núcleo. Es el
      hallazgo de C6 y nace como sugerencia de revisión pendiente en el producto (AUTONOMIA-03, U4/U5).
    attributes:
      - { name: id, type: text, required: true, unique: true, constraints: "<entrevista>-C<nn>, nn desde 01 y con dos dígitos como mínimo" }
      - { name: hecho, type: text, required: true }
      - { name: tipo, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      - { name: cita_a, type: reference, references: QuoteClaim, required: true, description: "verification = verified" }
      - { name: cita_b, type: reference, references: QuoteClaim, required: true, description: "verification = verified" }
      - { name: observaciones, type: text, required: true }
    constraints:
      - "Ningún campo de veracidad ni puntaje (AUTONOMIA-03); actos no se emite (FD-U11-12)."
      - "hecho y observaciones pasaron el escáner (VE-02)."

  - name: PromptBundle
    status: nuevo
    description: >
      Archivo versionado de solo lectura con las instrucciones del sistema del juez y del verificador y
      los esquemas de sus respuestas (punto 6). Va como dato del paquete de la biblioteca; su SHA-256 es
      prompt_sha256 (FR4.6, AC3.3.1).
    attributes:
      - { name: path, type: text, required: true, default: "libs/incoherence_analyzer/data/prompt.v1.md", description: "propuesta; FD-U11-21" }
      - { name: version, type: text, required: true, constraints: "semver" }
      - { name: judge_instructions, type: text, required: true }
      - { name: verifier_instructions, type: text, required: true }
      - { name: judge_response_schema, type: json_schema, required: true, description: "objeto hallazgos[] con hecho, tipo, cita_a{cita,turno}, cita_b{cita,turno}, observaciones; additionalProperties false" }
      - { name: verifier_response_schema, type: json_schema, required: true, description: "objeto { confirma: boolean }; additionalProperties false (punto 7)" }
      - { name: prompt_sha256, type: text, required: true, constraints: "SHA-256 de los bytes del archivo" }
    constraints:
      - "No contiene testimonio ni marcadores; nunca se concatena con la entrada."
      - "La copia del chart (U2/U4) debe tener el mismo SHA-256 (nivel 0)."

  # --- ExecutionProfiles --------------------------------------------------------------------------
  - name: ExecutionProfile
    status: nuevo
    description: >
      Una entrada de config/profiles.yaml (C18) validada con la función pura de U1 (kind analyzer,
      key_prefix VERIDICUS_) y con las reglas propias de ExecutionProfiles (rules.md BR2).
    attributes:
      - { name: profile_name, type: text, required: true, unique: true, constraints: "^[a-z0-9-]{1,48}$" }
      - { name: purpose, type: enum, required: true, allowed: [evaluation, demonstration, production] }
      - { name: judge, type: reference, references: "Destination (C18)", required: true }
      - { name: verifier, type: reference, references: "Destination (C18)", required: true }
      - { name: fallback_provider, type: reference, references: "Destination (C18)", required: false }
      - { name: permutation, type: boolean, required: true }
      - { name: chunking, type: object, required: false, description: "enabled, window, overlap" }
      - { name: same_family_declared, type: boolean, required: false, default: false }
      - { name: batch_only, type: boolean, required: false, description: "lo lee U4; U11 no lo usa para decidir" }
      - { name: has_external_destination, type: boolean, required: true, description: "derivado: algún papel o el alterno con scope external" }
      - { name: warnings, type: list, required: true, allowed: [same_family, fragmented], description: "ProfileWarning que muestran la consola, el reporte y la CLI" }
    constraints:
      - "Nunca guarda el valor de una clave: solo api_key_ref."
      - "Es inmutable mientras el proceso vive; un cambio entra por PR (FR9.2, US8.3)."
    relationships:
      - { to: EffectiveConfig, cardinality: "0..*", direction: "EffectiveConfig -> ExecutionProfile" }

  - name: EffectiveConfig
    status: nuevo
    description: >
      La configuración efectiva de C18 (effective-config.v1.yaml): versión del analizador, perfil,
      huellas y límites que cambian el resultado. Viaja en C2 en el producto; en la CLI la arma el
      ProfileResolver.
    attributes:
      - { name: analyzer_version, type: text, required: true, constraints: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
      - { name: profile_name, type: text, required: true }
      - { name: profile, type: reference, references: ExecutionProfile, required: true }
      - { name: profile_sha256, type: text, required: true, description: "SHA-256 de la forma JCS de profile" }
      - { name: prompt_sha256, type: text, required: true }
      - { name: limits, type: object, required: true, description: "model_call_timeout_s, run_deadline_incremental_s, run_deadline_final_s, fragment_window_turns, fragment_overlap_turns, ya bajados por el entorno" }
      - { name: config_sha256, type: text, required: true, description: "SHA-256 de la forma JCS de todo el objeto" }
    constraints:
      - "Misma configuración, misma huella, sin importar orden de claves ni formato del YAML (AC13.2.1)."
      - "Ningún valor de clave de API entra en la huella."

  - name: PriceTable
    status: nuevo
    description: config/prices.yaml (C18 prices.schema.v1.yaml); solo cambia por PR.
    attributes:
      - { name: version, type: text, required: true, constraints: "^[A-Za-z0-9._-]{1,32}$" }
      - { name: currency, type: enum, required: true, allowed: [USD] }
      - { name: prices, type: list, required: true, description: "provider, model, input_per_million, output_per_million" }

  - name: ProfileWarning
    status: nuevo
    description: Aviso que acompaña a un perfil válido y que la consola, el reporte y la CLI muestran.
    attributes:
      - { name: kind, type: enum, required: true, allowed: [same_family, fragmented] }
      - { name: window, type: integer, required: false, description: "solo fragmented" }
      - { name: overlap, type: integer, required: false, description: "solo fragmented" }
    constraints:
      - "Los textos visibles son los de AC13.1.2 y AC3.7.1, del catálogo de mensajes (U1/U4)."

  # --- ModelGateway (parte de U11) ----------------------------------------------------------------
  - name: GatewayAssembly
    status: nuevo
    description: >
      Cómo se arma el ModelGateway para un perfil: qué adaptador atiende cada papel y la ranura del
      alterno. La construye la raíz de composición (la CLI en U11; semantic-agent en U4) antes de
      cualquier llamada (C13, arranque).
    attributes:
      - { name: bindings, type: list, required: true, description: "por (papel, ranura): adaptador local u anonymizer" }
      - { name: anonymizing_provider, type: enum, required: false, allowed: [in_process_module, http_client_c21], description: "CLI: módulo de U10; semantic-agent: cliente HTTP de C21" }
    constraints:
      - "Todo papel o alterno con scope external tiene un AnonymizingProvider inyectado; si no, la construcción falla."
      - "Todo destino local tiene base_url interna (loopback, nombre de servicio del clúster o red privada)."
      - "El adaptador anonymizer nunca se usa con un destino local y el local nunca con uno externo."

  - name: LocalModelAdapter
    status: nuevo
    description: Adaptador compatible con OpenAI (C14) para juez y verificador locales; libs/model_gateway/adapters/.
    attributes:
      - { name: base_url, type: text, required: true }
      - { name: model, type: text, required: true }
      - { name: parameters, type: object, required: true, description: "temperature, seed, quantization, engine; reasoning apagado" }
      - { name: retry_policy, type: object, required: true, description: "hasta 2 reintentos (2 s y 6 s) ante conexión rechazada, 502, 503 o 504, solo si el plazo lo permite (C13)" }

  - name: AnonymizerHttpClient
    status: nuevo
    description: >
      Cliente HTTP de C21 en libs/model_gateway/adapters/anonymizer_http.py. Implementa
      AnonymizingProvider; solo importa los contratos. Lo inyecta semantic-agent (U4); U11 lo escribe y
      lo prueba.
    attributes:
      - { name: base_url, type: text, required: true, default: "http://veridicus-anonymizer-proxy:8080" }
      - { name: run_id, type: uuid, required: true, description: "solo para logs" }
    constraints:
      - "Nunca reintenta; traduce cada respuesta según las filas anonymizer de C13."
      - "check_ready() consulta /readyz y no es parte del Protocol."

  - name: RecordedResponse
    status: nuevo
    description: >
      Respuesta grabada y sintética de un proveedor (local o comercial) para las pruebas de contrato de
      nivel 0 sin red (AC13.6.1, AC13.7.1). Las comerciales se reproducen con el FakeTransport de U10.
    attributes:
      - { name: provider, type: enum, required: true, allowed: [anthropic, google, openai, local] }
      - { name: body, type: json, required: true }
      - { name: expected_valid, type: boolean, required: true }

  # --- IntegrityPolicy (reglas del analizador) ----------------------------------------------------
  - name: VocabularyScan
    status: nuevo
    description: >
      Una llamada a scan(text, literal_sources): busca los términos de C8 en un texto, excluyendo los
      tramos entre «…» que aparecen literales en alguna fuente y la cadena del aviso de VE-01.
    attributes:
      - { name: text, type: text, required: true }
      - { name: literal_sources, type: list, required: true, description: "textos de todos los turnos de la entrada" }
      - { name: excluded_spans, type: list, required: true, description: "tramos excluidos, con su posición" }
      - { name: matches, type: list, required: true, description: "término y posición; vacía si no hay coincidencia" }
      - { name: vocabulary_version, type: text, required: true, description: "schema_version de forbidden-vocabulary (C8)" }
    constraints:
      - "Los términos se leen del archivo de C8; ninguno está escrito en el código."
      - "Los logs del escáner nunca llevan el texto ni el término encontrado, solo conteos."

  - name: NoticeEmission
    status: nuevo
    description: >
      El aviso de VE-01 que escribe la CLI (P8 = A): el texto y la versión de contracts/integrity/notice.v1.yaml
      en stderr en cada ejecución, y en un archivo AVISO.txt en cada directorio de salida.
    attributes:
      - { name: notice_version, type: text, required: true }
      - { name: text, type: text, required: true, description: "copia exacta del archivo de C8" }
      - { name: destinations, type: list, required: true, allowed: [stderr, aviso_txt] }

  # --- AnalyzerCli ---------------------------------------------------------------------------------
  - name: CliInvocation
    status: nuevo
    description: Una ejecución de veridicus analyze o veridicus evaluate.
    attributes:
      - { name: subcommand, type: enum, required: true, allowed: [analyze, evaluate] }
      - { name: inputs, type: list, required: true, description: "archivos de transcripción (analyze), conjunto (evaluate) o directorios de salidas (evaluate --score)" }
      - { name: profile_name, type: text, required: false, description: "obligatorio salvo en evaluate --score" }
      - { name: output_dir, type: text, required: true, default: "resultados-locales/<fecha>-<subcomando> (FD-U11-16)" }
      - { name: mode, type: enum, required: true, allowed: [final, incremental], default: final }
      - { name: from_turn, type: integer, required: false }
      - { name: to_turn, type: integer, required: false }
      - { name: exit_code, type: enum, required: true, allowed: [0, 2, 3, 4, 5, 6], description: "6 es propuesta (FD-U11-10)" }
    constraints:
      - "Toda la validación previa termina antes de la primera llamada; si falla, no se escribe ningún archivo."
      - "incremental solo con un archivo de entrada y con from_turn y to_turn."

  - name: BatchItem
    status: nuevo
    description: Una transcripción de un lote de analyze.
    attributes:
      - { name: input_path, type: text, required: true }
      - { name: interview_sha256, type: text, required: true, description: "SHA-256 de los bytes del archivo; es lo único que va al reporte" }
      - { name: origen, type: enum, required: true, allowed: [corpus, guiada, sintetico] }
      - { name: output_path, type: text, required: true, description: "<output_dir>/<nombre del archivo sin extensión>.salida.json" }
      - { name: status, type: enum, required: true, allowed: [pending, ok, error, not_run], default: pending }
    constraints:
      - "El archivo de entrada es el objeto transcripcion de C6; la CLI arma la entrada con el modo y el perfil."
      - "Dos archivos de entrada con el mismo nombre sin extensión hacen fallar la validación previa."

  - name: CliReport
    status: nuevo
    description: >
      Reporte JSON de C19 (kind run o evaluation), sin texto libre. En evaluation lleva además lo que
      propone FD-U11-09 si se aprueba.
    attributes:
      - { name: kind, type: enum, required: true, allowed: [run, evaluation] }
      - { name: path, type: text, required: true, default: "<output_dir>/reporte.json" }
      - { name: runs, type: list, required: true, description: "por entrevista: interview_sha256, status, error_code, findings, discards, calls" }
    constraints:
      - "Valida contra C19 con el registro de U1 antes de escribirse; si no valida, la CLI termina con 5 y no deja el archivo."

  - name: ResultsDirectory
    status: nuevo
    description: Directorio de resultados por omisión, cubierto por .gitignore (AC12.4.1; FD-U11-16).
    attributes:
      - { name: path, type: text, required: true, default: "resultados-locales/" }
      - { name: git_ignored, type: boolean, required: true }

  # --- Evaluación ---------------------------------------------------------------------------------
  - name: EvaluationRun
    status: nuevo
    description: >
      Una ejecución de evaluate: el conjunto sintético corrido 3 veces con el mismo perfil (P6 = A), o
      tres directorios de salidas ya producidas (--score), puntuados contra el manifiesto.
    attributes:
      - { name: dataset, type: reference, references: SyntheticDataset, required: true }
      - { name: repetitions, type: integer, required: true, min: 3, max: 3 }
      - { name: adversarial, type: enum, required: false, allowed: [scenario_a], description: "Escenario A de NFR5 (AC3.3.2)" }
      - { name: metrics, type: list, required: true, description: "MetricResult" }
      - { name: bias_rows, type: list, required: true, description: "BiasRow" }
      - { name: passes, type: boolean, required: true }
    relationships:
      - { to: SyntheticDataset, cardinality: "1..1", direction: "EvaluationRun -> SyntheticDataset" }
      - { to: MetricResult, cardinality: "1..*", direction: "EvaluationRun -> MetricResult" }
      - { to: BiasRow, cardinality: "0..*", direction: "EvaluationRun -> BiasRow" }
      - { to: EvaluationThresholds, cardinality: "1..1", direction: "EvaluationRun -> EvaluationThresholds" }

  - name: MetricResult
    status: nuevo
    description: Una métrica de NFR4/NFR5 con su valor por corrida, su agregado y su umbral.
    attributes:
      - { name: name, type: enum, required: true, allowed: [verified_quotes, json_format_errors, permutation_coverage, anonymizer_leaks, completed_runs, precision, recall, reversed_order_consistency, three_run_agreement, type_agreement, scenario_a_marker_hits, scenario_a_difference] }
      - { name: kind, type: enum, required: true, allowed: [absolute, statistical, reported] }
      - { name: per_run, type: list, required: false, description: "3 valores; ausente en three_run_agreement" }
      - { name: aggregate, type: number, required: true, description: "absolute: el peor de las 3; statistical: la media (P6 = A)" }
      - { name: threshold, type: number, required: false, description: "de EvaluationThresholds; ausente en reported" }
      - { name: passes, type: boolean, required: false }
    constraints:
      - "absolute pasa solo si las 3 corridas cumplen; statistical pasa si la media cumple; reported no decide."

  - name: EvaluationThresholds
    status: nuevo
    description: >
      Archivo versionado evaluation/thresholds.v1.yaml con los umbrales que fija NFR Requirements; solo
      cambia por PR y nunca para bajarlos (team.md).
    attributes:
      - { name: version, type: text, required: true }
      - { name: values, type: map, required: true, description: "una cifra por métrica absolute y statistical" }

  - name: SyntheticDataset
    status: nuevo
    description: >
      Conjunto sintético de evaluation/synthetic/ con su manifiesto (B11, P12 = A de Delivery Planning):
      contradicciones sembradas de los 7 tipos, relatos coherentes y casos trampa. Lo genera un modelo
      comercial de una familia distinta a las del juez y del verificador, solo con datos sintéticos, y lo
      revisa a mano el autor.
    attributes:
      - { name: dataset_version, type: text, required: true, constraints: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }
      - { name: dataset_sha256, type: text, required: true, description: "SHA-256 de los bytes del manifiesto, que lista el SHA-256 de cada muestra" }
      - { name: generator, type: object, required: true, description: "provider, model y family del modelo generador (NFR5 Escenario B)" }
      - { name: review, type: object, required: true, description: "revisado_por y fecha de la revisión manual" }
      - { name: labels_version, type: text, required: true, description: "versión de las dos listas de BiasLabelList" }
      - { name: samples, type: list, required: true, description: "DatasetSample" }
    constraints:
      - "Toda muestra tiene origen sintetico; ningún dato real (project.md, Forbidden)."
      - "La composición mínima (cuántas por tipo y por caso trampa) la fija NFR Requirements; los 7 tipos y los 4 casos trampa aparecen al menos una vez."
    relationships:
      - { to: DatasetSample, cardinality: "1..*", direction: "SyntheticDataset -> DatasetSample" }
      - { to: BiasLabelList, cardinality: "2..2", direction: "SyntheticDataset -> BiasLabelList" }

  - name: DatasetSample
    status: nuevo
    description: Una transcripción sintética del conjunto con sus etiquetas y sus contradicciones esperadas.
    attributes:
      - { name: path, type: text, required: true }
      - { name: sha256, type: text, required: true }
      - { name: category, type: enum, required: true, allowed: [contradiccion, coherente, trampa] }
      - { name: trap_kind, type: enum, required: false, allowed: [vaguedad, emocion, detalle_periferico, version_terceros], description: "obligatorio si category = trampa" }
      - { name: tipo_hecho, type: text, required: true, description: "valor de la lista cerrada tipo-hecho (P7 = A)" }
      - { name: perfil_persona, type: text, required: true, description: "valor de la lista cerrada perfil-persona (P7 = A)" }
      - { name: expected, type: list, required: true, description: "ExpectedContradiction; vacía en coherente y trampa" }
    constraints:
      - "contradiccion tiene al menos una esperada; coherente y trampa, ninguna."

  - name: ExpectedContradiction
    status: nuevo
    description: Contradicción sembrada que la evaluación espera encontrar.
    attributes:
      - { name: turno_a, type: text, required: true, constraints: "^T[0-9]+$" }
      - { name: turno_b, type: text, required: true, constraints: "^T[0-9]+$" }
      - { name: tipo, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      - { name: cita_a, type: text, required: true }
      - { name: cita_b, type: text, required: true }
    constraints:
      - "Las dos citas verifican contra sus turnos con la regla del piloto (el conjunto es coherente consigo mismo)."
      - "El acierto se mide por el par no ordenado {turno_a, turno_b}."

  - name: BiasLabelList
    status: nuevo
    description: >
      Dos listas cerradas y versionadas en evaluation/labels/ (tipo-hecho.v1.yaml y
      perfil-persona.v1.yaml). Las iniciales las propone este diseño y las aprueba el autor (P7 = A).
    attributes:
      - { name: kind, type: enum, required: true, allowed: [tipo_hecho, perfil_persona] }
      - { name: version, type: text, required: true }
      - { name: values, type: list, required: true, constraints: "cada valor ^[a-z0-9-]{1,23}$, para que <tipo_hecho>__<perfil_persona> quepa en 48 caracteres" }

  - name: BiasRow
    status: nuevo
    description: Fila de bias_table de C19 (P7 = A).
    attributes:
      - { name: fact_type, type: enum, required: true, allowed: [fecha, numero, lugar, persona, negacion, secuencia, otro], description: "tipo de la contradicción" }
      - { name: synthetic_set, type: text, required: true, constraints: "<tipo_hecho>__<perfil_persona>" }
      - { name: expected, type: integer, required: true, min: 0 }
      - { name: found, type: integer, required: true, min: 0, description: "mediana de las 3 corridas" }

  # --- ZINE -----------------------------------------------------------------------------------------
  - name: ZinePackage
    status: nuevo
    description: >
      Paquete de entrada para ZINE que arma un script revisable fuera de Git (US14.2): transcripciones
      validadas, la wheelhouse de la CLI, el perfil local y el manifiesto con nombres y SHA-256. Lo copia y
      lo lanza el humano (AUTONOMIA-01).
    attributes:
      - { name: directory, type: text, required: true, default: "evaluation/zine/paquete/ (ignorado por Git; FD-U11-17)" }
      - { name: manifest_path, type: text, required: true, default: "evaluation/zine/manifest.v1.yaml (en Git: nombres y SHA-256, sin contenido)" }
      - { name: entries, type: list, required: true, description: "nombre, SHA-256 y fuente (sintetico o corpus)" }
      - { name: profile_name, type: text, required: true, description: "un perfil sin destinos externos" }
    constraints:
      - "Ningún archivo fuera del manifiesto; ninguna credencial; no contiene el repositorio."

  - name: ZineRunMetadata
    status: nuevo
    description: >
      Lo que una salida producida en ZINE debe declarar para que evaluate --score la acepte (US14.3): se lee
      de registro.llamadas de la salida de C6.
    attributes:
      - { name: model, type: text, required: true }
      - { name: version, type: text, required: true }
      - { name: quantization, type: text, required: true, description: "esfuerzo_o_cuantizacion" }
      - { name: engine, type: text, required: true, description: "motor" }
      - { name: capability_valid, type: boolean, required: true, description: "verdadero solo con Q8 (Q8_0) o BF16" }
```

## Resumen

| Grupo | Entidades | Dónde vive | Qué aporta |
|---|---|---|---|
| Núcleo | AnalysisRun, TranscriptWindow, JudgeCandidate, QuoteClaim, DiscardRecord, Finding, PromptBundle | `libs/incoherence_analyzer/` (memoria) | El ciclo de una corrida, sus ventanas, el filtro determinista y lo que sale en C6 |
| Perfiles | ExecutionProfile, EffectiveConfig, PriceTable, ProfileWarning | `libs/execution_profiles/` y `config/` | Validación, huellas, avisos y precios (C18) |
| Gateway | GatewayAssembly, LocalModelAdapter, AnonymizerHttpClient, RecordedResponse | `libs/model_gateway/` | El paso obligado por el anonimizador y el adaptador local (C13, C14, C21) |
| Integridad | VocabularyScan, NoticeEmission | `libs/integrity_policy/` | El escáner de C8 y el aviso de VE-01 |
| CLI | CliInvocation, BatchItem, CliReport, ResultsDirectory | `libs/incoherence_analyzer/cli/` | Lotes, códigos de salida, reporte C19 y directorio fuera de Git |
| Evaluación | EvaluationRun, MetricResult, EvaluationThresholds, SyntheticDataset, DatasetSample, ExpectedContradiction, BiasLabelList, BiasRow | `libs/incoherence_analyzer/cli/` y `evaluation/` | Las 3 corridas, las métricas de NFR4/NFR5 y la tabla de sesgo de VE-17 |
| ZINE | ZinePackage, ZineRunMetadata | `evaluation/zine/` | El paquete fuera de Git y lo que una corrida en ZINE debe declarar |

Son 31 entidades, todas nuevas. Ninguna se persiste en una base de datos. Las rutas de `libs/` siguen C13 y
C17; el nombre `libs/integrity_policy/` para el escáner sigue FD-U1-09.
