<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:51:00Z — El aprovisionador hostPath de Minikube ignora fsGroup y no publica kubelet_volume_stats: VERIDICUS_REPORTS_DIR pasa a ser un subdirectorio reports/ 0700 que crea el proceso, y el llenado se mide con la cuota propia de P3 = A.
- 2026-11-23T01:41:06Z — U2 revisión 2 dejó la API en RollingUpdate, pero NFR8.6 y P1 = A siguen pidiendo Recreate: no es una contradicción nueva (la resolvió el humano en la revisión 1), así que va como petición a U2 (IDS-U7-03) sin pregunta.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:51:00Z — El PVC queda en 2 GiB (reserva de U2) en lugar del 1 GiB de NFR8.5, y la API pasa a Recreate frente al RollingUpdate de U2/U3/U5/U6; ambas quedaron en la tabla de precisiones sin editar los originales.
- 2026-11-23T01:41:06Z — export_store sale de backup-db.sh y pasa al runbook, justo después del volcado, porque la lista cerrada de exec de U2 solo admite pg_dump, la consulta de U13 y verify_store; se conservan el orden base → volumen y el SHA256SUMS de P2 = A (IDS-U7-07).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:51:00Z — verify_store usa un rol nuevo veridicus_report_ro de solo SELECT (un Secret más) en vez de reutilizar veridicus_app, por mínimo privilegio; el respaldo usa export_store en Python para no exigir tar en la imagen mínima.
- 2026-11-23T01:41:06Z — El corte de Recreate se mide desde fuera con scripts/measure-cutover.sh (solo HTTP, umbral ≤ 90 s, contando la descarga de capas) en vez de con kubectl rollout status, que check-no-cluster-apply.sh prohíbe en scripts (IDS-U7-11).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
