# Requisitos de observabilidad — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01, la adenda 02 y el Functional Design de U7,
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Los requisitos conservan su ID y cada fila dice si **se mantiene**, **cambia** o es **nuevo**.
  Entra NFR15.5 (exportaciones y registro de acceso). Ninguno se retira.
- **Qué cambia.** Las métricas de U7 son internas de `session-api` y **no van a C15** (NFR-U3-03,
  NFR-U7-04). La regla del volumen usa los dos *gauges* de la cuota propia y no `kubelet_volume_stats`,
  que el aprovisionador hostPath no publica (P3 = A de Infrastructure Design de U7).

**Insumos.**
- Flujos F1–F10 y §12 (pregunta 3) de `functional-design/functional-spec.md` (functional-spec,
  revisión 2), y reglas BR4.3, BR5.1, BR7.1, BR7.2, BR9.6 y BR10.2 de `functional-design/rules.md`
  (rules).
- NFR7, NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements, revisión 3).
- C16 y C23 de `inception/contract-design/contract-summary.md` (contract-summary).
- `nfr-requirements-questions.md`, segunda pasada, sin preguntas.

## 1. Métricas (Prometheus, en `/metrics` del puerto interno 8081 de `session-api`)

| ID | Estado | Métrica | Tipo | Etiquetas | Cuándo cambia |
|---|---|---|---|---|---|
| NFR15.1 | cambia | `veridicus_report_consolidations_total` | counter | `result`: `created`, `conflict`, `blocked`, `forbidden_vocabulary`, `too_large`, `internal`, `unavailable` | +1 por cada petición de consolidar que llega a ReviewReport; `created` solo tras el *commit*; `blocked` agrupa los `409` de la guardia; `too_large` es el `413` de NFR8.9; `internal` sustituye a `storage_failed` (NFR-U7-03) |
| NFR15.1 | se mantiene | `veridicus_report_consolidation_seconds` | histogram | ninguna; *buckets* 0,1 · 0,25 · 0,5 · 1 · 1,5 · 2 · 5 · 10 s | Duración de cada consolidación `created` |
| NFR15.1 | cambia | `veridicus_report_previews_total` (antes `_downloads_total`) | counter | `result`: `ok`, `integrity_mismatch`, `not_consolidated` | +1 por vista previa respondida |
| NFR15.1 | se mantiene | `veridicus_report_orphans_removed_total` | counter | ninguna | +1 por archivo borrado en el barrido (NFR10.16) |
| NFR15.1 | cambia | `veridicus_report_volume_used_bytes` y `veridicus_report_volume_quota_bytes` | gauge | ninguna | Cada pasada de la medición del volumen (60 s, Infrastructure Design de U7) |
| NFR15.4 | cambia | `veridicus_session_mttv_seconds` | histogram | ninguna; *buckets* 60 · 120 · 300 · 600 · 900 · 1 800 · 3 600 s | Una observación por sesión **guiada** al crear su versión 1, con `mttv_seconds` de `domain/mttv.py` (NFR7.3); las importadas y las correcciones no observan |
| NFR15.5 | nuevo | `veridicus_report_exports_total` | counter | `result`: `created`, `integrity_mismatch`, `not_found`, `not_recorded`, `unavailable` | +1 por exportación que llega a ReviewReport; `created` solo tras el *commit*; `not_recorded` es el `503 report.export_not_recorded` (NFR11.7) |
| NFR15.5 | nuevo | `veridicus_report_exports_unaudited_total` | counter | ninguna | +1 por exportación `created` con el adaptador por defecto de `AccessLog` (sin U13) |

Las etiquetas solo llevan valores de enum (NFR10.10); no hay `session_id`, `report_version_id` ni
`user_id`. Los rechazos `401` y `403` los cuenta ConsoleApi (U3), no U7. Las métricas son internas de
`session-api` y se documentan aquí, no en C15 (NFR-U7-04). Prueba de nivel 1 que recorre cada camino y
comprueba el incremento exacto de cada serie; el trabajo de retención corre en el `Job` y no publica
métricas (su resultado es el recibo y el log, NFR15.2).

