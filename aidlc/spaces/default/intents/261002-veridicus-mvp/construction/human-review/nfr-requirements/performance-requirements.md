# Requisitos de rendimiento — U5 human-review

**Insumos.** Flujos F1–F5 de `functional-design/functional-spec.md` (functional-spec) y reglas BR2.1,
BR3.2, BR3.6 y BR4.1 de `functional-design/rules.md` (rules); NFR3, NFR7 y NFR8 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`.

Las mediciones son en la máquina de desarrollo (CPU), con PostgreSQL real en contenedor (nivel 1). U5
no llama a ningún modelo: sus tiempos no dependen del juez ni del perfil GPU. Las metas siguen la escala
de U3 (costo de F2 p95 ≤ 25 ms, NFR3.2 de U3) y de U4 (envío de turno p95 ≤ 300 ms, sondeo p95 ≤ 200 ms,
NFR3.2 y NFR3.3 de U4). Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un
*issue*; nunca se reintenta ni se baja su umbral (team-practices).

## 1. Escenario de medición

Todas las pruebas `perf` de esta unidad usan la misma sesión sintética, creada por un *fixture* de nivel
1: **50 sugerencias** (el doble de la carga esperada, `scalability-requirements.md` §1), **3 rondas**
(1 y 2 bloqueadas, 3 de corrección abierta) y, en cada ronda bloqueada, 2 decisiones por sugerencia.
Así la herencia de BR3.2 recorre dos rondas en cada lectura.

## 2. Latencia de las rutas de U5

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Respuesta `201` de `POST /suggestions/{id}/decisions`: F2 de U3, ronda abierta, estado vigente, validación, inserción, *commit* y actualización de las métricas de C15 | **p95 ≤ 200 ms** | 200 decisiones seguidas sobre el escenario de §1, alternando aceptar (con nota), editar y descartar | Prueba `perf` de nivel 1, `time.perf_counter` alrededor de la llamada HTTP en proceso |
| NFR3.2 | Respuesta `204` de `POST /suggestions/{id}/cot-views` | **p95 ≤ 100 ms**, igual la primera vez que al repetirla | 100 primeras consultas y 100 repetidas | Prueba `perf` de nivel 1 |
| NFR3.3 | Respuesta de rechazo (`403`, `409`, `422`) de la ruta de decisiones | p95 ≤ 100 ms, sin filas nuevas | 50 peticiones por cada `code` de BR1.1, BR2.1–BR2.4 y BR3.1 | Prueba `perf` de nivel 1 |

## 3. Consultas internas

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.4 | El estado vigente se calcula con un número fijo de consultas, sin importar cuántas rondas tenga la sesión (BR3.2). | El estado vigente de **todas** las sugerencias de una sesión sale de **una sola consulta** SQL (la usa también la vista de sesión de U4); una decisión ejecuta como mucho **6 sentencias** SQL. Prueba de nivel 1 que cuenta sentencias con el evento `before_cursor_execute` de SQLAlchemy con 1, 3 y 10 rondas: el número no cambia. Con 50 sugerencias y 10 rondas, p95 ≤ 50 ms para la consulta. |
| NFR3.5 | Las operaciones de C11 no frenan la consolidación de U7. | `open_round` + `pending_count` + `decisions` + `lock_round` sobre el escenario de §1, en una transacción: **p95 ≤ 150 ms** en total (200 repeticiones, con *rollback* entre ellas). |
| NFR3.6 | `/metrics` responde rápido aunque haya muchas sesiones. | Con 60 series de `veridicus_session_dismissal_ratio`, `GET /metrics` responde en p95 ≤ 100 ms sin consultar la base (el valor se calcula al decidir, `tech-stack-decisions.md` D7). Prueba `perf` de nivel 1. |

## 4. Consola

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.7 | Una decisión se ve en la tarjeta sin esperar al sondeo. | Con la respuesta `201`, la tarjeta muestra el estado nuevo a partir del cuerpo de la respuesta (sin actualización optimista, D11) y vuelve a pedir la sesión. Desde el clic en «Aceptar», «Guardar» o «Descartar» hasta el estado visible: ≤ 1 s. Prueba Playwright de nivel 3. El sondeo de U4 (2 s / 15 s, NFR3.7 de U4) no cambia. |
| NFR3.8 | Desplegar la CoT no espera a la red. | La CoT se despliega al instante con el texto que ya trajo la sesión; el `POST` de `cot-views` va en segundo plano y «Aceptar» y «Editar» se habilitan cuando responde `204` (BR5.1), en ≤ 1 s desde el clic. Prueba Playwright de nivel 3; Vitest comprueba que los botones siguen deshabilitados si el `POST` falla. |

## 5. Contribución al MTTV

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR7.1 | El tiempo de sistema de U5 es una parte despreciable del MTTV (< 10 min, NFR7). | Para revisar una sesión del Golden Dataset con 30 alertas (30 `cot-views` + 30 decisiones), el tiempo de servidor de U5 es ≤ 30 × (p95 de NFR3.1 + p95 de NFR3.2) = 9 s, es decir ≤ 1,5 % del objetivo de MTTV. Las marcas `at` de cada decisión las pone el servidor (reloj UTC inyectable, D10), nunca el navegador, para que U7 pueda calcular el MTTV. Se comprueba con las mediciones de NFR3.1 y NFR3.2. |

## 6. Recursos

| ID | Pod | Tope medido | Cómo se mide |
|---|---|---|---|
| NFR8.1 | `session-api` (proceso de la API) | U5 añade ≤ 32 MiB al pico de memoria (RSS) del proceso durante la carga de NFR3.1, frente a la misma corrida sin decisiones | Pico de RSS medido en la prueba `perf`; el `limits.memory` que fije Infrastructure Design ya incluye los topes de U3 y U4 |
