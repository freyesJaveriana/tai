# Plan de generación de código — U1 contracts (Bolt B1 «Contratos»)

**Revisión 2 (2026-11-23), segunda pasada por el cambio 01 (DT27), la adenda 02 y las revisiones 3.**
Sustituye al plan de la primera pasada (2026-10-30), que queda en el historial de Git y cuya aprobación
dejó de valer. Los pasos se renumeran: el plan viejo no tiene código construido que referenciar.

**Insumos.**
- Unidad U1 de `inception/units-generation/unit-of-work.md` (unit-of-work, revisión 3) y su orden interno
  en `unit-of-work-story-map.md`; Bolt B1 de `inception/delivery-planning/bolt-plan.md` (definición de
  terminado 1–6 y demo).
- C1–C25 de `inception/contract-design/contract-summary.md` (contract-summary, revisión 3).
- Flujos F1–F9, escenarios E1–E44 y precisiones FD-U1-01 a FD-U1-14 de
  `construction/contracts/functional-design/functional-spec.md`; reglas BR1.1–BR12.3 de `rules.md`;
  entidades de `entities.md`.
- NFR1.1–NFR15.1 de `construction/contracts/nfr-requirements/security-requirements.md` y D1–D16 de
  `tech-stack-decisions.md` (revisión 2).
- Controles §4.1–§4.19, catálogo C25 v1 (§5), cambios pedidos por otras unidades (§6) y precisiones
  NFRD-U1-01 a NFRD-U1-14 de `construction/contracts/nfr-design/security-design.md` (revisión 2).
- Peticiones a U1 de las tablas NFRD e IDS de otras unidades (lista en PD-2).
- Requisitos de `inception/requirements-analysis/requirements.md`; prácticas de `team.md` y `project.md`;
  método del loop de agentes en `docs/loop/README.md` §5.2.

**Alcance.** U1 es una unidad `spec`. Este plan produce:
- los contratos versionados de `contracts/` (inventario de functional-spec §1 más NFRD-U1-13);
- la distribución `veridicus-contracts` (importada como `veridicus_contracts`) con sus tres funciones
  puras y la huella JCS (`profiles.validate`, `limits.load`, `registry`, `canonical.sha256_jcs`);
- la jerarquía declarativa de excepciones de `libs/errors/`;
- la suite de nivel 0 en dos mitades (Python y `contracts/ts/`), sus herramientas y el *job* de CI
  `contracts-level0`.

No hay servicios, infraestructura de clúster ni migraciones. U1 no tiene historias propias; respalda
criterios de US3.6, US8.3, US12.6, US13.3 y US15.4 (AC3.6.2, AC3.2.1, AC5.5.3, AC5.5.4, AC8.3.1,
AC8.3.3, AC12.6.1, AC13.3.1, AC15.4.7).

**Ejecución.** La Parte 2 se hace con el **loop de agentes** (`docs/loop/README.md`, DT30): cada paso, o
cada grupo de pasos marcado como una tarea, se convierte en un archivo de `docs/loop/tareas/` con su
alcance, sus archivos y su comando de verificación. Los PR de tarea van a la rama del Bolt; el Bolt entra
a `main` con *squash-merge*. `Approve Plan` lo elige el humano (team.md, Mandated).

## Decisiones del plan

| # | Decisión | Alternativas descartadas | Consecuencia |
|---|---|---|---|
| PD-1 | La versión que publica B1 de cada contrato es contract-summary revisión 3 **más** las precisiones aprobadas de las tablas FD-U1, NFR-U1 y NFRD-U1 de U1. Las de FD-U1-01 a FD-U1-14 se toman como aprobadas con Functional Design. | Publicar solo contract-summary y que cada precisión entre luego como cambio | B1 sale con las formas que ya diseñó U1; los originales (`contract-summary.md`, `components.md`) se actualizan aparte si el humano lo decide (R-1). |
| PD-2 | B1 incluye además las peticiones a U1 **ya aprobadas** en NFR Design e Infrastructure Design de otras unidades que solo tocan contratos de U1: NFRD-U3-10 (`route.not_found` 404, `Retry-After` en el `503` de login), NFRD-U6-01 (`transcript_body_max_bytes`, `import_body_max_bytes` y su relación), NFRD-U7-04 (cuerpo `{ expected_cursor }`, `409 report.view_outdated`, `cursor_max_chars`), NFRD-U7-11 (glosario), NFRD-U8-05 (tope y `413` en la decisión), NFRD-U9-03 (`voice_body_max_bytes`), NFRD-U12-02 (`research_report_read_timeout_s`), NFRD-U13-08 (C24 v1.1.0 `count_session`), NFRD-U13-13 (`whitespace_code_points`) y los archivos de métricas de NFRD-U4-08, NFRD-U6-12, NFRD-U8-06, NFRD-U9-10 y NFRD-U10-02. | Un PR de U1 por cada unidad antes de su Bolt (security-design §6) | Evita unos 12 PR menores seguidos sobre contratos que nadie consume aún. Lo que se apruebe después de B1 sigue la regla de §6: PR de U1 antes del Bolt que lo pide. |
| PD-3 | Quedan **fuera** de B1 las precisiones que siguen abiertas para el humano: `GET /notice` pública (FD-U4-08), `PATCH /sessions/{session_id}/analysis` (NFR-U6-03) y la opción (b) de FD-U1-14. Si el humano las aprueba antes de empezar el paso 16, entran ahí; si no, entran por su PR de U1. | Incluirlas ya | Ninguna decisión pendiente se da por tomada. `auth_surface` admite la lista pública con motivo, así que sumar `GET /notice` no rompe la comprobación. |
| PD-4 | La copia del contrato común (C6) la pone el humano desde `/insumos/app/contratos/analizador/v1/` en el paso 6, con las huellas que recalcula allí (F7 paso 5, BR1.8). El agente no edita ni genera esos dos archivos. | Que el agente copie los archivos | Se respeta BR1.8 y la regla de no editar la copia; el paso 6 tiene una parada humana corta. |
| PD-5 | El orden del equipo (Testing Contract) se aplica así en una unidad `spec`: antes de cualquier contrato, el paso 5 escribe en rojo las pruebas de contratos de datos (C6, C2, C3, C5, C7, C18, C19, C21 y fallidos) y de las guardias AUTONOMIA-03/04/05. El resto de capas (carga, registro, funciones puras, comprobaciones, herramientas, mitad TypeScript) se implementa y se prueba enseguida, paso a paso. | Convertirlo en TDD por capa | Es la `ordering` exacta del contrato (custom); no se reinterpreta. |
| PD-6 | El escáner `scan(text, literal_sources)` es de U11 (FD-U1-09). U1 publica `integrity/scan-cases.v1.yaml` y valida solo su forma (BR5.8); no reimplementa el escáner. `checks/veracity.py` compara nombres, rótulos y enum por igualdad de palabras (BR3.3, BR6.3). | Un comparador propio de texto libre en U1 | Un solo escáner en el sistema; los casos E10–E14, E30 y E40 los ejecuta U11 en B11. |
| PD-7 | `libs/errors/` es una distribución aparte, `veridicus-errors` (importada como `veridicus_errors`), con su `pyproject.toml`, su `uv.lock`, sus pruebas y sus compuertas (V-ERRORS). `contracts/` **no** la importa ni la incluye en su rueda: `checks/error_codes.py` lee sus fuentes por ruta con `ast` (nombre de clase, base y atributo `code`) y las compara con el catálogo. | Dependencia por ruta en `uv` desde `contracts/`; meter las clases en la rueda de contratos | `check_package` (paso 22) y BR12.1 no cambian; `libs/errors` tiene sus propios tipos, *lint* y cobertura del 80 % (team.md) (R-03 de la revisión 1). |
| PD-8 | Los pasos que escriben un contrato antes de C25 (pasos 7, 8 y 11) o de C1 (pasos 13–15) solo prueban su forma y sus *fixtures*; las marcas `x-veridicus-limit` y `x-veridicus-max-bytes` se comprueban contra el catálogo en el paso 16 (`limits_match`), y las guardias que miran C1 pasan a verde en el paso 16. El esquema de C18 (`effective-config.v1.yaml`) lo escribe el paso 7 junto con C2, que lo referencia (E-5, sustituye a E-2). Cada guardia del paso 5 marca sus pruebas con un marcador de pytest por contrato (`c1`, `c6`, `c7`, `c13`, `c16`, `c18`, `c19`, `c21`, `c8`, `labels`, `speech`, `asyncapi`) para poder acotarlas con `-m`. | Mover C25 y C1 al principio | Se conserva el orden de bolt-plan; ninguna verificación exige verde a una prueba cuyo contrato aún no existe (R-01, R-02, R-11). C7 va antes que C8 porque su esquema no depende del vocabulario (R-12). |
| PD-9 | Los módulos Python de contratos viven en `contracts/src/veridicus_contracts/<módulo>.py` y no en `contracts/python/`; el nombre de importación (`veridicus_contracts.<módulo>`) no cambia. Los esquemas y catálogos siguen en sus directorios de `contracts/` y entran a la rueda como datos (decisión del humano el 2026-11-23, tras tres rondas NO-VERDE de U01-T01: F-01, F-05, F-08). | Mantener `python/` con un mapa de desarrollo propio (`__path__` ampliado y lector de recursos sustituido): funciona al importar, pero mypy no resuelve las importaciones cruzadas (F-08) | Cambian las rutas de V-GUARD y V-TYPES y las de los pasos 3, 10, 11, 12, 17 y 19. Los artefactos aprobados que citan `contracts/python/` (functional-spec §1, contract-summary, components, bolt-plan y otros) no se editan: la precisión queda en `decisiones-humano.md` y se lleva a los originales si el humano lo decide al cerrar la etapa. |

