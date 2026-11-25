# Ronda 5 — U01-T15

VEREDICTO: VERDE

Los seis criterios y la suite completa pasan. Los tres hallazgos de la ronda 4 están cerrados, y el rojo de `1b268cb` y el de `bdae221` los repetí yo: coinciden con la bitácora y fallan por la regla.

Al buscar más colisiones de rutas encontré una forma más, que dejo como AMARILLO y candidata: `prefixItems` o `properties` dentro de la misma rama que la marca. Ningún contrato real la usa. Solo alcanzaría a `turnos[].texto` si alguien añadiera `prefixItems` a la rama de refinamiento de C2, y esa no es una forma razonable para un arreglo de turnos. Detalle en F-01.

## Criterios de aceptación, verificados por mí (sobre `a063bb1`)
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15/contracts pytest tests/checks tests/guards tests/contracts --no-cov -q -p no:cacheprovider` | pasa: 1911 passed en 95,9 s |
| 2a | CA-2, pruebas | `timeout 400 uv run ... pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: 1664 passed |
| 2b | CA-2, cobertura | `uv run ... coverage report --include=&lt;los 5 módulos y _openapi.py&gt; --fail-under=100 --show-missing` | pasa: 677 líneas y 334 ramas al 100 % |
| 3 | CA-3 | `timeout 60 uv run ... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q -p no:cacheprovider` | pasa: 162 passed. El diff de C25 frente a la base son solo los dos `used_in` ya revisados |
| 4 | CA-4 | `timeout 120 uv run ... pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa: 8 passed |
| 5 | CA-5 | `uv run ... mypy --strict src` y `uv run ... ruff check .` | pasa: `Success: no issues found in 23 source files` y `All checks passed!` |
| 6 | CA-6 | `bash /workspace/.worktrees/U01-T15/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15` | pasa: 0 apariciones |
| — | Suite completa | `timeout 600 uv run ... pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2123 passed, 1 warning (`test_socket_bloqueado`, ya existía) |

Al terminar, el worktree está limpio, sin `stash`, y sigue en `a063bb1` sobre la base `d903f71`. El worktree temporal que usé para el rojo estaba en el scratchpad y ya lo quité.

## Comprobaciones pedidas
1. **F-01: cerrado.**
   - **La clase de cada segmento.** `_paso` devuelve `("prop", nombre)`, `("items",)`, `("prefixItems", i)`, `("additionalProperties",)` o `("patternProperties", patrón)`.
   - **Mis sondeos sobre copias en memoria de los contratos reales:**
     - `properties: {items: marca}` en C5 da rojo en `l/items`;
     - `properties: {additionalProperties: marca}` da rojo en `o/additionalProperties`;
     - `turnos: {properties: {items: …}}` en C2 da rojo en `…/turnos/items/properties/texto`;
     - una propiedad llamada `prefixItems/0` frente a la palabra clave da rojo;
     - una propiedad marcada frente a un texto de `patternProperties` también da rojo.
   - **Las marcas legítimas siguen acotando**: en `items`, `additionalProperties`, `prefixItems/0` y `patternProperties` con `/` en el patrón, sin hallazgos.
   - **`MARCA_PROPIA_OBLIGATORIA`** sigue siendo `entrada.transcripcion.turnos[].texto`, y `_ruta_en_texto` la produce con la nueva forma. Si una propiedad se llamara `turnos[]`, solo haría la regla más estricta, nunca más laxa.
   - **Encontré otra colisión**, de aplicabilidad dentro de la rama: ver F-01 de esta ronda.
2. **F-02: cerrado.**
   - **Problema explícito.** Pasado `TOPE_DE_NODOS = 20000`, sale «la guardia superó el tope de 20000 nodos de esquema y no revisa el resto (§4.4 a)». Sale también en un mensaje con tope de bytes (C2, que sondeé), y conserva los textos encontrados antes del tope.
   - **Tamaño de los contratos reales.** Medí con `_nodos` los nodos que expande cada uno de los 22 cuerpos y mensajes. El máximo es `RunRequested`, con 124; le siguen `POST /sessions` con 22 y C21 con 14. Ninguno se acerca a 20 000.
   - **La prueba de conteo de `bdae221` no es trivial.** Cuenta las llamadas a `hijas` y exige que no pasen de 40 000. Sin el tope, ese grafo expande unos 524 000 nodos.
