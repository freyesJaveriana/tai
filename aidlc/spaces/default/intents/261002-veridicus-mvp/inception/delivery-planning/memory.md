<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T22:21:26Z — «La primera unidad del plan es el flujo de texto» se cumplió con un primer Bolt que agrupa U1 + U3 + U4 (P1 = A); el grafo obliga a construir contratos y acceso antes del flujo, y agruparlos deja al primer Bolt como la única prueba de que la arquitectura funciona de punta a punta.
- 2026-10-02T22:21:26Z — El Golden Dataset y la configuración de GitHub se tratan como tareas previas al primer Bolt, no como Bolts: no pertenecen a ninguna unidad del grafo aprobado y no cambian el orden de unidades.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T22:21:26Z — Se precisa la regla «cada Bolt queda como un commit en main» como «cada PR queda como un commit»: un Bolt de varias unidades entra por varios PR cortos (≤ 2 días), y los contratos por PR propio (P9 = A, contradicción entre P1 y team-practices).
- 2026-10-02T22:35:02Z — En el cierre, al revisar el aprendizaje que contradecía `org.md`, el autor decidió «un solo commit por Bolt; la unidad es lo suficientemente precisa»: un Bolt por unidad (P1 y P9 pasan a B). El flujo de texto se reparte en B1 contratos, B2 acceso y B3 flujo de texto; el plan queda en 9 Bolts más el anonimizador condicional.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T22:21:26Z — Sin WSJF formal (P4 = A): el orden ya lo fijan la regla del flujo de texto, el grafo, la demo de la sustentación y los módulos 6–8; una tabla de puntos añadiría precisión falsa.
- 2026-10-02T22:21:26Z — Plataforma como segundo Bolt (P2 = A) en vez de dentro del primero: mantiene el primer Bolt probándose en contenedores (niveles 0–2) y alinea el despliegue y la NetworkPolicy con los módulos 6–7; las partes SHOULD/COULD de U2 quedan como sus últimas tareas para el módulo 8.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T22:21:26Z — U10 (anonimizador) queda fuera del plan hasta que se decida usar un modelo externo; si se decide, entra como Bolt condicional al final y exige revisar AUTONOMIA-04.
- 2026-10-02T22:21:26Z — El comando de verificación de Construction se difiere: este trabajo no escribe código y no existe todavía un comando ejecutable.
