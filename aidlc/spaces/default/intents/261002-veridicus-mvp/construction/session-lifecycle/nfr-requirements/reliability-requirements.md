# Requisitos de fiabilidad — U6 session-lifecycle

**Insumos.** Flujos F2, F4 y F5, la máquina de estados de §3 y §8 «Errores y bordes» de
`functional-design/functional-spec.md` (functional-spec); reglas BR1.1, BR2.5, BR2.6 y BR4.1–BR4.6 de
`functional-design/rules.md` (rules); FR3.3, FR8 y NFR4, NFR8 y NFR10 de
`inception/requirements-analysis/requirements.md` (requirements); C1 y C2 y las reglas de propiedad de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

## 1. Objetivos

El MVP no tiene SLA. U6 no agrega pasos a la corrida de NFR8 de U4 (texto escrito turno a turno), pero
sus objetivos medibles son los de FR8 (nada se pierde ni se duplica al reanudar) y FR3.3 (pegar da lo
mismo que escribir):

| ID | Objetivo | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.8 | Reanudar no pierde ni duplica nada (FR8.3, E12). | Prueba de nivel 1 con reloj controlado y el *fake* del juez: se pega una transcripción de 15 turnos, el dueño deja de sondear tras el turno 6, la sesión pasa a `suspended`, los turnos en cola terminan (E13) y el dueño reanuda. Al terminar: 15 turnos con números 1–15 sin huecos ni repetidos, un resultado por (`turn_id`, `attempt`), el mismo número de alertas y paquetes que en la corrida sin corte, y exactamente 2 filas nuevas de `SessionStatusChange` (`open → suspended` de sistema y `suspended → open` del dueño). | Nivel 1 |
| NFR4.1 | Pegar produce lo mismo que escribir turno a turno (BR2.6, E10). | Para cada una de las 10 transcripciones del Golden Dataset y el caso de Hecho No Documentado, en su forma sin líneas del entrevistador, la corrida pegada y la escrita coinciden en el 100 % de los turnos, comparados por ordinal de testimonio: fragmento, `document_id`, calificación de cada afirmación y tipo de resultado (alerta, paquete o ninguno). Nivel 1 con el *fake* del juez (cada PR) y nivel 2 con el modelo real (temperatura 0, semilla fija y una ranura, NFR4.2 de U4). Con las líneas del entrevistador, el reporte de nivel 2 registra cuántos turnos difieren, sin bloquear. | Nivel 1 y nivel 2 |