## 2. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | Cada hecho de U7 deja un evento estructurado sin texto. | JSON en una línea con `timestamp`, `level`, `service`, `event` y solo los campos de NFR10.7. `INFO`: `session.finalized` (`session_id`, `user_id`, `runs_in_progress`), `report.consolidated` (`report_version_id`, `session_id`, `round_id`, `version_number`, `byte_size`, `sha256`, `user_id`, `duration_ms`), `report.consolidation_rejected` (`session_id`, `user_id`, `code`), `report.previewed` (`report_version_id`, `user_id`), `report.exported` (`export_id`, `report_version_id`, `user_id`, `export_sha256`, `was_current`), `report.correction_opened` y `report.correction_discarded` (`session_id`, `round_id`, `user_id`), `report.purged` (`session_id`, conteos, `file_missing`). `WARNING`: `report.orphan_removed`, `report.unexpected_file`, `report.file_cleaned`, `report.access_log_not_configured` (por exportación, solo IDs), `report.purge_file_missing` y cada *timeout* (`code`). `ERROR`: `report.integrity_mismatch` (solo `report_version_id`), `report.cleanup_failed`, `report.export_not_recorded` y `system.internal` del volumen. Nunca transcripción, nota, reformulación, hecho, observaciones, cita, nombre de usuario de la marca ni contenido del reporte. Nivel 1 que reconstruye la historia de una sesión (finalizada, consolidada, vista, exportada, corregida, versión 2, purgada) solo con sus logs. |

## 3. Volumen, exportaciones y reglas

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.3 | cambia | El llenado del volumen se ve antes de que falle. | Regla de Prometheus (SHOULD, entra por PR con el chart): `veridicus_report_volume_used_bytes / veridicus_report_volume_quota_bytes > 0.8` durante 10 min → regla informativa. `promtool test rules` con dos series de ejemplo (75 % sin disparo, 85 % con disparo) en `services/session-api/tests/review_report/fixtures/volume_series.yaml`. Además `/readyz` pasa a `503` bajo el mínimo libre o sobre la cuota (NFR10.19). |
| NFR15.4 | cambia | El MTTV real se puede ver fuera del arnés. | `veridicus_session_mttv_seconds` permite consultar en Grafana `histogram_quantile` y la media; el valor de aceptación de NFR7 sigue siendo el del arnés (NFR7.1), con la misma función pura. Nivel 1: finalizar una guiada en *t*, consolidar en *t* + 420 s → una observación de 420; consolidar la versión 2 no añade otra; una importada consolidada no añade ninguna. |
| NFR15.5 | nuevo | Una exportación sin registro se ve y no pasa inadvertida (pregunta 3 de §12). | Regla informativa `increase(veridicus_report_exports_total{result="not_recorded"}[10m]) > 0`, con su `promtool test rules` (0 sin disparo, 1 con disparo). Cualquier `not_recorded` > 0 es un incidente que se revisa con el log `ERROR report.export_not_recorded`. Con el adaptador por defecto, `veridicus_report_exports_unaudited_total` y `access_log: not_configured` en `/readyz` lo muestran. Sin Alertmanager: la regla solo se ve en Prometheus y en el panel (Infrastructure Design de U2). |

## 4. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| MTTV | Media del arnés de nivel 2 (NFR7.1); en uso, `_sum / _count` de `veridicus_session_mttv_seconds` | < 600 s |
| Latencia de la consolidación | p95 de NFR3.2; en uso, `histogram_quantile(0.95, veridicus_report_consolidation_seconds)` | ≤ 1,5 s |
| Integridad de vistas previas y exportaciones | `result="integrity_mismatch"` de `previews_total` y `exports_total` | 0; cualquier valor es un incidente que se investiga con `verify_store` |
| Exportaciones registradas | `exports_total{result="not_recorded"}` | 0 |
| Huérfanos | `veridicus_report_orphans_removed_total` | Informativo: > 0 indica una consolidación interrumpida o un fallo de limpieza |
| Llenado del volumen | `used_bytes / quota_bytes` | < 0,8 |

## 5. Panel y trazas

- **Panel de Grafana (SHOULD, lo instala U2).** Consolidaciones y exportaciones por resultado, latencia
  p95, vistas previas por resultado, MTTV y uso del volumen frente a la cuota, junto a los paneles de U4 y
  U5.
- **Avisos.** Sin Alertmanager (Infrastructure Design de U2): ninguna regla notifica a alguien. Las
  reglas de NFR15.3 y NFR15.5 son informativas y se ven en el panel; una `integrity_mismatch` se ve en el
  panel y en el log `ERROR`.
- **Trazas distribuidas.** No aplican: U7 vive en un solo proceso; la correlación por `session_id`,
  `round_id`, `report_version_id` y `export_id` basta.
