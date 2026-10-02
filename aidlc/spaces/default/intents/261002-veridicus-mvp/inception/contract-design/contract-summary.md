# Contratos — Veridicus (MVP)

**Insumos.** Unidades y grafo de `inception/units-generation/unit-of-work.md` (unit-of-work) y
`unit-of-work-dependency.md` (unit-of-work-dependency); componentes, entidades y ADR de
`inception/domain-design/components.md` (components) y `decisions.md`; requisitos de
`inception/requirements-analysis/requirements.md` (requirements); códigos de error visibles de
`inception/refined-mockups/interaction-spec.md`; respuestas P1–P7 de `contract-design-questions.md`.

**Alcance.** Cada frontera por la que cruzan datos entre unidades, o entre el sistema y algo que no
escribimos (el navegador y los servidores de modelos). Los valores numéricos (plazos, intervalos,
tamaños máximos, umbral) son parámetros que fija NFR Requirements; aquí solo se nombran. Todo el
tráfico de estos contratos ocurre **dentro del clúster local** (AUTONOMIA-04): ninguno cruza su
frontera en el MVP.

**Decisiones de esta etapa.**

| P | Decisión |
|---|---|
| P1 | Colas con Redis Streams y grupos de consumidores: `XACK` tras procesar, `XAUTOCLAIM` de pendientes y un *stream* de fallidos por cola. |
| P2 | Versión semántica por contrato y `schema_version` en cada mensaje. Aditivo = menor (el consumidor ignora campos desconocidos). Incompatible = mayor, en un solo PR que cambia productor y consumidores. Mayor desconocido → fallidos, sin filas. |
| P3 | InterviewSession vigila el plazo de cada turno; la reentrega automática solo cubre fallos recuperables; la salida inválida del juez no se reintenta sola; el reintento humano publica `attempt + 1`; los resultados de intentos viejos se descartan. |
| P4 | Las fronteras en proceso son interfaces Python tipadas (`Protocol`), verificadas con mypy estricto e import-linter. |
| P5 | Sesión del servidor con cookie `HttpOnly`, `Secure`, `SameSite=Strict`, revocable, y cabecera anti-CSRF en peticiones que cambian estado. |
| P6 | Sondeo con cursor de cambios; cada consulta de la sesión cuenta como latido. |
| P7 | ModelGateway habla la API compatible con OpenAI con los servidores de modelos internos, con un adaptador propio para el TTS. |

## Tabla de contratos

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---|---|---|---|
| C1 | U3, U4, U5, U6, U7, U8, U9 (`session-api`, módulo ConsoleApi) | External: navegador del analista (`frontend`) | REST síncrono (HTTP/JSON) con cookie de sesión | U3 (seguridad y errores); cada unidad es dueña de sus rutas |
| C2 | U4 (InterviewSession) | U4, U8 (SemanticEvaluation, `semantic-agent`) | Mensaje asíncrono: Redis Stream `veridicus:turns` | U4 |
| C3 | U4, U8 (SemanticEvaluation) | U4 (InterviewSession) | Mensaje asíncrono: Redis Stream `veridicus:results` | U4 |
| C4 | U4 (TruthFrame, carga) | U4 (TruthFrame, indexador) | Mensaje asíncrono: Redis Stream `veridicus:indexing` | U4 |
| C5 | U9 (InterviewSession, voz) | U9 (SpeechProcessing, `audio-worker`) | Mensajes asíncronos: Redis Streams `veridicus:audio` y `veridicus:transcripts` | U9 |
| C6 | U1 (IntegrityPolicy) | U4, U8 (SemanticEvaluation) | Esquema compartido (JSON Schema) | U1 |
| C7 | U1 (IntegrityPolicy) | U4 (SemanticEvaluation, InterviewSession, HumanReview), U7 | Esquema compartido (JSON Schema) | U1 |
| C8 | U1 (IntegrityPolicy) | U4, U7, U8, `frontend` | Esquema compartido (lista versionada en YAML) | U1 |
| C9 | U4 (TruthFrame) | U4 (SemanticEvaluation) | Esquema de base de datos compartido, solo lectura | U4 |
| C10 | U4, U5 (HumanReview) | U4 (InterviewSession), U5 (ConsoleApi) | Interfaz en proceso (`Protocol`) | U5 |
| C11 | U4, U5 (HumanReview), U4, U6 (InterviewSession), U4 (TruthFrame) | U7 (ForensicReport) | Interfaces en proceso (`Protocol`) | U5, U4 |
| C12 | U3 (IdentityAccess) | U3 (ConsoleApi) | Interfaz en proceso (`Protocol`) | U3 |
| C13 | U4 (ModelGateway, `libs/`) | U4, U8, U9 (TruthFrame, SemanticEvaluation, SpeechProcessing); U10 como adaptador | Interfaz en proceso (`Protocol`) | U4 |
| C14 | External: servidores de modelos dentro del clúster (juez, *embeddings*, Whisper, TTS) | U4, U9, U10 (adaptadores de ModelGateway) | REST síncrono compatible con OpenAI | U2 despliega los servidores; U4 fija el subconjunto usado |
| C15 | U5 (HumanReview vía `session-api`) | U2 (regla de Prometheus) | Métricas Prometheus (`/metrics`) | U5 |
| C16 | `session-api`, `semantic-agent`, `audio-worker`, `anonymizer-proxy` | U2 (sondas de Kubernetes, `scripts/smoke.sh`) | REST síncrono: `/healthz` y `/readyz` | U2 |

Todos los archivos de especificación viven en `contracts/` (U1). La columna **Owner** dice qué unidad
decide los cambios del contrato; U1 los guarda, los versiona y prueba sus *fixtures*.

### Datos sensibles por contrato (AUTONOMIA-04)

