# Preguntas de NFR Requirements — U4 text-flow

**Unidad.** U4 `text-flow`: carga e indexación del escenario, sesión, turnos, evaluación semántica con
la guardia del umbral, juez, paquete de traspaso, ingesta y consola M2–M4
(`functional-design/functional-spec.md`, `rules.md`).

**Lo que ya está decidido y no se vuelve a preguntar.** Juez cuantizado de ≤ 8B parámetros en CPU,
temperatura 0 y semilla fija, *embeddings* multilingües locales, `top_k = 3`, un llamado al juez por
turno, metas de calidad de NFR4 y NFR5, indexación de 1 MB en < 3 min (NFR9), 50 sesiones en tandas de
3 con ≥ 98 % de éxito (NFR8), servidores con `llama.cpp` en GGUF (U2), turnos de 1–2 000 caracteres.
`requirements.md` dejó para esta etapa el umbral, el modelo del juez y de *embeddings*, la latencia por
turno y el *N* de la prueba de humo; son las preguntas de abajo, más el intervalo de sondeo.

---

## P1 — Modelo del juez

El juez califica cada afirmación y escribe la CoT en español. Debe ser de ≤ 8B parámetros, correr en
CPU en GGUF y ser de una familia distinta a la del modelo que genere el Golden Dataset (NFR5,
Escenario B). Un modelo más grande razona mejor pero tarda más por turno en CPU.

A. Qwen2.5-7B-Instruct, cuantizado Q4_K_M (unos 4,7 GB, licencia Apache 2.0): buen español y buena
   obediencia al esquema JSON. (Recomendada)
B. Llama-3.1-8B-Instruct, Q4_K_M (unos 4,9 GB, licencia comunitaria de Meta).
C. Qwen2.5-3B-Instruct, Q4_K_M (unos 2 GB): más del doble de rápido, con más riesgo de no llegar a las
   metas de NFR4.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Modelo de *embeddings*

Fija la dimensión del vector en `pgvector`, el tiempo de indexación (NFR9: 1 MB en < 3 min) y la
calidad de la recuperación de los 3 pasajes.

A. `multilingual-e5-base` (768 dimensiones, unos 280 M parámetros, ventana de 512 *tokens*): buen
   equilibrio entre calidad en español y velocidad en CPU. (Recomendada)
B. `bge-m3` (1 024 dimensiones, unos 570 M parámetros): mejor recuperación, pero 2 a 3 veces más lento,
   con riesgo para NFR9.
C. `multilingual-e5-small` (384 dimensiones, unos 120 M parámetros): el más rápido, con recuperación más
   pobre.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Valor del umbral de similitud y cómo se calibra

El umbral decide qué afirmaciones llegan al juez y cuáles quedan como Hecho No Documentado
(AUTONOMIA-05). El Golden Dataset aún no existe, así que no se puede medir hoy; hace falta un valor
inicial para que el servicio arranque y una regla para fijar el definitivo.

A. Valor inicial provisional 0,80 y calibración en el nivel 2: barrer de 0,70 a 0,95 en pasos de 0,01
   sobre el Golden Dataset y elegir el valor que cumple NFR4 (≥ 5 de 6 discrepancias, ≤ 1 alerta en las
   alineadas, 0 alertas en el caso de Hecho No Documentado) con más margen; el valor entra por PR con el
   reporte del barrido. (Recomendada)
B. Fijar ya 0,80 sin calibración.
C. Calibrar con un percentil de las similitudes de las transcripciones alineadas (por ejemplo, el 5.º
   percentil), sin barrido completo.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Latencia por turno, plazo de evaluación y *N* de la prueba de humo

Con un juez de 7B en CPU, un turno tarda decenas de segundos. El plazo (`deadline_at`) debe cubrir
además la cola cuando 3 sesiones envían turnos a la vez a un único servidor del juez (NFR8).

A. p95 ≤ 60 s por turno de texto del Golden Dataset con una sola sesión; plazo de evaluación de 300 s;
   *N* de la prueba de humo = 120 s. (Recomendada)
