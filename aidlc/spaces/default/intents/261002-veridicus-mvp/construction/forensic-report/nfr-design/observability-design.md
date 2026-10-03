# Diseño de observabilidad — U7 forensic-report

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; flujos F1–F7 de `functional-design/functional-spec.md`
(functional-spec); C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary);
respuestas P1 = A y P2 = A de `nfr-design-questions.md`; formateador de logs de U3 y paneles de U4 y U5.

## 1. Logs (NFR15.2)

- El formateador JSON de `libs/` con lista blanca (U3), una línea por evento con `timestamp`, `level`,
  `service`, `event`, `request_id` y solo identificadores, conteos, el SHA-256 y el `code`. Nunca
  transcripción, CoT, nota, reformulación, pasaje ni contenido del reporte.
- Campos de U7: `session_id`, `report_version_id`, `round_id`, `user_id`, `version_number`, `byte_size`,
  `sha256`, `code`, `file_name` (siempre `<uuid>.md` o `<uuid>.md.tmp`), `reason` (enum), `duration_ms`,
  `turns_in_progress`, `count`.

| Evento | Nivel | Campos | Cuándo |
|---|---|---|---|
| `session.finalized` | `INFO` | `session_id`, `user_id`, `turns_in_progress` | Tras el *commit* de F1 |
| `report.consolidated` | `INFO` | `report_version_id`, `session_id`, `round_id`, `version_number`, `byte_size`, `sha256`, `user_id`, `duration_ms` | `after_commit` |
| `report.consolidation_rejected` | `INFO` | `session_id`, `user_id`, `code` (incluido `report.view_outdated`, P1 = A) | Tras el *rollback* |
| `report.downloaded` | `INFO` | `report_version_id`, `user_id` | Tras enviar `200` |
| `report.correction_opened`, `report.correction_discarded` | `INFO` | `session_id`, `round_id`, `user_id` | Tras el *commit* |
| `report.orphan_removed`, `report.unexpected_file` | `WARNING` | `file_name` | Barrido |
| `report.file_cleaned` | `WARNING` | `file_name`, `reason`: `rollback` o `timeout` (P2 = A) | Limpieza síncrona o del hilo |
| *Timeout* | `WARNING` | `code` `system.unavailable`, `reason`: `db`, `lock`, `storage`, `deadline` | Al vencer |
| `report.integrity_mismatch` | `ERROR` | `report_version_id` | Descarga |
| `report.cleanup_failed`, `report.storage_failed` | `ERROR` | `file_name` o `report_version_id`, `code` | Volumen |

- **Correlación.** Sin trazas distribuidas (un solo proceso): `request_id` + `session_id` +
  `report_version_id` reconstruyen la historia.
- **Verificación.** Prueba de nivel 1 que reconstruye solo con logs la historia finalizada →
  consolidada → descargada → corregida → versión 2, y la prueba de la cadena centinela
  (security-design §7) con 0 coincidencias.

## 2. Métricas (NFR15.1, NFR15.4)

`prometheus-client` en `/metrics` del puerto interno de la API; etiquetas solo de enum.

| Métrica | Tipo | Etiquetas | Dónde se actualiza |
|---|---|---|---|
| `veridicus_report_consolidations_total` | counter | `result`: `created`, `conflict`, `blocked`, `outdated`, `forbidden_vocabulary`, `storage_failed`, `unavailable` | `created` en `after_commit`; los demás tras el *rollback*. `outdated` es `report.view_outdated` (P1 = A) |
| `veridicus_report_consolidation_seconds` | histogram (0,1 · 0,25 · 0,5 · 1 · 1,5 · 2 · 5 · 10 s) | — | De la guardia al *commit*, solo `created` |
| `veridicus_report_downloads_total` | counter | `result`: `ok`, `integrity_mismatch`, `not_consolidated` | Al responder |
| `veridicus_report_orphans_removed_total` | counter | — | Barrido |
| `veridicus_report_files_cleaned_total` | counter | `reason`: `rollback`, `timeout` | Limpieza síncrona o del hilo (P2 = A) |
| `veridicus_session_mttv_seconds` | histogram (60 · 120 · 300 · 600 · 900 · 1 800 · 3 600 s) | — | `after_commit` de la versión 1, con `domain/mttv.py` |

- Prueba de nivel 1 que recorre cada camino y comprueba el incremento exacto de cada serie; prueba de
  nivel 0 que valida cada etiqueta contra su enum (NFR10.10).
- **MTTV (NFR15.4).** Reloj en *t* al finalizar y *t* + 420 s al consolidar → una observación de 420;
  la versión 2 no observa.

## 3. Volumen y alertas (NFR15.3)

- Regla de Prometheus de U2 (SHOULD, por PR): `kubelet_volume_stats_used_bytes /
  kubelet_volume_stats_capacity_bytes > 0.8` sobre `veridicus-reports` durante 10 min → alerta
  informativa. U7 entrega las series de ejemplo en
  `services/session-api/tests/forensic_report/fixtures/volume_series.yaml`; `promtool test rules
  deploy/prometheus/tests/volume.yaml`: 75 % sin alerta, 85 % con alerta.
- `/readyz` en `503` bajo 50 MiB libres (reliability-design §4) cubre el caso en que la alerta no se
  atendió.
- Ninguna alerta despierta a alguien en el MVP.

## 4. SLI y objetivos del MVP

| SLI | Cálculo | Objetivo |
|---|---|---|
| MTTV | Arnés de nivel 2; en uso `_sum / _count` de `veridicus_session_mttv_seconds` | < 600 s |
| Latencia de consolidación | `histogram_quantile(0.95, …consolidation_seconds_bucket)` | ≤ 1,5 s |
| Integridad de descargas | `veridicus_report_downloads_total{result="integrity_mismatch"}` | 0; > 0 es un incidente que se investiga con `verify_store` |
| Huérfanos y limpiezas | `orphans_removed_total` y `files_cleaned_total{reason="timeout"}` | Informativos; un crecimiento sostenido indica un volumen lento |
| Vistas desactualizadas | `consolidations_total{result="outdated"}` | Informativo: cuántas veces el analista tuvo que revisar de nuevo el resumen |

## 5. Panel

Panel de Grafana (SHOULD, lo instala U2) junto a los de U4 y U5: consolidaciones por resultado,
latencia p95, descargas por resultado, MTTV, limpiezas por motivo y uso del volumen.

## 6. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `forensic-report/nfr-requirements/observability-requirements.md` (NFR15.1) | `veridicus_report_consolidations_total` admite `result="outdated"`; nueva serie `veridicus_report_files_cleaned_total{reason}` | P1 = A, P2 = A |
| `inception/contract-design/contract-summary.md` (C15) | Las dos precisiones anteriores entran en el mismo PR de U1 que las métricas de NFR15.1 | P1 = A, P2 = A |
| `identity-access/nfr-design/observability-design.md` (U3) | La lista blanca del formateador admite `version_number`, `byte_size`, `sha256`, `file_name`, `reason` y `turns_in_progress` (identificadores, conteos y enums); `report_version_id` y `round_id` ya los pidió U5 | NFR15.2 |
