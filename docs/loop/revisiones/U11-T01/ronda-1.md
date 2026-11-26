# Ronda 1 — U11-T01

`revisor` (`opus`), 2026-11-26.

VEREDICTO: NO-VERDE

Los diez criterios pasan cuando los corro yo, y los tres NARANJA de la revisión corta están resueltos. Lo que impide el verde es un NARANJA nuevo, F-01: la guardia AUTONOMIA-03 tiene un hueco a nivel de `analyze`, y ese archivo queda congelado con el rojo.

## Criterios de aceptación, verificados por mí

Todos se corrieron en `/workspace/.worktrees/U11-T01`, en HEAD `079ee1d`, con base `bolt/b11a-analyzer` = `main` = `f943b84`.

| # | Criterio | Comandos que corrí | Resultado |
|---|---|---|---|
| 1 | Lock, instalación y tipos de `src` | `timeout 600 uv lock`, `timeout 120 uv lock --check`, `timeout 600 uv sync --frozen` (con `--extra cli` en `incoherence_analyzer`) y `mypy --strict src`, una vez por paquete | Pasa en los 4. El lock se resuelve sin cambios y el worktree no se modifica. mypy: 21, 6, 4 y 3 archivos sin problemas. |
| 2 | Errores nuevos | `timeout 60 uv run --frozen --offline --directory .../libs/errors pytest` | Pasa: 14 pruebas, 8 de ellas en `test_analyzer_errors.py`, con 100 % de cobertura. |
| 3 | Ejecutor sin red | `pytest tests/test_package.py -q` por paquete, más la lectura de `addopts` | Pasa: 3, 3, 4 y 3 pruebas, y `SocketBlockedError` bloquea la conexión. `addopts = "--strict-markers --disable-socket -m 'not manual'"`, sin `--cov`. Los marcadores `manual` y `cli` están declarados. No hay `omit`. |
| 4 | `--rojo` | `pytest tests/test_conftest_rojo.py -q` | Pasa: 3 pruebas, con su control negativo y el mismo *hook* en `execution_profiles`. El de `integrity_policy` es idéntico (comprobado con `diff`). |
| 5 | Recolección | `--collect-only -q` en el analizador y en `execution_profiles` | Pasa: 107 + 14 = 121 pruebas y 0 errores. |
| 6 | Rojo | `pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=line --rojo` en los dos paquetes, más `tests/guards --rojo` en `integrity_policy` | Pasa. Los tres terminan con código 1: 107, 14 y 20 `FAILED`, y 0 `ERROR`. Todos fallan por el `NotImplementedError` de un *stub*. |
| 7 | Rojo en un commit propio | `git -C … log --oneline bolt/b11a-analyzer..tarea/U11-T01 -- <las 3 rutas>`, más el mismo comando con `support.py`, `integrity_policy/tests/guards` y `/tests/conftest.py` | Pasa: un solo commit, `82b2e6d`, con el mensaje exacto. `ROJO_SHA` coincide con el SHA de 40 caracteres. |
| 8 | Tipos, *lint* y formato | `mypy --strict src tests`, `ruff check .` y `ruff format --check .` por paquete | Pasa en los 4. |
| 9 | Anonimizador de B10a | `pytest --cov=veridicus_anonymizer --cov-branch --cov-fail-under=80` | Pasa: 459 pruebas y 99,54 % de cobertura. |
| 10 | Guardias del repositorio | `bash scripts/check-no-{datos-personales,cluster-ids,insumos}.sh /workspace/.worktrees/U11-T01` | Pasa: los tres dan `0 apariciones`. `check-no-cluster-apply.sh` también da 0. |

**Otras comprobaciones**

