<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-11-23T00:57:53Z — «Reporte adjunto al PR» se lee como un par versionado (C19 v2 y una evidencia con el commit evaluado) en evaluation/reports/level2/, porque C19 no tiene campo de commit y la CI no puede leer adjuntos (IDS-U11-04).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-23T00:57:53Z — U11 es library: solo cicd-pipeline.md y traceability.json (produces_kinds), aunque el brief nombraba los cuatro artefactos; máquina de la CLI, ZINE y frontera van en §5–§7 (IDS-U11-01).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-11-23T00:57:53Z — La wheelhouse de ZINE va sin el extra cli (sin torch ni libs-anonymizer) a cambio de que composition importe el anonimizador de forma diferida y un perfil comercial sin él dé código 3 (IDS-U11-02).
- 2026-11-23T00:57:53Z — El verificador del nivel 2 en la anfitriona reutiliza la imagen de llama-server de U2 por digest solo en loopback; conserva la salida de la red puente de Docker, riesgo residual igual al de la propia CLI (IDS-U11-05).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