B. p95 ≤ 30 s, plazo de 90 s y *N* = 60 s (exige el modelo de 3B de P1-C).
C. p95 ≤ 120 s, plazo de 600 s y *N* = 240 s.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Intervalo de sondeo de la consola

Mientras hay turnos en cola o procesándose, M4 consulta `GET /sessions/{id}?since=<cursor>`
(contract-design P6). Un intervalo corto muestra antes la alerta, pero carga más a `session-api`.

A. Cada 2 s mientras haya turnos `queued` o `processing`; sin turnos en curso, cada 15 s.
   (Recomendada)
B. Cada 5 s siempre.
C. Cada 1 s mientras haya turnos en curso; sin turnos en curso, cada 10 s.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

## Seguimiento

Al cruzar las respuestas aparecen tres huecos que impiden fijar criterios medibles.

## S1 — Plazo de evaluación cuando hay varios turnos en cola

P4 fija un plazo de 300 s contado desde que el turno entra en cola (`deadline_at`, BR5.4). El servidor
del juez atiende un turno a la vez (temperatura 0 y semilla fija exigen no mezclar peticiones). Si se
pega una transcripción de 15 turnos (FR3.3) o 3 sesiones envían a la vez (NFR8), los últimos turnos
esperan más de 300 s en cola y pasarían a «Error» por plazo aunque nada haya fallado; NFR8 cuenta ese
*timeout* como fallo.

A. Plazo proporcional a la cola: `deadline_at = enqueued_at + 300 s × (1 + turnos en `queued` o
   `processing` de todo el sistema al encolar)`, con tope de 3 600 s; el reintento lo calcula igual.
   Un turno sin cola conserva los 300 s de P4. (Recomendada)
B. Plazo fijo más largo para todos los turnos: 1 800 s.
C. Plazo fijo de 300 s; el arnés de NFR8 envía cada turno solo cuando el anterior quedó evaluado y la
   transcripción pegada (U6) se encola por tandas.
X. Other (please specify)

[Answer]: A **Mode:** guided

## S2 — Tamaño máximo de un pasaje del escenario

Functional Design (BR2.1) dejó para esta etapa el máximo de caracteres por pasaje. El modelo de
*embeddings* elegido (P2) lee hasta 512 *tokens*; un pasaje más largo se recorta en silencio. Pasajes
más cortos dan citas más precisas pero más pasajes por documento.

A. 1 000 caracteres (unos 250–300 *tokens*): cabe con holgura en la ventana y mantiene corto el
   *prompt* del juez; 1 MB da unos 1 100 pasajes. (Recomendada)
B. 1 600 caracteres: más contexto por pasaje, cerca del límite de 512 *tokens*.
C. 600 caracteres: citas más precisas; 1 MB da unos 1 800 pasajes y más tiempo de indexación.
X. Other (please specify)

[Answer]: A **Mode:** guided

## S3 — Turno cuyo *prompt* no cabe en la ventana del juez

Un turno de 2 000 caracteres con muchas afirmaciones cortas puede juntar decenas de pasajes; en CPU un
*prompt* muy largo tarda minutos y puede superar la ventana del modelo. Hace falta un límite y qué pasa
cuando se supera.

A. Ventana del servidor de 12 288 *tokens*; el bloque de datos lista cada pasaje una sola vez y no pasa
   de 6 000 *tokens* (contados con el tokenizador del propio servidor). Si los supera, no se llama al
   juez: el turno queda en «Error» con `turn.error.system`, 0 alertas, y el mensaje pide dividir el
   turno. (Recomendada)
B. El mismo límite, pero en vez de error se envían al juez solo las afirmaciones que caben, en orden, y
   las demás quedan «no documentada» y van al Paquete de Contexto de Traspaso.
C. Ventana de 32 768 *tokens* sin límite propio; un turno demasiado largo terminará por plazo.
X. Other (please specify)

[Answer]: A **Mode:** guided

---

# Segunda pasada — cambio 01, adenda 02 y Functional Design revisión vigente (2026-11-22)

