# Ronda 2: U01-T11

VEREDICTO: NO-VERDE

Revisión de f8586b5 contra 457ae17.

- Los seis criterios de aceptación pasan. CA-1a da 465 passed. En CA-3 la cobertura es del 100 %: `veracity` tiene 237 sentencias y 112 ramas.
- La edición de T03 se ajusta a lo autorizado por E-7: solo cambian `TERMINOS_DE_C8` y la prueba renombrada. El rojo con un término de menos y con uno de más se reproduce.
- **Mutación:**
  - `scan_cases.py`: 382 mutantes, con 3 vivos, todos equivalentes.
  - `veracity.py`: 502 mutantes, con 2 vivos, también equivalentes.
- **Corrección a la ronda 1:** el mutante `+ 2` de `scan_cases.py:263` era equivalente.

| Ronda 1 | Estado |
|---|---|
| F-01 | Parcial (R2-01) |
| F-02 | Cerrado |
| F-03 | Cerrado |
| F-04 | Cerrado |
| F-05 | Cerrado por E-7 |

## Hallazgos

### R2-01 · NARANJA · `veracity.py:122-128`: BR3.3 se rodea con dígitos y con un punto

Los nombres `falso2`, `es2falso`, `falso2x`, `FALSO2`, `es.falso`, `HTTPFALSO`, `EsEngaÑo` y `esＦａｌｓｏ` (ancho completo) dan False. Un campo `es_falso2` pasa la guardia.

**Corrección:** partir también en la frontera entre letra y dígito y en el punto. `HTTPFALSO` y las mayúsculas a mitad de palabra pueden quedar como limitación declarada.

### R2-02 · NARANJA · `docs/loop/bitacoras/U01-T11.md:70-91`: el rojo no se reproduce

La bitácora dice «26 failed», todos por aserción. Al repetirlo salen 31 failed: aparecen un `KeyError`, un `AttributeError` y cuatro `TypeError`, en pruebas que no figuran en ese rojo.

### R2-03 · AMARILLO · Para el humano: variantes de VE-02

Están los 7 términos, pero solo con variantes de género y número. Faltan las formas verbales: «mienten», «mintieron», «inculpan», «inculpó», «inculpar», «pruebe» y «engañó». VE-02 dice «con sus variantes», y E14 las declara como limitación.

### R2-04 · AMARILLO · BR3.2 y `$ref`

Pedir el enum en línea se justifica por contract-summary: C19 en las líneas 2474-2512 y C1 `papel` en la línea 444. Aun así, FD-U1-11 prefiere `$ref` por `$id`. Se sugiere aceptar también un `$ref` que resuelva a la ruta de C6.

### R2-05 · AMARILLO · Detalles

- El id `termino-enganos-sin-tilde` lleva un texto con tilde.
- «prueba» aparece en *fixtures* de otras tareas (`modelo-juez-prueba`), pero no en ningún contrato.

## Candidata

- Si los nombres de modelo llegan al reporte consolidado que se escanea, *fixtures* como `modelo-juez-prueba` harían fallar el escaneo.
