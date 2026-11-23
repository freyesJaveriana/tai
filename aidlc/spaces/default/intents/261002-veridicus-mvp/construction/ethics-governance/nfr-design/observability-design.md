# Diseño de observabilidad — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.** Todo es nuevo. Las precisiones están en la tabla NFRD-U13-xx de
`security-design.md` §17.

**Insumos.** `nfr-requirements/observability-requirements.md` (observability-requirements: NFR10.22–NFR10.24,
NFR15.1, §2 y §3) de esta unidad; BR2.1, BR2.5, BR3.9, BR5.9 y BR7.1, F3, F7 y F10 de
`functional-design/functional-spec.md` (functional-spec); C15, C16 y C23 de
`inception/contract-design/contract-summary.md` (contract-summary); formateador con lista blanca,
`request_id` y `veridicus_access_log_failures_total` del NFR Design de U3 (`observability-design.md` §1 y
§2); regla de etiquetas de U1 (NFRD-U1-05).

U13 no analiza ni llama a modelos: ninguna métrica de NFR15 es suya. Se observa por sus logs, por la salida
y las actas del `Job`, por el comando de consulta y por la salud de `session-api` (C16).

## 1. Líneas de las rutas (NFR10.23; NFRD-U13-11)

Una línea por escritura correcta o rechazada en el manejador, con el formateador único de U3. Los campos
comunes del formateador (`timestamp`, `level`, `service`, `request_id`, `route`, `method`) van siempre.

| `event` | Campos propios | Nivel |
|---|---|---|
| `ethics.acknowledged` | `user_id`, `text_version` | `INFO` |
| `ethics.problem_reported` | `problem_report_id`, `user_id`, `session_id`, `suggestion_id`, `category`, `testimony_warning` | `INFO` |
| `retention.reduced` | `session_id`, `user_id`, `from_days`, `to_days` | `INFO` |
| `access_log.record_failed` (de `record_access` de U3, con el adaptador de U13) | `resource_type`, `resource_id`, `user_id`, `code` | `WARNING` |

- Un rechazo del manejador (`422` de dominio) deja la línea genérica del manejador único con `code` y
  `WARNING`; los `401`, `403` y `413` de `GuardedRoute` también son líneas genéricas de U3.
- `note` no está en la lista blanca: aunque un caso de uso la pasara al *logger*, el formateador la
  descartaría. Prueba AST de nivel 0: ningún `logger` de `session_api.ethics_governance` ni de las rutas de
  U13 recibe `note`, el objeto del reporte ni un texto de turno.
- Prueba de nivel 1: compara el conjunto de claves de cada línea con esta tabla; una clave de más rompe la
  prueba.

## 2. Arranque (NFR10.24)

- Línea `ethics.startup` (`INFO`) con `usage_rules_version`, `usage_rules_sha256` (SHA-256 de los bytes del
  archivo) y `access_log_adapter: ethics_governance`.
- Si el arranque falla, línea `ERROR` `config.invalid_usage_rules` o `config.access_log_unavailable` con el
  nombre del archivo o de la tabla y la regla que falló, nunca el contenido.
- `/readyz` deja de traer `access_log: not_configured` (E13).

## 3. Salida del `Job` (NFR10.22; BR5.9)

Una línea JSON por candidata y un resumen, a la salida estándar del pod, con el mismo formateador y la lista
blanca de NFRD-U13-11.

| Línea | Campos (ningún otro) |
|---|---|
| `retention.candidate` | `event`, `job_run_id`, `mode` (`purge` o `dry_run`), `session_id` (nulo en la tanda sin sesión), `rule`, `effective_until`, `counts` (objeto de tabla → entero), `outcome` (`purged`, `would_purge` o `failed`), `code` (solo si falló), `duration_ms` |
| `retention.summary` | `event`, `job_run_id`, `mode`, `as_of`, el número de cada `outcome`, `exit_code`, `duration_ms` |

- `counts` sale de los `PurgeReceipt` en `purge` y de `count_session` en `dry_run` (NFRD-U13-08). Sus claves
  son nombres de tabla de un enum; sus valores, enteros.
- Los códigos 2 y 3 terminan antes de seleccionar: dejan solo el `retention.summary`, con todos los
  `outcome` en 0 y su `exit_code`, sin candidatas. `job_run_id` y `as_of` se fijan lo primero, para que el
  resumen exista siempre. En el código 2, `argparse` escribe además su uso en la salida de error, que solo
  nombra opciones.
- Prueba de nivel 1 (E47): con *canary* en turnos, notas y nombres de archivo, 0 coincidencias en la salida
  y en los logs; el conjunto de claves de cada línea coincide con esta tabla.

## 4. Métricas (NFR15.1)

- U13 no publica métricas nuevas y C15 no cambia. Contrato de import-linter `ethics-governance-no-metrics`:
  `session_api.ethics_governance` no importa `prometheus_client`, con su control negativo. Por eso U13 no
  tiene archivo `contracts/metrics/ethics-governance.v1.yaml`.
- El fallo del registro de acceso lo cuenta `veridicus_access_log_failures_total{resource_type}` de U3; tras
  cablear U13, un valor mayor que 0 se revisa a mano (panel de U3).
- Un `Job` que vive minutos no se raspa: su registro son las actas y su salida.
- Un contador futuro (reportes, borrados) entraría en `contracts/metrics/ethics-governance.v1.yaml` con
  etiquetas de la lista cerrada de U1 (NFRD-U1-05), nunca con la nota ni con `session_id`.

## 5. Salud (C16)

U13 no suma comprobaciones a `/readyz`: las reglas y el adaptador se comprueban al arrancar y el proceso no
abre el puerto si fallan (`reliability-design.md` §3). La prueba de humo de U2 cubre la disponibilidad tras
cada despliegue.

## 6. Qué responde cada señal

| Pregunta | Dónde se mira |
|---|---|
| ¿Quién abrió qué sesión, sugerencia o versión, y cuándo? | `access-log` del comando de consulta |
| ¿Qué se borró, por qué regla y cuándo? | `retention-acts` del comando y la salida del `Job` |
| ¿Qué problemas reportaron los analistas? | `problem-reports` del comando |
| ¿Quién redujo un plazo? | `retention_change` (mientras exista la sesión) y la línea `retention.reduced` |
| ¿Está cableado el registro de acceso real? | `/readyz` y la línea `ethics.startup` |
| ¿Falló el registro de una lectura? | `veridicus_access_log_failures_total` y la línea `access_log.record_failed` |
| ¿Con qué texto de reglas arrancó `session-api`? | `usage_rules_version` y `usage_rules_sha256` de `ethics.startup` |

Sin trazas distribuidas, como el resto de `session-api` (U3). Los logs se leen con `kubectl logs` en la
máquina del humano (sin Loki en el MVP) y, como solo llevan IDs, reglas, conteos y hashes, no tienen una
retención especial. La salida del `Job` queda en el log de su pod hasta que el humano borra el `Job`.
