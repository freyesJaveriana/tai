# Diseño de monitoreo — U7 forensic-report (módulo ReviewReport)

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design revisión 2.**
Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.**
  - Las métricas son internas de `session-api` y no van a C15 (NFR-U7-04).
  - `downloads_total` pasa a `previews_total`; `storage_failed` pasa a `internal`.
  - Entran las exportaciones (`exports_total`, `exports_unaudited_total`), la regla `not_recorded` y los
    eventos de la purga y de `commit_unknown`.
  - Reglas y panel pasan al subchart `monitoring-rules` de U2 (IDS-U7-13).
  - El corte por despliegue se mide con `scripts/measure-cutover.sh` (IDS-U7-11).
- **Numeración.** §1–§5 conservan su tema. La nueva §6 lista lo retirado.

**Insumos.**
- Presupuestos p95 de `nfr-design/performance-design.md` (performance-design).
- Regla de métricas sin texto y lista blanca de logs de `nfr-design/security-design.md` (security-design §7).
- Señales para escalar de `nfr-design/scalability-design.md` (scalability-design §5).
- Limpiezas, barrido, `/readyz`, `verify_store`, exportación y purga de `nfr-design/reliability-design.md`
  (reliability-design).
- Eventos, métricas, reglas, SLI y panel de `nfr-design/observability-design.md` (observability-design).
- Dominios de falla de `nfr-design/logical-components.md` (logical-components §2).
- Flujos F1–F10 de `functional-design/functional-spec.md` (functional-spec).
- ReviewReport de `inception/domain-design/components.md` (components).
- C16 y C23 de `inception/contract-design/contract-summary.md` (contract-summary).
- Pila común de U2 (`platform/infrastructure-design/monitoring-design.md`) y `ServiceMonitor` de U3.
- `infrastructure-specification.md` de esta carpeta.

U7 usa la pila de U2: Prometheus y Grafana desde el módulo 8 (SHOULD), `PrometheusRule` **sin
Alertmanager**, sin Loki y sin trazas, y logs JSON por la salida estándar con la rotación del kubelet. No añade
exportadores ni `ServiceMonitor`: sus series salen por el puerto `metrics` 8081 de la API, que raspa el
`ServiceMonitor` de `veridicus-session-api` de U3 cada 30 s. Las reglas y la fila del panel solo se renderizan
con `monitoring.enabled: true`, porque antes del módulo 8 el CRD no existe. Ninguna alerta despierta a nadie
en el MVP.

## 1. Métricas y KPI

