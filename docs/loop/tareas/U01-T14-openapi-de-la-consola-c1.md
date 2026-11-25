# U01-T14: OpenAPI de la consola C1 v2

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 16, primera mitad (T14), de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T11, U01-T12 y U01-T13, fusionadas (ola 7). T15 depende de esta tarea (ola 8).

---

## Alcance

**Dentro:**

> - `contracts/api/console.v2.yaml` (C1) en OpenAPI 3.1.0, `info.version: 2.0.0`. Se transcribe del bloque de C1 de `contract-summary.md` (§C1, líneas 158 a 1194, incluida «Revisión 4 de C1 (resto)»), más PD-1 y PD-2:
>   - `ErrorCode` con un `enum` igual a los `code` del catálogo de errores v2 que salen por HTTP (`http: true`).
>   - `CsrfToken` con `minLength: 32`, y `X-CSRF-Token` en toda operación `POST` y `PATCH`.
>   - `x-veridicus-roles` en toda operación salvo `/auth/login`, `/auth/logout`, `/auth/me` y la lista pública. La lista pública es `POST /auth/login` y `GET /notice` (D-1). `401` y `403` con `$ref` a `Problem` según NFRD-U1-12.
>   - Solo las extensiones cerradas de §4.6: `x-veridicus-roles`, `x-veridicus-owner-only`, `x-veridicus-owner-only-for-role`, `x-veridicus-access-log`, `x-veridicus-demo`, `x-veridicus-priority`, `x-veridicus-limit`, `x-veridicus-max-bytes` y `x-veridicus-cookie` en `sessionCookie`.
>   - `x-veridicus-limit` y `x-veridicus-max-bytes` con el nombre de una cifra que exista en `contracts/limits.v1.yaml` (C25). Cada `maxLength`, `maxItems` o tope de bytes lleva la misma cifra que el catálogo.
>   - Todo `multipart` declara `413 limits.exceeded` y `415`.
>   - `Retry-After` en el `503` de `POST /auth/login` (NFRD-U3-10).
>   - Cuerpo `{ expected_cursor }` y `409 report.view_outdated` en `POST /sessions/{session_id}/reports` (NFRD-U7-04).
>   - Tope y `413` en la decisión sobre una sugerencia (NFRD-U8-05).
>   - Las respuestas de NFR-U5-05, NFR-U7-02 (cabeceras de NFR10.4 en `/exports`), NFR-U12-02 y NFR-U13-03.
>   - `PATCH /sessions/{session_id}/analysis` con `202` (C-3). Las seis operaciones que encolan trabajo solo declaran `202` como 2xx.
>   - Fechas con el formato único `AAAA-MM-DDTHH:MM:SSZ` (BR8.1), con el mismo patrón en todas.
>   - `servers: [{url: /api/v1}]`.
>   - Los enum que vienen de C6 (`papel` en `ModelCall`) van en línea o con `$ref` por `$id` canónico a la ruta de C6 (BR3.2, como lo acepta la guardia de T11).
>   - Todo `$ref` estructural apunta a un componente que existe, de su mismo tipo y con un nombre `[A-Za-z0-9._-]+` (guardia de T13).
>   - Todo `pattern` usa el subconjunto portátil de NFRD-U1-14: anclado, sin `\d`, `\w`, `\s`, `\b`, grupos con nombre, banderas en línea ni miradas atrás.
> - Prueba de forma nueva `contracts/tests/contracts/test_console.py`, con rojo primero. Debe cubrir:
>   - la validez como OpenAPI 3.1 con `openapi-spec-validator`;
>   - la versión;
>   - la igualdad `ErrorCode` = catálogo `http: true`;
>   - `CsrfToken`;
>   - una prueba por cada precisión de PD-2 nombrada arriba, más C-3 y D-1.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Los módulos guardia de C1** (`checks/auth_surface.py`, `checks/strict_bodies.py`, `checks/config_write.py`, `checks/limits_match.py`) y la parte de C1 de `checks/error_codes.py`: son de T15. Aquí solo se escribe el contrato y su prueba de forma.
- **`contracts/limits.v1.yaml`**, incluidos los `used_in` (K-11): los alinea T15. Si una cifra que C1 necesita no existe en C25, para y lo informas.
- **El catálogo de errores** (`errors/error-codes.v2.yaml`): si C1 necesita un `code` que no está, para y lo informas.
- Implementar rutas, que es de U3 a U13. Las rutas `SHOULD` (U8, U9) se declaran con `x-veridicus-priority: SHOULD` y las de U13 con `x-veridicus-demo: true`, tal como dice contract-summary.
- Editar los *fixtures* o las pruebas de T03 (`tests/guards/`) y las de T11, T12 y T13.
- `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`: `api/` ya se empaqueta. Si necesitas tocarlos, para y lo informas.

