# Requisitos de seguridad — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
vigente de U3.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **IDs.** Los requisitos conservan su ID; cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
  NFR11.2 queda **Retirado** sin renumerar. Lo nuevo toma el número siguiente de su grupo:
  NFR10.16–NFR10.23 y NFR11.3–NFR11.5.
- **FD-U3-12:** NFR11.1 se precisa con BR6.1 (actor nunca nulo) y NFR11.2 (umbral) se retira; la
  configuración por PR pasa a NFR11.4.
- **Revisión 1:** se cierran sus hallazgos R-01 a R-06 (`reviews/review-01.md`), en las filas que los
  citan.
- **Sin preguntas** en esta pasada (ver `nfr-requirements-questions.md`); lo que precisa artefactos
  aprobados está en §7.

**Insumos.**
- Flujos F1–F13 y escenarios E1–E43 de `functional-design/functional-spec.md` (functional-spec, revisión
  2), reglas BR1.1–BR9.5 de `functional-design/rules.md` (rules, revisión 2) y entidades de
  `functional-design/entities.md`, con la tabla FD-U3-01 a FD-U3-13.
- FR1, FR9, NFR1, NFR10, NFR11 y NFR12 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3) y VE-09, VE-11, VE-13, A-2 y A-3 de `requirements-adenda-02.md`.
- C1, C12, C16, C23, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary,
  revisión 3).
- NFR de U1, revisión 2 (`construction/contracts/nfr-requirements/security-requirements.md`): tabla de
  valores delegados, NFR10.3, NFR10.7 y NFR10.14.
