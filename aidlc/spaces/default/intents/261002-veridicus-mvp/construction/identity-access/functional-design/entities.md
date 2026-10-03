# Entidades — U3 identity-access

**Insumos.** Unidad U3 de `inception/units-generation/unit-of-work.md` (unit-of-work); historias
US8.1–US8.4 (vía `unit-of-work-story-map.md`); FR1, FR9, NFR10 y NFR11 de
`inception/requirements-analysis/requirements.md` (requirements); componentes IdentityAccess y
ConsoleApi, ADR-003, ADR-004 y ADR-009 de `inception/domain-design/components.md` (components);
contratos C1 y C12 de `inception/contract-design/contract-summary.md` (contract-summary); pantallas M0 y
M6 de `refined-mockups/mockups.md`; respuestas P1–P3 de `functional-design-questions.md`.

**Frontera AUTONOMIA-04.** Todas las entidades viven en PostgreSQL dentro del clúster (módulo
IdentityAccess de `session-api`); ningún dato de esta unidad sale del clúster.

```yaml
entities:
  - name: User
    description: Usuario local de la consola. Agregado raíz de IdentityAccess.
    attributes:
      - { name: user_id, type: uuid, required: true, unique: true }
      - { name: username, type: text, required: true, unique: true, constraints: "único sin distinguir mayúsculas; se guarda normalizado en minúsculas; 3–32 caracteres de [a-z0-9._-]" }
      - { name: role, type: enum, required: true, allowed: [analista, admin] }
      - { name: password_hash, type: text, required: true, constraints: "hash adaptativo con sal; nunca la contraseña en claro (FR1.1)" }
      - { name: active, type: boolean, required: true, default: true }
      - { name: created_by, type: reference, references: User, required: false, description: "null solo para el primer admin creado por el comando de arranque (P1)" }
      - { name: created_at, type: UtcTimestamp, required: true }
    constraints:
      - "Exactamente dos roles."
      - "Siempre existe al menos un admin activo una vez creado el primero (P2)."
    relationships:
      - { to: UserChange, cardinality: "1..*", direction: "User -> UserChange (el alta es el primer cambio)" }
      - { to: WebSession, cardinality: "0..*", direction: "User -> WebSession" }

  - name: UserChange
    description: Historial de solo inserción de los cambios de un usuario (ADR-003).
    attributes:
      - { name: change_id, type: uuid, required: true, unique: true }
      - { name: user_id, type: reference, references: User, required: true }
      - { name: change, type: enum, required: true, allowed: [created, deactivated, reactivated, role_changed] }
      - { name: old_value, type: text, required: false, description: "rol o estado anterior" }
      - { name: new_value, type: text, required: false, description: "rol o estado nuevo" }
      - { name: actor_user_id, type: reference, references: User, required: false, description: "null solo cuando el actor es el comando de arranque; entonces actor_kind es system" }
      - { name: actor_kind, type: enum, required: true, allowed: [user, system] }
      - { name: at, type: UtcTimestamp, required: true }
    constraints:
      - "actor_kind = user ⇒ actor_user_id no nulo; actor_kind = system solo en el alta del primer admin."
      - "Sin UPDATE ni DELETE para el usuario de la aplicación."

  - name: WebSession
    description: Sesión web del servidor detrás de la cookie veridicus_session (contract-design P5).
    attributes:
      - { name: session_token_hash, type: text, required: true, unique: true, description: "solo el hash del identificador opaco de la cookie" }
      - { name: user_id, type: reference, references: User, required: true }
      - { name: csrf_token, type: text, required: true, constraints: "≥ 32 caracteres aleatorios (C1)" }
      - { name: created_at, type: UtcTimestamp, required: true }
      - { name: expires_at, type: UtcTimestamp, required: true, description: "duración que fija NFR Requirements" }
      - { name: revoked_at, type: UtcTimestamp, required: false }
    constraints:
      - "Una sesión es válida si no está revocada, no venció y su usuario está activo."

  - name: Principal
    description: Usuario autenticado tal como lo ve ConsoleApi (C12), valor.
    attributes:
      - { name: user_id, type: uuid, required: true }
      - { name: username, type: text, required: true }
      - { name: role, type: enum, required: true, allowed: [analista, admin] }

  - name: PermissionMatrix
    description: Matriz de FR1.2 como datos; ConsoleApi la aplica en cada ruta (ADR-009).
    attributes:
      - { name: action, type: enum, required: true, unique: true, allowed: [manage_users, upload_scenario, create_session_and_testimony, decide_alerts_and_consolidate, read_sessions_and_reports, apply_threshold_change] }
      - { name: analista, type: enum, required: true, allowed: [allow, deny, owner_only] }
      - { name: admin, type: enum, required: true, allowed: [allow, deny, owner_only] }
    constraints:
      - "apply_threshold_change no tiene ruta en C1: se aplica por PR a la configuración (FR9.2, AC8.3.1)."

  - name: AuditConvention
    description: >
      Convención común de historiales de solo inserción (ADR-003) que entrega U3 y verifican las demás
      unidades. No es una tabla: es el contrato que cumple cada tabla de historial.
    attributes:
      - { name: table, type: identifier, required: true, unique: true, description: "UserChange, SessionStatusChange, ReviewDecision, CotView, ReportVersion y las que se añadan" }
      - { name: actor_column, type: identifier, required: true, default: actor_user_id }
      - { name: at_column, type: identifier, required: true, default: at }
      - { name: registered_by_unit, type: identifier, required: true }
    constraints:
      - "Cada tabla registrada entra automáticamente en la prueba común de nivel 1."
```

## Resumen

- **User** es el agregado de IdentityAccess; **UserChange** es su historial de solo inserción, con
  actor «sistema» solo para el primer `admin` (P1).
- **WebSession** respalda la cookie de C1; la base guarda el hash del identificador, nunca el valor.
- **Principal** es lo que ConsoleApi recibe de IdentityAccess (C12); **PermissionMatrix** es la matriz
  de FR1.2 como datos, para que la pruebe una tabla de casos.
- **AuditConvention** es la convención que U3 entrega a las demás unidades (US8.4).
