# Ronda 2: U01-T25

VEREDICTO: VERDE

Rama `tarea/U01-T25` en f77720d, sobre fadeaa8. Corrí yo mismo los seis CA y todos pasan. F-01 a F-08 están resueltos y no queda ningún ROJO ni NARANJA. Quedan dos AMARILLO que no bloquean. Por E-40, este informe no nombra la ruta, el usuario ni los nodos reales del clúster. No edité nada. El worktree ya venía con un `__pycache__` sin versionar (ver A-02).

> Nota del orquestador: en esta copia persistida, el patrón de CA-2 de la fila 2 se sustituyó por `<patrón de CA-2>`, porque nombra el usuario y los nodos reales (E-40). El resto es literal.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | R-1 | `git -C /workspace/.worktrees/U01-T25 check-ignore -v resultados/x resultados-locales/x` | pasa: `.gitignore:113` y `:114` |
| 2 | R-2 | `git -C … grep -n -i -I -E "<patrón de CA-2>" -- docs/validacion-zine` | pasa: sin salida, código 1 |
| 3 | sintaxis | `bash -n` sobre `comun.sh`, los 9 `.sbatch` y `scripts/check-no-insumos.sh`, uno por llamada; `py_compile` de los 6 `.py` (`comprobar_reporte`, `contar_tokens`, `resumen_4l`, `resumir_bench`, `sondeo_api` y `paquete_prueba/…/__init__.py`), con `cfile` en `…/scratchpad/pyc2/` | pasa: código 0 en todos |
| 4 | guardia sobre el repositorio | `bash /workspace/.worktrees/U01-T25/scripts/check-no-insumos.sh /workspace/.worktrees/U01-T25` | pasa: `0 apariciones`, código 0 |
| 5 | control negativo | `bash …/check-no-insumos.sh …/scratchpad/repo-neg` | pasa: código 1; nombra `bin/blob.dat`, el archivo no ASCII, `rara:dos.txt` y `servicio/leeme.txt`; da `4 apariciones (archivos)` y no nombra `docs/nota.md`, que está exento |
| 6 | sin cambios al clúster, diff acotado | `bash …/check-no-cluster-apply.sh /workspace/.worktrees/U01-T25` y `git -C … diff --name-only fadeaa8...HEAD` | pasa: `0 apariciones`; el diff solo trae `.gitignore`, `docs/validacion-zine/**` (16 archivos), `scripts/check-no-insumos.sh` y la bitácora |
| R-3 | huellas | `python3 -I -c` (solo SHA-256 de `/insumos` frente a `git ls-files -z`) | pasa: 533 archivos de insumos y 1306 versionados comparados. Exactamente las 5 coincidencias permitidas (2 de C6 y 3 de `docs/loop/` de E-35), con las huellas de E-35 |
| E-39 / P-T25-1 | expresión y reporte | `python3 -I -B …/comprobar_reporte.py --autoprueba` y `… reporte.md --revision` | pasa: `51 casos, el control negativo funciona` y `completo con la revisión` |
| cifras | `reporte.md` | `git -C … diff --word-diff=plain --word-diff-regex=[^[:space:]]+ -U0 fadeaa8...HEAD -- docs/validacion-zine/reporte.md` | pasa: ninguna cifra ni ID de trabajo cambió. M0 y M3 llevan `ZINE_NODO`; M1, M2, M4, M5 y M6 llevan `ZINE_NODO_SL250S` |

## Estado de F-01 a F-08
- **F-01 (ROJO): resuelto.** El caso de continuidad usa `hpc-nodo-ejemplo`. Mi grep ampliado (usuario, montaje, nodo de entrada, nodos de trabajo con `hpc0`, `w00N` y `sl250s-N`, `/home/` y `@`) sobre `docs/validacion-zine` y la bitácora solo da tres falsos positivos:
  - `comun.sh:8`: confirmo que es `HOME=` más un subdirectorio que cuelga de la variable `VALID`; no es una ruta real.
  - `enviar.ps1:5` y la bitácora, línea 56: el relleno genérico `usuario@servidor`.

  Sobre las 282 líneas añadidas del diff, el mismo patrón (más el alias del servidor) no encuentra nada.
