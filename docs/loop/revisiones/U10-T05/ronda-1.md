# Ronda 1 — U10-T05

**VEREDICTO: NO-VERDE.** Todos los comandos pasan, pero las sondas muestran dos problemas en la regla de `scp`: abre un hueco nuevo y deja sin arreglar dos de los tres falsos positivos reales de F-05. El worktree quedó limpio.

## Comandos (sobre el worktree)
- `pytest tests/checks/test_ci_workflows.py --no-cov -q` en `contracts`: 79 pasan (CG-U10-09).
- `check-no-cluster-apply.sh`: 0 apariciones.
- `scripts/tests/autoprueba-guardias.sh`: 10 de 10 sondas, 10 de 10 controles, código 0.
- CA-2: la autoprueba de `07927f6` contra las guardias de ese commit da código 1, con 4 de 10 sondas y 8 de 10 controles. Coincide con la bitácora.
- `check-no-cluster-ids.sh`, `check-no-datos-personales.sh` y `check-no-insumos.sh`: 0 apariciones cada uno.
- Suite con `--cov-fail-under=80`: 451 pasan, 99,53 % de líneas.
- `coverage_gate coverage.json`: código 0.
- `mypy --strict src tests`: sin problemas en 50 archivos. `ruff check .` y `ruff format --check .`: limpios; en `libs/errors`, también.
- `lint-imports`: 4 contratos se cumplen.
- `contracts` completo: 2919 pasan, 97,94 %.
- `demo_fake.py`: código 0; muestra solo marcas, la respuesta restaurada, `AnonymizerUnavailable` y `peticiones=0`.
- CA-6: `version = "0.1.0"`.
- `yamllint -s -c .yamllint.yaml .github`: sin salida. No hay `actionlint` instalado.

**CI:** está bien. `anonymizer-level0.yml` no tiene filtro de rutas, lleva `contents: read`, acciones fijadas por SHA, `persist-credentials: false` y ningún secreto. Corre la suite al 80 %, la compuerta sobre `coverage.json`, `lint-imports`, `ruff format --check`, mypy y pip-audit con su compuerta. `repo-level0.yml` corre la autoprueba.

**Sondas sintéticas que detectan bien:** asignación del servidor con ámbito global y de script en mayúscula; nombre de nodo inventado en una carpeta anidada y en un nombre de archivo en mayúscula; `.PSD1` en mayúscula y `.psd1` sin espacios; `file:` con cuatro barras y `FILE:` con un segmento punto; host literal concatenado tras la arroba, de dos formas; A-05 en tres formas (palabra de contexto con el número exento más punto y cifras, «C.C.» con un decimal, el número exento con puntos más otro grupo). Los controles de exento con punto de fin de frase y de `.psd1` con el valor tomado de una variable dan 0.

**La autoprueba sí falla si se rompe una guardia** (probado en copias del scratchpad): sin la regla de nombre en la ruta, sin el arreglo de A-05, con una guardia que siempre sale con 2 y con una que siempre sale con 1; en todos los casos, código 1.

## Hallazgos

### F-01 · ROJO · `scripts/check-no-cluster-ids.sh:137` · Regresión: el `scp` hacia un host literal sin ruta ya no se detecta
La nueva condición tras los dos puntos deja de ver destinos que la guardia de `8732623` sí veía. En las tres sondas, antes daba 1 y ahora da 0: copia hacia «usuario@host:» al final de la línea; destino «host:» entre comillas; «host: ruta», con espacio tras los dos puntos. La primera es un `scp` válido hacia la carpeta personal y deja el host escrito en un repositorio público. El comentario de la línea 128 todavía dice «con o sin ruta remota», y la línea 30 declara como límite conocido un hueco que abre este mismo diff.

**Corrección:** admitir que tras los dos puntos venga el fin de línea o una comilla de cierre. Para separar un mensaje de un destino, usar otra señal (por ejemplo, que «scp» sea el comando al inicio de la instrucción). Añadir a la autoprueba una sonda «host sin ruta» y otra entre comillas.

### F-02 · ROJO · paso 13, viñeta 2 · Los falsos positivos reales de F-05 siguen apareciendo, y la bitácora da un dato falso
`docs/loop/revisiones/U01-T29/ronda-2.md` sí está en el worktree; la bitácora (línea 29) dice que no. Los controles se escribieron para casos deducidos que no son los de F-05. Con las guardias actuales dan 1: una línea de `scp` con una hora («12:30»); un comentario con «palabra:x» sin espacio; un destino desde una variable de entorno sin llaves seguida de dos puntos, con o sin comillas. Solo dejó de salir el comentario con espacio tras los dos puntos.

**Corrección:** cerrar los tres casos de F-05 como los describe esa revisión y añadirlos como controles. Corregir la línea 29 de la bitácora.

### F-03 · NARANJA · `libs/anonymizer/src/veridicus_anonymizer/testing/coverage_gate.py:80-84` · Un archivo guardia que falta en el informe pasa por omisión
La compuerta solo exige algún archivo de cada grupo. Con el `coverage.json` real sin `domain/masking.py`, `evaluate` devolvió `[]`. Hoy `source=` informa también los archivos no importados, pero un `omit` futuro dejaría fuera un módulo guardia sin aviso.

**Corrección:** comparar el informe con la lista de archivos `.py` de cada grupo en `src/` y fallar si falta alguno. Añadir la prueba de «falta un archivo de un grupo que tiene otros».

### F-04 · AMARILLO · `docs/glosario.md` · Dos glosarios
Hay uno en `docs/glosario.md` y otro en `contracts/README.md:177`, y `team.md` pide «un glosario único». No hay ningún término traducido de dos formas. **Corrección:** mover el de `contracts` a `docs/glosario.md` y dejar un enlace.

### F-05 · AMARILLO · `libs/anonymizer/examples/demo_fake.py:89-91` · La demostración no muestra el cuerpo entero
El «cuerpo que saldría» es solo el texto de los turnos; falta, por ejemplo, `system`. **Corrección:** decir que es un extracto, o imprimir el cuerpo serializado completo.

**ML-14:** la fila de los falsos positivos de `scp` no se cumple (F-02). El resto de viñetas de los pasos 12 a 15 están cubiertas.

**README:** coincide con el código en `build_anonymizer(env, transport=None)`, los errores, el transporte (TLS 1.2, `retries=0`, `trust_env=False`, sin redirecciones), los nombres `VERIDICUS_*`, los límites de PD-2 y F-06, y F-10. La demostración usa solo `FakeTransport` y datos inventados.

```
VEREDICTO: NO-VERDE
ROJO|scripts/check-no-cluster-ids.sh:137|regresión: scp hacia host literal sin ruta, entre comillas o con espacio ya no se detecta
ROJO|paso 13 viñeta 2|los falsos positivos de F-05 (hora, palabra:x, variable de entorno sin llaves) siguen; la bitácora afirma que la revisión de T29 no estaba
NARANJA|libs/anonymizer/src/veridicus_anonymizer/testing/coverage_gate.py:80|un archivo guardia ausente del informe pasa si su grupo tiene otro
AMARILLO|docs/glosario.md:1|dos glosarios frente a «glosario único»
AMARILLO|libs/anonymizer/examples/demo_fake.py:89|el «cuerpo que saldría» es solo el texto de los turnos
INFORME: docs/loop/revisiones/U10-T05/ronda-1.md
```
