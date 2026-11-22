<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:28:41Z — El Paquete de Contexto de Traspaso es uno por intento de turno (C3 trae un solo handoff_package): su fragmento es el texto del turno, con la lista de afirmaciones no documentadas y los 3 pasajes distintos más cercanos de esas afirmaciones.
- 2026-11-22T01:48:15Z — Segunda pasada (Modify por cambio 01, adenda 02 y revisiones 3): U4 deja de evaluar y pasa a orquestar. Conserva sesión, turnos, colas C2/C3, ingesta, creación de sugerencias por C10, escaneo de salida e interfaz con el escáner de U11, consola base y axe, y suma consentimiento, perfil, AnalysisWorker sobre C17, corridas con su registro de modelos, bloqueo por incidente e import-linter de semantic-agent. Lo que fijan C1–C3, C10, C17, C21, CD-01/06/11, U1 F3, FD-U3-04/08/10/13 y FD-U10-03/16 no se pregunta; solo quedan seis decisiones de criterio (P6–P11): efecto de anonimizador_no_disponible (UG-02), alcance y fin del bloqueo, incidente fuera de su sesión, quién marca processing, corrida de los turnos ENT y tramos cubiertos por el modo final.
- 2026-11-22T03:13:39Z — El bloqueo por incidente se modela con blocked_code permanente además del estado blocked: blocked solo reemplaza a open, paused o suspended, y una sesión finalized o terminated conserva su estado con blocked_code fijo. Así P7 = A («se puede finalizar y consolidar») cabe en el enum único de SessionStatus de C1; pide precisiones a U6 (FD-U4-18) y a U7, que no puede exigir un modo final terminado en una sesión que ya no lo puede lanzar (FD-U4-19).
- 2026-11-22T03:13:39Z — «Plegado» se explicó con D52 y D53 de la matriz del TG (pasajes poco relevantes reemplazados por «[pasaje plegado: N palabras]»), porque ni C6 ni requirements definen el término; queda como propuesta FD-U4-17.

## Deviations
- 2026-11-22T03:13:39Z — AnalysisRun se partió en tres tablas de solo inserción (AnalysisRun con la petición, RunStatusChange con cada estado y su actor, RunAttempt con el resultado de cada intento) en lugar de la fila con status, error_code y finished_at de components: responde a FD-U3-10 sin precisar AC8.4.2, a costa de derivar el estado vigente de la última fila (FD-U4-03).
- 2026-11-22T03:13:39Z — Se añadieron sin pregunta los code session.suspended y session.consolidated a C1 y el actor run-supervisor a la lista ActorSystem; los tres quedan en la tabla FD-U4 para decidir en la aprobación.
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:28:41Z — El escáner de vocabulario prohibido se asignó a U4 en libs/integrity_policy con la firma scan(text, literal_sources), resolviendo el hallazgo R-01 de la revisión de U1 desde esta unidad y dejándolo en la tabla de precisiones para el humano.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:28:41Z — Un solo llamado al juez por turno con solo las afirmaciones que pasan la guardia, en vez de uno por afirmación: menos latencia en CPU y coherente con el arreglo claims de C6, a cambio de que una afirmación mal formada invalide el turno entero (que es lo que pide FR4.2).
- 2026-11-22T03:13:39Z — Un resultado que se va a descartar (intento viejo, corrida cancelada o vencida) se revisa igual en busca de un incidente antes de descartarlo: cuesta una lectura del registro por mensaje descartado, pero no se pierde una llamada externa sin anonimizar que ya ocurrió (FD-U4-11, AUTONOMIA-04).
- 2026-11-22T03:13:39Z — AnonymizationIncident sobrevive a la retención sin clave foránea, solo con IDs, en vez de borrarse con la sesión como pide el orden de C24: conserva la evidencia de VE-14 a cambio de una excepción más al borrado (FD-U4-12).
- 2026-11-22T03:13:39Z — En la ingesta, el vocabulario prohibido en un hallazgo invalida la corrida entera (regla de U1, F3) aunque U11 descarte solo el candidato (FD-U11-02): son dos líneas distintas, y en la segunda no se quita nada en silencio.

## Open questions
- 2026-11-22T03:13:39Z — La interacción entre la pausa de U6 y la ruta de turnos (202 sin corrida en pausa) y el code para turnos sobre una sesión suspendida dependen de la segunda pasada de U6, que aún no se hace.
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:28:41Z — Máximo de caracteres por pasaje, dimensión del vector, intervalo de sondeo y plazo por turno quedan para NFR Requirements.
