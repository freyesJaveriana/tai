# Ronda 1 — U01-T03

VEREDICTO: NO-VERDE

Hay un solo hallazgo que bloquea, y es NARANJA: la guardia de `servers` internos pasa en vacío. El rojo es legítimo, se cumplen E-2 y E-3 y no hay datos del piloto en el diff. H-1 se reproduce y es un defecto real de T02.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Recolección sin errores | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T03/contracts pytest tests/contracts tests/guards --co -q --no-cov` | pasa: `138 tests collected`, código 0 |
| 2 | Rojo por fallos, no por errores | `timeout 60 uv run … pytest tests/contracts tests/guards --no-cov --junitxml=build/red.xml -q --tb=line` | pasa: código 1. `build/red.xml` dice `errors="0" failures="138" skipped="0" tests="138"` y no pasa ninguna |
| 2b | Causa del rojo | `grep -o -E "<failure message=\"Failed: (contrato\|módulo) ausente[^\"]*\"" …/build/red.xml` | 138 de 138: 136 por «contrato ausente» y 2 por «módulo ausente: veridicus_contracts.model_calls» |
| 3 | `check_red` lee el informe real | `uv run … python -m veridicus_contracts.tools.check_red build/red.xml` | pasa: `rojo comprobable: 138 fallos y 0 errores`, código 0 |
| 4 | Pruebas propias de `check_red` | `timeout 60 uv run … pytest tests/tools/test_check_red.py --no-cov -v` | pasa: 8 passed |
| 5 | Marcadores en todas las pruebas | la misma recolección con `-m "c1 or c6 or … or asyncapi"` | pasa: 138, igual que CA-1. `pyproject.toml` lleva `--strict-markers` y 12 marcadores; no baja ningún umbral |
| 6 | Las tareas anteriores siguen en verde | `timeout 120 uv run … pytest tests/test_runner.py … tests/test_validators.py --no-cov -q` | pasa: 76 passed |
| 7 | No se escribió ningún contrato | `git -C /workspace/.worktrees/U01-T03 diff --name-status feat/b1-contratos...HEAD` | pasa: solo `fixtures/`, `tests/`, `check_red.py`, `pyproject.toml` y la bitácora; borra `contracts/fixtures/.gitkeep` |
| 8 | Tipos y *lint* | `uv run … mypy --strict src` · `uv run … ruff check .` | pasa: `Success: no issues found in 7 source files` · `All checks passed!` |
| 9 | Ningún script aplica cambios al clúster | `bash /workspace/.worktrees/U01-T03/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T03` | pasa: 0 apariciones |
| — | Worktree limpio al terminar | `git -C … status --short --ignored contracts/build` | limpio; solo queda `contracts/build/`, que está ignorado |
| — | Fixtures de C6 frente a los esquemas en su sitio | `uv run … python …/scratchpad/check_c6.py …/analyzer/v1/fixtures` (lee `/insumos` en su sitio y no copia nada) | 16 de 16 dan lo esperado: 5 se aceptan y 11 se rechazan por la palabra clave, la ruta y el texto que declara la prueba |

**(a) Rojo legítimo.** `load_contract` y `importar_o_fallar` convierten lo que falta en un fallo. Contrasté los enum incrustados en `test_autonomia_03.py` (`tipo`, `codigo`, `motivo`, `papel`) con `/insumos/…/salida.schema.json` y coinciden. Los 9 términos coinciden con BR5.1. Las mutaciones de C6 en `test_autonomia_05.py` corresponden al `if/then` real del esquema: `maxItems: 0` en `hallazgos` y en `observaciones_conductor`, `required: [error]` y `not required error`. La marca `"description": "` que altera la prueba E18 existe en la línea 29. Las pruebas comparan contra lo que leen (la huella JCS contra `.sha256` y `effective_config` contra el fixture de C18), no contra códigos de salida.

**E-2 se cumple.** `test_effective_config_de_c2_cumple_c18` lleva `c18` además del `asyncapi` del módulo, y queda fuera con `-m "not c18"`.

