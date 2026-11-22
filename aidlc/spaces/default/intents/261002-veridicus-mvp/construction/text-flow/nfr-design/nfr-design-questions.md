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

---

# Segunda pasada — cambio 01, adenda 02 y NFR Requirements revisión vigente (2026-11-22)

**Por qué hay segunda pasada.** La revisión 1 (2026-10-03) diseñaba un evaluador propio: juez, *embeddings*,
umbral, indexación de escenarios y paquete de traspaso. Con el cambio 01, U4 deja de evaluar y orquesta las
corridas de la biblioteca de U11 (C17): crea la sesión con consentimiento y perfil, encola corridas (C2),
corre `AnalysisWorker`, ingiere la salida (C3) con el registro de modelos y el bloqueo por incidente, y la
muestra en M3 y M4. El Functional Design revisión 2 (F3–F15, FD-U4-01 a FD-U4-22) y el NFR Requirements
revisión 2 (tabla NFR-U4-01 a NFR-U4-13) ya están aprobados.

## Lo que ya está decidido

| Tema | Qué queda fijo | Fuente |
|---|---|---|
| P1 y P2 de la revisión 1 | P1 = A (reintento del juez) pierde su objeto: los reintentos de transporte son de U11 (C13). P2 = A sigue en su idea: el cursor es el `change_cursor` de la sesión, con la primitiva compartida `change_cursor.bump` de U5 y el orden sesión → ronda (BR19.2) | Revisión 1; cambio 01; FD-U3-13 |
| Requisitos | NFR1.1–NFR1.7, NFR3.1–NFR3.14, NFR4.6, NFR8.3–NFR8.12, NFR10.1–NFR10.25, NFR11.1–NFR11.5, NFR12.1, NFR15.1–NFR15.5, NFR2, NFR13, NFR14; decisiones D9–D20 | `nfr-requirements/`, revisión 2 |
| Cifras de C25 | Las de NFR-U4-01, -04 y -05, ya en C25 v1 | NFRD-U1-02 |
| Límites por entorno | El catálogo empaquetado es el techo; `VERIDICUS_LIMIT_<NOMBRE>` solo baja | NFRD-U1-09 |
| Métricas | En `contracts/metrics/<slug>.v1.yaml`, con la lista cerrada de etiquetas | NFRD-U1-05 |
| `limits.exceeded` | Siempre `413` | NFR-U1-03 |
| C21 | `413` ante un cuerpo grande; el cliente de U11 traduce `409`, `413`, `422`, `503` y `3xx` a `AnonymizerUnavailable`, con `trust_env=False` y `timeout_s = min(model_call_timeout_s, restante − 10 s)` | NFRD-U10-17; NFRD-U11-04; NFRD-U11-05 |
| Reentrega | El mismo cuerpo seudonimizado puede salir hasta 3 veces por la reentrega de C2 (`run_max_deliveries` = 3), declarado en el ADR | NFRD-U10-14 |
| Piso del plazo | `model_call_timeout_s` ≥ 270 s con perfil comercial, constante en `libs/execution_profiles` | NFRD-U11-03 |
| Latencia por llamada | Solo en memoria de U11; sus agregados van a C19 v2 | NFRD-U11-07 |
| Redis caído | La consola queda fuera de servicio (`/readyz` de U3) | NFR Design de U3 |
| Ingress y AOF | El Ingress `veridicus-web` no escribe cuerpos en disco y cubre el sondeo; la reescritura del AOF acota el rastro en disco | NFR Design de U2 (§3, §6) |

## Cómo se registra la revisión

- Los seis documentos y `traceability.json` pasan a la revisión 2 en el mismo archivo, con una nota de
  cabecera que dice qué cambia. La revisión 1 queda en el historial de Git.
- Las secciones conservan su número cuando siguen; las que salen quedan «Retirado» y nombran a su nuevo
  dueño; lo nuevo toma números nuevos.
- Las precisiones a artefactos aprobados van en la tabla NFRD-U4-xx de `security-design.md`. La tabla de la
  revisión 1 (`reliability-design.md` §10) queda «Superado». Ningún original se edita.

## Lo que el diseño resolverá sin preguntar

1. **Hallazgos de la revisión 1 de esta etapa que siguen vivos.** R-02 (lectura del sondeo en una sola
   instantánea), R-03 (supervisor por sesión con orden fijo de bloqueo), R-05 (solo el bucle del mismo
   consumidor reclama; renovación con `XCLAIM … JUSTID`), R-06 (mensajes de cola forjados) y R-07 (rastro en
   el AOF y en los logs de PostgreSQL, ya acotado por U2 y NFR-U13-12). R-01, R-04, R-08 y R-09 desaparecen
   con el juez de U4.
2. **Coherencia con U10.** La renovación del reclamo no cuenta entregas, y un mensaje con más de
   `run_max_deliveries` entregas va a fallidos sin llamar: el mismo cuerpo sale como mucho 3 veces.
3. **Lo que piden otras unidades:** publicación fallida tras confirmar (NFR-U6-10), vencimiento de los
   turnos de voz y liberación de esperas en el supervisor (NFR-U9-07), índices de `EthicsSessionPort`
   (NFR-U13-06), huella y permutación en la prueba de carga (NFR-U8-06), perfiles `batch_only` fuera de la
   consola (U11).
4. **Incidente que no se pierde.** Un resultado con incidente nunca va a fallidos sin registrar el
   incidente: la ingesta tiene una ruta mínima del incidente.

Ningún punto cambia el alcance ni deja salir del clúster algo que hoy no sale.

**Sin preguntas: todo lo fijan las fuentes.**
