# Diseño de monitoreo — U2 platform

**Insumos.** Regla AIR y puertos de métricas de `nfr-design/security-design.md` (security-design §2 y
§9b); D4 y D11 de `nfr-requirements/tech-stack-decisions.md`; NFR15.1 y NFR8.1 de
`nfr-requirements/security-requirements.md`; C15 y C16 de `inception/contract-design/contract-summary.md`
(contract-summary); dependencias externas de `inception/domain-design/components.md` (components);
`infrastructure-specification.md` de esta carpeta (servicios, recursos y namespaces); respuestas P1–P5
de `infrastructure-design-questions.md`.

U2 no tiene `observability-design` propio (es `packaging`): este documento define la pila de
monitoreo que comparten todas las unidades y las señales de la plataforma. Cada unidad de servicio
añade sus métricas y alertas en su propio `monitoring-design.md`.

## 1. Pila

| Pieza | Elección | Cuándo | Configuración |
|---|---|---|---|
| Métricas | `kube-prometheus-stack` (D4) con versión exacta, en `monitoring` | Módulo 8 (SHOULD) | Prometheus con retención de 48 h y PVC de 5 GiB; *scrape* cada 30 s; `ServiceMonitor`/`PodMonitor` en el chart de cada servicio |
| Paneles | Grafana del mismo chart | Módulo 8 | Paneles como JSON en `ConfigMap` con la etiqueta `grafana_dashboard: "1"`, versionados en `deploy/veridicus/dashboards/` |
| Alertas | `PrometheusRule`; **sin Alertmanager** ni notificaciones | Módulo 8 | MVP sin alertas que despierten a nadie (observability-requirements de U3); las alertas se ven en Prometheus y en el panel |
| Logs | Salida estándar en JSON de cada contenedor; `kubectl logs` | Desde el primer despliegue | Rotación del kubelet (10 MiB × 5 archivos por contenedor); sin Loki para no gastar memoria |
| Trazas | No hay | — | Ningún flujo cruza más de dos servicios; el `request_id` y el `turn_id` correlacionan |
| Uso de recursos | `metrics-server` de Minikube (`kubectl top`) | Desde el clúster inicial | Para comprobar `requests`/`limits` antes del módulo 8 |

Componentes de `kube-prometheus-stack` activos: Prometheus, operador, Grafana, kube-state-metrics y
node-exporter. Desactivados: Alertmanager y las reglas por defecto de etcd, controlador y planificador
de Minikube que no aportan en un solo nodo.

## 2. Métricas y KPI de la plataforma

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| Memoria de trabajo de cada contenedor / su `limits.memory` | kube-state-metrics + cAdvisor | > 0,9 durante 5 min | Un pod que llega a su límite muere por OOM (NFR8.1); el juez es el más expuesto |
| Reinicios de contenedor | `kube_pod_container_status_restarts_total` | > 0 en 15 min | Un reinicio durante una corrida invalida NFR8 de U4 |
| Pods no listos en `veridicus` | `kube_pod_status_ready{condition="false"}` | > 0 durante 2 min | Un servicio fuera del Service deja una parte del sistema sin atender |
| Uso del PVC de la base | `kubelet_volume_stats_used_bytes / capacity` | > 0,8 | La base deja de escribir si se llena |
| Uso del PVC de Redis | Ídem | > 0,8 | El AOF crece con las colas |
| Memoria usada por Redis / `maxmemory` | Sin exportador en el MVP; se ve con `redis-cli INFO memory` y por el error de escritura que reporta U4 (§6) | > 0,8 | Con `noeviction`, Redis rechaza escrituras al llenarse |
| *Tokens* por segundo del juez | `llamacpp:predicted_tokens_seconds` de `llama-server --metrics` | < 50 % de la línea base medida por U4 | Detecta un juez sin CPU suficiente antes de que los turnos venzan su plazo |
| Peticiones en cola del juez | `llamacpp:requests_deferred` | > 0 durante 10 min | Con una sola ranura, una cola sostenida alarga los turnos |
| Estado de la base | `cnpg_collector_up` del `PodMonitor` de CloudNativePG | = 0 durante 1 min | Sin base, nada autenticado funciona |
| Razón AIR por sesión (C15) | `veridicus_session_dismissal_ratio` de `session-api` | > 0,25 | FR9.3: propone revisar el umbral; nunca lo cambia (NFR15.1) |