- Lo que piden a U3 los Functional Design de U4, U6, U7, U12 y U13.
- Respuestas P1–P4 de `nfr-requirements-questions.md` y prácticas de `team.md` y `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de prueba de `team.md`: nivel 0
(unitarias y estáticas, cada PR), nivel 1 (integración con PostgreSQL y Redis reales, cada PR), nivel 3
(E2E y humo). Los comandos están en `tech-stack-decisions.md` §5.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera |
|---|---|---|
| IdentityAccess y ConsoleApi (autenticación, autorización, Problem Details, registro de acceso) | `session-api`, dentro del clúster | Cookie, token anti-CSRF y respuestas al navegador por el Ingress con TLS (BR1.8); al puerto `AccessLog` (C23) solo IDs |
| Contador de intentos | Redis, dentro del clúster | Solo claves derivadas (HMAC-SHA256) y contadores |
| `Job` `create-admin` | Dentro del clúster | Lee usuario y contraseña de un Secret; no los imprime ni los registra |
| Migración de la convención de auditoría (usuarios `veridicus_app` y `veridicus_retention`) | `Job` de migraciones, dentro del clúster | Solo permisos; las contraseñas de los usuarios de base de datos vienen de Secrets (NFR10.19) |
| AnalystConsole (M0, M6 y llegada a M8) | `frontend` estático servido por el clúster, corre en el navegador | Solo habla con ConsoleApi (ADR-004) |

U3 no hace ninguna llamada fuera del clúster. Datos que guarda: nombres de usuario y hashes de
contraseña (dato **confidencial**); tokens de sesión y anti-CSRF solo como hash (**restringido**);
historial de usuarios con actor y hora (**interno**).

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Probar contraseñas desde la consola | Spoofing | Alto | NFR10.5 |
| T2 | Robo de la base y ataque fuera de línea a los hashes | Information disclosure | Medio | NFR10.1, NFR10.2 |
| T3 | Robo o reutilización de la cookie de sesión | Spoofing | Medio | NFR10.3, NFR10.22 |
| T4 | Petición falsificada desde otro sitio (CSRF) | Tampering | Medio | NFR10.4 |
| T5 | Enumerar usuarios por la respuesta o por el tiempo | Information disclosure | Medio | NFR10.6, NFR10.5 |
| T6 | Una ruta nueva sin control de rol o con una extensión mal escrita | Elevation of privilege | Alto | NFR10.9, NFR10.16 |
| T7 | Un usuario desactivado o con rol cambiado sigue operando | Elevation of privilege | Medio | NFR10.3, NFR10.15 |
| T8 | Contraseña, token o testimonio en logs, columnas o Problem Details | Information disclosure | Alto | NFR10.7, NFR10.17 |
| T9 | Reescribir o borrar el historial | Repudiation | Alto | NFR11.1, NFR11.3, NFR11.5 |
| T10 | Muchos inicios de sesión a la vez agotan la memoria (Argon2id usa 64 MiB) | Denial of service | Medio | NFR8.1, NFR8.4 |
| T11 | Bloqueo inducido: alguien que conoce un nombre de usuario lo bloquea 15 minutos, o rota usuarios inventados para llenar el semáforo de Argon2id (R-02 de la revisión 1) | Denial of service | Medio | NFR10.5 (límite por origen antes de Argon2id), NFR8.4; riesgo aceptado en §6 |
| T12 | El `investigador` lee hallazgos o una ruta pública devuelve testimonio (VE-09) | Information disclosure | Alto | NFR10.20 |
| T13 | Una respuesta de validación revela la forma de una ruta a quien no puede usarla | Information disclosure | Bajo | NFR10.18 |
| T14 | Contraseñas de los usuarios de base de datos en una migración o en los logs de PostgreSQL | Information disclosure | Alto | NFR10.19 |
| T15 | Perfiles, *prompts*, precios o límites cambiados desde la consola o por un módulo que escribe | Tampering | Alto | NFR11.4 |
| T16 | `/metrics` alcanzable desde el navegador | Information disclosure | Bajo | NFR10.23 |

## 3. Requisitos

### NFR10 — Seguridad de la aplicación

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.1 | se mantiene | Las contraseñas se guardan con Argon2id (P1 = A). | Parámetros `m = 65 536 KiB`, `t = 3`, `p = 1`, sal aleatoria de 16 bytes y hash de 32 bytes; el hash guardado empieza por `$argon2id$v=19$m=65536,t=3,p=1$`. Si los parámetros configurados cambian, el siguiente inicio de sesión correcto vuelve a calcular el hash. | Nivel 0 (prefijo y re-hash) y nivel 1 (E2) |
| NFR10.2 | cambia | Política de contraseñas (P2: 8 con composición y lista común); el tope de longitud es una cifra de C25. | **Política** (`422` `user.weak_password`, BR2.9): menos de 8 caracteres; sin al menos una mayúscula (categoría Unicode `Lu`), una minúscula (`Ll`), un número (`Nd`) y un símbolo (cualquier carácter de las categorías `P*` o `S*`; el espacio no cuenta); o presente, sin distinguir mayúsculas, en la lista de contraseñas comunes de `tech-stack-decisions.md` D15 (≥ 10 000 entradas, SHA-256 comprobado por la prueba). La longitud se cuenta en puntos de código tras normalizar a NFC. **Tope**: más de `password_max_chars` = 128 lo rechaza el esquema con `422` `validation.invalid_request` (NFR10.7 de U1, NFR-U3-01). Aplica en `POST /users` y en `create-admin` (que termina con código distinto de 0). Casos: uno negativo y uno positivo por clase (`Abcdef1!` pasa; `abcdef1!`, `ABCDEF1!`, `Abcdefg!`, `Abcdefg1`, `Abcde1!` fallan; `Password1!` en la lista falla; `Ñandú12¿` pasa), más 128 y 129 caracteres (cierra R-04). | Nivel 0 |
| NFR10.3 | cambia | La sesión web caduca por inactividad y por tiempo total (P3 = A); las dos cifras viven en C25. | Token de 256 bits aleatorios; en la base solo su SHA-256. Caduca a los `web_session_idle_s` = 1 800 s sin peticiones autenticadas y a los `web_session_max_s` = 43 200 s del inicio de sesión (NFR-U3-01); el entorno solo puede bajarlas, y el arranque exige inactividad ≥ 300 s y total ≥ 3 600 s y mayor que la inactividad. `last_seen_at` se escribe como máximo una vez cada 60 s (cierra R-01): la caducidad tiene hasta 60 s de holgura. La cookie lleva `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/` y `Max-Age` igual a `web_session_max_s`. Desactivar al usuario, cambiar su rol o cerrar sesión vale desde la petición siguiente (sin caché de sesiones ni de principal). Pruebas con reloj controlado: sin actividad, 1 799 s válida y 1 801 s vencida; con una petición a los 30 s (no escribe) y otra a los 61 s (escribe), vence a los 1 861 s; 43 199 s válida con actividad, 43 201 s vencida. | Nivel 0 y nivel 1 |
| NFR10.4 | se mantiene | El token anti-CSRF no se puede adivinar ni comparar por tiempo. | 256 bits aleatorios por sesión web; comparación en tiempo constante (`hmac.compare_digest`); sin él o distinto, `403` `auth.csrf` sin filas (BR1.5, E4, E41). | Nivel 0 y nivel 1 |
| NFR10.5 | cambia | Se limitan los intentos fallidos (P4 = A), y el origen solo se toma del proxy de confianza. | Por usuario normalizado y por dirección de origen: al quinto fallo dentro de 900 s, las peticiones siguientes de ese usuario o de ese origen reciben `429` `auth.too_many_attempts` con `Retry-After: 900` durante 900 s, exista o no el usuario, sin verificar la contraseña ni tomar el semáforo de NFR8.1. Un inicio de sesión correcto pone a cero el contador del usuario. La clave en Redis es un HMAC-SHA256 del usuario o del origen (nunca en claro) y caduca sola. La dirección sale de `X-Forwarded-For` solo si la conexión viene de `VERIDICUS_TRUSTED_PROXY`, que en el despliegue es el pod CIDR (`project.md`) y el chart no puede dejar vacío (cierra R-02 b). Pruebas: 4 fallos y luego éxito; 5 fallos y luego `429` con contraseña correcta; lo mismo con usuario inexistente; dos `X-Forwarded-For` distintos desde el proxy de confianza no comparten contador; el mismo encabezado desde una conexión que no es de confianza se ignora. | Nivel 1 |
| NFR10.6 | se mantiene | No se revela si un usuario existe. | Usuario inexistente, contraseña errónea y usuario desactivado devuelven el mismo estado y el mismo cuerpo byte a byte (BR1.2, E1), y los tres caminos ejecutan exactamente una verificación Argon2id (el inexistente contra el hash señuelo). | Nivel 0 (espía sobre el verificador) y nivel 1 |
| NFR10.7 | se mantiene | Ninguna contraseña ni token aparece en columnas ni logs. | Tras crear un usuario con una contraseña sembrada e iniciar sesión, 0 coincidencias de la contraseña, del token de sesión y del token anti-CSRF en todas las columnas de texto y en la salida de logs capturada (E2); los logs llevan `user_id`, nunca el nombre de usuario. | Nivel 1 |
| NFR10.8 | cambia | El primer `admin` nace sin exponer su contraseña. | `create-admin` lee usuario y contraseña de variables que vienen de un Secret, valida BR2.9 y NFR10.2, no los imprime y termina con código distinto de 0 si ya existe un `admin` activo (BR3.1, E10). Su alta lleva `actor_kind: system` y `actor_system: create-admin`. Su `Job` corre sin root, con `backoffLimit: 0` y `ttlSecondsAfterFinished: 3600` (cierra R-06). | Nivel 1 y política de manifiestos de U2 |
| NFR10.9 | cambia | La autorización aplica la matriz de tres roles y niega por defecto. | Una ruta que no es pública ni de todos los roles autenticados (`/auth/logout`, `/auth/me`, `/notice`) y no declara `x-veridicus-roles` responde `403` `auth.forbidden` aunque el contrato la permitiera, y la suite de nivel 0 falla (BR4.3, E20). Cada celda «No», «Solo propias» y «Solo propias para el rol» de FR1.2 tiene su prueba `403` con Problem Details en español (BR4.1, BR4.2, BR4.4, E5, E19). Las rutas `x-veridicus-demo` pasan por las mismas guardias y declaran roles (BR4.5, E41). La matriz como datos coincide celda a celda con el OpenAPI (BR4.8, E22). | Nivel 0 y nivel 1 |
| NFR10.10 | se mantiene | Las respuestas de autenticación no se guardan en caché. | `POST /auth/login`, `POST /auth/logout` y `GET /auth/me` responden `Cache-Control: no-store`. | Nivel 0 |
| NFR10.16 | nuevo | ConsoleApi no arranca con una seguridad mal declarada ni con un catálogo de errores incompleto. | El arranque falla, con un log que nombra la ruta o el `code`, ante cada caso de BR4.7 (extensión `x-veridicus-*` desconocida, valor no permitido, `owner-only` junto con `owner-only-for-role`, `owner-only-for-role` fuera de los roles, marca de dueño o de registro sin resolvedor) y ante un `code` sin estado o sin mensaje (BR8.1). Un *fixture* por caso con su control positivo (E21). | Nivel 0 |
| NFR10.17 | nuevo | Todo error de ConsoleApi sale por el manejador único de Problem Details, sin datos sensibles y con el estado del catálogo. | El estado HTTP sale solo del catálogo de U1 (un estado por `code`): `limits.exceeded` responde `413` en toda ruta (P7 = A de U1). Una excepción fuera de la jerarquía de U1 → `500` `system.internal`; un *timeout* o error de PostgreSQL o Redis → `503` `system.unavailable` (BR8.3, E32). Cuerpo `application/problem+json` con `detail` del catálogo de mensajes e `instance` igual al identificador de la petición; 0 coincidencias de un nombre de usuario y de un texto de testimonio sembrados en la excepción, en la respuesta y en el log (BR8.2, E33). La transacción se revierte: 0 filas nuevas tras cualquier error. | Nivel 0 (recorrido del catálogo) y nivel 1 |
| NFR10.18 | nuevo | La validación del cuerpo corre después de la autorización. | Cuerpo y parámetros se validan contra el esquema de la operación de `contracts/api/console.v2.yaml` (`additionalProperties: false`) y responden `422` `validation.invalid_request` sin filas; la misma petición de un rol sin permiso responde `403`, no `422` (BR8.4, E31). | Nivel 1 |
| NFR10.19 | nuevo | Las contraseñas de los usuarios de base de datos nunca están en el repositorio, en una migración ni en los logs. | `veridicus_app` y `veridicus_retention` toman su contraseña de Secrets que crea el humano (`team.md`, Secrets). Ningún archivo de `db/migrations/` contiene `PASSWORD` seguido de un literal (regla estática con control negativo) y `gitleaks` no encuentra nada. Si la migración fija contraseñas, envía solo un verificador SCRAM-SHA-256, nunca el texto (D16). | Nivel 0 y CI |
| NFR10.20 | nuevo | El `investigador` nunca lee sesiones ni hallazgos, y no existe una ruta para la persona entrevistada (VE-09). | `GET /sessions`, `GET /sessions/{session_id}` y las lecturas de hallazgos y de reportes de sesión responden `403` `auth.forbidden` al `investigador`, sin registrar acceso (BR4.6, E17). El enum `Role` tiene exactamente tres valores y ninguna ruta pública devuelve `SessionView`, `ReviewSuggestion` ni contenido de reporte. Para `uploaded_by_username` (FD-U12-05) ConsoleApi resuelve solo el nombre del usuario que subió el reporte, nunca su rol, su estado ni la lista de usuarios. | Nivel 0 (OpenAPI) y nivel 1 |
| NFR10.22 | nuevo | La consola solo se sirve por HTTPS (BR1.8; cierra R-03). | El único acceso del navegador es el Ingress con TLS que fija Infrastructure Design de U3, en las dos máquinas. La prueba de humo inicia sesión sobre HTTPS y comprueba `Set-Cookie` con `Secure`, `HttpOnly` y `SameSite=Strict` (E39). | Nivel 3 |
| NFR10.23 | nuevo | `/metrics` no se publica al navegador. | Las métricas se sirven en un puerto interno que ningún Ingress enruta; una petición a `/metrics` por el Ingress responde `404`. | Nivel 3 (humo) y política de manifiestos de U2 |

NFR10.11–NFR10.15 y NFR10.21 están en `reliability-requirements.md`.

### NFR11 — Integridad y auditoría

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.1 | cambia (precisado por BR6.1, FD-U3-12) | Todo historial de todas las unidades solo admite inserciones para la aplicación y lleva actor y hora no nulos. | La prueba común aplica todas las migraciones y descubre las tablas por la marca `veridicus-audit` (BR6.3, E14). En cada tabla `history`: los cinco `INSERT` inválidos de F8 fallan (actor persona nulo con `actor_kind: user`, `actor_system` nulo con `system`, las dos columnas llenas, hora nula, actor fuera de la lista) y un caso válido de cada clase entra (BR6.1, BR6.4, E27, E28); con `veridicus_app`, `UPDATE` y `DELETE` fallan por permisos (BR6.2, E13); una columna declarada en la marca que no existe pone la prueba en rojo (BR6.6, E30). Sale la excepción «actor nulo en el alta del primer `admin`» de la revisión 1. | Nivel 1 (prueba común) y nivel 0 (lista frente a las restricciones CHECK) |
| NFR11.2 | **Retirado** | El umbral ya no existe tras el cambio 01 (FR9.2); la configuración por PR pasa a NFR11.4. | — | — |
| NFR11.3 | nuevo | Solo el usuario de retención borra, y solo las tablas purgables (A-2). | Con `veridicus_retention`, tabla por tabla: `DELETE` funciona si la marca dice `purgeable: true` y falla en `User`, `UserChange`, `WebSession`, `AnalystAcknowledgement`, `AccessLogEntry` y `RetentionAct`; `UPDATE` falla en todas; `INSERT` solo funciona en `RetentionAct` (BR6.5, E29). La prueba común recorre también las tablas de U4–U13 (pedido de U12 y U13). | Nivel 1 |
| NFR11.4 | nuevo | Perfiles, proveedores, *prompts*, precios y límites solo cambian por PR. | 0 operaciones del OpenAPI que los escriban, con el *fixture* de control `PATCH /profiles/{name}` en rojo (BR5.1, E11); Playwright no encuentra con ninguno de los tres roles un control que los cambie; la regla estática falla si un módulo distinto del cargador abre para escritura uno de esos archivos, con control negativo (BR5.2, E12); al cambiar un perfil cambia `config_sha256` (BR5.3). | Nivel 0 y nivel 3 |
| NFR11.5 | nuevo | Todo cambio de usuario queda completo en el historial o no se aplica. | Alta, desactivación, reactivación y cambio de rol insertan su `UserChange` en la misma transacción, con valor anterior y nuevo; un campo con el mismo valor no produce fila (BR2.8, E42). Un `PATCH` con `active` y `role` evalúa las guardias en el orden de BR2.11 y deja 0 o como máximo 2 filas, primero `deactivated`/`reactivated` y luego `role_changed` (E23). | Nivel 1 |

### NFR1 — Soberanía de datos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR1.1 | se mantiene | U3 no hace llamadas fuera del clúster. | El código de U3 no abre conexiones salvo a PostgreSQL y Redis configurados; la `NetworkPolicy` de U2 niega la salida a internet de `session-api`. | Política estática de U2 (nivel 0) |

### NFR12 — Datos sintéticos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR12.1 | se mantiene | Usuarios de prueba ficticios. | Todo usuario de las pruebas y de los datos de demostración tiene nombre del catálogo sintético de U1 (`contracts/fixtures/synthetic-names.yaml`). | Revisión del PR y comprobación de U1 |

## 4. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U3 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | El primer `admin`, los usuarios de base de datos y la configuración solo cambian por artefactos revisados (`Job`, migración y PR) | NFR10.8, NFR10.19, NFR11.4 |
| AUTONOMIA-02 | Cada requisito tiene su prueba y su umbral; los comandos están en `tech-stack-decisions.md` §5 | Todas |
| AUTONOMIA-03 | Toda acción queda con quién y cuándo; nadie reescribe el historial; solo la retención borra | NFR11.1, NFR11.3, NFR11.5 |
| AUTONOMIA-04 | Sin llamadas externas; el `investigador` no lee testimonio | NFR1.1, NFR10.20 |
| AUTONOMIA-05 | No aplica: U3 no emite hallazgos | — |

## 5. Respuestas a preguntas abiertas de otras unidades

| Unidad y pregunta | Respuesta de U3 |
|---|---|
| U13 §11 pregunta 3 y U7 §12 pregunta 3 (plazo de `AccessLog`) | En las lecturas marcadas (F11), `AccessLog.record` tiene 500 ms dentro de un punto de guardado (NFR10.21). La exportación llama al puerto ella misma y su plazo lo fija U7; si U7 no fija otro, usa el mismo valor |
| U12 (el manejador registra solo `code` e IDs) | NFR10.17 y NFR15.2 |
| U12 y U13 (la prueba común recorre sus tablas) | NFR11.1 y NFR11.3 descubren las tablas por la marca, sin lista |
| U4 (FD-U4-16) y U6 (FD-U6-13) (actores nuevos) | La lista `ActorSystem` v1 que comprueba NFR11.1 incluye `run-supervisor` y `session-supervisor` (NFR-U3-04) |

## 6. Riesgos aceptados

| Riesgo | Por qué queda | Tratamiento |
|---|---|---|
| Quien conoce un nombre de usuario puede bloquearlo 900 s, también al único analista de la demo (T11) | Es el costo de P4 = A, que limita por usuario además de por origen | No hay desbloqueo por la consola ni por un agente: se espera 900 s. La métrica `throttled` (NFR15.1) lo hace visible. Cierra R-02 a |
| Un atacante con muchos orígenes satura el semáforo de Argon2id (T11) | El límite por origen no frena orígenes distintos | NFR8.4 acota la espera y responde `503`; el clúster es local y sin salida pública |
| La caducidad por inactividad tiene hasta 60 s de holgura | `last_seen_at` se escribe como máximo cada 60 s (NFR10.3) | Aceptado: evita una escritura por sondeo |
| Una consola abierta no caduca por inactividad, porque cada sondeo cuenta como actividad | P3 = A de la revisión 1 | La caducidad total de 43 200 s sigue valiendo |
| El registro de una lectura puede faltar si falla el puerto | P5 = A de Functional Design (demostración) | Log de aviso y métrica (NFR10.21, NFR15.1); la exportación no tiene ese riesgo (VE-13, U7) |

## 7. Precisiones a artefactos ya aprobados (NFR-U3-xx)

No edité ningún artefacto aprobado (regla de `project.md`). En la aprobación decides cuáles se llevan al
original, cada una en su propio commit.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| NFR-U3-01 | `contract-design/contract-summary.md` (C25 y cuerpos de `POST /auth/login` y `POST /users` en C1) | U3 fija `web_session_max_s: { value: 43200, unit: s }`. Entran `web_session_idle_s: { value: 1800, unit: s }`, `username_max_chars: { value: 32, unit: chars }` y `password_max_chars: { value: 128, unit: chars }`. `username` y `password` declaran `maxLength` con `x-veridicus-limit` de esos nombres. Entran por un PR de U1 antes del código de B2 | Regla de `project.md` (catálogo único de límites); NFR10.7, NFR10.14 y NFR-U1-07 de U1; aplicada sin preguntar |
| NFR-U3-02 | `requirements-analysis/requirements.md` (NFR11, «el único con `DELETE`») | Se lee como «el único con `DELETE` sobre los historiales y las tablas purgables». `veridicus_app` conserva `DELETE` solo en `WebSession` (tabla `mutable`, no purgable por retención) para el barrido de 7 días que ya fija `entities.md`. Propuesta de texto: añadir «sobre las tablas de historial» | `entities.md` (WebSession); NFR8.3; aplicada sin preguntar |
| NFR-U3-03 | Revisión 1 de este NFR (§5, filas de `ErrorCode` y C15) | Las dos primeras filas quedan superadas por FD-U3-02 y FD-U3-03, ya aprobadas y citadas en NFR10.3 de U1. La tercera se retira: las métricas de U3 son internas de `session-api` y no van a C15, que es el contrato de AIR de U5 (cierra R-05) | R-05 de la revisión 1; aplicada sin preguntar |
| NFR-U3-04 | Functional Design de U3 (FD-U3-08, lista `ActorSystem` v1) | La lista v1 suma `run-supervisor` (FD-U4-16) y `session-supervisor` (FD-U6-13), propuestos por U4 y U6 y aprobados hoy. Entran con sus restricciones CHECK en el mismo PR (BR6.4) | FD-U4-16; FD-U6-13; aplicada sin preguntar |
| NFR-U3-05 | Functional Design de U3 (F11 paso 4, «con el *timeout* de E/S») | El registro corre en un punto de guardado (`SAVEPOINT`) con 500 ms: si falla o vence, se revierte solo el punto de guardado y la respuesta sale con las escrituras del manejador intactas (BR9.3) | BR9.3; preguntas 3 de U13 y de U7; aplicada sin preguntar |
