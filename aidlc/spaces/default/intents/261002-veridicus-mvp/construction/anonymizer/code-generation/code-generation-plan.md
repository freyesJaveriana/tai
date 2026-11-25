# Plan de generación de código — U10 anonymizer (Bolt B10a «Anonimizador mínimo»)

**Parte 1 de Code Generation, 2026-11-25.** El plan cubre solo el corte delgado B10a de la precisión DP-03 (`bolt-plan.md`, origen en el cambio 06 §3). Sigue el modo liviano DT31 (`/insumos/app/loop/README.md` §9): tiene 15 pasos (ML-1, con el tope de 15 que fija el cambio 06 para el sábado), agrupados en 5 tareas del loop (ML-3). Cada paso lleva su riesgo, su `Verificación:` y su `Umbral:` (AUTONOMIA-02).

**Qué entrega B10a.** La operación `Anonymizer.generate` de C20 en proceso, que la CLI de B11a inyectará en el `ModelGateway`. Sus partes:
- seudonimización con reglas y listas;
- restauración y marcas alteradas;
- **fallo cerrado**;
- **un** adaptador nativo, el de Anthropic (Messages API, modelo `claude-sonnet-5-5`);
- el `FakeTransport` que reutiliza B11a.

**Revisión 1 del plan (2026-11-25).** Integra la revisión adversarial ML-8 (R-01 a R-13, `NOT-READY`) y la corrección del proveedor que hizo el humano: vuelve Anthropic, como en el diseño aprobado.

Todo se prueba con *fixtures* sintéticos, sin red. Al cerrar el Bolt, el humano pone la etiqueta `anonymizer-v0.1.0`.

**Qué se difiere a B10b (DP-03), sin borrarlo:**
- el NER local;
- las métricas C15;
- el proceso `anonymizer-proxy` (C21, F8, F3a, BR6);
- la comprobación de dominios contra CoreDNS (F9, BR3.6);
- los adaptadores de OpenAI y Google;
- los Secrets.

En la trazabilidad, cada ID diferido queda con `Deferred` y el destino «B10b (DP-03)».

## Decisiones del plan

