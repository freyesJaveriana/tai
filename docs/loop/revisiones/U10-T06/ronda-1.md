# Ronda 1 — U10-T06 (excepción exacta de gitleaks, decisión A del humano)

**VEREDICTO: VERDE.** Revisor `sonnet`.

## Criterios, verificados por el revisor
| # | Criterio | Resultado |
|---|---|---|
| 1 | Alcance del diff `1defa6c..74c3d20` | Solo `.gitleaks.toml` (+9), la prueba nueva (+47) y la bitácora (+31). La entrada existente y `useDefault = true` no cambian |
| 2 | TOML válido (`test_gitleaks_allowlist.py --no-cov`) | 3 pasan |
| 3 | Suite completa con `--cov-fail-under=80` | 459 pasan, 99,54 % |
| 4 | `mypy --strict src tests`, `ruff check .`, `ruff format --check .` | limpios |
| 5 | `autoprueba-guardias.sh` | 17 de 17 sondas, 10 de 10 controles |
| 6 | Las 4 guardias `check-no-*` | 0 apariciones |
| 7 | Worktree | limpio |

## Excepción estrecha (`.gitleaks.toml:18-25`)
- El patrón único `\bsk-sintetico-canario-7f3a91c2d4e5\b` es una cadena literal con límites de palabra. No exime claves `sk-ant-…`, ni la variante con un carácter distinto, ni el valor con prefijo o sufijo alfanumérico; las tres están en la prueba.
- La descripción trae el motivo y «Revisar: 2027-05-25», que la prueba comprueba.
- La cadena solo aparece en `support.py:48`, en la excepción, en la bitácora y, como variante de un carácter, en la prueba.
- **Frente al *secret* de `generic-api-key`** (razonado, sin documentación consultada): sin `regexTarget`, la excepción se compara con el *secret*, que es el grupo de captura de la regla, con una clase que incluye el guion. Por eso captura el valor completo. La entrada previa usa el mismo esquema y ya funciona.

## Prueba no vacua
Borrar la entrada, ampliar el patrón a `sk-.*` o quitar la fecha hace fallar una prueba. Los mutantes se razonaron leyendo el código, sin ejecutarlos (regla del 2026-11-25).

## Hallazgos
- **F-01 · AMARILLO · `libs/anonymizer/tests/contracts/test_gitleaks_allowlist.py:35`.** La prueba no comprueba que la entrada no lleve `regexTarget`. Con `regexTarget = "line"`, el patrón seguiría eximiendo solo el canary, pero contra la línea entera. No bloquea.

**Pendiente:** la CI del PR 44 confirma que `repo-level0` queda en verde.

```
VEREDICTO: VERDE
AMARILLO|libs/anonymizer/tests/contracts/test_gitleaks_allowlist.py:35|la prueba no fija la ausencia de regexTarget
INFORME: docs/loop/revisiones/U10-T06/ronda-1.md
```
