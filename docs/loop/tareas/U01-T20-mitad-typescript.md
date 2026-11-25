# U01-T20: mitad TypeScript `contracts/ts/`

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 21 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T19, fusionada: `gen:check` corre `gen_ts --check`, y las pruebas leen `contracts/ts/generated/` y `contracts/fixtures/jcs-vectors.json`. Ola 10b.

---

## Alcance

**Dentro:**

> **Paquete `contracts/ts/`** (D13, security-design §4.14):
> - `package.json` con Node 22 en `engines` y los scripts `test`, `typecheck`, `lint` y `gen:check`; `.nvmrc` con `22`.
> - Dependencias fijadas en versión exacta: `ajv` (con `Ajv2020`), `ajv-formats`, `yaml`, `canonicalize`, `openapi-typescript`, `typescript`, `vitest`, `@vitest/coverage-v8`, `eslint` y lo mínimo que ESLint necesite para TypeScript. Verifica cada API en la documentación oficial por MCP.
> - `package-lock.json` generado con `npm --prefix contracts/ts install` (con red) y versionado. Nunca se edita a mano.
> - `tsconfig.json` estricto (`strict: true`, sin `any` implícito).
> - ESLint con `no-restricted-imports` que prohíbe importar `yaml` fuera de `src/loaders.ts`.
> - `vitest.config.ts` con cobertura v8 y umbral de 80 % de líneas, y un *setup* sin red: sustituye `globalThis.fetch`, `net.connect`, `net.createConnection`, `http.request`, `https.request` y `dns.lookup` por funciones que lanzan un error.
> - `gen:check` corre `uv run --frozen --offline --directory .. python -m veridicus_contracts.tools.gen_ts --check` y `openapi-typescript` sobre C1 comparando en memoria con `generated/`, sin escribir. Sale con código distinto de 0 si algo difiere.
>
> **Módulos en `contracts/ts/src/`:**
> - `loaders.ts`: carga YAML con `yaml` y `uniqueKeys: true`; una clave repetida es un error.
> - `registry.ts`: `Ajv2020` con `strict: true`, `allErrors: false`, `unicodeRegExp: true` y `ajv-formats`; cada esquema de `contracts/` con `addSchema` y base `https://veridicus.invalid/`, como `registry.py`; `addKeyword` solo con las extensiones `x-veridicus-*` de §4.6, ni una más.
> - `canonical.ts`: la huella SHA-256 de la forma JCS con `canonicalize`, como `canonical.sha256_jcs`.
> - Los tipos de C1 en `generated/`, generados con `openapi-typescript` desde `api/console.v2.yaml`. Conviven con los archivos que dejó `gen_ts` en T19, sin pisarlos.
>
> **Pruebas Vitest** en `contracts/ts/test/`:
> - **Mismos veredictos (NFR10.16):** recorren la misma lista de *fixtures* que Python (`contracts/**/fixtures/`, salvo los de forma YAML que solo valida Python, nombrados en una lista explícita con su motivo) y comparan cada resultado con su `expectation`. Un *fixture* que la mitad TypeScript no sabe validar es un fallo, no un salto.
> - **Carga estricta (BR1.9):** cada esquema de `contracts/` compila con ajv `strict`; un control negativo con una palabra clave desconocida falla.
> - **Vectores JCS:** las 200 huellas de `fixtures/jcs-vectors.json` coinciden, y también la de `effective-config.valid.json` (BR9.7).
> - **Sin red:** un `fetch` de control lanza el error del *setup*.
> - **C8:** un vocabulario con un término repetido se rechaza (clave repetida en `loaders.ts`).
> - **Extensiones:** un esquema con una extensión `x-veridicus-*` que no está en §4.6 falla al compilar.
>
> Cada decisión de forma que §4.14 no fije (nombres de archivos, versión exacta de cada dependencia, la lista de *fixtures* que solo valida Python) se anota en la bitácora como **P-T20-n**, con su fuente.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- Si `npm install` no tiene red. Pega la salida literal y para.
- Si una mitad da un veredicto distinto del `expectation` de un *fixture* (por ejemplo, un `pattern` que Python acepta y ajv con `unicodeRegExp` rechaza). Es un defecto de un contrato o de un *fixture*: lo informas con la ruta y no lo corriges.
- Si un esquema de `contracts/` no compila con ajv `strict`. Lo informas con la ruta y la palabra clave; no lo corriges ni relajas `strict`.
- Si `npm audit --audit-level=high` encuentra una vulnerabilidad `HIGH` o mayor con corrección. Lo informas; no subas de versión sin decirlo.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **La consola** (U4) y cualquier código fuera de `contracts/ts/`.
- **`tools/gen_ts.py` y los archivos que genera** (T19). Si `gen_ts` necesita un cambio, para y lo informas.
- **Editar contratos, *fixtures* o el catálogo.**
- **El *workflow* de la CI** (paso 24).
- **La mitad Python**: `pyproject.toml`, `uv.lock`, `src/`, `tests/`.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 21, la tabla de comandos (V-TS, V-TS-AUDIT) y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.6, §4.13 (pasos 8 a 11) y §4.14.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR1.9 y BR9.7.
- `contracts/src/veridicus_contracts/registry.py`, `loaders.py`, `canonical.py` y `checks/auth_surface.py` (solo lectura), como referencia de la mitad Python.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: V-TS.
  ```bash
  npm --prefix contracts/ts ci
  ```
  ```bash
  timeout 60 npm --prefix contracts/ts test
  ```
  ```bash
  npm --prefix contracts/ts run typecheck
  ```
  ```bash
  npm --prefix contracts/ts run lint
  ```
  ```bash
  npm --prefix contracts/ts run gen:check
  ```
  Esperado: `ci` termina sin error; `test` en verde en 60 s o menos con 80 % de líneas o más; `typecheck` y `lint` con 0 errores; `gen:check` sin diferencias.

