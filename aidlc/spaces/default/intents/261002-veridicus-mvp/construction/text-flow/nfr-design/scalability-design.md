# Diseño de escalabilidad — U4 text-flow

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** La capacidad ya no la fija el juez de U4 sino una corrida a la vez de `semantic-agent`
  sobre la biblioteca de U11, con un tope de 1 de las 4 peticiones simultáneas del proxy. La búsqueda de
  pasajes (NFR8.9) queda «Retirado».

**Insumos.** `nfr-requirements/scalability-requirements.md` (scalability-requirements: NFR8.7, NFR8.8,
NFR8.10, NFR8.11), `performance-requirements.md` (performance-requirements: NFR3.5),
`reliability-requirements.md` (reliability-requirements), `security-requirements.md`
(security-requirements), `observability-requirements.md` (observability-requirements),
`tech-stack-decisions.md` (tech-stack-decisions: D11, D12, D17), `functional-design/functional-spec.md`
(functional-spec), C2 y C3 de `contract-summary.md` (contract-summary); NFRD-U10-14.

## 1. Modelo de capacidad (NFR8.7, NFR8.8)

- **Una corrida a la vez.** Una réplica de `semantic-agent` con `XREADGROUP COUNT 1` y sin concurrencia
  interna: el *fake* de C17 nunca tiene 2 llamadas abiertas (prueba de nivel 1 con 3 sesiones). Así U4 usa
  como mucho 1 de las 4 peticiones simultáneas del proxy (NFR-U4-12).
- **Una sola cola FIFO.** `veridicus:runs` para todas las sesiones y los dos modos, sin prioridad.
- **Cuánto cabe.** Con p95 de 180 s por incremental (U11) y `run_queue_wait_max_s` = 10 800 s, caben
  60 incrementales por delante sin que venza ninguna. La prueba de carga de NFR8.5 (3 sesiones por tanda,
  una incremental y un modo final cada una) debe terminar sin `analysis.system` por plazo.
- **Reentrega acotada.** Como mucho 3 procesamientos por mensaje (`reliability-design.md` §3); la carga
  sobre el proxy y el proveedor en el peor caso es 3 veces la de una corrida, nunca más.

## 2. Colas con grupos de consumidores

| *Stream* | Grupo | Consumidores | Reclamo | Fallidos |
|---|---|---|---|---|
| `veridicus:runs` (C2) | `analysis-worker` | El bucle de `semantic-agent`, nombre = nombre del pod | `XAUTOCLAIM` tras 60 000 ms; renovación `XCLAIM … JUSTID` cada 15 s | `veridicus:runs:failed`, `MAXLEN ~ 1000` |
| `veridicus:results` (C3) | `session-ingest` | El hilo de ingesta del trabajador de `session-api` | `XAUTOCLAIM` tras 60 000 ms (la ingesta dura ≤ 5 s) | `veridicus:results:failed`, `MAXLEN ~ 1000` |

Los grupos se crean al arrancar con `XGROUP CREATE … MKSTREAM` (idempotente). Un segundo consumidor en el
mismo grupo funcionaría por diseño, pero el MVP no lo usa (§4).

## 3. Datos y crecimiento (NFR8.11)

- Los *streams* de C2 y C3 quedan vacíos tras procesar (`XDEL`); los de fallidos se recortan a 1 000.
- Las tablas de U4 guardan historial; la retención de U13 borra por sesión con `purge_session` (BR19.3).
  Estimación del MVP: < 200 MB, con unas 200 filas de `ModelCall` por sesión del piloto.
  `AnonymizationIncident` no se borra (NFR11.4) y crece solo con incidentes.
- Las claves de cancelación caducan solas (TTL).
- `NFR8.9` (búsqueda de pasajes): Retirado.

## 4. Señales para escalar y réplicas futuras (NFR8.10)

- `session-api` no guarda estado de sesiones ni de corridas en memoria; la numeración usa el bloqueo de la
  sesión y la ingesta es idempotente por (`run_id`, `attempt`). La API puede tener más réplicas sin cambios.
- **Una segunda réplica de `semantic-agent`** exige antes revisar NFR8.7 y NFR-U4-12 (peticiones
  simultáneas del proxy y de los servidores locales) y el cálculo del plazo, que hoy supone un solo
  consumidor. No se hace en el MVP.
- **Señales:** `veridicus_run_queue_depth` sostenido por encima de 20 y `veridicus_run_queue_wait_seconds`
  p95 por encima de 3 600 s (`observability-design.md` §4). Son informativas: nadie recibe notificaciones
  en el MVP.
