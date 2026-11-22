# Diseño de rendimiento — U4 text-flow

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** U4 ya no llama al juez ni a los *embeddings*: su presupuesto es la API, la cola y la
  ingesta (≤ 10 s de los 300 s de la prueba de humo). §2 (tamaño del *prompt*) y §4 (indexación) quedan
  «Retirado». §3 gana el sondeo en una instantánea (cierra R-02 de la revisión 1). Lo nuevo empieza en §8.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements: NFR3.1–NFR3.3,
NFR3.5–NFR3.10, NFR3.13, NFR3.14, NFR8.3, NFR8.12), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`security-requirements.md` (security-requirements), `observability-requirements.md`
(observability-requirements), `tech-stack-decisions.md` (tech-stack-decisions: D9, D11–D13, D15, D20),
`functional-design/functional-spec.md` (functional-spec: F4–F8, F13), C1, C2, C3 y C25 de
`contract-summary.md` (contract-summary); NFRD-U1-09; NFR-U13-06.

## 1. Camino crítico de U4 (NFR3.1, NFR3.8, NFR3.10)

| Tramo | Presupuesto p95 | Diseño |
|---|---|---|
| `RunResult` en `veridicus:results` → lectura de la ingesta | ≤ 0,5 s | `XREADGROUP BLOCK 5000` en un hilo dedicado; no comparte bucle con el supervisor |
| Parseo y segunda línea (C6, campos, escáner) | ≤ 1 s con 50 hallazgos | Validador compilado una vez al arrancar (D9); escáner de U11 sobre `hecho` y `observaciones` |
| Transacción de ingesta | ≤ 3 s, tope 5 s | Una transacción: `bump` → corrida → `RunAttempt`, `ModelCall` y `DiscardedCandidate` con `executemany` → `propose` (C10) → `COMMIT`; métricas en `after_commit` |
| `COMMIT` → tarjeta en M4 | ≤ 3 s (NFR3.8) | Sondeo cada 2 s con corridas activas (NFR3.7) más ≤ 200 ms del sondeo con `since` |
| **Total de U4** | **≤ 10 s** (NFR3.1); ingesta sola ≤ 5 s | Medido en nivel 1 (`perf`) con la hora de `XADD` y la del `COMMIT`, y en nivel 3 de punta a punta |

El resto de los 300 s de la prueba de humo (NFR3.10) es de U11 y U10. La prueba de nivel 1 usa un
`RunResult` de 50 hallazgos y 50 llamadas registradas.

## 2. Tamaño del *prompt* · Retirado

NFR3.11 y NFR3.12 pasan a U11 (ventana del juez y modo fragmentado). U4 solo rechaza antes de encolar lo
que pasa de C25 (§9).

## 3. Base de datos y sondeo

- **Índices** (NFRD-U4-11): `turn (session_id, n)` para la numeración y la carga; `(session_id,
  change_seq)` en `turn`, `run_status_change`, `run_attempt` y `review_suggestion` para el sondeo;
  `run_status_change (run_id, attempt, at DESC)` para el estado vigente; un índice parcial sobre las
  corridas `queued` por `at` para el plazo y el supervisor; `interview_session (retention_until)` y
  `(created_at) WHERE retention_until IS NULL` para `EthicsSessionPort` (NFR-U13-06).
- **Sondeo con `since` (NFR3.3, p95 ≤ 200 ms).** Una transacción `REPEATABLE READ READ ONLY` (cierra R-02):
  lee `change_cursor` de la sesión y después cada tabla con `change_seq > n` por su índice. El costo depende
  de lo que cambió, no del tamaño de la sesión. El estado vigente de las sugerencias con decisiones nuevas lo
  calcula la función de U5 sobre las filas devueltas.
- **Carga completa (p95 ≤ 1 s).** Misma transacción sin filtro, con 2 000 turnos y 250 000 caracteres:
  respuesta de ≈ 1,1 MB que se serializa con `orjson`. Medido en nivel 1 con 200 sondeos sobre la sesión
  de NFR3.3.
- **Pool.** `psycopg_pool` con 5 conexiones en la API y 3 en el trabajador (una por hilo); el `statement_timeout`
  de 2 s se fija al abrir cada conexión.
- **Numeración del turno.** `SELECT … FOR UPDATE` de la sesión vía `change_cursor.bump`, que ya bloquea la
  fila: el número sale del mismo bloqueo, sin secuencia aparte (BR5.2).

## 4. Indexación del escenario · Retirado

Sale con el cambio 01 (NFR9.1–NFR9.3 Retirado).

## 5. Separación de procesos (D11, D12; NFR3.2, NFR3.9)

