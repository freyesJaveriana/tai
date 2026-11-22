# Requisitos de observabilidad — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U8.** Sustituye a la revisión 1 del 2026-10-03. Los IDs se conservan; las métricas de los
extras de la revisión 1 salen con ellos.

**Insumos.**
- Flujos F4–F9 y §9 de `functional-design/functional-spec.md` (functional-spec); reglas BR5.7, BR5.10,
  BR5.13, BR5.17 y BR6.3 de `functional-design/rules.md` (rules).
- NFR10 y NFR15 de `inception/requirements-analysis/requirements.md` (requirements).
- C15, C16 y C19 de `inception/contract-design/contract-summary.md` (contract-summary).
- Lo que fijaron hoy U1 (etiquetas permitidas), U4 (métricas de la cola y del registro), U11 (la biblioteca
  no exporta métricas) y U2 (sin Alertmanager).

## 1. Logs

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR15.2 | cambia | Logs estructurados sin datos sensibles. | El formato de U4 con estos identificadores: `session_id`, `run_id`, `observation_id`, `source_finding_id`, `rule`, `state` y `code`. Nunca el tema, las citas, el `hecho` ni texto de turnos (NFR10.8) |
| NFR15.3 | cambia | Cada aclaración deja rastro correlacionable. | Biblioteca (CLI y `semantic-agent`): `clarification.discarded` (`run_id`, `source_finding_id`, `rule`) por descarte y `clarification.summary` (`run_id`, emitidas, descartadas) por corrida. `session-api`: `conductor_observation.ingested` (`run_id`, `session_id`, insertadas, ya existentes) y `conductor_observation.decided` (`observation_id`, `session_id`, `state`, `user_id`). Prueba de nivel 1 que sigue una aclaración desde la corrida hasta la decisión por sus logs |
| NFR15.4 | cambia | Los descartes se distinguen por regla y no son errores. | Cada evento de descarte es `INFO` con `rule` ∈ {`schema`, `mentions_contradiction`, `phrases`, `cites_turn`, `quote_text`, `quote_overlap`, `forbidden_vocabulary`}, porque es un resultado normal (functional-spec §9). Una aclaración inválida en la ingesta es `WARNING` con `code` `analysis.invalid_output`; una excepción del módulo es `ERROR` con su tipo, nunca su mensaje |

## 2. Métricas (Prometheus, en `/metrics` del puerto interno de `session-api`)

| ID | Estado | Métrica | Tipo | Etiquetas |
|---|---|---|---|---|
| NFR15.1 | cambia | `veridicus_conductor_observations_ingested_total` | counter | ninguna |
| NFR15.1 | cambia | `veridicus_conductor_observation_decisions_total` | counter | `state` (`approved`, `discarded`) |

- Las etiquetas salen de la lista permitida de U1 y solo llevan valores de enum (NFR-U8-05).
- Los descartes por regla no van a Prometheus, porque la biblioteca no exporta métricas: se cuentan en el
  reporte de nivel 2 (sección `clarifications` de C19 v2) y en los logs.
- La permutación no tiene métrica propia: las métricas de *tokens* por papel y la latencia de la corrida
  de U4 ya distinguen `verificador_permutado` (etiqueta `role`).

## 3. Indicadores (SLI) y objetivos

| SLI | Cálculo | Objetivo |
|---|---|---|
| Citas en los temas | Coincidencias de fragmentos de cita en los temas emitidos, en nivel 2 | 0 (NFR4.3, bloquea) |
| Tasa de descarte por regla | descartadas / (emitidas + descartadas), en nivel 2 | Se reporta; > 0,50 es señal de revisión (NFR4.6) |
| Latencia incremental con la permutación | p95 de la duración de la corrida con `comercial-piloto`, en el reporte de BR6.5 | ≤ 180 s (NFR3.1) |
| Corridas completas con `todo-local` | Fracción sin `tiempo_agotado`, en el reporte de BR6.5 | ≥ 98 % (NFR8.7) |
| Decisión | p95 de `POST /conductor-observations/{id}/decision` | ≤ 300 ms (NFR3.8) |

## 4. Panel y alertas

- **Panel de Grafana (SHOULD, U2).** Junto al de U4: aclaraciones ingeridas y decisiones por estado.
- **Sin alertas.** El MVP no tiene Alertmanager y no notifica a nadie (decisión de U2); las cifras de nivel
  2 se revisan en el PR.
- **Trazas distribuidas.** No: la correlación por `run_id`, `session_id` y `observation_id` basta.
