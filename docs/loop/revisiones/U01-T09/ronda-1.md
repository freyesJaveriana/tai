# Ronda 1 — U01-T09

VEREDICTO: NO-VERDE

Los 6 criterios pasan en mi propia ejecución. El veredicto es NO-VERDE porque quedan 5 hallazgos NARANJA, dos de ellos en el saneamiento de mensajes del módulo guardia.

Comprobaciones previas:
- **Hash de la tarea:** `sha256sum` da `6cf3570a…1a5`, coincide.
- **Diff:** `git diff --stat feat/b1-contratos...tarea/U01-T09` toca solo 6 archivos: los 3 esquemas, `profiles.py`, `tests/test_profiles.py` y la bitácora. No toca `effective-config.v1.yaml`, ni los archivos compartidos, ni los *fixtures*, ni las pruebas de T03. dcc2b16 tiene a 4425509 como padre directo, así que no revierte nada de la rama del Bolt.
- **Worktree:** `git status --porcelain` queda limpio al terminar; solo hay archivos ignorados (`.coverage` y cachés).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Paso 11 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T09/contracts pytest tests/test_profiles.py tests/contracts/test_profiles_contract.py --no-cov` | 54 passed |
| 2 | 100 % de ramas | `timeout 120 uv run … pytest tests/test_profiles.py --cov-fail-under=0` y luego `uv run … coverage report --include=src/veridicus_contracts/profiles.py --fail-under=100 --show-missing` | 47 passed; 91 líneas, 30 ramas, 100 % |
| 3 | C2 / c18 | `timeout 60 uv run … pytest tests/contracts/test_queue_messages.py --no-cov` | 18 passed |
| 4 | Mapa de la rueda | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov` | 7 passed |
| 5 | Tipos y *lint* | `uv run … mypy --strict src` y `uv run … ruff check .` | `Success: no issues found in 10 source files` y `All checks passed!` |
| 6 | Sin aplicar al clúster | `bash /workspace/.worktrees/U01-T09/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T09` | 0 apariciones, código 0 |

Más comprobaciones:
- **Marca c18:** `pytest -m c18` da 3 fallos en `test_autonomia_03`. Los tres son `contrato ausente: integrity/forbidden-vocabulary.v2.yaml`, un archivo de otra tarea. No es una regresión de T09.
- **Rojo primero:** la bitácora trae el rojo (51 failed y 2 passed, con `pytest.fail` y no errores de colección) y el verde. Las cifras del verde coinciden con las mías.
- **Datos:** solo sintéticos. No hay claves ni Secrets con forma real; el *canary* es `CANARY_ZXQ_7731`.

## Mutación (procesos aparte; el módulo se carga con exec desde la fuente, sin tocar el worktree)
Corrí 36 mutantes de `profiles.py` más una línea base en verde. El ejecutor está en `/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/mut_runner.py`.
- **Mueren 30**, entre ellos los cuatro de pureza (`open`, `os.environ`, `os.getenv` y `socket`).
  - El de `socket` no lo mata la prueba de pureza: lo detiene `pytest-socket` en la primera prueba.
- **Sobreviven 6:**
  - n.º 17 (`citados[0]` sin `_seguro`): equivalente, porque los nombres de `required` salen del esquema.
  - n.º 19 (`_seguro(ruta[-1])` → `str(...)`): no equivalente.
  - n.º 20 (sin `sorted`).
  - n.º 21 (sin `dict.fromkeys`).
  - n.º 27 (sin `format_checker`): no equivalente.
  - n.º 35 (formato de `str(error)`) y n.º 36 (`tuple(problems)`).

## Hallazgos

### F-01 · NARANJA · contracts/src/veridicus_contracts/profiles.py:114-118 · Se puede esquivar el `?` de los nombres sin forma segura
Los nombres sobrantes salen del texto del mensaje de jsonschema con `'([^']*)'`. Si una clave lleva comillas simples, su `repr` usa comillas dobles y la expresión extrae solo el trozo de dentro, que sí parece seguro. Prueba: en `judge` puse la clave `x'CANARY_ZXQ_7731'y` y salió `perfil todo-local, papel judge, ajuste CANARY_ZXQ_7731: ajuste no permitido`. El docstring promete que «todo nombre que no tenga una forma segura se reemplaza por `?`». La salida correcta es `ajuste ?`.

Arreglo propuesto: calcular los nombres sobrantes como las claves de la instancia que el esquema no declara, en vez de leer el mensaje. Hace falta una prueba de control.

### F-02 · NARANJA · tests/test_profiles.py · Dos mutantes no equivalentes sobreviven en el módulo guardia
- **n.º 19:** quitar `_seguro` de `ruta[-1]` filtraría el nombre. El caso es real: `roles: {"Clave CANARY_ZXQ_7731 x": "texto"}` hoy da `papel ?, ajuste ?: tipo incorrecto`, pero ninguna prueba lo ejercita.
- **n.º 27:** quitar `format_checker` deja pasar `base_url: "no es uri"`. Hoy se rechaza, pero ninguna prueba lo exige.

La cobertura de ramas no los ve, porque no son ramas.

