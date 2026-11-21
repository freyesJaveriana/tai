## Review

**Verdict:** READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-11-21T15:26:19Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/interaction-spec.md > §6 catálogo, fila `session.blocked_incident`; mockups.md > §6.4 fila «Sesión bloqueada por incidente» y tabla de precisiones | Corregido. La tabla de precisiones tiene la fila nueva que declara el texto de cabecera y el deshabilitado como propuesta de esta etapa. Dice con exactitud qué fija AC11.3.8 (el bloqueo, el `code` `anonymizer.incident` y el rechazo de corridas nuevas). La fila de §6.4 y la de `session.blocked_incident` se declaran propuesta y remiten a la tabla. La causa de la corrida sí es la de AC3.2.5 y el texto coincide literalmente. No aparece el vocabulario prohibido. | Ninguna. | Resolved |
| R-02 | Minor | mockups.md > §11 fila US15.8 | Corregido. La fila cita solo AC15.8.1 (`403` al investigador y al analista que no es dueño) y AC15.8.2 (marca de agua y SHA-256), y ambos coinciden con la adenda. La frase «los roles sin permiso no ven el botón» ya no está. | Ninguna. | Resolved |
| R-03 | Minor | mockups.md > §11 fila US15.5 | Corregido. Dice «en la cabecera y al final de cada sección de página (AC15.5.2)», igual que la adenda. | Ninguna. | Resolved |
| R-04 | Minor | mockups.md > §11 filas US15.1 y US15.2; tabla de precisiones | Corregido. Las dos ubicaciones (diálogo tras M0, estado también en la fila de M1) están en la tabla de precisiones. Esa fila dice qué fijan AC15.1.1 y AC15.2.4 y qué no. La corrección M2 → M4 de US15.2 también está registrada. | Ninguna. | Resolved |
| R-05 | Minor | mockups.md > §11 filas US15.4 y US15.7 | Corregido. US15.4 incluye AC15.4.4 en M3 y M7. US15.7 marca la reducción del plazo (AC15.7.3) como sin ubicación y la deja para Functional Design. El texto de AC15.4.4 y el de AC15.7.3 coinciden con la adenda. | Ninguna. | Resolved |
| R-06 | Minor | mockups.md > nota bajo el título de §11; fila US15.10 | Corregido en lo pedido. La nota aclara que las filas *(adenda 02)* solo ubican y que la especificación es la adenda (pregunta 13 = A). La fila de US15.10 dice «sin dibujar». Queda un problema nuevo, R-07. | Ninguna sobre R-06. | Resolved |
| R-07 | Major | mockups.md > §11 fila US15.10 frente a §10.2 y a la precisión «Consola de solo consulta del investigador» | La fila dice que M8 §10.2 «muestra la tabla de hallazgos agrupada por tipo de hecho y por perfil». Pero §10.2 solo dibuja métricas y registro de modelos, y la consola de M8 guarda solo metadatos y cifras, nunca hallazgos (NFR12; AC12.6.1). La tabla de AC15.10.2 es por transcripción y por hallazgo. Sin aclarar qué contiene, un desarrollador no sabe si M8 muestra hallazgos, conteos o nada. Esto contradice la regla de que M8 no guarda texto de hallazgos. | Reescribir la fila de US15.10 para decir qué muestra M8 de esa tabla: solo conteos agrupados por tipo de hecho y perfil, sin texto de hallazgos ni citas. O decir que la tabla queda en el JSON del reporte y M8 no la muestra. Registrar la decisión como propuesta en la tabla de precisiones. | New |
| R-08 | Minor | mockups.md > §11 fila US15.8 y §7 (M5), botón «Descargar reporte» | Con la frase retirada, nada dice cómo se ve el botón para el analista que no es dueño. El wireframe de M5 lo muestra siempre. Solo queda el `403` de la API, así que ese usuario llegaría a un error sin explicación. | Decidir y registrar como propuesta la conducta de la consola: botón deshabilitado con motivo (AC5.6.4) o mensaje de error al recibir el `403`. O dejarlo explícito para Functional Design. | New |
| R-09 | Minor | mockups.md > §11 fila US11.3–US11.6 | La fila dice que, «con AC11.3.8», el efecto visible es el estado «Sesión bloqueada por incidente». AC11.3.8 fija el bloqueo, no esa rotulación. La rotulación es la propuesta de la fila nueva de la tabla de precisiones. | Añadir «(rótulo propuesto; ver la tabla de precisiones)» o citar la tabla en vez de atribuirlo a AC11.3.8. | New |

### Summary

Las seis correcciones resuelven sus hallazgos. Los textos que la etapa propone quedan declarados como propuesta y los que citan criterios coinciden con la adenda. No aparece vocabulario prohibido en lo corregido. Queda un Major nuevo (R-07, la fila de US15.10 choca con la regla de que M8 no guarda hallazgos) y dos Minor. El Major tiene una salida clara y local, dentro del máximo de dos, así que el veredicto es READY. Conviene resolver R-07 antes de aprobar.
