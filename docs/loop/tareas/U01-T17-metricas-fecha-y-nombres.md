# U01-T17: métricas, formato de fecha y nombres

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 18 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T15, fusionada. Ola 9, en paralelo con T16 y T18.

---

## Alcance

**Dentro:**

> **Contratos de métricas en `contracts/metrics/`**, con la forma de C15 (`schema_version`, `endpoint`, `metrics[]` con `name`, `type`, `labels` y `description`):
>
> - **`review.v2.yaml`: C15 de U5.** Contract-summary, líneas 2120 a 2159, con la revisión 4.
> - **`text-flow.v1.yaml`.** NFRD-U4-08, en `construction/text-flow/nfr-design/security-design.md:284`. La lista de métricas está en `construction/text-flow/nfr-requirements/observability-requirements.md` §2. Suma `veridicus_runs_total`.
> - **`session-lifecycle.v1.yaml`.** NFRD-U6-12, en `construction/session-lifecycle/nfr-design/security-design.md:358`, con su `observability-requirements.md` §2.
> - **`assistant-extras.v1.yaml`.** NFRD-U8-06, en `construction/assistant-extras/nfr-design/security-design.md:276`, con su `observability-requirements.md` §2.
> - **`voice.v1.yaml`.** NFRD-U9-10, en `construction/voice/nfr-design/security-design.md:396`, con su `observability-requirements.md` §2.
> - **`anonymizer.v1.yaml`.** NFRD-U10-02, en `construction/anonymizer/nfr-design/security-design.md:330`, con `construction/anonymizer/nfr-design/observability-design.md` §2.
>
> Cada etiqueta, salvo `session_id`, declara sus `values`. `session_id` declara el patrón de un UUID. No inventes métricas, etiquetas ni valores: transcríbelos de las fuentes y cita en la bitácora la fuente de cada archivo.
>
> **`contracts/format/datetime.v1.yaml`.** Fija el patrón `AAAA-MM-DDTHH:MM:SSZ` (BR8.1). Si C1 ya declara un componente `DateTime` (T14), su `pattern` debe salir igual al de este archivo.
>
> **Módulos guardia en `contracts/src/veridicus_contracts/checks/`** (security-design §4.12):
>
> - **`metrics.py`.** Corre sobre todos los archivos de `metrics/`. Exige:
>   - todo nombre empieza por `veridicus_` y es único entre archivos;
>   - las etiquetas salen de la lista cerrada: `state`, `session_id`, `mode`, `outcome`, `error_code`, `provider`, `role`, `slot`, `category` y `origin`;
>   - toda etiqueta salvo `session_id` declara `values`;
>   - `error_code` toma valores del catálogo (`errors/error-codes.v2.yaml`);
>   - `session_id` lleva el patrón de un UUID;
>   - ninguna etiqueta es de texto libre.
> - **`datetime_format.py`.** Todo `format: date-time` de un contrato propio lleva el `pattern` de `format/datetime.v1.yaml`, y la validación de formato rechaza fechas imposibles (E16). La copia de C6 (`analyzer/v1/`) no se toca y queda fuera.
> - **`naming.py`.** Exige:
>   - propiedades, parámetros y nombres de métricas en ASCII `snake_case`, salvo los bloques de C6 que nombra la regla 8 de contract-summary (CD-05);
>   - todo `code` con la forma `dominio.motivo`.
>
> **Pruebas:** `tests/checks/test_metrics.py`, `test_datetime_format.py` y `test_naming.py`, de 5 a 7 por módulo. Cada regla lleva un control negativo sobre una copia en memoria y un control positivo sobre el contrato real. Deben incluir:
> - métrica sin prefijo;
> - nombre repetido entre dos archivos;
> - etiqueta fuera de la lista;
> - etiqueta sin `values`;
> - `error_code` fuera del catálogo;
> - E16, con `2026-10-02T21:40:00.123Z` y `2026-10-02T16:40:00-05:00`;
> - fecha imposible;
> - propiedad en `camelCase`;
> - `code` sin punto.

