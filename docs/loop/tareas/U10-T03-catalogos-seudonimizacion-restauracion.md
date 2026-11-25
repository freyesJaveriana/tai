# U10-T03: catálogos versionados, seudonimización (F4) y restauración (F6)

**Unidad:** U10 `anonymizer`   **Bolt:** B10a   **Rama base:** `bolt/b10a-anonymizer` (con U10-T01 y U10-T02 fusionadas, `76ab921`)
**Pasos del plan que cubre:** pasos 6, 7 y 8 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md`
**Historias que implementa:** US11.3 (AC11.3.1, AC11.3.2 y AC11.3.4 casos a–c del lado de U10) y la parte de datos de US11.5.
**Depende de:** U10-T02 (rojo `afa8f20`, `FakeTransport`).
**Riesgo (ML-4):** alto (anonimización y restauración que usa AUTONOMIA-05) → `revisor` con `opus`

---

## Alcance

**Dentro:**

> - paso 6: los YAML de `data/` (`detection-rules.v1.yaml`, `allowed-words.v1.yaml`, `allowed-domains.v1.yaml`, `capabilities.v1.yaml`) y su carga en `domain/catalogs.py`, que valida contra `data/schemas/` y falla cerrado;
> - paso 7: `domain/sentence.py`, `domain/detection.py` y `domain/masking.py`, con `MaskTable` solo en memoria;
> - paso 8: `domain/restoration.py`, que devuelve `RestorationOutcome` con `altered_markers`.

**Fuera** (rechazar aunque se vea roto):

- `application/generate.py`, `api.py` (`build_anonymizer`) y `providers/`: son de U10-T04 (pasos 9 a 11). Sus *stubs* siguen lanzando `NotImplementedError`.
- **Las rutas del rojo no se tocan:** `tests/guards`, `tests/contracts`, `tests/support.py` y `tests/fixtures` deben quedar idénticas a `afa8f20` (CG-U10-08). Las pruebas nuevas van en `tests/domain/`.
- NER, proxy, OpenAI, Google y Corefile: B10b (DP-03).
- `contracts/`, CI y `scripts/`.

---

## Archivos de contexto

- El plan: PD-2, PD-5, PD-8 y los pasos 6 a 8.
- `unit-test-instructions.md`, en la misma carpeta del plan.
- `construction/anonymizer/functional-design/functional-spec.md`: F4, F6 y los escenarios E1–E3, E9–E13, E15, E25 y E26.
- `construction/anonymizer/functional-design/rules.md`: BR1.1–BR1.8 (BR1.5 con CG-U10-02), BR3.1, BR4.1, BR4.2 y BR5.2.
- `construction/anonymizer/functional-design/entities.md`: `MaskTable`, `Marker`, `RestorationOutcome`.
- `libs/anonymizer/tests/` tal como quedó en `afa8f20`, y `docs/loop/bitacoras/U10-T02.md` (costuras fijadas por el rojo).
- `docs/loop/revisiones/U10-T02/ronda-2.md` (F-11 y F-12).
- `contracts/limits.v1.yaml` (`anonymizer_masking_budget_ratio`).

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U10-T03`. Primero, una sola vez: `timeout 600 uv sync --frozen --directory libs/anonymizer`.

- [ ] **CA-1 (paso 6):** el comando y el umbral del paso 6 del plan.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/domain/test_catalogs.py tests/contracts/test_data_files.py --cov=veridicus_anonymizer.domain.catalogs --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Esperado: código 0; al menos 2 pruebas por patrón; 100 % de ramas en `domain/catalogs.py`.

- [ ] **CA-2 (paso 7):** el comando y el umbral del paso 7 del plan.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/domain/test_sentence.py tests/domain/test_detection.py tests/domain/test_masking.py --cov=veridicus_anonymizer.domain.sentence --cov=veridicus_anonymizer.domain.detection --cov=veridicus_anonymizer.domain.masking --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Esperado: código 0; al menos 15 pruebas; 100 % de ramas en los tres módulos.

- [ ] **CA-3 (paso 8):** el comando y el umbral del paso 8 del plan.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/domain/test_restoration.py tests/guards/test_autonomia_05_restoration.py --cov=veridicus_anonymizer.domain.restoration --cov-branch --cov-fail-under=100 --cov-report=term-missing
  ```
  Esperado: código 0; al menos 6 pruebas propias más las del paso 4; 100 % de ramas en `domain/restoration.py`. **Excepción permitida:** si una prueba de `test_autonomia_05_restoration.py` solo puede pasar a través de `build_anonymizer` o `generate` (U10-T04), puede seguir en rojo por `NotImplementedError` de esos *stubs*; se nombra una por una en la bitácora con su causa, y U10-T04 la pasa a verde. Ninguna puede fallar por otra causa.

- [ ] **CA-4 (el rojo sigue intacto):**
  ```bash
  git -C /workspace/.worktrees/U10-T03 diff --exit-code afa8f20 -- libs/anonymizer/tests/guards libs/anonymizer/tests/contracts libs/anonymizer/tests/support.py libs/anonymizer/tests/fixtures
  ```
  Esperado: código 0.

- [ ] **CA-5 (estado del rojo):**
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer pytest tests/guards tests/contracts -p no:cacheprovider -rf
  ```
  Esperado: 0 `ERROR`. Toda prueba que siga en `FAILED` falla por `NotImplementedError` de `application/`, `api.py` o `providers/`, y la bitácora da la cuenta (pasan / siguen en rojo por T04).