| # | Datos sin anonimizar que transporta | Dónde viajan |
|---|---|---|
| C1 | Testimonio, alertas, CoT, reportes | Navegador ↔ `session-api` dentro del clúster |
| C2, C3 | Testimonio, afirmaciones, CoT, pasajes | Redis dentro del clúster (bajo la `NetworkPolicy` de salida denegada) |
| C4 | Ninguno (solo identificadores) | Redis |
| C5 | Audio crudo y su transcripción | Redis; el audio se borra del *stream* tras confirmarlo (ver pregunta abierta) |
| C9 | Pasajes de escenarios sintéticos | PostgreSQL dentro del clúster |
| C14 | Todo lo que se envía a un modelo | Solo servidores internos; un destino no interno impide arrancar (ADR-005) |
| C15, C16 | Ninguno (solo identificadores y contadores) | Dentro del clúster |

---

## C1 — API de la consola (ConsoleApi)

Única superficie expuesta al navegador (ADR-004). Reglas comunes:

- Toda ruta exige la cookie `veridicus_session` salvo `POST /api/v1/auth/login`, `/healthz` y
  `/readyz` (AC8.1.4). Sin cookie válida o con usuario desactivado: `401` (AC8.2.3).
- Toda petición que cambia estado (`POST`, `PATCH`) lleva `X-CSRF-Token` con el valor que entrega
  `GET /api/v1/auth/me`; sin él o con otro valor: `403` con `code: auth.csrf`.
- ConsoleApi aplica rol y propiedad de la sesión antes de delegar (ADR-009). Un rechazo es `403`
  Problem Details y no crea filas.
- Todo error es `application/problem+json` con `code` estable y `detail` en español (NFR10).
- Las fechas van en ISO 8601 UTC (`2026-10-02T21:40:00Z`); la consola las muestra en hora de
  Colombia.
- **No existe ninguna ruta que escriba el umbral** (AC8.3.1): el umbral solo cambia por PR a la
  configuración del despliegue.
- Las rutas marcadas `x-veridicus-priority: SHOULD` solo existen cuando su unidad (U8, U9) se construye.

