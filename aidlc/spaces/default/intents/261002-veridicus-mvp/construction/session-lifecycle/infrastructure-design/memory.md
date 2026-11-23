<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T11:00:11Z — U6 no añade procesos ni reglas de red; lo propio son tres ajustes en el bloque común de los values, un cuarto hilo del trabajador y una migración aditiva.
- 2026-11-23T01:27:06Z — Segunda pasada sin preguntas: U6 no cambia ninguna cifra de pod; con sus +100 MiB la API queda en ≈ 826 MiB frente a 1,125 GiB, aun con tres consolidaciones de U7 a la vez.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T11:00:11Z — veridicus_now() del clúster devuelve solo now(); la variante con hora inyectada la instala el fixture de nivel 1, para que ningún rol pueda adelantar la suspensión (precisión a D3).
- 2026-11-23T01:27:06Z — El plazo de inactividad de la revisión 1 («5 s» sin alcance en veridicus-pg) pasa a SET LOCAL por transacción en shared/db.py, que acepta idle_timeout_s para U7 (NFRD-U7-01, NFRD-U7-03; IDS-U6-02).

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T11:00:11Z — Tras minikube stop o la API caída > 180 s las sesiones abiertas se suspenden en la primera revisión; se acepta porque reanudar es un clic sin pérdida, en vez de complicar la revisión.
- 2026-11-23T01:27:06Z — El tope del Ingress iguala import_body_max_bytes, así que un cuerpo mayor recibe el 413 de nginx sin Problem Details; se acepta porque la consola nunca lo envía y el 413 de la API se prueba en nivel 1 (IDS-U6-09).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
