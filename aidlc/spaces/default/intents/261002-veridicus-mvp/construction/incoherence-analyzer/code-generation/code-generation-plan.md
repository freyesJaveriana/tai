# Plan de generación de código — U11 incoherence-analyzer (Bolt B11a «CLI del analizador»)

**Parte 1 de Code Generation, revisión 3, 2026-11-26.** Integra los hallazgos R-01 a R-15 de la ronda 1 de la revisión ML-8, y R-05, N-01, N-02 y N-03 de la ronda 2, que salió READY. Su tabla de resolución está al final del plan. El plan cubre solo el corte B11a de la precisión DP-03 (`bolt-plan.md`, línea 434; origen: cambio 06, §3). Sigue el modo liviano DT31 (`docs/loop/README.md` §9, ML-1 a ML-14) y tiene **15 pasos**, el tope del cambio 06 para llegar al sábado. Los pasos se agrupan en **6 tareas** del loop (ML-3). Cada paso lleva su riesgo, su `Verificación:` y su `Umbral:` (AUTONOMIA-02).

**Qué entrega B11a.** La CLI `veridicus analyze` lee una transcripción sintética, llama al juez y al verificador a través del `ModelGateway` y escribe la salida C6, con hallazgos de dos citas verificadas o con `estado: error`. Incluye:
- el puerto `ModelGateway` con **un solo adaptador**, `anonymizing`, que delega todo destino externo en el `Anonymizer` de B10a (C20, CD-04);
- un perfil de ejecución único de demostración, con juez y verificador Anthropic `claude-sonnet-5-5`, de una sola familia declarada y con aviso visible (pregunta 1 = A, CG-U11-09);
- la verificación determinista de las dos citas, sin rebaja (AUTONOMIA-05);
- el escáner de vocabulario y el aviso VE-01 (AUTONOMIA-03);
- una prueba de punta a punta con el `FakeTransport` de B10a, y una corrida real marcada `manual` que lanza el humano con su clave.

Todo se prueba con *fixtures* sintéticos y sin red. El humano pone la etiqueta `analyzer-v0.1.0` al cerrar el Bolt.

**Qué se difiere a B11b (DP-03).** Nada se borra; cada ID diferido queda marcado `Deferred` en la trazabilidad, con destino «B11b (DP-03)»:
- perfiles múltiples, `todo-local` y el archivo con un perfil comercial (BR2.4, BR2.6 a BR2.9; BR7.7);
- el adaptador `local` y `llama-server` (BR10.2);
- ventanas y modo fragmentado (BR4.1, BR4.2);
- el modo incremental (BR1.5, BR5.8);
- el alterno (la rama del alterno de BR7.3), el costo (BR8.4) y el cliente de C21 (BR10.4);
- `evaluate`, el conjunto sintético de nivel 2, el reporte C19 y ZINE (BR11.8, BR12, BR13, BR14);
- el *workflow* `analyzer-level2-gate.yml` (CG-U11-05).

## Decisiones del plan

| ID | Decisión | Origen |
|---|---|---|
| PD-1 | **Cuatro paquetes** con *src layout*, cada uno con su `pyproject.toml` y su `uv.lock`: `libs/incoherence_analyzer/` (`veridicus_incoherence_analyzer`), `libs/model_gateway/` (`veridicus_model_gateway`), `libs/execution_profiles/` (`veridicus_execution_profiles`) y `libs/integrity_policy/` (`veridicus_integrity_policy`). Los contratos de import-linter usan esos nombres, no `libs.*` | TS D1; E-1 de U1 y CG-U10-03 (CG-U11-01) |
| PD-2 | **Un solo adaptador, `anonymizing`.** Todo destino externo pasa por el `Anonymizer` de B10a, que solo atiende Anthropic `claude-sonnet-5-5`. El perfil único `demo-anthropic` tiene juez y verificador Anthropic, `purpose: demonstration`, `same_family_declared: true` y el aviso `same_family` visible en stderr y en `AVISO.txt` (BR2.5; `project.md`). Nunca es un perfil de evaluación | Pregunta 1 = A; CS C13; UW U11; SD DS2; R-3 de U10 (CG-U11-09) |
| PD-3 | La CLI lee el **objeto `transcripcion`** de C6 y arma la `Entrada` con el modo y el perfil (FD-U11-23) | FD-U11-23; BR11.1 (CG-U11-02) |
| PD-4 | `Entrada` y `Salida` **no** se agregan a `veridicus_contracts.analyzer.v1`. U11 valida los diccionarios contra el esquema C6 con `validate_instance` y define sus alias de tipo en `veridicus_incoherence_analyzer`. Así B11a no toca `contracts/`, cuya suite está al límite de 60 s en la CI | Hueco de C17; U01-T31 (CG-U11-03) |
| PD-5 | Los errores nuevos (`InputRejected`, `Cancelled`, `GatewayConfigError`, `CliInterrupted`) van en `libs/errors`, en la jerarquía única, con su `code` estable y su `detail` en español | team.md, Code Style (CG-U11-04) |
| PD-6 | **K-84 y CG-U10-10:** `system` es siempre el texto fijo del *prompt* para el papel y no lleva ningún carácter de la entrada. El testimonio va solo en el mensaje `user`, como JSON (`ensure_ascii=False`, separadores compactos), armado por una única función, `application/messages.py::build_messages`. Lo comprueba una propiedad Hypothesis (paso 8) | BR3.1; SD §5; K-84 = A |
| PD-7 | `cli/composition.py` es la única raíz de composición. Importa `veridicus_anonymizer` **de forma diferida**, solo si el perfil tiene un papel externo, y le pasa `os.environ`; en las pruebas le pasa también el `FakeTransport` | IDS-U11-02; SD §2 |
| PD-8 | La prueba compuesta de AUTONOMIA-04 (AC11.3.3, AC11.3.7, BR7.5, BR10.1) usa el `Anonymizer` real de B10a con el `FakeTransport`; su control negativo usa `veridicus_anonymizer.testing.bypass`. B10a no tiene NER, así que el caso (c), «NER pasado de presupuesto», se cubre con el presupuesto de seudonimización de U10 | SD §4; CG-U10-02 (CG-U11-06) |
| PD-9 | El rojo del paso 3 va en su **propio commit**: `test(analyzer): pruebas en rojo de AUTONOMIA-03/04/05 y contratos de datos`. Su SHA se anota como `ROJO_SHA` en la bitácora de U11-T01 y lo usa el paso 9 | Igual que PD-10 de U10 |
| PD-11 | **Dos esquemas por papel** (R-02). En `data/schemas/` hay dos esquemas para el juez y dos para el verificador:<br>• el **de cable** (`judge.wire.v1.json`, `verifier.wire.v1.json`) es el que viaja en `GenerateRequest.schema` hacia `output_config.format` de Anthropic. No lleva las palabras clave que esa API no admite (`minLength`, `maxLength`, `pattern`, `minimum`, `maximum`, `minItems` > 1);<br>• el **local estricto** (`judge.v1.json`, `verifier.v1.json`) es el que valida la respuesta, con `minLength: 1`, 7 tipos y `additionalProperties: false`.<br>Una prueba de nivel 0 recorre el esquema de cable y falla si encuentra alguna de esas palabras clave | Documentación de salidas estructuradas de Anthropic; `providers/anthropic.py` de B10a |
| PD-12 | **Costura de la CLI** (R-14). `cli/main.py::main()` llama a `run(sys.argv[1:], os.environ)`. `run(argv, env, *, transport=None)` es la única entrada que usan las pruebas, y el `transport` solo llega a `build_anonymizer(env, transport)`. Ningún argumento de línea de comandos ni variable de entorno lo activa | PD-7; SD §2 |
| PD-13 | **Referencia del *prompt*** (R-01). `data/prompt.v1.sha256` guarda, versionado, el SHA-256 de `data/prompt.v1.md`. El cargador lo pone en `EffectiveConfig.prompt_sha256`, y `analyze` lo compara con el hash de los bytes leídos. Si alguien cambia el *prompt* sin actualizar la referencia, la corrida da `salida_invalida` sin llamar, y el paso 8 tiene una prueba de ese caso | BR3.1; CG-U11-12 |
| PD-10 | **Plazo de 2×.** En U10 el *timeout* de `httpx` es por operación, así que una llamada puede pasarse del plazo restante. `application/deadline.py` comprueba el plazo antes y después de cada llamada y da `tiempo_agotado` si se pasó. El exceso posible queda declarado como límite en el README | README de U10; riesgo R-3 |

