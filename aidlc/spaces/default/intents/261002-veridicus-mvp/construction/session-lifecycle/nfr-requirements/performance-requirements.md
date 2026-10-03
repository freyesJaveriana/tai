# Requisitos de rendimiento — U6 session-lifecycle

**Insumos.** Flujos F1–F6 de `functional-design/functional-spec.md` (functional-spec) y reglas BR1.1,
BR2.1, BR2.3, BR2.5, BR4.1, BR4.2 y BR5.1 de `functional-design/rules.md` (rules); NFR2, NFR3, NFR8 y
NFR9 de `inception/requirements-analysis/requirements.md` (requirements); C1 (rutas de U6) y C2 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

Todas las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2) y con PostgreSQL y
Redis reales en contenedor. U6 no llama a ningún modelo por sí misma: los turnos pegados siguen el
camino de U4 y heredan sus metas (NFR3.1 de U4: p95 ≤ 60 s por turno; plazo proporcional a la cola con
tope de 3 600 s). Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*;
nunca se reintenta ni se baja su umbral para que pase (team-practices).

## 1. Respuesta de las rutas de U6

Las pruebas `perf` de nivel 1 corren en proceso, con `time.perf_counter` alrededor de la llamada HTTP,
como en U3 y U4.

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | `POST /sessions/{id}/transcript` (202): división en el servidor, validación, una transacción con todos los turnos y el `TranscriptPaste`, y publicación de C2 | **p95 ≤ 2 000 ms** en el peor caso permitido; **p95 ≤ 500 ms** con una transcripción de 15 turnos | Peor caso: 60 turnos de testimonio + 140 del entrevistador, 100 000 caracteres (NFR8.3); 20 repeticiones de cada caso, cada una en una sesión nueva | Prueba `perf` de nivel 1; la transacción además respeta el *timeout* de 5 s de NFR10.9 |
| NFR3.2 | `GET /sessions` (lista completa, con `pending_suggestions` por sesión) | p95 ≤ 300 ms y respuesta ≤ 200 KB | 500 sesiones con 20 turnos y 5 sugerencias cada una; 100 llamadas con y sin `status` | Prueba `perf` de nivel 1; una prueba aparte cuenta las sentencias SQL de la ruta: ≤ 2 (sin consultas por fila) |
| NFR3.3 | Coste del latido en el sondeo de U4 | `GET /sessions/{id}?since=` del dueño sigue en p95 ≤ 200 ms (NFR3.3 de U4) con la escritura del latido; `POST /sessions/{id}/heartbeat` p95 ≤ 100 ms | 200 sondeos del dueño cada 2 s simulados con reloj controlado | Prueba `perf` de nivel 1; la misma prueba cuenta ≤ 1 `UPDATE` de `last_heartbeat_at` por cada 15 s de reloj (NFR8.6) |
| NFR3.4 | `POST /sessions/{id}/resume` (200) | p95 ≤ 300 ms | Sesión suspendida con 60 turnos; 50 reanudaciones (cada una tras volver a suspender) | Prueba `perf` de nivel 1 |
| NFR3.5 | `POST /scenarios/{id}/versions` (202) | p95 ≤ 2 000 ms para un archivo de 1 048 576 bytes (lectura, SHA-256, comprobación de duplicado, fila e indexación encolada) | 20 cargas de archivos sintéticos distintos | Prueba `perf` de nivel 1 |

## 2. Vista previa del pegado en la consola

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.6 | La vista previa es inmediata y no llama a la API (BR2.4). | La división de BR2.1 en el navegador tarda ≤ 200 ms para 100 000 caracteres; prueba Vitest que mide con `performance.now()` sobre el texto de peor caso y comprueba 0 llamadas de red al pulsar «Continuar» y «Cancelar». |

