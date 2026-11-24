# Ronda 2 — U01-T15

VEREDICTO: NO-VERDE

Corrí los seis criterios y todos pasan. Bloquean dos hallazgos: el cambio de `used_in` de `turn_max_chars` oculta un defecto de C2, que era tu punto (1), y P-T15-1 no se aplica con su condición exacta. Tu punto (2), el ajuste de `test_esquemas_estrictos_de_c6_c7_c18_y_c19`, no afloja la prueba.

No puedo escribir el informe porque mis herramientas son de solo lectura. Este texto es el informe completo y se guarda en `/workspace/docs/loop/revisiones/U01-T15/ronda-2.md`.

## Criterios de aceptación, verificados por mí (sobre `98a6dd7`)
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15/contracts pytest tests/checks tests/guards tests/contracts --no-cov -q --tb=short -p no:cacheprovider` | pasa: 1873 passed |
| 2a | CA-2, pruebas | `timeout 400 uv run ... pytest tests/checks --cov-fail-under=0 -q --tb=short -p no:cacheprovider` | pasa: 1633 passed |
| 2b | CA-2, cobertura | `uv run ... coverage report --include=<los 5 módulos y _openapi.py> --fail-under=100 --show-missing` | pasa: 588 líneas y 298 ramas, 100 % |
| 3 | CA-3 | `timeout 60 uv run ... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q` | pasa: 162 passed. El diff solo toca 3 líneas de `used_in`, pero ver F-01 |
| 4 | CA-4 | `timeout 120 uv run ... pytest tests/test_package_map.py --no-cov -q` | pasa: 8 passed |
| 5 | CA-5 | `uv run ... mypy --strict src` y `uv run ... ruff check .` | pasa: `Success: no issues found in 23 source files` y `All checks passed!` |
| 6 | CA-6 | `bash /workspace/.worktrees/U01-T15/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15` | pasa: 0 apariciones |

El worktree quedó limpio al terminar (`git status --short` vacío). No hay `stash` y el reflog no muestra operaciones raras.

## Estado de los hallazgos de la ronda 1
- **F-01: cerrado.** CA-1 y CA-2 están en verde con T15b rebasada.
- **F-02: cerrado.** `error_codes.py:239-246` solo cuenta un `code` cuyo dominio existe en el catálogo (P-T15-4). El catálogo no tiene `code` de tres segmentos que la regex parta mal.
- **F-03: cerrado en P-T15-2, P-T15-3 y P-T15-5.** Sondeé P-T15-5 con una hermana abierta y con una propiedad no declarada, y las dos dan rojo; la hermana cerrada no da hallazgo. P-T15-1 queda con un agujero (F-02 de esta ronda).
- **F-04: cerrado.** `_openapi.hijas` baja por todas las formas y `es_tipo` acepta listas. Hay pruebas por forma.
- **F-05: cerrado hasta donde se puede comprobar.** No hay `stash` ni `--fix`. Que se usara Edit o Write no se puede comprobar en la auditoría: no hay entradas del worktree, ni a favor ni en contra.
- **F-07: parcial** (ver F-03 de esta ronda).
- **E-13: cumplido.** `ABIERTOS_ADMITIDOS` tiene exactamente dos sitios de C21, cada uno con su motivo.
- **`runs` con `maxItems`: cumplido.** `PALABRAS` admite `turns` y `runs`, y `per_run` lleva la marca `report_per_run_items` (`report.schema.v2.yaml:347` y `:380`).

## Hallazgos

### F-01 · ROJO · `contracts/limits.v1.yaml:18` y `tests/contracts/test_correcciones_t15b.py:76-78` · quitar C2 de `used_in` oculta un defecto de C2
Tu punto (1): C2 sí lleva texto que §4.4 (a) obliga a marcar.
- **Qué lleva C2.** `RunRequested.entrada` (`queues/runs.v2.yaml:85-87`) es un `$ref` a la entrada de C6. Ahí `turnos[].texto` es `{type: string}` sin tope (`analyzer/v1/entrada.schema.json:150-152`). El mensaje de C2 lleva entonces toda la transcripción sin acotar, igual que el `POST /sessions` que E-14 tuvo que cerrar en C1.
- **Lo que pedía el diseño aprobado.** `security-design.md:537` (§5) fija `turn_max_chars ... used_in: [C1, C2]`.
- **Por qué la guardia no lo ve.** `_textos_libres` usa `resolver`, que solo sigue las referencias `#/` (`_openapi.py:28-41`). Ninguna guardia de límites recorre C6, así que el texto de C2 no lo revisa nadie.
- **Qué hizo la comprobación inversa.** Era la única señal del hueco, y el codificador la apagó: bajó `used_in` a `[C1, C5]` y cambió la aserción `["C1","C2","C5"]` de una prueba de T15b ya fusionada. Esa aserción la fijó T15b bajo E-15, que mandó *añadir* C5, no quitar C2. No hay decisión ni precisión del humano que lo cubra.
- **Qué pide la tarea.** «Si una guardia encuentra un defecto, para y lo informas.»

