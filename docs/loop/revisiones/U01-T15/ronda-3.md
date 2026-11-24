# Ronda 3 — U01-T15

VEREDICTO: NO-VERDE

Los seis criterios y la suite completa pasan, y repetí yo los dos rojos de la ronda: coinciden con la bitácora y fallan por la regla. Bloquea un hallazgo NARANJA. Esta ronda `limits_match` empezó a buscar la marca de un texto por su ruta en la instancia, y eso abrió dos agujeros: una marca que no acota esa instancia cuenta igual, y un esquema compartido esconde la segunda ruta sin marca. Los dos alcanzan a `turnos[].texto`, que es la entrada de `MARCA_PROPIA_OBLIGATORIA`.

## Criterios de aceptación, verificados por mí (sobre `4bf7bc6`)
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15/contracts pytest tests/checks tests/guards tests/contracts --no-cov -q -p no:cacheprovider` | pasa: 1896 passed |
| 2a | CA-2, pruebas | `timeout 400 uv run ... pytest tests/checks --cov-fail-under=0 -q -p no:cacheprovider` | pasa: 1649 passed |
| 2b | CA-2, cobertura | `uv run ... coverage report --include=&lt;los 5 módulos y _openapi.py&gt; --fail-under=100 --show-missing` | pasa: 650 líneas y 324 ramas al 100 % |
| 3 | CA-3 | `timeout 60 uv run ... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q -p no:cacheprovider` | pasa: 162 passed. El diff de `limits.v1.yaml` solo toca 2 líneas de `used_in` |
| 4 | CA-4 | `timeout 120 uv run ... pytest tests/test_package_map.py --no-cov -q -p no:cacheprovider` | pasa: 8 passed |
| 5 | CA-5 | `uv run ... mypy --strict src` y `uv run ... ruff check .` | pasa: `Success: no issues found in 23 source files` y `All checks passed!` |
| 6 | CA-6 | `bash /workspace/.worktrees/U01-T15/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15` | pasa: 0 apariciones |
| — | Suite completa | `timeout 600 uv run ... pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2108 passed, 1 warning (`test_socket_bloqueado`, ya existía) |

Al terminar, el worktree está limpio, sin `stash`, y sigue en `4bf7bc6`. Los dos worktrees temporales que usé para el rojo están en el scratchpad y ya los quité con `git worktree remove`.

## Comprobaciones pedidas
1. **F-01 de la ronda 2: cerrado.**
   - `limits.v1.yaml:18` trae `turn_max_chars` con `used_in: [C1, C2, C5]`, y la línea 22 trae `run_message_max_bytes` con `[C2]`.
   - `git diff --stat feat/b1-contratos...HEAD -- contracts/tests` no nombra `test_correcciones_t15b.py`.
   - Frente a la base, el diff de C25 son solo dos `used_in`, y las dos marcas existen en los contratos (K-11 y K-14). `anonymizer_response_max_bytes` pasa a `[C21]` por `anonymizer-proxy.v1.yaml:81`, y `research_report_max_bytes` pasa a `[C1]` por `console.v2.yaml:1359`. Ninguna esconde un texto sin tope.
2. **P-T15-6: cumplido, con una salvedad (F-02).**
   - `_nodos` sigue los `$ref` por `$id` con `ids_de` de `strict_bodies`, sin un segundo resolvedor.
   - El tope se lee en el `requestBody` (C1 y C21) y en el `payload` (C2 y C5).
   - P-T15-5 se aplica en cada nivel anidado (`_bajar`/`_admite`), con controles negativos por nivel.
3. **P-T15-7: cumplido.** Lo sondeé con `_objetos_abiertos`:
   - con el código anterior (`753b878`), `{minLength: 0}`, `{description}` y `{not: …}` devuelven `[]`;
   - con el código nuevo, los tres devuelven `['']`, y `{type: object}` da rojo en `/additionalProperties`.
