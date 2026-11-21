# Reglas de negocio — U3 identity-access

**Revisión 2 (2026-11-21), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3 de
Inception.** Sustituye a la revisión 1 del 2026-10-02. Las reglas conservan su ID; ninguna sale. Lo nuevo
sigue la numeración (regla de `project.md`).
- **Siguen sin cambios de fondo:** BR1.1–BR1.6, BR2.1–BR2.6, BR2.8, BR3.2, BR4.2, BR6.2 y BR7.3.
- **Cambian:**
  - BR1.7: el `investigador` llega a M8 (AC8.1.1), y la ruta guardada es interna y se valida (R-07).
  - BR2.7: «pendiente» es toda sesión no consolidada (P8 = A).
  - BR3.1: actor `create-admin` y bloqueo asesor (P6 = A, R-05).
  - BR4.1 y BR4.3: tres roles, y se niega por defecto (NFR10.9 de U3).
  - BR5.1–BR5.3: pasan del umbral a la configuración por PR (FR9.2, AC8.3.1–AC8.3.3).
  - BR6.1: actor nunca nulo (P6 = A, R-02). BR6.3: marca única en el comentario (R-01).
  - BR7.1 y BR7.2: suman las acciones nuevas de M6.
- **Entran:**
  - BR1.8, HTTPS (R-07).
  - BR2.9–BR2.12: validación, 404, desactivación con sesiones pendientes, `PATCH` combinado y
    serialización (R-03, R-04, R-06, P8 = A).
  - BR4.4–BR4.8: extensiones nuevas de C1, VE-09 (P4 = A) y la coherencia matriz ↔ OpenAPI.
  - BR6.4–BR6.6: actores de sistema, usuarios de base de datos y columnas de la marca (P6, P7 = A, R-08).
  - BR8.1–BR8.4: manejador de Problem Details (unit-of-work U3, regla 6 de C1).
  - BR9.1–BR9.5: registro de acceso por la marca (P5 = A, C23).

**Insumos.** Los mismos de `entities.md`:
- `inception/units-generation/unit-of-work.md` (unit-of-work) y `unit-of-work-story-map.md`
  (unit-of-work-story-map);
- `inception/requirements-analysis/requirements.md` (requirements) y `requirements-adenda-02.md`;
- `inception/domain-design/components.md` (components) y `decisions.md`;
- `inception/contract-design/contract-summary.md` (contract-summary);
- las respuestas P1–P8.

Los niveles de prueba (N0, N1, N3, Manual) siguen `team.md` (Testing Posture). Los `code` que aún no
están en C1 se proponen en la tabla de precisiones de `functional-spec.md` (§10).

