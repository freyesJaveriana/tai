<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:01:37Z — P1 = A se aplicó como un Corefile versionado en deploy/cluster/coredns.yaml con zonas cluster.local, github.com y, solo con el proxy habilitado, exactamente upstreamHost; el resto responde NXDOMAIN y check-coredns.sh detecta la deriva que Minikube introduce al arrancar.
- 2026-11-23T00:47:00Z — Segunda pasada sin preguntas: la red, CoreDNS, el Secret, el endurecimiento y los requests/limits pasan a U2, así que U10 solo fija lo que necesita del pod y del anfitrión de la CLI y lo propone a U2 (IDS-U10-02 a IDS-U10-06); máquina supuesta de 64 GB solo CPU.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:01:37Z — Un rango publicado más ancho que /24 se parte en sus /24 en upstreamCidrs en lugar de relajar la política de NFR Design; solo se renderizan CIDR IPv4 porque el clúster Calico es IPv4. Quedó en la tabla de precisiones.
- 2026-11-23T00:47:00Z — El mamparo de 4 se limita a POST /v1/generate (IDS-U10-04), porque con 4 llamadas en curso una sonda sin cupo haría que la livenessProbe reiniciara el pod a mitad de una llamada.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:01:37Z — Los volcados de memoria se desactivan en el proceso (RLIMIT_CORE = 0 y no volcable) y no en el kernel de la anfitriona: no toca un ajuste compartido, a costa de depender de que el arranque lo haga antes de cargar nada (prueba de nivel 0).
- 2026-11-23T00:47:00Z — La prueba de 0 fugas con el NER real corre en la CI con el NER aprovisionado y verificado por sha256 antes de las pruebas (IDS-U10-07), y el rendimiento se mide en la máquina de desarrollo con una puerta que exige el reporte, porque los runners no son comparables.
- 2026-11-23T00:47:00Z — El modelo NER no se fija por nombre y hash en esta etapa sino por criterios y orden de candidatos (IDS-U10-01); su revisión y sha256 se fijan en B10 con la prueba de 0 fugas como compuerta.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