```yaml
openapi: 3.1.0
info:
  title: Veridicus ConsoleApi
  version: 1.0.0
servers:
  - url: /api/v1
security:
  - sessionCookie: []
components:
  securitySchemes:
    sessionCookie:
      type: apiKey
      in: cookie
      name: veridicus_session
  parameters:
    CsrfToken:
      name: X-CSRF-Token
      in: header
      required: true
      schema: { type: string, minLength: 32 }
    SessionId:
      name: session_id
      in: path
      required: true
      schema: { type: string, format: uuid }
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
        - scenario.invalid_format
        - scenario.too_large
        - scenario.duplicate_sha256
        - scenario.not_ready
        - session.finalized
        - session.not_owner
        - session.not_suspended
        - turn.not_in_error
        - turn.error.invalid_output
        - turn.error.timeout
        - turn.error.system
        - review.cot_not_viewed
        - review.note_required
        - review.invalid_transition
        - review.round_locked
        - report.session_not_finalized
        - report.turns_in_progress
        - report.pending_suggestions
        - report.forbidden_vocabulary
        - report.conflict
        - report.integrity_mismatch
    Role: { type: string, enum: [analista, admin] }
    Me:
      type: object
      required: [user_id, username, role, csrf_token]
      properties:
        user_id: { type: string, format: uuid }
        username: { type: string }
        role: { $ref: '#/components/schemas/Role' }
        csrf_token: { type: string }
    User:
      type: object
      required: [user_id, username, role, active, created_at]
      properties:
        user_id: { type: string, format: uuid }
        username: { type: string }
        role: { $ref: '#/components/schemas/Role' }
        active: { type: boolean }
        created_at: { type: string, format: date-time }
    ScenarioVersion:
      type: object
      required: [version_id, scenario_id, scenario_name, version_number, source_sha256, status, uploaded_by, uploaded_at]
      properties:
        version_id: { type: string, format: uuid }
        scenario_id: { type: string, format: uuid }
        scenario_name: { type: string }
        version_number: { type: integer, minimum: 1 }
        source_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        status: { type: string, enum: [indexing, ready, error] }
        error_code: { $ref: '#/components/schemas/ErrorCode' }
        uploaded_by: { type: string, format: uuid }
        uploaded_at: { type: string, format: date-time }
        ready_at: { type: string, format: date-time }
    Grade:
      type: string
      enum: [congruente, incongruente, no documentada]
    Turn:
      type: object
      required: [turn_id, number, text, origin, status, attempt, submitted_at]
      properties:
        turn_id: { type: string, format: uuid }
        number: { type: integer, minimum: 1 }
        text: { type: string }
        origin: { type: string, enum: [typed, pasted, voice] }
        status: { type: string, enum: [queued, processing, evaluated, error] }
        processing_stage: { type: string, enum: [transcribing, retrieving, judging] }
        error_code: { $ref: '#/components/schemas/ErrorCode' }
        attempt: { type: integer, minimum: 1 }
        submitted_at: { type: string, format: date-time }
        evaluated_at: { type: string, format: date-time }
        claims:
          type: array
          items:
            type: object
            required: [claim_index, text, grade]
            properties:
              claim_index: { type: integer, minimum: 0 }
              text: { type: string }
              grade: { $ref: '#/components/schemas/Grade' }
    ReviewSuggestion:
      type: object
      required: [suggestion_id, turn_id, fragment, quote, document_id, passage_id, cot, state, cot_viewed]
      properties:
        suggestion_id: { type: string, format: uuid }
        turn_id: { type: string, format: uuid }
        fragment: { type: string, minLength: 1 }
        quote: { type: string, minLength: 1 }
        document_id: { type: string, minLength: 1 }
        passage_id: { type: string, format: uuid }
        cot: { type: string, minLength: 1 }
        state: { type: string, enum: [pending, accepted, edited, dismissed] }
        note: { type: string }
        reformulation: { type: string }
        cot_viewed: { type: boolean, description: El usuario actual consultó la CoT }
        decided_by: { type: string, format: uuid }
        decided_at: { type: string, format: date-time }
    HandoffPackage:
      type: object
      required: [package_id, turn_id, fragment, previous_turns, nearest_passages, interrupted_cot]
      properties:
        package_id: { type: string, format: uuid }
        turn_id: { type: string, format: uuid }
        fragment: { type: string }
        previous_turns:
          type: array
          maxItems: 3
          items: { type: object, required: [number, text], properties: { number: { type: integer }, text: { type: string } } }
        nearest_passages:
          type: array
          maxItems: 3
          items:
            type: object
            required: [passage_id, document_id, quote, similarity]
            properties:
              passage_id: { type: string, format: uuid }
              document_id: { type: string }
              quote: { type: string }
              similarity: { type: number, minimum: 0, maximum: 1 }
        interrupted_cot: { type: string }
        affective_note: { type: string, description: Solo si el indicio afectivo (U8, COULD) está activo }
    SuggestedQuestion:
      type: object
      required: [question_id, turn_id, text, status]
      properties:
        question_id: { type: string, format: uuid }
        turn_id: { type: string, format: uuid }
        text: { type: string }
        status: { type: string, enum: [proposed, approved, discarded] }
    SessionSummary:
      type: object
      required: [session_id, owner_user_id, scenario_version_id, status, created_at, pending_suggestions]
      properties:
        session_id: { type: string, format: uuid }
        owner_user_id: { type: string, format: uuid }
        owner_username: { type: string }
        scenario_version_id: { type: string, format: uuid }
        status: { type: string, enum: [open, suspended, finalized, consolidated] }
        created_at: { type: string, format: date-time }
        finalized_at: { type: string, format: date-time }
        pending_suggestions: { type: integer, minimum: 0 }
    SessionView:
      allOf:
        - $ref: '#/components/schemas/SessionSummary'
        - type: object
          required: [scenario_sha256, cursor, turns, suggestions, handoff_packages, can_consolidate]
          properties:
            scenario_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
            cursor: { type: string, description: Opaco; se devuelve en el siguiente sondeo }
            turns: { type: array, items: { $ref: '#/components/schemas/Turn' } }
            suggestions: { type: array, items: { $ref: '#/components/schemas/ReviewSuggestion' } }
            handoff_packages: { type: array, items: { $ref: '#/components/schemas/HandoffPackage' } }
            suggested_questions: { type: array, items: { $ref: '#/components/schemas/SuggestedQuestion' } }
            can_consolidate: { type: boolean }
            consolidation_blockers:
              type: array
              items: { $ref: '#/components/schemas/ErrorCode' }
    ReportVersion:
      type: object
      required: [report_version_id, session_id, version_number, sha256, consolidated_by, consolidated_at]
      properties:
        report_version_id: { type: string, format: uuid }
        session_id: { type: string, format: uuid }
        version_number: { type: integer, minimum: 1 }
        sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
        consolidated_by: { type: string, format: uuid }
        consolidated_at: { type: string, format: date-time }
        supersedes_version_id: { type: string, format: uuid }
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
        '200': { description: Usuario actual y token anti-CSRF, content: { application/json: { schema: { $ref: '#/components/schemas/Me' } } } }
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
  /scenarios:
    get:
      responses:
        '200': { description: Catálogo de escenarios con sus versiones, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/ScenarioVersion' } } } } }
    post:
      x-veridicus-roles: [analista, admin]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [name, file]
              properties:
                name: { type: string, minLength: 1 }
                file: { type: string, format: binary, description: Markdown o texto UTF-8 hasta el tamaño de FR2.1 }
      responses:
        '202': { description: Versión 1 creada en indexing, content: { application/json: { schema: { $ref: '#/components/schemas/ScenarioVersion' } } } }
        '409': { $ref: '#/components/responses/Problem' }
        '413': { $ref: '#/components/responses/Problem' }
        '415': { $ref: '#/components/responses/Problem' }
  /scenarios/{scenario_id}/versions:
    post:
      x-veridicus-roles: [analista, admin]
      parameters:
        - { name: scenario_id, in: path, required: true, schema: { type: string, format: uuid } }
        - { $ref: '#/components/parameters/CsrfToken' }
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema: { type: object, required: [file], properties: { file: { type: string, format: binary } } }
      responses:
        '202': { description: Versión nueva en indexing, content: { application/json: { schema: { $ref: '#/components/schemas/ScenarioVersion' } } } }
        '409': { $ref: '#/components/responses/Problem' }
  /scenario-versions/{version_id}:
    get:
      parameters: [{ name: version_id, in: path, required: true, schema: { type: string, format: uuid } }]
      responses:
        '200': { description: Estado de la versión, content: { application/json: { schema: { $ref: '#/components/schemas/ScenarioVersion' } } } }
  /sessions:
    get:
      parameters:
        - { name: status, in: query, schema: { type: string, enum: [open, suspended, finalized, consolidated] } }
      responses:
        '200': { description: Lista de sesiones (todas visibles para ambos roles), content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/SessionSummary' } } } } }
    post:
      x-veridicus-roles: [analista]
      parameters: [{ $ref: '#/components/parameters/CsrfToken' }]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [scenario_version_id]
              additionalProperties: false
              properties:
                scenario_version_id: { type: string, format: uuid }
      responses:
        '201': { description: Sesión abierta con la instantánea del umbral vigente, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
        '409': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}:
    get:
      description: >
        Sondeo de la consola. Con `since` devuelve solo lo que cambió desde ese cursor. Cada llamada del
        dueño con la sesión abierta cuenta como latido (AC7.1.1).
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
        '204': { description: Latido sin turnos en proceso }
  /sessions/{session_id}/turns:
    post:
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
                client_request_id: { type: string, format: uuid, description: Evita turnos duplicados si el navegador reenvía }
      responses:
        '202': { description: Turno numerado y en cola; no espera a la evaluación, content: { application/json: { schema: { $ref: '#/components/schemas/Turn' } } } }
        '409': { $ref: '#/components/responses/Problem' }
  /sessions/{session_id}/transcript:
    post:
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
        '202': { description: Transcripción dividida en turnos, todos en cola en orden, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Turn' } } } } }
  /sessions/{session_id}/turns/{number}/retry:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters:
        - { $ref: '#/components/parameters/SessionId' }
        - { name: number, in: path, required: true, schema: { type: integer, minimum: 1 } }
        - { $ref: '#/components/parameters/CsrfToken' }
      responses:
        '202': { description: Mismo turno y mismo número con attempt + 1 (también en sesión finalizada), content: { application/json: { schema: { $ref: '#/components/schemas/Turn' } } } }
        '409': { description: El turno no está en error (turn.not_in_error) }
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
        '200': { description: Sesión finalizada; empieza la medición de MTTV, content: { application/json: { schema: { $ref: '#/components/schemas/SessionView' } } } }
  /suggestions/{suggestion_id}/cot-views:
    post:
      x-veridicus-roles: [analista, admin]
      parameters:
        - { name: suggestion_id, in: path, required: true, schema: { type: string, format: uuid } }
        - { $ref: '#/components/parameters/CsrfToken' }
      responses:
        '204': { description: Consulta de la CoT registrada (solo inserción) }
  /suggestions/{suggestion_id}/decisions:
    post:
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters:
        - { name: suggestion_id, in: path, required: true, schema: { type: string, format: uuid } }
        - { $ref: '#/components/parameters/CsrfToken' }
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
                reformulation: { type: string, description: Obligatoria si state es edited; nunca cambia fragmento, cita, documento ni CoT }
      responses:
        '201': { description: Decisión registrada en la ronda abierta, content: { application/json: { schema: { $ref: '#/components/schemas/ReviewSuggestion' } } } }
        '409': { description: Ronda bloqueada, CoT no consultada, nota faltante o transición inválida }
  /sessions/{session_id}/reports:
    get:
      parameters: [{ $ref: '#/components/parameters/SessionId' }]
      responses:
        '200': { description: Versiones del reporte, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/ReportVersion' } } } } }
    post:
      description: Finalizar y Consolidar. De dos consolidaciones simultáneas solo una gana; la otra recibe 409 report.conflict.
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
      parameters: [{ name: report_version_id, in: path, required: true, schema: { type: string, format: uuid } }]
      responses:
        '200':
          description: Markdown del reporte; el servidor recalcula el SHA-256 antes de enviarlo
          headers:
            X-Veridicus-SHA256: { schema: { type: string, pattern: '^[a-f0-9]{64}$' } }
          content:
            text/markdown: { schema: { type: string } }
        '409': { description: El archivo no coincide con el SHA-256 registrado (report.integrity_mismatch) }
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
            schema: { type: object, required: [audio, client_request_id], properties: { audio: { type: string, format: binary, description: WAV o MP3 }, client_request_id: { type: string, format: uuid } } }
      responses:
        '202': { description: Turno de voz numerado en transcribing, content: { application/json: { schema: { $ref: '#/components/schemas/Turn' } } } }
  /questions/{question_id}/decision:
    post:
      x-veridicus-priority: SHOULD
      x-veridicus-roles: [analista]
      x-veridicus-owner-only: true
      parameters:
        - { name: question_id, in: path, required: true, schema: { type: string, format: uuid } }
        - { $ref: '#/components/parameters/CsrfToken' }
      requestBody:
        required: true
        content:
          application/json:
            schema: { type: object, required: [status], additionalProperties: false, properties: { status: { type: string, enum: [approved, discarded] } } }
      responses:
        '200': { description: Decisión del analista sobre la pregunta, content: { application/json: { schema: { $ref: '#/components/schemas/SuggestedQuestion' } } } }
  /questions/{question_id}/audio:
    get:
      x-veridicus-priority: SHOULD
      parameters: [{ name: question_id, in: path, required: true, schema: { type: string, format: uuid } }]
      responses:
        '200': { description: Audio sintetizado en el clúster solo para una pregunta aprobada, content: { audio/wav: { schema: { type: string, format: binary } } } }
        '409': { description: La pregunta no está aprobada }
```