- [ ] **CA-6:** tipos, *lint*, fronteras y guardias.
  ```bash
  timeout 300 uv run --frozen --offline --directory libs/anonymizer mypy --strict src tests
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff check .
  ```
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer ruff format --check .
  ```
  ```bash
  bash scripts/check-no-datos-personales.sh
  ```
  ```bash
  bash scripts/check-no-cluster-ids.sh
  ```
  ```bash
  bash scripts/check-no-insumos.sh
  ```
  Esperado: todos terminan con 0; las guardias imprimen `0 apariciones`. Además, `grep -rn -P "^(import|from) (time|datetime)" libs/anonymizer/src/veridicus_anonymizer/domain` no imprime nada (F-12).

---

## Plan de pruebas

Orden del Testing Contract `custom`: el rojo de las guardias ya existe (`afa8f20`). En cada paso, se implementa la capa y enseguida se escriben y corren sus pruebas en `tests/domain/`, antes de pasar al paso siguiente (6 → 7 → 8). Contenido mínimo, del plan:

- **Paso 6:** un ejemplo positivo y uno negativo por patrón; ninguna entidad sembrada ni ningún nombre de `common_word_names.json` está en `allowed-words`; `test_data_files.py` pasa a verde.
- **Paso 7:** E1, E2, E3, E9, E10, E11, E12, E13 y E15; cada posición de apertura de PD-2; una colisión con `AllowedWordList`; **prefijo estable** (PD-5); una propiedad Hypothesis sobre textos sintéticos (no queda ninguna forma detectada fuera de una marca).
- **Paso 8:** respuesta vacía válida (`hallazgos: []`); «persona 3» sin corchetes no es marca; Hypothesis: restaurar lo seudonimizado devuelve el original byte a byte.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:** la red de seguridad falla del lado seguro (enmascara de más). Nunca se baja la fuga cero del conjunto sembrado.
- **AUTONOMIA-05, lado U10:** la restauración devuelve la forma exacta; una marca alterada queda sin restaurar y se anota.
- **AUTONOMIA-02:** cada criterio tiene su comando y su umbral.
- **Solo datos sintéticos.** `allowed-words` nunca lleva un nombre de pila.
- Las expresiones van en `google-re2` (tiempo lineal), nunca en `re` sobre texto del relato.

---

## Notas

- **F-11 (revisión de U10-T02, ronda 2): un nombre completo sin tratamiento lleva una sola marca.** La red de seguridad une en un solo tramo las palabras con mayúscula inicial seguidas, separadas solo por espacios, y lo marca como una `ENTIDAD`. Es la lectura de F4 paso 3 («se tocan en su unión») y de E2, que exige una marca para un nombre completo. BR1.5 dice «una palabra»; esta precisión no la contradice, porque cada palabra del tramo cumple BR1.5 por sí sola. Va a la tabla de precisiones del plan como parte de CG-U10-08.
- **F-12: el dominio no lee el reloj.** El presupuesto de NFR3.5 (`anonymizer_masking_budget_ratio` × `timeout_s`) se mide en `application/generate.py` con `application.generate.now`, que es la costura que fija el rojo. `domain/` no importa `time` ni `datetime`. Si la seudonimización necesita un punto de corte, el dominio recibe un parámetro (por ejemplo, una función que dice si queda presupuesto) y no lee la hora. La aplicación de ese corte es de U10-T04.
- **Costuras fijadas por el rojo** (bitácora de U10-T02): `pseudonymize` y `restore` en `application.generate`; `apply_rules`, `safety_net`, `build_table`, `serialize_messages` y `MaskTable`; `api.load_catalogs`. Respeta sus nombres y firmas; si alguna no encaja con el plan, lo dices en la bitácora y no cambias la prueba.
- **`capabilities.v1.yaml`:** Anthropic, `claude-sonnet-5-5`, `structured_mode: json_schema_native`. Datos de la documentación oficial, verificados por el orquestador: salida estructurada en `output_config.format` con `type: "json_schema"`; esfuerzo en `output_config.effort`; cabecera `anthropic-version: 2026-10-21`. Cita `https://platform.claude.com/docs/en/build-with-claude/structured-outputs` en la bitácora.
- **Bitácora:** `docs/loop/bitacoras/U10-T03.md`, con el par falla-pasa por paso y, como máximo, una página (ML-7).