3. **F-03: cerrado.** `not` entra en la prueba parametrizada (`test_limits_match.py:547`).
4. **Rojo: verificado.** Usé un worktree temporal en el scratchpad con el código de `1b268cb`, que es igual al de `c4b522d`:
   - con las pruebas de `1b268cb` salen 6 failed y 40 passed;
   - con las de `bdae221` salen 6 failed y 40 passed, en las líneas 655, 669, 682, 715, 748 y 776.

   Coincide con la bitácora (`:865`, 6 failed y 40 passed). Todos fallan por la aserción de la regla. La prueba del grafo falla en la aserción del problema explícito, no por el reloj. `not` pasa con el código anterior, como dice la respuesta.
5. **Nada se aflojó y los SHA están vigentes.**
   - `git diff c4b522d HEAD -- contracts/tests` solo añade pruebas y `"not"` al parámetro.
   - Ningún contrato cambia, salvo los dos `used_in` ya revisados.
   - Todos los SHA de 7 caracteres citados en la bitácora, en las cuatro respuestas y en las CANDIDATAS están en `git log feat/b1-contratos..HEAD`.
6. **Candidatas: cumplido.** K-38 está ampliada con `contains`, `dependentSchemas`, `propertyNames`, `unevaluatedItems` y `not`. K-39 no cambia.

## Estado de los hallazgos de la ronda 4
- **F-01 (NARANJA): cerrado.**
- **F-02 (AMARILLO): cerrado.**
- **F-03 (AMARILLO): cerrado.**

## Hallazgos

### F-01 · AMARILLO · `checks/limits_match.py` (`_es_efectivo`, `_textos_libres`) · `items` o `additionalProperties` de una rama acotan posiciones que esa rama no cubre
Dentro de una rama de `allOf`, `items` solo se aplica a las posiciones que no cubre el `prefixItems` de esa misma rama, y `additionalProperties` solo a las propiedades que no declara su `properties`. La guardia compara solo la ruta, así que da por acotada también la posición excluida.

Lo reproduje sobre copias en memoria:
- **Caso 8, en C5.** Con `l: {type: array, items: {type: string}, allOf: [{prefixItems: [{}], items: marca}]}`, no sale ningún hallazgo, y la posición 0 queda sin tope.
- **Caso 9, en C5.** Con `o: {additionalProperties: {type: string}, allOf: [{properties: {x: {}}, additionalProperties: marca}]}`, no sale ningún hallazgo, y la propiedad `x` queda sin tope.
- **En C2.** Si se añadiera `prefixItems: [{}]` a `turnos` en la rama de refinamiento, el turno 0 perdería `turn_max_chars` sin que lo detecte `limits_match`, ni tampoco `strict_bodies.comprobar_esquema`.

Por qué no bloquea, según el criterio de esta ronda:
- un barrido de todos los contratos reales no encuentra `prefixItems` ni `additionalProperties` con esquema dentro de un `allOf`;
- la única vía hacia `MARCA_PROPIA_OBLIGATORIA` es editar C2 con `prefixItems` en un arreglo de turnos homogéneo, que no es una forma razonable;
- C2 solo se edita por PR con revisión.

Va como tarea candidata, con su ejemplo.

## Tareas candidatas (defectos reales fuera de alcance)
- **K-40 (nueva).** `limits_match` (a): una marca en `items` o `additionalProperties` de una rama de `allOf` que trae además `prefixItems` o `properties` cuenta como si acotara las posiciones que esa rama excluye. Se arregla exigiendo que la rama con la marca no excluya posiciones, o comparando también `prefixItems` y `properties` de esa rama. Los ejemplos son los casos 8 y 9 de arriba.
- **K-38 y K-39 siguen vigentes**, como están anotadas.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/limits_match.py (_es_efectivo, _textos_libres)|items o additionalProperties de una rama de allOf con prefixItems o properties propios acotan posiciones que esa rama excluye; ningún contrato real usa la forma, candidata K-40
INFORME: docs/loop/revisiones/U01-T15/ronda-5.md
```
