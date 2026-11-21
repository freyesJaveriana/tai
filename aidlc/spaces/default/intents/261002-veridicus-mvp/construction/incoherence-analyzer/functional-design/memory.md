<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-21T23:42:00Z — Alcance de U11 leído como la biblioteca completa del analizador (núcleo C17, ModelGateway con adaptador local y cliente HTTP de C21, ExecutionProfiles, escáner y aviso de IntegrityPolicy), la CLI con `analyze` y `evaluate`, el conjunto sintético con su manifiesto y los `.sbatch` de ZINE. Quedan fuera las colas y sesiones (U4), la seudonimización y los adaptadores nativos (U10) y las aclaraciones neutras (U8). Solo se preguntan 8 decisiones de criterio que las fuentes no fijan o en las que se contradicen: orden de filtros, contexto del verificador, vocabulario prohibido (AC3.2.4 frente al motivo de C6), permutación en B11 frente a US10.5 en U8, alterno y familias, métricas de las 3 corridas, etiquetas de sesgo frente a `bias_table` de C19, y aviso de VE-01 en la CLI.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
