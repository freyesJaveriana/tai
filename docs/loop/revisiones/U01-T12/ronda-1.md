# Ronda 1: U01-T12

VEREDICTO: NO-VERDE

Revisor sobre `tarea/U01-T12` en 42ff2ea (base 8e9fb75). El sha256 de la tarea coincide (`410c303a…640afe`). El diff toca 4 archivos: esquema, guardia, pruebas y bitácora. No sale del alcance.

## Criterios de aceptación (corridos por el revisor)

| # | Resultado |
|---|---|
| CA-1 | `61 passed` |
| CA-2 | `1 passed, 13 deselected` |
| CA-3 | `57 passed`; `report_closed.py` 200 sentencias y 100 ramas, 100 % |
| CA-4 | `8 passed` |
| CA-5 | mypy `Success: no issues found in 15 source files`; ruff `All checks passed!` |
| CA-6 | `0 apariciones`, código 0 |
| Rojo | Reproducido en un worktree temporal desde 8e9fb75: `ImportError` de `report_closed` y `5 failed` por `contrato ausente: cli/report.schema.v2.yaml` |

## Hallazgos

### F-01 · NARANJA · `contracts/cli/report.schema.v2.yaml:263-277` y `127-155`: `metrics` contradice BR12.3, FD-U11-09 y C19 v1

**Faltan los valores por corrida.** Los piden C19 revisión 4 (contract-summary.md:2541), FD-U11-09 y BR12.3 de U11 («el reporte trae el valor de cada corrida»). `MetricResult` (entities.md:391) define `per_run` (3 valores) y `aggregate`. En cambio, el `metric` del esquema solo tiene `value`, `threshold` y `passes`, con `additionalProperties: false`. Por eso `{value: 0.9, per_run: [0.9, 0.8, 1.0]}` se RECHAZA.

**Rango más ancho que v1.** C19 v1 fija las fracciones en `[0, 1]` y `anonymizer_leaks` como entero. El esquema da `0..10^9` como `number` a todas:
- `precision.value = 500000000` se ACEPTA;
- `anonymizer_leaks.value = 0.5` se ACEPTA.

**Corrección:**
- Añadir `per_run` (array de exactamente 3), `aggregate`, `threshold` y `passes`.
- Dar a cada métrica su rango: `ratio` para las fracciones y `count` para `anonymizer_leaks` y `scenario_a_marker_hits`.

### F-02 · NARANJA · `contracts/src/veridicus_contracts/checks/report_closed.py:46, 112, 154-170`: la guardia no ve 13 esquemas defectuosos

Con `comprobar_documentos` sobre copias en memoria, todos estos dan «SIN PROBLEMAS»:

- **Patrones que admiten espacios.** `_ESPACIOS` solo busca un espacio literal o `\s`, así que pasan:
  - `^.{1,128}$`
  - `^[^<>]{1,128}$`
  - `^[a-z\x20]{1,128}$`
  - `^[a-z\W]{1,128}$`
- **Esquemas que aceptan cualquier valor:**
  - `properties.libre: true`
  - `{"anyOf": [true]}`
  - un `$ref` a un `$defs` vacío
  - `items: {}` en `distance_sensitivity`
  - `additionalProperties: {}` en `discards`
  - `patternProperties: {".*": {}}`
- **Claves abiertas.** Si se quita `propertyNames` de `discards` o de `clarifications.discarded`, las claves quedan abiertas.
- **`created_at`.** No tiene tope ni marca (ver F-04).

**Corrección:**
- Comprobar los patrones por lo que aceptan:
  - admitir solo clases de una lista blanca;
  - prohibir `.`, `[^`, `\W`, `\D`, `\S`, `\x`, `\u` y `\p`;
  - probar con `fullmatch` contra un espacio, un tabulador y un NBSP.
- Rechazar los esquemas `true` y los subesquemas sin `type`, `$ref`, `enum` ni `const`.
- Exigir `propertyNames` cerrado cuando `additionalProperties` sea un esquema, y rechazar `patternProperties`.
- Añadir un control negativo por cada caso.

### F-03 · NARANJA · `report_closed.py:98, 102, 117`: sobreviven mutantes no equivalentes

De 24 mutantes sobreviven 7. Tres son equivalentes (m07, m13 y m23/m24). Los no equivalentes son estos:

| Mutante | Cambio | Consecuencia |
|---|---|---|
| m04 | `sitio.endswith(".properties.seed")` pasa a `"seed" in sitio` | — |
| m06 | se quita el `break` del enum | los mensajes salen duplicados |
| m19 | se quita `isinstance(..., int)` de los enteros | se acepta `minimum: 0.0, maximum: 5.5` |
| m20 | se quita `isinstance(largo, bool)` | se acepta `maxLength: true` |

**Corrección:** un control negativo por cada mutante.

### F-04 · NARANJA · `report.schema.v2.yaml:51-53, 164-165, 181, 207-214`: cadenas sin tope y etiquetas abiertas donde la fuente fija un conjunto cerrado

- **`created_at`.** Solo lleva `format: date-time`, sin `maxLength: 128` ni marca, e incumple §4.18 y el paso 14. Un validador sin formatos (ajv sin ajv-formats) lo dejaría abierto.
  - Corrección: patrón RFC 3339, `maxLength: 128` y marca.
- **`clarifications.discarded`.** Usa `propertyNames: slug48`, pero NFRD-U8-09 fija 7 reglas. La clave `rocamora` se ACEPTA.
  - Corrección: `enum` con los 7 identificadores, o declarar el canal junto a FD-U1-05.
- **`distance_sensitivity.range`.** Usa `slug32`, pero BR12.5 fija 3 tramos.
  - Corrección: `enum`.
- **`synthetic_set`.** Usa `slug128`, pero FD-U11-07 y `BiasLabelList` fijan `<tipo_hecho>__<perfil_persona>`.
  - Corrección: `^[a-z0-9-]{1,23}__[a-z0-9-]{1,23}$`.

### F-05 · AMARILLO · `report.schema.v2.yaml:42, 152-155, 186-197`

- `profile_name` admite `_`, cuando C18 y C19 v1 usan `^[a-z0-9-]{1,48}$`.
- `metrics` se acepta con `kind: run`, cuando v1 dice «Solo evaluation». Falta un `if`/`then`.
- Los resultados del Escenario A aparecen dos veces: en `metrics.scenario_a_*` y en `adversarial`.

## Sin hallazgo

- Los mensajes solo llevan la regla y la ruta del esquema.
- No hay ningún campo de veracidad (AUTONOMIA-03).
- Coinciden con las fuentes:
  - `seed` admite negativos;
  - `estimated_cost` llega hasta 10^9;
  - las latencias son enteras;
  - el `allOf` acota los tres papeles.
- El límite del *canary* de FD-U1-05 está declarado.

## Candidata fuera de alcance

- `model_calls/model-call.v1.yaml` (T08): sus cadenas no llevan `x-veridicus-limit`, y `role` tiene `maxLength: 32`. T15 debe incluirlas al comparar con C25.