- **Historial:** `git log --oneline bolt/b11a-analyzer..tarea/U11-T01` muestra 7 commits, en Conventional Commits en español.
- **Contenido del commit del rojo:** `git show --stat 82b2e6d` lista 15 archivos, todos bajo `tests/`, más `support.py` y el `conftest` de `integrity_policy`. No toca `src/`. Las costuras de F-01 (`build_finding` y el `path` de `load_config`) entraron antes, en `8f75fba`.
- **V-ERRORS:** llamando a `guardia.comprobar(...)` directamente salen exactamente 3 problemas: `run.cancelled`, `config.invalid_gateway` y `system.interrupted`. La suite completa de `contracts` da `2 failed, 2918 passed`, y los dos fallos son de `test_error_codes.py`. No hay otros fallos.
- **Las pruebas rojas se pueden cumplir.** Lo comprobé con sondas en memoria contra el `Anonymizer` real y `ScriptedProvider`:
  - la cita restaurada coincide con T2 y T4, y no sale ninguna entidad;
  - `[PERSONA_9]` da `altered_markers=['/hallazgos/0/cita_b/cita']`;
  - las variantes (a) sin clave, (b) reloj desbocado y (c) `RuntimeError` dan `AnonymizerUnavailable` con 0 peticiones;
  - `make_entrada()` valida contra C6, y `c6_problems` resuelve su URI;
  - los documentos de `test_profile_contract.py` validan con `profiles.validate` y rechazan el campo extra, así que BR2.5 queda solo del lado de U11;
  - los textos de `test_autonomia_03_scan.py` coinciden con `forbidden-vocabulary.v2.yaml` y `notice.v1.yaml`: por ejemplo, «mienten» está en la lista y «verdaderos» no.
- **Datos:** los nombres sembrados no aparecen en `/insumos` (`grep -rlI` sin coincidencias), y la clave es un *canary*.
- **Red:** solo `uv lock` y `uv sync`.
- **Alcance:** el *diff* no toca `contracts/` ni `libs/anonymizer/`.
- **Revisión corta:**
  - F-01 está resuelto: `build_finding` con `monkeypatch`, más `registro.llamadas`.
  - F-02 está resuelto: `.filter(... strip)`.
  - F-03 está resuelto: `support.py` congelado.
  - Los AMARILLO 1 a 5 y 7 están resueltos (`test_autonomia_05_quotes.py:233-348`, `test_profile_contract.py:139-173`, `test_autonomia_03_scan.py`, `test_autonomia_04_composite.py:97,210`, `support.py:180`).
  - El AMARILLO 6 se acepta como simulación declarada.

## Hallazgos

### F-01 · NARANJA · `libs/incoherence_analyzer/tests/guards/test_autonomia_03_vocabulary.py:59-68` · El vínculo de BR9.3 entre `literal_sources` y los turnos de la entrada no se prueba a nivel de `analyze`

- **Qué pide la regla:** BR9.3 dice «se escanean hecho y observaciones con literal_sources = textos de todos los turnos». El paso 3 del plan da por cubiertas BR9.1 a BR9.5 con «aunque la cita literal que lo contiene se conserva».
- **Qué prueba hoy:** la prueba de la línea 59 pone «falso» solo en `cita_a`, que nunca se escanea. Además, `grep -rn "«" libs/incoherence_analyzer/tests` no encuentra ningún `hecho` ni `observaciones` con un tramo «…».
- **El hueco:** una implementación que llame `scan(observaciones, [observaciones])` pasa todo el rojo congelado. Esa implementación excluye cualquier tramo «…» y deja salir «miente» entre comillas angulares, lo que es una fuga de AUTONOMIA-03. Las pruebas directas de `scan()` en `integrity_policy` no cubren este vínculo.
- **Mutante no verificado:** no hay implementación todavía; es una deducción leyendo el código.
- **Corrección:** agregar al rojo dos pruebas a nivel de `analyze`:
  - (a) `observaciones` con `«era falso»` cuyo contenido está literal en un turno → el hallazgo sale y no hay descartes;
  - (b) `observaciones` con `«miente ahí»` que no está en ningún turno → descarte `vocabulario_prohibido`.

  Después, rehacer el commit del rojo dentro de la rama y actualizar `ROJO_SHA`.