- La API de `session-api` solo atiende HTTP: no consume colas ni corre el supervisor. Con el trabajador
  bloqueado, `POST /sessions/{id}/turns` sigue en p95 ≤ 300 ms (NFR3.2): valida, confirma, publica y
  responde `202`.
- El trabajador de `session-api` tiene tres hilos (ingesta, supervisor y liberación) con su propia conexión
  cada uno; una ingesta lenta no retrasa el supervisor.
- `semantic-agent` corre una corrida a la vez (NFR8.7) en su bucle; el servidor HTTP mínimo de salud y
  métricas vive en otro hilo y responde aunque `analyze` esté ocupado.
- NFR3.9 se mide en nivel 3: con una corrida en `processing`, escribir, enviar otro turno y abrir una
  sugerencia tardan < 1 s.

## 6. Consola (NFR3.7, NFR3.9)

- TanStack Query v5 con `refetchInterval` dinámico: `poll_interval_active_s` (2 s) si alguna corrida está en
  `queued` o `processing`, `poll_interval_s` (15 s) si no; las cifras se generan en *build* desde
  `contracts/limits.v1.yaml` (D13).
- La respuesta del sondeo se aplica como *upsert* por ID; la lista de turnos se virtualiza a partir de 200
  filas para que una sesión de 2 000 turnos no bloquee la interfaz.
- Envío de turnos optimista con `client_request_id`; el reenvío no duplica.

## 7. Recursos (NFR8.3, NFR8.12)

| Proceso | Pico | Cómo se respeta |
|---|---|---|
| `semantic-agent` | ≤ 768 MiB en un modo final con 250 000 caracteres y respuestas de 2 MiB | Una corrida a la vez; la entrada y la salida se sueltan al terminar; sin caché entre corridas; U11 lee las respuestas con tope de tamaño |
| Trabajador de `session-api` | ≤ 512 MiB ingiriendo un `RunResult` de 2 MiB | Un mensaje a la vez por hilo (`COUNT 1`); inserciones por lotes; la salida parseada se suelta tras el `COMMIT` |
| API de `session-api` | Sin cifra propia; el corte de NFR10.11 limita el crecimiento a ≤ 20 MiB con un cuerpo de 5 MB | Lectura por trozos del cuerpo |

Los `requests` y `limits` de cada contenedor los fija U2 en Infrastructure Design con estas cifras.

## 8. Liberación de corridas en espera (NFR3.13)

El hilo de liberación consulta cada `VERIDICUS_RELEASE_POLL_MS` = 500 ms las esperas cuya transcripción ya
se confirmó (consulta indexada sobre `RunPublicationHold` sin liberar), calcula el plazo con la hora de
liberación, confirma y publica en C2. Peor caso: 500 ms de espera más ≤ 200 ms de transacción y `XADD`,
dentro de 1 s. Prueba de nivel 1 con reloj controlado y 50 liberaciones.

## 9. Límites antes de encolar (NFR3.14, NFR10.1, NFR10.23)

- **Origen de las cifras.** `veridicus_contracts.limits.load(os.environ)` al arrancar (D20): el catálogo
  empaquetado es el techo y `VERIDICUS_LIMIT_<NOMBRE>` solo baja (NFRD-U1-09).
- **Orden de comprobación** en `POST /sessions/{id}/turns`, todo antes de crear filas:
  1. Corte por bytes del cuerpo (`security-design.md` §7).
  2. Turno de 1 a `turn_max_chars` caracteres tras quitar los bordes.
  3. Totales: `turn_count + 1 ≤ transcript_max_turns` y `char_count + len ≤ transcript_max_chars`, con
     contadores guardados en la fila de la sesión y actualizados en la misma transacción (sin sumar turnos).
  4. Tamaño del mensaje C2: el mensaje se serializa antes del `COMMIT` y se compara con
     `run_message_max_bytes`; si no cabe, `413` `limits.exceeded` y *rollback*.
- **Peor caso de NFR3.14.** 250 000 caracteres de 4 bytes (1 000 000 bytes) más 2 000 turnos con sus
  metadatos (≈ 160 bytes cada uno, 320 000 bytes) y la configuración efectiva: ≈ 1,35 MB, por debajo de
  2 097 152. Prueba de nivel 0 con el *fixture* límite de U1 y el mismo con un carácter más.

## 10. Plazo y supervisor (NFR3.5, NFR3.6)

El cálculo del plazo y el supervisor están en `reliability-design.md` §4. Su costo: la suma de plazos por
delante es una consulta agregada sobre el índice parcial de corridas `queued` o `processing`; el supervisor
lee solo los `session_id` vencidos y abre una transacción corta por sesión.
