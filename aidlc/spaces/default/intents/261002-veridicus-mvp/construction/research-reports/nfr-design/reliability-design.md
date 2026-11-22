# Diseño de fiabilidad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo. Las precisiones están en la tabla NFRD-U12-xx de
`security-design.md` §14.

**Insumos.** `nfr-requirements/reliability-requirements.md` (reliability-requirements: NFR10.11,
NFR10.14–NFR10.16, NFR11.4, NFR11.6, §2 y §4) y `tech-stack-decisions.md` (tech-stack-decisions, D4 y D5)
de esta unidad; F1, F5, §9 y E7, E8, E37 de `functional-design/functional-spec.md` (functional-spec); C1,
C12, C16 y C25 de `inception/contract-design/contract-summary.md` (contract-summary); manejador único y
arranque de U3; respaldos de U2 (NFRD-U2-13).

U12 no tiene objetivo de disponibilidad propio: está disponible cuando lo están `session-api` y PostgreSQL.
Lo que fija este documento es cómo falla: sin filas a medias, sin reintentos ocultos, sin conexiones
retenidas y sin arrancar con un catálogo roto.

## 1. Plazos (NFR10.14; NFRD-U12-02, NFRD-U12-07)

| Operación | Plazo | Dónde se fija | Al vencer |
|---|---|---|---|
| T1 de `GuardedRoute` | `statement_timeout` 2 s y `lock_timeout` 2 s | Conexión del pool (U3, U5) | `503` `system.unavailable`, `cause: db` |
| Espera de un hueco de subida | 5 s | `UPLOAD_SLOT_WAIT_S` | `503`, `cause: upload_slots`, `Retry-After: 10` |
| Lectura del cuerpo | `research_report_read_timeout_s` (30 s) en total, con `anyio.fail_after` | `limits.load` (C25) | `503`, `cause: upload_read_timeout`, 0 filas |
| T2 (duplicado) | `statement_timeout` 2 s | Conexión del pool | `503`, `cause: db` |
| T3 (escritura) | `SET LOCAL statement_timeout` = `research_report_write_timeout_s` (15 s) y `lock_timeout` 2 s en el `FOR SHARE` del usuario | `limits.load` (C25) | *Rollback*, `503`, `cause: db`, 0 filas |
| Lecturas (lista, detalle, comparación) | `statement_timeout` 2 s por sentencia | Conexión del pool | `503`, `cause: db` |

- T3 no deja huecos sin sentencias: las filas ya están armadas al abrirla, así que el plazo de inactividad
  de la base (5 s o 15 s, según U6 o U7) nunca corta una escritura legítima.
- El plazo de lectura es total, no por trozo: un cliente que manda un byte cada pocos segundos también
  vence.

## 2. Atomicidad (NFR11.4)

- La fila y sus tablas hijas se escriben en T3 y solo en T3. Las validaciones terminan antes de abrirla
  (BR2.1), así que un rechazo nunca deja filas.
- Ante cualquier excepción dentro de T3, el manejador único de U3 revierte antes de responder (§3.3 de U3).
- **Commit de resultado desconocido.** Si el `COMMIT` falla por conexión cortada, el servidor pudo haberlo
  aplicado. U12 no tiene nada fuera de la base que limpiar (no escribe archivos), así que responde `503`;
  el investigador vuelve a subir y recibe `201` (no se guardó) o `409` (sí se guardó). Nunca quedan dos
  filas.
- Pruebas de nivel 1: fallo inyectado tras la primera tabla hija (excepción del adaptador) y corte de la
  conexión a mitad de T3: `503` y 0 filas en las cuatro tablas; espera inyectada de 16 s: `503` y 0 filas.

## 3. Duplicados y concurrencia (NFR11.6, BR2.8)

- T2 da el `409` rápido. La garantía la da el índice único de `source_sha256` en T3: la
  `UniqueViolation` de psycopg (`23505`) sobre ese índice, y solo sobre él, se traduce a `409`
  `research.duplicate`; cualquier otra violación de integridad es `500`.
- Prueba de nivel 1 repetida 20 veces: dos subidas del mismo archivo sincronizadas con una barrera después
  de T2; una `201`, otra `409`, exactamente 1 fila.

## 4. Sin reintentos (NFR10.11)