**(b) Guardias.** Cubren lo que pide el paso 5:
- AUTONOMIA-05: los 5 campos obligatorios en C6 y en C7, y `error` ⇒ vacíos.
- AUTONOMIA-03: el vocabulario de veracidad y quién y cuándo.
- AUTONOMIA-04: C21 estricto, una sola puerta `generate`, C19 cerrado, y `anonimizador_no_disponible` e `incidente_anonimizacion` válidos.

Quedan para U10 y U11, fuera del paso 5: la cita alterada o en otro turno, la cita seudonimizada que se restaura, y el *payload* saliente con fallo cerrado. En U1 solo se fija el enum (`cita_en_otro_turno`, `marca_alterada`), y eso está comprobado.

**(c) E-3 y datos.**
- No hay ningún `*.schema.json` fuera de `vendor/` ni de `tests/data/`.
- Busqué 7 descripciones literales de C6 en el worktree y en la bitácora con `grep -rn -F` y hubo 0 coincidencias.
- Los nombres de `synthetic-names.yaml` no aparecen en `/insumos`. La única coincidencia es «Aurelio», en una sentencia pública de `triage_normas.csv`, y no viene del piloto.
- Los textos son sintéticos.

## Hallazgos

### F-01 · NARANJA · `tests/guards/test_autonomia_04.py:35-65` · la guardia de `servers` internos pasa en vacío
`servidores_externos` devuelve `[]` cuando el documento no declara `servers`, así que `test_los_servers_son_internos` pasa para un contrato sin servidores. El riesgo es concreto: el C2 de contract-summary (líneas 1204-1247) no tiene bloque `servers`, mientras que el paso 7 exige «`servers` internos». Si T05 copia esa forma, la guardia de AUTONOMIA-04 y NFR1.1 queda en verde sin haber comprobado nada. La tarea lo prohíbe: «Ninguna guardia pasa en vacío». **Arreglo:** exigir al menos un servidor (`assert servidores`) antes de comprobar que todos son internos. Esto afecta a los 7 casos parametrizados.

Barrido de la clase:
- `test_el_esquema_no_fija_el_prefijo_de_las_claves` (`all([])`) también pasa sin patrón, pero ahí es semánticamente correcto: sin patrón no hay prefijo fijado.
- `test_ningun_nombre_ni_enum_declara_veracidad` sí exige `nombres` no vacío.
- `_objetos_abiertos` revienta con `KeyError` si C21 usa `$ref` (falla, no pasa).

No encontré otros casos.

### F-02 · AMARILLO · `test_autonomia_04.py:143-161` · `_cadenas_abiertas` no ve todas las cadenas
Solo mira `type == "string"`. Una cadena declarada como `type: [string, "null"]` o sin `type` escapa al control de NFR1.4.

### F-03 · AMARILLO · marcadores · el mismo archivo lleva dos marcadores distintos
`model_calls/model-call.v1.yaml` lleva `c13` en `tests/contracts/test_model_call.py`, pero `c19` en `test_autonomia_03.py:150` y `test_autonomia_04.py:178`. PD-8 pide «el marcador del contrato que lee», y el archivo lo crea T08 (C13).

### F-04 · AMARILLO · fixtures de C2, C3, C5, C7, C18, C19 y C21 · UUID de relleno con secuencias de 8 y 12 dígitos (H-2)
Por ejemplo `11111111-aaaa-4bbb-8ccc-000000000001`. Según §4.10, `checks/synthetic.py` rechaza «en todo campo de texto» las secuencias de 6 a 10 dígitos. El problema aparece en unos 40 fixtures (lo conté con `grep -c -P`). Ahora es barato usar UUID con hexadecimal mezclado.

### F-05 · AMARILLO · `tests/helpers.py:134-143` · el helper repite la regla de URI del registro
`_uri_natural` hace `urljoin(BASE_URI, "/" + id.lstrip("/"))`. Eso duplica en las pruebas la regla de `registry._uri_de`, que debería ser el único resolvedor (BR12.3), y ya diverge de ella (es justo la diferencia de H-1). Cuando se corrija H-1, conviene que el helper use la función del registro.

