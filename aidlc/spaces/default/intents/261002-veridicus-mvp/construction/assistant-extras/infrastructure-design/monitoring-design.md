# Diseño de monitoreo — U8 assistant-extras

**Insumos.** Logs, métricas, SLI y reglas informativas de `nfr-design/observability-design.md`
(observability-design); presupuestos y plazo de `nfr-design/performance-design.md`
(performance-design); señal de escalado de `nfr-design/scalability-design.md` (scalability-design);
fallos por llamada y validación al arrancar de `nfr-design/reliability-design.md` (reliability-design);
logs sin datos sensibles de `nfr-design/security-design.md` (security-design §7); radio de impacto de
`nfr-design/logical-components.md` (logical-components); motivos de omisión de
`functional-design/functional-spec.md` (functional-spec); procesos de
`inception/domain-design/components.md` (components); C15 y C16 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta **P1 = A** de
`infrastructure-design-questions.md` (extras encendidos solo en la máquina de demostración); pila de U2 y
monitoreo de U4 (sus `monitoring-design.md`); `infrastructure-specification.md` de esta carpeta.

U8 usa la pila de U2 (Prometheus y Grafana desde el módulo 8, sin Alertmanager; logs JSON por salida
estándar; sin trazas) y los `ServiceMonitor` de U4 sobre el puerto `metrics` 8081: no añade objetivos de
*scrape*. Con P1 = A, las métricas de los extras solo se mueven en la máquina de demostración; en la de
desarrollo `veridicus_extras_enabled` vale 0 y el resto queda en 0.

## 1. Métricas y KPI

| Métrica | Fuente | Umbral | Por qué importa |
|---|---|---|---|
| `veridicus_extras_enabled{extra}` | `session-api`, al arrancar | En la máquina de desarrollo, cualquier valor 1 es un error de despliegue | Dice qué extras corren; P1 = A |
| `veridicus_extra_judge_duration_seconds{call, result}` | `semantic-agent`, por llamada de U8 al juez | p95 de `call="second_read"` > 50 s; p95 de `call="question"` > 30 s; `result="unavailable"` > 5 en 15 min | Presupuestos de performance-design §1 y reintentos de la segunda lectura (NFR10.12) |
| `veridicus_permutation_claims_total{sustained}` | `semantic-agent`, tras la regla | Tasa `sustained="true"` < 65 % en 24 h | La activación de la permutación exige > 65 % (NFR4.4) |
| `veridicus_suggested_questions_total{outcome, reason}` | `semantic-agent`, política de la pregunta | `reason=~"invalid_schema\|forbidden_vocabulary"` > 3 en 15 min; `reason="timeout"` > 30 % de los turnos en 1 h | Separa fallos de la pregunta por motivo (NFR15.4) y avisa si el plazo no alcanza |
| `veridicus_affective_notes_total` | `semantic-agent` | Sin umbral; se muestra | Frecuencia del indicio (NFR10.10) |
| `veridicus_question_decisions_total{status}` | API de `session-api`, tras el `COMMIT` | Sin umbral; se muestra | Cuántas preguntas aprueba o descarta el analista |
| `veridicus_turn_queue_depth` (U4) con extras | Trabajador | > 20 durante 10 min con `max(veridicus_extras_enabled) == 1` | Con extras caben 24 turnos sin vencer (NFR8.2) |
| Memoria de juez, `semantic-agent` y trabajador / su límite (U4) | cAdvisor | > 0,85 durante 5 min | Los extras no deben subir picos (NFR8.3) |

Todas las etiquetas son enums cerrados; una prueba de nivel 0 recorre `/metrics` y falla ante una
etiqueta fuera de su enum (NFR10.8).

## 2. Alertas

