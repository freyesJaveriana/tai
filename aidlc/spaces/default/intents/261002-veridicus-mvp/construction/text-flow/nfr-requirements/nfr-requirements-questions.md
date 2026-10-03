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
