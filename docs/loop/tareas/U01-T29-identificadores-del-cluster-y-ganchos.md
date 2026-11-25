# U01-T29: sin identificadores del clúster en todo el repositorio y ganchos `ruff` acotados

> El orquestador redactó esta tarea a partir de las candidatas K-73 (revisiones de U01-T27), K-74 (revisión de U01-T28) y los hallazgos F-05 y F-06 de la ronda 2 de T27, y de la decisión E-45 del humano (2026-11-25). Es una correctiva. El humano la revisa antes de que se despache.
>
> **Este archivo, junto con lo que cita, es todo lo que el codificador necesita leer.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Precisa:** E-32, el cambio 05 §4 (R-2), y las decisiones E-39, E-40, E-44 y E-45.
**Historias que implementa:** ninguna propia, porque U1 es `spec`.
**Depende de:** U01-T27 (#39) y U01-T28 (#38), las dos fusionadas. Va sola. Se fusiona antes del PR del Bolt a `main`.

---

## Alcance

**Los defectos.**
- **K-73.** Hay nombres reales de nodos y una ruta absoluta del clúster con el usuario fuera de `docs/validacion-zine/`. La guardia de T27 solo mira esa carpeta. Estas son las apariciones que hay hoy; las cita como `archivo:línea` y sin el texto (E-40):
  - `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/stories.md`: 714 y 723 (ruta con usuario), 733, 735 y 736 (nodo de entrada). Es un artefacto **aprobado**. E-45 autoriza editarlo **solo** para sustituir esos nombres.
  - `docs/devlog.md`: 20, 23 y 25 (nodos).
  - `docs/loop/tareas/U01-T25-repositorio-publico.md`: 22, 24 y 77 (ruta, nodo y el patrón de CA-2).
  - `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: 49 (fila E-39, nodos).
- **F-05 y F-06 (ronda 2 de T27).**
  - La regla (c) exime todo valor que empieza por `$`, así que un host fijo detrás de una variable pasa: `"$(…)@servidor-inventado"`.
  - Un host fijo en el destino de un `scp` tampoco se detecta.
- **K-74.** Los ganchos `ruff-check` y `ruff-format` del *pre-commit* no tienen `files:`, así que abarcan todo el repositorio. La CI solo mira `contracts/` y `libs/`.

**Dentro:**

> **1. Sustituir los nombres** de las apariciones listadas por las variables del README de `docs/validacion-zine/`:
> - la ruta base, con lo que cuelga de ella → `ZINE_BASE/…`;
> - el usuario → `ZINE_USUARIO`;
> - el nodo de entrada → `ZINE_NODO`;
> - un nodo de trabajo → `ZINE_NODO_SL250S` si era un SL250s, o `ZINE_NODO_TRABAJO`.
>
> Reglas para la sustitución:
> - Cambia solo esos nombres. El resto del texto, las cifras y el formato quedan iguales.
> - **`stories.md` va en su propio commit**, con un mensaje que cite E-45: `docs(user-stories): sustituye identificadores del clúster por variables (E-45, K-73)`.
> - En la fila E-39 de `decisiones-humano.md`, cambia solo los dos nombres de la columna de contexto, por ejemplo por «el nodo de entrada y los nodos de trabajo reales».
> - En la tarea T25, el patrón de CA-2 (línea 77) pasa a describir lo que busca sin escribirlo literal. Por ejemplo: «el usuario, el segmento de la ruta base y el prefijo del nodo de entrada».
>
> **2. `scripts/check-no-cluster-ids.sh` revisa todo el repositorio.**
> - **Qué revisa:** todos los archivos versionados (`git ls-files`), no solo `docs/validacion-zine/`.
> - **(a) nodos:** igual que ahora, sin distinguir mayúsculas.
> - **(b) rutas:** en todo el repositorio, solo una ruta **absoluta** que empieza por `/zine/`, es decir, sin carácter de palabra, `.`, `-` ni `/` delante, y seguida de un carácter de palabra. Así, la mención del patrón entre comillas invertidas, como en esta tarea y en la de T27, no cuenta. Hay muchas rutas relativas del repositorio (`…/zine/paquete/` y otras) en artefactos de `incoherence-analyzer`, y esas no deben contar. Mide los falsos positivos sobre el repositorio y escríbelos en la bitácora.
> - **(c) servidor:** solo en `*.ps1`, como ahora, y además cubre F-05 y F-06:
>   - un valor de `$Servidor` que, aunque empiece por `$`, contenga un literal de palabra justo después de `@`;
>   - un destino de `scp` con un host literal (`palabra:` o `usuario@palabra:`) que no salga de una variable.
>   - La línea de `enviar.ps1` que antepone `ZINE_USUARIO` y su `scp` actual deben seguir dando 0.
> - **Exenciones:** una lista cerrada y declarada en el script, cada una con su motivo. Pueden ser dos cosas:
>   - **Nombres inventados.** Un conjunto fijo de cadenas permitidas, como `hpc99-w999`, `hpc-nodo-ejemplo` y `hpcNN-wNNN`, que se usan en tareas, bitácoras, controles negativos e informes. Se comparan como palabra completa y sin distinguir mayúsculas.
>   - **La línea de autoprueba de `comprobar_reporte.py`**, como ahora.
>
>   No se exime ninguna carpeta entera. Si un informe de revisión (`docs/loop/revisiones/`) contiene un patrón de búsqueda que coincide (por ejemplo, el prefijo del nodo de entrada seguido de `\d`), **para y avísame** con `archivo:línea`. Esos informes son copias literales y el orquestador decide.
> - **Control negativo:** los casos de T27 siguen fallando, y se añaden:
>   - un nodo real en un `.md` fuera de `docs/validacion-zine/`;
>   - una ruta absoluta `/zine/` en un `.md`;
>   - un `"$(…)@servidor-inventado"`;
>   - un `scp … servidor-inventado:…`;
>   - un nombre inventado **que no está** en la lista de exenciones;
>   - dos casos que deben dar 0: una ruta relativa `docs/zine/x` y la mención `` `/zine/` `` entre comillas invertidas.
>
> **3. `repo-level0.yml`:** el paso de la guardia pasa la raíz `.`, sin otros cambios.
>
> **4. `.pre-commit-config.yaml` (K-74):** `ruff-check` y `ruff-format` llevan `files: ^(contracts|libs)/`. También se actualiza el comentario.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si la guardia, ya ampliada, encuentra hoy en el repositorio algo que no está en la lista de arriba, que no es un nombre inventado y que no es un falso positivo evidente. Nómbralo con `archivo:línea` y no lo corrijas.
- Si un informe de `docs/loop/revisiones/` hace saltar la guardia.
- Si sustituir un nombre en `stories.md` obliga a cambiar algo más que ese nombre.
- Si la regla (b) no puede evitar los falsos positivos de las rutas relativas sin una exención por carpeta.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **La historia de Git**: no se reescribe (E-45).
- **Cualquier otro artefacto aprobado de `aidlc/`**. Solo `stories.md`, y solo esos nombres.
- **Las rutas relativas `…/zine/…`** de los artefactos de `incoherence-analyzer`, porque no son del clúster.
- **El nombre de la institución** como texto del curso, o en la URL del repositorio.
- **Ejecutar** `enviar.ps1`, `sbatch`, `ssh`, `scp` o `rsync` (AUTONOMIA-01).
- **`contracts/`**, salvo `scripts/` y `.pre-commit-config.yaml`.

**Al escribir.** Aplica **E-40**: ni en la bitácora, ni en los commits, ni en la tarea escribas un nombre real, el usuario ni la ruta. Cita `archivo:línea` y la cuenta. Usa solo los nombres inventados de la lista.

---

## Archivos de contexto

- `docs/loop/CANDIDATAS.md`: K-73 y K-74.
- `decisiones-humano.md`: E-39, E-40, E-44 y E-45.
- `docs/loop/revisiones/U01-T27/ronda-2.md`: F-05 y F-06.
- `docs/loop/tareas/U01-T27-servidor-y-nodos-de-zine.md`, el antecedente.
- `scripts/check-no-cluster-ids.sh`, `docs/validacion-zine/README.md` (las variables), `.github/workflows/repo-level0.yml` y `.pre-commit-config.yaml`.
- Los cuatro archivos que se corrigen, solo en las líneas citadas.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1: la guardia sobre todo el repositorio.**
  ```bash
  bash scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T29
  ```
  Esperado: `0 apariciones` y código 0.

- [ ] **CA-2: control negativo.** El codificador nombra en la bitácora la ruta del control en el scratchpad y el comando de cada caso.
  Esperado:
  - código distinto de 0 en cada caso de ataque, de T27 y nuevos, con `archivo:línea`;
  - código 0 en `base`, en `usuario` y en la ruta relativa.

- [ ] **CA-3: no queda ningún nombre real.** Corre la búsqueda (a) y (b) sin exenciones sobre el repositorio:
  ```bash
  git -C /workspace/.worktrees/U01-T29 grep -c -i -I -P "(?<![A-Za-z0-9])hpc[\w-]+" -- .
  ```
  Esperado: solo archivos con nombres inventados de la lista de exenciones o la línea exenta de `comprobar_reporte.py`. La bitácora clasifica cada archivo.

- [ ] **CA-4: `stories.md` solo cambia en esos nombres.**
  ```bash
  git -C /workspace/.worktrees/U01-T29 diff --stat feat/b1-contratos...HEAD -- aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/stories.md
  ```
  ```bash
  git -C /workspace/.worktrees/U01-T29 log --format=%s feat/b1-contratos..HEAD -- aidlc/spaces/default/intents/261002-veridicus-mvp/inception/user-stories/stories.md
  ```
  Esperado:
  - el diff toca solo las líneas 714, 723, 733, 735 y 736;
  - un solo commit, que cita E-45.

- [ ] **CA-5: sintaxis, guardias y CI.**
  ```bash
  bash -n scripts/check-no-cluster-ids.sh
  ```
  ```bash
  bash scripts/check-no-cluster-apply.sh /workspace/.worktrees/U01-T29
  ```
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T29
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts yamllint -s -c /workspace/.worktrees/U01-T29/.yamllint.yaml /workspace/.worktrees/U01-T29/.github /workspace/.worktrees/U01-T29/.pre-commit-config.yaml
  ```
  Esperado:
  - `bash -n` con código 0;
  - `0 apariciones` en las dos guardias;
  - las pruebas en verde;
  - `yamllint` con código 0.

- [ ] **CA-6: el diff solo toca los archivos permitidos.**
  ```bash
  git -C /workspace/.worktrees/U01-T29 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo estos archivos:
  - `scripts/check-no-cluster-ids.sh`
  - `.github/workflows/repo-level0.yml`
  - `.pre-commit-config.yaml`
  - `docs/devlog.md`
  - `docs/loop/tareas/U01-T25-repositorio-publico.md`
  - `stories.md`
  - `decisiones-humano.md`
  - `docs/loop/bitacoras/U01-T29.md`

---

## Plan de pruebas

1. Escribe primero el control negativo con los casos nuevos.
2. Córrelo contra la guardia de `feat/b1-contratos`, es decir, la de T27 tal como está. Los casos nuevos deben dar 0.
3. Pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T29.md`, siguiendo la regla 12.
4. Amplía la guardia y corre CA-1 **antes** de sustituir los nombres. Debe fallar en las apariciones listadas. Pega solo `archivo:línea` y la cuenta (E-40).
5. Sustituye los nombres, con `stories.md` en su propio commit, hasta que CA-1 dé 0.
6. Si cambias la guardia después del rojo, repite el control negativo con el commit final.

---

## Reglas de la app que aplican

- **E-32 / R-2:** el repositorio es público y no dice dónde vive el trabajo en el clúster.
- **E-45:** autoriza esta única edición de `stories.md`.
- **AUTONOMIA-01:** nada de este repositorio lanza trabajos ni envía archivos.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **E-40:** la evidencia que contenga nombres reales se abrevia.

---

## Notas

- **Edición:** solo con Edit o Write. No uses `git stash`.
- **Bitácora:**
  - anexa con la regla 12;
  - en un heredoc, ninguna línea puede empezar por `#`.
- **Bash:**
  - solo caracteres ASCII imprimibles;
  - nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas;
  - usa `grep -P` con `\x24` y `\x60`.
- **SHA:** cita solo los vigentes. Si un rebase reescribe alguno, márcalo en la misma línea.
- **Commits:** Conventional Commits en español, con alcance `ci`, `docs`, `loop` o `user-stories`. Por ejemplo: `fix(ci): la guardia de identificadores del clúster revisa todo el repositorio (U01-T29, K-73)`.
