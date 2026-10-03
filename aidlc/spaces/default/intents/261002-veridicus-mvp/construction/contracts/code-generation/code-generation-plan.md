# Plan de generación de código — U1 contracts (Bolt B1 «Contratos»)

**Insumos.** Unidad U1 de `inception/units-generation/unit-of-work.md` (unit-of-work); B1 de
`inception/delivery-planning/bolt-plan.md` (orden interno, definición de terminado, demo); contratos
C1–C16 y reglas de propiedad de `inception/contract-design/contract-summary.md` (contract-summary);
flujos F1–F6, escenarios E1–E17 y precisiones de `construction/contracts/functional-design/`
(`functional-spec.md`, `rules.md`, `entities.md`); NFR1.1–NFR15.1 de
`construction/contracts/nfr-requirements/security-requirements.md` y decisiones D1–D12 de
`tech-stack-decisions.md`; controles §4.1–§4.13 de `construction/contracts/nfr-design/security-design.md`;
requisitos de `inception/requirements-analysis/requirements.md`; prácticas de `team.md` y `project.md`.

**Alcance.** U1 es una unidad `spec`: este plan produce los contratos versionados de `contracts/`, el
paquete Python `veridicus_contracts` con la suite de validación de nivel 0, sus generadores y el
*job* de CI que la corre. No hay comportamiento en ejecución, ni infraestructura, ni migraciones.
U1 no implementa historias propias; respalda AC2.2.3, AC3.2.1, AC3.2.4, AC5.5.3, AC5.5.4 y AC8.3.1
(story map de U1).

**Este trabajo se detiene aquí.** Por la regla de proceso de `team.md` («NEVER escribir código de
aplicación en este trabajo»), este plan es el entregable de Code Generation para U1: la Parte 2
(generación) la ejecutará el autor más adelante, fuera de este flujo.

## Decisiones del plan

| # | Decisión | Alternativas descartadas | Consecuencia |
|---|---|---|---|
| PD-1 | La versión 1.0.0 de cada contrato es `contract-summary.md` **más** todas las precisiones de las tablas «Precisiones a artefactos ya aprobados» de los diseños aprobados de U1–U10 (lista de fuentes en el paso 11). Las rutas, códigos y métricas de unidades SHOULD/COULD (U8, U9, U10) entran marcadas con `x-veridicus-priority`. | (a) Publicar solo `contract-summary.md` y que cada unidad suba un menor en su Bolt: unos 20 cambios menores seguidos sobre contratos que nadie consume todavía. (b) Incluir solo las precisiones de las unidades MUST: deja C1 incompleto para las rutas SHOULD que ya existen en contract-summary. | B1 sale con las formas que ya aprobaron todas las unidades; los cambios posteriores siguen BR1.5 (un PR por contrato). B1 es más grande, y el autor debe reconciliar las fuentes a mano: si dos precisiones chocan, se detiene y lo anota en el PR. |
| PD-2 | NFR10.6 se verifica con el análisis estático de `security-design.md` §4.5 (`maxLength` ≤ 256, sin repeticiones ilimitadas anidadas, alternancias solapadas ni referencias hacia atrás), no con el presupuesto de 50 ms de D8. | Medir 50 ms con Hypothesis (D8, NFR10.6 original) | Ninguna prueba mide tiempo de pared; es la precisión aprobada en NFR Design (P2 = A). |
| PD-3 | El escáner en ejecución `scan(text, literal_sources)` (F3 pasos 3–4) es de U4 en `libs/integrity_policy` (decisión de Functional Design, hallazgo R-01). U1 entrega la lista C8, sus *fixtures* E10–E14 con sus `literal_sources` y un comparador interno mínimo para revisar sus propios documentos (§4.8). | Construir `libs/integrity_policy` en U1 | U1 no adelanta código de U4. A cambio hay dos comparadores; ambos se prueban contra los mismos *fixtures* E13/E14. |
| PD-4 | Los tipos TypeScript de D9 se generan en `contracts/generated/ts/veridicus-contracts.ts`; la primera unidad que crea `frontend/` los importa y añade a su CI el paso de `openapi-typescript` y `git diff --exit-code`. | Generarlos ya en `frontend/`, que todavía no existe | Riesgo de tech-stack-decisions §5; queda fuera de este Bolt. |
| PD-5 | La copia versionada del subconjunto de C14 se guarda como `contracts/api/model-servers.v1.yaml` (el nombre no estaba fijado). | Guardarla dentro de `libs/model_gateway/` | `checks/servers.py` la revisa junto con C1 y C16 (NFR1.1). |

## Dependencias y punto de partida

- **Tarea previa P0.1** (configuración de GitHub: protección de `main`, comprobaciones obligatorias,
  GHCR privado, *deploy key*, Dependabot) debe estar cerrada antes de abrir el PR de B1
  (`bolt-plan.md`). Este plan no la ejecuta.
- **Rama:** `feat/b1-contratos` desde `main`; un solo PR con *squash-merge* y la salida de los comandos
  de verificación como evidencia (team-practices). Commits en Conventional Commits en español con
  alcance `contracts`.
- **AUTONOMIA-01:** ningún paso de este plan aplica cambios a un clúster, a una base ni a la nube: todo
  el trabajo son archivos del repositorio, una suite local sin red y un *workflow* de CI sin
  credenciales del clúster.