Todas internas de `session-api` (NFR-U7-04). Las etiquetas son enums cerrados validados en nivel 0, y ninguna
serie lleva `session_id`, `report_version_id`, `export_id` ni `user_id` (NFR10.10). Los dos *gauges* del
volumen no llevan etiquetas.

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_report_consolidations_total{result}` | API (`created` en `after_commit`; el resto tras el *rollback*) | `result=~"internal\|unavailable"` > 0 en 15 min; los demás se muestran | NFR15.1, NFR10.15, NFR10.17: un fallo del volumen o un plazo vencido |
| p95 de `veridicus_report_consolidation_seconds` | API | > 1,5 s en 1 h | NFR3.2: por debajo del `lock_timeout` de 2 s con el que espera una decisión |
| `veridicus_report_previews_total{result}` | API | `result="integrity_mismatch"` > 0 | NFR11.3: un archivo distinto del registrado es un incidente |
| `veridicus_report_exports_total{result}` | API | `result="not_recorded"` > 0 en 10 min; `integrity_mismatch` > 0 | NFR15.5, NFR11.7: ninguna copia sale sin registro |
| `veridicus_report_exports_unaudited_total` | API | Se muestra; crece mientras C23 use el adaptador por defecto | NFR15.5: exportaciones sin el registro real de U13 |
| `veridicus_report_files_cleaned_total{reason}` | API (limpieza tras el *rollback* o del hilo) | `reason="timeout"` > 3 en 1 h | NFR10.15, NFR10.17: un volumen lento |
| `veridicus_report_orphans_removed_total` | API (barrido al arrancar y cada 60 s) | > 0 se muestra | NFR10.16: una limpieza fallida o un `COMMIT` desconocido (DS4) |
| `veridicus_report_volume_used_bytes` / `veridicus_report_volume_quota_bytes` | API, cada 60 s | > 0,8 durante 10 min | NFR15.3, NFR8.5: el llenado se ve antes de que `/readyz` saque la API (IDS-U7-12) |
| `veridicus_session_mttv_seconds` | API (versión 1 de una sesión guiada) | Media > 600 s en 7 días | NFR15.4, NFR7.1 |
| `consolidations_total{result="outdated"}` | API | Se muestra | Cuántas veces el analista tuvo que revisar de nuevo el resumen (P1 = A de NFR Design) |
| `/readyz` de la API | `readinessProbe` y `smoke.sh` | ≠ 200 fuera de un despliegue | NFR10.19, C16: configuración, directorio, espacio, cuota, barrido y volumen colgado |
| Corte por despliegue | `scripts/measure-cutover.sh` | > 90 s | NFR8.6: costo de `Recreate` (IDS-U7-11) |
| Memoria de la API frente a su límite | cAdvisor (U2) | > 0,9 durante 5 min (regla de U2) | NFR8.1: ≈ 942 MiB de 1 152 MiB con el `exec` (IDS-U7-09) |

El `Job` de retención no publica métricas: su resultado son el recibo y el log `report.purged`.

## 2. Alertas

Reglas informativas en el subchart `monitoring-rules` de U2, cada una con su anotación `runbook` y su prueba
`promtool test rules deploy/veridicus/tests/report-rules.yaml`, con un caso que dispara y otro que no. Todas son
P3 (panel): nadie recibe una notificación y ninguna cambia un estado.

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusReportVolumeFilling` | `max(veridicus_report_volume_used_bytes) / max(veridicus_report_volume_quota_bytes) > 0.8` durante 10 min | info (P3) | Panel «Veridicus — reportes»; acción: acortar la retención (U13) o ampliar `reports.size` por PR |
| `VeridicusReportExportNotRecorded` | `increase(veridicus_report_exports_total{result="not_recorded"}[10m]) > 0` | warning (P3) | Panel; el runbook pide revisar el adaptador de C23 de U13 |
| `VeridicusReportIntegrityMismatch` | `increase(veridicus_report_previews_total{result="integrity_mismatch"}[15m]) + increase(veridicus_report_exports_total{result="integrity_mismatch"}[15m]) > 0` | warning (P3) | Panel; acción: `verify_store` y restauración del respaldo (`cicd-pipeline.md` §4) |
| `VeridicusReportConsolidationFailures` | `increase(veridicus_report_consolidations_total{result=~"internal\|unavailable"}[15m]) > 0` | warning (P3) | Panel |
| `VeridicusReportConsolidationSlow` | p95 de `veridicus_report_consolidation_seconds` > 1,5 s en 1 h | info (P3) | Panel; acción: medir por tramo (performance-design §1) |
| `VeridicusReportCleanupTimeouts` | `increase(veridicus_report_files_cleaned_total{reason="timeout"}[1h]) > 3` | info (P3) | Panel |
| Reglas de U2 y U3 (pod no listo, memoria) | Sin cambio. Con `Recreate`, el corte de un despliegue (≤ 90 s) queda por debajo de la ventana de 5 min de U2 | Las suyas | Sus paneles |

Las dos primeras son las reglas que pide observability-design §3. Las demás hacen visibles en el panel los
umbrales de §1. `report.cleanup_failed` no tiene alerta propia: se ve en el log, y su efecto, en el barrido
siguiente y en `verify_store`.

**Prueba de las reglas.** Series de ejemplo en `services/session-api/tests/review_report/fixtures/volume_series.yaml`:
- volumen al 75 %, sin alerta; al 85 % durante 10 min, con alerta; al 85 % durante 9 min, sin alerta;
- `not_recorded`: 0 sin disparo y 1 con disparo;
- `integrity_mismatch`: 0 sin disparo y 1 en vista previa con disparo.

## 3. SLIs / SLOs

Objetivos de verificación del MVP en el perfil CPU, no SLO con ventana de producción. Las pruebas `perf`
corren en el *runner* `ubuntu-24.04` de 4 vCPU (IDS-U3-09): una sola corrida, sin reintentos. Una falla
sospechosa de inestable se pone en cuarentena con un *issue* enlazado y el umbral nunca se baja.

