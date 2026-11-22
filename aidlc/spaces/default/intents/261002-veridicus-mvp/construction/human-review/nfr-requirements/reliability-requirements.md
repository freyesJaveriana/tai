# Requisitos de fiabilidad — U5 human-review

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U5. Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** El orden de bloqueo pasa a ser usuario → sesión → ronda, con `change_seq` (BR3.8).
  `propose` lo implementa U4, y U5 conserva el índice de la ronda 1. Las observaciones sustituyen a la
  CoT. Las métricas publican en orden (cierra R-03 de la revisión 1). Se añaden el objetivo de
  disponibilidad y la recuperación, que cierran R-04.
- **IDs.** Ninguno sale ni entra; NFR10.10–NFR10.18 y NFR8.7 conservan su número.

**Insumos.**
- Flujos F1–F7 y §10 «Errores y bordes» de `functional-design/functional-spec.md` (functional-spec).
- Reglas BR1.3, BR2.1, BR2.6, BR3.1–BR3.9, BR4.1 y BR6.1 de `functional-design/rules.md` (rules).
- NFR8, NFR10 y NFR11 de `inception/requirements-analysis/requirements.md` (requirements).
- C1, C10, C11, C15 v2, C16 y C24, con las reglas de propiedad, de
  `inception/contract-design/contract-summary.md` (contract-summary).
- Respuesta P1 = A de `nfr-requirements-questions.md`.

U5 no usa colas ni modelos: toda su fiabilidad descansa en transacciones de PostgreSQL. El `503`
`system.unavailable` y el manejador único son los de U3.

## 1. Objetivos

| ID | Estado | Objetivo | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.7 | cambia | El flujo de revisión funciona de punta a punta. | `frontend/e2e/review.spec.ts` pasa con 0 fallos en cada corrida de nivel 3 antes de etiquetar una entrega. Recorre: desplegar las observaciones, aceptar con nota, editar, descartar con nota, cambiar una decisión, consolidar, abrir una corrección, descartarla y ver una sesión ajena en solo lectura. | Nivel 3 |

**Disponibilidad y respaldo (cierra R-04).** U5 vive en `session-api` y no tiene un objetivo propio:
- hereda la disponibilidad de `session-api`;
- hereda el respaldo de CloudNativePG (RPO y RTO) que fija Infrastructure Design de U2.

Hasta que U2 los fije quedan como «por fijar» y U2 es el responsable. Decisiones, observaciones y rondas
son historial de auditoría (NFR11): ningún mecanismo de U5 las reconstruye si se pierde la base.

## 2. Transacciones y concurrencia

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.10 | cambia | Cada decisión es una sola transacción (F2). | Van en la `UnitOfWork` de la petición: el *bump*, la ronda abierta, el estado vigente, la validación y la inserción de `ReviewDecision`. Las métricas se actualizan solo después del *commit*. Se inyecta un fallo después de calcular el estado y otro después de insertar, antes del *commit*: quedan 0 filas nuevas, el `change_cursor` de la sesión no cambia y `veridicus_review_decisions_total` tampoco. | Nivel 1 |
| NFR10.11 | cambia | Dos decisiones simultáneas sobre la misma sesión no leen un estado viejo. | `decide` hace el *bump* con bloqueo exclusivo de la sesión y luego `SELECT … FOR UPDATE` de la ronda abierta, antes de calcular el estado vigente (D3, BR3.8). Se prueba con dos hilos y una barrera, 50 repeticiones. Aceptar y descartar la misma sugerencia a la vez dejan 2 filas con `change_seq` crecientes, y el `previous_state` de la segunda es el `state` de la primera. Dos peticiones idénticas dejan 1 fila, y la otra recibe `409` `review.invalid_transition` (E33). Una decisión simultánea con la ingesta de U4 no produce interbloqueo. | Nivel 1 |
| NFR10.12 | cambia | Bloquear la ronda es atómico (BR3.4, BR3.7, E11, E18, E20). | `lock_round` hace `UPDATE … SET status = 'locked' … WHERE round_id = :id AND status = 'open'` y comprueba que afectó 1 fila; si no, `report.conflict`. Con dos consolidaciones simultáneas (dos hilos, barrera, 50 repeticiones), exactamente una bloquea y la otra recibe `report.conflict`. Con una decisión simultánea a una consolidación que llama `open_round(for_update=True)` (C11 v2), pasa una de dos cosas: la decisión aparece en `decisions`, o recibe `409` `review.round_locked`. Nunca hay interbloqueo. Con 0 sugerencias, `open_round(for_update=True)` crea la ronda 1 y `lock_round` la bloquea. | Nivel 1 |
| NFR10.13 | cambia | Una sesión tiene como mucho una ronda abierta, también cuando U4 propone a la vez (BR3.5). | `propose` y su idempotencia los implementa y prueba U4 contra C10. U5 aporta el índice único parcial de NFR11.3. Prueba: dos `propose` simultáneas en una sesión sin rondas, más un `open_round(for_update=True)`, dejan una sola ronda `open` con las columnas de la ronda 1 (`kind: initial`; actor de sistema `analysis-worker` o el actor de la consolidación). | Nivel 1 |
| NFR10.14 | cambia | `observation-views` es idempotente (BR1.3). | Índice único (`suggestion_id`, `user_id`) e `INSERT … ON CONFLICT DO NOTHING`. 10 llamadas iguales dejan 1 fila, responden `204` las 10 veces y dejan 10 entradas de acceso. No hace *bump* de la sesión. | Nivel 1 |

