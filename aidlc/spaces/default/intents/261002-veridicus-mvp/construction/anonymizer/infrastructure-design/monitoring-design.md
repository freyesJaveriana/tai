# Diseño de monitoreo — U10 anonymizer

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01, la adenda 02 y el NFR Design revisión 2.**
Sustituye a la revisión 1 del 2026-10-03. Las métricas pasan al catálogo de
`contracts/metrics/anonymizer.v1.yaml` con las etiquetas `outcome` y `error_code` (NFRD-U10-02), el puerto
de métricas pasa de 8081 a 9090 (NFRD-U10-11) y el proxy ya no se entrega apagado, así que todo lo de
este documento rige desde que el módulo 8 instala Prometheus y Grafana. La alerta de DNS externo y su
indicador salen (§2 y §3, «Retirado»): la lista blanca de CoreDNS es de U2.

**Insumos.** De `nfr-design/` de esta unidad: observability-design §1–§7 (logs, catálogo de métricas,
salud, correlación, panel e indicadores), performance-design §1 y §6 (metas de 20 s y prueba de NFR8),
scalability-design §2 y §4 (mamparo y memoria), reliability-design §1 y §4 (estados y sondas),
security-design §7 (códigos de error) y logical-components §3 (dominios de falla). También:
functional-spec (§3.1, estados de una llamada), la tabla de fronteras de components, C16 y C21 de
contract-summary, la observabilidad de U2 (`platform/nfr-design/security-design.md` §11: raspado,
reglas informativas sin Alertmanager, sin Loki) e `infrastructure-specification.md` de esta carpeta.

Sin Alertmanager ni notificaciones en el MVP (`project.md`): cada alerta se ve en Prometheus y en el panel,
y la respuesta siempre es un PR. Ninguna regla cambia configuración ni apaga el proxy (AUTONOMIA-01).

## 1. Métricas y KPI

Recogidas por el `ServiceMonitor` de U2 sobre el puerto `metrics` (9090) cada 30 s. Todas las etiquetas
son enum de la lista cerrada de U1; nunca `run_id`, `model` ni `profile_name` (observability-design §3).

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_anonymizer_requests_total{outcome,error_code,provider,role,slot}` | Proxy | `outcome="failed_closed"` < 1 % por día; cada caso se mira | Volumen y desenlace; un cierre es un hallazgo de configuración o de detección aunque nada haya salido |
| `veridicus_anonymizer_requests_total{outcome="rejected"}` | Proxy | 0 en la corrida de NFR8 | `409`, `413` o `422` previos a `generate`: perfil desalineado o cuerpo demasiado grande |
| `veridicus_anonymizer_masking_seconds` (histograma) | Proxy | p95 ≤ 20 s con 250 000 caracteres; nunca cerca de 40,5 s | Presupuesto de seudonimización (NFR3.1, NFR3.5) |
| `veridicus_anonymizer_upstream_seconds{provider,role}` (histograma) | Proxy | Informativo; p95 frente a `model_call_timeout_s` = 270 s | Separa el tiempo del proveedor del propio (NFR3.6) |
| `veridicus_anonymizer_replacements_total{category}` | Proxy | Informativo | Una caída a 0 con tráfico indica datos o NER mal cargados |
| `veridicus_anonymizer_altered_markers_total{provider,role}` | Proxy | Informativo; la tasa la mide el nivel 2 de B11 | El modelo inventa o altera marcas (NFR6.2) |
| `veridicus_anonymizer_input_tokens_total`, `_output_tokens_total` | Proxy | Informativo | Costo por proveedor |
| `veridicus_anonymizer_inflight` | Proxy | Nunca 4 en el MVP (una corrida a la vez) | Saturación del mamparo (NFR8.2) |
| `veridicus_anonymizer_ready` | Proxy | 1 | Igual a `/readyz` 200 (NFR15.3) |
| `up{job="veridicus-anonymizer-proxy"}` | Prometheus | 1 | El raspado llega al pod |
| `container_memory_working_set_bytes{container="anonymizer-proxy"}` | kubelet (U2 lo raspa en 10250) | < 85 % del límite que renderiza el chart (≈ 1 825 361 101 bytes con 2 GiB) | Margen frente a `OOMKilled` (NFR8.1, NFR8.3) |

## 2. Alertas

Un `PrometheusRule` `veridicus-anonymizer` en el subchart de reglas de U2, con su prueba `promtool test
rules`: por cada alerta, un caso que dispara y otro que no. El límite de memoria se inyecta desde los
*values* del proxy, para no depender de `kube-state-metrics` (IDS-U10-10).

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusAnonymizerFailedClosed` | `increase(veridicus_anonymizer_requests_total{outcome="failed_closed"}[15m]) > 0` | `info` | Prometheus y panel; el humano revisa el log `anonymizer.call` por `run_id` |
| `VeridicusAnonymizerOutboundCheck` · Retirado | — | — | Retirado: el paso `outbound_check` ya no es etiqueta de métrica; queda en el log (security-design §3) y lo cubre `FailedClosed` |
| `VeridicusAnonymizerUnknownMarkers` → `VeridicusAnonymizerAlteredMarkers` | `increase(veridicus_anonymizer_altered_markers_total[15m]) > 3` | `info` | Ídem; U11 ya invalidó los hallazgos afectados |
| `VeridicusAnonymizerBusy` | `max_over_time(veridicus_anonymizer_inflight[15m]) >= 4` | `info` | Ídem; con una corrida a la vez no debería pasar nunca |
| `VeridicusAnonymizerMemoryHigh` | `max(container_memory_working_set_bytes{container="anonymizer-proxy"}) > 0.85 * <limits.memory en bytes>` durante 5 min | `warning` | Ídem; nueva medición del pico y PR de U2 |
| `VeridicusAnonymizerDown` | `up{job="veridicus-anonymizer-proxy"} == 0 or veridicus_anonymizer_ready == 0` durante 5 min | `warning` | Ídem; las corridas comerciales del clúster terminan en `anonimizador_no_disponible` y nada sale |
| `VeridicusAnonymizerProviderErrors` (nueva) | `increase(veridicus_anonymizer_requests_total{error_code=~"analysis.provider\|analysis.timeout"}[15m]) > 2` | `info` | Ídem; límite de tasa o caída del proveedor, sin reintento (reliability-design §3) |
| `VeridicusExternalDnsBlocked` · Retirado | — | — | Retirado: CoreDNS y su lista blanca son de U2 (con el hallazgo R-04 de la revisión 1) |

