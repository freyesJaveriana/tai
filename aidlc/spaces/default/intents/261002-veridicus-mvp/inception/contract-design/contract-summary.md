# Contratos — Veridicus (MVP)

**Revisión 2 (2026-11-09), segunda pasada por el cambio 01 (DT27) y la adenda 02.** Sustituye a la
revisión 1 del 2026-10-02. Los contratos conservan su número: los que salen quedan «Retirado» sin
renumerar, y los nuevos toman C17–C25 (regla de `project.md`). Cada contrato dice al principio si
**se mantiene**, **cambia**, **se reescribe** o es **nuevo**.

**Insumos.**
- Unidades y grafo: `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 2: U1–U13) y
  `unit-of-work-dependency.md` (unit-of-work-dependency, revisión 2).
- Componentes, entidades y ADR: `inception/domain-design/components.md` (components, revisión 2) y
  `decisions.md` (ADR-001 a ADR-017).
- Requisitos: `inception/requirements-analysis/requirements.md` (requirements, revisión 2) y
  `requirements-adenda-02.md` (VE-01 a VE-17, precisión A-4).
- Contrato común del analizador: propuesta v0.1 del cambio 01 §4 (DT17). Su fuente de verdad es el
  repositorio principal del TG (ADR-017); aquí se fija la versión 1.0.0, que aprueba el autor.
- Respuestas: P1–P7 (primera pasada) y P8–P14 (segunda pasada) en `contract-design-questions.md`.

**Alcance.** Cada frontera por la que cruzan datos entre unidades, o entre el sistema y algo que no
escribimos: el navegador, los servidores de modelos locales, los proveedores comerciales y el humano que
sube un reporte de la CLI. Los valores numéricos (plazos, intervalos, tamaños máximos) son parámetros
del catálogo único `contracts/limits.v1.yaml` (C25) que fija NFR Requirements; aquí solo se nombran.

**Lo que cambió desde la revisión 1.** Sale el contraste con el marco documental (TruthFrame,
SemanticEvaluation, umbral, pasajes y Paquete de Contexto de Traspaso), así que C4 y C9 se retiran y
C2, C3, C6, C7, C13 y C14 se reescriben sobre el contrato común. Entran la biblioteca del analizador con
su CLI (U11), el anonimizador (U10), la consola del investigador (U12) y la demostración ética (U13), con
sus contratos C17–C24. Por primera vez un contrato **cruza la frontera del clúster** (C22): solo
`anonymizer-proxy` habla con los proveedores comerciales, y solo con texto seudonimizado.

## Decisiones de esta etapa

| P | Decisión |
|---|---|
| P1 | Colas con Redis Streams y grupos de consumidores: `XACK` tras procesar, `XAUTOCLAIM` de pendientes y un *stream* de fallidos por cola. |
| P2 | Versión semántica por contrato y `schema_version` en cada mensaje. Aditivo = menor (el consumidor ignora campos desconocidos). Incompatible = mayor, en un solo PR que cambia productor y consumidores. Mayor desconocido → fallidos, sin filas. |
| P3 | Aplicada ahora a la **corrida**: InterviewSession vigila el plazo de cada corrida; la reentrega automática solo cubre fallos recuperables; una corrida en `error` no se reintenta sola; el reintento humano publica la misma corrida con `attempt + 1`, y los resultados de intentos viejos se descartan. |
| P4 | Las fronteras en proceso son interfaces Python tipadas (`Protocol`), verificadas con mypy estricto e import-linter. |
| P5 | Sesión del servidor con cookie `HttpOnly`, `Secure`, `SameSite=Strict`, revocable, y cabecera anti-CSRF en peticiones que cambian estado. |
| P6 | Sondeo con cursor de cambios; cada consulta de la sesión cuenta como latido. |
| P7 | Aplicada ahora solo al **servidor local**: API compatible con OpenAI dentro del clúster, con un adaptador propio para el TTS. Los proveedores comerciales usan su API nativa (FR15.1, C22). |
| P8 | Códigos de error del contrato común en español y `snake_case`: los cuatro de la v0.1 más `anonimizador_no_disponible` (fallo cerrado) e `incidente_anonimizacion`. El catálogo de Problem Details sigue en inglés con puntos y los traduce uno a uno (C1). |
| P9 | Sobre propio de Veridicus en las colas (`schema_version`, `run_id`, `attempt`…) alrededor de `entrada` y `salida`, que son exactamente el contrato común. |
| P10 | Bloque `registro` dentro de la salida del contrato común (llamadas, descartes sin texto, modo fragmentado, tokens y costo); reemplaza el campo `modelo` de la v0.1. |
| P11 | Bloque `consentimiento` mínimo y sin datos personales. La retirada no va en el contrato: la maneja InterviewSession. |
| P12 | El reporte JSON de la CLI no tiene campos de texto libre; la consola del investigador rechaza con `422` lo que no cumple el esquema, sin guardar nada. |
| P13 | `anonymizer-proxy` expone la misma operación del puerto (`POST /v1/generate`). Los adaptadores nativos de los proveedores comerciales y sus claves de API viven solo en el proxy (y en el módulo del anonimizador cuando lo usa la CLI). |
| P14 | Los campos del contrato común conservan su nombre en español en JSON y en Python, sin alias; todo lo propio de Veridicus va en inglés. |

## Tabla de contratos

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---|---|---|---|
| C1 | U3, U4, U5, U6, U7, U8, U9, U12, U13 (`session-api`, módulo ConsoleApi) | External: navegador del analista, del admin y del investigador (`frontend`) | REST síncrono (HTTP/JSON) con cookie de sesión | U3 (seguridad y errores); cada unidad es dueña de sus rutas |
| C2 | U4 (InterviewSession) | U4 (AnalysisWorker, `semantic-agent`) | Mensaje asíncrono: Redis Stream `veridicus:runs` | U4 |
| C3 | U4 (AnalysisWorker) | U4 (InterviewSession) | Mensaje asíncrono: Redis Stream `veridicus:results` | U4 |
| C4 | — | — | **Retirado** (cambio 01): sale la indexación de escenarios | — |
| C5 | U9 (InterviewSession, voz) | U9 (SpeechProcessing, `audio-worker`) | Mensajes asíncronos: Redis Streams `veridicus:audio` y `veridicus:transcripts` | U9 |
| C6 | U1 (IntegrityPolicy; fuente externa: repositorio principal del TG) | U4, U8, U11, U12; External: app `sistema` del TG | Esquema compartido (JSON Schema): contrato común del analizador v1.0.0 | U1 (propone), autor del TG (aprueba) |
| C7 | U1 (IntegrityPolicy) | U4, U5, U7, `frontend` | Esquema compartido (JSON Schema): sugerencia de revisión | U1 |
| C8 | U1 (IntegrityPolicy) | U4, U7, U8, U9, U11, U13, `frontend` | Esquema compartido (YAML versionado): vocabulario prohibido, regla de DT23 y aviso de VE-01 | U1 |
| C9 | — | — | **Retirado** (cambio 01): sale la lectura de pasajes con `pgvector` | — |
| C10 | U5 (HumanReview) | U4 (InterviewSession), U5 (ConsoleApi) | Interfaz en proceso (`Protocol`) | U5 |
| C11 | U5 (HumanReview), U4 y U6 (InterviewSession) | U7 (ReviewReport) | Interfaces en proceso (`Protocol`) | U5, U4 |
| C12 | U3 (IdentityAccess) | U3 (ConsoleApi) | Interfaz en proceso (`Protocol`) | U3 |
| C13 | U11 (ModelGateway, `libs/`) | U11 (IncoherenceAnalyzer), U9 (SpeechProcessing) | Interfaz en proceso (`Protocol`) | U11 |
| C14 | External: servidores de modelos locales (juez y verificador locales, Whisper, TTS) | U11, U9 (adaptadores locales de ModelGateway) | REST síncrono compatible con OpenAI | U2 despliega los servidores; U11 fija el subconjunto usado |
| C15 | U5 (HumanReview vía `session-api`) | U2 (regla de Prometheus y panel de Grafana) | Métricas Prometheus (`/metrics`) | U5 |
| C16 | `session-api`, `semantic-agent`, `audio-worker`, `anonymizer-proxy` | U2 (sondas de Kubernetes, `scripts/smoke.sh`) | REST síncrono: `/healthz` y `/readyz` | U2 |
| C17 | U11 (IncoherenceAnalyzer, AnalyzerCli) | U4 (AnalysisWorker), U8 | Interfaz en proceso (`Protocol`): API pública de la biblioteca | U11 |
| C18 | U11 (ExecutionProfiles) | U4, U11, `anonymizer-proxy` (U10); el humano por PR | Esquema compartido (YAML versionado): perfiles de ejecución y tabla de precios | U11 |
| C19 | U11 (AnalyzerCli) | U12 (ResearchReports); External: investigador y repositorio principal del TG | Esquema compartido (JSON Schema): reporte de corrida y de evaluación de la CLI; códigos de salida | U11 |
| C20 | U10 (módulo Anonymizer en `libs/`) | U11 (ModelGateway en la CLI) | Interfaz en proceso (`Protocol`) | U10 |
| C21 | U10 (`anonymizer-proxy`) | U11 (ModelGateway en `semantic-agent`) | REST síncrono dentro del clúster: `POST /v1/generate` | U10 |
| C22 | External: APIs de Anthropic, Google y OpenAI | U10 (adaptadores nativos del Anonymizer) | HTTPS por 443, solo dominios de la lista, solo texto seudonimizado | U10 (lista de dominios y subconjunto usado) |
| C23 | U13 (EthicsGovernance) | U3 (ConsoleApi); interfaz definida por U7 | Interfaz en proceso (`Protocol`): puerto `AccessLog` | U7 (interfaz), U13 (adaptador) |
| C24 | U4, U5, U7 (borrado de lo suyo) | U13 (Job de retención) | Interfaces en proceso (`Protocol`) | U13 (orden), cada unidad (su borrado) |
| C25 | U1 | Todas las unidades de código | Esquema compartido (YAML versionado): catálogo único de límites | U1 |

Todos los archivos de especificación viven en `contracts/` (U1). La columna **Owner** dice qué unidad
decide los cambios del contrato; U1 los guarda, los versiona y prueba sus *fixtures* válidos e
inválidos.

### Datos sensibles por contrato y frontera del clúster (AUTONOMIA-04)

| # | Datos sin seudonimizar que transporta | Dónde viajan |
|---|---|---|
| C1 | Testimonio, hallazgos con sus citas, observaciones, reportes | Navegador ↔ `session-api` dentro del clúster |
| C2, C3 | Transcripción, hallazgos, citas, observaciones; el bloque de consentimiento (sin datos personales, P11) | Redis dentro del clúster (bajo la `NetworkPolicy` de salida denegada) |
| C5 | Audio crudo y su transcripción | Redis; el audio se borra del *stream* tras confirmarlo |
| C14 | Todo lo que se envía a un modelo local | Solo servidores internos; un destino externo sin anonimizador impide arrancar |
| C17, C20 | Transcripción y salida del analizador | En el mismo proceso (`semantic-agent` o la CLI) |
| C21 | Mensajes con testimonio **antes** de seudonimizar, y la respuesta ya restaurada | `semantic-agent` ↔ `anonymizer-proxy` dentro del clúster |
| C22 | **Ninguno**: solo texto seudonimizado sale del clúster | `anonymizer-proxy` → internet, puerto 443, solo dominios de la lista |
| C19 | **Ninguno**: el reporte no tiene campos de texto libre (P12) | Máquina local o ZINE → navegador del investigador → `session-api` |
| C15, C16, C23, C24, C25 | Ninguno (identificadores, cifras y configuración) | Dentro del clúster o en el proceso |

Con la CLI (máquina local o ZINE), C20 y C22 ocurren en el mismo proceso: el módulo del anonimizador
seudonimiza antes de la llamada externa, y con un perfil todo local no interviene (P9 de `iteracion2`).

---

## C1 — API de la consola (ConsoleApi) · cambia

Única superficie expuesta al navegador (ADR-004). **Cambia:** salen las rutas `/scenarios*`, el umbral,
las calificaciones y el Paquete de Contexto de Traspaso; entran los perfiles, el aviso de VE-01, el
consentimiento, la importación, el modo final, las corridas con su registro de modelos, la pausa, la
terminación, la retirada del consentimiento, la exportación, la consola del investigador y la
demostración ética. Reglas comunes:

- Toda ruta exige la cookie `veridicus_session` salvo `POST /api/v1/auth/login`, `/healthz` y
  `/readyz` (AC8.1.4). Sin cookie válida o con usuario desactivado: `401` (AC8.2.3).
- Toda petición que cambia estado (`POST`, `PATCH`) lleva `X-CSRF-Token` con el valor que entrega
  `GET /api/v1/auth/me`; sin él o con otro valor: `403` con `code: auth.csrf`.
- ConsoleApi aplica rol y propiedad de la sesión antes de delegar (ADR-009). `x-veridicus-roles` dice
  qué roles entran; `x-veridicus-owner-only` exige además ser el dueño de la sesión. Un rechazo es `403`
  Problem Details y no crea filas. No hay rol ni ruta para la persona entrevistada (VE-09).
- Todo error es `application/problem+json` con `code` estable y `detail` en español (NFR10).
- **No existe ninguna ruta que escriba perfiles, proveedores, *prompts*, precios ni límites** (FR9.2,
  AC8.3.1): solo cambian por PR.
- Cada lectura de una sesión, de un hallazgo o de un reporte, y cada exportación, pasa por el puerto
  `AccessLog` (C23) antes de responder (VE-11, A-3).
- Los campos que vienen del contrato común (`hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones`,
  `actos`) conservan su nombre en español (P14); todo lo demás va en inglés.
- Las fechas van en ISO 8601 UTC (`2026-11-09T21:40:00Z`); la consola las muestra en hora de Colombia.
- Las rutas marcadas `x-veridicus-priority: SHOULD` solo existen cuando su unidad (U8, U9) se construye;
  las de U13 llevan `x-veridicus-demo: true` y nunca bloquean el uso (ADR-016).

```yaml
openapi: 3.1.0
info:
  title: Veridicus ConsoleApi
  version: 2.0.0
