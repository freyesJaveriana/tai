# Diseño de monitoreo — U6 session-lifecycle

**Insumos.** Eventos, métricas, SLI, panel y reglas informativas de `nfr-design/observability-design.md`
(observability-design); presupuestos de `nfr-design/performance-design.md` (performance-design);
señales de escalado de `nfr-design/scalability-design.md` (scalability-design); fallos de publicación y
de la revisión de `nfr-design/reliability-design.md` (reliability-design); lista blanca de logs y
prueba centinela de `nfr-design/security-design.md` (security-design); dominios de falla de
`nfr-design/logical-components.md` (logical-components); estados de la sesión de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de
`platform/infrastructure-design/monitoring-design.md` (U2), formateador de U3
(`identity-access/infrastructure-design/monitoring-design.md`) y `ServiceMonitor` y paneles de U4
(`text-flow/infrastructure-design/monitoring-design.md`); `infrastructure-specification.md` de esta
carpeta.

U6 usa la pila de U2 (Prometheus y Grafana desde el módulo 8, `PrometheusRule` **sin Alertmanager**,
logs JSON por salida estándar, sin trazas) y los `ServiceMonitor` de U4 sobre el puerto `metrics` 8081
de la API y del trabajador, con *scrape* cada 30 s. No añade exportadores ni objetivos de *scrape*.

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| p95 de `veridicus_transcript_paste_seconds` | API | > 2 s en 1 h | NFR3.1: presupuesto del pegado de peor caso |
| `veridicus_transcript_pastes_total{outcome, code}` | API | `outcome="rejected"` se muestra por `code`; sin umbral | NFR15.4: separa tamaño, turno largo y sesión no abierta |
| `veridicus_transcript_publish_total{result}` | API (`publish_batch`) | `result="failed"` > 0 en 15 min | NFR10.11: Redis no aceptó un lote confirmado |
| `veridicus_transcript_paste_turns{role}` | API | p95 de `testimony` ≥ 45 | NFR8.4: un pegado así llega al tope del plazo en CPU |
| `veridicus_session_heartbeat_writes_total{result}` | API (`HeartbeatWriter`) | `result="error"` > 5 en 15 min; `skipped_locked` se muestra | NFR3.3, NFR3.8, NFR8.6: el latido es barato y no espera bloqueos |
| `veridicus_session_status_changes_total{to_status, actor_kind}` | API y trabajador | Sin umbral; se muestra por hora | NFR11.2: cada transición tiene actor |
| `veridicus_sessions{status}` | Trabajador (`SuspensionSweeper`) | `open` > 50 | NFR8.6, NFR8.7: supuesto de capacidad del latido y de la revisión |
| p95 de `veridicus_suspension_sweep_seconds{result="ok"}` | Trabajador | > 0,1 s en 1 h | NFR3.9: el índice parcial mantiene barata la revisión |
| `veridicus_suspension_sweep_seconds_count{result="error"}` | Trabajador | > 2 en 5 min | NFR10.12: un fallo de la revisión se ve y no se acumula |
| `veridicus_turn_latency_seconds{origin="pasted"}` (C15) | Trabajador (ingesta de U4) | Sin umbral (incluye cola) | NFR3.10, NFR3.11: no se compara con la meta de 60 s de los turnos escritos |
| `veridicus_turn_queue_depth` (U4) | Trabajador | > 30 durante 10 min (regla de U4) | scalability-design §5: señal para perfil GPU o bajar el límite |
| Memoria de API y trabajador / su límite | cAdvisor (U2) | > 0,9 durante 5 min (regla de U2) | NFR8.1 |
| `/readyz` completo de la API y del trabajador | Sonda de `smoke.sh` y *scrape* cada 30 s (U3/U4) | ≠ 200 | NFR10.10: un ajuste de U6 inválido impide arrancar |

Las etiquetas son enums cerrados; la prueba de nivel 0 que recorre el registro (U4) falla con una
etiqueta nueva sin declarar.

## 2. Alertas

