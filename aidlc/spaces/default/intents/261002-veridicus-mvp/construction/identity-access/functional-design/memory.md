<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T23:08:41Z — La comprobación de «sesiones pendientes» del cambio de rol (P3) va en ConsoleApi y no en IdentityAccess, con el mismo criterio de ADR-009, para no crear dependencia de IdentityAccess hacia InterviewSession; hasta que U4 cree la tabla de sesiones, el puerto devuelve 0.
- 2026-11-21T22:45:12Z — Segunda pasada (Modify) de U3 por el cambio 01, la adenda 02 y las revisiones 3. Siguen BR1–BR4, BR6 y BR7 (autenticación, gestión de usuarios, primer admin, matriz, auditoría, accesibilidad) con P1–P3 = A. Cambian BR5 y F9, que pasan del umbral a la configuración por PR (perfiles, proveedores, prompts, precios y límites, AC8.3.x). Quedan «Retirado» las acciones upload_scenario y apply_threshold_change. Entran el rol investigador (destino M8), las extensiones owner-only-for-role y demo de C1, el manejador de Problem Details, el consumo de C23 y el usuario de retención de A-2 en la convención. Las precisiones user.* de la revisión 1 siguen pendientes, porque C1 v2 pone validation.invalid_request. Pregunté solo los cinco puntos de criterio (P4–P8): VE-09 frente a FR1.2, el registro de acceso y su fallo, el actor sistema (R-02), el usuario de retención y las sesiones pendientes con desactivación (R-03).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T23:08:41Z — U3 es de tipo service y no produce frontend-components.md, pero toca M0 y M6; los estados y textos de esas pantallas quedaron en §6 de functional-spec.md, y la accesibilidad de US5.6 se cubrió con BR7.1–BR7.3 porque el mapa de historias la reparte entre unidades.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T23:08:41Z — El primer admin nace con un comando ejecutado como Job revisable que lee un Secret (P1 = A), en vez de crearse al arrancar o por migración: respeta la prohibición de migraciones al arrancar y de versionar Secrets, a costa de un paso manual en la instalación.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T23:08:41Z — Política de contraseñas, duración de la sesión web y bloqueo por intentos fallidos quedan para NFR Requirements.
