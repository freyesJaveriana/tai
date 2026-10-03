# Diseño de monitoreo — U7 forensic-report

**Insumos.** Presupuestos p95 de `nfr-design/performance-design.md` (performance-design); regla de
métricas sin texto y lista blanca de logs de `nfr-design/security-design.md` (security-design); señales
para escalar de `nfr-design/scalability-design.md` (scalability-design); limpiezas, barrido, `/readyz` y
`verify_store` de `nfr-design/reliability-design.md` (reliability-design); eventos, métricas, SLI y
panel de `nfr-design/observability-design.md` (observability-design); dominios de falla de
`nfr-design/logical-components.md` (logical-components §2); flujos F1–F7 de
`functional-design/functional-spec.md` (functional-spec); módulo ForensicReport de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); requisitos NFR7, NFR15 y NFR10.10 de
`nfr-requirements/`; respuestas **P1 = A** (`Recreate`: el corte de cada despliegue es esperado),
**P2 = A** (el respaldo se comprueba con `SHA256SUMS` y `verify_store`) y **P3 = A** (*gauges* propios de
cuota y uso del volumen) de `infrastructure-design-questions.md`; Prometheus y Grafana de U2
(`platform/infrastructure-design/monitoring-design.md`) y paneles de U4, U5 y U6;
`infrastructure-specification.md` de esta carpeta.

U7 no trae su propio sistema de monitoreo: sus series salen por el puerto 8081 de la API, que ya recoge
el `ServiceMonitor` de U3, y sus logs por la salida estándar. Ninguna alerta despierta a nadie en el
MVP (U2, sin Alertmanager).

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| `veridicus_report_consolidations_total{result}` | API (`after_commit` o tras el *rollback*) | `result="storage_failed"` o `"unavailable"` > 0 en 15 min; los demás se muestran | NFR15.1, NFR10.15, NFR10.17: un fallo del volumen o un plazo vencido |
| p95 de `veridicus_report_consolidation_seconds` | API | > 1,5 s en 1 h | NFR3.2: por debajo del `lock_timeout` de 2 s que espera una decisión de U5 |
| `veridicus_report_downloads_total{result}` | API | `result="integrity_mismatch"` > 0 | NFR11.3: un archivo distinto del registrado es un incidente |
| `veridicus_report_files_cleaned_total{reason}` | API (limpieza síncrona o del hilo) | `reason="timeout"` > 3 en 1 h | NFR10.15, NFR10.17: un volumen lento |
| `veridicus_report_orphans_removed_total` | API (barrido al arrancar) | > 0 se muestra | NFR10.16: una consolidación interrumpida o una limpieza fallida |
| `veridicus_report_volume_used_bytes` / `veridicus_report_volume_quota_bytes` (P3 = A) | API, recorrido del directorio cada 60 s | > 0,8 durante 10 min | NFR15.3, NFR8.5: el llenado se ve antes de que `/readyz` saque la API |
| `veridicus_session_mttv_seconds` | API (versión 1) | Media > 600 s en 7 días | NFR15.4, NFR7.1: la meta de MTTV en uso real |
| `consolidations_total{result="outdated"}` | API | Se muestra | P1 = A de NFR Design: cuántas veces el analista volvió a confirmar el resumen |
| `/readyz?probe=kubernetes` de la API | Sonda de Kubernetes y `smoke.sh` | ≠ 200 fuera de un despliegue | NFR10.19, C16: configuración, directorio, espacio libre y barrido |
| Memoria de la API / su límite | cAdvisor (U2) | > 0,9 durante 5 min (regla de U2) | NFR8.1: margen de ≈ 47 % tras sumar U7 |

Las etiquetas son enums cerrados y no hay `session_id` ni `report_version_id` en ninguna serie
(NFR10.10); los dos *gauges* del volumen no llevan etiquetas.

## 2. Alertas

