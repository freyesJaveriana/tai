# Requisitos de rendimiento — U6 session-lifecycle

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U6. Sustituye a la revisión 1 del 2026-10-03.
- **IDs.** Los que siguen conservan su número; los que salen quedan «Retirado» sin renumerar; los nuevos
  son NFR3.13–NFR3.17. Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o está **Retirado**.
- **Revisión 1:** se cierran R-01 (el límite de 60 turnos sale con el plazo por turno) y R-02 (reloj
  controlado, `tech-stack-decisions.md` D3) de `reviews/review-01.md`.

**Insumos.**
- Flujos F2–F9 y escenarios E4–E47 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR2.1–BR2.7, BR3.4, BR4.1–BR4.5, BR5.1–BR5.3, BR7.1–BR7.7, BR8.1–BR8.3 y BR9.1–BR9.6 de
  `functional-design/rules.md` (rules).
- FR3.3, FR3.6, FR3.7, FR8, FR10.1, NFR2, NFR3 y NFR8 de `inception/requirements-analysis/requirements.md`
  (requirements, revisión 3; NFR9 «Retirado»).
- C1 (rutas de U6), C2, C11 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Las cifras de C25 que fijaron hoy U4 y U11, y la sección de segunda pasada de
  `nfr-requirements-questions.md`.

**Cómo se mide.** En la **máquina de desarrollo con CPU** (NFR2), con PostgreSQL y Redis reales en
contenedor y el *fake* de C17. Las pruebas `perf` de nivel 1 corren en proceso con `time.perf_counter`
alrededor de la llamada HTTP, como en U3 y U4. Una prueba de rendimiento inestable se arregla o se pone
en cuarentena con un *issue*; nunca se reintenta ni se baja su umbral (`team.md`).

**Cifras de referencia** (C25): bloque o transcripción máxima = 2 000 turnos, 250 000 caracteres y
20 000 por turno; archivo de importación ≤ 2 097 152 bytes (NFR-U6-01). La entrevista más larga del
piloto cabe en esas cifras con margen (comprobación fuera de Git de U4).

## 1. Respuesta de las rutas de U6

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | cambia | `POST /sessions/{id}/transcript` (202): división en el servidor, validación, una transacción con los turnos, `TranscriptPaste` y la corrida, y publicación de C2 | **p95 ≤ 2 500 ms** con el bloque máximo; **p95 ≤ 500 ms** con 60 turnos | Bloque máximo (2 000 turnos, 250 000 caracteres) y bloque de 60 turnos; 20 repeticiones de cada uno, cada una en una sesión nueva | Prueba `perf` de nivel 1. El pegado de la prueba de humo (≤ 60 turnos) cabe en los 10 s que U4 tiene de los 300 s de *N* |
| NFR3.2 | cambia | `GET /sessions` (lista completa, con `pending_suggestions`) | p95 ≤ 300 ms y respuesta ≤ 200 KB | 500 sesiones de los siete estados, 20 % con retirada, 5 sugerencias pendientes cada una; 100 llamadas con y sin `status` | Prueba `perf` de nivel 1; otra prueba cuenta las sentencias SQL de la ruta: ≤ 2, sin consultas por fila (NFR-U6-04) |
| NFR3.3 | cambia | Coste del latido en el sondeo de U4 | `GET /sessions/{id}?since=` del dueño sigue en p95 ≤ 200 ms con la escritura del latido; `POST /heartbeat` p95 ≤ 100 ms. El latido **nunca espera** un bloqueo de la fila de la sesión | 200 sondeos del dueño cada 2 s con reloj controlado; variante con otra transacción que retiene la fila de la sesión durante 3 s | Prueba `perf` de nivel 1: en la variante bloqueada el sondeo sigue en p95 ≤ 200 ms y ese latido se omite (D1) |
| NFR3.4 | cambia | `POST /sessions/{id}/resume` (200) | p95 ≤ 300 ms | Sesión suspendida de 2 000 turnos; 50 reanudaciones, cada una tras volver a suspender | Prueba `perf` de nivel 1 |
| NFR3.5 | Retirado | `POST /scenarios/{id}/versions` | Sale US1.2 con el marco documental (cambio 01) | — | — |
| NFR3.13 | nuevo | `POST /sessions/import` (201): lectura con tope, JSON, esquema de C6 con todos los problemas, consentimiento, perfil y una transacción con la sesión, el consentimiento y los turnos | **p95 ≤ 3 000 ms** con un archivo de 2 000 turnos y 2 MiB; **p95 ≤ 1 000 ms** con 312 turnos (E24). Un cuerpo de más de `import_file_max_bytes` + 16 384 bytes responde `413` en ≤ 500 ms **sin leerse entero** | 20 importaciones de cada tamaño, con archivos sintéticos distintos; un cuerpo de 10 MB para el rechazo | Prueba `perf` de nivel 1; el rechazo además mide que la memoria del proceso no crece más de 20 MiB |
| NFR3.15 | nuevo | `POST /sessions/{id}/final-runs` (202): bloqueo de la sesión, corrida con su plazo, armado de la entrada de C6 completa y publicación tras confirmar | p95 ≤ 1 000 ms con una sesión de 2 000 turnos y 250 000 caracteres; **no depende del trabajador** | 20 lanzamientos (cada uno tras dejar en error el anterior); variante con el *fake* de C17 bloqueado | Prueba `perf` de nivel 1 |
| NFR3.16 | nuevo | `PATCH /sessions/{id}/analysis`, `POST /terminate` y `POST /consent-withdrawal`, con la cancelación de lo encolado y la escritura de las claves antes de responder | p95 ≤ 500 ms cada una | Sesión con 20 corridas `queued` o `processing`; 20 repeticiones por ruta | Prueba `perf` de nivel 1; la misma prueba comprueba que las 20 claves existen cuando llega la respuesta |

