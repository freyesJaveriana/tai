# Diseño de monitoreo — U10 anonymizer

**Insumos.** De `nfr-design/` de esta unidad: observability-design §1–§3 (logs, métricas, SLI, alertas
informativas y panel), performance-design §1 y §5 (presupuesto de 250 ms y pico de memoria),
scalability-design §4 y §5 (corrida de NFR8.4 y señal para escalar), reliability-design §2 y §5
(plazos y sondas), security-design §2 y §5 (comprobación final y entrada de Prometheus) y
logical-components §2 (dominios de falla). También: `functional-design/functional-spec.md`
(functional-spec, máquina de estados), la frontera del clúster de `inception/domain-design/components.md`
(components), C15 y C16 de `inception/contract-design/contract-summary.md` (contract-summary), la
respuesta **P1 = A** de `infrastructure-design-questions.md` (CoreDNS con lista blanca), el diseño de
monitoreo de U2 (`kube-prometheus-stack` sin Alertmanager en el módulo 8, logs por `kubectl logs`) y
`infrastructure-specification.md` de esta carpeta.

Todo lo de este documento se renderiza solo con `anonymizer.enabled: true` y `monitoring.enabled:
true`, salvo la alerta de CoreDNS (§2), que rige siempre desde el módulo 8 porque protege a todo el
namespace. Con el proxy apagado, la observabilidad de U10 se prueba en los niveles 0 y 1 de cada PR.

## 1. Métricas y KPI

Recogidas por un `ServiceMonitor` del puerto `metrics` (8081) cada 30 s; las etiquetas solo llevan
valores de enum (observability-design §2).

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| `veridicus_anonymizer_requests_total{operation,result}` | Proxy | `result="busy"` = 0 en la corrida de NFR8.4 | Volumen y desenlace de cada llamada; `busy` sostenido es la señal para escalar por PR |
| `veridicus_anonymizer_failed_closed_total{reason}` | Proxy | 0 en una corrida de nivel 2; cada caso es un hallazgo | Muestra en qué rama se cerró una llamada sin enviar nada |
| `veridicus_anonymizer_failed_closed_total{reason="outbound_check"}` | Proxy | 0 siempre | Si sube, el enmascarado tiene un defecto que la segunda barrera atajó |
| `veridicus_anonymizer_replacements_total{category}` | Proxy | Informativo | Una caída a 0 con tráfico indica reglas o listas vacías |
| `veridicus_anonymizer_masking_seconds{operation}` | Proxy (histograma) | p95 `judge` ≤ 0,25 s | Sobrecosto del proxy en el turno (NFR3.3) |
| `veridicus_anonymizer_upstream_seconds{operation,result}` | Proxy (histograma) | p95 `judge` ≤ 170 s; `result="timeout"` = 0 en nivel 2 | Separa la latencia del proveedor de la del proxy |
| `veridicus_anonymizer_unknown_markers_total` | Proxy | ≤ 3 en 15 min | El destino inventa o altera marcadores |
| `veridicus_anonymizer_rules_info{schema_version}` | Proxy | Exactamente 1 serie | Qué versión de reglas corre (NFR10.11) |
| `container_memory_working_set_bytes` del proxy | kubelet (cAdvisor) | < 85 % de `limits.memory` (≈ 272 MiB) | Margen frente al corte por memoria (NFR8.1) |
| `kube_pod_container_status_restarts_total` del proxy | kube-state-metrics | 0 en 1 h | Reinicios por memoria o por configuración inválida |
| `coredns_dns_responses_total{zone=".",rcode="NXDOMAIN"}` | CoreDNS (9153) | 0 en 15 min | Un pod intentó resolver un nombre fuera de la lista blanca (T15) |

## 2. Alertas

