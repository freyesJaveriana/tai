<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T18:39:18Z — `pvb.md` sin ruta se leyó como el archivo de la raíz del proyecto (idéntico a `docs/pvb.md`); el PRD manda sobre el PVB según su propia nota H6 y `docs/coherencia-insumos.md`.
- 2026-10-02T18:39:18Z — La calificación de la IA se limita a «congruente / incongruente / no documentada» (corrección de Practices Discovery); solo «incongruente» por encima del umbral produce alerta.
- 2026-10-30T23:54:17Z — Segunda pasada por el cambio 01: se eligió «Modify» y se conservaron los ID de los requisitos que siguen; los que salen quedan como «retirado» en la tabla de trazabilidad en vez de renumerar, para no romper las referencias de las etapas siguientes.
- 2026-10-30T23:54:17Z — El contrato común v0.1 del cambio 01 (fuera del repositorio) se tomó como fuente de los campos del hallazgo y de la corrida; su texto exacto lo fija Contract Design al copiarlo al repositorio.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T18:39:18Z — Las decisiones ya aplicadas en el PRD (19 hallazgos de coherencia) no se volvieron a preguntar; se hicieron 8 preguntas más 1 de seguimiento sobre lo que faltaba para criterios medibles.
- 2026-10-30T23:54:17Z — No se volvieron a preguntar las 18 decisiones de `docs/iteracion2.md` (P1–P18); solo 8 preguntas nuevas sobre lo que faltaba para criterios medibles (verificador, regla de cita, fragmentos, familias, tamaño, acierto, anonimizador, costo).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T18:39:18Z — Los requisitos se trazan al PRD por segmento en lugar de a artefactos de Ideation, porque el scope `classic` omite Ideation; el origen queda documentado en cada requisito.
- 2026-10-02T18:39:18Z — Las métricas de adopción (uso semanal, desestimación en producción) quedan como hipótesis fuera de los criterios de aceptación; medirlas exigiría usuarios reales que el MVP no tiene.
- 2026-10-30T23:54:17Z — La regla de cita literal es la del piloto (solo espacios, « […] », aviso en turnos ENT o plegados) para que Veridicus y el TG se comporten igual, a costa de admitir citas del entrevistador con aviso.
- 2026-10-30T23:54:17Z — Con modelos locales, solo contradicciones dentro de cada ventana con solapamiento: limitación declarada y medida por distancia entre citas, en vez de inventar una segunda pasada que el TG no ha decidido.
- 2026-10-30T23:54:17Z — Juez y verificador de la misma familia solo en un perfil de demostración que lo declare, con aviso visible: deja correr `todo-local` en 20 GiB sin romper la regla en la evaluación.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T18:39:18Z — Valores que fija NFR Requirements: umbral de similitud, modelo exacto del juez y de embeddings, N segundos de la prueba de humo y latencia por turno de texto en CPU.
- 2026-10-30T23:54:17Z — NFR Requirements fija: umbrales de precisión, sensibilidad y acuerdo entre 3 corridas; composición del conjunto sintético; tamaño de ventana y solapamiento; nuevos límites de tamaño; latencias (C3).