## Dependencias y punto de partida

- **`main` en `f943b84`**, con B10a ya fusionado:
  - `veridicus-contracts` 0.1.1: C6, C13 (`model_calls.py`), perfiles (`profiles.py`, `profiles.schema.v1.yaml`), `effective-config.v1.yaml`, `limits.v1.yaml`, `canonical.sha256_jcs` e `integrity/notice.v1.yaml`;
  - `libs/errors`;
  - `veridicus-anonymizer` 0.1.0: `build_anonymizer`, `Anonymizer.generate`, `FakeTransport` y `testing/bypass.py`.
- **Dependencias entre paquetes:** los cuatro dependen por ruta de `../../contracts` y de `../errors`. Además:
  - `model_gateway` depende de `execution_profiles`, de donde toma el piso de 270 s (R-03);
  - `incoherence_analyzer` depende de los otros tres;
  - `veridicus-anonymizer` solo entra por el *extra* `cli` de `incoherence_analyzer`, como `{ path = "../anonymizer" }` en `tool.uv.sources` (TS; CS).
- **Lockfiles nuevos, con red, una vez y solo en U11-T01:** `timeout 600 uv lock --directory libs/<P>`.
- **Instalación con red, una vez por worktree:** `timeout 600 uv sync --frozen --directory libs/<P>`, con `--extra cli` en `incoherence_analyzer`. Después, todo corre con `--frozen --offline`.
- **Plazo de llamada de 300 s:** `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300`, que solo baja el techo de C25 (3600). Va en el README y en el comando de la corrida manual. Con un papel externo, el piso de 270 s rechaza cualquier valor menor (R-01).
- **Rama del Bolt:** `bolt/b11a-analyzer`, creada desde `main`. Las tareas entran con `git merge --no-ff` (ML-6) y el humano fusiona a `main` el PR del Bolt.
- **Pruebas sin red:** `pytest-socket` con `--disable-socket` en los cuatro paquetes. B11a no abre ningún socket, ni siquiera a `127.0.0.1`.
- **Sin acceso al clúster:** no se usa `kubectl`, `helm`, `sbatch`, `ssh` ni `scp` (AUTONOMIA-01).
- **Suite de `contracts`:** B11a no toca `contracts/` (PD-4). La tarea correctiva U01-T31 la acelera por su lado.

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

El bloque es idéntico al de U10, con las mismas huellas, porque la postura de pruebas de `org`, `team` y `project` no cambió desde entonces.

**Cómo se aplica el orden del contrato.**
1. **Pasos 1 y 2.** Arman los cuatro paquetes con *stubs* que lanzan `NotImplementedError` y dejan listo el ejecutor de pruebas.
2. **Paso 3.** Escribe en rojo, en su propio commit, las pruebas de las guardias y de los contratos de datos de U11:
   - **AUTONOMIA-05:** verificación de citas, rechazo sin campos, `error` ⇒ hallazgos vacíos, cita restaurada antes de verificar.
   - **AUTONOMIA-03:** vocabulario prohibido en la salida, aviso VE-01, esquema sin campos de veracidad.
   - **AUTONOMIA-04:** un destino externo sin anonimizador no arranca, payload compuesto, fallo cerrado e incidente de anonimización.
   - **Contratos de datos:** salida C6, esquemas cerrados del juez y del verificador, y perfil de ejecución.
3. **Pasos 4 a 12.** Cada capa se implementa y enseguida se prueba. En el paso 9, las pruebas del paso 3 pasan a verde sin cambios, salvo las de la CLI, que pasan a verde en el paso 12.

## Comandos de verificación

Todos se corren desde la raíz del worktree de la tarea (`/workspace/.worktrees/U11-TNN`), son de esta unidad y no usan red, salvo el `uv sync` inicial. `<P>` es uno de los cuatro paquetes y `<m>`, su módulo `veridicus_*`.

**Cobertura.** `addopts` **no** lleva `--cov`. Cada paso mide sus propios módulos con `--cov=<módulo> --cov-branch --cov-fail-under=100`. El 80 % de líneas por paquete se exige en la suite completa (paso 14) y en la CI.

