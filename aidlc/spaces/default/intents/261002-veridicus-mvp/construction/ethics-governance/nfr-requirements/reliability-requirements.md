# Requisitos de fiabilidad — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR10 y NFR11).
- **Alcance.** U13 vive dentro de `session-api`, sin réplica ni plataforma propias. No tiene un objetivo de
  disponibilidad aparte: está disponible cuando `session-api` y PostgreSQL lo están (U2). Lo que fija aquí es
  cómo falla: el registro de acceso nunca rompe una lectura, el `Job` borra una sesión entera o no la toca,
  nada se reintenta solo y nada arranca con una configuración rota.

**Insumos.** F3, F6, F7, F8, §9 y E14, E15, E39–E46 de functional-spec; BR1.1, BR2.1, BR2.3, BR4.4,
BR5.3–BR5.8 de rules; C23, C24 y C25 de contract-summary; NFR10.11 y NFR10.21 de U3 (plazos y punto de
guardado); NFR10.17 de U7 (500 ms en la exportación); NFR10.21 de U4 (clave de cancelación); NFR10.27 de
U7 y NFR3.9 de U5 (sus partes del borrado); NFR10.16 de U2 (`backoffLimit: 0`); Code Style de `team.md`
(*timeout* explícito, reintentos solo en lo recuperable e idempotente, configuración faltante impide
arrancar).

## 1. Requisitos

### NFR10 — Plazos, errores y arranque

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.13 | nuevo | El adaptador real de `AccessLog` tiene su plazo, no reintenta y no cambia el plazo de quien llama (BR2.3, FD-U13-11). | La inserción corre con `SET LOCAL statement_timeout` igual a `VERIDICUS_ACCESS_LOG_TIMEOUT_MS` (500 ms, U3) y después restaura el plazo anterior de la transacción. Con una espera inyectada de 600 ms, lanza la excepción de registro de acceso de la jerarquía común en ≤ 600 ms. En una lectura, la respuesta sale `200` con las escrituras del manejador (E14); en la exportación, `503` `report.export_not_recorded` sin bytes (E15). Tras un registro correcto, una sentencia de quien llama que tarda 1 s sigue funcionando (su plazo de 2 s no quedó en 500 ms). El código del adaptador no tiene bucles de reintento | Nivel 1 |
| NFR10.14 | nuevo | `session-api` no arranca con U13 roto (BR1.1, BR2.1). | Con `usage-rules.v1.yaml` ausente, inválido, con dos puntos o con una clave repetida, el proceso termina con código ≠ 0 antes de abrir el puerto y el log nombra el archivo (E9). Si el adaptador no puede comprobar su tabla al arrancar (falta la tabla o el permiso `INSERT`, con `connect_timeout` de 2 s), tampoco arranca. Con todo válido, `/readyz` responde `200` sin `access_log: not_configured` (E13) | Nivel 0 y nivel 1 |
| NFR10.15 | nuevo | Toda E/S de U13 tiene un plazo explícito. | Rutas: `statement_timeout` de 2 s (U3) y `lock_timeout` de 2 s (U5) en la `PATCH`. Redis: ≤ 0,5 s por operación (U3). `Job`: los mismos 2 s por sentencia, más un plazo por sesión de **60 s** (`VERIDICUS_RETENTION_SESSION_TIMEOUT_S`, entero entre 10 y 300) comprobado antes del *commit*, y el plazo de U7 para cada archivo (5 s). Comando de consulta: 2 s por sentencia y `--limit`. Al vencer: *rollback*, `503` `system.unavailable` en las rutas o `failed` con `system.unavailable` en el `Job`. Pruebas con una base retenida 3 s y un archivo que tarda 6 s | Nivel 0 (configuración) y nivel 1 |
| NFR10.16 | nuevo | Ninguna ruta de U13 se reintenta sola (§9 del Functional Design). | El código de las rutas no tiene bucles de reintento ni usa la política de reintentos del controlador (comprobación estática). Reconocer y reportar son inserciones nuevas; reducir dos veces con el mismo valor da `422` la segunda vez. La consola ofrece «Reintentar» solo tras un error, nunca de forma automática | Nivel 0 y nivel 1 |
| NFR10.17 | nuevo | El `Job` borra cada sesión entera o no la toca, y sigue con las demás (BR5.6). | Cada candidata corre en su propia transacción con el orden de C24. Fallo inyectado en la segunda de tres: la 1 y la 3 quedan borradas con su acta, la 2 queda entera (todas sus filas en todas las tablas) y el código de salida es 1 (E42). La línea de la 2 lleva `failed` y su `code`. Nunca se reintenta una sesión dentro de la misma ejecución | Nivel 1 |
| NFR10.18 | nuevo | El `Job` no borra una sesión cuya cancelación no pudo escribir (BR5.4, NFR-U13-05). | Con Redis caído o lento (> 0,5 s), la sesión queda `failed` con `system.unavailable`, sin borrar nada ni escribir acta, y el `Job` sigue. Con Redis disponible y una corrida en cola: la clave de CD-06 se escribe antes del borrado, el *fake* del trabajador registra 0 llamadas nuevas y un resultado tardío no crea filas (E40, FD-U13-13) | Nivel 1 |
| NFR10.19 | nuevo | Solo corre una ejecución del `Job` a la vez (NFR-U13-04). | La ejecución toma `pg_try_advisory_lock` con una clave fija antes de seleccionar. Si otra la tiene, termina con código **3** sin borrar ni escribir actas. `--dry-run` también toma el bloqueo, para no contar filas a mitad de un borrado. Prueba con dos ejecuciones simultáneas: una 0 y otra 3 | Nivel 1 |
| NFR10.20 | nuevo | Relanzar el `Job` es seguro (BR5.6, BR5.7; NFR10.27 de U7). | Tras una ejecución que vence su plazo o se interrumpe a mitad, la siguiente vuelve a seleccionar lo que falta y termina con código 0. Una sesión ya borrada no aparece ni da un segundo acta. Un archivo que ya no está queda en el acta con `file_missing: true` y el borrado sigue (E43). `backoffLimit: 0`: Kubernetes nunca relanza solo (U2) | Nivel 1 |
| NFR10.21 | nuevo | El `Job` usa el reloj real para borrar (BR5.3). | Sin `--dry-run`, `as_of` es la hora UTC del proceso en ese momento, igual en todas las candidatas de la ejecución y registrada en la línea de resumen. `--dry-run --as-of` con una fecha futura deja 0 filas borradas, 0 actas y 0 claves de cancelación (E45) | Nivel 0 y nivel 1 |

