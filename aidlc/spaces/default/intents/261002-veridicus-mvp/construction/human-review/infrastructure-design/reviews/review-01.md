## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T11:05:14Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/human-review/infrastructure-design/monitoring-design.md > §2 Alertas, fila VeridicusAirThresholdProposal; cicd-pipeline.md > §1 job rules | La regla se presenta como "de U2" con agregación max by (session_id) y U5 entrega un fixture que exige UNA sola alerta con dos pods. Pero la regla aprobada de U2 es solo veridicus_session_dismissal_ratio > 0.25 (platform monitoring-design §3, línea 48); el cambio solo existe como precisión pendiente en infrastructure-specification.md §5. Además el job rules ejecuta promtool sobre charts/session-api/tests/rules.yaml, mientras la regla vive en la PrometheusRule de U2: no queda claro en qué chart está ni quién la modifica. Si el humano no aprueba la precisión, la prueba de U5 falla o prueba una regla que no es la desplegada. | Fijar un único dueño y ruta de la regla AIR y declarar que el fixture air_series.yaml depende de aprobar la precisión a platform monitoring-design §3, o mover la regla al subchart session-api (PrometheusRule de U5). | New |
| R-02 | Minor | .../infrastructure-design/infrastructure-specification.md > §1 Estrategia y Sondas | Durante el RollingUpdate el pod viejo conserva su gauge AIR sin actualizar y el nuevo la reconstruye después de pasar la readinessProbe (la reconstrucción no entra en ninguna sonda). max by (session_id) toma el valor más alto, así que un valor viejo puede mantener una propuesta de umbral ya superada hasta que el pod viejo termina. Es solo una señal informativa, sin acción. | Documentar la ventana (segundos) como riesgo aceptado, o hacer que /readyz espere la reconstrucción de las series. | New |
| R-03 | Minor | .../infrastructure-design/infrastructure-specification.md > §2.1 VERIDICUS_DB_LOCK_TIMEOUT_MS | El rango válido llega hasta el statement_timeout (2 000 ms) y el valor por defecto es igual a él: con lock_timeout = statement_timeout ambos pueden saltar en la misma sentencia y no se distingue cuál. La prueba de ≤ 2,5 s no cubre el empate. | Exigir lock_timeout estrictamente menor que statement_timeout (por ejemplo 1 500 ms) o añadir una prueba del empate. | New |
| R-04 | Minor | .../infrastructure-design/cicd-pipeline.md > §1 test-level0/test-level1 y §2 | La prueba automatizada de AUTONOMIA-03 contra vocabulario de veracidad (scan con nota y reformulación como literal_sources) está solo en el nivel 3, que corre antes de etiquetar, no en cada PR. Cumple el mínimo de la regla, pero la guardia no bloquea los PR. | Añadir al nivel 0 un escaneo de los textos de la tarjeta y de los mensajes de C1 con scan, o declarar que el nivel 3 es la única puerta. | New |
| R-05 | Minor | .../infrastructure-design/infrastructure-specification.md > §2.3 Pérdida de la base | Restaurar un pg_dump anterior puede dejar una versión de reporte (archivo antes que fila) cuyas decisiones y ronda bloqueada ya no existen, y la consolidación quedaría sin su rastro de quién y cuándo (AUTONOMIA-03). Se acepta por usar solo datos sintéticos, pero no está dicho. | Registrar que, tras una restauración, los reportes posteriores al volcado se descartan, o añadirlo al runbook. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON de traceability.json | PASS: 50 upstream_ids, todos en coverage; un solo N/A (NFR10.20) justificado | Cobertura consistente |
| IDs NFR de nfr-requirements/ frente a upstream_ids | Falta solo NFR8.8, que es de U4 (scalability-requirements línea 14) | No es una brecha de U5 |
| Réplica única ligada a AIR (D7) | PASS: §1 la declara requisito y exige PR antes de subir | Coherente con scalability-design §4 |
| Memoria frente a U3 | PASS: 200 + 160 + 32 ≈ 392 MiB frente a 768 MiB; mismos requests/limits que U3 y U4 | Coherente |
| Migración como Job propio (AUTONOMIA-01) | PASS: migrations-job con veridicus_owner, PR propio, backup previo, nunca al arrancar | Cumple |
| Permisos de solo inserción (AUTONOMIA-03) | PASS: review_decision y cot_view INSERT, SELECT; review_round UPDATE en 4 columnas más trigger de fila locked | Cumple |
| Puertas con comando y umbral (AUTONOMIA-02) | PASS; ver R-04 | Cumple |
| Frontera (AUTONOMIA-04) | PASS: sin salidas nuevas, contrato human_review_no_network | Cumple |
| Precisiones sin editar originales | PASS: §5 las registra en tabla; ver R-01 | Cumple |
| Fragmentos de código ≤ 15 líneas | PASS: un solo bloque SQL de 5 líneas | Cumple |

### Summary

El diseño es implementable y respeta AUTONOMIA-01 a 05. La decisión principal es R-01: la prueba de la regla AIR de U5 depende de una precisión a U2 aún no aprobada y su ubicación es ambigua. El resto son riesgos menores.