## Dependencias y punto de partida

- **Tarea previa P0.1** (configuración de GitHub: protección de `main`, comprobaciones obligatorias, GHCR
  privado, *deploy key*, permisos de Actions, Dependabot) debe estar cerrada antes de abrir el PR del Bolt
  (`bolt-plan.md`). Este plan no la ejecuta.
- **Loop de agentes** configurado una vez (`docs/loop/README.md` §5.1): `.claude/agents/codificador.md` y
  `revisor.md`, carpetas de `docs/loop/`, `.worktrees/` en `.gitignore` y `gh pr merge` negado.
- **Rama del Bolt:** `feat/b1-contratos` desde `main`; PR de tarea hacia esa rama; PR del Bolt a `main` con
  *squash-merge* y la salida de los comandos como evidencia. Commits en Conventional Commits en español con
  alcance `contracts`.
- **Greenfield:** no hay código ni suite previa que mantener verde.
- **AUTONOMIA-01:** ningún paso aplica cambios a un clúster, a una base ni a la nube, ni envía trabajos a
  ZINE. Todo son archivos del repositorio, suites locales sin red y un *workflow* sin credenciales del
  clúster.
- **Datos:** solo sintéticos (`project.md`, NFR12.1). Nada de `/insumos` entra al repositorio salvo la copia
  de C6 (contrato común, permitido por `project.md` › Decided).

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (contrato común del analizador, esquema del hallazgo, mensajes de la cola, perfil de ejecución) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.",
  "scope": "classic",
  "test_strategy": "standard",
  "project_type": "greenfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Ordering**: En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (contrato común del analizador, esquema del hallazgo, mensajes de la cola, perfil de ejecución) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.\n- **Cobertura**: 80 % de líneas por cada servicio Python y por el frontend, medido en CI y bloqueante; **100 % de ramas** en los módulos guardia (verificación determinista de citas, validación y máquina de estados de la alerta, consolidación del reporte, anonimizador). Las exclusiones (migraciones, código generado, arnés de evaluación) se declaran en la configuración y cada exclusión nueva se justifica en el PR.\n- **Herramientas**: `pytest` + `pytest-cov` (+ `pytest-asyncio`, Hypothesis) y mypy estricto en Python; Vitest + React Testing Library y TypeScript estricto en el frontend; Playwright para E2E; validación de manifiestos con `helm template` → `kubeconform` → Kyverno CLI.\n- **Dobles de prueba**: los modelos se sustituyen por *fakes* deterministas del `ModelGateway` en los niveles 0 y 1, sin red; PostgreSQL y Redis son reales en contenedor.\n- **Niveles y compuertas**:\n  - **Nivel 0 (cada PR, bloquea)**: *lint*, tipos, unitarias, contratos, guardias AUTONOMIA deterministas, políticas de manifiestos, cobertura.\n  - **Nivel 1 (cada PR, bloquea)**: integración contra PostgreSQL y Redis reales (persistencia y reanudación de sesión, cola asíncrona, registro de quién y cuándo, anonimizador con su fallo cerrado).\n  - **Nivel 2, evaluación de IA con la línea de comandos del analizador**: corre contra cualquier proveedor del perfil, en la anfitriona o en ZINE, sobre el **conjunto sintético** versionado en `evaluation/` (contradicciones internas sembradas de los 7 tipos, relatos coherentes y casos trampa). Bloquea los PR que tocan la IA (filtro por rutas: *prompts*, perfiles, adaptadores de modelos, esquemas de salida) y toda entrega etiquetada. Se corre fuera de la CI y el reporte JSON (versión del dataset, *hash* del *prompt*, perfil con su huella, modelos por llamada, métricas) se adjunta al PR. Umbrales: 100 % de citas verificadas en lo emitido, 0 % de error de formato JSON, permutación de las dos citas en el 100 % de las consultas *offline*, consistencia > 65 % al invertir el orden, acuerdo entre 3 corridas y precisión y sensibilidad sobre el conjunto (umbrales en NFR Requirements). Incluye *red-teaming* (Escenarios A, B y C). Aparte, la CLI sobre las 10 entrevistas del piloto, con resultados fuera de Git, es prueba de humo frente a sus 4 contradicciones; no mide.\n  - **Nivel 3, E2E y humo**: antes de etiquetar una entrega y tras cada despliegue.\n  - **Manual**: calificación Likert de la CoT (≥ 4.5/5, dos evaluadores) y verificación de `NetworkPolicy` en el clúster, antes de la sustentación.\n- **CPU y GPU**: la suite completa corre en **CPU**, en la máquina de desarrollo. Las pruebas que de verdad requieren GPU (evaluación con modelos más grandes, ensayo de la demo) se agrupan en una **etapa separada del perfil GPU**, que se corre a demanda en la máquina GPU solo cuando es estrictamente necesario. Ninguna prueba de los niveles 0 y 1 exige GPU.\n- **Mapa AUTONOMIA** (cada plan de tareas cita la prueba por ID): 01 → comprobación estática de que ningún *workflow* ni *script* aplica cambios al clúster (nivel 0); 02 → cada tarea lleva `Verificación: <comando exacto>` y su umbral; 03 → máquina de estados con actor y hora, consolidación explícita con SHA-256, esquema sin campos de veracidad y escaneo de vocabulario prohibido en salida e interfaz que excluye las citas literales (niveles 0, 1 y 3); 04 → prueba del *payload* saliente del anonimizador, prueba de fallo cerrado, arranque rechazado con un destino externo sin anonimizador y política estática de `NetworkPolicy` (nivel 0) más verificación manual en el clúster; 05 → hallazgo rechazado sin cada uno de sus campos obligatorios, cita alterada o en otro turno que no sale, `error` ⇒ hallazgos vacíos y cita restaurada antes de verificarse (niveles 0, 1 y 2).\n- **Prueba de humo**: `scripts/smoke.sh <url-base>` termina con código 0 solo si (a) el *endpoint* de salud de cada servicio responde 200 y (b) el *spec* `frontend/e2e/smoke.spec.ts` comprueba que una transcripción sintética con una contradicción sembrada produce ≥ 1 hallazgo con sus dos citas en ≤ *N* s (*N* lo fija NFR Requirements) y que un relato coherente produce 0 hallazgos.\n- Las suites AUTONOMIA, de evaluación y de humo son **adicionales** al volumen de la Test Strategy y ningún plan las recorta. Ninguna prueba de los niveles 0 y 1 se reintenta para ocultar un fallo; una prueba inestable se arregla o se pone en cuarentena con un *issue* enlazado. Los umbrales nunca se bajan para que una compuerta pase."
    },
    {
      "layer": "project",
      "text": "- La GPU es opcional: el sistema y las suites de niveles 0 y 1 funcionan completos en CPU; las pruebas que requieren GPU (máquina de hasta 4 GPU y 32 GB de RAM) se agrupan en una etapa separada que corre a demanda. (learned 2026-10-02) \n\n- Los NFR de calidad (IA, MTTV, latencia, cobertura) no se escriben como historias; quedan diferidos a NFR Requirements y Build and Test. (learned 2026-10-02) \n\n- La evaluación de nivel 2 corre desde la anfitriona con kubectl port-forward al juez del clúster en vez de un Job: usa el mismo modelo y digest sin otra imagen, a cambio de depender de un script revisable que el humano ejecuta. (learned 2026-10-03) \n\n- La inyección del Escenario A se mide con una salida reconocible y frente al desacuerdo entre 3 corridas, en vez de exigir el mismo conjunto de hallazgos, porque los modelos comerciales no son deterministas. (learned 2026-11-02)"
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (contrato común del analizador, esquema del hallazgo, mensajes de la cola, perfil de ejecución) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:53ad1a19ebde80b92c68993236b48e0430e0e27607f25a1a825fd763bfb223f6",
  "contract_sha256": "sha256:08361ab4a76370b03282613ef4ad4b553abba374a19a2e9d0eb2205fba02740a"
}
```

**Cómo aplica el orden a U1** (PD-5). Las capas genéricas (base de datos, repositorio, API, frontend) no
existen en una unidad `spec`. Las capas reales son: carga y registro, validación estándar, contratos con
sus *fixtures*, funciones puras, comprobaciones transversales (`checks/`), herramientas y mitad
TypeScript. La nota de GPU del Testing Contract no aplica: no hay GPU (decisión del humano del
2026-11-23) y la suite de U1 corre entera en CPU.

## Comandos de verificación

Todos corren desde la raíz del repositorio, en CPU. Las suites no tienen red; solo los pasos marcados
«con red» la usan (security-design §4.13).

| Clave | Comando | Umbral |
|---|---|---|
| V-INSTALL | `uv sync --frozen --directory contracts` (con red) | Código 0; `uv.lock` con *hashes* coincide |
| V-SUITE | `timeout 60 uv run --frozen --offline --directory contracts pytest` | Verde, ≤ 60 s (meta ≤ 20 s), ≥ 80 % de líneas |
| V-GUARD | `uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/*,src/veridicus_contracts/profiles.py,src/veridicus_contracts/limits.py,src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100` | 100 % de ramas |
| V-TYPES | `uv run --frozen --offline --directory contracts mypy --strict src` | 0 errores |
| V-LINT | `uv run --frozen --offline --directory contracts ruff check .` | 0 hallazgos (reglas `S` incluidas) |
| V-AUDIT | `uv run --frozen --directory contracts pip-audit --format json --output build/pip-audit.json` (con red) y `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.audit_gate build/pip-audit.json --ignore .pip-audit-ignore.yaml` | 0 vulnerabilidades con versión corregida fuera de excepciones vigentes |
| V-GEN | `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check` y `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_jcs_vectors --check` | Sin diferencias |
| V-SURFACE | `timeout 60 uv run --frozen --offline --directory contracts pytest tests/tools/test_security_surface.py --no-cov` | Huella regenerada = archivo versionado |
| V-TS | `npm --prefix contracts/ts ci` (con red), `timeout 60 npm --prefix contracts/ts test`, `npm --prefix contracts/ts run typecheck`, `npm --prefix contracts/ts run lint`, `npm --prefix contracts/ts run gen:check` | Verde, ≤ 60 s, ≥ 80 % de líneas; 0 errores; sin diferencias |
| V-TS-AUDIT | `npm --prefix contracts/ts audit --audit-level=high` (con red) | 0 `HIGH`+ con corrección |
| V-PKG | `timeout 180 uv run --frozen --directory contracts python -m veridicus_contracts.tools.check_package` | Verde, ≤ 180 s |
| V-ERRORS | `uv sync --frozen --directory libs/errors` (con red); `timeout 60 uv run --frozen --offline --directory libs/errors pytest`; `uv run --frozen --offline --directory libs/errors mypy --strict src`; `uv run --frozen --offline --directory libs/errors ruff check .` | Verde, ≥ 80 % de líneas; 0 errores; 0 hallazgos |
| V-YAML | `uv run --frozen --offline --directory contracts yamllint -s ../.github/workflows/contracts-level0.yml ../.pre-commit-config.yaml` | Código 0 (`yamllint` en el grupo de desarrollo de `contracts/`) |

## Pasos

Cada paso nombra lo que cubre, los archivos, lo que queda fuera y su `Verificación:` (AUTONOMIA-02). Las
rutas son relativas a la raíz del repositorio. «Tarea» indica cómo se agrupa en el loop; los pasos de una
misma ola no dependen entre sí.

### Paso 1 — Estructura del paquete y configuración · tarea T01

- [x] `contracts/pyproject.toml`: distribución `veridicus-contracts` con `hatchling` y el mapa de rutas de
  functional-spec §1 con la precisión PD-9 (módulos en `src/veridicus_contracts/`, esquemas y catálogos
  como datos, `*/fixtures/` fuera) (D1, D15); la rueda, construida por `uv build` (sdist → rueda) o por
  `uv build --wheel`, y la instalación editable ven los mismos módulos y datos; dependencias de tech-stack-decisions §3 más `yamllint` en el grupo de desarrollo;
  `uv lock --directory contracts` (con red) genera `uv.lock` con *hashes*, que se versiona.
- [ ] `build/` en `.gitignore`; `tools/audit_gate.py` y el paso de `pip-audit` crean `build/` si falta.
- [x] Configuración en `pyproject.toml`: mypy estricto; Ruff con reglas por defecto + `S` (toda
  supresión `# noqa: S…` con motivo); cobertura con ramas y exclusión declarada solo para `ts/generated/`.
