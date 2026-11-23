# Diseño de monitoreo — U5 human-review

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** U5 publica solo las dos métricas de C15 v2; `veridicus_review_rejections_total` y sus dos
  alertas quedan «Retirado» (IDS-U5-06). La regla AIR es de U2 sin `max by` (IDS-U5-04). Entran los eventos
  de descarte de la copia, de purga y de retirada de series, la reconciliación de series y los SLI de
  `observation-views` (150 ms) y de `purge_session`.
- **Numeración.** §1–§5 conservan su tema; §6 lista lo retirado.

**Insumos.** Logs, métricas, SLI, panel y alertas de `nfr-design/observability-design.md`
(observability-design §1–§4); presupuestos de `nfr-design/performance-design.md` (performance-design §1–§3,
§6); *timeouts*, orden de las métricas y salud de `nfr-design/reliability-design.md` (reliability-design §3,
§4); cardinalidad y señales para escalar de `nfr-design/scalability-design.md` (scalability-design §5, §6);
lista blanca de `nfr-design/security-design.md` (security-design §6); dominios de falla de
`nfr-design/logical-components.md` (logical-components §2); eventos de F1–F7 de
`functional-design/functional-spec.md` (functional-spec); HumanReview de
`inception/domain-design/components.md` (components); C15 v2 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); pila común de
`platform/infrastructure-design/monitoring-design.md` (U2) y monitoreo de `session-api` de U3;
`infrastructure-specification.md` de esta carpeta.

U5 usa la pila de U2: Prometheus y Grafana desde el módulo 8, sin Alertmanager, sin Loki y sin trazas; logs
JSON por salida estándar con la rotación del kubelet. No añade `ServiceMonitor`: la API ya la raspa el de U3
en el puerto `metrics` 8081 cada 30 s. Antes del módulo 8, las mismas señales se leen en `/metrics` con
`kubectl port-forward` de solo lectura y en `kubectl logs`.

## 1. Métricas y KPI

Las dos métricas están declaradas en `contracts/metrics/review.v2.yaml` (C15 v2); una prueba de nivel 0 valida
cada etiqueta registrada contra su patrón (enum o UUID).

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_review_decisions_total{state}` | API de `session-api`, `after_commit` de `decide` | Sin umbral; se muestra | Ritmo de revisión del analista; base del MTTV (NFR7.1) |
| `veridicus_session_dismissal_ratio{session_id}` | API, `apply` tras `decide`; retirada tras `lock_round`, `discard_correction_round` y la reconciliación | > 0,25 (regla de U2) | Señal AIR: propone revisar el umbral por PR, nunca lo cambia (NFR15.4, NFR11.4) |
| `count(veridicus_session_dismissal_ratio)` | Ídem | 200 series (línea en el panel, sin regla) | Cardinalidad de C15 (NFR8.6); primera señal para escalar (scalability-design §6) |
| Memoria de la API / `limits.memory` | cAdvisor (U2) | > 0,9 durante 5 min | U5 suma ≤ 32 MiB al pico de la API (NFR8.1); regla común `VeridicusContainerNearMemoryLimit` de U2 |
| `veridicus-session-api` lista | kube-state-metrics (U2) | No lista durante 2 min | Sin base, con Redis caído o con la configuración de U5 inválida no hay revisión (NFR10.18); regla común `VeridicusPodNotReady` de U2 |

Los rechazos se cuentan en los logs con `review.decision_rejected` y su `code` (§4), no con una métrica.

## 2. Alertas

Ninguna avisa a nadie en el MVP: son reglas sin Alertmanager que se ven en Prometheus y en los paneles. U5 no
añade reglas propias (observability-design §4).

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusAirThresholdProposal` (de U2, en `charts/monitoring-rules/`) | `veridicus_session_dismissal_ratio > 0.25` | info (P3) | Panel «Veridicus — AIR»; la anotación **propone** revisar el umbral y no tiene acción |
| `VeridicusPodNotReady` (de U2) | Pod no listo durante 2 min | warning (P3) | Panel «Veridicus — plataforma» |
| `VeridicusContainerNearMemoryLimit` (de U2) | Memoria / límite > 0,9 durante 5 min | warning (P3) | Panel «Veridicus — plataforma» |
| `VeridicusReviewCotNotViewed` | **Retirado** (IDS-U5-06) | — | — |
| `VeridicusDismissalSeriesHigh` | **Retirado** (IDS-U5-06): la señal de 200 series pasa al panel | — | — |

**Prueba de la regla AIR.** U5 entrega `services/session-api/tests/human_review/fixtures/air_series.yaml`, con
una sesión en 0,25 (sin alerta) y otra en 0,375 (con alerta), calculadas con *W* = 8 de C25. U2 lo usa en su
prueba `promtool test rules` junto a sus propios casos (NFRD-U2-12). Durante un `RollingUpdate` la misma sesión
puede alertar desde los dos pods hasta ≤ 60 s; se acepta (IDS-U5-05).

