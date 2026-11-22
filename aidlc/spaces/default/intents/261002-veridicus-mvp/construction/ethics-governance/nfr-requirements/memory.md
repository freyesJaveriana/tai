<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-22T15:13:34Z — Sin preguntas: las preguntas abiertas 1–5 del Functional Design las resuelven U1, U2, U3, U5 y U7; el intervalo de bienestar no tiene cifra del TG en el repositorio, pero es un aviso que no bloquea, así que va como propuesta (2 700 s) a NFR-U13-01.
- 2026-11-22T15:13:34Z — El comando de consulta sigue a verify_store de U7 (kubectl exec, READ ONLY, sin Job ni rol propio), con 1 000 filas por defecto y 10 000 como máximo.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-22T15:13:34Z — Con Redis caído, el Job no borra la sesión (failed, system.unavailable) en vez de borrarla sin cancelar sus corridas: el borrado se retrasa a cambio de que ninguna llamada salga para una sesión ya borrada (NFR-U13-05).
- 2026-11-22T15:13:34Z — Una sola ejecución del Job a la vez con pg_try_advisory_lock y código de salida 3, en vez de confiar en que el humano no lance dos (NFR8.6 de U7, NFR-U13-04).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