## 2. Requisitos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR8.9 | La suspensión y la reanudación son idempotentes y no compiten. | La revisión hace un `UPDATE … SET status = 'suspended' … WHERE status = 'open' AND COALESCE(last_heartbeat_at, created_at) < now() − T RETURNING id` e inserta el `SessionStatusChange` de cada fila devuelta en la misma transacción; una sesión ya `suspended` no genera otra fila. Reanudar hace la transición inversa con la condición `status = 'suspended'` y pone `last_heartbeat_at = now()`. Pruebas de nivel 1: dos revisiones a la vez → 1 fila; revisión y reanudación a la vez → estado final coherente con exactamente las filas de las transiciones aplicadas; dos reanudaciones seguidas → la segunda `409` `session.not_suspended` y 1 fila; la revisión justo después de reanudar no vuelve a suspender. | Nivel 1 |
| NFR8.10 | El pegado es todo o nada y no se duplica (BR2.5, E9). | Numeración de todos los turnos, `TranscriptPaste` y plazos en una sola transacción con la fila de la sesión bloqueada (como BR5.2 de U4); un fallo a mitad (inyectado en la prueba) deja 0 turnos y 0 mensajes. Un reenvío con el mismo `client_request_id` devuelve los mismos turnos sin crear filas (restricción única `(session_id, client_request_id)`); dos envíos a la vez del mismo pegado crean un solo lote. Los turnos de testimonio se publican en C2 en el orden de su número. | Nivel 1 |
| NFR10.11 | Una falla al publicar no deja turnos varados. | La publicación de C2 va después de confirmar la transacción, en una canalización `MULTI`/`EXEC` de Redis con *timeout* de 0,5 s y un reintento. Si aun así falla, la API registra `ERROR` `transcript.publish_failed` con `session_id` y `paste_batch_id` y responde `503` `system.unavailable`; el reenvío con el mismo `client_request_id` vuelve a publicar los turnos de testimonio que siguen `queued` sin haber empezado. Una entrega doble se absorbe por la ingesta idempotente de U4. Si nadie reenvía, los turnos terminan por plazo (NFR10.17 de U4) y se reintentan a mano. Prueba de nivel 1 con Redis detenido justo tras confirmar. | Nivel 1 |
| NFR8.11 | La suspensión no detiene lo que ya está en cola (BR4.3, E13). | Con la sesión `suspended`, los turnos `queued` o `processing` terminan `evaluated` o `error` y sus resultados se ingieren; un turno o pegado nuevo responde `409` `session.not_open` con 0 filas. `finalize` desde `suspended` lo trata U7. | Nivel 1 |
| NFR8.12 | Corregir un escenario no altera lo que ya vio una sesión (BR1.1, E1). | Cargar la versión 2 deja la sesión ligada a la versión 1 con su `version_id` y SHA-256, y sus recuperaciones siguen devolviendo pasajes de la versión 1. Dos cargas a la vez del mismo escenario reciben números consecutivos sin repetir (restricción única `(scenario_id, version_number)`). La indexación de la versión nueva reutiliza el camino de U4 y es todo o nada (NFR10.18 de U4). | Nivel 1 |
| NFR10.9 | Toda E/S de U6 tiene *timeout* explícito, leído de la configuración validada al arrancar. | PostgreSQL ≤ 2 s por consulta y 5 s para la transacción del pegado y para la de la revisión de suspensión; Redis ≤ 0,5 s por operación (también la canalización del pegado). Mismos ajustes de U4; U6 no añade otros. | Nivel 0 (configuración) y nivel 1 |
| NFR10.10 | Una configuración de U6 inválida impide arrancar. | `VERIDICUS_HEARTBEAT_TIMEOUT_SECONDS`, `VERIDICUS_SUSPENSION_SWEEP_SECONDS` y `VERIDICUS_HEARTBEAT_WRITE_MIN_SECONDS` se validan con las reglas de `tech-stack-decisions.md` §2; un valor fuera de rango hace terminar el proceso con código distinto de 0 y un log que nombra el ajuste, y `/readyz` responde `503` mientras falte. Una prueba de nivel 0 por regla con su control positivo. | Nivel 0 |
| NFR10.12 | Un fallo de la revisión no se pierde ni se acumula. | Si PostgreSQL no responde, la revisión registra `ERROR` y vuelve a intentar en el siguiente intervalo; como la condición se evalúa sobre el estado y no sobre eventos, ninguna suspensión se pierde, solo se retrasa. Un error de la escritura del latido no hace fallar el sondeo: el `GET` responde 200 y registra `WARNING`. Prueba de nivel 1 con la base detenida durante dos intervalos. | Nivel 1 |

## 3. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| El navegador se cierra o pierde la red | Nada | La sesión pasa a `suspended` entre 165 y 210 s después del último sondeo real (NFR3.7, NFR3.8); el dueño reanuda y ve los turnos tal como quedaron (FR8.3) |
| Reinicio del trabajador de `session-api` | Nada | La revisión es sin estado: el siguiente ciclo suspende lo pendiente (NFR10.12) |
| Reinicio de la API a mitad de un pegado | El pegado sin confirmar | La transacción se revierte (NFR8.10); el navegador reenvía con el mismo `client_request_id` |
| Redis falla tras confirmar un pegado | Nada si se reenvía | NFR10.11 |
| Relojes distintos entre pods | Nada | Latido y revisión usan la hora de la base (`now()`), no la del pod |

## 4. Degradación

Si el juez no está disponible, U6 sigue respondiendo: se pegan transcripciones (los turnos esperan en
cola hasta su plazo), se listan sesiones, se suspende y se reanuda. Si Redis no responde, el pegado
responde `503` y `/readyz` de `session-api` responde `503` (NFR10.19 de U4); la lista y la reanudación,
que solo usan PostgreSQL, siguen funcionando.
