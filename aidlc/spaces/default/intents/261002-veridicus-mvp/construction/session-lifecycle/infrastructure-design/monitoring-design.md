# Diseño de monitoreo — U6 session-lifecycle

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen las métricas de publicación por lote, de latidos, de turnos por pegado y de la
  revisión con nombre viejo, y las que dependían de la cola de turnos de U4. Entran las métricas de
  `contracts/metrics/session-lifecycle.v1.yaml` (NFRD-U6-12): importaciones por `origin`, transiciones,
  revisión de suspensión y cancelaciones, con la etiqueta `error_code`.
- **Numeración.** §1–§5 conservan su tema; §6 (nueva) lista lo retirado.

**Insumos.** Eventos, métricas, SLI, panel y reglas informativas de `nfr-design/observability-design.md`
(observability-design §1–§4); presupuestos de `nfr-design/performance-design.md` (performance-design §1–§4,
§8–§10); señales de escalado de `nfr-design/scalability-design.md` (scalability-design §4, §5); fallos de la
revisión, de la publicación y de las claves de `nfr-design/reliability-design.md` (reliability-design §2, §3,
§11, §12); lista blanca y prueba centinela de `nfr-design/security-design.md` (security-design §4); radio de
impacto de `nfr-design/logical-components.md` (logical-components §2); estados de la sesión de
`functional-design/functional-spec.md` (functional-spec §3); procesos de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de U2
(`platform/infrastructure-design/monitoring-design.md`), `ServiceMonitor` de U3 y de U4;
`infrastructure-specification.md` de esta carpeta.

U6 usa la pila de U2: Prometheus y Grafana desde el módulo 8 (SHOULD), `PrometheusRule` **sin
Alertmanager**, sin Loki y sin trazas; logs JSON por salida estándar con la rotación del kubelet. No añade
exportadores ni `ServiceMonitor`: la API la raspa `veridicus-session-api` de U3 y el trabajador el
`ServiceMonitor` de U4, los dos en el puerto `metrics` 8081 cada 30 s. Las reglas y la fila del panel de U6
solo se renderizan con `monitoring.enabled: true`, porque antes del módulo 8 el CRD no existe (IDS-U6-07).

## 1. Métricas y KPI

Todas declaradas en `contracts/metrics/session-lifecycle.v1.yaml`; la comprobación de U1 en nivel 0 falla
ante una métrica, etiqueta o valor fuera del archivo. Ninguna etiqueta lleva `session_id` ni texto.

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| p95 de `veridicus_transcript_paste_seconds` | API | > 2,5 s en 1 h | NFR3.1: presupuesto del pegado con el bloque máximo |
| `veridicus_transcript_pastes_total{outcome, error_code}` | API | `rejected` se muestra por `error_code`; sin umbral | NFR15.4: separa tamaño, estado y consentimiento |
| p95 de `veridicus_session_import_seconds` | API | > 3 s en 1 h | NFR3.13 con el archivo máximo |
| `veridicus_session_imports_total{outcome, error_code, origin}` | API | `origin` se muestra; sin umbral | T10 de security-design: importaciones declaradas `sintetico` auditables |
| `veridicus_session_transitions_total{state}` | API y trabajador | Sin umbral; por hora | NFR11.2: cada transición queda en el historial con su actor |
| `veridicus_sessions{state}` | Trabajador (caché de 15 s) | `open` > 50 durante 15 min | scalability-design §4: supuesto de capacidad del latido y de la revisión (IDS-U6-14) |
| p95 de `veridicus_session_sweep_seconds{outcome="ok"}` | Trabajador (`SessionSupervisor`) | > 0,1 s en 1 h | NFR3.9: el índice parcial mantiene barata la vuelta (scalability-design §5) |
| `veridicus_session_sweep_seconds_count{outcome="error"}` | Trabajador | > 2 en 5 min | NFR10.12: una vuelta fallida se ve y no se acumula |
| `veridicus_run_cancellations_total{outcome}` | API (`SessionLifecycle`) | Cualquier aumento de `key_deferred` | NFR10.18 (a): una clave quedó para reescribir |
| `veridicus_runs_total{error_code="analysis.system"}` (U4) | Trabajador | La regla de U4 | Una publicación fallida de un bloque o de un modo final la cierra el supervisor de U4 (NFRD-U6-13) |
| `veridicus_run_queue_depth` (U4) | Trabajador | La regla de U4 | scalability-design §5: señal para ajustar perfil o plazo (IDS-U6-08) |
| Memoria de la API y del trabajador frente a su límite | cAdvisor (U2) | > 0,9 durante 5 min (reglas de U2 y U4) | NFR8.1 (`infrastructure-specification.md` §1.1) |
| `/readyz` de la API y `/healthz` del trabajador | Sondas de Kubernetes y `smoke.sh` | ≠ 200 | NFR10.10: una cifra fuera de regla impide arrancar; el hilo 4 entra en `/healthz` |

