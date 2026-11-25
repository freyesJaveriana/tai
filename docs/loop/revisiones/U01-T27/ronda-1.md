# Ronda 1: U01-T27

VEREDICTO: NO-VERDE

Los seis criterios pasan con mis propias ejecuciones y reproduje el rojo. Queda un NARANJA. La guardia nueva distingue mayúsculas y minúsculas, pero PowerShell y los nombres de host no. Por eso un `-Servidor` con valor por defecto escrito como `[String]` o como `servidor` pasa con 0, igual que un nodo en mayúsculas.

Revisé HEAD `35e6016` (tarea/U01-T27) contra la base `d2adcdf` (feat/b1-contratos). El worktree estaba limpio al terminar (`git -C /workspace/.worktrees/U01-T27 status --porcelain --untracked-files=all` sin salida). No ejecuté `enviar.ps1`, `sbatch`, `ssh` ni `scp`.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | La guardia sobre el repositorio da 0 | `bash /workspace/.worktrees/U01-T27/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T27` | pasa: `0 apariciones`, código 0 |
| 2 | Control negativo con 4 casos distintos de 0 | `bash <scratchpad>/neg.sh {nodo,ruta,servidor,nodo-en-comprobar,base} /workspace/.worktrees/U01-T27/scripts/check-no-cluster-ids.sh` | pasa: los 4 casos dan código 1 con `archivo:línea` (`comun.sh:2`, `comun.sh:2`, `enviar.ps1:1`, `comprobar_reporte.py:176`); el caso `base` da 0 |
| 3 | `-Servidor` sin valor por defecto y `ZINE_SERVIDOR` documentado | `git -C … grep -n -P "\[string\]\s*\x24Servidor\s*=" -- docs/validacion-zine/enviar.ps1` y `git -C … grep -c ZINE_SERVIDOR -- …enviar.ps1 …README.md` | pasa: la primera búsqueda no da salida; la segunda da `README.md:2` y `enviar.ps1:3` |
| 4 | Sintaxis | `bash -n /workspace/.worktrees/U01-T27/scripts/check-no-cluster-ids.sh` da 0; `which pwsh` da código 1 | pasa para el script de bash. `pwsh` tampoco está instalado aquí, así que revisé `enviar.ps1` leyéndolo (ver más abajo) |
| 5 | Las guardias existentes siguen en 0, `ci_workflows` y `yamllint` | `bash …/check-no-cluster-apply.sh /workspace/.worktrees/U01-T27`; `bash …/check-no-insumos.sh /workspace/.worktrees/U01-T27`; `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T27/contracts pytest tests/checks/test_ci_workflows.py --no-cov`; `uv run … yamllint -s …/.github/ …/.pre-commit-config.yaml` | pasa: 0 apariciones en las dos guardias, `79 passed`, `yamllint` con código 0 |
| 6 | El diff solo toca los archivos permitidos | `git -C /workspace/.worktrees/U01-T27 diff --name-only feat/b1-contratos...HEAD` | pasa: exactamente los 5 archivos permitidos |