## 3. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusAirThresholdProposal` | `veridicus_session_dismissal_ratio > 0.25` (D11) | info (P3) | Panel AIR; la anotación **propone** un umbral y no tiene acción |
| `VeridicusContainerNearMemoryLimit` | Memoria / límite > 0,9 durante 5 min | warning (P3) | Panel de plataforma |
| `VeridicusContainerRestarting` | Reinicios > 0 en 15 min en `veridicus` | warning (P3) | Panel de plataforma |
| `VeridicusPodNotReady` | Pod no listo durante 2 min | warning (P3) | Panel de plataforma |
| `VeridicusVolumeFilling` | PVC de base o Redis > 80 % | warning (P3) | Panel de plataforma |
| `VeridicusDatabaseDown` | `cnpg_collector_up == 0` durante 1 min | critical (P3) | Panel de plataforma |
| `VeridicusJudgeQueueBuilding` | `llamacpp:requests_deferred > 0` durante 10 min | info (P3) | Panel de latencia |

Todas son P3 (panel): nadie recibe una notificación en el MVP. Cada regla lleva en su anotación
`runbook` el enlace a su sección de `docs/operacion/instalacion.md`. `promtool test rules` prueba cada
una con un caso que dispara y otro que no (la AIR, por debajo y por encima de 0,25).

## 4. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| `scripts/smoke.sh <url-base>` termina con código 0 tras cada despliegue | 100 % de los despliegues; si falla, se revierte (team.md) | Cada despliegue |
| Reinicios de contenedores de `veridicus` durante la corrida de NFR8 de U4 | 0 | Una corrida de NFR8 (50 sesiones) |
| Peticiones a internet desde cada pod de `veridicus` bloqueadas (verificación manual de NFR1.1) | 100 % | Antes de la sustentación |
| Pods de `veridicus` listos durante la sustentación | 100 % de los sondeos | Ventana de la demostración |

No se fija un porcentaje de disponibilidad mensual: el MVP corre a demanda en una máquina de
desarrollo, sin usuarios fuera de las pruebas y la demostración.

## 5. Paneles

| Panel | Contenido |
|---|---|
| Veridicus — plataforma | Uso de CPU y memoria de cada pod frente a sus `requests`/`limits`, reinicios, pods listos, uso de PVC, estado de la base |
| Veridicus — latencia | `veridicus_turn_latency_seconds` (C15) por `origin`, p95 del inicio de sesión de U3, *tokens* por segundo y cola del juez |
| Veridicus — AIR | `veridicus_session_dismissal_ratio` por sesión con la línea de 0,25 y `veridicus_review_decisions_total` por estado (C15) |

Los paneles solo muestran identificadores y contadores (C15, C16): ninguna etiqueta lleva texto de
testimonio, nombres ni CoT.

## 6. Salud y sondas

| Servicio | `startupProbe` | `livenessProbe` | `readinessProbe` |
|---|---|---|---|
| Servicios propios | `/healthz` cada 2 s, hasta 60 s | `/healthz` cada 10 s, 3 fallos | La define cada unidad en su diseño (C16); U3 fija la de `session-api` |
| `veridicus-judge`, `veridicus-embeddings` | `/health` de `llama-server` cada 5 s, hasta 300 s (carga del modelo) | `/health` cada 15 s, 3 fallos | `/health` cada 5 s |
| `veridicus-whisper` | `/health` cada 5 s, hasta 120 s | `/health` cada 15 s | `/health` cada 5 s |
| `veridicus-redis` | — | `redis-cli ping` cada 10 s | `redis-cli ping` cada 5 s |
| `veridicus-pg` | Las define CloudNativePG | Ídem | Ídem |

La memoria de Redis (fila de §2) no tiene exportador en el MVP: se vigila con el uso del PVC y con el
error de escritura que reporta U4 al publicar en la cola; añadir `redis_exporter` queda como mejora
si la prueba de NFR8 lo pide.
