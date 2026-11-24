# U01-T18d — respuesta a la ronda 1

- F-01: Corregido en el commit de la bitácora de la ronda 2 (el último de la rama, posterior a 687d002): el rojo exacto de CA-1 sobre la base (código 124) y las salidas completas de CA-1, CA-2, CA-3, CA-4 y CA-5 están pegadas literales; la medición con `--durations` quedó rotulada como medición; el conteo de CA-4 es 20 líneas, no 22.
- F-02: Corregido en 687d002 (sin reescribir): `load_yaml_text` y `load_json_text` ya no guardan nada; la caché vive en el ayudante privado `_analizado_de_archivo`, que solo usa `load_file`. Pruebas nuevas en `tests/test_loaders.py` (sin `cache_info` en las públicas y el ayudante no crece con ellas); rojo previo pegado en la bitácora.
- F-03: Corregido en 687d002: la copia por llamada sigue siendo profunda; el cambio de los alias de YAML y de la profundidad máxima queda aceptado por P-T18d-1. Prueba nueva de que mutar el resultado de `load_file` no cambia la lectura siguiente.
