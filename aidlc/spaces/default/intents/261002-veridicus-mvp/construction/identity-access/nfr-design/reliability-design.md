# Diseño de fiabilidad — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y NFR Requirements revisión 2
de U3.** Sustituye a la revisión 1 del 2026-10-03.
- **Se mantienen:** *timeouts*, falla cerrada, sin reintentos y sin cortacircuitos.
- **Cambian:** la tabla de fallos dice la verdad sobre Redis con una réplica (cierra R-01); `/readyz`
  informa los puertos; `create-admin` usa el bloqueo asesor.
- **Nuevos:** el registro de acceso que nunca rompe la respuesta (NFR10.21) y el semáforo acotado
  (NFR8.4).

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad, revisión 2; flujos F1–F13 y §9 de
`functional-design/functional-spec.md` (functional-spec); C1, C12, C16 y C23 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P2 de
`nfr-design-questions.md`; NFR-U7-09 y NFR-U13-05.

## 1. Patrones elegidos

| Patrón | Dónde | Configuración | Requisito |
|---|---|---|---|
| *Timeout* | Toda consulta a PostgreSQL | `statement_timeout` = `VERIDICUS_DB_STATEMENT_TIMEOUT_MS` (2 000) por conexión; `connect_timeout = 2 s` | NFR10.11 |
| *Timeout* | Toda operación de Redis | `socket_timeout` y `socket_connect_timeout` = `VERIDICUS_REDIS_TIMEOUT_MS` (500) | NFR10.11 |
| *Timeout* | `AccessLog.record` | 500 ms en un punto de guardado (`security-design.md` §2.4) | NFR10.21 |
| Falla cerrada | Inicio de sesión y rutas autenticadas | Base o Redis caídos → `503` `system.unavailable`, nunca `401` ni acceso | NFR10.12 |
| Degradación aceptada | Registro de una lectura | Si falla, la respuesta sale con su 2xx; `WARNING` y métrica | NFR10.21 |
| *Bulkhead* | Verificación de contraseñas | Semáforo de 2, espera de 5 s, sin conexión retenida | NFR8.1, NFR8.4 |
| Sin reintentos | Toda la unidad | Ninguna operación se reintenta sola; la consola ofrece reintentar | NFR10.12 |
| Concurrencia | `PATCH /users`, `create-admin`, rutas que cambian estado | Bloqueos de `security-design.md` §5.4 y bloqueo asesor del conjunto de admins | NFR10.14, NFR10.15 |

Sin cortacircuitos: con una base y un Redis locales, un fallo responde en ≤ 2 s por el *timeout* y no
hay ruta alternativa a la que desviar.

## 2. Comportamiento ante fallos

| Falla | Inicio de sesión | Ruta autenticada | `/readyz` | Efecto en la consola |
|---|---|---|---|---|
| PostgreSQL no responde | `503` | `503` | `503` | Toda la consola sin servicio |
| Redis no responde | `503`: `reserve` no puede comprobar | Mientras el pod siga en el Service, funciona (F2 no usa Redis) | `503` | **Toda la consola sin servicio** tras el umbral de la sonda: con 1 réplica, Kubernetes saca el único pod del Service y el Ingress responde `503` (cierra R-01) |
| Cola del semáforo llena 5 s | `503` con `Retry-After: 5` | Sin efecto | Sin efecto | Solo los inicios en exceso |
| `AccessLog` falla o vence | — | 2xx con las escrituras del manejador; `WARNING` y métrica | Sin efecto | Ninguno visible |
| `COMMIT` falla | `503` | `503`; la respuesta no se envía antes del `COMMIT` | — | Reintentar |
| Configuración inválida | El proceso no arranca | — | — | El pod no queda listo |
| Redis pierde sus datos | Contadores a cero | Sin efecto | — | Ninguno |

**Por qué `/readyz` sigue dependiendo de Redis.** Lo fija NFR10.13 revisión 2, y con Redis caído tampoco
funcionan las colas de U4, U6 y U9 ni el limitador: una consola «lista» solo serviría lecturas. La
consecuencia, que la revisión 1 ocultaba, es que con una réplica la caída de Redis equivale a la caída de
toda la consola. `/healthz` no depende de Redis, así que el pod no entra en un ciclo de reinicios y
vuelve solo cuando Redis responde. Más réplicas no cambian esto, porque todas comparten Redis.

## 3. Salud (C16, NFR10.13)

- `/healthz`: `200` si el proceso atiende; no toca dependencias.
- `/readyz`: `SELECT 1` (≤ 1 s) y `PING` (≤ 0,5 s); cualquier fallo → `503`. Cuerpo:
  `{ status, postgres, redis, access_log: real | not_configured, pending_sessions: real | default }`.
  Con los adaptadores por defecto responde `200` (BR9.5, E38). Sin caché: la frecuencia la fija la sonda
  de U2.
- El proceso no arranca con las comprobaciones de `security-design.md` §3.1; un valor inválido termina
  el proceso con un log que nombra el ajuste, nunca su valor.

## 4. `create-admin` y concurrencia (NFR10.14, NFR10.15)

| Caso | Diseño | Prueba de nivel 1 |
|---|---|---|
| Segunda ejecución con un `admin` activo | Bloqueo asesor, conteo, código 2, 0 filas | E10 |
| Dos ejecuciones simultáneas sin `admin` | El bloqueo asesor las serializa; la segunda ve el `admin` recién confirmado y sale con código 2 | E26 |
| Dos desactivaciones del último par | Cada `PATCH` bloquea su objetivo y luego el bloqueo asesor; el segundo cuenta tras el `COMMIT` del primero → `409` `user.last_admin` | E8 |
| Último `admin` a otro rol | Misma guardia → `409` | E43 |
| Cambio de rol frente a creación de sesión | `FOR SHARE` frente a `FOR NO KEY UPDATE` sobre la fila del usuario | E25, en los dos órdenes |
| Interbloqueos | Orden único usuario → `WebSession` → sesión → ronda | Las pruebas anteriores con `lock_timeout = 5 s`: ninguna lo alcanza |

## 5. Recuperación

- Las sesiones web viven en PostgreSQL: reiniciar el pod no cierra sesiones.
- Si Redis pierde sus datos, solo se pierden los contadores del limitador.
- El barrido de sesiones web es idempotente (scalability-design §2).
- Un `PATCH` que falla a mitad no deja nada aplicado (NFR11.5).
- Cambiar los parámetros de Argon2id recalcula los hashes en el siguiente inicio de sesión correcto.
- El respaldo de la base es de CloudNativePG (Infrastructure Design).

## 6. Pruebas de fiabilidad (nivel 1)

| Prueba | Resultado esperado |
|---|---|
| Detener PostgreSQL durante el inicio de sesión y durante `GET /auth/me` (E32) | `503` en ambos; ningún `401` ni acceso |
| Detener Redis durante el inicio de sesión, y antes de `succeed` | `503`; el inicio no pasa y no queda `WebSession` |
| Detener Redis con una sesión abierta | `GET /auth/me` responde; `/readyz` responde `503` |
| Doble de `AccessLog` que falla, que tarda 600 ms y que funciona (E36) | `200` con las escrituras del manejador en los tres; en los dos primeros, `WARNING` y la métrica sube 1 |
| Rechazo `401`, `403`, `404` o `422` en una ruta marcada | 0 llamadas al puerto |
| `COMMIT` que falla con un doble de la base | `503`; el cliente no recibe el 2xx |
| Arranque sin adaptadores reales (E38) | `/readyz` `200` con `access_log: not_configured` y `pending_sessions: default` |
| E8, E10, E25, E26, E43 | Tabla de §4 |
