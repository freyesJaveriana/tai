# Diseño de monitoreo — U2 platform

**Revisión 2 (2026-11-23).** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git. Las
secciones conservan su número; lo que sale queda «Retirado».

**Insumos.**
- Observabilidad de la plataforma, red y respaldos de `nfr-design/security-design.md` revisión 2
  (security-design §2.1, §2.2, §11 y §12; NFRD-U2-03, NFRD-U2-05 y NFRD-U2-12).
- U2 no tiene observability-design propio (es `packaging`). Lo que piden a U2 los observability-design,
  reliability-design, performance-design y scalability-design de otras unidades llega por la tabla NFRD de
  cada `security-design.md`: raspado del proxy en 9090 con su panel copiado por SHA-256, reglas
  informativas sin Alertmanager y los picos de memoria de cada pod. logical-components de U2 no existe; los
  componentes son los de `inception/domain-design/components.md` (components).
- NFR8.1, NFR8.3, NFR10.19, NFR15.1 y NFR15.2 de `nfr-requirements/security-requirements.md`; D4 y D11 de
  `nfr-requirements/tech-stack-decisions.md`.
- C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary); functional-spec de
  otras unidades solo a través de esas tablas.
- `infrastructure-specification.md` revisión 2 de esta carpeta y respuestas P1–P8 de
  `infrastructure-design-questions.md`.

Este documento define la pila de monitoreo que comparten todas las unidades y las señales de la plataforma.
Cada unidad de servicio añade sus métricas y reglas en su propio `monitoring-design.md`, y U2 las empaqueta
en el subchart `monitoring-rules`.

## 1. Pila

| Pieza | Elección | Cuándo | Configuración |
|---|---|---|---|
| Métricas | `kube-prometheus-stack` (D4) con versión exacta, en `monitoring` | Módulo 8 (SHOULD) | Prometheus con retención de 48 h y PVC de 5 GiB; raspado cada 30 s; un `ServiceMonitor` por servicio con métricas |
| Paneles | Grafana del mismo chart, `check_for_updates: false`, sin *plugins* ni análisis de uso | Módulo 8 | Paneles como JSON en `ConfigMap` versionados en `charts/monitoring-rules/dashboards/` |
| Alertas | `PrometheusRule` **sin Alertmanager** | Módulo 8 | Nadie recibe notificaciones; las reglas se ven en Prometheus y en los paneles |
| Logs | Salida estándar en JSON de cada contenedor; `kubectl logs` | Desde el primer despliegue | Rotación del kubelet (10 MiB × 5 archivos por contenedor); sin Loki |
| Trazas | No hay | — | El `request_id`, el `run_id` y el `turn_id` correlacionan |
| Uso de recursos | `metrics-server` de Minikube (`kubectl top`) | Desde el clúster inicial | Para comprobar `requests` y `limits` antes del módulo 8 |

Componentes activos de `kube-prometheus-stack`: Prometheus, su operador, Grafana, kube-state-metrics y
node-exporter. Desactivados: Alertmanager y las reglas por defecto de etcd, del controlador y del
planificador, que no aportan en un solo nodo.

## 2. Métricas y KPI de la plataforma

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| Memoria de trabajo de cada contenedor / su `limits.memory` | cAdvisor del `kubelet` y kube-state-metrics | > 0,9 durante 5 min | Un pod que llega a su límite muere por OOM (NFR8.1); `model-judge` y `model-verifier` son los más expuestos |
| Memoria pedida en el nodo / 50 GiB de Minikube | kube-state-metrics (`kube_pod_container_resource_requests`) | > 0,9 | Un pod nuevo quedaría `Pending`; con el reparto de §4 de la especificación vale ≈ 0,82 |
| Reinicios de contenedor | `kube_pod_container_status_restarts_total` | > 0 en 15 min | Un reinicio durante una corrida invalida la prueba de NFR8 |
| Pods no listos en `veridicus` | `kube_pod_status_ready{condition="false"}` | > 0 durante 2 min | Una parte del sistema queda sin atender |
| Espacio libre del disco del nodo | `node_filesystem_avail_bytes` de node-exporter sobre el disco de Minikube | < 15 % | El aprovisionador hostPath de Minikube no publica `kubelet_volume_stats`; el disco del nodo contiene todos los PVC |
| Uso de los PVC por cuota propia | Métricas de cuota de U7, U9 y U13 | Las de cada unidad | El tamaño real de reportes y audio lo hace cumplir la aplicación |
| Estado de la base | `cnpg_collector_up` del `PodMonitor` de CloudNativePG, en su puerto de métricas | = 0 durante 1 min | Sin base, nada autenticado funciona |
| Llamadas del proxy | Métricas de `anonymizer-proxy` en el puerto 9090 (las define U10) | Las de U10 | Única salida de datos del clúster (NFR1.5) |
| Razón AIR por sesión (C15) | `veridicus_session_dismissal_ratio` de `session-api` | > 0,25 | Solo anota una revisión por PR; no cambia un umbral, un perfil ni un *prompt* (NFR15.1) |
| *Tokens* por segundo y cola del juez (`llamacpp:*`) | **Retirado** | — | Prometheus no alcanza `llama-server`: entraría por el puerto de la API, reservado a `semantic-agent` (NFR10.8). La latencia de los modelos la miden U4 y U11 desde el cliente |
| Uso del PVC por `kubelet_volume_stats` | **Retirado** | — | Minikube no la publica; la sustituyen el disco del nodo y las cuotas propias |

