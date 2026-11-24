# Ronda 4 — U01-T15

VEREDICTO: NO-VERDE

Los seis criterios y la suite completa pasan. Los cuatro hallazgos de la ronda 3 están cerrados: F-01, F-02 y F-03 por el retrabajo, y la candidata K-39 está anotada. Mis sondeos de F-01 dan rojo en todas las formas que pediste. El rojo de `a26cb05` lo repetí yo, con las pruebas de `a26cb05` y con las de `2b6323b`, y coincide con la bitácora.

Bloquea un hallazgo nuevo de la misma clase que el F-01 de la ronda 3: la ruta de la instancia no distingue una propiedad llamada `items` (o `additionalProperties`) de la palabra clave del mismo nombre. Así, una marca que no acota el texto sigue contando como si lo acotara, también en `turnos[].texto`.

## Criterios de aceptación, verificados por mí (sobre `7fddb25`)
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15/contracts pytest tests/checks tests/guards tests/contracts --no-cov -q -p no:cacheprovider` | pasa: 1904 passed en 92,7 s (88 s en la ronda 3) |
| 2a | CA-2, pruebas | `timeout 400 uv run ... pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: 1657 passed |
| 2b | CA-2, cobertura | `uv run ... coverage report --include=&lt;los 5 módulos y _openapi.py&gt; --fail-under=100 --show-missing` | pasa: 658 líneas y 324 ramas al 100 % |
| 3 | CA-3 | `timeout 60 uv run ... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q -p no:cacheprovider` | pasa: 162 passed. El diff de C25 frente a la base son solo los dos `used_in` ya revisados |
| 4 | CA-4 | `timeout 120 uv run ... pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa: 8 passed |
| 5 | CA-5 | `uv run ... mypy --strict src` y `uv run ... ruff check .` | pasa: `Success: no issues found in 23 source files` y `All checks passed!` |
| 6 | CA-6 | `bash /workspace/.worktrees/U01-T15/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15` | pasa: 0 apariciones |
| — | Suite completa | `timeout 600 uv run ... pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2116 passed, 1 warning (`test_socket_bloqueado`, ya existía) |

Al terminar, el worktree está limpio, sin `stash`, y sigue en `7fddb25` sobre la base `8481b3d`. El worktree temporal que usé para el rojo estaba en el scratchpad y ya lo quité.

## Comprobaciones pedidas
1. **F-01: cerrado en lo que pedía la ronda 3.** Repetí los sondeos sobre copias en memoria de los contratos reales:
   - **La rama marcada de C2 movida fuera del `allOf`.** Da rojo en `…/turnos/items/properties/texto (§4.4 a)` en los nueve casos: `oneOf`, `anyOf`, `if`, `then`, `else`, `not`, un `$ref` local dentro de `oneOf`, un `allOf` dentro de `anyOf` y un `allOf` dentro de `if`.
   - **El esquema compartido `T`**, en `p1` con marca y en `p2` sin ella, da rojo en `p2`. En orden inverso, da rojo en `a2`.
   - **Las marcas legítimas** en `prefixItems/0` y en `additionalProperties` acotan bien. Una marca en `items` no acota un texto de `prefixItems`, que es lo correcto.
   - **Los ciclos se cortan.** Un `A.x → A` da 2 nodos.
   - **El costo crece de forma exponencial** con la profundidad de los `$ref` compartidos (ver F-02). En los contratos reales no se nota.
   - **Encontré otra forma** de que una marca que no acota cuente como si acotara: F-01 de esta ronda.
2. **F-02 de la ronda 3: cerrado.** `_texto_de_cuerpos` pasa el `requestBody` y el tipo de contenido. Hay un caso positivo y uno negativo para C1 (`/sessions/{session_id}/transcript`) y para C21 (`/v1/generate`).
3. **F-03 de la ronda 3: cerrado.** Saqué los SHA de los cinco archivos de `docs/loop` con `grep -rhoP` y los crucé con `git log --format=%h feat/b1-contratos..HEAD`. Los 22 SHA distintos están en la rama. La única cadena de 40 caracteres es el hash de la tarea, no un commit. `U01-T15-ronda-3-respuesta.md` ya no está atrasada.
4. **Rojo: verificado.** Usé un worktree temporal en el scratchpad con el código de `a26cb05`, que es igual al de `ee56f8c`:
   - con las pruebas de `2b6323b` salen 8 failed y 31 passed, en las líneas 558 (×5), 575, 598 y 618;
   - con las pruebas de `a26cb05` sale el mismo resultado, 8 failed y 31 passed.

   Coincide con la bitácora (`:684-751`). Todos fallan por la aserción de la regla.
   - `2b6323b` solo intercambia dos elementos de una lista esperada en el caso negativo de C21. En el rojo no se llega a esa aserción, porque el caso positivo falla antes.
5. **Nada se aflojó.**
   - `git diff ee56f8c HEAD -- contracts/tests` solo añade pruebas.
   - Ningún contrato cambia, salvo los dos `used_in` ya revisados: `anonymizer_response_max_bytes` en `[C21]` y `research_report_max_bytes` en `[C1]`.