```yaml
rules:
  # BR1 — Autenticación
  - id: BR1.1
    statement: La contraseña se guarda solo como hash adaptativo con sal y nunca aparece en columnas ni logs.
    category: constraint
    applies_to: [User]
    trigger: Al crear un usuario, al ejecutar create-admin y al iniciar sesión
    logic: SI se guarda o se registra una contraseña ENTONCES solo se guarda su hash Argon2id con sal (parámetros en NFR10.1 de U3); los logs llevan solo identificadores.
    violation: La prueba de nivel 1 que busca una contraseña sembrada en todas las columnas de texto y en los logs capturados falla.
    source: FR1.1; AC8.1.3; NFR10
  - id: BR1.2
    statement: Usuario inexistente, contraseña errónea y usuario desactivado producen el mismo estado y el mismo cuerpo.
    category: authorization
    applies_to: [User]
    trigger: POST /auth/login
    logic: SI el usuario no existe, la contraseña no coincide o el usuario está desactivado ENTONCES 401 con code auth.invalid_credentials y el mismo cuerpo byte a byte; el caso de usuario inexistente verifica contra un hash señuelo para no revelar diferencias de tiempo.
    violation: La prueba de nivel 1 que compara los tres cuerpos falla.
    source: FR1.1; AC8.1.2; AC8.2.3
  - id: BR1.3
    statement: Un inicio de sesión válido crea una sesión web y la entrega en una cookie HttpOnly, Secure y SameSite=Strict.
    category: policy
    applies_to: [WebSession]
    trigger: POST /auth/login con credenciales válidas
    logic: SI las credenciales son válidas ENTONCES se crea una WebSession con su token anti-CSRF y responde 204 con la cookie veridicus_session.
    violation: La prueba de nivel 1 de los atributos de la cookie falla.
    source: FR1.1; AC8.1.1; P5 de Contract Design
  - id: BR1.4
    statement: Toda ruta exige una sesión web válida salvo inicio de sesión y salud.
    category: authorization
    applies_to: [WebSession, RouteSecurity]
    trigger: Cada petición a ConsoleApi
    logic: SI la ruta no es pública (POST /auth/login, /healthz, /readyz) Y no hay sesión válida (no revocada, no vencida por tiempo total ni por inactividad, usuario activo) ENTONCES 401 con code auth.unauthenticated y sin filas nuevas.
    violation: La prueba de nivel 1 que llama cada ruta del OpenAPI sin cookie falla.
    source: AC8.1.4; AC8.2.3
  - id: BR1.5
    statement: Toda petición que cambia estado lleva el token anti-CSRF de su sesión.
    category: authorization
    applies_to: [WebSession]
    trigger: Cada POST o PATCH autenticado
    logic: SI falta X-CSRF-Token o su hash no coincide con el de la sesión ENTONCES 403 con code auth.csrf y sin filas nuevas.
    violation: La prueba de nivel 1 de CSRF falla.
    source: P5 de Contract Design; NFR10
  - id: BR1.6
    statement: Cerrar sesión revoca la sesión web.
    category: policy
    applies_to: [WebSession]
    trigger: POST /auth/logout
    logic: SI el usuario cierra sesión ENTONCES revoked_at se fija y la petición siguiente con esa cookie responde 401.
    violation: La prueba de nivel 1 falla.
    source: C12
  - id: BR1.7
    statement: Tras iniciar sesión, cada rol llega a su inicio, salvo que vuelva de una sesión web vencida.
    category: policy
    applies_to: [Principal]
    trigger: Inicio de sesión exitoso en la consola
    logic: SI la consola guardó, al recibir un 401 por sesión vencida, una ruta interna (relativa, que empieza por una sola barra, sin esquema ni host y presente en la tabla de rutas del rol) junto con el user_id Y el usuario que entra es el mismo ENTONCES vuelve a esa ruta; SI no ENTONCES analista → M1 lista de sesiones, admin → M6 gestión de usuarios, investigador → M8 reportes de corridas y evaluaciones. La ruta se guarda en el almacenamiento de la pestaña y se borra al usarla o al cerrar sesión.
    violation: Pruebas Vitest de la navegación (incluida una ruta externa que se ignora) y prueba de nivel 1 de AC8.1.5.
    source: AC8.1.1; AC8.1.5; AC8.2.4; R-07
  - id: BR1.8
    statement: La consola solo se sirve por HTTPS, porque la cookie Secure no viaja por HTTP.
    category: constraint
    applies_to: [WebSession]
    trigger: Despliegue y prueba de humo
    logic: SI ConsoleApi se alcanza desde el navegador por un origen que no es HTTPS ENTONCES la cookie se descarta sin error visible; por eso el único acceso es el Ingress con TLS que fija Infrastructure Design de U3 y la prueba de humo comprueba que el inicio de sesión devuelve Set-Cookie con Secure sobre HTTPS.
    violation: La prueba de nivel 3 (humo) falla.
    source: R-07; P5 de Contract Design; infraestructura de U3 (Ingress con TLS)

  # BR2 — Gestión de usuarios
  - id: BR2.1
    statement: Solo un admin lista, crea, desactiva, reactiva o cambia el rol de un usuario.
    category: authorization
    applies_to: [User]
    trigger: GET y POST /users, PATCH /users/{user_id}
    logic: SI el principal no es admin ENTONCES 403 con code auth.forbidden y sin filas nuevas.
    violation: Una prueba de nivel 1 por cada rol que no es admin falla.
    source: FR1.2; AC8.2.2
  - id: BR2.2
    statement: Un usuario creado puede iniciar sesión con su rol y su alta queda en el historial.
    category: policy
    applies_to: [User, UserChange]
    trigger: POST /users
    logic: SI un admin crea un usuario analista, admin o investigador ENTONCES se guarda activo y se inserta UserChange created con actor_kind user y el admin como actor_user_id, en la misma transacción.
    violation: La prueba de nivel 1 de alta e inicio de sesión, una por rol, falla.
    source: AC8.2.1; AC8.2.4; FR1.3; ADR-003
  - id: BR2.3
    statement: El nombre de usuario es único sin distinguir mayúsculas.
    category: validation
    applies_to: [User]
    trigger: POST /users
    logic: SI ya existe un usuario con el mismo nombre normalizado ENTONCES 409 con code user.duplicate_username y sin filas nuevas.
    violation: La prueba de nivel 1 falla.
    source: FR1.1; decisión de esta etapa (revisión 1)
  - id: BR2.4
    statement: Desactivar un usuario revoca todas sus sesiones web y conserva la autoría de sus acciones pasadas.
    category: policy
    applies_to: [User, WebSession, UserChange]
    trigger: PATCH /users/{user_id} con active false
    logic: SI se desactiva un usuario ENTONCES se revocan sus WebSession, se inserta UserChange deactivated y ninguna fila de historial de otras unidades cambia.
    violation: La prueba de nivel 1 de AC8.2.3 falla.
    source: AC8.2.3; C12
  - id: BR2.5
    statement: Nadie se desactiva a sí mismo.
    category: constraint
    applies_to: [User]
    trigger: PATCH /users/{user_id} con active false
    logic: SI user_id es el del principal ENTONCES 409 con code user.self_deactivation y sin filas nuevas.
    violation: La prueba de nivel 1 falla.
    source: Respuesta P2 = A
  - id: BR2.6
    statement: El último admin activo no se puede desactivar ni pasar a otro rol.
    category: constraint
    applies_to: [User]
    trigger: PATCH /users/{user_id}
    logic: SI el usuario es admin activo Y es el único admin activo Y el cambio lo desactiva o le da otro rol ENTONCES 409 con code user.last_admin; la comprobación y el cambio van en la misma transacción bajo el bloqueo asesor del conjunto de admins, el mismo de BR3.1.
    violation: Prueba de nivel 1, incluida la de dos peticiones simultáneas.
    source: Respuesta P2 = A; R-05
  - id: BR2.7
    statement: Un usuario no cambia de rol mientras sea dueño de una sesión no consolidada.
    category: constraint
    applies_to: [User]
    trigger: PATCH /users/{user_id} con un role distinto del actual
    logic: SI el puerto PendingSessions de InterviewSession devuelve al menos una sesión del usuario en cualquier estado distinto de consolidated (open, paused, suspended, finalized, terminated o blocked) ENTONCES 409 con code user.has_pending_sessions y sin filas nuevas. ConsoleApi hace la consulta, no IdentityAccess, para no crear una dependencia de IdentityAccess hacia InterviewSession.
    violation: Prueba de nivel 1 con un doble del puerto, una por estado; la prueba con sesiones reales entra en el PR de U4 que crea la tabla de sesiones.
    source: Respuesta P3 = A; respuesta P8 = A; FR1.2; ADR-009
  - id: BR2.8
    statement: Todo cambio de usuario deja una fila en UserChange con estado anterior, nuevo, actor y hora.
    category: policy
    applies_to: [UserChange]
    trigger: Alta, desactivación, reactivación o cambio de rol
    logic: SI cambia un usuario ENTONCES se inserta UserChange en la misma transacción; un campo enviado con el mismo valor que ya tenía no produce fila.
    violation: La prueba de nivel 1 falla.
    source: FR1.3; ADR-003; C12
  - id: BR2.9
    statement: Los datos de un usuario se validan antes de tocar la base, y un usuario inexistente es un 404.
    category: validation
    applies_to: [User]
    trigger: POST /users y PATCH /users/{user_id}
    logic: SI el nombre no cumple 3–32 caracteres de [a-z0-9._-] tras normalizar, el rol no es uno de los tres o el cuerpo trae campos de más ENTONCES 422 con code validation.invalid_request; SI la contraseña no cumple la política de NFR10.2 de U3 ENTONCES 422 con code user.weak_password; SI el user_id del PATCH no existe ENTONCES 404 con code user.not_found. En los tres casos, sin filas nuevas.
    violation: Una prueba de nivel 0 por condición, con su control positivo, y una de nivel 1 del 404.
    source: R-06; NFR10; NFR10.2 de U3
  - id: BR2.10
    statement: Desactivar se permite aunque el usuario tenga sesiones sin consolidar, que quedan en solo lectura hasta que se le reactive.
    category: policy
    applies_to: [User]
    trigger: PATCH /users/{user_id} con active false
    logic: SI el usuario tiene sesiones no consolidadas ENTONCES la desactivación se aplica igual (es un control de seguridad); esas sesiones solo se pueden leer, porque las acciones de dueño exigen que el dueño inicie sesión; GET /users y la respuesta del PATCH incluyen pending_sessions para que M6 muestre el número en la confirmación.
    violation: Prueba de nivel 1 (desactivar con una sesión pendiente da 200 y luego toda acción de dueño sobre esa sesión, por cualquier usuario, da 401 o 403) y prueba Vitest del número en la confirmación.
    source: Respuesta P8 = A; R-03
  - id: BR2.11
    statement: Un PATCH con active y role se aplica completo o no se aplica, en un orden fijo de guardias.
    category: constraint
    applies_to: [User, UserChange]
    trigger: PATCH /users/{user_id} con los dos campos
    logic: SI el PATCH trae active y role ENTONCES, en una sola transacción, se evalúan en este orden validación (BR2.9), existencia (404), autodesactivación (BR2.5), último admin (BR2.6) y sesiones pendientes (BR2.7, solo si cambia el rol); la primera que falla responde y no aplica nada; si todas pasan, se aplica todo y se insertan como máximo dos filas, primero deactivated o reactivated y después role_changed.
    violation: Prueba de nivel 1 de cada combinación (dos campos válidos, el primero falla, el segundo falla).
    source: R-04; C1 (minProperties 1)
  - id: BR2.12
    statement: Un cambio de rol y una acción del mismo usuario no se cruzan.
    category: constraint
    applies_to: [User, Principal]
    trigger: Cada petición que cambia estado y PATCH /users/{user_id}
    logic: SI una petición cambia estado ENTONCES resolve toma un bloqueo compartido sobre la fila del usuario del principal en la transacción de la petición; SI un PATCH cambia active o role ENTONCES toma un bloqueo exclusivo sobre la fila del usuario objetivo antes de las guardias. Así, una sesión que el usuario crea a la vez que cambia su rol termina antes y la ve BR2.7, o empieza después y ve el rol nuevo (403). El orden de bloqueo es usuario → sesión → ronda.
    violation: Prueba de nivel 1 con dos transacciones concurrentes en los dos órdenes.
    source: R-04; ADR-009; regla de orden de bloqueo de NFR Design
  # BR3 — Primer admin
  - id: BR3.1
    statement: El primer admin solo lo crea el comando create-admin, y solo si no existe ningún admin activo.
    category: policy
    applies_to: [User, UserChange]
    trigger: Ejecución del Job create-admin, que el humano aplica
    logic: SI, bajo el bloqueo asesor del conjunto de admins, no hay ningún admin activo ENTONCES crea el admin con usuario y contraseña leídos de un Secret (validados con BR2.9) e inserta UserChange created con actor_kind system y actor_system create-admin; SI ya hay uno ENTONCES termina con código distinto de 0 y no cambia nada.
    violation: Prueba de nivel 1 de las dos ramas y de dos ejecuciones simultáneas (una gana, la otra termina con error).
    source: Respuesta P1 = A; respuesta P6 = A; R-05; AUTONOMIA-01; project.md Forbidden (Secrets)
  - id: BR3.2
    statement: Ninguna ruta de C1 crea usuarios sin un admin autenticado.
    category: authorization
    applies_to: [User, RouteSecurity]
    trigger: Validación del OpenAPI
    logic: SI una ruta crea usuarios sin seguridad sessionCookie y x-veridicus-roles [admin] ENTONCES la suite falla.
    violation: Prueba de nivel 0.
    source: FR1.2; respuesta P1 = A

  # BR4 — Matriz de roles y extensiones de C1
  - id: BR4.1
    statement: ConsoleApi aplica la matriz de tres roles antes de delegar; un rechazo es 403 Problem Details en español y no crea filas.
    category: authorization
    applies_to: [PermissionMatrix, RouteSecurity, Principal]
    trigger: Cada ruta con x-veridicus-roles
    logic: SI el rol del principal no está en x-veridicus-roles de la ruta ENTONCES 403 con code auth.forbidden y sin filas nuevas.
    violation: Una prueba de nivel 1 por cada celda «No» de la matriz.
    source: FR1.2; ADR-009; AC8.2.2
  - id: BR4.2
    statement: Las rutas marcadas solo para el dueño exigen que el principal sea el dueño de la sesión.
    category: authorization
    applies_to: [RouteSecurity, Principal]
    trigger: Cada ruta con x-veridicus-owner-only
    logic: SI el principal no es el dueño de la sesión que resuelve la unidad dueña de la ruta ENTONCES 403 con code session.not_owner; U3 entrega el mecanismo y cada unidad lo declara en sus rutas.
    violation: Una prueba de nivel 1 por cada celda «Solo propias», en la unidad dueña de la ruta.
    source: FR1.2; ADR-009
  - id: BR4.3
    statement: La autorización niega por defecto.
    category: constraint
    applies_to: [RouteSecurity]
    trigger: Validación del OpenAPI, arranque de ConsoleApi y cada petición
    logic: SI una ruta no es pública, no es de todos los roles autenticados (/auth/logout, /auth/me, /notice) Y no declara x-veridicus-roles ENTONCES la suite de nivel 0 falla y, en ejecución, la ruta responde 403 auth.forbidden aunque el contrato la permitiera.
    violation: Prueba de nivel 0 y prueba de nivel 1 con una ruta de control sin roles.
    source: FR1.2; NFR10; NFR10.9 de U3
  - id: BR4.4
    statement: Con x-veridicus-owner-only-for-role, solo el rol nombrado tiene que ser el dueño.
    category: authorization
    applies_to: [RouteSecurity, Principal]
    trigger: Cada ruta con x-veridicus-owner-only-for-role (hoy, POST /reports/{report_version_id}/exports)
    logic: SI el rol del principal es el que nombra la extensión Y no es el dueño de la sesión del recurso ENTONCES 403 con code session.not_owner; SI el rol es otro de los permitidos (el admin en la exportación) ENTONCES pasa sin comprobar dueño.
    violation: Prueba de nivel 1 de U3 con una ruta de control y de U7 en la exportación (analista dueño 201, analista no dueño 403, admin 201, investigador 403).
    source: A-3; VE-13; C1
  - id: BR4.5
    statement: Las rutas de demostración pasan por las mismas guardias y la marca no añade ninguna.
    category: policy
    applies_to: [RouteSecurity]
    trigger: Cada ruta con x-veridicus-demo
    logic: SI una ruta lleva x-veridicus-demo ENTONCES se autentica, se comprueba CSRF y rol igual que las demás, y debe declarar x-veridicus-roles; la marca solo se usa para etiquetar logs y métricas con demo=true; ningún resultado de una ruta demo bloquea una ruta que no lo es.
    violation: Prueba de nivel 0 (toda ruta demo declara roles) y de nivel 1 (POST /acknowledgements sin CSRF da 403).
    source: ADR-016; C1
  - id: BR4.6
    statement: Leen sesiones, hallazgos y reportes de sesión el analista y el admin; el investigador nunca; la persona entrevistada no tiene rol ni ruta.
    category: authorization
    applies_to: [PermissionMatrix, Principal]
    trigger: GET /sessions, GET /sessions/{session_id}, lecturas de hallazgos y de reportes de sesión
    logic: SI el principal es investigador ENTONCES 403 con code auth.forbidden; SI es analista (dueño o no) o admin ENTONCES lee la sesión con sus hallazgos según FR1.2; no existe un cuarto rol ni una ruta sin sesión web que devuelva hallazgos, citas u observaciones.
    violation: Prueba de nivel 0 sobre el OpenAPI (enum Role con exactamente tres valores; ninguna ruta pública devuelve SessionView, ReviewSuggestion ni contenido de reporte) y de nivel 1 del 403 del investigador.
    source: FR1.2; AC8.2.4; VE-09; respuesta P4 = A; AC5.4.4 (con la precisión FD-U3-01)
  - id: BR4.7
    statement: ConsoleApi no arranca con una extensión mal declarada ni con una ruta de dueño sin resolvedor.
    category: constraint
    applies_to: [RouteSecurity]
    trigger: Arranque de ConsoleApi y validación del OpenAPI
    logic: SI una operación trae una extensión x-veridicus-* desconocida, un valor fuera de lo permitido, owner_only junto con owner_only_for_role, un owner_only_for_role que no está en sus roles, o una marca de dueño o de registro de acceso sin parámetro de ruta ni resolvedor registrado ENTONCES el arranque falla con el log de la ruta y la suite de nivel 0 falla.
    violation: Prueba de nivel 0 con un fixture por cada caso y su control positivo.
    source: Code Style de team.md (configuración faltante impide arrancar); C1
  - id: BR4.8
    statement: La matriz como datos y el OpenAPI dicen lo mismo.
    category: constraint
    applies_to: [PermissionMatrix, RouteSecurity]
    trigger: Cada PR
    logic: SI la matriz que se deriva de x-veridicus-roles, x-veridicus-owner-only y x-veridicus-owner-only-for-role de cada ruta, agrupada por acción, no coincide celda a celda con PermissionMatrix ENTONCES la suite falla.
    violation: Prueba de nivel 0 de tabla de casos.
    source: FR1.2 (una prueba por celda); ADR-009

  # BR5 — Configuración solo por PR
  - id: BR5.1
    statement: Ninguna ruta ni control de la consola escribe perfiles, proveedores, prompts, la tabla de precios o los límites.
    category: authorization
    applies_to: [RouteSecurity, PermissionMatrix]
    trigger: Validación del OpenAPI y recorrido de la consola
    logic: SI el OpenAPI tiene una operación POST, PATCH, PUT o DELETE cuya ruta o cuerpo toca perfiles, proveedores, prompts, precios o límites (C18, C25) ENTONCES falla la prueba de nivel 0; SI Playwright, con cada uno de los tres roles, encuentra un control que los cambie ENTONCES falla la de nivel 3.
    violation: Prueba en rojo, con un fixture de control negativo (un OpenAPI con PATCH /profiles/{name}).
    source: AC8.3.1; FR9.2; regla 7 de C1
  - id: BR5.2
    statement: Solo el cargador de configuración abre los archivos de configuración, y solo para leer.
    category: constraint
    applies_to: [RouteSecurity]
    trigger: Regla estática en cada PR, sobre los servicios y la biblioteca
    logic: SI un módulo distinto del cargador de configuración abre para escritura un archivo de perfiles, prompts, precios o límites ENTONCES la regla estática falla; con control negativo.
    violation: Prueba de nivel 0.
    source: AC8.3.2; FR9.1; FR9.2
  - id: BR5.3
    statement: Un cambio de configuración es un PR fusionado en main, y se ve en la huella de las corridas siguientes.
    category: policy
    applies_to: [PermissionMatrix]
    trigger: Cambio de un perfil, un prompt, la tabla de precios o los límites
    logic: SI se cambia la configuración ENTONCES se hace con un PR fusionado en main que muestra autor, fecha y diferencia; las corridas posteriores llevan otra config_sha256; ninguna tarea lo aplica al clúster sin esa aprobación.
    violation: Verificación manual con el git log adjunto y prueba de nivel 0 de que la huella cambia al cambiar un perfil.
    source: AC8.3.3; FR9.2; AUTONOMIA-01

  # BR6 — Convención de auditoría
  - id: BR6.1
    statement: Toda fila de historial tiene un actor y una hora no nulos, sea una persona o un actor de sistema.
    category: constraint
    applies_to: [AuditConvention, UserChange, ActorSystem]
    trigger: INSERT en una tabla con kind history
    logic: SI actor_kind es user y la columna del actor persona es nula, SI actor_kind es system y actor_system es nulo, SI las dos columnas de actor tienen valor, o SI la hora es nula ENTONCES la base rechaza la fila con una restricción CHECK o NOT NULL.
    violation: Prueba común de nivel 1 que, en cada tabla history, intenta los cuatro casos y espera que fallen, más un caso válido de cada clase de actor.
    source: AC8.4.1; FR1.3; ADR-003; respuesta P6 = A; R-02
  - id: BR6.2
    statement: El usuario de la aplicación no puede modificar ni borrar filas de historial.
    category: constraint
    applies_to: [AuditConvention, DatabaseRole]
    trigger: UPDATE o DELETE en una tabla con kind history
    logic: SI veridicus_app intenta UPDATE o DELETE ENTONCES la base lo rechaza por permisos.
    violation: Prueba común de nivel 1 sobre cada tabla history.
    source: AC8.4.2; NFR11; ADR-003
  - id: BR6.3
    statement: Toda tabla de la aplicación declara su clase en una marca única en su comentario, y la prueba común la descubre sola.
    category: policy
    applies_to: [AuditConvention]
    trigger: Migración que crea o cambia una tabla
    logic: SI una tabla del esquema de la aplicación no lleva en su comentario la marca veridicus-audit con kind (history o mutable), purgeable y owner_unit ENTONCES la prueba común falla; las tablas history entran solas en BR6.1, BR6.2 y BR6.5; no hay sufijo de nombre ni lista paralela.
    violation: Prueba común de nivel 1 en rojo ante una migración de control con una tabla sin marca.
    source: US8.4; P5 de Units Generation; R-01
  - id: BR6.4
    statement: Un actor de sistema solo puede ser uno de la lista cerrada y versionada.
    category: validation
    applies_to: [ActorSystem, AuditConvention]
    trigger: INSERT con actor_kind system y cada PR que cambia la lista o una migración
    logic: SI actor_system no está en la lista ActorSystem ENTONCES la base rechaza la fila; SI la restricción CHECK de una tabla history no coincide con la lista versionada ENTONCES falla la prueba de nivel 0; un actor nuevo entra por PR que cambia la lista y las restricciones a la vez.
    violation: Prueba de nivel 1 (un valor fuera de la lista falla) y de nivel 0 (lista frente a migraciones, con control negativo).
    source: Respuesta P6 = A; AC8.4.1
  - id: BR6.5
    statement: Solo el usuario de retención borra, y solo las tablas purgables.
    category: constraint
    applies_to: [DatabaseRole, AuditConvention]
    trigger: DELETE o UPDATE con veridicus_retention
    logic: SI veridicus_retention borra en una tabla con purgeable true ENTONCES el borrado funciona; SI borra en una tabla con purgeable false (User, UserChange, WebSession, AnalystAcknowledgement, AccessLogEntry, RetentionAct) o intenta UPDATE en cualquier tabla ENTONCES la base lo rechaza; su único INSERT permitido es en RetentionAct. U3 define los dos usuarios y sus permisos en su migración; U13 los usa con el Secret que crea el humano.
    violation: Prueba común de nivel 1, tabla por tabla, de las dos ramas y del UPDATE.
    source: NFR11; A-2; C24; respuesta P7 = A
  - id: BR6.6
    statement: La marca dice cuáles son las columnas del actor y de la hora de cada historial.
    category: constraint
    applies_to: [AuditConvention]
    trigger: Migración que crea una tabla history
    logic: SI una tabla history nombra su actor persona o su hora con otra columna (p. ej. consolidated_by y consolidated_at) ENTONCES lo declara en la marca con actor_user_column y at_column; si no, valen actor_user_id y at; actor_kind y actor_system tienen siempre ese nombre; la prueba común falla si una columna declarada no existe.
    violation: Prueba común de nivel 1 con una marca de control que nombra una columna inexistente.
    source: ADR-003 (columnas actor y at); R-08

  # BR7 — Accesibilidad de M0 y M6 (US5.6, cumplida por cada unidad en sus pantallas)
  - id: BR7.1
    statement: M0 y M6 entran en la suite axe de U4 con WCAG 2.1 AA y 0 violaciones serious o critical.
    category: constraint
    applies_to: [User]
    trigger: Nivel 3, antes de etiquetar una entrega
    logic: SI axe reporta una violación serious o critical en M0, M6 o sus diálogos (crear usuario, cambiar rol, confirmar desactivación) ENTONCES la suite falla.
    violation: Prueba de nivel 3 en rojo.
    source: AC5.6.1; unit-of-work-story-map (US5.6 cruza U3)
  - id: BR7.2
    statement: Iniciar sesión y crear, desactivar, reactivar o cambiar el rol de un usuario se puede hacer solo con teclado y con el foco siempre visible.
    category: constraint
    applies_to: [User]
    trigger: Nivel 3
    logic: SI alguna de esas acciones exige ratón, el foco se pierde o Escape no cierra los diálogos de M6 ENTONCES la prueba falla.
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

  # BR8 — Manejador único de Problem Details
  - id: BR8.1
    statement: Todo error de ConsoleApi sale por un solo manejador como Problem Details con un code del catálogo.
    category: policy
    applies_to: [ProblemResponse]
    trigger: Cualquier excepción o rechazo en ConsoleApi
    logic: SI una ruta o una guardia falla ENTONCES el manejador traduce la excepción de la jerarquía de U1 a application/problem+json con su code, el status que fija el catálogo y el detail en español del catálogo de mensajes; SI un code no tiene status o mensaje ENTONCES ConsoleApi no arranca.
    violation: Prueba de nivel 0 que recorre el catálogo (cada code con status y mensaje) y de nivel 1 que fuerza cada clase de excepción.
    source: Unit-of-work U3 (manejador de errores); regla 6 de C1; NFR10; Code Style de team.md
  - id: BR8.2
    statement: Un Problem Details nunca lleva datos sensibles ni el texto de una excepción.
    category: constraint
    applies_to: [ProblemResponse]
    trigger: Cada respuesta de error
    logic: SI se arma un Problem Details ENTONCES detail sale solo del catálogo de mensajes, instance es el identificador de la petición y no se incluyen trazas, mensajes de excepción, nombres de usuario ni texto de testimonio; el log lleva solo IDs.
    violation: Prueba de nivel 1 que siembra un nombre de usuario y un texto de testimonio en una excepción y comprueba 0 coincidencias en la respuesta y en los logs.
    source: NFR10; Code Style de team.md
  - id: BR8.3
    statement: Un error inesperado es 500 y una dependencia caída es 503, nunca un 401 ni un 4xx que confunda al usuario.
    category: policy
    applies_to: [ProblemResponse]
    trigger: Excepción fuera de la jerarquía, timeout o error de PostgreSQL o Redis
    logic: SI la excepción no pertenece a la jerarquía de U1 ENTONCES 500 con code system.internal; SI falla o vence una E/S con PostgreSQL o Redis ENTONCES 503 con code system.unavailable; en los dos casos la transacción se revierte y no quedan filas.
    violation: Prueba de nivel 1 con la base detenida durante POST /auth/login (503, no 401) y con una excepción de control (500 sin traza).
    source: NFR10 (timeout explícito); construction.md (errores en fronteras); R-06
  - id: BR8.4
    statement: El cuerpo y los parámetros se validan contra el OpenAPI antes del manejador.
    category: validation
    applies_to: [RouteSecurity, ProblemResponse]
    trigger: Cada petición autenticada y autorizada
    logic: SI el cuerpo o un parámetro no cumple el esquema de la operación (tipos, campos requeridos, additionalProperties false) ENTONCES 422 con code validation.invalid_request y sin filas nuevas; la validación corre después de la autorización, para no revelar la forma de una ruta a quien no puede usarla.
    violation: Prueba de nivel 1 con un cuerpo con un campo extra en POST /users (422) y la misma petición de un analista (403, no 422).
    source: NFR10 (entradas validadas en las fronteras); C1

  # BR9 — Registro de acceso (C23, VE-11 demostración, VE-13 MUST)
  - id: BR9.1
    statement: Las lecturas marcadas se registran después de que el manejador termina bien y antes de responder.
    category: policy
    applies_to: [RouteSecurity, AccessRecord]
    trigger: Cada ruta con x-veridicus-access-log
    logic: SI el manejador termina con 2xx ENTONCES ConsoleApi llama a AccessLog.record con el user_id del principal, el resource_type de la marca y el resource_id del parámetro de ruta, y después responde; SI la petición se rechazó antes (401, 403, 404, 422) ENTONCES no registra nada.
    violation: Prueba de nivel 1 con un doble del puerto (una llamada por lectura correcta, ninguna por rechazo).
    source: VE-11; C1; C23; respuesta P5 = A
  - id: BR9.2
    statement: Toda ruta que abre una sesión, un hallazgo o un reporte declara la marca, y la exportación nunca.
    category: constraint
    applies_to: [RouteSecurity]
    trigger: Validación del OpenAPI en cada PR
    logic: SI una operación devuelve SessionView, abre las observaciones de un hallazgo o entrega el contenido de un reporte (lista de rutas en FD-U3-05) Y no declara x-veridicus-access-log con el valor que le corresponde ENTONCES la suite falla; SI la ruta de exportación declara la marca ENTONCES también falla, porque la exportación llama al puerto ella misma con export_sha256 (U7, UG-09).
    violation: Prueba de nivel 0 con fixtures de control (ruta de sesión sin marca; exportación con marca).
    source: VE-11; A-3; C1; respuesta P5 = A
  - id: BR9.3
    statement: Si falla el registro de una lectura, la respuesta sale igual y queda constancia.
    category: policy
    applies_to: [AccessRecord]
    trigger: Excepción o timeout de AccessLog.record en una lectura marcada
    logic: SI el registro de una lectura falla ENTONCES la respuesta sale con su 2xx, se escribe un log de aviso solo con IDs y sube la métrica veridicus_access_log_failures_total con el resource_type; el registro de acceso es una demostración y nunca bloquea el uso.
    violation: Prueba de nivel 1 con un doble del puerto que falla (200, log y métrica).
    source: VE-11; DD-02; ADR-016; respuesta P5 = A
  - id: BR9.4
    statement: El sondeo de una sesión ya abierta no es una apertura nueva.
    category: policy
    applies_to: [AccessRecord, RouteSecurity]
    trigger: GET /sessions/{session_id}
    logic: SI la petición trae el parámetro since (sondeo con cursor) ENTONCES no se registra; SI no lo trae (apertura) ENTONCES se registra una vez.
    violation: Prueba de nivel 1 (una apertura y cinco sondeos producen una sola llamada al puerto).
    source: VE-11 («quién abrió qué sesión»); P6 de Contract Design (sondeo); propuesta FD-U3-05
  - id: BR9.5
    statement: Mientras no exista el registro real, ConsoleApi usa el adaptador por defecto y lo avisa.
    category: policy
    applies_to: [AccessRecord]
    trigger: Arranque de ConsoleApi sin el adaptador de U13
    logic: SI no hay un adaptador real de AccessLog cableado ENTONCES se usa el adaptador por defecto de C23, que no registra, deja un aviso solo con IDs al arrancar y /readyz informa access_log not_configured sin dejar de responder 200.
    violation: Prueba de nivel 0 del cableado por defecto (la de la exportación es de U7, y la del adaptador real, de U13).
    source: C23; C16; UG-09
```

