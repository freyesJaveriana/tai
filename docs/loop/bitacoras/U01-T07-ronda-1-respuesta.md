# U01-T07: respuesta a la ronda 1

F-01: Corregido en este commit: los cinco estados del catálogo según la tabla del informe (451, 503, 409, 422, 409) y prueba que los fija; ninguna fuente aprobada se contradice con otra en esos cinco.
F-02: Corregido en este commit: prueba de `comprobar()` sobre una copia en `tmp_path` con un defecto sembrado por subcomprobación (M17, M18, M22 y M23).
F-03: Corregido en este commit: el guardia exige base `<Familia>FamilyError` que herede de `VeridicusError`, con dos controles negativos; `_hojas()` de `libs/errors` ya no oculta las hojas fuera de la jerarquía.
F-04: Corregido en este commit: `anonymizer.incident` con `http: false` y sin estado, según P-T07-1.
F-05: Corregido en este commit: un `code` no textual da su propio mensaje (E31) y la prueba lo afirma.
F-06: Corregido en este commit: `dist/` en `libs/errors/.gitignore`.
F-07: Corregido en este commit: sección «Propuestas y vacíos» de la bitácora; solo `run.not_in_error` queda como propuesta sin fuente. El «antes» de las capas 2 y 3 no existe (no se corrió rojo previo) y se declara así en la bitácora.
