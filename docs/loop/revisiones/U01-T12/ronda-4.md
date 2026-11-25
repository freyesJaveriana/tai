# Ronda 4: U01-T12

VEREDICTO: NO-VERDE

Revisión de f513f64 contra 105adac.

- Los seis criterios de aceptación pasan. En CA-3 hay 344 sentencias y 186 ramas, todas cubiertas (100 %).
- Quedan cerrados H-01 a H-04, y los mutantes p07 y p14 de H-05 ya mueren.
- Las cuatro pruebas ajustadas se justifican y no debilitan ningún control.
- **Suite integrada sobre `feat/b1-contratos` (107c00e):** fusiona sin conflictos. La base tenía 27 fallos y con el diff quedan 21. Todos vienen de C1, C6 y C8, que escribe T11, y el diff no añade ninguno.
- **Mutación:** de 21 mutantes, 18 mueren. q07 y q18 son equivalentes, y q21 sobrevive (F-02).

## Hallazgos

### F-01 · ROJO · `docs/loop/bitacoras/U01-T12.md:194-195`: el rojo no sale del commit

La bitácora declara 61 fallos y 262 aprobados. Con el archivo de pruebas de f513f64 salen 63 y 260. Las dos pruebas que sobran son `test_sin_el_allof_de_papeles_queda_en_rojo` y `test_sin_la_referencia_a_model_call_queda_en_rojo`.

### F-02 · NARANJA · `report_closed.py`, `_cierra`: el mutante q21 sobrevive

Ninguna prueba fija qué pasa con `false` dentro de `allOf` o de `anyOf`.

### F-03 · AMARILLO · ReDoS sin cuantificadores anidados

La guardia todavía admite `^(a|a)+$` y varios `[a-z]*` seguidos. Ver la candidata K-24.

### F-04 · AMARILLO · `(?i:`, `(?a:` y `(?-i:` compilan en Python, pero no en ECMA con la bandera `u`

Si se admiten, se rompe el consumidor de `contracts/ts/`.
