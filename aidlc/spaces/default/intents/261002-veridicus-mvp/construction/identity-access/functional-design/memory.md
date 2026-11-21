<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:08:41Z — La comprobación de «sesiones pendientes» del cambio de rol (P3) va en ConsoleApi y no en IdentityAccess, con el mismo criterio de ADR-009, para no crear dependencia de IdentityAccess hacia InterviewSession; hasta que U4 cree la tabla de sesiones, el puerto devuelve 0.
- 2026-11-21T22:45:12Z — Segunda pasada (Modify) de U3 por el cambio 01, la adenda 02 y las revisiones 3. Siguen BR1–BR4, BR6 y BR7 (autenticación, gestión de usuarios, primer admin, matriz, auditoría, accesibilidad) con P1–P3 = A. Cambian BR5 y F9, que pasan del umbral a la configuración por PR (perfiles, proveedores, prompts, precios y límites, AC8.3.x). Quedan «Retirado» las acciones upload_scenario y apply_threshold_change. Entran el rol investigador (destino M8), las extensiones owner-only-for-role y demo de C1, el manejador de Problem Details, el consumo de C23 y el usuario de retención de A-2 en la convención. Las precisiones user.* de la revisión 1 siguen pendientes, porque C1 v2 pone validation.invalid_request. Pregunté solo los cinco puntos de criterio (P4–P8): VE-09 frente a FR1.2, el registro de acceso y su fallo, el actor sistema (R-02), el usuario de retención y las sesiones pendientes con desactivación (R-03).
- 2026-11-21T23:10:30Z — Revisión 2 escrita con P4–P8 = A: 51 reglas (BR1.1–BR9.5, ninguna retirada) y 43 escenarios (E1–E43). La tabla de precisiones conserva el número §10 de la revisión 1 para no romper referencias, y va de FD-U3-01 a FD-U3-13.
- 2026-11-21T23:10:30Z — R-01: la marca de la convención es una sola, en el comentario de la tabla (`veridicus-audit`), y la llevan todas las tablas, no solo los historiales (kind history | mutable). Así la prueba común detecta una tabla sin registrar sin necesitar un sufijo ni una lista paralela.
- 2026-11-21T23:10:30Z — R-08: en vez de renombrar las columnas de actor y hora de las otras unidades (consolidated_by, exported_at…), la marca declara cuáles son; ADR-003 «actor/at» se lee como columnas lógicas (FD-U3-07).
- 2026-11-21T23:10:30Z — Registro de acceso: un sondeo con `since` no es una apertura y no se registra (BR9.4); la apertura de un hallazgo es el POST de observation-views. Ninguna de las dos cosas la decía P5; quedaron como propuesta en FD-U3-05.
- 2026-11-21T23:10:30Z — Los `code` `user.weak_password` y `auth.too_many_attempts` vienen de NFR Requirements de U3, y `system.internal` y `system.unavailable` del manejador; todos quedan como propuesta a C1 (FD-U3-02, FD-U3-03).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:08:41Z — U3 es de tipo service y no produce frontend-components.md, pero toca M0 y M6; los estados y textos de esas pantallas quedaron en §6 de functional-spec.md, y la accesibilidad de US5.6 se cubrió con BR7.1–BR7.3 porque el mapa de historias la reparte entre unidades.
- 2026-11-21T23:10:30Z — R-04: la revisión 1 pedía anotar la carrera entre el cambio de rol y U4 como riesgo aceptado. En su lugar la cerré dentro de U3 (BR2.12): toda petición que cambia estado bloquea en modo compartido la fila del usuario, y el PATCH en exclusivo. El orden de bloqueo pasa a usuario → sesión → ronda (FD-U3-13).
- 2026-11-21T23:10:30Z — P7 = A daba al usuario de retención SELECT y DELETE; le añadí INSERT solo en RetentionAct, porque el Job escribe el acta con su propio usuario (FD-U3-09).
- 2026-11-21T23:10:30Z — AC8.4.2 incluye «las corridas», pero AnalysisRun tiene estado mutable; no lo resolví desde U3 y lo dejé como FD-U3-10 para U4.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:08:41Z — El primer admin nace con un comando ejecutado como Job revisable que lee un Secret (P1 = A), en vez de crearse al arrancar o por migración: respeta la prohibición de migraciones al arrancar y de versionar Secrets, a costa de un paso manual en la instalación.
- 2026-11-21T23:10:30Z — Registro de acceso por marca declarativa en el pipeline (P5 = A), en vez de que cada unidad llame al puerto: una sola prueba de nivel 0 lo vigila, a costa de una extensión nueva en C1 y de que la exportación siga siendo la excepción que llama al puerto ella misma.
- 2026-11-21T23:10:30Z — Desactivar se permite con sesiones pendientes (P8 = A): prima el control de seguridad, a costa de sesiones en solo lectura hasta reactivar; M6 muestra su número con un campo `pending_sessions` nuevo en C1 (FD-U3-04).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:08:41Z — Política de contraseñas, duración de la sesión web y bloqueo por intentos fallidos quedan para NFR Requirements.
- 2026-11-21T23:10:30Z — NFR11.1 y NFR11.2 de NFR Requirements de U3 (revisión 1) quedan superados por BR6.1 y BR5.2; hay que actualizarlos en la segunda pasada de esa etapa (FD-U3-12).
- 2026-11-21T23:10:30Z — Los textos de M6 (Reactivar, Cambiar rol, confirmación con número, mensajes de 409 y 422), M0 (429) y M8 (403) son propuestas de esta etapa (FD-U3-11); los decide el humano en la aprobación.
