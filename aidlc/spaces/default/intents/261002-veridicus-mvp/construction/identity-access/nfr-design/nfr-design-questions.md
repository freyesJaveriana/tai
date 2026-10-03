# Preguntas de NFR Design — U3 identity-access

**Unidad.** U3 `identity-access` (tipo `service`): inicio y cierre de sesión, sesión web revocable,
anti-CSRF, roles y gestión de usuarios dentro de `session-api`.

**Lo que ya está decidido y no se vuelve a preguntar.** Argon2id `m = 65 536 KiB, t = 3, p = 1`,
política de contraseñas, sesión con inactividad de 1 800 s y máximo de 43 200 s sin caché de sesiones,
limitador de 5 fallos en 15 minutos con clave HMAC en Redis, falla cerrado con `503`
`system.unavailable`, semáforo de 2 verificaciones Argon2id por proceso, presupuestos NFR3.1–NFR3.3,
barrido diario de sesiones, métricas y logs (requisitos y decisiones D1–D12 de `nfr-requirements/`).
Solo quedan dos huecos de diseño.

---

## P1 — Cómo se registra la actividad de la sesión web para la caducidad por inactividad

Para caducar la sesión a los 1 800 s sin peticiones (NFR10.3) hay que guardar la hora de la última
petición autenticada. Escribirla en cada petición es una escritura en PostgreSQL por petición; con el
sondeo de la consola (cada pocos segundos por sesión abierta) eso suma muchas escrituras pequeñas.

A. Escribir `last_seen_at` en cada petición autenticada, con un `UPDATE` de una fila por clave
   primaria. Con ≤ 20 sesiones web a la vez el costo es pequeño y la caducidad es exacta al segundo,
   como piden las pruebas de 1 799 s y 1 801 s. (Recomendada)
B. Escribir `last_seen_at` solo si la última escritura tiene más de 60 s; la caducidad puede
   adelantarse hasta 60 s y las pruebas de NFR10.3 se ajustan a ese margen.
C. Guardar la última actividad en Redis con caducidad automática y la sesión en PostgreSQL.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué pasa cuando llegan más inicios de sesión que el semáforo de Argon2id

El semáforo deja como máximo 2 verificaciones de contraseña a la vez por proceso (NFR8.1). Con 10
inicios de sesión simultáneos, 8 esperan. Falta fijar cuánto esperan y qué reciben si no hay turno.

A. Esperan en cola hasta 5 s; si en ese tiempo no obtienen turno, reciben `503` `system.unavailable`
   con `Retry-After: 5` y la métrica de inicio de sesión cuenta `outcome="error"`. Con un p95 de 1 s
   por verificación, 10 simultáneos terminan sin error. (Recomendada)
B. Esperan sin límite hasta que haya turno (solo el *timeout* de la petición HTTP los corta).
C. No esperan: si el semáforo está lleno, reciben `503` de inmediato.
X. Other (please specify)

[Answer]: A **Mode:** guided
