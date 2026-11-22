<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:52:08Z — Una afirmación cuyas dos lecturas no coinciden queda «no documentada» y va al paquete (P2 = A), así el analista ve la discrepancia en vez de perderla.
- 2026-11-22T03:19:24Z — Segunda pasada. La lógica de la permutación ya es de U11 (F4, BR6.1–BR6.3, FD-U11-06), así que U8 solo decide su valor en los perfiles que no son de evaluación y la prueba por el camino del producto. La aclaración neutra (US10.3) es lo único que se diseña de nuevo: biblioteca, ingesta, ConductorObservation y consola. La pregunta por pasajes, la segunda lectura del juez y el indicio afectivo quedan «Retirado» sin renumerar. Solo se preguntan P4 (origen del tema), P5 (permutación fuera de evaluación) y P6 (aclaración en el reporte).

- 2026-11-22T03:44:00Z — AC10.3.4 «se registra como descartada» se leyó como evento de log con run_id, id del hallazgo y regla (no una fila), y «cita de cualquier turno» como la regla cites_turn de C8 más las citas de la salida; quedó como FD-U8-06 para decidir.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:52:08Z — El chequeo de trazabilidad pidió cubrir US5.5 y US5.6 porque el mapa de historias las cruza con U8; se añadieron BR4.1–BR4.4.
- 2026-11-22T03:44:00Z — Además de lo previsto en las preguntas, entraron BR4.5–BR4.7 (AC5.5.4, AC5.6.4 y AC5.6.5, nuevos o sin regla tras retirar BR4.3) y se retiró también AffectiveNote, que la lista de retiros no nombraba pero sale con US11.1.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:52:08Z — El indicio afectivo usa una lista versionada sin LLM (P3 = A): determinista y auditable, a costa de no captar emociones expresadas sin palabras clave.
- 2026-11-22T03:44:00Z — BR5.5 compara el tema con las citas de todos los hallazgos de la salida y no solo con el de origen: la biblioteca y la ingesta aplican la misma regla, a costa de quitar algunas aclaraciones más.
- 2026-11-22T03:44:00Z — La llegada de aclaraciones se anuncia como contador agregado y no una por una (FD-U8-10), para cumplir AC5.6.5 sin perder el anuncio del punto 8.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:52:08Z — El efecto de la segunda lectura sobre la latencia y NFR8 lo mide NFR Requirements.
- 2026-11-22T03:44:00Z — Para NFR Requirements: el costo de verifier_permuted en todo-local frente a NFR3 y NFR8, la tasa aceptable de aclaraciones descartadas por regla y si hace falta un tope de aclaraciones o de largo del tema en C25.
