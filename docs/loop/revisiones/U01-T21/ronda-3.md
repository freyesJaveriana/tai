# Ronda 3 — U01-T21

VEREDICTO: VERDE

F-06, F-07 y F-08 están resueltos. Corrí yo mismo CA-1 a CA-6 y todos pasan, incluidos CA-3 y CA-6, que el codificador no repitió. No queda ningún ROJO ni NARANJA. Lo único abierto es una nota AMARILLO, que no bloquea. La fusión la decide el humano.

## Criterios de aceptación, verificados por mí

Todas las corridas son sobre `6a95ae4`, rebasada sobre `eeee712`, en `/workspace/.worktrees/U01-T21`.

| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `timeout 120 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests/tools/test_check_package.py --no-cov -q -p no:cacheprovider` | pasa: 18 pasadas |
| CA-2 | `timeout 180 uv run --frozen --directory /workspace/.worktrees/U01-T21/contracts python -m veridicus_contracts.tools.check_package` | código 0 en 1.3 s, dentro del límite de 180 s |
| CA-3 | `timeout 180 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests/tools/test_check_package.py -k rueda_contaminada --no-cov -q -p no:cacheprovider` | pasa: 1 pasada, 17 sin seleccionar |
| CA-4 | `timeout 600 uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts pytest tests --no-cov -q -p no:cacheprovider` | pasa: 2551 pasadas en 121 s; el único aviso es el de pytest-socket |
| CA-5 | `pytest tests/test_package_map.py tests/checks/test_loader_usage.py tests/checks/test_fixture_coverage.py tests/checks/test_ci_workflows.py tests/checks/test_redos.py --no-cov -q -p no:cacheprovider` | pasa: 140 pasadas; las guardias de T18 siguen verdes |
| CA-5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts mypy --strict src` | `Success: no issues found in 42 source files` |
| CA-5 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T21/contracts ruff check .` | `All checks passed!` |
| CA-6 | `bash /workspace/.worktrees/U01-T21/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T21` | 0 apariciones |

Repetí la sonda de los 7 archivos sobre la rueda real como regresión:
- con la rueda completa no sale ningún problema (`[]`);
- al quitar los 7 archivos salen 7 problemas, uno por archivo;
- `DIRECTORIOS_RESERVADOS` es ahora de tipo `mappingproxy`.

El diff toca 5 archivos, todos dentro del alcance. Al terminar, `git status` sale limpio. No hay datos del piloto.

## Estado de los hallazgos anteriores

- **F-06 (NARANJA): resuelto.** El bloque de CA-2 de la ronda 3 (bitácora, líneas 320-334) coincide línea por línea con mi corrida. Ya no trae el paréntesis «(con --offline)» y sí trae la línea final `check_package: correcto en … s`. La única diferencia es el tiempo: 1.5 s en la bitácora y 1.3 s en mi corrida, algo esperable entre corridas. La nota «(codigo de salida 0)» va como anotación aparte, debajo de la salida. El bloque editado de la ronda 2 se retiró y lo sustituye una referencia (línea 299).
- **F-07 (AMARILLO): resuelto.** `DIRECTORIOS_RESERVADOS` es un `Mapping[str, str]` envuelto en `MappingProxyType`, con el mismo contenido. La prueba de `transcript` exige `TypeError` al intentar asignarle una clave nueva.
- **F-08 (AMARILLO): resuelto.** La limitación queda documentada en el docstring de `_datos_del_arbol`: un archivo que el repositorio ignora, suelto en un directorio de datos, da «falta el dato…». Es aceptable dejarlo así, porque filtrarlo exigiría llamar a `git` por `subprocess` o añadir una dependencia, y el fallo sigue siendo cerrado.

## Hallazgos

### F-09 · AMARILLO · `docs/loop/bitacoras/U01-T21.md:300,303` · CA-3 y CA-6 no se volvieron a correr sobre el HEAD final (no bloquea)

En la sección «Verde (ronda 2)» de la bitácora, CA-3 y CA-6 son corridas de la ronda 2, y CA-6 aparece todavía sin la raíz del worktree como argumento. Entre las dos rondas solo cambiaron una constante, un docstring y una prueba, y yo corrí los dos criterios sobre `6a95ae4`: pasan. Basta anotarlo; no hace falta otra ronda.

## Tareas candidatas (defectos reales fuera de alcance)

- Ninguna nueva. K-63 (`registry`) y K-64 (el *fixture* propio de C1) ya están registradas.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U01-T21.md:300,303|CA-3 y CA-6 no se volvieron a correr sobre el HEAD final (corridos por el revisor: pasan)
INFORME: docs/loop/revisiones/U01-T21/ronda-3.md
```
