# Diseño de monitoreo — U8 assistant-extras

**Revisión 2 (2026-11-23): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Design
revisión 2.** Sustituye a la revisión 1 del 2026-10-03, que queda en el historial de Git.
- **Qué cambia.** Salen las seis métricas de los extras, las cinco reglas informativas y el panel «Veridicus —
  extras» (IDS-U8-01). Entran los dos contadores de `contracts/metrics/assistant-extras.v1.yaml`
  (NFRD-U8-06), los eventos de la aclaración y dos paneles en el panel de U4.
- **Numeración.** §1–§5 conservan su tema. Lo nuevo es §6.

**Insumos.**
- Logs, métricas, SLI y panel de `nfr-design/observability-design.md` (observability-design §1–§4).
- Del resto de `nfr-design/`:
  - presupuestos de `nfr-design/performance-design.md` (performance-design §1, §4, §8);
  - señales de escalado de `nfr-design/scalability-design.md` (scalability-design §5);
  - arranque, decisión y fallos de `nfr-design/reliability-design.md` (reliability-design §4, §5, §7, §10);
  - centinela y campos tipados de `nfr-design/security-design.md` (security-design §7, NFRD-U8-07);
  - radio de impacto de `nfr-design/logical-components.md` (logical-components §2).
- Reglas de descarte y estados de `functional-design/functional-spec.md` (functional-spec §3, §9).
- Procesos de `inception/domain-design/components.md` (components).
- C15, C16 y C19 de `inception/contract-design/contract-summary.md` (contract-summary).
- Pila común de U2 y monitoreo de U4 (sus `monitoring-design.md`, revisión 2).
- `infrastructure-specification.md` de esta carpeta.

U8 usa la pila de U2: Prometheus y Grafana desde el módulo 8, sin Alertmanager, sin Loki y sin trazas, y
logs JSON por salida estándar con la rotación del kubelet. **No añade objetivos de raspado.** Sus dos
contadores salen por el puerto `metrics` 8081 de la API y del trabajador de `session-api`, que ya raspan los
`ServiceMonitor` de U3 y U4 (IDS-U8-06). La biblioteca no exporta métricas (U11). Los descartes por regla
viven en los logs y en la sección `clarifications` de C19 v2.

## 1. Métricas y KPI

Declaradas en `contracts/metrics/assistant-extras.v1.yaml`, con la forma de C15 y etiquetas de la lista
cerrada de U1. Una prueba de nivel 0 recorre `/metrics` tras una ingesta y una decisión de cada estado, y
falla ante un nombre, una etiqueta o un valor fuera del archivo (observability-design §2).

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| `veridicus_conductor_observations_ingested_total` | Trabajador de `session-api`, tras el `COMMIT` de la ingesta, por fila insertada | Sin umbral; se muestra | Cuántas aclaraciones llegan al analista (NFR15.1) |
| `veridicus_conductor_observation_decisions_total{state}` (`approved`, `discarded`) | API de `session-api`, tras el `COMMIT` de la decisión | Sin umbral; se muestra | Cuántas aprueba o descarta el analista; ninguna se decide sola (AUTONOMIA-03) |
| `veridicus_model_input_tokens_total` y `_output_tokens_total{role="verifier_permuted"}` (U4) | Trabajador, desde `ModelCall` | Sin umbral; se muestra | Costo de la permutación en el clúster; la permutación no tiene métrica propia (observability-design §2) |
| `veridicus_runs_total{error_code="analysis.invalid_output"}` (U4) | Trabajador | Cualquier aumento se revisa en el panel | Una aclaración inválida en la ingesta invalida la corrida entera (BR5.9) |
| `veridicus_runs_total{error_code="analysis.system"}` (U4) | Trabajador | La regla de U4 (§2) | Incluye una excepción del módulo (reliability-design §10) |
| Memoria de `semantic-agent` frente a su límite (U4) | `container_memory_working_set_bytes` (U2) | > 0,9 del límite durante 5 min, regla de U4 | El módulo suma ≤ 5 MiB con un margen estrecho (IDS-U8-02) |

Ninguna etiqueta lleva `session_id`, `observation_id` ni texto (NFR10.8).

## 2. Alertas

U8 **no crea reglas**: el MVP no tiene Alertmanager, y las cifras de nivel 2 se revisan en el PR
(observability-design §4). Los fallos de U8 que importan en el clúster ya los cubren reglas informativas de
U4, que no notifican a nadie:

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| `VeridicusRunSystemError` (U4) | `increase(veridicus_runs_total{error_code="analysis.system"}[15m]) > 0`, que incluye una excepción del módulo de aclaraciones | warning (P3) | Panel «Veridicus — corridas». El runbook suma buscar `exc_type` en los logs de `semantic-agent` con el `run_id` |
| `VeridicusU4PodNearMemoryLimit` (U4) | Memoria / límite > 0,9 durante 5 min en `semantic-agent` o en el trabajador | warning (P3) | Panel «Veridicus — plataforma» de U2 |
| `VeridicusRunQueueBacklog` (U4) | `veridicus_run_queue_depth > 20` durante 10 min | warning (P3) | Panel «Veridicus — corridas»; primera medida: scalability-design §5 de U8 |
| Alertas de los extras de la revisión 1 | — | **Retirado** (IDS-U8-01) | — |

Una regla `analysis.invalid_output` propia no se añade: un resultado así solo llega si alguien escribe en la
cola sin la biblioteca (T21), y queda a la vista en el panel de corridas por `error_code`.