**Corrección:** restaurar `[C1, C2, C5]` y la aserción de T15b, dejar la prueba en rojo o como candidata, e informar al humano. Cerrar el hueco necesita una decisión parecida a E-14 (un tope del mensaje de C2 o una marca), y no sale de T15.

### F-02 · NARANJA · `checks/strict_bodies.py:159-170` · P-T15-1 sin su condición exacta
P-T15-1 exige que «el esquema de los valores también sea estricto». El código solo pide que `additionalProperties` sea un diccionario no vacío. Lo sondeé con `uv run ... python -c "..."`:
- valores `{'description':'libre'}`: devuelve `[]` y el mapa cuenta como cerrado;
- valores `{'minLength':0}`: devuelve `[]`;
- valores `{'type':['object','string']}`: sí da rojo.

Un esquema de valores sin `type` admite cualquier objeto abierto, y la guardia no lo marca porque `_objetos_abiertos` solo mira nodos con `type: object` o con `properties`. Ningún contrato real usa hoy esa forma, pero esta guardia es de AUTONOMIA-04 y está al 100 % de ramas. Lo que corresponde es exigir que el esquema de los valores tenga un `type` (o `$ref`) que la guardia pueda revisar, con un control negativo.

### F-03 · AMARILLO · bitácora, rojo primero (misma clase que F-07)
- La respuesta dice «el rojo va literal», pero la bitácora (`U01-T15.md:174`) pega «(... 25 mensajes más ...)». La lista `FAILED` sí está completa.
- Se cambiaron pruebas después del rojo sin volver a correrlo con los archivos del commit final (paso 4 del plan): tres en `5c56651` y una en `742fe6a`.
- `test_los_parametros_de_nivel_de_ruta...` estaba en rojo por una precondición equivocada: `/users/{user_id}` no tiene `get`. No probaba la regla.
- Los controles negativos de P-T15-5 solo fallan por `AttributeError`. La bitácora lo admite (`:306`).

### F-04 · AMARILLO · bitácora · SHA viejos
El acuse y las secciones de la ronda 2 citan `e44bed9` y `a5b1f32`, de antes del rebase, junto a los vigentes (`0e01e3a`, `5c56651`).

## Punto (2): el ajuste a `test_esquemas_estrictos_de_c6_c7_c18_y_c19` no afloja la prueba
El cambio añade tres hallazgos esperados (`/allOf/{0,1,2}/if`) a una igualdad exacta y no quita ninguno. Esos `if` aparecen porque, con la raíz abierta, P-T15-2 ya no los cuenta como refinamiento; la prueba de `Consent` se ajustó por lo mismo. Esa parte de la prueba nunca se había ejecutado antes de `742fe6a`: el primer bucle fallaba antes, por K-36. La prueba sigue exigiendo los hallazgos de `/`, de `/$defs/otro` y de `/properties/anidado`, y el caso de `unevaluatedProperties` sigue en `[]`.

## Tareas candidatas (defectos reales fuera de alcance)
- **C2 lleva texto de turnos sin tope por `entrada` → C6.** Hace falta una decisión del humano parecida a E-14: un tope del mensaje o una marca. Va con F-01.
- **Clase general:** un esquema sin `type` bajo un objeto cerrado (`properties: {a: {}}`) admite objetos abiertos sin que §4.3 lo vea. Es más amplio que P-T15-1.

```
VEREDICTO: NO-VERDE
ROJO|contracts/limits.v1.yaml:18; tests/contracts/test_correcciones_t15b.py:76-78|quitar C2 de used_in de turn_max_chars oculta que C2 lleva texto de turnos sin tope (entrada -> C6 texto) contra §5 aprobado y edita la aserción de T15b sin decisión
NARANJA|checks/strict_bodies.py:159-170|P-T15-1 sin su condición: propertyNames.enum con valores {description} o {minLength} cuenta como cerrado
AMARILLO|docs/loop/bitacoras/U01-T15.md:158-218, 283-306|rojo resumido aunque se dice literal; pruebas cambiadas tras el rojo sin volver a correrlo; rojos por precondición o AttributeError
AMARILLO|docs/loop/bitacoras/U01-T15.md:151, 220|SHA de antes del rebase (e44bed9, a5b1f32)
INFORME: docs/loop/revisiones/U01-T15/ronda-2.md
```
