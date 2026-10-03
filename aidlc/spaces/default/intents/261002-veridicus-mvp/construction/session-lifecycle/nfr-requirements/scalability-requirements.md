# Requisitos de escalado — U6 session-lifecycle

**Insumos.** Flujos F2–F4 de `functional-design/functional-spec.md` (functional-spec); reglas BR2.3,
BR2.5, BR3.1 y BR4.1–BR4.2 de `functional-design/rules.md` (rules); NFR8 y los supuestos de
`inception/requirements-analysis/requirements.md` (requirements); C1 y C2 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1 y P2 de
`nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real); 3 sesiones concurrentes en la prueba de carga de U4 | Supuestos de requirements; NFR8 |
| Turnos de testimonio por transcripción pegada | ≤ 15 en el Golden Dataset; máximo admitido 60 | Golden Dataset; P2 = A |
| Sesiones en la base | ≤ 500 (las 50 de cada corrida de NFR8 más el uso manual) | Supuesto del MVP |
| Sesiones `open` a la vez | ≤ 50 | Mismo supuesto |
| Versiones por escenario | ≤ 20 en total en el sistema (NFR8.9 de U4) | Supuesto del MVP |

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.2 | U6 no impide correr más de una réplica de la API o del trabajador. | Ningún estado de sesión, latido ni lote pegado vive en memoria del proceso; la revisión de suspensión, la reanudación y el pegado son seguros con dos instancias a la vez gracias a sus sentencias condicionales y restricciones únicas (NFR8.9, NFR8.10). Prueba de nivel 1 con dos revisiones en hilos distintos y dos instancias de la aplicación: cada transición queda una vez. El MVP corre 1 réplica de cada proceso. |
| NFR8.3 | Un pegado tiene un tamaño acotado (P2 = A). | ≤ 60 turnos de testimonio, ≤ 200 turnos en total, ≤ 100 000 caracteres y ≤ 2 000 por turno; cuerpo HTTP ≤ 524 288 bytes (NFR10.1). Las cifras son constantes del archivo compartido de división (`tech-stack-decisions.md` D5), las mismas en la consola y en el servidor; prueba de nivel 0 que compara ambas lecturas del archivo. |
| NFR8.4 | La cola admite un pegado máximo dentro del plazo. | Con la cola vacía, el turno 60 recibe el tope de 3 600 s (NFR3.10) y la corrida de NFR3.11 termina sin `turn.error.timeout`. El margen depende de la latencia real: a 45 s por turno el pegado termina en ≈ 2 700 s; al p95 de 60 s llega justo al tope, sin margen (hallazgo R-06 de la revisión de U4). Si la cola ya tiene turnos de otras sesiones, los últimos turnos del pegado pueden vencer; es el riesgo aceptado de `security-requirements.md` §5. |
| NFR8.5 | La lista de sesiones no se pagina en el MVP. | `GET /sessions` devuelve todas las sesiones ordenadas por `created_at` descendente con una sola consulta agregada (NFR3.2: ≤ 2 sentencias, p95 ≤ 300 ms con 500 sesiones). Si la base pasa de 1 000 sesiones o NFR3.2 deja de cumplirse, se añade paginación por cursor como cambio menor de C1 en un PR propio. |
| NFR8.6 | El latido no multiplica las escrituras. | ≤ 1 `UPDATE` de `last_heartbeat_at` cada 15 s por sesión abierta, aunque la consola sondee cada 2 s (NFR3.8): con 50 sesiones abiertas, ≤ 200 escrituras por minuto. Prueba de nivel 1 que cuenta las sentencias con reloj controlado. |
| NFR8.7 | Las tablas de U6 crecen poco. | `TranscriptPaste` y `SessionStatusChange` son de solo inserción (NFR11) y no se purgan; con ≤ 500 sesiones su tamaño estimado es < 5 MB. Las columnas nuevas de `Turn` (`speaker`, `role`, `paste_batch_id`) no cambian el estimado de < 100 MB de U4 (NFR8.11 de U4). |

## 3. Señal para escalar

No hay autoescalado. Si un pegado deja la cola por encima de 30 turnos durante más de 10 minutos
(`veridicus_turn_queue_depth`, regla informativa de U4) o NFR3.11 falla en CPU, las opciones, en este
orden, son: usar el perfil GPU para la demostración, bajar el límite de turnos de testimonio por PR, o
añadir una segunda pareja juez + `semantic-agent` (U4 §4). Cada cambio entra por PR con su medición.