La ruta de cada unidad: U3 `/auth/*` y `/users*`; U4 `/scenarios` (POST de la versión 1 y catálogo),
`/scenario-versions/*`, `POST /sessions`, `GET /sessions/{id}`, `/turns`, `/turns/{n}/retry`,
`/suggestions/*/cot-views`; U5 `/suggestions/*/decisions`; U6 `/scenarios/{id}/versions`,
`GET /sessions`, `/transcript`, `/heartbeat`, `/resume`; U7 `/finalize`, `/reports`,
`/correction-rounds`, `/download`; U8 `/questions/*/decision`; U9 `/voice-turns`, `/questions/*/audio`.

---

## C2 — Cola de turnos a evaluar

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus turns
  version: 1.0.0
channels:
  turns:
    address: 'veridicus:turns'
    description: Redis Stream; grupo de consumidores `semantic-agent`
    messages:
      TurnToEvaluate: { $ref: '#/components/messages/TurnToEvaluate' }
operations:
  publishTurn:
    action: send
    channel: { $ref: '#/channels/turns' }
    summary: InterviewSession publica un turno (y cada reintento con attempt + 1)
  evaluateTurn:
    action: receive
    channel: { $ref: '#/channels/turns' }
    summary: SemanticEvaluation lo consume y hace XACK solo después de publicar el resultado (C3)
components:
  messages:
    TurnToEvaluate:
      contentType: application/json
      payload:
        type: object
        additionalProperties: true
        required: [schema_version, message_id, turn_id, session_id, attempt, turn_number, text, previous_turns, scenario_version_id, scenario_sha256, similarity_threshold, options, enqueued_at, deadline_at]
        properties:
          schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
          message_id: { type: string, format: uuid }
          turn_id: { type: string, format: uuid }
          session_id: { type: string, format: uuid }
          attempt: { type: integer, minimum: 1 }
          turn_number: { type: integer, minimum: 1 }
          text: { type: string, minLength: 1, description: Testimonio; va solo en el bloque de datos del prompt }
          previous_turns:
            type: array
            maxItems: 3
            items: { type: object, required: [number, text], properties: { number: { type: integer }, text: { type: string } } }
          scenario_version_id: { type: string, format: uuid }
          scenario_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
          similarity_threshold: { type: number, minimum: 0, maximum: 1, description: Instantánea guardada al crear la sesión (ADR-006) }
          options:
            type: object
            required: [permutation, suggest_question, affective]
            properties:
              permutation: { type: boolean, description: SHOULD, U8 }
              suggest_question: { type: boolean, description: SHOULD, U8 }
              affective: { type: boolean, description: COULD, U8 }
          enqueued_at: { type: string, format: date-time }
          deadline_at: { type: string, format: date-time, description: Plazo de evaluación (valor de NFR Requirements) }