| Uso | Comando |
|---|---|
| Instalación (una vez por worktree, con red) | `timeout 600 uv sync --frozen --directory libs/<P>`. En `incoherence_analyzer`: `timeout 600 uv sync --frozen --extra cli --directory libs/incoherence_analyzer` |
| Suite de un paquete, con su mínimo | `timeout 300 uv run --frozen --offline --directory libs/<P> pytest --cov=<m> --cov-branch --cov-report=json --cov-fail-under=80` |
| Un archivo, sin cobertura | `timeout 300 uv run --frozen --offline --directory libs/<P> pytest <archivo> --no-cov` |
| Ramas de los módulos guardia | `timeout 60 uv run --frozen --offline --directory libs/incoherence_analyzer python -m veridicus_incoherence_analyzer.testing.coverage_gate ../incoherence_analyzer/coverage.json ../model_gateway/coverage.json ../execution_profiles/coverage.json ../integrity_policy/coverage.json` |
| Tipos | `timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src tests` |
| *Lint* y formato | `timeout 120 uv run --frozen --offline --directory libs/<P> ruff check .` y `timeout 120 uv run --frozen --offline --directory libs/<P> ruff format --check .` |
| Fronteras | `timeout 120 uv run --frozen --offline --directory libs/<P> lint-imports` |
| Anonimizador (B10a; tiene que seguir en verde) | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-fail-under=80` |
| Errores (`libs/errors`) | `timeout 60 uv run --frozen --offline --directory libs/errors pytest` |
| Guardias del repositorio | `bash scripts/check-no-cluster-ids.sh`, `bash scripts/check-no-datos-personales.sh`, `bash scripts/check-no-insumos.sh`, `bash scripts/check-no-cluster-apply.sh` y `bash scripts/tests/autoprueba-guardias.sh` |

## Pasos

El riesgo de cada paso sigue ML-4:
- **Alto:** guardias AUTONOMIA, seguridad, contratos y datos. Lo revisa `revisor` con `opus`.
- **Bajo:** andamiaje, configuración y documentación. Lo revisa `revisor` con `sonnet`.

### Paso 1 — Estructura de los cuatro paquetes y errores nuevos · tarea U11-T01

- [x] Crear los cuatro paquetes de PD-1 **copiando el `pyproject.toml` de `libs/anonymizer`** como base (R-12). Cada paquete conserva de esa base:
  - `hatchling`, Python ≥ 3.12, la versión 0.1.0 y `py.typed`;
  - el grupo `dev` (`pytest`, `pytest-cov`, `pytest-socket`, `hypothesis`, `mypy`, `types-jsonschema`, `ruff`, `import-linter`, `pip-audit`);
  - la sección `[tool.mypy]` completa: `mypy_path = "src:../../contracts/src"`, `explicit_package_bases` y el `override` de `openapi_spec_validator`;
  - Ruff con las reglas `S`;
  - `tool.uv.sources`, con las rutas de PD-1 y de «Dependencias».

  Su `uv.lock` se genera con `timeout 600 uv lock --directory libs/<P>`. Módulos de cada paquete:
  - **`incoherence_analyzer`:**
    - `api.py`;
    - `domain/`: `quotes`, `filter`, `run_state`, `output`, `ids`;
    - `application/`: `analyze`, `preflight`, `messages`, `deadline`;
    - `data/`: `prompt.v1.md` y `schemas/`;
    - `cli/`: `main`, `composition`, `io_atomic`, `results_dir`, `messages`;
    - `testing/coverage_gate`;
    - *extra* `cli` con `veridicus-anonymizer`, y el *script* `veridicus = veridicus_incoherence_analyzer.cli.main:main`.
  - **`model_gateway`:** `port.py`, `gateway.py`, `adapters/anonymizing.py` y `testing/` (*fakes* del gateway).
  - **`execution_profiles`:** `loader.py`, `validate.py`, `floors.py`.
  - **`integrity_policy`:** `scan.py`, `notice.py`.
- [x] *Stubs*: cada símbolo público que importan las pruebas del paso 3 existe y lanza `NotImplementedError`. Son `analyze`, `verify_quote`, `gateway.build`, `load_profiles`, `validate_profile`, `load_response_schema`, `scan`, `load_notice` y `cli.main.run`. Las pruebas rojas nunca leen un archivo directamente: todo pasa por estos símbolos (R-07).
- [x] En `libs/errors`, agregar `InputRejected`, `Cancelled`, `GatewayConfigError` y `CliInterrupted`, con `code` y `detail` en español, y sus pruebas (PD-5).
- **Riesgo:** bajo.
- **Verificación:**
  - en cada paquete: `timeout 600 uv lock --directory libs/<P>`, `timeout 600 uv sync --frozen --directory libs/<P>`, `timeout 120 uv lock --check --directory libs/<P>` y `timeout 300 uv run --frozen --offline --directory libs/<P> mypy --strict src`;
  - además: `timeout 60 uv run --frozen --offline --directory libs/errors pytest`.
- **Umbral:** todos terminan con código 0.
- **Cubre:** PD-1, PD-5.

### Paso 2 — Ejecutor de pruebas listo · tarea U11-T01

- [x] En cada paquete: `addopts = "--strict-markers --disable-socket -m 'not manual'"`, sin `--cov`, y `branch = true`. Se declaran dos marcadores: `manual`, para el proveedor real, y `cli`, para las pruebas que pasan por `cli.main.run` (R-10).
- [x] En `libs/incoherence_analyzer/tests/conftest.py` y en el de `libs/execution_profiles/tests/`: con la opción `--rojo`, un `pytest_runtest_makereport` con `hookwrapper=True` marca como `ERROR` toda prueba que falle por una causa distinta de `NotImplementedError`. Para eso toma el reporte de la fase `call` y lo reescribe con `when="setup"` y `outcome="failed"`, que pytest muestra como `ERROR` (N-03). Una prueba del propio `conftest`, con control negativo, comprueba que ese *hook* funciona (R-07).
- [x] En cada paquete, `tests/test_package.py` importa el paquete y comprueba `py.typed`. Una prueba demuestra que `pytest-socket` bloquea una conexión.
- **Riesgo:** bajo.
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/<P> pytest tests/test_package.py -q` en los cuatro paquetes.
- **Umbral:** código 0 y al menos 2 pruebas por paquete.
- **Cubre:** Testing Contract (el ejecutor está listo antes de la primera prueba).

### Paso 3 — ROJO: guardias AUTONOMIA-03/04/05 y contratos de datos · tarea U11-T01

Estas pruebas se escriben primero y se ejecutan en rojo, en un commit propio (PD-9). Fallan por `NotImplementedError`, nunca por un error de recolección. Todo va en `libs/incoherence_analyzer/tests/`, salvo lo que se indica.

- [x] **`guards/test_autonomia_05_quotes.py`** (AUTONOMIA-05; BR5.2 a BR5.7):
  - Un hallazgo sin `hecho`, `tipo`, `cita_a`, `cita_b` u `observaciones`, o con alguno de ellos solo con espacios, se descarta con `campo_faltante` y no sale.
  - Una cita alterada en un carácter, una cita de otro turno y una cita inventada se descartan con `cita_no_verificada` o `cita_en_otro_turno`.
  - Se aplica la regla del piloto: solo se normalizan espacios, « […] » une fragmentos del mismo turno en orden y una cita en un turno `ENT` o plegado se acepta con aviso.
  - **Cita restaurada antes de verificar:** con el `Anonymizer` de B10a y el `FakeTransport`, una respuesta con marcas se restaura y la cita se verifica contra el turno original. Una marca alterada (`altered_markers`) descarta el candidato.
  - Propiedad Hypothesis: toda subcadena exacta de un turno verifica en ese turno, y ninguna cadena con un carácter cambiado verifica.
- [x] **`guards/test_autonomia_05_error.py`** (BR7.1, BR5.1): se prueba con cada error del gateway (`InvalidOutput`, `ContentBlocked`, `Timeout`, `ProviderError`, `AnonymizerUnavailable`) y con un candidato mal formado. En todos los casos sale `estado: error`, con el `error.codigo` correcto, `hallazgos: []` y `descartes: []`; nunca un resultado parcial.
- [x] **`guards/test_autonomia_03_vocabulary.py`** (BR9.1 a BR9.5):
  - Un `hecho` o unas `observaciones` con vocabulario de C8 se descartan con `vocabulario_prohibido`, aunque la cita literal que lo contiene se conserva.
  - La salida C6 no tiene ningún campo de veracidad.
  - El aviso VE-01 y el aviso `same_family` del perfil de demostración salen en stderr y en `AVISO.txt`. Sin el aviso VE-01, la CLI termina en 3 sin hacer ninguna llamada. Estas dos pruebas llevan `@pytest.mark.cli`.
- [x] **`guards/test_autonomia_04_composite.py`**: la **prueba compuesta** (AC11.3.3, AC11.3.7, BR7.5, BR10.1; PD-8).
  - Un perfil con papel externo y sin `Anonymizer` inyectado no arranca: `GatewayConfigError`, CLI 3 y 0 peticiones.
  - Con el `Anonymizer` real y el `FakeTransport`, ningún cuerpo capturado contiene una entidad sembrada. Control negativo con `bypass`: la misma aserción falla.
  - BR7.4, con 0 peticiones y sin reintento. Sale `anonimizador_no_disponible` en estas cuatro variantes:
    - (a) clave ausente;
    - (b) presupuesto de seudonimización agotado;
    - (c) el proveedor inyectado lanza una excepción ajena, por ejemplo `RuntimeError` en la seudonimización;
    - (d) el proveedor inyectado no responde dentro del plazo.
  - (e) El anonimizador no se puede construir: `build_anonymizer` lanza `ConfigInvalidProfileError` o `ConfigInvalidLimitError`. Eso es un error de configuración y da CLI 3, con 0 llamadas y **sin** salida C6. Esta prueba lleva `@pytest.mark.cli`.
  - Una llamada externa con `anonymized: false` da `incidente_anonimizacion` y CLI 4, con precedencia sobre los demás errores (BR7.6). Esta prueba lleva `@pytest.mark.cli`.
  - La prueba «perfil externo sin `Anonymizer` → CLI 3» también lleva `@pytest.mark.cli`. Las demás de este archivo llaman a `analyze` y a `gateway.build` directamente.
