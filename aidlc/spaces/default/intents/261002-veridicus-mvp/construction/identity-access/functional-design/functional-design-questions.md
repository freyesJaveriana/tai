# Preguntas de Functional Design — U3 identity-access

**Unidad.** U3 `identity-access` (tipo `service`): inicio de sesión y sesión web, gestión de usuarios
por el `admin`, matriz de roles de FR1.2 en ConsoleApi, ausencia de rutas que escriban el umbral y la
convención común de auditoría con su prueba de nivel 1 (`unit-of-work.md`; historias US8.1–US8.4).

**Lo que ya está decidido y no se vuelve a preguntar.** Dos roles y su matriz (FR1.2); hash adaptativo
con sal (FR1.1); mismo cuerpo de error para usuario inexistente y contraseña errónea (AC8.1.2); cookie
`HttpOnly`, `Secure`, `SameSite=Strict` y cabecera anti-CSRF (contract-design P5); usuario desactivado
→ `401` con sesiones revocadas (AC8.2.3, C12); historiales de solo inserción con `actor` y `at`
(ADR-003); autorización por dueño en ConsoleApi (ADR-009). La política de contraseñas y la duración de
la sesión web las fija NFR Requirements. Solo quedan los tres huecos de abajo.

---

## P1 — Cómo nace el primer `admin`

Solo un `admin` crea usuarios (FR1.2), así que una instalación nueva no tiene con quién entrar. Ningún
contrato prevé ese primer usuario, y team-practices prohíbe migraciones al arrancar un pod y versionar
valores de Secret.

A. Un comando de administración de `session-api` (`create-admin`), ejecutado por el humano como un
   `Job` revisable que lee usuario y contraseña de un Secret; solo funciona si no existe ningún `admin`
   activo y deja fila en el historial con actor «sistema». (Recomendada)
B. Al arrancar, `session-api` crea el `admin` a partir de variables de entorno si no existe ninguno.
C. Una migración de datos siembra el `admin` con una contraseña temporal que se cambia en el primer
   inicio de sesión.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Protección contra quedarse sin administrador

Si el único `admin` activo se desactiva (o lo desactiva otro `admin` que luego se va), nadie puede
volver a gestionar usuarios sin tocar la base de datos.

A. Se rechaza desactivar o cambiar de rol al último `admin` activo, y ningún usuario puede
   desactivarse a sí mismo; ambos casos responden `409` con un `code` nuevo. (Recomendada)
B. Solo se rechaza la autodesactivación; el último `admin` sí se puede desactivar (se recupera con P1).
C. Sin restricciones: la recuperación es siempre el comando de P1.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Cambio de rol de un usuario

C1 permite cambiar el rol (`PATCH /users/{user_id}` con `role`). Un `analista` que pasa a `admin` deja
de poder decidir sobre las alertas de sus sesiones abiertas (FR1.2: el `admin` nunca cambia alertas ni
consolida), y esas sesiones quedarían sin nadie que las cierre.

A. Se permite cambiar de rol solo si el usuario no es dueño de sesiones abiertas, suspendidas o
   finalizadas sin consolidar; si lo es, `409` con un `code` nuevo. (Recomendada)
B. Se permite siempre; las sesiones pendientes quedan en solo lectura hasta que otro analista…
   (no hay traspaso de dueño en el MVP, así que quedarían sin cerrar).
C. No se permite cambiar de rol: se desactiva el usuario y se crea otro con el rol nuevo (cambia C1:
   `role` sale del `PATCH`).
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y revisiones 3 (2026-11-21)

**Lo que ya está decidido y no se vuelve a preguntar.**
- **Tres roles.** `analista`, `admin` e `investigador`, con la matriz de FR1.2 (revisión 3): «Exportar
  el reporte» es solo de las propias sesiones para el analista, se permite al `admin` y se niega al
  `investigador` (A-3, VE-13), y los reportes de la CLI son solo del `investigador` (FR13.5). Lo recogen
  `Role` en C1 y C12 v2.0.0. El `investigador` llega a M8 al entrar (AC8.1.1, M0) y recibe `403` en las
  sesiones (AC8.2.4). M6 ofrece los tres roles (mockups §8).
- **Sale el umbral.** US8.3 cubre ahora perfiles, proveedores, *prompts*, tabla de precios y límites, que
  solo cambian por PR (FR9.2, AC8.3.1–AC8.3.3, regla 7 de C1). BR5.1–BR5.3 y F9 se reescriben sobre esa
  configuración y su `config_sha256`. Las acciones `upload_scenario` (FR2 retirado) y
  `apply_threshold_change` quedan «Retirado».
