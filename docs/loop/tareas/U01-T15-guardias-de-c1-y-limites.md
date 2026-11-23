# U01-T15: guardias de C1, límites en los dos sentidos y `code` de C1 y C21

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 16, segunda mitad (T15), de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T14, fusionada (C1 existe). Ola 8.

---

## Alcance

**Dentro:**

> Módulos guardia nuevos, uno por regla, en `contracts/src/veridicus_contracts/checks/`:
>
> - **`auth_surface.py`** (§4.6). Exige:
>   - `x-veridicus-roles` con valores de `Role` en toda operación, salvo `/auth/login`, `/auth/logout`, `/auth/me` y la lista pública. La lista pública es una constante con su motivo: `POST /auth/login` y `GET /notice` (D-1).
>   - `401` en toda operación con seguridad, y `403` en toda operación con roles, las dos con `$ref` a `Problem` (NFRD-U1-12).
>   - `X-CSRF-Token` en todo `POST` y `PATCH`.
>   - Ningún `PUT` ni `DELETE`.
>   - Las extensiones solo de la lista cerrada de §4.6.
>   - Ningún 2xx distinto de `202` en las seis operaciones que encolan. Van en una constante de seis `operationId`, entre ellas el `PATCH /sessions/{session_id}/analysis` de C-3.
> - **`strict_bodies.py`** (§4.3). Comprueba:
>   - `additionalProperties: false` en cada objeto de los cuerpos JSON de C1;
>   - en `multipart`, que cada parte no binaria esté acotada y que el cuerpo lleve `x-veridicus-max-bytes`;
>   - la estrictez de C6 (copia), C7, C18 efectiva, C19 con `model-call.v1.yaml`, C21 y la ruta interna de voz;
>   - las entradas de mensajes fallidos de C2, C3 y C5, sin campos de texto.
> - **`config_write.py`** (§4.8, BR7.1): ninguna operación de C1 escribe perfiles, proveedores, *prompts*, precios ni límites. La excepción es `profile_name`, que elige un perfil y no lo escribe. `checks/threshold.py` queda «Retirado»: no se crea.
> - **`limits_match.py`** (§4.4), en los dos sentidos:
>   - (a) Todo campo de texto de un cuerpo de C1, de un mensaje de C2 o C5 y de C21 lleva su marca.
>   - (b) El valor del contrato es igual al del catálogo.
>   - (c) La unidad es coherente con la palabra clave.
>   - Comprobación inversa: toda entrada con `used_in: [Cn]` aparece marcada en `Cn`, y toda marca nombra una entrada que la incluye en `used_in`.
>   - Cubre C1, C2, C5, C19 con `model-call.v1.yaml`, C21 y la ruta interna de voz.
> - **`error_codes.py`**, la parte de C1 y C21 (§4.7):
>   - todo `code` usado en C1 y en C21 existe en el catálogo;
>   - el estado declarado coincide con el del catálogo;
>   - todo `4xx` y `5xx` va con `$ref` a `Problem`;
>   - E44: un `code` de C1 que no está en el catálogo da rojo.
>
>   Este módulo ya existe (T07) y se amplía en su sitio. Debe buscar los `code` también donde no van bajo las claves `code` o `error_code`: en los `enum` de `ErrorCode` y en `description` (K-05, K-19).
>
> **Candidatas que se cierran aquí:**
>
> - **K-11 y K-14:** alinear los `used_in` de `contracts/limits.v1.yaml` con las marcas reales de C1, C2, C5, C19, C21 y la ruta de voz, entre ellas `anonymizer_response_max_bytes` y `speech_audio_max_bytes`. Es la única edición permitida en C25: no se cambia ninguna cifra ni se añade ninguna entrada.
> - **K-15:** §4.4 (a) no incluye la ruta interna de voz, así que `tema` no necesita marca. Fíjalo con una prueba y anótalo en la bitácora.
> - **K-16:** `model-call.v1.yaml` es parte de C19, así que cada `maxLength` lleva su `x-veridicus-limit`. Si C25 no tiene la cifra de un campo, por ejemplo `role` con 32, para y lo informas. No inventes cifras.
> - **K-18:** contrasta el estado de cada `code` de la ruta de voz y de C21 con el catálogo. Si un `code` se usa con otro estado, por ejemplo `speech.text_rejected` (409 en el catálogo) en un `422`, para y lo informas. No cambies el catálogo.
>
> **Pruebas nuevas, de 5 a 8 por módulo, con rojo primero:** `tests/checks/test_auth_surface.py`, `test_strict_bodies.py`, `test_config_write.py` y `test_limits_match.py`, además de casos nuevos en `test_error_codes.py`. Deben incluir los controles negativos de §4.3, §4.6 y §4.7:
>
> - ruta pública nueva;
> - escritura sin anti-CSRF;
> - operación sin roles;
> - `DELETE`;
> - `200` en una operación que encola;
> - cuerpo sin estrictez;
> - límite distinto del catálogo;
> - límite huérfano en los dos sentidos;
> - `409` sin `Problem`;
> - `code` fuera del catálogo;
> - E15 (`PUT /profiles`);
> - E44.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Editar C1** (`console.v2.yaml`, de T14) y los demás contratos. Si una guardia nueva encuentra un defecto en C1, C21 o C19, para y lo informas con la ruta y la regla. El orquestador decide si vuelve a T14.
- **Cambiar cifras de C25 o entradas del catálogo de errores.**
- **`checks/redos.py`, `checks/refs.py`, `checks/synthetic.py` y demás módulos del paso 19** (T18).
- **Editar los *fixtures* o las pruebas de T03** (`tests/guards/`) y las de T11, T12, T13 y T14.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.** Si necesitas tocarlos, para y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 16, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.3, §4.4, §4.6, §4.7, §4.8 y §5.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E15 y E44.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR7.1 a BR7.4.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: C-3, D-1 y P-T07-1.
- `docs/loop/CANDIDATAS.md`: K-05, K-11, K-14, K-15, K-16, K-18 y K-19.
- `contracts/api/console.v2.yaml` (T14), `contracts/api/anonymizer-proxy.v1.yaml`, `contracts/api/speech-internal.v1.yaml`, `contracts/limits.v1.yaml`, `contracts/errors/error-codes.v2.yaml` y `contracts/src/veridicus_contracts/checks/error_codes.py`.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 16, sin filtros de marcador.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks tests/guards tests/contracts --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: 100 % de ramas en los módulos guardia nuevos y en `error_codes.py`.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/auth_surface.py,src/veridicus_contracts/checks/strict_bodies.py,src/veridicus_contracts/checks/config_write.py,src/veridicus_contracts/checks/limits_match.py,src/veridicus_contracts/checks/error_codes.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, con el 100 % de líneas y de ramas.

