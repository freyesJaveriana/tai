<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:19:51Z — P1 = A se leyó con «alertas elegibles»: decididas, o pendientes que el analista dejó atrás (ignoradas, FR9.3); las pendientes al final de la bandeja no cuentan, para que la razón no suba sola mientras llegan alertas nuevas.
- 2026-10-03T02:19:51Z — La nota y la reformulación del analista son texto humano: no se censuran y el escaneo de vocabulario de nivel 3 las trata como citas literales; AUTONOMIA-03 prohíbe etiquetas automáticas, no el criterio del analista.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:19:51Z — C1 lista solo 201 y 409 para las decisiones aunque rules.md usa 422 y 403, C11 no permite bloquear la ronda al leerla y C15 no fija W; se registraron en la tabla de precisiones de security-requirements.md sin editar contract-summary.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:19:51Z — Bloqueo de la fila de la ronda (FOR UPDATE) en vez de SERIALIZABLE: serializa las decisiones de una sesión sin reintentar operaciones que no son idempotentes, a costa de que U7 deba tomar el mismo bloqueo al consolidar.
- 2026-10-03T02:19:51Z — La razón AIR se calcula al decidir y vive en memoria del proceso: /metrics no depende de la base, a costa de tener que cambiarlo si session-api pasa a varias réplicas.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
