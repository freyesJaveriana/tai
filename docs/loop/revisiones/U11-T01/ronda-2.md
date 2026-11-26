# Ronda 2 — U11-T01

`revisor` (`opus`), 2026-11-26.

VEREDICTO: VERDE

Los diez criterios se corrieron en `/workspace/.worktrees/U11-T01`, en HEAD `45bd164`, con base `bolt/b11a-analyzer` = `f943b84`. Todos pasan, y F-01, F-02 y F-04 están resueltos. Queda un AMARILLO nuevo que no bloquea. Después de los comandos, el worktree sigue limpio (`git status --porcelain` vacío).

## Criterios de aceptación, verificados por mí

| # | Comando que corrí (por paquete donde aplica) | Resultado |
|---|---|---|
| 1 | `timeout 600 uv lock --directory …/libs/<P>`, `timeout 600 uv sync --frozen [--extra cli] --directory …`, `timeout 120 uv lock --check --directory …` y `timeout 300 uv run --frozen --offline --directory …/libs/<P> mypy --strict src` | Pasa en los 4 paquetes, con código 0. Resolvió 80, 72, 71 y 71 paquetes, sin cambios en el lock. mypy: 21, 6, 4 y 3 archivos sin errores. |
| 2 | `timeout 60 uv run --frozen --offline --directory …/libs/errors pytest` | Pasa: 14 pruebas, 8 de ellas en `test_analyzer_errors.py`, con 100 % de cobertura. Incluye `CancelledError`, `GatewayConfigError` y `CliInterruptedError`. |
| 3 | `pytest tests/test_package.py -q` por paquete, más `grep -n "addopts\|manual\|cli:"` en los 4 `pyproject.toml` | Pasa: 3, 3, 4 y 3 pruebas, y `SocketBlockedError` bloquea la conexión. `addopts = "--strict-markers --disable-socket -m 'not manual'"`, sin `--cov`. Los marcadores `manual` y `cli` están declarados. |
| 4 | `pytest tests/test_conftest_rojo.py -q` (analizador) | Pasa: 3 pruebas. |
| 5 | `--collect-only -q` en el analizador (`tests/guards tests/contracts`) y en `execution_profiles` (`tests/contracts`) | Pasa: 111 + 14 = 125 pruebas y 0 errores. |
| 6 | `pytest tests/guards tests/contracts -p no:cacheprovider -rfE --tb=line --rojo` en el analizador, `tests/contracts … --rojo` en `execution_profiles` y `tests/guards --rojo` en `integrity_policy` | Pasa. Los tres terminan con código 1: `111 failed`, `14 failed` y `20 failed`, con 0 `ERROR`. Todos fallan por el `NotImplementedError` de un *stub*, también las 4 pruebas nuevas de F-01 (`load_config`). |
| 7 | `git -C … log --oneline bolt/b11a-analyzer..tarea/U11-T01 -- <las 6 rutas congeladas>` | Pasa con la regla aceptada de dos commits: `c7e6542` y `82b2e6d`. `ROJO_SHA: c7e6542c26f14ad6c4b35636bbfc791ff60a5145` aparece una sola vez en la bitácora. |
| 8 | `mypy --strict src tests`, `ruff check .` y `ruff format --check .` en los 4 paquetes, más los dos `ruff` en `libs/errors` | Pasa: mypy da 35, 8, 9 y 8 archivos sin errores; *All checks passed!*; todos los archivos ya tienen formato. |
| 9 | `timeout 300 uv run --frozen --offline --directory …/libs/anonymizer pytest --cov=veridicus_anonymizer --cov-branch --cov-fail-under=80 -q` | Pasa: 459 pruebas y 99,54 % de cobertura. |
| 10 | `bash …/scripts/check-no-{datos-personales,cluster-ids,insumos}.sh /workspace/.worktrees/U11-T01` | Pasa: los tres dan `0 apariciones`. |

**Otras comprobaciones**

- **Los commits del rojo solo traen pruebas.**
  - `git show --stat c7e6542` muestra un solo archivo, `tests/guards/test_autonomia_03_vocabulary.py`.
  - `82b2e6d` trae 15 archivos, todos bajo `tests/`, incluidos `support.py` y el `conftest` de `integrity_policy`.
  - Ninguno de los dos toca `src/`.