```

**Entrega y fallos.** Al menos una vez. Si el trabajador muere, el mensaje queda pendiente y otro lo
reclama con `XAUTOCLAIM` tras el plazo de inactividad; tras 3 entregas sin confirmar va a
`veridicus:turns:failed` y el turno pasa a «Error» con `turn.error.system`. Un mensaje que no cumple
el esquema o trae una versión mayor desconocida va directo a fallidos, sin evaluar. El evaluador no
escribe en la base (ADR-002).

## C3 — Cola de resultados de evaluación

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus evaluation results
  version: 1.0.0
channels:
  results:
    address: 'veridicus:results'
    description: Redis Stream; grupo de consumidores `session-api`
    messages:
      EvaluationResult: { $ref: '#/components/messages/EvaluationResult' }
operations:
  publishResult:
    action: send
    channel: { $ref: '#/channels/results' }
  ingestResult:
    action: receive
    channel: { $ref: '#/channels/results' }
    summary: InterviewSession lo persiste de forma idempotente por (turn_id, attempt) y luego hace XACK
components:
  messages:
    EvaluationResult:
      contentType: application/json
      payload:
        type: object
        additionalProperties: true
        required: [schema_version, message_id, turn_id, session_id, attempt, outcome, evaluated_at]
        properties:
          schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
          message_id: { type: string, format: uuid }
          turn_id: { type: string, format: uuid }
          session_id: { type: string, format: uuid }
          attempt: { type: integer, minimum: 1 }
          outcome: { type: string, enum: [evaluated, error] }
          error_code: { type: string, enum: [turn.error.invalid_output, turn.error.system], description: Solo si outcome es error }
          claims:
            type: array
            items:
              type: object
              required: [claim_index, text, grade, max_similarity, passage_ids, guard]
              properties:
                claim_index: { type: integer, minimum: 0 }
                text: { type: string }
                grade: { type: string, enum: [congruente, incongruente, no documentada] }
                max_similarity: { type: number, minimum: 0, maximum: 1 }
                passage_ids: { type: array, items: { type: string, format: uuid } }
                guard: { type: string, enum: [below_threshold, at_or_above_threshold] }
          alerts:
            type: array
            description: Cada elemento cumple C7. Solo afirmaciones incongruente con guard at_or_above_threshold.
            items: { $ref: 'contracts/schemas/alert.v1.json' }
          handoff_package:
            description: Presente si alguna afirmación es «no documentada»
            type: object
            required: [fragment, previous_turn_numbers, nearest_passages, interrupted_cot]
            properties:
              fragment: { type: string }
              previous_turn_numbers: { type: array, maxItems: 3, items: { type: integer } }
              nearest_passages:
                type: array
                maxItems: 3
                items:
                  type: object
                  required: [passage_id, document_id, quote, similarity]
                  properties:
                    passage_id: { type: string, format: uuid }
                    document_id: { type: string }
                    quote: { type: string }
                    similarity: { type: number }
              interrupted_cot: { type: string, description: Determinista, sin LLM }
              affective_note: { type: string }
          suggested_question:
            type: object
            description: SHOULD (U8). Ausente si alguna afirmación es «no documentada».
            required: [text]
            properties: { text: { type: string, minLength: 1 } }
          permutation_applied: { type: boolean }
          model_digest: { type: string }
          prompt_sha256: { type: string, pattern: '^[a-f0-9]{64}$' }
          evaluated_at: { type: string, format: date-time }
```

**Invariantes que el consumidor vuelve a comprobar.** `outcome: error` ⇒ `alerts` vacío, sin paquete
y sin pregunta (nunca una alerta parcial, FR4.2). Un resultado con `attempt` menor que el del turno, o
que llega con el turno ya evaluado, se confirma y se descarta. Una alerta que no cumple C7 hace que
el resultado entero se trate como `turn.error.invalid_output`. InterviewSession guarda la evaluación y
el paquete, y entrega las alertas a HumanReview (C10) en la **misma transacción**.

**Plazo.** InterviewSession revisa periódicamente los turnos `queued` o `processing` con `deadline_at`
vencido y los pasa a «Error» con `turn.error.timeout` (AC10.1.2). La salida inválida del juez no se
reintenta sola: el analista usa «Reintentar evaluación» (C1), que publica C2 con `attempt + 1`.

## C4 — Cola de indexación de escenarios

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus indexing
  version: 1.0.0
channels:
  indexing:
    address: 'veridicus:indexing'
    description: Redis Stream; grupo `session-api-indexer`. Productor y consumidor viven en session-api.
    messages:
      IndexScenarioVersion:
        contentType: application/json
        payload:
          type: object
          required: [schema_version, message_id, version_id, attempt]
          properties:
            schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
            message_id: { type: string, format: uuid }
            version_id: { type: string, format: uuid }
            attempt: { type: integer, minimum: 1 }
operations:
  requestIndexing: { action: send, channel: { $ref: '#/channels/indexing' } }
  indexVersion: { action: receive, channel: { $ref: '#/channels/indexing' } }
```

El documento fuente no viaja en el mensaje: el indexador lo lee de la base por `version_id`. Si
falla un pasaje, la versión queda en `error` sin pasajes (AC1.1.4); la reentrega no duplica pasajes
porque la indexación de una versión es una sola transacción.

## C5 — Colas de audio y transcripción (SHOULD, U9)

```yaml
asyncapi: 3.0.0
info:
  title: Veridicus speech
  version: 1.0.0
