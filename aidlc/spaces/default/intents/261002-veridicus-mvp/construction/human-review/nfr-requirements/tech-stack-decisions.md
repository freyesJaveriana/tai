# Decisiones de pila — U5 human-review

**Insumos.** Flujos F1–F5 de `functional-design/functional-spec.md` (functional-spec), reglas de
`functional-design/rules.md` (rules) y entidades de `entities.md`; NFR2, NFR10, NFR11, NFR13 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C10, C11 y C15 de
`inception/contract-design/contract-summary.md` (contract-summary); respuesta P1 = A de
`nfr-requirements-questions.md`; `security-requirements.md`; las decisiones de pila ya aprobadas de U3
(base de `session-api`) y de U4 (consola y escáner).

Lo que ya fijan `team.md`, U3 y U4 no se repite: Python 3.12, FastAPI y Uvicorn (U3 D1), Pydantic v2
y `pydantic-settings` (U3 D2), SQLAlchemy 2 síncrono con psycopg 3 y `statement_timeout` (U3 D3),
Alembic en un `Job` (U3 D4), `prometheus-client` (U3 D10), marca `perf` de `pytest` (U3 D11), reloj
inyectable (U3 D12), TanStack Query (U4 D13), `@axe-core/playwright` y `vitest-axe` (U4 D14),
`libs/integrity_policy` (U4), Problem Details desde `libs/`, `uv`, mypy estricto, Ruff, import-linter,
Vitest y Playwright. U5 no añade dependencias nuevas.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Máquina de estados | Función pura en `human_review/domain/state_machine.py` con la tabla de transiciones de functional-spec §3 como dato y una función `check(previous, requested, note, reformulation, cot_viewed) -> Allowed \| Rejection(code)` | Biblioteca `transitions`; reglas repartidas en la capa de aplicación | La tabla completa se prueba por casos con 100 % de ramas sin base de datos (AUTONOMIA-03) | NFR13.2, NFR10.3 |
| D2 | Estado vigente | Calculado, nunca guardado: una consulta con `DISTINCT ON (suggestion_id)` sobre las decisiones de las rondas de la sesión con número ≤ el de la ronda pedida, ordenadas por `number DESC, at DESC, seq DESC`; sin decisiones → `pending`. La función pura `domain/effective_state.py` (BR3.2) es la referencia | Columna `current_state` en `ReviewSuggestion`; recorrer las rondas una a una en Python | Una columna exigiría `UPDATE` sobre una tabla de auditoría y duplicaría la verdad; recorrer rondas hace N consultas (NFR3.4). La consulta equivale a BR3.2 porque cada corrección hereda de la ronda anterior (BR3.3); una prueba de propiedad (Hypothesis) compara la consulta con la función pura sobre historias aleatorias de hasta 10 rondas | NFR3.4, NFR13.2 |
| D3 | Concurrencia | `SELECT … FOR UPDATE` sobre la fila de la ronda `open` en `decide`, `lock_round` (vía `open_round(for_update=True)`) y `open_correction_round`; `lock_timeout` de 2 s | Aislamiento `SERIALIZABLE` con reintentos; *advisory locks* | Serializa lo que debe serializarse (una sesión) sin reintentos de decisiones que no son idempotentes; un solo analista no nota la espera | NFR10.11, NFR10.12, NFR10.15 |
| D4 | Orden de inserción | Columna `seq bigint GENERATED ALWAYS AS IDENTITY` en `ReviewDecision` como desempate de `at` | Confiar en `at` o en el UUID | BR3.2 pide «a igual hora, mayor orden de inserción»; un UUID v4 no tiene orden | NFR13.2 |
| D5 | Barreras en la base | Permisos `INSERT`/`SELECT` en `ReviewDecision` y `CotView`; `UPDATE` por columna en `ReviewRound` más un *trigger* que rechaza cambiar una ronda `locked`; `CHECK` de nota y reformulación; índices únicos de NFR8.3; *engine* con `hide_parameters=True` | Solo validación en la aplicación | Defensa en profundidad para AUTONOMIA-03 y para que un error de la base no lleve la nota a los logs | NFR11.1, NFR11.3, NFR10.6 |
| D6 | «En blanco» | `str.strip()` de Python como autoridad (espacios Unicode); `btrim` en el `CHECK` como segunda barrera | Expresiones regulares en la base | Python y PostgreSQL no coinciden en qué es espacio Unicode; la aplicación decide y la base solo ataja lo obvio | NFR10.5 |
| D7 | Métricas de C15 | `Counter` y `Gauge` de `prometheus-client`; la razón se calcula con una consulta de la ventana (NFR15.2) en un gancho `after_commit` de la `UnitOfWork`, y la serie se retira (`remove`) en el `after_commit` de `lock_round` | *Collector* propio que consulta la base en cada lectura de `/metrics` | `/metrics` no depende de la base y responde rápido (NFR3.6); con una réplica el valor es exacto. Límite conocido para varias réplicas en NFR8.4 | NFR15.1, NFR15.2, NFR10.17 |
| D8 | Ventana *W* | `VERIDICUS_AIR_WINDOW = 8`, que también es el mínimo para publicar | *W* = 12; *W* = 4 publicada desde la primera alerta | P1 = A: sin falsas alarmas al inicio y reacción rápida con decenas de alertas por sesión | NFR15.2 |
| D9 | Pruebas de concurrencia | Dos hilos con `threading.Barrier` y dos conexiones a PostgreSQL real, 50 repeticiones por caso | Simular el bloqueo con *mocks* | Solo la base real muestra la carrera; team-practices prohíbe *mocks* de la base | NFR10.11, NFR10.12 |
| D10 | Hora de las decisiones | `at` y `viewed_at` del reloj inyectable de U3 (UTC) en la capa de aplicación, guardados como `timestamptz` | `now()` de la base; hora del navegador | Probable con reloj controlado y nunca del cliente (NFR7.1) | NFR11.1, NFR7.1 |
| D11 | Consola | Mutación de TanStack Query sin actualización optimista: la tarjeta cambia con la respuesta `201` y se invalida la consulta de la sesión | Actualización optimista | La consola nunca muestra un estado que el servidor no registró (AUTONOMIA-03) | NFR3.7, NFR10.16 |
| D12 | Tamaño del cuerpo | Límite de 64 KiB al leer el cuerpo JSON de las rutas de U5, antes de validar | Confiar en el límite del *ingress* | Corta la entrada en la frontera (NFR10 de requirements) | NFR10.5 |

