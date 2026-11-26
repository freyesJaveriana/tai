# Ronda 2: U01-T33

Revisor `opus`. Revisó b943c77 (pruebas en 0bf1fef) contra la base `46dfba2`.

**Veredicto: NO-VERDE.** Queda un NARANJA en pie. Como es la última ronda (ML-5), la decisión pasa al humano.

F-01 de la ronda 1 quedó corregido. El barrido sobre los 0x110000 puntos de código no encuentra ningún carácter que NFKD convierta en letra y que esconda un término. Pero el mismo barrido encontró otra reducción de la detección, de otra causa, que la prueba de «solo amplía» no recorre.

## Criterios, corridos por el revisor (HEAD b943c77)

| # | Comando | Resultado |
|---|---|---|
| CA-1 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/contracts pytest tests/checks/test_veracity.py tests/tools/test_gen_ts.py --no-cov -q` | Pasa: 518 pasadas |
| CA-2 | `uv run … --directory …/libs/integrity_policy pytest -q` | Pasa: 288 pasadas |
| CA-3 | lectura de vuelta del C8 versionado | `2.1.0 NFKD 17` |
| CA-4 | `timeout 60 uv run … pytest`, en las dos rutas y en la misma sesión | `main`: 3005 pasadas, 97,97 %, **23,76 s**. Worktree: 3024 pasadas, 98,00 %, **23,99 s** |
| CA-5 | el paso 5 tal cual, los cuatro «Informe de cobertura de …» y `coverage_gate` | 100 % (3109 sentencias, 1484 ramas); la compuerta da código 0 |
| CA-6 | `timeout 300 … incoherence_analyzer pytest --cov… --cov-fail-under=80` | 568 pasadas, 99,26 % |
| CA-7 | `--collect-only` y `git diff --exit-code 46dfba2 -- …` | 3024 y 288 pruebas recogidas; el diff sale vacío |
| CA-8 | mypy, ruff check, ruff format y lint-imports en los dos paquetes, más los dos guiones | Todo en 0; los guiones dan `0 apariciones` |

Otras comprobaciones:

- **`compatibility_scope: word_characters`:** está en C8, `veracity.py:136`, `gen_ts.py:94`, el TypeScript generado (`FOLD_COMPATIBILITY_SCOPE`) y el escáner (`scan.py:103`, que falla cerrado si falta).
- **`security-surface.json`:** solo cambia la huella de C8.
- **El oráculo `_old_fold`:** coincide con el `scan.py` de `46dfba2`.
- **Mutantes, aplicados en memoria con `mock.patch.object`:** los cuatro mueren.
  - `covers` devuelve `False`: fallan 25 pruebas.
  - NFD para todo: fallan 8.
  - `_problemas_de_rangos` devuelve `[]`: fallan 9.
  - NFKD para todo, la regresión de F-01: fallan 6, entre ellas `test_the_fold_only_widens_what_the_scanner_detects`.
- **El worktree:** quedó limpio al terminar.

## Hallazgos

### F-04 · NARANJA · `scan.py:_dropped` y los rangos de C8 · Los 3769 `Cn` ahora unen palabras que en `main` estaban separadas

El revisor cargó el `scan.py` real de `main` junto al nuevo y probó 7 plantillas por punto de código. Resultado:

- **0 pérdidas** por NFKD.
- **7889 ampliaciones.**
- **3769 pérdidas reales**, todas de categoría `Cn`, cuando el carácter va entre una letra y el término.

Ejemplo: `'es' + chr(0x2065) + 'falso'` da `[('falso', 3, 8)]` en `main` y `[]` en el worktree. Lo mismo pasa con U+FFF0 a U+FFF8 y con los `Cn` de U+E0000 a U+E0FFF.

Hay dos huecos en la entrega:

- **La prueba de «solo amplía» no recorre estos puntos.** Solo recorre los 3812 puntos donde NFKD difiere de NFD, y su supuesto («los rangos solo descartan más») es falso: descartar más une dos palabras.
- **C8, `scan.py` y la bitácora dicen algo que no es cierto.** C8 (líneas 31 a 34), el comentario de `scan.py` y la bitácora afirman «el plegado solo amplía la detección».

**Atenuante:** es el mismo comportamiento que `main` ya acepta para `Cf` (`test_a_format_character_used_as_a_separator_joins_the_two_words`), y sigue la idea de K-91 de que un invisible no parte la palabra.

Salidas posibles:

- **(a) Mantener «solo amplía».** Se detecta sobre dos pliegues, con los `Cn` de los rangos como descarte y como separador, y se unen los resultados. La prueba de «solo amplía» se extiende a todos los puntos de los rangos.
- **(b) Aceptar la unión como limitación declarada**, igual que con `Cf`. Se corrigen las afirmaciones y se añade una prueba explícita de que `es` + `Cn` + `falso` da `[]`.

### F-05 · AMARILLO · `scan.py:_read_fold` · El fallo cerrado de F-02 no cubre los separadores

Un C8 adulterado con `dropped_code_points: [[0x20, 0x20]]` carga sin error, y con él `'El testigo dijo que es falso y miente.'` da `[]`. El chequeo solo rechaza `L*` y `N*`, así que pasan `Z*`, `P*` y `S*`. El comentario de la línea 37 exagera. No bloquea: `veracity.py` exige la lista aprobada en la CI.

### F-03 (ronda 1) · Cerrado

Con 19 pruebas más, el aumento es de 0,23 s, y lo explican las pruebas nuevas de `test_veracity.py`. Ninguna es cara sin necesidad. 23,99 s cabe en el techo local de 24 s, aunque apenas.

## Tareas candidatas

- Validar en tiempo de ejecución la huella de `match.fold` (o la lista exacta de rangos) frente a la aprobada (F-05).
- Llevar a `scan-cases.v1.yaml`, en su propio PR (BR1.5), los casos compartidos con U8: ancho completo, Hangul, `Cn`, símbolos de compatibilidad junto al término y la regla que se elija para F-04.

```
VEREDICTO: NO-VERDE
NARANJA|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:_dropped (rangos Cn de C8)|Los 3769 Cn unen palabras que main separaba: 'es'+U+2065+'falso' se detectaba y ya no; la prueba de solo amplía no los recorre y C8 afirma que el plegado solo amplía
AMARILLO|scan.py:_read_fold|El fallo cerrado acepta un rango sobre el espacio (U+0020) y el escáner queda ciego sin error
INFORME: docs/loop/revisiones/U01-T33/ronda-2.md
```
