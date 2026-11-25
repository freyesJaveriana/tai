# Ronda 1 — U10-T02

**VEREDICTO: NO-VERDE.** Los 7 criterios pasan, pero dos pruebas rojas de las guardias tienen fallos de fondo. Varios hallazgos obligan a cambiar pruebas rojas, aunque el plan las fija desde `ROJO_SHA` (`32317a9`). Lo señalo en cada uno.

## Criterios, corridos por mí

| CA | Comando (rutas absolutas en el worktree) | Resultado |
|---|---|---|
| 1 | `uv sync --frozen`, `uv lock --check` y `mypy --strict src` | 0, 0 y 0 (15 archivos) |
| 2 | `pytest tests/test_package.py -q`, y lectura de `addopts` en `pyproject.toml` | 3 pruebas pasan; `--disable-socket` sin `--cov` |
| 3 | `pytest tests/guards tests/contracts --collect-only -q` | 0; 89 pruebas, 0 errores |
| 4 | El mismo `pytest -rf`, pero en una copia de `32317a9` sacada con `git archive` al scratchpad | 1; 89 FAILED, 0 ERROR (junitxml); todo `NotImplementedError` |
| 4b | Ese mismo comando en HEAD `91aa097` | 1; 89 FAILED |
| 4c | `git log -- tests/guards tests/contracts` | un solo commit, `32317a9` |
| 5 | `pytest tests/testing --cov=…fake_transport --cov-branch --cov-fail-under=100` | 0; 10 pruebas, 100 % de ramas |
| 6 | `mypy --strict src tests`, `ruff check .` y `ruff format --check .` | 0, 0 y 0 |
| 7 | las tres guardias `check-no-*` | `0 apariciones` cada una |
| — | `git status --short --untracked-files=all` al terminar | worktree limpio |

## Hallazgos

**F-01 · ROJO · `tests/guards/test_autonomia_05_restoration.py` y `fixtures/anthropic/altered_markers.json` · Esperan `[PERSONA_1]` donde, según PD-2, solo puede salir `[ENTIDAD_n]`**
- «Casilda Roncancio» no lleva tratamiento, y sin NER solo la detecta la red de seguridad, que marca como `ENTIDAD` (PD-2 y BR1.5).
- La respuesta guionada usa `[PERSONA_1]`, así que una implementación fiel al plan lo trataría como marca inventada.
- Así, E5, E25 (los 4 casos), E26, la prueba del *fixture* grabado y la de «persona 3» no pueden pasar a verde sin contradecir PD-2. Son 8 pruebas.
- **Corrección (cambia pruebas rojas):** sembrar «doña Casilda Roncancio», para que la regla de tratamiento dé `PERSONA`, o tomar la marca que devuelve `pseudonymize`.

**F-02 · ROJO · `test_autonomia_04_payload.py::test_every_sentence_opening_position…` y `fixtures/transcripts/seeded.json` · La extensión de PD-2 a la apertura de oración queda sin probar**
- Cada turno lista solo nombres completos, y el apellido, a mitad de oración, ya lo marca la red base.
- Lo comprobé con una sonda: un cuerpo con el nombre de pila sin enmascarar y el apellido como marca pasa `assert_no_entity_in_payload` para la posición `tras_punto`.
- La prueba global E29 tampoco lo cubre en 6 posiciones (inicio de valor, `.`, `:`, `;`, `"` y `“`): esos nombres de pila salen a mitad de oración en el turno 17 y la propagación los tapa.
- «Paz», la colisión con nombre común, no está en ninguna lista de entidades.
- **Corrección (cambia pruebas rojas):** listar por turno cada palabra sola, quitar la propagación desde el turno 17 en las pruebas por posición y añadir «Paz».

**F-03 · NARANJA · `test_autonomia_04_fail_closed.py:133-135` · La prueba de BR1.8 puede pasar sin comprobar nada**
- `all([])` es verdadero en las ramas donde no se exige ninguna tabla. En `error_de_serializacion` la tabla ya existe y no se exige.
- Nada comprueba que la tabla tuviera entradas antes de vaciarse.
- **Corrección (cambia una prueba roja):** que `RecordingTable` anote cuántas entradas tenía al llamar a `clear()`, y exigir al menos una tabla también en `error_de_serializacion`.

**F-04 · NARANJA · `test_autonomia_04_payload.py:79-95` (E2) · Compara la primera marca de cada cadena, no la del nombre**
- Si «Vi» o «Luego» faltan en `allowed-words`, la prueba falla o pasa por una razón ajena al nombre.
- **Corrección (cambia una prueba roja):** comparar plantillas exactas, por ejemplo «Vi a X en la plaza.».

**F-05 · NARANJA · `test_autonomia_04_no_leak.py:36-50` · No cubre todas las ramas de error**
- El plan pide «cada rama de error», pero faltan `Timeout`, `ContentBlocked`, `InvalidOutput` (esquema) y las ramas previas al envío (clave, presupuesto, red de seguridad).
- En las ramas de error no se busca ninguno de los dos *canaries* en el `ModelCall` que lleva la excepción.
- **Corrección (añade casos a una prueba roja):** sumar esas ramas y revisar `repr(error.call)`.

