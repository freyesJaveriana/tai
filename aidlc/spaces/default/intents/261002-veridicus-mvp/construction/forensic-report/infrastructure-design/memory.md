<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:51:00Z — El aprovisionador hostPath de Minikube ignora fsGroup y no publica kubelet_volume_stats: VERIDICUS_REPORTS_DIR pasa a ser un subdirectorio reports/ 0700 que crea el proceso, y el llenado se mide con la cuota propia de P3 = A.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:51:00Z — El PVC queda en 2 GiB (reserva de U2) en lugar del 1 GiB de NFR8.5, y la API pasa a Recreate frente al RollingUpdate de U2/U3/U5/U6; ambas quedaron en la tabla de precisiones sin editar los originales.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:51:00Z — verify_store usa un rol nuevo veridicus_report_ro de solo SELECT (un Secret más) en vez de reutilizar veridicus_app, por mínimo privilegio; el respaldo usa export_store en Python para no exigir tar en la imagen mínima.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