- [x] Directorios del inventario: `api/`, `errors/`, `queues/`, `analyzer/v1/`, `integrity/`, `ui/`,
  `profiles/`, `model_calls/`, `cli/`, `metrics/`, `health/`, `format/`, `transcript/`,
  `vendor/`, `fixtures/`, `src/veridicus_contracts/{checks,tools}/`, `tests/`; `py.typed`.
- [x] Fuera de `contracts/`: `.gitattributes` con `contracts/** text eol=lf` (NFRD-U1-13); `.gitignore`
  con `.env`, `*.pem`, `*.key`, `kubeconfig*`, `secrets*.yaml`, `.worktrees/` y `build/` si faltan.
- Cubre: D1, D15, BR12.1; NFR13.2. Fuera: código de contratos y pruebas.
- Verificación: `uv lock --check --directory contracts` → código 0, y `uv sync --frozen --directory contracts`
  → código 0.

### Paso 2 — Ejecutor de pruebas listo (antes de la primera prueba) · tarea T01

- [x] `pytest` en `pyproject.toml`: `testpaths = ["tests"]`, `addopts` con `--disable-socket
  --cov=veridicus_contracts --cov-branch --cov-fail-under=80` (D6, D7); perfil de Hypothesis determinista
  (`derandomize = true`, sin `deadline`).
- [x] `tests/conftest.py` (rutas al árbol `contracts/`) y `tests/test_runner.py`: abrir un *socket* lanza
  `SocketBlockedError`; el árbol se resuelve.
- Cubre: NFR2.1, NFR10.5. Fuera: F7 en `pytest_sessionstart` (paso 6).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_runner.py --no-cov`
  → 2 pruebas en verde. Es el comando por unidad de `unit-test-instructions.md`.

### Paso 3 — Carga, registro y huella JCS (implementar y probar) · tarea T02

- [x] `src/veridicus_contracts/loaders.py`: único punto que crea `ruamel.yaml.YAML(typ="safe",
  pure=True)` con `allow_duplicate_keys = False` y YAML 1.2; lectura de JSON (D5, §4.1).
- [x] `src/veridicus_contracts/registry.py`: registro `referencing` que recorre los esquemas presentes bajo `contracts/`
  (incluido `vendor/` cuando el paso 4 lo cree) bajo `https://veridicus.invalid/` + `$id`; recuperación
  que lanza error ante cualquier URI ajena (§4.2, BR12.3, FD-U1-11). Las pruebas de este paso usan
  esquemas mínimos en `tests/data/`.
- [x] `src/veridicus_contracts/canonical.py`: `sha256_jcs(obj)` sobre `rfc8785` (D14).
- [x] Pruebas (5–8 por módulo; 100 % de ramas en `registry` y `canonical`): YAML válido; clave duplicada
  rechazada; `!!python/object` rechazado; `no`/`on` como texto; `$ref` canónico resuelto; forma antigua
  `contracts/analyzer/v1/salida.schema.json#/$defs/cita` no resuelta (E36); `https://` rechazado sin red;
  vectores JCS límite (`1e21`, `-0`, `5e-324`, `0.1`).
