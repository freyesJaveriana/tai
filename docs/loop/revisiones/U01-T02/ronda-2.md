# Ronda 2 — U01-T02

VEREDICTO: VERDE

Corrí yo los 7 criterios sobre `830d729` y todos pasan. Los tres NARANJA de la ronda 1 quedaron cerrados, y comprobé F-01 y F-03 corriéndolos, no leyendo el código. Al terminar, el worktree está limpio: `git -C /workspace/.worktrees/U01-T02 status --short` no da salida y solo quedan `__pycache__` ignorados.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | Carga, registro, JCS | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest tests/test_loaders.py tests/test_registry.py tests/test_canonical.py --no-cov -q` | pasa: 30 passed, 0,09 s |
| 2 | Validación estándar | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest tests/test_validators.py --no-cov -v` | pasa: 37 passed. Son 10 funciones con parametrización: las 7 del plan siguen y se suman las regresiones de F-01, F-02 y F-03 |
| 3 | Suite y 100 % de ramas | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest` y `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts coverage report --include="src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100` | pasa: 76 passed en 3,73 s, 98,22 % en total; canonical y registry al 100 % (registry: 20 ramas, 0 parciales) |
| 4 | Tipos y *lint* | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts mypy --strict src` y `… ruff check .` | pasa: `Success: no issues found in 6 source files` y `All checks passed!` |
| 5 | `vendor/` en el mapa y en la rueda | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T02/contracts pytest tests/test_package_map.py --no-cov -q` | pasa: 7 passed |
| 6 | Un solo `YAML(` | `grep -rn "YAML(" /workspace/.worktrees/U01-T02/contracts/src` | pasa: solo aparece en `loaders.py:22` |
| 7 | Sin aplicaciones al clúster | `bash /workspace/.worktrees/U01-T02/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T02` | pasa: `0 apariciones` |

Además: `uv lock --check --offline --directory /workspace/.worktrees/U01-T02/contracts` da `Resolved 79 packages`. En la ronda 1 el hook no me dejó correrlo; ahora queda comprobado.

## Cierre de los hallazgos de la ronda 1, comprobado corriendo

- **F-01, cerrado.** Lo corrí en un entorno aislado sin el grupo dev: `uv run --frozen --offline --no-dev --isolated --directory /workspace/.worktrees/U01-T02/contracts python -I -c "…"`. Se instalaron 21 paquetes y `find_spec('openapi_spec_validator')` da `False`. El import de `validators` funciona, y `validate_json_schema`, `validate_instance` (uuid) y `validate_asyncapi` responden bien. `validate_openapi` lanza `ValidationFailure: validate_openapi necesita openapi-spec-validator (dependencia de desarrollo, D3)`.
  - Instalar la rueda construida no fue posible: falta `rpds-py` en la caché sin red. La rueda sí se construyó en el scratchpad (`/tmp/claude-1000/-workspace/5399d6a8-973e-4041-af9d-c81b243406a0/scratchpad/r2/dist/veridicus_contracts-0.1.0-py3-none-any.whl`), y el entorno aislado prueba lo mismo: el módulo no necesita ninguna dependencia de desarrollo para importarse.
- **F-02, cerrado.** La misma reproducción de la ronda 1, con `{'properties': ['a'], 'allOf': 5}`, ahora da `ValidationFailure: esquema no válido: $.properties: ['a'] is not of type 'object'; $.allOf: 5 is not of type 'array'`. Las parametrizaciones de `test_un_esquema_mal_formado…`, `test_un_asyncapi_mal_formado…` y `test_un_sha256sums_mal_formado…` pasan.
- **F-03, cerrado.** Probé un AsyncAPI con un canal que referencia `components/messages/alias`, y ese alias a su vez es un `$ref` hacia `real`. `validate_asyncapi` lo acepta y `extract_message_payloads` devuelve `{'components/messages/real': {'type': 'object'}}`. Para escribir `$ref` dentro de `python -c` usé `'\x24ref'`, porque las comillas dobles del shell lo expandían.