- **Greenfield:** no existe código; no hay suite previa que mantener verde.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (esquema de la alerta, JSON del juez, mensajes de la cola) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.",
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
      "text": "- **Methodology**: custom\n- **Ordering**: En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (esquema de la alerta, JSON del juez, mensajes de la cola) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.\n- **Cobertura**: 80 % de líneas por cada servicio Python y por el frontend, medido en CI y bloqueante; **100 % de ramas** en los módulos guardia (decisión de umbral del Silencio Fáctico, validación y máquina de estados de la alerta, consolidación del reporte, anonimizador si se construye). Las exclusiones (migraciones, código generado, arnés de evaluación) se declaran en la configuración y cada exclusión nueva se justifica en el PR.\n- **Herramientas**: `pytest` + `pytest-cov` (+ `pytest-asyncio`, Hypothesis) y mypy estricto en Python; Vitest + React Testing Library y TypeScript estricto en el frontend; Playwright para E2E; validación de manifiestos con `helm template` → `kubeconform` → Kyverno CLI.\n- **Dobles de prueba**: el LLM y los *embeddings* se sustituyen por *fakes* deterministas detrás de una interfaz propia en los niveles 0 y 1; PostgreSQL + `pgvector` y Redis son reales en contenedor (sin *mocks* de la base vectorial).\n- **Niveles y compuertas**:\n  - **Nivel 0 (cada PR, bloquea)**: *lint*, tipos, unitarias, contratos, guardias AUTONOMIA deterministas, políticas de manifiestos, cobertura.\n  - **Nivel 1 (cada PR, bloquea)**: integración contra PostgreSQL + `pgvector` y Redis reales (similitud, persistencia y reanudación de sesión, cola asíncrona, registro de quién y cuándo).\n  - **Nivel 2, evaluación de IA sobre el Golden Dataset**: bloquea los PR que tocan la IA (filtro por rutas: *prompts*, modelo, umbral, recuperación, esquemas de salida) y toda entrega etiquetada. Se corre fuera de la CI y el reporte JSON (versión del dataset, *hash* del *prompt*, umbral, *digest* del modelo, perfil CPU/GPU, métricas) se adjunta al PR. Umbrales: 100 % de trazabilidad factual, 0 % de error de formato JSON, permutación en el 100 % de las consultas *offline*, consistencia > 65 % al invertir el orden, y el caso de Hecho No Documentado con 0 alertas, 0 preguntas y 1 Paquete de Contexto de Traspaso. Incluye *red-teaming* (Escenarios A, B y C). Temperatura 0 y semilla fija.\n  - **Nivel 3, E2E y humo**: antes de etiquetar una entrega y tras cada despliegue.\n  - **Manual**: calificación Likert de la CoT (≥ 4.5/5, dos evaluadores) y verificación de `NetworkPolicy` en el clúster, antes de la sustentación.\n- **CPU y GPU**: la suite completa corre en **CPU**, en la máquina de desarrollo. Las pruebas que de verdad requieren GPU (evaluación con modelos más grandes, ensayo de la demo) se agrupan en una **etapa separada del perfil GPU**, que se corre a demanda en la máquina GPU solo cuando es estrictamente necesario. Ninguna prueba de los niveles 0 y 1 exige GPU.\n- **Mapa AUTONOMIA** (cada plan de tareas cita la prueba por ID): 01 → comprobación estática de que ningún *workflow* ni *script* aplica cambios al clúster (nivel 0); 02 → cada tarea lleva `Verificación: <comando exacto>` y su umbral; 03 → máquina de estados con actor y hora, consolidación explícita con SHA-256, esquema sin campos de veracidad y escaneo de vocabulario prohibido en salida e interfaz que excluye las citas literales (niveles 0, 1 y 3); 04 → prueba del *payload* saliente del anonimizador y política estática de `NetworkPolicy` (nivel 0) más verificación manual en el clúster; 05 → alerta rechazada sin cada uno de sus 4 campos, umbral leído de configuración y prueba por debajo del umbral (niveles 0, 1 y 2).\n- **Prueba de humo**: `scripts/smoke.sh <url-base>` termina con código 0 solo si (a) el *endpoint* de salud de cada servicio responde 200 y (b) el *spec* `frontend/e2e/smoke.spec.ts` comprueba que la transcripción con discrepancia sembrada produce ≥ 1 alerta con sus 4 campos obligatorios en ≤ *N* s (*N* lo fija NFR Requirements) y que el caso de Hecho No Documentado produce el paquete de traspaso sin alerta.\n- Las suites AUTONOMIA, de evaluación y de humo son **adicionales** al volumen de la Test Strategy y ningún plan las recorta. Ninguna prueba de los niveles 0 y 1 se reintenta para ocultar un fallo; una prueba inestable se arregla o se pone en cuarentena con un *issue* enlazado. Los umbrales nunca se bajan para que una compuerta pase."
    },
    {
      "layer": "project",
      "text": "- La GPU es opcional: el sistema y las suites de niveles 0 y 1 funcionan completos en CPU; las pruebas que requieren GPU (máquina de hasta 4 GPU y 32 GB de RAM) se agrupan en una etapa separada que corre a demanda. (learned 2026-10-02) \n\n- Los NFR de calidad (IA, MTTV, latencia, cobertura) no se escriben como historias; quedan diferidos a NFR Requirements y Build and Test. (learned 2026-10-02) \n\n- La evaluación de nivel 2 corre desde la anfitriona con kubectl port-forward al juez del clúster en vez de un Job: usa el mismo modelo y digest sin otra imagen, a cambio de depender de un script revisable que el humano ejecuta. (learned 2026-10-03)"
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
      "Custom ordering - En cada unidad, las pruebas de las guardias AUTONOMIA-03/04/05 y de los contratos de datos (esquema de la alerta, JSON del juez, mensajes de la cola) se escriben primero y se ejecutan en rojo antes de implementar; el resto de cada capa comprobable se implementa y enseguida se escriben y ejecutan sus pruebas antes de pasar a la siguiente capa.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:786408b35fc9ef7b0a094b98e70905ebf3060100ce021f51222415dc227b62c9",
  "contract_sha256": "sha256:81712dbd6813851333913a5e06319bad43df262c7f054d83f5ef9f3fbcc30ffc"
}
```

**Cómo aplica el orden del equipo a U1.** Las capas comprobables genéricas (base de datos, repositorio,
API, frontend) no existen en una unidad `spec`. Sus capas reales son: carga segura (`loaders`),
validación estándar (`validators`), contratos con sus *fixtures*, comprobaciones de reglas (`checks/`,
módulos guardia) y herramientas (`tools/`). Según el orden del equipo:

- **Primero, en rojo (paso 5):** las pruebas de contratos de datos (mensajes de cola C2–C5, salida del
  juez C6, alerta C7) y de las guardias AUTONOMIA-03 (sin campos ni rótulos de veracidad, enum de tres
  calificaciones, C8 con 9 términos, ninguna ruta que escriba el umbral), AUTONOMIA-04 (ningún destino
  externo) y AUTONOMIA-05 (alerta con sus 4 campos, sin alertas por debajo del umbral). Se corren y su
  salida en rojo se guarda como evidencia antes de escribir ningún contrato.
- **Después, capa por capa:** cada contrato o módulo restante se implementa y enseguida se escriben y
  corren sus pruebas, antes del paso siguiente.

## Comandos de verificación

Todos corren desde la raíz del repositorio, sin GPU. La suite no tiene red (`--disable-socket`); solo
los pasos de instalación y auditoría la usan (`security-design.md` §4.13).

| Clave | Comando | Umbral |
|---|---|---|
| V-INSTALL | `uv sync --frozen --directory contracts` | Código 0; `uv.lock` con *hashes* coincide |
| V-SUITE | `timeout 60 uv run --offline --directory contracts pytest` | Verde, ≤ 60 s (meta ≤ 20 s), ≥ 80 % de líneas |
| V-GUARD | `uv run --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/*" --fail-under=100` | 100 % de ramas en `checks/` |
| V-TYPES | `uv run --offline --directory contracts mypy --strict src python` | 0 errores |
| V-LINT | `uv run --offline --directory contracts ruff check .` | 0 hallazgos (reglas `S` incluidas) |
| V-AUDIT | `uv run --directory contracts pip-audit` | 0 `HIGH`/`CRITICAL` con corrección |
| V-TS | `uv run --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check` | Sin diferencias |
| V-SURFACE | `uv run --offline --directory contracts pytest tests/tools/test_security_surface.py` | Huella regenerada = archivo versionado |

## Pasos

Cada paso nombra su comprobación con `Verificación:` (AUTONOMIA-02) y la regla o el requisito que
cubre. Las rutas son relativas a la raíz del repositorio.

### Paso 1 — Estructura del paquete y configuración

- [ ] Crear `contracts/` como paquete Python 3.12 autocontenido (D1): `pyproject.toml` con las
  dependencias de `tech-stack-decisions.md` §3 (`jsonschema[format]`, `openapi-spec-validator`,
  `referencing`, `ruamel.yaml`; desarrollo: `pytest`, `pytest-cov`, `pytest-socket`, `hypothesis`,
  `mypy`, `ruff`, `pip-audit`), `uv.lock` con *hashes*, `src/veridicus_contracts/__init__.py` con
  `py.typed`, y los directorios vacíos de `functional-spec.md` §1 (`api/`, `errors/`, `queues/`,
  `schemas/`, `integrity/`, `ui/`, `db/`, `metrics/`, `health/`, `format/`, `python/`, `fixtures/`,
  `vendor/`, `generated/ts/`).
- [ ] Configurar en `pyproject.toml` mypy estricto, Ruff (reglas por defecto + `S`, toda supresión
  `# noqa: S…` con motivo) y cobertura con ramas; exclusiones declaradas solo para `generated/`.
- [ ] Añadir a `.gitignore` de la raíz `.env`, `*.pem`, `*.key`, `kubeconfig*` y `secrets*.yaml` si no
  están (team-practices, Deployment).
- Cubre: D1, D11, NFR13.2.
- Verificación: `uv sync --frozen --directory contracts` → código 0.

### Paso 2 — Ejecutor de pruebas listo (antes de la primera prueba)

- [ ] Configurar `pytest` en `pyproject.toml`: `testpaths = ["tests"]`, `addopts` con
  `--disable-socket --cov=veridicus_contracts --cov-branch --cov-fail-under=80` (D6, D7) y un perfil de
  Hypothesis determinista (`derandomize = true`, sin plazos de tiempo).
- [ ] Crear `tests/conftest.py` (rutas al árbol `contracts/`) y `tests/test_runner.py` con dos pruebas:
  abrir un *socket* lanza `SocketBlockedError`, y el árbol de `contracts/` se resuelve.
- Cubre: NFR2.1, NFR10.5 (red bloqueada).
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/test_runner.py --no-cov`
  → 2 pruebas en verde. Este es el comando por unidad que queda en `unit-test-instructions.md`.

### Paso 3 — Capa de carga segura (implementar y probar)

- [ ] `src/veridicus_contracts/loaders.py`: único punto que instancia
  `ruamel.yaml.YAML(typ="safe", pure=True)` con `allow_duplicate_keys = False` y YAML 1.2 (D5, §4.1);
  lectura de JSON; registro `referencing` cerrado con todos los documentos de `contracts/` y
  `contracts/vendor/` indexados por `$id` o ruta, cuya recuperación lanza error para cualquier URI fuera
  del registro (§4.2).
- [ ] `tests/test_loaders.py` (6 pruebas): YAML válido; clave duplicada rechazada; `!!python/object`
  rechazado; `no`/`on` leídos como texto (YAML 1.2); `$ref` interno resuelto; `$ref` a `https://`
  rechazado sin red.
- Cubre: NFR10.4, NFR10.5; amenazas T4, T5.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/test_loaders.py --no-cov`
  → verde.

### Paso 4 — Capa de validación estándar y meta-esquemas (implementar y probar)

- [ ] Copiar el meta-esquema empaquetado de AsyncAPI 3.0.0 y los de JSON Schema 2020-12 y OpenAPI 3.1
  que haga falta a `contracts/vendor/`, con `vendor/SHA256SUMS` (D4, NFR10.9).
- [ ] `src/veridicus_contracts/validators.py`: validar OpenAPI 3.1 con `openapi-spec-validator` (D3),
  AsyncAPI 3.0 contra el meta-esquema de `vendor/` y extraer la carga de cada mensaje (D4), y JSON
  Schema 2020-12 con verificación de formatos `uuid` y `date-time` (D2). La forma de fecha de BR8.1 se
  añade como comprobador de formato propio.
- [ ] `tests/test_validators.py` (7 pruebas): cada `vendor/` coincide con `SHA256SUMS`; un meta-esquema
  alterado falla; OpenAPI mínimo válido e inválido; AsyncAPI mínimo válido e inválido; extracción de la
  carga de un mensaje; `date-time` con fracción o desfase rechazado (E16).
- Cubre: D2–D4, NFR10.9, NFR11.2.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/test_validators.py --no-cov`
  → verde.

### Paso 5 — ROJO: pruebas de contratos de datos y de guardias AUTONOMIA-03/04/05

Se escriben **antes** de cualquier contrato y se corren en rojo (orden del equipo).

- [ ] Formato de *fixture* (§4.10): archivo YAML con `fixture_id`, `contract`, `synthetic: true`,
  `expectation: accept|reject`, `reject_reason: <ID de regla>` (obligatorio en `reject`), `mentions` y
  `payload`. Catálogo `contracts/fixtures/synthetic-names.yaml` con nombres y lugares inventados.
- [ ] *Fixtures* de datos, uno por escenario de `functional-spec.md` §6 como mínimo:
  - C2 `fixtures/turns/`: válido; E1 sin `text` (BR2.1); `text` vacío (BR2.1); E2 `schema_version:
    2.0.0` (BR1.2); E3 1.1.0 con campo nuevo, aceptado (BR1.3); E4 umbral 1.2 y umbral ausente (BR2.2);
    `previous_turns` con 4 elementos.
  - C3 `fixtures/results/`: `evaluated` válido; `error` válido; E5 `error` con alerta (BR2.3); `error`
    sin `error_code` (BR2.3); E6 alerta sobre afirmación `congruente` y sobre `guard: below_threshold`
    (BR2.4, AUTONOMIA-05); afirmación `no documentada` con `suggested_question` o sin
    `handoff_package` (BR2.5, AUTONOMIA-05).
  - C4 y C5 `fixtures/indexing/`, `fixtures/speech/`: válido; obligatorio ausente; mayor desconocido.
  - C6 `fixtures/judge-output/`: válido; E7 con `is_truthful` en la raíz y dentro de una afirmación
    (BR3.1, BR3.3); E8 calificación «falsa» (BR3.2); `claims` vacío (BR3.1); `cot` vacío.
  - C7 `fixtures/alert/`: válido; E9 cuatro negativos, uno por cada campo ausente (`fragment`,
    `quote`, `document_id`, `cot`) y cuatro más con el campo vacío (BR4.1); alerta con `is_truthful`
    (BR4.2).
- [ ] `tests/contracts/test_queue_messages.py`, `test_judge_output.py`, `test_alert.py`: cargan cada
  *fixture*, validan contra su contrato y exigen aceptar o rechazar **por su** `reject_reason`
  (NFR10.10, F1 paso 3).
- [ ] `tests/guards/test_autonomia_03.py`: ningún nombre de propiedad, parámetro, valor de enum o
  rótulo de ningún documento coincide con C8 o con `categories_forbidden_in_schemas` (BR3.3); enum de
  calificación exactamente `congruente`, `incongruente`, `no documentada` en C1, C3 y C6 (BR3.2); C8
  1.0.0 con exactamente sus 9 términos (BR5.1, prueba `test_c8_has_exactly_nine_terms`); catálogo de
  rótulos con exactamente sus tres filas y asociación fija (BR6.1–BR6.3, prueba
  `test_result_labels_are_exactly_three`); ninguna operación POST, PUT, PATCH o DELETE de C1 con `threshold` o
  `umbral` en ruta, parámetro o cuerpo, con control negativo E15 (copia de C1 con `PATCH
  /config/threshold`) (BR7.1, AC8.3.1).
- [ ] `tests/guards/test_autonomia_04.py`: todo `servers[].url` y valor por defecto de C1, C14, C16 y
  de los AsyncAPI es relativo o termina en `.svc.cluster.local[:puerto]`; control negativo: copia de C14
  con `https://api.openai.com` (NFR1.1).
- [ ] `tests/guards/test_autonomia_05.py`: C7 rechaza cada uno de los 8 *fixtures* de E9; C3 rechaza
  E6 y los casos de BR2.5; `similarity_threshold` de C2 acotado a [0, 1].
- [ ] Correr las pruebas y guardar la salida en rojo en el PR (evidencia de que fallan por falta de
  contratos, no por errores de importación o de sintaxis de las pruebas).
- Cubre: AC2.2.3, AC3.2.1, AC5.5.3, AC5.5.4, AC8.3.1; BR1.2, BR1.3, BR2.1–BR2.5, BR3.1–BR3.3, BR4.1,
  BR4.2, BR5.1, BR6.1–BR6.3, BR7.1; NFR1.1, NFR10.2, NFR10.8, NFR10.10, NFR11.3.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/contracts tests/guards --no-cov`
  → **código distinto de 0**, y cada fallo es un `AssertionError` o un archivo de contrato ausente
  (ningún `ImportError`, `SyntaxError` ni error de recolección).

### Paso 6 — Contratos de cola C2–C5 (verde)

- [ ] `contracts/queues/turns.v1.yaml` (C2), `results.v1.yaml` (C3), `indexing.v1.yaml` (C4),
  `speech.v1.yaml` (C5, `x-veridicus-priority: SHOULD`) en AsyncAPI 3.0, versión 1.0.0, con el sobre
  común `schema_version`, `message_id`, `attempt ≥ 1` (BR1.1) y las precisiones de PD-1: `top_k` en C2;
  `undocumented_claim_indexes` y `threshold_used` en `handoff_package`, `turn.error.timeout` en
  `error_code` y los campos de relectura (`forward_grade`, `reversed_grade`, `sustained`) y
  `source_passage_ids`/`question_prompt_sha256` en C3; `audio_base64` con `maxLength: 8000000` y
  `turn.error.invalid_output` en C5; entradas de `<cola>:failed` solo con identificadores y `code`.
- [ ] BR2.3 y BR2.5 se expresan en el esquema de C3 con `if`/`then` de 2020-12.
- [ ] `checks/result_invariants.py` (módulo guardia): BR2.4, que el esquema no puede expresar (una
  alerta solo apunta a un `claim_index` `incongruente` con `guard: at_or_above_threshold`); devuelve
  hallazgos con el ID de regla.
- [ ] `tests/checks/test_result_invariants.py` (6 pruebas, 100 % de ramas).
- Cubre: C2–C5; BR1.1–BR1.3, BR2.1–BR2.5; NFR10.2, NFR10.7.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/contracts/test_queue_messages.py tests/checks/test_result_invariants.py --no-cov`
  → verde.

### Paso 7 — Esquemas estrictos C6 y C7 (verde)

- [ ] `contracts/schemas/judge-output.v1.json` (C6) y `contracts/schemas/alert.v1.json` (C7): JSON
  Schema 2020-12, `$id` versionado, `additionalProperties: false` en cada objeto, `minLength: 1` en
  `fragment`, `quote`, `document_id` y `cot`, enum `Grade` de tres valores (BR3.1, BR3.2, BR4.1, BR4.2).
- Cubre: C6, C7; AC3.2.1, AC5.5.3; BR3.1–BR3.3, BR4.1, BR4.2; NFR10.2.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/contracts/test_judge_output.py tests/contracts/test_alert.py tests/guards/test_autonomia_05.py --no-cov`
  → verde.

### Paso 8 — Vocabulario prohibido C8 y catálogo de rótulos (verde)

- [ ] `contracts/integrity/forbidden-vocabulary.v1.yaml` (C8) 1.0.0: los 9 términos (`mentiroso`,
  `mentirosa`, `miente`, `mintió`, `falso`, `falsa`, `verdadero`, `verdadera`, `engaño`), `match`
  (palabra completa, sin mayúsculas ni tildes), `excluded_spans`, `quote_delimiters: [«, »]` y
  `categories_forbidden_in_schemas` (entities, P1, P2).
- [ ] `contracts/ui/result-labels.v1.yaml` 1.0.0: `review_suggestion` → «Sugerencia de revisión»,
  `semantic_incongruence` → «Incongruencia semántica» (`incongruente`), `undocumented_fact` → «Hecho No
  Documentado» (`no documentada`); `congruente` sin rótulo.
- [ ] *Fixtures* `fixtures/forbidden-vocabulary/` para el escáner de U4 (PD-3), cada uno con su CoT y
  sus `literal_sources`: E10 «el compareciente miente»; E11 «falso» dentro de «…» literal del pasaje;
  E12 «miente» dentro de «…» que no aparece en las fuentes; E13 «MIENTE» y «mintio»; E14 «falsete» y
  «mienten» (válidos con la lista 1.0.0); un término nuevo sin control negativo (BR5.1).
- [ ] `checks/vocabulary.py` (módulo guardia): comparador mínimo de palabra completa sin mayúsculas ni
  tildes para revisar nombres, rótulos, descripciones y ejemplos de los propios contratos; un ejemplo de
  CoT con un término fuera de «…» literales hace fallar (§4.8). Exige además un *fixture* negativo por
  término de la lista (BR5.1).
- [ ] `checks/veracity.py` (módulo guardia, §4.8): usa `checks/vocabulary.py` para comprobar BR3.2,
  BR3.3, BR5.1 y BR6.1–BR6.3 sobre todos los documentos; es el código que ejercitan las guardias de
  AUTONOMIA-03 del paso 5. `tests/checks/test_veracity.py` (6 pruebas, 100 % de ramas).
- [ ] `tests/checks/test_vocabulary.py` (8 pruebas, 100 % de ramas): E10, E13, E14, término con tilde
  y sin tilde, palabra dentro de otra, ejemplo de documento con «miente» fuera de comillas, cita literal
  excluida.
- Cubre: C8; AC3.2.4, AC5.5.4; BR5.1–BR5.5, BR6.1–BR6.3; NFR11.3.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/guards/test_autonomia_03.py::test_c8_has_exactly_nine_terms tests/guards/test_autonomia_03.py::test_result_labels_are_exactly_three tests/checks/test_vocabulary.py tests/checks/test_veracity.py --no-cov`
  → verde. Las demás pruebas de `test_autonomia_03.py` dependen de C1 y pasan a verde en el paso 11.

### Paso 9 — Catálogo de errores y catálogo de límites (implementar y probar)

- [ ] `contracts/errors/error-codes.v1.yaml` 1.0.0: cada `code` con estado HTTP, unidad dueña y si es
  visible; incluye los de contract-summary y los de PD-1 (`turn.too_long`, `transcript.too_large`,
  `session.not_open`, `system.unavailable`, `auth.too_many_attempts`, `user.weak_password`,
  `user.duplicate_username`, `user.self_deactivation`, `user.last_admin`, `user.has_open_sessions`,
  `report.not_consolidated`, `report.storage_failed`, `report.view_outdated`,
  `question.already_decided`, `question.not_approved`, `turn.audio_unavailable`, `speech.unavailable`).
  BR3.4 exige `turn.error.invalid_output`, `turn.error.timeout` y `turn.error.system` como tres códigos.
- [ ] `contracts/limits.v1.yaml` 1.0.0 con las 8 entradas de `security-design.md` §4.4, y
  `src/veridicus_contracts/limits.py` con `get(key) -> int` de solo lectura sobre el archivo empaquetado.
- [ ] `tests/test_limits.py` (5 pruebas): cada clave devuelve su entero; clave desconocida lanza error;
  `voice_audio_base64_max_chars = 4 × ⌈voice_audio_max_bytes / 3⌉`; el archivo se lee del paquete
  instalado; los valores son enteros positivos.
- Cubre: BR3.4, BR7.2; NFR10.3, NFR10.7; DS1.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/test_limits.py --no-cov`
  → verde.

### Paso 10 — Formato de fecha (implementar y probar)

- [ ] `contracts/format/datetime.v1.yaml` 1.0.0: forma `AAAA-MM-DDTHH:MM:SSZ`, su `pattern` y la regla
  de fecha real (P4).
- [ ] `checks/datetime_format.py` (módulo guardia): todo campo `date-time` de C1–C7 lleva ese `pattern`.
- [ ] `tests/checks/test_datetime_format.py` (5 pruebas): forma válida; fracción (E16); desfase
  `-05:00` (E16); 30 de febrero; campo `date-time` sin el `pattern`.
- Cubre: BR8.1; NFR11.2.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/checks/test_datetime_format.py --no-cov`
  → verde.

### Paso 11 — OpenAPI de la consola C1 1.0.0 y sus comprobaciones (implementar y probar)

- [ ] `contracts/api/console.v1.yaml` (C1) en OpenAPI 3.1, armado desde contract-summary §C1 más las
  precisiones de PD-1, tomadas de las tablas «Precisiones a artefactos ya aprobados» de:
  `contracts/` (functional-spec §9, security-requirements §6, security-design §8),
  `identity-access/` (functional-spec, nfr-requirements, nfr-design), `text-flow/` (functional-spec,
  nfr-requirements), `human-review/` (nfr-requirements, nfr-design), `forensic-report/`
  (nfr-requirements, nfr-design), `session-lifecycle/` (functional-spec, nfr-requirements),
  `assistant-extras/` (nfr-requirements), `voice/` (nfr-requirements, nfr-design). Entre otras:
  `ErrorCode` igual al catálogo del paso 9; `Turn` con `speaker` y `role`; `ScenarioVersion` con sus
  documentos; cuerpo `{ expected_cursor }` en `POST /sessions/{session_id}/reports`; `maxLength: 2000`
  en `note` y `reformulation`; respuestas `403`, `409`, `422`, `429` y `503` con `$ref` a `Problem`;
  `Retry-After` en `/auth/login`; `Cache-Control: no-store` en el audio; `x-veridicus-roles` en toda
  operación salvo `/auth/login`, `/auth/logout` y `/auth/me`; `x-veridicus-owner-only` donde aplica;
  `x-veridicus-limit` en cada `maxLength` y parte binaria; `x-veridicus-cookie` en `sessionCookie`.
  Si dos precisiones chocan, el paso se detiene y el conflicto se anota en el PR.
- [ ] Módulos guardia, uno por regla (§4.3, §4.6, §4.7):
  - `checks/threshold.py` (BR7.1, NFR10.8): la guardia de AUTONOMIA-03 del paso 5.
  - `checks/strict_bodies.py` (BR7.3, NFR10.1): `additionalProperties: false` en todo cuerpo JSON y
    *multipart* de C1, en todos los niveles, y en C6/C7.
  - `checks/limits_match.py` (NFR10.7, DS1): todo texto libre de C1 y C2 y toda parte binaria lleva
    `x-veridicus-limit` y su valor es igual al del catálogo; respuestas de exceso `413`
    `scenario.too_large` y `422` `validation.invalid_request`.
  - `checks/auth_surface.py` (NFR10.11, NFR10.12, NFR11.1, NFR3.1): seguridad efectiva, `CsrfToken` en
    POST/PATCH, roles, dueño, `401`/`403` con `Problem`, sin DELETE ni PUT, una sola PATCH, las seis
    operaciones que encolan trabajo de IA solo con `202`.
  - `checks/error_codes.py` (BR3.4, BR7.2, NFR10.3): `ErrorCode` = catálogo; todo `code` de C1–C5
    existe; toda 4xx/5xx de C1 es `$ref` a `Problem`.
- [ ] `tests/checks/test_<módulo>.py` para cada uno (5–8 pruebas por módulo, 100 % de ramas), con los
  controles negativos de §4.3, §4.6 y §4.7 (ruta pública nueva, escritura sin anti-CSRF, operación sin
  roles, DELETE, `200` en una operación que encola, cuerpo sin la marca, límite distinto del catálogo,
  `409` sin `Problem`, `code` fuera del catálogo).
- Cubre: C1; AC8.3.1; BR7.1–BR7.3, BR3.4; NFR3.1, NFR10.1, NFR10.3, NFR10.7, NFR10.8, NFR10.11,
  NFR10.12, NFR11.1.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/checks tests/guards --no-cov`
  → verde (las guardias del paso 5 que dependían de C1 pasan a verde aquí).

### Paso 12 — C9, C14, C15, C16 y sus comprobaciones (implementar y probar)

- [ ] `contracts/db/truthframe-read.v1.yaml` (C9) 1.0.0 como en contract-summary.
- [ ] `contracts/api/model-servers.v1.yaml` (C14, PD-5): copia del subconjunto compatible con OpenAI
  que fija U4, con servidores `*.svc.cluster.local`.
- [ ] `contracts/health/health.v1.yaml` (C16) 1.0.0: `/healthz` y `/readyz` públicos dentro del
  clúster, con el parámetro `probe=kubernetes` (precisión de U3).
- [ ] `contracts/metrics/review.v1.yaml` (C15) 1.0.0: métricas de contract-summary más las de las
  `observability-requirements.md` §2 de U3–U9 y las precisiones de U5 y U7 (*W* = 8,
  `veridicus_review_rejections_total`, los dos *gauges* del volumen de reportes), todas con etiquetas de
  enum o identificador.
- [ ] `checks/servers.py` (NFR1.1; guardia de AUTONOMIA-04 del paso 5), `checks/metrics.py` (BR8.2,
  NFR15.1) y `checks/naming.py` (NFR14.1: ASCII `snake_case`, `code` en `dominio.motivo`, enums del
  PRD en español exacto), con `tests/checks/test_servers.py`, `test_metrics.py`, `test_naming.py`
  (5–7 pruebas cada uno, 100 % de ramas).
- Cubre: C9, C14, C15, C16; BR8.2; NFR1.1, NFR14.1, NFR15.1.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/checks/test_servers.py tests/checks/test_metrics.py tests/checks/test_naming.py tests/guards/test_autonomia_04.py --no-cov`
  → verde.

### Paso 13 — Interfaces en proceso C10–C12 (implementar y probar)

- [ ] `contracts/python/human_review.py` (C10), `forensic_ports.py` (C11), `identity.py` (C12), versión
  1.0.0 en el encabezado, como `Protocol` tipados, con las precisiones de PD-1: `propose` rechaza con
  `review.round_locked` y exige la `UnitOfWork` con el bloqueo de la sesión; `open_round(uow,
  session_id, *, for_update: bool = False)`; `change_cursor.bump` antes de tocar ronda o sesión;
  puerto «sesiones pendientes del usuario»; `UserChange` con `actor_kind: system` solo para el primer
  `admin`.
- [ ] `tests/typing/test_protocols.py` (5 pruebas): un *fake* mínimo de cada interfaz satisface su
  `Protocol` (comprobado por mypy estricto) y uno con una firma distinta falla (`assert_type` y un
  módulo de control negativo excluido de la verificación normal y comprobado aparte por la prueba).
- Cubre: C10–C12; NFR13.2.
- Verificación: `uv run --offline --directory contracts mypy --strict src python` → 0 errores, y
  `timeout 60 uv run --offline --directory contracts pytest tests/typing --no-cov` → verde.

### Paso 14 — Comprobaciones de integridad de la suite (implementar y probar)

- [ ] `checks/loader_usage.py` (§4.1, R-03): recorre con `ast` `src/`, `tests/` y `python/`; falla con
  `import yaml`, `YAML(...)` fuera de `loaders.py`, `typ` distinto de `"safe"`, `load_all` o `Loader=`.
- [ ] `checks/refs.py` (§4.2): falla ante `$ref` `http:`, `https:` o `file:` o que salga de
  `contracts/` tras normalizar `..`.
- [ ] `checks/redos.py` (§4.5, PD-2): `maxLength` ≤ 256 con todo `pattern` (excepción declarada en
  `limits.v1.yaml`), y análisis del árbol con `re._parser.parse` contra repeticiones ilimitadas
  anidadas, alternancias solapadas repetidas y referencias hacia atrás; Hypothesis comprueba que cada
  `pattern` acepta y rechaza bien hasta su `maxLength`, sin medir tiempo.
- [ ] `checks/synthetic.py` (NFR12.1, BR1.6): `synthetic: true`; cada mención existe en
  `synthetic-names.yaml` y aparece en el texto; rechaza secuencias de 6–10 dígitos y de 23 dígitos con o
  sin separadores en *fixtures* y en los `example` de los contratos.
- [ ] `checks/fixture_coverage.py` (NFR10.10): al menos un `accept` y un `reject` por cada regla
  BR1.1–BR8.2 que se prueba en nivel 0; un `reject` que no falla, o que falla por otra regla, hace fallar.
- [ ] `tests/checks/test_<módulo>.py` por cada uno (5–8 pruebas, 100 % de ramas), con los controles
  negativos de §4.1, §4.2, §4.5 y §4.10: `YAML(typ="unsafe")` en un módulo sintético, `$ref` remoto y
  `../`, `^(a+)+$`, `^(a|aa)*$`, `^(\w+)\1$`, `pattern` sin `maxLength`, mención fuera del catálogo,
  cédula y radicado inventados, `reject` sin `reject_reason`.
- Cubre: BR1.6; NFR10.4–NFR10.6, NFR10.10, NFR12.1; amenazas T2–T6.
- Verificación: `timeout 60 uv run --offline --directory contracts pytest tests/checks --no-cov` → verde.

### Paso 15 — Huella de seguridad versionada (implementar y probar)

- [ ] `src/veridicus_contracts/tools/security_surface.py` (§4.11, DS3): proyección determinista
  (claves ordenadas, una línea por elemento, sin fechas) con las secciones `operations`, `schemas`,
  `cookie`, `servers` e `integrity`; modo `--write` que escribe `contracts/security-surface.json`.
- [ ] Generar `contracts/security-surface.json` y crear `.github/pull_request_template.md` con la casilla
  que pide justificar todo cambio de ese archivo.
- [ ] `tests/tools/test_security_surface.py` (5 pruebas): regenerada = versionada; mismo resultado en dos
  ejecuciones; una ruta que pasa a pública cambia `operations`; un límite que sube cambia `operations`;
  el *hash* de C8 está en `integrity`.
- Cubre: DS3; amenazas T1, T8.
- Verificación: `uv run --offline --directory contracts pytest tests/tools/test_security_surface.py --no-cov`
  → verde.

### Paso 16 — Generador de constantes TypeScript (implementar y probar)

- [ ] `src/veridicus_contracts/tools/gen_ts.py` (D9, PD-4): constantes `as const` del catálogo de `code`,
  de los rótulos y de C8, escritas en `contracts/generated/ts/veridicus-contracts.ts`; modo `--check`
  que falla si el archivo difiere.
- [ ] `tests/tools/test_gen_ts.py` (5 pruebas): salida determinista; `--check` en verde con el archivo
  al día; `--check` en rojo tras cambiar un rótulo; los tres rótulos y los 9 términos presentes;
  escape correcto de «» y tildes.
- Cubre: D9; NFR14.1, NFR11.3.
- Verificación: `uv run --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check`
  → código 0, y `timeout 60 uv run --offline --directory contracts pytest tests/tools/test_gen_ts.py --no-cov`
  → verde.

### Paso 17 — Suite completa y compuertas de calidad

- [ ] Correr la suite completa con cobertura, las ramas de los módulos guardia, tipos, *lint* y
  auditoría. Ningún umbral se baja para que pase (team-practices); un hueco se informa en el PR.
- Cubre: NFR2.1, NFR10.9, NFR13.1, NFR13.2.
- Verificación: V-SUITE (verde, ≤ 60 s, ≥ 80 % de líneas), V-GUARD (100 %), V-TYPES (0), V-LINT (0),
  V-AUDIT (0 `HIGH`/`CRITICAL` con corrección), V-TS (sin diferencias), V-SURFACE (verde).

### Paso 18 — CI y ganchos locales

- [ ] `.github/workflows/contracts-level0.yml`: *job* `contracts-level0` con los pasos de §4.13 en orden
  (instalar y auditar con red; suite, ramas guardia, tipos y *lint*, y tipos TypeScript sin red),
  `permissions: contents: read`, cada acción fijada por SHA, sin `kubeconfig` ni credenciales del
  clúster (AUTONOMIA-01) y `gitleaks` sobre el repositorio (NFR12.2).
- [ ] `.pre-commit-config.yaml` en la raíz con `gitleaks`, Ruff y `yamllint` (team-practices).
- [ ] Pedir en el PR que `contracts-level0` sea comprobación obligatoria de `main` (lo aplica el autor
  en GitHub; parte de P0.1).
- Cubre: NFR10.9, NFR12.2; AUTONOMIA-01, AUTONOMIA-02.
- Verificación: `yamllint -s .github/workflows/contracts-level0.yml .pre-commit-config.yaml` → código 0;
  `pre-commit run --all-files` → código 0; y el *job* `contracts-level0` en verde en el PR (enlace en la
  evidencia).

### Paso 19 — Documentación y trazabilidad

- [ ] `contracts/README.md` en español: inventario, cómo cambiar un contrato (F5: PR propio, versión,
  *fixtures*, huella), cómo usar `limits.get` y los esquemas desde un servicio, y los comandos V-*.
- [ ] Docstrings en español en `loaders`, `validators`, `limits` y cada módulo de `checks/` (nombre de
  la regla que protege).
- [ ] Al terminar la Parte 2: `code-summary.md`, `source-manifest.json` y `traceability.json` de esta
  unidad.
- Cubre: BR1.5 (proceso de cambio documentado).
- Verificación: `test -s contracts/README.md` → código 0, y la demo de B1: la ejecución de V-SUITE en CI
  rechaza los *fixtures* negativos (alerta incompleta, campo de veracidad, versión mayor desconocida) y
  acepta los positivos.

## Trazabilidad

| Origen | Pasos |
|---|---|
| AC2.2.3 (turno mal formado rechazado) | 5, 6 |
| AC3.2.1 (salida inválida del juez → `turn.error.invalid_output`) | 5, 6, 7, 9 |
| AC3.2.4 (vocabulario prohibido en la CoT, citas literales excluidas) | 8 |
| AC5.5.3 (sin campos de veracidad) | 5, 7 |
| AC5.5.4 (enum de tres calificaciones y rótulos) | 5, 7, 8 |
| AC8.3.1 (ninguna ruta escribe el umbral) | 5, 11 |
| BR1.1–BR1.3 | 6 |
| BR1.4 (C6/C7 estrictos, `$id` versionado) | 7, 15 |
| BR1.5 | 19 |
| BR1.6 | 14 |
| BR2.1–BR2.5 | 5, 6 |
| BR3.1–BR3.3 | 5, 7 |
| BR3.4 | 9, 11 |
| BR4.1, BR4.2 | 5, 7 |
| BR5.1–BR5.5 | 8 |
| BR6.1–BR6.3 | 5, 8 |
| BR7.1–BR7.3 | 5, 11 |
| BR8.1 | 4, 10 |
| BR8.2 | 12 |
| NFR1.1 | 5, 12 |
| NFR2.1 | 2, 17 |
| NFR3.1, NFR10.1, NFR10.3, NFR10.11, NFR10.12, NFR11.1 | 11 |
| NFR10.2 | 6, 7 |
| NFR10.4, NFR10.5 | 3, 14 |
| NFR10.6 | 14 (PD-2) |
| NFR10.7 | 9, 11 |
| NFR10.8, NFR11.3 | 5, 8, 11 |
| NFR10.9 | 4, 17, 18 |
| NFR10.10 | 5, 14 |
| NFR11.2 | 4, 10 |
| NFR12.1 | 14 |
| NFR12.2 | 18 |
| NFR13.1, NFR13.2 | 13, 17 |
| NFR14.1 | 12, 16 |
| NFR15.1 | 12 |
| AUTONOMIA-01 | Dependencias; 18 |
| AUTONOMIA-02 | Todos (línea `Verificación:`) |
| AUTONOMIA-03 | 5, 7, 8, 11, 15 |
| AUTONOMIA-04 | 5, 12 |
| AUTONOMIA-05 | 5, 6, 7 |

## Riesgos y preguntas abiertas

| Riesgo o pregunta | Tratamiento |
|---|---|
| PD-1 hace de B1 un PR grande, y alguna precisión de otra unidad puede chocar con otra | El paso 11 se detiene ante un choque y lo anota en el PR; el autor decide antes de fusionar |
| Las tablas de precisiones aún no se han trasladado a `contract-summary.md` | El plan las toma como insumo aprobado; si el humano prefiere actualizar primero el original, se hace en su propio commit (`project.md`) |
| El nombre del archivo de C14 (PD-5) y la ruta de los tipos TypeScript (PD-4) no estaban fijados | Se fijan aquí; cambiarlos es un cambio de este plan |
| El meta-esquema de AsyncAPI 3.0 empaquetado puede quedar viejo | Actualización por PR con su SHA-256 (riesgo residual de security-design §7) |
| La suite debe caber en 60 s con Hypothesis | Perfil determinista y número de ejemplos acotado; la meta es ≤ 20 s |