- [ ] **CA-2**: V-TS-AUDIT (con red).
  ```bash
  npm --prefix contracts/ts audit --audit-level=high
  ```
  Esperado: 0 vulnerabilidades `HIGH` o mayores con corrección.

- [ ] **CA-3**: los veredictos coinciden con los de Python sobre los mismos *fixtures*.
  ```bash
  timeout 600 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde. La lista de *fixtures* que recorre Vitest es la misma que recorre la suite de Python, salvo la lista explícita de §4.14, y la bitácora muestra el recuento de las dos.

- [ ] **CA-4**: el diff solo toca `contracts/ts/` y la bitácora.
  ```bash
  git -C /workspace/.worktrees/U01-T20 diff --name-only feat/b1-contratos...HEAD
  ```
  Esperado: solo rutas bajo `contracts/ts/` (sin `node_modules/`) y `docs/loop/bitacoras/U01-T20.md`.

- [ ] **CA-5**: sin cambios al clúster.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Crea el esqueleto del paquete (`package.json`, `tsconfig.json`, `vitest.config.ts` con el *setup*) y escribe primero las pruebas Vitest.
2. Haz el commit de las pruebas, corre el rojo y pega la salida **literal y completa** en `docs/loop/bitacoras/U01-T20.md`.
3. Escribe los módulos y genera los tipos hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con los archivos del commit final y pega esa salida completa.

Cada rojo debe fallar por la regla que prueba, no por un error de importación ni por una precondición equivocada.

---

## Reglas de la app que aplican

- **AUTONOMIA-04 y NFR10.15:** la mitad TypeScript calcula la misma huella que Python, sin red.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- `node_modules/` no se versiona: `.gitignore` de la raíz ya lo cubre (línea 22).
- **Edita solo con Edit o Write**, también las pruebas. Los generados y `package-lock.json` salen de sus herramientas, nunca a mano. El único heredoc permitido es el anexo a la bitácora, con `cat >> RUTA <<'FIN'`, y la bitácora se crea con Write.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): mitad TypeScript de los contratos (U01-T20)`. Sin signo de dólar en el mensaje.
