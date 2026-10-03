<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-03T01:38:15Z — P2 se respondió con texto propio («8 con composición y lista común»); se leyó como mínimo 8 con mayúscula, minúscula, número y símbolo más la lista de contraseñas comunes, y se añadió un máximo de 128 caracteres para acotar el costo de Argon2id.
- 2026-10-03T01:38:15Z — U3 es el primer Bolt que construye session-api (B2), así que sus decisiones de pila fijan la base del proceso para U4–U7: FastAPI, Pydantic v2, SQLAlchemy 2 con psycopg 3, Alembic en un Job y redis-py.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-03T01:38:15Z — Las métricas de autenticación, los code auth.too_many_attempts, user.weak_password y system.unavailable y la cabecera Retry-After no están en los contratos aprobados; se registraron en la tabla de precisiones en vez de editar contract-summary.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-03T01:38:15Z — El limitador de intentos falla cerrado (503) si Redis no responde: se prefiere no dejar entrar a nadie antes que permitir probar contraseñas sin límite, a costa de que una caída de Redis bloquee el inicio de sesión.
- 2026-10-03T01:38:15Z — last_seen_at se escribe como máximo una vez por minuto aunque la consola sondee más seguido: evita una escritura por sondeo a costa de que la caducidad por inactividad tenga hasta 60 s de holgura.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