## Resumen

| Grupo | Reglas | De qué protege |
|---|---|---|
| BR1 Autenticación | BR1.1–BR1.8 | Contraseñas en claro, enumeración de usuarios, rutas sin sesión, CSRF, cookie perdida por HTTP |
| BR2 Gestión de usuarios | BR2.1–BR2.12 | Gestión por otro rol, datos inválidos, quedarse sin admin (P2), sesiones sin dueño por cambio de rol (P3, P8), cambios a medias y carreras |
| BR3 Primer admin | BR3.1–BR3.2 | Instalación sin admin, dos admins simultáneos, altas fuera de la consola (P1) |
| BR4 Matriz y extensiones | BR4.1–BR4.8 | Acciones fuera del rol o de la sesión propia, rutas sin declarar, la persona entrevistada (VE-09), matriz y OpenAPI desalineados |
| BR5 Configuración por PR | BR5.1–BR5.3 | Que perfiles, proveedores, *prompts*, precios o límites cambien fuera de un PR (AC8.3.1–AC8.3.3) |
| BR6 Auditoría | BR6.1–BR6.6 | Historiales sin autor, reescribibles o sin registrar; borrado fuera del `Job` de retención (AC8.4.1, AC8.4.2, A-2) |
| BR7 Accesibilidad | BR7.1–BR7.3 | M0 y M6 fuera de WCAG 2.1 AA (US5.6) |
| BR8 Problem Details | BR8.1–BR8.4 | Errores sin `code`, con datos sensibles o con un estado engañoso |
| BR9 Registro de acceso | BR9.1–BR9.5 | Lecturas sin registrar, registro que bloquea el uso, sondeos que inundan el registro |
