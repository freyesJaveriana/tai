<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-03T10:20:04Z — P3 («una cifra intermedia, como 24 gb», partición Ubuntu con Docker) se leyó como Ubuntu nativo con 24 GB; con P5 = B se dieron 18 GiB y 10 CPU a Minikube y 6 GiB al sistema.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

- 2026-10-03T10:20:04Z — Pod Security restricted prohíbe hostPath en el pod, así que los modelos se montan con un PersistentVolume estático de solo lectura y su PVC; se añadió un rol veridicus_owner para que el REVOKE de las tablas de historial sea efectivo; ambos quedaron en la tabla de precisiones.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-03T10:20:04Z — La suma de los limits (≈ 19 GiB) supera los 18 GiB de Minikube y la de los requests (≈ 13,7 GiB) cabe; se aceptó porque solo el juez se acerca a su pico, y el primer recorte ante presión es apagar el monitoreo durante NFR8.
- 2026-10-03T10:20:04Z — Sin Alertmanager, Loki ni redis_exporter: el MVP no notifica a nadie y cada pieza cuesta memoria en una sola máquina; las alertas se ven en el panel.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

- 2026-10-03T10:20:04Z — La memoria de GPU de la máquina GPU no se conoce; values-gpu.yaml asume que el juez de 7B cabe entero (≥ 6 GiB de VRAM) y U4 la confirma al elegir modelos más grandes para la evaluación.