| SLI | SLO target | Measurement window |
|---|---|---|
| MTTV medio (versión 1, sesiones guiadas) | < 600 s | Arnés de nivel 2 sobre el conjunto sintético (40 transcripciones hoy); en uso, `_sum / _count` en 7 días |
| Latencia de la consolidación | p95 ≤ 1,5 s y máximo ≤ 2 s (100 turnos); p95 ≤ 6 s y máximo ≤ 8 s (caso máximo) | `pytest -m perf` de cada PR; en uso, 1 h |
| Latencia de la vista previa | p95 ≤ 250 ms (100 turnos); ≤ 500 ms (8 MiB) | `perf` de cada PR |
| Latencia de la exportación | p95 ≤ 500 ms (100 turnos); ≤ 2 000 ms (8 MiB) | `perf` de cada PR |
| Purga | p95 ≤ 2 s con 10 versiones y 100 exportaciones | `perf` de cada PR, con `veridicus_retention` |
| Integridad | 0 `integrity_mismatch` | Continuo; `verify_store` con código 0 tras cada restauración y antes de la sustentación |
| Exportaciones registradas | 0 `not_recorded` | Continuo |
| Versiones sin archivo íntegro | 0 versiones sin archivo, 0 SHA-256 distintos, 0 huérfanos tras el barrido a +301 s | Tras toda la suite de nivel 1 (NFR8.8) y en cada `verify_store` |
| Uso del volumen | < 80 % de la cuota | 10 min continuos |
| Corte por despliegue de la API | ≤ 90 s | Cada despliegue, con `scripts/measure-cutover.sh` (IDS-U7-11) |
| Respaldo y restauración | RTO ≤ 30 min hasta `verify_store` con 0 | Ensayo previo a la sustentación |

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con el formateador único de `libs/` (U3). La lista blanca suma `export_id`, `export_sha256`, `was_current`, `version_number`, `byte_size`, `sha256`, `file_name` (`<uuid>.md` o `.md.tmp`), `reason` y `runs_in_progress` (petición NFRD-U7-10 a U3). Nunca texto del caso, del reporte ni el nombre de usuario de la marca (NFR10.7) |
| Eventos `INFO` | `session.finalized`, `report.consolidated`, `report.consolidation_rejected`, `report.previewed`, `report.exported`, `report.correction_opened`, `report.correction_discarded`, `report.purged` (este, en el `Job`) |
| Eventos `WARNING` | `report.orphan_removed`, `report.unexpected_file`, `report.file_cleaned`, `report.commit_unknown`, `report.access_log_not_configured`, `report.purge_file_missing`, *timeouts* con `reason` |
| Eventos `ERROR` | `report.integrity_mismatch`, `report.cleanup_failed`, `report.export_not_recorded`, `system.internal` del volumen |
| Comandos de operación | `verify_store`, `export_store` e `import_store` escriben solo conteos e IDs por la salida estándar (la de `export_store`, por la de error, porque la estándar lleva el `tar`). El runbook guarda esa salida junto al respaldo |
| Correlación | `request_id`, `session_id`, `round_id`, `report_version_id` y `export_id`; sin trazas distribuidas (un solo proceso) |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-session-api -c session-api` y los del `Job` de retención (solo lectura); rotación del kubelet; sin Loki (U2) |
| Control | Prueba centinela de nivel 1 (security-design §7): 0 coincidencias en logs, Problem Details y `/metrics`, también tras `purge_session` y el barrido |

## 5. Paneles

| Panel | Contenido de U7 |
|---|---|
| Veridicus — reportes (fila de U7 en el chart de U2) | Consolidaciones y exportaciones por `result`; p50/p95 de `consolidation_seconds`; vistas previas por `result`, con `integrity_mismatch` resaltado; exportaciones sin auditar; uso del volumen frente a la cuota, con la línea del 80 %; limpiezas por `reason`; huérfanos; MTTV con la línea de 600 s |
| Veridicus — revisión (U5) y sesiones (U6) | Enlaces |
| Veridicus — plataforma (U2) | CPU y memoria de la API frente a su límite |

El original vive en `services/session-api/observability/review-report.json`. Se empaqueta en
`charts/monitoring-rules/dashboards/` de U2 con el mismo SHA-256, comprobado por `check-config-copy.sh`
(petición IDS-U7-13). Solo muestra contadores, histogramas y *gauges* con etiquetas de enum.

## 6. Retirado de la revisión 1

Salen:
- las métricas `veridicus_report_downloads_total` (la sustituye `previews_total`) y el valor
  `result="storage_failed"` (pasa a `internal`);
- las alertas `VeridicusReportStorageFailures` (la sustituye `VeridicusReportConsolidationFailures`) y la
  versión anterior de `VeridicusReportIntegrityMismatch`, que solo miraba descargas;
- el evento `report.storage_failed` y el evento `report.downloaded`;
- la regla en `deploy/prometheus/` y su prueba `deploy/prometheus/tests/volume.yaml`;
- el JSON `deploy/veridicus/dashboards/veridicus-reports.json` como archivo propio del chart;
- el `Job` de verificación como fuente de conteos;
- el SLI de corte medido por `smoke.sh`, con el umbral de 60 s.
