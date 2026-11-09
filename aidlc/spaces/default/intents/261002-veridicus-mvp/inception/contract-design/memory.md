<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T22:05:00Z — Las fronteras en proceso dentro de session-api (C10–C12) se trataron como contratos aunque no crucen la red, porque unen módulos de unidades distintas (U4, U5, U7) y la respuesta P4 pidió interfaces tipadas.
- 2026-11-09T13:41:01Z — Los adaptadores nativos de los proveedores comerciales se pusieron en el Anonymizer y no en ModelGateway, porque components ya le da al Anonymizer las API comerciales como dependencia externa y así U11 no depende de código de U10 al revés (P13 = A, CD-04).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T22:05:00Z — Los hallazgos R-02 y R-03 de Units Generation se resolvieron en el contrato (ronda 1 abierta por propose; métricas AIR emitidas por U5) y se anotaron en una tabla para el humano, sin editar unit-of-work.md ya aprobado.
- 2026-11-09T13:41:01Z — La segunda pasada conservó C1–C16, marcó C4 y C9 «Retirado» y numeró lo nuevo C17–C25, en lugar de rehacer el documento, para no romper las referencias de las etapas de Construction.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T22:05:00Z — El audio viaja en base64 dentro del Redis Stream (C5) para no compartir un volumen entre pods; queda como pregunta abierta cambiar a una referencia a volumen si el tamaño máximo lo hace inviable.
- 2026-11-09T13:41:01Z — La cancelación de corridas usa una clave de Redis que InterviewSession escribe y el trabajador solo lee, en vez de darle al trabajador acceso a la base: así ninguna llamada nueva sale tras la retirada del consentimiento (VE-10 (a)) sin romper ADR-002 ni ADR-006 (CD-06).
- 2026-11-09T13:41:01Z — El reporte de la CLI cierra con `pattern` cada cadena permitida (versiones, hashes, nombres de perfil y etiquetas) para que no quepa testimonio, en vez de filtrar el texto en la consola (P12 = A).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-09T13:41:01Z — La v1.0.0 del contrato común queda aprobada aquí por el autor, pero falta su aprobación en el repositorio principal del TG; hasta entonces la copia en `contracts/` lleva la versión de esta etapa.
