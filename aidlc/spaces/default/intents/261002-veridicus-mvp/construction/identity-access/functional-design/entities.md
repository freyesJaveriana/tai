# Entidades — U3 identity-access

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-02. Las entidades conservan su nombre y lo que sale
queda «Retirado» sin renumerar (regla de `project.md`).
- **Siguen:** `User`, `UserChange`, `WebSession`, `Principal`, `PermissionMatrix` y `AuditConvention`.
- **Cambian:**
  - `role` suma `investigador` (FR1.2 revisión 3, C12 v2.0.0).
  - `UserChange` lleva `actor_kind` con un actor que nunca es nulo: `actor_user_id` o `actor_system`
    (P6 = A, cierra R-02).
  - `WebSession` declara su clave primaria, `last_seen_at` para la caducidad por inactividad y su purga
    (NFR10.3 y NFR8.3 de U3, cierra R-08).
  - `AuditConvention` deja de ser una lista de nombres. Ahora es la marca única en el comentario de cada
    tabla, con su clase, su condición de purgable y sus columnas de actor y hora (cierra R-01 y R-08,
    P7 = A).
  - `PermissionMatrix` sigue la matriz de tres roles de FR1.2 revisión 3.
- **Salen («Retirado»):** las acciones `upload_scenario` (FR2 retirado), `apply_threshold_change` (sale
  el umbral, FR9.2) y `decide_alerts_and_consolidate`. Esta última la sustituye
  `decide_suggestions_and_consolidate`, porque la «alerta» ya no existe tras el cambio 01.
- **Entran:**
  - `ActorSystem`, la lista cerrada y versionada de actores que no son personas (P6 = A).
  - `DatabaseRole`, con el usuario de la aplicación y el del `Job` de retención (P7 = A, NFR11, A-2).
  - `RouteSecurity`, las extensiones `x-veridicus-*` de C1 como datos, incluidas `owner-only-for-role`,
    `demo` y la nueva `access-log` (P5 = A).
  - `ProblemResponse`, el cuerpo del manejador único de Problem Details (unit-of-work U3, regla 6 de C1).
  - `AccessRecord`, la llamada al puerto `AccessLog` de C23 (P5 = A).

**Insumos.**
- Unidad U3 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) e historias
  US8.1–US8.4 y US5.6 de `unit-of-work-story-map.md` (unit-of-work-story-map, revisión 3).
- FR1, FR9, NFR10 y NFR11 de `inception/requirements-analysis/requirements.md` (requirements,
  revisión 3), y VE-09, VE-11, VE-13, A-2 y A-3 de `requirements-adenda-02.md`.
- IdentityAccess, ConsoleApi, EthicsGovernance y la tabla «Propiedad de las entidades» de
  `inception/domain-design/components.md` (components, revisión 3), con ADR-003, ADR-009 y ADR-016 de
  `decisions.md`.
- C1, C12, C23, C24 y CD-11 de `inception/contract-design/contract-summary.md` (contract-summary,
  revisión 3).
- AC5.4.4 de `inception/user-stories/stories-adenda-02.md`, y M0, M6 y M8 de
  `inception/refined-mockups/mockups.md`.
- Respuestas P1–P3 (revisión 1) y P4–P8 (segunda pasada) de `functional-design-questions.md`, y hallazgos
  R-01 a R-08 de `reviews/review-01.md`.

**Frontera AUTONOMIA-04.** Todas las entidades viven en PostgreSQL dentro del clúster (módulo
IdentityAccess de `session-api`) o son valores en memoria de ConsoleApi. Ningún dato de esta unidad sale
del clúster. El registro de acceso (`AccessRecord`) solo lleva identificadores.