servers:
  - url: /api/v1
security:
  - sessionCookie: []
components:
  securitySchemes:
    sessionCookie: { type: apiKey, in: cookie, name: veridicus_session }
  parameters:
    CsrfToken: { name: X-CSRF-Token, in: header, required: true, schema: { type: string, minLength: 32 } }
    SessionId: { name: session_id, in: path, required: true, schema: { type: string, format: uuid } }
    RunId: { name: run_id, in: path, required: true, schema: { type: string, format: uuid } }
    SuggestionId: { name: suggestion_id, in: path, required: true, schema: { type: string, format: uuid } }
  responses:
    Problem:
      description: Error en formato Problem Details (RFC 9457)
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
  schemas:
    Problem:
      type: object
      required: [type, title, status, code, detail]
      properties:
        type: { type: string, format: uri-reference }
        title: { type: string }
        status: { type: integer }
        code: { $ref: '#/components/schemas/ErrorCode' }
        detail: { type: string, description: Texto en español, sin datos sensibles }
        instance: { type: string }
    ErrorCode:
      type: string
      enum:
        - auth.invalid_credentials
        - auth.unauthenticated
        - auth.forbidden
        - auth.csrf
        - validation.invalid_request
        - limits.exceeded                  # una cifra del catálogo C25
        - profile.not_approved
        - profile.transfer_not_authorized  # perfil con proveedor comercial sin autorización de transferencia (VE-07)
        - session.not_owner
        - session.finalized
        - session.not_suspended
        - session.closed_to_new_turns      # importada, terminada o con consentimiento retirado
        - session.paused
        - session.terminated
        - session.blocked                  # bloqueada por anonymizer.incident (VE-14)
        - session.consent_missing
        - session.consent_withdrawn
        - session.voice_not_authorized
        - import.invalid_type
        - import.invalid_transcript        # no cumple C6 (entrada)
        - run.not_in_error
        - run.final_in_progress            # segundo lanzamiento simultáneo del modo final (409)
        - analysis.invalid_output          # contrato: salida_invalida
        - analysis.content_blocked         # contrato: bloqueo_contenido
        - analysis.timeout                 # contrato: tiempo_agotado
        - analysis.provider                # contrato: proveedor
        - analysis.anonymizer_unavailable  # contrato: anonimizador_no_disponible
        - anonymizer.incident              # contrato: incidente_anonimizacion
        - analysis.system                  # la corrida no volvió a tiempo o agotó sus entregas (C2)
        - review.observations_not_viewed
        - review.note_required
        - review.invalid_transition
        - review.round_locked
        - report.session_not_finalized
        - report.runs_in_progress
        - report.pending_suggestions
        - report.forbidden_vocabulary
        - report.conflict
        - report.integrity_mismatch
        - report.not_consolidated
        - research.invalid_report          # no cumple C19 o trae un campo no permitido (P12)
        - research.duplicate
        - research.not_comparable
        - conductor_observation.not_approved
    Role: { type: string, enum: [analista, admin, investigador] }
    Me:
      type: object
      required: [user_id, username, role, csrf_token]
      properties:
        user_id: { type: string, format: uuid }
        username: { type: string }
        role: { $ref: '#/components/schemas/Role' }
        csrf_token: { type: string }
        acknowledgement: { $ref: '#/components/schemas/AcknowledgementStatus' }
    User:
      type: object
      required: [user_id, username, role, active, created_at]
      properties:
        user_id: { type: string, format: uuid }
        username: { type: string }
        role: { $ref: '#/components/schemas/Role' }
        active: { type: boolean }
        created_at: { type: string, format: date-time }
    Notice:
      type: object
      required: [text, version]
      description: Aviso de propósito limitado (VE-01), leído de C8 en ejecución; la consola no guarda copia
      properties:
        text: { type: string }
        version: { type: string }
    ProfileSummary:
      type: object
      required: [profile_name, purpose, roles, config_sha256]
      properties:
        profile_name: { type: string }
        purpose: { type: string, enum: [evaluacion, demostracion, produccion] }
        config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        roles:
          type: array
          items:
            type: object
            required: [role, commercial, via_anonymizer]
            properties:
              role: { type: string, enum: [juez, verificador] }
              commercial: { type: boolean }
              via_anonymizer: { type: boolean, description: true siempre que commercial es true (FR14.5) }
        fragmented: { type: boolean }
        same_family_warning: { type: boolean, description: Perfil de demostración que declara la misma familia (FR14.4) }
    Consent:
      type: object
      description: Bloque `consentimiento` de C6 (P11); sin datos personales
      required: [tipo, version_texto, autoriza_transferencia, autoriza_voz, autoriza_conservar_audio]
      additionalProperties: false
      properties:
        tipo: { type: string, enum: [persona, autoridad] }
        version_texto: { type: string }
        autoriza_transferencia: { type: boolean }
        autoriza_voz: { type: boolean }
        autoriza_conservar_audio: { type: boolean }
        constancia: { type: string, description: Solo un identificador de la constancia; obligatorio si tipo es autoridad }
    SessionStatus:
      type: string
      enum: [open, paused, suspended, finalized, terminated, blocked, consolidated]
    Turn:
      type: object
      required: [turn_id, n, hablante, texto, origin, submitted_at]
      properties:
        turn_id: { type: string, format: uuid }
        n: { type: integer, minimum: 1 }
        hablante: { type: string, enum: [ENT, TEST] }
        texto: { type: string }
        pagina: { type: integer, minimum: 1, description: Ausente en turnos guiados (P4 de iteracion2) }
        pagina_fin: { type: integer, minimum: 1 }
        estado: { type: string, enum: [visible, plegado] }
        origin: { type: string, enum: [typed, pasted, voice, imported] }
        voice_status: { type: string, enum: [transcribing, transcribed, error], description: Solo turnos de voz (SHOULD) }
        submitted_at: { type: string, format: date-time }
    Run:
      type: object
      required: [run_id, mode, desde_turno, hasta_turno, status, attempt, profile_name, config_sha256, requested_at]
      properties:
        run_id: { type: string, format: uuid }
        mode: { type: string, enum: [incremental, final] }
        desde_turno: { type: integer, minimum: 1 }
        hasta_turno: { type: integer, minimum: 1 }
        status: { type: string, enum: [queued, processing, done, error, cancelled] }
        error_code: { $ref: '#/components/schemas/ErrorCode' }
        attempt: { type: integer, minimum: 1 }
        profile_name: { type: string }
        config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        fragmented: { type: object, properties: { activo: { type: boolean }, ventana: { type: integer }, solapamiento: { type: integer } } }
        requested_at: { type: string, format: date-time }
        finished_at: { type: string, format: date-time }
    ModelCall:
      type: object
      description: Una fila del registro de modelos de la corrida (FR15.3), de solo lectura (AC12.5.3)
      required: [papel, proveedor, modelo, tokens_entrada, tokens_salida, proveedor_alterno, anonimizado, fecha]
      properties:
        papel: { type: string, enum: [juez, verificador, verificador_permutado] }
        proveedor: { type: string }
        modelo: { type: string }
        version: { type: string }
        esfuerzo_o_cuantizacion: { type: string }
        motor: { type: string }
        semilla: { type: integer }
        tokens_entrada: { type: integer, minimum: 0 }
        tokens_salida: { type: integer, minimum: 0 }
        proveedor_alterno: { type: boolean }
        anonimizado: { type: boolean }
        fecha: { type: string, format: date-time }
    ReviewSuggestion: { $ref: 'contracts/integrity/review-suggestion.v2.json' }   # C7
    ConductorObservation:
      type: object
      required: [observation_id, run_id, tema, turnos, status]
      properties:
        observation_id: { type: string, format: uuid }
        run_id: { type: string, format: uuid }
        tema: { type: string, description: Nunca contiene el texto de las citas (AC10.3.2) }
        turnos: { type: array, items: { type: string, pattern: '^T[0-9]+$' } }
        status: { type: string, enum: [proposed, approved, discarded] }
    SessionSummary:
      type: object
      required: [session_id, entrevista, owner_user_id, status, profile_name, created_at, pending_suggestions]
      properties:
        session_id: { type: string, format: uuid }
        entrevista: { type: string }
        owner_user_id: { type: string, format: uuid }
        owner_username: { type: string }
        status: { $ref: '#/components/schemas/SessionStatus' }
        origin: { type: string, enum: [guiada, corpus, sintetico] }
        profile_name: { type: string }
        created_at: { type: string, format: date-time }
        finalized_at: { type: string, format: date-time }
        pending_suggestions: { type: integer, minimum: 0 }
    SessionView:
      allOf:
        - $ref: '#/components/schemas/SessionSummary'
        - type: object
          required: [config_sha256, cursor, closed_to_new_turns, analysis_paused, turns, runs, suggestions, can_consolidate]
          properties:
            config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
            cursor: { type: string, description: Opaco; se devuelve en el siguiente sondeo }
            closed_to_new_turns: { type: boolean }
            analysis_paused: { type: boolean }
            consent_withdrawn_at: { type: string, format: date-time }
            blocked_code: { $ref: '#/components/schemas/ErrorCode' }
            turns: { type: array, items: { $ref: '#/components/schemas/Turn' } }
            runs: { type: array, items: { $ref: '#/components/schemas/Run' } }
            suggestions: { type: array, items: { $ref: '#/components/schemas/ReviewSuggestion' } }
            conductor_observations: { type: array, items: { $ref: '#/components/schemas/ConductorObservation' } }
            can_consolidate: { type: boolean }
            consolidation_blockers: { type: array, items: { $ref: '#/components/schemas/ErrorCode' } }
    ReportVersion:
      type: object
      required: [report_version_id, session_id, version_number, sha256, consolidated_by, consolidated_at]
      properties:
        report_version_id: { type: string, format: uuid }
        session_id: { type: string, format: uuid }
        version_number: { type: integer, minimum: 1 }
        sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        notice_version: { type: string }
        consolidated_by: { type: string, format: uuid }
        consolidated_at: { type: string, format: date-time }
        supersedes_version_id: { type: string, format: uuid }
    ResearchReportSummary:
      type: object
      required: [research_report_id, kind, profile_name, config_sha256, prompt_sha256, analyzer_version, source_sha256, uploaded_at]
      properties:
        research_report_id: { type: string, format: uuid }
        kind: { type: string, enum: [corrida, evaluacion] }
        profile_name: { type: string }
        config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        prompt_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        analyzer_version: { type: string }
        dataset_version: { type: string }
        source_sha256: { type: string, pattern: '^[a-f0-9]{64}$', description: SHA-256 del archivo subido; dos subidas iguales dan research.duplicate }
        uploaded_by: { type: string, format: uuid }
        uploaded_at: { type: string, format: date-time }
    ResearchReportDetail:
      allOf:
        - $ref: '#/components/schemas/ResearchReportSummary'
        - type: object
          description: Solo cifras de C19; ningún texto de transcripciones, hallazgos ni citas (NFR12)
          properties:
            model_log: { type: array, items: { $ref: '#/components/schemas/ModelCall' } }
            tokens_in: { type: integer }
            tokens_out: { type: integer }
            estimated_cost: { type: number }
            metrics: { type: object }
            bias_table: { type: array, items: { type: object } }
    AcknowledgementStatus:
      type: object
      required: [status]
      properties:
        status: { type: string, enum: [valid, missing, expired, text_changed], description: Solo avisa; nunca impide abrir sesiones (VE-04, demostración) }
        text_version: { type: string }
        at: { type: string, format: date-time }
