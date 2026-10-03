## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-03T02:26:47Z
**Iteration:** 1

Revisión advisory de una sola pasada. Dos hallazgos Major para que el humano los sopese; ningún Critical.

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/nfr-requirements/scalability-requirements.md > NFR8.3; security-requirements.md > NFR1.4 | Los marcadores se numeran por llamada (NFR8.3: `[PERSONA_1]` en ambas llamadas aunque el orden cambie). Los vectores externos de pasajes (lotes de 32, llamadas distintas) y los de la consulta de una afirmación quedan con marcadores que no designan a la misma persona entre llamadas. La afirmación de functional-design de que la comparación por similitud «conserva sentido» no se sostiene con esa numeración, y nada en NFR1.4 ni NFR4.1 lo mide por separado; solo el PR de habilitación (NFR4.1) lo detectaría, tarde. | Decidir: numerar de forma determinista por valor normalizado (p. ej. por el orden de la lista de nombres del escenario) para `embed`, o añadir una prueba de nivel 1 que compare la similitud enmascarada contra la no enmascarada sobre el Golden Dataset y, si falla, dejar `embed` externo fuera de alcance. | New |
| R-02 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/nfr-requirements/security-requirements.md > NFR1.5 (política `veridicus-egress-only-anonymizer`) | La política solo evalúa reglas de salida con `ipBlock` fuera del clúster. No cubre salidas abiertas sin `ipBlock`: `egress: [{}]` o `to` vacío (permite todo), `hostNetwork: true`, un pod sin `NetworkPolicy` de salida (depende de la denegación por defecto de U2, que aquí solo se cita) ni un `namespaceSelector` hacia un namespace con salida. Los controles negativos listados (E7, `0.0.0.0/0`, puerto 80, sin anotación) no incluyen esos casos. Es la guardia estática de AUTONOMIA-04 y la única barrera contra T3 antes de la verificación manual. | Añadir a NFR1.5 reglas y controles negativos para: regla de salida vacía o sin `to`, `hostNetwork`, y pod con datos sin anonimizar sin política de denegación por defecto; confirmar con U2 que esa denegación está en su NFR1.1 (referencia verificable, no solo cita). | New |
| R-03 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/nfr-requirements/reliability-requirements.md > NFR6.1 | La restauración devuelve valores originales dentro de una respuesta que es JSON del juez (C6). Un nombre con comillas, barra invertida o salto de línea restaurado en crudo puede romper el JSON y producir un error de formato (umbral 0 %). La prueba de propiedad solo cubre texto plano. | Especificar la restauración con escape JSON dentro de cadenas y añadir una prueba de propiedad sobre JSON con nombres sintéticos con caracteres especiales. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/nfr-requirements/reliability-requirements.md > NFR10.4 | El presupuesto 2 s (enmascarado) + 5 s (conexión) + 170 s (lectura) = 177 s frente a los 180 s del cliente de U4 deja 3 s de margen, y el *timeout* de lectura de `httpx` es por lectura, no total: un destino que gotea bytes supera 170 s sin disparar 504. | Imponer un plazo total por llamada (170 s `judge`, 25 s `embed`) con `anyio.fail_after` y probarlo con un *fake* que gotea. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/nfr-requirements/security-requirements.md > NFR1.8 y NFR1.7 | La lista permitida cubre campos del cuerpo, pero no las cabeceras: no dice si `X-Request-Id` o la `Authorization` del cliente llegan al destino. Además NFR1.7 usa `kubectl exec ... curl`, que no existe en imágenes mínimas sin root fijadas por digest. | Declarar una lista permitida de cabeceras salientes (solo `Authorization` propia y `Content-Type`) con prueba; cambiar la verificación manual a una herramienta presente o documentar `curl` en la imagen. | New |
| R-06 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/nfr-requirements/tech-stack-decisions.md > NFR13.2 | El 100 % de ramas se exige también sobre la validación de destinos de `libs/model_gateway`, que es de U4 (C13); U10 impone una puerta de cobertura sobre código de otra unidad sin que el contrato lo asigne. | Confirmar en C13 quién es dueño de esa validación o limitar la puerta a la parte añadida por NFR1.6. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| traceability.json (JSON válido; cada NFRx.y citado existe en los .md) | PASS: JSON válido, 46 IDs NFRx.y definidos, 0 referencias sin resolver | La cobertura declarada es coherente; NFR7 N/A queda justificado |

### Summary

Diseño acotado y consistente (apagado por defecto, falla cerrada, trazabilidad completa). Lo que el humano debe sopesar es la numeración de marcadores por llamada, que puede deteriorar los embeddings externos (R-01), y la cobertura incompleta de la política estática de salida (R-02). Ninguno bloquea; ambos son aprobables como precisiones.
