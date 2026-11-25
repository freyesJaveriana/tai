# U01-T27: `docs/validacion-zine` sin servidor por defecto y con guardia permanente

> El orquestador redactó esta tarea a partir de la candidata K-68, que salió de la revisión 1 de U01-T25, y de la decisión E-44 del humano (2026-11-25). Es una correctiva. El humano la revisa antes de que se despache.
>
> **Este archivo, junto con lo que cita, es todo lo que el codificador necesita leer.** No va a leer el PRD.

- **Unidad:** U01: `contracts`
- **Bolt:** B1
- **Rama base:** `feat/b1-contratos`
- **Precisa:** E-32, el cambio 05 §4 (R-2), y las decisiones E-39, E-40 y P-T25-1.
- **Historias que implementa:** ninguna propia, porque U1 es `spec`.
- **Depende de:** U01-T25 y U01-T22, las dos fusionadas. Va en paralelo con U01-T28 porque no comparten archivos: esta tarea toca `repo-level0.yml` y T28 toca `contracts-level0.yml` y `.pre-commit-config.yaml`. Se fusiona antes del PR del Bolt a `main`.

---

## Alcance

**El defecto (K-68).**
- `docs/validacion-zine/enviar.ps1:6-7` trae como valor por defecto de `-Servidor` un alias que identifica a la institución. El repositorio es público.
- R-2 de T25 cambió por variables la ruta, el usuario y los nodos, pero no ese alias.
- El patrón de CA-2 de T25 solo se corrió una vez. Ninguna guardia permanente impide que vuelvan a entrar:
  - un nombre de nodo, sea de entrada o de trabajo;
  - una ruta absoluta del clúster;
  - un servidor fijo.

**Dentro:**

> **1. `docs/validacion-zine/enviar.ps1`.** `-Servidor` deja de tener valor por defecto.
> - El servidor sale de `-Servidor` o de la variable `ZINE_SERVIDOR`, en ese orden.
> - Si no hay ninguno de los dos, el script se detiene con un mensaje en español, igual que con `ZINE_BASE`.
> - El comentario de uso (línea 6) muestra un ejemplo genérico, sin el alias.
> - Nada más del script cambia de comportamiento.
>
> **2. `docs/validacion-zine/README.md`.** Añade `ZINE_SERVIDOR` al bloque de variables (líneas 26 a 29) y a la nota de Windows (línea 36), con un valor genérico.
>
> **3. Guardia permanente `scripts/check-no-cluster-ids.sh RAIZ`.** Sigue el estilo de `scripts/check-no-insumos.sh`: mismo formato de salida y mismo código de retorno.
> - **Archivos que mira:** los versionados (`git ls-files`) bajo `docs/validacion-zine/`.
> - **Falla, nombrando archivo y línea, si un archivo contiene:**
>   - (a) un nombre de nodo con la forma de E-39, `\bhpc[\w-]+`, sea nodo de entrada o de trabajo;
>   - (b) una ruta absoluta que empiece por `/zine/`;
>   - (c) en `enviar.ps1`, un parámetro `[string]$Servidor` con un valor por defecto.
> - **Una sola excepción, declarada en el script con su motivo:** la expresión de `comprobar_reporte.py` (E-39 y P-T25-1) y su `SAMPLE`. Existen para detectar esos nombres. Declara la excepción por archivo y por línea concreta, no por archivo entero, para que un nombre real en otra línea de ese archivo sí falle.
> - **Salida:** imprime `N apariciones` y termina con código 0 solo si `N` es 0.
> - **Control negativo:** un repositorio de prueba en el scratchpad con cuatro casos. Cada uno, por separado, hace que el script devuelva un código distinto de 0:
>   - un nodo de trabajo inventado con la forma `hpcNN-wNNN`;
>   - una ruta `/zine/…`;
>   - un `-Servidor` con valor por defecto;
>   - un nombre de nodo en `comprobar_reporte.py` fuera de la línea exenta.
>
> **4. `.github/workflows/repo-level0.yml`:** un paso nuevo, justo después del de `check-no-insumos.sh`, que corre `bash scripts/check-no-cluster-ids.sh .`.
> - El paso no lleva `uses:` ni cambia permisos, para que la guardia `ci_workflows` de T22b siga en 0.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si la guardia nueva encuentra hoy algún nombre, ruta o servidor en un archivo versionado de `docs/validacion-zine/` aparte del alias de `enviar.ps1`. Nómbralo y no lo corrijas.
- Si quitar el valor por defecto obliga a cambiar algo más de `enviar.ps1`, además de leer la variable.
- Si `comprobar_reporte.py` necesita cambiar para que la excepción quede acotada a su línea.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Ejecutar** `enviar.ps1`, `sbatch`, `ssh`, `scp` o `rsync`, contra el clúster o contra cualquier otro destino (AUTONOMIA-01). `enviar.ps1` solo se comprueba con un análisis de sintaxis, nunca se ejecuta.
- **La historia de Git**: no se reescribe.
- **Los artefactos aprobados de `aidlc/`**, `contracts/` y `contracts-level0.yml`, que son de T28.
- **Ampliar la guardia a otras carpetas.** Si encuentras el alias o un nodo fuera de `docs/validacion-zine/`, nómbralo en la bitácora como candidata.

