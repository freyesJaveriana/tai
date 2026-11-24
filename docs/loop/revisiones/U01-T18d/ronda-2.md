# Ronda 2 — U01-T18d

VEREDICTO: NO-VERDE

F-01, F-02 y F-03 están resueltos, y CA-1 a CA-5 pasan en mis propias corridas. El veredicto es NO-VERDE por un hallazgo nuevo, NARANJA: la prueba nueva que debe vigilar P-T18d-1 sigue pasando si se vuelve a poner una caché en `load_yaml_text`.

**Lo revisado.** Rama `tarea/U01-T18d` en c5f5bc0, con el código en 687d002 y una base de fusión 9b39bb3. Comparé con `git diff feat/b1-contratos...tarea/U01-T18d`. `feat/b1-contratos` ya avanzó a 18164f9, pero de 9b39bb3 a 18164f9 solo cambian documentos (`docs/loop/CANDIDATAS.md` y los informes de T19 y T21). El worktree quedó limpio al terminar (`git status --porcelain` vacío).

**Rebase y alcance.**
- De 69e5d4b a 9b39bb3 solo cambian `decisiones-humano.md`, `CANDIDATAS.md` y el informe de la ronda 1.
- El diff de la tarea toca solo `loaders.py`, `tests/test_loaders.py` (exactamente las 2 pruebas que autoriza P-T18d-1, más el import) y dos bitácoras.
- No cambian *fixtures*, contratos, `pyproject.toml` ni `uv.lock`.
- 60b20f4 sigue vigente en la rama: es el commit rebasado. 5121ba0 quedó reescrito y la bitácora ya no lo cita. Los demás SHA que cita la bitácora (9b39bb3, 69e5d4b, 687d002) existen.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | V-SUITE | `cat /proc/loadavg` (0.99 1.56 1.53), luego `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18d/contracts pytest -q` | `2535 passed, 1 warning in 27.86s`, cobertura 99.75 %, código 0: pasa |
| 2 | no se recogen menos pruebas | `uv run … pytest --collect-only -q --no-cov -p no:cacheprovider` | 2535, frente a 2533 en la base (contada en la ronda 1; `contracts/` no cambió desde entonces): pasa |
| 3 | guardias al 100 % de ramas | `timeout 300 uv run … pytest tests/checks -q --cov-report=`, luego `coverage report --include=*/veridicus_contracts/checks/* --fail-under=100 --format=total` | `1886 passed in 20.19s`; total `100`, código 0: pasa |
| 4 | nada se aflojó | `git -C … diff feat/b1-contratos...HEAD -- contracts/pyproject.toml contracts/uv.lock` y `git grep -c -E "max_examples\|deadline=\|skip\|xfail"` en HEAD y en la base | diff vacío; mismos conteos por archivo (20 líneas): pasa |
| 5 | tipos | `uv run … mypy --strict src` | `Success: no issues found in 41 source files` |
| 5 | lint | `uv run … ruff check .` | `All checks passed!` |
| 5 | clúster | `bash /workspace/.worktrees/U01-T18d/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18d` | `0 apariciones`, código 0 |

## Estado de los hallazgos de la ronda 1
- **F-01, resuelto.** La bitácora (líneas 144-171) trae el rojo exacto de CA-1 sobre la base, con código 124 y salida literal. Mi corrida de la ronda 1 dio el mismo resultado. CA-1, CA-3, CA-4 y CA-5 están pegados completos (líneas 189-513) y el conteo de CA-4 está corregido a 20.
- **F-02, resuelto en el código.** `load_yaml_text` y `load_json_text` vuelven a ser idénticas a la base; solo cambian sus docstrings. La caché vive en el ayudante privado `_analizado_de_archivo(es_yaml, texto)`, que solo usa `load_file`. La prueba que lo vigila es débil (ver F-04).
- **F-03, resuelto.** Las funciones públicas ya no copian. El cambio de alias en `load_file` queda aceptado por P-T18d-1.

**Relectura de un archivo modificado (lo que pediste mirar).** `load_file` llama a `read_text` en cada llamada y la clave de la caché es `(es_yaml, texto)`, así que todo cambio en el archivo se vuelve a analizar. Mi sonda con `load_file` sobre un archivo temporal lo confirma:

| Contenido | Resultado |
|---|---|
| `x: 1` | `{'x': 1}` |
| `x: 2` | `{'x': 2}` |
| clave duplicada | `LoadError` |
| `x: 1` otra vez | `{'x': 1}` |
| `{"x": 01}` en `.json` | `LoadError` |
| `{"x": 01}` en `.yaml` | `{'x': 1}` |

La caché terminó con `currsize=3`. Un error no se guarda, y el mismo texto con otro sufijo no se mezcla.

## Hallazgos

### F-04 · NARANJA · contracts/tests/test_loaders.py:73-89 · La prueba de P-T18d-1 no falla si las funciones públicas vuelven a tener caché
Para decidir que no hay caché, `test_las_funciones_publicas_de_texto_no_tienen_cache` mira tres cosas:
- que no exista `cache_info` en la función pública;
- que el resultado sea una copia;
- el `currsize` de `_analizado_de_archivo`.

Las tres siguen igual si se vuelve a poner un ayudante con caché dentro de `load_yaml_text`, que es justo lo que hacía 60b20f4. Lo comprobé con un mutante en proceso: `load_yaml_text = _copia(functools.cache(original)(texto))`, aplicado antes de importar `tests.test_loaders`.

```
usa mutante: True
la prueba PASA con load_yaml_text recordando textos; memo: CacheInfo(hits=2, misses=2, maxsize=None, currsize=2)
```

La bitácora tampoco trae el rojo de esta prueba. Su «rojo de P-T18d-1» (líneas 175-181) es una sonda del scratchpad, no esta prueba corrida contra 60b20f4: contra 60b20f4 la prueba habría fallado por el import de `_analizado_de_archivo`, no por la caché.

Arreglo sugerido, dentro de las dos pruebas que autoriza P-T18d-1: contar las llamadas a `loaders._lector_yaml` con `monkeypatch` y exigir dos análisis para dos llamadas con el mismo texto. En JSON, hacer lo mismo con un doble de `json.loads` en el módulo. Pegar el rojo de esa versión contra 60b20f4.

### F-05 · AMARILLO · contracts/tests/test_loaders.py:73 · Parámetro sin uso
`test_las_funciones_publicas_de_texto_no_tienen_cache` recibe `tmp_path` y no lo usa.

## Tareas candidatas (defectos reales fuera de alcance)
- Sigue en pie la de la ronda 1: `ruff format --check` falla en `loaders.py` también en la base, y no hay `ruff format` en `.github/`.

```
VEREDICTO: NO-VERDE
NARANJA|contracts/tests/test_loaders.py:73-89|La prueba de P-T18d-1 no falla si las funciones públicas vuelven a tener caché
AMARILLO|contracts/tests/test_loaders.py:73|Parámetro sin uso
INFORME: docs/loop/revisiones/U01-T18d/ronda-2.md
```
