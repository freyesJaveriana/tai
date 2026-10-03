# Preguntas de Functional Design — U6 session-lifecycle

**Unidad.** U6 `session-lifecycle` (tipo `service`): versión nueva de un escenario (US1.2), pegar una
transcripción (US2.3), lista de sesiones (US2.5), suspensión y reanudación (US7.1), progreso (US10.1,
SHOULD) e historial lateral (US11.2, COULD).

**Lo que ya está decidido y no se vuelve a preguntar.** Versión nueva con SHA-256 propio e inmutable
(FR2.4, AC1.2.1–AC1.2.4); la suspensión por falta de latido con *T* de NFR Requirements y el sondeo como
latido (contract-design P6); el diálogo de reanudación (AC7.1.2); los turnos pegados siguen el mismo
camino que los enviados uno a uno, con tope de 2 000 caracteres por turno (Functional Design de U4,
P5). Quedan los tres huecos que `requirements.md` §7 y `contract-summary.md` asignaron a esta etapa.

---

## P1 — Formato de la marca de hablante

Una transcripción se divide en turnos por línea vacía o por marca de hablante (FR3.3), y
`requirements.md` dejó a esta etapa el formato exacto de la marca (un prefijo de línea del tipo
`Nombre:`).

A. Una línea que empieza por 1 a 30 caracteres sin dígitos ni `:` seguidos de `:` y espacio (p. ej.
   «Compareciente: », «Analista: ») abre un turno nuevo; la marca se guarda aparte como hablante y no
   entra en el texto del turno. (Recomendada)
B. Solo cuentan como marca las etiquetas de una lista fija («Compareciente:», «Analista:»,
   «Entrevistador:»).
C. La marca abre un turno nuevo pero se conserva dentro del texto del turno.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Qué pasa con las líneas del entrevistador

Una transcripción real alterna preguntas del analista y respuestas del compareciente. Si todo se evalúa,
las preguntas del analista se contrastan con el marco de verdad como si fueran testimonio.

A. Los turnos cuyo hablante es el entrevistador (marca de una lista configurable, por defecto
   «Analista» y «Entrevistador») se guardan como contexto, no se evalúan y sí cuentan como turnos
   previos del paquete; los demás se evalúan. (Recomendada)
B. Todos los turnos se evalúan, sin importar el hablante.
C. Los turnos del entrevistador se descartan: no se guardan.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Tamaño máximo de una transcripción pegada

`contract-summary.md` dejó a esta etapa el tamaño máximo de una transcripción pegada. Todos sus turnos
entran a la cola a la vez, y cada uno respeta el tope de 2 000 caracteres.

A. Hasta 100 turnos y 100 000 caracteres; un turno de más de 2 000 caracteres se marca en la vista
   previa e impide confirmar hasta corregirlo. (Recomendada)
B. Hasta 50 turnos y 50 000 caracteres, con el mismo tratamiento.
C. Sin tope de turnos; solo los 2 000 caracteres por turno.
X. Other (please specify)

[Answer]: A **Mode:** guided