## 2. Alertas

Reglas informativas en el subchart de reglas de U2, cada una con su anotación `runbook` y su prueba
`promtool test rules` con un caso que dispara y otro que no. Todas son P3 (panel): nadie recibe una
notificación y ninguna cambia el estado de una sesión (FR9.1).

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusSessionSweepErrors` | `increase(veridicus_session_sweep_seconds_count{outcome="error"}[5m]) > 2` | warning (P3) | Panel «Veridicus — sesiones»; el runbook pide buscar `session.sweep_failed` en los logs del trabajador |
| `VeridicusCancelKeyDeferred` | `increase(veridicus_run_cancellations_total{outcome="key_deferred"}[15m]) > 0` | warning (P3) | Panel «Veridicus — sesiones»; el runbook pide buscar `run.cancel_key_failed` y confirmar que la clave existe tras la siguiente vuelta |
| `VeridicusOpenSessionsHigh` | `veridicus_sessions{state="open"} > 50` durante 15 min | info (P3) | Panel «Veridicus — sesiones» (IDS-U6-14) |
| `VeridicusSessionSweepSlow` | p95 de `veridicus_session_sweep_seconds{outcome="ok"}` > 0,1 s en 1 h | info (P3) | Panel «Veridicus — sesiones» |
| `VeridicusPasteSlow` | p95 de `veridicus_transcript_paste_seconds` > 2,5 s en 1 h | info (P3) | Panel «Veridicus — sesiones» |
| `VeridicusImportSlow` | p95 de `veridicus_session_import_seconds` > 3 s en 1 h | info (P3) | Panel «Veridicus — sesiones» |
| Reglas de U2 y U4 (`VeridicusRunSystemError`, `VeridicusRunQueueBacklog`, `VeridicusU4PodNearMemoryLimit` y las de plataforma) | Sin cambio | Las suyas | Sus paneles |

Las dos primeras son las reglas que pide observability-design §4; las otras cuatro solo hacen visibles en el
panel los umbrales de §1.

## 3. SLIs / SLOs

Objetivos de verificación del MVP en el perfil CPU (NFR2.2), no SLO con ventana de producción. Las pruebas
`perf` corren en el *runner* `ubuntu-24.04` de 4 vCPU (IDS-U3-09): una sola corrida, sin reintentos; una
falla sospechosa de inestable se pone en cuarentena con un *issue* enlazado y el umbral nunca se baja.

| SLI | SLO target | Measurement window |
|---|---|---|
| p95 del pegado | ≤ 2,5 s con 2 000 turnos y 250 000 caracteres; ≤ 0,5 s con 60 turnos; bloqueo de la sesión ≤ 1 s (NFR3.1) | `pytest -m perf` de cada PR |
| p95 del sondeo con latido | ≤ 200 ms, también con otra transacción que retiene la fila 3 s (NFR3.3) | Ídem |
| p95 de la lista y de la reanudación | ≤ 300 ms con 500 sesiones y una sesión de 2 000 turnos (NFR3.2, NFR3.4) | Ídem |
| p95 de la importación | ≤ 3 s con 2 MiB y 2 000 turnos; ≤ 1 s con 312 turnos (NFR3.13) | Ídem |
| p95 del modo final y de pausa, terminación y retirada | ≤ 1 s y ≤ 500 ms con 20 corridas (NFR3.15, NFR3.16) | Ídem |
| Detección de la suspensión | `SessionStatusChange.at` − `coalesce(last_heartbeat_at, created_at)` entre 180 y 210 s; nunca con 179 s (NFR3.7) | Prueba de nivel 1 con reloj controlado |
| Vueltas de la revisión con error | 0 (NFR10.12) | Corrida de NFR8 y prueba de humo |
| Claves de cancelación diferidas | 0 en la demostración (NFR10.18) | Ídem |
| Rutas de U6 en la prueba de NFR8 | 0 respuestas 5xx en `/transcript` y `/final-runs`; 0 suspensiones de sesiones sondeadas (NFR8.13, NFR8.14) | Sección de U6 del reporte de `run_batches.py` |
| Duración del modo final máximo | Comparada con `run_deadline_final_s` efectivo por perfil, sin umbral (NFR3.17) | Reporte de `final_run_max.py`, a demanda |

Si la corrida de carga aprieta la memoria, el primer recorte de U2 es apagar el monitoreo; entonces los SLI
de U6 salen del reporte de `run_batches.py`.

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con el formateador único de `libs/` (U3) y la lista blanca de U4 más `paste_batch_id`, `origin`, tamaños en bytes, `turn_count`, `char_count`, `problem_count`, `idle_seconds`, `cancelled_runs` y `code`. Nunca el texto pegado o importado, el nombre del archivo, el mensaje de un `ImportProblem` ni datos del consentimiento (NFR10.4) |
| Eventos de la API | `transcript.pasted`, `transcript.rejected`, `transcript.replayed`, `session.imported`, `session.import_rejected`, `final_run.requested`, `session.paused`, `session.analysis_resumed`, `session.terminated`, `session.consent_withdrawn`, `session.resumed`, `heartbeat.write_failed`; de U4, `run.publish_failed` y `run.cancel_key_failed` con `session_id` y `run_id` (NFRD-U6-17) |
| Eventos del trabajador | `session.suspended` (con `actor_system = session-supervisor` e `idle_seconds`) y `session.sweep_failed` |
| Ruido | El latido omitido por `SKIP LOCKED` no se registra |
| Correlación | `session_id` → `paste_batch_id` → `run_id` + `attempt` (U4); basta para seguir un bloque hasta su resultado |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-session-api` y `deploy/veridicus-session-api-worker` (solo lectura); sin Loki en el MVP (U2) |
| Control | Prueba centinela de nivel 1: 0 apariciones de la cadena sembrada (bloque, archivo, nombre del archivo, `constancia`) en los logs de la API y del trabajador y en los Problem Details |
| Trazas | Sin trazas distribuidas (observability-design §4) |

