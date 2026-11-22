# Requisitos de fiabilidad — U6 session-lifecycle

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U6. Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Los que siguen conservan su número; los que salen quedan «Retirado»; los nuevos son NFR8.13 y
  NFR10.15–NFR10.18.
- **Revisión 1:** se cierran R-02 (reloj controlado, NFR8.9 y `tech-stack-decisions.md` D3) y R-04
  (entrega doble, NFR10.11) de `reviews/review-01.md`.

**Insumos.**
- Flujos F2, F4, F5, F7, F8 y F9, la máquina de estados de §3 y §8 «Errores y bordes» de
  `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR2.5–BR2.7, BR4.1–BR4.6, BR5.2, BR7.6, BR8.1–BR8.3 y BR9.1–BR9.8 de
  `functional-design/rules.md` (rules).
- FR3.3, FR3.6, FR8, NFR4, NFR8 y NFR10 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3) y VE-10 de la adenda 02.
- C1, C2 y C25 de `inception/contract-design/contract-summary.md` (contract-summary), con CD-06.
- Las cifras de C25 de U4 (`cancel_key_margin_s`, `poll_interval_s`) y de U11 (`run_deadline_final_s`).

## 1. Objetivos

El MVP no tiene SLA. Los objetivos medibles de U6 son los de FR8 (nada se pierde ni se duplica al
reanudar), FR3.3 y FR3.6 (pegar e importar dan los mismos turnos que escribir) y su parte de NFR8.

| ID | Estado | Objetivo | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.8 | cambia | Reanudar no pierde ni duplica nada (FR8.3, E12, E13, E44). | Prueba de nivel 1 con reloj controlado y el *fake* de C17: se pega un bloque de 15 turnos y se lanza una corrida; el dueño deja de sondear, la sesión pasa a `suspended`, la corrida en cola termina y se ingiere, y el dueño reanuda. Al terminar: los mismos turnos (números, hablante y texto), corridas, sugerencias y decisiones que antes del corte más lo que terminó mientras tanto, sin duplicados, y exactamente 2 filas nuevas de `SessionStatusChange` (FD-U6-14). Variante de E44 con una importación y el modo final | Nivel 1 |
| NFR4.1 | cambia | Escribir, pegar e importar la misma transcripción da los mismos turnos (BR2.6, E10). | Para cada transcripción sintética de los ejemplos de `speaker-markers.v1.yaml` y una del conjunto de U11, las tres entradas coinciden en el 100 % de los turnos en `n`, hablante y texto (el origen y la página difieren por definición). Ya no se exige igualdad de hallazgos: un bloque da una corrida y un turno escrito da una por turno | Nivel 1 |
| NFR8.13 | nuevo | U6 no hace fallar la prueba de NFR8 (50 sesiones en tandas de 3, con el modo final). | En la corrida de carga de U4, en la que cada sesión entra como un bloque pegado y corre su modo final, las rutas `/transcript` y `/final-runs` responden 0 errores 5xx y 0 rechazos inesperados; la revisión de suspensión no suspende ninguna sesión que la prueba esté sondeando | Corrida de carga a demanda (`scalability-requirements.md` §3) |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible | Verificación |
|---|---|---|---|---|
| NFR8.9 | cambia | La suspensión y la reanudación son idempotentes y no compiten (BR4.2, BR4.5). | La revisión toma las filas `open` vencidas con `FOR UPDATE SKIP LOCKED` (nunca espera a una escritura del usuario), sube `change_cursor` y pasa cada una a `suspended` con su `SessionStatusChange` en la misma transacción; una sesión ya `suspended` o `paused` no genera fila. Reanudar exige `status = 'suspended'` y pone `last_heartbeat_at` en la hora de la base. Pruebas de nivel 1 con el reloj inyectado de D3: dos revisiones a la vez → 1 fila; revisión y reanudación a la vez → estado final coherente con exactamente las filas de las transiciones aplicadas; dos reanudaciones seguidas → la segunda `409` `session.not_suspended` y 1 fila; la revisión justo después de reanudar no vuelve a suspender (E21) | Nivel 1 |
| NFR8.10 | cambia | El pegado es todo o nada y no se duplica (BR2.5, E9). | Turnos, `TranscriptPaste` y la corrida en una sola transacción con la fila de la sesión bloqueada (orden usuario → sesión); un fallo a mitad (inyectado) deja 0 turnos y 0 mensajes. Un reenvío con el mismo `client_request_id` devuelve los mismos turnos y la misma corrida sin filas nuevas (restricción única); dos envíos a la vez del mismo bloque crean un solo lote | Nivel 1 |
| NFR10.11 | cambia | Una falla al publicar no deja corridas varadas (BR2.5, NFR-U6-10). | La publicación de C2 va después de confirmar, con un solo `XADD` por corrida y *timeout* de 0,5 s, sin reintento en U6. Si falla, la respuesta sigue siendo `202`, se registra `ERROR` `run.publish_failed` con `session_id` y `run_id`, y el supervisor de plazos de U4 deja la corrida en `error` con `analysis.system` antes de `deadline_at` + 30 s (E19); M4 ofrece «Reintentar tramo» o «Relanzar modo final». Si el `XADD` llegó pero su respuesta venció, una entrega doble no crea dos resultados: la ingesta de U4 es idempotente por (`run_id`, `attempt`) (R-04 de la revisión 1). Pruebas de nivel 1 con Redis detenido justo tras confirmar y con la misma corrida publicada dos veces | Nivel 1 |
| NFR8.11 | cambia | La suspensión no detiene lo que ya está en cola (BR4.3, E13). | Con la sesión `suspended`, las corridas `queued` o `processing` terminan y se ingieren; un turno, un bloque, el modo final o la pausa responden `409` `session.suspended` con 0 filas; terminar y registrar la retirada sí se admiten | Nivel 1 |
| NFR8.12 | Retirado | Corregir un escenario no altera lo que vio una sesión. | Sale US1.2 con el marco documental (cambio 01) | — |
| NFR10.9 | cambia | Toda E/S de U6 tiene *timeout* explícito, leído de la configuración validada al arrancar. | PostgreSQL ≤ 2 s por consulta y 5 s por transacción (pegado, importación, modo final, pausa, terminación, retirada, revisión de suspensión); Redis ≤ 0,5 s por operación (publicación y claves de cancelación). Son los ajustes de U4; U6 no añade otros | Nivel 0 (configuración) y nivel 1 |
| NFR10.10 | cambia | Una configuración de U6 inválida impide arrancar. | `heartbeat_timeout_s`, `session_sweep_interval_s`, `heartbeat_write_min_s` e `import_file_max_bytes` salen de `limits.load` (C25); una `VERIDICUS_LIMIT_<NOMBRE>` solo puede bajarlas. Además se comprueba al arrancar: *T* ≥ 4 × `poll_interval_s`, `session_sweep_interval_s` ≤ *T* / 2 y 1 ≤ `heartbeat_write_min_s` ≤ *T* / 4. Un valor fuera de regla termina el proceso con código ≠ 0 y un log que nombra el ajuste sin su valor; `/readyz` responde `503`. Una prueba de nivel 0 por regla con su control positivo | Nivel 0 |
| NFR10.12 | se mantiene | Un fallo de la revisión no se pierde ni se acumula. | Si PostgreSQL no responde, la revisión registra `ERROR` y vuelve a intentar en el siguiente intervalo; como la condición se evalúa sobre el estado, ninguna suspensión se pierde, solo se retrasa. Un error al escribir el latido no hace fallar el sondeo: el `GET` responde 200 y registra `WARNING`. Prueba de nivel 1 con la base detenida durante dos intervalos | Nivel 1 |
| NFR10.15 | nuevo | La importación es todo o nada (BR7.6). | La sesión, el consentimiento, los 2 000 turnos y el cambio de estado inicial se crean en una sola transacción; un fallo a mitad (inyectado tras el turno 1 000) deja 0 sesiones y 0 turnos. Una importación válida crea 0 corridas (E24) | Nivel 1 |
| NFR10.16 | nuevo | El modo final no se duplica (BR8.2, E34). | Dos `POST /final-runs` simultáneos sobre la misma sesión: uno `202` y otro `409` `run.final_in_progress`, una sola corrida nueva; lo garantiza el bloqueo exclusivo de la fila de la sesión | Nivel 1 |
| NFR10.17 | nuevo | Las transiciones concurrentes terminan en un estado válido (BR9.8). | Pares a la vez: pausar y suspender, terminar y bloquear (U4), retirar y lanzar el modo final, pausar y lanzar un bloque. En cada caso el estado final está en la tabla de §3, el historial tiene exactamente las filas de las transiciones aplicadas y ninguna corrida queda `queued` en una sesión que no las admite. Orden único de bloqueo usuario → sesión → ronda | Nivel 1 |
| NFR10.18 | nuevo | La cancelación resiste fallos de Redis y desfase de relojes (BR9.6, CD-06). | (a) Si escribir la clave falla, la transición ya confirmada se mantiene y la clave se escribe en la reconexión; mientras tanto el plazo detiene la corrida (prueba con Redis cortado al escribir la clave: 0 llamadas nuevas tras la reconexión). (b) La clave vence en `deadline_at` + `cancel_key_margin_s` (120 s); con el reloj del trabajador 110 s atrasado, el *fake* sigue registrando 0 llamadas nuevas (NFR-U6-08). En Minikube de un nodo los pods comparten reloj | Nivel 1 |

## 3. Recuperación

| Falla | Qué se pierde | Cómo se recupera |
|---|---|---|
| El navegador se cierra o pierde la red | Nada | La sesión pasa a `suspended` entre 165 y 210 s después del último sondeo real (NFR3.7, NFR3.8); las corridas siguen; el dueño reanuda y ve todo como quedó (E44) |
| Reinicio del trabajador de `session-api` | Nada | La revisión es sin estado: el siguiente ciclo suspende lo pendiente (NFR10.12) |
| Reinicio de la API a mitad de un pegado o de una importación | Lo no confirmado | La transacción se revierte (NFR8.10, NFR10.15); el navegador reenvía el pegado con el mismo `client_request_id`; la importación se vuelve a pedir |
| Redis falla tras confirmar un bloque, un modo final o una reanudación del análisis | Nada visible salvo la espera | La corrida termina en `analysis.system` por plazo y se reintenta a mano (NFR10.11) |
| Redis falla al cancelar | Nada | La clave se escribe en la reconexión y el plazo cubre el resto (NFR10.18) |
| Relojes distintos entre pods | Nada | Latido y revisión usan la hora de la base (D3); la clave tiene 120 s de margen (NFR10.18) |

## 4. Degradación

- **Sin trabajador de corridas o sin modelos.** U6 sigue respondiendo: se pega, se importa, se lanza el
  modo final (queda en cola hasta su plazo), se lista, se pausa, se termina, se retira el consentimiento,
  se suspende y se reanuda.
- **Sin Redis.** El pegado, el modo final y la reanudación del análisis confirman y sus corridas terminan
  por plazo; `/readyz` de `session-api` responde `503` (regla de U4). La lista, la importación, la
  suspensión y la reanudación, que solo usan PostgreSQL, siguen funcionando.
