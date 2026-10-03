<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T02:00:43Z — S1 = A se leyó con la cola de todo el sistema (no solo la de la sesión), porque el juez atiende un turno a la vez para todas las sesiones; el tope de 3 600 s limita la capacidad a unos 60 turnos en cola.
- 2026-10-03T02:00:43Z — S3 = A usa turn.error.system para el prompt demasiado largo; para no crear un code nuevo, el mensaje de catálogo de ese code cubre los dos casos (dividir el turno o reintentar).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T02:00:43Z — BR8.2 usa turn.error.timeout para el juez que no responde, pero el enum error_code de C3 no lo incluye; se registró en la tabla de precisiones sin editar contract-summary, junto con count_tokens en C13 y el XDEL de C2/C3.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T02:00:43Z — Búsqueda exacta por versión en vez de un índice HNSW: con unos 1 100 pasajes por versión cumple 100 ms y no pierde pasajes al filtrar por versión, a costa de recorrer toda la versión en cada consulta.
- 2026-10-03T02:00:43Z — Una sola ranura en el servidor del juez y un turno a la vez en semantic-agent: resultados repetibles con semilla fija, a costa de que la prueba de carga de NFR8 dure horas.
- 2026-10-03T02:00:43Z — El bloque de datos del prompt va como JSON en el mensaje user en vez de delimitadores de texto: el testimonio no puede cerrar el bloque, a costa de unos tokens más.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-03T02:00:43Z — Confirmar al construir el Golden Dataset que ninguna transcripción pasa de 15 turnos; si pasa, la prueba de NFR8 con transcripciones pegadas puede vencer plazos.
