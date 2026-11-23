# Diseño de observabilidad — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01, la adenda 02 y el NFR Requirements de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.**
  - Las métricas son internas de `session-api`: no van a C15 ni a `contracts/metrics/` (NFR-U7-04; diseño
    de U1).
  - `downloads_total` pasa a `previews_total`.
  - Entran las exportaciones, la cuota del volumen y los eventos de la purga.
  - `storage_failed` pasa a `internal`.
  - Se conservan, como precisión, `outdated` (P1 = A) y `files_cleaned_total` (P2 = A) (NFRD-U7-08).
  - La regla del volumen usa la cuota propia.
- **Numeración.** §1–§5 conservan su número. La tabla de precisiones de §6 queda «Retirado»: sus filas están
  en `security-design.md` §14.

**Insumos.**
- De esta unidad, en `nfr-requirements/`: `observability-requirements.md` (observability-requirements:
  NFR15.1–NFR15.5), `performance-requirements.md` (performance-requirements), `security-requirements.md`
  (security-requirements), `scalability-requirements.md` (scalability-requirements),
  `reliability-requirements.md` (reliability-requirements) y `tech-stack-decisions.md`
  (tech-stack-decisions).
- F1–F10 de `functional-design/functional-spec.md` (functional-spec).
- C16 y C23 de `inception/contract-design/contract-summary.md` (contract-summary).
- P1 = A y P2 = A.
- De otras unidades: el formateador de logs de U3 y los paneles de U4 y U5.

## 1. Logs (NFR15.2)

- Formateador JSON de `libs/` con lista blanca (U3): una línea por evento, con `timestamp`, `level`,
  `service`, `event`, `request_id` y solo los campos de NFR10.7. Nunca transcripción, nota, reformulación,
  hecho, observaciones, cita, nombre de usuario de la marca ni contenido del reporte.

| Evento | Nivel | Campos | Cuándo |
|---|---|---|---|
| `session.finalized` | `INFO` | `session_id`, `user_id`, `runs_in_progress` | `after_commit` de F1 |
| `report.consolidated` | `INFO` | `report_version_id`, `session_id`, `round_id`, `version_number`, `byte_size`, `sha256`, `user_id`, `duration_ms` | `after_commit` |
| `report.consolidation_rejected` | `INFO` | `session_id`, `user_id`, `code` (incluido `report.view_outdated`) | Tras el *rollback* |
| `report.previewed` | `INFO` | `report_version_id`, `user_id` | Tras responder `200` |
| `report.exported` | `INFO` | `export_id`, `report_version_id`, `user_id`, `export_sha256`, `was_current` | `after_commit` |
| `report.correction_opened`, `report.correction_discarded` | `INFO` | `session_id`, `round_id`, `user_id` | `after_commit` |
| `report.purged` | `INFO` | `session_id`, conteos, `file_missing` | Al volver de `purge_session` (en el `Job`) |
| `report.orphan_removed`, `report.unexpected_file` | `WARNING` | `file_name` | Barrido |
| `report.file_cleaned` | `WARNING` | `file_name`, `reason`: `rollback` o `timeout` | Limpieza tras el *rollback* o del hilo |
| `report.commit_unknown` | `WARNING` | `report_version_id` | `COMMIT` fallido (DS4) |
| `report.access_log_not_configured` | `WARNING` | `export_id`, `report_version_id` | Cada exportación con el adaptador por defecto |
| `report.purge_file_missing` | `WARNING` | `report_version_id` | Purga |
| *Timeout* | `WARNING` | `code` `system.unavailable`, `reason`: `db`, `lock`, `storage`, `deadline`, `idle` | Al vencer |
| `report.integrity_mismatch` | `ERROR` | `report_version_id` | Vista previa o exportación |
| `report.cleanup_failed`, `report.export_not_recorded`, `system.internal` del volumen | `ERROR` | `file_name` o `report_version_id`, `code` | Volumen o `AccessLog` |

- **Correlación.** Sin trazas distribuidas, porque es un solo proceso. `request_id`, `session_id`,
  `round_id`, `report_version_id` y `export_id` reconstruyen la historia.
- **Verificación (nivel 1).** Una prueba reconstruye solo con logs la historia finalizada → consolidada →
  vista → exportada → corregida → versión 2 → purgada. Otra aplica la cadena centinela de
  `security-design.md` §7, con 0 coincidencias.

## 2. Métricas (NFR15.1, NFR15.4, NFR15.5)

`prometheus-client` en `/metrics` del puerto interno 8081. Las etiquetas son solo de enum (`result`,
`reason`), validadas contra su lista en nivel 0.

