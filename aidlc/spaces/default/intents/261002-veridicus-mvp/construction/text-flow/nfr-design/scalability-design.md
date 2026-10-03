# Diseño de escalado — U4 text-flow

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions) de esta unidad; `functional-design/functional-spec.md` (functional-spec);
C2, C3, C4 y C9 de `inception/contract-design/contract-summary.md` (contract-summary); respuestas
P1–P2 de `nfr-design-questions.md`.

## 1. Modelo de capacidad

El cuello de botella es el juez: **un turno a la vez** en un servidor con una sola ranura (NFR8.7). La
cola de Redis absorbe la concurrencia y el plazo proporcional evita que un turno falle solo por esperar.

| Elemento | Réplicas en el MVP | Concurrencia | Cómo escala si hace falta |
|---|---|---|---|
| API de `session-api` | 1 | Hilos de FastAPI | Más réplicas: no guarda estado en memoria |
| Trabajador de `session-api` | 1 | Un hilo por cola | Más réplicas en el mismo grupo de consumidores |
| `semantic-agent` + `model-judge` | 1 pareja | 1 turno | Una pareja más por PR, cada una con su ranura (KEDA es COULD) |
| `model-embeddings` | 1 | Lotes de 32 | Más réplicas detrás del mismo Service |

Capacidad dentro del plazo: con p95 de 60 s y tope de 3 600 s, hasta 60 turnos en cola (NFR8.8). La
prueba de NFR8 (3 transcripciones de ≤ 15 turnos) deja ≤ 45 en cola.

## 2. Colas con grupos de consumidores

| *Stream* | Grupo | Consumidores | Idempotencia |
|---|---|---|---|
| `veridicus:turns` (C2) | `semantic-agent` | 1 por pod | El resultado lleva (`turn_id`, `attempt`); la ingesta descarta duplicados |
| `veridicus:results` (C3) | `session-api-ingest` | 1 hilo por trabajador | Restricción única (`turn_id`, `attempt`) en `TurnEvaluation`; un duplicado se confirma sin efectos |
| `veridicus:indexing` (C4) | `session-api-indexer` | 1 hilo por trabajador | Una versión `ready` o `error` se confirma sin efectos |

Con dos consumidores en el mismo grupo cada resultado se guarda una vez (prueba de NFR8.10). La
numeración de turnos y el `change_seq` del sondeo usan el bloqueo de la fila de la sesión, así que
siguen siendo correctos con varias réplicas de la API.

## 3. Datos y crecimiento (NFR8.9, NFR8.11)

- Pasajes: ≤ 22 000 en total (≈ 70 MB de vectores); búsqueda exacta filtrada por `version_id`, cuyo
  costo depende de los ≈ 1 100 pasajes de una versión, no del total.
- *Streams* de C2 y C3 vacíos tras procesar (`XDEL`); fallidos recortados a 1 000 entradas.
- Tablas de U4 sin borrado (auditoría); crecimiento estimado < 100 MB en el MVP.

## 4. Señales para escalar

| Señal | Umbral | Acción, en este orden, por PR con medición |
|---|---|---|
| `veridicus_turn_queue_depth` | > 30 durante 10 minutos | Perfil GPU para la demostración; ajustar hilos del juez; segunda pareja juez + `semantic-agent` |
| p95 de `veridicus_turn_latency_seconds` | > 60 s en la corrida de nivel 2 | Igual que arriba; nunca subir la meta |
| Pico de memoria de un pod | Sobre su tope de performance-design §7 | Corregir por PR; no subir el tope en silencio |
