# Ronda 3 — U01-T18d

VEREDICTO: VERDE

F-04 y F-05 están resueltos. Mis dos mutantes de la ronda 2, con caché en la función pública de YAML o de JSON, ahora hacen fallar la prueba por la regla. CA-1 a CA-5 pasan en mis propias corridas. No queda nada que bloquee: los dos puntos que señalo abajo son AMARILLO y no impiden fusionar.

**Lo revisado.** Rama `tarea/U01-T18d` en 623a3f7, con base de fusión bf93de8. De bf93de8 a eeee712 solo cambian `docs/loop/` (`CANDIDATAS.md` y los informes de T19 y T21). La ronda 3 solo toca `contracts/tests/test_loaders.py` (en f60d902) y las bitácoras. `loaders.py` sigue igual que en 9c1c2b7. El worktree quedó limpio al terminar (`git status --porcelain` vacío).

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | V-SUITE | `cat /proc/loadavg` (2.00 1.40 1.49), luego `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T18d/contracts pytest -q --cov-report=` | `2535 passed, 1 warning in 27.16s`, cobertura 99.75 %, código 0: pasa |
| 2 | no se recogen menos pruebas | `uv run … pytest --collect-only -q --no-cov -p no:cacheprovider -k test_loaders` | `10/2535 tests collected`: 2535 en total, frente a 2533 en la base (`contracts/` no cambió desde la ronda 1): pasa |
| 3 | guardias al 100 % de ramas | `timeout 300 uv run … pytest tests/checks -q --cov-report=`, luego `coverage report --include=*/veridicus_contracts/checks/* --fail-under=100 --format=total` | `1886 passed in 19.74s`; total `100`, código 0: pasa |
| 4 | nada se aflojó | `git -C … diff feat/b1-contratos...HEAD -- contracts/pyproject.toml contracts/uv.lock` y `git grep -c -E "max_examples\|deadline=\|skip\|xfail"` en HEAD y en la base | diff vacío; mismos conteos por archivo (1, 2, 11, 1, 4, 1): pasa |
| 5 | tipos | `uv run … mypy --strict src` | `Success: no issues found in 41 source files` |
| 5 | lint | `uv run … ruff check .` | `All checks passed!` |
| 5 | clúster | `bash /workspace/.worktrees/U01-T18d/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T18d` | `0 apariciones`, código 0 |

## Estado de los hallazgos de la ronda 2
- **F-04, resuelto.** La prueba ahora cuenta los análisis reales. En YAML usa un doble de `loaders._lector_yaml`. En JSON usa un doble de `json` dentro del módulo, que cuenta solo las llamadas con `object_pairs_hook`; así la copia de `load_file` no cuenta como análisis. En los dos casos exige 2 análisis para 2 llamadas con el mismo texto. Mis mutantes en proceso (`python -c "exec(...)"`, la función pública envuelta en `functools.cache` y copiada) dieron:
  - **YAML:** `usa mutante YAML: True` → `FALLA: load_yaml_text recuerda los textos que recibe`.
  - **JSON, con YAML intacto:** `usa mutante JSON: True  YAML original: True` → `FALLA: load_json_text recuerda los textos que recibe`, con `CacheInfo(hits=1, misses=1, …)`.
- **El rojo de la bitácora (líneas 524-607) es literal y falla por la regla.** Son dos salidas de pytest completas: `assert 1 == 2` en `tests/test_loaders.py:84` (YAML) y en `:103` (JSON), con `1 failed, 9 passed`. No hay ningún error de import. La línea 610 trae el verde sobre el código real: `10 passed`.
- **F-05, resuelto.** La prueba ya no recibe `tmp_path`.
- **Alcance.** Siguen siendo solo las dos pruebas que autoriza P-T18d-1. `monkeypatch` deshace los dobles al terminar, así que no se filtra estado a otras pruebas.

## Hallazgos (ninguno bloquea)

### F-06 · AMARILLO · docs/loop/bitacoras/U01-T18d.md:175-176, 188 y U01-T18d-ronda-1-respuesta.md:3-5 · SHA reescritos sin la marca en la misma línea
Esas líneas citan 60b20f4 y 687d002, que el rebase reescribió. La tarea pide marcar cada SHA reescrito «en la misma línea». La línea 519 ya los declara reescritos todos juntos y da su equivalencia (5cfd5b5, 9c1c2b7, 435be84), así que nada se presta a confusión. Solo falta la marca en cada línea.

### F-07 · AMARILLO · contracts/tests/test_loaders.py:73-103 · La prueba depende de un detalle de la implementación
La prueba cuenta cuántas veces se crea el lector de YAML. Una optimización futura que reutilice el objeto `YAML`, sin guardar ningún texto, la haría fallar en falso. Hoy no afecta a nada. Si ese cambio llega, la prueba se ajusta en ese momento.

## Tareas candidatas (defectos reales fuera de alcance)
- Sigue en pie la de las rondas anteriores: `ruff format --check` falla en `loaders.py` también en la base, y no hay `ruff format` en `.github/`.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U01-T18d.md:175-176,188|SHA reescritos sin la marca en la misma línea
AMARILLO|contracts/tests/test_loaders.py:73-103|La prueba depende de un detalle de la implementación
INFORME: docs/loop/revisiones/U01-T18d/ronda-3.md
```
