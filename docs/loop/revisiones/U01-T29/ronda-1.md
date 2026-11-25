# Ronda 1: U01-T29

VEREDICTO: NO-VERDE

La guardia no detecta el `scp` más habitual, el que lleva una ruta remota absoluta (`host:/ruta`). Ese es justo el defecto F-06 que esta tarea corrige. Todo lo demás pasa: CA-1, CA-3 a CA-6, las sustituciones de nombres y el alcance de K-74.

Material revisado: `tarea/U01-T29` en 9d900c0 sobre `feat/b1-contratos` f461fe6. El worktree quedó limpio al terminar (`git status --porcelain` vacío).

> Nota del orquestador (P-T29-2): en esta copia persistida, los nombres y rutas inventados de las sondas que la guardia detecta a propósito (líneas de exenciones, rutas, F-03 y nombres de archivo) se describen con palabras o con `<R>` y `<nodo-inventado>`, para que la guardia de todo el repositorio no salte sobre el propio informe. Los casos y los resultados son los mismos. El resto es literal.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| CA-1 | Guardia sobre todo el repositorio | `bash /workspace/.worktrees/U01-T29/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T29` | pasa: `0 apariciones`, código 0 |
| CA-2 | Control negativo | mi propio arnés en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev29/` (repos de prueba con la copia real de `enviar.ps1` y `comprobar_reporte.py`), con la guardia nueva y con la de f461fe6 | los casos literales de la tarea pasan; el alcance de F-06 no (F-01) |
| CA-3 | Ningún nombre real | `git -C /workspace/.worktrees/U01-T29 grep -c -i -I -P "(?<![A-Za-z0-9])hpc[\w-]+" -- .` y lo mismo con `-h -o` | pasa: 12 archivos y 41 coincidencias, todas de la lista inventada (`hpc99-w999`, `hpc-nodo-ejemplo`, `hpcNN-wNNN`, `hpchead99`, en cualquier caja) |
| CA-4 | `stories.md` solo cambia en esos nombres | `git … diff --word-diff=porcelain --unified=0 feat/b1-contratos...HEAD -- <4 archivos>` y `git … log --format=%h%x20%s --name-only feat/b1-contratos..HEAD` | pasa: solo 714, 723, 733, 735 y 736, y solo el nombre; un solo commit (f5df16f) que toca solo `stories.md` y cita E-45 |
| CA-5 | Sintaxis, guardias y CI | `bash -n …`, `check-no-cluster-apply.sh`, `check-no-insumos.sh`, `timeout 60 uv run … pytest tests/checks/test_ci_workflows.py --no-cov -q`, `uv run … yamllint -s -c …` | pasa: código 0, 0 apariciones en las dos guardias, 79 passed, yamllint código 0 |
| CA-6 | El diff solo toca los archivos permitidos | `git -C /workspace/.worktrees/U01-T29 diff --name-only feat/b1-contratos...HEAD` | pasa: exactamente los 8 archivos permitidos |

## Comprobaciones
- **Rojo reproducido contra la guardia de f461fe6** (sacada con `git show f461fe6:scripts/check-no-cluster-ids.sh`; no cambia respecto de a52a7fa, `diff --stat` vacío). Los seis casos de ataque nuevos dan 0 con esa guardia: `nodo-md`, `ruta-md`, `host-tras-var`, `scp-host`, `scp-usuario-host` y `no-exento`. Con la guardia nueva dan 1, con `archivo:línea`.
- **Exenciones por cadena: no tapan nombres no exentos.** Todos dan 1:
  - un exento pegado a otra cosa: el exento con una letra o un dígito al final, el exento unido con `-`, `.` o `_` a otro nombre inventado no exento, y el exento seguido de otro nombre inventado (siete casos);
  - un exento y un no exento en la misma línea;
  - un archivo con dos puntos en el nombre;
  - un `.yaml`.

  Los exentos en mayúsculas dan 0, como se espera.
- **Sin la exención por línea de `comprobar_reporte.py`**, un nombre no exento da 1 en los tres casos: sustituido en la línea 121, añadido a su lado o en otra línea (176).
- **Rutas** (`<R>` es la ruta absoluta de ejemplo bajo el montaje del clúster). Dan 1: `<R>` tras `~`, entre comillas dobles, entre comillas invertidas, tras `X=`, al inicio de línea, entre paréntesis y tras `host:`. Dan 0: las rutas relativas `./`, `../` y `docs/…` con ese segmento, la mención del patrón entre comillas invertidas y una URL con ese segmento.
- **`.ps1`.**
  - El `enviar.ps1` actual da 0.
  - Repetir la línea que antepone `ZINE_USUARIO` (`…@`+`Servidor`) da 0.
  - F-05 con concatenación y comilla simple da 1; F-05 en `docs/otra/otro.ps1` da 1.
  - Dan 1: `scp … servidor-inventado:~/x`, `SCP …` y el `scp` relativo en otro `.ps1`.
  - Sin falsos positivos: `scp C:\datos\x "{Servidor}:base/"` y `scp "{Servidor}:base/x" C:/local` dan 0.
- **Nombres reales sin exenciones (E-40, solo cuentas).**
  - `hpc…`: 0 nombres reales.
  - Segmento `/zine/` seguido de una palabra: 0.
  - El identificador del usuario: 15 archivos, de los que 13 son la URL del repositorio en GitHub o el correo del autor. Son el usuario de GitHub y la institución, que la tarea deja fuera. Los 2 restantes (`plan-aidlc.md:106` y `research/…/Propuesta_TG_…_V2.md:30-31`) llevan además datos personales del autor (ver candidatas). Ninguno es la ruta del clúster.
- **K-74.** El *pre-commit* usa `files: ^(contracts|libs)/` y la CI corre `ruff check` y `ruff format --check` en `contracts/` y `ruff check` en `libs/errors`. Hoy `libs/` solo contiene `libs/errors`, y `ruff format --check` y `ruff check` pasan sobre `libs/`. Por eso hoy cubren lo mismo.

## Hallazgos

### F-01 · ROJO · `scripts/check-no-cluster-ids.sh:96` · F-06 no cubre un destino `scp` con ruta remota absoluta
La expresión termina en `:(?![\\/])`. Esa parte excluye las unidades de Windows (`C:\`), pero también descarta todo `host:/ruta`, que es la forma más habitual de un destino `scp`.

| Caso del arnés | Línea probada | Guardia nueva |
|---|---|---|
| `c-f06-abs` | `scp -r -q val "servidor-inventado:/srv/x/"` | 0 |
| `c-f06-usuario-abs` | `… usuario-inv@servidor-inventado:/srv/x` | 0 |
| `c-f06-otro-ps1-abs` | `scp a servidor-inventado:/x` en `otro.ps1` | 0 |

Las tres deberían dar 1. El control del codificador solo probó `:base/` (relativo), así que no lo detectó. El comentario de la línea 17 dice que la guardia cubre cualquier «destino de host literal», y no es así.

Arreglo: excluir solo la letra de unidad suelta, por ejemplo con `(?<![A-Za-z])[A-Za-z]:[\\/]`. Hay que añadir los tres casos al control y mantener en 0 los dos casos sin falso positivo de Windows.

### F-02 · NARANJA · `scripts/check-no-cluster-ids.sh:95-96` · Un host literal que empieza por dígito (IP) pasa en F-05 y F-06
La tarea pide detectar un literal de palabra justo después de `@`, y la clase `\w` incluye los dígitos. La guardia usa `[A-Za-z]`.

| Caso del arnés | Línea probada | Guardia nueva |
|---|---|---|
| `c-f05-ip` | `Servidor = "u@10.1.2.3"` | 0 |
| `c-f06-ip` | `scp a 10.1.2.3:x` | 0 |

Las dos deberían dar 1. Una IP fija del clúster dice dónde vive el trabajo igual que un nombre de host (E-32).

### F-03 · AMARILLO · `scripts/check-no-cluster-ids.sh:84` · Variantes equivalentes de una ruta absoluta pasan
La ruta `<R>` con dos barras al inicio, con dos barras en medio o con un segmento `.` da 0, y Linux las resuelve igual que `<R>`. Solo aparecerían si alguien ofusca a propósito, así que no bloquea. Conviene un caso en el control, o documentarlo en «Límites conocidos».

### F-04 · AMARILLO · `scripts/check-no-cluster-ids.sh:92-97` · Otras formas de `.ps1` que escapan
- Un `scp` partido en dos líneas con continuación por comilla invertida da 0 (`c-f06-continuacion`).
- Un archivo `OTRO.PS1` en mayúsculas da 0: el *pathspec* `'*.ps1'` distingue mayúsculas, y tampoco cubre `.psm1`.
- Al menos la primera debería figurar en «Límites conocidos».

## Tareas candidatas (defectos reales fuera de alcance)
- **Asignación con ámbito.** La guardia no ve una asignación de `Servidor` con ámbito (`script:Servidor = '…'`, caso `c-scope`, 0 con las dos guardias). Viene de T27.
- **Nombres de archivo.** Un archivo versionado con un nombre de nodo en su ruta (`docs/<nodo-inventado>.md`) da 0, porque la guardia solo mira el contenido. Valdría añadir `git ls-files` a la regla (a).
- **Datos personales del autor fuera de la frontera del clúster.** `plan-aidlc.md:106` (correo) y `research/06-documentacion-propia/Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md:30-31` (correo institucional, correo personal y un documento de identidad) están en el repositorio público. Lo decide el humano. No los cito.
- **Comprobación de formato en `libs/`.** La CI no corre `ruff format --check` en `libs/errors`; el *pre-commit* sí la corre. Hoy no hay diferencia práctica, pero conviene igualarlo cuando `libs/` crezca.

```
VEREDICTO: NO-VERDE
ROJO|scripts/check-no-cluster-ids.sh:96|F-06 no cubre un destino scp con ruta remota absoluta (host:/ruta)
NARANJA|scripts/check-no-cluster-ids.sh:95-96|un host literal que empieza por dígito (IP) pasa en F-05 y F-06
AMARILLO|scripts/check-no-cluster-ids.sh:84|variantes //zine/, /zine// y /zine/./ pasan
AMARILLO|scripts/check-no-cluster-ids.sh:92-97|scp en varias líneas y extensión .PS1/.psm1 no se revisan
INFORME: docs/loop/revisiones/U01-T29/ronda-1.md
```
