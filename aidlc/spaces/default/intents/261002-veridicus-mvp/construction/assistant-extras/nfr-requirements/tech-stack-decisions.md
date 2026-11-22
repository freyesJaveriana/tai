# Decisiones de pila — U8 assistant-extras

**Revisión 2 (2026-11-22), segunda pasada por el cambio 01 (DT27), la adenda 02 y el Functional Design
revisión 2 de U8.** Sustituye a la revisión 1 del 2026-10-03. Las decisiones conservan su número: D1, D2,
D4, D5, D6, D7 y D10 de la revisión 1 quedan **Retirado**; D3, D8 y D9 **cambian**; lo nuevo es D11–D14.

**Insumos.** Flujos F4–F9 de `functional-design/functional-spec.md` (functional-spec) y reglas BR4–BR6 de
`functional-design/rules.md` (rules); NFR2, NFR13 y NFR14 de
`inception/requirements-analysis/requirements.md` (requirements); C1, C3, C6, C8, C15, C18 y C19 de
`inception/contract-design/contract-summary.md` (contract-summary); `security-requirements.md`; las
decisiones de pila de U1 (cargador seguro, `veridicus_contracts`), U3, U4 y U11 de hoy.

Lo que ya fijan `team.md`, U1, U3, U4 y U11 no se repite. U8 **no añade dependencias nuevas**: usa las de
`libs/incoherence_analyzer`, `libs/integrity_policy`, `veridicus_contracts`, `semantic-agent`,
`session-api` y `frontend`.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | Retirado | Modelo y servidor de los extras | — | — | U8 ya no llama a ningún modelo | — |
| D2 | Retirado | Segunda lectura del juez | — | — | Sale con el cambio 01; la permutación es la del verificador de U11 | — |
| D3 | cambia | Validación de la aclaración | Función pura en `libs/incoherence_analyzer/domain/clarification.py`: arma la candidata (BR5.1), aplica BR5.3–BR5.6 en orden, deduplica (BR5.8) y devuelve aclaraciones y eventos de descarte; sin E/S. La ingesta de `session-api` importa el mismo validador para su segunda línea (BR5.9) | Validar con el LLM; reglas distintas en la biblioteca y en la ingesta | Código puro de AUTONOMIA-03 y VE-05 en `domain/` (`team.md`), 100 % de ramas, y una sola implementación para los dos puntos | NFR10.1, NFR10.5, NFR4.5, NFR13.2 |
| D4 | Retirado | *Prompt* de la pregunta | — | — | Sale con la pregunta sugerida | — |
| D5 | Retirado | Salida de la pregunta | — | — | Sale con la pregunta sugerida | — |
| D6 | Retirado | Política de la pregunta | — | — | La sustituye D3 | — |
| D7 | Retirado | Indicio afectivo | — | — | Sale con US11.1 | — |
| D8 | cambia | Activación de la permutación | `permutation: true` en cada perfil de `config/profiles.yaml`, cambiado solo por PR, más una prueba de nivel 0 de U8 que lo exige (BR6.1) | Banderas en los *values* de `session-api`; opción por sesión en la consola | La configuración vive en archivos versionados (FR9.2) y entra en `config_sha256` | NFR10.9, NFR11.4 |
| D9 | cambia | Decisión del analista | Transacción con `change_cursor.bump` de la sesión, `SELECT … FOR UPDATE` de `conductor_observation`, cambio de `status` e `INSERT` en `conductor_observation_decision`; permiso por columna y disparador que rechaza cambios fuera de `proposed`; migración en su propio `Job` y PR | `UPDATE … WHERE status = 'proposed'` sin bloqueo de la sesión (la revisión 1); bloqueo optimista con versión | Sigue el orden único sesión → fila de NFR Design y mueve el cursor del sondeo en la misma transacción | NFR10.15, NFR11.1, NFR11.2, NFR8.4 |
| D10 | Retirado | Corrida de nivel 2 con extras en el arnés de U4 | — | — | La sustituye D13 | — |
| D11 | nuevo | Normalización y regla de DT23 | Las funciones de normalización del escáner de C8 (`libs/integrity_policy`: palabra completa, sin mayúsculas ni tildes, espacios colapsados) y la regla de aclaración neutra leída en ejecución con el cargador seguro de `veridicus_contracts` | Expresiones regulares propias; copiar la lista en el código | Un solo criterio de palabra para el escáner y la aclaración; la lista cambia solo por PR de U1 | NFR10.5, NFR10.14 |
| D12 | nuevo | Persistencia de las aclaraciones | Dos tablas en el esquema de `session-api`: `conductor_observation` (índice único `(session_id, turnos, tema_key)`, `tema_key` = tema normalizado) y `conductor_observation_decision`; inserción con `ON CONFLICT DO NOTHING` dentro de la transacción de la ingesta de U4 | Tabla en Redis; una fila por corrida sin deduplicar | Idempotente sin estado en memoria y purgable con la sesión | NFR10.17, NFR8.4, NFR8.5, NFR11.5 |
| D13 | nuevo | Mediciones de nivel 2 de B8 | La CLI de U11: `veridicus analyze` en modo incremental por entrevista para BR5.17 y la permutación, más un comprobador independiente en `evaluation/clarifications/check_quotes.py` que solo imprime conteos | El arnés de U4; medir en el clúster | El nivel 2 lo corre la CLI (decisión de U4 y U11); el comprobador no reutiliza el validador de D3, para que sea independiente | NFR4.3, NFR4.6, NFR3.13, NFR8.7 |
| D14 | nuevo | Panel en M4 | Componente `ConductorObservationPanel` con TanStack Query sobre el sondeo de U4; el tema se pinta como texto (nunca HTML); región `aria-live="polite"` con el contador | Llamada propia de sondeo; anunciar cada aclaración | Un solo ciclo de sondeo y los anuncios agregados de BR4.7 | NFR3.10, NFR10.16 |

