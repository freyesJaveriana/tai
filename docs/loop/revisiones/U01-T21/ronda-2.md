# Ronda 2 — U01-T21

VEREDICTO: NO-VERDE

El código queda bien: F-01, F-03, F-04 y F-05 están resueltos, y F-02 también, con el rojo con esqueleto anexado literal. Los seis criterios pasan con mis propias corridas. Bloquea un solo NARANJA nuevo: la salida de CA-2 pegada en la bitácora no es literal. Trae una línea que el código no puede imprimir y le falta la línea final.

## Criterios de aceptación, verificados por mí

Todas las corridas son sobre `e44249f`, rebasada sobre `18164f9`, en `/workspace/.worktrees/U01-T21`.

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests/tools/test_check_package.py --no-cov -q -p no:cacheprovider` | pasa: 18 pasadas (8 funciones) |
| CA-2 | `timeout 180 uv run --frozen --directory /workspace/.worktrees/U01-T21/contracts python -m veridicus_contracts.tools.check_package` | código 0 en 1.3 s; «43 datos, 1 sueltos y 1 reservados»; C7 21, C1 21, C19 4; la forma antigua no se resuelve |
| CA-3 | `timeout 180 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests/tools/test_check_package.py -k rueda_contaminada --no-cov -q -p no:cacheprovider` | pasa: 1 pasada |
| CA-4 | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2551 pasadas en 123 s; el único aviso es el de pytest-socket |
| CA-5 | `pytest tests/test_package_map.py tests/checks/test_loader_usage.py tests/checks/test_fixture_coverage.py tests/checks/test_ci_workflows.py tests/checks/test_redos.py --no-cov -q -p no:cacheprovider` | pasa: 140 pasadas; las guardias de T18 siguen verdes |
| CA-5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts mypy --strict src` | `Success: no issues found in 42 source files` |
| CA-5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts ruff check .` | `All checks passed!` |
| CA-6 | `bash /workspace/.worktrees/U01-T21/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T21` | 0 apariciones |

El diff toca 4 archivos, todos dentro del alcance. Al terminar, `git status` sale limpio. No hay datos del piloto.

## Comprobaciones pedidas

- **La sonda de los 7 archivos, repetida sobre la rueda real** (`construir(..., offline=True, solo_rueda=True)` y luego `comparar_rueda`):
  - con la rueda completa, `real: []`;
  - al quitar los 7 archivos salen **7 problemas**, uno por archivo, cada uno «falta el dato veridicus_contracts/<ruta> en la rueda». Están `errors/error-codes.v2.yaml`, `format/datetime.v1.yaml`, `health/health.v2.yaml`, los tres de `queues/` y `ui/result-labels.v2.yaml`.
  - F-01 queda cerrado. El guion del paso 4 lee también archivo por archivo (`tabla["datos"]`), y `test_el_guion_falla_ante_un_dato_ausente...` lo prueba.
- **`DIRECTORIOS_RESERVADOS`** (`check_package.py:160-162`) es una lista cerrada:
  - Tiene una sola clave, `transcript`, con su motivo. La prueba fija `keys() == {"transcript"}` y `tabla.reservados == ("transcript",)`.
  - `tabla_de_rutas` solo marca reservado un directorio sin datos que esté en esa lista.
  - Sonda: con `ui/` sin datos y solo `.gitkeep`, el resultado es `['el directorio veridicus_contracts/ui no tiene datos en el árbol y no es reservado']`.
  - El directorio reservado exige su `.gitkeep`. Si `transcript` recibe datos, pasan a `datos` y se comparan uno a uno.
  - Sin la ruta de `contracts`, `datos` y `reservados` salen vacíos y todo directorio falla, así que el fallo es cerrado.
  - No encontré otro hueco.
- **El rojo con esqueleto (F-02)** está anexado literal en la bitácora (líneas 104-293):
  - En modo esqueleto, `16 failed, 1 passed`, todas por aserción.
  - En modo «antigua» (la regla por directorio de la ronda 1), `6 failed, 11 passed`, y fallan por la regla (`:71`, `:92`).
  - Repetí el modo «antigua» con la lógica por directorio parcheada en memoria: **6 failed, 12 passed**, en las mismas líneas `:71` y `:92`. Coincide con la bitácora.
  - En modo esqueleto, las de un solo catálogo caen en la precondición `:69` y no en la regla. El modo «antigua» sí las muestra fallando por la regla, así que entre los dos se cubre.
- **F-03:** `verificar` llama a `construir(..., offline=True)` (`:365`).
- **F-04:** el rótulo es «C1 (ReviewSuggestion, fixtures de C7)».
- **F-05:** la bitácora corrige el origen del aviso.

## Hallazgos

### F-06 · NARANJA · `docs/loop/bitacoras/U01-T21.md:299-310` · la salida de CA-2 pegada no es literal

- La tarea pide para CA-2 «la salida completa y el tiempo».
- La línea pegada como `paso 1: uv build de la rueda y el sdist (con --offline)` no la puede imprimir el código. `_paso(1, "uv build de la rueda y el sdist")` en `:363` imprime sin el paréntesis, y así sale en mi corrida.
- Falta la línea final `check_package: correcto en … s`, que aparece resumida en el encabezado.
- El comportamiento es correcto según mi corrida, pero la evidencia pegada está editada.
- Qué hacer: volver a pegar la salida tal cual sale, y poner fuera del bloque cualquier comentario sobre `--offline`.

### F-07 · AMARILLO · `check_package.py:160` · `DIRECTORIOS_RESERVADOS` es un `dict` mutable

Un `MappingProxyType` o un `frozenset` de pares lo haría inmutable. Es la constante que cierra la excepción, y la prueba solo fija sus claves en el momento de importar.

### F-08 · AMARILLO · `check_package.py:181-189` · el árbol de origen incluye archivos que el repositorio ignora

`_datos_del_arbol` recorre el disco y hatchling excluye lo que está en `.gitignore` (`.env`, `*.pem`, `*.key`, `*.local`, `*.log`, `*.sw?`). Un archivo así, suelto en un directorio de datos local, daría «falta el dato …» en vez de nombrar la causa. El fallo sigue siendo cerrado, solo que con un mensaje engañoso. Basta documentarlo o filtrar con `git ls-files`.

## Tareas candidatas (defectos reales fuera de alcance)

- Ninguna nueva. K-63 (`registry`) y K-64 (*fixture* propio de C1) ya están registradas.

```
VEREDICTO: NO-VERDE
NARANJA|docs/loop/bitacoras/U01-T21.md:299-310|La salida de CA-2 pegada no es literal: una línea que el código no imprime y falta la línea final
AMARILLO|contracts/src/veridicus_contracts/tools/check_package.py:160|DIRECTORIOS_RESERVADOS es un dict mutable
AMARILLO|contracts/src/veridicus_contracts/tools/check_package.py:181-189|El árbol de origen incluye archivos que el repositorio ignora: mensaje engañoso
INFORME: docs/loop/revisiones/U01-T21/ronda-2.md
```