- Cubre: BR4.3, BR12.3; NFR10.4, NFR10.5, NFR10.15; D2, D5, D14. Fuera: comprobación AST de uso (paso 19).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py --no-cov`
  → verde.

### Paso 4 — Validación estándar y meta-esquemas (implementar y probar) · tarea T02

- [x] `contracts/vendor/`: meta-esquemas empaquetados de AsyncAPI 3.0.0, JSON Schema 2020-12 y OpenAPI
  3.1, con `vendor/SHA256SUMS` (D4, NFR10.9).
- [x] `src/veridicus_contracts/validators.py`: OpenAPI 3.1 con `openapi-spec-validator` (D3); AsyncAPI
  3.0 contra `vendor/` y extracción de la carga de cada mensaje (D4); JSON Schema 2020-12 estricto (palabra
  clave desconocida = error, BR1.9) con formatos `uuid` y `date-time` (D2).
- [x] `tests/test_validators.py` (7 pruebas): `vendor/` = `SHA256SUMS`; meta-esquema alterado falla;
  OpenAPI y AsyncAPI mínimos válido e inválido; carga extraída; palabra clave desconocida rechazada.
- Cubre: BR1.9; D2–D4; NFR10.9. Fuera: reglas propias de `checks/`.
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_validators.py --no-cov`
  → verde.

### Paso 5 — ROJO: contratos de datos y guardias AUTONOMIA-03/04/05 · tarea T03

Se escriben **antes** de cualquier contrato y se corren en rojo (Testing Contract, PD-5).

- [x] Formato de *fixture* (§4.10): YAML o JSON con `fixture_id`, `contract`, `synthetic: true`,
  `expectation: accept|reject`, `reject_reason` (ID de regla, obligatorio en `reject`), `mentions` y
  `payload`. Catálogo `contracts/fixtures/synthetic-names.yaml` con nombres y lugares inventados.
- [x] *Fixtures* de datos, uno por escenario como mínimo:
  - C6 `analyzer/v1/fixtures/`: salida válida; E5 `estado: error` con un hallazgo (BR3.6); E7
    `is_truthful` en un hallazgo (BR3.1, BR3.3); E8 `tipo: falso` (BR3.2); hallazgo sin cada uno de
    `hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones` (BR3.1); E19 `origen: corpus` sin consentimiento
    y `origen: sintetico` sin él (BR3.5); E20 `requiere_mandato: true` sin `constancia_mandato` (BR3.5);
    `anonimizador_no_disponible` e `incidente_anonimizacion` válidos (CD-01).
  - C2 `queues/fixtures/runs/`: válido; E1 sin `entrada` (BR2.1); E2 mayor desconocido (BR1.2); E3 menor con
    campo nuevo, aceptado (BR1.3); fallido con un campo `text`, rechazado (NFRD-U1-07).
  - C3 `queues/fixtures/results/`: válido; `salida` que no cumple C6 (BR2.3); fallido con texto.
  - C5 `queues/fixtures/speech/`: válido; obligatorio ausente; mayor desconocido; fallido con texto.
  - C7 `integrity/fixtures/review-suggestion/`: válido; E9 sin cada uno de los 5 campos y con cada uno
    vacío (BR4.1); con `is_truthful` (BR4.2); E35 una por condición de BR4.4.
  - C18 `profiles/fixtures/`: `effective-config.valid.json` con su huella JCS; perfil del analizador con
    un papel extra (E22, BR9.3).
  - C19 `cli/fixtures/`: válido; E28 papel `prueba_a` (BR10.2); E29 frase en `model` y en
    `price_table_version` (BR10.1).
  - C21 `api/fixtures/anonymizer-proxy/`: válido; con `destination`; con `api_key_ref` (NFR1.3).
- [x] `tests/contracts/test_analyzer_copy.py`, `test_queue_messages.py`, `test_review_suggestion.py`,
  `test_profiles_contract.py`, `test_cli_report.py`, `test_anonymizer_proxy.py`, `test_model_call.py`:
  cargan cada *fixture*, validan contra su contrato y exigen aceptar o rechazar **por su**
  `reject_reason` (NFR10.10, F1).
- [x] `tests/helpers.py`: `load_contract(path)` convierte un contrato ausente en `pytest.fail("contrato
  ausente: <ruta>")`, para que el rojo sea un fallo y no un error; marcadores por contrato de PD-8
  registrados en `pyproject.toml` (`--strict-markers`).
- [x] `tests/guards/test_autonomia_03.py`: ningún nombre de propiedad, parámetro, enum o rótulo con un
  término de C8 o de `categories_forbidden_in_schemas` (BR3.3); enum de C6 iguales en C1, C7 y C19
  (BR3.2); C8 con exactamente sus 9 términos (BR5.1); exactamente nueve rótulos (BR6.1–BR6.3); 0
  operaciones de C1 que escriban perfiles, proveedores, *prompts*, precios o límites, con control E15
  (`PUT /profiles`) (BR7.1, AC8.3.1); C7 con quién y cuándo (BR4.4).
- [x] `tests/guards/test_autonomia_04.py`: `servers` internos en C1, C16, C21, ruta interna de voz y
  AsyncAPI, con control de C21 con `https://api.openai.com` (NFR1.1); `AnonymizingProvider` con un solo
  `generate` (BR9.9, NFR1.2); C21 estricto (NFR1.3); C19 sin texto libre (NFR1.4).
- [x] `tests/guards/test_autonomia_05.py`: C6 rechaza el hallazgo sin cada campo obligatorio y la salida
  `error` con hallazgos (BR3.1, BR3.6); C7 rechaza los *fixtures* de E9; F7 detecta E18 (BR1.7).
- [x] Correr y guardar la salida en rojo en la bitácora de la tarea.
- Cubre: definición de terminado 2–5 de B1; AC3.2.1, AC3.6.2, AC5.5.3, AC8.3.1, AC12.6.1, AC13.3.1,
  AC15.4.7; BR1.2, BR1.3, BR1.7, BR2.1, BR2.3, BR3.1–BR3.6, BR4.1–BR4.4, BR5.1, BR6.1–BR6.3, BR7.1,
  BR9.3, BR9.9, BR10.1, BR10.2; NFR1.1–NFR1.4, NFR10.2, NFR10.8, NFR10.10, NFR11.3–NFR11.5. Fuera:
  cualquier contrato.
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --co -q --no-cov`
  → código 0 (0 errores de recolección); y `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --no-cov --junitxml=build/red.xml`
  → código 1 (fallos, no errores); y `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.check_red build/red.xml`
  → código 0 solo si `errors="0"` y `failures` > 0 (herramienta pequeña de este paso, R-14 de la
  revisión 2).

### Paso 6 — Copia del contrato común C6 y F7 (verde) · tarea T04, con parada humana

- [x] **El humano** copia `entrada.schema.json` y `salida.schema.json` desde
  `/insumos/app/contratos/analizador/v1/` a `contracts/analyzer/v1/` y escribe `SHA256SUMS` (dos líneas)
  con las huellas que recalcula allí con `sha256sum`; anota origen y huellas en la descripción del PR de
  la tarea (PD-4, BR1.8). El agente no edita esos archivos.
- [x] `tests/conftest.py`: F7 en `pytest_sessionstart` — `SHA256SUMS` de exactamente dos líneas, SHA-256
  de bytes igual, `contrato: { const: "1.0.0" }` en los dos; si falla, aborta la sesión con el mensaje de
  F7 paso 4 (§4.19).
- [x] Prueba E18: copia en memoria de `salida.schema.json` con un byte cambiado en una `description` →
  F7 en rojo.
- Cubre: definición de terminado 2 y 4 de B1; BR1.7, BR1.8, BR3.1–BR3.6; NFR11.4. Fuera: editar C6.
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_analyzer_copy.py tests/guards/test_autonomia_05.py -m c6 --no-cov`
  → verde. Las pruebas de C7 de `test_autonomia_05.py` pasan a verde en el paso 8 (PD-8).

### Paso 7 — Mensajes de cola C2, C3 y C5 v2 (verde) · tarea T05 (ola con T06)

- [x] `contracts/queues/runs.v2.yaml` (C2), `results.v2.yaml` (C3), `speech.v2.yaml` (C5,
  `x-veridicus-priority: SHOULD`) en AsyncAPI 3.0: sobre con `schema_version`, `message_id`,
  `attempt ≥ 1`; `entrada` y `salida` por `$ref` canónico a la copia de C6; `effective_config` contra C18;
  `audio_base64` con `x-veridicus-limit: audio_base64_max_chars`; `servers` internos. Sin el umbral ni las
  calificaciones retiradas (BR2.2, BR2.4, BR2.5 «Retirado»). `queues/indexing.v1.yaml` (C4) **no** se
  entrega. Las marcas `x-veridicus-limit` se comprueban contra C25 en el paso 16 (PD-8).
- [x] Los *fixtures* y `tests/contracts/test_queue_messages.py` ya existen (paso 5); este paso solo
  escribe los contratos.
