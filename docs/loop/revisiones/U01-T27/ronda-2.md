# Ronda 2: U01-T27

VEREDICTO: VERDE

Los seis criterios pasan con mis propias corridas sobre a042bae, siempre con la raíz del worktree. F-01, F-02, F-03 y F-04 están resueltos y el rojo nuevo falla por la regla. No queda ningún ROJO ni NARANJA; solo dos AMARILLO que no bloquean, los dos sobre el *lookahead*.

Revisé HEAD `a042bae` (tarea/U01-T27) contra la base `885af74` (feat/b1-contratos). El worktree quedó limpio (`git -C /workspace/.worktrees/U01-T27 status --porcelain --untracked-files=all` no da salida). No ejecuté `enviar.ps1`, `sbatch`, `ssh` ni `scp`.

## Criterios de aceptación, verificados por mí
| # | Criterio | Comando que corrí | Resultado |
|---|---|---|---|
| 1 | La guardia sobre el repositorio | `bash /workspace/.worktrees/U01-T27/scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T27` | pasa: `0 apariciones`, código 0 |
| 2 | Control negativo | `bash <scratchpad>/neg.sh <caso> /workspace/.worktrees/U01-T27/scripts/check-no-cluster-ids.sh` con 12 casos | pasa: los 10 casos de ataque dan código 1 con `archivo:línea`; `base` y `usuario` dan 0 |
| 3 | Sin valor por defecto y con `ZINE_SERVIDOR` | `git -C /workspace/.worktrees/U01-T27 grep -n -P "\[string\]\s*\x24Servidor\s*=" -- docs/validacion-zine/enviar.ps1` y `git -C … grep -c ZINE_SERVIDOR -- …enviar.ps1 …README.md` | pasa: la primera no da salida; la segunda da `README.md:2` y `enviar.ps1:3` |
| 4 | Sintaxis | `bash -n /workspace/.worktrees/U01-T27/scripts/check-no-cluster-ids.sh` da 0; `which pwsh` da código 1 | pasa: `bash -n` da 0. Sin `pwsh`, revisé `enviar.ps1` leyéndolo |
| 5 | Las guardias existentes, `ci_workflows` y `yamllint` | `bash …/check-no-cluster-apply.sh /workspace/.worktrees/U01-T27`; `bash …/check-no-insumos.sh /workspace/.worktrees/U01-T27`; `timeout 60 uv run --frozen --offline --directory /workspace/.worktrees/U01-T27/contracts pytest tests/checks/test_ci_workflows.py --no-cov`; `uv run … yamllint -s …/.github/ …/.pre-commit-config.yaml` | pasa: 0 apariciones en las dos guardias, `79 passed`, `yamllint` con código 0 |
| 6 | El diff solo toca lo permitido | `git -C /workspace/.worktrees/U01-T27 diff --name-only feat/b1-contratos...HEAD` | pasa: los 5 archivos permitidos más `U01-T27-ronda-1-respuesta.md`, que aceptaste en el diff |

## Comprobaciones

### 1. El rojo falla por la regla
Extraje la guardia de la ronda 1 ya rebasada (`30a38a9`) a `<scratchpad>/rev2/r1/` y corrí los 12 casos de `neg.sh` contra ella y contra la guardia nueva.
- Con la guardia de la ronda 1, los seis casos nuevos dan 0: `mayus`, `tipo-mayus`, `sin-tipo`, `respaldo`, `otro-ps1` y `guion-bajo`.
- Con la guardia nueva, esos seis dan 1, cada uno con su `archivo:línea`.
- Los cuatro casos anteriores dan 1 con las dos guardias.
- `base` y `usuario` dan 0 con las dos.

### 2. Repetición de mis sondas de la ronda 1
Las corrí en `/tmp/claude-1000/-workspace/87e67c60-aa1c-4b11-8928-da89d2e300bd/scratchpad/rev2/p/<caso>`, con 47 repositorios de prueba y solo nombres inventados.

Ahora dan 1 todas las que antes daban 0, salvo los límites ya documentados:
- `HPC99-W999`, `HPCHEAD99` y `Hpc99-w999`;
- `nodo_hpc…`;
- `[String]$Servidor` y `$servidor`;
- un parámetro sin tipo;
- el tipo escrito en otra línea;
- un respaldo fijo en el cuerpo del script;
- el mismo parámetro en `otro.ps1` y en `sub/x.ps1`;
- un nombre en mayúsculas en otra línea de `comprobar_reporte.py`.

Siguen dando 1: los nodos entre comillas, `/zine/` dentro de una URL o tras `=`, un servidor por defecto con comillas dobles o con espacios, la línea exenta modificada, la línea exenta en otro archivo, un archivo con espacios en el nombre y un archivo en una subcarpeta.

Dan 0, como corresponde: los archivos sin versionar (también un `.ps1`), la carpeta de fuera y `xhpc99-w999`. Este último lo deja pasar a propósito el *lookbehind*. Los binarios también dan 0, como límite documentado.

### 3. El *lookahead* `(?!\x24)`
Probé valores que empiezan por `$`. Todos dan 0:
- `"$('servidor-inventado')"`, `"${a}servidor-inventado"` y `"$()servidor-inventado"`;
- `"$Servidor-x"`, que es un valor derivado y está bien que no cuente;
- `"$($env:ZINE_USUARIO)@servidor-inventado"` y `"$env:ZINE_USUARIO@servidor-inventado"`.