**Choques:** si dos precisiones aprobadas se contradicen, o si una precisión choca con una guardia ya fusionada (T11, T12 o T13), para. No elijas tú. Anota el choque con sus dos fuentes en la bitácora y en tu informe (plan, paso 16).

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 16, PD-1, PD-2, PD-3, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: §C1 (líneas 158 a 1194).
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: C-3, D-1 y P-T07-1.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.3, §4.4, §4.6, §4.7, §4.9 y las filas NFRD-U1 de su tabla de precisiones.
- Las precisiones de PD-2 de otras unidades: NFRD-U3-10, NFRD-U7-04 y NFRD-U8-05 en el `nfr-design/` de U3, U7 y U8, y NFR-U5-05, NFR-U7-02, NFR-U12-02 y NFR-U13-03 en el `nfr-requirements/` de U5, U7, U12 y U13, bajo `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/<unidad>/`. Búscalas por su ID con grep.
- `contracts/errors/error-codes.v2.yaml` y `contracts/limits.v1.yaml`: léelos, no los edites.
- `contracts/tests/guards/test_autonomia_03.py` y `contracts/tests/guards/test_autonomia_04.py` (T03), y los módulos `checks/veracity.py` (T11) y `checks/servers.py` (T13). Ya esperan C1. Léelos, no los edites.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: la prueba de forma de C1 y las guardias que ya esperan C1.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_console.py --no-cov
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards -m c1 --no-cov
  ```
  Esperado: verde las dos. Esto incluye `servers[c1]` de AUTONOMIA-04, el escaneo de vocabulario de C1, que no escriba configuración, y el control E15 de AUTONOMIA-03.

- [ ] **CA-2**: sin regresiones en la suite del Bolt.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks tests/guards tests/contracts --no-cov
  ```
  Esperado: verde. Si falla algo que no es de C1, para y lo informas.

- [ ] **CA-3**: los contratos están en la instalación editable y en la rueda.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-4**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory contracts yamllint api/console.v2.yaml
  ```
  Esperado: `Success: no issues found`, `All checks passed!` y `yamllint` sin errores.

- [ ] **CA-5**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero `test_console.py`, con una prueba por regla de forma y por precisión: validez 3.1, versión, `ErrorCode`, `CsrfToken`, `Retry-After`, `expected_cursor`, el tope de la decisión, C-3, D-1 y las respuestas de NFR-U5-05, NFR-U7-02, NFR-U12-02 y NFR-U13-03.
2. Haz commit de las pruebas.
3. Corre el rojo contra `feat/b1-contratos`, junto con `pytest tests/guards -m c1`. Pega la salida literal en `docs/loop/bitacoras/U01-T14.md`.
4. Escribe `console.v2.yaml` hasta el verde.
5. Si cambias las pruebas después del rojo, vuelve a correrlo con el archivo del commit final y pega esa salida. El rojo de la bitácora tiene que salir de las pruebas tal como están en el commit (rondas de T11, T12 y T13).

---

## Reglas de la app que aplican

- **AUTONOMIA-03:**
  - Ningún campo ni texto de C1 lleva una etiqueta de veracidad. La guardia de T11 (C8, 51 términos) escanea C1.
  - No hay ninguna ruta que escriba perfiles, proveedores, *prompts*, precios ni límites (BR7.1, AC8.3.1, E15).
  - La consolidación exige una acción explícita del analista.
- **AUTONOMIA-04:** `servers` internos (`/api/v1`). Ningún destino externo.
- **AUTONOMIA-05:** los campos de C6 (`hecho`, `tipo`, `cita_a`, `cita_b`, `observaciones`) conservan su nombre en español y son obligatorios donde C6 los exige.
- **Solo datos sintéticos** en los ejemplos (`project.md`).
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- Este es el contrato más grande del Bolt: unas 1000 líneas en contract-summary. Transcribe con cuidado y no inventes rutas ni campos. Si contract-summary y una precisión de PD-2 difieren, manda la precisión (PD-1). Si dos precisiones difieren entre sí, para (ver «Choques»).
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`. Para añadir a la bitácora, usa `cat >> RUTA <<'FIN'`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): OpenAPI de la consola C1 v2 (U01-T14)`. Sin signo de dólar en el mensaje.
