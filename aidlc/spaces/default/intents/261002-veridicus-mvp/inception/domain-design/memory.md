<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T20:41:42Z — Las colas de petición y respuesta (turno → resultado, audio → texto) se modelan como una sola arista del solicitante hacia el evaluador o el transcriptor; la respuesta viaja como parte de la misma interacción, así el grafo de componentes queda sin ciclos.
- 2026-11-06T23:13:46Z — La respuesta 10 (protocolo solo demostrativo) contradecía la adenda 02 aprobada (VE MUST); se resolvió con el Seguimiento 1 = A: el analizador cumple las reglas éticas del TG sin rebaja y la consola demuestra el resto en EthicsGovernance sin compuertas. Las rebajas quedan como propuestas DD-01 a DD-07 para que el humano decida en la aprobación.
- 2026-11-06T23:13:46Z — VE-10 (pausa, terminación y retirada del consentimiento) se dejó en InterviewSession como estados de la sesión y no como demostración, porque que nada se analice tras la retirada es un principio del analizador (A-4); quedó como DD-06 para decidir.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T20:41:42Z — Se añadieron cuatro ADR que no salieron de las preguntas (ADR-006 a ADR-009) porque las historias ya fijaban la decisión (AC2.1.2, AC3.3.2, AC6.3.4, FR1.2) y solo faltaba registrar su consecuencia en los componentes.
- 2026-11-06T23:13:46Z — El trabajador semantic-agent aparece en el catálogo como AnalysisWorker, sin reglas propias, aunque la pregunta 6 solo nombraba IncoherenceAnalyzer y AnalyzerCli; sustituye a SemanticEvaluation, que queda retirado junto con TruthFrame (DD-10).
- 2026-11-06T23:13:46Z — Se añadió ADR-017 (contrato común como fuente externa, con el consentimiento dentro) sin pregunta propia, porque ya lo decidían DT17, project.md y A-4.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T20:41:42Z — La propiedad de la sesión se verifica en ConsoleApi y no en HumanReview para evitar un ciclo InterviewSession ↔ HumanReview; el costo es que toda entrada futura debe repetir la verificación (ADR-009).
- 2026-11-06T23:13:46Z — El registro de acceso y de exportaciones lo escribe ConsoleApi en EthicsGovernance, no ReviewReport, para que la retención (EthicsGovernance → ReviewReport) no cierre un ciclo; el costo es que una exportación fuera de ConsoleApi no quedaría registrada.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-06T23:13:46Z — El mensaje de corrida lleva la transcripción hasta hasta_turno (ADR-006); NFR Requirements debe confirmar que su tamaño cabe en Redis con el catálogo de límites, como ya se dejó abierto para el audio en base64.