### F-06 · AMARILLO · `test_autonomia_03.py:281-291` · `test_c7_registra_quien_y_cuando_decidio` es débil
Comprueba con `campo in str(condiciones)`, que se cumple aunque la condición prohíba el campo. Lo compensan los fixtures E35 (`accepted-sin-decided-by` y `pending-con-decided-at`).

## (d) Supuestos que la bitácora impone a otras tareas
- **T04:** pide una función `check_c6_copy(carpeta) -> list[str]` en `conftest`. Es compatible con F7 en `pytest_sessionstart`.
- **T05:** propone que `effective_config` quede como `type: object` hasta T09. Eso **contradice** el paso 7 («`effective_config` contra C18») y contract-summary (`$ref`). La propuesta nace de un hueco real de E-2 (ver la primera tarea candidata), pero la decisión es del humano. Los mensajes `RunFailed`, `ResultFailed` y `AudioFailed` no tienen nombre en contract-summary; están declarados como supuesto y son razonables.
- **T08:** que `model_calls.py` conviva con el directorio de datos `model_calls/` funciona al importar, porque el módulo gana al paquete de espacios de nombres. El riesgo es que `importlib.resources` ya no vea `veridicus_contracts.model_calls` como paquete de datos.
- **T09, T11 y T12:** coherentes con FD-U1-02 y con los pasos 13 y 14.

## (e) H-1, confirmado
Corrí `uv run … python …/scratchpad/registry_probe/probe.py …/registry_probe/datos` con el esquema sintético que tiene `$id: veridicus/contracts/prueba/sin-barra`. Resultado: `LoadError … un $id absoluto solo se admite bajo vendor/`.

Ese `$id` es una referencia relativa, no absoluta. `urljoin(BASE_URI, id)` da la misma URI que con barra. Es un **defecto de T02** frente a tres textos:
- el paso 3: «bajo `https://veridicus.invalid/` + `$id`»;
- FD-U1-11: «sin tocar la copia de C6»;
- BR12.3.

Bloquea la verificación `-m c6` del paso 6.

## Tareas candidatas (defectos reales fuera de alcance)
- **H-1:** `registry._uri_de` debe aceptar un `$id` sin barra inicial resolviéndolo con `urljoin(BASE_URI, …)`, con su prueba (rama sin barra, y `https://` ajeno sigue rechazado). Tiene que ir antes de T04, o dentro de T04.
- **Hueco de E-2:** si C2 lleva `$ref` a C18, todas las validaciones de C2 (`asyncapi`, no solo el caso `c18`) fallan por referencia sin resolver hasta T09. Entonces `-m "not c18"` del paso 7 no puede ponerse en verde. El humano decide entre dos opciones: (i) `type: object` en T05, que se cierra en T09; o (ii) marcar `c18` en todos los casos de C2 y cambiar la verificación del paso 7.
- **Verificación del paso 15:** `test_autonomia_04.py -m "not c1"` incluye los casos `c19`, que dependen de T12, y T12 va en la misma ola que T13. Hay que ordenar T12 antes de T13 o usar `-m "not c1 and not c19"`.
- **§4.10:** aclarar si `checks/synthetic.py` exime los campos `format: uuid` y los de *hash* de la regla de 6 a 10 dígitos.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/tests/guards/test_autonomia_04.py:35-65|la guardia de servers internos pasa en vacío sin bloque servers
AMARILLO|contracts/tests/guards/test_autonomia_04.py:143-161|_cadenas_abiertas no ve type lista ni cadenas sin type
AMARILLO|test_model_call.py / test_autonomia_03.py:150 / test_autonomia_04.py:178|model-call.v1.yaml con marcador c13 y c19 a la vez
AMARILLO|fixtures de C2, C3, C5, C7, C18, C19 y C21|UUID de relleno con secuencias de 8 y 12 dígitos frente a §4.10
AMARILLO|contracts/tests/helpers.py:134-143|el helper duplica la regla de URI del registro (BR12.3)
AMARILLO|contracts/tests/guards/test_autonomia_03.py:281-291|quién y cuándo comprobado por subcadena
INFORME: docs/loop/revisiones/U01-T03/ronda-1.md
```
