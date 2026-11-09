## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-09T14:29:08Z
**Iteration:** 1

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Critical | inception/contract-design/contract-summary.md > C13, C18, C20, CD-09 | El módulo neutral `model_calls` de U1 elimina el ciclo U10↔U11. No cambió en esta pasada. | Ninguna. | Resolved |
| R-02 | Major | inception/contract-design/contract-summary.md > C2, C25 | Plazo vencido, clave de cancelación con margen y AOF de Redis siguen declarados. | Ninguna. | Resolved |
| R-03 | Major | inception/contract-design/contract-summary.md > C13, C18, C19, C21, regla 8 | Nombres en inglés y tabla de correspondencia con C6. | Ninguna obligatoria. | Resolved |
| R-04 | Major | inception/contract-design/contract-summary.md > C19 | Esquema cerrado de las llamadas del reporte, con fixtures inválidos y prueba del canary. | Ninguna. | Resolved |
| R-05 | Major | inception/contract-design/contract-summary.md > C13 «Reintentos», C21 | La tabla de reintentos separa `local` de `anonymizer` y concuerda con las respuestas de C21. | Ninguna. | Resolved |
| R-06 | Major | inception/contract-design/contract-summary.md > C21, C18 | El proxy resuelve el destino en su copia del perfil y trae pruebas negativas. | Ninguna. | Resolved |
| R-07 | Minor | inception/contract-design/contract-summary.md > C1 `/sessions/import` | Sin cambios. | Ninguna. | Resolved |
| R-08 | Minor | inception/contract-design/contract-summary.md > C18 «Ventana del modo fragmentado» | Resuelto. El texto fija que manda `chunking.window` del perfil y que `limits.fragment_window_turns` es su tope. Lo mismo vale para `overlap`. ExecutionProfiles rechaza un perfil que pase del tope. Sin `window` se usa el tope, y la ventana usada queda en `registro.fragmentado.ventana`. Las `description` del esquema lo repiten. | Ninguna. | Resolved |
| R-09 | Minor | inception/contract-design/contract-summary.md > C25 | Sin cambios. | Ninguna. | Resolved |
| R-10 | Minor | inception/contract-design/contract-summary.md > `SessionStatus`, tabla `error.codigo` | Sin cambios. | Ninguna. | Resolved |
| R-11 | Minor | inception/contract-design/contract-summary.md > C1 `Consent`, C6, CD-10 | Sin cambios. | Ninguna. | Resolved |
| R-12 | Major | inception/contract-design/contract-summary.md > C21 (cuerpo, `destination_slot`, pruebas negativas), C13 (`DestinationSlot`, `GenerateRequest`, tabla de reintentos), C20 | Resuelto. C21 añade `destination_slot` (`primary`/`fallback`) como campo obligatorio, con `additionalProperties: false`. El proxy lo resuelve en su copia del perfil. Responde 422 si `fallback` no tiene `fallback_provider` o este es local. `DestinationSlot` está definido en C13 y `GenerateRequest` lo lleva. La CLI lo recibe como el `destination` ya resuelto (C20). La tabla de reintentos tiene dos filas de 451: con `primary` se hace una sola llamada nueva con `fallback`, y con `fallback` la corrida termina en `bloqueo_contenido`. No hay bucle. La llamada de respaldo se registra con `fallback_provider: true`. Hay pruebas negativas y una positiva, y en los rechazos el doble no recibe llamadas. Queda una imprecisión menor: el comentario de `GenerateRequest` dice «fallback solo tras ContentBlocked». Es una regla del núcleo y el proxy no la hace cumplir, lo cual es aceptable. | Ninguna. | Resolved |
| R-13 | Minor | inception/contract-design/contract-summary.md > bloques YAML (C1, C2, C6, C7, C18, C19) y regla 1 de propiedad | Resuelto. Las 18 bloques YAML cargan con PyYAML y no queda ninguna clave suelta por comas en `description`. La única clave con valor nulo son los `value: null` intencionales del catálogo C25. La regla 1 añade a U1 una prueba de nivel 0 con validador estricto (`jsonschema` con metaesquema y ajv `strict`), que falla si una `description` deja una clave suelta. | Ninguna. | Resolved |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| PyYAML `safe_load_all` sobre los 18 bloques ```yaml | PASS, 0 errores | Todos los bloques parsean. |
| Búsqueda de claves con valor nulo en los mapas | Solo `limits.*.value` (C25, intencional) | No quedan claves nulas espurias por comas en `description`. |
| `ast.parse` sobre los 9 bloques ```python | PASS, 0 errores | Los Protocol compilan. |
| Referencias cruzadas de `destination_slot` | Coherentes entre C13 (Protocol y reintentos), C20 y C21 (esquema, 422, pruebas) | Sin hueco ni contradicción. |

### Summary

R-12 y R-13 están corregidos y R-08 queda decidido: manda `chunking.window` y `limits` es el tope. Los YAML y Python validan. Sin hallazgos nuevos que bloqueen, así que el contrato es implementable sin que U10, U11 o U1 tengan que inventar rutas.
