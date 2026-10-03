## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-02T23:54:19Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/functional-design/rules.md > BR4.5 y BR4.2 | La reanudación no reinicia `last_heartbeat_at` («nada más cambia»). La tarea de BR4.2 evalúa `now − last_heartbeat_at > T`; justo después de reanudar el valor sigue vencido, así que la sesión puede volver a `suspended` en la siguiente revisión, antes de que la consola envíe un latido. Tampoco se define el caso `last_heartbeat_at` nulo (sesión recién creada) en BR4.2. | Fijar que `resume` (y la creación de sesión) establece `last_heartbeat_at = ahora`; definir el comportamiento con valor nulo; añadir a la prueba de nivel 1 de BR4.5 el caso reanudar y revisar en el siguiente ciclo. | New |
| R-02 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/functional-design/rules.md > BR2.5 | «En una transacción... y luego se publica C2» no es atómico: si el proceso cae tras el commit y antes de publicar, los turnos `testimony` quedan numerados pero nunca encolados, y un reenvío con el mismo `client_request_id` «devuelve los mismos turnos» sin republicar. Solo la tarea de plazos (BR5.2) los pasaría a `error` al vencer. Contradice la meta de no perder ni duplicar nada. | Especificar una entrega fiable (p. ej. outbox en la misma transacción o reconciliación de turnos `queued` sin mensaje) y qué hace el reenvío idempotente si no se publicó; añadir prueba de nivel 1 con corte entre commit y publicación. | New |
| R-03 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/functional-design/functional-spec.md > F4 paso 3 y §9 | Los códigos `session.not_open` (409) y `turn.too_long` (422) no existen en el `ErrorCode` de C1 (`contract-summary.md` solo trae `session.finalized`, `session.not_suspended`, `session.not_owner`, etc.). La tabla §9 solo añade `transcript.too_large`. Un desarrollador no sabe si reutilizar `session.finalized` o crear códigos nuevos. | Ampliar la tabla §9 con `session.not_open` (o elegir un código existente) y confirmar el origen de `turn.too_long` (U4 o esta unidad). | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/functional-design/rules.md > BR2.1 y BR2.2 | La marca (1–30 caracteres sin dígitos ni «:» seguidos de «: ») abre turno también con líneas de testimonio como «Entonces dijo: ...» o «Nota: ...», y cualquier hablante fuera de `InterviewerLabels` (p. ej. un tercero) se evalúa como testimonio del compareciente sin posibilidad de ajustar el rol. Tampoco se define el pegado sobre una sesión con turnos previos, con turnos aún en cola o no `open`. | Documentar los ejemplos límite (con la prueba compartida) y la política para roles desconocidos; precisar numeración, orden y rechazo del pegado según el estado de la sesión. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/session-lifecycle/functional-design/entities.md > SessionListItem.pending_suggestions y ScenarioVersion.version_number | `pending_suggestions` no tiene regla BR ni historia que lo respalde; `version_number` carece de restricción única `(scenario_id, version_number)` frente a cargas concurrentes. | Añadir la regla o retirar el atributo; declarar la restricción única y su manejo (409). | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Sensores / trazabilidad | PASS (informado por el orquestador) | Sin referencias rotas; los hallazgos son de comportamiento y de contrato, no de estructura |

### Summary

El diseño es coherente con P1–P3, la máquina de estados es completa y respeta AUTONOMIA-04, pero tres hallazgos Major (re-suspensión tras reanudar, encolado no atómico del pegado y códigos de error fuera del contrato C1) superan el umbral de la regla de severidad. Al ser una pasada asesora, el veredicto informa al humano: se recomienda «Request Changes» para integrarlos.
