# Decisiones de pila — U5 human-review

**Revisión 2 (2026-11-22).** Es la segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional
Design revisión 2 de U5. Sustituye a la revisión 1 del 2026-10-03.

**Qué cambia.**
- D2 salta las rondas `discarded`.
- D3 sigue el orden usuario → sesión → ronda.
- D4 pasa de `seq` a `change_seq`.
- D8 y D12 leen sus cifras de C25.

**Qué entra.**
- D13: publicación en orden de la razón (cierra R-03).
- D14: `purge_session`.
- D15: catálogo de límites.

**Insumos.**
- Flujos F1–F7 de `functional-design/functional-spec.md` (functional-spec).
- Reglas de `functional-design/rules.md` (rules) y entidades de `entities.md`.
- NFR2, NFR10, NFR11, NFR13 y NFR14 de `inception/requirements-analysis/requirements.md` (requirements).
- C1, C10, C11, C15 v2, C24 y C25 de `inception/contract-design/contract-summary.md` (contract-summary).
- Respuesta P1 = A de `nfr-requirements-questions.md`.
- `security-requirements.md`.
- Las decisiones de pila ya aprobadas de U3 (la base de `session-api`), U4 (consola y escáner) y U1 (C25).

**Lo que no se repite**, porque ya lo fijan `team.md`, U3 y U4:
- Python 3.12, FastAPI y Uvicorn;
- Pydantic v2 y `pydantic-settings`;
- SQLAlchemy 2 síncrono con psycopg 3 y `statement_timeout`;
- Alembic en un `Job`;
- `prometheus-client`;
- la marca `perf` de `pytest` y el reloj inyectable;
- TanStack Query, `@axe-core/playwright` y `vitest-axe`;
- `libs/integrity_policy` y Problem Details desde `libs/`;
- `uv`, mypy estricto, Ruff, import-linter, Vitest y Playwright.

