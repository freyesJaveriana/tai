# Preguntas de Functional Design — U1 contracts

**Unidad.** U1 `contracts` (tipo `spec`): contratos versionados en `contracts/` y sus pruebas de
validación con *fixtures*; ningún comportamiento (`unit-of-work.md`). Respalda AC2.2.3, US3.2
(AC3.2.1, AC3.2.4), AC5.5.3, AC5.5.4 y AC8.3.1 (`unit-of-work-story-map.md`, `bolt-plan.md` B1).

**Lo que ya está decidido y no se vuelve a preguntar.** Las formas de C1–C16, la versión semántica por
contrato con `schema_version` en cada mensaje, `additionalProperties: false` en C6 y C7, el enum de
tres calificaciones, los cuatro campos obligatorios de la alerta, el catálogo único de `code`, la
ausencia de rutas que escriban el umbral y los datos solo sintéticos (`contract-summary.md`,
`requirements.md`, `stories.md`, team-practices). Solo quedan los cuatro huecos de abajo.

---

## P1 — Cómo reconoce el escaneo una cita literal dentro de la CoT

La lista de vocabulario prohibido (C8) excluye las citas literales del testimonio y del escenario
(AC5.5.1, AC5.5.2), pero la CoT es texto libre y la regla de que una CoT con vocabulario prohibido
fuera de las citas es salida inválida (AC3.2.4) necesita saber dónde empieza y termina una cita. Esto
fija la regla del contrato C8 (y, en la opción C, la forma de C6).

A. Una cita es el texto entre comillas angulares «…», y solo cuenta como cita si aparece **literal** en
   el fragmento del turno o en uno de los pasajes recuperados; si no aparece, se escanea como texto
   normal (así «miente» entre comillas inventadas no pasa). (Recomendada)
B. Todo texto entre «…» o "…" se excluye del escaneo, sin comprobar que sea literal.
C. Cambiar C6: la CoT no puede llevar citas; las citas van solo en campos separados del juez y la CoT
   se escanea completa.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P2 — Lista inicial de vocabulario prohibido

La lista aprobada de C8 tiene 9 términos (mentiroso, mentirosa, miente, mintió, falso, falsa,
verdadero, verdadera, engaño). Como el escaneo es por palabra completa, una flexión que no esté en la
lista no se detecta (por ejemplo «mienten» o «falsedad»). La lista es la base de la prueba guardia de
AUTONOMIA-03.

A. Dejar los 9 términos y ampliarlos después, cada uno con su PR.
B. Ampliar desde la versión 1.0.0 con flexiones y derivados directos: mienten, mintieron, mentir,
   mintiendo, mentira, mentiras, mentirosos, mentirosas, falsos, falsas, falsedad, verdaderos,
   verdaderas, veraz, engaña, engañó, engaños, engañoso, engañosa. (Recomendada)
C. Lo de B más términos de credibilidad sobre la persona: creíble, increíble, fiable, sincero, sincera.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P3 — Rótulos de resultado visibles en la consola (AC5.5.4)

AC5.5.4 exige que los únicos rótulos de resultado en pantalla sean «Sugerencia de revisión»,
«Incongruencia semántica» y «Hecho No Documentado», y se prueba en nivel 0 en esta unidad.

A. U1 publica un contrato pequeño que asocia cada calificación y tipo de resultado con su rótulo
   visible; la consola lo importa y la prueba de U1 comprueba que solo existen esos tres rótulos.
   (Recomendada)
B. U1 solo fija el enum de calificación; la prueba de los rótulos en pantalla la hace U4 en la consola.
X. Other (please specify)

[Answer]: A **Mode:** guided

## P4 — Formato de fecha compartido

C1 usa ISO 8601 en UTC (ejemplo `2026-10-02T21:40:00Z`) y la consola muestra hora de Colombia. Falta
fijar la precisión y si se aceptan desfases, porque la misma regla valida los mensajes de las colas,
las respuestas de la API y el reporte con su SHA-256.

A. RFC 3339 en UTC con `Z`, precisión de segundos, sin fracciones ni desfases
   (`2026-10-02T21:40:00Z`); cualquier otra forma se rechaza. (Recomendada)
B. RFC 3339 en UTC con `Z` y milisegundos opcionales (`2026-10-02T21:40:00.123Z`).
C. RFC 3339 con cualquier desfase horario (`-05:00` incluido); el consumidor normaliza a UTC.
X. Other (please specify)

[Answer]: A **Mode:** guided