## 3. SLIs / SLOs

U10 no tiene objetivo de disponibilidad (una réplica en una máquina, reliability-design). Sus objetivos son
de confidencialidad y de tiempo, y son informativos salvo el de fugas, que bloquea en CI.

| SLI | SLO target | Measurement window |
|---|---|---|
| Valores sembrados en los cuerpos salientes (prueba de NFR1.3 con el NER real) | 0, bloqueante | Cada PR que toca `libs/anonymizer/**` (`cicd-pipeline.md` §2) |
| `requests_total{outcome="failed_closed"}` / total | < 1 % | Ventana móvil de 24 h en el clúster |
| p95 de `veridicus_anonymizer_masking_seconds` | ≤ 20 s | Reporte `-m perf` con 250 000 caracteres y ventana móvil de 24 h |
| `requests_total{error_code="analysis.anonymizer_unavailable"}` durante la prueba de NFR8 | 0 | Prueba de carga de NFR8 (50 sesiones en tandas de 3) |
| `OOMKilled` del proxy | 0 | Prueba de carga de NFR8 |
| `altered_markers_total` / llamadas restauradas | Se informa | Nivel 2 de B11 (NFR4.1) |
| Consultas NXDOMAIN de la zona raíz · Retirado | — | Retirado con la alerta de DNS (U2) |

## 4. Logs y trazas

| Aspecto | Decisión |
|---|---|
| Formato | JSON por línea en `stdout`, con el formateador de lista blanca tipada de `libs/` y el perfil de U10 (observability-design §1): `anonymizer.call`, `anonymizer.startup` y `anonymizer.startup_failed` |
| Agregación | `kubectl logs` con la rotación del kubelet de U2; sin Loki |
| Datos | Nunca testimonio, nombres, marcas restauradas, claves, cuerpos del proveedor ni mensajes de excepción; prueba *canary* de niveles 0 y 1 en cada PR, y la captura de logs de todos los contenedores de U2 en nivel 1 |
| Correlación | `run_id` del cuerpo de C21, solo en el log del proxy; nunca va al proveedor. `X-Request-Id` de entrada se ignora |
| Trazas distribuidas | No en el MVP: con una llamada a la vez, `run_id`, `masking_ms` y `upstream_ms` bastan |
| Auditoría | Cada llamada queda en el `ModelCall` que U11 registra con `anonymized: true`; el arranque deja los SHA-256 de los datos y del NER (NFR11.1) |

## 5. Paneles

| Panel | Contenido | Dónde |
|---|---|---|
| «Anonimizador» | Llamadas por `outcome` y `provider`; p95 de `masking_seconds` con líneas en 20 s y 40,5 s; p95 de `upstream_seconds` por proveedor; reemplazos por categoría; marcas alteradas; `inflight` frente a 4; *tokens* por proveedor; `ready` | Fuente: `services/anonymizer-proxy/observability/grafana-dashboard.json`. U2 lo copia a `charts/monitoring-rules/dashboards/` con el mismo SHA-256 (NFRD-U10-09, IDS-U10-08) |
| Fila «DNS externo» · Retirado | — | Retirado: es de U2 |
