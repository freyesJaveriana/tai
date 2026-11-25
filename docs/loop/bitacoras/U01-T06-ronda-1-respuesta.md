# U01-T06 — respuesta a la ronda 1

F-01: Corregido: `note` y `reformulation` de C7 llevan `minLength: 1` (BR4.4, P-T06-1); dos fixtures negativos nuevos (`dismissed-note-vacia`, `edited-reformulation-vacia`, `reject_reason: BR4.4`) y la guardia exige ambos campos no vacíos; rojo en la bitácora (8 fallos) y verde con 44 y 23 pruebas.
F-02: Corregido: prueba nueva `test_un_fixture_que_se_rechaza_por_otra_regla_queda_en_rojo` con `expectation: reject` y `reject_reason: BR4.1`; el mutante `!= REGLA and 0` ahora falla (`1 failed, 22 passed`); el módulo sigue en 8 funciones de prueba y 100 % de ramas.
F-03: Fuera de alcance: se deja como nota, sin cambios (`hecho` con `minLength: 1` sigue a contract-summary).
F-04: Corregido: el rojo completo de la ronda 2 está pegado en la bitácora (lista de fallos y causas).
