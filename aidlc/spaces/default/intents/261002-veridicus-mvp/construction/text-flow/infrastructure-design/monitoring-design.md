# Diseño de monitoreo — U4 text-flow

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen las métricas del juez, de los *embeddings*, del umbral, de la indexación y de los
  turnos (`veridicus_turn_*`). Entran las métricas de corrida de `contracts/metrics/text-flow.v1.yaml`
  (NFRD-U4-08), las reglas informativas de observability-design §4 y el evento del incidente (NFR15.5).
- **Numeración.** §1–§6 conservan su tema; §5 (trazas) sigue sin trazas distribuidas.

**Insumos.** Logs, métricas, SLI, panel y reglas de `nfr-design/observability-design.md`
(observability-design §1–§4); presupuestos del camino crítico de `nfr-design/performance-design.md`
(performance-design §1, §7, §8); señales de escalado de `nfr-design/scalability-design.md`
(scalability-design §4); plazos, salud y publicación fallida de `nfr-design/reliability-design.md`
(reliability-design §3, §4, §6, §10); lista blanca de logs y *canary* de `nfr-design/security-design.md`
(security-design §6); radio de impacto de `nfr-design/logical-components.md` (logical-components §2);
estados de sesión y corrida de `functional-design/functional-spec.md` (functional-spec §3); procesos de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de
`platform/infrastructure-design/monitoring-design.md` (U2); `infrastructure-specification.md` de esta
carpeta.

U4 usa la pila de U2: Prometheus y Grafana desde el módulo 8, sin Alertmanager, sin Loki y sin trazas; logs
JSON por salida estándar con la rotación del kubelet. Añade un `ServiceMonitor` para el trabajador y otro
para `semantic-agent` sobre el puerto `metrics` 8081, con raspado cada 30 s; la API ya la raspa el
`ServiceMonitor` `veridicus-session-api` de U3 en el mismo puerto. Los `ServiceMonitor`, la
`PrometheusRule` y la fila del panel de U4 solo se renderizan con `monitoring.enabled: true`, porque antes
del módulo 8 el CRD no existe (IDS-U4-14).

## 1. Métricas y KPI

Todas declaradas en `contracts/metrics/text-flow.v1.yaml`; una prueba de nivel 0 falla ante una métrica, una
etiqueta o un valor de etiqueta fuera del archivo (observability-design §2).

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_run_queue_depth` | Trabajador (`RunSupervisor`, cada 15 s) | > 20 durante 10 min | scalability-design §4: con más corridas por delante el plazo empieza a acercarse a `run_queue_wait_max_s` |
| p95 de `veridicus_run_queue_wait_seconds` por `mode` | Trabajador, de `enqueued_at` a `RunStarted` | > 3 600 s en 1 h | Señal de escalado (NFR8.10); NFR3.5 |
| `veridicus_runs_total{outcome, mode, error_code}` | Trabajador, en `after_commit` | Cualquier `error_code="analysis.system"` en 15 min | Plazo vencido, mensaje a fallidos o publicación fallida (reliability-design §9, §10) |
| `veridicus_runs_total{error_code="analysis.anonymizer_unavailable"}` | Trabajador | > 0 en 15 min | El proxy de U10 no responde o rechaza (NFRD-U4-07) |
| p95 de `veridicus_ingest_duration_seconds` | Trabajador | > 5 s en 1 h | Presupuesto de la ingesta (performance-design §1) |
| `veridicus_ingest_duration_seconds_count{outcome="rolled_back"}` | Trabajador | > 0 en 15 min | La base cortó la transacción de 5 s; el mensaje queda pendiente |
| `veridicus_run_latency_seconds` por `mode` y `outcome` | Trabajador, al ingerir | Sin umbral; se muestra | Latencia de punta a punta del analizador vista por U4 |
| `veridicus_model_input_tokens_total`, `veridicus_model_output_tokens_total` por `provider` y `role` | Trabajador, desde `ModelCall` | Sin umbral; se muestra | Consumo por proveedor y papel (C18) |
| `veridicus_sessions_blocked_total` | API y trabajador | Cualquier aumento | Incidente de anonimización (NFR15.5, AUTONOMIA-04) |
| Memoria del trabajador y de `semantic-agent` frente al límite que renderiza el chart | `container_memory_working_set_bytes` (U2) | > 0,9 del límite durante 5 min | Con el margen de 1,2 × (pico + `/tmp`), pasar de 0,9 es acercarse al pico medido |

Ninguna etiqueta lleva `session_id` ni texto; la latencia por llamada y el costo por proveedor viven en C19 v2
de U11 y U4 no los duplica (observability-design §2).

## 2. Alertas

Reglas informativas en el subchart de reglas de U2, cada una con su anotación `runbook` y su prueba
`promtool test rules` con un caso que dispara y otro que no. Ninguna notifica a nadie ni cambia nada.

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusRunQueueBacklog` | `veridicus_run_queue_depth > 20` durante 10 min | warning (P3) | Panel «Veridicus — corridas», fila de U4 |
| `VeridicusRunQueueWaitHigh` | p95 de `veridicus_run_queue_wait_seconds` > 3 600 en 1 h | info (P3) | Panel «Veridicus — corridas» |
| `VeridicusRunSystemError` | `increase(veridicus_runs_total{error_code="analysis.system"}[15m]) > 0` | warning (P3) | Panel «Veridicus — corridas»; el runbook pide buscar `run.publish_failed`, `run.claim_lost` y mensajes en `:failed` en los logs |
| `VeridicusAnonymizerUnavailable` | `increase(veridicus_runs_total{error_code="analysis.anonymizer_unavailable"}[15m]) > 0` | warning (P3) | Panel «Veridicus — corridas» y panel del proxy de U10 |
| `VeridicusSessionBlocked` | `increase(veridicus_sessions_blocked_total[15m]) > 0` | critical (P3, sin notificación) | Panel «Veridicus — corridas»; el runbook remite al registro del incidente y al ADR del proveedor |
| `VeridicusIngestSlow` | p95 de `veridicus_ingest_duration_seconds` > 5 en 1 h, o algún `rolled_back` en 15 min | warning (P3) | Panel «Veridicus — corridas» |
| `VeridicusU4PodNearMemoryLimit` | Memoria / límite > 0,9 durante 5 min en el trabajador o en `semantic-agent` | warning (P3) | Panel «Veridicus — plataforma» de U2 |

