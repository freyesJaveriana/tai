# U01-T25: repositorio público (R-1 a R-3)

> El orquestador llenó esta tarea a partir del cambio 05 de la app, §4 (decisión E-32 del humano, 2026-11-24). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan:** ninguno; es el cambio 05. T22 (paso 24) conecta después en la CI el script de R-3. No cambia ningún comando de verificación del plan.
**Historias que implementa:** ninguna.
**Depende de:** nada pendiente. Va en la ola 10b, en paralelo con T20.

---

## Alcance

**Dentro:**

> **R-1.** Añade `resultados/` y `resultados-locales/` al `.gitignore` raíz, en el bloque propio del proyecto. No toques el bloque `AI-DLC:gitignore`. Lo pide `veridicus-01` §7.
>
> **R-2.** En los archivos versionados de `docs/validacion-zine/`, cambia por variables lo que dice dónde vive el trabajo en el clúster:
> - **Qué se cambia:**
>   - la ruta base `/zine/HPC02S1/freyes/tg4L` y las que cuelgan de ella;
>   - el usuario del clúster;
>   - los nombres de nodos (`hpchead02` y cualquier otro).
> - **Variables:** `ZINE_BASE` y `ZINE_USUARIO`, y `ZINE_NODO` si hace falta para los nodos. Se fijan al enviar (`enviar.ps1`) o al lanzar.
> - **Los `#SBATCH` no expanden variables.** Para `--output`, usa una ruta relativa al directorio desde el que se lanza, que el README fija como `ZINE_BASE/validacion`. Pasa `--nodelist` en la línea de `sbatch` que el README muestra, no en la directiva.
> - **README:** un ejemplo genérico que fija las variables y muestra cómo se lanza, como texto para el humano. Nada de este repositorio lanza trabajos.
> - **`reporte.md` y `resumen_4l.py`:** las rutas pasan a la forma con la variable. Las cifras medidas no cambian.
> - **No se reescribe la historia de Git**, porque no son secretos.
>
> **R-3.**
> - **Comprobación única, sin publicar nada.** Calcula el SHA-256 de cada archivo bajo `/insumos` y compáralo con el de cada archivo versionado (`git ls-files`). La única coincidencia permitida son los dos esquemas de C6 en `contracts/analyzer/v1/`. Deja la evidencia en la bitácora: cuántos archivos se compararon y qué coincidencias hubo, **solo con rutas y huellas, sin contenido**.
> - **Guardia permanente:** `scripts/check-no-insumos.sh RAIZ`, al estilo de `scripts/check-no-cluster-apply.sh`.
>   - Falla, nombrando cada archivo, si un archivo versionado contiene la cadena `/insumos/` fuera de una lista cerrada de exenciones.
>   - Esa lista está declarada en el script, con su motivo: `aidlc/`, `docs/` y `plan-aidlc.md`. Son documentación que cita de dónde vino un insumo, y los artefactos aprobados no se editan.
>   - Imprime `N apariciones` y termina con código 0 solo si `N` es 0.
>   - **Control negativo:** un repositorio de prueba en el scratchpad, con un archivo versionado fuera de las exenciones que contiene `/insumos/`, hace que el script dé código distinto de 0.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si la comprobación única encuentra otra coincidencia, aparte de los dos esquemas de C6.
- Si `git grep` encuentra `/insumos/` en un archivo versionado fuera de `aidlc/`, `docs/` y `plan-aidlc.md`.
- Si cambiar las rutas cambia lo que hace un script, más allá de leer la variable. También si un script de comprobación (`comprobar_reporte.py`) depende de una ruta literal.
- Si encuentras el usuario o la ruta del clúster en un archivo versionado fuera de `docs/validacion-zine/`. Hay al menos dos en `inception/user-stories/stories.md` (líneas 714 y 723), que es un artefacto aprobado: no lo edites, solo nómbralo.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Ejecutar** `sbatch`, `ssh`, `scp`, `rsync` o `enviar.ps1`, contra el clúster o contra cualquier otro destino (AUTONOMIA-01).
- **Leer o copiar contenido de `/insumos`:** solo se calculan huellas.
- **La CI:** `.github/workflows/` lo hace T22.
- **`contracts/`.**
- **Los artefactos aprobados de `aidlc/`.**
- **La historia de Git.**

---

## Archivos de contexto

- `/insumos/app/cambios/veridicus-05_etiquetas_y_repositorio_publico.md` §4: solo lectura.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-32.
- `docs/validacion-zine/` (todos sus archivos versionados), `.gitignore` y `scripts/check-no-cluster-apply.sh` (como modelo).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: R-1.
  ```bash
  git -C /workspace/.worktrees/U01-T25 check-ignore -v resultados/x resultados-locales/x
  ```
  Esperado: las dos rutas ignoradas por las líneas nuevas del `.gitignore`.

- [ ] **CA-2**: R-2, sin usuario, rutas ni nodos del clúster.
  ```bash
  git -C /workspace/.worktrees/U01-T25 grep -n -i -I -E "freyes|HPC02S1|hpchead" -- docs/validacion-zine
  ```
  Esperado: sin salida (código 1).

- [ ] **CA-3**: los scripts siguen siendo sintácticamente válidos. Corre `bash -n` sobre `comun.sh` y sobre cada `.sbatch`, un archivo por llamada, y `python -m py_compile` sobre cada `.py` de `docs/validacion-zine/`.
  Esperado: código 0 en todos.

- [ ] **CA-4**: R-3, la guardia sobre el repositorio.
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T25
  ```
  Esperado: `0 apariciones`, con código 0.

- [ ] **CA-5**: R-3, el control negativo sobre el repositorio de prueba del scratchpad (el codificador nombra la ruta en la bitácora).
  Esperado: código distinto de 0, con el archivo nombrado.

- [ ] **CA-6**: sin cambios al clúster y diff acotado.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  ```bash
  git -C /workspace/.worktrees/U01-T25 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado:
  - `0 apariciones`;
  - en el diff, solo `.gitignore`, archivos de `docs/validacion-zine/`, `scripts/check-no-insumos.sh` y `docs/loop/bitacoras/U01-T25.md`.

---

## Plan de pruebas

1. Escribe primero `scripts/check-no-insumos.sh` como esqueleto que siempre da 0.
2. Corre el control negativo (CA-5) y pega su salida **literal y completa** en `docs/loop/bitacoras/U01-T25.md`. Es el rojo: el esqueleto da 0 donde debía fallar.
3. Implementa hasta que CA-4 y CA-5 den lo esperado.
4. R-1 y R-2 se verifican con CA-1 a CA-3, antes y después. Pega el CA-2 de antes, con sus apariciones, como evidencia del cambio.

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** ningún script lanza trabajos ni cambia el clúster; los `sbatch` los lanza el humano.
- **Proceso (`team.md`):** nunca copiar al repositorio nada del piloto ni de `/insumos`, salvo el contrato común y los ID de decisión.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- **Edita solo con Edit o Write.** El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write.
- Cita en la bitácora solo los SHA vigentes. Si un rebase los reescribe, márcalos como reescritos en la misma línea.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas, **en los comandos que corres**. Los scripts que escribes sí pueden usar variables. Usa `grep -P` con `\x24` y `\x60`.
- Conventional Commits en español, con alcance `docs` o `scripts`, por ejemplo `chore(scripts): guardia de rutas de insumos (U01-T25)`.