4. **E-18 y P-T15-8: cumplido en lo que pide la precisión.**
   - `MARCA_PROPIA_OBLIGATORIA` (`limits_match.py:73-77`) tiene una sola entrada, con su motivo, y `test_la_lista_de_marca_propia_obligatoria_…` fija la lista exacta.
   - Sondeé sobre copias en memoria de los contratos reales:
     - C2 sin la rama de refinamiento da rojo en `…/turnos/items/properties/texto … (§4.4 a)` y además en la inversa de `turn_max_chars`;
     - C2 sin el tope del `payload` da rojo en los cinco textos de C6 más la inversa de `run_message_max_bytes`.
5. **Las tres pruebas ajustadas: ninguna se aflojó.**
   - `git diff 7728a13 9a79ed4` solo añade llamadas a `_sin_tope_de_runs` en la copia mutada, más la prueba nueva de la lista.
   - `753b878` solo envuelve cadenas entre paréntesis (ISC004), añade un caso esperado y añade un bloque a una prueba de esta misma tarea.
   - `test_error_codes.py` (T07) solo cambia la línea del `import`, como ya estaba en rondas anteriores.
6. **Rojo real: verificado.** Los dos rojos fallan por la aserción de la regla, nunca por `KeyError` ni `AttributeError`.
   - **P-T15-8.** Corrí las pruebas de `9a79ed4` con su propio código, que es idéntico al de `2688747`. Salió 5 failed, 26 passed, en las líneas 50, 501, 512, 520 y 541. Coincide con la bitácora (`:594-639`).
   - **P-T15-6 y P-T15-7.** Corrí las pruebas de `3155a83` sobre el código de `753b878`. Salió 10 failed, 50 passed, con los mismos mensajes. Coincide con la bitácora (`:355-443`).
   - **Orden.** El acuse de la ronda 3 (`:337`) va antes del rojo (`:350`).
   - **SHA.** Siguen apareciendo SHA de antes del rebase (ver F-03).
7. **Candidatas: cumplido.** K-37 está «Cerrada por E-18 y P-T15-8» y K-38 sigue «Pendiente».
8. **Proceso.**
   - No hay `stash`. El reflog solo muestra rebases y commits.
   - Ningún contrato cambia fuera de `used_in`.
   - Que no hubo heredoc fuera del anexo no se puede comprobar desde git.

## Estado de los hallazgos de la ronda 2
- **F-01 (ROJO): cerrado**, como se describe arriba.
- **F-02 (NARANJA): cerrado.** P-T15-7 está implementado en `strict_bodies.py:196-208` y lo sondeé.
- **F-03 (AMARILLO): cerrado.** El rojo es literal y lo reproduje. Las pruebas que cambiaron después del rojo se volvieron a correr con el archivo del commit final, y cada rojo falla por la regla.
- **F-04 (AMARILLO): no cerrado.** Ver F-03 de esta ronda.

## Hallazgos

### F-01 · NARANJA · `checks/limits_match.py:174-219` · una marca que no acota la instancia, o un esquema compartido, oculta un texto sin marca
`_textos_libres` da por acotado un texto si cualquier nodo con la misma ruta en la instancia lleva `x-veridicus-limit`. `_nodos` visita cada esquema una sola vez, por `id`. Las dos cosas llegaron en `2688747`: antes, la marca se miraba en el mismo nodo.

Es una sola clase de defecto, con dos casos que reproduje sobre copias en memoria de los contratos reales (`uv run … python -c` con `comprobar_documentos`):
- **La rama con la marca pasa del `allOf` a un `oneOf: [rama, {}]`, a un `anyOf: [rama, {}]` o a un `if: rama`.**
  - Resultado: cero problemas nuevos. `turnos[].texto` deja de tener un tope efectivo y no da rojo, ni siquiera en la inversa, porque la marca sigue existiendo.
  - Lo que exigen E-16 y P-T15-6 es la marca «de una rama hermana del mismo `allOf`». El propio docstring de `limits_match.py:10` lo dice así.
