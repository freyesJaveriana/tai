## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-02T23:52:47Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/human-review/functional-design/rules.md > BR3.5; functional-spec.md > F4 y §9 | `propose` se rechaza con `review.round_locked` cuando todas las rondas están bloqueadas, pero U4 (BR11.1) llama `propose` dentro de la transacción que ingiere el resultado de C3 y solo después hace XACK. Si el rechazo revierte la transacción, el mensaje nunca se confirma y queda en redelivery indefinido (mensaje venenoso); además U4 BR5.9 (aprobada) permite reintentar «también en una sesión finalizada», y el §9 la contradice sin definir qué hace U4 con el turno ni con el mensaje. Una sesión consolidada con un turno en vuelo es un caso real. | Definir el contrato de fallo de `propose`: qué estado queda en el turno (`error` con código), si se confirma el mensaje y cómo se cuenta el reintento; dejarlo en la tabla §9 como decisión para que el humano apruebe la precisión a U4 BR5.9 y C10. | New |
| R-02 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/human-review/functional-design/rules.md > BR2.x, BR3.1, BR3.2, BR3.4; entities.md > ReviewDecision | Falta definir la concurrencia entre una decisión y `lock_round`: F2 lee la ronda `open` y luego inserta, sin bloqueo ni aislamiento declarado, así que una decisión puede entrar tras el bloqueo y después del `pending_count` / SHA-256 de U7, rompiendo la consolidación explícita de AUTONOMIA-03. Además BR3.2 desempata «a igual hora, mayor orden de inserción», pero `ReviewDecision` no tiene secuencia ni columna de orden. | Especificar que la decisión toma la ronda `FOR UPDATE` (o equivalente) y que `lock_round` usa el mismo candado; añadir un atributo monotónico (`seq`) a `ReviewDecision` para BR3.2; añadir prueba de nivel 1 de decisión frente a bloqueo simultáneo. | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/human-review/functional-design/entities.md > ReviewDecision.reformulation; rules.md > BR3.6 | Tras `edited` -> `accepted`, la decisión nueva no lleva reformulación («ausente en otro caso»), así que el estado vigente aceptado no dice si el texto que consolida U7 es el original de la IA o la reformulación previa. | Fijar en BR3.6 qué texto devuelve `decisions` para un estado `accepted` precedido de `edited` (y para `dismissed` tras `edited`). | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/human-review/functional-design/functional-spec.md > F4, F5; entities.md > ReviewRound | Si ningún turno produce sugerencias (solo Hecho No Documentado), nunca se abre la ronda 1; `open_round` devuelve nada y `lock_round` no tiene a qué aplicarse. No se dice qué ve U7 al consolidar una sesión sin ronda. | Declarar el comportamiento esperado (por ejemplo `pending_count` = 0 sin ronda y consolidación permitida) o que U7 lo trate. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/human-review/functional-design/functional-spec.md > §8; rules.md > BR2.x, BR4.1 | No hay error para una sugerencia inexistente o ajena a la sesión (404), y «las etiquetas solo llevan identificadores» de BR4.1 no excluye `session_id` como etiqueta de Prometheus (cardinalidad). | Añadir el caso 404 a la tabla de errores y fijar que `veridicus_session_dismissal_ratio` no use `session_id` sin acotarlo. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Sensores de etapa / trazabilidad | PASS (según el encargo) | No revisado de nuevo; sin hallazgos estructurales propios. |
| Spot-check text-flow/functional-design/rules.md (BR5.9, BR11.1, BR11.2) | Confirma R-01 | BR11.1 llama `propose` dentro de la transacción y hace XACK después; BR5.9 permite reintento en sesión finalizada. |

### Summary

La máquina de estados y las reglas de transición son coherentes con AUTONOMIA-03. Los dos puntos a pesar antes de aprobar son el fallo de `propose` con rondas bloqueadas (riesgo de mensaje venenoso en la ingesta de U4) y la concurrencia decisión frente a bloqueo con el orden de inserción sin columna; ninguno es crítico y caben como refinamientos en este diseño.
