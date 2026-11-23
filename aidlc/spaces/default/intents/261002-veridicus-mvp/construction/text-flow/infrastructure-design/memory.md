<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T10:41:31Z — P1 («la máquina demo tiene 32 gb… deja 4 gb al sistema») se aplicó como Minikube de 28 GiB en la máquina de demostración, y P2 = A extendió la misma regla a la de desarrollo (20 GiB); los límites con ≥ 20 % de margen quedaron como valores de U4 y precisan los de U2.
- 2026-11-23T01:10:01Z — Segunda pasada sin preguntas: U4 adopta los recursos que ya fijó U2 para el trabajador y semantic-agent (caben con el /tmp en memoria de 16 MiB) y solo pide a U2 lo que falta, sin darlo por aplicado (IDS-U4-01, -02, -03, -07, -10, -14).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T10:41:31Z — El archivo del prompt vive en el chart (charts/semantic-agent/files/) porque Helm no lee fuera del chart; las pruebas de semantic-agent lo leen desde ahí para no tener dos copias.
- 2026-11-23T01:10:01Z — semantic-agent y el trabajador van con Recreate en vez del RollingUpdate de U2 §5: con maxSurge 1 convivirían dos consumidores de C2 (contra NFR8.7) y el trabajador abriría 8 conexiones; cierra R-01 de la revisión 1.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T10:41:31Z — La evaluación de nivel 2 corre desde la anfitriona con kubectl port-forward al juez del clúster en vez de un Job: usa el mismo modelo y digest sin otra imagen, a cambio de depender de un script revisable que el humano ejecuta.
- 2026-10-03T10:41:31Z — El juez pide 3 CPU y limita en 6: la suma de requests cabe en 10 CPU y el juez sigue usando sus 6 hilos cuando el resto está quieto.
- 2026-11-23T01:10:01Z — Con el cuarto hilo del trabajador el pico de veridicus_app iguala el connectionLimit de 25 (API 20 en rodadura, trabajador 4, create-admin 1); se pide 30 a U2 en vez de bajar el pool de la API de U3, a costa de 5 conexiones más dentro de max_connections 50.
- 2026-11-23T01:10:01Z — Un despliegue de semantic-agent a mitad de corrida reenvía el mismo cuerpo seudonimizado dentro del tope de 3 entregas; se acepta con un paso del runbook (desplegar sin corridas en processing) en vez de un periodo de gracia de horas.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
