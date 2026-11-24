# U01-T18d — respuesta a la ronda 2

- F-04: Corregido en f60d902: `test_las_funciones_publicas_de_texto_no_tienen_cache` cuenta los análisis reales con `monkeypatch` (dobles de `loaders._lector_yaml` y de `json` dentro del módulo) y exige dos análisis para dos llamadas con el mismo texto. Rojo contra un mutante con caché en `load_yaml_text` (el `loaders.py` de 5cfd5b5) y contra otro solo de JSON, ambos por la regla y no por un import; las salidas literales están en la bitácora.
- F-05: Corregido en f60d902: la prueba ya no recibe `tmp_path`.