paths:
  /auth/login:
    post:
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, password]
              additionalProperties: false
              properties:
                username: { type: string, minLength: 1 }
                password: { type: string, minLength: 1 }
      responses:
        '204': { description: Sesión creada; responde Set-Cookie veridicus_session (HttpOnly, Secure, SameSite=Strict) }
        '401': { $ref: '#/components/responses/Problem' }
  /auth/logout:
    post:
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '204': { description: Sesión revocada }
  /auth/me:
    get:
      responses:
        '200': { description: Usuario actual, token anti-CSRF y estado del reconocimiento, content: { application/json: { schema: { $ref: '#/components/schemas/Me' } } } }
        '401': { $ref: '#/components/responses/Problem' }
  /users:
    get:
      x-veridicus-roles: [admin]
      responses:
        '200': { description: Usuarios, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/User' } } } } }
        '403': { $ref: '#/components/responses/Problem' }
    post:
      x-veridicus-roles: [admin]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [username, password, role]
              additionalProperties: false
              properties:
                username: { type: string, minLength: 1 }
                password: { type: string, minLength: 1 }
                role: { $ref: '#/components/schemas/Role' }
      responses:
        '201': { description: Usuario creado, content: { application/json: { schema: { $ref: '#/components/schemas/User' } } } }
        '403': { $ref: '#/components/responses/Problem' }
  /users/{user_id}:
    patch:
      x-veridicus-roles: [admin]
      parameters:
        - { name: user_id, in: path, required: true, schema: { type: string, format: uuid } }
        - { $ref: '#/components/parameters/CsrfToken' }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              additionalProperties: false
              minProperties: 1
              properties:
                active: { type: boolean }
                role: { $ref: '#/components/schemas/Role' }
      responses:
        '200': { description: Usuario actualizado; deja fila en el historial de usuario, content: { application/json: { schema: { $ref: '#/components/schemas/User' } } } }
        '403': { $ref: '#/components/responses/Problem' }
        '409': { description: Cambio de rol con sesiones pendientes (validation.invalid_request) }
  /notice:
    get:
      responses:
        '200': { description: Texto y versión del aviso de VE-01, content: { application/json: { schema: { $ref: '#/components/schemas/Notice' } } } }
  /profiles:
    get:
      x-veridicus-roles: [analista, admin, investigador]
      responses:
        '200': { description: Solo los perfiles aprobados (C18), con su indicación de proveedor comercial (FR14.5), content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/ProfileSummary' } } } } }
  /sessions:
    get:
      x-veridicus-roles: [analista, admin]
      parameters:
        - { name: status, in: query, schema: { $ref: '#/components/schemas/SessionStatus' } }
      responses:
        '200': { description: Lista de sesiones, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/SessionSummary' } } } } }
    post:
      description: Sesión guiada. Exige consentimiento y un perfil aprobado; un perfil con proveedor comercial sin autoriza_transferencia da 422 profile.transfer_not_authorized antes de crear filas.
      x-veridicus-roles: [analista]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [entrevista, profile_name, consentimiento]
              additionalProperties: false
              properties:
                entrevista: { type: string, minLength: 1 }
                profile_name: { type: string }
                consentimiento: { $ref: '#/components/schemas/Consent' }
      responses:
        '201': { description: Sesión abierta y ligada al perfil y a su config_sha256 (FR3.1), content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
        '422': { $ref: '#/components/responses/Problem' }
  /sessions/import:
    post:
      description: >
        Importa una transcripción en el formato de entrada de C6 con su bloque `consentimiento`. Sin el
        bloque se rechaza completa (salvo origen sintetico). La sesión nace cerrada a turnos nuevos
        (FR3.6) y el modo final se puede lanzar enseguida.
      x-veridicus-roles: [analista]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file, profile_name]
              properties:
                file: { type: string, format: binary, description: JSON o YAML de la entrada de C6 }
                profile_name: { type: string }
      responses:
        '201': { description: Sesión importada, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
        '413': { $ref: '#/components/responses/Problem' }
        '415': { $ref: '#/components/responses/Problem' }
        '422': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}:
    get:
      description: >
        Sondeo de la consola. Con `since` devuelve solo lo que cambió desde ese cursor. Cada llamada del
        dueño con la sesión abierta cuenta como latido (AC7.1.1). Registra el acceso (C23).
      x-veridicus-roles: [analista, admin]
      parameters:
        - { $ref: '#/components/parameters/SessionId' }
        - { name: since, in: query, schema: { type: string } }
      responses:
        '200': { description: Vista de la sesión, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
  /sessions/{session_id}/heartbeat:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '204': { description: Latido sin corridas en proceso }
  /sessions/{session_id}/turns:
    post:
      description: Un turno escrito; encola una corrida incremental con desde_turno = hasta_turno = n (FR4.9), salvo con el análisis en pausa.
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [hablante, texto, client_request_id]
              additionalProperties: false
              properties:
                hablante: { type: string, enum: [ENT, TEST] }
                texto: { type: string, minLength: 1 }
                client_request_id: { type: string, format: uuid, description: Evita turnos duplicados si el navegador reenvía }
      responses:
        '202':
          description: Turno numerado; la corrida queda en cola y no se espera
          content:
            application/json:
              schema:
                type: object
                required: [turn]
                properties:
                  turn: { $ref: '#/components/schemas/Turn' }
                  run: { $ref: '#/components/schemas/Run' }
        '409': { $ref: '#/components/responses/Problem' }
        '413': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}/transcript:
    post:
      description: Bloque pegado, dividido en turnos con la especificación versionada (FR3.3); una sola corrida desde su primer turno.
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [text, client_request_id]
              additionalProperties: false
              properties:
                text: { type: string, minLength: 1 }
                client_request_id: { type: string, format: uuid }
      responses:
        '202': { description: Turnos numerados en orden y una corrida en cola, content: { application/json: { schema: { type: object, required: [turns], properties: { turns: { type: array, items: { $ref: '#/components/schemas/Turn' } }, run: { $ref: '#/components/schemas/Run' } } } } } }
        '409': { $ref: '#/components/responses/Problem' }
        '413': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}/final-runs:
    post:
      description: Lanza (o relanza) el modo final sobre toda la transcripción. Cuenta el último lanzado. De dos lanzamientos simultáneos, uno recibe 202 y el otro 409 run.final_in_progress.
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '202': { description: Corrida final en cola, content: { application/json: { schema: { $ref: '#/components/schemas/Run' } } } }
        '409': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}/runs/{run_id}/retry:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/RunId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '202': { description: Misma corrida, mismo tramo, attempt + 1, content: { application/json: { schema: { $ref: '#/components/schemas/Run' } } } }
        '409': { description: La corrida no está en error (run.not_in_error) o la sesión no admite corridas (session.blocked, session.consent_withdrawn, session.terminated) }
  /sessions/{session_id}/runs/{run_id}/model-calls:
    get:
      x-veridicus-roles: [analista, admin]
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/RunId' }]
      responses:
        '200': { description: Registro de modelos de la corrida, solo lectura (US12.5), content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/ModelCall' } } } } }
  /sessions/{session_id}/analysis:
    patch:
      description: Pausar o reanudar el análisis. En pausa los turnos se guardan sin encolar y las corridas en cola se cancelan sin llamar a modelos (DD-06).
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema: { type: object, required: [paused], additionalProperties: false, properties: { paused: { type: boolean } } }
      responses:
        '200': { description: Sesión actualizada, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
  /sessions/{session_id}/terminate:
    post:
      description: Terminar sesión. Cancela lo encolado y cierra la sesión a turnos nuevos; se puede consolidar después.
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '200': { description: Sesión terminada, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
  /sessions/{session_id}/consent-withdrawal:
    post:
      description: Registra la retirada del consentimiento con actor y hora (AC15.2.3). Desde ese momento no se encola ni se analiza ninguna corrida (VE-10 (a)).
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '200': { description: Retirada registrada, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
  /sessions/{session_id}/resume:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '200': { description: Sesión suspendida vuelve a abierta desde el último turno registrado, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
        '409': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}/finalize:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '200': { description: Sesión finalizada (también desde suspendida); empieza la medición de MTTV, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
  /suggestions/{suggestion_id}/observation-views:
    post:
      x-veridicus-roles: [analista, admin]
      parameters: [{ $ref: '#/components/parameters/SuggestionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '204': { description: «Observaciones desplegadas» registradas (solo inserción) y acceso registrado (C23) }
  /suggestions/{suggestion_id}/decisions:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SuggestionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [state]
              additionalProperties: false
              properties:
                state: { type: string, enum: [accepted, edited, dismissed] }
                note: { type: string, description: Obligatoria y no vacía si state es dismissed }
                reformulation: { type: string, description: Obligatoria si state es edited; nunca cambia hecho, tipo, citas ni observaciones }
      responses:
        '201': { description: Decisión registrada en la ronda abierta, content: { application/json: { schema: { $ref: '#/components/schemas/ReviewSuggestion' } } } }
        '409': { description: Ronda bloqueada, observaciones no desplegadas, nota faltante o transición inválida }
  /sessions/{session_id}/reports:
    get:
      x-veridicus-roles: [analista, admin]
      parameters: [{ $ref: '#/components/parameters/SessionId' }]
      responses:
        '200': { description: Versiones del reporte, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/ReportVersion' } } } } }
    post:
      description: Consolidar. De dos consolidaciones simultáneas solo una gana; la otra recibe 409 report.conflict.
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '201': { description: Reporte consolidado, guardado y con su SHA-256, content: { application/json: { schema: { $ref: '#/components/schemas/ReportVersion' } } } }
        '409': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}/correction-rounds:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '201': { description: Abre o retoma la única ronda de corrección, que parte de la versión vigente }
  /reports/{report_version_id}/download:
    get:
      x-veridicus-roles: [analista, admin]
      parameters: [{ name: report_version_id, in: path, required: true, schema: { type: string, format: uuid } }]
      responses:
        '200':
          description: Markdown del reporte; el servidor recalcula el SHA-256 antes de enviarlo
          headers:
            X-Veridicus-SHA256: { schema: { type: string, pattern: '^[a-f0-9]{64}$' } }
          content:
            text/markdown: { schema: { type: string } }
        '409': { description: El archivo no coincide con el SHA-256 registrado (report.integrity_mismatch) o no hay versión (report.not_consolidated) }
  /reports/{report_version_id}/exports:
    post:
      description: Exportación con marca visible de usuario y hora, y el SHA-256 de la versión en la cabecera (US15.8). Solo el dueño y el admin; el investigador no (A-3).
      x-veridicus-roles: [analista, admin]
      x-veridicus-owner-only-for-role: analista
      parameters: [{ name: report_version_id, in: path, required: true, schema: { type: string, format: uuid } }, { $ref: '#/components/parameters/CsrfToken' }]
      responses:
        '201':
          description: Archivo exportado; cada exportación es un artefacto propio con su hash, registrado por C23
          headers:
            X-Veridicus-Export-SHA256: { schema: { type: string, pattern: '^[a-f0-9]{64}$' } }
          content:
            text/markdown: { schema: { type: string } }
  /conductor-observations/{observation_id}/decision:
    post:
      x-veridicus-priority: SHOULD
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters:
        - { name: observation_id, in: path, required: true, schema: { type: string, format: uuid } }
        - { $ref: '#/components/parameters/CsrfToken' }
      requestBody:
        required: true
        content:
          application/json:
            schema: { type: object, required: [status], additionalProperties: false, properties: { status: { type: string, enum: [approved, discarded] } } }
      responses:
        '200': { description: Decisión del analista sobre la aclaración, content: { application/json: { schema: { $ref: '#/components/schemas/ConductorObservation' } } } }
  /conductor-observations/{observation_id}/audio:
    get:
      x-veridicus-priority: SHOULD
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ name: observation_id, in: path, required: true, schema: { type: string, format: uuid } }]
      responses:
        '200': { description: Audio sintetizado en el clúster solo para una aclaración aprobada que cumple DT23, content: { audio/wav: { schema: { type: string, format: binary } } } }
        '409': { description: La aclaración no está aprobada (conductor_observation.not_approved) }
  /sessions/{session_id}/voice-turns:
    post:
      x-veridicus-priority: SHOULD
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters: [{ $ref: '#/components/parameters/SessionId' }, { $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema: { type: object, required: [audio, hablante, client_request_id], properties: { audio: { type: string, format: binary, description: WAV mono de 16 kHz o MP3 }, hablante: { type: string, enum: [ENT, TEST] }, client_request_id: { type: string, format: uuid } } }
      responses:
        '202': { description: Turno de voz numerado en transcribing, content: { application/json: { schema: { $ref: '#/components/schemas/Turn' } } } }
        '409': { description: Sin autorización de voz (session.voice_not_authorized) }
  /research-reports:
    get:
      x-veridicus-roles: [investigador]
      responses:
        '200': { description: Reportes subidos, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/ResearchReportSummary' } } } } }
    post:
      description: Sube un reporte de la CLI (C19). Lo que no cumple el esquema se rechaza con 422 research.invalid_report sin guardar nada (P12).
      x-veridicus-roles: [investigador]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema: { type: object, required: [file], properties: { file: { type: string, format: binary, description: JSON de C19 } } }
      responses:
        '201': { description: Reporte guardado (solo cifras), content: { application/json: { schema: { $ref: '#/components/schemas/ResearchReportDetail' } } } }
        '409': { description: El mismo archivo ya se subió (research.duplicate) }
        '413': { $ref: '#/components/responses/Problem' }
        '422': { $ref: '#/components/responses/Problem' }
  /research-reports/{research_report_id}:
    get:
      x-veridicus-roles: [investigador]
      parameters: [{ name: research_report_id, in: path, required: true, schema: { type: string, format: uuid } }]
      responses:
        '200': { description: Detalle, content: { application/json: { schema: { $ref: '#/components/schemas/ResearchReportDetail' } } } }
  /research-reports/compare:
    get:
      x-veridicus-priority: SHOULD
      x-veridicus-roles: [investigador]
      parameters:
        - { name: a, in: query, required: true, schema: { type: string, format: uuid } }
        - { name: b, in: query, required: true, schema: { type: string, format: uuid } }
      responses:
        '200': { description: Las cifras de los dos reportes lado a lado, content: { application/json: { schema: { type: array, minItems: 2, maxItems: 2, items: { $ref: '#/components/schemas/ResearchReportDetail' } } } } }
        '409': { description: Reportes de tipo distinto (research.not_comparable) }
  /acknowledgements:
    post:
      x-veridicus-demo: true
      x-veridicus-roles: [analista]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema: { type: object, required: [text_version], additionalProperties: false, properties: { text_version: { type: string } } }
      responses:
        '201': { description: Reconocimiento registrado (VE-04), content: { application/json: { schema: { $ref: '#/components/schemas/AcknowledgementStatus' } } } }
  /problem-reports:
    post:
      x-veridicus-demo: true
      x-veridicus-roles: [analista, admin]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [category, note]
              additionalProperties: false
              properties:
                category: { type: string, description: Catálogo de categorías de VE-15 }
                session_id: { type: string, format: uuid }
                suggestion_id: { type: string, format: uuid, description: Si viene, session_id se deriva de la sugerencia (UG-01) }
                note: { type: string, minLength: 1 }
      responses:
        '201':
          description: Reporte guardado; avisa, sin rechazar, si la nota trae 8 o más palabras seguidas de un turno (VE-15)
          content:
            application/json:
              schema: { type: object, required: [problem_report_id, testimony_warning], properties: { problem_report_id: { type: string, format: uuid }, testimony_warning: { type: boolean } } }
```

**Ruta de cada unidad.**

| Unidad | Rutas |
|---|---|
| U3 | `/auth/*`, `/users*`, el manejador de Problem Details y las reglas de rol y CSRF |
| U4 | `/notice`, `/profiles`, `POST /sessions`, `GET /sessions/{id}`, `/turns`, `/runs/{id}/retry`, `/runs/{id}/model-calls` |
| U5 | `/suggestions/*/observation-views`, `/suggestions/*/decisions` |
| U6 | `GET /sessions`, `/sessions/import`, `/transcript`, `/final-runs`, `/heartbeat`, `/resume`, `/analysis`, `/terminate`, `/consent-withdrawal` |
| U7 | `/finalize`, `/reports`, `/correction-rounds`, `/download`, `/exports` |
| U8 | `/conductor-observations/*/decision` |
| U9 | `/voice-turns`, `/conductor-observations/*/audio` |
| U12 | `/research-reports*` |
| U13 | `/acknowledgements`, `/problem-reports`, el estado del reconocimiento en `/auth/me` y el adaptador real de C23 |

El catálogo `ErrorCode` es uno solo (regla 6). Los seis códigos `analysis.*` y `anonymizer.incident`
traducen uno a uno los `error.codigo` de C6 (P8).

---

## C2 — Cola de corridas · se reescribe

**Antes:** un turno con sus 3 turnos previos, la instantánea del umbral y la versión del escenario.
**Ahora:** una corrida del contrato común. El sobre es de Veridicus (P9) y `entrada` es exactamente la
entrada de C6. El modo incremental necesita la transcripción hasta `hasta_turno`, no solo 3 turnos
previos (iteracion2 §2.6).

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus runs
  version: 2.0.0
channels:
  runs:
    address: 'veridicus:runs'
    description: Redis Stream; grupo de consumidores `semantic-agent`
    messages:
      RunRequested: { $ref: '#/components/messages/RunRequested' }
operations:
  publishRun:
    action: send
    channel: { $ref: '#/channels/runs' }
    summary: InterviewSession publica una corrida (y cada reintento humano con attempt + 1)
  analyzeRun:
    action: receive
    channel: { $ref: '#/channels/runs' }
    summary: AnalysisWorker llama a la biblioteca (C17) y hace XACK solo después de publicar el resultado (C3)
components:
  messages:
    RunRequested:
      contentType: application/json
      payload:
        type: object
        additionalProperties: true
        required: [schema_version, message_id, run_id, session_id, attempt, effective_config, config_sha256, entrada, enqueued_at, deadline_at]
        properties:
          schema_version: { type: string, pattern: '^2\.[0-9]+\.[0-9]+$' }
          message_id: { type: string, format: uuid }
          run_id: { type: string, format: uuid }
          session_id: { type: string, format: uuid }
          attempt: { type: integer, minimum: 1 }
          effective_config:
            $ref: 'contracts/profiles/effective-config.v1.json'
            description: Configuración efectiva fijada al crear la sesión (ADR-006, C18); el trabajador no lee el archivo de perfiles vigente para correr
          config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
          entrada:
            $ref: 'contracts/analyzer/v1/entrada.schema.json'
            description: Entrada de C6 con la transcripción hasta hasta_turno y el bloque consentimiento
          enqueued_at: { type: string, format: date-time }
          deadline_at: { type: string, format: date-time, description: Plazo de la corrida (C25, valor de NFR Requirements) }
```

**Entrega y fallos.** Al menos una vez. Si el trabajador muere, el mensaje queda pendiente y otro lo
reclama con `XAUTOCLAIM` tras el plazo de inactividad; tras 3 entregas sin confirmar va a
`veridicus:runs:failed` y la corrida pasa a `error` con `analysis.system`. Un mensaje que no cumple el
esquema o trae una versión mayor desconocida va directo a fallidos, sin analizar. InterviewSession nunca
publica una corrida de una sesión en pausa, terminada, bloqueada o con el consentimiento retirado.

**Cancelación.** Al pausar, terminar, retirar el consentimiento o bloquear la sesión, InterviewSession
marca `cancelled` las corridas en cola o en proceso y escribe en Redis la clave
`veridicus:run-cancelled:{run_id}` con vencimiento en `deadline_at`. El trabajador la consulta antes de
empezar la corrida y antes de cada llamada a un modelo; si existe, no llama a nada más, no publica
resultado y confirma el mensaje. Así ninguna llamada nueva sale después de la retirada (VE-10 (a)), y un
resultado que llegue igual se descarta en la ingesta (C3). El trabajador no escribe en la base
(ADR-002); la clave es la única escritura que hace InterviewSession fuera de la cola, y el trabajador
solo la lee. El tamaño máximo del mensaje lo acota C25.

## C3 — Cola de resultados · se reescribe

**Antes:** las calificaciones de un turno y los candidatos a alerta. **Ahora:** la salida de C6 de una
corrida, dentro del sobre de Veridicus (P9).

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus analysis results
  version: 2.0.0
channels:
  results:
    address: 'veridicus:results'
    description: Redis Stream; grupo de consumidores `session-api`
    messages:
      RunResult: { $ref: '#/components/messages/RunResult' }
operations:
  publishResult:
    action: send
    channel: { $ref: '#/channels/results' }
  ingestResult:
    action: receive
    channel: { $ref: '#/channels/results' }
    summary: InterviewSession valida la salida contra C6, la persiste de forma idempotente por (run_id, attempt) y pasa los hallazgos a HumanReview (C10)
components:
  messages:
    RunResult:
      contentType: application/json
      payload:
        type: object
        additionalProperties: true
        required: [schema_version, message_id, run_id, attempt, salida, finished_at]
        properties:
          schema_version: { type: string, pattern: '^2\.[0-9]+\.[0-9]+$' }
          message_id: { type: string, format: uuid }
          run_id: { type: string, format: uuid }
          attempt: { type: integer, minimum: 1 }
          salida: { $ref: 'contracts/analyzer/v1/salida.schema.json' }
          finished_at: { type: string, format: date-time }
```

**Ingesta.** Un resultado de un intento viejo, o de una corrida ya `cancelled` o vencida, se confirma y
se descarta sin crear filas. Una `salida` que no cumple C6 deja la corrida en `error` con
`analysis.invalid_output`. Con `estado: error`, InterviewSession guarda la corrida y su `registro`, sin
hallazgos. Con `error.codigo: incidente_anonimizacion`, o con una llamada del `registro` a un destino
externo que traiga `anonimizado: false`, bloquea la sesión con `anonymizer.incident`, rechaza corridas
nuevas y registra el incidente solo con IDs (VE-14, ADR-013). Las `observaciones_conductor` se guardan
como ConductorObservation (U8).

## C4 — Cola de indexación de escenarios · Retirado

Sale con TruthFrame (cambio 01). El *stream* `veridicus:indexing` no se crea.

## C5 — Colas de audio y transcripción (SHOULD, U9) · cambia

**Se mantiene** la forma de la revisión 1; **cambia** que el audio solo se acepta con
`autoriza_voz` y que el turno transcrito encola una corrida de C2 como un turno escrito.

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus speech
  version: 1.1.0
channels:
  audio:
    address: 'veridicus:audio'
    description: Redis Stream; grupo `audio-worker`
    messages:
      AudioToTranscribe:
        contentType: application/json
        payload:
          type: object
          required: [schema_version, message_id, turn_id, session_id, attempt, audio_format, audio_base64, retain_audio, deadline_at]
          properties:
            schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
            message_id: { type: string, format: uuid }
            turn_id: { type: string, format: uuid }
            session_id: { type: string, format: uuid }
            attempt: { type: integer, minimum: 1 }
            audio_format: { type: string, enum: [wav, mp3] }
            audio_base64: { type: string, description: Tamaño máximo en C25 (ver pregunta abierta) }
            retain_audio: { type: boolean, description: Copia de autoriza_conservar_audio (VE-08); el trabajador nunca guarda audio, solo lo indica a InterviewSession }
            deadline_at: { type: string, format: date-time }
  transcripts:
    address: 'veridicus:transcripts'
    description: Redis Stream; grupo `session-api`
    messages:
      TranscriptResult:
        contentType: application/json
        payload:
          type: object
          required: [schema_version, message_id, turn_id, attempt, outcome]
          properties:
            schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
            message_id: { type: string, format: uuid }
            turn_id: { type: string, format: uuid }
            attempt: { type: integer, minimum: 1 }
            outcome: { type: string, enum: [transcribed, error] }
            text: { type: string, description: Solo si outcome es transcribed }
            error_code: { type: string, enum: [analysis.system, analysis.timeout] }
            model_digest: { type: string }
operations:
  sendAudio: { action: send, channel: { $ref: '#/channels/audio' } }
  transcribe: { action: receive, channel: { $ref: '#/channels/audio' } }
  sendTranscript: { action: send, channel: { $ref: '#/channels/transcripts' } }
  ingestTranscript: { action: receive, channel: { $ref: '#/channels/transcripts' } }
```

Tras confirmar un audio, el trabajador lo borra del *stream* (`XDEL`). Sin `retain_audio` el audio
crudo no se conserva en ninguna parte (VE-08); con él, lo guarda InterviewSession en su volumen
(TurnAudio), nunca el trabajador. Whisper caído no se reintenta: el turno queda en error y el analista
graba de nuevo (regla de `project.md`).

## C6 — Contrato común del analizador v1.0.0 · se reescribe

**Antes:** el esquema de la salida del juez con tres calificaciones. **Ahora:** el contrato común del
TG (DT17) que implementan la biblioteca (C17), la CLI (C19), el trabajador (C2, C3) y la importación
(C1). Es una **fuente externa** (ADR-017): `veridicus` propone aquí la versión 1.0.0, el autor la aprueba
y la copia versionada vive en `contracts/analyzer/v1/` con una comprobación de su versión.

**Cambios frente a la propuesta v0.1 del cambio 01 §4** (los lleva el autor al repositorio principal):

| # | Cambio | Origen |
|---|---|---|
| 1 | `origen` admite `sintetico`, exento del bloque `consentimiento` (con una prueba que impide la exención con `corpus`) | ADR-017, A-4 |
| 2 | `pagina` y `pagina_fin` son opcionales; los turnos guiados no las traen | iteracion2 P4 = A |
| 3 | Bloque `consentimiento` obligatorio en la entrada, salvo `origen: sintetico` | A-4, P11 |
| 4 | `error.codigo` suma `anonimizador_no_disponible` e `incidente_anonimizacion` | FR4.2, UG-02, P8 |
| 5 | El bloque `registro` reemplaza el campo `modelo` | FR15.3, FR15.4, FR4.5, FR4.8, P10 |
| 6 | Cada cita lleva `avisos` (turno del entrevistador o plegado) | FR4.4 |
| 7 | `estado: error` implica también `observaciones_conductor` vacío | FR4.2, AUTONOMIA-05 |

**Entrada** (`contracts/analyzer/v1/entrada.schema.json`, mostrada en YAML):

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: veridicus/contracts/analyzer/v1/entrada
title: Entrada del contrato común del analizador
type: object
additionalProperties: false
required: [contrato, transcripcion, modo, perfil]
properties:
  contrato: { const: "1.0.0" }
  transcripcion:
    type: object
    additionalProperties: false
    required: [entrevista, origen, turnos]
    properties:
      entrevista: { type: string, minLength: 1, description: 'p. ej. "414-AA-00001" o el id de una entrevista guiada' }
      origen: { enum: [corpus, guiada, sintetico] }
      consentimiento:
        type: object
        additionalProperties: false
        required: [tipo, version_texto, autoriza_transferencia, autoriza_voz, autoriza_conservar_audio, registrado_en]
        properties:
          tipo: { enum: [persona, autoridad] }
          version_texto: { type: string, minLength: 1 }
          autoriza_transferencia: { type: boolean, description: Transferencia a un proveedor comercial, siempre seudonimizada }
          autoriza_voz: { type: boolean }
          autoriza_conservar_audio: { type: boolean }
          constancia: { type: string, description: Identificador de la constancia; nunca un nombre }
          registrado_en: { type: string, format: date-time }
        allOf:
          - if: { properties: { tipo: { const: autoridad } } }
            then: { required: [constancia] }
      turnos:
        type: array
        minItems: 1
        items:
          type: object
          additionalProperties: false
          required: [n, hablante, texto]
          properties:
            n: { type: integer, minimum: 1, description: Se cita como "T<n>" }
            hablante: { enum: [ENT, TEST] }
            pagina: { type: integer, minimum: 1 }
            pagina_fin: { type: integer, minimum: 1 }
            texto: { type: string }
            estado: { enum: [visible, plegado], default: visible }
    allOf:
      - if: { properties: { origen: { enum: [corpus, guiada] } } }
        then: { required: [consentimiento] }
  modo: { enum: [final, incremental] }
  hasta_turno: { type: integer, minimum: 1, description: Incremental; analiza hasta aquí }
  desde_turno: { type: integer, minimum: 1, description: Incremental; solo contradicciones con al menos una cita en un turno >= desde_turno }
  perfil: { type: string, minLength: 1, description: Nombre de un perfil aprobado (C18) }
allOf:
  - if: { properties: { modo: { const: incremental } } }
    then: { required: [hasta_turno, desde_turno] }
```

**Salida** (`contracts/analyzer/v1/salida.schema.json`):

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: veridicus/contracts/analyzer/v1/salida
title: Salida del contrato común del analizador
type: object
additionalProperties: false
required: [contrato, analizador, version, entrevista, prompt_sha256, perfil, config_sha256, fecha, estado, hallazgos, registro]
properties:
  contrato: { const: "1.0.0" }
  analizador: { const: incoherencias }
  version: { type: string, description: Versión del analizador (paquete de U11) }
  entrevista: { type: string }
  prompt_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
  perfil: { type: string }
  config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
  fecha: { type: string, format: date-time }
  estado: { enum: [ok, error] }
  error:
    type: object
    additionalProperties: false
    required: [codigo]
    properties:
      codigo: { enum: [salida_invalida, bloqueo_contenido, tiempo_agotado, proveedor, anonimizador_no_disponible, incidente_anonimizacion] }
  hallazgos: { type: array, items: { $ref: '#/$defs/hallazgo' } }
  observaciones_conductor:
    type: array
    description: Solo en modo incremental (DT23); vocabulario cerrado
    items:
      type: object
      additionalProperties: false
      required: [tipo, tema, turnos]
      properties:
        tipo: { const: aclaracion_neutra }
        tema: { type: string, minLength: 1, description: Nunca el texto de las citas ni «antes dijo» (VE-05) }
        turnos: { type: array, minItems: 1, items: { type: string, pattern: '^T[0-9]+$' } }
  registro: { $ref: '#/$defs/registro' }
allOf:
  - if: { properties: { estado: { const: error } } }
    then:
      required: [error]
      properties:
        hallazgos: { maxItems: 0 }
        observaciones_conductor: { maxItems: 0 }
  - if: { properties: { estado: { const: ok } } }
    then: { not: { required: [error] } }
$defs:
  cita:
    type: object
    additionalProperties: false
    required: [cita, turno]
    properties:
      cita: { type: string, minLength: 1, description: 'Texto literal; « […] » separa fragmentos del mismo turno en orden' }
      turno: { type: string, pattern: '^T[0-9]+$' }
      pagina: { type: integer, minimum: 1, description: Ausente si el turno no tiene página }
      avisos:
        type: array
        uniqueItems: true
        items: { enum: [turno_entrevistador, turno_plegado] }
  hallazgo:
    type: object
    additionalProperties: false
    required: [id, hecho, tipo, cita_a, cita_b, observaciones]
    properties:
      id: { type: string, pattern: '^.+-C[0-9]{2,}$', description: '<entrevista>-C<nn>' }
      hecho: { type: string, minLength: 1 }
      tipo: { enum: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
      actos: { type: array, items: { type: string } }
      cita_a: { $ref: '#/$defs/cita' }
      cita_b: { $ref: '#/$defs/cita' }
      observaciones: { type: string, minLength: 1, description: Justificación sin juicio sobre la persona }
  registro:
    type: object
    additionalProperties: false
    required: [llamadas, descartes, fragmentado, tokens_entrada, tokens_salida]
    properties:
      llamadas:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [papel, proveedor, modelo, tokens_entrada, tokens_salida, proveedor_alterno, anonimizado, fecha]
          properties:
            papel: { enum: [juez, verificador, verificador_permutado] }
            proveedor: { type: string }
            modelo: { type: string }
            version: { type: string }
            esfuerzo_o_cuantizacion: { type: string }
            motor: { type: string }
            semilla: { type: integer }
            tokens_entrada: { type: integer, minimum: 0 }
            tokens_salida: { type: integer, minimum: 0 }
            proveedor_alterno: { type: boolean }
            anonimizado: { type: boolean, description: false con un proveedor local; false con un destino externo es un incidente }
            fecha: { type: string, format: date-time }
      descartes:
        type: array
        description: Candidatos que no salieron; sin texto de citas
        items:
          type: object
          additionalProperties: false
          required: [motivo]
          properties:
            motivo: { enum: [cita_no_verificada, cita_en_otro_turno, marca_alterada, campo_faltante, rechazado_verificador, rechazado_permutacion, fuera_de_tramo, vocabulario_prohibido] }
            turno_a: { type: string, pattern: '^T[0-9]+$' }
            turno_b: { type: string, pattern: '^T[0-9]+$' }
      fragmentado:
        type: object
        additionalProperties: false
        required: [activo]
        properties:
          activo: { type: boolean }
          ventana: { type: integer, minimum: 1, description: En turnos (C25) }
          solapamiento: { type: integer, minimum: 0 }
      tokens_entrada: { type: integer, minimum: 0 }
      tokens_salida: { type: integer, minimum: 0 }
      costo_estimado: { type: number, minimum: 0, description: Según la tabla de precios de C18 (FR15.4); sin tope en el MVP }
      tabla_precios: { type: string, description: Versión de la tabla usada }
```

**Reglas que el esquema no puede expresar** (cada una con su prueba de nivel 0 en U11; las de
AUTONOMIA-05 con 100 % de ramas):
1. Cada cita se verifica contra su turno con la regla del piloto antes de salir; si pasó por el
   anonimizador, se restaura primero y se verifica después (FR4.4). Una cita que no aparece invalida el
   hallazgo y queda en `descartes`.
2. `cita_a` y `cita_b` están en turnos de la transcripción de entrada; con `modo: incremental`, al
   menos una está en un turno `>= desde_turno`.
3. Ningún campo de veracidad ni etiqueta sobre la persona; `hecho`, `observaciones` y `tema` pasan el
   escaneo de C8.
4. Dos corridas con la misma configuración dan el mismo `config_sha256` (FR14.2).

**Fixtures** en `contracts/analyzer/v1/fixtures/`: una entrada y una salida válidas por modo, y una
inválida por cada campo obligatorio, por `tipo` fuera del enum, por `estado: error` con hallazgos, por
`origen: corpus` sin consentimiento y por `origen: sintetico` sin él (válida). Todas sintéticas.

## C7 — Sugerencia de revisión · se reescribe

**Antes:** la alerta con fragmento, cita del documento, pasaje y CoT. **Ahora:** el hallazgo de C6
convertido en sugerencia de revisión con su estado (AUTONOMIA-03). Lo usan HumanReview para guardar, la
consola para mostrar y ReviewReport para el reporte. Estricto: `additionalProperties: false` y sin
campos de veracidad.

```yaml
# contracts/integrity/review-suggestion.v2.json (en YAML)
$schema: https://json-schema.org/draft/2020-12/schema
$id: veridicus/contracts/integrity/review-suggestion/v2
type: object
additionalProperties: false
required: [suggestion_id, session_id, first_run_id, hecho, tipo, cita_a, cita_b, observaciones, state, observations_viewed]
properties:
  suggestion_id: { type: string, format: uuid }
  session_id: { type: string, format: uuid }
  first_run_id: { type: string, format: uuid }
  hallazgo_id: { type: string, description: id del hallazgo en C6 de la corrida que lo propuso }
  hecho: { type: string, minLength: 1 }
  tipo: { enum: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
  actos: { type: array, items: { type: string } }
  cita_a: { $ref: 'contracts/analyzer/v1/salida.schema.json#/$defs/cita' }
  cita_b: { $ref: 'contracts/analyzer/v1/salida.schema.json#/$defs/cita' }
  observaciones: { type: string, minLength: 1 }
  state: { enum: [pending, accepted, edited, dismissed] }
  note: { type: string }
  reformulation: { type: string, description: Del analista; nunca reemplaza hecho, tipo, citas ni observaciones }
  observations_viewed: { type: boolean, description: El usuario actual desplegó las observaciones (FR6.2) }
  decided_by: { type: string, format: uuid }
  decided_at: { type: string, format: date-time }
```

`pair_key` (el par no ordenado de (turno, cita normalizada en espacios), FR4.9) es interno de
HumanReview y no sale en el contrato. La consola muestra «Sugerencia de revisión» y nunca un veredicto.

## C8 — Vocabulario prohibido, regla de DT23 y aviso de VE-01 · cambia

**Se mantiene** la lista con su forma de comparación; **cambia** el alcance del escaneo (VE-02:
`hecho`, `observaciones`, `tema`, reporte, catálogo de mensajes, nota y reformulación no) y **entran**
la regla de las aclaraciones neutras (VE-05) y el texto versionado del aviso (VE-01), que IntegrityPolicy
lee en ejecución (R-03 de Domain Design).

```yaml
# contracts/integrity/forbidden-vocabulary.v2.yaml
schema_version: 2.0.0
match:
  whole_word: true
  case_insensitive: true
  accent_insensitive: true
  excluded_spans: [cita_literal, analyst_text, notice_text]
terms:                                   # 1.0.0 conserva 9 términos (regla de project.md); cada ampliación, su PR con control negativo
  - mentiroso
  - mentirosa
  - miente
  - mintió
  - falso
  - falsa
  - verdadero
  - verdadera
  - engaño
categories_forbidden_in_schemas: [veracity_score, is_lying, truthfulness, veracidad, credibilidad]
scanned:
  - salida.hallazgos[].hecho
  - salida.hallazgos[].observaciones
  - salida.observaciones_conductor[].tema
  - reporte consolidado
  - catálogo de mensajes de la consola
---
# contracts/integrity/neutral-clarification.v1.yaml  (VE-05, DT23)
schema_version: 1.0.0
reject_if:
  mentions_contradiction: true           # «contradicción», «contradice», «incoherencia»
  phrases: ["antes dijo", "dijo antes", "se contradice"]
  cites_turn: true                       # «T<n>» o «turno <n>» dentro de tema
---
# contracts/integrity/notice.v1.yaml  (VE-01)
schema_version: 1.0.0
version: "1.0.0"
text: >
  Texto versionado del aviso de propósito limitado. Debe contener la frase base de VE-01; una prueba lo
  comprueba. La consola (C1 /notice) y el reporte muestran esta misma versión.
```

El texto exacto del aviso lo fija el autor en el PR de U1 (lo redacta y versiona el TG, VE-07).

## C9 — Lectura de pasajes del evaluador · Retirado

Sale con TruthFrame y `pgvector` (cambio 01). No existe el rol `veridicus_judge_ro`.

---

## C10 — HumanReview hacia InterviewSession y ConsoleApi (en proceso) · cambia

**Se mantiene** la forma; **cambia** el candidato (hallazgo de C6 en lugar de la alerta) y el despliegue
de la CoT pasa a «observaciones desplegadas».

```python
# contracts/python/human_review.py  — v2.0.0
from typing import Protocol, Literal
from uuid import UUID
from datetime import datetime
from contracts.analyzer.v1 import Hallazgo        # modelo generado de C6; campos en español (P14)

DecisionState = Literal["accepted", "edited", "dismissed"]

class Actor(Protocol):
    user_id: UUID | None                 # None = sistema (al proponer)
    at: datetime

class SuggestionProposer(Protocol):
    def propose(self, uow: "UnitOfWork", session_id: UUID, run_id: UUID,
                hallazgos: list[Hallazgo]) -> list[UUID]:
        """Guarda cada hallazgo como sugerencia pendiente (C7).
        Une sin duplicar por el par no ordenado de (turno, cita normalizada en espacios) (FR4.9):
        un hallazgo ya decidido conserva su estado y su historial.
        Si la sesión no tiene ronda, abre la ronda 1 en la misma transacción (ADR-007).
        Rechaza un hallazgo sin sus campos obligatorios (AUTONOMIA-05).
        Con todas las rondas bloqueadas rechaza con review.round_locked."""

class ReviewCommands(Protocol):
    def record_observations_view(self, uow: "UnitOfWork", suggestion_id: UUID, actor: Actor) -> None: ...
    def decide(self, uow: "UnitOfWork", suggestion_id: UUID, state: DecisionState,
               note: str | None, reformulation: str | None, actor: Actor) -> UUID:
        """El actor ya viene autorizado como dueño (ADR-009).
        Errores: review.observations_not_viewed, review.note_required,
        review.invalid_transition, review.round_locked."""
```

## C11 — Lo que ReviewReport usa de los demás módulos (en proceso) · cambia

**Sale** `ScenarioReader` (TruthFrame); **cambia** la instantánea de la sesión (corridas, registro de
modelos y perfil en lugar de paquetes de traspaso) y **se renombra** el consumidor (ReviewReport, antes
ForensicReport).

```python
# contracts/python/report_ports.py  — v2.0.0
class SessionReader(Protocol):           # dueño: InterviewSession (U4, U6)
    def snapshot(self, uow: "UnitOfWork", session_id: UUID) -> "SessionSnapshot":
        """Estado, dueño, perfil y config_sha256, finalized_at, turnos con hablante, página y estado,
        corridas con su registro de modelos y su modo fragmentado, y cuántas corridas siguen
        queued o processing. Sin consentimiento con datos personales (no los hay, P11)."""

class ReviewRounds(Protocol):            # dueño: HumanReview (U5)
    def open_round(self, uow: "UnitOfWork", session_id: UUID, for_update: bool = False) -> "RoundView | None":
        """Con for_update=True bloquea la fila de la ronda; el orden de bloqueo es sesión → ronda
        (regla de project.md)."""
    def pending_count(self, uow: "UnitOfWork", round_id: UUID) -> int: ...
    def decisions(self, uow: "UnitOfWork", round_id: UUID) -> list["SuggestionWithDecision"]: ...
    def lock_round(self, uow: "UnitOfWork", round_id: UUID, report_version_id: UUID,
                   actor: Actor) -> None:
        """Falla con report.conflict si la ronda ya está bloqueada (una sola consolidación gana)."""
    def open_correction_round(self, uow: "UnitOfWork", session_id: UUID, actor: Actor) -> UUID:
        """Abre o retoma la única ronda de corrección de la sesión. No guarda la versión de la que parte:
        ReviewReport la deduce de la ronda bloqueada anterior (R-01 de Domain Design)."""
```

`UnitOfWork` es la transacción compartida de `session-api`: la consolidación lee, escribe la versión
del reporte y bloquea la ronda en una sola transacción (ADR-001, AC6.1.6). Ningún módulo abre su
propia transacción dentro de estas llamadas. `for_update` sale de las precisiones de NFR Requirements
de la primera pasada (regla de `project.md`) y aquí entra al contrato.

## C12 — IdentityAccess hacia ConsoleApi (en proceso) · cambia

**Se mantiene** la forma; **cambia** el conjunto de roles: entra `investigador` (FR1.2).

```python
# contracts/python/identity.py  — v2.0.0
Role = Literal["analista", "admin", "investigador"]

class Principal(Protocol):
    user_id: UUID; username: str; role: Role

class Authenticator(Protocol):
    def login(self, uow: "UnitOfWork", username: str, password: str) -> tuple[Principal, str]:
        """Devuelve el principal y el identificador de sesión para la cookie.
        Mismo error (auth.invalid_credentials) para usuario inexistente y contraseña errónea."""
    def resolve(self, uow: "UnitOfWork", session_token: str) -> Principal:
        """auth.unauthenticated si la sesión no existe, venció o el usuario está desactivado."""
    def csrf_token(self, session_token: str) -> str: ...
    def logout(self, uow: "UnitOfWork", session_token: str) -> None: ...

class UserAdmin(Protocol):
    def create(self, uow: "UnitOfWork", username: str, password: str, role: Role, actor: Principal) -> UUID: ...
    def update(self, uow: "UnitOfWork", user_id: UUID, active: bool | None, role: Role | None,
               actor: Principal) -> None:
        """Desactivar revoca todas las sesiones del usuario. Deja fila en UserChange."""
```

## C13 — Puerto ModelGateway · se reescribe

**Antes:** `judge`, `embed`, `transcribe` y `synthesize`, con destino siempre interno. **Ahora:** una
operación genérica `generate(papel, mensajes, esquema)` (FR15.1, DT21); sale `embed`. Vive en
`libs/model_gateway/` (U11).

```python
# libs/model_gateway/port.py  — contrato v2.0.0
from typing import Protocol, Literal, Any
from datetime import datetime

Papel = Literal["juez", "verificador", "verificador_permutado"]

class Mensaje(Protocol):
    rol: Literal["system", "user", "assistant"]
    contenido: str                       # el testimonio va como JSON dentro del mensaje user (FR4.6)

class GenerateRequest(Protocol):
    papel: Papel
    destino: "Destino"                   # proveedor, modelo, versión y parámetros del papel, de C18
    mensajes: list[Mensaje]
    esquema: dict[str, Any]              # JSON Schema de la respuesta; salida JSON forzada
    semilla: int | None
    timeout_s: float                     # explícito siempre (C25)

class LlamadaRegistrada(Protocol):       # una fila de salida.registro.llamadas (C6)
    papel: Papel; proveedor: str; modelo: str; version: str | None
    esfuerzo_o_cuantizacion: str | None; motor: str | None; semilla: int | None
    tokens_entrada: int; tokens_salida: int; proveedor_alterno: bool; anonimizado: bool
    fecha: datetime

class GenerateResult(Protocol):
    contenido: dict[str, Any]            # ya parseado; quien llama lo valida contra su esquema
    llamada: LlamadaRegistrada

class ModelGateway(Protocol):
    def generate(self, req: GenerateRequest) -> GenerateResult:
        """Errores tipados (FR15.2): ContentBlocked, Timeout, ProviderError, InvalidOutput,
        AnonymizerUnavailable (fallo cerrado: no salió ninguna llamada).
        Un destino externo pasa siempre por el anonimizador: C20 en la CLI, C21 en el clúster."""
    def transcribe(self, audio: bytes, audio_format: str, timeout_s: float) -> "Transcript": ...  # SHOULD, solo local
    def synthesize(self, text: str, timeout_s: float) -> bytes: ...                              # SHOULD, solo local
```

**Adaptadores.**
- `local`: servidor compatible con OpenAI (C14); `anonimizado: false` es correcto.
- `anonymizer`: todo destino externo. En la CLI llama al módulo en proceso (C20); en `semantic-agent`,
  al proxy por HTTP (C21). No hay otro camino a un destino externo: los adaptadores nativos de los
  proveedores no se instalan en `semantic-agent` (P13), y una comprobación de import-linter lo impide.
- *fakes* deterministas para los niveles 0 y 1, con este mismo `Protocol`.

**Arranque.** Al construir el gateway con el perfil se valida, antes de cualquier llamada (FR14.3): que
todo papel con destino externo tenga el adaptador `anonymizer` configurado (en el clúster, la URL de
`anonymizer-proxy`, que debe responder en `/readyz`), que todo destino local sea interno del clúster o
de la máquina, y que el perfil sea válido según C18. Si algo falla, el servicio no arranca o la CLI
termina con código ≠ 0. Los reintentos solo ante conexión rechazada o `502`/`503`/`504`, dentro del
plazo de la corrida (regla de `project.md`).

## C14 — Servidores de modelos locales (API compatible con OpenAI) · cambia

**Se mantiene** el protocolo (P7); **cambia** el alcance: solo modelos locales (juez y verificador
locales, Whisper, TTS); **sale** `/v1/embeddings`.

```yaml
openapi: 3.1.0
info:
  title: Subconjunto de la API compatible con OpenAI que usa Veridicus
  version: 2.0.0
paths:
  /v1/chat/completions:
    post:
      description: >
        Juez y verificador locales (llama.cpp, vLLM u Ollama). Veridicus envía model, messages,
        temperature, seed (si el servidor la admite) y response_format con json_schema; el razonamiento
        va apagado (validación en ZINE). Usa de la respuesta choices[0].message.content y usage.
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [model, messages, response_format]
              properties:
                model: { type: string }
                messages: { type: array, items: { type: object, required: [role, content] } }
                temperature: { type: number }
                seed: { type: integer }
                response_format: { type: object, required: [type, json_schema], properties: { type: { const: json_schema } } }
      responses:
        '200': { description: Respuesta del modelo }
  /v1/audio/transcriptions:
    post:
      description: Whisper en CPU (SHOULD, U9)
      responses:
        '200': { description: '{ "text": "..." }' }
  /v1/audio/speech:
    post:
      description: TTS local (SHOULD, U9); si el servidor no la ofrece, U9 escribe su adaptador
      responses:
        '200': { description: audio/wav }
```

Los servidores del clúster los despliega U2 con su artefacto fijado por `sha256`; en ZINE, el humano
los lanza dentro de un trabajo de SLURM (AUTONOMIA-01). El mismo contrato sirve en los dos.

## C15 — Métrica de descartes (SHOULD) · cambia

**Antes:** la razón AIR con propuesta de umbral. **Ahora:** solo la razón de descartes como señal en
Grafana (P13 de iteracion2, US10.8); sale la propuesta de umbral.

```yaml
# contracts/metrics/review.v2.yaml
schema_version: 2.0.0
endpoint: GET /metrics  # session-api, puerto interno, sin autenticación de usuario, no expuesto al navegador
metrics:
  - name: veridicus_review_decisions_total
    type: counter
    labels: [state]                      # accepted | edited | dismissed
  - name: veridicus_session_dismissal_ratio
    type: gauge
    labels: [session_id]
    description: >
      Fracción de sugerencias descartadas entre las últimas W decididas de la sesión (W en C25). La
      regla de U2 alerta por encima de 0.25 (AC10.8.1); nunca cambia un perfil ni un prompt (AC10.8.2).
  - name: veridicus_run_duration_seconds
    type: histogram
    labels: [mode, outcome]              # incremental | final ; ok | error
  - name: veridicus_runs_total
    type: counter
    labels: [mode, error_code]           # error_code vacío si ok
```

Las etiquetas solo llevan identificadores y enumeraciones, nunca texto (NFR10).

## C16 — Salud de cada servicio · cambia

**Se mantiene** la forma; **cambia** lo que comprueba `/readyz` (perfiles y anonimizador en lugar del
umbral) y entra el estado informativo del registro de acceso (UG-09).

```yaml
openapi: 3.1.0
info:
  title: Salud de los servicios de Veridicus
  version: 2.0.0
paths:
  /healthz:
    get:
      security: []
      summary: Vida del proceso (sonda liveness)
      responses:
        '200': { description: '{ "status": "ok" }' }
  /readyz:
    get:
      security: []
      summary: Listo para trabajar (sonda readiness y scripts/smoke.sh)
      description: >
        200 solo si el archivo de perfiles es válido (C18), las claves que referencia existen, la base y
        Redis responden, y los destinos del servicio responden: servidores locales internos y, si algún
        perfil tiene destino externo, `anonymizer-proxy`. En `session-api`, `checks` incluye
        `access_log: not_configured` mientras U13 no exista, como dato informativo, sin dejar de
        responder 200 (UG-09).
      responses:
        '200': { description: '{ "status": "ready", "checks": [{ "name": "access_log", "ok": true, "info": "not_configured" }] }' }
        '503': { description: '{ "status": "not_ready", "checks": [{ "name": "redis", "ok": false }] } — sin datos sensibles' }
```

`semantic-agent`, `audio-worker` y `anonymizer-proxy` exponen estas dos rutas en un puerto interno
aunque no tengan API de negocio.

## C17 — API pública de la biblioteca del analizador (en proceso) · nuevo

La única entrada al núcleo para el trabajador, la CLI y, más adelante, el plugin de `sistema` (DT20).
No importa Redis, Kubernetes ni controladores de base de datos (FR13.1, import-linter).

```python
# libs/incoherence_analyzer/api.py  — contrato v1.0.0
from typing import Protocol
from contracts.analyzer.v1 import Entrada, Salida      # modelos generados de C6 (P14)
from libs.execution_profiles import EffectiveConfig    # C18
from libs.model_gateway.port import ModelGateway       # C13

class CancelCheck(Protocol):
    def __call__(self) -> bool: ...      # True = la corrida se canceló; el núcleo no hace más llamadas

class IncoherenceAnalyzer(Protocol):
    def analyze(self, entrada: Entrada, config: EffectiveConfig, gateway: ModelGateway,
                cancelled: CancelCheck | None = None) -> Salida:
        """Implementa C6. Antes de cualquier llamada:
        - rechaza una entrada que no cumple C6, una transcripción sin consentimiento (salvo
          origen sintetico) y un perfil con destino externo que el consentimiento no autoriza;
          en esos casos lanza InputRejected y no devuelve Salida.
        Después, nunca lanza por un fallo del modelo o del anonimizador: devuelve estado error
        con su codigo, hallazgos vacíos y el registro de lo que alcanzó a llamar (FR4.2).
        Si cancelled() devuelve True, no hace más llamadas y lanza Cancelled sin devolver Salida."""

class ProfileResolver(Protocol):         # para la CLI: del nombre del perfil a su configuración
    def resolve(self, profile_name: str) -> EffectiveConfig: ...
```

**Errores antes de llamar** (`InputRejected`, con un `code` del catálogo C1): `import.invalid_transcript`,
`session.consent_missing`, `profile.not_approved`, `profile.transfer_not_authorized`. En el trabajador
eso no debería ocurrir (InterviewSession ya validó); si ocurre, la corrida pasa a `error` con
`analysis.system` y el mensaje va a fallidos.

## C18 — Perfiles de ejecución y tabla de precios · nuevo

Archivos versionados que solo cambian por PR (FR9.2, ADR-012). ExecutionProfiles los valida igual en la
biblioteca, la CLI, el trabajador, `session-api` y `anonymizer-proxy`.

```yaml
# contracts/profiles/profiles.schema.v1.yaml — esquema de config/profiles.yaml
$schema: https://json-schema.org/draft/2020-12/schema
type: object
additionalProperties: false
required: [schema_version, profiles]
properties:
  schema_version: { const: "1.0.0" }
  profiles:
    type: object
    additionalProperties: { $ref: '#/$defs/profile' }
$defs:
  destino:
    type: object
    additionalProperties: false
    required: [proveedor, modelo, alcance]
    properties:
      proveedor: { enum: [anthropic, google, openai, local] }
      modelo: { type: string }
      version: { type: string }
      familia: { type: string, description: Para la regla de familias distintas (FR14.4) }
      alcance: { enum: [local, externo] }
      base_url: { type: string, description: Solo local; interno del clúster o de la máquina }
      api_key_ref: { type: string, description: 'Nombre de la variable o del Secret, p. ej. VERIDICUS_ANTHROPIC_API_KEY; nunca el valor' }
      parametros:
        type: object
        additionalProperties: false
        properties:
          esfuerzo: { type: string }
          temperatura: { type: number }
          cuantizacion: { type: string }
          motor: { type: string }
          semilla: { type: integer }
  profile:
    type: object
    additionalProperties: false
    required: [proposito, juez, verificador, permutacion]
    properties:
      proposito: { enum: [evaluacion, demostracion, produccion] }
      juez: { $ref: '#/$defs/destino' }
      verificador: { $ref: '#/$defs/destino' }
      permutacion: { type: boolean, description: FR10.5 }
      proveedor_alterno: { $ref: '#/$defs/destino' }
      fragmentado:
        type: object
        additionalProperties: false
        required: [activo]
        properties:
          activo: { type: boolean }
          ventana: { type: integer, minimum: 1 }
          solapamiento: { type: integer, minimum: 0 }
      misma_familia_declarada: { type: boolean, default: false }
      solo_lotes: { type: boolean, description: Perfiles locales en CPU (validación en ZINE) }
```

**Configuración efectiva** (`contracts/profiles/effective-config.v1.json`): el perfil resuelto con las
cifras de C25 que aplica, sin `api_key_ref` resueltas, y `prompt_sha256`. Es lo que viaja en C2 y lo que
se guarda en la sesión. `config_sha256` es el SHA-256 de su serialización JSON canónica (claves
ordenadas, sin espacios, UTF-8): misma configuración, misma huella (FR14.2).

**Reglas de validación** (cada una con su control negativo; FR14.3, FR14.4, A-4): archivo inválido;
destino `externo` sin anonimizador delante; `api_key_ref` sin valor en el entorno; `proposito:
evaluacion` con la misma `familia` en juez y verificador; `misma_familia_declarada` fuera de
`demostracion`; destino `local` con `base_url` externa; y, al correr, destino `externo` sin
`autoriza_transferencia` en el consentimiento.

```yaml
# contracts/profiles/prices.schema.v1.yaml — esquema de config/prices.yaml
type: object
additionalProperties: false
required: [schema_version, version, moneda, precios]
properties:
  schema_version: { const: "1.0.0" }
  version: { type: string }
  moneda: { const: USD }
  precios:
    type: array
    items:
      type: object
      additionalProperties: false
      required: [proveedor, modelo, entrada_por_millon, salida_por_millon]
      properties:
        proveedor: { type: string }
        modelo: { type: string }
        entrada_por_millon: { type: number, minimum: 0 }
        salida_por_millon: { type: number, minimum: 0 }
```

`config/profiles.yaml` trae al menos `comercial-piloto` y `todo-local` (FR14.1). Los modelos concretos
los fija NFR Requirements.

## C19 — Reporte de la CLI y códigos de salida · nuevo

El reporte que escribe la CLI (corrida por lotes o evaluación) y que el investigador sube a la consola
(C1 `/research-reports`) o copia al repositorio principal. **No tiene campos de texto libre** (P12): los
hallazgos con sus citas van en los archivos de salida de C6, uno por entrevista, nunca dentro del
reporte.

```yaml
# contracts/cli/report.schema.v1.yaml
$schema: https://json-schema.org/draft/2020-12/schema
type: object
additionalProperties: false
required: [schema_version, tipo, analizador_version, contrato, perfil, config_sha256, prompt_sha256, fecha, corridas, totales]
properties:
  schema_version: { const: "1.0.0" }
  tipo: { enum: [corrida, evaluacion] }
  analizador_version: { type: string, pattern: '^[0-9]+\.[0-9]+\.[0-9]+$' }
  contrato: { const: "1.0.0" }
  perfil: { type: string, pattern: '^[a-z0-9-]+$' }
  config_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
  prompt_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
  dataset_version: { type: string, pattern: '^[0-9]+\.[0-9]+\.[0-9]+$', description: Solo evaluacion }
  fecha: { type: string, format: date-time }
  corridas:
    type: array
    items:
      type: object
      additionalProperties: false
      required: [entrevista_sha256, estado, hallazgos, descartes, llamadas]
      properties:
        entrevista_sha256: { type: string, pattern: '^[a-f0-9]{64}$', description: Hash del archivo de entrada, nunca su id ni su texto }
        estado: { enum: [ok, error] }
        codigo: { enum: [salida_invalida, bloqueo_contenido, tiempo_agotado, proveedor, anonimizador_no_disponible, incidente_anonimizacion] }
        hallazgos: { type: integer, minimum: 0, description: Cuántos, no cuáles }
        descartes: { type: object, additionalProperties: { type: integer, minimum: 0 }, propertyNames: { enum: [cita_no_verificada, cita_en_otro_turno, marca_alterada, campo_faltante, rechazado_verificador, rechazado_permutacion, fuera_de_tramo, vocabulario_prohibido] } }
        llamadas: { type: array, items: { $ref: 'contracts/analyzer/v1/salida.schema.json#/$defs/registro/properties/llamadas/items' } }
  totales:
    type: object
    additionalProperties: false
    required: [tokens_entrada, tokens_salida]
    properties:
      tokens_entrada: { type: integer, minimum: 0 }
      tokens_salida: { type: integer, minimum: 0 }
      costo_estimado: { type: number, minimum: 0 }
      tabla_precios: { type: string }
  metricas:
    type: object
    additionalProperties: false
    description: Solo evaluacion (NFR4); los umbrales los fija NFR Requirements
    properties:
      precision: { type: number, minimum: 0, maximum: 1 }
      sensibilidad: { type: number, minimum: 0, maximum: 1 }
      citas_verificadas: { type: number, minimum: 0, maximum: 1 }
      error_formato_json: { type: number, minimum: 0, maximum: 1 }
      consistencia_orden_inverso: { type: number, minimum: 0, maximum: 1 }
      acuerdo_3_corridas: { type: number, minimum: 0, maximum: 1 }
      fuga_anonimizador: { type: integer, minimum: 0 }
  tabla_sesgo:
    type: array
    description: VE-17; por tipo de hecho y por perfil
    items:
      type: object
      additionalProperties: false
      required: [tipo, perfil_conjunto, esperadas, encontradas]
      properties:
        tipo: { enum: [fecha, numero, lugar, persona, negacion, secuencia, otro] }
        perfil_conjunto: { type: string, pattern: '^[a-z0-9_-]+$', description: Etiqueta del conjunto sintético, no texto }
        esperadas: { type: integer, minimum: 0 }
        encontradas: { type: integer, minimum: 0 }
```

Los `pattern` cierran las cadenas que sí existen (versiones, hashes, nombres de perfil y etiquetas): una
cadena con espacios o testimonio no valida. La consola rechaza con `422` `research.invalid_report` y no
guarda nada; la prueba del *canary* de FR13.5 comprueba que el texto no aparece en ninguna columna ni
log.

**Códigos de salida de la CLI** (FR13.2, FR14.3, R-04):

| Código | Cuándo |
|---|---|
| 0 | Todas las corridas terminaron, aunque alguna tenga `estado: error` |
| 2 | Argumento inválido, archivo de entrada que no cumple C6 o transcripción sin consentimiento (antes de cualquier llamada) |
| 3 | Perfil inválido, destino externo sin anonimizador, clave ausente o transferencia no autorizada (antes de cualquier llamada) |
| 4 | Una corrida terminó con `incidente_anonimizacion`: el lote se detiene sin lanzar más corridas |
| 5 | Error inesperado del proceso |

## C20 — Módulo del anonimizador (en proceso) · nuevo

Lo que la CLI usa en el mismo proceso, y lo que `anonymizer-proxy` envuelve por HTTP (C21). Vive en
`libs/anonymizer/` (U10). Es un módulo guardia con 100 % de ramas.

```python
# libs/anonymizer/api.py  — contrato v1.0.0
from typing import Protocol
from libs.model_gateway.port import GenerateRequest, GenerateResult

class AnonymizingProvider(Protocol):
    def generate(self, req: GenerateRequest) -> GenerateResult:
        """Para un destino externo:
        1. comprueba que el dominio del proveedor está en la lista (FR11.4); si no, AnonymizerUnavailable;
        2. seudonimiza los mensajes con marcas coherentes en toda la llamada ([PERSONA_3]) y guarda la
           tabla solo en memoria, durante la llamada, nunca en logs ni en disco (FR11.3);
        3. llama con el adaptador nativo del proveedor (C22) usando la clave de api_key_ref;
        4. restaura las marcas en la respuesta y marca como inválida la parte cuya marca alteró el
           modelo (el núcleo la descarta con motivo marca_alterada);
        5. devuelve llamada.anonimizado = True.
        Si cualquier paso antes del 3 falla, lanza AnonymizerUnavailable y no sale ninguna llamada
        (falla cerrado). Un destino local nunca llega aquí."""
```

La tabla de correspondencia no sale del módulo. Las pruebas de AUTONOMIA-04 se hacen aquí: el
*payload* que llega al adaptador nativo no contiene ninguna entidad sembrada del conjunto sintético, y con
el módulo en fallo el doble del adaptador nativo no recibe ninguna llamada.

## C21 — `anonymizer-proxy` por HTTP dentro del clúster · nuevo

La misma operación de C20 por la red (P13). Solo la llama `semantic-agent`; la `NetworkPolicy` de U2
admite la entrada solo desde ese pod.

```yaml
openapi: 3.1.0
info:
  title: Veridicus anonymizer-proxy
  version: 1.0.0
servers:
  - url: http://veridicus-anonymizer-proxy:8080
paths:
  /v1/generate:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              additionalProperties: false
              required: [schema_version, run_id, papel, destino, mensajes, esquema, timeout_s]
              properties:
                schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
                run_id: { type: string, format: uuid, description: Solo para logs con IDs }
                papel: { enum: [juez, verificador, verificador_permutado] }
                destino: { $ref: 'contracts/profiles/profiles.schema.v1.yaml#/$defs/destino' }
                mensajes: { type: array, items: { type: object, required: [rol, contenido], properties: { rol: { enum: [system, user, assistant] }, contenido: { type: string } } } }
                esquema: { type: object }
                semilla: { type: integer }
                timeout_s: { type: number, exclusiveMinimum: 0 }
      responses:
        '200':
          description: Respuesta restaurada y su registro
          content:
            application/json:
              schema:
                type: object
                required: [contenido, llamada]
                properties:
                  contenido: { type: object }
                  marcas_alteradas: { type: array, items: { type: string }, description: Rutas JSON de las partes invalidadas }
                  llamada: { $ref: 'contracts/analyzer/v1/salida.schema.json#/$defs/registro/properties/llamadas/items' }
        '422': { description: 'Petición inválida o destino fuera de la lista: { "code": "analysis.anonymizer_unavailable" }' }
        '502': { description: 'Error del proveedor: { "code": "analysis.provider" }' }
        '503': { description: 'Anonimizador no disponible; no salió ninguna llamada: { "code": "analysis.anonymizer_unavailable" }' }
        '504': { description: 'Tiempo agotado: { "code": "analysis.timeout" }' }
        '451': { description: 'Bloqueo de contenido del proveedor: { "code": "analysis.content_blocked" }' }
```

El adaptador `anonymizer` de C13 traduce cada respuesta a los errores tipados del puerto. Un `503` del
proxy, o no poder conectarse a él, es `AnonymizerUnavailable` y la corrida termina en
`anonimizador_no_disponible`. Los logs del proxy solo llevan `run_id`, papel, proveedor y códigos.

## C22 — Proveedores comerciales (externo) · nuevo

La única frontera que cruza el clúster. La consume el adaptador nativo de cada proveedor dentro del
Anonymizer (P13); `veridicus` no controla estas API, solo fija el subconjunto que usa.

| Proveedor | Dominio en la lista | Operación usada | Salida JSON forzada |
|---|---|---|---|
| Anthropic | `api.anthropic.com` | Messages API | Esquema de salida de la herramienta o JSON del proveedor |
| Google | `generativelanguage.googleapis.com` | `generateContent` | `responseSchema` |
| OpenAI | `api.openai.com` | Responses o Chat Completions | `json_schema` |

**Reglas.** Solo HTTPS por 443; la `NetworkPolicy` (U2) solo da salida a `anonymizer-proxy` y la lista
de dominios la impone el módulo (FR11.4, P10 de iteracion2), junto con la lista blanca de CoreDNS. Solo
viaja texto seudonimizado. Las claves viven en un `Secret` que crea el humano y que se monta solo en el
pod `anonymizer-proxy` (FR12.4, P13); en la CLI, en variables de entorno de la máquina, nunca en el
repositorio. El bloqueo de contenido del proveedor se traduce a `bloqueo_contenido`, y el núcleo usa el
`proveedor_alterno` del perfil si lo hay (FR15.2).

## C23 — Puerto `AccessLog` (en proceso) · nuevo

La interfaz la define U7 y el adaptador real lo aporta U13; ConsoleApi la cablea y la llama
(UG-09, ADR-016). EthicsGovernance no importa nada de ConsoleApi.

```python
# contracts/python/access_log.py  — v1.0.0
ResourceType = Literal["session", "suggestion", "report_version", "report_export"]

class AccessLog(Protocol):
    def record(self, uow: "UnitOfWork", user_id: UUID, resource_type: ResourceType,
               resource_id: UUID, export_sha256: str | None = None) -> None:
        """Solo inserción y sin texto (VE-11). export_sha256 solo para report_export (A-3)."""
```

**Adaptador por defecto** (mientras U13 no exista): no registra, deja un aviso en el log solo con IDs al
arrancar y en cada exportación, y `/readyz` informa `access_log: not_configured` sin dejar de responder
200 (C16). La prueba de nivel 0 de U7 lo verifica; la de nivel 1 de U13 verifica que el adaptador real
está conectado y que la exportación queda registrada.

## C24 — Puertos de borrado para la retención (en proceso) · nuevo

El Job de retención de U13 (demostración, lo lanza el humano) borra una sesión vencida en el orden
inverso de las referencias (components, EthicsGovernance). Cada unidad borra solo lo suyo.

```python
# contracts/python/retention.py  — v1.0.0
class Purgeable(Protocol):
    def purge_session(self, uow: "UnitOfWork", session_id: UUID) -> "PurgeReceipt":
        """Borra lo de la sesión que pertenece a este módulo y devuelve los IDs borrados y, en
        ReviewReport, los SHA-256 de los reportes. Nunca devuelve texto."""

# Orden del Job: (1) EthicsGovernance.ProblemReport de la sesión (incluidos los ligados por sugerencia,
# UG-01); (2) ReviewReport: ReportExport y ReportVersion de la más nueva a la más antigua, con sus
# archivos; (3) HumanReview: ObservationsView, ReviewDecision, ReviewSuggestion, ReviewRound;
# (4) InterviewSession: todo lo de la sesión y por último InterviewSessionRecord.
```

Solo el usuario de base de datos del Job tiene `DELETE` (A-2). El acta (RetentionAct) y el registro de
acceso sobreviven sin clave foránea.

## C25 — Catálogo único de límites · nuevo

Toda cifra de límite vive aquí; el contrato y los servicios la leen de este archivo y una variable de
entorno solo puede bajarla, nunca subirla (regla de `project.md`). Las cifras las fija NFR Requirements.

```yaml
# contracts/limits.v1.yaml — forma; los valores son de NFR Requirements
schema_version: 1.0.0
limits:
  turn_max_chars: { value: null, unit: chars }
  transcript_max_turns: { value: null, unit: turns }
  transcript_max_chars: { value: null, unit: chars }
  import_file_max_bytes: { value: null, unit: bytes }
  audio_max_bytes: { value: null, unit: bytes }
  audio_max_seconds: { value: null, unit: s }
  run_message_max_bytes: { value: null, unit: bytes }
  run_deadline_incremental_s: { value: null, unit: s }
  run_deadline_final_s: { value: null, unit: s }
  model_call_timeout_s: { value: null, unit: s }
  claim_idle_ms: { value: null, unit: ms }
  poll_interval_s: { value: null, unit: s }
  heartbeat_timeout_s: { value: null, unit: s }
  web_session_max_s: { value: null, unit: s }
  fragment_window_turns: { value: null, unit: turns }
  fragment_overlap_turns: { value: null, unit: turns }
  dismissal_window_w: { value: null, unit: suggestions }
  research_report_max_bytes: { value: null, unit: bytes }
```

Una prueba de nivel 0 falla si un servicio usa una cifra de límite que no viene de este archivo, o si
una variable de entorno intenta subir una.

---

## Reglas de propiedad y cambio

1. **Dónde vive cada contrato.** Todo contrato está en `contracts/` (U1) con su versión semántica y sus
   *fixtures* válidos e inválidos, todos sintéticos. Las interfaces en proceso (C10–C13, C17, C20, C23,
   C24) viven en `contracts/python/` y `libs/`, y se verifican con mypy estricto e import-linter: un
   módulo solo importa la interfaz pública del otro.
2. **Quién decide.** La unidad dueña (columna Owner) propone el cambio; el PR lleva la prueba de
   contrato del productor y de cada consumidor. Revisa y aprueba el autor, como cualquier PR (team.md).
3. **El contrato común (C6) es externo.** Su fuente de verdad es el repositorio principal del TG. Un
   cambio se propone allá, se aprueba allá y entra aquí como copia versionada en su propio PR; una prueba
   de nivel 0 compara la versión de la copia con la declarada. La versión 1.0.0 la aprueba el autor en
   esta etapa (ADR-017).
4. **Cambio aditivo (versión menor).** Un campo nuevo opcional o una ruta nueva. Los consumidores
   ignoran campos que no conocen en los sobres de cola (C2, C3, C5) y en las respuestas de C1.
   **Excepción:** C6, C7, C18, C19 y C21 son estrictos (`additionalProperties: false`); en ellos todo
   cambio de forma es mayor.
5. **Cambio incompatible (versión mayor).** Entra en **un solo PR** que actualiza el productor y todos
   los consumidores del monorepo. Un consumidor que recibe una versión mayor que no conoce manda el
   mensaje a `<cola>:failed` sin crear filas. Esta revisión sube C1, C2, C3, C10–C16 a su versión 2.
6. **Errores.** Un solo catálogo de `code` (C1 `ErrorCode`) en `contracts/`, con su jerarquía de
   excepciones en `libs/` (una clase por `code`); añadir un código es menor, cambiar el significado de
   uno es mayor. Los `error.codigo` de C6 se traducen uno a uno (P8). El `detail` en español vive en el
   catálogo de mensajes de la consola.
7. **Configuración.** Ningún contrato permite escribir perfiles, precios, *prompts* ni límites desde la
   consola; solo cambian por PR (FR9.2).
8. **Idioma de los campos.** Los del contrato común (C6, y lo que de él copian C7 y C19) en español;
   todo lo demás en inglés (P14).

## Decisiones que precisan artefactos ya aprobados

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada uno en su propio commit.

| ID | Artefacto aprobado | Precisión propuesta | Origen |
|---|---|---|---|
| CD-01 | `domain-design/components.md` (IncoherenceAnalyzer, InterviewSession, AnalyzerCli) y `units-generation/unit-of-work.md` (UG-02) | Dentro del contrato común el incidente es `codigo: incidente_anonimizacion` y el fallo cerrado `anonimizador_no_disponible`; `anonymizer.incident` y `analysis.anonymizer_unavailable` quedan como códigos de Problem Details. Cierra la parte de UG-02 que tocaba a U1; si el fallo cerrado bloquea la sesión sigue en U4 (Functional Design) | P8 |
| CD-02 | `requirements-analysis/requirements.md` (FR4.2) | El código propuesto `anonimizador` se llama `anonimizador_no_disponible` | P8 |
| CD-03 | `domain-design/components.md` (ResearchReports) | «Descarta antes de guardar todo texto» pasa a «rechaza con `422` el reporte que trae texto o no cumple el esquema»; el reporte de la CLI no tiene campos de texto libre | P12 |
| CD-04 | `requirements-analysis/requirements.md` (FR15.1) y `domain-design/components.md` (ModelGateway) | Los adaptadores nativos de Anthropic, Google y OpenAI viven en el Anonymizer (módulo en `libs/` y pod `anonymizer-proxy`), no en `semantic-agent`; ModelGateway los alcanza solo a través de él. Las claves se montan solo en `anonymizer-proxy` | P13 |
| CD-05 | `aidlc/spaces/default/memory/team.md` (Code Style, «Idioma») | Excepción al glosario: los campos del contrato común del TG conservan su nombre en español en JSON y en Python, sin alias | P14 |
| CD-06 | `domain-design/components.md` (InterviewSession, ConsoleApi) | La cancelación de corridas usa la clave `veridicus:run-cancelled:{run_id}` que InterviewSession escribe y el trabajador solo lee (C2) | Esta etapa (VE-10 (a)) |
| CD-07 | `units-generation/unit-of-work-dependency.md` (puntos de integración) | La métrica de descartes la emite HumanReview (U5) desde `session-api`, no U4 | Revisión 1 R-03, C15 |
| CD-08 | `refined-mockups/interaction-spec.md` | Los errores de análisis se muestran por corrida con los códigos `analysis.*` y `anonymizer.incident` de C1 | P8 |

## Preguntas abiertas

| Contract | Question | Blocks |
|---|---|---|
| C6 | Aprobación de la v1.0.0 en el repositorio principal del TG; hasta entonces la copia en `contracts/` lleva la versión aprobada aquí por el autor. | U1 (Code Generation), U11 |
| C25 | Todas las cifras del catálogo (plazos de corrida, *timeout* por llamada, ventana y solapamiento del modo fragmentado, tamaños máximos, *W* de descartes). | U4, U6, U9, U11, U12 (NFR Requirements) |
| C5 | Tamaño máximo del audio en el mensaje; si supera lo razonable para Redis, cambiar a una referencia a un volumen temporal con borrado tras transcribir. | U9 |
| C18 | Modelos concretos de `comercial-piloto` y `todo-local`, y modelo local de demostración. | U11 (NFR Requirements) |
| C22 | Forma exacta de forzar la salida JSON y el esfuerzo en cada proveedor, y si Responses o Chat Completions con OpenAI. | U10 (Functional Design) |
| C14 | Servidor concreto de cada modelo local y adaptador del TTS. | U9, U2 (Infrastructure Design) |
| C8 | Texto exacto del aviso de VE-01 (lo redacta el TG). | U1 |
