# Requisitos de observabilidad — U13 ethics-governance

**Revisión 1 (2026-11-22): primera pasada.**
- **IDs.** Todo es **nuevo** y hereda el ID del NFR de Inception (NFR10, por los logs solo con IDs, y NFR15).
- **Alcance.** NFR15 (SHOULD) pide en Prometheus las métricas de los pods de IA, la latencia por análisis,
  los *tokens* por proveedor y la AIR. Ninguna es de U13, que no analiza. U13 se observa por sus logs, por su
  salida del `Job`, por sus actas y por la salud de `session-api` (C16). No añade métricas a C15: el fallo
  del registro de acceso ya lo cuenta `veridicus_access_log_failures_total` de U3. Un `Job` que vive minutos
  no se puede raspar con Prometheus, así que su registro son las actas y su salida.

**Insumos.** BR2.1, BR2.5, BR3.9, BR5.9 y BR7.1 de rules; F3, F7 y F10 de functional-spec; NFR10 y NFR15 de
requirements; C15, C16 y C23 de contract-summary; NFR15.1 de U1 (etiquetas cerradas) y NFR15.1 de U3
(`veridicus_access_log_failures_total`); Code Style de `team.md` (logs sin datos sensibles, solo IDs).

## 1. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.22 | nuevo | La salida del `Job` es una línea JSON por candidata y un resumen, solo con IDs, reglas, conteos y `code` (BR5.9). | Por candidata: `event` (`retention.candidate`), `job_run_id`, `mode` (`purge` o `dry_run`), `session_id` (nulo en la tanda sin sesión), `rule`, `effective_until`, `counts` (filas por tabla), `outcome` (`purged`, `would_purge` o `failed`), `code` (si falló) y `duration_ms`. Resumen: `event` (`retention.summary`), `job_run_id`, `mode`, `as_of`, el número de cada `outcome`, `exit_code` y `duration_ms`. Ningún otro campo: la prueba compara el conjunto de claves. Con datos sintéticos con *canary* en turnos, notas y nombres de archivo, 0 coincidencias en la salida y en los logs (E47) | Nivel 1 |
| NFR10.23 | nuevo | Las rutas de U13 dejan una línea de log por escritura, sin texto (BR2.5, BR3.9). | `POST /acknowledgements`: `event` (`ethics.acknowledged`), `user_id`, `text_version`. `POST /problem-reports`: `event` (`ethics.problem_reported`), `problem_report_id`, `user_id`, `session_id`, `suggestion_id`, `category`, `testimony_warning`. `PATCH /sessions/{id}/retention`: `event` (`retention.reduced`), `session_id`, `user_id`, `from_days`, `to_days`. Un fallo del adaptador de `AccessLog`: `WARNING` con `resource_type`, `resource_id`, `user_id` y `code`. Nivel `INFO` en el éxito y `WARNING` en el rechazo o el fallo. Ningún otro campo; nunca la nota (NFR10.5) | Nivel 1 |
| NFR10.24 | nuevo | El arranque deja constancia de U13 (BR1.1, BR2.1). | El log de arranque de `session-api` lleva la versión de `usage-rules.v1.yaml`, su SHA-256 y `access_log_adapter: ethics_governance`. `/readyz` deja de traer `access_log: not_configured` (E13). Si el arranque falla, el log nombra el archivo o la tabla y la regla que falló, nunca su contenido | Nivel 0 y nivel 1 |
| NFR15.1 | nuevo | U13 no publica métricas nuevas. | C15 no cambia por U13 y `ethics_governance` no importa `prometheus_client` (import-linter). El fallo del registro de acceso lo cuenta `veridicus_access_log_failures_total` de U3; tras cablear U13, cualquier valor mayor que 0 se revisa a mano (U3). Si más adelante se quiere un contador de reportes o de borrados, entra como precisión a C15 con etiquetas de la lista cerrada de U1; nunca con la nota ni con `session_id` como texto libre | Nivel 0 |

## 2. Qué responde cada señal

| Pregunta | Dónde se mira |
|---|---|
| ¿Quién abrió qué sesión, sugerencia o reporte, y cuándo? | `access-log` del comando de consulta (BR7.1) |
| ¿Qué se borró, por qué regla y cuándo? | `retention-acts` del comando de consulta y la salida del `Job` (NFR10.22) |
| ¿Qué problemas reportaron los analistas? | `problem-reports` del comando de consulta |
| ¿Quién redujo un plazo? | `RetentionChange` (mientras exista la sesión) y la línea `retention.reduced` (NFR10.23) |
| ¿Está cableado el registro de acceso real? | `/readyz` y el log de arranque (NFR10.24) |
| ¿Falló el registro de una lectura? | `veridicus_access_log_failures_total` de U3 y la línea `WARNING` (NFR10.23) |

## 3. Retención y acceso a los logs

Los logs de U13 siguen la política de `session-api` que fija U2 (sin Loki en el MVP; los del contenedor se
leen con `kubectl logs` en la máquina del humano). Como solo llevan IDs, reglas, conteos y hashes, no tienen
una retención especial. La salida del `Job` queda en el log de su pod hasta que el humano lo borra; las
actas son el registro que dura.
