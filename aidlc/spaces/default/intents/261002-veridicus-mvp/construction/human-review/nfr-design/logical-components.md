# Componentes lógicos — U5 human-review

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions, D1–D12) de esta unidad; `functional-design/functional-spec.md` (functional-spec);
C1, C10, C11 y C15 de `inception/contract-design/contract-summary.md` (contract-summary); respuesta
P1 = A de `nfr-design-questions.md`; los demás documentos de diseño de esta carpeta.

## 1. Inventario

| Componente lógico | Proceso | Dentro / fuera del clúster | Responsabilidad | Patrones de NFR |
|---|---|---|---|---|
| Rutas `decisions` y `cot-views` | API de `session-api` | Dentro | C1 de U5 | `authorize` de U3; cuerpo ≤ 64 KiB; sin reintentos |
| `suggestion_owner` | API de `session-api` | Dentro | Resolver el dueño para U3 | Mismo `403` para inexistente y ajeno |
| `ReviewCommands.decide` | `human_review/application` | Dentro | F2, F3 | Orden sesión → ronda (P1 = A); una `UnitOfWork` |
| `SuggestionProposer.propose` | `human_review/application` | Dentro | F4 (C10) | Idempotencia; exige el bloqueo de sesión de U4 |
| `ReviewRounds` | `human_review/application` | Dentro | F5 (C11) | `open_round(for_update=True)` con `bump`; `lock_round` atómico |
| `state_machine`, `effective_state`, `dismissal_window` | `human_review/domain` | Dentro | Reglas puras | 100 % de ramas en los dos primeros |
| `effective_state_query`, `round_repository` | `human_review/adapters` | Dentro | Consultas con número fijo de sentencias; único `FOR UPDATE` de rondas | Índices de scalability-design §3 |
| `change_cursor.bump` | `session_api/shared` | Dentro | Bloqueo de la sesión y `change_seq` | Compartido con U4 y U7 sin ciclos |
| `ReviewMetrics` | API de `session-api` | Dentro | C15 | `after_commit`; fallo aislado |
| Tarjeta de sugerencia | `frontend` (navegador) | Dentro (solo habla con ConsoleApi) | BR5 | Sin actualización optimista |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Radio |
|---|---|---|---|
| PostgreSQL | Todo U5 | — | Todo el sistema |
| Bloqueo de una sesión retenido | Decisiones y turnos de **esa** sesión (`503` a los 2 s) | Las demás sesiones | Una sesión |
| Recálculo de métricas | La razón AIR de una sesión | Decisiones (`201`) | Solo la señal AIR |
| Prometheus o Grafana | Señal AIR y panel | Revisión completa | Observabilidad |
| Juez, *embeddings*, Redis | Nada de U5 | Revisión y consolidación | — |

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso API de `session-api` | U3, U4, U6, U7 | Capas e import-linter; `human_review.domain` sin E/S; nada pesado |
| Fila de la sesión (`change_seq`) | U4, U7 | Orden único sesión → ronda; transacciones cortas sin E/S de red; `lock_timeout` 2 s |
| Base PostgreSQL | Todas las unidades | Solo inserción en `review_decision` y `cot_view`; columnas acotadas en `review_round` |
| `/metrics` | U3, U4 | Prefijos `veridicus_review_*` y `veridicus_session_dismissal_ratio` |

## 4. Entrega a Infrastructure Design

- Sin `Deployment` propio: U5 corre en la API de `session-api`, con 1 réplica en el MVP (límite de la
  razón AIR, scalability-design §4).
- Sumar ≤ 32 MiB de RSS de U5 al `limits.memory` de la API, con ≥ 20 % de margen.
- La migración de U5 (tablas, permisos, *trigger*, índices, columna `change_seq`) entra como `Job` de
  migración en su propio PR.
- Valores `VERIDICUS_AIR_WINDOW`, `VERIDICUS_REVIEW_TEXT_MAX_CHARS` y `VERIDICUS_DB_LOCK_TIMEOUT_MS` en
  los *values* de `session-api`.

## 5. Calidad, pruebas y textos (NFR2.1, NFR13.1, NFR13.2, NFR13.3, NFR14.1)

- **CPU y sin modelos.** U5 no usa modelos; niveles 0 y 1 con PostgreSQL real en contenedor, sin GPU ni
  descargas.
- **Cobertura.** ≥ 80 % de líneas en `services/session-api` y `frontend` (bloqueante en CI); 100 % de
  ramas en `human_review/domain/state_machine.py` y `domain/effective_state.py` con
  `.coveragerc-guards` (`fail_under = 100`): la tabla de functional-spec §3 se prueba celda por celda.
- **Fronteras.** import-linter: `human_review.domain` no importa `api`, `adapters` ni otros módulos;
  `human_review` no importa clientes de red; ConsoleApi y U4 solo usan `contracts/python/human_review.py`
  (C10) y U7 `forensic_ports.py` (C11); todos pueden usar `session_api.shared`. Control negativo en CI:
  `lint-imports` con 0 errores.
- **Textos.** Tarjeta, editor y errores solo con cadenas del catálogo de U1; la prueba de nivel 0 de U4
  sobre literales visibles cubre los componentes de U5; identificadores del glosario
  (`review_suggestion`, `review_decision`, `review_round`, `cot_view`).
- **Accesibilidad.** `vitest-axe` sobre la tarjeta y `@axe-core/playwright` en `review.spec.ts`: 0
  violaciones `serious` o `critical`.
