# Requisitos de rendimiento — U4 text-flow

**Insumos.** Flujos F1–F10 de `functional-design/functional-spec.md` (functional-spec) y reglas BR2.1,
BR5.4, BR5.8, BR7.2 y BR9.1 de `functional-design/rules.md` (rules); NFR2, NFR3, NFR8 y NFR9 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C2, C3, C9 y C14 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P5 y S1–S3 de
`nfr-requirements-questions.md`.

Todas las metas se miden en la **máquina de desarrollo con el perfil CPU** (NFR2), con el juez
Qwen2.5-7B-Instruct Q4_K_M y `multilingual-e5-base` (P1, P2). El perfil GPU puede ir más rápido, pero
ninguna meta depende de él. Una prueba de rendimiento inestable se arregla o se pone en cuarentena con
un *issue*; nunca se reintenta ni se baja su umbral para que pase (team-practices).

## 1. Latencia del turno de texto

| ID | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|
| NFR3.1 | Tiempo desde que el turno queda `queued` hasta `evaluated` (`evaluated_at − submitted_at`) | **p95 ≤ 60 s** (P4) | Todos los turnos de texto de las 10 transcripciones del Golden Dataset, una sola sesión a la vez | Nivel 2: el reporte JSON registra p50, p95 y máximo; la marca de hora la guarda el sistema |
| NFR3.2 | Respuesta de `POST /sessions/{id}/turns` (202) | p95 ≤ 300 ms, **también con el juez bloqueado** (E7) | 100 envíos seguidos; en la variante bloqueada, el *fake* del juez no responde | Prueba `perf` de nivel 1 en proceso, `time.perf_counter` alrededor de la llamada HTTP |
| NFR3.3 | Respuesta de `GET /sessions/{id}?since=<cursor>` | p95 ≤ 200 ms | Sesión con 50 turnos, 20 sugerencias y 5 paquetes; 200 sondeos con y sin `since` | Prueba `perf` de nivel 1 |
| NFR3.4 | Recuperación de los 3 pasajes de una afirmación (C9) | p95 ≤ 100 ms | Versión de 1 MB (unos 1 100 pasajes), 200 consultas | Prueba `perf` de nivel 1 con PostgreSQL + `pgvector` real |

**Presupuesto orientativo de NFR3.1** (lo confirma la medición, no la reemplaza): *embeddings* de las
afirmaciones ≤ 3 s; recuperación ≤ 1 s; *prompt* del juez (instrucciones en caché del servidor más el
bloque de datos) y generación ≤ 50 s; ingesta y sondeo ≤ 4 s.

## 2. Plazo de evaluación (S1)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.5 | El plazo crece con la cola para que un turno no falle solo por esperar. | Al encolar (y al reintentar): `deadline_at = enqueued_at + 300 s × (1 + n)`, donde `n` es el número de turnos en `queued` o `processing` de **todo el sistema** en ese momento, con tope de 3 600 s. Pruebas de nivel 0 con `n = 0` (300 s), `n = 2` (900 s) y `n = 20` (3 600 s). El valor base y el tope son configuración (`VERIDICUS_TURN_DEADLINE_BASE_SECONDS`, `VERIDICUS_TURN_DEADLINE_MAX_SECONDS`). |
| NFR3.6 | La revisión de plazos es frecuente y barata. | La tarea de BR5.8 corre cada 15 s; un turno vencido pasa a `error` con `turn.error.timeout` a más tardar 30 s después de su `deadline_at` (prueba de nivel 1 con reloj controlado). |