- Ninguna fase se reintenta sola: ni la lectura, ni T2, ni T3. El pool no tiene política de reintentos y
  una comprobación estática de nivel 0 falla si el código de U12 tiene un bucle de reintento o usa
  `tenacity`.
- La repetición la decide el investigador con «Reintentar» del estado `failed` del diálogo, y es segura
  por la unicidad de `source_sha256`.
- En la consola, TanStack Query lleva `retry: false` en la mutación de la subida; las consultas de lectura
  siguen la política de la consola de U4.

## 5. Corte del cliente

- Si el navegador corta durante la lectura (`ClientDisconnect` de Starlette, o «Cancelar» con
  `AbortController`), la subida termina sin T2 ni T3, suelta el hueco y deja la línea de log con
  `outcome: aborted` (NFRD-U12-03).
- Si corta después de T3, la fila queda: es un reporte válido y completo. El diálogo, al cerrarse, vuelve a
  pedir la lista (NFRD-U12-06).

## 6. Arranque (NFR10.15, BR3.6)

| Paso | Qué se comprueba | Si falla |
|---|---|---|
| 1 | Cifras de U12 en C25 con `limits.load` (incluida `research_report_read_timeout_s`) | El proceso termina con código ≠ 0 antes de abrir el puerto; el log nombra la cifra |
| 2 | Los cuatro archivos del catálogo existen, cargan con el YAML seguro de U1 y sin claves repetidas | Igual; el log nombra el archivo y la regla, nunca el contenido |
| 3 | `config/profiles.yaml` pasa `profiles.validate`; las listas de etiquetas no están vacías ni repiten | Igual |
| 4 | El validador de C19 vigente compila desde `veridicus_contracts.registry` | Igual |
| 5 | `ReferenceCatalog` inmutable y `catalog_sha256` en el log de arranque | — |

Como el proceso no abre el puerto, `/readyz` (C16) nunca responde `200` con un catálogo roto, y la prueba
de humo de U2 falla y lleva a `git revert` (`team.md`). Pruebas de nivel 0: cada archivo ausente, inválido o
con una clave repetida.

## 7. Recuperación (NFR10.16)

- El investigador conserva el JSON que produjo la CLI. Tras restaurar PostgreSQL con el procedimiento de
  U2, un reporte perdido se vuelve a subir (`201`) y uno que ya estaba da `409`.
- RPO: el último volcado manual de U2; RTO: el de una restauración manual de `session-api` (NFRD-U2-13).
- Prueba de nivel 1 de la re-subida tras vaciar las tablas de U12.

## 8. Degradación

| Situación | Comportamiento | Diseño |
|---|---|---|
| PostgreSQL caído o lento al subir | `503` `system.unavailable` y 0 filas; M8 muestra el error del sistema con «Reintentar» | §1, §2 |
| PostgreSQL caído al leer | `503`; la lista muestra «Error» con «Reintentar» | §1 |
| Dos subidas en curso | La tercera espera hasta 5 s y después `503` con `Retry-After` | §1; `scalability-design.md` §3 |
| Cliente lento | Vence a los 30 s sin retener conexión | §1 |
| Catálogo roto en un despliegue | `session-api` no arranca; la prueba de humo falla y se revierte | §6 |
| Archivo enorme o patológico | `413` o `422` sin afectar a las demás peticiones | `security-design.md` §3, §4 |

## 9. Pruebas de fiabilidad

| Prueba | Camino feliz | Casos de error |
|---|---|---|
| Atomicidad | Subida típica con `201` y las cuatro tablas escritas | Fallo tras la primera hija; corte de la conexión; plazo vencido |
| Duplicados | Dos archivos distintos aceptados | Mismo archivo seguido (E7); en paralelo (E8) |
| Huecos | Dos subidas a la vez con `201` | Tercera con `503`; hueco suelto tras un `422` y tras un corte del cliente |
| Plazo de lectura | Subida máxima en ≤ 30 s | Cliente que envía 1 KiB por segundo: `503` a los 30 s y 0 filas |
| Rol entre T1 y T3 | Sin cambio: `201` | `PATCH` que quita el rol: `403`; desactivación: `401`; 0 filas en los dos |
| Arranque | Los cuatro archivos válidos | Uno ausente; uno inválido; uno con clave repetida |