## 3. SLIs / SLOs

Son objetivos de verificación del MVP, no SLO con ventana de producción (observability-design §3).

| SLI | SLO target | Measurement window |
|---|---|---|
| Citas en los temas emitidos (comprobador independiente) | **0** coincidencias; bloquea (NFR4.3) | `clarifications.run` sobre el conjunto sintético, una vez por PR que toca rutas de U8 (§7 de `infrastructure-specification.md`) |
| Vocabulario de C8 y regla de DT23 en los temas | **0** (NFR10.5 (d)) | La misma corrida |
| Tasa de descarte por regla | Se reporta; > 0,50 pone `review_signal: true` (NFR4.6) | La misma corrida |
| p95 de la corrida incremental con `comercial-piloto` y la permutación | ≤ 180 s (NFR3.1) | `permutation_cost` |
| Corridas con `todo-local` sin `tiempo_agotado` | ≥ 98 % (NFR8.7) | `permutation_cost` |
| Corridas que terminan `done` o `error` con `code` del catálogo | 100 % (NFR8.7) | `permutation_cost` |
| Crecimiento del `VmHWM` del verificador | ≤ 1 % (NFR8.3, NFRD-U8-11) | `permutation_cost`, tras el calentamiento y al final |
| Decisión | p95 ≤ 300 ms con 100 decisiones (NFR3.8) | Prueba `perf` de nivel 1 |
| Sondeo con aclaraciones | p95 ≤ 200 ms con `since`, ≤ 1 s sin él (NFR3.9) | Prueba `perf` de nivel 1 |
| Panel actualizado | ≤ 3 s desde el `COMMIT` de la ingesta (NFR3.10) | Playwright de nivel 3 |
| Fallos atribuibles a U8 en el humo | 0, con el par `verifier` y `verifier_permuted` presente (NFR8.6, NFR3.12) | Cada despliegue |
| Picos de `semantic-agent` y del trabajador en la carga | Dentro de 1,2 × pico ≤ límite (NFR8.3) | `run_batches.py --prometheus-url`, con el monitoreo encendido |

## 4. Logs & Tracing

| Aspecto | Diseño |
|---|---|
| Formato | El formateador JSON de lista blanca de U3, ampliado solo para los eventos `clarification.*` y `conductor_observation.*` con `observation_id`, `source_finding_id`, `rule`, `state`, `emitted`, `discarded`, `inserted` y `existing` (NFRD-U8-07, petición a U3). Nunca el tema, las citas, el `hecho` ni el texto de los turnos (NFR10.8) |
| Eventos | `clarification.discarded` y `clarification.summary` (`INFO`, emitidos por quien llama a la biblioteca: `semantic-agent` o la CLI con su catálogo cerrado); `conductor_observation.ingested` (`INFO`) y `conductor_observation.invalid` (`WARNING`) en el trabajador; `conductor_observation.decided` (`INFO`) en la API; excepción del módulo (`ERROR`, solo `run_id` y `exc_type`) (observability-design §1) |
| Correlación | `run_id` une la corrida con la ingesta; `observation_id` y `session_id` unen la ingesta con la decisión. Prueba de nivel 1 que sigue una aclaración solo por sus logs (NFR15.3) |
| Dónde se leen | `kubectl logs -n veridicus deploy/veridicus-semantic-agent`, `deploy/veridicus-session-api-worker` y `deploy/veridicus-session-api` (solo lectura); en la anfitriona, la salida de error de la CLI |
| Centinela | Una cadena sembrada en un `hecho`, en las dos citas y en un turno aparece **0 veces** en los logs, en `/metrics` y en los eventos de descarte (security-design §7). Nivel 0 en la biblioteca y nivel 1 en los servicios |
| Trazas | Sin trazas distribuidas: la correlación por identificadores cubre el flujo |

## 5. Paneles

| Panel | Contenido de U8 |
|---|---|
| Veridicus — corridas (panel de U4, empaquetado por U2) | Dos paneles nuevos: aclaraciones ingeridas por minuto (`rate` del contador de ingesta) y decisiones por `state`. Viven en el original de U4 en `services/session-api/observability/` y se copian al chart con el mismo SHA-256 (IDS-U8-05) |
| Veridicus — plataforma (U2) | Sin cambios: memoria y CPU de `semantic-agent` y del trabajador frente a su límite |
| Veridicus — extras | **Retirado** (IDS-U8-01) |

Los paneles se validan con la comprobación de JSON de paneles de U2 y solo se renderizan con
`monitoring.enabled: true`. Solo muestran contadores y etiquetas de enum cerradas.

## 6. Retirado de la revisión 1

Salen las métricas `veridicus_extras_enabled`, `veridicus_extra_judge_duration_seconds`,
`veridicus_permutation_claims_total`, `veridicus_suggested_questions_total`,
`veridicus_affective_notes_total` y `veridicus_question_decisions_total`. Salen también las alertas
`VeridicusExtrasQueueBacklog`, `VeridicusQuestionOutputRejected`, `VeridicusSecondReadRetrying`,
`VeridicusQuestionDeadlineSkips` y `VeridicusExtrasOnDevMachine`, los eventos `turn.permutation`,
`turn.question`, `turn.affective` y `question.decided`, y la etiqueta externa `cluster`. Todo salió con el cambio
01 (IDS-U8-01).
