# Requisitos de rendimiento — U4 text-flow

**Revisión 2 (2026-11-22).** Esta es la segunda pasada por el cambio 01 (DT27), la adenda 02 y el
Functional Design revisión 2 de U4. Sustituye a la revisión 1 del 2026-10-03.

**Qué cambia de la revisión 1.**
- Con el cambio 01, U4 ya no evalúa: orquesta las corridas del analizador (C17, U11).
- La latencia de `analyze`, el *prompt* y los modelos pasan a U11.
- U4 solo mide su parte: encolado, plazo, ingesta, sondeo y la prueba de humo de punta a punta.

**IDs.**
- Los que siguen conservan su número.
- Los retirados quedan como «Retirado».
- Los nuevos son NFR3.13–NFR3.14 y NFR8.12.

**Insumos.**
- Flujos F3–F8 y F10–F15 de `functional-design/functional-spec.md` (functional-spec).
- Reglas BR5.1–BR5.9, BR15.1–BR15.5 y BR17 de `functional-design/rules.md` (rules).
- FR3.7, NFR2, NFR3 y NFR8 de `inception/requirements-analysis/requirements.md` (requirements), donde
  NFR9 está «Retirado».
- De `inception/contract-design/contract-summary.md` (contract-summary): C1, C2, C3, C17, C18 y C25.
- Las cifras de U11, que son los topes y valores de C25 para la máquina de desarrollo:
  - p95 de `analyze` incremental ≤ 180 s;
  - *N* = 300 s con `comercial-piloto` y ≤ 60 turnos.
- Las respuestas P5 = A, S1 = A (adaptada), P6 = A y P7 = A de `nfr-requirements-questions.md`.

**Cómo se mide.**
- Las metas se miden en la **máquina de desarrollo con CPU** (NFR2).
- En los niveles 0 y 1 se usa el *fake* de C17. La prueba de humo usa el sistema desplegado con su
  perfil.
- Una prueba de rendimiento inestable se arregla o se pone en cuarentena con un *issue*. Nunca se
  reintenta ni se baja su umbral (`team.md`).

## 1. Latencia propia de U4

| ID | Estado | Qué se mide | Objetivo | Carga | Cómo se mide |
|---|---|---|---|---|---|
| NFR3.1 | cambia | Desde que `RunResult` llega a `veridicus:results` hasta que sus sugerencias se ven en M4 | **p95 ≤ 10 s** con sondeo activo; la ingesta sola, p95 ≤ 5 s | Resultado de 50 hallazgos y 50 llamadas registradas | Nivel 1 para la ingesta (`perf`), con la hora de `XADD` y la del *commit*; nivel 3 de punta a punta con el *fake* de C17 |
| NFR3.2 | se mantiene | Respuesta de `POST /sessions/{id}/turns` (202) | p95 ≤ 300 ms, **también con el trabajador bloqueado** | 100 envíos seguidos a una sesión de 1 900 turnos; en la variante bloqueada, el *fake* de C17 no responde | Prueba `perf` de nivel 1 en proceso con `time.perf_counter` |
| NFR3.3 | cambia | Respuesta de `GET /sessions/{id}` | Con `since`: p95 ≤ 200 ms. Sin `since` (carga completa): p95 ≤ 1 s | Sesión de 2 000 turnos y 250 000 caracteres (P6 = A, P7 = A), con 100 sugerencias, 20 corridas y 200 llamadas registradas; 200 sondeos | Prueba `perf` de nivel 1 |
| NFR3.4 | Retirado | Recuperación de los 3 pasajes (C9) | Se retira: el cambio 01 quita el marco documental | — | — |
| NFR3.13 | nuevo | Liberación de una corrida en espera (RunPublicationHold, FD-U9-07) | ≤ 1 s desde que se confirma la transcripción que esperaba hasta el `XADD` de C2 | 50 liberaciones | Nivel 1 con reloj controlado (NFR-U4-10) |
| NFR3.14 | nuevo | Un mensaje C2 con la transcripción máxima cabe en `run_message_max_bytes` | El mensaje mide ≤ 2 097 152 bytes en el peor caso admitido: 2 000 turnos, 250 000 caracteres de 4 bytes en UTF-8 y los metadatos de cada turno. Si un caso no cabe, se rechaza con `413` `limits.exceeded` antes de encolar (FR3.7) | Caso límite y el mismo con un carácter más | Nivel 0 (prueba de contrato con el *fixture* de U1) |

**Presupuesto orientativo de NFR3.1.** La medición lo confirma; no lo reemplaza.

| Tramo | Presupuesto |
|---|---|
| Lectura y validación contra C6 | ≤ 1 s |
| Transacción de ingesta | ≤ 2 s |
| Un ciclo de sondeo | ≤ 2 s (`poll_interval_active_s`) |
| Renderizado | ≤ 1 s |

