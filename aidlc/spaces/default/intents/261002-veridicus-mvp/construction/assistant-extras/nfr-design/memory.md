<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T03:34:45Z — La comprobación de plazo de la pregunta (P2 = A) suma también los 5 s de count_tokens: ahora + 5 + 60 + 15 s < deadline_at; la omisión usa reason timeout para no ampliar el enum de NFR15.4.

- 2026-11-22T16:46:08Z — Segunda pasada: el sondeo de U4 no leía las tablas de U8; se pidió a U4 (NFRD-U8-02) que las incluya con change_seq en las dos tablas, y la decisión de la aclaración no cambia su change_seq para respetar «solo cambia status».

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-22T16:46:08Z — El índice único de D12 pasa a usar el SHA-256 de tema_key (NFRD-U8-03), porque un tema largo no cabe en una entrada B-tree; quedó como precisión sin editar D12.
- 2026-10-03T03:34:45Z — Con el reintento de P1 = A el peor caso de un turno con tres extras es 482,2 s y supera el reclamo aprobado de 480 s; el diseño fija 510 s en los values con extras. Quedó en la tabla de precisiones de performance-design sin editar NFR3.6 ni NFR3.7.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T03:34:45Z — La lista afectiva y el prompt de la pregunta se validan al arrancar aunque los extras estén apagados; un archivo roto impide arrancar semantic-agent, a cambio de que activar un extra por PR nunca descubra el fallo en el clúster.

- 2026-11-22T16:46:08Z — Un disparador diferido exige la fila de historial al confirmar cada cambio de estado (cierra R-04 de la revisión 1), a cambio de un disparador más que probar; la prueba de humo comprueba la permutación en el registro de llamadas en vez de añadir el perfil a C1.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
