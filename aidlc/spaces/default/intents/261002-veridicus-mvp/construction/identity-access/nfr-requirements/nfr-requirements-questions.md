# Preguntas de NFR Requirements — U3 identity-access

**Unidad.** U3 `identity-access` (tipo `service`): inicio de sesión, sesión web, matriz de roles en
ConsoleApi, gestión de usuarios y primer `admin` (`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Usuario y contraseña locales con hash
adaptativo con sal (FR1.1); mismo `401` para los tres fallos con hash señuelo (BR1.2); cookie
`HttpOnly`, `Secure`, `SameSite=Strict` revocable y token anti-CSRF (C1, P5 de Contract Design);
desactivar revoca sesiones (BR2.4); historiales solo de inserción (BR6.1–BR6.2); logs solo con
identificadores (NFR10). `requirements.md` dejó para esta etapa la política de contraseñas y la
duración de la sesión web; esas son las preguntas de abajo, más dos huecos de seguridad.

---

## P1 — Algoritmo de hash de contraseñas y su costo

FR1.1 exige un hash adaptativo con sal, pero no cuál. Su costo fija cuánto tarda cada inicio de sesión
en la CPU de la máquina de desarrollo y cuánto cuesta a un atacante probar contraseñas si roba la base.

A. Argon2id (`argon2-cffi`) con 64 MiB de memoria, 3 iteraciones y 1 hilo: unos 0,3–0,5 s por
   verificación en CPU; los parámetros quedan dentro del hash para poder subirlos después. (Recomendada)
B. bcrypt con costo 12 (unos 0,25 s); limita las contraseñas a 72 bytes.
C. scrypt (N = 2^15, r = 8, p = 1).
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Política de contraseñas

Las contraseñas las fija el `admin` al crear un usuario y el comando `create-admin` desde un Secret.
Hay que decidir qué contraseñas se rechazan, con un `422` y un mensaje en español.

A. Mínimo 12 y máximo 128 caracteres, sin reglas de composición, y rechazo de las contraseñas de una
   lista de contraseñas comunes guardada en el repositorio (sin consultas a internet). (Recomendada)
B. Mínimo 8 caracteres con mayúscula, minúscula, número y símbolo.
C. Mínimo 15 caracteres, sin lista de contraseñas comunes.
X. Other (please specify)

[Answer]: X. Other: «8 con composición y lista común» — mínimo 8 caracteres con mayúscula, minúscula, número y símbolo, y además rechazo de la lista de contraseñas comunes **Mode:** guided

## P3 — Duración de la sesión web

La sesión web (`WebSession.expires_at`) caduca y entonces la consola vuelve a M0 y, al entrar, a la
misma ruta (BR1.7). La consola sondea mientras está abierta, así que cada sondeo cuenta como actividad.

A. Caduca tras 30 minutos sin peticiones autenticadas y, en todo caso, 12 horas después del inicio de
   sesión. (Recomendada)
B. 15 minutos sin actividad y 8 horas como máximo.
C. Solo un máximo fijo de 8 horas, sin caducidad por inactividad.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Límite de intentos fallidos de inicio de sesión

Nada limita hoy cuántas contraseñas puede probar alguien desde la consola. Un bloqueo que respondiera
distinto según el usuario exista o no rompería BR1.2.

A. Por usuario normalizado y por dirección de origen: tras 5 fallos en 15 minutos, `429` con un `code`
   nuevo `auth.too_many_attempts` durante 15 minutos, igual exista o no el usuario; el contador vive en
   Redis y caduca solo. (Recomendada)
B. Sin límite: el clúster es local y hay un solo analista.
C. Retardo creciente (1 s, 2 s, 4 s… hasta 30 s) por usuario, sin bloqueo.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Sin preguntas: todo lo fijan las fuentes.** Ninguna decisión de esta pasada enfrenta dos fuentes
aprobadas ni cambia el alcance, el riesgo aceptado o un dato que sale del clúster (regla de `project.md`
del 2026-11-22). Lo que se aplica sin preguntar queda en la tabla NFR-U3-xx de
`security-requirements.md` §7 y se presenta en la aprobación.

## Lo que ya está decidido

- Las respuestas P1–P4 de la revisión 1 siguen: Argon2id, política «8 con composición y lista común»,
  30 minutos de inactividad y 12 horas en total, y 5 fallos en 15 minutos por usuario y por origen.
- El Functional Design de U3, revisión 2 (aprobado hoy), fija tres roles con el `investigador`, la
  negación por defecto, `x-veridicus-owner-only-for-role`, el manejador único de Problem Details
  (BR8.1–BR8.4), el registro de acceso por marca (BR9.1–BR9.5), la convención de auditoría con actor
  nunca nulo y los dos usuarios de base de datos (BR6.1–BR6.6), y la configuración solo por PR
  (BR5.1–BR5.3).
- El NFR de U1, revisión 2: `limits.exceeded` responde siempre `413` (P7 = A), el catálogo C25 no admite
  nulos y todo tope de un cuerpo de C1 lleva el nombre de su cifra de C25 (NFR10.7 y NFR10.14 de U1).
- `project.md`: toda cifra de límite de sesión vive en C25; `VERIDICUS_TRUSTED_PROXY` toma el pod CIDR.

## Cómo se registra la revisión 2

- Los requisitos conservan su ID y cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
- NFR11.1 queda **precisado** por BR6.1 y NFR11.2 queda **Retirado** (el umbral salió con el cambio 01),
  tal como pide FD-U3-12. Lo nuevo toma el número siguiente de su grupo.
- Se cierran los hallazgos R-01 a R-06 de `reviews/review-01.md`.

## Lo que el diseño resolverá sin preguntar

- Cifras de C25 de U3: `web_session_max_s` = 43 200 s; entran `web_session_idle_s` = 1 800 s,
  `username_max_chars` = 32 y `password_max_chars` = 128 (NFR-U3-01).
- Plazo del registro de una lectura en `AccessLog.record`: 500 ms, en un punto de guardado, sin revertir
  el manejador (responde a la pregunta 3 de U13; la exportación la decide U7).
- Las métricas de U3 son internas de `session-api` y no van a C15 (cierra R-05).
- Clases de caracteres y fuente de la lista de contraseñas comunes (cierra R-04).
- El bloqueo inducido por el limitador queda como riesgo aceptado con su espera de 15 minutos (cierra
  R-02); el proxy de confianza se fija al pod CIDR.
- `ttlSecondsAfterFinished` de `create-admin` y el barrido de sesiones web con una sola réplica activa
  por bloqueo asesor (cierra R-06).