- [x] Entradas de `<cola>:failed` con esquema estricto: solo `message_id`, ID de la corrida o del audio,
  `attempt` y `code` (NFRD-U1-07, NFR-U4-07, NFR-U9-03).
- Cubre: C2, C3, C5; BR1.1–BR1.3, BR2.1, BR2.3; NFR10.2. Fuera: lógica de productores y consumidores (U4,
  U9).
- [x] `contracts/profiles/effective-config.v1.yaml` (C18, estricto), que C2 referencia; la huella de
  `effective-config.valid.json` es su `sha256_jcs` (BR9.7). Se adelanta desde el paso 11 (E-5).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_queue_messages.py --no-cov`
  → verde, incluido el caso `c18` de C2.

### Paso 8 — Sugerencia de revisión C7 v2 (verde) · tarea T06 (ola con T05)

- [x] `contracts/integrity/review-suggestion.v2.json`: JSON Schema 2020-12 estricto, `$id` versionado;
  `hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones` obligatorios y no vacíos; citas por `$ref` canónico
  a `/veridicus/contracts/analyzer/v1/salida#/$defs/cita` (BR4.3); estados `pending`, `accepted`,
  `edited`, `dismissed` con las cuatro condiciones `if/then` de FD-U1-13 (BR4.4).
- [x] `src/veridicus_contracts/checks/suggestion_conditions.py` (módulo guardia): C7 declara las cuatro
  condiciones y hay un *fixture* negativo por cada una (§4.8, NFR11.5); 5–8 pruebas, 100 % de ramas.
- Cubre: C7; AC5.5.3; BR4.1–BR4.4; NFR11.5; AUTONOMIA-03 (quién y cuándo). Fuera: máquina de estados en
  ejecución (U5).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_review_suggestion.py tests/checks/test_suggestion_conditions.py --no-cov`
  → verde, y `timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_05.py --no-cov`
  → verde (todo el archivo, C6 y C7).

### Paso 9 — Catálogo de errores v2 y excepciones de `libs/errors/` · tarea T07

- [x] `contracts/errors/error-codes.v2.yaml`: por `code`, un solo `status`, `class`, unidad dueña y
  `http: true|false`; `limits.exceeded` = `413` (D16); arranque y log con `http: false`
  (`config.invalid_profile`, `config.invalid_limit`, `run.publish_failed`); los `code` de NFR10.3 y de
  contract-summary revisión 3, incluidos `session.blocked` (CD-11), `route.not_found` (`404`,
  NFRD-U3-10), `report.view_outdated` (`409`, NFRD-U7-04), `import.invalid_type` y
  `research.invalid_type` (`415`); tabla `error.codigo` de C6 → `code` uno a uno, con
  `proveedor` → `analysis.provider` (BR3.4, E34).
- [x] `libs/errors/` (PD-7): distribución `veridicus-errors` con `pyproject.toml` (hatchling, Python 3.12,
  mypy estricto, Ruff con `S`, `pytest-cov` al 80 %), `uv.lock` generado con `uv lock --directory
  libs/errors`, `src/veridicus_errors/` con una clase sin lógica por `code` (atributo de clase `code`)
  y su jerarquía (BR7.4), y `tests/` con 5–8 pruebas (jerarquía, `code` único, `status` no expuesto en
  la clase). El manejador que traduce a Problem Details es de cada servicio.
- [x] `src/veridicus_contracts/checks/error_codes.py` (módulo guardia, §4.7 a–e; la parte de C1 se
  completa en el paso 16): catálogo y clases uno a uno leyendo `libs/errors/src/` con `ast`, sin importar
  (E31, E44); tabla de C6 completa (E34).
- [x] `tests/checks/test_error_codes.py` y `tests/test_errors_catalog.py` (forma del catálogo, un
  `status` por `code`, `limits.exceeded` = 413, `http: false` en los de arranque).
- Cubre: definición de terminado 4 de B1; BR3.4, BR7.2, BR7.4; NFR10.3. Fuera: `ErrorCode` de C1 (paso
  16).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_error_codes.py tests/test_errors_catalog.py --no-cov`
  → verde, y V-ERRORS → verde, 0 errores, 0 hallazgos.

### Paso 10 — Tipos de llamadas a modelos y puerta única (implementar y probar) · tarea T08

- [x] `contracts/src/veridicus_contracts/model_calls.py`: tipos de C13 con `Role` como `str` con patrón
  `^[a-z][a-z0-9_]{0,31}$` (FD-U1-01, BR9.1); `GenerateRequest`, `GenerateResult`, `ModelCall`;
  `ModelCallError` y sus cinco subclases (`ContentBlocked`, `Timeout`, `ProviderError` e `InvalidOutput`
  con `call: ModelCall`; `AnonymizerUnavailable` sin él); `Protocol` `AnonymizingProvider` con solo
  `generate(self, request: GenerateRequest) -> GenerateResult`, sin importar nada fuera de
  `veridicus_contracts`, `typing`, `dataclasses`, `enum` y `datetime` (BR9.9, revisión 3 de C13).
- [x] `contracts/model_calls/model-call.v1.yaml` (estricto, `role` con patrón) y `role-translation.v1.yaml`
  (solo los tres papeles del analizador a `registro.llamadas` de C6, BR9.6).
- [x] `src/veridicus_contracts/checks/protocol_surface.py` (módulo guardia, §4.17) y `tests/typing/`: doble
  con solo `generate` → 0 errores de `mypy.api.run --strict`; doble sin él → el error esperado (E42);
  `check_ready()` en el `Protocol` o una importación ajena → rojo (E43); E27 (`role: "Prueba A"`).
- [x] `tests/typing/test_anonymizing_provider.py` y `tests/checks/test_protocol_surface.py` (5–8 pruebas);
  `tests/contracts/test_model_call.py` ya existe (paso 5).
- Cubre: definición de terminado 6 de B1; C13 (tipos); BR9.1, BR9.6, BR9.9; NFR1.2. Fuera: el
  ModelGateway y los adaptadores (U11, U10).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/typing tests/checks/test_protocol_surface.py tests/contracts/test_model_call.py --no-cov`
  → verde, y `uv run --frozen --offline --directory contracts mypy --strict src` → 0 errores.

### Paso 11 — Perfiles, configuración efectiva y `profiles.validate` (implementar y probar) · tarea T09

- [x] `contracts/profiles/profile-base.schema.v1.yaml` (abierto: al menos un papel, `role_aliases`, un
  `fallback_provider`, `api_key_ref` con `^[A-Z][A-Z0-9_]{2,63}$`, `purpose` con patrón) y
  `profiles.schema.v1.yaml` (especialización del analizador cerrada con `unevaluatedProperties: false`:
  exactamente `judge` y `verifier`, alias `verifier_permuted → verifier`, `purpose` en su enum)
  (FD-U1-02, FD-U1-12, BR9.2–BR9.5).
- [x] `contracts/profiles/prices.schema.v1.yaml` (C18, estricto). `effective-config.v1.yaml` ya lo
  escribió el paso 7 (E-5).
- [x] `contracts/src/veridicus_contracts/profiles.py`: `validate(data, *, key_prefix, kind)` sin E/S — sobre
  (`schema_version: 1.0.0`, nombres `^[a-z0-9-]{1,48}$`), referencias cruzadas de alias, prefijo de
  `api_key_ref` y especialización con `kind: analyzer`; `ProfileValidationError`
  (`config.invalid_profile`) que nombra perfil, papel y ajuste, nunca su valor (F8, BR9.8, §4.15).
- [x] Pruebas (módulo guardia, 100 % de ramas): E21–E26, E38, E39; pureza con `open`, `os.environ` y
  `socket.socket` sustituidos; *canary* en `api_key_ref` ausente de todo mensaje.
- Cubre: C18; AC13.3.1; BR9.2–BR9.5, BR9.7, BR9.8; NFR10.13, NFR10.15. Fuera: claves presentes y
  anonimizador obligatorio (U11).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_profiles.py tests/contracts/test_profiles_contract.py --no-cov`
  → verde.

### Paso 12 — Catálogo de límites C25 y `limits.load` (implementar y probar) · tarea T10

- [x] `contracts/limits.v1.yaml`: las cifras de security-design §5 más `transcript_body_max_bytes`
  (1 004 096) e `import_body_max_bytes` (2 113 536) con `import_file_max_bytes` < `import_body_max_bytes`
  (NFRD-U6-01), `cursor_max_chars` (128, U4, NFRD-U7-04), `voice_body_max_bytes` (6 016 384,
  NFRD-U9-03) y `research_report_read_timeout_s` (30, NFRD-U12-02); cada entrada con `value`, `unit` de la
  lista cerrada, `owner`, `used_in` y `derived_from` opcional; sección `relations` (§4.4, NFRD-U1-01,
  NFRD-U1-02).
