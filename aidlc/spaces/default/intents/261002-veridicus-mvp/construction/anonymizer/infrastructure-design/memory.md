<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:01:37Z — P1 = A se aplicó como un Corefile versionado en deploy/cluster/coredns.yaml con zonas cluster.local, github.com y, solo con el proxy habilitado, exactamente upstreamHost; el resto responde NXDOMAIN y check-coredns.sh detecta la deriva que Minikube introduce al arrancar.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:01:37Z — Un rango publicado más ancho que /24 se parte en sus /24 en upstreamCidrs en lugar de relajar la política de NFR Design; solo se renderizan CIDR IPv4 porque el clúster Calico es IPv4. Quedó en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:01:37Z — Los volcados de memoria se desactivan en el proceso (RLIMIT_CORE = 0 y no volcable) y no en el kernel de la anfitriona: no toca un ajuste compartido, a costa de depender de que el arranque lo haga antes de cargar nada (prueba de nivel 0).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