- [x] **`guards/test_k84_system_fixed.py`** (PD-6): en cada petición capturada, `system` es idéntico byte a byte al texto del *prompt* del papel, y ninguna cadena de la transcripción aparece en `system`.
- [x] **`contracts/test_c6_output.py`** (BR8.1): la salida de una corrida sintética valida contra el esquema C6 de salida con `validate_instance`. Una salida que no valida se sustituye por la salida en error.
- [x] **`contracts/test_response_schemas.py`** (BR3.4; PD-11), a través de `load_response_schema(role, kind)`:
  - los esquemas locales del juez y del verificador son cerrados (`additionalProperties: false`, `minLength: 1`, 7 tipos), y un candidato con un campo de más se rechaza;
  - los esquemas de cable no llevan ninguna palabra clave que Anthropic no admita;
  - control negativo: un esquema de cable con `minLength` hace fallar la comprobación.
- [x] **`libs/execution_profiles/tests/contracts/test_profile_contract.py`**, a través de `load_profiles` y `validate_profile` (R-07):
  - el perfil único de `config/profiles.yaml` valida con `profiles.validate(..., key_prefix="VERIDICUS_", kind="analyzer")` (R-01);
  - su huella JCS no contiene el valor de ninguna clave (BR2.10);
  - un perfil con un campo de más se rechaza;
  - un perfil con juez y verificador de la misma `family` y `purpose` distinto de `demonstration` se rechaza (BR2.5).
- **Riesgo:** alto (guardias AUTONOMIA-03, 04 y 05).
- **Verificación:**
  - `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts --collect-only -q`
  - `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=line --rojo`
  - `timeout 300 uv run --frozen --offline --directory libs/execution_profiles pytest tests/contracts -p no:cacheprovider -rfE --tb=line --rojo`
- **Umbral:**
  - la recolección termina con código 0, 0 errores y al menos 35 pruebas;
  - las dos ejecuciones terminan con código 1, con el 100 % de las pruebas en `FAILED` y ninguna en `ERROR`. Con `--rojo`, cualquier fallo por una causa distinta de `NotImplementedError` cuenta como `ERROR`;
  - el commit del rojo existe y su SHA queda en la bitácora como `ROJO_SHA`;
  - la revisión corta del rojo (ML-13) sale aprobada antes de ese commit.
- **Cubre:** AC11.3.3, AC11.3.7, AC11.3.8; BR1.1, BR2.5, BR2.10, BR3.1, BR3.4, BR5.1 a BR5.7, BR7.1, BR7.4 a BR7.6, BR8.1, BR9.1 a BR9.5, BR10.1.

### Paso 4 — Perfiles de ejecución y configuración (arranque de F8) · tarea U11-T02

- [ ] **`execution_profiles/loader.py`:**
  - carga `config/profiles.yaml` con el cargador seguro y lo valida con `profiles.validate` de U1;
  - llama a `limits.load(environ)`;
  - resuelve la `EffectiveConfig` (`effective-config.v1.yaml`), con huellas `canonical.sha256_jcs` que no incluyen el valor de la clave.
- [ ] **`execution_profiles/validate.py`:**
  - BR2.1;
  - BR2.2: la variable de `api_key_ref` existe en el entorno; si no, CLI 3 nombrando la variable;
  - BR2.3: `base_url` privada solo en destinos locales;
  - BR2.5: misma familia solo con `purpose: demonstration` y `same_family_declared`;
  - BR2.11: la configuración es de solo lectura.
- [ ] **`execution_profiles/floors.py`** (NFRD-U11-03): `COMMERCIAL_MIN_CALL_TIMEOUT_S = 270`. Con un papel externo, 269 falla y 270 arranca.
- [ ] **`config/profiles.yaml`** (R-01; CG-U11-12): `schema_version: "1.0.0"` y **un solo perfil**, `demo-anthropic`. Solo lleva campos de `profiles.schema.v1.yaml` y `profile-base`:
  - `roles.judge` y `roles.verifier`: los dos con `scope: external`, proveedor `anthropic`, modelo `claude-sonnet-5-5`, `family: claude` y `api_key_ref: VERIDICUS_ANTHROPIC_API_KEY`;
  - `role_aliases: {verifier_permuted: verifier}`;
  - `permutation: true`, sin `fallback_provider`;
  - `purpose: demonstration` y `same_family_declared: true`.

  `prompt_sha256` y los límites **no** van en el perfil; viven en la `EffectiveConfig` (PD-13; «Dependencias»). Antes de escribir el perfil, el codificador lee `profile-base.schema.v1` y anota en la bitácora los nombres exactos de los campos de cada papel.
- [ ] Prueba de que el perfil escrito valida con `profiles.validate(..., kind="analyzer")` real, sin *stub*. Esta prueba no forma parte del rojo.
- **Riesgo:** alto (esta configuración decide si salen datos).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/execution_profiles pytest --cov=veridicus_execution_profiles.validate --cov=veridicus_execution_profiles.floors --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0, al menos 10 pruebas, 100 % de ramas en `validate.py` y `floors.py`, y la prueba de contrato del paso 3 pasa.
- **Cubre:** BR2.1, BR2.2, BR2.3, BR2.5, BR2.10, BR2.11; NFRD-U11-03.

### Paso 5 — Escáner de vocabulario y aviso VE-01 · tarea U11-T02

- [ ] `integrity_policy/scan.py`: `scan(text, literal_sources)` con la lista de C8 de `contracts`. Excluye las citas literales y la cadena completa del aviso (BR9.1 a BR9.4).
- [ ] `integrity_policy/notice.py`: lee `contracts/integrity/notice.v1.yaml` y devuelve el texto y la versión. Si el archivo falta o no trae versión, lanza el error de configuración (BR9.5).
- [ ] `tests/test_scan_cases.py` (BR9.4; R-06; N-01): una prueba parametrizada ejecuta **todos** los casos `rule: vocabulary` de `contracts/integrity/scan-cases.v1.yaml` y falla si alguno no da lo esperado.
  - Los casos `rule: clarification` son de U8 (FD-U8-09) y quedan fuera de U11.
  - Otra prueba fija el conjunto de valores de `rule` en `{vocabulary, clarification}`. Si aparece cualquier otro, la suite falla.
  - El control negativo es un caso `vocabulary` con el resultado esperado invertido, que tiene que fallar.
- **Riesgo:** alto (AUTONOMIA-03).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/integrity_policy pytest --cov=veridicus_integrity_policy.scan --cov=veridicus_integrity_policy.notice --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:**
  - código 0;
  - al menos 8 pruebas, más todos los casos de `scan-cases.v1.yaml`;
  - un caso positivo y uno negativo por cada término de la lista;
  - 100 % de ramas.
- **Cubre:** BR9.1 a BR9.5; AUTONOMIA-03 (escaneo).

### Paso 6 — `ModelGateway`: puerto, armado y adaptador `anonymizing` · tarea U11-T03

- [ ] `port.py`: `ModelGateway.generate(req: GenerateRequest) -> GenerateResult`. Solo lanza los errores de `model_calls` (C13).
- [ ] `gateway.py::build(config, anonymizing_provider=None)`:
  - recorre los papeles;
  - `scope: external` exige el proveedor inyectado y el piso de 270 s, que importa de `veridicus_execution_profiles.floors`; si falta alguno, lanza `GatewayConfigError`;
  - `scope: local` lanza `GatewayConfigError` («adaptador local diferido a B11b»);
  - registra cada `ModelCall` en orden y mide la latencia en memoria, fuera de C6.