## 2. Vista previa en la consola

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.6 | cambia | La vista previa del pegado es inmediata y no llama a la API (BR2.4). | La división de BR2.1 con `speaker-markers.v1.yaml` tarda ≤ 300 ms para 250 000 caracteres y la vista previa de 2 000 turnos se pinta en ≤ 1 s (la lista puede virtualizarse). Prueba Vitest con `performance.now()` sobre el texto máximo; 0 llamadas de red al pulsar «Continuar», «Volver a editar» y «Cancelar» |
| NFR3.14 | nuevo | La validación del archivo en M7 no bloquea la consola y no llama a la API hasta «Importar» (BR7.1–BR7.4, BR7.7). | Leer, analizar y validar con ajv un archivo de 2 MiB y 2 000 turnos tarda ≤ 1 500 ms fuera del hilo principal (D12): durante la validación, un temporizador de 50 ms del hilo principal no se retrasa más de 100 ms. Un archivo de más de `import_file_max_bytes` se rechaza sin leerlo. Prueba Vitest; 0 llamadas de red hasta pulsar «Importar» |

## 3. Suspensión por falta de latido (P1 = A)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.7 | cambia | *T* = `heartbeat_timeout_s` = **180 s** y revisión cada `session_sweep_interval_s` = **30 s** (C25, NFR-U6-01). | Una sesión `open`, guiada o importada, cuyo `coalesce(last_heartbeat_at, created_at)` tiene más de 180 s pasa a `suspended` entre 180 y 210 s después de ese valor; con 179 s no se suspende; una sesión `paused` nunca se suspende (E20, E22). Prueba de nivel 1 con reloj controlado (D3) en los dos bordes |
| NFR3.8 | cambia | La escritura del latido está acotada (respuesta a §11 del Functional Design). | El latido se escribe solo si el valor registrado tiene `heartbeat_write_min_s` = **15 s** o más, con la hora de la base. Medida desde el **último sondeo real**, la suspensión llega entre 165 y 210 s después; 165 s queda muy por encima del temporizador de una pestaña en segundo plano (≈ 60 s), que es lo que P1 protege. Prueba de nivel 1: con sondeos cada 2 s durante 60 s hay ≤ 4 escrituras, y tras el último sondeo la sesión no se suspende antes de 165 s |
| NFR3.9 | se mantiene | La revisión es barata. | La sentencia de suspensión usa el índice parcial sobre las sesiones `open` y tarda p95 ≤ 100 ms con 500 sesiones, de ellas 50 abiertas; prueba `perf` de nivel 1 |

## 4. Corridas de un bloque y del modo final

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.10 | Retirado | Plazo proporcional por turno pegado. | Un bloque crea una sola corrida incremental (BR2.5) y su plazo lo calcula U4 con su fórmula de cola; U6 no calcula plazos |
| NFR3.11 | Retirado | Pegado de 60 turnos sin vencer plazos. | Sale con el plazo por turno (cierra R-01 de la revisión 1); la duración del modo final la registra NFR3.17 |
| NFR3.17 | nuevo | La duración del modo final sobre la transcripción importada máxima queda medida (§11 del Functional Design). | Medición **sin umbral**, a demanda antes de la demostración: importar el archivo sintético máximo (2 000 turnos) y lanzar el modo final con `comercial-piloto` y con `todo-local` en la máquina de desarrollo. El reporte JSON tiene una sección por perfil con la duración, el número de ventanas (BR5.3), el estado final y `run_deadline_final_s` efectivo. Comprobación con control negativo: un reporte sin alguna sección hace fallar el script. La revisión humana decide con dos cifras (duración frente a `run_deadline_final_s` de desarrollo) entre mantener el valor, subirlo por PR hasta el tope de 43 200 s de U11 o limitar la demostración a transcripciones más cortas (NFR-U6-07) |

## 5. Progreso de la corrida (US10.1, SHOULD)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.12 | cambia | El cambio de etapa se ve en un ciclo de sondeo (BR5.1, BR5.3). | Desde que la corrida cambia de estado en el servidor hasta que la franja o el turno muestran el texto nuevo: ≤ 3 s con corridas en curso (`poll_interval_active_s` = 2 más el renderizado). El cronómetro mm:ss se actualiza cada segundo en el navegador sin llamadas a la API, y «N ventanas» se calcula sin llamar a la API. Prueba Vitest con temporizadores falsos y prueba Playwright de nivel 3 con el *fake* de C17 |

## 6. Indexación de una versión nueva

| ID | Estado | Requisito |
|---|---|---|
| NFR9.1 | Retirado | Sale la indexación del escenario (cambio 01; NFR9 «Retirado» en requirements) |

## 7. Recursos

| ID | Estado | Pod | Tope | Cómo se mide |
|---|---|---|---|---|
| NFR8.1 | cambia | API y trabajador de `session-api` | La importación y el pegado máximos no suben el RSS de la API más de 100 MiB; la revisión de suspensión no cambia el tope del trabajador que fija U4 | Pico de RSS durante las corridas de NFR3.1 y NFR3.13 y durante la prueba de NFR8 |

El `limits.memory` de cada pod lo fija Infrastructure Design con un 20 % sobre el pico medido; un pico que
supera su tope se corrige por PR, nunca subiendo el tope en silencio.
