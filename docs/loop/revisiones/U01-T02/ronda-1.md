# Ronda 1 — U01-T02

VEREDICTO: NO-VERDE

Los 7 criterios pasan cuando los corro yo. Quedan tres hallazgos NARANJA en `validators.py`: un defecto que aparece al instalar el paquete y dos casos en que una entrada mal formada o válida produce el error equivocado. El worktree quedó limpio (`git -C /workspace/.worktrees/U01-T02 status --short` sin salida). Rama en `ac0901c`, un solo commit sobre `feat/b1-contratos`.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Carga, registro, JCS | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py --no-cov -v` | pasa: 28 passed en 0,09 s (loaders 7, registry 10, canonical 11). Están todos los casos del paso 3: clave duplicada, `!!python/object`, `no`/`on`, `$ref` canónico, E36, `https://` rechazado, y los vectores `1e21`, `-0`, `5e-324`, `0.1` |
| 2 | Validación estándar | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest tests/test_validators.py --no-cov -v` | pasa: 7 passed, entre ellos `vendor/` = `SHA256SUMS` y meta-esquema alterado |
| 3 | Suite y 100 % de ramas | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest` y `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts coverage report --include="src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100` | pasa: 44 passed en 3,54 s, 97,29 % en total; canonical y registry al 100 % (registry: 18 ramas, 0 parciales) |
| 4 | Tipos y *lint* | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts mypy --strict src` y `… ruff check .` | pasa: `Success: no issues found in 6 source files` y `All checks passed!` |
| 5 | `vendor/` en el mapa y en la rueda | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest tests/test_package_map.py --no-cov -v` | pasa: 7 passed; el inventario ahora compara también `cache-keys` (F-11) y las dos vías de construcción traen `vendor/` |
| 6 | Un solo `YAML(` | `grep -rn "YAML(" /workspace/.worktrees/U01-T02/contracts/src` | pasa: solo aparece en `loaders.py:22` |
| 7 | Sin aplicaciones al clúster | `bash /workspace/.worktrees/U01-T02/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T02` | pasa: `0 apariciones` |

Rojo previo: la bitácora trae la salida antes (`ModuleNotFoundError` en los 4 archivos) y después. Basta para una capa que solo se comprueba con sus pruebas; esta tarea no tiene guardias AUTONOMIA ni contratos de datos.

## Hallazgos

### F-01 · NARANJA · `contracts/src/veridicus_contracts/validators.py:22-24` · El módulo que va en la rueda importa una dependencia que solo es de desarrollo

`validators.py` importa `openapi_spec_validator` al cargarse. Esa biblioteca solo está en el grupo `dev` (`pyproject.toml:23`), y tech-stack-decisions §3, línea 75, la declara como «desarrollo». Las dependencias del paquete (`pyproject.toml:10-15`) no la incluyen.

Consecuencia: si se instala la rueda sin el grupo de desarrollo, `import veridicus_contracts.validators` falla. Con eso caen también `validate_instance`, `validate_json_schema` y `validate_asyncapi`, que no necesitan esa biblioteca.

Esto lo encontré leyendo el código. Al intentar comprobarlo en un entorno limpio, el hook `plan-approval-guard` bloqueó mis comandos `uv` posteriores.

Arreglo dentro del alcance: importar la biblioteca solo dentro de `validate_openapi`. Pasarla a las dependencias principales contradiría §3 y le toca decidirlo al humano.

### F-02 · NARANJA · `validators.py:129`, `:132`, `:183-190` · Una entrada mal formada lanza `TypeError` o `AttributeError` en vez de `ValidationFailure`

Lo comprobé corriendo:

`uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts python -I -c "from veridicus_contracts.validators import validate_json_schema as v; … v({'allOf': 5})"`

Sale `TypeError: 'int' object is not iterable` en `_desconocidas` (línea 129). El meta-esquema ya había detectado el error, pero ese mensaje se pierde.

Revisé las demás apariciones de la misma clase:
- Línea 132: `valor.items()` sobre un valor que no es un mapa (por ejemplo, `properties` como lista) lanza `AttributeError`.
- Línea 129: si el valor es un mapa, `enumerate` recorre sus claves en silencio.
- `extract_message_payloads`, líneas 183-190: `.get`, `.items` e `in` sobre canales o mensajes que no son objetos.

