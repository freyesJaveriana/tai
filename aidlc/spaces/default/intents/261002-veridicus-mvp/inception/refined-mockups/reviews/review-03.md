## Review

**Verdict:** READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-11-03T13:42:20Z
**Iteration:** 2

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §5 (M3) y §6.1; interaction-spec.md > §4.2 y §6 | Verificado: `session.empty` lleva el texto exacto de AC2.2.5 («Aún no hay turnos. Escribe el primer turno o pega un bloque de turnos»), «Enviar turno» queda deshabilitado y enfocable con el motivo `turn.send_empty` («Escribe el turno para enviarlo»), y ambas claves están en el catálogo. | Ninguna. | Resolved |
| R-02 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §9 (M7); interaction-spec.md > §4.12 y §6 | Verificado: M7 muestra el texto exacto de AC2.6.5 con «Importar» y «Cancelar»; la clave `import.preview_confirm` coincide carácter por carácter. | Ninguna. | Resolved |
| R-03 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §6.8 y §11; interaction-spec.md > §4.14 | Verificado: cada fila de «Corridas» despliega el registro de modelos en solo lectura (estado `run-detail`, «sin precio», «Aún no hay llamadas registradas»), y la cobertura de US12.5 apunta a M4 §6.8 y M8. | Ninguna. | Resolved |
| R-04 | Major | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §1 y §3; accessibility-checklist.md > C-3 | Verificado: el `admin` llega a M1, M4 y M5 en solo lectura desde «Sesiones» (mapa, cabecera, tabla de roles y C-3), sin «Nueva sesión» ni «Importar» (AC2.1.4), con el banner de solo lectura. | Ninguna. | Resolved |
| R-05 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §6.1, §6.7, §6.10; interaction-spec.md > §6 | Verificado: «Enviar turno» y «Confirmar» como en los AC; `profile.windowed_short` lleva el texto de AC13.1.3. | Ninguna. | Resolved |
| R-06 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/interaction-spec.md > §6 | Verificado: hay claves nuevas y la regla de que toda cadena visible sale del catálogo. | Ninguna. | Resolved |
| R-07 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > tabla de precisiones | Verificado: AC12.6.1–AC12.6.4 y AC12.7.1–AC12.7.3 son Given/When/Then con nivel y prueba (canary, 409, 403, «No informado», comparar con 2). | Ninguna. | Resolved |
| R-08 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > tabla de precisiones, fila 1 | El número quedó en FR13.5 (resuelto). Pero la resolución dice que se citan AC8.1.1, US8.2 y AC2.1.4 como artefactos que el humano decide actualizar, y la fila 1 sigue citando solo FR1.2; esos tres solo aparecen en el texto de navegación. | Añadir AC8.1.1 (destino al iniciar sesión), US8.2 (roles creables) y AC2.1.4 a la columna «Artefacto aprobado que precisa» de la fila del rol `investigador`. | Unresolved |
| R-09 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §6.4 (fila «Procesando») | La regla única de anuncios está en la tabla de precisiones, en interaction-spec §2 y en accessibility R-3, de forma coherente. Pero la fila «Procesando» de §6.4 todavía dice, para un turno, «Cambios anunciados en aria-live (AC10.1.1)», lo que contradice «nunca el estado de cada turno». | Cambiar esa celda a «Se lee al enfocarlo; el avance de la corrida se anuncia por corrida (regla de la tabla de precisiones)». | Unresolved |
| R-10 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/mockups.md > §6.6; interaction-spec.md > §4.3 | Verificado: existe el estado «hallazgo seleccionado» con las marcas A y B a la vez. | Ninguna. | Resolved |
| R-11 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/design-system-mapping.md > §3.1 y §4 | Verificado: la prueba falla solo si dos estados comparten icono y texto a la vez, los estados que faltaban tienen token y la referencia apunta a §1 (P-6). | Ninguna. | Resolved |
| R-12 | Minor | aidlc/spaces/default/intents/261002-veridicus-mvp/inception/refined-mockups/accessibility-checklist.md > P-10–P-12, O-10, O-11, C-8; mockups.md > tabla de precisiones | Verificado: están las filas 1.3.4, 1.3.5, 1.4.12, 2.4.5, 2.5.1–2.5.4 y 3.2.4 con su comprobación, y la excepción por debajo de 1024 px queda declarada y acota P-6. | Ninguna. | Resolved |

### Summary

Los cuatro hallazgos Major quedaron resueltos con los textos exactos de AC2.2.5, AC2.6.5 y AC13.1.3, el registro de modelos de AC12.5.3, la lectura del `admin` y la tabla de precisiones con FR13.5 y los AC propuestos de US12.6 y US12.7. Quedan dos Minor sin bloqueo: faltan tres citas en la fila del rol de la tabla de precisiones (R-08) y una celda de §6.4 que aún contradice la regla de anuncios (R-09).