- [ ] `adapters/anonymizing.py`: delega `generate(req)` en el `AnonymizingProvider` y no reintenta (BR10.3). Deja pasar los errores de `model_calls` tal cual. Cualquier otra excepción del proveedor la traduce a `AnonymizerUnavailable`, conservando la causa sin testimonio (BR7.4; SD; R-05).
- [ ] `testing/`: un *fake* determinista del gateway, para las pruebas de `incoherence_analyzer` (team.md, Dobles de prueba).
- **Riesgo:** alto (frontera de salida de datos).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/model_gateway pytest --cov=veridicus_model_gateway --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0, al menos 8 pruebas y 100 % de ramas en `adapters/anonymizing.py` y `gateway.py`.
- **Cubre:** BR10.1, BR10.3; C13 (la parte del puerto).

### Paso 7 — Dominio: verificación de citas, filtro, estado y salida · tarea U11-T03

- [ ] `domain/quotes.py::verify_quote(turn_text, quote) -> QuoteCheck`: función pura con la regla del piloto (`project.md`).
- [ ] `domain/filter.py`: filtro sin llamadas, en el orden fijo de BR5.2 (marca alterada, campo vacío, `cita_a`, `cita_b`, vocabulario), más la deduplicación por par no ordenado (BR4.3).
- [ ] `domain/run_state.py`: la máquina de estados de la corrida y `fail`, con la precedencia de `incidente_anonimizacion` (BR7.1, BR7.6).
- [ ] `domain/output.py` e `ids.py`: arman la salida C6.
  - `id` determinista con la forma `<entrevista>-Cnn` (BR8.2);
  - `pagina` y `avisos` tomados del turno citado;
  - `registro.llamadas` con la tabla de papeles (BR8.3);
  - `fragmentado: false` declarado (BR8.5);
  - sin `observaciones_conductor` (BR8.6);
  - la misma entrada da la misma salida (BR8.7).
- **Riesgo:** alto (AUTONOMIA-05).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/domain --cov=veridicus_incoherence_analyzer.domain --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:**
  - código 0;
  - al menos 20 pruebas;
  - 100 % de ramas en `domain/`;
  - `tests/domain/test_quotes_perf.py` mide con `time.perf_counter` la verificación de una cita sobre un turno de 20 000 caracteres y afirma ≤ 150 ms, que es la meta de 50 ms con el margen 3× de la CI (PR; R-09).
- **Cubre:** BR4.3, BR5.2 a BR5.7, BR7.1, BR7.6, BR8.2, BR8.3, BR8.5 a BR8.7.

### Paso 8 — *Prompt*, mensajes y esquemas de respuesta · tarea U11-T03

- [ ] `data/prompt.v1.md`: un solo archivo para el juez y el verificador, que se lee con `importlib.resources`. `prompt_sha256` es el SHA-256 de sus bytes y debe coincidir con el de la configuración; si no coincide, la corrida da `salida_invalida` sin llamar (BR3.1).
- [ ] `data/prompt.v1.sha256` con la referencia del *prompt* (PD-13). Una prueba cambia un byte del *prompt* en memoria y comprueba que da `salida_invalida` sin llamar.
- [ ] En `data/schemas/`, los esquemas locales `judge.v1.json` y `verifier.v1.json`, cerrados (BR3.4), y los de cable `judge.wire.v1.json` y `verifier.wire.v1.json` (PD-11). El esquema de cable es el que va en `GenerateRequest.schema`.
- [ ] `tests/application/test_prompt_through_anonymizer.py` (R-14): el texto del *prompt* pasa por el `Anonymizer` real sin ninguna marca. Así el `system` que sale es byte a byte el del archivo.
- [ ] `application/messages.py::build_messages` (PD-6):
  - `system` fijo por papel;
  - `user` con el JSON de los turnos para el juez, y con `{hecho, tipo, cita_a, cita_b}` para el verificador (BR3.3);
  - con la permutación, las citas van intercambiadas.
- [ ] El texto del *prompt* no lleva vocabulario de C8; lo comprueba el escáner del paso 5.
- **Riesgo:** alto (es lo que sale hacia el proveedor).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/application/test_messages.py tests/application/test_prompt_through_anonymizer.py tests/contracts/test_response_schemas.py --cov=veridicus_incoherence_analyzer.application.messages --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:**
  - código 0 y al menos 8 pruebas;
  - una propiedad Hypothesis sobre transcripciones sintéticas: `system` idéntico byte a byte, y `user` se vuelve a parsear igual;
  - 100 % de ramas.
- **Cubre:** BR3.1, BR3.3, BR3.4; K-84 (CG-U10-10).

### Paso 9 — `analyze`: validación previa, juez, verificador y permutación (F1 a F7) · tarea U11-T04

- [ ] `application/preflight.py` (BR1.1 a BR1.4): todo se comprueba antes de llamar, y un fallo lanza `InputRejected`.
  - esquema C6 de entrada (Draft 2020-12);
  - límites de C25: 20 000 caracteres por turno, 2 000 turnos y 250 000 caracteres en total;
  - consentimiento según el origen;
  - transferencia autorizada;
  - perfil aprobado.
- [ ] `application/deadline.py` (BR7.2; PD-10): `timeout_s = min(model_call_timeout_s, plazo − ahora)`; la cancelación se revisa antes de cada llamada y el plazo, después de cada llamada.
- [ ] `application/analyze.py` (BR3.2, BR6.1 a BR6.4):
  - una sola ventana con todos los turnos, sin fragmentar, porque el juez es externo;
  - después, el filtro;
  - una llamada `verifier` por cada sobreviviente, en el orden del primer turno citado;
  - con `permutation: true`, la llamada `verifier_permuted` siempre va después de la directa;
  - los descartes `rechazado_verificador` y `rechazado_permutacion`;
  - nunca lanza una excepción por un fallo del modelo.
- [ ] `api.py`: `analyze(entrada, config, gateway, cancelled=None) -> Salida`. Además, una clase `IncoherenceAnalyzer` que cumple el `Protocol` de C17 y delega en esa función (CG-U11-03; R-15).
- [ ] `tests/application/test_run_perf.py` (R-09): con el *fake* del gateway, una corrida de una entrevista sintética de 2 000 turnos tarda ≤ 6 s, medido con `time.perf_counter`. Es la meta de 2 s con el margen 3× de la CI.
- [ ] Las pruebas rojas del paso 3 pasan a verde **sin cambiarlas**, incluida `test_k84_system_fixed.py`, que necesita `analyze` (N-02). La excepción son las de la CLI, que pasan en el paso 10.
- **Riesgo:** alto (AUTONOMIA-05 de punta a punta).
- **Verificación:**
  - `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/application tests/guards tests/contracts --cov=veridicus_incoherence_analyzer.application --cov=veridicus_incoherence_analyzer.api --cov-branch --cov-fail-under=100 --cov-report=term-missing -m "not cli and not manual"`
  - `git -C /workspace/.worktrees/U11-T04 diff --exit-code <ROJO_SHA> -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts`. `<ROJO_SHA>` es el SHA de 40 caracteres de la línea `ROJO_SHA:` de `docs/loop/bitacoras/U11-T01.md`; el orquestador lo escribe literal en el archivo de la tarea U11-T04 (R-09).
- **Umbral:** los dos comandos terminan con código 0, el *diff* sale vacío y hay 100 % de ramas en `application/preflight.py`, `application/analyze.py`, `application/deadline.py` y `api.py`.
- **Cubre:** AC11.3.8; BR1.1 a BR1.4, BR3.2, BR6.1 a BR6.4, BR7.2; F1 a F7.

### Paso 10 — CLI `veridicus analyze` (F9) · tarea U11-T05

- [ ] `cli/main.py`, con `argparse` y la costura de PD-12 (`main()` → `run(argv, env, *, transport=None)`):
  - uso: `veridicus analyze <archivo.json | directorio> --perfil <nombre> [--salida <dir>]`;
  - lee el objeto `transcripcion` y arma la `Entrada` (PD-3);
  - al inicio escribe en stderr el aviso VE-01 y el aviso `same_family`, y los deja también en `AVISO.txt` dentro del directorio de salida (BR9.5; PD-2).
