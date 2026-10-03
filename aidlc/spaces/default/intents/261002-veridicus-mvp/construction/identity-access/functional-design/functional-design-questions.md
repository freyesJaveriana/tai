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