## 2. Configuración (prefijo `VERIDICUS_`)

U8 no añade ajustes. Los de la revisión 1 (`VERIDICUS_EXTRAS_*`, `VERIDICUS_QUESTION_*`,
`VERIDICUS_AFFECTIVE_KEYWORDS_PATH`) quedan **Retirado**, y `VERIDICUS_TURN_DEADLINE_BASE_SECONDS` y
`VERIDICUS_QUEUE_RECLAIM_IDLE_SECONDS` vuelven a ser solo de U4. La regla de aclaración neutra viene en el
paquete `veridicus_contracts` y la permutación en `config/profiles.yaml`.

## 3. Calidad del código (NFR2, NFR13, NFR14)

| ID | Estado | Requisito | Criterio medible |
|---|---|---|---|
| NFR2.1 | cambia | Todo U8 se prueba en CPU sin modelos reales en los niveles 0 y 1. | El gateway *fake* de U11 cubre las llamadas directa y permutada; ninguna prueba de los niveles 0 y 1 descarga un modelo, abre un *socket* hacia fuera ni exige GPU |
| NFR2.2 | cambia | U8 funciona con `todo-local` en CPU (NFR2). | La medición de BR6.5 (NFR3.13) corre `todo-local` en la máquina de desarrollo sin GPU; las aclaraciones no dependen del perfil |
| NFR13.1 | cambia | Cobertura de líneas. | ≥ 80 % en `libs/incoherence_analyzer`, `services/semantic-agent`, `services/session-api` y `frontend` con el código de U8 incluido, medido en la CI y bloqueante |
| NFR13.2 | cambia | 100 % de ramas en los módulos guardia de U8. | `libs/incoherence_analyzer/domain/clarification.py` (BR5.3–BR5.8) y `services/session-api/.../domain/conductor_observation_state.py` (BR5.12): `--cov-branch` con `fail_under = 100`, añadidos a `.coveragerc-guards`. Sus pruebas se escriben primero y se ejecutan en rojo (`team.md`, Ordering) |
| NFR14.1 | cambia | Textos visibles en español y del catálogo; identificadores del glosario. | El rótulo, los estados, los botones, los motivos y los mensajes de error del panel salen del catálogo de U1; la prueba de literales de U4 cubre el panel. Identificadores: `conductor_observation`, `clarification_candidate`, `clarification_discard_event`, y `tema` y `turnos` sin traducir (CD-05) |
| NFR14.2 | Retirado | La pregunta está en español. | Sale con la pregunta sugerida |

