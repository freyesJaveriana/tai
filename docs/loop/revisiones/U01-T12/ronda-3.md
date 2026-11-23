# Ronda 3: U01-T12

VEREDICTO: NO-VERDE

Revisión de 105adac contra 933b2d9.

- Los seis criterios de aceptación pasan.
  - CA-1: 248 passed.
  - CA-3: 316 sentencias y 166 ramas, cubiertas al 100 %.
- Quedan cerrados G-02, G-04 y el AMARILLO del Escenario A.
- C19 declara en línea los enum de C6 (BR3.2 de T11): `status`, `error_code` (6), `discards` (8) y `fact_type` (7). Son idénticos a la copia de C6.
- Portabilidad a ECMA, comprobada con `node -u`: los patrones del contrato compilan.

## Hallazgos

### H-01 · ROJO · `docs/loop/bitacoras/U01-T12.md:134-137`: el rojo no sale del archivo del commit

| | Fallos | Pruebas | Patrones |
|---|---|---|---|
| Bitácora | 80 | 245 | 27 |
| Archivo del commit | 79 | 244 | 26 |

### H-02 · NARANJA · `report_closed.py:178-202, 222`: una alternancia en el nivel superior burla el anclaje

`pattern` usa `search`. Por eso `^a|b$`, `^[a-z]{1,9}|x$` y `^a|$` aceptan frases con espacios, y `^a|$` acepta cualquier cadena.

**Corrección:** todo `|` debe ir dentro de un grupo.

### H-03 · NARANJA · `report_closed.py:46, 234-238`: un `allOf` con ramas abiertas cuenta como tipado

`{"allOf": [true]}`, `[{}]`, `[{"minimum": 0}]` y `prefixItems` con `unevaluatedItems: true` salen ciegos. La guardia no detecta ninguno.

**Corrección:** un nodo así queda abierto salvo que alguna rama lo cierre. Lo mismo vale para `anyOf` y `oneOf`.

### H-04 · NARANJA · `report.schema.v2.yaml:13-35`: `kind: evaluation` no exige `metrics`

NFR4.13 y cicd-pipeline §4.2 piden las métricas. Hoy, un reporte sin `metrics` o con `metrics: {}` se acepta.

### H-05 · NARANJA · `report_closed.py:58, 180`: dos mutantes vivos

- **p07:** un cuantificador de 4 cifras.
- **p14:** `lstrip` y `rstrip` sobre las anclas.

### AMARILLO

- La gramática admite patrones que no compilan, como `^(a$`, `^*a$` y `^a{2}{3}$`, y cuantificadores anidados, que abren la puerta a ReDoS.
- En Python, `$` acepta un salto de línea final (`todo-local\n`) y ECMA no.
- `role_families.verifier_permuted` puede ser distinto de `verifier`.
- `adversarial` no se cruza con `scenario_a_*`.
