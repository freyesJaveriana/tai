# Requisitos de escalado — U3 identity-access

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design vigente
de U3.** Sustituye a la revisión 1 del 2026-10-03. Los requisitos conservan su ID; cada fila dice si **se
mantiene** o **cambia**. Ninguno entra ni se retira.

**Insumos.** Flujos F2, F5 y F13 de `functional-design/functional-spec.md` (functional-spec, revisión 2)
y reglas BR2.12 y BR6.5 de `functional-design/rules.md` (rules), con `entities.md` (WebSession); NFR8 y
los supuestos de `inception/requirements-analysis/requirements.md` (requirements, revisión 3); C1 y C12
de `inception/contract-design/contract-summary.md` (contract-summary).

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Usuarios registrados | ≤ 50 (tres roles) | Supuesto del MVP académico (un analista en la sustentación) |
| Sesiones web activas a la vez | ≤ 20 | Holgura sobre las 3 sesiones concurrentes de NFR8 |
| Inicios de sesión simultáneos | ≤ 10 | Mismo supuesto |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.2 | se mantiene | U3 no impide correr más de una réplica de `session-api`. | Sesiones web en PostgreSQL y contadores en Redis, nada en memoria del proceso salvo el semáforo de NFR8.1: una prueba de nivel 1 crea la sesión en una instancia de la aplicación y la usa en otra. El MVP corre 1 réplica. |
| NFR8.3 | cambia | `WebSession` no crece sin límite, y el barrido nunca corre dos veces a la vez (cierra R-06). | Un barrido de `session-api`, al arrancar y luego cada 24 h, borra con `veridicus_app` las filas de `WebSession` vencidas o revocadas hace más de 7 días, en lotes de hasta 1 000 filas por transacción. Antes toma `pg_try_advisory_xact_lock` con una clave fija: si otra réplica lo tiene, no barre. Es idempotente. `UserChange` no se borra nunca (NFR11.1, NFR11.3). Pruebas de nivel 1: fila de 8 días vencida se borra, de 6 días no, válida no; dos barridos simultáneos borran una sola vez sin error. |

## 3. Señal para escalar

Si una prueba de carga de NFR8 muestra inicios de sesión en espera por el semáforo de NFR8.1 (respuestas
`503` de NFR8.4), se sube el semáforo o el `limits.memory` por PR; no hay autoescalado para U3. El bloqueo
compartido de la fila del usuario (BR2.12) no crea contención entre peticiones del mismo usuario; solo el
`PATCH` de usuario lo toma exclusivo.