- **Renombre (`057a724`):** cambia solo las 2 clases, sus pruebas y una línea del docstring de `api.py`. `grep -rnwP "Cancelled|CliInterrupted"` sobre `libs/` no encuentra nada.
- **Los `code` que faltan en el catálogo:** `guardia.comprobar(...)` devuelve exactamente los 3 esperados (`run.cancelled`, `config.invalid_gateway`, `system.interrupted`), cada uno como E31. Es lo previsto hasta que entre U01-T32.
- **Alcance:** el diff no toca `contracts/` ni `libs/anonymizer/`. Fuera de los 4 paquetes solo cambian `libs/errors` y `docs/loop/`.
- **Hashes de la bitácora:** `git rev-parse HEAD:<ruta>` da `db7b327…` y `3702f5f…`, los mismos que anota la bitácora.

## Comprobación de F-01, F-02 y F-04

- **F-01, resuelto.** `test_autonomia_03_vocabulary.py:79-112` trae dos pruebas a nivel de `analyze`, cada una con `hecho` y con `observaciones`.
  - La regla de C8 es esta: un tramo «…» de más de un término no se escanea si aparece literal en un turno (`scan_bare_term_spans`).
  - La simulé en memoria. Con los turnos como `literal_sources`, el escáner da `[]` en (a) y `['miente']` en (b). Con los dos mutantes:

    | Mutante | (a) «era falso» | (b) «miente ahí» | Efecto |
    |---|---|---|---|
    | `scan(observaciones, [observaciones])` | — | `[]` | falla (b): mutante eliminado |
    | escáner sin ninguna exclusión | `['falso']` | — | falla (a): mutante eliminado |

  - Lo que se probó es el escáner, no `analyze`, que sigue siendo un *stub*. Que `analyze` le pase los turnos al escáner lo razoné leyendo el código.
- **F-02, resuelto.** La bitácora tiene 47 líneas, una sola línea `ROJO_SHA:`, las 6 rutas congeladas y ninguna de las líneas viejas.
- **F-04, resuelto.** `_forbidden_field_names()` (`:38-46`) lee `categories_forbidden_in_schemas` del C8 que trae `veridicus_contracts`. No es un archivo de T02 o T03, así que no choca con R-07.

## Hallazgos

### F-06 · AMARILLO · `libs/incoherence_analyzer/tests/guards/test_autonomia_03_vocabulary.py:79-94` · La prueba (a) no distingue «todos los turnos» de «solo los turnos citados»

- **Qué pasa:** la prueba (a) pone «era falso» dentro de T2, que es el mismo turno de `cita_a`. Por eso también la pasa una implementación que use solo los textos de las citas (`[cita_a, cita_b]`) como `literal_sources`.
- **Comprobado en la sonda:** con ese mutante, el escáner da `[]` en (a) y `['miente']` en (b), igual que la implementación correcta. Ninguna prueba congelada lo detecta.
- **Gravedad:** BR9.3 pide «textos de todos los turnos». Este mutante descarta de más (un tramo que es literal de un turno no citado), pero no deja pasar vocabulario prohibido, así que no hay fuga de AUTONOMIA-03.
- **Corrección:** el archivo ya está congelado. En U11-T04 (paso 9), agregar en un archivo de pruebas no congelado un caso con «era falso» literal en un turno **no citado** (p. ej. T3), que debe salir sin descartes.

## Tareas candidatas (defectos reales fuera de alcance)

No hay nuevas. Siguen en pie las dos de la ronda 1: la ruta `cita_a.texto` en C8 (K-86) y BR2.2 frente a `validate_profile` en semantic-agent (K-87).

```
VEREDICTO: VERDE
AMARILLO|libs/incoherence_analyzer/tests/guards/test_autonomia_03_vocabulary.py:79-94|BR9.3: la prueba (a) no distingue literal_sources de todos los turnos frente a solo las citas (cubrirlo en U11-T04)
INFORME: docs/loop/revisiones/U11-T01/ronda-2.md
```
