# Ronda 1: U01-T25

VEREDICTO: NO-VERDE

Hay un ROJO y un NARANJA. Corrí yo mismo los seis CA y todos pasan, pero R-2 sigue sin cumplirse en un punto que CA-2 no detecta, y la guardia de R-3 se salta los binarios sin avisar. No edité nada. El worktree queda limpio (`git status --porcelain --ignored` sin salida y sin `__pycache__`). El informe va aquí y no en disco, porque no tengo Write; lo guarda el orquestador en la ruta del bloque final.

## Criterios de aceptación, verificados por mí

| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | R-1 | `git -C /workspace/.worktrees/U01-T25 check-ignore -v resultados/x resultados-locales/x` | pasa: `.gitignore:113` y `:114`, fuera del bloque AI-DLC |
| 2 | R-2 (grep de la tarea) | `git -C … grep -n -i -I -E "<patrón de CA-2>" -- docs/validacion-zine` | pasa: sin salida, código 1. Pero ver F-01 |
| 3 | sintaxis | `bash -n` sobre `comun.sh` y los 9 `.sbatch`, uno por llamada; `py_compile` de los 6 `.py` con `cfile` en el scratchpad | pasa: código 0 en todos |
| 4 | guardia sobre el repositorio | `bash /workspace/.worktrees/U01-T25/scripts/check-no-insumos.sh /workspace/.worktrees/U01-T25` | pasa: `0 apariciones`, código 0 |
| 5 | control negativo | `bash …/check-no-insumos.sh …/scratchpad/repo-neg` | pasa: código 1, `archivo: servicio/leeme.txt`, `1 apariciones` |
| 6 | sin cambios al clúster, diff acotado | `bash …/check-no-cluster-apply.sh /workspace/.worktrees/U01-T25` y `git -C … diff --name-only feat/b1-contratos...HEAD` | pasa: `0 apariciones`; el diff solo trae `.gitignore`, `docs/validacion-zine/**`, `scripts/check-no-insumos.sh` y la bitácora |
| R-3 | huellas, comparación propia y completa | `python3 -I -c` con `os.walk('/insumos')` y `git ls-files -z`, solo SHA-256 | pasa: 533 archivos de insumos, 1305 versionados comparados, 0 errores. Exactamente 5 coincidencias, las de la lista cerrada (2 de C6 y 3 de `docs/loop/`); sus huellas cuadran con E-35 |
| E-39 | expresión y autoprueba | `python3 -I -B …/comprobar_reporte.py --autoprueba` y `… reporte.md --revision` | pasa: `51 casos, el control negativo funciona` y `completo con la revisión` |
| cifras | `reporte.md` | `git -C … diff --word-diff=plain --word-diff-regex=[^[:space:]]+ -U0 feat/b1-contratos...HEAD -- docs/validacion-zine/reporte.md` | pasa: ninguna cifra ni ID de trabajo cambió. Solo cambian las 7 líneas `Nodo:`, la ruta de la línea 5 (la pide R-2) y la prosa sobre el nodo de entrada de las líneas 34, 96 y 108 |

> Nota del orquestador: en esta copia persistida se omitieron los nombres reales de usuario, nodo y ruta del clúster que citaba el informe original, para no volver a publicarlos (F-06). El resto es literal.

Otras comprobaciones:
- **Exenciones:** las tres son de la raíz y exactas. `docsx/` y `plan-aidlc.mdx` no quedan exentos, y los nombres con espacios se detectan (lo probé en un repositorio del scratchpad, `rev-t25`).
- **Construcciones prohibidas:** `check-no-cluster-apply.sh` da 0 sobre `scripts/`. `test_ci_workflows.py` solo mira `.github/workflows`, así que el script nuevo no le afecta.
- **Lanzamiento:** el `--output` relativo es coherente. Toda línea de lanzamiento hace antes `cd "$ZINE_BASE/validacion"`, `enviar.ps1` crea `logs/`, los `--export` usan `ALL,` y conservan `ZINE_BASE`, y `--nodelist` va en la línea de `sbatch` de los 5 trabajos del nodo de entrada.

## Hallazgos

### F-01 · ROJO · `docs/validacion-zine/comprobar_reporte.py:121` · Queda el nombre de un nodo real
R-2 pide quitar «los nombres de nodos (el nodo de entrada y cualquier otro)». El caso de continuidad de la autoprueba usa el nombre de un nodo SL250s real: en la base, `m3-tokens.sbatch:9` lo tenía en `--nodelist`, y la ronda 1 lo quitó de ahí. E-39 solo pedía un caso positivo con `ZINE_NODO` y uno negativo, no este caso.

Lo encontré con un `git grep` ampliado sobre `docs/validacion-zine`, con patrones de nodos de trabajo, rutas del clúster, alias del servidor y `/home/`. Salida: una sola línea, `comprobar_reporte.py:121`, con `Nodo: <nodo SL250s real>`.

CA-2 no lo detecta porque su patrón no incluye los nodos de trabajo. Arreglo: un nombre ficticio que siga empezando por `hpc` (p. ej. `hpc-nodo-ejemplo`).

