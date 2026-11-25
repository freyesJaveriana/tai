# U01-T30: sin datos personales del autor en el repositorio público

> El orquestador redactó esta tarea a partir de la candidata K-75 (revisión de U01-T29, ronda 1) y de la decisión del humano del 2026-11-25 (K-75 = A). Es una correctiva. El humano la revisa antes de que se despache.
>
> **Este archivo, junto con lo que cita, es todo lo que el codificador necesita leer.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Precisa:** E-32 (repositorio público), K-75 y la precisión P-T30-1.
**Historias que implementa:** ninguna propia, porque U1 es `spec`.
**Depende de:** U01-T29 (#40), fusionada. Va sola. Se fusiona antes del PR del Bolt a `main`.

---

## Alcance

**El defecto (K-75).** El repositorio es público y tiene datos personales del autor. Las apariciones se citan solo como `archivo:línea`, sin el texto:
- `plan-aidlc.md:106`: un correo del autor.
- `research/06-documentacion-propia/Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md:30-31`: el correo institucional, el correo personal y un número de documento de identidad del autor.

**Dentro:**

> **1. Sustituir los datos** de esas tres líneas.
> - Cada correo pasa a ser `[correo del autor, omitido]`.
> - El documento pasa a ser `[documento de identidad, omitido]`.
> - Cambia solo esos datos. El nombre del autor, el resto del texto y el formato quedan iguales.
>
> **2. Guardia nueva, `scripts/check-no-datos-personales.sh`.** Revisa todos los archivos versionados (`git ls-files`, con `-I`) y falla nombrando `archivo:línea` (nunca el texto) en dos casos:
> - **(a) Documento de identidad:** una palabra de contexto seguida, a menos de 20 caracteres, de un número de 6 a 10 dígitos, con o sin puntos de miles. Las palabras de contexto son `C.C.`, `CC`, `cédula`, `cedula` y `documento de identidad`, sin distinguir mayúsculas.
> - **(b) Correos del autor:** cada correo que aparece en un archivo versionado se pasa a minúsculas y se calcula su SHA-256. La guardia falla si ese hash está en una lista cerrada del propio script.
>   - La lista lleva **solo hashes, nunca el correo**. Tiene un hash por correo del autor: el personal y el institucional.
>   - Calcula los hashes a partir de las líneas citadas **antes** de sustituirlas, sin imprimir el correo en ninguna salida, bitácora ni commit.
>   - El correo institucional también aparece en otros archivos, en el pie de los documentos del curso. P-T30-1 decide que ese uso se mantiene. Por eso el hash del correo institucional **solo** cuenta en las dos rutas de este alcance, `plan-aidlc.md` y `research/06-documentacion-propia/`. El hash del personal cuenta en todo el repositorio.
>
>   Los correos de autores de artículos de terceros en `research/` no cuentan.
> - **Control negativo** en el scratchpad, con repositorios de prueba y solo datos inventados. Debe dar 1:
>   - `C.C. 12.345.678`;
>   - `cédula: 1234567890`;
>   - un correo inventado cuyo hash se añade solo a la lista del control.
>
>   Debe dar 0:
>   - un año o una cifra sin palabra de contexto (`2026`, `1234567`);
>   - un correo inventado que no está en la lista.
>
> **3. `repo-level0.yml`:** un paso nuevo corre la guardia con la raíz `.`, justo después del de `check-no-cluster-ids.sh`. No lleva `uses:` ni cambia permisos.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si la guardia, antes de sustituir, encuentra algo que no está en la lista de arriba. Nómbralo con `archivo:línea` y no lo corrijas.
- Si la regla (a) marca falsos positivos en el repositorio que no se pueden evitar sin exenciones por carpeta.
- Si una línea con datos personales es también parte de un artefacto aprobado de `aidlc/`.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **La historia de Git**: no se reescribe (decisión K-75 = A). Por eso no se toca `.gitleaks.toml`: la CI corre `gitleaks git` sobre toda la historia, y una regla nueva fallaría por los commits ya publicados.
- **El nombre del autor**, la URL del repositorio y el correo institucional fuera de las dos rutas del alcance (P-T30-1).
- **Los artículos de terceros** de `research/`.
- **`contracts/`** y cualquier artefacto de `aidlc/`.

**Al escribir.** Ni en la bitácora, ni en los commits, ni en la tarea escribas un correo, un número de documento ni un hash completo del autor. Cita `archivo:línea` y la cuenta. Para un hash, basta con sus 8 primeros caracteres.

---

## Archivos de contexto

- `docs/loop/CANDIDATAS.md`: K-75.
- `decisiones-humano.md`: P-T30-1.
- `docs/loop/revisiones/U01-T29/ronda-1.md` y `ronda-2.md`: las candidatas.
- `scripts/check-no-cluster-ids.sh`, como modelo de guardia (estructura, salida `archivo:línea` y código).
- `.github/workflows/repo-level0.yml`.
- Las dos líneas y el archivo que se corrigen, solo en las líneas citadas.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1: la guardia sobre todo el repositorio.**
  ```bash
  bash scripts/check-no-datos-personales.sh /workspace/.worktrees/U01-T30
  ```
  Esperado: `0 apariciones` y código 0.

- [ ] **CA-2: control negativo.** El codificador nombra en la bitácora la ruta del control en el scratchpad y el comando de cada caso.
  Esperado: código 1 con `archivo:línea` en los casos de ataque, y código 0 en los dos casos sin falso positivo.

- [ ] **CA-3: solo cambian esos datos.**
  ```bash
  git -C /workspace/.worktrees/U01-T30 diff --word-diff=porcelain --unified=0 feat/b1-contratos...HEAD -- plan-aidlc.md research/06-documentacion-propia/Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md
  ```
  Esperado: solo `plan-aidlc.md:106` y las líneas 30 y 31 de la propuesta, y en ellas solo los datos sustituidos.

- [ ] **CA-4: sintaxis, guardias y CI.**
  ```bash
  bash -n scripts/check-no-datos-personales.sh
  ```
  ```bash
  bash scripts/check-no-cluster-ids.sh /workspace/.worktrees/U01-T30
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts yamllint -s -c /workspace/.worktrees/U01-T30/.yamllint.yaml /workspace/.worktrees/U01-T30/.github
  ```
  Esperado:
  - `bash -n` con código 0;
  - `0 apariciones` en la guardia de T29;
  - las pruebas en verde;
  - `yamllint` con código 0.

- [ ] **CA-5: el diff solo toca los archivos permitidos.**
  ```bash
  git -C /workspace/.worktrees/U01-T30 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo estos archivos:
  - `scripts/check-no-datos-personales.sh`
  - `.github/workflows/repo-level0.yml`
  - `plan-aidlc.md`
  - `research/06-documentacion-propia/Propuesta_TG_Dialogos_para_la_Memoria_MINSC_V2.md`
  - `docs/loop/bitacoras/U01-T30.md`

---

## Plan de pruebas

1. Escribe primero la guardia y el control negativo.
2. Corre CA-1 **antes** de sustituir. Debe fallar en las tres líneas citadas. Pega solo `archivo:línea` y la cuenta en `docs/loop/bitacoras/U01-T30.md`, siguiendo la regla 12.
3. Sustituye los datos hasta que CA-1 dé 0.
4. Si cambias la guardia después del rojo, repite el control negativo con el commit final.

---

## Reglas de la app que aplican

- **E-32:** el repositorio es público.
- **Proyecto, Forbidden:** nada de datos reales en el repositorio.
- **AUTONOMIA-02:** cada criterio tiene un comando.

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
- **Commits:** Conventional Commits en español. Por ejemplo: `fix(docs): quita datos personales del autor del repositorio público (U01-T30, K-75)`.