channels:
  audio:
    address: 'veridicus:audio'
    description: Redis Stream; grupo `audio-worker`
    messages:
      AudioToTranscribe:
        contentType: application/json
        payload:
          type: object
          required: [schema_version, message_id, turn_id, session_id, attempt, audio_format, audio_base64, deadline_at]
          properties:
            schema_version: { type: string, pattern: '^1\.[0-9]+\.[0-9]+$' }
            message_id: { type: string, format: uuid }
            turn_id: { type: string, format: uuid }
            session_id: { type: string, format: uuid }
            attempt: { type: integer, minimum: 1 }
            audio_format: { type: string, enum: [wav, mp3] }
            audio_base64: { type: string, description: Tamaño máximo lo fija NFR Requirements (ver pregunta abierta) }
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
            error_code: { type: string, enum: [turn.error.system, turn.error.timeout] }
            model_digest: { type: string }
operations:
  sendAudio: { action: send, channel: { $ref: '#/channels/audio' } }
  transcribe: { action: receive, channel: { $ref: '#/channels/audio' } }
  sendTranscript: { action: send, channel: { $ref: '#/channels/transcripts' } }
  ingestTranscript: { action: receive, channel: { $ref: '#/channels/transcripts' } }
```

Tras confirmar un audio, el trabajador lo borra del *stream* (`XDEL`): el audio crudo no se conserva
(SpeechProcessing). Con el texto, InterviewSession publica el mismo turno en C2: el turno de voz sigue
el camino del de texto.

## C6 — Esquema de la salida del juez

Estricto: el juez solo puede devolver esto; cualquier otra cosa es `turn.error.invalid_output`.

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: contracts/schemas/judge-output.v1.json
title: Salida del juez (v1)
type: object
additionalProperties: false
required: [claims]
properties:
  claims:
    type: array
    minItems: 1
    items:
      type: object
      additionalProperties: false
      required: [claim_index, grade, passage_ids, cot]
      properties:
        claim_index: { type: integer, minimum: 0 }
        grade: { type: string, enum: [congruente, incongruente, no documentada] }
        passage_ids:
          type: array
          items: { type: string, format: uuid }
          description: Cada uno debe estar entre los pasajes recuperados para esa afirmación
        cot: { type: string, minLength: 1 }
```

Sin campos de veracidad, puntajes de verdad ni etiquetas sobre el compareciente (AC5.5.3). El enum
de calificación es exactamente el de AC5.5.4.

## C7 — Esquema de la alerta (sugerencia de revisión)

```yaml
$schema: https://json-schema.org/draft/2020-12/schema
$id: contracts/schemas/alert.v1.json
title: Alerta de incongruencia (v1)
type: object
additionalProperties: false
required: [turn_id, claim_index, fragment, quote, document_id, passage_id, cot]
properties:
  turn_id: { type: string, format: uuid }
  claim_index: { type: integer, minimum: 0 }
  fragment: { type: string, minLength: 1, description: Fragmento literal de la transcripción }
  quote: { type: string, minLength: 1, description: Cita literal del pasaje }
  document_id: { type: string, minLength: 1, description: Debe pertenecer a la versión de escenario de la sesión }
  passage_id: { type: string, format: uuid }
  cot: { type: string, minLength: 1 }
```

Los cuatro campos obligatorios de AUTONOMIA-05 (`fragment`, `quote`, `document_id`, `cot`) se validan
en tres puntos: al producir (SemanticEvaluation), al ingerir (InterviewSession) y al guardar
(HumanReview, AC3.1.2). Una alerta sin cualquiera de ellos se rechaza.

## C8 — Lista de vocabulario prohibido

```yaml
# contracts/integrity/forbidden-vocabulary.v1.yaml
schema_version: 1.0.0
match:
  whole_word: true
  case_insensitive: true
  accent_insensitive: true
  excluded_spans: [literal_testimony_quote, literal_scenario_quote, analyst_text]
terms:
  - mentiroso
  - mentirosa
  - miente
  - mintió
  - falso
  - falsa
  - verdadero
  - verdadera
  - engaño
categories_forbidden_in_schemas:
  - veracity_score
  - is_lying
  - truthfulness
```

La usan el escáner de IntegrityPolicy (salida del juez, reporte, pregunta sugerida, indicio afectivo)
y la prueba del catálogo de mensajes de la consola. La lista exacta de términos la amplía U1 por PR,
con su control negativo; ningún término sale sin un PR propio.

## C9 — Lectura de pasajes del evaluador (base compartida, solo lectura)

```yaml
# contracts/db/truthframe-read.v1.yaml
schema_version: 1.0.0
role: veridicus_judge_ro
grants:
  - { object: truthframe.passage_search, privilege: SELECT }
denied: [INSERT, UPDATE, DELETE, TRUNCATE]
view:
  name: truthframe.passage_search
  description: Solo pasajes de versiones en estado ready
  columns:
    passage_id: uuid
    version_id: uuid
    document_id: text
    position: integer
    text: text
    embedding: vector   # dimensión fijada por el modelo de embeddings (NFR Requirements)
query:
  inputs: [version_id, claim_embedding, top_k]
  order_by: distancia coseno ascendente
  returns: [passage_id, document_id, text, similarity]   # similarity = 1 - distancia coseno
```

U4 crea la vista, el rol y sus permisos en una migración; cambiar la vista es un cambio de contrato.
Una prueba de nivel 1 verifica que el rol no puede escribir (AC3.3.2).

## C10 — HumanReview hacia InterviewSession y ConsoleApi (en proceso)

