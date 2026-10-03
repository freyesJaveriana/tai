# Requisitos de escalado — U4 text-flow

**Insumos.** Flujos F2, F4, F5 y F7 de `functional-design/functional-spec.md` (functional-spec);
reglas BR2.1, BR5.4, BR5.8 y BR7.2 de `functional-design/rules.md` (rules); NFR2, NFR8 y NFR9 y los
supuestos de `inception/requirements-analysis/requirements.md` (requirements); C2, C3, C4 y C9 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P4, S1 y S2 de
`nfr-requirements-questions.md`.

## 1. Carga esperada del MVP

| Dimensión | Valor | Origen |
|---|---|---|
| Analistas a la vez | 1 (uso real); 3 sesiones concurrentes en la prueba de carga | Supuestos de requirements; NFR8 |
| Turnos por transcripción del Golden Dataset | ≤ 15 (supuesto; se confirma al construir el dataset) | Golden Dataset |
| Escenarios y versiones | ≤ 20 versiones de ≤ 1 MB | Supuesto del MVP |
| Pasajes por versión | ≈ 1 100 para 1 MB con pasajes de 1 000 caracteres | S2 |
| Pasajes en total | ≤ 22 000 (≈ 70 MB de vectores de 768 dimensiones) | Cálculo |

## 2. Requisitos

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR8.7 | El juez atiende un turno a la vez. | Un servidor `model-judge` con una sola ranura y una réplica de `semantic-agent` que procesa un turno a la vez; así la temperatura 0 y la semilla dan resultados repetibles (NFR4.2). La cola en Redis es la que absorbe la concurrencia. |
| NFR8.8 | Capacidad de la cola dentro del plazo. | Con p95 de 60 s y tope de plazo de 3 600 s (NFR3.5), el sistema sostiene hasta 60 turnos en cola sin que ninguno venza. La prueba de carga con 3 transcripciones pegadas de ≤ 15 turnos (≤ 45 turnos en cola) termina sin `turn.error.timeout`. Si el Golden Dataset trae transcripciones más largas, es un hallazgo que se resuelve antes de la corrida de NFR8. |
| NFR8.9 | La búsqueda de pasajes no se degrada con más versiones. | Búsqueda exacta filtrada por versión (índice B-tree sobre `version_id`, sin índice aproximado): p95 ≤ 100 ms con 20 versiones cargadas (NFR3.4). |
| NFR8.10 | Los procesos de U4 no impiden más réplicas en el futuro. | `session-api` no guarda estado de sesión ni de turnos en memoria; la numeración usa bloqueo en la base (BR5.2) y la ingesta es idempotente por (`turn_id`, `attempt`). Prueba de nivel 1 con dos consumidores de C3 en el mismo grupo: cada resultado se guarda una vez. El MVP corre 1 réplica de cada proceso. |
| NFR8.11 | Las tablas y *streams* de U4 no crecen sin límite por sí solos. | Los *streams* de C2 y C3 quedan vacíos tras procesar (`XDEL`, NFR10.9); los de fallidos se recortan a 1 000 entradas. Las tablas de U4 conservan todo (historial de auditoría, NFR11); su crecimiento estimado es < 100 MB en el MVP. |

## 3. Prueba de carga de NFR8

- **Qué corre.** `evaluation/load/run_batches.py` crea 50 sesiones de texto con las transcripciones
  del Golden Dataset, en tandas de 3 sesiones concurrentes, y registra por sesión: éxito, turnos en
  `error` con su `code`, reinicios de pods y `OOMKilled`, y el pico de memoria de cada pod.
- **Dónde y cuándo.** En la máquina de CPU contra el sistema desplegado, a demanda y antes de cada
  entrega etiquetada; no corre en la CI. Con el juez atendiendo un turno a la vez, la corrida dura
  varias horas (≈ 50 × 12 turnos × 45 s ≈ 7,5 h); el reporte JSON registra la duración.
- **Umbral.** NFR8.5 (≥ 98 %) y los topes de memoria de `performance-requirements.md` §7.

## 4. Señal para escalar

No hay autoescalado en el MVP. Si la profundidad de la cola (`veridicus_turn_queue_depth`) pasa de 30
de forma sostenida o NFR3.1 no se cumple en CPU, las opciones, en este orden, son: usar el perfil GPU
para la demostración, ajustar hilos del servidor del juez, o añadir una segunda pareja juez +
`semantic-agent` (KEDA es COULD). Cada cambio entra por PR con su medición.
