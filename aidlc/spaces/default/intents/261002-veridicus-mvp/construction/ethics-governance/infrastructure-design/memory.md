<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-23T01:56:42Z — «La forma exacta de los dos manifiestos» que U13 dejó a esta etapa se fijó como dos plantillas de `deploy/jobs/` con el mismo pod; `--as-of` solo en la de simulación, para que un valor mal pasado nunca convierta una simulación en un borrado (IDS-U13-01).
- 2026-11-23T01:56:42Z — El `Job` lee el `ConfigMap` de la API con `configMapKeyRef` clave por clave y no con `envFrom`: así una clave que falte impide arrancar y la comprobación de IDS-U5-02 la ve en el render (IDS-U13-03).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-23T01:56:42Z — Sin alerta para el `Job`: lo lanza el humano y lee su salida al terminar; una regla sobre `kube_job_status_failed` avisaría a la misma persona más tarde y sin la causa.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