- [ ] `cli/composition.py` (PD-7):
  - arranca en el orden de RD: límites, perfiles, *prompt*, aviso y gateway con el piso;
  - importa `veridicus_anonymizer` de forma diferida, solo cuando hay un papel externo;
  - cualquier fallo da CLI 3 y 0 llamadas.
- [ ] `cli/io_atomic.py` y `cli/results_dir.py`:
  - escritura atómica de `<nombre>.salida.json` (BR11.4);
  - validación previa completa del lote, y 0 archivos si falla (BR11.2);
  - una salida con origen corpus solo puede ir a un directorio que Git no rastrea (BR11.5);
  - BR11.6 (R-11): `.gitignore` cubre `resultados-locales/`, y una prueba de nivel 0 lo comprueba con `git check-ignore`. El control negativo es una ruta que Git sí rastrea, que tiene que fallar.
- [ ] Sin `reporte.json` en B11a. Con el código 4, la CLI escribe solo la salida en error (CG-U11-13).
- [ ] `cli/messages.py`: catálogo cerrado de mensajes en español. stderr nunca lleva testimonio, y un *canary* lo comprueba (BR11.7).
- [ ] Códigos de salida: 0, 2, 3, 4 y 5 (BR11.3).
- **Riesgo:** alto (fallo cerrado y frontera del disco).
- **Verificación:**
  - `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/cli tests/guards -m cli --cov=veridicus_incoherence_analyzer.cli.composition --cov-branch --cov-fail-under=100 --cov-report=term-missing`
  - `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/cli --cov=veridicus_incoherence_analyzer.cli --cov-report=term-missing --cov-fail-under=90`
- **Umbral:**
  - los dos comandos terminan con código 0;
  - al menos 12 pruebas, con una por código de salida y una por regla BR11;
  - las pruebas `cli` del paso 3 pasan sin cambios;
  - 100 % de ramas en `composition.py`, que es módulo guardia, y ≥ 90 % de líneas en `cli/` (R-08).
- **Cubre:** BR9.5, BR11.1 a BR11.7; F9.

### Paso 11 — Fronteras · tarea U11-T05

- [ ] Contratos de import-linter (SD §1):
  - `u11-no-infra`: nada de `redis`, `kubernetes`, `psycopg`, `asyncpg`, `sqlalchemy` ni `prometheus_client`;
  - `gateway-no-anonymizer` y `core-no-anonymizer`, con `cli.composition` como única excepción;
  - `layers`: `domain` no importa `application`, `adapters`, `cli` ni `httpx`.
- [ ] En `tests/boundaries/`:
  - por cada contrato, un módulo que lo viola y hace fallar `lint-imports` (control negativo);
  - una prueba AST que impide que un `__init__` reexporte `cli.composition`.
- [ ] La lista prohibida de `libs/anonymizer/pyproject.toml` suma `veridicus_integrity_policy` (CG-U11-08).
- **Riesgo:** alto (fronteras de seguridad).
- **Verificación:** `timeout 120 uv run --frozen --offline --directory libs/<P> lint-imports` en los cuatro paquetes y en `libs/anonymizer`, y `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/boundaries --no-cov -q`
- **Umbral:** `lint-imports` termina con 0 en los cinco paquetes. Las pruebas terminan con 0 y son al menos 5, y cada control negativo hace fallar `lint-imports` dentro de su prueba.
- **Cubre:** BR10.5; SD §1.

### Paso 12 — Punta a punta con el doble y corrida manual · tarea U11-T05

- [ ] `tests/e2e/test_cli_fake.py` corre la CLI por su punto de entrada sobre transcripciones sintéticas de `tests/fixtures/`. Usa el `Anonymizer` real y el `FakeTransport` de B10a, con respuestas grabadas del juez y del verificador, y comprueba que:
  - una contradicción sembrada produce ≥ 1 hallazgo con sus dos citas verificadas y código 0;
  - un relato coherente produce 0 hallazgos y código 0;
  - una respuesta del juez con una cita alterada produce un descarte, y ningún hallazgo sale con esa cita;
  - las pruebas de la CLI del paso 3 pasan sin cambios.
- [ ] `tests/manual/test_real_provider.py`, marcada `manual` y excluida por defecto. Corre la CLI con el proveedor real y una entrevista **sintética**, usando la clave de `VERIDICUS_ANTHROPIC_API_KEY` y `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300`. La lanza el humano **el viernes 27, en cuanto cierre U11-T05** (R-13). Su resultado no se versiona.
  - **Comando**, que queda en el README y en la bitácora de U11-T05: `timeout 900 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/manual -m manual --no-cov --force-enable-socket -q` (R-04).
- **Riesgo:** alto (es la demostración del sábado).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/e2e --no-cov -q` y `timeout 300 uv run --frozen --offline --directory libs/incoherence_analyzer pytest tests/manual -m manual --no-cov --force-enable-socket --collect-only -q`
- **Umbral:** el primer comando termina con 0 y al menos 4 pruebas. El segundo recolecta al menos 1 prueba, y la corrida por defecto no la ejecuta.
- **Cubre:** demostración esperada de B11 (`bolt-plan.md`); AC11.3.3 y AC11.3.7 de punta a punta.

### Paso 13 — CI de nivel 0 · tarea U11-T06

- [ ] `.github/workflows/analyzer-level0.yml`, **sin filtro por rutas** y con el patrón de `anonymizer-level0.yml`:
  - un *job* por paquete con `uv sync --frozen`, `uv lock --check`, `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, `pip-audit` (`HIGH`+ con corrección) y la suite con su mínimo;
  - el `coverage_gate`;
  - disparo también con `tags: ["analyzer-v*"]`;
  - acciones fijadas por SHA (solo `actions/*` y el `astral-sh/setup-uv` ya permitido) y `permissions: contents: read`.
- [ ] Sin `analyzer-level2-gate.yml` en B11a (CG-U11-05).
- **Riesgo:** bajo (configuración).
- **Verificación:** `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov` y `bash scripts/check-no-cluster-apply.sh`
- **Umbral:** los dos comandos terminan con código 0, y la prueba recorre todos los *workflows* reales, incluido el nuevo.
- **Cubre:** NFR13 de U11 (CI); CI §8 (recorte de B11a).

### Paso 14 — Suite completa y compuertas de calidad · tarea U11-T06

- [ ] `testing/coverage_gate.py` lee los `coverage.json` de los cuatro paquetes y exige:
  - el 100 % de ramas en los módulos guardia: `domain/quotes.py`, `domain/filter.py`, `domain/run_state.py`, `domain/output.py`, `application/preflight.py`, `cli/composition.py`, `model_gateway/adapters/anonymizing.py`, `integrity_policy/scan.py` y `execution_profiles/validate.py`;
  - el 80 % de líneas por paquete;
  - fallar cerrado si falta alguno de esos archivos;
  - tener sus propias pruebas, con dos controles negativos (R-09): un `coverage.json` con un módulo guardia al 99 % de ramas y otro sin uno de los archivos guardia. Los dos tienen que hacer fallar la compuerta.
- [ ] Correr en el worktree todo lo de «Comandos de verificación».
- **Riesgo:** bajo (agregación).
- **Verificación:** las filas «Suite de un paquete», «Ramas de los módulos guardia», «Tipos», «*Lint* y formato», «Fronteras», «Anonimizador», «Errores» y «Guardias del repositorio» de la tabla de comandos.
- **Umbral:** todos terminan con código 0, incluidas las pruebas de tiempo de los pasos 7 y 9. La suite de cada paquete termina dentro de su `timeout 300`.
- **Cubre:** Testing Posture (cobertura y herramientas); RD (guardias).