## 3. Tiempos de espera y fallos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR10.15 | se mantiene | Toda E/S de U5 tiene *timeout* y una espera de bloqueo acotada. | `statement_timeout` de 2 s (el de U3) y `lock_timeout` de 2 s (`VERIDICUS_DB_LOCK_TIMEOUT_MS`, D3), leídos de la configuración que se valida al arrancar. Si se vence: *rollback*, `503` `system.unavailable`, 0 filas y una línea `WARNING` con `code`. Prueba con una transacción que retiene el bloqueo de la sesión 3 s: la decisión responde `503` en ≤ 2,5 s. | Nivel 0 (configuración) y nivel 1 |
| NFR10.16 | cambia | Las decisiones no se reintentan solas. | Una decisión no es idempotente: ni el servidor ni la consola la reintentan. Si la petición falla por red o por `503`: <br>• la consola conserva la nota o la reformulación escrita; <br>• muestra el mensaje del catálogo; <br>• vuelve a pedir la sesión. <br>Un reenvío manual idéntico de una decisión que sí se guardó recibe `409` `review.invalid_transition`, y la consola muestra el estado vigente. `observation-views` sí se reintenta hasta 3 veces, a los 0,5 s, 1 s y 2 s. Un `404`, `403` o `413` no se reintenta. Vitest con un servidor *fake* que falla y otro que responde `409`. | Vitest |
| NFR10.17 | cambia | Un fallo de las métricas nunca tumba una decisión, y la serie se publica en orden (cierra R-03). | Si el cálculo de la razón falla después del *commit*: <br>• la respuesta sigue siendo `201`; <br>• se registra un `WARNING` con el evento `metrics.update_failed` (solo en logs, no es un `code` de C1); <br>• la serie conserva su último valor. <br>El cálculo y la publicación van bajo un candado en proceso por sesión. Se publica solo si el `change_seq` leído es mayor o igual que el último publicado (D13). Prueba con dos decisiones simultáneas de la misma sesión, 50 repeticiones: el valor final del *gauge* es igual al de `dismissal_window` calculado sobre la base. Al arrancar, `session-api` reconstruye las series de las sesiones con ronda `open` con una consulta de ≤ 2 s. Si falla, el proceso arranca igual y `/readyz` no depende de ello (C15 es SHOULD). | Nivel 1 |
| NFR10.18 | cambia | `/readyz` refleja lo que U5 necesita (C16). | `/readyz` responde `503` si PostgreSQL no responde. Si la configuración de U5 falta o es inválida (`tech-stack-decisions.md` §2), el proceso termina con código distinto de 0. También termina así si una variable intenta subir una cifra de C25. | Nivel 0 y nivel 1 |

## 4. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| Reinicio de `session-api` en medio de una decisión | Nada: la transacción no se confirmó | El analista ve el estado vigente al recargar y repite la decisión |
| Reinicio de `session-api` | Los valores en memoria de `veridicus_session_dismissal_ratio` | Se reconstruyen al arrancar (NFR10.17). `veridicus_review_decisions_total` vuelve a 0, como todo contador de Prometheus; `rate()` lo tolera |
| PostgreSQL no responde | Nada guardado | `503` `system.unavailable`; la consola conserva lo escrito (NFR10.16) |
| Falla el `Job` de retención a mitad de `purge_session` | Nada: el borrado va en la transacción del `Job` (C24) y se revierte entero | El humano vuelve a lanzar el `Job`; purgar de nuevo es seguro (E32) |
| Pérdida de la base | Según el respaldo de CloudNativePG | Lo fija Infrastructure Design de U2 (§1) |

## 5. Degradación

Si el analizador, el anonimizador o Redis no están disponibles, U5 sigue funcionando: se pueden revisar,
decidir, consolidar y corregir las sugerencias ya emitidas, porque U5 solo necesita PostgreSQL. Las
decisiones siguen en cualquier estado de la sesión mientras la ronda esté abierta (BR3.10, E27). Si
Prometheus no está, no hay señal AIR, pero ninguna decisión depende de ella.