| Alerta | Condición | Severidad | Va a |
|---|---|---|---|
| `VeridicusExtrasQueueBacklog` | `max(veridicus_extras_enabled) == 1 and veridicus_turn_queue_depth > 20` durante 10 min | warning (P3) | Panel «Veridicus — extras» |
| `VeridicusQuestionOutputRejected` | `increase(veridicus_suggested_questions_total{reason=~"invalid_schema\|forbidden_vocabulary"}[15m]) > 3` | warning (P3) | Panel «Veridicus — extras» |
| `VeridicusSecondReadRetrying` | `increase(veridicus_extra_judge_duration_seconds_count{call="second_read", result="unavailable"}[15m]) > 5` | warning (P3) | Panel «Veridicus — evaluación» de U4 |
| `VeridicusQuestionDeadlineSkips` | Omisiones con `reason="timeout"` / preguntas pedidas > 0,3 en 1 h | info (P3) | Panel «Veridicus — extras» |
| `VeridicusExtrasOnDevMachine` | `max(veridicus_extras_enabled{cluster="dev"}) == 1` | warning (P3) | Panel «Veridicus — extras» |

Ninguna regla despierta a nadie ni cambia nada (observability-design §4, FR9.1). Cada una lleva su
anotación `runbook` y su prueba `promtool test rules` en nivel 0, con un caso que dispara y otro que
no. La etiqueta externa `cluster` (`dev` o `demo`) la fijan los *values* de Prometheus de cada máquina.

## 3. SLI y SLO

| SLI | SLO | Ventana de medición |
|---|---|---|
| p95 de `evaluated_at − submitted_at` con extras | ≤ 150 s (NFR3.1) | Corrida de nivel 2 con `--extras all` en CPU |
| Tasa en línea de la permutación | > 65 % para encenderla (NFR4.4) | Corrida de nivel 2; 24 h en la máquina de demostración |
| Preguntas publicadas en el caso de Hecho No Documentado | 0 (NFR4.3) | Corrida de nivel 2 |
| Turnos con extras terminados | 100 % `evaluated` o `error` con `code` del catálogo, 0 `turn.error.timeout` (NFR8.7) | Corrida de nivel 2 |
| Fallos atribuibles a U8 en `scripts/smoke.sh` | 0 (NFR8.6) | Cada despliegue (120 s en desarrollo, 300 s en demostración) |
| Tarjeta de la pregunta visible | ≤ 3 s desde `evaluated_at` (NFR3.10) | Prueba Playwright de nivel 3 |
| Decisión sobre una pregunta | p95 ≤ 300 ms con 100 decisiones (NFR3.8) | Prueba `perf` de nivel 1 |

## 4. Logs y trazas

| Aspecto | Diseño |
|---|---|
| Formato | Formateador JSON con lista blanca de U3, ampliado con `claim_index`, `sustained`, `question_id`, `status`, `reason`, `outcome` y `matched`; nunca el texto de la pregunta, de afirmaciones, pasajes, la CoT de la segunda lectura ni la palabra afectiva (NFR15.2, NFR10.8) |
| Eventos | `turn.permutation`, `judge.retry` con `reason = second_read`, `turn.question` (`published` u `omitted` con `reason`; `WARNING` para `invalid_schema`, `forbidden_vocabulary`, `timeout`, `unavailable`, `too_long`), `turn.affective`, `question.decided` (NFR15.3, NFR15.4) |
| Correlación | `turn_id` + `attempt` + `message_id` en `semantic-agent`; `question_id` + `turn_id` en `session-api` |
| Dónde se leen | `kubectl logs -n veridicus deploy/semantic-agent` y `deploy/session-api`; rotación del kubelet de U4 |
| Trazas | No hay trazas distribuidas; la correlación por identificadores cubre el flujo |
| Verificación | Prueba de nivel 1 con una cadena centinela en el turno, la pregunta del juez *fake* y la CoT de la segunda lectura: 0 coincidencias en logs y en `/metrics` |

## 5. Paneles

| Panel | Contenido |
|---|---|
| Veridicus — extras (nuevo, SHOULD de U2) | Extras activos por máquina; duración de la segunda lectura y de la pregunta por resultado; tasa de sostenidas; preguntas publicadas y omitidas por motivo; indicios; decisiones por estado; cola con extras frente al umbral de 20 |
| Veridicus — evaluación (U4) | Añade los reintentos de la segunda lectura |
| Veridicus — plataforma (U2) | Sin cambios: memoria de los pods de IA frente a sus límites |

Los paneles viven como `ConfigMap` de Grafana en el chart (`grafana_dashboard: "1"`) y solo muestran
contadores con etiquetas de enum.
