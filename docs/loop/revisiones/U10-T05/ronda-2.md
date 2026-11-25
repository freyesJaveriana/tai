# Ronda 2 — U10-T05

**VEREDICTO: NO-VERDE.** F-03, F-04 y F-05 están cerrados, y CA-1 a CA-6 pasan con mis propias corridas. Pero el arreglo de F-01 y F-02 trae una regresión: la regla de `scp` deja de ver doce formas que la guardia base (`8732623`) sí veía, entre ellas las dos que pedía el encargo (con `sudo` y con una variable delante). El worktree quedó limpio.

## Comandos (en el worktree, en `393721c`)
- Hash de la tarea: `e2de17fa…`, coincide.
- `pytest tests/checks/test_ci_workflows.py --no-cov -q` en `contracts`: 79 pasan.
- `check-no-cluster-apply.sh`, `check-no-cluster-ids.sh`, `check-no-datos-personales.sh` y `check-no-insumos.sh`: 0 apariciones cada una.
- `autoprueba-guardias.sh`: 14 de 14 sondas y 16 de 16 controles, código 0.
- CA-2, rojo de la ronda: la autoprueba y las guardias de `f806172` dan código 1, con 10 de 13 sondas y 12 de 16 controles; fallan justo los 3 casos de F-01 y los 4 de F-02.
- Suite del anonimizador con `--cov-branch --cov-fail-under=80`: 456 pasan, 99,54 %. `coverage_gate` sobre `coverage.json`: código 0.
- `mypy --strict src tests`: sin problemas en 50 archivos. `ruff check .` y `ruff format --check .`: limpios. `lint-imports`: 4 contratos se cumplen.
- `contracts` completo: 2920 pasan, 97,94 %. `tests/test_readme.py`: 230 pasan.
- `demo_fake.py`: código 0. Imprime el cuerpo completo (`model`, `messages`, `output_config`, `system`) solo con marcas, `AnonymizerUnavailable` y `peticiones=0`. Usa `FakeTransport` y no abre red.
- `version = "0.1.0"`.
- **Umbrales:** ninguno baja.

## Mutantes (en copias del scratchpad, antes de la regla nueva de 2026-11-25)
Sin la regla de `scp`: 9 de 14 sondas. Sin la de `.psd1`: 13 de 14. Sin la de `file:`: 13 de 14. En los tres, código 1: la autoprueba sigue fallando cuando se rompe una guardia.

## Hallazgos

### F-01 · ROJO · `scripts/check-no-cluster-ids.sh:140` · El arreglo deja de ver doce formas de `scp` hacia un host literal
La condición nueva exige que `scp` esté al inicio de la instrucción (inicio de línea, o tras `; | & ( {`). De 36 sondas sintéticas, dan 0 con la guardia nueva y 1 con la de `8732623`: `sudo` delante; una asignación de variable delante; una variable de entorno al estilo bash delante; dentro de `bash -c "…"`; `wsl` delante; la ruta absoluta de Linux del binario; la ruta de Windows del binario, con `&` y comillas o sin ellas; `& "scp"` con el nombre entre comillas; `Start-Process scp -ArgumentList "…"`; `Invoke-Expression "scp …"`; un nombre de archivo con `#` antes del destino. Siguen dando 1 el resto: sin ruta, entre comillas, con espacio tras los dos puntos, con opciones, tras `;`, `&&` o `|`, con espacios al inicio, `scp.exe`, dentro de bloques, comillas simples, mayúsculas, la IP, el origen remoto y otras extensiones. Ni el comentario ni «Límites conocidos» lo declaran, y la autoprueba no tiene ninguna de esas formas.

**Corrección:** admitir antes de `scp` un prefijo de comando, una ruta del binario y comillas; añadir a la autoprueba al menos las sondas con `sudo`, con una variable delante y con una ruta absoluta.

### F-02 · AMARILLO · `scripts/check-no-cluster-ids.sh:140` · Falso positivo que queda en la línea de la copia
Los tres casos de F-05 de T29 están cerrados. Pero si en la misma línea, tras `;`, viene un mensaje con una palabra seguida de dos puntos, la guardia da 1. Falla cerrado y la base ya lo hacía. Basta con un control o una línea en «Límites conocidos».

### F-03 · cerrado
Las pruebas cubren un informe al que le falta un archivo de un grupo con otros y un archivo guardia de `src/` ausente del informe. `guard_files` solo lista los cinco grupos guardia; un archivo fuera de ellos no rompe la compuerta. Con el informe real, código 0.

### F-04 · cerrado, con observación AMARILLO · `contracts/README.md:177`
Un solo glosario, `docs/glosario.md`, sin términos repetidos; `contracts/README.md` deja el enlace y `test_readme.py` sigue probando algo real. **Observación:** `contracts/README.md` y `contracts/tests/test_readme.py` quedan fuera del «Dentro» literal de la tarea; lo pidió el F-04 de la ronda 1, así que no se cuenta como desborde.

### F-05 · cerrado
La demostración imprime el cuerpo serializado completo, solo con marcas, y `test_demo.py` lo comprueba.

```
VEREDICTO: NO-VERDE
ROJO|scripts/check-no-cluster-ids.sh:140|regresión: scp con sudo, variable delante, bash -c, wsl, ruta del binario, Start-Process, Invoke-Expression o # ya no se detecta
AMARILLO|scripts/check-no-cluster-ids.sh:140|falso positivo con «palabra:» tras ; en la línea del scp (falla cerrado, ya estaba en la base)
AMARILLO|contracts/README.md:177|cambio en contracts/ fuera del «Dentro» literal, pedido por el F-04 de la ronda 1
INFORME: docs/loop/revisiones/U10-T05/ronda-2.md
```
