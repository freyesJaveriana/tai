# Diseño de escalabilidad — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo.

**Insumos.** `nfr-requirements/scalability-requirements.md` (scalability-requirements: §1, NFR3.9–NFR3.12 y
§3) y `performance-requirements.md` (performance-requirements, NFR3.6 y NFR3.7) de esta unidad; BR2.4,
BR3.5, BR5.2, BR5.7 y BR7.1 de `functional-design/functional-spec.md` (functional-spec); C1, C24 y C25 de
`inception/contract-design/contract-summary.md` (contract-summary); índices de U4 (NFRD-U4-11), pool de la
API de U3 y forma del `Job` de U2 (§13).

## 1. Forma del despliegue

- U13 no tiene proceso propio en marcha: vive en la API de `session-api`, con **1 réplica** en el MVP (una
  máquina, un analista en la sustentación, ≤ 500 sesiones en la base). No hay autoescalado.
- La API no guarda estado de U13 entre peticiones: el texto de las reglas es inmutable y se carga al
  arrancar; el estado del reconocimiento se calcula en cada `/auth/me`. Con más réplicas, todas darían lo
  mismo.
- El `Job` es un proceso aparte que vive minutos y lanza el humano. El bloqueo consultivo de PostgreSQL
  garantiza una ejecución a la vez aunque se lancen dos (NFR10.19), sin depender del número de réplicas.

## 2. Topes que acotan el trabajo

| Cifra | Valor | De dónde | Qué acota |
|---|---|---|---|
| `ethics_body_max_bytes` | 32 768 | C25 (NFR-U13-01) | Bytes por petición de las tres rutas |
| `problem_report_note_max_chars` | 2 000 | C25 | Secuencias de la nota (≤ 1 000) y tamaño de la fila |
| `testimony_warning_words` | 8 | C25 | Ventana de la comparación |
| `transcript_max_turns` y `transcript_max_chars` | 2 000 y 250 000 | C25 (U4) | Turnos que recorre la comparación y que borra el `Job` |
| `retention_max_days` / `retention_min_days` | 90 / 1 | C25 | Cuánto vive una sesión; sin rebaja por proceso (NFRD-U13-10) |
| `--limit` del comando | 1 000 por defecto, 10 000 como máximo | Argumentos (NFR-U13-09) | Filas por consulta |
| `VERIDICUS_RETENTION_SESSION_TIMEOUT_S` | 60 | Entorno del `Job` (tech-stack-decisions §2) | Duración de una sesión en el `Job` |

Las cifras de C25 se leen con `limits.load` y el entorno solo puede bajarlas (NFRD-U1-09), salvo
`retention_max_days`, que ningún manifiesto baja (NFRD-U13-10).

## 3. Crecimiento de las tablas (NFR3.9)

| Tabla | Crece con | Se borra | Estimación con 500 sesiones típicas |
|---|---|---|---|
| `access_log_entry` | Cada apertura de sesión, sugerencia o versión y cada exportación (no el sondeo) | Nunca (VE-11) | 150 000 filas, ≤ 40 MiB con sus cuatro índices |
| `retention_act` | Una por sesión borrada y una por tanda de reportes sin sesión | Nunca (A-2) | ≤ 1 MiB por acta de la sesión máxima; ≤ 100 MiB con 500 |
| `analyst_acknowledgement` | Un reconocimiento cada ≤ 90 días por analista | Nunca | Despreciable |
| `problem_report` y `retention_change` | Uso de la consola | Con su sesión o por antigüedad | ≤ 10 MiB junto con la anterior |

- Filas estrechas: UUID, enums, enteros, hora y, en `problem_report`, la nota de ≤ 2 000 caracteres. El acta
  usa `jsonb` de tipos cerrados.
- Prueba de nivel 1: `pg_total_relation_size` antes y después de sembrar las filas de NFR3.9.
  Infrastructure Design suma las tablas que no se borran al volumen de PostgreSQL
  (`logical-components.md` §5).

## 4. Índices (NFR3.10)

