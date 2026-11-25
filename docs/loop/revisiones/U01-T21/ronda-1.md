# Ronda 1 — U01-T21

VEREDICTO: NO-VERDE

Los seis criterios pasan con mis propias corridas. Aun así, la herramienta no cumple la regla central del paso 2: debe fallar si falta un esquema o catálogo. Con el `.gitkeep` que dejan los directorios de datos, se pueden quitar de la rueda siete catálogos y esquemas (entre ellos los de `errors/`, `ui/` y `queues/`) y la comparación del paso 2 los da por presentes.

## Criterios de aceptación, verificados por mí

Todas las corridas son sobre `d247533`, en `/workspace/.worktrees/U01-T21`.

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests/tools/test_check_package.py --no-cov -v` | pasa: 15 pasadas (8 funciones) |
| CA-2 | `timeout 180 uv run --frozen --directory /workspace/.worktrees/U01-T21/contracts python -m veridicus_contracts.tools.check_package` | código 0 en 1.3 s; C7 21, C1 21, C19 4; la forma antigua no se resuelve |
| CA-3 | `timeout 180 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests/tools/test_check_package.py -k rueda_contaminada --no-cov` | pasa: 1 pasada |
| CA-4 | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests --no-cov -q` | pasa: 2548 pasadas en 123 s |
| CA-4 con cobertura | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests -q -p no:cacheprovider --cov-report=term-missing:skip-covered` | pasa: 98.20 % (piso 80 %); `check_package.py` 58 % |
| CA-5 | `pytest tests/test_package_map.py tests/checks/test_loader_usage.py tests/checks/test_fixture_coverage.py tests/checks/test_ci_workflows.py tests/checks/test_redos.py --no-cov -q -p no:cacheprovider` | pasa: 140 pasadas, incluidas las guardias de T18 |
| CA-5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts mypy --strict src` | `Success: no issues found in 42 source files` |
| CA-5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts ruff check .` | `All checks passed!` |
| CA-6 | `bash /workspace/.worktrees/U01-T21/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T21` | 0 apariciones |

Comprobé el aislamiento del entorno limpio con una sonda propia: construir, `crear_entorno`, `instalar` y luego `ejecutar_guion` imprimiendo `veridicus_contracts.__path__` y `sys.path`. Solo aparecen la biblioteca estándar y `/tmp/tmp…/env/lib/python3.12/site-packages`; nada viene de `.venv` ni del repositorio.

El diff toca 3 archivos, todos dentro del alcance. Al terminar, `git status` sale limpio. No hay datos del piloto.

## Hallazgos

### F-01 · ROJO · `check_package.py:202-206` y guion `:90-94` · un directorio con solo `.gitkeep` cuenta como presente, y faltan esquemas y catálogos sin que nada falle

- **Qué pide la tarea:** el paso 2 debe fallar «si falta un esquema o catálogo de la tabla» (Alcance paso 2, security-design §4.16 paso 2). El F9.2 pide que «cada esquema y catálogo se lee como dato del paquete».
- **Qué hace el código:** `comparar_rueda` da un directorio por presente si hay cualquier archivo debajo. No es solo el caso de `transcript/`: `.gitkeep` también está en `ui/`, `errors/`, `health/`, `format/` y `queues/`.
- **Sonda:** construí la rueda real con `construir(..., offline=True, solo_rueda=True)` y le quité 7 entradas:
  - `errors/error-codes.v2.yaml`
  - `ui/result-labels.v2.yaml`
  - `health/health.v2.yaml`
  - `format/datetime.v1.yaml`
  - los tres de `queues/`
- **Salida:**
  ```
  real: []
  quitados 7
  sin catalogos: []
  ['veridicus_contracts/errors/.gitkeep', 'veridicus_contracts/ui/.gitkeep']
  ```
- **Los demás controles tampoco lo atrapan:**
  - El guion del paso 4 tiene el mismo defecto: `leidos` no queda vacío con un `.gitkeep` de 0 bytes.
  - `registry.build_registry` recorre lo que exista y salta en silencio lo que falta.
  - C7, C1 y C19 no referencian esos catálogos.
  - Resultado: la corrida completa daría código 0 sin el catálogo de errores ni el de rótulos.
- **Las pruebas no lo cubren:** «una lista sin un esquema de la tabla falla» quita directorios enteros (`analyzer/`, `cli/`, `vendor/`), nunca un archivo dentro de un directorio con más de uno.
- **Barrido de la clase:** el defecto está en `comparar_rueda`, en el guion (lectura por directorio) y en la parametrización de la prueba de faltantes.
- **Corrección sin tocar `pyproject.toml`:** para cada entrada de `sources`, exigir en la rueda cada archivo del árbol de origen que no sea de `fixtures/`. Añadir un control negativo que quite un solo catálogo, por ejemplo `errors/error-codes.v2.yaml`.

### F-02 · NARANJA · bitácora, «Rojo primero» · la premisa «solo puede fallar por módulo ausente» es falsa y el «falla por su regla» solo se afirma

- **Qué dice la bitácora:** que el rojo «solo puede fallar por módulo ausente», y que «en el verde se muestra» que cada control negativo falla por su regla. Esa segunda parte es prosa, no una salida.
- **La premisa no se sostiene:** corrí la suite con un esqueleto parcheado en memoria (`comparar_rueda=lambda n,t: []`, `tabla_de_rutas` vacía, `PREAMBULO=''`). Resultado: **14 failed, 1 passed**, todas por aserción y ninguna por importación:
  - `assert 0 == 1` en las de faltante y ruta prohibida;
  - `set() == {...}` en la de la tabla derivada;
  - `assert 0 != 0` con `llego` en la del socket.

  Comando: `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts python -c "...c.comparar_rueda=lambda n,t: []; c.tabla_de_rutas=...; c.PREAMBULO=''; pytest.main([...,'-p','no:cacheprovider'])"`.
- **Alcance de la exigencia:** el Testing Contract (PD-5) no exige rojo primero en la capa de herramientas, así que esto no llega a ROJO. Pero el plan de pruebas de la tarea solo admitía la salida por módulo ausente si de verdad no había otra.
- **Qué falta:** la bitácora debe traer un rojo con esqueleto de firma, con su salida, como en T18. Mi corrida muestra que las pruebas sí discriminan; falta que la evidencia sea del codificador.

### F-03 · AMARILLO · `check_package.py:257-262` · `uv build` del paso 1 corre con red

La tarea (paso 3) y security-design §4.13 («Sí, solo para instalar») limitan la red a la instalación. `construir` solo pasa `--offline` cuando lo piden, y `verificar` lo llama sin él. CA-3 demuestra que el build funciona con `--offline`, así que el paso 1 podría correr sin red. El guion del paso 4 sí corre sin red: `socket.socket` queda sustituido y la prueba lo demuestra.

### F-04 · AMARILLO · guion `:131` · el rótulo «C1: 21 fixtures» confunde

No hay *fixtures* con `contract: C1`; lo comprobé con `grep -rhoP "^contract:\s*\S+"`. Son los 21 de C7 validados a través de `console.v2.yaml#/components/schemas/ReviewSuggestion`, que hace `$ref` a `/veridicus/contracts/integrity/review-suggestion/v2`. Eso sí prueba la cadena C1 → C7 → C6 desde el paquete instalado, que es lo que pide F9.4 (BR12.3). Por eso la falta de un *fixture* propio de C1 no rompe lo que la tarea exige. Aun así, el mensaje debería decir «C1 (ReviewSuggestion, *fixtures* de C7)».