- [x] `contracts/src/veridicus_contracts/limits.py`: `load(environ)` lee el catálogo empaquetado una vez y aplica
  `VERIDICUS_LIMIT_<NOMBRE>` solo para bajar; rechaza subir, nombre inexistente, variable
  `VERIDICUS_LIMIT_*` desconocida, valor inválido para su unidad y relación rota con `LimitsConfigError`
  (`config.invalid_limit`) (BR11.1, §4.15, NFRD-U1-09).
- [x] `src/veridicus_contracts/checks/limits_catalog.py` (módulo guardia): forma, tipos (entero salvo
  `ratio` y `s`), derivadas (`audio_base64_max_chars` = 8 000 000) y relaciones. Pruebas con E33 y E37.
- Cubre: C25; BR11.1; NFR10.14; DS1. Fuera: marcas `x-veridicus-limit` en C1 (paso 16).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov`
  → verde.

### Paso 13 — Vocabulario, aviso, casos de escaneo y rótulos (implementar y probar) · tarea T11

- [x] `contracts/integrity/forbidden-vocabulary.v2.yaml` (C8): los 9 términos, `match` (palabra completa,
  sin mayúsculas ni tildes), `excluded_spans` con `quote_delimiters: [«, »]` sobre `hecho`,
  `observaciones` y `tema`, exclusiones enteras de BR5.5 y `categories_forbidden_in_schemas`.
- [x] `integrity/neutral-clarification.v1.yaml` (VE-05, BR5.6), `integrity/notice.v1.yaml` (VE-01, frase
  base y versión, BR5.7), `integrity/scan-cases.v1.yaml` (E10–E14, E30 y un caso por término y por frase,
  con sus `literal_sources`, BR5.8, PD-6) e `integrity/testimony-warning-cases.v1.yaml` con
  `whitespace_code_points` y los casos U+00A0, U+3000, U+FEFF, tabulador y salto de línea (NFR-U13-10,
  NFRD-U13-13).
- [x] `contracts/ui/result-labels.v2.yaml`: «Sugerencia de revisión», «Contradicción en el relato» y los 7
  de tipo «Fecha», «Número», «Lugar», «Persona», «Negación», «Secuencia», «Otro» (FD-U1-08, BR6.1–BR6.3).
- [x] `src/veridicus_contracts/checks/veracity.py` y `checks/scan_cases.py` (módulos guardia, §4.8): BR3.2,
  BR3.3, BR5.1, BR6.1–BR6.3 sobre todos los documentos; forma de los casos y uno por término y por frase
  (E40); E17 (décimo rótulo) en rojo.
- Cubre: C8; AC3.2.4, AC5.5.4; BR5.1–BR5.8, BR6.1–BR6.3; NFR11.3. Fuera: ejecutar el escáner (U11).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_veracity.py tests/checks/test_scan_cases.py --no-cov`
  → verde, y `timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_03.py -m "c8 or labels" --no-cov`
  → verde. Las pruebas `c1` de `test_autonomia_03.py` pasan a verde en el paso 16 (PD-8).

### Paso 14 — Reporte de la CLI C19 v2 (verde) · tarea T12 (ola con T13)

- [x] `contracts/cli/report.schema.v2.yaml` con `model-call.v1.yaml`: toda cadena `enum`, `const` o patrón
  portátil sin espacios con `maxLength: 128` y `x-veridicus-limit: report_token_max_chars`; enteros con
  `minimum` y `maximum` (0..2^53 − 1, `seed` también negativo, `estimated_cost` ≤ 10^9); `origin`,
  `blocking`, latencia p50 y p95 por papel en ms enteros, sección opcional `clarifications` solo con
  enteros; `allOf` que restringe las llamadas a los tres papeles del analizador (§4.18, NFRD-U1-06,
  FD-U1-03).
- [x] `src/veridicus_contracts/checks/report_closed.py` (módulo guardia): E28, E29; límite declarado del
  *canary* de una palabra (FD-U1-05, lo cierra U12). `report_token_max_chars` se compara con C25 en el
  paso 16 (PD-8).
- Cubre: definición de terminado 5 de B1; C19; AC12.6.1 (parte de U1); BR10.1, BR10.2; NFR1.4, NFR12.3.
  Fuera: ingesta y persistencia (U12).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_cli_report.py tests/checks/test_report_closed.py --no-cov`
  → verde.

### Paso 15 — C21, ruta interna de voz, salud C16 y soberanía (verde) · tarea T13 (ola con T12)

- [x] `contracts/api/anonymizer-proxy.v1.yaml` (C21): petición y respuesta estrictas en todos los niveles,
  `role` con patrón, `profile_sha256` `^[0-9a-f]{64}$`, `x-veridicus-max-bytes` de petición y respuesta,
  `servers` internos (§4.17, NFRD-U1-04).
- [x] `contracts/api/speech-internal.v1.yaml`: `POST /internal/v1/speech` con `bearerAuth`, cuerpo
  estricto, `401`, `422` con `rule_id` cerrado, `503` y `audio/wav` con
  `x-veridicus-max-bytes: speech_audio_max_bytes` (NFRD-U1-08).
- [x] `contracts/health/health.v2.yaml` (C16): `/healthz` y `/readyz` públicas dentro del clúster.
- [x] `src/veridicus_contracts/checks/servers.py` (módulo guardia, §4.9): ruta relativa, nombre corto
  `http://veridicus-<nombre>:<puerto>` o `*.svc.cluster.local`, siempre `http`; control de C21 con
  `https://api.openai.com`.
- Cubre: C16, C21; NFR1.1, NFR1.3; AUTONOMIA-04. Fuera: el proxy (U10) y `audio-worker` (U9).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_anonymizer_proxy.py tests/checks/test_servers.py --no-cov`
  → verde, y `timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_04.py -m "not c1 and not c19" --no-cov`
  → verde. Las pruebas `c19` de `test_autonomia_04.py` las pone en verde el paso 14 (T12, misma ola; E-6) y las `c1`, el paso 16 (PD-8).

### Paso 16 — OpenAPI de la consola C1 v2 y sus comprobaciones (implementar y probar) · tareas T14 y T15

- [x] T14 — `contracts/api/console.v2.yaml` (C1) en OpenAPI 3.1, desde contract-summary §C1 revisión 3 más
  PD-1 y PD-2: `ErrorCode` igual al catálogo; `CsrfToken` (`minLength: 32`); `x-veridicus-roles` en toda
  operación salvo `/auth/login`, `/auth/logout`, `/auth/me` y la lista pública (NFRD-U1-12); extensiones
  cerradas de §4.6; `x-veridicus-limit` y `x-veridicus-max-bytes` iguales a C25; `413 limits.exceeded` y
  `415` donde corresponde; `Retry-After` en el `503` de login (NFRD-U3-10); `{ expected_cursor }` en
  `POST /sessions/{session_id}/reports` (NFRD-U7-04); tope y `413` en la decisión (NFRD-U8-05);
  respuestas de NFR-U5-05, NFR-U7-02, NFR-U12-02 y NFR-U13-03; `x-veridicus-cookie` en `sessionCookie`;
  fechas con el formato único. Si dos precisiones chocan, el paso se detiene y lo anota en el PR.
- [x] T15 — módulos guardia, uno por regla: `checks/auth_surface.py` (§4.6, con la constante de seis
  `operationId` que encolan), `checks/strict_bodies.py` (§4.3), `checks/config_write.py` (§4.8, BR7.1,
  con la excepción `profile_name`; `checks/threshold.py` queda «Retirado»), `checks/limits_match.py`
  (§4.4, comprobación en los dos sentidos) y la parte de C1 de `checks/error_codes.py`; 5–8 pruebas por
  módulo con los controles negativos de §4.3, §4.6 y §4.7 (ruta pública nueva, escritura sin anti-CSRF,
  operación sin roles, DELETE, `200` en una operación que encola, cuerpo sin estrictez, límite distinto
  del catálogo, límite huérfano, `409` sin `Problem`, `code` fuera del catálogo, E15, E44).
- Cubre: C1; AC8.3.1, AC8.3.3; BR7.1–BR7.4; NFR3.1, NFR10.1, NFR10.3, NFR10.7, NFR10.8, NFR10.11,
  NFR10.12, NFR11.1. Fuera: implementación de rutas (U3–U13); PD-3.
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks tests/guards tests/contracts --no-cov`
  → verde, sin filtros de marcador (las pruebas `c1` y `limits_match` de los pasos 5, 7, 13, 14 y 15
  pasan a verde aquí).

