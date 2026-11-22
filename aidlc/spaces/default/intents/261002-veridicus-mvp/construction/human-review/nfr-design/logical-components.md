# Componentes lógicos — U5 human-review

**Revisión 2 (2026-11-22): segunda pasada por el cambio 01 (DT27), la adenda 02 y el NFR Requirements
revisión 2.** Sustituye a la revisión 1 del 2026-10-03.
- **Qué cambia.** Entran el resolvedor para `GuardedRoute`, `purge_session`, `discard_correction_round`,
  `changed_since` y la reconciliación de métricas. La ruta `cot-views` pasa a `observation-views`. Las
  variables de C25 cambian de nombre (NFRD-U5-03).
- **Numeración.** §1–§5 conservan su número.

**Insumos.** `nfr-requirements/performance-requirements.md` (performance-requirements),
`security-requirements.md` (security-requirements), `scalability-requirements.md`
(scalability-requirements), `reliability-requirements.md` (reliability-requirements),
`observability-requirements.md` (observability-requirements) y `tech-stack-decisions.md`
(tech-stack-decisions: D1–D15, NFR2.1, NFR13.1–NFR13.3, NFR14.1) de esta unidad;
`functional-design/functional-spec.md` (functional-spec); C1, C10, C11, C15 v2, C23, C24 y C25 de
`contract-summary.md` (contract-summary); los demás documentos de esta carpeta.

## 1. Inventario

| Componente lógico | Proceso | Dentro / fuera del clúster | Responsabilidad | Patrones de NFR |
|---|---|---|---|---|
| Rutas `decisions` y `observation-views` | API de `session-api` | Dentro | C1 de U5 | `GuardedRoute` de U3; tope del cuerpo; sin reintentos de decisiones |
| `suggestion_owner` | API de `session-api` | Dentro | Resolvedor de U3 para las dos rutas | `404` uniforme; `403` `session.not_owner` |
| `ReviewCommands.decide`, `record_observations_view` | `human_review/application` | Dentro | F1, F2, F3 | Orden usuario → sesión → ronda; una `UnitOfWork` |
| `ReviewRounds` (C11) | `human_review/application` | Dentro | F5, F7 | `bump` memorizado; `lock_round` y `discard_correction_round` atómicos |
| `SuggestionProposer.propose` (C10) | Trabajador de `session-api` (código de U4) | Dentro | F4 | Bajo el `bump` de la ingesta |
| `HumanReviewPurge.purge_session` (C24) | `Job` de retención de U13 | Dentro | F6 | Cuatro `DELETE … RETURNING` en la transacción del `Job` |
| `state_machine`, `effective_state`, `dismissal_window` | `human_review/domain` | Dentro | Reglas puras | 100 % de ramas en los dos primeros |
| `effective_state_query` (con `changed_since`), `round_repository` | `human_review/adapters` | Dentro | Consultas de número fijo de sentencias; único `FOR UPDATE` de rondas | Índices de `scalability-design.md` §3 |
| `change_cursor.bump`, `db.py` | `session_api/shared` | Dentro | Bloqueo de la sesión; `statement_timeout`, `lock_timeout` y `hide_parameters` | Compartidos con U4, U7 y U13 sin ciclos |
| `ReviewMetrics` | API de `session-api` | Dentro | C15 v2 | `apply` con `change_seq`; reconciliación cada 60 s; fallo aislado |
| Tarjeta de la sugerencia | `frontend` (navegador) | Dentro (solo habla con ConsoleApi) | BR5 | Sin actualización optimista |

## 2. Dominios de falla y radio de impacto