U5 no añade dependencias nuevas.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | cambia | Máquina de estados | Función pura en `human_review/domain/state_machine.py`, con la tabla de transiciones como dato y la función `check(previous, requested, note, reformulation, observations_viewed) -> Allowed \| Rejection(code)` | La biblioteca `transitions`; las reglas repartidas en la capa de aplicación | La tabla completa se prueba por casos, con 100 % de ramas y sin base de datos (AUTONOMIA-03) | NFR13.2, NFR10.3 |
| D2 | cambia | Estado vigente | Se calcula y nunca se guarda: una consulta con `DISTINCT ON (suggestion_id)` sobre las decisiones de las rondas de la sesión con `status <> 'discarded'` y número ≤ el de la ronda pedida, ordenadas por `number DESC, change_seq DESC`. Sin decisiones → `pending`. La función pura `domain/effective_state.py` (BR3.2) es la referencia | Columna `current_state` en `ReviewSuggestion`; recorrer las rondas una a una en Python | Una columna exigiría `UPDATE` sobre una tabla de auditoría. Recorrer rondas hace N consultas (NFR3.4). La consulta equivale a BR3.2 porque toda corrección hereda de la última ronda `locked` y una ronda `discarded` nunca es base. Una prueba de propiedad (Hypothesis) compara la consulta con la función pura sobre historias aleatorias de hasta 10 rondas con descartes | NFR3.4, NFR13.2 |
| D3 | cambia | Concurrencia | Orden único: bloqueo compartido del usuario (ConsoleApi), luego `change_cursor.bump` con bloqueo exclusivo de la sesión, luego `SELECT … FOR UPDATE` de la ronda. Aplica en `decide`, `open_round(for_update=True)`, `lock_round`, `open_correction_round` y `discard_correction_round`. `lock_timeout` de 2 s. `record_observations_view` no bloquea la sesión | Aislamiento `SERIALIZABLE` con reintentos; *advisory locks* | Serializa lo que debe serializarse (una sesión) sin interbloqueos con la ingesta, porque todos toman el mismo orden. Evita reintentar decisiones que no son idempotentes | NFR10.11, NFR10.12, NFR10.15 |
| D4 | cambia | Orden de las decisiones | `change_seq bigint` de la sesión, obtenido del *bump*, en `ReviewDecision` y `ReviewRound`. Índice único (`round_id`, `suggestion_id`, `change_seq`) | La columna `seq` de identidad de la revisión 1; confiar en `at` o en el UUID | Un mismo número ordena las decisiones, la ventana AIR y el sondeo de U4. Dos escrituras de una sesión nunca comparten `change_seq` | NFR13.2, NFR15.2 |
| D5 | cambia | Barreras en la base | `INSERT`/`SELECT` en las tablas `history`. En `ReviewRound`, `UPDATE` por columna más el disparador de NFR11.3. `DELETE` solo para `veridicus_retention`. `CHECK` de nota y reformulación, índices únicos de NFR8.3 y *engine* con `hide_parameters=True` | Validar solo en la aplicación | Defensa en profundidad para AUTONOMIA-03, y para que un error de la base no lleve la nota a los logs | NFR11.1, NFR11.3, NFR11.5, NFR10.6 |
| D6 | se mantiene | «En blanco» | `str.strip()` de Python como autoridad (espacios Unicode); `btrim` en el `CHECK` como segunda barrera | Expresiones regulares en la base | Python y PostgreSQL no coinciden en qué es un espacio Unicode: decide la aplicación y la base solo ataja lo obvio | NFR10.5 |
| D7 | cambia | Métricas de C15 v2 | `Counter` y `Gauge` de `prometheus-client`. La razón se calcula con la consulta de la ventana (NFR15.2) en un gancho `after_commit` de la `UnitOfWork`. La serie se retira (`remove`) en el `after_commit` de `lock_round`, de `discard_correction_round` y de `purge_session` | Un *collector* propio que consulta la base en cada lectura de `/metrics` | `/metrics` no depende de la base y responde rápido (NFR3.6). Con varias réplicas el valor es eventualmente exacto (NFR8.4) | NFR15.1, NFR15.2, NFR10.17 |
| D8 | cambia | Ventana *W* | `dismissal_window_w` = 8 de C25, que también es el mínimo para publicar | *W* = 12; *W* = 4 publicada desde la primera decisión | P1 = A: sin falsas alarmas al inicio y reacción rápida con decenas de sugerencias por sesión | NFR15.2 |
| D9 | se mantiene | Pruebas de concurrencia | Dos hilos con `threading.Barrier`, dos conexiones a PostgreSQL real y 50 repeticiones por caso | Simular el bloqueo con *mocks* | Solo la base real muestra la carrera, y `team.md` pide PostgreSQL real | NFR10.11, NFR10.12, NFR10.17 |
| D10 | se mantiene | Hora de las decisiones | `at`, `viewed_at`, `locked_at` y `discarded_at` vienen del reloj inyectable de U3 (UTC) en la capa de aplicación y se guardan como `timestamptz` | `now()` de la base; la hora del navegador | Se puede probar con reloj controlado y nunca viene del cliente (NFR7.1) | NFR11.1, NFR7.1 |
| D11 | se mantiene | Consola | Mutación de TanStack Query sin actualización optimista: la tarjeta cambia con la respuesta `201` y se invalida la consulta de la sesión | Actualización optimista | La consola nunca muestra un estado que el servidor no registró (AUTONOMIA-03) | NFR3.7, NFR10.16 |
| D12 | cambia | Tamaño del cuerpo | Se deja de leer el cuerpo JSON de las rutas de U5 al pasar de `review_body_max_bytes` = 65 536 bytes, antes de validar, y se responde `413` `limits.exceeded` | Confiar en el límite del Ingress | Corta la entrada en la frontera con la cifra del catálogo (NFR10 de requirements) | NFR10.5 |
| D13 | nuevo | Publicación en orden de la razón (R-03) | Un candado en proceso por sesión envuelve el cálculo y el `set`. Se publica solo si el `change_seq` máximo leído es ≥ al último publicado de esa sesión | Publicar sin orden; recalcular dentro de la transacción | Dos `after_commit` de la misma sesión no dejan un valor viejo. Calcular dentro de la transacción alargaría el bloqueo de la sesión | NFR10.17 |
| D14 | nuevo | `purge_session` | `DELETE … WHERE … RETURNING id` por tabla, en el orden de BR6.1, con la `UnitOfWork` del `Job` (usuario `veridicus_retention`). Arma el `PurgeReceipt` con los ID devueltos | Borrado en cascada con `ON DELETE CASCADE`; borrar fila por fila | El orden explícito no depende de las claves foráneas de otras unidades, y el recibo sale de lo que de verdad se borró. `CASCADE` borraría en silencio | NFR10.22, NFR3.9 |
| D15 | nuevo | Cifras de límite | Se leen de `contracts/limits.v1.yaml` (C25) con el cargador de U1. Una variable `VERIDICUS_*` solo puede bajarlas | Constantes en el código; variables que pueden subir | Es la regla de `project.md` (catálogo único). Una prueba de nivel 0 de U1 falla si U5 usa una cifra que no viene de ahí | NFR10.5, NFR15.2 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Estado | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|---|
| `VERIDICUS_AIR_WINDOW` | **Retirado** | — | Lo sustituye `VERIDICUS_DISMISSAL_WINDOW_W` con la cifra de C25 | — |
| `VERIDICUS_DISMISSAL_WINDOW_W` | nuevo | `dismissal_window_w` de C25 (8) | Entero entre 2 y la cifra de C25; si es mayor, el proceso no arranca | `session-api` |
| `VERIDICUS_REVIEW_TEXT_MAX_CHARS` | cambia | `review_text_max_chars` de C25 (2 000) | Entero entre 1 y la cifra de C25; aplica a la nota y a la reformulación | `session-api` |
| `VERIDICUS_REVIEW_BODY_MAX_BYTES` | nuevo | `review_body_max_bytes` de C25 (65 536) | Entero entre 16 384 y la cifra de C25 | `session-api` |
| `VERIDICUS_DB_LOCK_TIMEOUT_MS` | se mantiene | 2000 | Entero entre 100 y el `statement_timeout` de U3 | `session-api` |

