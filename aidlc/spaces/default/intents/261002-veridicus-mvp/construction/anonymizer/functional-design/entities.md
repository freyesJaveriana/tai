# Entidades — U10 anonymizer

**Insumos.** Unidad U10 de `inception/units-generation/unit-of-work.md` (unit-of-work) e historia US11.3
(`unit-of-work-story-map.md`), con US9.1 cruzando esta unidad; FR11.3, FR12.3, NFR1 y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); ModelGateway y ADR-005 de
`inception/domain-design/components.md` (components); C13 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P2 de
`functional-design-questions.md`.

**Frontera AUTONOMIA-04.** El anonimizador es el **único** componente con salida fuera del clúster, y
solo hacia el destino externo configurado. Lo que cruza la frontera es el *payload* ya enmascarado
(marcadores en lugar de nombres, lugares y expedientes); la tabla de equivalencias nunca sale ni se
guarda. U10 solo se construye si se decide usar un modelo externo; ninguna unidad MUST depende de él.

```yaml
entities:
  - name: MaskingRequest
    description: Una llamada saliente (juez o embeddings) que el proxy enmascara antes de enviar.
    attributes:
      - { name: request_id, type: uuid, required: true, unique: true }
      - { name: operation, type: enum, required: true, allowed: [judge, embed] }
      - { name: scenario_version_id, type: uuid, required: false, description: "para cargar la lista de nombres propios del escenario" }
      - { name: inbound_payload, type: document, required: true, description: "nunca se registra ni se guarda" }
      - { name: outbound_payload, type: document, required: true, description: "el único contenido que sale del clúster" }

  - name: MaskTable
    description: >
      Tabla de equivalencias valor → marcador de una sola llamada (P1 = A). Vive solo en memoria del
      proxy durante la llamada; nunca se registra, se guarda ni sale del clúster.
    attributes:
      - { name: entries, type: list, required: true, description: "pares (valor original normalizado, marcador)" }
      - { name: counters, type: map, required: true, description: "contador por categoría para numerar marcadores" }
    constraints:
      - "Un mismo valor (sin mayúsculas ni tildes) recibe siempre el mismo marcador dentro de la llamada."
      - "Se destruye al terminar la llamada, con éxito o con error."

  - name: MaskCategory
    description: Categoría de dato a enmascarar (valor).
    attributes:
      - { name: value, type: enum, required: true, allowed: [PERSONA, LUGAR, EXPEDIENTE] }
      - { name: marker_format, type: text, required: true, default: "[<CATEGORIA>_<n>]" }

  - name: DetectionRuleSet
    description: Reglas de detección versionadas (P2 = A).
    attributes:
      - { name: schema_version, type: semver, required: true }
      - { name: person_patterns, type: list, required: true, description: "tratamientos («señor», «doña», «don», «sargento»…) seguidos de palabras con mayúscula inicial; secuencias de 2 o más palabras con mayúscula inicial" }
      - { name: place_patterns, type: list, required: true, description: "prefijos de lugar («vereda», «corregimiento», «municipio de», «barrio»…) seguidos de palabras con mayúscula inicial" }
      - { name: case_number_patterns, type: list, required: true, description: "formatos de radicado y expediente (secuencias de dígitos con guiones o barras de 6 o más caracteres)" }
      - { name: scenario_proper_nouns, type: list, required: true, description: "nombres propios extraídos de los documentos de la versión de escenario de la sesión" }
    constraints:
      - "Ante una coincidencia ambigua (persona o lugar), se enmascara con la categoría de la regla que coincidió primero; nunca se deja sin enmascarar."

  - name: OutboundDestination
    description: Destino externo configurado del proxy.
    attributes:
      - { name: url, type: url, required: true, constraints: "HTTPS; único destino externo permitido" }
      - { name: credential_ref, type: secret_ref, required: true, description: "referencia a un Secret; nunca el valor" }
```

## Resumen

- **MaskingRequest** es cada llamada que pasa por el proxy; solo su `outbound_payload` sale del clúster.
- **MaskTable** da marcadores consistentes por llamada y restaura la respuesta dentro del clúster (P1); no
  persiste.
- **DetectionRuleSet** combina expresiones regulares en español con la lista de nombres propios del
  escenario y enmascara ante la duda (P2).
- **OutboundDestination** es el único destino externo, con su credencial por referencia.
