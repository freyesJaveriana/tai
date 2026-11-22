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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Sin preguntas: todo lo fijan las fuentes.** Ninguna decisión de esta pasada enfrenta dos fuentes
aprobadas ni cambia el alcance, el riesgo aceptado o un dato que sale del clúster (regla de `project.md`
del 2026-11-22). Lo que se aplica sin preguntar queda en la tabla NFRD-U3-xx de `security-design.md`
§12 y se presenta en la aprobación.

## Lo que ya está decidido

- NFR Requirements de U3, revisión 2 (aprobado hoy): NFR10.1–NFR10.23, NFR11.1, NFR11.3–NFR11.5 (NFR11.2
  Retirado), NFR3.1–NFR3.4, NFR8.1–NFR8.4, NFR13.1, NFR14.1, NFR15.1–NFR15.3 y D1–D17, con la tabla
  NFR-U3-01 a NFR-U3-05.
- `last_seen_at` se escribe como máximo una vez cada 60 s (NFR10.3 revisión 2): supera P1 = A de la
  revisión 1 de esta etapa.
- P2 = A de la revisión 1 sigue: espera de 5 s del semáforo, ahora con el nombre
  `VERIDICUS_ARGON2_QUEUE_TIMEOUT_S` de `tech-stack-decisions.md` §2 y el `503` de NFR8.4.
- `Retry-After: 900` fijo en el `429` (NFR10.5 revisión 2), `ttlSecondsAfterFinished: 3600` en
  `create-admin` (NFR10.8) y `/readyz` en `503` si PostgreSQL o Redis no responden (NFR10.13).
- U1 (NFR Design revisión 2): C25 v1 con `web_session_max_s`, `web_session_idle_s`, `username_max_chars`
  y `password_max_chars`; lista cerrada de extensiones `x-veridicus-*`; `x-veridicus-roles` en toda
  operación salvo `/auth/login`, `/auth/logout`, `/auth/me` y la lista pública (NFRD-U1-12);
  `limits.exceeded` siempre `413`.
- Lo que piden otras unidades: `audio-worker` en `ActorSystem` (NFR-U9-06); punto de guardado de 500 ms
  para `observation-views` (U5) y lectura de reportes (U7); exportación con su propia llamada a
  `AccessLog` y reversión completa (NFR-U7-09); Ingress sin escritura en disco (NFR-U6-06, NFR-U7-07,
  NFR-U12-05); tres usuarios de base de datos con su Secret (NFR-U2-08).

## Cómo se registra la revisión 2

- Los seis documentos y `traceability.json` se reescriben como revisión 2; la revisión 1 queda en el
  historial de Git.
- Los patrones conservan su sección; cada documento dice qué **se mantiene**, qué **cambia** y qué es
  **nuevo**. Lo que cubría NFR11.2 queda «Retirado».
- Se cierran los hallazgos R-01 a R-08 de `reviews/review-01.md` en las secciones que los citan.

## Lo que el diseño resolverá sin preguntar

- Orden de bloqueo con la escritura de actividad: usuario → `WebSession` → sesión → ronda (NFRD-U3-01).
- Token anti-CSRF derivado del token de sesión, para que la base guarde solo su hash y `GET /auth/me`
  pueda devolverlo (NFRD-U3-03).
- Limitador con reserva atómica en Lua antes de verificar (cierra R-03 y R-05).
- Inicio de sesión en dos transacciones cortas, sin conexión retenida mientras espera el semáforo
  (cierra R-07 c).
- Clase de ruta propia que autoriza, valida, delega, registra el acceso y confirma antes de responder.
- Marca `veridicus-audit` como única fuente de los permisos, con un `DOMAIN` para `ActorSystem`.
- Consecuencia de `/readyz` con Redis caído y una réplica: toda la consola queda sin servicio (cierra
  R-01, documentado en `reliability-design.md` y `logical-components.md`).