## 5. Paneles

| Panel | Contenido de U6 |
|---|---|
| Veridicus — sesiones (fila de U6 en el chart de U2) | Sesiones por `state`; transiciones por hora; pegados e importaciones por `outcome` y `error_code`; importaciones por `origin`; p50/p95 del pegado y de la importación; vueltas de la revisión por `outcome` y su p95; cancelaciones por `outcome` |
| Veridicus — corridas (U4) | Enlace: la cola y las corridas de los bloques y del modo final |
| Veridicus — plataforma (U2) | CPU y memoria de la API y del trabajador frente a su límite |

El original vive en `services/session-api/observability/` y se empaqueta en el chart de U2 con el mismo
SHA-256, comprobado por `check-config-copy.sh` (petición IDS-U6-07). Solo muestra contadores y etiquetas de
enum cerradas.

## 6. Retirado de la revisión 1

Salen `veridicus_transcript_publish_total`, `veridicus_transcript_paste_turns`,
`veridicus_session_heartbeat_writes_total`, `veridicus_session_status_changes_total` (lo sustituye
`veridicus_session_transitions_total{state}`), `veridicus_suspension_sweep_seconds` (lo sustituye
`veridicus_session_sweep_seconds`), `veridicus_turn_latency_seconds` y `veridicus_turn_queue_depth` (U4 los
retiró); las alertas `VeridicusPastePublishFailed`, `VeridicusSuspensionSweepErrors`,
`VeridicusSuspensionSweepSlow` y `VeridicusHeartbeatErrors` con su nombre viejo; los eventos
`transcript.republish_skipped`, `transcript.publish_failed`, `suspension.sweep_failed` y
`scenario.version_created`; el SLO «exactamente 1 publicación por lote» y el del pegado de 60 turnos en nivel 2;
y el JSON `deploy/veridicus/dashboards/veridicus-sessions.json` como archivo propio del chart.