| ID | Decisión | Origen |
|---|---|---|
| PD-1 | El proveedor de la primera rebanada es **Anthropic**, como fija D10 de NFR Requirements (P2 = A). El adaptador usa la Messages API con salida estructurada por JSON Schema y el parámetro de esfuerzo, por `httpx` directo y en `providers/` (CD-04). El modelo es `claude-sonnet-5-5`, en modo `json_schema_native`; la herramienta forzada queda para un modelo que la tabla marque sin salida estructurada. Los nombres exactos de los parámetros se toman de la documentación oficial vigente y se citan en la bitácora (FD-U10-09). OpenAI y Google tienen dominio en la lista de C22 pero no adaptador: fallan cerrado hasta B10b (CG-U10-01) | D10; corrección del humano, 2026-11-25 |
| PD-2 | **Sin NER en B10a.** La detección usa las reglas (`google-re2`), las cadenas con forma de marca y una red de seguridad **ampliada**: también marca como `ENTIDAD` toda palabra con mayúscula inicial que abre oración, no está clasificada y no está en `AllowedWordList`. **«Abre oración»** se define una sola vez, en `domain/sentence.py`: la palabra va al inicio de un valor de texto, o la precede (ignorando espacios) `.`, `?`, `!`, `¿`, `¡`, `:`, `;`, un salto de línea, una comilla de apertura («, ", “) o una raya (—). `AllowedWordList` se amplía con comienzos de oración y palabras de función frecuentes («El», «Entonces», «Yo»…), y **nunca** contiene un nombre de pila. Una prueba la compara con una lista sintética versionada de nombres de pila que también son palabras comunes («Paz», «Esperanza», «Rosario», «Dolores», «Luz»…). Enmascara de más, pero falla del lado seguro, y la prueba de fuga cero de AC11.3.1 sigue con el mismo umbral sobre el conjunto sembrado. **Límite declarado:** un apodo escrito todo en minúscula no lo detecta ninguna regla; una prueba documenta ese límite y no se cuenta como fuga del conjunto (CG-U10-02) | Cambio 06 §3; decisión del humano, 2026-11-25; R-09 |
| PD-3 | El paquete es `libs/anonymizer/` con *src layout*: `src/veridicus_anonymizer/` (`api.py`, `domain/`, `application/`, `providers/`, `testing/`, `data/`). Los contratos de import-linter nombran `veridicus_anonymizer` en lugar de `libs.anonymizer` | Igual que E-1 de U1 y `libs/errors` (CG-U10-03) |
| PD-4 | K-56: `validate_instance` de `veridicus-contracts` admite la lista cerrada de marcas que usan hoy los contratos y rechaza cualquier otra `x-veridicus-*`. La lista es `x-veridicus-version` (solo en la raíz, como ya exige E-30), `-limit`, `-max-bytes`, `-cookie`, `-owner-only`, `-owner-only-for-role`, `-priority`, `-roles`, `-access-log` y `-demo`. Sale `veridicus-contracts` 0.1.1, y el humano pone la etiqueta `contracts-v0.1.1` | Decisión del humano, 2026-11-25 (CG-U10-04); R-10 |
| PD-5 | K-58: se mantiene FD-U10-01 (marcas coherentes dentro de cada llamada). V-2 se cubre con una prueba de **prefijo estable**: un texto T y el texto T con turnos nuevos al final dan los mismos números a las entidades de T, porque la numeración es por primera aparición. Entre papeles que reciben contenido distinto (juez, verificador y verificador permutado), la misma persona puede llevar otra marca. Es aceptable, porque cada llamada se restaura con su propia tabla antes de verificar las citas | K-58; FD-U10-01; R-08 (CG-U10-05) |
| PD-6 | K-76, decidido por el humano «en B10»: en las guardias del repositorio público se cierran los huecos de `check-no-cluster-ids.sh` (F-05 a F-07 de T29) y el exento seguido de punto y cifras de `check-no-datos-personales.sh` (A-05 de T30), y se agrega `ruff format --check` de `libs/errors` a la CI | `docs/loop/CANDIDATAS.md` K-76 |
| PD-7 | Se construye en la CLI con `build_anonymizer(env, transport=None)` (F3b sin NER). La función valida las listas, la tabla de capacidades y que la clave exista. Sin `transport`, usa la fábrica de producción `providers/http.py::default_transport()`: TLS ≥ 1.2 con verificación, `follow_redirects=False`, `retries=0` y `trust_env=False`; esa fábrica tiene su propia prueba. `build_anonymizer` **no tiene ningún parámetro** para saltarse la seudonimización. El control negativo `testing/bypass.py` reemplaza la función interna con `monkeypatch` solo dentro de las pruebas. La validación de perfiles es de U11 | F3b; R-12 (CG-U10-06) |
| PD-8 | La restauración la hace `application/`: el adaptador devuelve el JSON ya parseado y validado, y `application` llama a `domain/restoration.py`. Así `providers` y `domain` no se importan entre sí | R-12 |
| PD-9 | Una excepción inesperada **después** del envío (por ejemplo, al restaurar) sale como `ProviderError` con su `ModelCall`, porque la llamada ya salió y debe contar (BR2.6). F7 no la distingue (CG-U10-07) | R-06 |
| PD-10 | El rojo del paso 4 va en su **propio commit** (`test(anonymizer): pruebas en rojo de AUTONOMIA-04/05 y contratos de datos`). Su SHA se anota en la bitácora de U10-T02 como `ROJO_SHA` y lo usa el paso 10 | R-03 |

## Dependencias y punto de partida

- `main` en 88efacb, con B1 fusionado: `veridicus-contracts` 0.1.0 (`model_calls.py` con `AnonymizingProvider`, `GenerateRequest`, `ModelCall` y los errores tipados; `model-call.v1.yaml`; `limits.v1.yaml` con `anonymizer_masking_budget_ratio` 0,15 y `anonymizer_response_max_bytes` de 2 MiB) y `libs/errors/`.
- `libs/anonymizer` depende de `veridicus-contracts` por ruta (`../../contracts`, fuente de `uv`), así toma 0.1.1 en el mismo Bolt.
  - T02 genera su `uv.lock` contra la 0.1.0.
  - T04 parte de la rama del Bolt con T01 ya fusionada, regenera ese lock con `uv lock --directory libs/anonymizer` y lo verifica con `uv lock --check` (R-04).
- **Instalación con red, solo una vez por worktree.** El primer comando de cada tarea es `timeout 600 uv sync --frozen --directory <paquete>`. Usa red para bajar del índice lo que fija el lockfile, con sus hashes, igual que la CI. Después, todo corre con `--frozen --offline` (R-04).
- Rama del Bolt: `bolt/b10a-anonymizer`, desde `main`. Su primer commit es `chore(loop): modo liviano (DT31)`: la §9 copiada a `docs/loop/README.md` y la nota en `docs/loop/orquestador.md` (cambio 06 §4). Las tareas entran a esa rama con `git merge --no-ff` (ML-6), y el humano fusiona el PR del Bolt a `main`.
- Sin red en las pruebas: `pytest-socket` con `--disable-socket`. No se usan `kubectl`, `helm`, `sbatch` ni `ssh` (AUTONOMIA-01).

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

**Cómo se aplica el orden del contrato.**
- **Paso 1.** Escribe primero, y ejecuta en rojo contra 0.1.0, la prueba de contrato de datos de K-56. Después corrige el validador.
- **Pasos 2 y 3.** Arman la estructura con *stubs* que lanzan `NotImplementedError` y dejan listo el ejecutor de pruebas.
- **Paso 4.** Escribe en rojo, en su propio commit, las pruebas de las guardias que tocan a U10:
  - AUTONOMIA-04: payload saliente, fallo cerrado y ausencia de fugas;
  - AUTONOMIA-05, del lado de U10: la cita seudonimizada se restaura antes de verificarse, y las marcas alteradas se informan;
  - los contratos de datos del módulo: el `ModelCall` de C13 y los esquemas de sus listas y tablas.
- **Pasos 5 a 11.** Cada capa se implementa y enseguida se prueba.
- **Paso 10.** Las pruebas del paso 4 pasan a verde sin cambios.

## Comandos de verificación

Todos corren desde la raíz del worktree de la tarea (`/workspace/.worktrees/U10-TNN`), son de esta unidad y no usan red. Hay una sola excepción: el `uv sync` inicial de cada worktree.

**Cobertura (R-01).** `addopts` **no** lleva `--cov`. Cada paso mide la cobertura de sus propios módulos con `--cov=<módulo> --cov-branch --cov-fail-under=100`. El mínimo del 80 % de líneas del paquete se exige solo en la suite completa (paso 14) y en la CI.

| Uso | Comando |
|---|---|
| Instalación (una vez por worktree, con red) | `timeout 600 uv sync --frozen --directory libs/anonymizer` |
| Suite de la unidad, con su mínimo | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-report=json --cov-fail-under=80` |
| Un archivo, sin cobertura | `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest <archivo de prueba> --no-cov` |
| Ramas de los módulos guardia | `timeout 60 uv run --frozen --offline --directory libs/anonymizer python -m veridicus_anonymizer.testing.coverage_gate coverage.json` (lee el JSON de la suite) |
| Tipos | `timeout 300 uv run --frozen --offline --directory libs/anonymizer mypy --strict src tests` |
| *Lint* y formato | `timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff check .` y `timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff format --check .` |
| Fronteras | `timeout 120 uv run --frozen --offline --directory libs/anonymizer lint-imports` |
| Contratos (U1) | `timeout 60 uv run --frozen --offline --directory contracts pytest` |
| Guardias del repositorio | `bash scripts/check-no-cluster-ids.sh`, `bash scripts/check-no-datos-personales.sh`, `bash scripts/check-no-insumos.sh`, `bash scripts/check-no-cluster-apply.sh` y `bash scripts/tests/autoprueba-guardias.sh` |

## Pasos

Riesgo según ML-4. **Alto**: guardias AUTONOMIA, seguridad, contratos, datos y anonimización; lo revisa `revisor` con `opus`. **Bajo**: andamiaje, configuración y documentación; lo revisa `revisor` con `sonnet`.

### Paso 1 — K-56: el validador admite las marcas `x-veridicus-*` del catálogo · tarea U10-T01

- [x] **Rojo primero.** Pruebas nuevas en `contracts/tests/test_validators.py`, que se ejecutan contra el código actual y deben fallar antes del arreglo:
  - una instancia válida de `model-call.v1.yaml` pasa `validate_instance`, y lo mismo una de C18 y una de C19;
  - control negativo: un esquema con una marca `x-veridicus-` fuera de la lista cerrada de PD-4 se rechaza;
  - control negativo: una instancia que rompe el `x-veridicus-limit` anidado se rechaza;
  - control negativo: un `x-veridicus-version` que no es semver se rechaza;
  - control negativo: un `x-veridicus-version` fuera de la raíz se sigue rechazando (E-30).
- [x] **Arreglo.** `validate_json_schema` y `validate_instance` aceptan la lista cerrada de PD-4, escrita como constante en el código, en cualquier nivel de anidación, salvo `x-veridicus-version`, que solo vale en la raíz. Comprueban también la forma semver de `x-veridicus-version`.
- [x] `contracts/pyproject.toml` pasa a la versión 0.1.1, y se regenera `contracts/uv.lock` con `uv lock --directory contracts`. La etiqueta `contracts-v0.1.1` la pone el humano.
- **Riesgo:** alto (contratos).
- **Verificación:**
  1. Antes del arreglo: `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_validators.py -k k56 --no-cov`.
  2. Después: `timeout 60 uv run --frozen --offline --directory contracts pytest`, `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_validators.py -k k56 --no-cov -q` y `timeout 60 uv lock --check --directory contracts`.
- **Umbral:**
  - El comando 1 termina con código 1, con al menos 3 pruebas `k56` en `FAILED`.
  - Los tres comandos de después terminan con código 0, y el conteo de `-q` muestra al menos 6 pruebas `k56` que pasan, 4 de ellas controles negativos.
  - Se mantiene el 100 % de ramas en los módulos guardia de `contracts`, y la suite corre en ≤ 60 s (NFR2.1).
- **Cubre:** K-56; BR2.5 (habilita la validación del `ModelCall`).

### Paso 2 — Estructura del paquete con *stubs* · tarea U10-T02

- [x] Crear `libs/anonymizer/`:
  - `pyproject.toml` con `hatchling`, Python ≥ 3.12 y la versión 0.1.0;
  - dependencias `httpx`, `google-re2` y `veridicus-contracts` (por ruta);
  - grupo `dev` con `pytest`, `pytest-cov`, `pytest-socket`, `hypothesis`, `mypy`, `ruff`, `import-linter` y `pip-audit`;
  - `uv.lock`;
  - `src/veridicus_anonymizer/` con `__init__.py`, `py.typed`, `api.py`, `domain/`, `application/`, `providers/`, `testing/` y `data/`;
  - `tests/`.
- [x] **Stubs (R-02).** Cada símbolo público que importan las pruebas del paso 4 existe y lanza `NotImplementedError`:
  - `Anonymizer`, `Anonymizer.generate` y `build_anonymizer`;
  - `FakeTransport` y `testing.bypass`;
  - `domain.restoration.restore` y `domain.catalogs.load_catalogs`.

  Así el rojo falla en la ejecución y no en la recolección.
- [x] Ruff (con las reglas `S`), mypy estricto y `[tool.importlinter]` quedan configurados como en `libs/errors`.
- **Riesgo:** bajo.
- **Verificación:** `timeout 600 uv sync --frozen --directory libs/anonymizer`, `timeout 120 uv lock --check --directory libs/anonymizer` y `timeout 120 uv run --frozen --offline --directory libs/anonymizer mypy --strict src`
- **Umbral:** los tres comandos terminan con código 0.
- **Cubre:** PD-3; R-02.

### Paso 3 — Ejecutor de pruebas listo · tarea U10-T02

- [x] En `[tool.pytest.ini_options]`, `addopts = "--strict-markers --disable-socket"`, sin `--cov` (R-01). En `[tool.coverage.run]`, `branch = true` y `source = ["veridicus_anonymizer"]`.
- [x] `tests/test_package.py` importa el paquete y comprueba `py.typed`.
- [x] Una prueba demuestra que `pytest-socket` bloquea una conexión.
- **Riesgo:** bajo.
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/test_package.py -q`
- **Umbral:** código 0, con al menos 2 pruebas.
- **Cubre:** Testing Contract (ejecutor antes de la primera prueba).

### Paso 4 — ROJO: guardias AUTONOMIA-04/05 y contratos de datos del módulo · tarea U10-T02

Se escriben primero y se ejecutan en rojo, en un commit propio (PD-10). Fallan por `NotImplementedError`, nunca por un error de recolección.

- [x] `tests/guards/test_autonomia_04_payload.py`: **AUTONOMIA-04, payload saliente** (AC11.3.1 y AC11.3.7 del lado de U10).
  - Escenarios E1, E2, E9 y E29, sobre el conjunto sembrado de `tests/fixtures/`. Hay nombres con mayúscula en **cada** posición de apertura de PD-2, con tilde, sin tilde y escritos con secuencias de escape Unicode del JSON. También hay un nombre de la lista de nombres que son palabras comunes al comienzo de una oración.
  - Ningún cuerpo que capture el `FakeTransport` contiene una entidad sembrada, y todos llevan marcas `[PERSONA_n]`.
  - Control negativo: el *fixture* `bypass` hace fallar la misma aserción.
  - Una prueba documenta el límite declarado del apodo en minúscula (PD-2).
- [x] `tests/guards/test_autonomia_04_fail_closed.py`: **AUTONOMIA-04, fallo cerrado** (AC11.3.3 y AC11.3.6 del lado de U10). La prueba está parametrizada (R-06).
  - **Casos:**
    - destino local;
    - proveedor desconocido;
    - proveedor conocido sin adaptador en B10a (`openai` y `google`);
    - dominio fuera de la lista y puerto distinto de 443, con un catálogo alterado inyectado en `build_anonymizer`;
    - modelo fuera de la tabla;
    - clave ausente;
    - una regla que lanza;
    - la red de seguridad que lanza;
    - error al construir la tabla;
    - error de serialización;
    - presupuesto agotado, con el reloj inyectado;
    - una excepción inesperada antes del envío.
  - **Lo que se afirma en cada caso:**
    - sale `AnonymizerUnavailable` sin `ModelCall`;
    - el mensaje nombra el paso que falló, sin ningún valor;
    - el `FakeTransport` queda con 0 peticiones;
    - **control positivo:** el mismo *fixture*, con esa sola condición corregida, produce exactamente 1 petición.
  - **Después del envío:** una excepción inesperada al restaurar sale como `ProviderError` con su `ModelCall` (PD-9).
  - **La tabla se suelta (BR1.8):** la `MaskTable` queda vacía tras el éxito y tras cada rama de error.
- [x] `tests/guards/test_autonomia_04_no_leak.py`: un *canary* va en el testimonio y otro en el valor de la clave (E6 y E34; BR1.8, BR2.3 y BR5.4; R-07).
  - **Control positivo:** el *canary* de la clave está en la cabecera de autenticación de la petición **cruda**.
  - **Control negativo:** no está en la URL, en el cuerpo ni en ninguna otra cabecera.
  - Ninguno de los dos *canaries* aparece en los logs capturados, en el `ModelCall` ni en el texto de las excepciones. Se recorre la cadena completa de `__cause__` y `__context__`, en el éxito y en cada rama de error.
- [x] `tests/guards/test_autonomia_05_restoration.py`: **AUTONOMIA-05 del lado de U10, «cita restaurada antes de verificarse»** (R-05).
  - E5: una cita seudonimizada se restaura byte a byte igual al turno original.
  - E25 y E26: una marca alterada y una inventada en `cita_a`, en `hecho` y en `observaciones` dejan su puntero RFC 6901 en `altered_markers`, sin repetidos y en orden; las marcas conocidas de esa misma cadena sí se restauran.
- [x] `tests/contracts/test_model_call_contract.py`:
  - el `ModelCall` de una llamada que salió valida contra `model-call.v1.yaml` con `validate_instance` y lleva `anonymized: true` (BR2.5);
  - los errores posteriores al envío llevan su `ModelCall`, y `AnonymizerUnavailable` no lo lleva (BR2.6).

  Esta prueba depende de 0.1.1 (paso 1): hasta que T01 se fusione puede fallar por K-56, y eso también cuenta como rojo.
- [x] `tests/contracts/test_data_files.py`: cada archivo de `data/` (reglas, palabras permitidas, dominios y capacidades) valida contra su esquema JSON versionado en `data/schemas/`, y un archivo con un campo de más se rechaza.
- **Riesgo:** alto (guardias AUTONOMIA-04 y 05).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts --collect-only -q` y `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts -p no:cacheprovider -rf`
- **Umbral:**
  - la recolección termina con código 0, con 0 errores de recolección y al menos 30 pruebas;
  - la ejecución termina con código 1, con el 100 % de las pruebas en `FAILED` y 0 en `ERROR`; el resumen `-rf` muestra `NotImplementedError` o el rechazo de K-56;
  - el commit del rojo existe y su SHA queda anotado como `ROJO_SHA` en la bitácora.
- **Cubre:** AC11.3.1, AC11.3.3, AC11.3.4 (casos a, b y c), AC11.3.5, AC11.3.6 y AC11.3.7; BR1.1, BR1.3, BR1.6, BR1.8, BR2.1, BR2.3, BR2.5, BR2.6, BR3.1, BR4.1, BR4.2, BR5.4 y BR5.5.

### Paso 5 — `FakeTransport` y transporte inyectado · tarea U10-T02

- [x] `testing/fake_transport.py`, sobre `httpx.MockTransport` (R-07).
  - Guarda la petición **cruda**: método, dominio, puerto, ruta, cabeceras y cuerpo.
  - Oculta la clave solo al representarla (`repr` y mensajes de aserción).
  - Devuelve respuestas grabadas sintéticas o errores simulados: 5xx, bloqueo, *timeout*, cuerpo que no es JSON y `307`.
  - Nunca abre red.
- [x] `testing/bypass.py`: el control negativo que reemplaza con `monkeypatch` la función interna de seudonimización (PD-7). Solo lo alcanzan las pruebas (BR5.5).
- [x] Pruebas: de 6 a 8 en `tests/testing/test_fake_transport.py`.
- **Riesgo:** alto (lo reutiliza la prueba compuesta de AUTONOMIA-04 en B11a).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/testing --cov=veridicus_anonymizer.testing.fake_transport --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0; al menos 6 pruebas; 100 % de ramas en `testing/fake_transport.py`.
- **Cubre:** BR5.5; E19 y E23 (soporte).

### Paso 6 — Listas y tablas versionadas del módulo · tarea U10-T03

- [x] Los archivos de `data/` y su carga:
  - `detection-rules.v1.yaml`: tratamientos, prefijos de lugar, radicados y expedientes, cédula, teléfono, correo, placa y cuenta. Cada patrón está en `google-re2`, en tiempo lineal.
  - `allowed-words.v1.yaml`: instituciones, meses, días, rótulos de C6 y, por PD-2, comienzos de oración y palabras de función frecuentes. No lleva nombres de pila.
  - `allowed-domains.v1.yaml`: exactamente los tres pares de C22.
  - `capabilities.v1.yaml`: una entrada de Anthropic, `claude-sonnet-5-5`, con `structured_mode: json_schema_native` y el parámetro de esfuerzo. Los nombres de los parámetros salen de la documentación oficial, citada en la bitácora.
  - La carga (`domain/catalogs.py`) valida contra `data/schemas/` y falla cerrado ante un archivo inválido.
- [x] Pruebas:
  - al menos un ejemplo positivo y uno negativo por patrón;
  - ninguna entidad sembrada del conjunto sintético, ni ningún nombre de la lista de nombres que son palabras comunes, está en `allowed-words` (BR1.5 y PD-2);
  - `test_data_files.py` del paso 4 pasa a verde.
- **Riesgo:** alto (datos de la anonimización).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/domain/test_catalogs.py tests/contracts/test_data_files.py --cov=veridicus_anonymizer.domain.catalogs --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0; al menos 2 pruebas por patrón; 100 % de ramas en `domain/catalogs.py`.
- **Cubre:** BR1.2 (parte de reglas), BR1.5, BR3.1 (lista) y BR5.2 (tabla, Anthropic).

### Paso 7 — Seudonimización (F4) · tarea U10-T03

- [x] `domain/sentence.py`, `domain/detection.py` y `domain/masking.py`:
  - recorren los mensajes; si el contenido es JSON, recorren sus valores de cadena en orden de documento, sin tocar claves ni números;
  - detectan con las reglas, con las cadenas con forma de marca (`input_marker`) y con la red de seguridad ampliada de PD-2, que no se aplica a `system`;
  - fusionan los tramos por precedencia, propagan por forma exacta con límites de palabra Unicode y numeran por primera aparición;
  - reemplazan de derecha a izquierda y vuelven a serializar sin escapar caracteres no ASCII.
- [x] `MaskTable` vive solo en memoria: no tiene `__repr__` ni `__str__` que muestren valores, no se serializa y tiene un método para vaciarla.
- [ ] El presupuesto es `anonymizer_masking_budget_ratio` × `timeout_s`, leído de C25 con la carga de límites de U1; si se supera, la llamada falla cerrado (NFR3.5).
- [x] Pruebas:
  - E1, E2, E3, E9, E10, E11, E12, E13 y E15;
  - cada posición de apertura de PD-2;
  - una colisión con `AllowedWordList`;
  - **prefijo estable** (PD-5): T y T más turnos nuevos dan los mismos números para las entidades de T;
  - una propiedad Hypothesis sobre textos sintéticos: no queda ninguna forma detectada fuera de una marca.
- **Riesgo:** alto (anonimización).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/domain/test_sentence.py tests/domain/test_detection.py tests/domain/test_masking.py --cov=veridicus_anonymizer.domain.sentence --cov=veridicus_anonymizer.domain.detection --cov=veridicus_anonymizer.domain.masking --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0; al menos 15 pruebas; 100 % de ramas en los tres módulos.
- **Cubre:** AC11.3.1 y AC11.3.2; BR1.1, BR1.2, BR1.5, BR1.7 y BR1.8; NFR3.5; K-58.

### Paso 8 — Restauración y marcas alteradas (F6) · tarea U10-T03

- [x] `domain/restoration.py`:
  - recorre los valores de cadena del JSON ya parseado con su puntero RFC 6901;
  - restaura cada marca canónica de la tabla a su forma exacta;
  - deja sin restaurar toda forma de marca que no esté en la tabla y anota su puntero en `altered_markers`;
  - devuelve `RestorationOutcome`.
- [x] Pruebas de la capa, además de las del paso 4:
  - una respuesta vacía válida (`hallazgos: []`);
  - «persona 3» sin corchetes no cuenta como marca;
  - Hypothesis: restaurar lo seudonimizado devuelve el original byte a byte.
- [ ] `test_autonomia_05_restoration.py` del paso 4 pasa a verde **sin cambios**.
- **Riesgo:** alto (lo usa la verificación de citas de AUTONOMIA-05 en B11a).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/domain/test_restoration.py tests/guards/test_autonomia_05_restoration.py --cov=veridicus_anonymizer.domain.restoration --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0; al menos 6 pruebas propias más las del paso 4; 100 % de ramas en `domain/restoration.py`.
- **Cubre:** AC11.3.4 (casos a, b y c del lado de U10); BR1.3, BR4.1 y BR4.2.

### Paso 9 — Adaptador nativo de Anthropic y transporte de producción (F5, C22) · tarea U10-T04

- [ ] `providers/http.py::default_transport()`: TLS ≥ 1.2 con verificación, `follow_redirects=False`, `retries=0` y `trust_env=False` (R-12). Su prueba inspecciona el cliente construido, sin abrir red.
- [ ] `providers/anthropic.py`:
  - **Envío.** La URL base es la constante `https://api.anthropic.com`, con la ruta de la Messages API. La salida estructurada va por JSON Schema, construida desde `req.schema`, y el esfuerzo va según la tabla de capacidades. Los nombres de los parámetros y la versión de la API se citan de la documentación oficial vigente en la bitácora (FD-U10-09). Se envía **una sola vez**, con lectura por bloques con tope `anonymizer_response_max_bytes` y un *timeout* igual al plazo restante.
  - **Clave.** Va solo en la cabecera de autenticación de Anthropic.
  - **Respuesta (BR5.3).** Devuelve el JSON parseado y validado contra `req.schema`, sin restaurar (PD-8). Bloqueo o rechazo de contenido → `ContentBlocked`; plazo agotado → `Timeout`; 5xx, redirección o corte → `ProviderError`; respuesta que no es JSON estricto o no valida → `InvalidOutput`. Todos llevan su `ModelCall`.
  - **`ModelCall`.** Cumple BR2.5: tokens del proveedor (0 si no los informa), `fallback_provider` según la ranura y `anonymized: true`.
- [ ] Pruebas en `tests/providers/`:
  - prueba de contrato con respuestas grabadas sintéticas cuya forma se contrasta con la documentación oficial, citada en la bitácora: E27, solo el lado de Anthropic;
  - E19, E20, E21 y E23;
  - una sola petición ante un 503 seguido de un 200 (BR2.4);
  - `default_transport`.
- **Riesgo:** alto (salida al exterior).
- **Verificación:** `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/providers --cov=veridicus_anonymizer.providers --cov-branch --cov-fail-under=100 --cov-report=term-missing`
- **Umbral:** código 0; al menos 10 pruebas; 100 % de ramas en `providers/`; 0 conexiones reales (`pytest-socket`).
- **Cubre:** AC13.6.1 (Anthropic) y AC13.6.2; BR2.4, BR2.5, BR2.6, BR3.5, BR5.2 (Anthropic), BR5.3 y BR5.4.

### Paso 10 — `Anonymizer.generate` y construcción en la CLI (F1, F7, F3b) · tarea U10-T04

- [ ] Primero se regenera `libs/anonymizer/uv.lock` contra `contracts` 0.1.1 (R-04).
- [ ] `application/generate.py` y `api.py`:
  - **Comprobación del destino:** `scope` externo; proveedor `anthropic` (`openai` y `google` fallan cerrado hasta B10b); dominio en la lista; puerto 443; modelo en la tabla; clave en el entorno recibido.
  - **Orden:** seudonimizar, enviar **una vez**, restaurar (PD-8) y devolver `GenerateResult`.
  - **Liberación de la tabla:** en todos los finales, con `try/finally`.
  - **Logs:** solo IDs y cifras.
  - **Errores:** cualquier excepción antes del envío sale como `AnonymizerUnavailable`; una excepción inesperada después del envío sale como `ProviderError` con su `ModelCall` (PD-9).
  - **Protocolo:** `Anonymizer` cumple `AnonymizingProvider`, y mypy lo comprueba.
- [ ] `build_anonymizer(env, transport=None)` (PD-7):
  - carga y valida `data/`;
  - falla con el error de configuración de `libs/errors` antes de cualquier llamada;
  - no tiene ningún parámetro para saltarse la seudonimización, cosa que comprueba una prueba de su firma.
- [ ] Las pruebas rojas del paso 4 pasan a verde **sin cambiarlas**.
- **Riesgo:** alto (fallo cerrado, AUTONOMIA-04).
- **Verificación:**
  - `timeout 120 uv lock --check --directory libs/anonymizer`
  - `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts tests/application --cov=veridicus_anonymizer.application --cov=veridicus_anonymizer.api --cov-branch --cov-fail-under=100 --cov-report=term-missing`
  - `git -C /workspace/.worktrees/U10-T04 diff --exit-code ROJO_SHA -- libs/anonymizer/tests/guards libs/anonymizer/tests/contracts`, con el SHA de la bitácora de U10-T02 en lugar de `ROJO_SHA`
- **Umbral:**
  - los tres comandos terminan con código 0;
  - todas las pruebas del paso 4 pasan;
  - el *diff* sale vacío, como comprueba `--exit-code`;
  - 100 % de ramas en `application/` y `api.py`.
- **Cubre:** AC11.3.3, AC11.3.6, AC11.3.7 y AC13.3.2 (sin NER); BR1.6, BR2.1, BR2.2 (parte de la CLI) y BR3.1.

### Paso 11 — Fronteras y logs · tarea U10-T04

- [ ] Contratos de import-linter:
  - `anonymizer-independent`: el paquete no importa `model_gateway`, `execution_profiles` ni `incoherence_analyzer`;
  - `anonymizer-layers`: `providers` y `domain` no se importan entre sí;
  - `anonymizer-testing-not-in-production`: nada de `src/` fuera de `testing/` importa `testing`.

  Que nada fuera del paquete importe `providers` lo configura U4 en `semantic-agent` (BR5.1).
- [ ] En `tests/boundaries/`, un módulo de prueba que viola cada contrato hace fallar `lint-imports` (control negativo).
- [ ] Prueba con `caplog`: cada línea de log solo lleva campos de la lista de BR2.3.
- **Riesgo:** alto (fronteras de seguridad).
- **Verificación:** `timeout 120 uv run --frozen --offline --directory libs/anonymizer lint-imports` y `timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/boundaries --no-cov -q`
- **Umbral:**
  - `lint-imports` termina con código 0 sobre el paquete;
  - las pruebas terminan con código 0, con al menos 4 pruebas;
  - cada uno de los 3 controles negativos hace fallar `lint-imports` (código ≠ 0) dentro de su prueba.
- **Cubre:** BR2.3, BR5.1 y BR5.5; FD-U10-03 (con los nombres de PD-3).

### Paso 12 — CI de nivel 0 · tarea U10-T05

- [ ] `.github/workflows/anonymizer-level0.yml`, **sin filtro por rutas**, para que pueda ser comprobación obligatoria de `main` (R-11):
  - *job* `anonymizer-level0` con `uv sync --frozen`, `uv lock --check`, `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, `pip-audit` (`HIGH`+ con corrección), la suite con su mínimo y `coverage_gate`;
  - acciones fijadas por SHA y `permissions: contents: read`.
- [ ] En `contracts-level0.yml`, el *job* `errors-level0` suma `ruff format --check` (K-76).
- **Riesgo:** bajo (configuración).
- **Verificación:** `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py` y `bash scripts/check-no-cluster-apply.sh`
- **Umbral:** los dos comandos terminan con código 0. La prueba recorre todos los *workflows* reales, también el nuevo.
- **Cubre:** NFR13 de U10 (CI); K-76 (`libs/errors`).

### Paso 13 — K-76: huecos de las guardias del repositorio público · tarea U10-T05

- [ ] `scripts/check-no-cluster-ids.sh` detecta:
  - una asignación con ámbito del servidor;
  - un nombre de nodo en la ruta de un archivo versionado;
  - `.psd1`;
  - una URL `file:` con tres barras;
  - un host concatenado tras `@`.
- [ ] La regla del destino de `scp` deja de dar los falsos positivos de F-05 a F-07.
- [ ] `scripts/check-no-datos-personales.sh` no exime un número exento seguido de punto y cifras (A-05).
- [ ] Hoy las guardias no tienen suite, así que se crea `scripts/tests/autoprueba-guardias.sh` (R-11). La autoprueba:
  - arma un repositorio de Git temporal fuera del árbol versionado;
  - construye **en tiempo de ejecución, a partir de fragmentos**, una sonda sintética por caso y su control negativo, para que ninguna sonda quede escrita entera en un archivo versionado;
  - corre cada guardia sobre ese repositorio, con su raíz como argumento;
  - termina con 0 solo si cada sonda da 1 y cada control da 0.

  Los informes describen las sondas con palabras (P-T29-2).
- [ ] `.github/workflows/repo-level0.yml` corre la autoprueba.
- **Riesgo:** alto (seguridad del repositorio público).
- **Verificación:** `bash scripts/tests/autoprueba-guardias.sh`, `bash scripts/check-no-cluster-ids.sh`, `bash scripts/check-no-datos-personales.sh` y `timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py`
- **Umbral:**
  - los cuatro comandos terminan con código 0;
  - la autoprueba informa al menos 7 sondas, todas detectadas, y al menos 7 controles, todos limpios.
- **Cubre:** K-76 (F-05 a F-07 de T29, A-05 de T30).

### Paso 14 — Suite completa y compuertas de calidad · tarea U10-T05

- [ ] `testing/coverage_gate.py` lee `coverage.json` y exige:
  - el 100 % de ramas en `domain/`, `application/`, `api.py`, `providers/` y `testing/fake_transport.py`;
  - el 80 % de líneas en el paquete.
- [ ] Corre en el worktree todo lo de «Comandos de verificación».
- **Riesgo:** bajo (agregación).
- **Verificación:** los comandos «Suite de la unidad, con su mínimo», «Ramas de los módulos guardia», «Tipos», «*Lint* y formato», «Fronteras», «Contratos (U1)» y «Guardias del repositorio» de la tabla de arriba.
- **Umbral:**
  - todos terminan con código 0;
  - 100 % de ramas en los módulos guardia y ≥ 80 % de líneas en el paquete;
  - la suite de la unidad corre en ≤ 300 s en CPU.
- **Cubre:** Testing Posture (cobertura y herramientas).

### Paso 15 — Documentación, demostración y versión · tarea U10-T05

- [ ] `libs/anonymizer/README.md`, en español, con:
  - qué hace el módulo;
  - cómo lo construye la CLI de B11a (`build_anonymizer`);
  - las variables de entorno, solo con nombres `VERIDICUS_*`;
  - qué no hace todavía, es decir, lo diferido a B10b (DP-03);
  - el límite declarado de PD-2.
- [ ] `libs/anonymizer/examples/demo_fake.py` corre con el `FakeTransport` y una transcripción sintética, e imprime:
  - el cuerpo que saldría, que solo lleva marcas;
  - la respuesta restaurada;
  - con un destino `openai`, que falla cerrado, la línea `AnonymizerUnavailable` y el texto `peticiones=0`.

  La garantía de fuga cero no la da la demostración sino `test_autonomia_04_payload.py` (R-13).
- [ ] Entradas en el glosario (`docs/`) y en `docs/devlog.md`. Versión 0.1.0; la etiqueta `anonymizer-v0.1.0` la pone el humano.
- **Riesgo:** bajo (documentación).
- **Verificación:** `timeout 120 uv run --frozen --offline --directory libs/anonymizer python examples/demo_fake.py` y `bash scripts/check-no-datos-personales.sh`
- **Umbral:** los dos comandos terminan con código 0, y la salida de la demostración contiene `AnonymizerUnavailable` y `peticiones=0`.
- **Cubre:** demostración esperada de B10 (`bolt-plan.md`); NFR14 de U10 (documentación).

## Olas del loop

| Tarea | Pasos | Riesgo | Revisor | Depende de | Ola |
|---|---|---|---|---|---|
| U10-T01 | 1 | alto | `opus` | — | 1 (en paralelo con T02) |
| U10-T02 | 2, 3, 4, 5 | alto | `opus` | — | 1 |
| U10-T03 | 6, 7, 8 | alto | `opus` | T02 | 2 |
| U10-T04 | 9, 10, 11 | alto | `opus` | T01, T03 | 3 |
| U10-T05 | 12, 13, 14, 15 | alto (por el paso 13) | `opus` | T04 | 4 |

**Por qué T01 y T02 pueden ir en paralelo (R-04).** No tocan los mismos archivos. La única dependencia entre ellas es la de `test_model_call_contract.py`: queda en rojo hasta que llegue 0.1.1, y eso cuenta como rojo. El lock de `libs/anonymizer` lo regenera T04 sobre la rama del Bolt, con T01 ya fusionada.

**Tamaño de las tareas.** U10-T01 tiene un solo paso, por debajo de los 3 de ML-3. Toca `contracts/`, una zona aparte, y conviene que salga primero. Quedan 5 tareas, por debajo de la meta de 8 de ML-3, con dos rondas como máximo cada una (ML-5).

## Trazabilidad

| ID | Estado | Paso o destino |
|---|---|---|
| US11.3 (AC11.3.1, AC11.3.2, AC11.3.3, AC11.3.5, AC11.3.6, AC11.3.7) | En B10a | 4, 7, 10 |
| AC11.3.4 (casos a–c, lado de U10) | En B10a | 4, 8 |
| AC11.3.8 | No es de U10 (FD-U10-16) | U11 en B11a |
| US11.5 (AC11.5.1) | En B10a | 4, 6, 10 |
| AC11.5.2 (Corefile) | Deferred | B10b (DP-03) |
| AC13.3.1 (caso c, proxy) | Deferred | B10b (DP-03) |
| AC13.3.2 (CLI) | En B10a, sin NER | 10 |
| AC13.6.1 | En B10a para Anthropic; OpenAI y Google Deferred | 9; B10b (DP-03) |
| AC13.6.2 | En B10a | 9 |
| BR1.1, BR1.3, BR1.5, BR1.6, BR1.7, BR1.8 | En B10a | 4, 7, 8, 10 |
| BR1.2 | Reglas en B10a; NER Deferred | 6, 7; B10b (DP-03, PD-2) |
| BR2.1, BR2.3, BR2.4, BR2.5, BR2.6 | En B10a | 4, 9, 10, 11 |
| BR2.2 | CLI en B10a; proxy y NER Deferred | 10; B10b (DP-03) |
| BR3.1, BR3.5 | En B10a | 6, 9, 10 |
| BR3.6 | Deferred | B10b (DP-03) |
| BR4.1, BR4.2 | En B10a | 4, 8 |
| BR5.1, BR5.3, BR5.4, BR5.5 | En B10a | 5, 9, 11 |
| BR5.2 | Anthropic en B10a; OpenAI y Google Deferred | 6, 9; B10b (DP-03) |
| BR6.1–BR6.5 | Deferred | B10b (DP-03) |
| BR1.4, BR3.2, BR3.3, BR3.4 | Retirado | — |
| NFR3.5 (presupuesto) | En B10a | 7 |
| K-56, K-58, K-76 | En B10a | 1; 7; 12, 13 |

Escenarios fuera de B10a: E17, E18, E24, E28 y E30 a E33 (proxy, NER, Corefile y los adaptadores de OpenAI y Google) → B10b (DP-03).

## Precisiones para decidir en la aprobación

No se edita ningún artefacto aprobado. En la aprobación decides cuáles se llevan al original, cada una en su propio commit.

| ID | Artefacto aprobado | Precisión | Origen |
|---|---|---|---|
| CG-U10-01 | `functional-spec.md` F7 y `allowed-domains.v1.yaml` (C22) | En B10a, los tres dominios de C22 están en la lista, pero solo Anthropic tiene adaptador. Un destino `openai` o `google` falla cerrado con `AnonymizerUnavailable` hasta B10b | DP-03; revisión ML-8 |
| CG-U10-02 | `rules.md` (BR1.2, BR1.5), FD-U10-02 y `functional-spec.md` §8 | Sin NER en B10a. La red de seguridad también marca la palabra con mayúscula que abre oración (definición única de PD-2) si no está en `AllowedWordList`. La lista se amplía y nunca lleva nombres de pila. El apodo en minúscula queda como límite declarado. El NER vuelve en B10b | Cambio 06 §3; humano, 2026-11-25 |
| CG-U10-03 | `functional-spec.md` §1 (rutas `libs/anonymizer/*.py`), FD-U10-03 y C20 | *src layout* `libs/anonymizer/src/veridicus_anonymizer/`; los contratos de import-linter usan `veridicus_anonymizer` | E-1 de U1 |
| CG-U10-04 | U1 `code-summary.md` y `contract-summary.md` (validación de instancias) | `validate_instance` admite la lista cerrada de 10 marcas `x-veridicus-*` de PD-4, y sale `veridicus-contracts` 0.1.1 | K-56; humano, 2026-11-25 |
| CG-U10-05 | FD-U10-01 | Se mantiene la coherencia por llamada. V-2 se cubre con la prueba de prefijo estable. Entre papeles con contenido distinto, la marca puede cambiar | K-58; R-08 |
| CG-U10-06 | `functional-spec.md` F3b | `build_anonymizer(env, transport=None)` no carga NER en B10a; valida listas, tabla y clave, y usa `default_transport()` en producción | DP-03; R-12 |
| CG-U10-07 | `functional-spec.md` F7 y BR5.3 | Una excepción inesperada después del envío sale como `ProviderError` con su `ModelCall` | R-06 |

## Riesgos y preguntas abiertas

- **Q1 (resuelta 2026-11-25):** el proveedor es Anthropic y el modelo `claude-sonnet-5-5`. Los nombres exactos de los parámetros de salida estructurada y de esfuerzo se toman de la documentación oficial en los pasos 6 y 9.
- **R-1. Enmascarar de más (PD-2).** Los comienzos de oración que falten en `AllowedWordList` salen como `[ENTIDAD_n]`. El juez pierde algo de contexto, pero ningún dato sale sin seudonimizar. Se mitiga ampliando la lista por PR.
- **R-2. Nombres que no detectan las reglas.** Un apodo todo en minúscula es el límite declarado de PD-2, más amplio sin NER. Si el conjunto sintético de B11a encuentra una fuga dentro del conjunto sembrado, la prueba falla y no se baja el umbral (team.md).
- **R-3. Familias en B11a.** `project.md` exige que el juez y el verificador sean de familias distintas en los perfiles de evaluación. Con el juez en Claude, el perfil de evaluación de B11a necesita un verificador de otra familia; si no, se declara como perfil de demostración, con su aviso visible.
- **R-4. Calendario.** Las 5 tareas caben en el jueves 26 solo si T01 y T02 salen en la primera ronda. A la tercera ronda NO-VERDE se para y se lleva al humano (ML-5).
- **Riesgos menores de la revisión ML-8 que se aceptan:**
  - las respuestas grabadas de Anthropic se escriben a mano y se contrastan con la documentación, pero no son una grabación real (R-13);
  - `gitleaks` ya corre para todo el repositorio en `repo-level0.yml`, así que no se agrega por paquete (R-11).
