# Preguntas de Functional Design — U4 text-flow

**Unidad.** U4 `text-flow` (sin tipo): cargar e indexar un escenario y elegirlo (US1.1, US1.3), crear la
sesión (US2.1), enviar turnos sin bloquear (US2.2), evaluar con la guardia del umbral antes del juez y
sin alertas parciales (US3.1–US3.3, US4.1, US4.3), Paquete de Contexto de Traspaso (US4.2), creación de
sugerencias, escaneo de vocabulario prohibido (US5.5) y base de accesibilidad (US5.6).

**Lo que ya está decidido y no se vuelve a preguntar.** Guardia por afirmación antes del juez (ADR-006,
AC4.1.1–AC4.1.5); «no documentada» del juez se trata como por debajo del umbral; CoT interrumpida
determinista sin LLM; salida estricta C6 y alerta C7; colas C2–C4; cita literal entre «…» y lista de 9
términos (Functional Design de U1); 1 MB, Markdown o texto UTF-8 (FR2.1); 3 pasajes en el paquete
(FR5.3). Quedan los cinco huecos que `requirements.md` §7 y `contract-summary.md` asignaron a esta etapa.

---

## P1 — Regla para dividir un turno en afirmaciones (AC3.1.5)

La regla debe ser determinista y cada afirmación debe ser una subcadena literal del turno. Cada
afirmación se recupera y se califica por separado, así que la regla decide qué se puede alertar.

A. Por oración: cortar tras `.`, `?`, `!` o `…` seguidos de espacio o fin de línea, y en cada salto de
   línea; quitar espacios de los bordes y descartar trozos sin letras. Un turno sin esos signos es una
   sola afirmación. (Recomendada)
B. El turno completo es una sola afirmación.
C. Lo de A más cortes en `;` y en las conjunciones «y», «pero», «aunque» precedidas de coma.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Cómo se segmenta el escenario en pasajes (FR2.2)

Cada pasaje es lo que se cita en una alerta (cita literal) y lo que se compara por similitud con cada
afirmación.

A. Por párrafo (bloques separados por línea vacía) y por encabezado Markdown; un párrafo largo se parte
   en oraciones completas hasta un máximo de caracteres por pasaje, y nunca se parte una oración.
   (Recomendada)
B. Ventanas de tamaño fijo con solapamiento, sin mirar párrafos ni oraciones.
C. Una oración por pasaje.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Qué es el «identificador de documento» que cita la alerta

La alerta exige un ID de documento que pertenezca a la versión de escenario (AC3.1.2), y el PRD pide
enlazar la cita con «el identificador de documento dentro de la base de conocimiento». Un escenario es
un solo archivo, pero puede reunir varias piezas documentales (actas, informes).

A. Cada encabezado de primer nivel con la forma `# [DOC-…] Título` abre un documento con ese ID; si el
   archivo no tiene ninguno, todo el archivo es un documento con ID `DOC-1`. El ID es único dentro de la
   versión o la carga se rechaza. (Recomendada)
B. El ID de documento es siempre el de la versión de escenario (un documento por archivo).
C. El ID de documento es el encabezado Markdown más cercano al pasaje, tal como esté escrito.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Cuántos pasajes se recuperan por afirmación (top_k)

Los pasajes recuperados son lo único que el juez ve y lo único que la CoT puede citar (AC3.1.4); el
paquete muestra 3 (FR5.3). Más pasajes dan más contexto al juez pero alargan el *prompt* en CPU.

A. 3 por afirmación, los mismos que guarda el registro de evaluación y que muestra el paquete.
   (Recomendada)
B. 5 por afirmación al juez; el registro y el paquete guardan los 3 primeros.
C. Configurable entre 3 y 8, con 3 por defecto; el valor queda en la instantánea de la sesión.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P5 — Tamaño máximo de un turno

`contract-summary.md` dejó para esta etapa el tamaño máximo de un turno. Un turno largo es más lento en
CPU y produce más afirmaciones en un solo llamado al juez.

A. 2 000 caracteres; más largo se rechaza con `422` y el mensaje «El turno supera 2 000 caracteres.
   Divídelo en turnos más cortos». (Recomendada)
B. 4 000 caracteres, con el mismo tratamiento.
C. 8 000 caracteres, con el mismo tratamiento.
X. Other (please specify)

[Answer]: A **Mode:** guided
