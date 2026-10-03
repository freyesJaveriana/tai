# Diseño de monitoreo — U4 text-flow

**Insumos.** Logs, métricas, SLI y reglas informativas de `nfr-design/observability-design.md`
(observability-design); presupuestos y topes de `nfr-design/performance-design.md`
(performance-design); señales de escalado de `nfr-design/scalability-design.md` (scalability-design);
fallos del juez, plazos y salud de `nfr-design/reliability-design.md` (reliability-design); logs sin
datos sensibles de `nfr-design/security-design.md` (security-design); radio de impacto de
`nfr-design/logical-components.md` (logical-components); estados del turno de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de
`platform/infrastructure-design/monitoring-design.md`; `infrastructure-specification.md` de esta
carpeta.

U4 usa la pila de U2 (Prometheus y Grafana desde el módulo 8, sin Alertmanager; logs JSON por salida
estándar; sin trazas) y añade un `ServiceMonitor` por proceso sobre el puerto `metrics` 8081 de la API,
del trabajador y de `semantic-agent`, con *scrape* cada 30 s.

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| p95 de `veridicus_turn_latency_seconds{origin="typed"}` (C15) | Trabajador, al ingerir | > 60 s en 1 h | NFR3.1; es lo que espera el analista |
| `veridicus_turn_queue_depth` | Hilo de plazos del trabajador | > 30 durante 10 min | NFR8.8: con más turnos en cola, los plazos empiezan a vencer |
| `veridicus_turns_total{outcome="error", code}` | Trabajador | `turn.error.invalid_output` > 3 en 15 min; cualquier `turn.error.system` | NFR15.4: separa fallos del juez, plazos y defectos |
| `veridicus_judge_duration_seconds{result}` | `semantic-agent` | `result="unavailable"` > 5 en 15 min; p95 de `ok` > 50 s | Reintentos del juez (P1 de NFR Design) y presupuesto del camino crítico |
| `veridicus_judge_prompt_tokens` | `semantic-agent` | p95 > 5 000 | Turnos cerca del tope de 6 000 *tokens* (NFR3.11) |
| `veridicus_embedding_duration_seconds{purpose}` | Trabajador y `semantic-agent` | p95 de `query` > 3 s | Presupuesto de *embeddings* del turno |
| `veridicus_scenario_indexing_seconds{result}` | Trabajador | > 180 s o `result="error"` | NFR9.1 |
| `veridicus_claims_total{grade, guard}`, `veridicus_alerts_total`, `veridicus_handoff_packages_total` | `semantic-agent` | Sin umbral; se muestran | Comportamiento de la guardia del umbral (AUTONOMIA-05) |
| Memoria de juez, *embeddings*, `semantic-agent` y trabajador / su límite | cAdvisor (U2) | > 0,85 durante 5 min | Con el margen del 20 %, pasar de 0,85 es pasar el pico medido |
| *Tokens* por segundo y cola del juez | `llama-server --metrics` (U2) | Ver U2 | CPU insuficiente para el juez |

## 2. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusTurnQueueBacklog` | `veridicus_turn_queue_depth > 30` durante 10 min | warning (P3) | Panel «Veridicus — latencia» |
| `VeridicusTurnLatencyHigh` | p95 de latencia de turnos escritos > 60 s en 1 h | info (P3) | Panel «Veridicus — latencia» |
| `VeridicusJudgeInvalidOutput` | `increase(veridicus_turns_total{code="turn.error.invalid_output"}[15m]) > 3` | warning (P3) | Panel «Veridicus — evaluación» |
| `VeridicusJudgeRetrying` | `increase(veridicus_judge_duration_seconds_count{result="unavailable"}[15m]) > 5` | warning (P3) | Panel «Veridicus — evaluación» (el juez se está reiniciando) |
| `VeridicusTurnSystemError` | `increase(veridicus_turns_total{code="turn.error.system"}[15m]) > 0` | warning (P3) | Panel «Veridicus — evaluación» |
| `VeridicusIndexingFailed` | `increase(veridicus_scenario_indexing_seconds_count{result="error"}[15m]) > 0` | warning (P3) | Panel «Veridicus — evaluación» |
| `VeridicusAiPodNearMemoryPeak` | Memoria / límite > 0,85 durante 5 min en un pod de IA | warning (P3) | Panel «Veridicus — plataforma» de U2 |

Ninguna alerta despierta a nadie ni cambia nada (observability-design §4); cada una tiene su anotación
`runbook` y su prueba `promtool test rules` con un caso que dispara y otro que no.

## 3. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 de la latencia de un turno escrito | ≤ 60 s (NFR3.1) | Corrida de nivel 2 en CPU y 1 h móvil en Prometheus |
| Sesiones sin turnos en error en la corrida de carga | ≥ 98 % de 50 sesiones (NFR8.5) | Una corrida de NFR8 |
| Fallos atribuibles a U4 en `scripts/smoke.sh` | 0 (NFR8.6) | Cada despliegue |
| Alerta visible en la consola | ≤ 3 s desde `evaluated_at` (NFR3.8) | Prueba Playwright de nivel 3 |
| Profundidad de la cola | ≤ 30 sostenido | 1 h móvil |
| Escenario de 1 MB indexado | < 180 s (NFR9.1) | Medición de nivel 2 en CPU |

Durante la corrida de NFR8 en la máquina de desarrollo se apaga el monitoreo (SHOULD) si la memoria
aprieta; los SLI de esa corrida salen del reporte del arnés, no de Prometheus.

## 4. Logs

| Aspecto | Diseño |
|---|---|
| Formato | Una línea JSON por evento con la lista blanca de observability-design §1 (`timestamp`, `level`, `service`, `event`, `session_id`, `turn_id`, `attempt`, `message_id`, `version_id`, `code`, `duration_ms`, `count`); nunca texto de turnos, afirmaciones, pasajes, CoT ni *prompts* (NFR10.7, NFR15.2) |
| Correlación | `turn_id` + `attempt` + `message_id` siguen un turno por la API, `semantic-agent` y el trabajador (NFR15.3) |
| Servidores de modelos | `llama-server` sin `--verbose` ni registro de peticiones (NFR10.8); verificación manual con una cadena centinela antes de la sustentación |
| Dónde se leen | `kubectl logs -n veridicus deploy/<proceso>`; rotación del kubelet (10 MiB × 5) |

## 5. Trazas

No hay trazas distribuidas; la correlación por `message_id` cubre el único flujo de varios servicios
(observability-design §1).

## 6. Paneles

| Panel | Contenido de U4 |
|---|---|
| Veridicus — latencia (U2) | p50/p95 de la latencia del turno por `origin`, profundidad de la cola, duración del juez |
| Veridicus — evaluación (nuevo, de U4) | Turnos por `outcome` y `code`, reintentos del juez, *tokens* del *prompt*, afirmaciones por `grade` y `guard`, alertas y paquetes emitidos, indexaciones por resultado |
| Veridicus — plataforma (U2) | CPU y memoria de los pods de IA frente a sus límites |

Los paneles muestran solo contadores y etiquetas de enum cerradas; ninguna etiqueta lleva texto.