**Unidad.** U4 `text-flow` (MUST, L; Bolt B3). Después del cambio 01, U4 deja de evaluar y pasa a
orquestar (`functional-design/functional-spec.md`, revisión 2). Hace cinco cosas:
- crea la sesión con su consentimiento y su perfil;
- recibe los turnos y encola una corrida incremental por turno TEST (C2);
- corre `AnalysisWorker` en `semantic-agent` sobre la biblioteca de U11 (C17);
- ingiere el resultado (C3), con el registro de modelos, el bloqueo por incidente y las sugerencias por C10;
- muestra todo en M3 y M4, con el aviso de propósito limitado.

La revisión 1 de esta etapa (2026-10-03) es anterior al cambio 01. Sus respuestas P1–P5 y S1–S3 se
revisan aquí por Modify.

## Lo que ya está decidido

No se vuelve a preguntar.

- **Sale de U4** con el cambio 01 (unit-of-work revisión 3; `docs/iteracion2.md` §2.8):
  - el juez, el *prompt*, los *embeddings* y `pgvector`;
  - el umbral, la indexación de escenarios y el Paquete de Contexto de Traspaso.
  Con ellos quedan superadas **P1, P2, P3, S2 y S3**. El modelo y la calidad de la IA (NFR4, NFR5, NFR6)
  pasan a U11, que ya los fijó hoy.
- **De la respuesta P4** salen el p95 de 60 s, el plazo de 300 s y el *N* de 120 s. Los sustituyen:
  - el p95 de `analyze` incremental de U11 (≤ 180 s, NFR3.1 de U11);
  - los topes de C25 que fijó U11: `model_call_timeout_s` = 3600 y `run_deadline_incremental_s` = 1200,
    con 300 y 900 en la máquina de desarrollo;
  - el *N* de la prueba de humo, 300 s (NFR-U11-10), dentro del cual U4 suma su parte de cola,
    ingesta y consola.
- **P5 = A sigue vigente** (sondeo cada 2 s con corridas en curso y cada 15 s sin ellas).
- **S1 = A sigue vigente en su idea**: el plazo de una corrida crece con lo que tiene por delante en la
  cola. Se adapta a las corridas y a los plazos de C25 (ver «Lo que el diseño resolverá sin preguntar»).
- **U1:** `limits.exceeded` es siempre `413`, y C25 no admite nulos (NFR-U1-03, NFR-U1-07).
- **U2:** `semantic-agent` ya no alcanza PostgreSQL. El Job de retención alcanza Redis.
- **U3:** `AccessLog.record` corre en un punto de guardado de 500 ms (NFR-U3-05), y el sondeo con
  `since` no registra acceso (E11 de U13). `ActorSystem` suma `run-supervisor`.
- **U10:** el proxy responde `503` `analysis.anonymizer_unavailable` con más de 4 peticiones
  simultáneas (NFR-U10-08).
- **U11:** verificador local gpt-oss-20b en CPU y permutación activa en todos los perfiles
  (NFR-U11-01, NFR-U11-08). La franja del modo fragmentado muestra lo que diga
  `registro.fragmentado`, no el ejemplo 40/8 de E42 (NFR-U11-13).
- **Functional Design de U4 (aprobado hoy):** una sola cola FIFO (FD-U4-09), un trabajador sin base de
  datos, el bloqueo por incidente, la cancelación con la clave de CD-06, el registro de modelos sin texto
  y la tabla FD-U4-01 a FD-U4-22.
- **Precisiones de otras unidades que recaen en U4:**
  - `EthicsSessionPort`, y el descarte en la ingesta de los resultados de una sesión ya borrada
    (FD-U13-08, FD-U13-13);
  - RunPublicationHold y la cancelación de las corridas en espera (FD-U9-07, FD-U9-08);
  - la tubería que reutilizan el pegado, la importación y el modo final (FD-U6-07, FD-U6-15, FD-U6-19);
  - `discard_correction_round` (FD-U5-04), que no cambia nada de U4.

## Cómo se registra la revisión 2

Igual que en las demás segundas pasadas (regla de `project.md`):
- **IDs.** Los requisitos que siguen conservan su ID; los que salen quedan «Retirado» sin renumerar y
  nombran a su nuevo dueño; lo nuevo toma el número siguiente de su grupo.
