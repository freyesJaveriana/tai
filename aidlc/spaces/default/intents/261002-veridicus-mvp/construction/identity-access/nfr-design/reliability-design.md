# Diseño de fiabilidad — U3 identity-access

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F1–F9 y §9 de
`functional-design/functional-spec.md` (functional-spec); C1, C12 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P2 de
`nfr-design-questions.md`.

## 1. Patrones elegidos

| Patrón | Dónde | Configuración | Requisito |
|---|---|---|---|
| *Timeout* | Toda consulta a PostgreSQL | `statement_timeout = 2 000 ms` por conexión y `connect_timeout = 2 s` | NFR10.11 |
| *Timeout* | Toda operación de Redis | `socket_timeout = 0,5 s`, `socket_connect_timeout = 0,5 s` | NFR10.11 |
| Falla cerrada | Inicio de sesión y rutas autenticadas | Error de base o de Redis → `503` `system.unavailable`, nunca `401` ni acceso | NFR10.12 |
| *Bulkhead* | Verificación de contraseñas | Semáforo de 2 con espera de 5 s (P2 = A) | NFR8.1 |
| Sin reintentos | Toda la unidad | Ninguna operación de U3 se reintenta sola: una petición fallida responde `503` y la consola ofrece reintentar | NFR10.12 |
| Concurrencia | Desactivar o cambiar el rol de un `admin` | `SELECT … FROM app_user WHERE role = 'admin' AND active FOR UPDATE` antes de contar | NFR10.15 |
| Idempotencia | `create-admin` | Transacción con bloqueo y salida 2 si ya hay un `admin` activo | NFR10.14 |

No se usa cortacircuitos: con una sola base y un solo Redis locales, un fallo responde en ≤ 2 s por el
*timeout* y no hay una ruta alternativa a la que desviar.

## 2. Comportamiento ante fallos

| Falla | Inicio de sesión | Ruta autenticada | `/readyz` |
|---|---|---|---|
| PostgreSQL no responde | `503` `system.unavailable` | `503` `system.unavailable` | `503` |
| Redis no responde | `503`: el limitador no puede comprobar, así que no deja pasar | Sin efecto (F2 no usa Redis) | `503` |
| Cola del semáforo llena 5 s | `503` con `Retry-After: 5` | Sin efecto | Sin efecto |
| Configuración inválida | El proceso no arranca | — | — |
| Redis pierde sus datos | Los contadores vuelven a cero | Sin efecto | — |

Los `503` usan el manejador único de Problem Details de `libs/` y escriben una línea `ERROR` con el tipo
de falla (observability-design §1).

## 3. Salud (C16, NFR10.13)

- `/healthz`: responde `200` si el proceso atiende; no toca dependencias.
- `/readyz`: ejecuta `SELECT 1` (≤ 1 s) y `PING` a Redis (≤ 0,5 s) y comprueba que la configuración de
  U3 se cargó; cualquier fallo → `503`. El resultado no se guarda en caché: la sonda de Kubernetes ya
  fija su propia frecuencia (U2).
- La configuración se valida con `pydantic-settings` antes de crear la aplicación (D2): duraciones,
  parámetros de Argon2id, `VERIDICUS_ARGON2_QUEUE_SECONDS`, proxy de confianza y clave HMAC de ≥ 32
  bytes. Un valor inválido termina el proceso con un log que nombra el ajuste.

## 4. Recuperación

- Las sesiones web viven en PostgreSQL: reiniciar el pod no cierra sesiones.
- Un despliegue nuevo no invalida sesiones; cambiar los parámetros de Argon2id re-calcula hashes en el
  siguiente inicio de sesión correcto (NFR10.1).
- El respaldo de la base es de CloudNativePG (Infrastructure Design).

## 5. Pruebas de fiabilidad (nivel 1)

| Prueba | Resultado esperado |
|---|---|
| Detener PostgreSQL durante el inicio de sesión y en `GET /auth/me` | `503` en ambos; ningún `401` ni acceso |
| Detener Redis durante el inicio de sesión | `503`; el inicio de sesión no pasa |
| E8: dos desactivaciones simultáneas del último par de `admin` | Una gana, la otra `409` `user.last_admin` |
| E10: `create-admin` dos veces | Segunda ejecución con código 2 y 0 filas nuevas |
| `/readyz` con configuración inválida o dependencias caídas | `503` |