- [ ] **CA-3**: el catálogo de límites sigue válido tras alinear `used_in`.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_limits.py tests/checks/test_limits_catalog.py --no-cov
  ```
  Esperado: verde. `git diff` de `limits.v1.yaml` solo toca líneas de `used_in`.

- [ ] **CA-4**: los contratos están en la instalación editable y en la rueda.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-5**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-6**: la CI del repositorio sigue en verde.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero las pruebas de los cuatro módulos nuevos y los casos nuevos de `test_error_codes.py`. Cada regla lleva un control negativo, sobre una copia en memoria del contrato real, y un control positivo sobre el contrato real.
2. Haz el commit de las pruebas, corre el rojo contra `feat/b1-contratos` y pega la salida literal en `docs/loop/bitacoras/U01-T15.md`.
3. Escribe los módulos y alinea `used_in` hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con el archivo del commit final y pega esa salida. El rojo de la bitácora debe salir de las pruebas tal como están en el commit.

---

## Reglas de la app que aplican

- **AUTONOMIA-03 y BR7.1:** ninguna operación de C1 escribe configuración (E15). Ninguna ruta permite una consolidación sin el analista.
- **AUTONOMIA-04:** estrictez de C21 y de los cuerpos que pueden llevar texto, para que ningún campo abierto deje salir testimonio.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- Los mensajes de las guardias nombran la ruta, el puntero y la regla, nunca el valor del contrato.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`. Para añadir a la bitácora, usa `cat >> RUTA <<'FIN'`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): guardias de C1 y límites en los dos sentidos (U01-T15)`. Sin signo de dólar en el mensaje.
