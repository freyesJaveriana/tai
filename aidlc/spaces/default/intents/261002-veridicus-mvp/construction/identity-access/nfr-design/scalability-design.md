# Diseño de escalado — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y NFR Requirements revisión 2
de U3.** Sustituye a la revisión 1 del 2026-10-03.
- **Se mantienen:** escalado horizontal manual con 1 réplica en el MVP y estado fuera del proceso.
- **Cambian:** el barrido usa lotes de 1 000 con `pg_try_advisory_xact_lock` por lote (NFR8.3 revisión
  2) y cubre las sesiones vencidas por inactividad.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1 y D17) de esta unidad, revisión 2; flujos F2, F5 y F13 de
`functional-design/functional-spec.md` (functional-spec) y `entities.md` (WebSession); C1 y C12 de
`inception/contract-design/contract-summary.md` (contract-summary); prácticas de `team.md`.

## 1. Modelo de escalado (NFR8.2)

`session-api` escala solo en horizontal y por PR; el MVP corre **1 réplica** (≤ 50 usuarios, ≤ 20
sesiones web, ≤ 10 inicios simultáneos).

| Estado | Dónde vive | Por qué permite varias réplicas |
|---|---|---|
| Sesiones web y `last_seen_at` | PostgreSQL | Cualquier réplica resuelve la cookie |
| Contadores del limitador | Redis, scripts Lua atómicos | Un contador por clave para todas las réplicas |
| Hash señuelo, `RouteSecurity`, validadores compilados, configuración, catálogo de mensajes | Memoria de cada proceso | Se construyen igual al arrancar desde el mismo contrato; no son estado compartido |
| Semáforo de Argon2id | Memoria de cada proceso | Límite de memoria **por proceso** (NFR8.1): con N réplicas, N × 2 verificaciones |

Prueba de nivel 1: dos instancias de la aplicación en el mismo proceso de prueba, con la misma base y el
mismo Redis; la sesión creada en una se usa en la otra, y 5 fallos repartidos entre ambas disparan el
`429`.

## 2. Crecimiento de `WebSession` (NFR8.3, D17)

- Tarea de `session-api` en un hilo propio, al arrancar y luego cada 24 h; la antigüedad de purga es
  `VERIDICUS_WEB_SESSION_PURGE_DAYS` (7).
- Cada lote es una transacción con `veridicus_app` (único `DELETE` de la aplicación, NFR-U3-02):
  1. `pg_try_advisory_xact_lock(<clave del barrido de U3>)`; si otra réplica lo tiene, se detiene;
  2. `DELETE` de hasta 1 000 filas por clave primaria, elegidas con `FOR UPDATE SKIP LOCKED`, cuya
     revocación, `expires_at` o `last_seen_at + web_session_idle_s` tienen más de 7 días según `:now` del
     reloj inyectable;
  3. si borró 1 000, sigue con otro lote; si no, termina.
- Idempotente: si se interrumpe, el siguiente borra lo que faltó. `UserChange` no se borra nunca.
- Pruebas de nivel 1: vencida hace 8 días se borra, hace 6 no, válida no, vencida por inactividad hace 8
  días se borra; dos barridos simultáneos borran una vez sin error; 2 500 filas vencidas → tres lotes.

## 3. Capacidad y señales

| Recurso | Uso esperado del MVP | Límite de diseño | Señal para actuar |
|---|---|---|---|
| Memoria por Argon2id | 2 × 64 MiB | ≤ 160 MiB extra (NFR8.1), medido por la prueba de `performance-design.md` §4 | `503` del semáforo (NFR8.4) en la prueba de carga de NFR8 de U4 |
| Conexiones a PostgreSQL | ≤ 10 por réplica (*pool* 5 + 5) | `max_connections` que fije Infrastructure Design | `system.unavailable` por `pool_timeout` en los logs |
| Claves de Redis de U3 | ≤ 2 por origen y usuario con intentos, caducan a los 900 s | Despreciable | — |
| Filas de `WebSession` | Decenas por día | Purga a los 7 días | — |

La señal de escalado se lee en la prueba de carga de NFR8 que hace U4 (D11): si hay `503` de NFR8.4,
se sube `VERIDICUS_ARGON2_MAX_CONCURRENT` o el `limits.memory` por PR; no hay autoescalado. El bloqueo
compartido del usuario (BR2.12) no crea contención entre peticiones del mismo usuario; solo el `PATCH` lo
toma exclusivo.