**Cuándo parar y avisar** (no lo resuelvas por tu cuenta):

- **Fuentes que se contradicen.** Por ejemplo:
  - NFRD-U9-10 dice que `veridicus_turn_latency_seconds{origin}` «sigue en C15», pero C15 no la lista;
  - NFRD-U10-02 da a `error_code` el valor `ok`, mientras C15 deja `error_code` vacío si la corrida va bien.

  Para y lo informas con las dos fuentes y las salidas posibles.
- **Una guardia nueva encuentra un defecto en un contrato ya fusionado** (C1, C2, C5, C7, C18, C19 o C21), por ejemplo un `date-time` sin patrón o un nombre que no es `snake_case`. Para y lo informas con la ruta y la regla. No edites ese contrato.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- **Emitir métricas.** Lo hacen los servicios.
- **Editar contratos ya fusionados, el catálogo de errores o C25.**
- **`pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`.**
- **Los módulos de T15 y T18.**
- **Las pruebas de otras tareas.**

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 18 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.12.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR8.1 y BR8.2.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E16.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C15 y la regla 8.
- Las cinco fuentes de unidad citadas en el alcance.
- `contracts/errors/error-codes.v2.yaml` y `contracts/api/console.v2.yaml` (`DateTime`).

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 18.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_metrics.py tests/checks/test_datetime_format.py tests/checks/test_naming.py --no-cov
  ```
  Esperado: verde.

- [ ] **CA-2**: 100 % de ramas en los tres módulos guardia.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests/checks --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/metrics.py,src/veridicus_contracts/checks/datetime_format.py,src/veridicus_contracts/checks/naming.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, con el 100 % de líneas y de ramas.

- [ ] **CA-3**: la suite del Bolt sigue en verde.
  ```bash
  timeout 300 uv run --frozen --offline --directory contracts pytest tests --no-cov
  ```
  Esperado: verde.

- [ ] **CA-4**: rueda, tipos y *lint*.
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/test_package_map.py --no-cov
  ```
  ```bash
  uv run --frozen --offline --directory contracts mypy --strict src
  ```
  ```bash
  uv run --frozen --offline --directory contracts ruff check .
  ```
  ```bash
  uv run --frozen --offline --directory contracts yamllint metrics format
  ```
  Esperado: todo verde y sin hallazgos.

- [ ] **CA-5**: sin cambios al clúster.
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: `0 apariciones`, código 0.

---

## Plan de pruebas

1. Escribe primero las tres pruebas.
2. Haz el commit de las pruebas, corre el rojo contra `feat/b1-contratos` y pega la salida literal en `docs/loop/bitacoras/U01-T17.md`.
3. Escribe los contratos y los módulos hasta el verde.
4. Si cambias las pruebas después del rojo, vuelve a correrlo con el archivo del commit final y pega esa salida.

---

## Reglas de la app que aplican

- **AUTONOMIA-04 y NFR10:** las etiquetas de las métricas llevan solo identificadores y enumeraciones, nunca texto del testimonio.
- **AUTONOMIA-03:** `veridicus_session_dismissal_ratio` nunca cambia un perfil ni un *prompt* (AC10.8.2). Va en la `description`.
- **AUTONOMIA-02:** cada criterio tiene un comando.
- **Solo datos sintéticos** (`project.md`).

---

## Notas

- Los mensajes de las guardias nombran el archivo, el puntero y la regla, nunca el valor.
- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Bash: solo caracteres ASCII imprimibles. Nada de signo de dólar, acento grave ni `$(`, ni siquiera entre comillas. Usa `grep -P` con `\x24` y `\x60`, y escapes `\uXXXX` en `python -c`. Para añadir a la bitácora, usa `cat >> RUTA <<'FIN'`.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): métricas, formato de fecha y nombres (U01-T17)`.
