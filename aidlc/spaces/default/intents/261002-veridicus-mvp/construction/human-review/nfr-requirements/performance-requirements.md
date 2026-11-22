# Requisitos de rendimiento — U5 human-review

**Revisión 2 (2026-11-22).** Es la segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional
Design revisión 2 de U5. Sustituye a la revisión 1 del 2026-10-03.

**Qué cambia.**
- La decisión incluye ahora el *bump* de la sesión (BR3.8).
- La ruta de observaciones registra el acceso (C23).
- C11 suma `discard_correction_round`.
- Entra la latencia de `purge_session` (C24), que responde a la pregunta del Functional Design §11.

**IDs.** Los que siguen conservan su número; el nuevo es NFR3.9.

**Insumos.**
- Flujos F1, F2, F5, F6 y F7 de `functional-design/functional-spec.md` (functional-spec, revisión 2).
- Reglas BR1.3, BR3.2, BR3.6–BR3.9, BR4.1 y BR6.1 de `functional-design/rules.md` (rules).
- NFR3, NFR7 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements).
- C1, C10, C11, C15 v2, C23 y C24 de `inception/contract-design/contract-summary.md` (contract-summary).
- Respuesta P1 = A de `nfr-requirements-questions.md`.

**Cómo se mide.**
- En la máquina de desarrollo (CPU), con PostgreSQL real en contenedor (nivel 1).
- U5 no llama a ningún modelo: sus tiempos no dependen del juez, del anonimizador ni del perfil.
- No forma parte de los 300 s de la prueba de humo: el humo no decide sugerencias.
- Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*. Nunca se
  reintenta ni se baja su umbral (`team.md`).

## 1. Escenario de medición

Todas las pruebas `perf` de esta unidad usan la misma sesión sintética, que crea un *fixture* de nivel 1:
- **50 sugerencias**, el doble de la carga esperada (`scalability-requirements.md` §1);
- **4 rondas**: la 1 y la 2 bloqueadas, la 3 de corrección descartada y la 4 de corrección abierta;
- 2 decisiones por sugerencia en cada ronda bloqueada y en la descartada.

Así la herencia de BR3.2 recorre dos rondas y salta la descartada en cada lectura.

## 2. Latencia de las rutas de U5

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | cambia | Respuesta `201` de `POST /suggestions/{id}/decisions`. Incluye la autorización de U3 con el bloqueo compartido del usuario, el *bump* de la sesión, `FOR UPDATE` de la ronda, el estado vigente, la validación, la inserción, el *commit* y la actualización de las métricas | **p95 ≤ 200 ms** | 200 decisiones seguidas sobre el escenario de §1, alternando aceptar con nota, editar y descartar | Prueba `perf` de nivel 1, con `time.perf_counter` alrededor de la llamada HTTP en proceso |
| NFR3.2 | cambia | Respuesta `204` de `POST /suggestions/{id}/observation-views`, con el registro de acceso real de U13 | **p95 ≤ 150 ms**, igual la primera vez que al repetirla. El registro de acceso tiene como mucho 500 ms en su punto de guardado (U3) | 100 primeras aperturas y 100 repetidas | Prueba `perf` de nivel 1 |
| NFR3.3 | cambia | Respuesta de rechazo (`403`, `404`, `409`, `413`, `422`) de la ruta de decisiones | p95 ≤ 100 ms, sin filas nuevas. El `413` del cuerpo grande responde sin leer más de `review_body_max_bytes` | 50 peticiones por cada `code` de BR1.1, BR1.4, BR2.1–BR2.4, BR2.7 y BR3.1 | Prueba `perf` de nivel 1 |