| Métrica | Tipo | Etiquetas | Dónde se actualiza |
|---|---|---|---|
| `veridicus_report_consolidations_total` | counter | `result`: `created`, `conflict`, `blocked`, `outdated`, `forbidden_vocabulary`, `too_large`, `internal`, `unavailable` | `created` en `after_commit`; los demás tras el *rollback*. `outdated` es el `409 report.view_outdated` (NFRD-U7-08) |
| `veridicus_report_consolidation_seconds` | histogram (0,1 · 0,25 · 0,5 · 1 · 1,5 · 2 · 5 · 10 s) | — | De la guardia al final del manejador, solo con `created` |
| `veridicus_report_previews_total` | counter | `result`: `ok`, `integrity_mismatch`, `not_consolidated` | Al responder |
| `veridicus_report_exports_total` | counter | `result`: `created`, `integrity_mismatch`, `not_found`, `not_recorded`, `unavailable` | `created` en `after_commit`; los demás tras el *rollback* |
| `veridicus_report_exports_unaudited_total` | counter | — | `after_commit` de una exportación con el adaptador por defecto |
| `veridicus_report_orphans_removed_total` | counter | — | Barrido |
| `veridicus_report_files_cleaned_total` | counter | `reason`: `rollback`, `timeout` | Limpieza tras el *rollback* o del hilo (NFRD-U7-08) |
| `veridicus_report_volume_used_bytes`, `veridicus_report_volume_quota_bytes` | gauge | — | Cada pasada de la medición (60 s) |
| `veridicus_session_mttv_seconds` | histogram (60 · 120 · 300 · 600 · 900 · 1 800 · 3 600 s) | — | `after_commit` de la versión 1 de una sesión guiada, con `domain/mttv.py` |

- Los `401` y `403` los cuenta ConsoleApi (U3). El `Job` de retención no publica métricas: su resultado
  son el recibo y el log.
- Una prueba de nivel 1 recorre cada camino y comprueba el incremento exacto de cada serie. Una prueba de
  nivel 0 valida cada etiqueta contra su enum (NFR10.10).
- **MTTV (NFR15.4).** Con el reloj en *t* al finalizar una guiada y en *t* + 420 s al consolidar, queda una
  observación de 420. La versión 2 no observa, y una importada tampoco.

## 3. Volumen, exportaciones y reglas (NFR15.3, NFR15.5)

- **Volumen.** Regla de Prometheus (SHOULD, entra por PR con el chart):
  `veridicus_report_volume_used_bytes / veridicus_report_volume_quota_bytes > 0.8` durante 10 min, como
  regla informativa. Las series de ejemplo están en
  `services/session-api/tests/review_report/fixtures/volume_series.yaml`. `promtool test rules
  deploy/veridicus/tests/report-rules.yaml`: 75 % sin disparo y 85 % con disparo.
- **Exportación sin registro.** `increase(veridicus_report_exports_total{result="not_recorded"}[10m]) > 0`
  en el mismo archivo de pruebas, con 0 sin disparo y 1 con disparo.
- `/readyz` en `503` bajo el mínimo libre, sobre la cuota o con el volumen colgado
  (`reliability-design.md` §4) cubre el caso en que la regla no se atendió.
- Sin Alertmanager: ninguna regla despierta a nadie en el MVP. Se ven en Prometheus y en el panel.

## 4. SLI y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| MTTV | Media del arnés de nivel 2; en uso, `_sum / _count` de `veridicus_session_mttv_seconds` | < 600 s |
| Latencia de la consolidación | `histogram_quantile(0.95, …consolidation_seconds_bucket)` | ≤ 1,5 s |
| Integridad | `result="integrity_mismatch"` de `previews_total` y `exports_total` | 0. Cualquier valor es un incidente que se investiga con `verify_store` |
| Exportaciones registradas | `exports_total{result="not_recorded"}` | 0 |
| Huérfanos y limpiezas | `orphans_removed_total` y `files_cleaned_total{reason="timeout"}` | Informativo: un crecimiento sostenido indica un volumen lento |
| Vistas desactualizadas | `consolidations_total{result="outdated"}` | Informativo: cuántas veces el analista tuvo que revisar de nuevo el resumen |
| Llenado del volumen | `used_bytes / quota_bytes` | < 0,8 |

## 5. Panel

Panel de Grafana (SHOULD, lo instala U2) junto a los de U4 y U5. Muestra:
- consolidaciones y exportaciones por resultado;
- latencia p95;
- vistas previas por resultado;
- exportaciones sin auditar;
- MTTV;
- limpiezas por motivo;
- uso del volumen frente a la cuota.
