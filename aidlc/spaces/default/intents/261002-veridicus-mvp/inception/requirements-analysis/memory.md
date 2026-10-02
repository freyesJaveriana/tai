<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T18:39:18Z — `pvb.md` sin ruta se leyó como el archivo de la raíz del proyecto (idéntico a `docs/pvb.md`); el PRD manda sobre el PVB según su propia nota H6 y `docs/coherencia-insumos.md`.
- 2026-10-02T18:39:18Z — La calificación de la IA se limita a «congruente / incongruente / no documentada» (corrección de Practices Discovery); solo «incongruente» por encima del umbral produce alerta.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T18:39:18Z — Las decisiones ya aplicadas en el PRD (19 hallazgos de coherencia) no se volvieron a preguntar; se hicieron 8 preguntas más 1 de seguimiento sobre lo que faltaba para criterios medibles.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T18:39:18Z — Los requisitos se trazan al PRD por segmento en lugar de a artefactos de Ideation, porque el scope `classic` omite Ideation; el origen queda documentado en cada requisito.
- 2026-10-02T18:39:18Z — Las métricas de adopción (uso semanal, desestimación en producción) quedan como hipótesis fuera de los criterios de aceptación; medirlas exigiría usuarios reales que el MVP no tiene.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T18:39:18Z — Valores que fija NFR Requirements: umbral de similitud, modelo exacto del juez y de embeddings, N segundos de la prueba de humo y latencia por turno de texto en CPU.
