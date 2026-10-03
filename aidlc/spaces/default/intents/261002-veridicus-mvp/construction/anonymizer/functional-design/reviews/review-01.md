## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-02T23:59:21Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/functional-design/functional-spec.md > sección 1 (tabla de componentes) y rules.md > BR3.1 | El proxy recibe texto SIN enmascarar (el spec lo declara: «Texto sin enmascarar hacia el proxy») y a la vez es el único pod con salida. AC9.1.1 y AUTONOMIA-04 exigen que todo pod con datos sin anonimizar tenga salida denegada. BR3.1 y la clasificación de AC9.1.1 no dicen cómo se etiqueta el proxy ni cómo la política de nivel 0 lo exceptúa sin abrir un hueco. El proxy es, de hecho, un pod con datos sin anonimizar con egress: la única barrera es el enmascarador. | Declarar explícitamente el proxy como excepción acotada a AC9.1.1 (etiqueta de clasificación propia, egress solo a su destino) y precisar el control compensatorio. Añadir a BR3.1 un control negativo: un pod con datos sin anonimizar distinto del proxy con egress falla; el proxy con egress a otro destino falla. | New |
| R-02 | Major | rules.md > BR1.2, entities.md > DetectionRuleSet, functional-spec.md > sección 8 | El detector se basa en tratamientos, secuencias de 2+ palabras con mayúscula y la lista del escenario. Un nombre suelto («Ana», un apodo) o de una víctima que no esté en los documentos del escenario no coincide con ninguna regla y sale del clúster. El spec lo reconoce como «límite conocido», pero BR1.2 afirma que «ningún tramo que coincida queda sin enmascarar» (solo cubre lo que coincide) y AC11.3.1 se prueba solo con valores sembrados. No hay comprobación de salida (defensa en profundidad) ni política para tokens con mayúscula no clasificados, lo que incumple el espíritu de AUTONOMIA-04 («NEVER enviar nombres de víctimas»). | Decidir y registrar una de estas: (a) falla cerrada si queda un token con mayúscula inicial no clasificado ni en lista de excepciones, (b) verificación posterior al enmascarado contra la lista de nombres del escenario, o (c) aceptar el riesgo por escrito como «Accepted risk» con la condición de que el proxy solo se use con datos sintéticos. Añadir casos de prueba con nombres sueltos y apodos. | New |
| R-03 | Major | functional-spec.md > F2 y rules.md > BR1.4 | El spec afirma que enmascarar ambos lados conserva la similitud «dentro de la misma llamada». Pero los vectores de los pasajes del escenario se indexan en session-api (otra llamada, otro momento) y se comparan en pgvector con el vector del testimonio de otra llamada. Los marcadores se numeran por llamada (`[PERSONA_1]` no designa a la misma persona entre llamadas) y el texto enmascarado produce vectores distintos de los del texto real/interno. No se define si el índice se construye enmascarado y con qué numeración, ni si mezclar espacios de embeddings (interno vs. externo) invalida el umbral de similitud (AUTONOMIA-05). Además, un fallo de embed en la indexación no es un turno, así que `turn.error.system` (BR2.1) no aplica. | Definir la semántica de embed: indexar y consultar con el mismo adaptador y la misma regla de enmascarado determinista entre llamadas (o marcadores sin numeración), declarar que el umbral se recalibra con el adaptador externo, y definir el error de falla cerrada para el flujo de indexación. Si no se resuelve, acotar el proxy a la operación judge. | New |
| R-04 | Minor | rules.md > BR3.1 | Una `NetworkPolicy` estándar filtra por IP/puerto, no por URL HTTPS. «Salida solo hacia su destino» exige CIDR fijo o una CNI con reglas FQDN; la regla no lo menciona y la prueba Kyverno de nivel 0 no puede verificar el host. | Registrar como supuesto de Infrastructure Design (CNI con FQDN o CIDR del destino) y cómo lo comprueba la política. | New |
| R-05 | Minor | entities.md > MaskTable y rules.md > BR1.3 | La tabla guarda el valor «normalizado» (sin mayúsculas ni tildes), pero la restauración debe devolver el valor original; no se define cuál forma se restaura cuando el mismo valor aparece con variantes. Tampoco se trata un marcador literal ya presente en el texto de entrada (colisión con la restauración). | Precisar que la tabla guarda la primera forma original y escapar o rechazar texto con marcadores literales. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| traceability.json (JSON válido) | PASS | Parsea; los 7 AC de upstream_ids (AC11.3.1, AC11.3.2, AC9.1.1–AC9.1.5) cubren US11.3 y US9.1 del story map para U10. |
| Targets BRx.y vs rules.md | PASS (inspección) | BR1.1, BR1.4, BR2.1, BR3.1–BR3.4 y BR2.3 existen; BR1.2, BR1.3 y BR2.2 figuran en reverse con origen. |
| Referencias a contratos (C13, C14, C16, turn.error.system) | PASS | Existen en contract-summary.md. |

### Summary

La trazabilidad es sólida y el diseño es coherente con C13, pero tres decisiones de fondo quedan abiertas: la excepción del proxy a la regla de pods con datos sin anonimizar, la fuga residual de nombres no detectables por regex, y la semántica de embeddings enmascarados entre llamadas distintas. Al ser una pasada ADVISORY, el humano decide si las acepta como riesgo (unidad COULD, por defecto el juez es interno) o pide cambios antes de aprobar.
