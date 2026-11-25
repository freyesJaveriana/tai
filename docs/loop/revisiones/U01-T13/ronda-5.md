# Ronda 5: U01-T13

VEREDICTO: VERDE

Revisión de a86794f contra c00ec19.

## Criterios y pruebas

- **Criterios de aceptación:** los seis pasan.
  - CA-1a: 280 passed.
  - CA-2: 221 sentencias y 94 ramas, 100 %.
  - CA-5: `mypy --strict` y `ruff` limpios.
  - CA-6: 0 apariciones.
- **Rojo:** el `test_servers.py` final da 62 failed y 215 passed contra c00ec19. La bitácora registra 59 de 263 porque el rojo se tomó antes de añadir los controles que matan mutantes.
- **Mutantes que el codificador dijo haber matado:** todos mueren.

  | Mutante | Pruebas que fallan |
  |---|---|
  | R11 | 9 |
  | R11b a R11e | 6 cada uno |
  | R14 a R16 | 15 |
  | R18 y sus variantes | 1 cada uno |

- **Mutación:** 31 mutantes, 26 muertos y 5 equivalentes (R14b, X12, V07, X04 y X05).
- **Versión:** C16, C21, la ruta de voz, C2, C3 y C5 la cumplen. C1 también, según contract-summary, línea 209: `openapi: 3.1.0`.

## AMARILLO, candidatas para §4.9 (K-17)

Estas vías de escape exigen un documento redactado a propósito, y ningún contrato del plan las usa:

- Canales de AsyncAPI que son un `$ref` o que están en `components.channels`, y el destino de `operations.*.channel`.
- Un `$ref` en `responses`, algo que OpenAPI 3.1 no admite.
- Un `operationRef` a otro documento.
- `NOMBRE_DE_COMPONENTE` admite `~`. Debería ser el patrón de OpenAPI 3.1 (`[a-zA-Z0-9.\-_]+`).