## 3. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusAirThresholdProposal` | `veridicus_session_dismissal_ratio > 0.25` | info (P3) | Panel AIR; la anotación **propone** revisar y no tiene acción |
| `VeridicusContainerNearMemoryLimit` | Memoria / límite > 0,9 durante 5 min | warning (P3) | Panel de plataforma |
| `VeridicusNodeRequestsHigh` | Memoria pedida / 50 GiB > 0,9 | warning (P3) | Panel de plataforma |
| `VeridicusContainerRestarting` | Reinicios > 0 en 15 min en `veridicus` | warning (P3) | Panel de plataforma |
| `VeridicusPodNotReady` | Pod no listo durante 2 min | warning (P3) | Panel de plataforma |
| `VeridicusNodeDiskFilling` | Disco libre del nodo < 15 % | warning (P3) | Panel de plataforma |
| `VeridicusDatabaseDown` | `cnpg_collector_up == 0` durante 1 min | critical (P3) | Panel de plataforma |
| `VeridicusVolumeFilling` | **Retirado** (lo sustituye `VeridicusNodeDiskFilling`) | — | — |
| `VeridicusJudgeQueueBuilding` | **Retirado** (sin raspado de `llama-server`) | — | — |

Todas son P3 (panel): nadie recibe notificaciones en el MVP. Cada regla lleva en su anotación `runbook` el
enlace a su sección de `docs/operacion/instalacion.md`. `promtool test rules` prueba cada una con un caso que
dispara y otro que no; la regla AIR usa a la vez los *fixtures* de U2 (0,25 sin alerta; 0,30 con alerta) y
los de U5 (0,25 sin alerta; 0,375 con alerta), con *W* = 8 del catálogo C25. Las reglas informativas de otras
unidades (por ejemplo, las exportaciones no registradas de U7) viven en el mismo subchart con su propia
prueba `promtool`.

## 4. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| `scripts/smoke.sh https://veridicus.local:8443` termina con código 0 tras cada despliegue (cuatro `/healthz` y `smoke.spec.ts` con *N* = 300 s) | 100 % de los despliegues; si falla, se revierte (team.md) | Cada despliegue |
| `scripts/check-ingress-routes.sh https://veridicus.local:8443` termina con código 0 | 100 % de los despliegues | Cada despliegue |
| Reinicios de contenedores de `veridicus` durante la corrida de NFR8 | 0 | Una corrida de NFR8 |
| Peticiones a internet bloqueadas desde cada pod de `veridicus` distinto del proxy (verificación manual) | 100 % | Antes de la sustentación |
| Pods de `veridicus` listos durante la sustentación | 100 % de los sondeos | Ventana de la demostración |

No se fija un porcentaje de disponibilidad mensual: el MVP corre a demanda en un solo equipo, sin usuarios
fuera de las pruebas y la demostración.

## 5. Paneles

| Panel | Contenido |
|---|---|
| Veridicus — plataforma | CPU y memoria de cada pod frente a sus `requests` y `limits`, memoria pedida frente a 50 GiB, reinicios, pods listos, disco del nodo, estado de la base |
| Veridicus — latencia | `veridicus_turn_latency_seconds` (C15) por `origin` y el p95 del inicio de sesión de U3 |
| Veridicus — AIR | `veridicus_session_dismissal_ratio` por sesión con la línea de 0,25 y `veridicus_review_decisions_total` por estado (C15) |
| Veridicus — anonimizador | Copia del panel de U10, con el mismo SHA-256 que `services/anonymizer-proxy/observability/grafana-dashboard.json`; `scripts/check-config-copy.sh` lo compara (control negativo: un byte distinto) |
| Paneles de las demás unidades | Uno por unidad, como lo entregue cada una |

Los paneles solo muestran identificadores y contadores (C15, C16): ninguna etiqueta lleva testimonio,
nombres ni CoT.

## 6. Salud y sondas

| Servicio | `startupProbe` | `livenessProbe` | `readinessProbe` |
|---|---|---|---|
| Servicios propios (`session-api`, `semantic-agent`, `audio-worker`) | `/healthz` cada 2 s, hasta 60 s | `/healthz` cada 10 s, 3 fallos | `/readyz` según cada unidad (C16) |
| `anonymizer-proxy` | `/healthz` cada 5 s, hasta 120 s (≥ 90 s por la carga del NER) | `/healthz` cada 10 s, 3 fallos | `/readyz` |
| `model-judge`, `model-verifier` | `/health` de `llama-server` cada 10 s, hasta 600 s (cargar 21 GB desde el ext4 de WSL2) | `/health` cada 15 s, 3 fallos | `/health` cada 5 s |
| `model-whisper`, `model-tts` | `/health` cada 5 s, hasta 120 s | `/health` cada 15 s | `/health` cada 5 s (TTS tras su calentamiento) |
| `veridicus-redis` | — | `tcpSocket` 6379 cada 10 s | `redis-cli ping` con `REDISCLI_AUTH` leído del archivo, cada 5 s |
| `veridicus-pg` | Las de CloudNativePG | Ídem | Ídem |

## 7. Logs sin datos

- `llama-server`, Whisper y Piper corren con un nivel de log que no imprime cuerpos.
- PostgreSQL no deja parámetros, consultas ni detalles en su log (los cinco parámetros de la especificación
  §2.1, incluido `log_error_verbosity: terse`).
- En nivel 1, `deploy/tests/level1` captura los logs de todos los contenedores tras el turno con *canary* y
  exige 0 apariciones (NFR10.19).
