# Ronda 3: U01-T11

VEREDICTO: NO-VERDE

Revisión de 010a990 contra f8586b5.

## Lo que pasa

- Los seis criterios de aceptación pasan. CA-1a da 663 passed. CA-3 cubre el 100 %: `veracity` tiene 243 sentencias y 114 ramas.
- Quedan cerrados R2-02 (34/362, reproducido), R2-04 (`$ref` a C6 con un control positivo y otro negativo) y R2-05.
- E-8 se cumple:
  - C8 tiene 51 términos y no incluye ninguna forma de «probar».
  - Hay un caso de escaneo por cada forma.
  - La edición de T03 se limita a `TERMINOS_DE_C8` y a la cuenta, y su rojo da 50==51 y 52==51.
- Mutación: en `scan_cases.py` sobreviven 3 de 382 mutantes y en `veracity.py` 2 de 530. Todos son equivalentes.

## Hallazgos

### R3-01 · NARANJA · `veracity.py:145-151`: BR3.3 se rodea con cualquier signo que no sea `_`, `-`, `.` o un espacio

Se escapan, entre otros:
- `filter[falso]` y `falso[]` (deepObject de OpenAPI);
- `es/falso`, `es:falso`, `es+falso` y `es(falso)`;
- el espacio de ancho cero, el guion blando, el punto medio y los guiones Unicode.

**Corrección:** después de NFKC, tratar como frontera todo lo que no sea letra ni dígito.

### R3-02 · AMARILLO: los segmentos sin tilde coinciden

«menti», «engane» e «inculpo» coinciden como segmento. Hoy no hay ningún caso real ni en los contratos ni en C1.

### R3-03 · AMARILLO: detalles de E-8

- Se añadieron formas del imperfecto (`mentía`, `mentían`).
- «Vosotros» está en presente y falta en pretérito.

### R3-04 · AMARILLO: limitaciones sin declarar

- letras de otro alfabeto que se parecen a las latinas (`а` cirílica);
- letras fuera de Latin-1 antes de una mayúscula;
- dígitos que no son ASCII;
- `Ⅻfalso`.

### R3-05 · AMARILLO: rojo de la bitácora

El rojo de 16 fallos que registra la bitácora se tomó de un estado intermedio que no está en ningún commit.