### F-03 · NARANJA · contracts/profiles/profiles.schema.v1.yaml:28-50 · Error doble y falso en `fallback_provider` (candidata del codificador: es un defecto dentro del alcance)
Con un campo sobrante en el proveedor alterno aparecen dos problemas:
- `perfil todo-local, papel -, ajuste fallback_provider: ajuste no permitido`
- `… papel fallback_provider, ajuste sobra: ajuste no permitido`

El primero es falso: dice que un ajuste permitido no lo es, y contradice BR9.8 («nombra … el ajuste» que falla). La causa: `fallback_provider` solo se declara en la base del `allOf`. Cuando esa subrama falla, sus anotaciones se pierden y `unevaluatedProperties: false` lo cuenta como no evaluado. Arreglo: declarar `fallback_provider` en las `properties` del analizador, con `true` o con un `$ref`.

La prueba `test_un_error_del_proveedor_alterno_lo_nombra_como_papel` lo oculta porque compara con `in error.problems`. Debería exigir que esa tupla sea exactamente un problema.

### F-04 · NARANJA · contracts/profiles/profile-base.schema.v1.yaml:11-22 · El sobre de la base queda abierto
Con `kind="base"`, un archivo con la clave raíz `extra_top` se acepta; con `kind="analyzer"`, se rechaza (`ajuste extra_top: ajuste no permitido`). Esto choca con tres fuentes:
- FD-U1-12: «El sobre del archivo … es el mismo para todos».
- C18: la raíz lleva `additionalProperties: false`.
- F8, paso 0: «valida el sobre».

Lo abierto es el perfil, no el sobre. Ninguna prueba cubre una clave raíz sobrante con `kind="base"`.

### F-05 · NARANJA · contracts/profiles/prices.schema.v1.yaml · Un contrato de datos de C18 sin ninguna prueba
`grep -rn -l prices contracts/tests contracts/src` no devuelve nada. Nada comprueba el metaesquema, el *fixture* válido o inválido, ni que se resuelva el `$ref` a `profiles.schema.v1#/$defs/token`. A mano comprobé que funciona: metaesquema OK, un caso válido sin errores y un caso inválido con `additionalProperties ×2`, `minimum` y `pattern`. Aun así, el Testing Contract pide que los contratos de datos se prueben primero, y la tarea dice «pone en verde los casos de perfiles y precios».

### F-06 · AMARILLO · tests/test_profiles.py · Mutantes cosméticos que sobreviven
- n.º 20: `test_los_problemas_salen_en_un_orden_estable` solo compara dos corridas iguales y no fija el orden.
- n.º 21: la eliminación de duplicados nunca se prueba, aunque el caso se da (`purpose` ausente en el analizador produce dos errores idénticos que hoy salen como uno).
- n.º 35: el formato de `str(error)` no está fijado.
- n.º 17 y n.º 36 son equivalentes.

### F-07 · AMARILLO · profiles.py:47-57 · Motivos genéricos
`format`, `minimum` y similares no están en `_MOTIVOS`, así que dan «no cumple el esquema» (por ejemplo, `base_url` o `chunking.window: 0`).

## Candidatas del codificador
- **`same_family_declared`:** no es un defecto de T09. C18 («Reglas de validación de ExecutionProfiles») asigna la regla `same_family_declared` fuera de `demonstration` a U11, y no está en F8 ni en BR9.2–BR9.5 ni BR9.8. Comprobé que hoy `purpose: evaluation` con `same_family_declared: true` se acepta. Conviene que U11 lo cubra con su control negativo y que el orquestador aclare la línea de «Reglas de la app» de la tarea, que se lee como si tocara a T09.
- **Error doble de `fallback_provider`:** sí es un defecto dentro del alcance (F-03).

## Tareas candidatas (defectos reales fuera de alcance)
- **`effective-config.v1.yaml` (T05, E-5):** copia `destination` y `profile` en vez de apuntar con `$ref` a `profiles.schema.v1.yaml`. Hoy coinciden, pero hay riesgo de que diverjan; hace falta una prueba de igualdad o un `$ref`.
- **U11:** la regla `same_family_declared` solo en `demonstration`, y misma `family` en `evaluation`, cada una con su control negativo.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/profiles.py:114-118|Se puede esquivar el ? de los nombres sin forma segura (clave con comillas filtra el canary)
NARANJA|contracts/tests/test_profiles.py|Sobreviven los mutantes no equivalentes 19 (_seguro de ruta[-1]) y 27 (format_checker)
NARANJA|contracts/profiles/profiles.schema.v1.yaml:28-50|Error doble y falso «fallback_provider: ajuste no permitido»
NARANJA|contracts/profiles/profile-base.schema.v1.yaml:11-22|El sobre de la base queda abierto, a diferencia del analizador (FD-U1-12)
NARANJA|contracts/profiles/prices.schema.v1.yaml|Contrato de precios C18 sin ninguna prueba
AMARILLO|contracts/tests/test_profiles.py|Sobreviven mutantes cosméticos (orden, duplicados, formato de str)
AMARILLO|contracts/src/veridicus_contracts/profiles.py:47-57|Motivos genéricos para format y minimum
INFORME: docs/loop/revisiones/U01-T09/ronda-1.md
```
