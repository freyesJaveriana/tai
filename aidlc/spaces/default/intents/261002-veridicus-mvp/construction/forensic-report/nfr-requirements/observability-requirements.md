# Requisitos de observabilidad — U7 forensic-report

**Insumos.** Flujos F1–F7 de `functional-design/functional-spec.md` (functional-spec) y reglas BR4.3,
BR5.1, BR7.1 y BR7.2 de `functional-design/rules.md` (rules); NFR7, NFR10 y NFR15 de
`inception/requirements-analysis/requirements.md` (requirements); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); `nfr-requirements-questions.md`
(sin preguntas nuevas).

## 1. Métricas (Prometheus, en `/metrics` del puerto interno de la API de `session-api`)

| ID | Métrica | Tipo | Etiquetas | Cuándo cambia |
|---|---|---|---|---|
| NFR15.1 | `veridicus_report_consolidations_total` | counter | `result`: `created`, `conflict`, `blocked`, `forbidden_vocabulary`, `storage_failed`, `unavailable` | +1 por cada petición de consolidar que llega a ForensicReport; `created` solo después del *commit*. `blocked` agrupa los `409` de BR2.2–BR2.4 |
| NFR15.1 | `veridicus_report_consolidation_seconds` | histogram | ninguna; *buckets* 0,1 · 0,25 · 0,5 · 1 · 1,5 · 2 · 5 · 10 s | Duración de cada consolidación `created` (de la guardia al *commit*) |
| NFR15.1 | `veridicus_report_downloads_total` | counter | `result`: `ok`, `integrity_mismatch`, `not_consolidated` | +1 por descarga respondida |
| NFR15.1 | `veridicus_report_orphans_removed_total` | counter | ninguna | +1 por archivo borrado en el barrido (NFR10.16) |
| NFR15.4 | `veridicus_session_mttv_seconds` | histogram | ninguna; *buckets* 60 · 120 · 300 · 600 · 900 · 1 800 · 3 600 s | Una observación por sesión al crear su **versión 1**, con `mttv_seconds` de `domain/mttv.py` (NFR7.3); las correcciones no observan |

Las etiquetas solo llevan valores de enum (NFR10.10); no hay `session_id` ni `report_version_id`. Las
métricas se añaden a C15 por un PR de U1, como las de U3, U4 y U5 (precisión en
`security-requirements.md` §6). Prueba de nivel 1 que recorre cada camino y comprueba el incremento
exacto de cada serie.

## 2. Logs

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.2 | Cada hecho de U7 deja un evento estructurado sin texto. | JSON en una línea con `timestamp`, `level`, `service`, `event` y solo los campos de NFR10.7. Eventos `INFO`: `session.finalized` (`session_id`, `user_id`, `turns_in_progress`), `report.consolidated` (`report_version_id`, `session_id`, `round_id`, `version_number`, `byte_size`, `sha256`, `user_id`, `duration_ms`), `report.consolidation_rejected` (`session_id`, `user_id`, `code`), `report.downloaded` (`report_version_id`, `user_id`), `report.correction_opened` y `report.correction_discarded` (`session_id`, `round_id`, `user_id`). `WARNING`: `report.orphan_removed`, `report.unexpected_file`, `report.file_cleaned` y cada *timeout* (`code`). `ERROR`: `report.integrity_mismatch` (solo `report_version_id`), `report.cleanup_failed` y `report.storage_failed`. Nunca transcripción, CoT, nota, reformulación, pasaje ni contenido del reporte. Prueba de nivel 1 que reconstruye la historia de una sesión (finalizada, consolidada, descargada, corregida, versión 2) solo con sus logs. |

## 3. Volumen y alertas

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR15.3 | El llenado del volumen se ve antes de que falle. | Regla de Prometheus de U2 (SHOULD, entra por PR): `kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.8` sobre el PVC `veridicus-reports` durante 10 min → alerta informativa. `promtool test rules` con dos series de ejemplo (75 % sin alerta, 85 % con alerta) que entrega U7 en `services/session-api/tests/forensic_report/fixtures/volume_series.yaml`. Además `/readyz` pasa a `503` bajo 50 MiB libres (NFR10.19). |
| NFR15.4 | El MTTV real se puede ver fuera del arnés. | `veridicus_session_mttv_seconds` (§1) permite consultar en Grafana `histogram_quantile` y la media (`_sum / _count`) del MTTV de las sesiones consolidadas; el valor de aceptación de NFR7 sigue siendo el del arnés (NFR7.1), que usa la misma función pura. Prueba de nivel 1: finalizar con el reloj en *t*, consolidar en *t* + 420 s → una observación de 420 en el histograma; consolidar la versión 2 no añade otra. |

## 4. Indicadores (SLI) y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| MTTV | Media del arnés de nivel 2 (NFR7.1); en uso, `_sum / _count` de `veridicus_session_mttv_seconds` | < 600 s |
| Latencia de la consolidación | p95 de la prueba `perf` de NFR3.2; en uso, `histogram_quantile(0.95, veridicus_report_consolidation_seconds)` | ≤ 1,5 s |
| Integridad de las descargas | `veridicus_report_downloads_total{result="integrity_mismatch"}` | 0; cualquier valor > 0 es un incidente que se investiga con NFR10.20 |
| Huérfanos por arranque | `veridicus_report_orphans_removed_total` | Informativo: un valor > 0 indica una consolidación interrumpida o un fallo de limpieza |

## 5. Panel y trazas

- **Panel de Grafana (SHOULD, lo instala U2).** Consolidaciones por resultado, latencia p95, descargas
  por resultado, MTTV y uso del volumen, junto a los paneles de U4 y U5.
- **Alertas.** Ninguna despierta a alguien en el MVP; la de volumen (NFR15.3) es informativa. Una
  `integrity_mismatch` se ve en el panel y en el log `ERROR`.
- **Trazas distribuidas.** No aplican: U7 vive en un solo proceso; la correlación por `session_id`,
  `round_id` y `report_version_id` basta.