Todas son P3 (panel), como en U2. Cada regla lleva en su anotación el requisito y la acción por PR.

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusReportVolumeFilling` | `max(veridicus_report_volume_used_bytes) / max(veridicus_report_volume_quota_bytes) > 0.8` durante 10 min | info (P3) | Panel «Veridicus — reportes»; acción: ampliar `reports.size` por PR |
| `VeridicusReportIntegrityMismatch` | `increase(veridicus_report_downloads_total{result="integrity_mismatch"}[15m]) > 0` | warning (P3) | Panel; acción: `Job` `veridicus-verify-store` y restauración del respaldo (cicd-pipeline §5) |
| `VeridicusReportStorageFailures` | `increase(veridicus_report_consolidations_total{result=~"storage_failed\|unavailable"}[15m]) > 0` | warning (P3) | Panel |
| `VeridicusReportConsolidationSlow` | p95 de `veridicus_report_consolidation_seconds` > 1,5 s en 1 h | info (P3) | Panel; acción: medir por tramo (performance-design) |
| `VeridicusReportCleanupTimeouts` | `increase(veridicus_report_files_cleaned_total{reason="timeout"}[1h]) > 3` | info (P3) | Panel |
| `VeridicusPodNotReady` (U2) | Sin cambio; el corte de ≈ 20–40 s de un despliegue con `Recreate` queda por debajo de su ventana de 5 min | Las de U2 | Su panel |

El `ERROR` `report.cleanup_failed` no tiene alerta propia: se ve en el log y su efecto (huérfanos) en el
barrido del siguiente arranque y en `verify_store`.

**Prueba de la regla.** `promtool test rules deploy/prometheus/tests/volume.yaml` con las series de
`services/session-api/tests/forensic_report/fixtures/volume_series.yaml` (ahora con los dos *gauges*):
75 % sin alerta, 85 % durante 10 min con alerta, 85 % durante 9 min sin alerta.

## 3. SLI y SLO

Objetivos del MVP medidos en la máquina de desarrollo con `values-cpu.yaml`.

| SLI | SLO | Ventana de medición |
|---|---|---|
| MTTV medio (versión 1) | < 600 s | Arnés de nivel 2 sobre las 11 sesiones de cada corrida etiquetada; en uso, `_sum / _count` en 7 días |
| Latencia de consolidación (p95) | ≤ 1,5 s; máximo ≤ 2 s | Corrida `pytest -m perf` de cada PR; en uso, 1 h |
| Latencia de descarga (p95) | ≤ 250 ms (caso de 100 turnos); ≤ 500 ms (2 MiB) | Corrida `perf` de cada PR |
| Integridad de descargas | 0 `integrity_mismatch` | Continuo; y `verify_store` con código 0 tras cada restauración y antes de la sustentación |
| Versiones sin archivo íntegro | 0 versiones sin archivo, 0 SHA-256 distintos, 0 huérfanos > 300 s | Tras toda la suite de nivel 1 (NFR8.8) y en cada `Job` de verificación |
| Uso del volumen | < 80 % de la cuota | 10 min continuos |
| Corte por despliegue de la API | ≤ 60 s hasta `/readyz` en 200 | Cada despliegue, medido por `smoke.sh` |

## 4. Logs y trazas

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con el formateador de U3; la lista blanca suma `version_number`, `byte_size`, `sha256`, `file_name` (`<uuid>.md` o `.md.tmp`), `reason` y `turns_in_progress` (observability-design §6). Nunca texto del caso ni del reporte (NFR10.7) |
| Eventos | `session.finalized`, `report.consolidated`, `report.consolidation_rejected`, `report.downloaded`, `report.correction_opened`, `report.correction_discarded` (`INFO`); `report.orphan_removed`, `report.unexpected_file`, `report.file_cleaned`, *timeouts* (`WARNING`); `report.integrity_mismatch`, `report.cleanup_failed`, `report.storage_failed` (`ERROR`) |
| Eventos de operación | `export_store`, `import_store` y `verify_store` escriben solo conteos e identificadores por la salida estándar; el *script* de respaldo guarda esa salida junto al `tar` |
| Correlación | `request_id` + `session_id` + `report_version_id`; sin trazas distribuidas (un solo proceso) |
| Recolección | `kubectl logs` y la rotación del kubelet (10 MiB × 5) de U2; sin Loki |
| Control | Prueba centinela de nivel 1 (security-design §7): 0 coincidencias en logs, Problem Details y `/metrics` |

## 5. Paneles

Un JSON versionado en `deploy/veridicus/dashboards/veridicus-reports.json`, publicado como `ConfigMap`
con `grafana_dashboard: "1"` (mecanismo de U2, módulo 8):

| Fila del panel «Veridicus — reportes» | Contenido |
|---|---|
| Consolidación | Consolidaciones por `result`; p50/p95 de `consolidation_seconds`; vistas desactualizadas |
| Descarga e integridad | Descargas por `result`, con `integrity_mismatch` resaltado |
| Volumen | Uso frente a cuota (P3 = A) con la línea del 80 %; limpiezas por `reason`; huérfanos por arranque |
| MTTV | Histograma y media de `veridicus_session_mttv_seconds` con la línea de 600 s |
| Contexto | Enlaces a los paneles de revisión (U5) y de sesiones (U6) |
