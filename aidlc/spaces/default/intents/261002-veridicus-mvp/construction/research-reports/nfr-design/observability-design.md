# Diseño de observabilidad — U12 research-reports

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo. Las precisiones están en la tabla NFRD-U12-xx de
`security-design.md` §14.

**Insumos.** `nfr-requirements/observability-requirements.md` (observability-requirements: NFR10.17–NFR10.19
y NFR15.1) de esta unidad; BR3.6, BR4.2 y BR4.3, F5 y F6 de `functional-design/functional-spec.md`
(functional-spec); C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); el
formateador con lista blanca, el `request_id` y las métricas internas del NFR Design de U3
(`observability-design.md` §1 y §2); la regla de etiquetas de U1 (NFRD-U1-05).

U12 no analiza ni llama a modelos: ninguna métrica de NFR15 es suya. Se observa por sus logs, por la salud de
`session-api` (C16) y por las métricas genéricas que U3 ya publica para todas las rutas.

## 1. Línea de la subida (NFR10.17, BR4.3; NFRD-U12-03)

Una línea del evento `research_report.upload` por cada `POST /research-reports` que llega a ResearchReports
(desde la comprobación del tipo), emitida en un `finally` con el formateador único de U3.

| Campo | Valor | Siempre |
|---|---|---|
| Comunes del formateador | `timestamp`, `level`, `service`, `request_id`, `route`, `method`, `user_id` | Sí |
| `event` | `research_report.upload` | Sí |
| `outcome` | `accepted`, `rejected` o `aborted` | Sí |
| `status` | Estado HTTP | Salvo en `aborted` |
| `code` | `code` del rechazo | Solo si se rechazó |
| `rule` | Regla del primer problema (enum de §6.2 del Functional Design) | Solo en `422` `research.invalid_report` |
| `problem_count` | Total de problemas | Solo en `422` |
| `resource_type`, `resource_id` | `research_report` y el `research_report_id` | Solo si se aceptó |
| `source_sha256` | SHA-256 del archivo | Si se leyó entero (no en `413`, `415`, `503` previo ni `aborted`) |
| `source_bytes` | Bytes leídos de la parte `file` | Si se empezó a leer |
| `cause` | `upload_slots`, `upload_read_timeout` o `db` | Solo en `503` |
| `duration_ms` | Desde la entrada a la ruta | Sí |

- Nivel `INFO` en `accepted`, `WARNING` en `rejected` y `aborted`, `ERROR` en `503` (como U3).
- Los `401` y `403` de T1 no llegan a ResearchReports: quedan en la línea genérica de U3, como en las demás
  rutas. El manejador único sigue dejando su línea genérica de los `4xx`; la línea de U12 es la única con
  `event: research_report.upload`.
- Prueba de nivel 1: compara el conjunto de claves de la línea en `201`, `409`, `413`, `415`, `422`, `503`
  y `aborted` con esta tabla; una clave de más rompe la prueba.

## 2. Arranque (NFR10.18)

Una línea `research_reports.catalog_loaded` (`INFO`) con `catalog_sha256`, `price_table_version`,
`profile_count` y `c19_version`. El `catalog_sha256` es el SHA-256 de la
concatenación, en orden fijo, del SHA-256 de cada uno de los cuatro archivos. Si el arranque falla, una línea
`ERROR` `config.invalid_reference_catalog` con el nombre del archivo y la regla que falló, nunca su contenido.
Los nombres de campo nuevos (`price_table_version`, `profile_count`, `c19_version`) entran en la lista
blanca de U3 con la precisión NFRD-U12-03.

## 3. Logs sin contenido (NFR10.19)

- La lista blanca de U3 descarta todo campo fuera de la tabla de §1 y §2, se llame como se llame.
- Prueba de nivel 0 (AST): ningún `logger` de `session_api.research_reports` recibe como argumento el
  cuerpo, el `bytearray`, el documento JSON, el `filename` ni una excepción de `json` o de `jsonschema`, y
  ningún `log.exception` corre dentro de la validación.
- El acceso de Uvicorn está apagado (`security-design.md` §5). La prueba del *canary* de NFR12.1 se repite
  sobre los logs capturados de la aplicación y de `uvicorn.error`.

## 4. Métricas (NFR15.1)

- U12 no publica métricas nuevas y C15 no cambia. El contrato de import-linter
  `research-reports-no-metrics` prohíbe `prometheus_client` en `session_api.research_reports`, con su
  control negativo.
- La métrica genérica de U3 ya cubre las rutas de U12 sin código de U12: `veridicus_problem_responses_total`
  cuenta en el manejador único los `500` y `503` (etiqueta `status`), también los de la subida.
- Un contador de subidas futuro entra como precisión a C15 con la etiqueta `outcome` de la lista cerrada de
  U1, declarado en `contracts/metrics/research-reports.v1.yaml` (NFRD-U1-05); nunca con valores del
  reporte.

## 5. Salud (C16)

U12 no suma comprobaciones a `/readyz`: el catálogo se valida al arrancar y el proceso no abre el puerto si
falla (`reliability-design.md` §6). `/readyz` de `session-api` ya comprueba la base. La prueba de humo de U2
cubre la disponibilidad tras cada despliegue.

## 6. Qué responde cada señal

| Pregunta | Dónde se mira |
|---|---|
| ¿Quién subió un reporte y cuándo? | `uploaded_by` y `uploaded_at` de la fila, y la línea de §1 |
| ¿Por qué se rechazó una subida? | `code`, `rule` y `problem_count` de la línea, con el mismo SHA-256 que vio el investigador en M8 |
| ¿Se cortan subidas por los huecos o por el plazo de lectura? | `cause` en las líneas `503` |
| ¿Con qué catálogo arrancó `session-api`? | `catalog_sha256` del log de arranque |
| ¿Está disponible? | `/readyz` de `session-api` y la prueba de humo de U2 |

Sin trazas distribuidas, como el resto de `session-api` (U3). Los logs se leen con `kubectl logs` en la
máquina del humano (sin Loki en el MVP) y, como solo llevan IDs, cifras y hashes, no tienen una retención
especial.