- **Estado.** Cada fila dice si **se mantiene**, **cambia**, es **nuevo** o está **Retirado**.
- **Lo que se retira:**
  - NFR3.4 (`pgvector`) y NFR3.11–NFR3.12 (*prompt* del juez);
  - NFR4.1–NFR4.5, NFR5.1–NFR5.2, NFR6.1 y NFR14.2, que pasan a U11;
  - NFR8.1, NFR8.2 y NFR8.4 (servidores del juez, de *embeddings* y del indexador);
  - NFR9.1–NFR9.3 (NFR9 queda «Retirado» en requirements);
  - NFR10.2, NFR10.3, NFR10.6, NFR10.8, NFR10.11 y NFR10.12 (*prompt*, usuario de solo lectura,
    servidores de modelos, carga de escenarios y modelos fijados), que pasan a U11, U2 o salen;
  - las decisiones de pila D1–D8, D10 y D16.
- **Tabla de precisiones.** La tabla de §6 de `security-requirements.md` conserva sus filas de la
  revisión 1 marcadas «Superado» y suma las filas `NFR-U4-01` en adelante.
- **`traceability.json`.** NFR9 pasa a `N/A` con su motivo, y NFR7 sigue en `N/A`.

## Lo que el diseño resolverá sin preguntar

Sale de las fuentes aprobadas. Va como propuesta a la tabla NFR-U4 y puedes objetarlo en la aprobación.

- **Plazo de la corrida (S1 = A, adaptada).** El plazo propio es `run_deadline_incremental_s` o
  `run_deadline_final_s` de la `effective_config` de la sesión.
  - `deadline_at = enqueued_at + plazo propio + suma de los plazos propios de las corridas que están por
    delante en la cola de todo el sistema (en `queued` o `processing`)`.
  - Esa suma tiene un tope: la cifra nueva de C25 `run_queue_wait_max_s` = 10 800 s, que cubre tres modos
    finales por delante.
  - Sin la suma, con la cola FIFO única, una corrida detrás de un modo final de 3600 s vencería sin que
    nada fallara, y NFR8 no llegaría al 98 %.
  - Una corrida en espera (RunPublicationHold, FD-U9-07) no tiene plazo hasta que se libera.
- **Reclamo de mensajes.** El trabajador renueva cada 15 s el reclamo del mensaje que está procesando
  (`XCLAIM … JUSTID`), así que `claim_idle_ms` = 60 000 basta aunque un modo final dure una hora. Además,
  `run_max_deliveries` = 3 y `cancel_key_margin_s` = 120 (un solo nodo de Minikube con NTP). La
  renovación es una precisión a C2.
- **Sondeo.** `poll_interval_s` = 15 (sin corridas en curso) y una cifra nueva,
  `poll_interval_active_s` = 2 (con corridas en curso), como dice P5 = A. Ante un fallo, espera
  creciente hasta 30 s. *T* (`heartbeat_timeout_s`) es de U6.
- **Mensaje de corrida.** `run_message_max_bytes` = 2 097 152, igual que `anonymizer_request_max_bytes`
  de U10, porque C2 y C21 llevan la misma transcripción.
- **Latencia propia de U4** (máquina de desarrollo, cola vacía):
  - desde que el resultado llega a Redis hasta que la sugerencia se ve en M4, ≤ 10 s, dentro de los 300 s
    del humo;
  - `POST /turns` con p95 ≤ 300 ms, también con el trabajador bloqueado;
  - `GET /sessions/{id}?since=` con p95 ≤ 200 ms.
- **Concurrencia.** Una réplica de `semantic-agent` con una corrida a la vez y sin prioridad por modo
  (FD-U4-09): la latencia del único analista del MVP no lo pide. Así el trabajador nunca pasa de 1 de las
  4 peticiones del proxy; si aun así recibe el `503`, la corrida termina en
  `analysis.anonymizer_unavailable` (BR16.7).
