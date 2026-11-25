# Ronda 2: U01-T12

VEREDICTO: NO-VERDE

Revisión de 933b2d9 contra 42ff2ea.

- Los seis criterios de aceptación pasan: CA-1 con 145 passed y CA-3 con 248 sentencias y 124 ramas al 100 %.
- El rojo de la ronda 2 se reproduce: 52 failed y 89 passed.
- El alcance sigue limpio.

## Hallazgos de la ronda 1

| Hallazgo | Estado |
|---|---|
| F-01 | Cerrado, salvo G-04 |
| F-02 | Abierto: G-01 y G-02 |
| F-03 | Cerrado |
| F-04 | Cerrado. Las 7 reglas salen de NFR15.4 de U8 |
| F-05 | Cerrado |

## Hallazgos nuevos

### G-01 · NARANJA · `report_closed.py:47-50, 113-137`: la lista blanca admite espacios por ocho rodeos

Estos patrones pasan la guardia aunque `re.fullmatch` acepta un texto con espacio en blanco:
- `\040`
- `\N{SPACE}`
- `\U00000020`
- `\r`, `\v` y `\f`
- U+2003 y U+3000 escritos tal cual en el patrón

Hay también un AMARILLO: `[+-z]` acepta `<>;=?[\]^_`.

Corrección:
- Sustituir la lista negra por una gramática blanca:
  - `^` y `$`;
  - clases con rangos solo dentro de `A-Za-z0-9`;
  - los escapes `\.`, `\-` y `\+`;
  - los literales de la lista blanca;
  - `( ) | ?`;
  - los cuantificadores.
- Rechazar cualquier otra barra invertida y cualquier carácter fuera de ASCII.
- Usar como sondas todos los caracteres para los que `str.isspace()` es verdadero.

### G-02 · NARANJA · `report_closed.py:170-185`: arrays abiertos

La guardia no ve estos casos:
- `{"type": "array"}` sin `items`;
- `type` como lista que incluye `array`;
- `contains` sin `items`;
- `prefixItems: [true]`.

### G-03 · NARANJA · `report_closed.py:48, 206`: mutantes vivos

- **n03:** quita `re.DOTALL` del tokenizador. Ninguna prueba lleva un salto de línea literal en el patrón.
- **n19:** cambia `_ESPACIO.search(valor)` por `" " in valor`. Ninguna prueba usa un valor de `enum` con tabulador.

### G-04 · NARANJA · `report.schema.v2.yaml:270-277, 288-295`: `per_run` opcional en todas las métricas

BR12.3 lo exige. Según entities.md:391 y BR12.6, solo se exime en `three_run_agreement`, `scenario_a_difference` y `scenario_a_marker_hits`.

### G-05 · NARANJA · `report.schema.v2.yaml:35-221`: faltan campos de U11

- **NFR4.13** (`reliability-requirements.md:56`) pide `profile_sha256`, y reliability-design.md:140/159 y cicd-pipeline.md:114 piden además el SHA-256 de los umbrales. Sin ellos, todo reporte de U11 terminaría con el código 5.
- **NFR5.2** (`security-requirements.md:94`, Escenario B) pide que el reporte declare la familia de cada papel y la del generador.

## Decisiones del codificador, contrastadas

- **Tramos de BR12.5:** ninguna fuente fija los identificadores. Los nombres elegidos siguen la descripción de U11. Queda como precisión para que U11 la confirme.
- **Escenario A en `metrics`:** lo respaldan entities.md:389, BR12.6, NFR5.1 y cicd-pipeline.md:113. Se pierde el indicador `EvaluationRun.adversarial`, pero queda implícito en `scenario_a_*` (AMARILLO).
- **Escenario C:** está cubierto por `permutation_coverage` y `reversed_order_consistency`.

## Sin hallazgo

- Los mensajes no llevan valores.
- La exención de K-16 está acotada a `model-call.v1`, con sus pruebas. El mutante n13 muere.
- No hay ningún campo de veracidad.

## Candidata

- `model-call.v1.yaml` (T08) no tiene campo de familia, `at` solo tiene `format` y `role` tiene `maxLength: 32`. Se amplía K-16.
