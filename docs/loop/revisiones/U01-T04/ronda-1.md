# Ronda 1 — U01-T04

VEREDICTO: VERDE

La tarea queda en VERDE: corrí yo mismo CA-1 a CA-7 y todos pasan. No hay ningún hallazgo ROJO ni NARANJA; quedan tres AMARILLO que no bloquean. El worktree sigue limpio después de todas las corridas.

Tarea: `sha256sum` da `b66646d2…7c046`, que coincide con el valor del encargo. El diff `feat/b1-contratos...tarea/U01-T04` toca 6 archivos, todos dentro del alcance.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | La copia de C6 entró solo por el commit del humano | `git -C /workspace/.worktrees/U01-T04 log --format="%h %an %s" feat/b1-contratos..HEAD -- contracts/analyzer/v1/entrada.schema.json contracts/analyzer/v1/salida.schema.json contracts/analyzer/v1/SHA256SUMS` | pasa: una sola línea, `0597012`. `git show --stat 0597012` muestra solo los 3 archivos y `95b52de` (codificador) no los toca |
| 2 | Las huellas coinciden con `SHA256SUMS`, con el PR y con el origen | `sha256sum` sobre la copia y sobre `/insumos/app/contratos/analizador/v1/`, y lectura de `SHA256SUMS` | pasa: `28606016…c41a8` (entrada) y `e1528b7d…bedeaf` (salida), iguales en la copia, en `SHA256SUMS` (2 líneas), en el origen y en las huellas que anotó el humano |
| 3 | C6 y F7 en verde | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T04/contracts pytest tests/contracts/test_analyzer_copy.py tests/guards/test_autonomia_05.py -m c6 --no-cov -v` | pasa: `29 passed, 10 deselected`, incluida `test_f7_detecta_e18_una_copia_con_un_byte_cambiado` |
| 4 | F7 no bloquea una sesión sana | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T04/contracts pytest tests/test_runner.py --no-cov` | pasa: `2 passed, 1 warning` (el aviso viene del socket bloqueado a propósito) |
| 5 | El mapa de la rueda no cambia | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T04/contracts pytest tests/test_package_map.py --no-cov` | pasa: `7 passed` |
| 6 | Tipos y *lint* | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T04/contracts mypy --strict src` y `… ruff check .` | pasa: `Success: no issues found in 7 source files` y `All checks passed!` |
| 7 | La CI sigue en verde | `bash /workspace/.worktrees/U01-T04/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T04` | pasa: `0 apariciones`, código 0 |

## Comprobaciones pedidas por el orquestador

- **F7 aborta la sesión de verdad.** Hice copias de `tests/`, `analyzer/` y `pyproject.toml` en `/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/f7/`. Las corrí con `/workspace/.worktrees/U01-T04/contracts/.venv/bin/python -m pytest -p no:cacheprovider --rootdir=<copia> -c <copia>/pyproject.toml <copia>/tests/test_runner.py --no-cov`.
  - `linea_de_mas`: código 3, `…repositorio principal: SHA256SUMS debe tener exactamente dos líneas, una por esquema`.
  - `linea_de_menos`: código 3, el mismo mensaje más `salida.schema.json: su SHA-256 no coincide`.
  - `linea_duplicada`: código 3.
  - `byte`: código 3, `salida.schema.json: su SHA-256 no coincide con SHA256SUMS`. También aborta si la corrida apunta a `tests/guards/test_autonomia_05.py -m c6`, así que el conftest se carga también desde un subdirectorio.
  - `version` (`const` cambiado a `1.0.1` y huella recalculada para que solo falle la versión): código 3, `entrada.schema.json: falta contrato: { const: "1.0.0" }`.
  - Control `sano`: la sesión pasa de `sessionstart` y corre las pruebas. El único fallo es `test_raiz_de_contracts`, porque no copié `src/`; no viene de F7.
  - Todos los mensajes empiezan por el texto exacto de F7 paso 4.
