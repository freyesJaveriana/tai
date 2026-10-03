# Diseño de escalado — U3 identity-access

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F1–F9 de `functional-design/functional-spec.md`
(functional-spec); C1, C12, C15 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1–P2 de `nfr-design-questions.md`; prácticas de `team.md`.

## 1. Modelo de escalado

`session-api` escala solo en horizontal y de forma manual (réplicas por PR); el MVP corre **1 réplica**
(scalability-requirements §1: ≤ 50 usuarios, ≤ 20 sesiones web, ≤ 10 inicios simultáneos). U3 no
guarda estado en el proceso, así que añadir réplicas no cambia su comportamiento.

| Estado | Dónde vive | Por qué permite varias réplicas (NFR8.2) |
|---|---|---|
| Sesiones web y `last_seen_at` | PostgreSQL | Cualquier réplica resuelve la cookie |
| Contadores de intentos | Redis | Un contador por clave para todas las réplicas |
| Hash señuelo, mapa de rutas desde C1, configuración | Memoria de cada proceso | Se recalculan igual al arrancar; no son estado compartido |
| Semáforo de Argon2id | Memoria de cada proceso | Es un límite de memoria **por proceso** (NFR8.1); con N réplicas, N × 2 verificaciones |

Prueba de nivel 1 (NFR8.2): dos instancias de la aplicación en el mismo proceso de prueba, con la misma
base y el mismo Redis; la sesión creada en una se usa en la otra, y 5 fallos repartidos entre ambas
disparan el `429`.

## 2. Crecimiento de tablas (NFR8.3)

- Barrido diario dentro de `session-api`: una tarea que corre al arrancar y luego cada 24 h, protegida
  con `pg_try_advisory_lock(<constante de U3>)` para que, con varias réplicas, solo una lo ejecute.
- Borra por lotes de 500 filas de `web_session` donde `revoked_at` o la caducidad máxima tienen más de
  7 días, usando el índice de `expires_at`.
- `user_change` no se borra nunca (NFR11). Con ≤ 50 usuarios crece en decenas de filas.

## 3. Capacidad y señales

| Recurso | Uso esperado del MVP | Límite de diseño | Señal para actuar |
|---|---|---|---|
| Memoria por Argon2id | 2 × 64 MiB | ≤ 160 MiB extra (NFR8.1) | `503` por cola del semáforo en la prueba de carga |
| Conexiones a PostgreSQL | ≤ 10 por réplica (pool 5 + 5) | `max_connections` que fije Infrastructure Design | `pool_timeout` alcanzado en logs |
| Claves de Redis de U3 | ≤ 2 por intento fallido, caducan a los 900 s | Despreciable | — |

Si la prueba de carga de NFR8 muestra inicios de sesión en cola, se sube el semáforo o el
`limits.memory` por PR; no hay autoescalado.
