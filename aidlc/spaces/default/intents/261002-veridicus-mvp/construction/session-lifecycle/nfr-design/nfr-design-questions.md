# Preguntas de NFR Design — U6 session-lifecycle

**Unidad.** U6 `session-lifecycle`: versiones nuevas de escenarios, transcripción pegada, lista de
sesiones, latido, suspensión y reanudación, y progreso del turno, todo dentro de `session-api` (API y
trabajador) y de la consola.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D10 de
`nfr-requirements/`: *T* = 180 s y revisión cada 30 s, latido escrito como máximo cada 15 s con la hora
de la base, revisión de suspensión como tarea del trabajador con `UPDATE … RETURNING` condicional,
límite de 60 turnos de testimonio y 200 en total, transacción única del pegado con la fila de la sesión
bloqueada, publicación tras confirmar con `MULTI`/`EXEC` de Redis (sin tabla *outbox*), archivo de
división compartido, lista sin paginar y *timeouts* de U4. También el cursor `change_seq` por sesión que
diseñó U4: toda transacción que cambia algo de una sesión bloquea su fila, incrementa el contador y marca
sus filas; por eso la revisión de suspensión, la reanudación y el pegado de U6 también lo incrementan.
Quedan dos huecos de diseño.

---

## P1 — Cómo sabe el reenvío de un pegado si sus turnos ya llegaron a la cola

Si la publicación en Redis falla o vence su *timeout* de 0,5 s tras confirmar el pegado, la API responde
`503` y el navegador reenvía con el mismo `client_request_id`; lo aprobado (NFR10.11) es volver a
publicar los turnos de testimonio que siguen `queued`. Pero un turno ya publicado que espera en la cola
también está `queued`: si el primer `EXEC` sí llegó a Redis (el *timeout* no dice si llegó), el reenvío
duplica hasta 60 turnos. La ingesta descarta el resultado repetido, pero el juez, que atiende un turno a
la vez a ≈ 45–60 s cada uno, los evalúa dos veces: hasta una hora más de cola, y los turnos de detrás
pueden vencer su plazo (tope de 3 600 s).

A. Marca de lote en Redis dentro de la misma transacción `MULTI`/`EXEC`: junto con los `XADD` se
   escribe la clave `veridicus:paste-published:<paste_batch_id>` (solo el identificador, con expiración
   de 24 h). Como `EXEC` es todo o nada en Redis, el reenvío consulta esa clave: si existe, devuelve los
   turnos sin volver a publicar; si no, publica el lote completo. Cubre también el caso de *timeout* sin
   saber si llegó, y no toca `TranscriptPaste`, que es de solo inserción (NFR11.2). (Recomendada)
B. Columna `published_at` en `TranscriptPaste`, escrita después de un `EXEC` correcto; el reenvío solo
   publica si está vacía. Exige permitir un `UPDATE` sobre una tabla de solo inserción y sigue
   duplicando cuando el `EXEC` llegó pero su respuesta se perdió.
C. Se mantiene lo aprobado: republicar todo lo `queued` y aceptar la evaluación doble, que la ingesta
   absorbe por (`turn_id`, `attempt`).
X. Other (please specify)

[Answer]: A **Mode:** guided
## P2 — Cómo conviven el latido y la revisión de suspensión con el bloqueo de la fila de la sesión

El cursor `change_seq` de U4 obliga a bloquear la fila de la sesión en cada escritura (encolar, ingerir
un resultado, vencer un plazo, pegar). El latido de U6 es un `UPDATE` sobre esa misma fila dentro del
sondeo `GET /sessions/{id}`, cuya meta es p95 ≤ 200 ms (NFR3.3); si coincide con un pegado de 200 turnos
(hasta 2 s, *timeout* de 5 s) el sondeo espera ese tiempo. Además, la revisión de suspensión cambia
varias sesiones en un solo `UPDATE` y también debe incrementar su `change_seq` para que la consola vea
el estado «Suspendida».

A. Ni el latido ni la revisión esperan un bloqueo: el latido se escribe en una transacción corta aparte,
   después de leer, con `FOR UPDATE SKIP LOCKED` (si la fila está bloqueada, otra escritura de la sesión
   está en curso y basta el siguiente latido) y **sin** incrementar `change_seq`, porque la consola no lo
   muestra; un error del latido nunca hace fallar el sondeo (NFR10.12). La revisión selecciona las
   sesiones vencidas con `FOR UPDATE SKIP LOCKED`, y en el mismo `UPDATE … RETURNING` pone `suspended`,
   `suspended_at` e incrementa `change_seq`; una sesión bloqueada se revisa en la siguiente vuelta.
   (Recomendada)
B. El latido se escribe en la misma transacción que la lectura y espera el bloqueo como cualquier otra
   escritura (simple, pero el sondeo puede tardar hasta 2 s durante un pegado) e incrementa
   `change_seq`, con lo que cada latido aparece como un cambio en el siguiente sondeo.
C. El latido pasa a una tabla propia (`session_heartbeat`, una fila por sesión) que nunca bloquea la
   fila de la sesión; la revisión hace un `JOIN` con ella. Elimina la espera, pero mueve
   `last_heartbeat_at` fuera de `InterviewSessionRecord`, ya aprobada.
X. Other (please specify)

[Answer]: A **Mode:** guided