- **Prueba de carga de NFR8.**
  - 50 sesiones sintéticas con `comercial-piloto`, en tandas de 3.
  - Cada sesión entra como un bloque pegado (una corrida incremental), se finaliza y corre su modo final.
  - Meta: ≥ 98 %. Solo se intenta si pasa NFR8.2 de U11.
  - Dura unas 7 h, corre a demanda y nunca en la CI.
- **Datos fuera del clúster.** Nada propio: U4 no sale del clúster. Los mensajes C2 y C3 se borran del
  *stream* tras confirmarlos (`XDEL`). Los fallidos llevan solo IDs y `code`.
- **Descartes en la ingesta.** El resultado de una sesión ya borrada se confirma sin filas (FD-U13-13),
  pero un incidente que traiga se registra igual, solo con IDs (FD-U4-11, FD-U4-12).

Queda una decisión de criterio en dos partes. Dos fuentes aprobadas se contradicen, y la cifra decide cuánto
testimonio seudonimizado puede salir del clúster en una sola llamada.

---

## P6 — Tamaño máximo de la transcripción (`transcript_max_chars`)

FR3.7 pide admitir «al menos la entrevista más larga del corpus del piloto **con margen**». Esa entrevista
mide unos 186 000 caracteres (47 294 *tokens* de solo texto en M3 de `docs/validacion-zine/reporte.md`;
NFR-U10-01).

Los NFR de U10 y U11 aprobados hoy usan 186 000 como «el tamaño máximo de C25»:
- U11 en NFR3.2 y NFR3.4;
- U10 en NFR-U10-04, que ata a esta cifra su presupuesto de seudonimización.

Así no queda margen. La cifra la usan:
- el turno guiado de U4 (la entrada de C2 lleva los turnos 1..n);
- el pegado y la importación (U6);
- la CLI (U11).

Una cifra mayor deja pasar más testimonio en una sola llamada al proveedor comercial y obliga a U10 y U11 a
repetir sus comprobaciones con ella.

A. **250 000 caracteres** (≈ 34 % sobre la más larga):
   - U10 y U11 repiten sus comprobaciones con esta cifra en sus PR (NFR-U10-04 (a) y (b); NFR3.2 y
     NFR3.4 de U11);
   - el presupuesto de U10 pide `model_call_timeout_s` ≥ 270 s, y los 300 s de la máquina de desarrollo
     alcanzan.
   (Recomendada)
B. **186 000 caracteres**, como asumieron U10 y U11: no cambia nada, pero contradice el margen de FR3.7, y
   una entrevista un poco más larga que la del piloto se rechaza con `413`.
C. **372 000 caracteres** (el doble):
   - más margen;
   - pide `model_call_timeout_s` ≥ 400 s, así que hay que subir el valor de la máquina de desarrollo y
     repetir la medición de U11.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P7 — Tamaño máximo de un turno (`turn_max_chars`) y número máximo de turnos (`transcript_max_turns`)

La revisión 1 fijó 2 000 caracteres por turno pensando en el juez en CPU, que salió con el cambio 01.
Ahora `turn_max_chars` vale también para cada turno importado y para la CLI (NFR10.1 de U11).

Un turno del piloto puede ser un monólogo largo, y ni el turno más largo ni el número de turnos de la
entrevista más larga están en el repositorio (el corpus está fuera de Git). Una cifra corta impide importar
el piloto; una larga permite un turno escrito enorme en la consola.

A. `turn_max_chars` = **20 000** y `transcript_max_turns` = **2 000**:
   - antes del PR de U1 que las fija, el humano las comprueba fuera de Git sobre las 10 entrevistas del
     piloto con un script revisable que solo imprime dos cifras (turno más largo y número de turnos);
   - si alguna no cabe con un 25 % de margen, se sube por ese PR.
   (Recomendada)
B. `turn_max_chars` = **2 000** (la cifra de la revisión 1) y `transcript_max_turns` = **2 000**: un turno
   importado más largo se rechaza y hay que partirlo a mano.
C. Dos cifras: `turn_max_chars` = 20 000 para la importación y la CLI, y una nueva `typed_turn_max_chars`
   = 2 000 para el turno escrito en M4. Suma una cifra a C25 y una regla más a U4.
X. Other (please specify)

[Answer]: A **Mode:** guided