## 3. Suspensión por falta de latido (P1)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.7 | *T* = 180 s sin latido y revisión cada 30 s. | Una sesión `open` cuyo `last_heartbeat_at` registrado tiene más de 180 s pasa a `suspended` entre 180 y 210 s después de ese valor; con 179 s no se suspende. Prueba de nivel 1 con reloj controlado en ambos bordes. Valores en configuración (`VERIDICUS_HEARTBEAT_TIMEOUT_SECONDS`, `VERIDICUS_SUSPENSION_SWEEP_SECONDS`, `tech-stack-decisions.md` §2). |
| NFR3.8 | La escritura del latido está acotada. | El latido solo se escribe si el valor registrado tiene 15 s o más (`VERIDICUS_HEARTBEAT_WRITE_MIN_SECONDS`), con la hora de la base. Por eso, medido desde el **último sondeo real**, la suspensión llega entre 165 y 210 s después; 165 s sigue muy por encima del temporizador de una pestaña en segundo plano (≈ 60 s), que es lo que P1 protege. Prueba de nivel 1: con sondeos cada 2 s durante 60 s hay ≤ 4 escrituras, y tras el último sondeo la sesión no se suspende antes de 165 s. |
| NFR3.9 | La revisión es barata. | La sentencia de suspensión (`UPDATE … WHERE status = 'open' AND …`) usa un índice parcial sobre las sesiones `open` y tarda p95 ≤ 100 ms con 500 sesiones, de ellas 50 abiertas; prueba `perf` de nivel 1. |

## 4. Turnos pegados en la cola (P2)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.10 | El plazo de cada turno pegado cuenta los que tiene delante. | En la transacción del pegado, el turno de testimonio *k* (1-indexado) recibe `deadline_at = enqueued_at + 300 s × (1 + n₀ + k − 1)` con tope de 3 600 s, donde `n₀` es el número de turnos `queued` o `processing` del sistema antes del pegado (fórmula de NFR3.5 de U4). Los turnos del entrevistador no reciben plazo ni cuentan en `n`. Prueba de nivel 0: con `n₀ = 0`, los turnos 1, 2 y 12 reciben 300, 600 y 3 600 s; con `n₀ = 5`, el turno 1 recibe 1 800 s. |
| NFR3.11 | Un pegado de 60 turnos de testimonio termina sin vencer plazos. | Con la cola vacía, una transcripción sintética de 60 turnos de testimonio queda con 60 turnos `evaluated` y 0 `turn.error.timeout`. Corrida de nivel 2 a demanda, antes de cada entrega etiquetada (≈ 45–60 min en CPU); el reporte JSON registra la duración de cada turno. Si falla, es un hallazgo que se resuelve por PR (perfil o límite), nunca subiendo el tope del plazo en silencio. |

## 5. Progreso del turno (US10.1, SHOULD)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.12 | El cambio de etapa se ve en un ciclo de sondeo. | Desde que el turno cambia de etapa en el servidor hasta que TurnItem muestra el texto nuevo: ≤ 3 s con turnos en curso (sondeo de 2 s de U4 más el renderizado). El cronómetro mm:ss se actualiza cada segundo en el navegador sin llamadas a la API. Prueba Vitest con temporizadores falsos y prueba Playwright de nivel 3 con el *fake* del juez. |

## 6. Indexación de una versión nueva

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR9.1 | Una versión nueva usa la misma indexación de U4 y cumple su meta. | `POST /scenarios/{id}/versions` publica en C4 un mensaje con el mismo esquema que `POST /scenarios` y lo procesa el mismo indexador, sin código de indexación propio de U6 (prueba de nivel 1 que valida el mensaje contra C4). Una versión de 1 048 576 bytes queda `ready` en < 180 s (NFR9.1 de U4), medido en la misma corrida de nivel 2. |

## 7. Recursos

| ID | Pod | Tope | Cómo se mide |
|---|---|---|---|
| NFR8.1 | Trabajador de `session-api` (con la revisión de suspensión) y API de `session-api` | La revisión de suspensión no cambia el tope de 768 MiB del trabajador (NFR8.4 de U4); el pegado de peor caso no sube el RSS de la API más de 50 MiB | Pico de RSS durante la corrida de NFR3.1 y durante la de NFR8 de U4 |
