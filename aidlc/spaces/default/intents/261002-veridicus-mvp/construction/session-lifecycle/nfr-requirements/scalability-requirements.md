# Requisitos de escalado — U6 session-lifecycle

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U6. Sustituye a la revisión 1 del 2026-10-03. Los IDs que siguen conservan su número; lo que
sale queda «Retirado»; el nuevo es NFR8.14.

**Insumos.**
- Flujos F2–F4, F7 y F8 de `functional-design/functional-spec.md` (functional-spec, revisión 2) y la
  pregunta abierta de §11 sobre la paginación.
- Reglas BR2.3, BR2.5, BR3.1, BR3.4, BR4.1, BR4.2, BR7.2 y BR8.3 de `functional-design/rules.md` (rules).
- NFR8 y los supuestos de `inception/requirements-analysis/requirements.md` (requirements).
- C1, C2, C11 y C25 de `inception/contract-design/contract-summary.md` (contract-summary), con las cifras
  que fijaron hoy U4 y U11.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 en uso real; 3 sesiones concurrentes en la prueba de NFR8 | Supuestos de requirements; NFR8 |
| Turnos por bloque pegado o por archivo importado | Típico: 15–60 (conjunto sintético) y ≈ 300 (E24); máximo admitido 2 000 turnos y 250 000 caracteres | C25 (U4); conjunto de U11 |
| Tamaño del archivo importado | Típico ≈ 0,1–0,6 MB; máximo 2 097 152 bytes | NFR-U6-01 |
| Sesiones en la base | ≤ 500 (cada corrida de NFR8 crea 50; la retención de U13 borra las vencidas) | Supuesto del MVP |
| Sesiones `open` a la vez | ≤ 50 | Mismo supuesto |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.2 | se mantiene | U6 no impide correr más de una réplica de la API o del trabajador. | Ningún estado de sesión, latido, lote ni importación vive en memoria del proceso; la revisión, la reanudación, el pegado, el modo final y la cancelación son seguros con dos instancias a la vez gracias a sus sentencias condicionales, `SKIP LOCKED`, el bloqueo de la fila de la sesión y las restricciones únicas (NFR8.9, NFR8.10, NFR10.16). Prueba de nivel 1 con dos revisiones en hilos distintos y dos instancias: cada transición queda una vez. El MVP corre 1 réplica de cada proceso |
| NFR8.3 | cambia | Un bloque y un archivo tienen un tamaño acotado por C25. | ≤ `transcript_max_turns` = 2 000 turnos, ≤ `transcript_max_chars` = 250 000 caracteres, ≤ `turn_max_chars` = 20 000 por turno, sin pasar los totales de la sesión (NFR-U6-02); archivo ≤ `import_file_max_bytes` = 2 097 152 bytes. La consola y el servidor leen las mismas cifras de `contracts/limits.v1.yaml` (Python con `limits.load` y TypeScript con `contracts/ts/`); una prueba de nivel 0 compara las dos lecturas |
| NFR8.4 | Retirado | La cola admite un pegado máximo dentro del plazo por turno. | Un bloque es una sola corrida con el plazo de cola de U4; la duración del modo final la mide NFR3.17 |
| NFR8.5 | cambia | La lista de sesiones **no se pagina en el servidor** en el MVP (respuesta a §11 del Functional Design: NFR8 no lo exige). | `GET /sessions` devuelve todas las sesiones ordenadas por `created_at` descendente con ≤ 2 sentencias (NFR3.2: p95 ≤ 300 ms y ≤ 200 KB con 500 sesiones); la consola pagina de 25 en 25 (BR3.4). NFR8 añade 50 sesiones por corrida, muy por debajo. Si la base pasa de 1 000 sesiones o NFR3.2 deja de cumplirse, se añade paginación por cursor como cambio menor de C1 en un PR propio |
| NFR8.6 | se mantiene | El latido no multiplica las escrituras. | ≤ 1 `UPDATE` de `last_heartbeat_at` cada 15 s por sesión abierta, aunque la consola sondee cada 2 s (NFR3.8): con 50 sesiones abiertas, ≤ 200 escrituras por minuto. Prueba de nivel 1 que cuenta las sentencias con reloj controlado |
| NFR8.7 | cambia | Las tablas de U6 crecen de forma acotada. | `TranscriptPaste` y `SessionStatusChange` son de solo inserción y las borra solo la retención (U13, `purge_session`); con ≤ 500 sesiones ocupan < 5 MB. Los turnos importados son lo que más crece: en el peor caso teórico (500 sesiones de 250 000 caracteres) ≈ 150 MB de texto; con el tamaño típico, < 50 MB. Infrastructure Design dimensiona el volumen de la base con el peor caso |
| NFR8.14 | nuevo | La parte de U6 en la prueba de NFR8 escala a 3 sesiones concurrentes. | Con 3 sesiones a la vez que pegan su bloque, sondean cada 2 s y lanzan su modo final, las rutas de U6 cumplen sus metas de `performance-requirements.md` (NFR3.1, NFR3.3, NFR3.15) medidas durante la corrida, y NFR8.13 se cumple |

## 3. Señal para escalar

No hay autoescalado. Las señales son:
- la profundidad de la cola de U4 (`veridicus_run_queue_depth`) por encima de 10 durante 10 minutos;
- el modo final de NFR3.17 más largo que `run_deadline_final_s` de desarrollo.

Las opciones, en este orden: usar el perfil GPU para la demostración, ajustar el perfil o el plazo por PR
(U11), o limitar la demostración a transcripciones más cortas. U6 no sube ninguna cifra de C25 en
silencio: todo cambio entra por PR con su medición.
