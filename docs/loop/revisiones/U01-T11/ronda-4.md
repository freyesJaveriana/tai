# Ronda 4 — U01-T11

VEREDICTO: VERDE

Las correcciones de R3-01 a R3-05 funcionan. El revisor corrió él mismo CA-1 a CA-6 sobre 9702e18 y todos pasan. Los dos rojos salen con las mismas cifras que la bitácora. En la mutación solo sobreviven mutantes equivalentes que ya se conocían. No hay ningún rodeo con un nombre plausible en un contrato, y `comprobar` sobre el repositorio sigue vacío.

Aviso de Bash: dos sondas del revisor detuvieron al humano. Llevaban un `$ref` y un acento grave literales, y caracteres no ASCII. Las sondas siguientes solo llevaron ASCII y escapes.

## Criterios de aceptación, verificados por el revisor (HEAD 9702e18; el código es el de 3029ba2, porque 9702e18 solo toca la bitácora)

| # | Criterio | Comando | Resultado |
|---|---|---|---|
| 1 | Pruebas de veracidad y de casos | `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T11/contracts pytest tests/checks/test_veracity.py tests/checks/test_scan_cases.py --no-cov -q` | 724 passed |
| 1 | T03, marcas c8 y labels | `… pytest tests/guards/test_autonomia_03.py -m "c8 or labels" --no-cov -q` | 4 passed, 20 deselected |
| 2 | T03 sin c1, c19 ni c21 | `… pytest tests/guards/test_autonomia_03.py -m "not c1 and not c19 and not c21" --no-cov -q` | 17 passed, 7 deselected |
| 3 | Cobertura de los módulos guardia | `timeout 120 … --cov-fail-under=0 -q`, luego `uv run … coverage report --include=…veracity.py,…scan_cases.py --fail-under=100 --show-missing` | 100 % de líneas y de ramas (scan_cases: 236 líneas y 116 ramas; veracity: 243 y 114) |
| 4 | Mapa del paquete | `… pytest tests/test_package_map.py --no-cov -q` | 8 passed |
| 5 | Tipos y lint | `uv run … mypy --strict src` y `uv run … ruff check .` | sin errores / All checks passed! |
| 6 | Sin cambios al clúster | `bash /workspace/.worktrees/U01-T11/scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T11` | 0 apariciones |

## Rojo reproducido (copia temporal, ya retirada)

- **Código y datos de 010a990 con las pruebas de 3029ba2:** `… pytest tests/checks/test_veracity.py tests/checks/test_scan_cases.py tests/guards/test_autonomia_03.py -m "not c1 and not c19 and not c21" --no-cov -q --tb=no -p no:cacheprovider` da **196 failed, 545 passed, 7 deselected**, igual que la bitácora.
  - Fallan las 29 fronteras de R3-01, las tres formas nuevas de E-8 y E40 por cada término.
  - Falla `test_c8_tiene_exactamente_los_terminos_aprobados`.
- **R3-05, código y datos de f8586b5 con las mismas pruebas:** `… pytest tests/checks/test_veracity.py --no-cov -q --tb=no -rf -p no:cacheprovider -k "digitos_y_puntos or nfkc or limitacion_declarada_mayusculas or rutas_de_c6 or un_ref or con_ref_a_las_rutas"` da **16 failed, 15 passed, 375 deselected**: 12 de R2-01 y 4 de R2-04, como dice la bitácora.

## Mutación (3029ba2, script en AST propio)

- **veracity.py:** 533 mutantes, 2 vivos. Son los equivalentes ya conocidos: borrar el `continue` tras `_FALLO` (línea 479) y el de `elif relativa in ARCHIVOS_CLAVE` (línea 475).
- **scan_cases.py:** 382 mutantes, 3 vivos, todos equivalentes ya conocidos:
  - `+1 → +2` en los `range` de `_advierte` (líneas 260 y 264);
  - la constante del `" ".join` de D-2 (línea 189).
- `range(0x110000)` ya no sobrevive.

## R3-01: rodeos y falsos positivos con `[\W_]+` tras NFKC

- **Se detectan:** separadores ASCII (`filter[falso]`, `es/falso`, `es:falso`, `x-veridicus-falso`, `es_falso_v2`), caracteres invisibles o de formato (U+200B, U+00AD, U+2011, U+FEFF, U+2060, U+180E, U+034F), espacios y barras Unicode (U+2028, U+2215, U+FF0F, U+3000, U+00A0, U+00B4), marcas combinantes con forma compuesta, letras matemáticas que NFKC normaliza, `is‑lying` y `veracity·score`.
- **Limpios, como corresponde:** `page[size]`, `x-veridicus-limit` y `falsoª` (NFKC lo pasa a «falsoa»).
- **`esVeracidad`, `esIsLying` y `es-is_lying` no se detectan, y es correcto:** BR3.3 (rules.md:174) compara la categoría con el nombre completo y solo los términos de C8 por segmento.
- **Falsos positivos:** `veracity.comprobar(contracts)` y `scan_cases.comprobar(contracts)` devuelven `[]`.

## E-8 y R3-03

- C8 tiene **54 términos**. `test_c8_tiene_exactamente_los_terminos_aprobados` exige 54 y en 010a990 falla con `51 == 54`.
- Cada forma nueva tiene su caso sintético: `e8-mentisteis` (scan-cases.v1.yaml:325), `e8-inculpasteis` (413) y `e8-enganasteis` (501).
- No entra ninguna forma de «probar».
- La edición de T03 sigue limitada: `git diff 010a990..9702e18 -- contracts/tests/guards/test_autonomia_03.py` solo cambia `TERMINOS_DE_C8`, la cuenta (51 → 54) y la cifra del docstring.

## Limitaciones ya decididas: declaradas y fijadas

Las cuatro (`HTTPFALSO`, las mayúsculas a mitad de palabra, R3-02 y R3-04) están declaradas en el comentario de `FRONTERAS_DE_PALABRA` y cada una la fija una prueba en test_veracity.py (líneas 655, 697 y 704).

## Hallazgos

### R4-01 · AMARILLO · veracity.py `FRONTERAS_DE_PALABRA` · Marcas combinantes sin forma compuesta y letras modificadoras

- `fa̱lso`: la marca combinante no tiene forma compuesta en NFKC y es `\W`, así que parte la palabra en «fa» y «lso».
- `esʼfalso`: la letra modificadora U+02BC es `\w` y une las dos palabras.

Ninguno de los dos se detecta. No es un nombre plausible en un contrato, así que no bloquea. Es de la misma familia que R3-04, pero no está declarado. Registrado como K-28.

## Tareas candidatas

Ninguna nueva del revisor; el orquestador registra R4-01 como K-28.

Estado final: el worktree revisado está limpio (`git status --porcelain` vacío) en 9702e18.

```
VEREDICTO: VERDE
AMARILLO|contracts/src/veridicus_contracts/checks/veracity.py:FRONTERAS_DE_PALABRA|Marcas combinantes sin forma compuesta y letras modificadoras (U+0331, U+02BC) no declaradas como limitación
INFORME: docs/loop/revisiones/U01-T11/ronda-4.md
```
