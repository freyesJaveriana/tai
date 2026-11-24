# Ronda 1: U01-T15

VEREDICTO: NO-VERDE

CA-1 y CA-2 fallan en mi corrida, igual que en la bitácora: 4 pruebas rojas. Tres de esos fallos son defectos reales de los contratos. El cuarto mezcla un defecto real con un falso positivo de la guardia, que se explica en F-02. Además, las guardias dejan pasar tres familias de esquemas y el codificador aflojó la regla de §4.3 para que C1 y C19 pasaran, sin pedir decisión.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | CA-1 | `timeout 300 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15/contracts pytest tests/checks tests/guards tests/contracts --no-cov -q --tb=short -p no:cacheprovider` | **falla**: 4 failed, 1809 passed |
| 2a | CA-2, pruebas | `timeout 300 uv run ... pytest tests/checks --cov-fail-under=0 -q --tb=no -p no:cacheprovider` | **falla**: 4 failed, 1581 passed (las mismas 4) |
| 2b | CA-2, cobertura | `uv run ... coverage report --include=<los 5 módulos> --fail-under=100 --show-missing` | pasa: 501 líneas y 268 ramas, 100 % |
| 3 | CA-3 | `timeout 60 uv run ... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q` | pasa: 161 passed. `git diff` de `limits.v1.yaml`: solo cambian 3 líneas de `used_in` |
| 4 | CA-4 | `timeout 120 uv run ... pytest tests/test_package_map.py --no-cov -q` | pasa: 8 passed |
| 5 | CA-5 | `uv run ... mypy --strict src` / `uv run ... ruff check .` | pasa: `Success: no issues found in 23 source files` y `All checks passed!` |
| 6 | CA-6 | `bash /workspace/.worktrees/U01-T15/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15` | pasa: 0 apariciones |

Al terminar, el worktree está limpio. Solo quedan artefactos ignorados, como `.coverage` y las cachés.

## Hallazgos

### F-01 · ROJO · CA-1 y CA-2 · cuatro pruebas de control positivo en rojo
Corrí una sonda que llama a `comprobar()` de cada guardia sobre el árbol real. Encontré exactamente los 17 problemas que cita la bitácora:
- **limits_match, 11 problemas:**
  - 5 textos de `POST /sessions` sin tope (`console.v2.yaml:653-655` y `Consent`).
  - `TranscriptResult.text` y `model_digest` sin tope (`speech.v2.yaml:123-130`).
  - `per_run` con `maxItems: 3` sin marca.
  - `role` con `maxLength: 32` y `/$defs/token` con `maxLength: 128` sin marca.

  Los 11 son reales.
- **strict_bodies, 2 problemas:** `schema` y `content` de C21 son `{type: object}` abiertos (`anonymizer-proxy.v1.yaml:69` y `:87`). Son reales frente a §4.3; E-13 los resuelve.
- **error_codes:** `POST /acknowledgements 409` con `ethics.text_version_outdated`, que el catálogo da como 422. Es real. El otro problema de esta guardia es F-02.

Ninguna prueba se saltó y ningún umbral se bajó. El criterio no se cumple hasta la ronda 2 sobre T15b.

### F-02 · NARANJA · `error_codes.py` (`CODE_EN_TEXTO`) y `console.v2.yaml:587-589` · falso positivo en `PATCH /users/{user_id} 409`
La descripción dice literalmente «…user.last_admin; **deja de citar** validation.invalid_request (FD-U3-02)». El 409 ya no usa ese `code`, y el 422 de la misma ruta ya lo lleva (`:592`). La guardia toma cualquier mención en prosa como un uso.

La bitácora lo informó como «nombra `validation.invalid_request`», y E-12 se decidió sobre esa lectura: «C1 pasa esos code a su 422». Ese cambio ya está hecho. Para el humano y T15b esto queda así:
- en esta ruta, T15b solo tiene que borrar la frase;
- o la guardia necesita una forma explícita de citar los `code` (por ejemplo, una lista bajo una extensión) en vez de una regex sobre texto libre.

La misma regex también marcará siglas como «e.g.».

### F-03 · NARANJA · `strict_bodies.py:61-104`, `_openapi.py:48-54` y `test_strict_bodies.py` (diff `304ca7d..c2c73ba`) · regla de §4.3 y §4.7 (d) aflojada para que C1 y C19 pasen, sin informar ni decidir
La tarea manda «si una guardia encuentra un defecto en C1, C21 o C19, para y lo informas». En vez de eso, el codificador amplió tres reglas. Mi sonda lo muestra: con la regla literal de BR1.4 fallan `cli/report.schema.v2.yaml` `/properties/runs/items/properties/discards`, `/properties/clarifications/properties/discarded` (por `propertyNames.enum`) y `.../calls/items/allOf/1` (por la regla de «refina»).
1. Cuenta `propertyNames.enum` como objeto cerrado.
2. Trata una rama de `allOf`, `anyOf` u `oneOf` que solo trae `properties` como un refinamiento, no como un objeto. Después del rojo, la prueba se cambió para dejar de esperar `allOf/1` en `{properties: {}}`.
3. `es_problem` acepta un `application/problem+json` en línea, cuando §4.7 (d) pide `$ref: '#/components/responses/Problem'`. Es el caso del 429 y el 503 de `/auth/login`.

