# Ronda 2: U01-T29

VEREDICTO: VERDE

La ronda 2 corrige F-01 a F-04, y CA-1 a CA-6 pasan con mis propias ejecuciones sobre 0446890. Quedan cuatro observaciones AMARILLO que no bloquean. La fusión es tuya.

Revisé `tarea/U01-T29` en 0446890; su base de fusión con `feat/b1-contratos` es eb61418. El worktree quedó limpio al terminar (`git status --porcelain` sin salida).

Este informe sigue P-T29-2: cito las sondas por el nombre de su caso, sin escribir nodos no exentos ni rutas absolutas de ejemplo.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | La guardia sobre todo el repositorio | `bash /workspace/.worktrees/U01-T29/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T29` | pasa: `0 apariciones`, código 0 |
| CA-2 | Control negativo | mi arnés en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev29/repos2/`, con 69 casos y tres guardias: f461fe6 (T27), f571d1b (ronda 1 rebasada) y HEAD | pasa (detalle abajo) |
| CA-3 | Ningún nombre real | `git -C /workspace/.worktrees/U01-T29 grep -c -i -I -P "(?<![A-Za-z0-9])hpc[\w-]+" -- .` y lo mismo con `-h -o` | pasa: 13 archivos, 45 coincidencias, todas de la lista exenta (`hpc99-w999`, `hpc-nodo-ejemplo`, `hpcNN-wNNN`, `hpchead99`, en cualquier caja) |
| CA-4 | `stories.md` | `git … diff --stat feat/b1-contratos...HEAD -- …/stories.md` y `git … log --format=%h%x20%s feat/b1-contratos..HEAD -- …/stories.md` | pasa: 5+/5- en 714, 723, 733, 735 y 736, y solo el nombre; un solo commit, 3811075, que cita E-45 |
| CA-5 | Sintaxis, guardias y CI | `bash -n …`, `check-no-cluster-apply.sh …`, `check-no-insumos.sh …`, `timeout 60 uv run … pytest tests/checks/test_ci_workflows.py --no-cov -q`, `uv run … yamllint -s -c …` | pasa: código 0, 0 apariciones en las dos guardias, 79 passed, yamllint con código 0 |
| CA-6 | Archivos permitidos | `git -C /workspace/.worktrees/U01-T29 diff --name-only feat/b1-contratos...HEAD` | pasa: exactamente los 8 archivos permitidos |

## Comprobaciones
- **El rojo falla por la regla.** Con la guardia de la ronda 1 (f571d1b), los casos de F-01 a F-04 dan 0. Con HEAD dan 1, con `archivo:línea`. Mi columna r1 reproduce `ctl29/rojo-2.txt`: los 10 casos de ataque nuevos dan 0, y `url`, `win-origen` y `win-destino` dan 0.
- **F-01, destino `scp` con ruta remota absoluta: resuelto.** `c-f06-abs`, `c-f06-usuario-abs` y `c-f06-otro-ps1-abs` dan 1.
- **F-02, IP: resuelto.** `c-f05-ip`, `c-f06-ip`, `c-f06-ip-usuario-abs` y `c-f06-ip-abs-comillas` dan 1.
- **F-03, variantes de ruta: resuelto.**
  - Dan 1: `b-doble-inicio`, `b-triple-inicio`, `b-doble-medio`, `b-punto-medio`, `b-punto-barra-medio`, y siguen dando 1 tilde, comillas, comillas invertidas, inicio de línea, paréntesis y tras dos puntos.
  - Dan 0: `b-rel-punto`, `b-rel-ddot`, `b-rel-docs`, `b-rel-doble`, `b-mencion` y `b-mencion-doble`.
- **F-04, extensiones: resuelto.** `c-f06-ext-mayus` (.PS1), `c-f06-psm1` y `c-f06-psm1-mayus` dan 1. El `scp` partido en varias líneas (`c-f06-continuacion`) sigue dando 0, pero ahora está declarado en «Límites conocidos», como pedí.
- **Ronda 1 completa.** Las exenciones pegadas o combinadas, los tres casos de `comprobar_reporte.py` y los de T27 dan el mismo resultado que en la ronda 1.
- **Falsos positivos de los cambios.** Todos dan 0, como se espera:
  - las URL: `d-url-https` y `d-url-host-zine` (`http` y `https` con host o segmento zine);
  - la unidad de Windows como origen y como destino, con `\` y con `/`, en mayúscula o en minúscula y entre comillas: `e-win-*`, seis casos;
  - una versión con puntos tras `@` en un `.md`: `e-version-md` (las reglas de `scp` y de servidor solo miran `.ps1` y `.psm1`);
  - el `enviar.ps1` real (`e-real-enviar`) y la línea que antepone `ZINE_USUARIO` (`e-var-usuario`);
  - el repositorio entero (CA-1).
- **Búsqueda sin exenciones (solo cuentas, E-40):**
  - nodos `hpc…`: 0 reales;
  - ruta absoluta zine sin exención: 1 coincidencia, el comentario de ejemplo de URL de la propia guardia (línea 11), que no es del clúster;
  - el identificador del usuario: 15 archivos. 14 son la URL del repositorio en GitHub o el correo institucional, que quedan fuera de alcance. El restante es el correo personal de `research/…_V2.md`, ya registrado en K-75.
- **SHA de la bitácora.** En la línea 154, 9d900c0 aparece marcado como rebasado, como pide la tarea.

## Hallazgos
### F-05 · AMARILLO · `scripts/check-no-cluster-ids.sh:103` · Falsos positivos de la regla `scp` en `.ps1`
Fallan cerrados (marcan de más, no dejan pasar nada) y hoy no aparecen en el repositorio:
- **Nuevo en esta ronda**, porque el host puede empezar por dígito: una línea con la palabra `scp` y una hora (`e-hora-scp`) da 1.
- **Ya estaba en la ronda 1:**
  - un comentario con «palabra:» en la línea del `scp` (`e-comentario-scp`);
  - un destino que sale de una variable de entorno sin llaves seguida de dos puntos (`e-env-dest`).

### F-06 · AMARILLO · `scripts/check-no-cluster-ids.sh:90` · Una URL `file:` con tres barras hacia la carpeta zine no se detecta
`d-file-url` da 0, porque las barras van tras dos puntos y la regla las toma por una URL. Basta con un caso en el control o una línea en «Límites conocidos».

### F-07 · AMARILLO · `scripts/check-no-cluster-ids.sh:104` · Quedan formas sin cubrir en los scripts de PowerShell
- `.psd1` no se revisa (`c-f06-psd1`).
- Un host concatenado después de la `@` (`c-f05-concat`) no se detecta.
- La asignación con ámbito (`c-scope`) sigue sin verse; ya está en K-76.

### F-08 · AMARILLO · `docs/loop/bitacoras/U01-T29.md:152` · Contradicción de base en la bitácora
Dice «rebase sobre af5653e»; la base vigente es eb61418, y así lo dice la línea 308. Conviene unificarlo.

## Tareas candidatas (defectos reales fuera de alcance)
- K-75 y K-76 ya recogen los datos personales del autor, la asignación con ámbito, los nombres de archivo y `ruff format` en `libs/errors`. Se puede sumar a K-76 lo de F-05 a F-07: `.psd1`, el `scp` en varias líneas, la URL `file:` y el host concatenado tras `@`.

```
VEREDICTO: VERDE
AMARILLO|scripts/check-no-cluster-ids.sh:103|falsos positivos de la regla scp (hora, comentario con dos puntos, variable de entorno sin llaves)
AMARILLO|scripts/check-no-cluster-ids.sh:90|una URL file con tres barras hacia zine no se detecta
AMARILLO|scripts/check-no-cluster-ids.sh:104|.psd1, host concatenado tras @ y asignación con ámbito sin cubrir
AMARILLO|docs/loop/bitacoras/U01-T29.md:152|la bitácora cita af5653e como base; la vigente es eb61418
INFORME: docs/loop/revisiones/U01-T29/ronda-2.md
```
