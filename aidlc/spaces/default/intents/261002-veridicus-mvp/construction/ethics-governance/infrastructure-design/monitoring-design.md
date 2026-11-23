# Diseño de monitoreo — U13 ethics-governance

**Revisión 1 (2026-11-23): primera pasada.** Todo es nuevo.

**Insumos.** Líneas de log, salida del `Job`, métricas y salud de `nfr-design/observability-design.md`
(observability-design §1–§6); presupuestos de `nfr-design/performance-design.md` (performance-design §1, §3,
§4, §5); señales que se degradan primero de `nfr-design/scalability-design.md` (scalability-design §3, §8);
plazos y degradación de `nfr-design/reliability-design.md` (reliability-design §1, §2, §4, §7); la nota fuera
de los logs de `nfr-design/security-design.md` (security-design §4, §8.4); radio de impacto de
`nfr-design/logical-components.md` (logical-components §3); F7, F8 y F10 de
`functional-design/functional-spec.md` (functional-spec); EthicsGovernance en
`inception/domain-design/components.md` (components); C15, C16 y C23 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de U2 y monitoreo de
`session-api` de U3; `infrastructure-specification.md` de esta carpeta.

U13 no publica métricas propias (`ethics-governance-no-metrics` prohíbe `prometheus_client` en su módulo) y
C15 no cambia. Se observa con cinco fuentes que ya existen o que son suyas sin infraestructura nueva: las
líneas de log de las rutas, la salida JSON del `Job`, las actas y el registro leídos con el comando de
consulta, la métrica `veridicus_access_log_failures_total` de U3 y la salud de `session-api` (C16). Usa la
pila de U2: Prometheus y Grafana desde el módulo 8, sin Alertmanager, sin Loki y sin trazas; antes del módulo
8, `kubectl logs` y `scripts/smoke.sh`.

## 1. Métricas y KPI

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_access_log_failures_total{resource_type}` | `session-api` `:8081/metrics` (métrica de U3) | > 0 en 15 min (regla `VeridicusAccessLogFailures` de U3) | Una lectura respondió sin dejar registro (E14); la exportación nunca sale sin registro (`503 report.export_not_recorded`) |
| `session-api` lista | kube-state-metrics | No lista durante 2 min (regla de U3) | Con las reglas de uso rotas o sin `INSERT` en `access_log_entry`, el pod nuevo nunca abre el puerto (reliability-design §3) |
| `veridicus_problem_responses_total{status="500"}` | Métrica genérica de U3 | > 0 en 15 min (regla de U3) | Un fallo del código de U13 deja `500` `system.internal` y 0 filas |
| Código de salida y `retention.summary` del `Job` | `kubectl get job` y `kubectl logs job/veridicus-retention` | Código ≠ 0, o algún `outcome: failed` | 1: alguna sesión no se borró; 2: configuración o argumentos; 3: otra ejecución tenía el bloqueo. El humano lo lee al terminar, porque él lo lanzó |
| Duración del `Job` | `duration_ms` del resumen y estado `DeadlineExceeded` del `Job` | > 50 % de `activeDeadlineSeconds` (1 800 s) | Disparador para medir de nuevo NFR3.11 y ajustar el plazo por PR (scalability-design §8; IDS-U13-13) |
| Tamaño de las tablas que no se borran | `pg_total_relation_size` de `access_log_entry` y `retention_act`, por el comando de consulta o una consulta de solo lectura en la revisión de B13 | > 150 MiB, o más de 1 000 000 de filas en el registro | Disparador de la política de archivo y de revisar el PVC (scalability-design §3 y §8; IDS-U13-10) |

Ninguna serie lleva `session_id`, la nota ni un texto de turno. Un contador futuro (reportes, borrados)
entraría en `contracts/metrics/ethics-governance.v1.yaml` con etiquetas de la lista cerrada de U1
(observability-design §4); esta revisión no lo crea.

## 2. Alertas

U13 no crea reglas nuevas. Las que la cubren ya existen en `charts/monitoring-rules/` de U2, con su prueba
`promtool`, solo con `monitoring.enabled: true`, y ninguna notifica a nadie (`project.md`: sin Alertmanager).

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusAccessLogFailures` (de U3) | `increase(veridicus_access_log_failures_total[15m]) > 0` | warning (P3) | Panel «Veridicus — acceso»; buscar líneas `access_log.record_failed` por `request_id` |
| `VeridicusSessionApiNotReady` (de U3) | Pod de `veridicus-session-api` no listo durante 2 min | critical (P3) | Panel «Veridicus — plataforma»; con un despliegue reciente, buscar `config.invalid_usage_rules` o `config.access_log_unavailable` |
| `VeridicusInternalErrors` (de U3) | `increase(veridicus_problem_responses_total{status="500"}[15m]) > 0` | warning (P3) | Panel «Veridicus — acceso» |

**Por qué el `Job` no tiene alerta.** Lo lanza el humano y vive minutos: no se raspa, y su resultado lo lee
quien lo lanzó, en la salida y en las actas (observability-design §4). Una regla sobre `kube_job_status_failed`
avisaría a la misma persona, más tarde y sin causa.