| Tabla | Índices | Los usa |
|---|---|---|
| `analyst_acknowledgement` | `(actor_user_id, at DESC)` | Estado de `/auth/me` |
| `access_log_entry` | `(resource_id, at)`, `(actor_user_id, at)`, `(at DESC)` | Comando de consulta |
| `problem_report` | `(session_id)`, `(suggestion_id)`, `(reported_at) WHERE session_id IS NULL`, `(reported_at DESC)` | Borrado por sesión, reportes sin sesión, comando |
| `retention_change` | `(session_id)` | Borrado por sesión |
| `retention_act` | `(deleted_session_id)`, `(job_run_id)`, `(executed_at DESC)` | Comando |
| `interview_session` (U4) | `(retention_until)`, `(created_at) WHERE retention_until IS NULL` | `expired_sessions` (NFRD-U4-11) |

Los índices por hora `(at DESC)`, `(reported_at DESC)` y `(executed_at DESC)` son nuevos (NFRD-U13-12).
Prueba de nivel 1 con las filas de NFR3.9: `pg_indexes` contiene la lista y `EXPLAIN` del estado de
`/auth/me`, de `expired_sessions`, de la selección de reportes sin sesión, del borrado de BR5.5 y de cada
consulta del comando no hace `Seq Scan` sobre esas tablas.

## 5. Volumen del `Job` (NFR3.11)

- Sin tope por ejecución: con ≤ 500 sesiones, el peor caso es que venzan todas a la vez.
- Una transacción por sesión: la duración crece de forma lineal y una ejecución larga no retiene bloqueos
  más allá de la sesión en curso.
- Si vence `activeDeadlineSeconds`, la siguiente ejecución sigue donde quedó (NFR10.20). El valor se ajusta
  por PR a 2 × la medición de 500 sesiones típicas (NFR-U13-07, U2 §13).

## 6. Concurrencia (NFR3.12)

| Caso | Diseño | Resultado esperado |
|---|---|---|
| Dos `POST /problem-reports` de la misma sesión | Inserciones independientes; ninguna bloquea la sesión | Dos `201`, 2 filas |
| Dos `PATCH` que reducen la misma sesión de 30 a 10 | `change_cursor.bump` serializa; la segunda lee 10 bajo el bloqueo | Un `200` y un `422` `retention.cannot_extend`; 1 `retention_change` |
| Dos `Job` | Bloqueo consultivo | Uno 0 y otro 3 |
| `Job` en curso y sondeo de U4 | El `Job` bloquea solo la sesión vencida que borra; el sondeo de U4 lee en `REPEATABLE READ` sin bloqueos de fila (NFRD-U4-05) | El p95 de `GET /sessions/{id}?since=` sube ≤ 200 ms |
| `Job` y una escritura de la API sobre la misma sesión | La API espera el bloqueo de la sesión | `503` tras 2 s o el «no existe» tras el `COMMIT` |

Pruebas de nivel 1 con barrera, 20 repeticiones sin fallos.

## 7. Conexiones

- Las rutas usan el pool de la API de U3: una conexión por petición, por milisegundos.
- El `Job` abre **una** conexión de `veridicus_retention` y un cliente de Redis; el comando usa una conexión
  de `veridicus_app` dentro del contenedor de la API, fuera de su pool. Ninguno compite con el pool de la
  API por más de una conexión.

## 8. Qué se degrada primero

| Señal | Qué pasa | Qué se hace |
|---|---|---|
| `access_log_entry` pasa de 1 000 000 de filas | El comando tarda más que NFR3.7 | Política de archivo del registro por PR; no se borra sin cambiar VE-11 |
| Muchas sesiones vencen a la vez | El `Job` tarda más que `activeDeadlineSeconds` | Se relanza; el plazo se ajusta por PR con la medición |
| Nota legítima de más de 2 000 caracteres | `413` `limits.exceeded` | Se sube la cifra por PR de U1 tras medir NFR3.1 |
| Acta de la sesión máxima > 1 MiB | NFR3.9 en rojo | Formato binario de los UUID dentro de la lista, por PR |