### NFR11 — Atomicidad

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.7 | nuevo | Reducir el plazo escribe todo o nada (BR4.4). | En una transacción y con el orden de bloqueo sesión primero (`change_cursor.bump` y después el resto): los dos campos de U4, el `change_cursor` y el `RetentionChange`. Con un fallo inyectado después de `set_retention`, la respuesta es `503` `system.unavailable` y ni los campos ni el historial cambian. Dos reducciones simultáneas: NFR3.12 | Nivel 1 |
| NFR11.8 | nuevo | Un reconocimiento y un reporte se guardan enteros o no se guardan (BR1.3, BR3.6). | Con la base caída o un fallo inyectado antes del *commit*: `503` `system.unavailable` y 0 filas. La creación con plazo (F5) guarda `retention_days` y `retention_until` en la misma transacción que la sesión: una creación fallida no deja una sesión sin plazo | Nivel 1 |

## 2. Degradación

| Situación | Comportamiento | Requisito |
|---|---|---|
| La tabla del registro de acceso bloqueada o lenta | Las lecturas responden igual, con un aviso con IDs y la métrica de U3; la exportación responde `503 report.export_not_recorded` sin bytes | NFR10.13 |
| PostgreSQL caído | Las rutas de U13 responden `503` `system.unavailable` sin filas; la consola sigue usable (el diálogo y la franja no bloquean, BR1.6) | NFR10.15, NFR11.8 |
| `usage-rules.v1.yaml` roto en un despliegue | `session-api` no arranca; la prueba de humo falla y se revierte con `git revert` (`team.md`) | NFR10.14 |
| Redis caído durante el `Job` | Ninguna sesión se borra; todas quedan `failed`, la salida es 1 y la siguiente ejecución las retoma | NFR10.18 |
| El `Job` vence su `activeDeadlineSeconds` | Lo confirmado queda borrado con su acta; lo que estaba a mitad se revierte; se relanza | NFR10.20 |
| Dos `Job` lanzados a la vez | El segundo sale con código 3 sin tocar nada | NFR10.19 |

## 3. Pruebas de fiabilidad

Cada prueba cubre el camino feliz y al menos dos casos de error (fase de Construction):

| Prueba | Camino feliz | Casos de error |
|---|---|---|
| Registro de acceso | Lectura y exportación registradas | Tabla bloqueada en la lectura; tabla bloqueada en la exportación; adaptador que tarda 600 ms |
| Arranque | Archivo de reglas válido y adaptador conectado | Archivo ausente; archivo con dos puntos; tabla sin permiso `INSERT` |
| Borrado por sesión | Tres sesiones vencidas borradas | Fallo en la segunda; Redis caído; plazo por sesión vencido |
| Relanzamiento | Una ejecución completa | Interrumpida a mitad; archivo que ya falta; dos ejecuciones simultáneas |
| Reducir el plazo | Reducción con su historial | Fallo tras `set_retention`; dos reducciones simultáneas; ampliar |

## 4. Riesgos que se deciden en la aprobación

Vienen de la pregunta 6 del Functional Design, que no bloquea.

| Riesgo | Tratamiento |
|---|---|
| **Con P3 = A, una sesión que sigue abierta se borra al vencer** | Aceptado en el Functional Design. Mitigaciones sin cambio de diseño: la cabecera de M4 muestra el vencimiento; el `Job` cancela antes las corridas (NFR10.18); `--dry-run` muestra lo que vencería antes de borrar |
| **Con P5 = A, la demo en vivo necesita una sesión creada el día anterior** | Aceptado (FD-U13-09): `--dry-run --as-of` con una fecha futura muestra el efecto sin esperar. La sesión de 1 día se crea en el ensayo de la demo |
| **Con P6 = A, un reporte sin sesión puede traer testimonio durante 90 días** | Mitigado por el aviso fijo de BR3.8 y el borrado por antigüedad (BR5.8). Ver `security-requirements.md` §6 |
| **Una purga revertida tras borrar un archivo** deja una fila sin archivo hasta la siguiente ejecución | Aceptado (U7): la vista previa responde `409 report.integrity_mismatch` y la siguiente ejecución termina con `file_missing` (NFR10.20) |
