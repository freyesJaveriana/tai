<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T10:20:04Z — U3 fija la forma del despliegue de session-api (réplica, sondas, base de recursos) porque es el primer Bolt que lo construye; U4–U7 solo añaden configuración, salida de red y memoria.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T10:20:04Z — P1 = B cambia C16 y NFR10.13 aprobados (la sonda de Kubernetes usa /readyz?probe=kubernetes sin Redis); quedó en la tabla de precisiones sin editar los originales.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T10:20:04Z — VERIDICUS_TRUSTED_PROXY toma todo el pod CIDR porque solo ingress-nginx alcanza el puerto 8080; detrás de Minikube todos los navegadores comparten dirección, así que el contador por dirección es común (aceptable con un analista en la sustentación).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