## 2. Plazo de la corrida (S1 adaptada)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.5 | cambia | El plazo crece con la cola para que una corrida no falle solo por esperar. | Ver el detalle debajo de la tabla (NFR-U4-04) |
| NFR3.6 | cambia | La revisión de plazos es frecuente y barata. | El supervisor (`run-supervisor`, BR5.8) corre cada 15 s. Una corrida vencida pasa a `error` con `analysis.system` a más tardar 30 s después de su `deadline_at`, y su clave de cancelación queda escrita. Se prueba en nivel 1 con reloj controlado |

**Criterio medible de NFR3.5** (NFR-U4-04).
- Al encolar y al reintentar se calcula:
  `deadline_at = enqueued_at + plazo propio + min(Σ plazos propios de las corridas por delante en queued o processing de todo el sistema, run_queue_wait_max_s)`.
- El plazo propio sale de `effective_config.limits`:
  - `run_deadline_incremental_s`, que vale 900 s en desarrollo;
  - `run_deadline_final_s`, que vale 3 600 s en desarrollo.
- El tope `run_queue_wait_max_s` vale 10 800 s.
- Una corrida en espera no tiene plazo hasta que se libera.
- Pruebas de nivel 0:

| Corridas por delante | Plazo esperado |
|---|---|
| Ninguna | 900 s |
| Dos incrementales | 2 700 s |
| Un modo final | 4 500 s |
| Veinte incrementales | 900 + 10 800 s |

## 3. Consola

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.7 | cambia | Intervalo de sondeo de M4 (P5 = A). | Cada `poll_interval_active_s` = 2 s mientras haya una corrida en `queued` o `processing`, y cada `poll_interval_s` = 15 s cuando no (NFR-U4-05). Las dos cifras salen de C25. Una prueba Vitest con temporizadores falsos cuenta las llamadas en cada estado |
| NFR3.8 | cambia | Una sugerencia se ve poco después de ingerirse. | Desde el *commit* de la ingesta hasta que la tarjeta aparece en M4: ≤ 3 s con corridas en curso. Prueba Playwright de nivel 3 con el *fake* de C17 |
| NFR3.9 | se mantiene | La interfaz no se bloquea mientras se analiza (NFR3 de requirements). | Con una corrida en `processing`, escribir, enviar otro turno y abrir una sugerencia responden sin esperar al trabajador. La prueba de nivel 3 mide < 1 s por interacción |

## 4. Prueba de humo (*N* de `team.md`)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR3.10 | cambia | *N* = **300 s** con `comercial-piloto` y transcripciones de ≤ 60 turnos (la cifra de U11). | Ver el detalle debajo de la tabla |

**Criterio medible de NFR3.10.**
- `frontend/e2e/smoke.spec.ts`, que llama `scripts/smoke.sh <url-base>`, pega una transcripción
  sintética con una contradicción sembrada.
- Comprueba que aparece ≥ 1 sugerencia con sus dos citas en ≤ 300 s desde el envío.
- Comprueba que un relato coherente produce 0 sugerencias en ≤ 300 s.
- Corre contra el sistema desplegado.
- U4 dispone de ≤ 10 s de esos 300 s (NFR3.1). El resto es de U11 y U10.

## 5. Indexación del escenario

| ID | Estado | Requisito |
|---|---|---|
| NFR9.1 | Retirado | Indexar 1 MB en < 3 min. Sale el escenario (cambio 01) |
| NFR9.2 | Retirado | Tamaño del pasaje. Sale el escenario |
| NFR9.3 | Retirado | Lotes de *embeddings*. Sale el escenario |

## 6. Tamaño del *prompt* del juez

| ID | Estado | Requisito |
|---|---|---|
| NFR3.11 | Retirado | Ventana del juez. Pasa a U11: el *prompt* y la ventana son suyos, y el modo fragmentado lo resuelve U11 |
| NFR3.12 | Retirado | Rechazo de un *prompt* que no cabe. Pasa a U11. U4 rechaza antes de encolar solo lo que pasa de C25 (NFR10.1) |

## 7. Recursos

Los `requests` y `limits` concretos los fija Infrastructure Design con estos topes medidos.

| ID | Estado | Pod | Tope de memoria medido | Cómo se mide |
|---|---|---|---|---|
| NFR8.1 | Retirado | Servidor del juez | Pasa a U2 y U11 | — |
| NFR8.2 | Retirado | Servidor de *embeddings* | Sale con el cambio 01 | — |
| NFR8.3 | cambia | `semantic-agent`, con la biblioteca de U11 en proceso | Pico ≤ 768 MiB en un modo final con la transcripción de 250 000 caracteres y respuestas de 2 MiB | Pico de RSS durante la prueba de NFR8 y una prueba de nivel 1 con el caso máximo |
| NFR8.4 | Retirado | Trabajador de `session-api` indexando 1 MB | Sale la indexación; lo sustituye NFR8.12 | — |
| NFR8.12 | nuevo | Trabajador de `session-api` (ingesta, supervisor y liberación) | Pico ≤ 512 MiB ingiriendo un `RunResult` de 2 MiB | Nivel 1 con el caso máximo y durante la prueba de NFR8 |

El `limits.memory` de cada pod deja al menos un 20 % sobre el pico medido. Si un pico supera su tope, es
un hallazgo que se corrige por PR, no un tope que se sube en silencio.