Reglas en un `PrometheusRule` (`veridicus-anonymizer`), validadas con `promtool test rules` en
`deploy-level0.yml`. Sin Alertmanager: ninguna despierta a nadie, se ven en Prometheus y en el panel.
Ninguna regla cambia configuración ni apaga el proxy (AUTONOMIA-01); la respuesta siempre es un PR.

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusAnonymizerFailedClosed` | `increase(veridicus_anonymizer_failed_closed_total[15m]) > 0` | `info` | Prometheus y fila «Anonimizador»; el humano revisa las reglas |
| `VeridicusAnonymizerOutboundCheck` | `increase(veridicus_anonymizer_failed_closed_total{reason="outbound_check"}[15m]) > 0` | `warning` | Ídem; hallazgo del enmascarado aunque nada haya salido |
| `VeridicusAnonymizerUnknownMarkers` | `increase(veridicus_anonymizer_unknown_markers_total[15m]) > 3` | `info` | Ídem |
| `VeridicusAnonymizerBusy` | `increase(veridicus_anonymizer_requests_total{result="busy"}[15m]) > 0` | `info` | Ídem; evaluar subir la concurrencia por PR con nueva medición |
| `VeridicusAnonymizerMemoryHigh` | `max(container_memory_working_set_bytes{container="anonymizer-proxy"}) / max(kube_pod_container_resource_limits{resource="memory",container="anonymizer-proxy"}) > 0.85` durante 5 min | `warning` | Ídem; nueva medición de pico y PR |
| `VeridicusAnonymizerDown` | `up{job="veridicus-anonymizer-proxy"} == 0` durante 5 min con el proxy habilitado | `warning` | Ídem; los turnos terminan en error, nada sale |
| `VeridicusExternalDnsBlocked` | `increase(coredns_dns_responses_total{zone=".",rcode="NXDOMAIN"}[15m]) > 0` | `warning` | Ídem; revisar qué pod consulta nombres externos (configuración nueva o intento de exfiltración) |

## 3. SLI y SLO

U10 no tiene objetivo de disponibilidad (COULD); sus objetivos son de confidencialidad y sobrecosto, y
solo rigen con el proxy habilitado.

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 de `veridicus_anonymizer_masking_seconds{operation="judge"}` | ≤ 0,25 s | Corrida de nivel 2 del PR de habilitación y ventana móvil de 1 h en el clúster |
| `failed_closed_total{reason="outbound_check"}` | 0 | Cada corrida de nivel 2 y cada día de uso |
| `failed_closed_total` (todas las razones) | 0 en el Golden Dataset | Cada corrida de nivel 2 |
| `requests_total{result="busy"}` | 0 | Corrida de NFR8.4 (50 sesiones, concurrencia 3) |
| Sesiones sin turnos en error con el proxy en el camino | ≥ 98 % | Corrida de NFR8.4 |
| p95 de `evaluated_at − submitted_at` con el proxy | ≤ 60 s | Corrida de nivel 2 del PR de habilitación (NFR3.5) |
| Consultas NXDOMAIN de la zona raíz en CoreDNS | 0 | Ventana móvil de 24 h desde el módulo 8 |

## 4. Logs y trazas

| Aspecto | Decisión |
|---|---|
| Formato | JSON por la salida estándar con el formateador de lista blanca de `libs/` (U3) y el perfil de U10: `request_id`, `operation`, `replacements`, `result`, `code`, `reason`, `upstream_status`, `unknown_markers`, `masking_ms`, `upstream_ms` |
| Volumen | Una línea por llamada, emitida tras borrar la tabla; `WARNING` para `failed_closed`, `rejected` y `failed`; `ERROR` al no arrancar, con el nombre del ajuste y nunca su valor |
| Agregación | `kubectl logs` con la rotación del kubelet de U2 (10 MiB × 5); sin Loki |
| Datos | Nunca texto del testimonio, nombres, marcadores restaurados, credencial, host del proveedor ni URL con parámetros; prueba *canary* de nivel 1 en cada PR |
| Correlación | `X-Request-Id` por llamada; `AnonymizerGateway` registra `turn_id` y `request_id`; el proxy registra `request_id` y no lo reenvía |
| Trazas distribuidas | No en el MVP; basta la correlación por `request_id` |
| Auditoría | Cabeceras `X-Veridicus-Masking-Rules` y `X-Veridicus-Model`; el SHA-256 del modelo queda en `model_digest` de C3 (NFR11.1) |

## 5. Paneles

| Panel | Contenido | Dónde |
|---|---|---|
| Fila «Anonimizador» del panel de U4 | Llamadas por `result`; cierres por `reason`; p95 de enmascarado y de destino; `busy`; memoria frente al límite; versión de reglas | JSON en `deploy/veridicus/dashboards/`, `ConfigMap` con `grafana_dashboard: "1"`; visible solo con el proxy habilitado |
| Fila «DNS externo» del panel de plataforma | NXDOMAIN de la zona raíz y consultas reenviadas por zona (`github.com`, host del ADR) | Mismo mecanismo; desde el módulo 8, con el proxy encendido o apagado |