- **Un esquema `#/components/schemas/T = {type: string}` se usa en `p1` con una rama marcada (`allOf: [T, marca]`) y en `p2` sin marca, en C5, que no tiene tope.**
  - Resultado: `p2` no da rojo.
  - Con solo `p2`, sí da rojo. El esquema se visitó con la ruta de `p1` y la de `p2` nunca se revisa.

Ningún contrato real usa hoy esas formas. Pero es la regla (a) de una guardia de AUTONOMIA-04 al 100 % de ramas, y el primer caso desactiva sin aviso la única entrada de `MARCA_PROPIA_OBLIGATORIA`.

Corrección sugerida:
- contar solo las marcas de ramas de `allOf`, no de `oneOf`, `anyOf`, `if`, `then` ni `else`;
- deduplicar por (esquema, ruta) en lugar de solo por esquema;
- un control negativo por cada caso.

### F-02 · AMARILLO · `checks/_openapi.py:122-126` y `limits_match.py:237` · el tope en el tipo de contenido no se lee
P-T15-6 dice «en el `requestBody` o en el tipo de contenido» para los OpenAPI, pero `cuerpos` solo pasa el `requestBody` como `acota`. Hoy C1 y C21 ponen la marca en el `requestBody` (`grep` en `contracts/api`), así que el efecto es un rojo de más, no un agujero. O se lee también el tipo de contenido, o se deja anotado que no se admite.

### F-03 · AMARILLO · `docs/loop/bitacoras/U01-T15.md:281, 283, 308, 310` y `U01-T15-ronda-3-respuesta.md:3, 5, 8` · SHA viejos y respuesta desactualizada (sigue F-04 de la ronda 2)
- **La bitácora cita SHA que no están en la rama.** Son `0e01e3a`, `5c56651`, `c1fd2db`, `87e2bca` y `742fe6a` (`git log feat/b1-contratos..HEAD` no los trae, y `742fe6a` no está en ninguna rama).
- **La respuesta afirma lo contrario.** Dice que la bitácora «cita solo los SHA vigentes».
- **La respuesta quedó atrasada.** Dice «Rebasada sobre `2a06d5b`», y la base vigente es `b24ba38`. Además, en su punto F-01 dice que K-37 queda «en rojo en `test_los_contratos_versionados…`», lo que ya no es cierto.

## Tareas candidatas (defectos reales fuera de alcance)
- **K-38 sigue vigente.** Un esquema sin `type` bajo un objeto cerrado admite objetos abiertos sin que §4.3 lo vea.
- **`strict_bodies.comprobar` no recorre `RunRequested.entrada` de C2.** P-T15-5 anidado solo lo fija `test_la_rama_anidada_de_c2_…`, que llama a `comprobar_esquema` sobre el fragmento real. Si se quiere que la guardia lo cubra por sí sola, hace falta una precisión, porque la tarea solo pide las entradas de fallidos de C2.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/limits_match.py:174-219|la marca por ruta acepta una rama de oneOf/anyOf/if que no acota la instancia, y la visita única por esquema oculta la segunda ruta sin marca de un esquema compartido (afecta a MARCA_PROPIA_OBLIGATORIA)
AMARILLO|contracts/src/veridicus_contracts/checks/_openapi.py:122-126; limits_match.py:237|P-T15-6: el tope x-veridicus-max-bytes en el tipo de contenido de C1 y C21 no se lee
AMARILLO|docs/loop/bitacoras/U01-T15.md:281,283,308,310; U01-T15-ronda-3-respuesta.md:3,5,8|SHA de antes del rebase (0e01e3a, 5c56651, c1fd2db, 87e2bca, 742fe6a) y respuesta desactualizada que afirma lo contrario
INFORME: docs/loop/revisiones/U01-T15/ronda-3.md
```