### F-02 · NARANJA · `scripts/check-no-insumos.sh:31` · Se salta los binarios sin avisar
Con `-I`, un archivo binario versionado que contenga la ruta de insumos no se detecta, y el script no lo dice al correr. El comentario «-I: sin binarios» lo declara, pero la salida no.

Prueba: en el repositorio `…/scratchpad/rev-t25`, `bin/blob.dat` lleva la ruta entre bytes nulos y no aparece entre los 5 archivos nombrados. Hay que quitar `-I` (git grep reporta «Binary file … matches») o contar y nombrar los binarios.

### F-03 · AMARILLO · `scripts/check-no-insumos.sh:41` · Nombres mal impresos en dos casos
- `cut -d: -f1` corta los nombres con dos puntos: `rara:dos.txt` sale como `archivo: rara`.
- Los nombres no ASCII salen entre comillas y con escapes (`"n\303\261.txt"`).

Con `git grep -l -z` (o `-c`) se arreglan los dos casos sin parsear la salida.

### F-04 · AMARILLO · `scripts/check-no-insumos.sh:31` · Pasa con archivos que no puede leer
Si un archivo versionado no se puede leer, git grep da `error: failed to stat` con código 1. El script lo toma por «sin coincidencias» e imprime `0 apariciones` con código 0 (lo probé con `chmod 0` en `…/scratchpad/rev-t25b`). Además, `|| true` taparía también un código 128. Lo seguro es tratar como fallo todo código distinto de 0 y 1.

### F-05 · AMARILLO · `docs/validacion-zine/reporte.md` (M1, M2, M4, M5, M6) · `Nodo:` dice algo falso
El README define `ZINE_NODO` como el nodo de entrada. Esas cinco mediciones corrieron en un SL250s, así que `Nodo: ZINE_NODO` ahora afirma algo que no pasó. E-39 aceptó perder el dato del nodo, no afirmar otro. Se puede poner `ZINE_NODO_SL250S`, o aclarar en el README que en `reporte.md` es un marcador neutro. Este caso necesitaría ampliar la expresión de E-39: lo decide el humano.

### F-06 · AMARILLO · `docs/loop/bitacoras/U01-T25.md` · La bitácora vuelve a publicar lo que R-2 quita
Un `grep -c` de la bitácora con el patrón de CA-2 ampliado a los nodos de trabajo da **65** líneas. Es el CA-2 de antes pegado literal, con la ruta, el usuario y los nodos reales. La tarea lo pedía («Pega el CA-2 de antes, con sus apariciones»), así que no es culpa del codificador. Pero choca con el fin de R-2 en un repositorio público. Lo decide el humano: abreviar la evidencia (p. ej. solo archivo:línea y el número de apariciones) o aceptarlo como en E-33 (3).

### F-07 · AMARILLO · bitácora, «R-3, comprobación única» · Conteo desactualizado
- La bitácora dice «1295 versionados (a 8377162)». Ese conteo es de antes del rebase; hoy son 1305. Las coincidencias no cambian, según mi corrida.
- 8377162 sigue siendo un ancestro de la rama base, así que no quedó reescrito; solo falta decir que el conteo es anterior al rebase.
- El «Acuse» cita la base 2e123ee, pero la rama ya está sobre 6fb34d7.

### F-08 · AMARILLO · `docs/validacion-zine/README.md:46` · Viñeta fuera de su lista
La sección nueva «## Variables» se metió dentro de la lista de reglas. La viñeta «Las entrevistas del piloto solo se copian al clúster…» quedó bajo «Variables».

## Tareas candidatas (defectos reales fuera de alcance)
- **Alias del servidor:** `enviar.ps1:6-7` trae como servidor por defecto un alias que identifica a la institución. R-2 no lo nombra (pide ruta, usuario y nodos); el humano decide si también pasa a variable.
- **Patrón de CA-2:** solo cubre el usuario, la máquina y el nodo de entrada. Una guardia permanente para `docs/validacion-zine` debería incluir también los nodos de trabajo.

```
VEREDICTO: NO-VERDE
ROJO|docs/validacion-zine/comprobar_reporte.py:121|Queda el nombre de un nodo real, contra R-2
NARANJA|scripts/check-no-insumos.sh:31|Se salta los binarios sin avisar (-I)
AMARILLO|scripts/check-no-insumos.sh:41|Nombres con dos puntos o no ASCII mal impresos
AMARILLO|scripts/check-no-insumos.sh:31|Pasa con 0 cuando no puede leer un archivo
AMARILLO|docs/validacion-zine/reporte.md|Nodo: ZINE_NODO dice nodo de entrada en mediciones hechas en un SL250s
AMARILLO|docs/loop/bitacoras/U01-T25.md|La bitácora vuelve a publicar ruta, usuario y nodos reales (lo pedía la tarea)
AMARILLO|docs/loop/bitacoras/U01-T25.md|Conteo de R-3 y SHA base anteriores al rebase
AMARILLO|docs/validacion-zine/README.md:46|Viñeta de las entrevistas quedó bajo «Variables»
INFORME: docs/loop/revisiones/U01-T25/ronda-1.md
```
