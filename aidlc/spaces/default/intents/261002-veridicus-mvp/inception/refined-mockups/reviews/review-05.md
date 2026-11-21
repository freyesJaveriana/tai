## Review

**Verdict:** READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-11-21T15:12:28Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/interaction-spec.md > §6 catálogo, fila `session.blocked_incident`; mockups.md > §6.4 fila «Sesión bloqueada por incidente» | El texto «Sesión bloqueada por un incidente de anonimización. No se lanzan corridas nuevas» no está en AC3.2.5 ni en AC11.3.8 (este solo dice que la sesión pasa a bloqueada y rechaza corridas nuevas), pero la fila lo cita como si ellos lo fijaran. Lo mismo vale para dejar «Reintentar tramo» y «Lanzar modo final» deshabilitados y enfocables. Las dos causas del anonimizador sí coinciden palabra por palabra con AC3.2.5. | Añadir a la tabla de precisiones de `mockups.md` una fila que declare el texto de cabecera y el deshabilitado de los dos botones como propuesta de esta etapa (origen: AC11.3.8, CD-08), para que el humano la decida en la aprobación. | New |
| R-02 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §11 fila US15.8 | «Los roles sin permiso no ven el botón» no está en la adenda: AC15.8.1 pide `403`, y la consola deshabilita con motivo en vez de ocultar (AC5.6.4). | Quitar la frase o registrarla como precisión con el criterio de ocultar frente a deshabilitar. | New |
| R-03 | Minor | mockups.md > §11 fila US15.5 | La fila dice «pie de cada página del reporte», pero AC15.5.2 pide el aviso en la cabecera y al final de cada sección de página. | Citar cabecera y pie, como AC15.5.2. | New |
| R-04 | Minor | mockups.md > §11 filas US15.1 y US15.2 | «Después de M0» (US15.1) y «en M1» (US15.2) no los dice la adenda, que solo exige «al entrar a la consola» y que el estado se lea con texto (AC15.2.4). | Registrar las dos ubicaciones como precisiones, o quitarlas. | New |
| R-05 | Minor | mockups.md > §11 filas US15.4 y US15.7 | La fila de US15.4 no menciona AC15.4.4 (constancia del mandato y garantías legales) y la de US15.7 no ubica la reducción del plazo (AC15.7.3). Un lector de §11 no sabría que faltan en M3 y M7. | Añadir AC15.4.4 a la fila de US15.4 y marcar la reducción de plazo en la de US15.7 como sin interfaz propia o sin ubicación. | New |
| R-06 | Minor | mockups.md > §11 fila US15.10 | La fila dice «M8 §10.2 (tabla por tipo de hecho y perfil)», pero §10.2 no dibuja esa tabla. Con la pregunta 13 = A no hay que dibujarla. | Aclarar en una nota de §11 que las filas US15.x indican solo la ubicación y que la especificación es la adenda, no los wireframes. | New |

### Summary

La revalidación se mantiene dentro de su alcance. Las dos causas del anonimizador coinciden exactamente con AC3.2.5, el desliz M2 → M4 de US15.2 está registrado y ningún texto nuevo usa el vocabulario prohibido (0 coincidencias de «prueba», «probatorio», «pliego», «inculpa», «miente», «engaño» o «falso» fuera de comentarios sobre pruebas). Las filas US15.1–US15.10 coinciden en su mayoría con la adenda. El único hallazgo con peso es R-01, un texto nuevo atribuido a criterios que no lo fijan. R-02 a R-06 son ajustes de redacción de §11 y no bloquean, así que el veredicto es READY.