## 3. SLIs / SLOs

Son objetivos de verificación del MVP (pruebas `perf` de nivel 1 y Playwright de nivel 3), no SLO con ventana
de producción: U13 no tiene objetivo de disponibilidad propio y está disponible cuando lo están
`session-api` y PostgreSQL (reliability-design, introducción).

| SLI | SLO target | Measurement window |
|---|---|---|
| p95 de `POST /problem-reports` con la sesión máxima y la nota máxima | ≤ 500 ms (NFR3.1) | 50 repeticiones de la marca `perf` |
| Comparación local en la consola | ≤ 30 ms típica; ≤ 150 ms máxima; 0 tareas > 200 ms (NFR3.2) | Playwright con `performance.now()` y `longtask` |
| Estado del reconocimiento en `/auth/me` | ≤ 20 ms sobre el p95 de `/auth/me` con 1 000 filas (NFR3.3) | Marca `perf` |
| p95 de `POST /acknowledgements` y de la `PATCH` del plazo | ≤ 150 ms y ≤ 200 ms (NFR3.4) | Ídem |
| p95 de `AccessLog.record` con 150 000 filas | ≤ 20 ms (NFR3.5) | Ídem |
| Borrado de la sesión máxima | p95 ≤ 10 s; pico ≤ 256 MiB (NFR3.6) | Marca `perf` con `psutil` |
| Comando de consulta | ≤ 2 s con `--session`; ≤ 5 s con `--limit 10000` sobre 150 000 filas (NFR3.7) | Ídem |
| Avisos sin bloqueo | ≤ 100 ms con el recordatorio y el panel abiertos (NFR3.8) | Playwright |
| Acta de la sesión máxima | ≤ 1 MiB (≈ 0,8 MiB estimado) (NFR3.9) | Nivel 1 con `pg_column_size` |
| Simulación y escala del borrado | 500 sesiones (200 vencidas) en ≤ 60 s; 50 típicas en ≤ 5 min (NFR3.6) | Marca `perf` |
| Ejecución con 500 sesiones típicas frente a `activeDeadlineSeconds` | 2 × la medición ≤ el plazo del manifiesto (NFR3.11) | Marca `perf`; la cifra entra en el PR de B13 (IDS-U13-13) |
| Sondeo de U4 durante el `Job` | + ≤ 200 ms en el p95 (NFR3.12) | Nivel 1 con barrera, 20 repeticiones |

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Líneas de las rutas | `ethics.acknowledged`, `ethics.problem_reported`, `retention.reduced` y `access_log.record_failed`, con el formateador único y la lista blanca de U3 ampliada por NFRD-U13-11; `INFO`, salvo el fallo del registro (`WARNING`) |
| Línea de arranque | `ethics.startup` con `usage_rules_version`, `usage_rules_sha256` y `access_log_adapter: ethics_governance`; ante un fallo, `ERROR` `config.invalid_usage_rules` o `config.access_log_unavailable`, con el archivo o la tabla y la regla, nunca el contenido |
| Salida del `Job` | Una línea `retention.candidate` por candidata y un `retention.summary`, en JSON por la salida estándar del pod, con el conjunto cerrado de claves de observability-design §3. Queda en el log del pod hasta que el humano borra el `Job` (sin `ttlSecondsAfterFinished`) |
| Sin contenido | `note` no está en la lista blanca; `repr=False`, `hide_parameters=True`, acceso de Uvicorn apagado. En PostgreSQL, `log_error_verbosity: terse` y los parámetros de log a 0 (U2 §2.1). La captura de logs con el *canary* de U2 (`deploy-level1.yml`) cubre también `session-api` |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-session-api -c session-api` y `kubectl logs -n veridicus job/veridicus-retention` (o `job/veridicus-retention-dry-run`), de solo lectura; rotación del kubelet (10 MiB × 5) |
| Registro y actas | No son logs: viven en `access_log_entry` y `retention_act`, nunca se borran y se leen con el comando de consulta (§5 de la especificación) |
| Qué responde | Quién abrió qué y cuándo (`access-log`); qué se borró, por qué regla y cuándo (`retention-acts` y la salida); qué reportaron los analistas (`problem-reports`); con qué reglas arrancó la API (`ethics.startup`) |
| Retención de logs | Sin retención especial: las líneas solo llevan IDs, enums, conteos y hashes |
| Trazas | Sin trazas distribuidas, como el resto de `session-api` (U3); el `request_id` correlaciona la consola con su línea y `job_run_id` las líneas del `Job` con sus actas |

## 5. Paneles

| Panel | Contenido de U13 |
|---|---|
| Veridicus — acceso (U3) | `veridicus_access_log_failures_total` por `resource_type` y las respuestas `500`, que ya incluyen las rutas de U13 |
| Veridicus — plataforma (U2) | Estado de `session-api`; la memoria de la API no cambia por U13 |

U13 no añade un panel propio: sin métricas nuevas, una fila más solo repetiría las de U3 y U2, y el `Job` no
se raspa.
