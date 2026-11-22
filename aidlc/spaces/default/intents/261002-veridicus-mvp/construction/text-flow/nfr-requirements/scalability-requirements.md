# Requisitos de escalado — U4 text-flow

**Revisión 2 (2026-11-22).** Segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U4. Sustituye a la revisión 1 del 2026-10-03. Los IDs se conservan; NFR8.9 queda «Retirado».

**Insumos.**
- Flujos F5–F7 y F11 de `functional-design/functional-spec.md` (functional-spec), con FD-U4-09 (una
  sola cola).
- Reglas BR5.4, BR5.8 y BR15.1–BR15.3 de `functional-design/rules.md` (rules).
- FR3.7, NFR2 y NFR8, y los supuestos, de `inception/requirements-analysis/requirements.md`
  (requirements).
- C2, C3, C17, C21 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- NFR-U10-08 (4 peticiones simultáneas en el proxy) y NFR8.2 de U11.
- Respuestas S1 = A (adaptada), P6 = A y P7 = A de `nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 en el uso real; 3 sesiones concurrentes en la prueba de carga | Supuestos de requirements; NFR8 |
| Transcripción máxima | 2 000 turnos y 250 000 caracteres; turnos de hasta 20 000 caracteres | P6 = A, P7 = A |
| Entrevista más larga del piloto | ≈ 186 000 caracteres; queda un 34 % de margen | `docs/validacion-zine/reporte.md` M3 |
| Corridas por sesión | Una incremental por turno TEST, más un modo final | FR3, BR5.3 |
| Corridas simultáneas | 1, en todo el sistema | FD-U4-09; NFR8.7 |

## 2. Requisitos

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR8.7 | cambia | El trabajador atiende una corrida a la vez. | Una réplica de `semantic-agent` con una corrida a la vez, en una sola cola FIFO para todas las sesiones, sin prioridad por modo. Por eso nunca usa más de 1 de las 4 peticiones simultáneas del proxy (NFR-U4-12). La cola de Redis absorbe la concurrencia. Una prueba de nivel 1 con 3 sesiones comprueba que el *fake* de C17 nunca tiene 2 llamadas abiertas |
| NFR8.8 | cambia | La cola cabe dentro del plazo. | Con un p95 de 180 s por corrida incremental (U11) y un tope de espera de `run_queue_wait_max_s` = 10 800 s (NFR3.5), el sistema sostiene hasta 60 corridas incrementales por delante sin que venza ninguna. La prueba de carga (3 sesiones por tanda, cada una con una incremental y un modo final) termina sin `analysis.system` por plazo. Si una tanda vence, es un hallazgo que se resuelve antes de la corrida de NFR8 |
| NFR8.9 | Retirado | Búsqueda de pasajes | Sale el escenario (cambio 01) |
| NFR8.10 | cambia | Los procesos de U4 no impiden más réplicas en el futuro. | `session-api` no guarda en memoria el estado de las sesiones ni de las corridas. La numeración usa un bloqueo en la base (BR5.2) y la ingesta es idempotente por (`run_id`, `attempt`) (NFR10.22). El MVP corre 1 réplica de cada proceso; una segunda réplica del trabajador exige antes revisar NFR8.7 y NFR-U4-12 |
| NFR8.11 | cambia | Los *streams* y las tablas de U4 no crecen sin límite por sí solos. | Los *streams* de C2 y C3 quedan vacíos tras procesar (`XDEL`, NFR10.9), y los de fallidos se recortan a 1 000 entradas. Las tablas guardan el historial (NFR11), y la retención de U13 borra por sesión (BR19.3). En el MVP crecen < 200 MB, con unas 200 filas de `ModelCall` por sesión del piloto. `AnonymizationIncident` no se borra (NFR11.4) |

## 3. Prueba de carga de NFR8

- **Qué corre.** `evaluation/load/run_batches.py`:
  - crea 50 sesiones sintéticas del conjunto de `evaluation/` con `comercial-piloto`, en tandas de 3
    concurrentes;
  - cada sesión entra como un bloque pegado (una corrida incremental), se finaliza y corre su modo final
    (NFR-U4-11);
  - por sesión registra: éxito, corridas en `error` con su `code`, reinicios de pods, `OOMKilled` y el
    pico de memoria de `semantic-agent` y del trabajador.
- **Cuándo se corre.** Solo si pasa NFR8.2 de U11. Se corre a demanda contra el sistema desplegado en la
  máquina de desarrollo, antes de cada entrega etiquetada, y nunca en la CI.
  - Dura unas 7 h, con una corrida a la vez.
  - Gasta llamadas a Anthropic, solo sobre datos sintéticos.
  - El reporte JSON registra la duración y las cifras, sin texto.
- **Umbral.** NFR8.5 (≥ 98 %) y los topes de memoria de `performance-requirements.md` §7.

## 4. Señal para escalar

No hay autoescalado en el MVP.

**Cuándo hay que escalar.** En cualquiera de estos dos casos:
- `veridicus_run_queue_depth` pasa de 10 de forma sostenida;
- `veridicus_run_queue_wait_seconds` se acerca al tope.

**Opciones, en este orden:**
1. Usar en la demostración un perfil con modelos más rápidos (perfil GPU o comercial).
2. Ajustar los tamaños de ventana de U11.
3. Revisar la regla de una corrida a la vez junto con el límite del proxy.

Cada cambio entra por PR con su medición.
