# Revisión acotada (arreglo corto A, ML-5) — U10-T05

**VEREDICTO: VERDE.** La regla de `scp` vuelve a ser la de `8732623`, detecta las 15 formas sintéticas probadas, los falsos positivos declarados ocurren tal como se describen y todos los criterios pasan. El worktree quedó limpio.

**1. Regla restaurada.** El patrón de `scp` en `scripts/check-no-cluster-ids.sh:143` es idéntico carácter por carácter al de `8732623`. En la guardia, el diff `393721c..606b2d8` solo toca esa línea y los comentarios (líneas 24 a 33 y 134 a 137); las demás diferencias con `8732623` (reglas de K-76) ya existían. `7795ae4` solo añade 7 líneas a la autoprueba: es el rojo.

**2. Sondas** (15 formas sintéticas, en un archivo temporal del worktree sin commit, con un host inventado): `sudo` delante; una asignación delante; una variable de entorno al estilo bash delante; dentro de `bash -c`; `wsl` delante; la ruta Linux del binario; la ruta Windows del binario, con operador de llamada y comillas y sin ellos; el nombre del comando entre comillas tras el operador de llamada; `Start-Process`; `Invoke-Expression`; `#` en el nombre del archivo; sin ruta remota; host entre comillas; espacio tras los dos puntos. La guardia da código 1 y marca las 15. Limpieza con `git rm --cached` y `git clean -f` limitados a esos archivos; `git status --short` vacío.

**3. Autoprueba.** 17 de 17 sondas y 10 de 10 controles, código 0; el mínimo de 7 y 7 sigue en `autoprueba-guardias.sh:142`. Los 6 controles retirados son exactamente los límites declarados (mensaje con dos puntos, URL, hora, comentario con palabra seguida de dos puntos y variable de entorno sin llaves, con comillas y sin ellas). Los 8 controles restantes (líneas 108 a 122) son legítimos. Las tres sondas nuevas (líneas 94 a 99) no son vacuas: con la regla de la ronda 2 daban 0 (rojo de `7795ae4`, 14 de 17), y ninguna otra regla las detecta. Mutante no verificado por ejecución (regla de 2026-11-25), solo por razonamiento.

**4. Comentarios.** Las 6 formas de «Límites conocidos» dan falso positivo como se declara, y las 2 líneas reescritas con llaves quedan limpias. El comentario de las líneas 134 a 137 describe el patrón real.

**5. Criterios.**

| Criterio | Comando | Resultado |
|---|---|---|
| CA-3 / guardias | las 4 guardias con raíz en el worktree y en `/workspace` | `0 apariciones` en las 8 corridas |
| CA-1 | `pytest tests/checks/test_ci_workflows.py --no-cov -q` en `contracts` | 79 pasan |
| CA-4 | suite del anonimizador con `--cov-branch --cov-fail-under=80` | 456 pasan, 99,54 % |
| CA-4 | `coverage_gate coverage.json` | código 0 |
| CA-4 | `mypy --strict src tests`, `ruff check .`, `ruff format --check .` | limpios |
| CA-4 | `lint-imports` | 4 contratos se cumplen |
| CA-4 | `contracts` completo | 2920 pasan, 97,94 % |
| CA-5 | `demo_fake.py` | código 0, `AnonymizerUnavailable` y `peticiones=0`, cuerpo solo con marcas |

Ningún umbral baja. Sin hallazgos ROJO ni NARANJA. K-87 sigue como candidata.

```
VEREDICTO: VERDE
INFORME: docs/loop/revisiones/U10-T05/ronda-3.md
```
