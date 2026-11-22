# Requisitos de fiabilidad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR10 y NFR11).
- **Alcance.** U12 vive dentro de `session-api`, sin réplica ni plataforma propias. No tiene un objetivo de
  disponibilidad aparte: está disponible cuando `session-api` y PostgreSQL lo están (U2). Lo que fija aquí es
  cómo falla: sin filas a medias, sin reintentos ocultos y sin arrancar con un catálogo roto.

**Insumos.** F1, F5, §9 y E7, E8, E37 de functional-spec; BR2.1, BR2.8 y BR3.6 de rules; C1, C16 y C25 de
contract-summary; `system.unavailable` de U3; Code Style de `team.md` (*timeout* explícito, reintentos solo
en lo recuperable e idempotente, configuración faltante impide arrancar).

## 1. Requisitos

### NFR11 — Integridad

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR11.4 | nuevo | Un reporte se guarda entero o no se guarda (BR2.1). | La fila y sus tablas hijas se escriben en una sola transacción. Con un fallo inyectado después de la primera tabla hija (excepción del adaptador y corte de la conexión), la respuesta es `503` `system.unavailable` y quedan **0 filas** en todas las tablas de U12 | Nivel 1 |
| NFR11.6 | nuevo | Un archivo no se guarda dos veces, ni siquiera en paralelo (BR2.8). | `source_sha256` tiene un índice único. Dos subidas simultáneas del mismo archivo, sincronizadas con una barrera para que las dos pasen la comprobación previa del duplicado: una responde `201`, la otra `409` `research.duplicate`, y queda **exactamente 1 fila**. La violación de unicidad se traduce a `409`, nunca a `500` | Nivel 1 (repetido 20 veces sin fallos) |

### NFR10 — Plazos, errores y arranque

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.11 | nuevo | Ninguna operación de U12 se reintenta sola (§9 del Functional Design). | El código de la subida no tiene bucles de reintento ni usa una política de reintentos del controlador de la base (comprobación estática). Ante un error de la base, la respuesta es `503` `system.unavailable` con 0 filas; el investigador vuelve a subir y la unicidad de `source_sha256` hace segura la repetición. La consola ofrece «Reintentar» solo en el estado `failed` del diálogo, nunca de forma automática | Nivel 0 y nivel 1 |
| NFR10.14 | nuevo | La escritura tiene un plazo explícito. | La transacción de escritura corre con `SET LOCAL statement_timeout` igual a `research_report_write_timeout_s` (15 s, NFR-U12-01), leído de C25 con `limits.load`. Con una espera inyectada de 16 s en la base, la respuesta es `503` `system.unavailable`, la transacción se deshace y quedan 0 filas. Las lecturas (lista, detalle, comparación) usan el plazo común de las consultas de `session-api`; si ninguna unidad lo fijó, lo fija NFR Design | Nivel 1 |
| NFR10.15 | nuevo | Sin catálogo de referencia válido, `session-api` no arranca (BR3.6, F5). | Con cada uno de los cuatro archivos ausente, inválido o con una clave repetida, el proceso termina con código ≠ 0 antes de abrir el puerto, y el log nombra el archivo. Así `/readyz` (C16) nunca responde `200` con un catálogo roto. Con los cuatro válidos, el log de arranque lleva `catalog_sha256` | Nivel 0 |
| NFR10.16 | nuevo | Recuperación de los reportes. | Un reporte se puede reconstruir siempre: el investigador conserva el JSON que produjo la CLI (en su máquina o en la salida de ZINE). Tras restaurar PostgreSQL desde la copia que define U2, un reporte perdido se vuelve a subir y responde `201`; uno que ya estaba responde `409`. El RPO de U12 es el de la copia de U2, y su RTO el de `session-api` | Revisión del procedimiento de U2 y prueba de nivel 1 de la re-subida |

## 2. Degradación

| Situación | Comportamiento | Requisito |
|---|---|---|
| PostgreSQL caído o lento al subir | `503` `system.unavailable`, 0 filas; la consola muestra el error del sistema con «Reintentar» | NFR10.11, NFR10.14, NFR11.4 |
| PostgreSQL caído al leer | `503` `system.unavailable`; la lista muestra su estado «Error» con «Reintentar» | NFR10.11 |
| Catálogo de referencia roto en un despliegue | `session-api` no arranca; la prueba de humo (`scripts/smoke.sh`) falla y se revierte con `git revert` (`team.md`) | NFR10.15 |
| Archivo enorme o patológico | `413` o `422` sin afectar a las demás peticiones | NFR10.3, NFR10.5 de `security-requirements.md`; NFR3.10 |

## 3. Pruebas de fiabilidad

Cada prueba cubre el camino feliz y al menos dos casos de error (fase de Construction):

| Prueba | Camino feliz | Casos de error |
|---|---|---|
| Atomicidad | Subida típica con 201 y todas las tablas hijas escritas | Fallo tras la primera tabla hija; corte de la conexión; plazo vencido |
| Duplicados | Dos archivos distintos aceptados | Mismo archivo seguido (E7); mismo archivo en paralelo (E8) |
| Arranque | Los cuatro archivos válidos | Uno ausente; uno inválido; uno con clave repetida |

## 4. Riesgos

| Riesgo | Tratamiento |
|---|---|
| **Costo de P1 = A (E18 y E19, pregunta abierta 5 del Functional Design).** Un reporte hecho antes de cambiar un perfil o la tabla de precios por PR ya no se puede subir, porque se contrasta con lo vigente | Aceptado en el Functional Design; **se decide en la aprobación de esta etapa**. Mitigaciones sin cambio de diseño: subir los reportes antes de fusionar el cambio, y crear un perfil con otro nombre cuando cambia el modelo (los nombres no se reutilizan). Si no basta, una revisión futura guarda las versiones anteriores de perfiles y precios (precisión a C18) |
| **Cambio de la versión vigente de C19** (v1 → v2) | Un reporte de la otra versión se rechaza (E14). Igual que arriba: subir antes de desplegar el cambio, o volver a generar el reporte con la CLI nueva |
| **Detalle grande** (unas 7 200 llamadas en el peor caso estimado) | NFR3.5 lo mide. Si no se alcanza, se propone por PR de U1 que C1 devuelva las llamadas ya agrupadas, como las muestra M8 (FD-U12-09); el umbral no se baja |
