# Ronda 1 — U01-T10

VEREDICTO: NO-VERDE

Los 6 criterios pasan con mis propias corridas. El empaquetado de F-12 es correcto y la suite no tiene ningún fallo nuevo. El veredicto queda en NO-VERDE porque las pruebas de los dos módulos guardia son débiles: **24 de 89 mutantes sobreviven** (el encargo pedía que no sobreviviera ninguno), y falta la prueba de pureza que pide §4.15.

Hash de la tarea comprobado: `sha256sum` = 778b771f…2bfd2, coincide. HEAD está en 7b4bd48 y el worktree sigue limpio después de todas mis corridas (`git status --short` vacío; solo hay cachés ignorados).

## Criterios de aceptación, verificados por mí
| # | Comando que corrí | Resultado |
|---|---|---|
| CA-1 | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T10/contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov -q` | pasa: 104 en 1,76 s |
| CA-2 | `… pytest … --cov-fail-under=0 -q`, luego `… coverage report --include=src/veridicus_contracts/limits.py,src/veridicus_contracts/checks/limits_catalog.py --fail-under=100 --show-missing` | pasa: 100 % de líneas y de ramas (152 líneas y 66 ramas, 0 sin cubrir) |
| CA-3 | `timeout 300 uv run … pytest tests/test_package_map.py --no-cov -q` | pasa: 8 |
| CA-4 | `uv lock --check --directory /workspace/.worktrees/U01-T10/contracts` | pasa: 79 paquetes resueltos; `uv.lock` no está en el diff |
| CA-5 | `… mypy --strict src` y `… ruff check .` | pasa: «Success: no issues found in 11 source files» y «All checks passed!» |
| CA-6 | `bash /workspace/.worktrees/U01-T10/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T10` | pasa: 0 apariciones |

## Puntos que pediste mirar
1. **La desviación de F-12 está justificada.** Repetí la alternativa de la tarea (`include` + `sources`) en una copia en el scratchpad. La rueda saca el archivo en la raíz (`['limits.v1.yaml', …]`), como dice la bitácora.
   - Con `force-include`, `limits.v1.yaml` queda solo en `veridicus_contracts/`, tanto en la rueda como en site-packages de la instalación editable. No hay copia en la raíz de ninguno de los dos.
   - La rueda directa y la que sale del sdist son idénticas.
   - Comparada con la rueda de la base, solo suma `limits.py`, `checks/limits_catalog.py` y `limits.v1.yaml`. No se pierde ningún dato que ya empaquetaba `hatch_build.py`.
   - El cambio en `pyproject.toml` es mínimo: la tabla `force-include` con una entrada, una `cache-key` y comentarios.
   - Riesgo con T08: hoy no hay conflicto. T08 no tiene commits y su worktree está limpio, y su tarea le prohíbe tocar `pyproject.toml` y `hatch_build.py`. Lo único que T08 podría tocar a la vez es `test_package_map.py`, que no es de T10 en la tabla.
2. **Las cifras coinciden con sus fuentes.** Comparé las 56 cifras de §5, con su unidad y su dueña: todas coinciden. Las cinco nuevas también, y sus fórmulas salen de sus fuentes:
   - 4·250 000 + 4 096 = 1 004 096 (session-lifecycle security-design:76);
   - 2 097 152 + 16 384 = 2 113 536;
   - 6 000 000 + 16 384 = 6 016 384;
   - 128 y 30.
   - Están las 7 relaciones de §5 más la de NFRD-U6-01.
3. **`load` cumple la regla.** Subir una cifra, un nombre desconocido, un valor que no es entero, uno negativo o cero, y una relación rota dan todos `LimitsConfigError` con `code = config.invalid_limit`. Igualar la cifra y bajarla se aceptan.
4. **Mutación:** lo detallo en F-01.
5. **`used_in: []` no hace pasar nada en vacío** en esta tarea. El único control sobre `used_in` es de forma, y §4.4 permite la lista vacía. La comprobación inversa es de T15 (ver tareas candidatas).
6. **El diff no revierte nada.** El diff de tres puntos solo trae los 9 archivos de la tarea.
   - La base avanzó a 7c0eedb (f61764c y 7c0eedb, solo `docs/` y `aidlc/`). El diff de dos puntos las muestra como borradas, pero `git merge-tree --write-tree` fusiona sin conflicto.
   - Suite completa: base 52 fallos y 237 pasan; T10 52 fallos y 342 pasan. Comparé los JUnit de las dos corridas: el conjunto de fallos es idéntico, sin fallos nuevos, sin arreglados, sin pruebas desaparecidas ni omitidas, y 105 pruebas nuevas.

## Hallazgos

### F-01 · NARANJA · checks/limits_catalog.py y limits.py · 24 mutantes vivos en los módulos guardia
Hice 89 mutantes en dos rondas, cada uno en un proceso de pytest aparte, sobre una copia en el scratchpad con su propio `.venv` (sin tocar el worktree). Sobreviven 24. Los agrupo por clase:
- **Relaciones obligatorias (7 de 8):** si se quita de `RELACIONES_OBLIGATORIAS` cualquiera salvo `import_file < import_body`, la suite sigue verde. `test_cada_relacion_de_security_design_esta_declarada` mira el YAML, no la guardia. Un PR que borre una relación del YAML pasaría la guardia mutada.
- **Fórmulas de las derivadas solo probadas en un punto:**
  - `4*-(-o//3)` → `4*(o//3)` vive, porque 6 000 000 y 6 000 003 son múltiplos de 3.
  - `+ (origen != 250000)` en transcript, y lo mismo en import y en voice, viven: nunca se cambia el origen de esas tres.
- **Listas y patrones cerrados sin fijar:**
  - añadir `"hours"` a `UNIDADES` vive;
  - `C[0-9]+` → `C[0-9]*` vive (acepta `"C"`);
  - quitar `import_body_max_bytes` o `import_file_max_bytes` de `OBLIGATORIAS` vive (no se prueba el borrado de la primera).
- **Forma de las relaciones:** `len == 3` → `>= 3` vive. Con la guardia mutada, una relación de 4 elementos hace fallar `relaciones_rotas` con `ValueError` en vez de reportarse. Quitar el control `all(isinstance(str))` también vive.
- **`derived_from`:** quitar los controles `== nombre` y `not in nombres` vive. La etapa de derivadas los tapa en parte, pero si falta el origen (`transcript_max_chars`), `comprobar_derivadas` da `KeyError`.
- **`_convertir`:**
  - `_DECIMAL.fullmatch` → `.match` vive: `VERIDICUS_LIMIT_POLL_INTERVAL_S=5abc` saldría como `ValueError` desnudo y no como `LimitsConfigError`;
  - `{1,18}` → `{0,18}` vive (aceptaría `"5."`);
  - `(?:0|…)` → `(?:[0-9]+|…)` vive (aceptaría `"007.5"`);
  - quitar `int(numero) if is_integer()` vive (devolvería 1.0 en vez de 1).
- Uno es equivalente y no cuenta como hueco: `!= SECCIONES` → `not <=`, porque la falta de una sección ya la detecta otra rama.

El comando completo está en esta sesión: un `python3 -I -c` que recorre la lista de mutantes con `…/scratchpad/mut/contracts/.venv/bin/python -B -m pytest … -x`.

### F-02 · NARANJA · tests/test_limits.py · falta la prueba de pureza de §4.15
§4.15 dice que la pureza de `limits.load` se comprueba con «la misma prueba» que la de `profiles.validate`: sustituir `open`, `os.environ` y `socket.socket` por funciones que fallan. Lo que hay no llega a eso:
- `test_load_no_toca_el_entorno_del_proceso` pone una variable en el entorno, pero no hace fallar `os.environ`;
- `open` no se sustituye;
- `socket` solo lo cubre `pytest-socket` para toda la suite.

### F-03 · AMARILLO · limits.py:89 y limits.py:52 · los mensajes llevan cifras
`sube la cifra de {efectivos} a {valor}` y `relación rota: … ({valor})` repiten el valor recibido, ya convertido a número. Ninguna fuente aprobada lo prohíbe para `limits`: entities.md:492 («nunca un valor») es de `profiles.validate`. Además el texto que no es un número nunca llega al mensaje, porque `_convertir` falla antes. Si el humano quiere aplicar la misma regla a los límites, el cambio es pequeño.

### F-04 · AMARILLO · limits.v1.yaml:13-14 · `used_in` de la cookie
§4.4 dice que `sessionCookie` de C1 marca `web_session_max_s` y `web_session_idle_s`, pero las dos quedan con `used_in: []`. Es válido hoy (§5 deja los `used_in` al PR de cada unidad), pero la comprobación inversa de T15 los va a pedir.

## Tareas candidatas (defectos reales fuera de alcance)
- T14/T15: alinear los `used_in` con las marcas reales de C1, C2, C5, C19 y C21. Por ejemplo, `web_session_*` → `[C1]` según §4.4.
- `load` no recalcula ni comprueba las derivadas tras bajar una cifra. Por ejemplo, bajar `audio_base64_max_chars` sin bajar `audio_max_bytes` deja un tope de base64 menor que el audio permitido. Ninguna relación de §5 lo cubre: lo debe decidir el diseño.

Archivos del revisor en el scratchpad: `base-junit.xml`, `t10-junit.xml`, `dist-t10/` y `dist-alt/` (la rueda de la alternativa con `include` + `sources`).

```
VEREDICTO: NO-VERDE
NARANJA|contracts/src/veridicus_contracts/checks/limits_catalog.py y limits.py|24 mutantes vivos en los módulos guardia (relaciones obligatorias, fórmulas, listas cerradas, _convertir)
NARANJA|contracts/tests/test_limits.py|falta la prueba de pureza de §4.15 (open, os.environ y socket.socket que fallan)
AMARILLO|contracts/src/veridicus_contracts/limits.py:89|los mensajes de LimitsConfigError repiten la cifra recibida
AMARILLO|contracts/limits.v1.yaml:13|used_in de web_session_* vacío aunque §4.4 los marca en C1
INFORME: docs/loop/revisiones/U01-T10/ronda-1.md
```
