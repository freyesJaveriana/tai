# Reglas de negocio — U3 identity-access

**Insumos.** Los mismos de `entities.md`. Los niveles de prueba (N0, N1, N3) siguen team-practices.

```yaml
rules:
  # BR1 — Autenticación
  - id: BR1.1
    statement: La contraseña se guarda solo como hash adaptativo con sal y nunca aparece en columnas ni logs.
    category: constraint
    applies_to: [User]
    trigger: Al crear un usuario y al iniciar sesión
    logic: SI se guarda o se registra una contraseña ENTONCES solo se guarda su hash adaptativo con sal; los logs llevan solo identificadores.
    violation: La prueba de nivel 1 que busca una contraseña sembrada en la base y en los logs falla.
    source: FR1.1; AC8.1.3; NFR10
  - id: BR1.2
    statement: Usuario inexistente, contraseña errónea y usuario desactivado producen el mismo estado y el mismo cuerpo.
    category: authorization
    applies_to: [User]
    trigger: POST /auth/login
    logic: SI el usuario no existe, la contraseña no coincide o el usuario está desactivado ENTONCES 401 con code auth.invalid_credentials y el mismo cuerpo byte a byte; el caso de usuario inexistente igual verifica contra un hash señuelo para no revelar diferencias de tiempo.
    violation: La prueba de nivel 1 que compara los cuerpos falla.
    source: FR1.1; AC8.1.2; AC8.2.3
  - id: BR1.3
    statement: Un inicio de sesión válido crea una sesión web y la entrega en una cookie HttpOnly, Secure y SameSite=Strict.
    category: policy
    applies_to: [WebSession]
    trigger: POST /auth/login con credenciales válidas
    logic: SI las credenciales son válidas ENTONCES se crea una WebSession con su token anti-CSRF y responde 204 con la cookie veridicus_session.
    violation: Prueba de nivel 1 de la cookie.
    source: FR1.1; AC8.1.1; contract-design P5
  - id: BR1.4
    statement: Toda ruta exige una sesión web válida salvo inicio de sesión y salud.
    category: authorization
    applies_to: [WebSession]
    trigger: Cada petición a ConsoleApi
    logic: SI la ruta no es /auth/login, /healthz ni /readyz Y no hay sesión válida (no revocada, no vencida, usuario activo) ENTONCES 401 con code auth.unauthenticated.
    violation: La prueba de nivel 1 que llama cada ruta del OpenAPI sin cookie falla.
    source: AC8.1.4; AC8.2.3
  - id: BR1.5
    statement: Toda petición que cambia estado lleva el token anti-CSRF de su sesión.
    category: authorization
    applies_to: [WebSession]
    trigger: Cada POST o PATCH
    logic: SI falta X-CSRF-Token o no coincide con el de la sesión ENTONCES 403 con code auth.csrf y sin filas nuevas.
    violation: Prueba de nivel 1 de CSRF.
    source: contract-design P5; NFR10
  - id: BR1.6
    statement: Cerrar sesión revoca la sesión web.
    category: policy
    applies_to: [WebSession]
    trigger: POST /auth/logout
    logic: SI el usuario cierra sesión ENTONCES revoked_at se fija y la cookie deja de valer.
    violation: Prueba de nivel 1.
    source: C12
  - id: BR1.7
    statement: Tras iniciar sesión, el analista llega a la lista de sesiones y el admin a la gestión de usuarios, salvo que vuelva de una sesión web vencida.
    category: policy
    applies_to: [Principal]
    trigger: Inicio de sesión exitoso en la consola
    logic: SI la consola guardó la ruta donde ocurrió un 401 por sesión vencida Y el usuario que entra es el mismo ENTONCES vuelve a esa ruta; SI no ENTONCES analista → lista de sesiones y admin → gestión de usuarios.
    violation: Pruebas Vitest de la navegación y de nivel 1 de AC8.1.5.
    source: AC8.1.1; AC8.1.5

  # BR2 — Gestión de usuarios
  - id: BR2.1
    statement: Solo un admin crea, desactiva, reactiva o cambia el rol de un usuario.
    category: authorization
    applies_to: [User]
    trigger: GET, POST /users y PATCH /users/{user_id}
    logic: SI el principal no es admin ENTONCES 403 con code auth.forbidden y sin filas nuevas.
    violation: Prueba de nivel 1 de la celda «No» de la matriz.
    source: FR1.2; AC8.2.2
  - id: BR2.2
    statement: Un usuario creado puede iniciar sesión con su rol y su alta queda en el historial.
    category: policy
    applies_to: [User, UserChange]
    trigger: POST /users
    logic: SI un admin crea un usuario con nombre libre ENTONCES se guarda activo y se inserta UserChange created con el admin como actor, en la misma transacción.
    violation: Prueba de nivel 1 de alta e inicio de sesión.
    source: AC8.2.1; FR1.3; ADR-003
  - id: BR2.3
    statement: El nombre de usuario es único sin distinguir mayúsculas.
    category: validation
    applies_to: [User]
    trigger: POST /users
    logic: SI ya existe un usuario con el mismo nombre normalizado ENTONCES 409 con code user.duplicate_username.
    violation: Prueba de nivel 1.
    source: FR1.1; Interpretación de esta etapa
  - id: BR2.4
    statement: Desactivar un usuario revoca todas sus sesiones web y conserva la autoría de sus acciones pasadas.
    category: policy
    applies_to: [User, WebSession, UserChange]
    trigger: PATCH /users/{user_id} con active false
    logic: SI se desactiva un usuario ENTONCES se revocan sus WebSession, se inserta UserChange deactivated y ninguna fila de historial de otras unidades cambia.
    violation: Prueba de nivel 1 de AC8.2.3.
    source: AC8.2.3; C12
  - id: BR2.5
    statement: Nadie se desactiva a sí mismo.
    category: constraint
    applies_to: [User]
    trigger: PATCH /users/{user_id} con active false
    logic: SI user_id es el del principal ENTONCES 409 con code user.self_deactivation.
    violation: Prueba de nivel 1.
    source: Respuesta P2 = A
  - id: BR2.6
    statement: El último admin activo no se puede desactivar ni pasar a analista.
    category: constraint
    applies_to: [User]
    trigger: PATCH /users/{user_id}
    logic: SI el usuario es admin activo Y es el único admin activo Y el cambio lo desactiva o lo pasa a analista ENTONCES 409 con code user.last_admin; la comprobación y el cambio van en la misma transacción con bloqueo para que dos peticiones simultáneas no dejen cero admins.
    violation: Prueba de nivel 1, incluida la de dos peticiones simultáneas.
    source: Respuesta P2 = A
  - id: BR2.7
    statement: Un usuario no cambia de rol mientras sea dueño de sesiones abiertas, suspendidas o finalizadas sin consolidar.
    category: constraint
    applies_to: [User]
    trigger: PATCH /users/{user_id} con role
    logic: SI el usuario es dueño de al menos una sesión en estado open, suspended o finalized ENTONCES 409 con code user.has_open_sessions.
    violation: Prueba de nivel 1 (con el puerto de sesiones de InterviewSession).
    source: Respuesta P3 = A; FR1.2
  - id: BR2.8
    statement: Todo cambio de usuario deja una fila en UserChange con estado anterior, nuevo, actor y hora.
    category: policy
    applies_to: [UserChange]
    trigger: Alta, desactivación, reactivación o cambio de rol
    logic: SI cambia un usuario ENTONCES se inserta UserChange en la misma transacción.
    violation: Prueba de nivel 1.
    source: FR1.3; ADR-003; C12

  # BR3 — Primer admin
  - id: BR3.1
    statement: El primer admin solo lo crea el comando de arranque, y solo si no existe ningún admin activo.
    category: policy
    applies_to: [User, UserChange]
    trigger: Ejecución del comando create-admin como Job revisable
    logic: SI no hay ningún admin activo ENTONCES crea el admin con usuario y contraseña leídos de un Secret e inserta UserChange created con actor_kind system; SI ya hay uno ENTONCES termina con error y no cambia nada.
    violation: Prueba de nivel 1 de las dos ramas.
    source: Respuesta P1 = A; AUTONOMIA-01; project.md Forbidden (Secrets)
  - id: BR3.2
    statement: Ninguna ruta de C1 crea usuarios sin un admin autenticado.
    category: authorization
    applies_to: [User]
    trigger: Validación del OpenAPI
    logic: SI una ruta crea usuarios sin seguridad sessionCookie y rol admin ENTONCES la suite falla.
    violation: Prueba de nivel 0.
    source: FR1.2; Respuesta P1 = A

  # BR4 — Matriz de roles
  - id: BR4.1
    statement: ConsoleApi aplica la matriz de FR1.2 antes de delegar; un rechazo es 403 Problem Details en español y no crea filas.
    category: authorization
    applies_to: [PermissionMatrix, Principal]
    trigger: Cada ruta con x-veridicus-roles
    logic: SI el rol del principal no está en x-veridicus-roles de la ruta ENTONCES 403 con code auth.forbidden y sin filas nuevas.
    violation: Una prueba de nivel 1 por cada celda «No» de la matriz.
    source: FR1.2; ADR-009; AC8.2.2
  - id: BR4.2
    statement: Las rutas marcadas solo para el dueño exigen que el principal sea el dueño de la sesión.
    category: authorization
    applies_to: [PermissionMatrix, Principal]
    trigger: Cada ruta con x-veridicus-owner-only
    logic: SI el principal no es el dueño de la sesión ENTONCES 403 con code session.not_owner; U3 entrega el mecanismo y cada unidad lo declara en sus rutas.
    violation: Una prueba de nivel 1 por cada celda «Solo propias», en la unidad dueña de la ruta.
    source: FR1.2; ADR-009
  - id: BR4.3
    statement: Cada ruta del OpenAPI declara sus roles o que es pública.
    category: constraint
    applies_to: [PermissionMatrix]
    trigger: Validación del OpenAPI y arranque de ConsoleApi
    logic: SI una ruta no es /auth/login, /healthz ni /readyz Y no declara x-veridicus-roles ni es de lectura para ambos roles ENTONCES la suite falla.
    violation: Prueba de nivel 0.
    source: FR1.2; NFR10

  # BR5 — Umbral
  - id: BR5.1
    statement: Ninguna ruta ni control de la consola escribe el umbral.
    category: authorization
    applies_to: [PermissionMatrix]
    trigger: Validación del OpenAPI y recorrido de la consola
    logic: SI existe una ruta que escriba el umbral o un control de umbral en la consola ENTONCES falla la prueba de nivel 0 (OpenAPI) o la de nivel 3 (Playwright con ambos roles).
    violation: Prueba en rojo.
    source: AC8.3.1; FR9.1
  - id: BR5.2
    statement: Solo el cargador de configuración lee y fija el umbral.
    category: constraint
    applies_to: [PermissionMatrix]
    trigger: Regla estática en cada PR
    logic: SI un módulo distinto del cargador de configuración asigna el ajuste del umbral ENTONCES la regla estática falla; con control negativo.
    violation: Prueba de nivel 0.
    source: AC8.3.2; FR9.1
  - id: BR5.3
    statement: Un cambio de umbral es un PR a la configuración del despliegue, y su historial es el de git.
    category: policy
    applies_to: [PermissionMatrix]
    trigger: Cambio de umbral
    logic: SI se cambia el umbral ENTONCES se hace con un PR fusionado en main que muestra autor, fecha, valor anterior y nuevo; ninguna tarea lo aplica al clúster sin esa aprobación.
    violation: Verificación manual con el git log adjunto.
    source: AC8.3.3; FR9.2; AUTONOMIA-01

  # BR6 — Convención de auditoría
  - id: BR6.1
    statement: Toda tabla de historial tiene actor y hora no nulos.
    category: constraint
    applies_to: [AuditConvention, UserChange]
    trigger: INSERT en una tabla registrada
    logic: SI actor o hora son nulos (salvo actor_kind system en el alta del primer admin) ENTONCES la base rechaza la fila.
    violation: Prueba común de nivel 1 sobre cada tabla registrada.
    source: AC8.4.1; FR1.3; ADR-003
  - id: BR6.2
    statement: El usuario de la aplicación no puede modificar ni borrar filas de historial.
    category: constraint
    applies_to: [AuditConvention]
    trigger: UPDATE o DELETE en una tabla registrada
    logic: SI el usuario de la aplicación intenta UPDATE o DELETE ENTONCES la base lo rechaza por permisos.
    violation: Prueba común de nivel 1 sobre cada tabla registrada.
    source: AC8.4.2; NFR11; ADR-003
  - id: BR6.3
    statement: Una tabla de historial nueva se registra en la convención y entra sola en la prueba común.
    category: policy
    applies_to: [AuditConvention]
    trigger: Migración que crea una tabla de historial
    logic: SI una unidad crea una tabla de historial ENTONCES la registra en AuditConvention en el mismo PR; la prueba común falla si encuentra una tabla de historial sin registrar (por el sufijo de nombre acordado o por la marca en su comentario).
    violation: Prueba común de nivel 1.
    source: US8.4; P5 de Units Generation

  # BR7 — Accesibilidad de M0 y M6 (US5.6, cumplida por cada unidad en sus pantallas)
  - id: BR7.1
    statement: M0 y M6 entran en la suite axe de U4 con WCAG 2.1 AA y 0 violaciones serious o critical.
    category: constraint
    applies_to: [User]
    trigger: Nivel 3, antes de etiquetar una entrega
    logic: SI axe reporta una violación serious o critical en M0, M6 o sus diálogos ENTONCES la suite falla.
    violation: Prueba de nivel 3 en rojo.
    source: AC5.6.1; unit-of-work-story-map (US5.6 cruza U3)
  - id: BR7.2
    statement: Iniciar sesión, crear, desactivar y reactivar usuarios se puede hacer solo con teclado y con el foco siempre visible.
    category: constraint
    applies_to: [User]
    trigger: Nivel 3
    logic: SI alguna de esas acciones exige ratón, el foco se pierde o Escape no cierra los diálogos de crear usuario y de confirmar desactivación ENTONCES la prueba falla.
    violation: Prueba de nivel 3 en rojo.
    source: AC5.6.2
  - id: BR7.3
    statement: El estado de un usuario y los errores de M0 y M6 se identifican por texto o icono además del color.
    category: constraint
    applies_to: [User]
    trigger: Nivel 0, Vitest
    logic: SI un estado (Activo, Desactivado) o un mensaje de error se distingue solo por color ENTONCES la prueba falla.
    violation: Prueba de nivel 0 en rojo.
    source: AC5.6.3
```

## Resumen

| Grupo | Reglas | De qué protege |
|---|---|---|
| BR1 Autenticación | BR1.1–BR1.7 | Contraseñas en claro, enumeración de usuarios, rutas sin sesión, CSRF |
| BR2 Gestión de usuarios | BR2.1–BR2.8 | Gestión por un analista, duplicados, quedarse sin admin (P2), sesiones huérfanas por cambio de rol (P3) |
| BR3 Primer admin | BR3.1–BR3.2 | Instalación sin admin; altas fuera de la consola (P1) |
| BR4 Matriz de roles | BR4.1–BR4.3 | Acciones fuera del rol o de la sesión propia (FR1.2, ADR-009) |
| BR5 Umbral | BR5.1–BR5.3 | Que el umbral cambie fuera de un PR revisable (AC8.3.1–AC8.3.3) |
| BR6 Auditoría | BR6.1–BR6.3 | Historiales sin autor o reescribibles (AC8.4.1, AC8.4.2) |