**Al escribir:**
- **E-40:** ni en la bitácora ni en los mensajes de commit escribas el alias real, un nodo real, el usuario ni la ruta del clúster. Cita `archivo:línea` y el número de apariciones.
- En las pruebas y en el control negativo, usa solo nombres inventados.

---

## Archivos de contexto

- `docs/loop/CANDIDATAS.md`: K-68.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: E-32, E-39, E-40, P-T25-1 y E-44.
- `docs/loop/tareas/U01-T25-repositorio-publico.md`, que es el antecedente.
- `docs/validacion-zine/enviar.ps1`, `docs/validacion-zine/README.md` y `docs/validacion-zine/comprobar_reporte.py`.
- `scripts/check-no-insumos.sh`, como modelo.
- `.github/workflows/repo-level0.yml`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: la guardia sobre el repositorio.
  ```bash
  bash scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T27
  ```
  Esperado: `0 apariciones` y código 0.

- [ ] **CA-2**: el control negativo. El codificador nombra en la bitácora la ruta del repositorio de prueba en el scratchpad y el comando de cada caso.
  Esperado: código distinto de 0 en cada uno de los cuatro casos, con el archivo y la línea nombrados.

- [ ] **CA-3**: `enviar.ps1` sin valor por defecto.
  ```bash
  git -C /workspace/.worktrees/U01-T27 grep -n -P "\[string\]\s*\x24Servidor\s*=" -- docs/validacion-zine/enviar.ps1
  ```
  Esperado: sin salida (código 1). El parámetro ya no tiene valor por defecto. La línea que antepone `ZINE_USUARIO` puede seguir igual. Además, `ZINE_SERVIDOR` aparece en `enviar.ps1` y en el README:
  ```bash
  git -C /workspace/.worktrees/U01-T27 grep -c ZINE_SERVIDOR -- docs/validacion-zine/enviar.ps1 docs/validacion-zine/README.md
  ```

- [ ] **CA-4**: la sintaxis de lo tocado.
  ```bash
  bash -n scripts/check-no-cluster-ids.sh
  ```
  Si `pwsh` está instalado, analiza `enviar.ps1` con `[System.Management.Automation.Language.Parser]::ParseFile` y sin ejecutarlo. Si no está, dilo en la bitácora y deja la comprobación al revisor.
  Esperado: código 0.

- [ ] **CA-5**: las guardias existentes siguen en 0, y los *workflows* pasan la guardia de T22b.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  ```bash
  bash scripts/check-no-insumos.sh /workspace/.worktrees/U01-T27
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts yamllint -s /workspace/.worktrees/U01-T27/.github/ /workspace/.worktrees/U01-T27/.pre-commit-config.yaml
  ```
  Esperado: `0 apariciones` en las dos guardias, las pruebas en verde y `yamllint` con código 0.

- [ ] **CA-6**: el diff solo toca los archivos permitidos.
  ```bash
  git -C /workspace/.worktrees/U01-T27 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo `docs/validacion-zine/enviar.ps1`, `docs/validacion-zine/README.md`, `scripts/check-no-cluster-ids.sh`, `.github/workflows/repo-level0.yml` y `docs/loop/bitacoras/U01-T27.md`.

---

## Plan de pruebas

1. Escribe primero `scripts/check-no-cluster-ids.sh` como esqueleto que siempre da 0, y haz su commit.
2. Corre el control negativo (CA-2) contra el esqueleto y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T27.md`. Es el rojo: el esqueleto da 0 donde debía fallar.
3. Corre también CA-1 con el script final, **antes** de cambiar `enviar.ps1`. Debe fallar en `enviar.ps1`. Pega solo `archivo:línea` y la cuenta, nunca el alias (E-40).
4. Cambia `enviar.ps1` y el README hasta que CA-1 dé 0.
5. Si cambias el script después del rojo, vuelve a correr el control negativo con el commit final y pega esa salida completa.

---

## Reglas de la app que aplican

- **E-32 / R-2:** el repositorio es público y no dice dónde vive el trabajo en el clúster.
- **AUTONOMIA-01:** nada de este repositorio lanza trabajos ni envía archivos. El humano ejecuta `enviar.ps1`.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **E-40:** la evidencia con nombres reales se abrevia.

---

## Notas

- **Edita solo con Edit o Write.** No uses `git stash`.
- **Bitácora:** anexa siguiendo la regla 12. En un heredoc, ninguna línea puede empezar por `#`.
- **Bash:** solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
- **SHA:** cita en la bitácora solo los vigentes. Si un rebase reescribe alguno, márcalo en la misma línea.
- **Commits:** Conventional Commits en español con alcance `validacion-zine` o `ci`. Por ejemplo, `fix(validacion-zine): el servidor de enviar.ps1 sale de ZINE_SERVIDOR (U01-T27, K-68)`.
