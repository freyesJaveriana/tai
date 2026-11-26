F-01: Corregido en d946600: toda palabra con alguna mayúscula (con guion, guion bajo, dígitos o \uXXXX) se enmascara entera; \n, \r y \t con barra invertida separan palabras; cinco formas en test_detection.py y en la propiedad Hypothesis.
F-02: Corregido en 8d58c61: salen Abril, Mayo, Junio y Marzo de allowed-words; prueba con lista negativa propia en test_catalogs.py.
F-03: No es un defecto: límite declarado (las claves y los números JSON no se seudonimizan, por diseño); candidata K-82 para U11.
F-04: Corregido en d946600: cada palabra con mayúscula de un tramo de varias palabras es forma propagable (también en system) con su propia marca, porque el rojo E2 exige que «Casilda» sola difiera de «Casilda Roncancio».
F-05: Fuera de alcance: tarea candidata K-81 (NER de B10b).