- **F-02 (NARANJA): resuelto.** Sin `-I`, la sonda `rev-t25` nombra `bin/blob.dat`.
- **F-03: resuelto.** Con `-l -z` y lectura por NUL, `rev-t25` da 6 archivos, código 1. Salen tal cual el nombre con espacio, `nñ.txt` y `rara:dos.txt`. `docsx/n.md` y `plan-aidlc.mdx` siguen sin quedar exentos.
- **F-04: resuelto.** La sonda `rev-t25b`, con un archivo ilegible, da código 2 y el mensaje `FALLO al buscar`; nunca imprime `0 apariciones`. El script también falla cerrado ante cualquier código de git grep distinto de 0 y 1, o ante cualquier mensaje en stderr.
- **F-05: resuelto** según P-T25-1: la expresión es `\b(?:hpc[\w-]+|ZINE_NODO(?:_SL250S)?)\b`, hay un caso positivo nuevo en la autoprueba y el README explica los dos marcadores.
- **F-06: resuelto** según E-40: la bitácora queda abreviada y la salida completa está en el scratchpad.
- **F-07: resuelto.** La bitácora da 1306 archivos sobre la base fadeaa8, igual que mi corrida, y marca el conteo viejo como anterior a los rebases.
- **F-08: resuelto.** La viñeta de las entrevistas volvió a «Reglas que respetan los trabajos».

El rojo primero de esta ronda está en la bitácora: la autoprueba falló con `ZINE_NODO_SL250S` y el script viejo falló sobre `repo-neg` ampliado y sobre `repo-ilegible`.

Además, el script nuevo no usa nada que `check-no-cluster-apply.sh` rechace (da 0 apariciones sobre `scripts/`). `test_ci_workflows.py` solo revisa `.github/workflows`. «N apariciones» ahora cuenta archivos. Lo dice el encabezado del script, y CA-4 sigue imprimiendo `0 apariciones` literal.

## Hallazgos
### A-01 · AMARILLO · `docs/loop/bitacoras/U01-T25.md:50` · Conteo de archivos mal escrito
La bitácora dice «58 apariciones en 16 archivos (… y los 10 `.sbatch`)». La salida de CA-2 antes, que vi en la ronda 1, abarca 14 archivos: `README.md`, `comprobar_reporte.py`, `comun.sh`, `enviar.ps1`, `reporte.md` y los 9 `.sbatch`. Las 58 apariciones sí son correctas. No bloquea.

### A-02 · AMARILLO · worktree · `__pycache__` sin versionar
`docs/validacion-zine/__pycache__/comprobar_reporte.cpython-312.pyc` (fechado a las 18:00:58, 14 s después del commit f77720d) estaba en el worktree antes de que yo corriera nada. Seguramente salió de una autoprueba sin `-B`. No está en el diff ni lo ignora `.gitignore`, así que un `git add -A` lo metería. Es un defecto del bucle: el codificador debe borrarlo, y no lo toqué. No bloquea.

## Tareas candidatas (defectos reales fuera de alcance)
- Ninguna nueva. El alias de `enviar.ps1` y la guardia permanente para los nodos de trabajo quedan en K-68, fuera de esta revisión.

```
VEREDICTO: VERDE
AMARILLO|docs/loop/bitacoras/U01-T25.md:50|CA-2 antes: dice 16 archivos y 10 .sbatch; son 14 y 9
AMARILLO|worktree docs/validacion-zine/__pycache__/|Pyc sin versionar ni ignorar, dejado por el codificador (defecto del bucle)
INFORME: docs/loop/revisiones/U01-T25/ronda-2.md
```
