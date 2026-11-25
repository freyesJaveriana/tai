# U01-T13: C21, ruta interna de voz, salud C16 y guardia de `servers`

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 15 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T05 a U01-T10, ya fusionadas (ola 7, en paralelo con U01-T11 y U01-T12).

---

## Alcance

**Dentro:**

> - `contracts/api/anonymizer-proxy.v1.yaml` (C21):
>   - petición y respuesta estrictas en todos los niveles;
>   - `role` con patrón y `profile_sha256` con `^[0-9a-f]{64}$`;
>   - `x-veridicus-max-bytes` en la petición y en la respuesta;
>   - `servers` internos;
>   - los estados de respuesta de C21 revisión 4 (`409`, `413`, `422`, `451`, `502`, `503` y `504`) con sus `code` del catálogo de errores v2 (§4.17, NFRD-U1-04).
> - `contracts/api/speech-internal.v1.yaml`: `POST /internal/v1/speech` con `bearerAuth` y cuerpo estricto. Responde `401`, `422` con `rule_id` cerrado, `503` y `audio/wav` con `x-veridicus-max-bytes: speech_audio_max_bytes` (NFRD-U1-08).
> - `contracts/health/health.v2.yaml` (C16): `/healthz` y `/readyz`, públicas dentro del clúster.
> - `contracts/src/veridicus_contracts/checks/servers.py`, módulo guardia de §4.9. Exige que cada `server` sea una ruta relativa o `http://veridicus-<nombre>:<puerto>` o `*.svc.cluster.local`, siempre con `http`. Tiene un control con C21 apuntando a `https://api.openai.com`.
> - Pruebas nuevas en `contracts/tests/checks/test_servers.py`. Rojo primero.
> - Los *fixtures* de C21 y `tests/contracts/test_anonymizer_proxy.py` ya existen (T03): este paso escribe los contratos y la guardia.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- El proxy del anonimizador, que es de U10, y `audio-worker`, que es de U9.
- C1 (`console.v2.yaml`): es del paso 16 (T14). Sus casos de `servers` (`c1`) siguen en rojo.
- Comparar `x-veridicus-max-bytes` con C25 y comprobar los `code` usados en C21: los hace el paso 16 (T15, PD-8).
- Editar los *fixtures* o las pruebas de T03, el catálogo de errores y C25.
- **Archivos de las tareas vecinas de la ola 7:** `contracts/integrity/`, `contracts/ui/`, `contracts/cli/`, `checks/veracity.py`, `checks/scan_cases.py` y `checks/report_closed.py`, con sus pruebas.
- `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`: `api/` y `health/` ya se empaquetan. Si necesitas tocarlos, para y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 15, PD-8, E-6 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C16, C21 (revisión 4) y la ruta interna de voz.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: P-T07-1 (`anonymizer.incident` no es respuesta de ninguna ruta).
- `contracts/errors/error-codes.v2.yaml`: el estado de cada `code` que use C21.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.9, §4.17, NFRD-U1-04 y NFRD-U1-08.
- `contracts/tests/contracts/test_anonymizer_proxy.py` y `contracts/tests/guards/test_autonomia_04.py` (T03): ya esperan estos contratos. Léelos, no los edites.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 15.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts/test_anonymizer_proxy.py tests/checks/test_servers.py --no-cov
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_04.py -m "not c1 and not c19" --no-cov
  ```
  Esperado: verde las dos (E-6). Los casos `c19` son de U01-T12, de la misma ola, y los `c1` son del paso 16.

- [ ] **CA-2**: 100 % de ramas en `checks/servers.py` (módulo guardia).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/checks/test_servers.py --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/servers.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, 100 % de líneas y de ramas.

- [ ] **CA-3**: los estados de C21 coinciden con el catálogo de errores v2.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_error_codes.py --no-cov
  ```
  Esperado: verde. Ninguna respuesta de C21 declara un estado distinto del que el catálogo da a su `code`. `anonymizer.incident` no aparece como respuesta (P-T07-1).

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

1. Escribe primero `test_servers.py`, con un control negativo por regla:
   - `https://api.openai.com` en C21;
   - una IP literal;
   - `https` dentro del clúster;
   - un nombre sin el prefijo `veridicus-`;
   - un `server` ausente.
2. Mira fallar `test_servers.py`, `test_anonymizer_proxy.py` y los casos de `test_autonomia_04.py`, y pega la salida en rojo en `docs/loop/bitacoras/U01-T13.md`.
3. Escribe los contratos y la guardia hasta el verde.

---

## Reglas de la app que aplican

- **AUTONOMIA-04:**
  - Ningún contrato declara un destino externo. El anonimizador es el único que sale, y C21 es su ruta interna.
  - El cuerpo de C21 nunca lleva una clave de API: `api_key_ref` se rechaza (*fixture* de T03).
- **AUTONOMIA-03:** ningún campo de veracidad.
- **Solo datos sintéticos** (`project.md`).
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): C21, voz interna, salud C16 y guardia de servers (U01-T13)`. Sin signo de dólar en el mensaje.
