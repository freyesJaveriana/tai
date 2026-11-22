<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:28:41Z — El Paquete de Contexto de Traspaso es uno por intento de turno (C3 trae un solo handoff_package): su fragmento es el texto del turno, con la lista de afirmaciones no documentadas y los 3 pasajes distintos más cercanos de esas afirmaciones.
- 2026-11-22T01:48:15Z — Segunda pasada (Modify por cambio 01, adenda 02 y revisiones 3): U4 deja de evaluar y pasa a orquestar. Conserva sesión, turnos, colas C2/C3, ingesta, creación de sugerencias por C10, escaneo de salida e interfaz con el escáner de U11, consola base y axe, y suma consentimiento, perfil, AnalysisWorker sobre C17, corridas con su registro de modelos, bloqueo por incidente e import-linter de semantic-agent. Lo que fijan C1–C3, C10, C17, C21, CD-01/06/11, U1 F3, FD-U3-04/08/10/13 y FD-U10-03/16 no se pregunta; solo quedan seis decisiones de criterio (P6–P11): efecto de anonimizador_no_disponible (UG-02), alcance y fin del bloqueo, incidente fuera de su sesión, quién marca processing, corrida de los turnos ENT y tramos cubiertos por el modo final.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:28:41Z — El escáner de vocabulario prohibido se asignó a U4 en libs/integrity_policy con la firma scan(text, literal_sources), resolviendo el hallazgo R-01 de la revisión de U1 desde esta unidad y dejándolo en la tabla de precisiones para el humano.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:28:41Z — Un solo llamado al juez por turno con solo las afirmaciones que pasan la guardia, en vez de uno por afirmación: menos latencia en CPU y coherente con el arreglo claims de C6, a cambio de que una afirmación mal formada invalide el turno entero (que es lo que pide FR4.2).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:28:41Z — Máximo de caracteres por pasaje, dimensión del vector, intervalo de sondeo y plazo por turno quedan para NFR Requirements.
