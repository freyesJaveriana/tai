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
