# Requisitos de fiabilidad — U5 human-review

**Insumos.** Flujos F2–F5 y §8 «Errores y bordes» de `functional-design/functional-spec.md`
(functional-spec); reglas BR2.1, BR2.6, BR3.1–BR3.6 y BR4.1 de `functional-design/rules.md` (rules);
NFR8, NFR10 y NFR11 de `inception/requirements-analysis/requirements.md` (requirements); C1, C10, C11 y
C15 y las reglas de propiedad de `inception/contract-design/contract-summary.md` (contract-summary);
respuesta P1 = A de `nfr-requirements-questions.md`.

U5 no usa colas ni modelos: toda su fiabilidad descansa en transacciones de PostgreSQL. Los *timeouts*
y el error `503` `system.unavailable` son los de U3 (NFR10.11 y NFR10.12 de U3); aquí se fijan los
propios de U5.

## 1. Objetivo

| ID | Objetivo | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.7 | El flujo de revisión funciona de punta a punta. | `frontend/e2e/review.spec.ts` (desplegar la CoT, aceptar con nota, editar, descartar con nota, cambiar una decisión y ver una sesión ajena en solo lectura) pasa con 0 fallos en cada corrida de nivel 3 antes de etiquetar una entrega. | Nivel 3 |

## 2. Transacciones y concurrencia

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.10 | Cada decisión es una sola transacción (F2 paso 3). | Ronda abierta, estado vigente, validación e inserción de `ReviewDecision` van en una `UnitOfWork`; las métricas se actualizan solo después del *commit*. Prueba con fallo inyectado después de calcular el estado y después de insertar (antes del *commit*): 0 filas nuevas y `veridicus_review_decisions_total` sin cambio. | Nivel 1 |
| NFR10.11 | Dos decisiones simultáneas sobre la misma sesión no leen un estado viejo. | `decide` toma `SELECT … FOR UPDATE` sobre la fila de la ronda abierta antes de calcular el estado vigente (D3). Con dos hilos y una barrera, 50 repeticiones: aceptar y descartar la misma sugerencia a la vez dejan 2 filas en orden, y el `previous_state` de la segunda es el `state` de la primera; dos peticiones idénticas dejan 1 fila y la otra recibe `409` `review.invalid_transition`. | Nivel 1 |
| NFR10.12 | Bloquear la ronda es atómico (BR3.4, E11). | `lock_round` es `UPDATE … SET status = 'locked' … WHERE round_id = :id AND status = 'open'` y comprueba que afectó 1 fila; si no, `report.conflict`. Con dos consolidaciones simultáneas (dos hilos, barrera, 50 repeticiones): exactamente una bloquea la ronda y la otra recibe `report.conflict`. Con una decisión simultánea a una consolidación (que llama `open_round(..., for_update=True)`, precisión en `security-requirements.md` §6): o la decisión aparece en `decisions` del reporte, o recibe `409` `review.round_locked`; nunca queda una decisión con `at` posterior a `locked_at`. | Nivel 1 |
| NFR10.13 | `propose` es idempotente y abre una sola ronda 1 (C10, BR3.5). | Llamarla dos veces con el mismo (`turn_id`, `attempt`, `claim_index`) devuelve los mismos `suggestion_id` sin filas nuevas (índice único). Dos `propose` simultáneas en una sesión sin rondas: el índice único parcial de NFR11.3 deja una sola ronda `open`; la transacción perdedora falla, U4 no confirma su mensaje y la reentrega (NFR10.15 de U4) la guarda en la ronda ya abierta. | Nivel 1 |
| NFR10.14 | `cot-views` es idempotente. | Índice único (`suggestion_id`, `user_id`) e `INSERT … ON CONFLICT DO NOTHING`: 10 llamadas iguales dejan 1 fila y responden `204` las 10 veces. | Nivel 1 |

## 3. Tiempos de espera y fallos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.15 | Toda E/S de U5 tiene *timeout* y espera de bloqueo acotada. | `statement_timeout` de 2 s (el de U3) y `lock_timeout` de 2 s (`VERIDICUS_DB_LOCK_TIMEOUT_MS`, D3), leídos de la configuración validada al arrancar. Si se vence: *rollback*, `503` `system.unavailable`, 0 filas y una línea `WARNING` con `code`. Prueba con una transacción que retiene el bloqueo de la ronda 3 s: la decisión responde `503` en ≤ 2,5 s. | Nivel 0 (configuración) y nivel 1 |
| NFR10.16 | Las decisiones no se reintentan solas. | Una decisión no es idempotente: ni el servidor ni la consola la reintentan. Si la petición falla por red o `503`, la consola conserva la nota o la reformulación escrita, muestra el mensaje del catálogo y vuelve a pedir la sesión; un reenvío manual idéntico de una decisión que sí se guardó recibe `409` `review.invalid_transition`, y la consola entonces muestra el estado vigente. `cot-views` sí se reintenta: hasta 3 veces (0,5 s, 1 s y 2 s). Vitest con un servidor *fake* que falla y que responde `409`. | Vitest |
| NFR10.17 | Un fallo de las métricas nunca tumba una decisión. | Si el cálculo de la razón de descarte falla después del *commit*, la respuesta sigue siendo `201`, se registra un `WARNING` con `code` `metrics.update_failed` (solo en logs, no es un `code` de C1) y la serie conserva su último valor. Al arrancar, `session-api` reconstruye las series de las sesiones con ronda `open` con una consulta de ≤ 2 s; si falla, el proceso arranca igual y `/readyz` no depende de ello (las métricas de C15 son SHOULD). | Nivel 1 |
| NFR10.18 | `/readyz` refleja lo que U5 necesita (C16). | `503` si falta o es inválida la configuración de U5 (§4 de `tech-stack-decisions.md`) o si PostgreSQL no responde; configuración inválida → el proceso termina con código distinto de 0. | Nivel 1 |

## 4. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `session-api` en medio de una decisión | Nada: la transacción no se confirmó | El analista ve el estado vigente al recargar y repite la decisión |
| Reinicio de `session-api` | Los valores en memoria de `veridicus_session_dismissal_ratio` | Se reconstruyen al arrancar (NFR10.17); el contador `veridicus_review_decisions_total` vuelve a 0, como todo contador de Prometheus (`rate()` lo tolera) |
| PostgreSQL no responde | Nada guardado | `503` `system.unavailable`; la consola conserva lo escrito (NFR10.16) |
| Pérdida de la base | Según el respaldo de CloudNativePG | Lo fija Infrastructure Design; decisiones y rondas son historial de auditoría (NFR11) |

## 5. Degradación

Si el juez o Redis no están disponibles, U5 sigue funcionando: se pueden revisar, decidir y consolidar
las sugerencias ya emitidas, porque U5 solo necesita PostgreSQL. Si Prometheus no está, no hay señal
AIR, pero ninguna decisión depende de ella.
