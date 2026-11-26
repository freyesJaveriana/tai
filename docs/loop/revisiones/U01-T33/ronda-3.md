# Ronda 3: U01-T33

Revisor `opus`. Revisó ff7c055 (pruebas en db23695) contra la base `46dfba2`. Es la ronda que autorizó el humano como excepción a ML-5, con doble pliegue para F-04 y solo invisibles para F-05.

**Veredicto: VERDE.** No queda ningún ROJO ni NARANJA; hay tres AMARILLO. El worktree quedó limpio.

## Criterios, corridos por el revisor

| # | Comando | Resultado |
|---|---|---|
| CA-1 | `uv run --frozen --offline --directory /workspace/.worktrees/U01-T33/contracts pytest tests/checks/test_veracity.py tests/tools/test_gen_ts.py --no-cov -q` | 519 pasan |
| CA-2 | `uv run … --directory …/libs/integrity_policy pytest -q` | 300 pasan (en `main`, 195) |
| CA-3 | Lectura de vuelta del C8 versionado | `2.1.0 NFKD 17` |
| CA-4 | `timeout 60 uv run … pytest` en las dos rutas, seguidas y sin carga de fondo | `main`: 3005 pasan, 97,97 %, **23,85 s**. Worktree: 3025 pasan, 98,00 %, **23,77 s** |
| CA-5 | El paso 5 tal cual, los cuatro «Informe de cobertura de …» y `coverage_gate` | 100 % (3109 sentencias, 1484 ramas); la compuerta da código 0 |
| CA-6 | `timeout 300 … incoherence_analyzer pytest --cov… --cov-fail-under=80` | 568 pasan, 99,26 % |
| CA-7 | `--collect-only` y `git diff --exit-code 46dfba2 -- …` | 3025 frente a 3005 en `main`, y 300 frente a 195; el diff sale vacío |
| CA-8 | mypy, ruff check, ruff format y lint-imports en los dos paquetes, más los dos guiones | Todo en 0; los guiones dan `0 apariciones` |

Desviaciones menores de los comandos literales: CA-6 y la primera pasada de CA-4 se corrieron con `-q`, y las rutas de `coverage_gate` se pasaron desde `--directory`, que es la misma resolución que usa la CI.

## Verificaciones

1. **Barrido «nunca detecta menos».** El `scan.py` real de 46dfba2 se cargó en memoria junto al nuevo.
   - Las 7 plantillas sobre los 0x110000 puntos de código dan 7 784 448 casos, **0 pérdidas** y 7899 ampliaciones.
   - Las 12 plantillas combinadas (un `Cn` separador con otro `Cn` dentro del término, un relleno Hangul junto a letras de ancho completo, etc.) dan 1 114 428 casos y **0 pérdidas**.
2. **F-05.** El escáner rechaza `dropped_categories` vacío y cualquier rango sobre un espacio, un signo, un símbolo, una letra o un dígito. Queda el hueco F-07.
3. **`test_the_fold_never_detects_less_than_before`.** No es vacía: tiene más de 5000 casos y tarda 1,07 s. Su oráculo es fiel a `main`. Los cuatro mutantes mueren:
   - sin la segunda pasada, fallan 8;
   - con NFKD para todo, fallan 6;
   - con `covers` en `False`, fallan 23;
   - sin la validación de solo invisibles, fallan 7.
4. **Cambios de expectativa.** Ninguno debilita una garantía: son ampliaciones, o repiten lo que `main` ya hacía.
5. **Regresión.** Pasan:
   - los casos sonda;
   - `tests/guards/` en los dos paquetes (90 y 192 pruebas);
   - `scan-cases.v1.yaml`, sin cambios;
   - `security-surface.json`, donde solo cambia la huella de C8;
   - el TypeScript `FOLD_*`, igual a C8.

## Hallazgos

### F-06 · AMARILLO · `scan.py:scan_detailed` · La unión da tramos solapados y alarga algunos tramos

- **Tramos solapados.** `'falso'+chr(0x2065)+'s'` da `[('falso',0,6),('falsos',0,7)]`. Lo mismo pasa con `miente`/`mientes`, `prueba`+U+FFA0+`s` y `engaño`/`engaños`.
- **Tramos más largos.** `_span_end` absorbe el `Cn` final: `falso`+U+2065+`es` da (0,6), y `main` daba (0,5).
- **Efecto hoy.** Ningún consumidor se rompe: `filter.py:153` solo mira si hay alguna coincidencia, y la restauración de U10 no usa el escáner. U8 sí contaría o resaltaría dos veces.

### F-07 · AMARILLO · `scan.py:_read_fold` · El fallo cerrado acepta un subconjunto de `dropped_categories`

Un C8 adulterado con `dropped_categories: [Cf]` carga sin error y deja de detectar `fal`+U+0941+`so` (`Mn` de clase 0) y `fal`+U+20DD+`so` (`Me`). Hoy no es realista, porque `veracity.py` exige la lista exacta en la CI.

### F-08 · AMARILLO · Limitación no declarada · Dos `Cn`, uno pegado a una letra y otro dentro del término

`'es'+chr(0x2065)+'fa'+chr(0x2065)+'lso'` da `[]`. `main` tampoco lo detecta, así que no es una pérdida, pero ni C8 ni la bitácora lo declaran.

## Tareas candidatas

- Decidir si la unión se queda con la coincidencia más larga por inicio, o documentar los solapes para U8 (F-06).
- Exigir en tiempo de ejecución que `dropped_categories` sea exactamente `{Mn, Me, Cf}`, o validar la huella de `match.fold` (F-07).
- Llevar a `scan-cases.v1.yaml`, en su propio PR (BR1.5), los casos de doble pliegue y la limitación F-08.
- Para U8: `newly_dropped` depende de la versión de Unicode de cada motor. Conviene exportar la lista explícita en vez de derivarla.

```
VEREDICTO: VERDE
AMARILLO|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:scan_detailed|La unión da tramos solapados (falso y falsos sobre la misma ocurrencia) y alarga el tramo sobre un Cn final; ningún consumidor actual se rompe
AMARILLO|libs/integrity_policy/src/veridicus_integrity_policy/scan.py:_read_fold|El fallo cerrado acepta dropped_categories [Cf] y entonces deja de descartar Mn de clase 0 y Me, que main descartaba
AMARILLO|C8 match.fold.also_as_separators|Limitación no declarada: es+Cn+fa+Cn+lso evade las dos pasadas (main tampoco lo detecta)
INFORME: docs/loop/revisiones/U01-T33/ronda-3.md
```