## 4. Trabajo en otras unidades que U8 necesita

Prerrequisitos del plan de tareas de U8 (cierra R-05 de la revisión 1); cada uno entra por el PR de su
unidad antes del código de B8:
- **U1:** los `code` de FD-U8-02, la versión 1.1.0 de la regla de aclaración neutra (FD-U8-04), la sección
  `clarifications` de C19 v2 (FD-U8-09), el esquema de `ConductorObservation` (NFR-U8-04) y las métricas
  en C15 (NFR-U8-05).
- **U11:** el punto de inserción del módulo y el cambio de su prueba de `observaciones_conductor`
  (FD-U8-01).
- **U4:** la segunda línea de validación y el guardado en la ingesta, y el borrado por la retención
  (FD-U8-07); la prueba de carga con la permutación activa (NFR-U8-06).
- **U9:** la prueba de nivel 1 de la ruta de audio (NFR-U8-07).

## 5. Comandos de verificación (AUTONOMIA-02)

| Qué verifica | Comando | Umbral |
|---|---|---|
| Unitarias, contratos y guardias (nivel 0) | `uv run --directory libs/incoherence_analyzer pytest -m "not integration and not perf"`, y lo mismo en `services/semantic-agent` y `services/session-api` | Verde |
| Ramas de los módulos guardia | `uv run --directory libs/incoherence_analyzer pytest --cov-branch --cov-config=.coveragerc-guards` y lo mismo en `services/session-api` | 100 % (NFR13.2) |
| Perfiles con la permutación activa | `uv run --directory libs/incoherence_analyzer pytest -k profiles_permutation` | Verde; rojo con el *fixture* de E41 |
| Integración (nivel 1) | `uv run --directory services/session-api pytest -m integration -k conductor_observation` y `uv run --directory services/semantic-agent pytest -m integration -k permutation` | Verde |
| Rendimiento en proceso | `uv run --directory services/session-api pytest -m perf -k conductor_observation` y `uv run --directory libs/incoherence_analyzer pytest -m perf -k clarification` | NFR3.2, NFR3.8, NFR3.9 |
| Consola | `npm --prefix frontend run test -- --coverage` y `npm --prefix frontend run typecheck` | Verde; ≥ 80 % de líneas |
| Aclaraciones en nivel 2 (fuera de la CI) | `uv run --directory evaluation python -m clarifications.run --profile comercial-piloto --report out/u8-clarifications.json`, que llama a `veridicus analyze` por entrevista y después a `check_quotes.py` | 0 coincidencias (NFR4.3); tasa reportada (NFR4.6) |
| Costo de la permutación (nivel 2, fuera de la CI) | `uv run --directory evaluation python -m clarifications.permutation_cost --profiles todo-local,comercial-piloto --report out/u8-permutation-cost.json` | NFR3.1, NFR3.13, NFR8.7 |
| Carga (a demanda) | `uv run --directory evaluation python -m load.run_batches --sessions 50 --concurrency 3 --report out/nfr8.json` | ≥ 98 % con la permutación activa (NFR8.1) |
| Humo (nivel 3) | `scripts/smoke.sh <url-base>` | Código 0 en ≤ 300 s por caso (NFR3.12) |
| E2E y accesibilidad del panel (nivel 3) | `npx --prefix frontend playwright test e2e/conductor-observations.spec.ts` | NFR3.10, BR4.4, NFR10.5 |
| Tipos, *lint* y fronteras | `mypy --strict`, `ruff check` y `lint-imports` en cada paquete | 0 errores |

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| El juez de U11 escribe `hecho` que describen la contradicción y casi todas las aclaraciones se descartan | NFR4.6 lo hace visible; la corrección es del *prompt* de U11 por PR, nunca de las reglas de VE-05 |
| La permutación con `todo-local` no cabe en el plazo de la demostración | NFR8.7 la mide; se apaga en `todo-local` por PR (NFR-U8-01) |
| El comprobador de nivel 2 comparte un error con el validador | D13 lo escribe aparte, con búsqueda directa de subcadenas normalizadas, y su control negativo |