6. **K-38 y K-39: cumplido.** Las dos están en `docs/loop/CANDIDATAS.md:46-47`, como «Pendiente».

## Estado de los hallazgos de la ronda 3
- **F-01 (NARANJA): cerrado.** Las marcas de `oneOf`, `anyOf`, `if`, `then` y `else` ya no cuentan, y el esquema compartido se revisa en cada ruta.
- **F-02 (AMARILLO): cerrado.**
- **F-03 (AMARILLO): cerrado.**
- **Candidata K-39: anotada.**

## Hallazgos

### F-01 · NARANJA · `checks/limits_match.py:161-171` (`_paso`) · la ruta de la instancia confunde una propiedad llamada `items` con la palabra clave `items`
`_paso` devuelve el nombre de la propiedad cuando la hija es una propiedad, y el resto del puntero (`items`, `additionalProperties`, `prefixItems/0`, `patternProperties/&lt;x&gt;`) cuando es un valor. Las dos formas dan el mismo segmento de ruta. Una marca bajo `properties: {items: …}` queda en la misma ruta que los elementos de un array, aunque `properties` no se aplica a un array.

Lo reproduje sobre copias en memoria de los contratos reales:
- **En C5, que no tiene tope.** Con `l: {type: array, items: {type: string}, allOf: [{properties: {items: &lt;marca&gt;}}]}`, no sale ningún problema y el texto de los elementos queda sin tope. Con `additionalProperties` en lugar de `items` pasa lo mismo.
- **En C2, sobre `turnos[].texto`, la entrada de `MARCA_PROPIA_OBLIGATORIA`.** Cambié la rama de refinamiento de `turnos: {items: …}` a `turnos: {properties: {items: …}}`, y `limits_match` no da ningún problema nuevo.

Hoy lo atrapa otra guardia: `strict_bodies.comprobar_esquema` sobre esa entrada da rojo en `…/turnos` y en `…/turnos/properties/items`, y `test_la_rama_anidada_de_c2_…` lo vería en CI. Pero esa red es indirecta y solo cubre el fragmento real de C2 (K-39). La regla (a) de `limits_match` sigue aceptando una marca que no acota.

Corrección sugerida:
- que cada segmento de la ruta lleve su clase, por ejemplo `("prop", nombre)` frente a `("items",)` o `("additionalProperties",)`;
- un control negativo con `properties: {items: …}` frente a `items`;
- otro con `properties: {additionalProperties: …}` frente a `additionalProperties`.

### F-02 · AMARILLO · `checks/limits_match.py:181-213` (`_nodos`) · costo exponencial con la profundidad de los `$ref` compartidos
Al deduplicar por (esquema, ruta, efectividad), cada camino distinto se recorre aparte. Lo medí con un grafo de *n* niveles, cada uno con dos `$ref` al siguiente:

| *n* | nodos | tiempo |
|---|---|---|
| 10 | 2047 | 0,01 s |
| 14 | 32 767 | 0,13 s |
| 16 | 131 071 | 0,54 s |
| 18 | 524 287 | 2,41 s |

Los ciclos se cortan bien, y en los contratos reales no se nota (CA-1 tarda 92 s, frente a 88 s en la ronda 3). Conviene dejar un tope de profundidad, o una nota en el docstring, antes de que un contrato con `$defs` muy reutilizados lo dispare.

### F-03 · AMARILLO · `tests/checks/test_limits_match.py:547-560` · `not` sin control propio
La prueba parametrizada cubre `oneOf`, `anyOf`, `if`, `then` y `else`, pero no `not`. Mi sondeo da rojo con la rama en `not`, porque `hijas` no baja por `not` y la marca no se ve. Ninguna prueba fija ese comportamiento: si mañana `hijas` bajara por `not` con efectividad heredada, nada lo detectaría.

## Tareas candidatas (defectos reales fuera de alcance)
- **K-38, más amplia.** `_openapi.hijas` no baja por `contains`, `dependentSchemas`, `propertyNames`, `unevaluatedItems` ni `not`, así que un texto bajo esas formas no lo revisa §4.4 (a). En C5, `contains: {type: string}` y `dependentSchemas: {a: {properties: {b: {type: string}}}}` no dan rojo. Es la misma clase que K-38: lo que la guardia no ve.
- **K-39 sigue vigente**, como está anotada.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/limits_match.py:161-171|la ruta de la instancia no distingue una propiedad llamada items o additionalProperties de la palabra clave: una marca bajo properties.items acota los elementos de un array, también turnos[].texto de MARCA_PROPIA_OBLIGATORIA
AMARILLO|contracts/src/veridicus_contracts/checks/limits_match.py:181-213|la deduplicación por (esquema, ruta, efectividad) recorre cada camino: costo exponencial con la profundidad de los $ref compartidos (2,4 s con 18 niveles)
AMARILLO|contracts/tests/checks/test_limits_match.py:547-560|la marca en not no tiene control negativo propio
INFORME: docs/loop/revisiones/U01-T15/ronda-4.md
```
