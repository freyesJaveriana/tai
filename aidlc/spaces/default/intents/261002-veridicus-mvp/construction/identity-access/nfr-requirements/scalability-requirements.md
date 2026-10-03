# Requisitos de escalado — U3 identity-access

**Insumos.** Flujos de `functional-design/functional-spec.md` (functional-spec) y reglas de
`functional-design/rules.md` (rules); NFR8 y los supuestos de
`inception/requirements-analysis/requirements.md` (requirements); C1 y C12 de
`inception/contract-design/contract-summary.md` (contract-summary).

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Usuarios registrados | ≤ 50 | Supuesto del MVP académico (un analista en la sustentación) |
| Sesiones web activas a la vez | ≤ 20 | Holgura sobre las 3 sesiones concurrentes de NFR8 |
| Inicios de sesión simultáneos | ≤ 10 | Mismo supuesto |

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.2 | U3 no impide correr más de una réplica de `session-api`. | Sesiones web en PostgreSQL y contadores de intentos en Redis, nada en memoria del proceso: una prueba de nivel 1 crea la sesión en una instancia de la aplicación y la usa en otra. El MVP corre 1 réplica. |
| NFR8.3 | Las tablas de U3 no crecen sin límite. | Un barrido diario (tarea del propio `session-api`) borra de `WebSession` las filas vencidas o revocadas hace más de 7 días; `UserChange` no se borra nunca (NFR11). |

## 3. Señal para escalar

Si una prueba de carga de NFR8 muestra inicios de sesión en cola por el semáforo de NFR8.1, se sube el
semáforo o el `limits.memory` por PR; no hay autoescalado para U3.
