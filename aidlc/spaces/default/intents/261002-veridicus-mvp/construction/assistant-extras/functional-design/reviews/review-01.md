## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-02T23:55:51Z
**Iteration:** 1

Revisión ADVISORY de una sola pasada: los hallazgos informan al humano en la compuerta de aprobación.

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/functional-design/rules.md > BR1.2 y BR1.3 (con text-flow rules.md > BR8.6) | BR8.6 de U4 arma la alerta con `quote` y `document_id` del «primer passage_id que el juez citó» y con la `cot` validada de una sola lectura. Con permutación hay dos lecturas, cada una con su CoT y sus pasajes citados (los pasajes llegan en orden distinto). BR1.2 solo dice que la alerta «sigue el camino de U4» y no fija de cuál lectura salen `cot`, `quote` y `document_id`. Estos son los campos obligatorios de AUTONOMIA-05; un desarrollador tendría que adivinar, y la elección cambia el contenido que ve el analista. | Fijar en BR1.2 de qué lectura salen `cot`, `quote` y `document_id` (por ejemplo, la lectura `forward`, que es la de U4) y añadir una prueba de nivel 0 con un juez fake que cite pasajes distintos en cada orden. | New |
| R-02 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/functional-design/entities.md > SuggestedQuestion.source_passage_ids; functional-spec.md > §9 y F2 paso 4 (contra inception/contract-design/contract-summary.md, esquema de C3 `suggested_question` y esquema REST `SuggestedQuestion`) | La entidad exige `source_passage_ids` (required, «solo pasajes recuperados para el turno») y `attempt`. C3 define `suggested_question` con solo `[text]`, y el esquema REST `SuggestedQuestion` solo trae `question_id`, `turn_id`, `text` y `status`. La tabla §9 declara como precisión a C3 únicamente `forward_grade`, `reversed_grade` y `sustained`. Con el contrato aprobado, InterviewSession no puede poblar `source_passage_ids` ni verificar que la pregunta use solo pasajes recuperados (AC10.3.1). | Añadir a la tabla §9 la precisión de C3 (`suggested_question.source_passage_ids`) y definir la propiedad en el esquema, o bien quitar el atributo de la entidad y decidir cómo se comprueba AC10.3.1 sin él. | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/functional-design/rules.md > BR2.2 (contra text-flow rules.md > BR9.1, BR9.2) | La pregunta sugerida usa «un prompt propio» que recibe el testimonio como dato. BR9.1 y BR9.2 de U4 (archivo montado `readOnly` desde un ConfigMap y SHA-256 verificado al arrancar) cubren solo el prompt del juez. U8 no extiende esa integridad al prompt de la pregunta ni registra su hash. Es el segundo punto donde texto no confiable entra a un LLM. | Declarar en BR2.2 que el prompt de la pregunta se monta y se verifica igual que el del juez, e incluirlo en la política de manifiestos de nivel 0. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/functional-design/rules.md > BR2.4 y BR2.5 (contra contract-summary.md, `/questions/{question_id}/decision`) | BR2.4 y BR2.5 usan 403 y 409 sin código estable. U4 usa Problem Details con códigos como `session.not_owner`. La operación `decision` del contrato aprobado solo documenta 200, y no declara 403, 404 ni 409. | Fijar los códigos (por ejemplo `question.not_owner` y `question.already_decided`) y añadirlos como precisión al contrato en §9. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/functional-design/functional-spec.md > F1 y §8 (con text-flow rules.md > BR5.8, BR8.2) | La segunda lectura y la pregunta suman dos llamadas al juez por turno dentro del mismo `deadline_at`. No se dice si un timeout de la segunda lectura da `turn.error.timeout` para todo el turno ni cómo se relaciona con el plazo de BR5.8. Se difiere la medición a NFR Requirements, pero la regla de fallo es de diseño funcional. | Añadir que un timeout en la segunda lectura sigue BR8.2 (turno en error, 0 alertas) y que la pregunta nunca consume el plazo del turno: su timeout la omite. | New |
| R-06 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/assistant-extras/functional-design/entities.md > SuggestedQuestion (`decided_by`, `decided_at`) y QuestionDecision | La decisión se guarda dos veces: campos mutables en SuggestedQuestion y el historial de solo inserción QuestionDecision. BR2.6 solo cubre el historial; nada obliga a que las dos copias coincidan, ni se dice si SuggestedQuestion queda en AuditConvention. | Indicar que el estado se actualiza y que QuestionDecision se inserta en la misma transacción (con una prueba de nivel 1), o derivar `decided_*` del historial. | New |

### Validation Tool Results

| Tool | Result | Interpretación |
|---|---|---|
| traceability (sensor) | PASS (informado por el orquestador; `traceability.json` cubre AC10.3.x, AC10.5.1, AC11.1.1, AC5.5.x, AC5.6.x) | La cobertura de criterios es completa; los hallazgos son de contenido, no de trazabilidad. |
| Lectura de contratos (C3, `/questions/*`) | R-02 y R-04 confirmados contra `contract-summary.md` | El contrato aprobado no trae `source_passage_ids` ni los errores 403/409. |

### Summary

El diseño es coherente con AUTONOMIA-03/05: la permutación solo reduce alertas, la guardia del umbral sigue primero y la pregunta pasa por aprobación del dueño. Antes de aprobar conviene pesar R-01 (origen de los campos obligatorios de la alerta con dos lecturas) y R-02 (la entidad exige un campo que el contrato C3 aprobado no transporta); el resto son precisiones menores.