Las tres son razonables en lo semántico, pero E-13 solo cubre C21. La bitácora las menciona dentro de «Cambio», no entre los defectos que necesitan decisión.

### F-04 · NARANJA · `strict_bodies.py`, `limits_match.py:132-143`, `config_write.py:52-81` · las guardias no ven todo el esquema (barrido de clase)
Lo comprobé con sondas en memoria sobre C1. Cada una devolvió `[]`, es decir, ningún hallazgo nuevo:
- **strict_bodies:** `x1: {oneOf: [{properties: {libre: {type: string}}}]}` deja pasar un objeto abierto. Es la regla de «refina» aplicada sin un padre cerrado. Tampoco baja por `patternProperties`, `additionalProperties` (cuando es un esquema) ni `if/then/else`.
- **limits_match (a):** un texto sin tope pasa si va dentro de `oneOf` o `anyOf`, o con `type: [string, 'null']`. `_textos_libres` solo baja por `properties` e `items`.
- **config_write:** pasan un parámetro de nivel de ruta (`paths./users/{user_id}.parameters` con `price_limit`) y una propiedad `provider` bajo `patternProperties`.

Los contratos actuales no usan esas formas. Es un agujero latente en guardias de AUTONOMIA-03 y AUTONOMIA-04 que están al 100 % de ramas.

### F-05 · NARANJA · bitácora, línea 71 · pruebas editadas fuera de Edit/Write
El codificador declara `ruff check --select ISC004 --fix` sobre sus cuatro archivos de prueba, y además movió archivos con `git stash push/pop`. Así no se disparan `write-audit-log` ni `run-sensors`. La tarea solo permite heredoc para añadir a la bitácora. Revisé el diff `304ca7d..c2c73ba`: los cambios de ISC004 solo ponen paréntesis, así que no hubo daño semántico. Aun así se rompe la regla vigente.

### F-06 · AMARILLO · `auth_surface.py:96-100` · «seguridad efectiva = sessionCookie» no se comprueba
El docstring lo promete, pero `security: [{}]` (anónima permitida), `security: [{bearerAuth: []}]` y una operación `head` pública no dan hallazgo (lo comprobé con una sonda). Lo mitiga `tests/contracts/test_console.py:206` y `:280-284` (T14) sobre el C1 real, pero la guardia por sí sola no lo cubre.

### F-07 · AMARILLO · rojo primero
- El segundo rojo, con las pruebas del commit final, se pegó resumido («última línea») y no literal.
- `_openapi.py` ya estaba escrito antes del rojo.

El rojo por módulo ausente es plausible, y las pruebas de `c2c73ba` son las mismas que en el commit final.

### F-08 · AMARILLO · cobertura de reglas menores
- `error_codes` (d) no revisa la respuesta `default`.
- `limits_match` (a) no revisa los textos de las respuestas de C21 (`altered_markers.items` es un `string` sin tope).
- Las extensiones solo se validan por nombre, no por sitio ni valor (tabla de §4.6).

## Tareas candidatas (defectos reales fuera de alcance)
- **Ronda 2 y T15b:** E-11 y P-T15b-1 crean la unidad `runs` para el `maxItems` de `per_run`, pero `limits_match.PALABRAS` solo acepta `turns` con `maxItems`. Así T15b dará rojo en (c). La guardia y §4.4 (c) tienen que admitir `runs`.
- **K-32 (de la bitácora):** identificador de contrato para la ruta interna de voz en `used_in`.

```
VEREDICTO: NO-VERDE
ROJO|CA-1, CA-2|cuatro pruebas de control positivo en rojo por defectos de C1, C5, C19 y C21
NARANJA|checks/error_codes.py CODE_EN_TEXTO; console.v2.yaml:587-589|falso positivo en PATCH /users 409: la descripción dice "deja de citar"; E-12 se decidió sobre esa lectura
NARANJA|checks/strict_bodies.py:61-104; checks/_openapi.py:48-54|regla de §4.3 y §4.7 d aflojada para C19 y C1 sin informar ni decidir
NARANJA|strict_bodies.py, limits_match.py:132-143, config_write.py:52-81|las guardias no ven oneOf/anyOf, type en lista, patternProperties ni parámetros de nivel de ruta
NARANJA|docs/loop/bitacoras/U01-T15.md:71|pruebas editadas con ruff --fix y git stash fuera de Edit/Write
AMARILLO|checks/auth_surface.py:96-100|seguridad efectiva sessionCookie sin comprobar (lo cubre T14)
AMARILLO|bitácora, rojo primero|segundo rojo resumido; _openapi.py escrito antes del rojo
AMARILLO|error_codes d, limits_match a, §4.6|default, respuestas de C21 y valores de extensiones sin cubrir
INFORME: docs/loop/revisiones/U01-T15/ronda-1.md
```