## 3. Consola

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.7 | Intervalo de sondeo de M4 (P5). | Cada 2 s mientras algún turno esté `queued` o `processing`; cada 15 s cuando no. Prueba Vitest con temporizadores falsos que cuenta las llamadas en cada estado. |
| NFR3.8 | Una alerta se ve poco después de evaluarse. | Desde `evaluated_at` hasta que la tarjeta aparece en M4: ≤ 3 s con turnos en curso (un ciclo de sondeo más el renderizado). Prueba Playwright de nivel 3 con el *fake* del juez. |
| NFR3.9 | La interfaz no se bloquea mientras se evalúa (NFR3 de requirements). | Con un turno en `processing`, escribir, enviar otro turno y abrir una alerta responden sin esperar al juez (E7); la prueba de nivel 3 mide < 1 s por interacción. |

## 4. Prueba de humo (*N* de team-practices)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.10 | *N* = 120 s (P4). | `frontend/e2e/smoke.spec.ts` (llamado por `scripts/smoke.sh <url-base>`) envía la transcripción con discrepancia sembrada y comprueba ≥ 1 alerta con sus 4 campos obligatorios en ≤ 120 s; envía el caso de Hecho No Documentado y comprueba 1 paquete sin alerta ni pregunta en ≤ 120 s. Corre contra el sistema desplegado con los modelos reales en CPU. |

## 5. Indexación del escenario

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR9.1 | Un documento de 1 MB queda listo en menos de 3 minutos. | Desde la respuesta 202 de `POST /scenarios` hasta `ready_at`: < 180 s para un archivo sintético de 1 048 576 bytes. Prueba de nivel 2 (necesita el modelo real); el reporte registra el tiempo y el número de pasajes. |
| NFR9.2 | Tamaño máximo de un pasaje (S2). | 1 000 caracteres; una oración más larga queda sola en su pasaje (BR2.1). Prueba de propiedad de nivel 0: ningún pasaje supera 1 000 caracteres salvo los de una sola oración. |
| NFR9.3 | Los *embeddings* se piden por lotes. | Lotes de 32 textos con *timeout* de 30 s por lote; ningún lote supera 512 *tokens* por texto (con el prefijo `passage: `). |

## 6. Tamaño del *prompt* del juez (S3)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR3.11 | El *prompt* de un turno cabe en la ventana del juez. | Ventana del servidor de 12 288 *tokens*. El bloque de datos lista cada pasaje una sola vez y no pasa de 6 000 *tokens*, contados con el tokenizador del propio servidor del juez antes de llamarlo. Instrucciones ≤ 1 000 *tokens* (prueba de nivel 0 sobre el archivo del *prompt*) y salida `max_tokens = min(4 096, 200 × afirmaciones enviadas)`. |
| NFR3.12 | Un turno que no cabe se rechaza sin llamar al juez. | Si el bloque supera 6 000 *tokens*: no hay llamada al juez, el resultado es `error` con `turn.error.system`, 0 alertas, 0 paquetes, y la consola muestra el mensaje del catálogo para `turn.error.system`, que pide dividir un turno largo (precisión en `security-requirements.md` §6). Prueba de nivel 0 con un turno de 2 000 caracteres de afirmaciones cortas y un contador de *tokens* falso. |

## 7. Recursos

Los `requests` y `limits` concretos los fija Infrastructure Design con estos topes medidos:

| ID | Pod | Tope de memoria medido | Cómo se mide |
|---|---|---|---|
| NFR8.1 | Servidor del juez (`model-judge`) | Pico ≤ 7 GiB con la ventana de 12 288 *tokens* llena | Pico de RSS durante la corrida de NFR8 |
| NFR8.2 | Servidor de *embeddings* (`model-embeddings`) | Pico ≤ 1,5 GiB con lotes de 32 | Ídem |
| NFR8.3 | `semantic-agent` | Pico ≤ 512 MiB | Ídem |
| NFR8.4 | Trabajador de `session-api` (ingesta, indexador, plazos) | Pico ≤ 768 MiB indexando 1 MB | Ídem, durante NFR9.1 |

El `limits.memory` de cada pod deja al menos un 20 % sobre el pico medido; si un pico supera su tope,
es un hallazgo que se corrige por PR, no un tope que se sube en silencio.