## 3. Consultas y operaciones internas

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.4 | cambia | El estado vigente se calcula con un número fijo de consultas, sin importar cuántas rondas tenga la sesión (BR3.2). | Una sola consulta SQL da el estado vigente de **todas** las sugerencias de una sesión, saltando las rondas `discarded`. La usa también la vista de sesión de U4. Una decisión ejecuta como mucho **7 sentencias** SQL, *bump* incluido. Una prueba de nivel 1 cuenta las sentencias con el evento `before_cursor_execute` de SQLAlchemy con 1, 4 y 10 rondas, y el número no cambia. Con 50 sugerencias y 10 rondas, la consulta tarda p95 ≤ 50 ms. |
| NFR3.5 | cambia | Las operaciones de C11 no frenan la consolidación ni la corrección de U7. | En una transacción sobre el escenario de §1, `open_round(for_update=True)` + `pending_count` + `decisions` + `lock_round` suman **p95 ≤ 150 ms**. `open_correction_round` y `discard_correction_round` tardan p95 ≤ 50 ms cada una. Se miden 200 repeticiones, con *rollback* entre ellas. |
| NFR3.6 | se mantiene | `/metrics` responde rápido aunque haya muchas sesiones. | Con 60 series de `veridicus_session_dismissal_ratio`, `GET /metrics` responde en p95 ≤ 100 ms sin consultar la base: el valor se calcula al decidir (`tech-stack-decisions.md` D7). Prueba `perf` de nivel 1. |
| NFR3.9 | nuevo | `purge_session` borra el peor caso de una sesión dentro del plazo de sentencia (BR6.1, C24). | El peor caso de NFR8.2 es una sesión con 250 sugerencias, 10 rondas, 3 decisiones por sugerencia y ronda (7 500 decisiones) y 250 `ObservationsView`. `purge_session` lo borra en **p95 ≤ 2 s** en total, y ninguna sentencia pasa del `statement_timeout` de 2 s. Con las filas de otras 99 sesiones cargadas, `EXPLAIN` de cada `DELETE` no hace `Seq Scan`. Se miden 20 repeticiones con *rollback*. |

## 4. Consola

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.7 | se mantiene | Una decisión se ve en la tarjeta sin esperar al sondeo. | Con la respuesta `201`, la tarjeta muestra el estado nuevo a partir del cuerpo de la respuesta, sin actualización optimista (D11), y vuelve a pedir la sesión. Desde el clic en «Confirmar aceptación», «Guardar» o «Descartar» hasta el estado visible pasa ≤ 1 s. Prueba Playwright de nivel 3. El sondeo de U4 no cambia: `poll_interval_active_s` = 2 s y `poll_interval_s` = 15 s. |
| NFR3.8 | cambia | Desplegar las observaciones no espera a la red. | Las observaciones se despliegan al instante con el texto que ya trajo la sesión. El `POST` de `observation-views` va en segundo plano, y «Aceptar» y «Editar» se habilitan cuando responde `204` (BR5.1), en ≤ 1 s desde el clic. Prueba Playwright de nivel 3. Vitest comprueba que los botones siguen con `aria-disabled` si el `POST` falla. |

## 5. Contribución al MTTV

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR7.1 | cambia | El tiempo de sistema de U5 es una parte despreciable del MTTV (< 10 min, NFR7). | Se toma una sesión del conjunto sintético con 30 sugerencias: 30 aperturas de observaciones y 30 decisiones. El tiempo de servidor de U5 es ≤ 30 × (p95 de NFR3.1 + p95 de NFR3.2) = 10,5 s, es decir ≤ 1,75 % del objetivo de MTTV. El servidor pone la hora `at` de cada decisión con el reloj UTC inyectable (D10), nunca el navegador, para que U7 calcule el MTTV. Se comprueba con las mediciones de NFR3.1 y NFR3.2. |

## 6. Recursos

| ID | Estado | Pod | Tope medido | Cómo se mide |
|---|---|---|---|---|
| NFR8.1 | se mantiene | `session-api` (proceso de la API) | U5 añade ≤ 32 MiB al pico de memoria (RSS) del proceso durante la carga de NFR3.1, frente a la misma corrida sin decisiones | Pico de RSS medido en la prueba `perf`. El `limits.memory` que fije Infrastructure Design ya incluye los topes de U3 y U4 |