Fuera del *lookahead*, también dan 0:
- `$script:Servidor = '…'`, `${Servidor} = '…'` y `$Servidor ??= '…'`;
- la asignación indirecta `$s = '…'` seguida de `$Servidor = $s`;
- `Set-Variable -Name Servidor -Value '…'`;
- un `scp` con el host escrito en la misma línea.

Dan 1: la concatenación `'servidor' + '-inventado'` y `$Servidor="…"` sin espacios. No hay falsos positivos: `-eq 'x'` y `$Servidor = $env:ZINE_SERVIDOR` dan 0.

Riesgo real: la mayoría de estos casos exigen ofuscar a propósito, y lo que se pidió en (c) queda cubierto de sobra. Hay dos formas plausibles de volver a meter el servidor sin querer. Una es reescribir la línea 14 con el host fijo después de `@`. La otra es escribir el host directamente en el `scp` de la línea 31. Las dejo como AMARILLO.

### 4. La excepción sigue en la línea 121
`git -C … grep -n -i -I -P "(?<![A-Za-z0-9])hpc[\w-]+" -- docs/validacion-zine` da una sola línea, `comprobar_reporte.py:121`, que es la exenta. La excepción sigue atada al archivo y al texto exacto: la línea modificada y la línea copiada a otro archivo fallan. Una copia idéntica dentro del mismo archivo queda exenta, pero lleva el nombre inventado, así que es inofensiva.

### 5. Falsos positivos de `(?<![A-Za-z0-9])` con `-i`
- En `docs/validacion-zine/` no hay ninguno: solo aparece la línea exenta.
- En `enviar.ps1`, las líneas 7, 12 y 14 contienen `$Servidor` y ninguna salta; CA-1 da 0.
- Fuera de la carpeta, la versión sin distinguir mayúsculas solo añade un segmento de la ruta real del clúster: `stories.md` 2 líneas y `U01-T25-repositorio-publico.md` 2 líneas, más las citas de mi informe de la ronda 1. Es un acierto, no un falso positivo, y ya está registrado como candidata.

### 6. `enviar.ps1`, leído de nuevo
No cambió en la ronda 2: el diff contra la base es idéntico al de la ronda 1. El orden sigue siendo `-Servidor`, luego `ZINE_SERVIDOR` y, si no hay ninguno, `throw`, todo antes de crear `$tmp`. Si `ZINE_SERVIDOR` no está fijada, `[string]` la convierte en cadena vacía y el `throw` salta. El resto del script queda igual y no veo errores de sintaxis.

### 7. E-40
Busqué nombres reales en `U01-T27.md`, `U01-T27-ronda-1-respuesta.md`, `check-no-cluster-ids.sh` y los mensajes de los commits. Ninguno lleva nombres reales. La única coincidencia, `U01-T27.md:9`, es el nombre inventado `hpc99-w999`.

## Hallazgos
### F-05 · AMARILLO · scripts/check-no-cluster-ids.sh:57 · El *lookahead* deja pasar un host fijo después de una variable
`(?!\x24)` exime todo valor que empieza por `$`. Por eso `$Servidor = "$($env:ZINE_USUARIO)@servidor-inventado"` da 0, y es justo la forma en que alguien reescribiría la línea 14 con el host fijo.

Una regla más ajustada evitaría esto. Por ejemplo, eximir solo los valores formados únicamente por referencias a variables, o marcar todo literal de palabra que siga a `@` dentro del valor.

### F-06 · AMARILLO · scripts/check-no-cluster-ids.sh:57 · Un host escrito fuera de una asignación a `$Servidor` no se detecta
Pasan con 0:
- `scp … "servidor-inventado:$base/"`;
- `$script:Servidor`, `${Servidor}` y `??=`;
- la asignación indirecta y `Set-Variable`.

Esto queda fuera de lo que se pidió en (c). Si se quiere cerrar el caso más plausible, la propuesta es una regla para un host literal en el destino de `scp`.

## Tareas candidatas (defectos reales fuera de alcance)
- Sigue en pie la candidata de la ronda 1: hay nombres reales de nodos y la ruta del clúster en la base, fuera de `docs/validacion-zine/`.
  - `aidlc/…/inception/user-stories/stories.md`: 5 líneas;
  - `docs/devlog.md`: 3;
  - `docs/loop/tareas/U01-T25-repositorio-publico.md`: 2;
  - `decisiones-humano.md`: 1.

  La versión sin distinguir mayúsculas de la regla (a) encuentra además el segmento de la ruta en mayúsculas en `stories.md` (2 líneas) y en `U01-T25-repositorio-publico.md` (2).

```
VEREDICTO: VERDE
AMARILLO|scripts/check-no-cluster-ids.sh:57|El lookahead (?!\x24) deja pasar un host fijo tras una variable ("$($env:ZINE_USUARIO)@host")
AMARILLO|scripts/check-no-cluster-ids.sh:57|Un host fijo fuera de una asignación a $Servidor (scp directo, $script:, ${Servidor}, ??=, indirecto) no se detecta
INFORME: docs/loop/revisiones/U01-T27/ronda-2.md
```
