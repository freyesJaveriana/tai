<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T10:41:31Z — P1 («la máquina demo tiene 32 gb… deja 4 gb al sistema») se aplicó como Minikube de 28 GiB en la máquina de demostración, y P2 = A extendió la misma regla a la de desarrollo (20 GiB); los límites con ≥ 20 % de margen quedaron como valores de U4 y precisan los de U2.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T10:41:31Z — El archivo del prompt vive en el chart (charts/semantic-agent/files/) porque Helm no lee fuera del chart; las pruebas de semantic-agent lo leen desde ahí para no tener dos copias.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T10:41:31Z — La evaluación de nivel 2 corre desde la anfitriona con kubectl port-forward al juez del clúster en vez de un Job: usa el mismo modelo y digest sin otra imagen, a cambio de depender de un script revisable que el humano ejecuta.
- 2026-10-03T10:41:31Z — El juez pide 3 CPU y limita en 6: la suma de requests cabe en 10 CPU y el juez sigue usando sus 6 hilos cuando el resto está quieto.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
