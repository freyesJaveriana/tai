# Ronda 1 — U01-T31

Revisor `opus`. Revisó d3ba9d1 (rojo en 62b9128) contra la base `2de43aa`.

## Criterios de aceptación, verificados por el revisor

| # | Comando que corrió | Resultado |
|---|---|---|
| CA-1 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts pytest tests/checks/test_veracity.py --no-cov -q --durations=15` | `491 passed in 1.50s` |
| CA-1 (rojo) | `git -C … show --stat 62b9128` | El commit del rojo solo trae pruebas, sin cambios en `veracity.py`. Sin `problemas_de_rutas` y con C8 en 2.0.0, las pruebas de los casos sonda fallan. El rojo es válido. |
| CA-2 | `uv run … python -c "…load_file(Path('/workspace/.worktrees/U01-T31/contracts/integrity/forbidden-vocabulary.v2.yaml'))…"` | `2.0.1 ['salida.hallazgos[].cita_a.cita', 'salida.hallazgos[].cita_b.cita']`. Lee el archivo versionado. |
| CA-3 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T31/contracts pytest` | `3005 passed, 1 warning in 23.76s`, cobertura 97,97 %. Está bajo el techo de 24 s. |
| CA-4 | `coverage report --include="…checks/*,…profiles.py,…limits.py,…canonical.py,…registry.py" --fail-under=100`, literal del paso 5 | `TOTAL … 100%`; `veracity.py` con 303 sentencias y 140 ramas, todas cubiertas. Código 0. |
| CA-5 | `pytest --collect-only -q --no-cov` | `3005 tests collected`. La base tiene 2920: el diff solo añade las 85 pruebas y no quita ninguna. |
| CA-5 | `git -C … diff --exit-code 2de43aa -- contracts/pyproject.toml contracts/uv.lock libs` | Código 0. |
| CA-6 | `uv run … --directory …/libs/integrity_policy pytest -q` | `195 passed`. Además, la copia instalada en su `.venv` ya trae C8 con `2.0.1`, así que la prueba de verdad usa el C8 nuevo. |
| CA-7 | `mypy --strict src` · `ruff check .` · `ruff format --check .` · los dos guiones | Sin problemas · `All checks passed!` · `113 files already formatted` · `0 apariciones` y `0 apariciones`. |

## Ataques y mutantes

- **Casos sonda 1 a 7:** cada uno tiene su prueba y todas pasan. La propiedad Hypothesis sobre las rutas es correcta frente al C6 real: por ejemplo, `estado` solo tiene `enum` y se rechaza como se espera.
- **Mutante 1, la comprobación de tipo `string` anulada** (`mock.patch.object(v,'_nodo_de_ruta',…)`): fallan 24 pruebas. Las pruebas no son vacuas.
- **Mutante 2, `problemas_de_rutas` devuelve `[]`:** fallan las 4 pruebas del defecto original, también las de punta a punta que pasan por `comprobar`.
- **Fallo cerrado ante `$ref`:** los `$ref` rotos, externos, a la raíz (`#`), de tipo distinto de texto o en ciclo de 1 o 2 saltos informan el problema. El tope de 16 saltos impide que se cuelgue.
- **Sin falso positivo:** las 5 rutas `salida.…` aprobadas pasan. La ruta opcional `observaciones_conductor[].tema` también pasa.
- **AUTONOMIA-03 no cambia de alcance:** `terms`, `scanned` y el resto de `match` no cambian. El único consumidor, `libs/integrity_policy/scan.py`, no lee `excluded_whole_texts`. `tests/guards/test_autonomia_03.py` sigue en verde.

## Las dos decisiones del codificador

- **(a) Usar el C6 que `comprobar` ya carga, no `build_registry`:** no es un problema. Ese C6 sale del archivo versionado, leído con `load_file`, y no de una lista copiada a mano. Como C6 solo tiene `$ref` internos, el registro no añadiría nada.
- **(b) Regenerar `security-surface.json`:** no es un desborde. Cambia una sola línea, la huella de C8, y es la consecuencia mecánica de cambiar C8. Sin ella fallan sus pruebas, y las 17 de `test_security_surface` pasan.

## Pruebas caras

Ninguna es cara sin necesidad. Las dos propiedades Hypothesis usan 60 y 80 ejemplos y tardan 0,11 s y 0,05 s. Todo `test_veracity.py` corre en 1,5 s.

## Hallazgos

### F-01 · AMARILLO · `veracity.py`, `problemas_de_rutas` · El límite del tipo exacto no está declarado
La comprobación exige `type == "string"` exacto. Rechazaría un texto definido solo con `enum` o `const`, o con `type: ["string", "null"]`. Es una postura de fallo cerrado y está bien, pero la bitácora y la docstring no lo declaran como límite.

### F-02 · AMARILLO · CA-3 · No hay línea base de `main`
La tarea pide explicar cualquier subida de más de 0,5 s respecto de `main`, y nadie midió `main`. Las pruebas nuevas añaden unos 0,3 s, según `--durations`. Hoy el margen frente al techo de 24 s es de 0,24 s.

### F-03 · AMARILLO · El PR debe rebasarse antes de fusionar
La rama sigue sobre `2de43aa`. El PR #56 ya está en `origin/main`, así que hay que rebasar antes de fusionar. El codificador ya lo anotó.

## Tareas candidatas (defectos reales fuera de alcance)

- `libs/anonymizer/tests/guards/test_autonomia_05_restoration.py` usa los punteros `/hallazgos/0/cita_a/texto`, cuando C6 llama `cita` a ese campo. Conviene confirmar que la restauración de citas de U10 apunta al campo `cita` de C6 y no a `texto`.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/veracity.py:problemas_de_rutas|Exigir type == "string" exacto rechaza textos con solo enum o const o con tipo unión; falta declararlo como límite
AMARILLO|CA-3|Sin línea base de main para la regla de +0,5 s; 23,76 s frente al techo de 24 s
AMARILLO|rama tarea/U01-T31|Rebasar sobre origin/main (#56) antes de fusionar
INFORME: docs/loop/revisiones/U01-T31/ronda-1.md
```