### F-02 · AMARILLO · `docs/loop/bitacoras/U11-T01.md:28,39,54,57,61` · Líneas viejas en la bitácora (barrido de la clase)

- La línea 39 dice `ROJO_SHA: pendiente`, así que hay dos líneas `ROJO_SHA:` y la primera no es un SHA. El paso 9 lee «la línea `ROJO_SHA:`».
- La línea 57 («Supuestos que T02 a T05 deben respetar») todavía dice «BR8.1 se prueba con tokens negativos».
- La línea 28 dice que `support.py` queda «fuera de las rutas congeladas».
- La línea 54 no menciona `build_finding` ni el `path` de `load_config`.
- La línea 61 dice que `InputRejected` lleva su `code` por instancia.
- La bitácora pasa de una página (ML-7).
- **Corrección:** marcar esas líneas como reemplazadas o borrarlas, y dejar una sola línea `ROJO_SHA:`.

### F-03 · AMARILLO · Plan, paso 9 (`git diff --exit-code <ROJO_SHA>`) · F-03 de la revisión corta está resuelto a medias

`support.py`, `integrity_policy/tests/guards/` e `integrity_policy/tests/conftest.py` ya están en el commit del rojo. Pero el comando del paso 9 y el CA-7 de esta tarea siguen nombrando solo las 3 rutas originales. El orquestador tiene que escribir las 6 rutas en U11-T04.

### F-04 · AMARILLO · `test_autonomia_03_vocabulary.py:35-41` · Nombres de campo de veracidad copiados a mano

`FORBIDDEN_FIELD_NAMES` repite a mano `categories_forbidden_in_schemas` de C8. Si C8 crece, la prueba no lo sigue. **Corrección:** tomar los nombres de `veridicus_contracts` o de un *stub* que los exponga.

### F-05 · AMARILLO · `libs/execution_profiles/src/veridicus_execution_profiles/floors.py:6` · Constante del paso 4 adelantada

`COMMERCIAL_MIN_CALL_TIMEOUT_S = 270` es del paso 4. Es solo una constante, sin lógica, y la fija `test_package.py:21`. No bloquea.

### Estado del worktree

Hay un directorio sin seguimiento, `docs/loop/revisiones/U11-T01/`, con la revisión corta del orquestador. Ya estaba antes de la revisión; mis comandos no cambiaron nada.

## Tareas candidatas (defectos reales fuera de alcance)

- `contracts/integrity/forbidden-vocabulary.v2.yaml:19-20` nombra `salida.hallazgos[].cita_a.texto`, pero en C6 el campo es `cita`. Es de U1.
- BR2.2 dice que semantic-agent no resuelve claves. Sin embargo, `validate_profile` exige la variable en `env`, y `load_config` la llama. Hay que decidir en U4 cómo carga semantic-agent la configuración sin la clave.

```
VEREDICTO: NO-VERDE
NARANJA|libs/incoherence_analyzer/tests/guards/test_autonomia_03_vocabulary.py:59-68|BR9.3: el vínculo de literal_sources con los turnos no se prueba en analyze (hueco de AUTONOMIA-03)
AMARILLO|docs/loop/bitacoras/U11-T01.md:28,39,54,57,61|Líneas viejas en la bitácora, con dos ROJO_SHA (uno «pendiente»)
AMARILLO|code-generation-plan.md paso 9|El diff del paso 9 y CA-7 no incluyen support.py ni integrity_policy/tests
AMARILLO|libs/incoherence_analyzer/tests/guards/test_autonomia_03_vocabulary.py:35-41|FORBIDDEN_FIELD_NAMES repite a mano la lista de C8
AMARILLO|libs/execution_profiles/src/veridicus_execution_profiles/floors.py:6|Constante del paso 4 adelantada
INFORME: docs/loop/revisiones/U11-T01/ronda-1.md
```
