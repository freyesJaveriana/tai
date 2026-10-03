# Diseño de monitoreo — U5 human-review

**Insumos.** Logs, métricas, SLI y panel de `nfr-design/observability-design.md`
(observability-design); presupuestos de `nfr-design/performance-design.md` (performance-design);
*timeouts*, fallos de métricas y salud de `nfr-design/reliability-design.md` (reliability-design);
cardinalidad y señales para escalar de `nfr-design/scalability-design.md` (scalability-design); texto
fuera de logs y métricas de `nfr-design/security-design.md` (security-design §6); dominios de falla de
`nfr-design/logical-components.md` (logical-components §2); eventos de F1–F5 de
`functional-design/functional-spec.md` (functional-spec); módulo HumanReview de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de
`platform/infrastructure-design/monitoring-design.md` (U2), monitoreo de `session-api` de
`identity-access/infrastructure-design/monitoring-design.md` (U3) y de
`text-flow/infrastructure-design/monitoring-design.md` (U4); `infrastructure-specification.md` de esta
carpeta.

U5 usa la pila de U2: Prometheus y Grafana desde el módulo 8, sin Alertmanager; logs JSON por salida
estándar; sin trazas. Antes del módulo 8, las mismas señales se leen en `/metrics` con
`kubectl port-forward` y en `kubectl logs`.

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| `veridicus_review_decisions_total` por `state` | `session-api` `:8081/metrics`, `ServiceMonitor` de U3 cada 30 s | Informativo | Ritmo de revisión del analista; base del MTTV (NFR7.1) |
| `veridicus_review_rejections_total{code="review.cot_not_viewed"}` | Ídem | > 0 en 15 min | La consola nunca envía «aceptar» sin CoT consultada: un rechazo indica un cliente que no es la consola (AUTONOMIA-03, NFR10.3) |
| `veridicus_review_rejections_total` por otros `code` | Ídem | Informativo | `invalid_transition` repetido señala reenvíos manuales tras un `503` (NFR10.16) |
| `veridicus_session_dismissal_ratio` por `session_id` | Ídem | > 0,25 (regla de U2) | Señal AIR: propone revisar el umbral, nunca lo cambia (NFR15.4, NFR11.4) |
| `count(veridicus_session_dismissal_ratio)` | Ídem | > 200 series | Cardinalidad de C15 (NFR8.6); primera señal para retirar la etiqueta `session_id` (scalability-design §6) |
| Memoria de la API / `limits.memory` | cAdvisor (U2) | > 0,9 durante 5 min | La suma de U3–U5 debe quedar bajo 768 MiB (NFR8.1); alerta común de U2 |
| `session-api` lista | kube-state-metrics | No lista durante 2 min | Sin base o con configuración de U5 inválida no hay revisión (NFR10.18); alerta común de U3 |

## 2. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusReviewCotNotViewed` (nueva) | `increase(veridicus_review_rejections_total{code="review.cot_not_viewed"}[15m]) > 0` | info (P3) | Panel «Veridicus — AIR»; revisión manual del cliente |
| `VeridicusDismissalSeriesHigh` (nueva) | `count(veridicus_session_dismissal_ratio) > 200` | warning (P3) | Panel «Veridicus — AIR»; abre un PR de cambio de C15 |
| `VeridicusAirThresholdProposal` (de U2) | `max by (session_id) (veridicus_session_dismissal_ratio) > 0.25` | info (P3) | Panel «Veridicus — AIR»; la anotación **propone** un umbral |
| `VeridicusSessionApiNotReady` (de U3) | Pod no listo durante 2 min | critical (P3) | Panel «Veridicus — plataforma» |

Las dos reglas nuevas van en la `PrometheusRule` del subchart `session-api`, con anotación `runbook`
hacia `docs/operacion/instalacion.md`. Ninguna notifica a nadie en el MVP. `promtool test rules` las
prueba con un caso que dispara y otro que no; para la AIR, U5 entrega
`services/session-api/tests/human_review/fixtures/air_series.yaml` (una sesión en 0,25 sin alerta,
otra en 0,375 con alerta, y la misma sesión publicada por dos pods que produce **una** sola alerta).

## 3. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 de la decisión `201` | ≤ 200 ms (NFR3.1); ≤ 200 ms con 250 sugerencias y 10 rondas (NFR8.2) | Prueba `perf` de nivel 1 (200 decisiones) en cada PR de `session-api` |
| p95 de `cot-views` `204` | ≤ 100 ms (NFR3.2) | Prueba `perf` (100 primeras + 100 repetidas) |
| p95 de los rechazos `403`/`409`/`422` | ≤ 100 ms y 0 filas (NFR3.3) | Prueba `perf` (50 por `code`) |
| p95 de las operaciones de C11 en una transacción | ≤ 150 ms (NFR3.5) | Prueba `perf` (200 repeticiones) |
| p95 de `GET /metrics` con 60 series | ≤ 100 ms (NFR3.6) | Prueba `perf` |
| Esperas por bloqueo (`WARNING` `system.unavailable` en rutas de U5) | 0 | Cada corrida de nivel 3 (`review.spec.ts`) |
| `review.spec.ts` | 0 fallos (NFR8.7) | Cada corrida de nivel 3 antes de etiquetar una entrega |
| Clic → estado visible en la tarjeta | ≤ 1 s (NFR3.7, NFR3.8) | Playwright de nivel 3 |

No hay histograma por ruta en Prometheus: las latencias se miden en las pruebas, como en U3. No se
fija disponibilidad mensual (U2 §4).

## 4. Logs y trazas

| Aspecto | Diseño |
|---|---|
| Formato | JSON de una línea con el formateador de lista blanca de U3: `timestamp`, `level`, `service`, `request_id`, `event` y solo `session_id`, `suggestion_id`, `round_id`, `decision_id`, `report_version_id`, `user_id`, `state`, `previous_state`, `kind`, `first`, `code`, `duration_ms` (NFR15.5, NFR10.6) |
| Eventos `INFO` | `review.decision_recorded`, `review.decision_rejected`, `review.cot_viewed`, `review.round_opened`, `review.round_locked`, emitidos tras el *commit* o el *rollback* |
| Eventos `WARNING` / `ERROR` | *Timeout* de bloqueo o sentencia (`system.unavailable`, `duration_ms`); `metrics.update_failed` (NFR10.17); base sin respuesta |
| Texto del analista | Nunca: `hide_parameters=True` en el *engine*, Problem Details sin interpolar (NFR10.7) |
| Dónde se leen | `kubectl logs -n veridicus deploy/session-api`; rotación del kubelet (10 MiB × 5); sin agregación central |
| Trazas | No hay: U5 vive en un solo proceso; `request_id` correlaciona dentro de una petición y `suggestion_id`/`round_id` entre peticiones |

## 5. Paneles

| Panel | Lo que aporta U5 |
|---|---|
| Veridicus — AIR (de U2) | Razón de descarte por sesión con la línea de 0,25; `rate(veridicus_review_decisions_total[5m])` por `state`; rechazos por `code`; conteo de series de la razón frente a 200 |
| Veridicus — plataforma (de U2) | Memoria de la API frente a 768 MiB, que ya incluye a U5 |

El panel solo muestra contadores, enums y UUID de sesión (NFR10.8); vive como JSON en
`deploy/veridicus/dashboards/` con la etiqueta `grafana_dashboard: "1"` y cambia por PR.