Las comprobaciones de T03 en adelante esperarán `ValidationFailure`, así que estas excepciones se les escaparían.

Arreglo: recorrer solo cuando el tipo es el esperado, o detenerse cuando el meta-esquema ya devolvió errores.

### F-03 · NARANJA · `validators.py:188-190` · Un mensaje de `components` escrito como referencia se rechaza como «mensaje sin carga»

En los canales, un mensaje con `$ref` se salta (línea 185). En `components.messages` no se hace esa comprobación. AsyncAPI 3.0 permite ahí un Reference Object, así que un documento válido con `components.messages.X = {"$ref": …}` fallaría con `ValidationFailure: … sin carga`.

Lo encontré leyendo el código; el hook bloqueó la ejecución. Ninguna prueba cubre el caso: `test_la_carga_de_cada_mensaje_se_extrae` solo prueba `$ref` dentro de un canal.

## Respuestas a las notas del orquestador

- **uv.lock:** el diff solo agrega líneas, no borra ninguna (5 bloques). Son el `sdist` y 89 ruedas de `coverage 7.17.5`, que ya estaba en esa versión en la base; el paquete `types-jsonschema 4.26.0.20261006`, cuya única dependencia es `referencing`, que ya existía; y sus dos entradas en `dev`. No cambia ninguna versión ni entra ninguna dependencia de ejecución. No pude correr `uv lock --check --offline` porque lo bloqueó el hook.
- **Hashes de `vendor/`:** `sha256sum` de los 10 archivos coincide con `SHA256SUMS`. Contra su fuente, sin usar red, los comparé con las copias que traen los paquetes instalados:
  - `json-schema-2020-12.schema.json` es idéntico en contenido a `jsonschema_specifications/.../draft202012/metaschema.json`.
  - Los 7 vocabularios difieren solo en que les falta el bloque `$vocabulary` (comprobado con `diff` en core y validation). Parece una revisión publicada por json-schema.org, pero no lo puedo confirmar sin red.
  - La suite no usa red: `--disable-socket` sigue activo y ninguna prueba lo desactiva.
- **El registro rechaza URIs ajenas:** sí. `https://example.com/…`, `http://json-schema.org/draft-07/schema` y `file:///etc/passwd` dan `Unretrievable` con causa `ForeignUriError`. La forma antigua de E36 da `Unresolvable` sin intentar ir a la red.
- **OpenAPI empaquetado sin usar:** cumple la letra del paso 4 («empaquetados» en `vendor/`) y de D3 («con `openapi-spec-validator`»). Ver A-01.
- **Fechas sin comillas y valores que no son JSON:** rechazarlos es coherente con «todo valor leído es compatible con JSON» y está probado.

## Avisos (AMARILLO)

- **A-01:** `vendor/openapi-3.1.schema.json` y el esquema que usa `openapi-spec-validator` tienen el mismo `$id` (`…/2022-10-07`) pero contenido distinto: `path-item` frente a `path-item-or-reference` en la línea 294, y un `if/then` de `responses`. Hoy se valida con el segundo, que no pasa por `SHA256SUMS`. Conviene que el humano decida si `validate_openapi` debe usar el de `vendor/` o si se documenta esa diferencia.
- **A-02:** `validate_instance` sin registro reconstruye el registro de todo el paquete en cada llamada. El codificador ya lo anotó.
- **A-03:** la bitácora registra la URL y una sola fecha para los 10 archivos, pero no la huella que tenían al descargarse. `SHA256SUMS` demuestra que no cambiaron desde el commit, no que coincidan con la fuente.

## Tareas candidatas (defectos reales fuera de alcance)

- Ninguna.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/validators.py:22-24|el módulo que va en la rueda importa openapi-spec-validator, que solo es de desarrollo
NARANJA|contracts/src/veridicus_contracts/validators.py:129,132,183-190|una entrada mal formada lanza TypeError/AttributeError en vez de ValidationFailure
NARANJA|contracts/src/veridicus_contracts/validators.py:188-190|un mensaje de components escrito como referencia se rechaza como «mensaje sin carga»
INFORME: docs/loop/revisiones/U01-T02/ronda-1.md
```