### Paso 15 — Documentación, demostración y versión · tarea U11-T06

- [ ] `libs/incoherence_analyzer/README.md`, en español. Explica:
  - qué hace la CLI y el comando de la demostración;
  - las variables `VERIDICUS_*`;
  - el perfil único con su aviso de una sola familia;
  - el comando de la corrida manual;
  - los límites declarados (PD-10, una sola familia) y lo que queda diferido a B11b.
- [ ] `libs/incoherence_analyzer/examples/demo_fake.py`: corre la CLI con el `FakeTransport` sobre una transcripción sintética e imprime la ruta de la salida y el número de hallazgos.
- [ ] En `docs/glosario.md`, la sección de U11 (EN: `AnalysisRun`, `JudgeCandidate`, `DiscardRecord`…). En `docs/devlog.md`, la entrada del Bolt.
- [ ] Los cuatro paquetes quedan en la versión 0.1.0. La etiqueta `analyzer-v0.1.0` la pone el humano.
- **Riesgo:** bajo (documentación).
- **Verificación:** `timeout 120 uv run --frozen --offline --directory libs/incoherence_analyzer python examples/demo_fake.py` y `bash scripts/check-no-datos-personales.sh`
- **Umbral:** los dos comandos terminan con 0, y la salida de la demostración nombra el archivo `.salida.json` y al menos 1 hallazgo.
- **Cubre:** demostración del sábado (cambio 06); NFR14 de U11 (documentación).

## Olas del loop

| Tarea | Pasos | Riesgo | Revisor | Depende de | Ola |
|---|---|---|---|---|---|
| U11-T01 | 1, 2, 3 | alto (por el paso 3) | `opus` | — | 1 |
| U11-T02 | 4, 5 | alto | `opus` | T01 | 2 |
| U11-T03 | 6, 7, 8 | alto | `opus` | T02 | 3 |
| U11-T04 | 9 | alto | `opus` | T03 | 4 |
| U11-T05 | 10, 11, 12 | alto | `opus` | T04 | 5 |
| U11-T06 | 13, 14, 15 | bajo | `sonnet` | T05 | 6 |

**Las olas son secuenciales** (R-03). T03 usa `integrity_policy.scan` en el filtro del paso 7 y en la prueba del *prompt* del paso 8, y toma el piso de 270 s de `execution_profiles.floors` en el paso 6. Las dos piezas las construye T02.

**Corrida real el viernes** (R-13). Apenas U11-T05 sale VERDE y se fusiona en la rama del Bolt, el orquestador le pasa al humano el comando de la corrida manual. Así, un problema de clave, de red o del proveedor aparece el viernes y no el sábado.

**U11-T04 tiene un solo paso**, por debajo de los 3 de ML-3, porque es la orquestación de todo el flujo y conviene revisarla aparte. En total son 6 tareas, menos que la meta de 8 de ML-3, y cada una admite como máximo dos rondas (ML-5).

## Trazabilidad

| ID | Estado | Paso o destino |
|---|---|---|
| AC11.3.3, AC11.3.7 (lado de U11) | En B11a | 3, 6, 12 |
| AC11.3.8 | En B11a | 3, 9 |
| BR1.1 a BR1.4 | En B11a | 3, 9 |
| BR1.5, BR5.8 | Deferred (modo incremental) | B11b (DP-03; CG-U11-07) |
| BR2.1, BR2.2, BR2.3, BR2.5, BR2.10, BR2.11 | En B11a | 3, 4 |
| BR2.4, BR2.6 a BR2.9 | Deferred | B11b (DP-03) |
| BR3.1 a BR3.4 | En B11a | 3, 8, 9 |
| BR4.3 | En B11a | 7 |
| BR4.1, BR4.2 | Deferred | B11b (DP-03) |
| BR5.1 a BR5.7 | En B11a | 3, 7 |
| BR6.1 a BR6.4 | En B11a | 9 |
| BR7.1, BR7.2, BR7.4, BR7.5, BR7.6 | En B11a | 3, 7, 9 |
| BR7.3 | En B11a sin alterno; la rama del alterno, Deferred | 9; B11b (DP-03) |
| BR7.7 | Deferred | B11b (DP-03) |
| BR8.1 a BR8.3, BR8.5 a BR8.7 | En B11a | 3, 7 |
| BR8.4 | Deferred | B11b (DP-03) |
| BR9.1 a BR9.5 | En B11a | 3, 5, 10 |
| Casos `rule: clarification` de `scan-cases.v1.yaml` | Deferred | U8 assistant-extras (FD-U8-09; N-01) |
| BR10.1, BR10.3, BR10.5 | En B11a | 3, 6, 11 |
| BR10.2, BR10.4, BR10.6 | Deferred | B11b (DP-03) |
| BR11.1 a BR11.7, sin `reporte.json` | En B11a | 10 |
| `reporte.json` de BR11.1 y BR11.3 (C19, `kind: run`) | Deferred | B11b (DP-03; CG-U11-13) |
| BR11.8, BR12.1–BR12.7, BR13.1–BR13.5, BR14.1–BR14.5 | Deferred | B11b (DP-03) |

## Precisiones para decidir en la aprobación

No se edita ningún artefacto aprobado. En la aprobación decides cuáles se llevan al original; cada una va en su propio commit.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| CG-U11-01 | SD §1 y LC (rutas `libs/incoherence_analyzer/...` e imports `libs.*`) | Se usa *src layout* `libs/<pkg>/src/veridicus_<pkg>/`, y los contratos de import-linter usan los nombres `veridicus_*` | E-1 de U1; CG-U10-03 |
| CG-U11-02 | `bolt-plan.md` DP-03 («lee la entrada C6») | La CLI lee el objeto `transcripcion` de C6 y arma la `Entrada`, como fija FD-U11-23 | FD-U11-23 |
| CG-U11-03 | C17 (`contract-summary.md`: `Entrada` y `Salida` de `contracts.analyzer.v1`, y `IncoherenceAnalyzer` como `Protocol`) | Los tipos no se agregan a `contracts` en B11a. U11 valida contra el esquema C6 con `validate_instance(esquema, instancia, build_registry())` y define sus propios alias; los tipos se agregan cuando U4 los necesite. `api.py` ofrece la función `analyze` y la clase `IncoherenceAnalyzer`, que cumple el `Protocol` de C17 | PD-4; R-15; suite de `contracts` al límite |
| CG-U11-04 | `libs/errors` (U1) | Se agregan `InputRejected`, `Cancelled`, `GatewayConfigError` y `CliInterrupted` | PD-5 |
| CG-U11-05 | `cicd-pipeline.md` (`analyzer-level2-gate.yml`, IDS-U11-12) | La etiqueta `analyzer-v0.1.0` no exige reporte de nivel 2: el *workflow* `analyzer-level2-gate.yml` y el nivel 2 pasan a B11b | DP-03 |
| CG-U11-06 | SD §4 (prueba compuesta con el NER de prueba) y BR7.4 | B10a no tiene NER. El caso del NER pasado de presupuesto se cubre con el presupuesto de seudonimización de U10, variante (b). Las variantes de BR7.4 (caído, excepción ajena y sin respuesta) se cubren con (c), (d) y (e) del paso 3 | CG-U10-02; R-05 |
| CG-U11-07 | FS F9 (`--modo incremental`) | En B11a la CLI corre solo en modo final. El modo incremental, BR1.5 y BR5.8 pasan a B11b | Tope de 15 pasos (cambio 06) |
| CG-U11-08 | `libs/anonymizer/pyproject.toml` (lista prohibida de U10) | La lista prohibida suma `veridicus_integrity_policy` | Revisión del diseño de U11 |
| CG-U11-09 | `bolt-plan.md` DP-03 («un adaptador compatible con OpenAI») y TS/SR (`comercial-piloto`, NFR-U11-01) | El único adaptador de B11a es `anonymizing`, hacia Anthropic. El perfil es `demo-anthropic`: de demostración, de una sola familia declarada y con aviso visible. `comercial-piloto` (juez Anthropic y verificador local gpt-oss-20b) pasa a B11b junto con el adaptador local | Pregunta 1 = A (humano, 2026-11-26); contradicción entre DP-03, el diseño y B10a |
| CG-U11-10 | SD (`Anonymizer.build(transport=...)`) | En el código, la función se llama `build_anonymizer(env, transport)` | Código de B10a |
| CG-U11-11 | `unit-of-work-dependency.md` (grafo de Units Generation) | **Aristas temporales** `identity-access → incoherence-analyzer` y `platform → incoherence-analyzer`. El motor ordena Code Generation por capas del grafo y U3 y U2 frenaban a U11. No cambian el orden real de entrega (B4 y B2 ya iban después de B11 en `bolt-plan.md`). Se quitan al cerrar B11a, en su propio commit | Decisión del humano (A), 2026-11-26 |