### Paso 17 — Interfaces en proceso C10–C12, C23 y C24 (implementar y probar) · tarea T16

- [x] `contracts/src/veridicus_contracts/human_review.py` (C10), `report_ports.py` (C11), `identity.py` (C12),
  `access_log.py` (C23) y `retention.py` (C24 v1.1.0 con `Purgeable.count_session(uow, session_id) ->
  Mapping[str, int]`, NFRD-U13-08) como `Protocol` tipados con su versión en el encabezado y las firmas de
  contract-summary revisión 3 y de las precisiones aprobadas (p. ej. `open_round(..., for_update=False)`,
  `discard_correction_round`).
- [x] `tests/typing/test_protocols.py` (5–8 pruebas): un *fake* mínimo de cada interfaz pasa mypy estricto
  y uno con firma distinta falla.
- Cubre: C10–C12, C23, C24; NFR13.2. Fuera: implementaciones (U4, U5, U7, U13).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/typing/test_protocols.py --no-cov`
  → verde, y `uv run --frozen --offline --directory contracts mypy --strict src` → 0 errores.

### Paso 18 — Métricas, formato de fecha y nombres (implementar y probar) · tarea T17

- [x] `contracts/metrics/review.v2.yaml` (C15, de U5) y `metrics/text-flow.v1.yaml`,
  `session-lifecycle.v1.yaml`, `assistant-extras.v1.yaml`, `voice.v1.yaml`, `anonymizer.v1.yaml` con los
  nombres y valores de NFRD-U4-08, NFRD-U6-12, NFRD-U8-06, NFRD-U9-10 y NFRD-U10-02 (DS7, NFRD-U1-05).
- [x] `contracts/format/datetime.v1.yaml` (`AAAA-MM-DDTHH:MM:SSZ`, BR8.1).
- [x] Módulos guardia `checks/metrics.py` (prefijo, unicidad entre archivos, etiquetas de la lista
  cerrada con `values`, `error_code` del catálogo, `session_id` con patrón UUID), `checks/datetime_format.py`
  (E16; la copia de C6 no se toca) y `checks/naming.py` (ASCII `snake_case` salvo los bloques de C6 de la
  regla 8, `code` en `dominio.motivo`), con 5–7 pruebas cada uno.
- Cubre: C15; BR8.1, BR8.2; NFR11.2, NFR14.1, NFR15.1. Fuera: emitir métricas (servicios).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_metrics.py tests/checks/test_datetime_format.py tests/checks/test_naming.py --no-cov`
  → verde.

### Paso 19 — Integridad de la suite (implementar y probar) · tarea T18

- [x] Módulos guardia: `checks/loader_usage.py` (§4.1 y §4.2: PyYAML, `YAML(...)` fuera de `loaders.py`,
  `typ` distinto de `"safe"`, `load_all`, `Loader=`, `subprocess`/`multiprocessing`/`os.system` en
  `checks/`, `tests/` o los módulos de `src/veridicus_contracts/`; publicada como `scan(paths)`), `checks/refs.py` (§4.2, E36),
  `checks/redos.py` (§4.5: recorrido completo, subconjunto portátil, entrada acotada, Hypothesis con techo
  de 1 s y prueba de versión 3.12), `checks/synthetic.py` (§4.10, publicada como `scan(paths)`),
  `checks/fixture_coverage.py` (§4.10) y `checks/ci_workflows.py` (§4.11: ningún *workflow* con
  `--write`, `kubectl apply`, `helm install|upgrade` ni credenciales del clúster; AUTONOMIA-01).
- [x] Prueba AST de E32: ningún módulo importa `contracts.` como nombre de primer nivel (BR12.1).
- [x] 5–8 pruebas por módulo con los controles de §4.1, §4.2, §4.5, §4.10 y §4.11.
- Cubre: BR1.6, BR12.1; NFR10.4–NFR10.6, NFR10.10, NFR12.1; AUTONOMIA-01. Fuera: *workflow* (paso 24).
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_loader_usage.py tests/checks/test_refs.py tests/checks/test_redos.py tests/checks/test_synthetic.py tests/checks/test_fixture_coverage.py tests/checks/test_ci_workflows.py --no-cov`
  → verde.

### Paso 20 — Herramientas deterministas (implementar y probar) · tarea T19

- [x] `tools/security_surface.py` (§4.11, DS3) con `--write` explícito; `contracts/security-surface.json`;
  `.github/pull_request_template.md` con el apartado que justifica su cambio (NFRD-U1-13).
- [x] `tools/gen_ts.py` (D9): constantes `as const` del catálogo de `code`, rótulos, C8 y listas de §4.6 en
  `contracts/ts/generated/` (crea la carpeta si falta; T20 la consume después); `--check`.
- [x] `tools/gen_jcs_vectors.py` (§4.14): `contracts/fixtures/jcs-vectors.json` con 200 vectores de semilla
  fija; `--check`.
- [x] `tools/audit_gate.py` y `contracts/.pip-audit-ignore.yaml` (NFRD-U1-11): excepción vencida = fallo.
- [x] Pruebas (5 por herramienta): regenerada = versionada; idempotencia en bytes; cambios de seguridad
  visibles en la huella; `--check` en rojo tras un cambio; plantilla de PR presente.
- Cubre: DS3, DS6, DS8; D9; NFR10.9, NFR10.15. Fuera: la CI nunca ejecuta `--write`.
- Verificación: V-SURFACE, V-GEN, y `timeout 60 uv run --frozen --offline --directory contracts pytest tests/tools --no-cov`
  → verde.

### Paso 21 — Mitad TypeScript `contracts/ts/` (implementar y probar) · tarea T20

- [x] `contracts/ts/` (D13): `package.json` con Node 22 en `engines`, `.nvmrc`, `package-lock.json`
  generado con `npm --prefix contracts/ts install` (con red) y versionado, script `gen:check` que corre
  `gen_ts --check` y `openapi-typescript` sin escribir,
  `tsconfig.json` estricto, ESLint con `no-restricted-imports` para `yaml`, `vitest.config.ts` con
  cobertura v8 al 80 % y *setup* sin red (§4.14).
- [x] `src/loaders.ts` (`yaml` con `uniqueKeys: true`), `src/registry.ts` (`Ajv2020` `strict`,
  `ajv-formats`, `addSchema` con base `https://veridicus.invalid/`, `addKeyword` solo con las extensiones
  de §4.6), `src/canonical.ts` (`canonicalize`); tipos de C1 con `openapi-typescript` en `generated/`.
- [x] Pruebas Vitest: mismos *fixtures* que Python comparados con su `expectation` (NFR10.16); vectores JCS
  y huella de `effective-config.valid.json`; control de `fetch` bloqueado; C8 con término repetido
  rechazado.
- Cubre: NFR2.1, NFR10.4, NFR10.15, NFR10.16; D9, D13. Fuera: la consola (U4).
- Verificación: V-TS → verde, ≤ 60 s, ≥ 80 % de líneas, 0 errores, sin diferencias.

### Paso 22 — Paquete en entorno limpio (implementar y probar) · tarea T21

- [x] `tools/check_package.py` (§4.16, F9): `uv build`; lista de la rueda contra la tabla de rutas (falla
  si falta un dato o aparece `fixtures/`, `tests/`, `.env*`, `*.pem`, `*.key`); `uv venv` limpio; guion con
  `python -I` y `socket.socket` bloqueado que importa `veridicus_contracts`, lee cada dato con
  `importlib.resources` y valida sin red los *fixtures* de C7, C1 y C19 (BR12.3).
- Cubre: BR12.1, BR12.3; NFR2.2. Fuera: la etiqueta (paso 25).
- Verificación: V-PKG → verde, ≤ 180 s.

### Paso 23 — Suite completa y compuertas de calidad · tarea T22

- [ ] Correr todo. Ningún umbral se baja para que pase; un hueco se informa en el PR.
- Cubre: NFR2.1, NFR2.2, NFR10.9, NFR13.1, NFR13.2.
- Verificación: V-SUITE (verde, ≤ 60 s, ≥ 80 %), V-GUARD (100 %), V-TYPES (0), V-LINT (0), V-AUDIT,
  V-GEN, V-SURFACE, V-TS, V-TS-AUDIT, V-PKG y V-ERRORS.

### Paso 24 — CI y ganchos locales · tarea T22

