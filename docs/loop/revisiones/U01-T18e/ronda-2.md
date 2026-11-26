# Ronda 2 — U01-T18e

**Veredicto:** VERDE

Revisé `c304454` sobre `origin/main` = `a8d7756`, que es también el merge-base. El worktree quedó limpio al terminar.

## Criterios de aceptación (comprobados por el revisor)

| # | Comando | Resultado |
|---|---|---|
| CA-1 | `timeout 60 uv run --frozen --offline --directory …/contracts pytest` | Código 0. `2920 passed, 1 warning in 23.91s`, dentro de los 24 s (P-T18e-1). |
| CA-2 | `uv sync --frozen --offline --compile-bytecode …` y después CA-1 | Compiló 2504 archivos. El paso 4 no construyó ni instaló nada. |
| CA-3 | `--collect-only`, `git diff` de `pyproject.toml` y `uv.lock`, conteo de marcadores | 2920 pruebas recolectadas. Sin diferencias en dependencias ni en marcadores con respecto a `main`. |
| CA-4 | Paso 5 literal | `TOTAL 3012 0 1428 0 100%` |
| CA-5 | mypy, ruff check, ruff format, yamllint y los tres guiones | Código 0 en todos. Los guiones dan `0 apariciones`. |

## CA-6 (medido por el orquestador en el PR #49)

- **Corrida:** 45854891387, job 140030551112, sobre `c304454`.
- **Paso 3b** (sincronizar y compilar los `.pyc`): de 16:02:18Z a 16:02:21Z, 3 s.
- **Paso 4** (suite de Python): de 16:02:21Z a 16:03:10Z, **49 s**. Cumple el máximo de 52 s de P-T18e-1 y deja 11 s de margen frente al límite de 60 s. En la ronda 1 fueron 51 s.
- El job entero terminó en verde en 1 min 40 s.

## Correcciones de la ronda 1

- **F-02 (cerrado):** el paso 3b usa ahora `uv sync --frozen --offline --compile-bytecode`. El paso 4 conserva su texto literal.
- **F-03 (cerrado):** `normalizar` y `con_veracidad` vuelven a ser públicas y sin caché. La caché pasó a `_con_veracidad_recordada`, que es privada y da el mismo resultado.
- **F-04 (cerrado):** la bitácora documenta el cambio de `RecursionError`.

## Hallazgos

- **F-05 · AMARILLO · CA-1:** el margen local es de solo 0,09 s (23,91 s frente a 24 s). No bloquea, porque lo que decide es CA-6.
- **F-06 · AMARILLO · `contracts-level0.yml:70-71`:** no se sabía si `--compile-bytecode` ahorraba tiempo en la CI. La medición de CA-6 muestra que el paso 4 bajó de 51 s a 49 s. No bloquea.

## Tareas candidatas

Ninguna.
