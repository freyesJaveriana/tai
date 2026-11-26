# U01-T31: las rutas de C8 que excluyen las citas apuntan a campos que existen en C6

**Unidad:** U1 `contracts` (tarea correctiva, fuera de un plan de Bolt)   **Rama base:** `main` en `2de43aa`
**Destino:** PR a `main`, que fusiona el humano (como U01-T32)
**Origen:** K-86 (revisión de U11-T01, ronda 1). La agrupación U01-T31 nació en el plan de U11 (PD-4, R-5). Su parte de velocidad ya la cerró U01-T18e (PR #49). K-90 se cerró como «no aplica» por decisión del humano (2026-11-26).
**Depende de:** ninguna.
**Riesgo (ML-4):** alto. Toca un contrato (C8) y la guardia de AUTONOMIA-03 → `revisor` con `opus`.

---

## Problema

`contracts/integrity/forbidden-vocabulary.v2.yaml` (C8), en `match.excluded_whole_texts`, excluye del escaneo los textos `salida.hallazgos[].cita_a.texto` y `salida.hallazgos[].cita_b.texto`. Pero en C6 (`contracts/analyzer/v1/salida.schema.json`, `$defs.cita`) el campo de texto de la cita se llama **`cita`**, no `texto`. Por eso las dos rutas no nombran nada.

Nadie lo detectó por dos razones:
- `checks/veracity.py` (`COINCIDENCIA["excluded_whole_texts"]`) y `tests/checks/test_veracity.py` copian la misma ruta equivocada. Comparan C8 consigo mismo.
- Nada comprueba que las rutas `salida.…` de C8 (`excluded_whole_texts` y `scanned`) existan en el esquema C6.

## Alcance

**Dentro:**

> Corregir las dos rutas a `salida.hallazgos[].cita_a.cita` y `salida.hallazgos[].cita_b.cita` en C8, en `checks/veracity.py` y en sus pruebas. Subir `schema_version` de C8 de `2.0.0` a `2.0.1` (corrección sin cambio de forma, BR1.1 y BR1.5). Añadir a `checks/veracity.py` una comprobación que falle si una ruta `salida.…` de `match.excluded_whole_texts` o de `scanned` no existe en el esquema C6, con su control negativo.

- La comprobación nueva resuelve cada ruta contra el esquema C6 cargado con el registro de `contracts` (`properties`, `items` y `$ref` internos). No usa una lista copiada a mano.
- Las rutas que no empiezan por `salida.` (`sugerencia.note`, `sugerencia.reformulation`, `aviso.text`, `reporte consolidado` y `catálogo de mensajes de la consola`) quedan fuera de esta comprobación. Se anota en la bitácora como límite declarado.
- Todo lugar de `contracts/` que fije `2.0.0` para C8 (por ejemplo, `README.md` con `test_readme.py`, o `tools/security_surface.py`) pasa a `2.0.1`, solo si de verdad se refiere a C8.

**Fuera** (rechazar aunque se vea relacionado):

- El nombre del archivo: sigue siendo `forbidden-vocabulary.v2.yaml`. `libs/integrity_policy/scan.py` lo lee por ese nombre.
- La lista `terms`, `scanned` y el resto de `match`: no cambian.
- K-89 (normalización NFKC de C8) y K-91: son otras tareas.
- La versión del paquete `veridicus-contracts` (0.1.1), cualquier `pyproject.toml` y los `uv.lock`, en `contracts/` y en `libs/`. Si una prueba exige subirlos, para y repórtalo.
- `libs/` completo. `libs/anonymizer/tests/guards/test_autonomia_05_restoration.py` usa punteros `/hallazgos/0/cita_a/texto` sobre su propio JSON sintético: no es C6 y no se toca. Anótalo como candidata si crees que debe alinearse.
- C6 (`salida.schema.json`): es el contrato común del TG y no cambia (ADR-017).

---

## Archivos de contexto

- `contracts/integrity/forbidden-vocabulary.v2.yaml` (C8)
- `contracts/analyzer/v1/salida.schema.json` (C6; `$defs.cita` y `$defs.hallazgo`)
- `contracts/src/veridicus_contracts/checks/veracity.py` (`COINCIDENCIA`, `ESCANEADOS`, `problemas_de_vocabulario`)
- `contracts/tests/checks/test_veracity.py`
- `contracts/src/veridicus_contracts/registry.py` y `loaders.py` (cómo se cargan C6 y C8)
- Los archivos que citan C8 o su versión: `git -C /workspace/.worktrees/U01-T31 grep -n "forbidden-vocabulary\|2\.0\.0" -- contracts`
- Reglas de U1: `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`, BR1.1, BR1.5 y BR5.1 a BR5.5
- `docs/loop/CANDIDATAS.md`, filas K-86 y K-90
- `docs/loop/bitacoras/U01-T18e.md`: el tiempo de la suite está al límite (51 s en la CI, techo de 60 s, umbral aceptado de 52 s)

---

## Casos sonda obligatorios (ML-11)

El revisor intentará esto. Cada caso es una prueba antes de entregar:

1. **El defecto original:** una copia de C8 con `…cita_a.texto` hace fallar la comprobación nueva y nombra la ruta.
2. **Ruta casi buena:** `salida.hallazgos[].cita_a` (el objeto, no el texto), `salida.hallazgos.cita_a.cita` (sin `[]`) y `salida.hallazgo[].cita_a.cita` (singular) se rechazan.
3. **Campo que no es texto:** `salida.hallazgos[].cita_a.pagina` (entero) y `salida.hallazgos[].cita_a.avisos` (arreglo) se rechazan: una exclusión de texto entero tiene que apuntar a un `string`.
4. **`scanned` también se comprueba:** una copia con `salida.hallazgos[].hechos` en `scanned` falla.
5. **Sin falso positivo:** las rutas aprobadas pasan, y también las tres `salida.…` de `scanned`. Para `observaciones_conductor[].tema`, C6 la define como propiedad opcional y la comprobación no exige que sea obligatoria.
6. **Fallo cerrado:** si el esquema C6 no se puede cargar, o si una ruta lleva un `$ref` que no se resuelve, la comprobación informa un problema. No pasa en silencio.
7. **Versión:** C8 con `2.0.0`, o con algo distinto de `2.0.1`, falla en `problemas_de_vocabulario`.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U01-T31`.

- [ ] **CA-1 (rojo y verde):** las pruebas nuevas de `test_veracity.py`.
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts pytest tests/checks/test_veracity.py --no-cov -q
  ```
  Esperado: código 0. Par falla-pasa en la bitácora: con C8 y `veracity.py` de `main`, los casos sonda 1, 2, 3, 4, 6 y 7 fallan. Con el cambio, pasan.

- [ ] **CA-2 (lectura de vuelta sobre el C8 versionado):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts python -c "from veridicus_contracts.loaders import load_contract; m = load_contract('integrity/forbidden-vocabulary.v2.yaml'); print(m['schema_version'], m['match']['excluded_whole_texts'][:2])"
  ```
  Esperado: `2.0.1 ['salida.hallazgos[].cita_a.cita', 'salida.hallazgos[].cita_b.cita']`. Si `load_contract` tiene otra firma, usa la que use `test_veracity.py` y anota el comando exacto en la bitácora.

- [ ] **CA-3 (la suite completa en el paso literal de la CI, dentro del techo):**
  ```bash
  timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts pytest
  ```
  Esperado: código 0, cobertura de 80 % o más y **24 s o menos** en local según la línea final (umbral de U01-T18e). Anota el tiempo. Si sube más de 0,5 s respecto de `main`, explica por qué.

- [ ] **CA-4 (guardias al 100 %):** después de CA-3, el paso 5 de `.github/workflows/contracts-level0.yml`, con su `coverage report --include=… --fail-under=100` literal tomado del *workflow*.
  Esperado: código 0.

- [ ] **CA-5 (no se quitó nada):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts pytest --collect-only -q --no-cov
  ```
  Esperado: al menos las pruebas de `main` (anota los dos números).
  ```bash
  git -C /workspace/.worktrees/U01-T31 diff --exit-code origin/main -- contracts/pyproject.toml contracts/uv.lock libs
  ```
  Esperado: código 0.

- [ ] **CA-6 (consumidores):** `libs/integrity_policy` sigue en verde con el C8 nuevo.
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/libs/integrity_policy pytest -q
  ```
  Esperado: código 0. Si su entorno no existe, el primer `uv sync --frozen --directory …/libs/integrity_policy` puede pedir red: anótalo.

- [ ] **CA-7 (estático y guardias del repositorio):**
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts ruff format --check .
  ```
  ```bash
  bash /workspace/.worktrees/U01-T31/scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T31
  ```
  ```bash
  bash /workspace/.worktrees/U01-T31/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T31
  ```
  Esperado: código 0 en todos, y `0 apariciones` en los dos guiones.

---

## Plan de pruebas (Testing Contract de U1: guardias y contratos primero, en rojo)

1. Primero, en rojo: los casos sonda 1 a 7 en `tests/checks/test_veracity.py`, junto con la expectativa nueva de las rutas y de la versión. Commit del rojo aparte (`test(contracts): …`).
2. Después: C8, `veracity.py` y los demás lugares que fijan `2.0.0` para C8. Commit `fix(contracts): …`.

---

## Reglas de la app que aplican

- **AUTONOMIA-03:** C8 es la lista de la prueba de vocabulario prohibido. El cambio no debe ampliar ni reducir lo que se escanea: solo corrige a qué campo apunta una exclusión. La suite de `tests/guards/test_autonomia_03.py` sigue en verde.
- **BR1.5:** el PR cambia solo C8, sube su versión y trae fixtures, en este caso las copias de C8 de los casos sonda, que ejercitan el cambio.
- Solo datos sintéticos. Sin red, salvo un `uv sync` si el entorno lo pide.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U01-T31.md`, de una página como máximo (ML-7). Lleva el par falla-pasa, los tiempos de CA-3 y la tabla de autorrevisión (ML-14): una fila por viñeta de «Dentro» y por caso sonda, con la prueba que lo cubre.
- **Commits:** Conventional Commits en español, con alcance `contracts`, citando K-86, y el pie de tu modelo.
- **Al terminar:** haz *push* de `tarea/U01-T31` y vuelve con el informe. No abras el PR ni fusiones.
- Bash simple: un comando por llamada, con rutas absolutas, sin pipes, `bash -c`, `time` ni redirecciones. El tiempo sale de la línea final de pytest.