**F-06 · NARANJA · Paso 10 del plan frente a `tests/support.py` y `tests/fixtures/` · El candado no protege todo el rojo**
- El `git diff --exit-code ROJO_SHA` solo cubre `tests/guards` y `tests/contracts`.
- Fuera de esas rutas quedan `FAIL_CLOSED_CASES`, `assert_no_entity_in_payload`, `exception_texts` y las listas de entidades, que T03 o T04 podrían debilitar sin que el candado lo note.
- **Corrección:** una precisión del plan que amplíe el `diff` a `tests/support.py` y `tests/fixtures`. No cambia pruebas.

**F-07 · NARANJA · `src/veridicus_anonymizer/api.py:27-33` · El parámetro `catalogs` de `build_anonymizer` es una vía de escape desde producción**
- Un `Catalogs` con `rules=()` y una lista de palabras permitidas muy amplia anula la detección. Eso choca con la firma literal de PD-7 y con la prueba de firma del paso 10.
- **Corrección:** anotar una precisión CG y fijar en el *stub* que T04 revalide el catálogo inyectado, con las mismas reglas y palabras del `data/` versionado; solo dominios y capacidades podrían cambiar, y solo para fallar. No cambia pruebas.

**F-08 · AMARILLO · `docs/loop/bitacoras/U10-T02.md:15` · La causa del rojo no es la que dice la bitácora**
- En `ROJO_SHA`, la mayoría de las pruebas fallan por los *stubs* `FakeTransport`, `FakeResponse` y `bypass` (paso 5), no por `build_anonymizer`.
- **Corrección:** decirlo así en la bitácora.

**F-09 · AMARILLO · `tests/fixtures/anthropic/error_503.json` · *Fixtures* de Anthropic sin verificar**
- Este *fixture* combina un 503 con `overloaded_error`, y, que yo sepa, Anthropic devuelve ese error con 529.
- No pude consultar la documentación: no tengo la herramienta MCP de docs.
- `x-api-key`, `stop_reason: "refusal"` y `usage` coinciden con lo que conozco de la API.
- **Corrección:** T04 debe verificar estos puntos y citarlos en su bitácora: versión de la API, salida estructurada y esfuerzo.

**F-10 · AMARILLO · `test_autonomia_04_fail_closed.py:64-65` · El mensaje se revisa solo en parte**
- «Sin ningún valor» se comprueba solo contra las entidades y los *canaries*, no contra el modelo, el dominio ni el nombre de la clave.

## Lo que sí está bien
- Los controles positivos de fallo cerrado sí podrían dar 1 petición: la misma condición, sin romper.
- El control `bypass` sí rompe la aserción de payload.
- La prueba de la clave busca en la petición cruda, y `repr` la oculta (R-07).
- La cadena de excepciones recorre `__cause__` y `__context__`.
- Solo hay datos sintéticos y *stubs*; ningún umbral bajó.
- La configuración de mypy no tapa errores del paquete: el `ignore_missing_imports` solo afecta a `openapi_spec_validator`.

```
VEREDICTO: NO-VERDE
ROJO|libs/anonymizer/tests/guards/test_autonomia_05_restoration.py|E5/E25/E26 esperan [PERSONA_1] donde PD-2 solo produce [ENTIDAD_n]: 8 pruebas no pueden pasar a verde
ROJO|libs/anonymizer/tests/fixtures/transcripts/seeded.json|la extensión de PD-2 a la apertura de oración queda sin probar en las pruebas por posición (sonda) y en 6 posiciones de E29; falta «Paz»
NARANJA|libs/anonymizer/tests/guards/test_autonomia_04_fail_closed.py:133|BR1.8 puede pasar sin comprobar nada
NARANJA|libs/anonymizer/tests/guards/test_autonomia_04_payload.py:79|E2 compara la primera marca y no la del nombre
NARANJA|libs/anonymizer/tests/guards/test_autonomia_04_no_leak.py:36|faltan ramas de error y el ModelCall de los errores
NARANJA|code-generation-plan.md paso 10|el candado ROJO_SHA no cubre tests/support.py ni tests/fixtures
NARANJA|libs/anonymizer/src/veridicus_anonymizer/api.py:27|el parámetro catalogs es una vía de escape desde producción (PD-7)
AMARILLO|docs/loop/bitacoras/U10-T02.md:15|la causa del rojo en ROJO_SHA no es la que dice la bitácora
AMARILLO|libs/anonymizer/tests/fixtures/anthropic/error_503.json|fixtures de Anthropic sin verificar (529 para overloaded)
AMARILLO|libs/anonymizer/tests/guards/test_autonomia_04_fail_closed.py:64|el mensaje no se revisa contra modelo, dominio ni nombre de la clave
INFORME: docs/loop/revisiones/U10-T02/ronda-1.md
```