- **Nuevo en U3.** El manejador único de Problem Details de ConsoleApi (unit-of-work U3, regla 6 de C1,
  Code Style de team.md). Las extensiones de C1 que aplica F2: `x-veridicus-roles`,
  `x-veridicus-owner-only`, `x-veridicus-owner-only-for-role` (exportación) y `x-veridicus-demo`, sin rol
  ni ruta para la persona entrevistada (VE-09). ConsoleApi es el consumidor de C23 (`AccessLog`) y usa su
  adaptador por defecto mientras U13 no exista (UG-09).
- **Convención de auditoría.** AC8.4.1 y AC8.4.2 suman tablas: lanzamientos del modo final,
  «Observaciones consultadas», corridas y registro de llamadas a modelos. NFR11 y A-2 fijan que solo el
  usuario de base de datos del `Job` de retención tiene `DELETE`, y C24 que el acta y el registro de acceso
  sobreviven.
- **Siguen.** P1–P3 = A (primer `admin`, último `admin`, cambio de rol con sesiones pendientes), la cookie
  con CSRF (P5 de Contract Design) y ADR-009. La política de contraseñas y la duración de la sesión web ya
  las fijó NFR Requirements de U3.
- **Cómo se registra la revisión 2.** Reglas, flujos y escenarios conservan su ID. Lo que sale queda
  «Retirado», sin renumerar, y lo nuevo sigue la numeración. Las precisiones pendientes de la revisión 1
  vuelven a la tabla de precisiones como FD-U3-xx:
  - los `code` `user.*` de C1, que hoy pone `validation.invalid_request` en el `409` de
    `PATCH /users/{user_id}`;
  - el puerto de sesiones pendientes;
  - el actor del alta del primer `admin` (según P6).

  Los hallazgos R-01 y R-04 a R-08 de `reviews/review-01.md` son de conocimiento y se corrigen en esta
  pasada sin pregunta. Por ejemplo, para R-01 habrá una sola marca de descubrimiento de las tablas de
  historial, en el comentario de la tabla. R-02 y R-03 son de criterio y van en P6 y P8.

Solo quedan los cinco huecos de abajo.

## P4 — Quién lee los hallazgos de una sesión (VE-09 frente a FR1.2)

Hay dos artefactos aprobados que se contradicen, y la matriz que U3 guarda como datos tiene que elegir
entre ellos:
- FR1.2 (revisión 3) da a `analista` y `admin` «Leer sesiones y reportes: Todas». C1 abre a los dos roles,
  sin `x-veridicus-owner-only`, `GET /sessions/{session_id}` (que trae los hallazgos), las observaciones y
  los reportes.
- AC5.4.4 (adenda 02, VE-09, MUST sin rebaja por DD-07) pide `403` a «cualquier rol distinto del dueño de
  la sesión» que pida sus hallazgos.

ADR-009 lee VE-09 como «la persona entrevistada no tiene rol». A-3 deja exportar al `admin` un reporte
que contiene los hallazgos.

A. La matriz sigue FR1.2: `analista` y `admin` leen todas las sesiones con sus hallazgos, y el
   `investigador` no lee ninguna. VE-09 se cumple así: no existe rol ni pantalla para la persona
   entrevistada, y el `investigador` recibe `403`. Se propone una precisión a AC5.4.4 con ese texto. Es
   coherente con ADR-009, con A-3 y con que el registro de acceso (VE-11) tenga sentido. (Recomendada)
B. Se aplica AC5.4.4 al pie de la letra: solo el dueño lee los hallazgos, y el `admin` y los demás
   analistas ven la sesión sin hallazgos ni reportes. Precisa FR1.2 y las rutas de C1 de U4, U5 y U7, y
   choca con A-3, porque el `admin` exporta un reporte con hallazgos.
C. Término medio: el `admin` lee todo (supervisión y exportación) y otro analista ve la sesión sin
   hallazgos. Precisa FR1.2, AC5.4.4 y C1.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Cómo registra ConsoleApi los accesos (C23) y qué pasa si el registro falla

C1 exige que cada lectura de una sesión, un hallazgo o un reporte, y cada exportación, pase por
`AccessLog` antes de responder. Las exigencias no son iguales:
- VE-11 es una demostración que nunca bloquea el uso (DD-02, ADR-016).
- VE-13 es MUST y exige que la exportación quede en el registro con su SHA-256.

C1 no dice cómo se marca una ruta que registra ni qué pasa si el registro falla.