## Puntos que pidió el orquestador

- **(a) `UserWarning` de pytest-socket: no hay riesgo de red ni de prueba frágil.**
  - Leí `urllib3/util/connection.py:114-137`. `_has_ipv6("::1")` solo hace `bind` en el loopback, nunca `connect`, y lo envuelve en `except Exception`. `SocketBlockedError` cae en ese `except`, igual que un `UserWarning` promovido con `-W error`.
  - El único efecto es que `HAS_IPV6=False` durante la sesión, y eso no afecta a ninguna prueba.
  - El aviso aparece en la prueba que importa urllib3 primero. Eso depende del orden, pero no del resultado.
- **(b) No hay desborde.** El barrido extra solo toca los cuatro módulos del alcance:
  - `verify_vendor`/`_leer_sumas`: línea mal formada, `/`, `..`, texto que no es UTF-8.
  - `build_registry`: `$schema` que no es texto.
  - `load_file`: archivo que no es UTF-8.
  - Cada caso tiene su prueba, y la bitácora registra el rojo previo.
- **(c) La edición con `python -c` está en el diff y es correcta.**
  - La reescritura de `verify_vendor` aparece en `git diff ac0901c 830d729`, en `validators.py:71-104`.
  - Es correcta: rechaza las líneas sin separador doble, sin nombre o con `/` o `\`. `.` y `..` acaban en `OSError`, que sale como `ValidationFailure`. Los archivos sobrantes y los faltantes se siguen detectando.
  - No dejó nada fuera del worktree. `git -C /workspace status --short` solo muestra el fragmento de auditoría que ya estaba modificado al empezar esta revisión.
  - Es un incumplimiento de proceso que el propio codificador declaró. Lo dejo como A-02; no bloquea.
- **(d) No se revierte nada de la rama del Bolt.**
  - `feat/b1-contratos` y `origin/feat/b1-contratos` apuntan al mismo commit, `9e80aa1`.
  - `git diff --stat` con dos puntos y con tres puntos da lo mismo: 28 archivos, 12 023 líneas añadidas y 1 borrada.
  - `--diff-filter=DM` solo encuentra `pyproject.toml`, `test_package_map.py` y `uv.lock`, que son los cambios previstos, y el borrado de `vendor/.gitkeep`.

## Hallazgos

Ninguno ROJO ni NARANJA.

## Avisos (AMARILLO)

- **A-01:** `test_el_modulo_se_importa_sin_openapi_spec_validator` vuelve a importar `veridicus_contracts.validators`. `monkeypatch` restaura `sys.modules`, pero no el atributo `validators` del paquete padre, que queda apuntando al módulo reimportado. Si una prueba posterior escribe `import veridicus_contracts.validators as v`, recibiría ese módulo, con otra clase `ValidationFailure`. Hoy ninguna prueba lo hace. Conviene restaurar también el atributo con `monkeypatch.setattr`.
- **A-02:** el codificador editó un archivo con `python -c` (regla 10 de su bitácora). Revisé el resultado y es correcto; queda solo como aviso de proceso.
- **A-03:** la tabla de huellas «al descargarse» se añadió después y es idéntica a `SHA256SUMS`. No es evidencia independiente de que coincidan con la fuente. Sin red, confirmé que el meta-esquema 2020-12 coincide en contenido con el de `jsonschema_specifications`. Los vocabularios solo difieren en el bloque `$vocabulary`.
- **A-04:** `validate_instance` ahora valida el esquema en modo estricto y reconstruye el registro en cada llamada. Es correcto según BR1.9, pero cuesta más si T03 en adelante la usan en bucles.
- **A-05:** el criterio CA-2 de la tarea dice «7 pruebas». Ahora son 37 por las regresiones pedidas. Podría actualizarse el texto de la tarea.

## Tareas candidatas (defectos reales fuera de alcance)

- Ninguna.

```
VEREDICTO: VERDE
INFORME: docs/loop/revisiones/U01-T02/ronda-2.md
```
