# U01-T33: C8 define el plegado del texto y el escáner lo lee de ahí

**Unidad:** U1 `contracts` (tarea correctiva, fuera de un plan de Bolt), con su consumidor `libs/integrity_policy`
**Rama base:** `main` en `46dfba2`   **Destino:** PR a `main`, que fusiona el humano
**Origen:** K-89 (revisión de U11-T02, ronda 1), ampliada en K-91 (ronda 3)
**Depende de:** U01-T31, ya fusionada (#57)
**Riesgo (ML-4):** alto. Toca el contrato C8 y la guardia AUTONOMIA-03, así que el revisor será `opus`.

---

## Problema

C8 dice `case_insensitive` y `accent_insensitive`, pero no dice **cómo** se pliega el texto. Por eso cada consumidor escanea a su manera:

- `libs/integrity_policy/scan.py` (`_fold`, `_dropped`) descompone con **NFD**. Descarta las marcas combinantes y los caracteres `Cf`, `Mn` y `Me`. No aplica normalización de compatibilidad, así que `ｆａｌｓｏ` (ancho completo) y `ﬁ` (ligadura) evaden el escáner.
- `contracts/.../checks/veracity.py` (`normalizar`) usa **NFKD**: los dos pliegues ya difieren.
- Según K-91, ronda 3, los cuatro rellenos Hangul (`Lo`) y los 3769 `Cn` sin asignar del grupo `Default_Ignorable_Code_Point` no se descartan. Insertados dentro de un término, lo esconden.
- U8 (la consola) tendrá que escanear igual que U11, pero no tiene de dónde leer la regla. `contracts/ts/forbidden-vocabulary.ts` solo trae los términos.

## Alcance

**Dentro:**

> 1. C8 declara el plegado en `match.fold`, y `schema_version` sube a `2.1.0`. Es un campo nuevo en un contrato no estricto (BR1.3).
> 2. `checks/veracity.py` valida `fold`.
> 3. `scan.py` lee el plegado de C8 en lugar de tenerlo escrito en el código.
> 4. `gen_ts.py` exporta el plegado a `contracts/ts/forbidden-vocabulary.ts`.

**Forma de `match.fold`.** Los nombres de clave son una propuesta del orquestador; si el codificador ve uno mejor, lo justifica en la bitácora.

```yaml
  fold:
    # Por carácter: descomposición de compatibilidad, descarte y plegado de mayúsculas, en ese orden.
    normalization: NFKD
    case: casefold
    dropped_categories: [Mn, Me, Cf]   # además, todo carácter con clase combinante distinta de 0
    # Default_Ignorable_Code_Point (Unicode 15.0/16.0, DerivedCoreProperties.txt), en rangos cerrados.
    dropped_code_points:
      - [0x00AD, 0x00AD]
      - [0x034F, 0x034F]
      - [0x061C, 0x061C]
      - [0x115F, 0x1160]
      - [0x17B4, 0x17B5]
      - [0x180B, 0x180F]
      - [0x200B, 0x200F]
      - [0x202A, 0x202E]
      - [0x2060, 0x206F]
      - [0x3164, 0x3164]
      - [0xFE00, 0xFE0F]
      - [0xFEFF, 0xFEFF]
      - [0xFFA0, 0xFFA0]
      - [0xFFF0, 0xFFF8]
      - [0x1BCA0, 0x1BCA3]
      - [0x1D173, 0x1D17A]
      - [0xE0000, 0xE0FFF]
```

La lista coincide con lo que mide K-91. Trae 4 rellenos Hangul: U+115F, U+1160, U+3164 y U+FFA0. Trae 3769 `Cn`, que salen de U+2065 (1), U+FFF0–U+FFF8 (9), U+E0000 (1), U+E0002–U+E001F (30), U+E0080–U+E00FF (128) y U+E01F0–U+E0FFF (3600). El codificador comprueba esas cifras con `unicodedata` en una prueba. Si no cuadran, para y lo reporta: no ajusta la lista para que cuadre.

**Detalle de cada pieza:**

- **`checks/veracity.py`:**
  - `COINCIDENCIA`/`_problemas_de_coincidencia` aceptan y exigen `fold` con los valores aprobados. Puede ser una constante `PLEGADO` aparte.
  - Además, una comprobación de forma: rangos `[inicio, fin]` enteros con `0 <= inicio <= fin <= 0x10FFFF`, ordenados y sin solaparse.
  - `schema_version` debe ser `2.1.0`.
- **`libs/integrity_policy/scan.py`:**
  - `_fold` y `_dropped` usan los valores de `match.fold` leídos de C8 una sola vez, igual que `_vocabulary`.
  - Por cada carácter: NFKD, después el descarte por categoría, por clase combinante o por rango, y luego `casefold`.
  - `_span_end` (K-91) sigue llevando al tramo las marcas descartadas que siguen al término.
  - La pertenencia a un rango se resuelve con `bisect` o con un conjunto precalculado, no recorriendo la lista en cada carácter.
  - Si `fold` falta o trae un valor que el escáner no conoce, la carga falla cerrada con una excepción. Nunca vuelve en silencio al pliegue anterior.
- **`tools/gen_ts.py`:**
  - `_vocabulario` añade, por ejemplo, `FOLD_NORMALIZATION`, `FOLD_DROPPED_CATEGORIES` y `FOLD_DROPPED_CODE_POINTS`.
  - Se regenera `contracts/ts/` con la herramienta, no a mano, y su prueba de deriva pasa.
- **`contracts/security-surface.json`:** se regenera con `--write`. Cambia la huella de C8.
- **`contracts/README.md`, `test_readme.py`, `test_loader_usage.py`:** pasan de `2.0.1` a `2.1.0`, donde citen C8.

**Fuera** (rechazar aunque se vea relacionado):

- La lista `terms`, `scanned` y el resto de `match` no cambian. La lista de vocabulario no se amplía.
- `scan-cases.v1.yaml` no se toca, porque BR1.5 pide un contrato por PR. Los casos nuevos van como pruebas de `libs/integrity_policy`. Si crees que deben ser casos compartidos, anótalo como candidata.
- `normalizar` y `FRONTERAS_DE_PALABRA` de `veracity.py` comparan **nombres de campos** de los esquemas, no texto escaneado: no se cambian. Si ves que deben seguir el mismo plegado, anótalo como candidata.
- Los homoglifos (la `а` cirílica) son una limitación declarada; NFKD no los resuelve.
- La versión de los paquetes, `pyproject.toml` y los `uv.lock`, en `contracts/` y en `libs/`. Si una prueba exige subirlos, para y repórtalo.
- `libs/incoherence_analyzer` y los demás paquetes no se tocan. Solo se corre su suite como consumidor.
- K-92 y K-28.

---

## Archivos de contexto

- `contracts/integrity/forbidden-vocabulary.v2.yaml` (C8)
- `contracts/src/veridicus_contracts/checks/veracity.py` (`COINCIDENCIA`, `CLAVES_DE_C8`, `problemas_de_vocabulario`, `_problemas_de_coincidencia`)
- `contracts/tests/checks/test_veracity.py`
- `contracts/src/veridicus_contracts/tools/gen_ts.py` y `contracts/tests/tools/test_gen_ts.py`
- `contracts/src/veridicus_contracts/tools/security_surface.py`
- `libs/integrity_policy/src/veridicus_integrity_policy/scan.py`
- `libs/integrity_policy/tests/test_invisible_and_cache.py`, `test_scan_cases.py` y `tests/guards/`
- `.github/workflows/contracts-level0.yml` (paso 5, guardias al 100 %) y `.github/workflows/analyzer-level0.yml` (job `integrity_policy` y la compuerta `coverage_gate`)
- Reglas de U1: `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`, BR1.3, BR1.5 y BR5.1 a BR5.5
- `docs/loop/CANDIDATAS.md`, filas K-89, K-91 y K-28
- `docs/loop/revisiones/U01-T31/ronda-1.md`. Ahí está el antecedente: la suite de `contracts` queda a 0,24 s del techo de 24 s

---

## Casos sonda obligatorios (ML-11)

Cada caso se convierte en una prueba antes de entregar.

1. **Ancho completo:** `ｆａｌｓｏ`, `ＭＩＥＮＴＥ` y una mezcla, `fａlso`, se detectan con el término correcto. El tramo informado cubre los caracteres originales de ancho completo.
2. **Ligaduras y compatibilidad:** `ﬁ` dentro de una palabra se pliega a `fi`. Un término escrito con letras matemáticas, por ejemplo `𝐟𝐚𝐥𝐬𝐨` (U+1D41F…), se detecta. Pon como control negativo una palabra parecida que no es término.
3. **Rellenos Hangul:** cada uno de los 4, insertado dentro de `falso`, no evade el escáner. Al borde del término, conserva la frontera de palabra, igual que hoy con `Cf`.
4. **`Cn` sin asignar:** U+2065, U+FFF0, U+E0002, U+E0080 y U+E0FFF, dentro de un término, no lo esconden.
5. **Fallo cerrado:** C8 sin `fold`, con `normalization: NFC`, con un rango invertido (`[0x2060, 0x200B]`), solapado o fuera de `0x10FFFF`. En `veracity.py` cada caso da un problema que lo nombra. En el escáner, uno sin `fold` o con un valor desconocido lanza la excepción al cargar.
6. **Sin falso positivo:**
   - Un carácter visible de un rango vecino que no se descarta, por ejemplo U+2010 (guion) o U+3165, sigue partiendo la palabra.
   - Un texto sin términos y con caracteres de ancho completo da cero coincidencias.
   - Los casos de `scan-cases.v1.yaml` siguen pasando sin cambios.
7. **Las exclusiones siguen igual:** una cita literal «…» que contiene `ｆａｌｓｏ`, presente literal en una fuente, se excluye. Un tramo «ｆａｌｓｏ» que es solo el término se escanea (D-2).
8. **Propiedad Hypothesis (ML-12):** genera un término de C8, un número de inserciones de cualquier punto de `dropped_code_points` (asignado o no) en cualquier posición y una sustitución de letras ASCII por su forma de ancho completo. El escáner siempre detecta el término y el tramo empieza y termina dentro del texto. Pon un tope de ejemplos con tiempo medido, porque la suite está al límite.
9. **Versión:** C8 con `2.0.1` falla en `problemas_de_vocabulario`. El TypeScript generado trae los rangos y la normalización.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U01-T33`. Si un entorno de `uv` no existe y pide red, para y repórtalo: el humano corre el `uv sync`.

- [ ] **CA-1 (rojo y verde de `contracts`):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/contracts pytest tests/checks/test_veracity.py tests/tools/test_gen_ts.py --no-cov -q
  ```
  Esperado: código 0. La bitácora trae el par falla-pasa.

- [ ] **CA-2 (rojo y verde del escáner):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/libs/integrity_policy pytest -q
  ```
  Esperado: código 0. El rojo de los casos sonda 1 a 4, 7 y 8 falla sobre el `scan.py` de `main`.

- [ ] **CA-3 (lectura de vuelta del C8 versionado):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/contracts python -c "from pathlib import Path; from veridicus_contracts.loaders import load_file; m = load_file(Path('/workspace/.worktrees/U01-T33/contracts/integrity/forbidden-vocabulary.v2.yaml')); print(m['schema_version'], m['match']['fold']['normalization'], len(m['match']['fold']['dropped_code_points']))"
  ```
  Esperado: `2.1.0 NFKD 17`, o el número de rangos que justifique la bitácora.

- [ ] **CA-4 (suite completa de `contracts` en el paso literal de la CI, dentro del techo):**
  ```bash
  timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/contracts pytest
  ```
  Esperado: código 0, cobertura de 80 % o más y **24 s o menos** según la línea final. Corre también la suite de `main`, en `/workspace/contracts`, con el mismo comando y su ruta, para tener la línea base (F-02 de U01-T31). Anota los dos tiempos.

- [ ] **CA-5 (guardias al 100 %):**
  - Después de CA-4, el paso 5 de `.github/workflows/contracts-level0.yml`, con su comando literal.
  - Después de CA-6, la compuerta de `analyzer-level0.yml`, «Ramas de los módulos guardia al 100 % y líneas al 80 % por paquete», con su comando literal. Necesita los cuatro `coverage.json`, que se generan con los cuatro pasos «Informe de cobertura de …» del mismo workflow, corridos tal cual.

  Esperado: código 0 en las dos.

- [ ] **CA-6 (consumidores):**
  ```bash
  timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/libs/incoherence_analyzer pytest --cov=veridicus_incoherence_analyzer --cov-branch --cov-report=json --cov-fail-under=80
  ```
  Esperado: código 0. El analizador sigue en verde con el escáner nuevo.

- [ ] **CA-7 (no se quitó nada):**
  - `pytest --collect-only -q --no-cov` en `contracts` y en `libs/integrity_policy`. Esperado: al menos las pruebas de `main` en cada uno; anota los números.
  - ```bash
    git -C /workspace/.worktrees/U01-T33 diff --exit-code 46dfba2 -- contracts/pyproject.toml contracts/uv.lock libs/integrity_policy/pyproject.toml libs/integrity_policy/uv.lock contracts/integrity/scan-cases.v1.yaml libs/incoherence_analyzer
    ```
    Esperado: código 0.

- [ ] **CA-8 (estático y guardias del repositorio):**
  - En `contracts`: `mypy --strict src`, `ruff check .` y `ruff format --check .`.
  - En `libs/integrity_policy`: `mypy --strict src tests`, `ruff check .`, `ruff format --check .` y `lint-imports`.
  - Todos con `uv run --frozen --offline --directory <ruta absoluta>`.
  - Además, los dos guiones:
    ```bash
    bash /workspace/.worktrees/U01-T33/scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T33
    ```
    ```bash
    bash /workspace/.worktrees/U01-T33/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T33
    ```

  Esperado: código 0 en todos y `0 apariciones` en los dos guiones.

---

## Plan de pruebas (Testing Contract de U1: guardias y contratos primero, en rojo)

1. **Rojo (ML-13):** primero, los casos sonda 1 a 9 en `contracts/tests/checks/test_veracity.py`, `contracts/tests/tools/test_gen_ts.py` y `libs/integrity_policy/tests/`.
   - **Para antes del commit del rojo y avísame.** El orquestador despacha un `revisor` con `sonnet` solo sobre esas pruebas. Después corriges lo que encuentre.
   - El commit va aparte: `test(contracts): …`.
2. **Verde:** C8, `veracity.py`, `gen_ts.py` con `contracts/ts/` regenerado, `scan.py`, `security-surface.json` y las versiones. El commit es `fix(contracts): …`.

---

## Reglas de la app que aplican

- **AUTONOMIA-03:** el cambio solo puede **ampliar** lo que el escáner detecta, nunca reducirlo. Todos los casos de `scan-cases.v1.yaml` y la suite de `tests/guards/` siguen en verde.
- **BR1.3 y BR1.5:** el PR cambia un solo contrato, C8. Sube el menor porque añade un campo, y trae las pruebas que ejercitan el cambio.
- **Solo datos sintéticos.** Sin red, salvo un `uv sync` que corre el humano.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U01-T33.md`, de una página como máximo (ML-7). Trae los pares falla-pasa, los tiempos de CA-4 con la línea base y la tabla de autorrevisión ML-14: una fila por viñeta de «Dentro» y por caso sonda, cada una con la prueba que lo cubre.
- **Commits:** Conventional Commits en español, con alcance `contracts`, citando K-89 y K-91, y el pie de tu modelo.
- **Al terminar:** haz *push* de `tarea/U01-T33` y vuelve con el informe. No abras el PR ni fusiones.
- **Bash simple:** un comando por llamada, con rutas absolutas. Sin pipes, `bash -c`, `time` ni redirecciones, salvo los `timeout` que piden los criterios.
