# U01-T15, ronda 3: respuesta a la ronda 2

Rebasada sobre `feat/b1-contratos` (2a06d5b, con T15c y P-T15-6 y P-T15-7), sin conflictos. Rojo: `a8fb54a` (pruebas finales `d5dac0f` y `0fc4cb6`). Cambio: `842c13a`.

- F-01: Corregido en 2f30cda: `turn_max_chars` vuelve a `used_in: [C1, C2, C5]` y la aserción de `test_correcciones_t15b.py` queda como en la base. Con T15c, C2 marca `turn_max_chars` en la rama de refinamiento de `entrada`. La guardia ya sigue el `$ref` de C2 a C6 por `$id` (842c13a, P-T15-6) y da por bueno `turnos[].texto`; con un control negativo (C2 sin la rama de refinamiento da rojo en `turnos[].texto`). Al seguir el `$ref`, la guardia encuentra cinco textos de C6 sin marca en C2 (`entrevista`, `version_texto`, `constancia`, `constancia_mandato`, `perfil`): defecto real que no cubren E-16 ni E-17, informado como K-37 y dejado en rojo en `test_los_contratos_versionados_coinciden_con_el_catalogo`.
- F-02: Corregido en 842c13a: P-T15-7, el esquema de los valores de un mapa con `propertyNames.enum` debe tener `type` o `$ref`; controles negativos con `{description}` y con `{minLength: 0}`, y controles positivos con `type` en lista y con `$ref`.
- F-03: Corregido en a8fb54a y 0fc4cb6: el rojo va literal y completo en la bitácora, repetido con los archivos de prueba finales; los 10 rojos fallan por la regla (un `AttributeError` que quedaba se cambió por una aserción en 0fc4cb6). El control negativo de P-T15-5 por nivel falla por la regla (el hallazgo sobra o falta), no por `AttributeError`.
- F-04: Corregido: la bitácora cita solo los SHA vigentes después del rebase (sección «SHA vigentes»); `e44bed9` y `a5b1f32` ya no aparecen.
- K-37: Fuera de alcance: tarea candidata propuesta, en `docs/loop/CANDIDATAS.md` (decisión del humano: marcar los cinco textos en la rama de C2 o aceptar el tope de bytes del mensaje).
- K-38: Fuera de alcance: tarea candidata propuesta, en `docs/loop/CANDIDATAS.md` (esquema sin `type` bajo un objeto cerrado).