| CG-U11-12 | TS (`model_call_timeout_s = 300`), SD/RD (`prompt_sha256` «de la configuración») y SD:85 (PD-11) | El perfil solo lleva campos de `profiles.schema.v1.yaml`. Los 300 s se fijan con `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300`. La referencia del *prompt* es `data/prompt.v1.sha256`. Los esquemas de respuesta se separan en uno de cable y uno local, porque la API de Anthropic no admite `minLength` en `output_config.format` | R-01; R-02 |
| CG-U11-13 | FS F9 y BR11.1/BR11.3 (`reporte.json`, C19 `kind: run`) | B11a no escribe `reporte.json`: el reporte C19 entra con el costo y las métricas en B11b. Con el código 4, la CLI escribe solo la salida en error | DP-03 («sin reporte»); R-11 |

## Riesgos y preguntas abiertas

- **R-1. Calendario.** Las 6 tareas son secuenciales y caben en el viernes 27 solo si cada una sale en una o dos rondas. A la tercera ronda NO-VERDE se para y decide el humano (ML-5). Si el viernes no alcanza, al sábado temprano solo se puede mover el paso 13 (CI). Los pasos 14 y 15 traen la compuerta de cobertura y `demo_fake.py`, que la demostración necesita.
- **R-2. Una sola familia.** Con juez y verificador de la misma familia, el verificador es menos independiente al confirmar. Por eso el perfil es de demostración, con el aviso visible, y nunca de evaluación (`project.md`). La evaluación con familias distintas queda para B11b.
- **R-3. Plazo de 2× (PD-10).** Una llamada puede pasarse del plazo restante hasta el doble. Se detecta después de la llamada y queda declarado en el README.
- **R-4. Respuestas grabadas.** Las respuestas del juez y del verificador para el `FakeTransport` se escriben a mano con la forma de la Messages API. La corrida manual del paso 12 es la que muestra el comportamiento real.
- **R-5. Suite de `contracts`.** B11a no toca `contracts/`. El paso 13 corre solo `test_ci_workflows.py`, con `--no-cov`, y eso tarda poco. U01-T31 recupera el margen de la suite completa.
- **R-6. Deriva consultiva.** El motor marca como desfasadas, en modo consultivo, las etapas de Requirements Analysis a Infrastructure Design, por precisiones ya aprobadas antes de B11a. El enrutamiento sigue y B11a no lo empeora. La revalidación en bloque queda para después de la demostración.

## Revisión ML-8 del plan (ronda 1, NOT-READY) y su resolución

El 2026-11-26 revisó el plan `aidlc-architecture-reviewer-agent`. Leyó los archivos, pero no ejecutó `pytest`, `uv` ni `mypy`. Cuando se levante la guardia de Plan Approval, el informe se copia a `docs/loop/revisiones/U11-plan/ronda-1.md`. Todos los hallazgos se resolvieron con las fuentes, sin pregunta de criterio (`project.md`).

| ID | Severidad | Hallazgo | Resolución en la revisión 2 |
|---|---|---|---|
| R-01 | bloqueante | El perfil `demo-anthropic` no validaba, `kind` no tenía valor, el plazo de 300 s no quedaba fijado y el hash del *prompt* se comparaba contra sí mismo | Paso 4 reescrito; `kind="analyzer"`; `VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S=300`; PD-13; CG-U11-12 |
| R-02 | bloqueante | `minLength` no es válido en `output_config.format` de Anthropic: daría 400 en la demostración | PD-11, con esquema de cable y esquema local, más una prueba de nivel 0 con control negativo |
| R-03 | importante | T02 y T03 no podían ir en paralelo | Olas secuenciales; `model_gateway` depende de `execution_profiles` |
| R-04 | importante | Comando manual con `-p no:socket` | `--force-enable-socket`, probado con `--collect-only` en el paso 12 |
| R-05 | importante | Faltaba traducir una excepción ajena a `AnonymizerUnavailable` | Paso 6, más las variantes (a) a (e) en el paso 3; CG-U11-06 |
| R-06 | importante | Faltaba BR9.4 (`scan-cases.v1.yaml`) | Paso 5, con prueba parametrizada y control negativo |
| R-07 | importante | El rojo no garantizaba la causa `NotImplementedError` | *Stubs* por símbolo y `conftest --rojo` (pasos 1 a 3) |
| R-08 | importante | `composition.py` llegaba al 100 % recién en el paso 14 | Se exige en el paso 10 |
| R-09 | importante | Tiempos sin medir, `ROJO_SHA` literal y `coverage_gate` sin pruebas | Pruebas con `perf_counter` (pasos 7 y 9); SHA tomado de la bitácora; controles negativos del `coverage_gate` (paso 14) |
| R-10 | importante | Marcador `cli` | Declarado en el paso 2 y aplicado por prueba en el paso 3 |
| R-11 | importante | `reporte.json` y BR11.6 | CG-U11-13; `git check-ignore` en el paso 10 |
| R-12 | importante | `pyproject.toml` incompleto y sin `uv lock` | Paso 1 |
| R-13 | menor | La corrida real quedaba para el sábado | Corrida manual el viernes, después de T05; R-1 corregido |
| R-14 | menor | No estaba definida la costura de `main` ni la prueba del *prompt* frente al anonimizador | PD-12; prueba en el paso 8 |
| R-15 | menor | C17 como `Protocol` y la firma de `validate_instance` | CG-U11-03; paso 9 |

**Ronda 2 (READY), 2026-11-26.** De la ronda 1, R-01 a R-04 y R-07 a R-15 quedaron resueltos. R-05 y R-06 quedaron parciales y se cierran así:

| ID | Severidad | Hallazgo | Resolución en la revisión 3 |
|---|---|---|---|
| R-05 | parcial | La variante (e) es un error de configuración, no `anonimizador_no_disponible` | Paso 3: (e) da CLI 3, sin salida C6 |
| N-01 | importante | `scan-cases.v1.yaml` mezcla casos `vocabulary` y `clarification` | Paso 5: solo los casos `vocabulary`, con el conjunto de `rule` fijado; los `clarification` pasan a U8 en la trazabilidad |
| N-02 | importante | K-84 necesita `analyze`, que sigue siendo *stub* en el paso 8 | Su verificación pasa al paso 9 |
| N-03 | menor | El mecanismo de `--rojo` no estaba dicho | `hookwrapper` que reescribe el reporte a `when="setup"` |
| N-04 | menor | Orden de PD-10 a PD-13 | Sin cambio: es solo orden |