### F-05 · AMARILLO · bitácora, CA-4 · el aviso está mal descrito

El único aviso viene de `tests/test_runner.py::test_socket_bloqueado` (pytest-socket). La bitácora lo atribuye a «la documentación de capturas»: lo que cita es la línea de enlace a la documentación de pytest, no el aviso.

## Respuesta a los puntos del encargo

- **El rojo:** falta el rojo con esqueleto (F-02). Era posible y las pruebas discriminan, como muestra mi corrida.
- **La red:** coincide con V-PKG y con §4.16 para instalar. El guion corre sin red y el entorno está aislado. El *build* también podría ir sin red (F-03).
- **«Presente»:** sí esconde directorios mal empaquetados (F-01, ROJO).
- **Guardias de T18:** verdes (`fixture_coverage`, `ci_workflows`, `redos`, `loader_usage` y `package_map`; 140 pasadas).
- **La candidata del codificador:** no afecta a lo que la tarea exige (F-04).

## Tareas candidatas (defectos reales fuera de alcance)

- `registry.build_registry` salta en silencio los archivos que faltan. Un registro que compare contra un inventario esperado convertiría F-01 en un fallo también fuera de `check_package`. Toca `registry.py`, que está fuera del alcance de esta tarea.
- Un *fixture* propio de C1 (por ejemplo, una respuesta de la consola con `ReviewSuggestion`), como ya propuso el codificador.

```
VEREDICTO: NO-VERDE
ROJO|contracts/src/veridicus_contracts/tools/check_package.py:202-206 y guion :90-94|Un directorio con solo .gitkeep cuenta como presente: faltan 7 catálogos y esquemas y no falla
NARANJA|docs/loop/bitacoras/U01-T21.md (Rojo primero)|Rojo solo por módulo ausente cuando era posible uno con esqueleto; «falla por su regla» solo se afirma
AMARILLO|contracts/src/veridicus_contracts/tools/check_package.py:257-262|uv build del paso 1 corre con red; la red debía limitarse a instalar
AMARILLO|contracts/src/veridicus_contracts/tools/check_package.py:131|El rótulo «C1: 21 fixtures» son fixtures de C7 vía ReviewSuggestion
AMARILLO|docs/loop/bitacoras/U01-T21.md (CA-4)|El aviso de la suite viene de pytest-socket y está mal descrito
INFORME: docs/loop/revisiones/U01-T21/ronda-1.md
```