| Falla | Qué deja de funcionar | Qué sigue | Radio |
|---|---|---|---|
| PostgreSQL | Todo U5 | — | Todo el sistema |
| Redis | Toda la consola, por `/readyz` de U3 con 1 réplica | El módulo HumanReview no lo usa; el trabajador y el `Job` siguen | Toda la consola (NFRD-U5-08) |
| Bloqueo de una sesión retenido | Decisiones, turnos y consolidación de **esa** sesión (`503` a los 2 s) | Las demás sesiones | Una sesión |
| Recálculo o reconciliación de métricas | La razón de descartes de una sesión | Decisiones (`201`) | Solo la señal AIR |
| Adaptador del registro de acceso | La entrada de acceso de esa apertura | `observation-views` responde `204` | Una entrada (riesgo aceptado de U3) |
| `Job` de retención | El borrado de esa sesión | Todo lo demás; se relanza | Una sesión |
| Prometheus o Grafana | Señal AIR y panel | Revisión completa | Observabilidad |
| Juez o anonimizador | Nada de U5 | Revisión y consolidación | — |

## 3. Recursos compartidos

| Recurso | Compartido con | Aislamiento |
|---|---|---|
| Proceso API de `session-api` | U3, U4, U6, U7, U13 | Capas e import-linter; `human_review.domain` sin E/S; nada pesado en memoria |
| Fila de la sesión (`change_cursor`) | U4, U6, U7 | Orden único; transacciones cortas sin E/S de red; `lock_timeout` de 2 s |
| Base PostgreSQL | Todas las unidades | Solo inserción en tres tablas; columnas acotadas en `review_round`; `DELETE` solo para `veridicus_retention` |
| `/metrics` | U3, U4, U7 | Nombres de C15 v2; etiquetas validadas |

## 4. Entrega a Infrastructure Design

- Sin `Deployment` propio: U5 corre en la API, el trabajador y el `Job` de retención de `session-api`, con 1
  réplica de la API en el MVP (límite de la razón, `scalability-design.md` §4).
- Sumar ≤ 32 MiB de RSS de U5 al `limits.memory` de la API.
- La migración de U5 (columnas de `review_round`, tablas `review_decision` y `observations_view`, permisos de
  `veridicus_app` y `veridicus_retention`, disparadores, `CHECK` e índices) entra como `Job` de migración en su
  propio PR.
- *Values* de `session-api`: `VERIDICUS_DB_LOCK_TIMEOUT_MS`; y, solo si se quiere bajar una cifra,
  `VERIDICUS_LIMIT_REVIEW_TEXT_MAX_CHARS`, `VERIDICUS_LIMIT_REVIEW_BODY_MAX_BYTES` y
  `VERIDICUS_LIMIT_DISMISSAL_WINDOW_W` (NFRD-U5-03). Sale `VERIDICUS_AIR_WINDOW`.

## 5. Calidad, pruebas y textos (NFR2.1, NFR13.1, NFR13.2, NFR13.3, NFR14.1)

- **CPU y sin modelos.** U5 no usa modelos; niveles 0 y 1 con PostgreSQL real en contenedor, sin GPU ni
  descargas.
- **Cobertura.** ≥ 80 % de líneas en `services/session-api` y `frontend`, bloqueante en la CI; 100 % de ramas
  en `human_review/domain/state_machine.py` y `domain/effective_state.py` con `.coveragerc-guards`
  (`fail_under = 100`). `dismissal_window.py` entra en el 80 % general con los casos de NFR15.3.
- **Fronteras.** import-linter con control negativo: `human_review.domain` no importa `api`, `adapters` ni
  otros módulos; `human_review` no importa clientes de red (`security-design.md` §1); ConsoleApi y U4 solo
  usan la interfaz de C10, U7 la de C11 y U13 la de `Purgeable` (C24); todos pueden usar `session_api.shared`.
  `lint-imports` con 0 errores.
- **Textos.** Tarjeta, editor y errores solo con cadenas del catálogo de mensajes (BR5.1–BR5.8, FD-U5-10); la
  prueba de nivel 0 de literales visibles cubre los componentes de U5. Identificadores del glosario:
  `review_suggestion`, `review_decision`, `review_round` y `observations_view`.
- **Accesibilidad.** `vitest-axe` sobre la tarjeta y sus formularios y `@axe-core/playwright` en
  `review.spec.ts`: 0 violaciones `serious` o `critical`, todo con teclado y `aria-disabled` en los botones
  con motivo.
