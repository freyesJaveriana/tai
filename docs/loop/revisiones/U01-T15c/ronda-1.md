# Ronda 1, U01-T15c

VEREDICTO: VERDE

Corrí yo mismo los seis criterios (CA-1 a CA-6) y la prueba del rojo, y todos pasan. Quedan tres hallazgos AMARILLO y ninguno ROJO ni NARANJA.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Lecturas de vuelta y validación real | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15c/contracts pytest tests/contracts/test_correcciones_t15c.py --no-cov -v` | pasa: 7 passed in 0.49s |
| 2 | Suite completa | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T15c/contracts pytest tests --no-cov -q -rs` | pasa: 2002 passed, 1 warning (la ya conocida de `test_socket_bloqueado`), 0 omitidos |
| 3 | Catálogo de límites y su diff | `... pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q` y `git -C ... diff feat/b1-contratos...HEAD -- contracts/limits.v1.yaml` | pasa: 162 passed. El diff es una sola línea: `run_message_max_bytes` pasa a `used_in: [C2]` |
| 4 | Archivos permitidos | `git -C /workspace/.worktrees/U01-T15c diff --name-only feat/b1-contratos...HEAD` | pasa: `limits.v1.yaml`, `runs.v2.yaml`, `test_correcciones_t15c.py` y la bitácora |
| 5 | Mapa del paquete | `... pytest tests/test_package_map.py --no-cov -q` | pasa: 8 passed |
| 6 | Tipos, lint y CI | `... mypy --strict src` · `... ruff check .` · `bash /workspace/.worktrees/U01-T15c/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T15c` | pasa: `Success: no issues found in 18 source files`, `All checks passed!` y `0 apariciones` |

## Puntos del encargo
- **Rama de refinamiento.** El diff de `runs.v2.yaml` (líneas 86 a 98) solo añade el camino `transcripcion` → `turnos` → `items` → `texto`, con `maxLength: 20000` y `x-veridicus-limit: turn_max_chars`. No añade propiedades nuevas, ni `required`, ni `additionalProperties`. El `$ref` a `/veridicus/contracts/analyzer/v1/entrada` es la primera rama y no cambió, y la `description` se conserva igual.
- **C6 sin cambios.** `git diff --stat feat/b1-contratos...HEAD -- contracts/analyzer` no devuelve nada. En C6, `texto` sigue siendo `{"type": "string"}`, sin tope propio.
- **`turn_max_chars` en la base.** Confirmo lo que dice el codificador: `git show feat/b1-contratos:contracts/limits.v1.yaml` ya trae `turn_max_chars ... used_in: [C1, C2, C5]`.
- **El 20001 se rechaza por la regla.** Hice una sonda con el validador del paquete y el registro de esquemas, sobre la fixture `run.valid.yaml`:
  - 20000 caracteres: ningún error.
  - 20001 caracteres: un solo error, de tipo `maxLength`, en la ruta `['entrada','transcripcion','turnos',1,'texto']`.
  - 20001 caracteres no ASCII en el turno 0 (`ENT`): también `maxLength`. El tope vale para todos los turnos.
- **Rojo primero y literal.**
  - El commit del rojo (`b0223d9`) solo añade el archivo de pruebas frente a la base (`git diff --stat feat/b1-contratos b0223d9`), y ese archivo no cambia después (`git diff --stat b0223d9 HEAD` no lo nombra).
  - Repetí el rojo en memoria contra los contratos de la base, con las mismas funciones `comprobar_*`. Las tres fallan por su regla: `entrada trae ['$ref', 'description']`, `RunRequested sin x-veridicus-max-bytes (None)` y `run_message_max_bytes: used_in [] distinto de ['C2']`.
- **Sitio de la marca del mensaje.** C2 no tenía ninguna extensión `x-veridicus-*`. Por eso la marca va en el `payload`, como la tarea prevé para ese caso, y la bitácora lo anota. Esto concuerda con C5, que marca sus topes dentro del `payload`. C1 y C21, en cambio, la ponen en `requestBody` o en el tipo de contenido, no dentro del esquema. Lo dejo como observación para T14 (ver tarea candidata), no como defecto.
- **Edición solo con Edit o Write.** No pude comprobarlo: la auditoría del intent no registra las escrituras del worktree. Tampoco veo nada en contra: el diff es limpio y sin rastros de `sed`.
- **Worktree limpio.** `git -C ... status --porcelain` no devuelve nada al terminar.

## Hallazgos
### F-01 · AMARILLO · `test_correcciones_t15c.py:107-120, 154-160` · Dos controles negativos dan rojo por `KeyError`
En el rojo, los dos controles negativos de C2 fallan con `KeyError: 'allOf'` y `KeyError: 'x-veridicus-max-bytes'`. Es decir, fallan por una precondición y no por la regla que prueban. La tarea pide que «cada rojo falle por la regla». No bloquea, por tres razones: las pruebas de la regla (forma, validación real, tope y `used_in`) sí fallaron por la regla; un control negativo no puede dar un rojo con sentido antes de que exista lo que muta; y el codificador lo declaró en la bitácora.

### F-02 · AMARILLO · `docs/loop/bitacoras/U01-T15c.md:115` · El rojo no está completo
Faltan las tres líneas iniciales de `uv`, aunque la bitácora lo declara. La tarea pedía la salida «literal y completa».

### F-03 · AMARILLO · bitácora · El acuse se escribió después del rojo
El acuse de lectura se completó después de escribir las pruebas y correr el rojo, y el propio codificador lo reconoce. No cambió ninguna decisión, pero rompe el orden del bucle.

## Tareas candidatas (defectos reales fuera de alcance)
- Cuando T14 compare los valores de `x-veridicus-max-bytes` con C25, conviene decidir en qué nivel se leen en los AsyncAPI: en el Message Object, análogo al `requestBody` de C1, o en el `payload`, como queda ahora en C2. Así la guardia tendrá un único criterio para todos los contratos.

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/contracts/test_correcciones_t15c.py:107-160|Controles negativos con rojo por KeyError (precondición) y no por la regla
AMARILLO|docs/loop/bitacoras/U01-T15c.md:115|El rojo omite las tres líneas iniciales de uv aunque se pedía literal y completo
AMARILLO|docs/loop/bitacoras/U01-T15c.md:9|Acuse de lectura completado después del rojo
INFORME: docs/loop/revisiones/U01-T15c/ronda-1.md
```