- **Rojo primero (rojo comprobado).** Puse el `conftest.py` de la rama base en `/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/f7/rojo`. La prueba E18 falla con `Failed: F7 ausente: conftest.check_c6_copy(carpeta) -> list[str] (T04)`, igual que en la bitácora. El par falla-pasa es real.
- **E18 no escribe en `analyzer/v1/`.** `test_autonomia_05.py:132-158` solo escribe en `tmp_path / "v1"`; `check_c6_copy` solo lee. Después de todas las corridas, `git status --porcelain --ignored contracts/analyzer` sale vacío.
- **`helpers` usa la regla del registro (F-05 de T03).** `_uri_natural` ya no repite la regla de `urljoin`: llama a `registry._uri_de`. Para los `$id` relativos de C6 (`veridicus/contracts/analyzer/v1/…`) da la misma URI que registra `build_registry`.
- **No se toca nada de T03 salvo `conftest.py` y `helpers.py`.** `git diff --name-status` solo muestra `A` en los 3 archivos de C6 y en la bitácora, y `M` en `contracts/tests/conftest.py` y `contracts/tests/helpers.py`.
- **Datos del piloto.** No hay ninguno. Lo único que entra de `/insumos` es el contrato común, y `project.md` › Decided lo permite.

## Hallazgos

### F-01 · AMARILLO · contracts/tests/conftest.py:34 · F7 tolera una línea vacía de más y los finales CRLF
`lineas = [linea for linea in texto.splitlines() if linea]` descarta las líneas vacías, y `splitlines()` acepta `\r\n`. Probé dos variantes en el scratchpad, `linea_vacia_extra` (`SHA256SUMS` con una tercera línea vacía) y `crlf`: las dos pasan F7 sin abortar. F7 paso 1 y §4.19 dicen «exactamente dos líneas».

No bloquea por tres razones:
- La garantía declarada («nadie cambió la copia sin cambiar sus huellas») se cumple igual.
- La prueba aprobada de T03 (`test_analyzer_copy.py:79`) lee el archivo de la misma forma.
- El archivo real tiene dos líneas y un salto final.

Si se quiere la lectura literal, se puede exigir `texto == l1 + "\n" + l2 + "\n"`.

### F-02 · AMARILLO · contracts/tests/helpers.py:34,139 · Uso de `registry._uri_de`, que es privada, con `en_vendor=False` fijo
La tarea lo permite («`registry._uri_de` o la pública que exista»), así que no es desborde. Aun así deja dos problemas:
- Las pruebas quedan atadas a una firma privada: si alguien cambia los parámetros de `_uri_de`, ni mypy ni ruff avisan del contrato roto con las pruebas.
- `en_vendor=False` va fijo, y `LoadError` se convierte en silencio con `None`. Un esquema de `vendor/` (con `$id` absoluto) que pase por `validador_de` caería sin aviso a la URI `_documentos/…`. Hoy ninguna llamada a `validador_de` apunta a `vendor/`: lo comprobé con grep sobre `tests/`.

Recomiendo una función pública en `registry.py`, por ejemplo `uri_for(archivo, contenido) -> str`, que deduzca `en_vendor` de la ruta. `src/` está fuera del alcance de T04, así que va como tarea candidata.

### F-03 · AMARILLO · docs/loop/bitacoras/U01-T04.md · La bitácora se aparta en dos puntos de la tarea
- La corrida en rojo aparece como `uv run --directory …`, sin el `--frozen --offline` de CA-3. `uv.lock` no cambió en el diff, así que no hay efecto.
- El Plan de pruebas pedía una F7 «que recibe los bytes de los dos esquemas y el texto de `SHA256SUMS`», y E18 «en memoria». Se usó `check_c6_copy(carpeta)` sobre `tmp_path`, que es la interfaz que fijó T03 y la que permiten las Notas, pero la bitácora no explica la elección, como pedía la Nota 3 («si no, explícalo en la bitácora»).

## Tareas candidatas (defectos reales fuera de alcance)
- Publicar en `veridicus_contracts.registry` una función `uri_for(archivo, contenido)` (o similar) que deduzca `en_vendor` de la ruta, y hacer que `tests/helpers.py` la use en lugar de `_uri_de` (F-02).
- Si el humano quiere la lectura estricta de «exactamente dos líneas», que F7 y `test_sha256sums_tiene_dos_lineas_y_coincide_con_los_bytes` rechacen las líneas vacías y los CRLF (F-01).

```
VEREDICTO: VERDE
AMARILLO|contracts/tests/conftest.py:34|F7 tolera una línea vacía de más y los finales CRLF en SHA256SUMS
AMARILLO|contracts/tests/helpers.py:34|Uso de registry._uri_de, que es privada, con en_vendor=False fijo; conviene una función pública
AMARILLO|docs/loop/bitacoras/U01-T04.md|El rojo se corrió sin --frozen --offline y no se explica check_c6_copy(carpeta) frente a la función sobre bytes
INFORME: docs/loop/revisiones/U01-T04/ronda-1.md
```
