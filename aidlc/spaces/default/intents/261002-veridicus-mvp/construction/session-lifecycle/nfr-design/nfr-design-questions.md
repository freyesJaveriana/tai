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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñó el pegado de hasta 60 turnos de
testimonio con un turno por mensaje, la marca de lote en Redis, la versión nueva de un escenario, la
lista, el latido y la suspensión. El cambio 01 retira el escenario y el plazo por turno: un bloque crea
**una** corrida incremental, y entran la importación, el modo final, la pausa, la terminación y la
retirada del consentimiento. El Functional Design revisión 2 (F2–F9, FD-U6-01 a FD-U6-24) y el NFR
Requirements revisión 2 (tabla NFR-U6-01 a NFR-U6-12) ya están aprobados.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| P1 y P2 de la revisión 1 | P1 = A (marca de lote) pierde su objeto: BR2.5 revisión 2 no republica en el reenvío y la publicación fallida se cierra por plazo (NFR-U6-10). P2 = A sigue: latido y revisión nunca esperan un bloqueo | Revisión 1; Functional Design revisión 2 |
| Requisitos | NFR1.1–NFR1.4, NFR2.1–NFR2.2, NFR3.1–NFR3.17 (NFR3.5, NFR3.10, NFR3.11 Retirado), NFR4.1, NFR8.1–NFR8.14 (NFR8.4, NFR8.12 Retirado), NFR9.1 (Retirado), NFR10.1–NFR10.18, NFR11.1–NFR11.3, NFR12.1, NFR13.1–NFR13.2, NFR14.1–NFR14.2, NFR15.1–NFR15.5; decisiones D1–D13 | `nfr-requirements/`, revisión 2 |
| `PATCH /sessions/{id}/analysis` | Responde `202` con `SessionView` como única 2xx (NFR-U6-03), aunque C1 diga `200` | Puerta de NFR Requirements |
| Cifras de C25 de U6 | `import_file_max_bytes` = 2 097 152, `heartbeat_timeout_s` = 180, `session_sweep_interval_s` = 30, `heartbeat_write_min_s` = 15, ya en C25 v1 con sus relaciones | NFR-U6-01; §5 del NFR Design de U1 |
| Métricas | En `contracts/metrics/session-lifecycle.v1.yaml`, con la etiqueta `origin` ya en la lista cerrada | NFRD-U1-05 |
| Tubería de corridas | Plazo (`domain/deadline.py`), `RunEnqueuer`, espera de publicación, clave de cancelación y su reescritura, supervisor por sesión, publicación fallida con `202` | NFRD-U4-02, NFRD-U4-05, NFRD-U4-06; `reliability-design.md` §4, §10, §11 de U4 |
| Cursor | `change_cursor.bump` primero y orden usuario → sesión → corrida → ronda; sondeo en `REPEATABLE READ READ ONLY` | NFRD-U4-05; `project.md` |
| Ingress sin disco | `veridicus-web` sin *buffering* a disco y tope de 2 113 536 bytes en `/api/` | NFR Design de U2 §3 |
| Redis caído | La consola queda fuera de servicio por `/readyz` | NFR Design de U3 |

## Cómo se registra la revisión

- Los seis documentos y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia y por qué. La revisión 1 queda en el historial de Git.
- Las secciones conservan su número cuando siguen; las que salen quedan «Retirado» sin renumerar y lo
  nuevo toma números nuevos.
- Las precisiones a artefactos aprobados van en la tabla NFRD-U6-xx de `security-design.md`. Las tablas
  de precisiones de la revisión 1 quedan «Superado». Ningún original se edita.

## Lo que el diseño resolverá sin preguntar

1. **Hallazgos de la revisión 1 de esta etapa.** R-01 (codes fuera de C1) queda caduco con C1 revisión 3,
   FD-U6-01 y FD-U6-02. R-02 (margen nulo del turno 60) desaparece con el plazo por turno. R-03
   (`change_cursor.bump` y `lock_timeout`) se cierra: toda escritura de U6 usa `bump`, y el pegado hace
   el trabajo de CPU fuera del bloqueo. R-04 (orden del reenvío) se cierra: el lote se busca antes de
   comprobar el estado. R-05 (`/readyz` frente a terminar al arrancar) se cierra: el proceso termina.
2. **Redis caído.** NFR Requirements de U6 (§4) dice que la lista y la importación siguen. El NFR Design
   de U3 deja la consola fuera de servicio por `/readyz`. Sin Redis no hay sesión web, así que ninguna
   ruta responde. Solo la revisión de suspensión, que corre en el trabajador, sigue. Se aplica la
   decisión de U3.
3. **Supervisor de sesiones.** Corre como cuarto hilo del trabajador de `session-api`, con su conexión,
   para que un supervisor de corridas lento no retrase la suspensión.
4. **Modo final.** La entrada de C6 se arma fuera del bloqueo de la sesión, porque una sesión que admite
   el modo final ya está cerrada a turnos nuevos. Bajo el bloqueo solo se comprueban el estado y los
   contadores.
5. **Tope del cuerpo del pegado.** La cifra derivada de NFR10.1 (1 004 096 bytes) entra en C25 con nombre
   y `derived_from`, para que U6 no use un literal.
6. **Lector `multipart` en memoria.** Es el mismo de U12 en `session-api`. Lo escribe U6 en B7, porque
   B7 va antes que B12.

Ningún punto cambia el alcance ni deja salir del clúster algo que hoy no sale.

**Sin preguntas: todo lo fijan las fuentes.**