## 3. SLIs / SLOs

Son objetivos de verificación del MVP (prueba de carga, nivel 1 y humo), no SLO con ventana de producción
(observability-design §3).

| SLI | SLO target | Measurement window |
|---|---|---|
| p95 de la ingesta | ≤ 5 s | Prueba `perf` de nivel 1 con un `RunResult` de 50 hallazgos; 1 h móvil en Prometheus |
| Tramo de U4 en el camino crítico (`XADD` de C3 → tarjeta en M4) | ≤ 10 s p95 (NFR3.1) | Nivel 1 (`perf`) y nivel 3 |
| Corridas que terminan sin `analysis.system` | 100 % de las 50 sesiones de NFR8.5 | Una corrida de `run_batches.py` |
| Espera en cola p95 | ≤ 3 600 s | La misma corrida de carga |
| Sesiones bloqueadas | 0 en la prueba de carga | La misma corrida |
| Liberación de una espera | ≤ 1 s (NFR3.13) | Prueba de nivel 1 con reloj controlado |
| Corrida vencida que pasa a `error` | ≤ 30 s tras `deadline_at` (NFR3.6) | Prueba de nivel 1 con reloj controlado |
| Prueba de humo | Código 0 con ≤ 300 s por caso (NFR3.10, NFR8.6) | Cada despliegue |

Si la corrida de carga aprieta la memoria, el primer recorte es apagar el monitoreo (U2 §4); entonces los
SLI salen del reporte de `run_batches.py`, y los picos por pod de NFRD-U8-11 se toman solo cuando el
monitoreo está encendido.

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con el formateador único de `libs/` (U3): `timestamp`, `level`, `service`, `event` y solo los campos de la lista blanca (`session_id`, `run_id`, `turn_id`, `attempt`, `message_id`, `code`, `duration_ms`, `size_bytes`, `count`). Excepciones por tipo y `code`, sin `exc_info` en módulos con testimonio (security-design §6) |
| Eventos de corrida | `run.queued`, `run.held`, `run.processing`, `run.completed`, `run.error`, `run.cancelled` con `run_id`, `attempt` y `message_id`; `WARNING` `run.claim_lost` y `limits.exceeded`; `ERROR` `run.publish_failed`, `run.cancel_key_failed`, `session.blocked` y caídas de dependencia (observability-design §1; NFRD-U6-17) |
| Correlación | `run_id` + `attempt` + `message_id` siguen una corrida por la API, `semantic-agent` y el trabajador; prueba de nivel 1 que la reconstruye y encuentra el *canary* 0 veces |
| Dónde se leen | `kubectl logs -n veridicus deploy/<proceso>` (solo lectura); rotación del kubelet. La captura de logs con el *canary* es de U2 (NFR10.19 de U2) |
| Trazas | Sin trazas distribuidas: la correlación por `message_id` cubre el único flujo de varios servicios |

## 5. Paneles

| Panel | Contenido de U4 |
|---|---|
| Veridicus — corridas (fila de U4 en el panel de U2) | Profundidad de cola, espera p95 por `mode`, corridas por `outcome` y `error_code`, ingesta p95 y `rolled_back`, tokens por `provider` y `role`, sesiones bloqueadas |
| Veridicus — plataforma (U2) | CPU y memoria del trabajador y de `semantic-agent` frente a su límite |

Los paneles muestran solo contadores y etiquetas de enum cerradas. La fila de U4 se empaqueta en el chart de
U2 con el mismo SHA-256 que su original en `services/session-api/observability/` (mismo mecanismo que
`check-config-copy.sh` aplica al panel de U10).

## 6. Retirado de la revisión 1

Salen `veridicus_turn_latency_seconds`, `veridicus_turn_queue_depth`, `veridicus_turns_total`,
`veridicus_judge_*`, `veridicus_embedding_*`, `veridicus_scenario_indexing_seconds`,
`veridicus_claims_total`, `veridicus_alerts_total`, `veridicus_handoff_packages_total`, las alertas
`VeridicusJudge*`, `VeridicusIndexingFailed` y `VeridicusAiPodNearMemoryPeak`, y el panel «Veridicus —
evaluación». Las métricas de los servidores de modelos son de U2.