```python
# contracts/python/human_review.py  — v1.0.0
from typing import Protocol, Literal
from uuid import UUID
from datetime import datetime

DecisionState = Literal["accepted", "edited", "dismissed"]

class AlertCandidate(Protocol):          # forma de C7
    turn_id: UUID; claim_index: int
    fragment: str; quote: str; document_id: str; passage_id: UUID; cot: str

class Actor(Protocol):
    user_id: UUID | None                 # None = sistema (al proponer)
    at: datetime

class SuggestionProposer(Protocol):
    def propose(self, uow: "UnitOfWork", session_id: UUID, scenario_version_id: UUID,
                attempt: int, candidates: list[AlertCandidate]) -> list[UUID]:
        """Guarda las sugerencias en estado pendiente.
        Idempotente por (turn_id, attempt, claim_index).
        Si la sesión no tiene ronda, abre la ronda 1 en la misma transacción (ADR-007).
        Rechaza un candidato sin los 4 campos o con un documento de otra versión."""

class ReviewCommands(Protocol):
    def record_cot_view(self, uow: "UnitOfWork", suggestion_id: UUID, actor: Actor) -> None: ...
    def decide(self, uow: "UnitOfWork", suggestion_id: UUID, state: DecisionState,
               note: str | None, reformulation: str | None, actor: Actor) -> UUID:
        """El actor ya viene autorizado como dueño (ADR-009).
        Errores: review.cot_not_viewed, review.note_required,
        review.invalid_transition, review.round_locked."""
```

## C11 — Lo que ForensicReport usa de los demás módulos (en proceso)

```python
# contracts/python/forensic_ports.py  — v1.0.0
class SessionReader(Protocol):           # dueño: InterviewSession (U4, U6)
    def snapshot(self, uow: "UnitOfWork", session_id: UUID) -> "SessionSnapshot":
        """Estado, dueño, versión de escenario, finalized_at, turnos con texto y estado,
        paquetes de traspaso y cuántos turnos siguen queued o processing."""

class ScenarioReader(Protocol):          # dueño: TruthFrame (U4)
    def version_info(self, uow: "UnitOfWork", version_id: UUID) -> "VersionInfo": ...

class ReviewRounds(Protocol):            # dueño: HumanReview (U5)
    def open_round(self, uow: "UnitOfWork", session_id: UUID) -> "RoundView | None": ...
    def pending_count(self, uow: "UnitOfWork", round_id: UUID) -> int: ...
    def decisions(self, uow: "UnitOfWork", round_id: UUID) -> list["SuggestionWithDecision"]: ...
    def lock_round(self, uow: "UnitOfWork", round_id: UUID, report_version_id: UUID,
                   actor: Actor) -> None:
        """Falla con report.conflict si la ronda ya está bloqueada (una sola consolidación gana)."""
    def open_correction_round(self, uow: "UnitOfWork", session_id: UUID,
                              based_on_report_version_id: UUID, actor: Actor) -> UUID:
        """Abre o retoma la única ronda de corrección de la sesión."""
```

`UnitOfWork` es la transacción compartida de `session-api`: la consolidación lee, escribe la versión
del reporte y bloquea la ronda en una sola transacción (ADR-001, AC6.1.6). Ningún módulo abre su
propia transacción dentro de estas llamadas.

## C12 — IdentityAccess hacia ConsoleApi (en proceso)

```python
# contracts/python/identity.py  — v1.0.0
Role = Literal["analista", "admin"]

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

## C13 — Puerto ModelGateway (biblioteca en `libs/`)

```python
# libs/model_gateway/port.py  — contrato v1.0.0
class JudgeRequest(Protocol):
    system_prompt: str                   # leído de archivo montado, SHA-256 verificado
    data_block: str                      # testimonio y pasajes, delimitados como datos
    json_schema: dict                    # C6
    temperature: float                   # siempre 0
    seed: int

class ModelGateway(Protocol):
    def judge(self, req: JudgeRequest, timeout_s: float) -> "JudgeResponse":
        """Devuelve el texto crudo, model_digest y prompt_sha256; no valida contra C6."""
    def embed(self, texts: list[str], timeout_s: float) -> list[list[float]]: ...
    def transcribe(self, audio: bytes, audio_format: str, timeout_s: float) -> "Transcript": ...  # SHOULD
    def synthesize(self, text: str, timeout_s: float) -> bytes: ...                              # SHOULD
```

Al construir el adaptador se valida que cada URL de destino sea interna del clúster; si no, el
servicio no arranca (AC9.1.4). Todo método lleva *timeout* explícito. Los *fakes* deterministas de
los niveles 0 y 1 implementan este mismo `Protocol`. El anonimizador (U10) es otro adaptador con la
misma forma que enmascara antes de llamar y falla cerrado (AC11.3.1).

## C14 — Servidores de modelos dentro del clúster (API compatible con OpenAI)

```yaml
openapi: 3.1.0
info:
  title: Subconjunto usado de la API compatible con OpenAI
  version: 1.0.0
servers:
  - url: '{base}'
    variables:
      base:
        default: http://veridicus-judge.veridicus.svc.cluster.local:8080
        description: Una URL por servidor en VERIDICUS_JUDGE_URL, VERIDICUS_EMBEDDINGS_URL, VERIDICUS_WHISPER_URL
paths:
  /v1/chat/completions:
    post:
      summary: Juez LLM
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [model, messages, temperature, seed, response_format]
              properties:
                model: { type: string }
                messages:
                  type: array
                  items: { type: object, required: [role, content], properties: { role: { enum: [system, user] }, content: { type: string } } }
                temperature: { type: number, const: 0 }
                seed: { type: integer }
                response_format:
                  type: object
                  required: [type, json_schema]
                  properties: { type: { const: json_schema }, json_schema: { type: object } }
      responses:
        '200':
          description: choices[0].message.content trae el JSON que se valida contra C6
  /v1/embeddings:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema: { type: object, required: [model, input], properties: { model: { type: string }, input: { type: array, items: { type: string } } } }
      responses:
        '200': { description: data[i].embedding por cada texto, en el mismo orden }
  /v1/audio/transcriptions:
    post:
      summary: SHOULD (U9)
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema: { type: object, required: [file, model, language], properties: { file: { type: string, format: binary }, model: { type: string }, language: { const: es } } }
      responses:
        '200': { description: '{ "text": "..." }' }