## 2. Configuración (prefijo `VERIDICUS_`)

| Ajuste | Valor por defecto | Validación al arrancar | Servicio |
|---|---|---|---|
| `VERIDICUS_AIR_WINDOW` | 8 | Entero entre 2 y 50 | `session-api` |
| `VERIDICUS_REVIEW_TEXT_MAX_CHARS` | 2000 | Entero igual a 2 000 en el MVP (el `maxLength` de C1, precisión en `security-requirements.md` §6); aplica a nota y reformulación | `session-api` |
| `VERIDICUS_DB_LOCK_TIMEOUT_MS` | 2000 | Entero entre 100 y el `statement_timeout` de U3 | `session-api` |

Una configuración faltante o inválida impide arrancar el pod (team-practices; NFR10.18).

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Requisito | Criterio medible |
|---|---|---|
| NFR2.1 | Todo U5 se prueba en CPU y sin modelos. | U5 no llama a modelos; los niveles 0 y 1 corren con PostgreSQL real en contenedor y ninguna prueba exige GPU ni descarga nada. |
| NFR13.1 | Cobertura de líneas. | ≥ 80 % en `services/session-api` (incluido el módulo `human_review`) y en `frontend`, medido en la CI y bloqueante. |
| NFR13.2 | 100 % de ramas en los módulos guardia de U5. | `services/session-api/src/session_api/human_review/domain/state_machine.py` (BR2.1–BR2.5) y `domain/effective_state.py` (BR3.2): `--cov-branch` con `fail_under = 100` sobre esos módulos. La tabla de functional-spec §3 se prueba celda por celda, incluidos «igual a igual sin cambios» y «hacia `pending`». `domain/dismissal_window.py` lleva los casos de NFR15.3 y entra en el 80 % general. |
| NFR13.3 | Las fronteras del módulo se respetan. | import-linter: `human_review.domain` no importa `api`, `adapters` ni otros módulos; ConsoleApi y U4 solo importan la interfaz de `contracts/python/human_review.py` (C10) y U7 la de `forensic_ports.py` (C11). Control negativo en la CI. |
| NFR14.1 | Textos visibles en español y del catálogo. | La tarjeta, el editor y los mensajes de error usan solo cadenas del catálogo de U1 (BR5.1–BR5.4); la prueba de nivel 0 de U4 sobre literales visibles cubre los componentes de U5; identificadores según el glosario (`review_suggestion`, `review_decision`, `review_round`, `cot_view`). |

## 4. Accesibilidad

BR5.5 reutiliza la base de U4 (D14 de U4): `vitest-axe` sobre la tarjeta y sus formularios, y
`@axe-core/playwright` en `frontend/e2e/review.spec.ts`; 0 violaciones `serious` o `critical`, las tres
acciones se completan solo con teclado y cada estado lleva texto además del color.

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias y guardias (nivel 0) | `uv run --directory services/session-api pytest tests/human_review -m "not integration and not perf"` | Verde |
| Ramas de los módulos guardia | `uv run --directory services/session-api pytest tests/human_review --cov-branch --cov-config=.coveragerc-guards` | 100 % (NFR13.2) |
| Integración (nivel 1): permisos, concurrencia, idempotencia, logs y métricas | `uv run --directory services/session-api pytest tests/human_review -m integration` | Verde; NFR10.1–NFR10.18, NFR11.1–NFR11.3, NFR8.3–NFR8.6, NFR15.3 |
| Rendimiento en proceso | `uv run --directory services/session-api pytest tests/human_review -m perf` | NFR3.1–NFR3.6, NFR8.1, NFR8.2 |
| Prueba común de auditoría (U3) | `uv run --directory services/session-api pytest -m integration -k audit_convention` | `ReviewDecision` y `CotView` registradas; `UPDATE`/`DELETE` fallan |
| Consola | `npm --prefix frontend run test -- --coverage src/review` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| E2E (nivel 3) | `npx --prefix frontend playwright test e2e/review.spec.ts` | 0 fallos (NFR8.7, NFR3.7, NFR3.8, NFR10.9) |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check`, `lint-imports` en `services/session-api` | 0 errores (NFR13.3) |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| La consulta de D2 deja de equivaler a BR3.2 si un día una corrección hereda de una ronda que no es la anterior | La prueba de propiedad de D2 compara con la función pura; si BR3.3 cambia, la prueba falla y obliga a revisar la consulta |
| El bloqueo de la ronda frena las decisiones si U7 tarda en consolidar | `lock_timeout` de 2 s y `503` claro (NFR10.15); la consolidación de U7 mide p95 ≤ 150 ms en lo que toca a U5 (NFR3.5) |
| La razón AIR por proceso diverge con varias réplicas | Límite declarado en NFR8.4; el MVP corre 1 réplica |
| U7 olvida llamar `open_round(for_update=True)` | Precisión registrada para C11 y U7; la prueba de NFR10.12 falla sin ella |
