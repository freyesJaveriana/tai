F-01: Corregido en el commit de la ronda 2: `build_registry` lanza `LoadError` "URI repetida" nombrando los dos archivos; pruebas con las dos grafías y con dos id idénticos, vistas en rojo antes.
F-02: Corregido en el commit de la ronda 2: `_uri_de` rechaza id vacío, con fragmento o con consulta (5 casos parametrizados, vistos en rojo antes).
F-03: Corregido en el commit de la ronda 2: la prueba de `../x`, `a/../../x` y `//example.com/x` exige el mensaje "sale de la base".