A. Una marca declarativa en el OpenAPI, `x-veridicus-access-log: session | suggestion | report_version`:
   - El *pipeline* de U3 la aplica cuando el manejador termina bien y antes de responder.
   - Una prueba de nivel 0 comprueba que toda ruta de lectura de esos recursos la declara.
   - Si falla el registro de una lectura, la respuesta sale igual y queda un log con IDs y una métrica,
     porque es una demostración.
   - La exportación llama al puerto ella misma con `export_sha256` (U7, UG-09). Si su registro falla, no
     entrega el archivo (VE-13).

   (Recomendada)
B. La misma marca, pero todo fallo del registro, de lectura o de exportación, responde `503` con
   Problem Details y sin datos.
C. Sin marca: cada unidad llama al puerto desde sus rutas y U3 solo cablea el adaptador.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P6 — Actor de las filas de historial que no escribe una persona

AC8.4.1 y FR1.3 piden que ninguna fila de historial admita un actor nulo. La revisión 1 dejó
`actor_kind: system` con actor nulo para el alta del primer `admin`. El hallazgo R-02 de la revisión 1
lo señaló, porque así la prueba común no se aplica igual a todas las tablas. Esta pasada suma más filas
que no escribe una persona: el acta del `Job` de retención (A-2), y el registro de llamadas a modelos y
las corridas que escribe el trabajador (AC8.4.2).

A. Cada tabla registrada lleva `actor_kind` (`user` | `system`) y un actor que nunca es nulo:
   `actor_user_id` si es `user`, o `actor_system` si es `system`. `actor_system` sale de una lista
   cerrada y versionada en la convención (`create-admin`, `retention-job`, `analysis-worker`…), con una
   restricción `CHECK`. La prueba común prueba los dos nulos en cada tabla. (Recomendada)
B. Un usuario reservado «sistema» en `User`, que no puede iniciar sesión, y `actor_user_id` no nulo en
   todas las tablas. Precisa FR1.2 («exactamente tres roles») o el `Role` de C12.
C. La excepción sigue solo en `UserChange`, y la convención declara, tabla por tabla, qué filas admiten
   actor nulo. Precisa AC8.4.1.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — El usuario de base de datos del `Job` de retención dentro de la convención

NFR11 y A-2 fijan que solo el usuario del `Job` tiene `DELETE`. La prueba comprueba que el usuario de la
aplicación no borra y que el del `Job` sí. El acta y el registro de acceso sobreviven (C24). La
convención y su prueba común son de U3 (US8.4), y el `Job` es de U13 (demostración). Falta decidir
quién define ese usuario y sus permisos, y qué tablas puede borrar.

A. La convención de U3 define los dos usuarios en su migración:
   - El de la aplicación tiene `SELECT` e `INSERT` en los historiales, nunca `UPDATE` ni `DELETE`.
   - El de retención tiene `SELECT` y `DELETE`, nunca `UPDATE`.

   Cada tabla registrada declara si es «purgable». `UserChange`, el registro de acceso y el acta no lo
   son. La prueba común comprueba, tabla por tabla, que el usuario de la aplicación no modifica ni borra
   y que el de retención borra solo las purgables. U13 usa ese usuario con su Secret, que crea el humano.
   (Recomendada)
B. U3 solo prueba al usuario de la aplicación. U13 crea el usuario de retención, sus permisos y su mitad
   de la prueba.
C. Cada unidad concede `DELETE` al usuario de retención sobre sus propias tablas, y U3 solo comprueba
   que el de la aplicación no lo tiene.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P8 — Sesiones pendientes con los estados nuevos, y desactivación de su dueño

P3 = A bloqueó el cambio de rol cuando el usuario es dueño de sesiones `open`, `suspended` o `finalized`
sin consolidar. C1 v2 suma tres estados: `paused`, `terminated` y `blocked`. Además, el hallazgo R-03 de
la revisión 1 señaló que desactivar a un analista dueño de sesiones pendientes las deja sin nadie que las
cierre, porque no hay traspaso de dueño.

A. «Pendiente» es toda sesión propia que no está `consolidated`, así que incluye `paused`, `terminated`
   y `blocked`. Solo bloquea el cambio de rol (`409`). Desactivar se permite siempre, porque es un
   control de seguridad: las sesiones pendientes quedan en solo lectura hasta que se reactive al
   usuario, y la confirmación de M6 lo advierte con su número. (Recomendada)
B. Igual que A, pero desactivar también se rechaza con `409` mientras el usuario tenga sesiones
   pendientes.
C. Solo son pendientes `open`, `paused`, `suspended` y `finalized`; `terminated` y `blocked` no
   bloquean el cambio de rol.
X. Other (please specify)

[Answer]: A **Mode:** guided