- [ ] `.github/workflows/contracts-level0.yml`: *job* `contracts-level0` con los 12 pasos de §4.13 en orden,
  `permissions: contents: read`, acciones fijadas por SHA, sin `kubeconfig` ni credenciales del clúster, y
  `gitleaks` sobre el repositorio (NFR12.2); más un *job* hermano `errors-level0` con V-ERRORS, extensión
  de §4.13 por PD-7 que se anota en el PR (R-13 de la revisión 2).
- [ ] `.pre-commit-config.yaml` en la raíz con `gitleaks`, Ruff y `yamllint`.
- [ ] Pedir en el PR del Bolt que `contracts-level0` sea comprobación obligatoria de `main` (lo aplica el
  humano en GitHub).
- Cubre: NFR10.9, NFR12.2; AUTONOMIA-01, AUTONOMIA-02.
- Verificación: V-YAML → código 0, y
  `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov`
  → verde. Evidencia del PR (no criterio del paso): el *job* `contracts-level0` en verde, con enlace.
  `gitleaks` corre en CI con la acción fijada por SHA y en el gancho de `pre-commit`, que lo instala.

### Paso 25 — Documentación, glosario y etiqueta · tarea T23

- [ ] `contracts/README.md` en español: inventario, cómo cambiar un contrato (F5) y la copia de C6 (F7),
  cómo usar `limits.load`, `profiles.validate` y `registry` desde un servicio, y los comandos V-*.
- [ ] Glosario de identificadores en `contracts/README.md` con `cancel_token` y `view_outdated`
  (NFRD-U7-11), `review_report`, `review_suggestion`, `undocumented_fact` (team.md, Code Style).
- [ ] Docstrings en español en `loaders`, `validators`, cada función pura y cada módulo de `checks/` (regla
  que protege).
- [ ] `tests/test_readme.py`: el README existe y su glosario contiene `cancel_token`, `view_outdated`,
  `review_report`, `review_suggestion` y `undocumented_fact`.
- Cubre: BR1.5; NFR14.1.
- Verificación: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_readme.py --no-cov`
  → verde.

**Fuera del plan (definición de terminado del Bolt):** al fusionar el Bolt, **el humano** etiqueta
`vX.Y.Z` para que `sistema` la fije (BR12.2). La demo de B1 (el *job* rechaza los *fixtures* negativos y
acepta los positivos) la dan `tests/contracts` y `tests/guards` en verde en el *job* `contracts-level0`.

## Olas del loop

| Ola | Tareas | Depende de |
|---|---|---|
| 1 | T01 (pasos 1–2) | — |
| 2 | T02 (pasos 3–4) | T01 |
| 3 | T03 (paso 5, rojo) | T02 |
| 4 | T04 (paso 6, parada humana) | T03 |
| 5 | T05, T06, T07 (pasos 7, 8, 9) | T04 |
| 6 | T08, T09, T10 (pasos 10, 11, 12) | ola 5 |
| 7 | T11, T12, T13 (pasos 13, 14, 15) | ola 6 |
| 8 | T14 → T15 (paso 16) | ola 7 |
| 9 | T16, T17, T18 (pasos 17, 18, 19) | T15 |
| 10 | T19 (paso 20), T21 (paso 22) | ola 9 |
| 10b | T20 (paso 21) | T19 (consume `ts/generated/`) |
| 11 | T22 (pasos 23–24) → T23 (paso 25) | olas 10 y 10b |

Máximo tres codificadores en paralelo (`docs/loop/README.md` §5.3).

## Trazabilidad

| Origen | Pasos |
|---|---|
| Definición de terminado 1 de B1 (versión semántica, *fixtures*, suite en CI) | 5–25 |
| Definición de terminado 2 (hallazgo completo, `error` sin hallazgos) | 5, 6 |
| Definición de terminado 3 (sin campos de veracidad) | 5, 8, 13 |
| Definición de terminado 4 (`anonimizador_no_disponible`, `incidente_anonimizacion`) | 5, 6, 9 |
| Definición de terminado 5 (reporte de la CLI cerrado) | 5, 14 |
| Definición de terminado 6 (`AnonymizingProvider`) | 10 |
| AC3.2.1, AC3.6.2 | 5, 6, 7 |
| AC3.2.4, AC5.5.4 | 13 |
| AC5.5.3 | 5, 8 |
| AC8.3.1, AC8.3.3 | 5, 11, 16 |
| AC12.6.1 (parte de U1) | 5, 14 |
| AC13.3.1 | 5, 11 |
| AC15.4.7 | 5, 6 |
| BR1.1–BR1.3 | 5, 7 |
| BR1.4 | 7, 8, 11, 14, 15, 20 |
| BR1.5 | 25 |
| BR1.6 | 19 |
| BR1.7, BR1.8 | 5, 6 |
| BR1.9 | 4, 21 |
| BR2.1, BR2.3 | 5, 7 |
| BR3.1–BR3.3, BR3.5, BR3.6 | 5, 6 |
| BR3.4 | 9 |
| BR4.1–BR4.4 | 5, 8 |
| BR5.1–BR5.8 | 13 |
| BR6.1–BR6.3 | 5, 13 |
| BR7.1–BR7.3 | 5, 16 |
| BR7.4 | 9, 16 |
| BR8.1, BR8.2 | 18 |
| BR9.1, BR9.6, BR9.9 | 10 |
| BR9.2–BR9.5, BR9.7, BR9.8 | 11 |
| BR10.1, BR10.2 | 14 |
| BR11.1 | 12 |
| BR12.1 | 1, 19, 22 |
| BR12.2 | Definición de terminado del Bolt (tras el paso 25) |
| BR12.3 | 3, 22 |
| NFR1.1 | 5, 15 |
| NFR1.2 | 5, 10 |
| NFR1.3 | 5, 15 |
| NFR1.4, NFR12.3 | 5, 14 |
| NFR2.1 | 2, 21, 23 |
| NFR2.2 | 22, 23 |
| NFR3.1, NFR10.1, NFR10.11, NFR10.12, NFR11.1 | 16 |
| NFR10.2 | 5, 7, 8 |
| NFR10.3 | 9, 16 |
| NFR10.4, NFR10.5 | 3, 19, 21 |
| NFR10.6 | 19 |
| NFR10.7 | 12, 16 |
| NFR10.8 | 5, 16 |
| NFR10.9 | 4, 20, 23, 24 |
| NFR10.10 | 5, 19 |
| NFR10.13 | 11 |
| NFR10.14 | 12 |
| NFR10.15 | 3, 11, 20, 21 |
| NFR10.16 | 21 |
| NFR11.2 | 18 |
| NFR11.3 | 5, 13 |
| NFR11.4 | 6 |
| NFR11.5 | 8 |
| NFR12.1 | 19 |
| NFR12.2 | 24 |
| NFR13.1, NFR13.2 | 10, 17, 23 |
| NFR14.1 | 18, 25 |
| NFR15.1 | 18 |
| AUTONOMIA-01 | Dependencias; 19, 24 |
| AUTONOMIA-02 | Todos (línea `Verificación:`) |
| AUTONOMIA-03 | 5, 8, 13, 16 |
| AUTONOMIA-04 | 5, 10, 14, 15 |
| AUTONOMIA-05 | 5, 6, 8 |

## Riesgos y preguntas abiertas

| # | Riesgo o pregunta | Tratamiento |
|---|---|---|
| R-1 | Las tablas de precisiones (FD-U1, NFRD-U1 y las de otras unidades de PD-2) aún no se han llevado a `contract-summary.md` ni a `components.md` | El plan las toma como insumo aprobado (PD-1, PD-2). Si el humano prefiere actualizar primero los originales, se hace en commits propios antes de la ola 5 |
| R-2 | B1 crece mucho con PD-2 | Olas de hasta tres tareas; el paso 16 se parte en T14 y T15; un choque entre precisiones detiene la tarea y se anota en su PR |
| R-3 | La copia de C6 depende de un paso humano (PD-4) | Parada corta en la ola 4; sin ella el resto no tiene sentido (F7 corre primero) |
| R-4 | PD-3: tres decisiones abiertas fuera de B1 | Entran por su propio PR de U1 cuando el humano decida |
| R-5 | El análisis de patrones usa la API privada `re._parser` | Python fijado en 3.12 y prueba de versión con controles conocidos (§4.5) |
| R-6 | Las dos suites deben caber en 60 s | Perfil determinista de Hypothesis y meta ≤ 20 s por mitad |
| R-7 | El meta-esquema empaquetado de AsyncAPI 3.0 puede quedar viejo | Actualización por PR con su SHA-256 |
| R-8 | P0.1 (configuración de GitHub) no está confirmada | El PR del Bolt no se abre hasta que P0.1 esté cerrada; las tareas pueden avanzar en la rama |