Todas son P3 (panel), como en U2: nadie recibe una notificación y ninguna cambia el estado de una
sesión. Cada regla lleva en su anotación el requisito y la acción por PR.

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusPastePublishFailed` | `increase(veridicus_transcript_publish_total{result="failed"}[15m]) > 0` | warning (P3) | Panel «Veridicus — sesiones» |
| `VeridicusSuspensionSweepErrors` | `increase(veridicus_suspension_sweep_seconds_count{result="error"}[5m]) > 2` | warning (P3) | Panel «Veridicus — sesiones» |
| `VeridicusSuspensionSweepSlow` | p95 de `veridicus_suspension_sweep_seconds{result="ok"}` > 0,1 s en 1 h | info (P3) | Panel «Veridicus — sesiones» |
| `VeridicusPasteSlow` | p95 de `veridicus_transcript_paste_seconds` > 2 s en 1 h | info (P3) | Panel «Veridicus — sesiones» |
| `VeridicusHeartbeatErrors` | `increase(veridicus_session_heartbeat_writes_total{result="error"}[15m]) > 5` | info (P3) | Panel «Veridicus — sesiones» |
| Reglas de U2 y U4 (`VeridicusContainerRestarting`, `VeridicusPodNotReady`, `VeridicusTurnQueueBacklog`, `VeridicusDatabaseDown`) | Sin cambio | Las de U2/U4 | Sus paneles |

## 3. SLI y SLO

Objetivos del MVP medidos en la máquina de desarrollo con `values-cpu.yaml` (NFR2.2).

| SLI | SLO | Ventana de medición |
|---|---|---|
| Latencia del pegado (p95 de `veridicus_transcript_paste_seconds`) | ≤ 2 s con 200 turnos; ≤ 0,5 s con 15 turnos | Corrida de `pytest -m perf` de cada PR |
| Sondeo con latido (p95 de `GET /sessions/{id}`) | ≤ 200 ms con un pegado de peor caso en paralelo | Ídem |
| Lista y reanudación (p95) | ≤ 300 ms con 500 sesiones / 60 turnos | Ídem |
| Detección de la suspensión (`suspended_at − last_heartbeat_at`) | 180–210 s; nunca con 179 s | Prueba de nivel 1 con reloj controlado |
| Revisiones con error | 0 | Corridas de NFR8 y de humo |
| Publicaciones por lote en la prueba de reenvío | Exactamente 1 por `paste_batch_id` | Prueba de nivel 1 de cada PR |
| Pegado de 60 turnos | 0 `turn.error.timeout` | Corrida de nivel 2 antes de cada entrega etiquetada |

## 4. Logs y trazas

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con el formateador de U3; la lista blanca suma `paste_batch_id`, `scenario_id`, `turn_count`, `testimony_count`, `char_count` e `idle_seconds`. Nunca texto pegado, texto de un turno ni nombre de hablante (NFR10.4, NFR15.2) |
| Eventos | `transcript.pasted`, `transcript.rejected`, `transcript.republish_skipped`, `transcript.publish_failed` (API); `session.suspended`, `suspension.sweep_failed` (trabajador); `session.resumed`, `heartbeat.write_failed`, `scenario.version_created` (API) (NFR15.3, NFR15.4) |
| Ruido | El latido omitido por `SKIP LOCKED` no se registra; solo se cuenta |
| Correlación | `paste_batch_id` → `turn_id` + `attempt` + `message_id` de U4; basta para seguir un lote hasta cada resultado sin trazas distribuidas |
| Recolección | `kubectl logs` y la salida estándar de los pods; sin Loki en el MVP (U2) |
| Control | Prueba centinela de nivel 1: 0 coincidencias de la cadena sembrada en logs de API y trabajador y en Problem Details |

## 5. Paneles

Un JSON versionado en `deploy/veridicus/dashboards/veridicus-sessions.json`, publicado como `ConfigMap`
con `grafana_dashboard: "1"` (mecanismo de U2, módulo 8):

| Fila del panel «Veridicus — sesiones» | Contenido |
|---|---|
| Estado | `veridicus_sessions` por `status`; suspensiones y reanudaciones por hora (`to_status`, `actor_kind`) |
| Pegado | Aceptados y rechazados por `code`; p50/p95 de duración; turnos por pegado por `role`; publicaciones por `result` |
| Latido y revisión | Latidos por `result`; p95 y errores de la revisión |
| Contexto | Enlace al panel «Veridicus — latencia» de U4 (cola, latencia `origin="pasted"`) |
