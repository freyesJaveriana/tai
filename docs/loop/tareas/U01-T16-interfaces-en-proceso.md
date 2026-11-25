# U01-T16: interfaces en proceso C10, C11, C12, C23 y C24

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 17 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T15, fusionada. Ola 9, en paralelo con T17 y T18.

---

## Alcance

**Dentro:**

> Cinco módulos de `Protocol` tipados en `contracts/src/veridicus_contracts/`. Cada uno lleva su versión en el encabezado y transcribe las firmas de contract-summary con las revisiones que se citan abajo:
>
> - **`human_review.py`: C10 v2.0.0.** Contract-summary, líneas 1788 a 1827.
>   - `DecisionState`, `Actor`, `SuggestionProposer.propose` y `ReviewCommands` (`record_observations_view`, `decide`).
>   - La docstring de `decide` incluye los errores de la revisión 4: `suggestion.not_found` y `limits.exceeded`.
> - **`report_ports.py`: C11 v2.0.0.** Líneas 1829 a 1879.
>   - `SessionReader.snapshot`.
>   - `ReviewRounds` con `open_round(..., for_update: bool = False)`, `pending_count`, `pending_counts(uow, session_ids) -> dict[UUID, int]`, `decisions`, `lock_round`, `open_correction_round` y `discard_correction_round(uow, session_id, actor) -> None`.
>   - Los puertos nuevos `SessionLifecycle` (`finalize`, `mark_consolidated(..., finalize_first=False)`) y `PendingSessions.count_pending(uow, owner_user_id) -> int`.
>   - Las docstrings de la revisión 4 (FD-U5-03, FD-U5-04 y FD-U5-05).
> - **`identity.py`: C12 v2.0.0.** Líneas 1881 a 1910.
>   - `Role = Literal["analista", "admin", "investigador"]`, `Principal`, `Authenticator` (`login`, `resolve`, `csrf_token`, `logout`) y `UserAdmin` (`create`, `update`).
>   - `Role` debe ser igual al enum `Role` de C1 (`api/console.v2.yaml`). Pruébalo.
> - **`access_log.py`: C23 v1.0.0.** Líneas 2755 a 2778.
>   - `ResourceType` y `AccessLog.record(..., export_sha256: str | None = None)`.
>   - La docstring recoge la revisión 4: excepción ante un fallo, sin reintentos.
> - **`retention.py`: C24 v1.1.0.** Líneas 2780 a 2814.
>   - `Purgeable.purge_session` y `Purgeable.count_session(uow, session_id) -> Mapping[str, int]` (NFRD-U13-08).
>   - El orden del Job va como comentario del módulo.
>
> **Tipos auxiliares.** contract-summary los nombra entre comillas pero no los define del todo: `UnitOfWork`, `SessionSnapshot`, `RoundView`, `SuggestionWithDecision` y `PurgeReceipt`.
> - Decláralos como `Protocol` de solo atributos, con los campos que nombran las docstrings y las revisiones 4. Por ejemplo, `PurgeReceipt` lleva por versión `report_version_id`, `sha256` y `file_missing` (FD-U7-12), y `SessionSnapshot` lleva `consent_withdrawn_at` y `blocked_code`.
> - `UnitOfWork` es la transacción de `session-api`. Aquí va como `Protocol` sin métodos, en un solo módulo que importan los demás.
> - Cada decisión de nombre, tipo o ubicación que contract-summary no fije se anota en la bitácora como **P-T16-n**, con su fuente. El orquestador la registra.
>
> **`Hallazgo`.** C10 importa `Hallazgo` de `veridicus_contracts.analyzer.v1` (FD-U1-04), y ese módulo de Python no existe todavía. Antes de escribir:
> - Comprueba con `tests/test_package_map.py` y `hatch_build.py` si puede convivir un módulo `veridicus_contracts/analyzer/v1.py` con los datos de `contracts/analyzer/v1/`. Mira cómo conviven `model_calls.py` y `model_calls/` (K-12).
> - Si pueden convivir, `Hallazgo` es un `TypedDict` con los campos de `$defs` de `analyzer/v1/salida.schema.json`, con sus nombres en español (CD-05). Una prueba exige que sus claves sean exactamente las `properties` del esquema.
> - Si no pueden convivir, o hace falta tocar `hatch_build.py` o `pyproject.toml`, **para y lo informas** con las dos salidas.
>
> **Pruebas:** `tests/typing/test_protocols.py`, de 5 a 8 pruebas, con el mismo patrón que `tests/typing/test_anonymizing_provider.py` (`mypy.api.run` con `--strict` sobre dobles en `tmp_path`):
> - un doble mínimo de cada interfaz pasa mypy;
> - un doble con firma distinta falla. Por ejemplo, `open_round` sin `for_update`, `decide` sin `actor` o `count_session` que devuelve `int`;
> - `Role` es igual al enum de C1;
> - la versión del encabezado de cada módulo es la de arriba.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Implementaciones y adaptadores.** Son de U3, U4, U5, U7 y U13. Eso incluye el adaptador por defecto de C23 y el de `PendingSessions`.
- **Editar los contratos YAML o JSON**, entre ellos C1 y la copia de C6.
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.** Si los necesitas, para y lo informas.
- **Las pruebas de T03 y de las demás tareas.**
- **C13** (`model_calls.py`, de T08).

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 17 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: líneas 1788 a 1910 y 2755 a 2814.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: FD-U1-04.
- `contracts/src/veridicus_contracts/model_calls.py` y `contracts/tests/typing/test_anonymizing_provider.py`, como modelo de estilo.
- `contracts/analyzer/v1/salida.schema.json` (solo lectura) y `contracts/api/console.v2.yaml` (`Role`).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 17.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/typing/test_protocols.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: tipos y *lint*.
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  Esperado: `Success: no issues found` y `All checks passed!`.

- [ ] **CA-3**: la suite del Bolt sigue en verde.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde.

- [ ] **CA-4**: los módulos nuevos están en la instalación editable y en la rueda.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-5**: sin cambios al clúster.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero `tests/typing/test_protocols.py`.
2. Haz el commit de las pruebas, corre el rojo contra `feat/b1-contratos` (los módulos no existen) y pega la salida literal en `docs/loop/bitacoras/U01-T16.md`.
3. Escribe los módulos hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con el archivo del commit final y pega esa salida.

---

## Reglas de la app que aplican

- **AUTONOMIA-03:** `lock_round` y `mark_consolidated` reciben siempre un `actor`. Ninguna firma consolida sin un humano.
- **AUTONOMIA-05:** la docstring de `propose` conserva el rechazo de un hallazgo sin sus campos obligatorios.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- Las docstrings y los comentarios van en español; los identificadores, en inglés. La excepción son los campos de C6 (CD-05).
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`. Para añadir a la bitácora, usa `cat >> RUTA <<'FIN'`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): interfaces en proceso C10 a C12, C23 y C24 (U01-T16)`.
