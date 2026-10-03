# Preguntas de NFR Design — U4 text-flow

**Unidad.** U4 `text-flow` (flujo de texto de punta a punta): carga e indexación del escenario,
turnos de texto, cola C2/C3, evaluación con guardia del umbral y juez, alertas, Paquete de Contexto de
Traspaso y consola M2–M4.

**Lo que ya está decidido y no se vuelve a preguntar.** Requisitos y decisiones D1–D16 de
`nfr-requirements/`: juez Qwen2.5-7B Q4_K_M con una sola ranura, `multilingual-e5-base`, búsqueda
exacta en `pgvector`, umbral inicial 0,80, plazo proporcional a la cola, *timeouts* (juez 180 s,
*embeddings* 30 s), reclamo de pendientes a los 240 s y 3 entregas como máximo, `XDEL` tras confirmar,
bloque de datos en JSON, *prompt* inmutable con SHA-256, trabajador aparte en `session-api`, sondeo
cada 2 s o 15 s con reintento creciente. Quedan dos huecos de diseño.

---

## P1 — Qué hace el evaluador cuando el servidor del juez falla un momento

Hoy, si el juez rechaza la conexión o responde 5xx, el evaluador no confirma el mensaje y el turno
vuelve por `XAUTOCLAIM` a los 240 s (NFR10.16). Un reinicio breve del juez (por ejemplo al cambiar de
pod) le suma así al menos 4 minutos a cada turno en curso, muy por encima del p95 de 60 s.

A. Reintento acotado dentro del mismo procesamiento: solo ante conexión rechazada, `502`, `503` o
   `504`, hasta 2 reintentos con espera de 2 s y 6 s (con variación aleatoria), y solo si el plazo del
   turno lo permite. Si sigue fallando, no se confirma y queda el reclamo de 240 s. El *timeout* de
   180 s y la salida inválida siguen sin reintento. (Recomendada)
B. Se mantiene lo aprobado: ningún reintento en el proceso, solo el reclamo de 240 s.
C. Reintentos con espera creciente hasta que el juez responda o venza el plazo del turno.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Cómo se construye el cursor del sondeo para no perder cambios

La consola consulta `GET /sessions/{id}?since=<cursor>` y solo recibe lo que cambió (C1, P6). Si el
cursor fuera una hora o una secuencia global, dos transacciones que confirman en otro orden pueden
hacer que la consola se salte un cambio (NFR10.20 pide no perder ninguno).

A. Un contador por sesión (`change_seq`) en la fila de la sesión: cada transacción que cambia algo de
   esa sesión (turno, evaluación, sugerencia, paquete) bloquea la fila, incrementa el contador y marca
   sus filas con el nuevo valor. El cursor es ese número codificado de forma opaca; como las escrituras
   de una sesión quedan en serie, ningún cambio confirma con un número menor que uno ya entregado.
   (Recomendada)
B. Hora de actualización (`updated_at > since`) con un margen de 2 s de solapamiento y
   desduplicación en la consola.
C. Una secuencia global de PostgreSQL y un margen de solapamiento.
X. Other (please specify)

[Answer]: A **Mode:** guided