## 3. SLIs / SLOs

Son objetivos de verificación del MVP medidos en las pruebas, no SLO con ventana de producción: no hay
histograma por ruta en Prometheus (observability-design §3) ni porcentaje de disponibilidad mensual (U2 §4).

| SLI | SLO target | Measurement window |
|---|---|---|
| p95 de la decisión `201` | ≤ 200 ms (NFR3.1); ≤ 200 ms con 250 sugerencias y 10 rondas (NFR8.2) | Prueba `perf` de nivel 1, 200 decisiones, en cada PR de `session-api` |
| p95 de `observation-views` `204` | ≤ 150 ms (NFR3.2), igual la primera vez que al repetirla | Prueba `perf` |
| p95 de los rechazos `401`/`403`/`404`/`409`/`413`/`422` | ≤ 100 ms y 0 filas (NFR3.3) | Prueba `perf`, 50 por `code` |
| Sentencias de U5 por decisión | ≤ 6 (tope 7, NFR3.4) | Contador de sentencias con 1, 4 y 10 rondas |
| p95 de C11 en la transacción de U7 | ≤ 150 ms; `open_correction_round` y `discard_correction_round` ≤ 50 ms cada una (NFR3.5) | Prueba `perf`, 200 repeticiones |
| p95 de `GET /metrics` | ≤ 100 ms con 60 series (NFR3.6) | Prueba `perf` |
| p95 de `purge_session` en el peor caso | ≤ 2 s y ninguna sentencia sobre el `statement_timeout` (NFR3.9) | Prueba `perf`, 20 repeticiones con *rollback* |
| Series vivas tras la reconciliación | ≤ 30 con 60 sesiones (20 consolidadas, 5 descartadas, 5 purgadas) (NFR8.6) | Prueba de nivel 1 |
| Clic → estado visible en la tarjeta | ≤ 1 s (NFR3.7, NFR3.8) | Playwright de nivel 3 |
| Esperas por bloqueo (`WARNING` `system.unavailable` en rutas de U5) | 0 | Cada corrida de nivel 3 |
| `frontend/e2e/review.spec.ts` | 0 fallos (NFR8.7) | Cada corrida de nivel 3 antes de etiquetar una entrega |

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Formato | JSON de una línea con el formateador de lista blanca de U3 en `libs/`: `timestamp`, `level`, `service`, `event`, `request_id` y solo `session_id`, `suggestion_id`, `round_id`, `decision_id`, `user_id`, `state`, `previous_state`, `code`, `kind`, `first`, `cause`, duraciones y conteos (NFR15.5, NFR10.6) |
| Eventos `INFO` | `review.decision_recorded`, `review.decision_rejected`, `review.observations_viewed`, `review.round_opened`, `review.round_locked`, `review.round_discarded`, `review.session_purged`, `review.series_retired` (con `cause`: `locked`, `discarded`, `reconciled`); todos en `after_commit` o tras el *rollback* |
| Eventos `WARNING` / `ERROR` | *Timeout* de bloqueo o de sentencia (`system.unavailable`, `duration_ms`); `metrics.update_failed`; fallo de la reconciliación; base sin respuesta |
| Texto del analista | Nunca: `hide_parameters=True` en el *engine* (NFRD-U5-10), Problem Details sin interpolar y etiquetas validadas (NFR10.7, NFR10.8) |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-session-api` (y `deploy/veridicus-session-api-worker`, `job/veridicus-retention`), solo lectura; rotación del kubelet (10 MiB × 5) |
| Trazas | No hay: U5 vive en un proceso por petición; `request_id` correlaciona dentro de una petición y `suggestion_id` / `round_id` entre peticiones. Una prueba de nivel 1 reconstruye la historia de una sugerencia solo con los logs y encuentra la cadena centinela 0 veces |

## 5. Paneles

| Panel | Lo que aporta U5 |
|---|---|
| Veridicus — AIR (de U2) | Razón de descartes por sesión con la línea de 0,25; `rate(veridicus_review_decisions_total[5m])` por `state`; **petición a U2** (IDS-U5-06): conteo de series de la razón con la línea de 200 |
| Veridicus — plataforma (de U2) | Memoria de la API frente a su límite de 1,125 GiB, que ya incluye a U5 |

Los paneles solo muestran contadores, enums y UUID de sesión (NFR10.8). Viven como JSON en
`charts/monitoring-rules/dashboards/` de U2 y cambian por PR; se renderizan solo con `monitoring.enabled: true`.

## 6. Retirado de la revisión 1

Salen `veridicus_review_rejections_total`, las alertas `VeridicusReviewCotNotViewed` y
`VeridicusDismissalSeriesHigh`, la agregación `max by (session_id)` de la regla AIR y su caso de dos pods, el
evento `review.cot_viewed` (lo sustituye `review.observations_viewed`), la `PrometheusRule` en el subchart
`session-api`, el panel en `deploy/veridicus/dashboards/` y el límite de 768 MiB como referencia de memoria.
