# Ronda 1 — U01-T18d

VEREDICTO: NO-VERDE

El cambio de código funciona: la suite pasa en 27,8 s y respeta el tope de 60 s. El veredicto es NO-VERDE por un solo NARANJA, la bitácora: el rojo no está pegado literal y completo como exige la tarea.

Revisé la rama `tarea/U01-T18d` en 5121ba0 contra `feat/b1-contratos` en 69e5d4b. El diff toca solo `contracts/src/veridicus_contracts/loaders.py` y la bitácora. El worktree quedó limpio al terminar (`git status --porcelain` vacío).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| rojo | CA-1 sobre la base | `timeout 60 uv run --frozen --offline --directory /workspace/contracts pytest -q -p no:cacheprovider` (carga 2.04 1.91 1.41) | código 124, cortado al 8 %: el rojo se confirma |
| 1 | V-SUITE | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18d/contracts pytest -q -p no:cacheprovider` (carga 1.13 1.67 1.22) | pasa: `2533 passed, 1 warning in 27.80s`, cobertura 99.75 % |
| 1 | V-SUITE, 2.ª corrida | `timeout 60 uv run … pytest -q --cov-report=` (carga 2.67 2.10 1.51) | pasa: `2533 passed, 1 warning in 27.79s` |
| 2 | pruebas recogidas | `uv run … pytest --collect-only -q --no-cov -p no:cacheprovider`, en el worktree y en `/workspace/contracts` | 2533 en ambas: pasa |
| 3 | guardias al 100 % de ramas | `timeout 300 uv run … pytest tests/checks -q -p no:cacheprovider --cov-report=`, luego `coverage report --include=*/veridicus_contracts/checks/* --fail-under=100` | `1886 passed in 19.85s`; TOTAL 2724/0, 1316/0, 100 %, código 0: pasa |
| 4 | nada se aflojó | `git -C … diff --stat feat/b1-contratos...HEAD -- contracts/pyproject.toml contracts/uv.lock contracts/tests` y `git grep -c -E "max_examples\|deadline=\|skip\|xfail"` en HEAD y en la base | diff vacío; mismos conteos por archivo (1, 2, 11, 1, 4, 1, total 20 líneas): pasa |
| 5 | tipos | `uv run … mypy --strict src` | `Success: no issues found in 41 source files` |
| 5 | lint | `uv run … ruff check .` | `All checks passed!` |
| 5 | clúster | `bash /workspace/.worktrees/U01-T18d/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18d` | `0 apariciones`, código 0 |

La carga se mantuvo baja (≤ 2,7 en 8 núcleos). No hizo falta repetir CA-1 por corte; la segunda corrida es solo para confirmar el tiempo.

**Sondas propias sobre `loaders`** (`uv run … python -c "exec('…')"`):
- **Copia profunda:** mutar el resultado en un nivel anidado (asignar, `append`, añadir claves) no cambia la lectura siguiente, ni en YAML ni en JSON. Dos llamadas dan objetos distintos (`is not` → True).
- **Las excepciones no se cachean:** los 6 textos inválidos (YAML con clave duplicada, fecha sin comillas o etiqueta `!!python`; JSON con clave duplicada, `NaN` o mal formado) fallan dos veces cada uno con el mismo mensaje. `cache_info` lo confirma: `currsize=1` en cada caché.
- **Mismo comportamiento:** `.nan`, `-.inf`, `-0.0`, `1e400` y `\ud800` salen iguales que en el análisis base. Los mensajes de error no incluyen la ruta, así que cachear por texto no cambia qué ruta se informa. `load_file` sigue informando el nombre del archivo igual que antes. Las firmas públicas no cambian.

## Hallazgos

### F-01 · NARANJA · docs/loop/bitacoras/U01-T18d.md:21-25, 114-139 · Rojo y evidencias condensados, contra el Plan de pruebas de la tarea
La tarea pide pegar la salida de CA-1 sobre la base «literal y completa» y dice «no la condenses». La bitácora no lo cumple en estos puntos:
- **El rojo no es CA-1.** El comando pegado no lleva `timeout 60`, sustituye `addopts` y añade `--durations` y `--junitxml`. De su salida solo aparece la última línea, `2533 passed, 1 warning in 346.53s`.
- **El verde de CA-1 está recortado** con `...`.
- **CA-3 y CA-5 están reducidos** a una línea cada uno.
- **El diff de CA-4 nunca se pegó**, aunque la bitácora dice «se pega tras el commit».
- **El conteo de CA-4 es incorrecto:** la bitácora dice «22 líneas» y son 20. Lo conté con `git grep -c` en HEAD y en la base.

Mis corridas confirman todo lo que afirma el codificador. El defecto es de evidencia, no de código. No es ROJO porque la tarea no exige escribir una prueba primero: su rojo es una medición.

### F-02 · AMARILLO · contracts/src/veridicus_contracts/loaders.py:50, 83 · Caché sin límite en funciones públicas
`load_yaml_text` y `load_json_text` son públicas. Con `@cache` sin `maxsize`, cada texto que reciben queda guardado mientras viva el proceso.

Hoy no hay riesgo: el único consumidor es `load_file`, que solo lee archivos del paquete (`registry`, `limits`, `profiles`, `checks/*`) y *fixtures*. Ningún servicio importa `loaders` y `validators.py` no lo usa.

El riesgo futuro: si un servicio las usara con datos de ejecución, por ejemplo mensajes de cola con transcripciones, la memoria crecería sin tope y el testimonio quedaría retenido en el proceso. Recomiendo una de dos: advertirlo en el docstring público, o cachear solo dentro de `load_file` o con `maxsize`.

Un texto con el mismo contenido y otra ruta no causa problema: comparte el análisis y recibe su propia copia.

### F-03 · AMARILLO · loaders.py:45-47 · La copia por `json.dumps`/`json.loads` cambia dos bordes
- **Alias YAML:** en la base, `a: &r [1, 2]` con `b: *r` dejaba un objeto compartido; ahora salen dos copias. La sonda dio `alias base comparte: True  nuevo comparte: False`. Una entrada con alias anidados («billion laughs») ahora también se expande en memoria, no solo en tiempo. Los contratos no usan alias (el grep de anclas en `*.yaml` no encontró nada), y en la base `_comprobar_json` ya era exponencial en tiempo.
- **Profundidad máxima de JSON:** baja de 9994 a 9991 niveles. Pasado ese punto, ambas versiones fallan con `RecursionError`.

Ninguno de los dos afecta a la suite ni a los contratos actuales.

## Tareas candidatas (defectos reales fuera de alcance)
- `ruff format --check src/veridicus_contracts/loaders.py` falla en la línea del `raise LoadError(...)` de YAML, también en `feat/b1-contratos`. Es un fallo anterior a esta tarea. No hay `ruff format` en `.github/` (lo busqué con `grep`) y el `.pre-commit-config.yaml` no existe en el worktree, así que nada lo detecta hoy.

```
VEREDICTO: NO-VERDE
NARANJA|docs/loop/bitacoras/U01-T18d.md:21-25,114-139|Rojo y evidencias condensados, contra el Plan de pruebas de la tarea
AMARILLO|contracts/src/veridicus_contracts/loaders.py:50,83|Caché sin límite en funciones públicas
AMARILLO|contracts/src/veridicus_contracts/loaders.py:45-47|La copia por json.dumps/json.loads cambia dos bordes
INFORME: docs/loop/revisiones/U01-T18d/ronda-1.md
```
