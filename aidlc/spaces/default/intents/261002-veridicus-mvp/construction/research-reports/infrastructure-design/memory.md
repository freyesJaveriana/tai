<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-23T01:26:02Z — La memoria de la API que fijó U2 (1 152 MiB = 1,2 × 944) no incluye las subidas de U12: con dos subidas no cabe ni sin margen (1 404 MiB); se pide a U2 1 792 MiB (IDS-U12-01), sin tocar `requests`.
- 2026-11-23T01:26:02Z — NFR-U12-06 deja abierto imagen o ConfigMap: perfiles y precios desde `veridicus-profiles` (lo mismo que corre `semantic-agent`) y etiquetas en la imagen, para no ampliar `check-no-data.sh` (IDS-U12-03).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-23T01:26:02Z — Los `limits` de Minikube suben a ≈ 52,4 GiB (2,4 GiB sobre 50) a cambio de no subir `requests` por un pico raro; se apoya en el sobrecompromiso que U2 ya aceptó y en sus recortes.
- 2026-11-23T01:26:02Z — T3 fija `idle_in_transaction_session_timeout` de 5 s con `SET LOCAL` (respuesta a la nota NFRD-U7-02): no tiene huecos sin sentencias, así que no corta escrituras legítimas (IDS-U12-06).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
