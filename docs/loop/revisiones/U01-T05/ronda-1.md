# Ronda 1 — U01-T05

VEREDICTO: VERDE

Hash de la tarea comprobado: `sha256sum` da `9fe18bbd…b060`, igual al del despacho. La rama `tarea/U01-T05` está en `76c713d`. Al terminar, `git status --short` sale vacío: solo quedan cachés ignoradas.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Los mensajes de cola aceptan o rechazan sus *fixtures* | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T05/contracts pytest tests/contracts/test_queue_messages.py --no-cov -v` | pasa: 18 passed, incluidos `test_effective_config_de_c2_cumple_c18` y E1, E2, E3, BR2.3 y NFRD-U1-07 |
| CA-2 | Solo contratos y no se entrega C4 | `git -C /workspace/.worktrees/U01-T05 diff --name-only feat/b1-contratos...HEAD` | pasa: 9 archivos, todos autorizados por la tarea, E-5, F-07 o la ampliación. `ls contracts/queues` no muestra `indexing.v1.yaml` (ver Y-03) |
| CA-3 | El mapa de la rueda sigue igual | `timeout 120 uv run … pytest tests/test_package_map.py --no-cov -q` | pasa: 7 passed |
| CA-4 | Tipos y *lint* limpios | `uv run … mypy --strict src` y `uv run … ruff check .` | pasa: `Success: no issues found in 7 source files` y `All checks passed!` |
| CA-5 | La comprobación de no aplicar al clúster sigue en verde | `bash /workspace/.worktrees/U01-T05/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T05` | pasa: `0 apariciones`, código 0 |
| Ampliación 1 | Pruebas del registro | `timeout 60 uv run … pytest tests/test_registry.py --cov-fail-under=0 -q` | pasa: 27 passed |
| Ampliación 2 | `registry.py` al 100 % | `uv run … coverage report --include=src/veridicus_contracts/registry.py --fail-under=100` | pasa: 60 sentencias y 28 ramas, sin nada sin cubrir: 100 % |

## Comprobaciones adicionales del encargo

- **Sin retrocesos en las suites vecinas.** Corrí registry, validators, loaders, canonical, runner, package_map, analyzer_copy, tools y queue_messages: 137 passed.
- **Qué registra el registro.** `build_registry()` del paquete registra 13 URI: los meta-esquemas de vendor, OpenAPI y AsyncAPI, `entrada` y `salida` de C6, y C18. Ningún AsyncAPI ni *fixture* entra en el registro.
- **Casos adversos en el scratchpad** (`/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/reg` y `/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/reg2`):
  - Un *fixture* con `$schema` y `$id` que repite una URI: no se carga, y no da URI repetida.
  - Un AsyncAPI con `$id` y sin `$schema`: se salta.
  - Un `.yml` con los dos campos: se registra.
  - Un directorio `x/y/tests/z/`: se salta.
- **Reglas de T02b en YAML.** Todas se mantienen:
  - URI repetida entre `.yaml` y `.yml`: rechazada, nombrando los dos archivos.
  - `$id` vacío, con fragmento o con consulta: rechazado.
  - `$id` que sale de la base con `..`: rechazado.
  - `$id` absoluto: rechazado fuera de `vendor/`, aceptado dentro.
  - `$id` que no es texto, `$schema` que no es texto y `.schema.json` sin `$id`: rechazados.
- **C2 → C18.** `runs.v2.yaml:79` usa `$ref: '/veridicus/contracts/profiles/effective-config.v1'` y no queda `components/schemas` (grep `schemas:` sin resultados). Altero en memoria el *fixture* válido y C2 rechaza cada cambio a través del `$ref`: una clave de más en `effective_config`, un `api_key` dentro del perfil, `limits` ausente, `attempt: 0` y un `code` con texto libre en `RunFailed`. Así compruebo que el `$ref` de verdad valida.
- **C3 y AUTONOMIA-05.** `results.v2.yaml:64` usa `$ref: '/veridicus/contracts/analyzer/v1/salida'`. Un grep de `cita_a|cita_b|hallazgos|observaciones|hecho` solo encuentra la palabra «hallazgos» en un `summary`: nada redefine el hallazgo.
- **AUTONOMIA-04.** Los tres contratos declaran `veridicus-redis:6379` con protocolo redis, sin URL externa. `pytest tests/guards/test_autonomia_04.py --no-cov -k servers` da c2, c3 y c5 PASSED. c1, c16, c21 y voz-interna fallan por contrato ausente, y esos contratos son de otras tareas.
- **Entradas fallidas.** `RunFailed`, `ResultFailed` y `AudioFailed` llevan `additionalProperties: false`, solo `message_id`, el ID de la corrida o del turno, `attempt ≥ 1` y `code`, con un patrón sin espacios.
- **C5.** La versión 1.2.0 y `^1\.` coinciden con la revisión 4 del contract-summary y con los *fixtures* de T03. `audio_base64` lleva `x-veridicus-limit: audio_base64_max_chars`, y `x-veridicus-priority: SHOULD` está presente.
- **Archivos intocables.** `git diff --stat` sobre `contracts/analyzer`, `contracts/queues/fixtures`, `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py` y `helpers.py` sale vacío. No se tocan umbrales.
- **Rojo primero.** La bitácora trae el rojo de CA-1 («contrato ausente») y el rojo de las pruebas del registro (4 failed antes del cambio). El rojo de las pruebas de cola es de T03, y la bitácora lo reprodujo.
- **Datos.** No hay datos del piloto ni datos reales en el diff ni en la bitácora; solo IDs y esquemas.

## Hallazgos

### Y-01 · AMARILLO · contracts/src/veridicus_contracts/registry.py:85-88 · Un archivo que no es esquema ahora puede tumbar todo el registro

Antes, el registro solo abría `*.schema.json`. Ahora `load_file` lee todo `.yaml`, `.yml` y `.json` antes de decidir si es esquema. En el scratchpad, tres archivos que no son esquemas hacen fallar `build_registry` entero:
- `fecha: 2026-11-23` sin comillas;
- un YAML de plantilla `{{ .Values.x }}`;
- un JSON con `NaN`.

Además, el error de la fecha no dice qué archivo lo causó: `fecha sin comillas en $.fecha`. Fallar en voz alta es coherente con D5, pero ninguna prueba fija esta decisión. Sugiero dos cosas: poner el nombre del archivo en el `LoadError` y añadir una prueba que fije el comportamiento elegido. No bloquea: hoy ningún archivo del paquete lo dispara.

### Y-02 · AMARILLO · contracts/tests/contracts/test_queue_messages.py:3 · Docstring editado fuera de las líneas que permite F-07

F-07 permite tocar las líneas 9 y 120. La línea 3 también cambió: «Rojo hasta T05… (o ajustar aquí en el mismo PR)» pasó a «Verde desde T05. Supuestos que T05 cumple». No cambia ninguna aserción, el propio docstring invitaba a ajustarlo, y si no se tocara quedaría falso. Que el orquestador lo ratifique.

### Y-03 · AMARILLO · Tarea, CA-2 · El «Esperado» de CA-2 quedó desactualizado

CA-2 espera solo `contracts/queues/` y la bitácora. El diff también lleva otros archivos, todos autorizados en otras secciones de la tarea:
- `profiles/effective-config.v1.yaml` (E-5);
- `registry.py` y `test_registry.py` (la ampliación);
- dos docstrings (F-07).

Conviene corregir el texto de CA-2 en la tarea.

### Y-04 · AMARILLO · docs/loop/bitacoras/U01-T05.md:78-82 · La bitácora no trae la evidencia del criterio de cobertura corregido

La bitácora registra el comando anterior (`--cov-fail-under=100` sobre todo el paquete) y lo declara bloqueado. No trae la salida de `coverage report --include=… --fail-under=100`, ni el hash vigente de la tarea (cita `8dacb80…`). Yo lo corrí sobre `76c713d` y da 100 %. Que el codificador la añada en su próxima pasada.

## Tareas candidatas (defectos reales fuera de alcance)

- **C3, revisión 4 del contract-summary (líneas 1351-1363).** Pide la versión 2.1.0 con el mensaje `RunStarted` (`kind: run_started`, `run_id`, `attempt`, `started_at`) y `kind: run_result` opcional en `RunResult` (FD-U4-02). `results.v2.yaml` se entregó en la 2.0.0 sin ellos. La tarea cita la «revisión 3» y el paso 7 no los nombra, así que no es un desborde ni un fallo de T05. Hace falta una tarea con sus *fixtures* antes de que U4 los consuma.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/registry.py:85-88|Un archivo que no es esquema puede tumbar todo el registro y el error no nombra el archivo
AMARILLO|contracts/tests/contracts/test_queue_messages.py:3|Docstring editado fuera de las líneas que permite F-07
AMARILLO|Tarea CA-2|El Esperado de CA-2 no cuenta E-5, la ampliación ni F-07
AMARILLO|docs/loop/bitacoras/U01-T05.md:78-82|Falta la evidencia del criterio de cobertura corregido
INFORME: docs/loop/revisiones/U01-T05/ronda-1.md
```