```yaml
entities:
  - name: User
    description: Usuario local de la consola. Agregado raíz de IdentityAccess.
    storage: { kind: mutable, purgeable: false }
    attributes:
      - { name: user_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: username, type: text, required: true, unique: true, min: 3, max: 32, constraints: "se guarda normalizado en minúsculas; único sin distinguir mayúsculas; solo [a-z0-9._-]" }
      - { name: role, type: enum, required: true, allowed: [analista, admin, investigador] }
      - { name: password_hash, type: text, required: true, constraints: "Argon2id con sal (FR1.1, NFR10.1 de U3); nunca la contraseña en claro" }
      - { name: active, type: boolean, required: true, default: true }
      - { name: created_by, type: reference, references: User, required: false, description: "nulo solo en el primer admin; quién lo creó queda en UserChange con actor_system create-admin" }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "Exactamente tres roles (FR1.2)."
      - "Una vez creado el primero, siempre hay al menos un admin activo (P2 = A)."
      - "User no es un historial: admite UPDATE de active y role, y cada cambio deja su fila en UserChange en la misma transacción."
    relationships:
      - { to: UserChange, cardinality: "1..*", direction: "User -> UserChange (el alta es el primer cambio)" }
      - { to: WebSession, cardinality: "0..*", direction: "User -> WebSession" }

  - name: UserChange
    description: Historial de solo inserción de los cambios de un usuario (ADR-003). Cumple AuditConvention.
    storage: { kind: history, purgeable: false }
    attributes:
      - { name: change_id, type: uuid, required: true, unique: true, constraints: "clave primaria" }
      - { name: user_id, type: reference, references: User, required: true }
      - { name: change, type: enum, required: true, allowed: [created, deactivated, reactivated, role_changed] }
      - { name: old_value, type: text, required: false, description: "rol o estado anterior; nulo en created" }
      - { name: new_value, type: text, required: true, description: "rol o estado nuevo" }
      - { name: actor_kind, type: enum, required: true, allowed: [user, system] }
      - { name: actor_user_id, type: reference, references: User, required: false, description: "no nulo si y solo si actor_kind es user" }
      - { name: actor_system, type: reference, references: ActorSystem, required: false, description: "no nulo si y solo si actor_kind es system" }
      - { name: at, type: UtcTimestamp, required: true }
    constraints:
      - "Restricción CHECK: (actor_kind = user Y actor_user_id no nulo Y actor_system nulo) O (actor_kind = system Y actor_system no nulo Y actor_user_id nulo)."
      - "actor_system solo admite valores de ActorSystem (restricción CHECK generada de la lista versionada)."
      - "Sin UPDATE ni DELETE para ningún usuario de base de datos; tampoco para el de retención (no es purgable)."

  - name: WebSession
    description: Sesión web del servidor detrás de la cookie veridicus_session (P5 de Contract Design).
    storage: { kind: mutable, purgeable: false }
    attributes:
      - { name: session_token_hash, type: text, required: true, unique: true, constraints: "clave primaria; SHA-256 del token de 256 bits de la cookie; nunca el token" }
      - { name: user_id, type: reference, references: User, required: true }
      - { name: csrf_token_hash, type: text, required: true, description: "SHA-256 del token anti-CSRF (≥ 32 caracteres, C1); el valor solo viaja en GET /auth/me" }
      - { name: created_at, type: UtcTimestamp, required: true }
      - { name: last_seen_at, type: UtcTimestamp, required: true, description: "última petición autenticada; caducidad por inactividad (NFR10.3 de U3)" }
      - { name: expires_at, type: UtcTimestamp, required: true, description: "created_at más la duración total (NFR10.3 de U3)" }
      - { name: revoked_at, type: UtcTimestamp, required: false }
    constraints:
      - "Válida si y solo si revoked_at es nulo, no pasó expires_at, no pasó la inactividad máxima desde last_seen_at y su usuario está activo."
      - "La purga diaria de session-api borra las filas vencidas o revocadas hace más de 7 días (NFR8.3 de U3); WebSession no es historial."

  - name: Principal
    description: Usuario autenticado tal como lo recibe ConsoleApi de IdentityAccess (C12 v2.0.0). Valor, sin almacenamiento.
    attributes:
      - { name: user_id, type: uuid, required: true }
      - { name: username, type: text, required: true }
      - { name: role, type: enum, required: true, allowed: [analista, admin, investigador] }
    constraints:
      - "Se resuelve de la base en cada petición, sin caché (NFR10.3 de U3): un cambio de rol o una desactivación vale desde la petición siguiente."

  - name: PermissionMatrix
    description: Matriz de FR1.2 (revisión 3) como datos. ConsoleApi la aplica con las extensiones de cada ruta (ADR-009); una prueba la compara con el OpenAPI.
    storage: { kind: versioned_file }
    attributes:
      - name: action
        type: enum
        required: true
        unique: true
        allowed:
          - manage_users
          - create_session_and_testimony
          - launch_final_mode
          - decide_suggestions_and_consolidate
          - read_sessions_and_reports
          - export_report
          - research_reports
          - change_configuration
        retired:
          - { value: upload_scenario, reason: "FR2 retirado (cambio 01)" }
          - { value: apply_threshold_change, reason: "sale el umbral; la sustituye change_configuration (FR9.2)" }
          - { value: decide_alerts_and_consolidate, reason: "la alerta no existe tras el cambio 01; la sustituye decide_suggestions_and_consolidate" }
      - { name: analista, type: enum, required: true, allowed: [allow, deny, owner_only] }
      - { name: admin, type: enum, required: true, allowed: [allow, deny, owner_only] }
      - { name: investigador, type: enum, required: true, allowed: [allow, deny, owner_only] }
    constraints:
      - "Valores vigentes: manage_users (deny, allow, deny); create_session_and_testimony (allow, deny, deny); launch_final_mode (owner_only, deny, deny); decide_suggestions_and_consolidate (owner_only, deny, deny); read_sessions_and_reports (allow, allow, deny), según P4 = A; export_report (owner_only, allow, deny), según A-3; research_reports (deny, deny, allow), según FR13.5; change_configuration (deny, deny, deny), sin ruta en C1 (FR9.2)."
      - "No existe columna ni valor para la persona entrevistada (VE-09)."

  - name: RouteSecurity
    description: Las extensiones de seguridad de cada operación del OpenAPI de C1, leídas como datos al arrancar ConsoleApi.
    storage: { kind: versioned_file, source: "contracts/api/console.v2.yaml (U1)" }
    attributes:
      - { name: path, type: text, required: true }
      - { name: method, type: enum, required: true, allowed: [get, post, patch] }
      - { name: public, type: boolean, required: true, description: "true solo en POST /auth/login, /healthz y /readyz (security: [])" }
      - { name: roles, type: list, required: false, allowed: [analista, admin, investigador], description: "x-veridicus-roles; ausente solo en rutas públicas y en las rutas de todos los roles autenticados (/auth/logout, /auth/me, /notice)" }
      - { name: owner_only, type: boolean, required: true, default: false, description: "x-veridicus-owner-only" }
      - { name: owner_only_for_role, type: enum, required: false, allowed: [analista, admin, investigador], description: "x-veridicus-owner-only-for-role; debe ser uno de roles" }
      - { name: demo, type: boolean, required: true, default: false, description: "x-veridicus-demo (ADR-016)" }
      - { name: access_log, type: enum, required: false, allowed: [session, suggestion, report_version], description: "x-veridicus-access-log (P5 = A); report_export nunca va por la marca" }
      - { name: priority, type: enum, required: false, allowed: [SHOULD], description: "x-veridicus-priority" }
    constraints:
      - "owner_only y owner_only_for_role no se declaran juntos."
      - "Toda ruta con owner_only, owner_only_for_role o access_log tiene un parámetro de ruta del que sale el recurso y un resolvedor registrado por la unidad dueña de la ruta."
      - "Una extensión x-veridicus-* desconocida o con un valor fuera de lo permitido impide arrancar ConsoleApi."

  - name: AuditConvention
    description: >
      Convención común de historiales (ADR-003) que entrega U3 y cumplen las demás unidades. No es una
      tabla: es la marca única que cada tabla de la base lleva en su comentario, y que la prueba común
      descubre en el catálogo de PostgreSQL.
    storage: { kind: table_comment, marker: "veridicus-audit" }
    attributes:
      - { name: table, type: identifier, required: true, unique: true, description: "tabla que lleva la marca" }
      - { name: kind, type: enum, required: true, allowed: [history, mutable], description: "history: solo inserción para el usuario de la aplicación; mutable: el resto" }
      - { name: purgeable, type: boolean, required: true, description: "si el usuario de retención puede borrar sus filas (P7 = A)" }
      - { name: actor_user_column, type: identifier, required: false, default: actor_user_id, description: "solo en history; columna del actor persona (ADR-003 «actor»)" }
      - { name: at_column, type: identifier, required: false, default: at, description: "solo en history; columna de la hora (ADR-003 «at»)" }
      - { name: owner_unit, type: enum, required: true, allowed: [U3, U4, U5, U6, U7, U8, U9, U12, U13] }
    constraints:
      - "Toda tabla del esquema de la aplicación lleva la marca; una tabla sin marca pone en rojo la prueba común (R-01)."
      - "Toda tabla history tiene actor_kind, la columna del actor persona, actor_system y la columna de la hora, con la misma restricción CHECK que UserChange."
      - "No son purgables: User, UserChange, WebSession, AnalystAcknowledgement, AccessLogEntry y RetentionAct (A-2, C24)."
      - "La marca es lo único que la prueba común lee: no hay sufijo de nombre ni lista paralela."

  - name: ActorSystem
    description: Lista cerrada y versionada de actores que no son personas, para las filas de historial que no escribe un usuario (P6 = A).
    storage: { kind: versioned_file, source: "db/audit/actor-systems.v1.yaml (U3)" }
    attributes:
      - { name: name, type: text, required: true, unique: true, constraints: "kebab-case, [a-z][a-z0-9-]{2,31}" }
      - { name: owner_unit, type: enum, required: true, allowed: [U3, U4, U5, U6, U7, U8, U9, U12, U13] }
      - { name: writes_to, type: list, required: true, description: "tablas history en las que puede aparecer" }
    constraints:
      - "Valores iniciales (v1): create-admin (U3: UserChange), retention-job (U13: RetentionAct), analysis-worker (U4: las tablas de corridas y del registro de llamadas a modelos). Cada valor nuevo entra por PR con una versión menor."
      - "La restricción CHECK de cada tabla history se genera de esta lista; una prueba de nivel 0 compara la lista con las restricciones de las migraciones."

  - name: DatabaseRole
    description: Usuarios de base de datos que la convención define en su migración (P7 = A, NFR11, A-2).
    storage: { kind: migration }
    attributes:
      - { name: name, type: enum, required: true, unique: true, allowed: [veridicus_app, veridicus_retention] }
      - { name: on_history, type: list, required: true, description: "permisos sobre tablas history" }
      - { name: on_mutable, type: list, required: true, description: "permisos sobre tablas mutable" }
      - { name: secret_ref, type: text, required: true, description: "nombre del Secret que crea el humano; los manifiestos solo lo referencian" }
    constraints:
      - "veridicus_app: SELECT e INSERT en history, nunca UPDATE ni DELETE; en mutable, lo que declare cada unidad en su migración."
      - "veridicus_retention: SELECT en todas las tablas; DELETE solo en las purgables; INSERT solo en RetentionAct; nunca UPDATE."
      - "Ninguno de los dos es dueño de las tablas ni puede cambiar permisos; las migraciones corren con un tercer usuario, solo en el Job de migraciones (project.md Forbidden)."

  - name: ProblemResponse
    description: Cuerpo de error del manejador único de ConsoleApi (RFC 9457, regla 6 de C1). Valor.
    attributes:
      - { name: type, type: uri-reference, required: true }
      - { name: title, type: text, required: true }
      - { name: status, type: integer, required: true, description: "el que fija el catálogo para el code" }
      - { name: code, type: enum, required: true, description: "un valor del catálogo único ErrorCode de U1" }
      - { name: detail, type: text, required: true, description: "en español, del catálogo de mensajes; nunca el mensaje de una excepción" }
      - { name: instance, type: text, required: false, description: "identificador de la petición, sin datos" }
    constraints:
      - "Media type application/problem+json."
      - "Sin datos sensibles: ni texto de testimonio, ni nombres de usuario, ni trazas."

  - name: AccessRecord
    description: Lo que ConsoleApi entrega al puerto AccessLog (C23) tras una lectura marcada. Valor; lo guarda EthicsGovernance (U13) como AccessLogEntry.
    attributes:
      - { name: user_id, type: uuid, required: true }
      - { name: resource_type, type: enum, required: true, allowed: [session, suggestion, report_version, report_export] }
      - { name: resource_id, type: uuid, required: true }
      - { name: export_sha256, type: text, required: false, description: "solo en report_export, y lo envía la ruta de exportación de U7, no la marca" }
    constraints:
      - "Solo identificadores (VE-11, NFR10)."
```

## Resumen

- **User** es el agregado de IdentityAccess, con tres roles. **UserChange** es su historial. Su actor
  nunca es nulo: una persona (`actor_user_id`) o un actor de sistema de la lista cerrada
  (`actor_system`, p. ej. `create-admin`).
- **WebSession** respalda la cookie de C1. La base guarda solo el hash del token y caduca por inactividad
  y por tiempo total.
- **Principal** es lo que ConsoleApi recibe en cada petición (C12). **PermissionMatrix** y
  **RouteSecurity** son la matriz de FR1.2 y las extensiones de C1 como datos, para que una tabla de
  casos las pruebe y para que ConsoleApi no arranque con una ruta mal declarada.
- **AuditConvention**, **ActorSystem** y **DatabaseRole** son lo que U3 entrega a las demás unidades
  (US8.4):
  - una marca única por tabla;
  - una lista cerrada de actores de sistema;
  - dos usuarios de base de datos, el de la aplicación y el de retención.
- **ProblemResponse** y **AccessRecord** son los valores que ConsoleApi produce en el manejador de errores
  y en el registro de acceso.