Una configuración que falta, es inválida o intenta subir una cifra de C25 impide arrancar el pod
(`team.md`; NFR10.18).

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | se mantiene | Todo U5 se prueba en CPU y sin modelos. | U5 no llama a modelos. Los niveles 0 y 1 corren con PostgreSQL real en contenedor, y ninguna prueba exige GPU ni descarga nada. |
| NFR13.1 | se mantiene | Cobertura de líneas. | ≥ 80 % en `services/session-api` (incluido el módulo `human_review`) y en `frontend`, medido en la CI y bloqueante. |
| NFR13.2 | cambia | 100 % de ramas en los módulos guardia de U5. | Los módulos guardia son `services/session-api/src/session_api/human_review/domain/state_machine.py` (BR2.1–BR2.5) y `domain/effective_state.py` (BR3.2, con rondas `discarded`). Se miden con `--cov-branch` y `fail_under = 100`. La tabla de transiciones se prueba celda por celda, incluidos «igual a igual sin cambios» y «hacia `pending`». `domain/dismissal_window.py` lleva los casos de NFR15.3 y entra en el 80 % general. |
| NFR13.3 | cambia | Las fronteras del módulo se respetan. | import-linter con control negativo en la CI: <br>• `human_review.domain` no importa `api`, `adapters` ni otros módulos; <br>• ConsoleApi y U4 solo importan la interfaz de C10; <br>• U7, la de C11; <br>• U13, la de `Purgeable` (C24); <br>• HumanReview no importa clientes HTTP ni de Redis (NFR1.1). |
| NFR14.1 | cambia | Textos visibles en español y del catálogo. | La tarjeta, el editor y los mensajes de error usan solo cadenas del catálogo de mensajes (BR5.1–BR5.8 y FD-U5-10). La prueba de nivel 0 de literales visibles cubre los componentes de U5. Los identificadores siguen el glosario: `review_suggestion`, `review_decision`, `review_round` y `observations_view`. |

## 4. Accesibilidad

BR5.5 y BR5.6 reutilizan la base de U4. Se usan `vitest-axe` sobre la tarjeta y sus formularios, y
`@axe-core/playwright` en `frontend/e2e/review.spec.ts`. Criterios:
- 0 violaciones `serious` o `critical`;
- las acciones se completan solo con teclado;
- los botones con motivo usan `aria-disabled` y siguen en el orden de Tab;
- cada estado lleva icono y texto, además del color.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias y guardias (nivel 0) | `uv run --directory services/session-api pytest tests/human_review -m "not integration and not perf"` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest tests/human_review --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1): permisos, roles, concurrencia, idempotencia, retención, logs y métricas | `uv run --directory services/session-api pytest tests/human_review -m integration` | Verde: NFR10.1–NFR10.22, NFR11.1–NFR11.6, NFR8.3–NFR8.6 y NFR15.2–NFR15.5 |
| Rendimiento en proceso | `uv run --directory services/session-api pytest tests/human_review -m perf` | NFR3.1–NFR3.6, NFR3.9, NFR8.1 y NFR8.2 |
| Prueba común de auditoría y retención (U3) | `uv run --directory services/session-api pytest -m integration -k audit_convention` | Las cuatro tablas de U5 descubiertas por la marca; `UPDATE`/`DELETE` fallan con `veridicus_app`; `DELETE` funciona con `veridicus_retention` |
| Consola | `npm --prefix frontend run test -- --coverage src/review` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| E2E (nivel 3) | `npx --prefix frontend playwright test e2e/review.spec.ts` | 0 fallos (NFR8.7, NFR3.7, NFR3.8, NFR10.9) |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en `services/session-api` | 0 errores (NFR13.3) |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| La consulta de D2 deja de equivaler a BR3.2 si un día una corrección hereda de una ronda que no es la última bloqueada | La prueba de propiedad de D2 compara con la función pura. Si BR3.3 cambia, la prueba falla y obliga a revisar la consulta |
| El bloqueo de la sesión frena las decisiones si U7 tarda en consolidar o U4 en ingerir | `lock_timeout` de 2 s y un `503` claro (NFR10.15). Lo que toca a U5 en la consolidación mide p95 ≤ 150 ms (NFR3.5) |
| La razón AIR diverge con varias réplicas | Límite declarado en NFR8.4; el MVP corre 1 réplica |
| Un `Job` de retención borra con un orden distinto | El orden lo fija `purge_session` (D14), no el `Job`, y la prueba de NFR10.22 lo cubre |