```

El TTS (SHOULD) no tiene un estándar en este subconjunto: lo cubre un adaptador propio dentro de C13,
contra el servidor que elija Infrastructure Design. Las versiones de los modelos se fijan por
`sha256` y se descargan en el aprovisionamiento, nunca en ejecución (team-practices).

## C15 — Métricas de revisión para la regla AIR (SHOULD)

```yaml
# contracts/metrics/review.v1.yaml
schema_version: 1.0.0
endpoint: GET /metrics  # session-api, puerto interno, sin autenticación de usuario, no expuesto al navegador
metrics:
  - name: veridicus_review_decisions_total
    type: counter
    labels: [state]                      # accepted | edited | dismissed
  - name: veridicus_session_dismissal_ratio
    type: gauge
    labels: [session_id]
    description: >
      Fracción de alertas descartadas o sin decidir entre las últimas W alertas decididas de la
      sesión (W lo fija NFR Requirements). La regla de U2 alerta con una propuesta de umbral cuando
      supera 0.25 (FR9.3); nunca cambia el umbral.
  - name: veridicus_turn_latency_seconds
    type: histogram
    labels: [origin]                     # typed | pasted | voice
```

Las etiquetas solo llevan identificadores, nunca texto (NFR10). `session_id` es aceptable porque el
MVP tiene pocas sesiones; si crece, la regla se calcula por consulta y la etiqueta se retira con un
cambio mayor.

## C16 — Salud de cada servicio

```yaml
openapi: 3.1.0
info:
  title: Salud de los servicios de Veridicus
  version: 1.0.0
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
        200 solo si la configuración es válida (incluido el umbral, AC4.3.1), la base y Redis
        responden, y los servidores de modelos que el servicio usa son internos y responden.
      responses:
        '200': { description: '{ "status": "ready" }' }
        '503': { description: '{ "status": "not_ready", "checks": [{ "name": "redis", "ok": false }] } — sin datos sensibles' }
```

`semantic-agent`, `audio-worker` y `anonymizer-proxy` exponen estas dos rutas en un puerto interno
aunque no tengan API de negocio.

---

## Reglas de propiedad y cambio

1. **Dónde vive cada contrato.** Todo contrato está en `contracts/` (U1) con su versión semántica y
   sus *fixtures* válidos e inválidos. Las interfaces en proceso (C10–C13) viven en `contracts/python/`
   y `libs/`, y se verifican con mypy estricto e import-linter: un módulo solo importa la interfaz
   pública del otro.
2. **Quién decide.** La unidad dueña (columna Owner) propone el cambio; el PR lleva la prueba de
   contrato del productor y de cada consumidor. Revisa y aprueba el autor, como cualquier PR
   (team-practices).
3. **Cambio aditivo (versión menor).** Un campo nuevo opcional o una ruta nueva. Los consumidores
   ignoran campos que no conocen en los mensajes (C2–C5) y en las respuestas de C1. **Excepción:** C6
   y C7 son estrictos (`additionalProperties: false`); en ellos todo cambio es mayor.
4. **Cambio incompatible (versión mayor).** Entra en **un solo PR** que actualiza el productor y todos
   los consumidores del monorepo. Un consumidor que recibe una versión mayor que no conoce manda el
   mensaje a `<cola>:failed` sin crear filas.
5. **Colas.** Redis Streams con grupo por consumidor; confirmación (`XACK`) solo después de persistir o
   publicar el efecto; reclamo de pendientes con `XAUTOCLAIM`; a los 3 intentos, `<cola>:failed`.
   Idempotencia por (`turn_id`, `attempt`) o por `version_id`.
6. **Errores.** Un solo catálogo de `code` (C1 `ErrorCode`) en `contracts/`; añadir un código es un
   cambio menor, cambiar el significado de uno es mayor. El `detail` en español vive en el catálogo de
   mensajes de la consola.
7. **Umbral.** Ningún contrato permite escribir el umbral; solo viaja como instantánea de lectura (C2).

## Decisiones que precisan artefactos ya aprobados

Estas decisiones de contrato tocan artefactos ya aprobados. No los edité; decides en la aprobación si
se actualizan.

| Artefacto | Qué precisa este contrato | Hallazgo de origen |
|---|---|---|
| `units-generation/unit-of-work.md` (U4, U5) | La ronda 1 la abre `SuggestionProposer.propose` (C10) en la misma transacción en que U4 guarda la primera sugerencia. Por eso U4 crea las tablas `ReviewSuggestion` y `ReviewRound`, y U5 crea `ReviewDecision` y `CotView` con la máquina de estados. | R-02 de Units Generation |
| `units-generation/unit-of-work.md` (U5) | U5 emite las métricas de C15 desde `session-api`; U2 solo escribe la regla. | R-03 de Units Generation |
| `refined-mockups/mockups.md` | La maqueta de turno en error muestra `Código: judge_invalid_output`; el código del contrato es `turn.error.invalid_output`, igual que en `interaction-spec.md`. | — |

## Preguntas abiertas

| Contract | Question | Blocks |
|---|---|---|
| C2, C3 | Plazo de evaluación por turno y plazo de inactividad para reclamar pendientes. | U4 (NFR Requirements) |
| C1 | Intervalo de sondeo, *T* del latido y duración de la sesión web. | U4, U6, U3 (NFR Requirements) |
| C5 | Tamaño máximo del audio en el mensaje; si supera lo razonable para Redis, cambiar a una referencia a un volumen temporal con borrado tras transcribir. | U9 |
| C1 | Tamaño máximo de un turno y de una transcripción pegada, y regla de división en turnos. | U4, U6 (Functional Design) |
| C9 | Dimensión del vector y `top_k` por afirmación. | U4 (NFR Requirements, Functional Design) |
| C15 | Ventana *W* de alertas decididas para la razón AIR. | U5, U2 (NFR Requirements) |
| C14 | Servidor concreto de cada modelo y adaptador del TTS. | U9, U2 (Infrastructure Design) |
