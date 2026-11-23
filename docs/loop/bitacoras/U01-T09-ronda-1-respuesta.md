F-01: Corregido: los nombres sobrantes salen de las claves de la instancia que el esquema no declara (y los faltantes de `required` del esquema), sin leer el mensaje; se retiró la expresión regular. Control con la clave `x'CANARY_ZXQ_7731'y`: sale `ajuste ?`.
F-02: Corregido: pruebas `test_una_clave_de_papel_sin_forma_segura_en_un_error_de_tipo_sale_como_interrogacion` (mutante 19) y `test_una_base_url_que_no_es_uri_se_rechaza_con_su_motivo` (mutante 27).
F-03: Corregido: `fallback_provider: true` en las `properties` del analizador; la prueba exige la tupla exacta de un solo problema.
F-04: Corregido: `additionalProperties: false` en el sobre de `profile-base`; control negativo con `extra_top` en `base` y `analyzer`, y positivo sin la clave.
F-05: Corregido: cinco pruebas de precios (metaesquema, caso válido, clave sobrante en raíz y en un precio, `minimum`, `pattern`, `$ref` al token, obligatorios y moneda).
F-06: Corregido: orden exacto por ruta (`permutation` antes de `purpose`), duplicados (un `purpose` ausente da un solo problema) y formato exacto de `str(error)`.
F-07: Corregido: motivos para `format`, `minimum` y `exclusiveMinimum`.
