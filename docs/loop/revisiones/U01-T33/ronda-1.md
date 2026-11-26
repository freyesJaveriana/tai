# Ronda 1: U01-T33

Revisor `opus`. Revisó b0854a9 (el rojo está en e2c50d3) contra la base `46dfba2`.

VEREDICTO: NO-VERDE

## Criterios de aceptación, verificados por el revisor

| # | Comando que corrió (rutas absolutas) | Resultado |
|---|---|---|
| CA-1 | `uv run … contracts pytest tests/checks/test_veracity.py tests/tools/test_gen_ts.py --no-cov -q` | Pasa: 544 pasadas |
| CA-2 | `uv run … libs/integrity_policy pytest -q` | Pasa: 273 pasadas |
| CA-2, rojo | `test_fold.py` del worktree corrido con el entorno de `main` (`--directory /workspace/libs/integrity_policy`) | 53 fallan y 25 pasan: el rojo es real sobre el `scan.py` de `main` |
| CA-3 | Lectura de vuelta del C8 versionado | `2.1.0 NFKD 17` |
| CA-4 | `timeout 60 uv run … contracts pytest` | 3050 pasadas, 98,00 %, **24,14 s**. En `main`: 3005 pasadas, **23,68 s** |
| CA-5 | Paso 5 de `contracts-level0.yml`, más los cuatro «Informe de cobertura de …» y `coverage_gate` | 100 % (3109 sentencias, 1484 ramas); la compuerta da código 0 |
| CA-6 | `timeout 300 … incoherence_analyzer pytest --cov… --cov-fail-under=80` | 568 pasadas, 99,26 % |
| CA-7 | `--collect-only` y `git diff --exit-code 46dfba2 -- …` | 3050 y 273 pruebas recogidas; el diff sale vacío |
| CA-8 | mypy, ruff check, ruff format y lint-imports en los dos paquetes, más los dos guiones | Todo en 0; los guiones dan `0 apariciones` |

Lo que el orquestador pidió comprobar aparte:

- **Revisión corta (F-01 a F-03, F-05 a F-07):** sus correcciones están en e2c50d3. Entre e2c50d3 y b0854a9 las pruebas solo suman 26 líneas: los 10 casos de fallo cerrado.
- **Mutantes, aplicados en memoria con `mock.patch.object`:**
  - sin descarte por rango (`_Fold.covers` devuelve `False`): fallan 25 pruebas;
  - NFD en lugar de NFKD: fallan 8;
  - sin la forma de los rangos en `veracity.py`: fallan 17.

  Los tres mueren.
- **Tramos con NFKD:** las letras matemáticas dan el tramo `(2, 7)` exacto, y la propiedad Hypothesis verifica que `start` y `end` caen dentro del texto. `_span_end` sigue llevando al tramo las marcas descartadas que van detrás del término, también los rellenos Hangul y los `Cn`.
- **Fallo cerrado:** con un `fold` ausente o desconocido, la carga lanza `ValueError`; nunca vuelve a NFD. Las exclusiones (cita literal y D-2) siguen igual.
- **TypeScript y `security-surface.json`:** el TypeScript generado coincide con C8 (17 rangos, NFKD, casefold), y en `security-surface.json` solo cambia la huella de C8.
- **Los diez casos de fallo cerrado añadidos en el verde:** son legítimos. Ejercen ramas reales de `scan.py` y también fallan contra `main`.
- **Ligaduras:** `casefold` ya las pliega en `main`, así que son pruebas de regresión, y están bien declaradas en la bitácora.

## Hallazgos

### F-01 · ROJO · `libs/integrity_policy/src/veridicus_integrity_policy/scan.py:157` (`_fold`, NFKD) · El cambio reduce lo que el escáner detecta (AUTONOMIA-03)

NFKD convierte en letras algunos símbolos que hoy separan palabras. Cuando uno de ellos va pegado a un término, el término deja de detectarse.

Con el mismo `python -c` en los dos entornos:

| Texto | `main` | worktree |
|---|---|---|
| `'Es falso' + chr(0x2122)` (™) | `[('falso', 3, 8)]` | `[]` |
| `chr(0x2122) + 'falso'` | `[('falso', 1, 6)]` | `[]` |
| U+24D0 (ⓐ), U+2116 (№), U+33A1 (㎡) o U+2120 (℠) junto a `falso` | detecta | `[]` |

Un barrido sobre los 0x110000 puntos de código, que compara el pliegue NFD con el NFKD y mira si el carácter queda como letra (`\w`), encontró 779 puntos que pasan de no ser letra a serlo al principio de su forma plegada, y 778 al final. Entre ellos están ™, ℠, №, ℡, las letras en círculo (U+24B6 a U+24E9) y los símbolos cuadrados como ㎡.

La tarea dice que el cambio «solo puede ampliar lo que el escáner detecta, nunca reducirlo». La propiedad Hypothesis no lo vio porque solo inserta puntos de `dropped_code_points`, nunca un vecino que NFKD expande.

Qué falta, a criterio del codificador:

- decidir la frontera de palabra sobre el carácter original, o tratar como separador la expansión de un carácter que no era letra;
- declarar esa regla en `match.fold`, para que U8 escanee igual;
- añadir una prueba de «solo amplía»: todo carácter que separaba un término en `main` lo sigue separando.

### F-02 · AMARILLO · `scan.py`, `_read_fold` · El escáner solo comprueba la forma de C8, no sus valores

`_read_fold` acepta cualquier categoría general (por ejemplo `[Lu, Ll]`) y cualquier rango válido (por ejemplo `[0x41, 0x7A]`). Un C8 así descartaría las letras y el escáner no detectaría nada, sin fallar. Hoy solo lo impide `veracity.py` en la CI. No bloquea, porque el contrato versionado está protegido, pero no es fallo cerrado en tiempo de ejecución.

### F-03 · AMARILLO · CA-4 · La suite de `contracts` queda en el techo

En la corrida del revisor, el worktree tardó 24,14 s y `main` 23,68 s, o sea +0,46 s por las 45 pruebas nuevas de `test_veracity.py`. Ninguna prueba nueva es cara sin necesidad. No bloquea, porque el umbral de la CI es de 52 s, pero queda a 0,14 s del techo local.

## Tareas candidatas (defectos reales fuera de alcance)

- Llevar a `scan-cases.v1.yaml` los casos de ancho completo, Hangul y `Cn`, y los de símbolos de compatibilidad junto al término, para que U8 los comparta. Por BR1.5 va en otro PR.
- Validar en tiempo de ejecución que `match.fold` de C8 es el aprobado, o comprobar su huella, en vez de fiarse solo de la CI (F-02).

```
VEREDICTO: NO-VERDE
ROJO|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:157 (_fold NFKD)|NFKD convierte ™, ℠, №, ⓐ y ㎡ (779/778 puntos) en letras y esconde términos que main detectaba (AUTONOMIA-03)
AMARILLO|scan.py _read_fold|El escáner solo valida la forma de match.fold, no sus valores
AMARILLO|CA-4|La suite de contracts tarda 24,14 s frente a 23,68 s en main (techo local 24 s)
INFORME: docs/loop/revisiones/U01-T33/ronda-1.md
```