## Comprobaciones
- **Rojo reproducido.** Saqué el esqueleto de `d6b1be1` con `git archive` a `<scratchpad>/rev/esq/` y corrí `neg.sh` sobre él. Los 4 casos dan `0 apariciones` y `codigo=0`, igual que la bitácora. El orden de los commits es correcto: esqueleto, luego guardia, luego corrección.
- **Sondas propias.** Las corrí en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev/p/<caso>`, con 28 repositorios de prueba y solo nombres inventados.
  - **Se detectan (código 1):**
    - nodos entre comillas dobles o simples;
    - `ZINE_NODO=hpc99-w999`;
    - `/zine/` dentro de una URL y después de `=`;
    - el servidor por defecto con comillas dobles y con espacios alrededor del `=`;
    - un nombre en otra línea de `comprobar_reporte.py`;
    - la línea exenta con texto añadido;
    - la línea exenta copiada a otro archivo;
    - un archivo con espacios en el nombre;
    - un archivo en una subcarpeta.
  - **No se detectan (código 0):**
    - `HPC99-W999`, `HPCHEAD99`, `Hpc99-w999`;
    - `[String]$Servidor = '…'` y `[string]$servidor = '…'`;
    - un parámetro sin `[string]`;
    - el tipo escrito en otra línea;
    - un valor de respaldo fijo en el cuerpo del script;
    - el mismo parámetro en otro `.ps1`;
    - `nodo_hpc99-w999` (el `\b` no corta después de `_`);
    - un archivo binario (se salta por `-I`);
    - un archivo sin versionar. Este es el resultado correcto: no debe contar.
- **La excepción no tapa nada más.** Compara el archivo y el texto exacto de la línea. Si el texto cambia, o la misma línea aparece en otro archivo, la guardia falla. Si esa línea se repite tal cual dentro del mismo archivo, también queda exenta, pero lleva un nombre inventado, así que es inofensivo. Un nombre de archivo con dos puntos no logra forjar la excepción, porque el texto queda con el prefijo del número de línea. Hoy la expresión de la línea 53 no coincide (después de `hpc` viene `[`), así que la excepción solo cubre la línea 121.
- **`enviar.ps1` (lectura, sin `pwsh`).** Las líneas 12 y 13 aplican el orden pedido: primero `-Servidor`, después `ZINE_SERVIDOR` y, si no hay ninguno, `throw` con un mensaje en español. El `throw` ocurre antes de crear `$tmp`, igual que en `ZINE_BASE`, así que no deja nada por limpiar. Si `ZINE_SERVIDOR` no está fijada, `[string]` la convierte en una cadena vacía y `-not` la toma como falsa: el comportamiento es correcto. `ZINE_USUARIO` antepone el usuario después de resolver el servidor. El resto del script no cambió, y no veo errores de sintaxis.
- **`repo-level0.yml`.** El paso nuevo va justo después del de `check-no-insumos.sh`, sin `uses:` y sin tocar permisos. `test_ci_workflows.py` incluye el `repo-level0.yml` real (línea 45) y pasa.
- **Fuera de la carpeta.** El alias aparece como nombre de la institución en muchos documentos del curso. No lo evalué, porque ahí no figura como servidor.

## Hallazgos
### F-01 · NARANJA · scripts/check-no-cluster-ids.sh:44-45 · La guardia distingue mayúsculas donde PowerShell y los nombres de host no
`buscar` usa `git grep -P` sin `-i`. PowerShell no distingue mayúsculas ni en los tipos ni en las variables, así que `param([String]$servidor = 'x')` es exactamente el caso (c) y pasa con 0. Las sondas `srv-String-mayus` y `srv-variable-minus` lo muestran. Con los nombres de host pasa lo mismo: `HPC99-W999` y `HPCHEAD99` también dan 0.

La guardia es permanente y su fin es que esto no vuelva a entrar. Corregirlo no cuesta nada: `git -C … grep -c -i -I -P "\bhpc[\w-]+|/zine/|\[string\]\s*\x24Servidor\s*=" -- docs/validacion-zine` sobre el repositorio de hoy da solo `comprobar_reporte.py:1`, que es la línea ya exenta. No aparecen falsos positivos nuevos.

La corrección sería aplicar `(?i)` o `-i` por lo menos a (a) y (c), y añadir un caso en mayúsculas al control negativo. El `/ZINE/` en mayúsculas no hace falta, porque las rutas de Linux sí distinguen mayúsculas.

### F-02 · AMARILLO · scripts/check-no-cluster-ids.sh:45 · (c) solo cubre la forma literal
Pasan con 0:
- un `$Servidor = '…'` sin tipo;
- `[string]` en una línea y `$Servidor = …` en la siguiente;
- un respaldo fijo en el cuerpo del script (`if (-not $Servidor) { $Servidor = '…' }`);
- el mismo parámetro en otro `.ps1` de la carpeta.

La tarea definió (c) en su forma literal, así que esto no bloquea. Ampliar el patrón a `\x24Servidor\s*=\s*['"]` en todos los `*.ps1` cerraría casi todos los casos.

### F-03 · AMARILLO · scripts/check-no-cluster-ids.sh:36,44 · Bordes menores de la búsqueda
- `\b` no detecta `nodo_hpc…`.
- `-I` salta los archivos binarios.
- Con un nombre de archivo que tiene dos puntos, la salida pierde el número de línea, aunque la aparición sí se cuenta.

### F-04 · AMARILLO · bitácora:89-90 · Evidencia de CA-5 tomada desde otro directorio
La salida pegada de `check-no-cluster-apply.sh` dice `./.github ./scripts`. El comando se corrió sin raíz y revisó el directorio de trabajo en que se lanzó, que no tiene por qué ser el worktree. El comando de la tarea tampoco lleva raíz.

Yo lo corrí con `/workspace/.worktrees/U01-T27` como raíz y da 0 apariciones, así que no cambia el resultado. Para próximas tareas, conviene pasar siempre la raíz.

## Tareas candidatas (defectos reales fuera de alcance)
- Hay nombres reales de nodos de entrada y de trabajo, y una ruta absoluta del clúster con el usuario, fuera de `docs/validacion-zine/`. Vienen de la base, no de este diff:
  - `aidlc/…/inception/user-stories/stories.md`: 5 líneas;
  - `docs/devlog.md`: 3;
  - `docs/loop/tareas/U01-T25-repositorio-publico.md`: 2;
  - `aidlc/…/contracts/code-generation/decisiones-humano.md`: 1, en la fila de E-39.

  Lo encontré con `git -C /workspace/.worktrees/U01-T27 grep -c -I -P "<patrón de los nodos y la ruta reales>" -- .`.

  > Nota del orquestador: el patrón de este comando se omitió en esta copia porque reproduce el prefijo de los nodos y el segmento de la ruta reales (E-40, P-T29-1). El resto del informe es literal. El repositorio es público (E-32). Que la guardia cubra esas carpetas, o que se corrijan los originales aprobados, lo decide el humano. La coincidencia en `docs/loop/bitacoras/U01-T27.md:9` es el nombre inventado `hpc99-w999`.

```
VEREDICTO: NO-VERDE
NARANJA|scripts/check-no-cluster-ids.sh:44-45|La guardia distingue mayúsculas donde PowerShell y los nombres de host no ([String]$servidor y HPC99-W999 pasan con 0)
AMARILLO|scripts/check-no-cluster-ids.sh:45|(c) solo cubre la forma literal (sin tipo, tipo en otra línea, respaldo en el cuerpo, otro .ps1)
AMARILLO|scripts/check-no-cluster-ids.sh:36,44|Bordes menores: \b tras _, -I salta binarios, nombre con dos puntos pierde la línea
AMARILLO|docs/loop/bitacoras/U01-T27.md:89-90|La evidencia de CA-5 de check-no-cluster-apply se tomó sin raíz, desde otro directorio
INFORME: docs/loop/revisiones/U01-T27/ronda-1.md
```
