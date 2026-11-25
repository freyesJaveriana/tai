# U01-T11: vocabulario prohibido C8, aviso, casos de escaneo y rótulos

> El orquestador llenó esta tarea a partir del `code-generation-plan.md` de U1 (reaprobado con E-5 y E-6 el 2026-11-23). El humano la revisa antes del despacho.
>
> **Este archivo, con los pasos del plan que cita, es todo el mundo del codificador.** No va a leer el PRD.

**Unidad:** U01: `contracts`   **Bolt:** B1   **Rama base:** `feat/b1-contratos`
**Pasos del plan que cubre:** paso 13 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`
**Historias que implementa:** ninguna propia (U1 es `spec`).
**Depende de:** U01-T05 a U01-T10, ya fusionadas (ola 7, en paralelo con U01-T12 y U01-T13).

---

## Alcance

**Dentro:**

> - `contracts/integrity/forbidden-vocabulary.v2.yaml` (C8) lleva:
>   - los 9 términos;
>   - `match`: palabra completa, sin distinguir mayúsculas ni tildes;
>   - `excluded_spans` con `quote_delimiters: [«, »]` sobre `hecho`, `observaciones` y `tema`;
>   - las exclusiones enteras de BR5.5;
>   - `categories_forbidden_in_schemas`.
> - En `contracts/integrity/`:
>   - `neutral-clarification.v1.yaml` (VE-05, BR5.6);
>   - `notice.v1.yaml` (VE-01, frase base y versión, BR5.7);
>   - `scan-cases.v1.yaml` (E10–E14, E30 y un caso por término y por frase, con sus `literal_sources`, BR5.8, PD-6);
>   - `testimony-warning-cases.v1.yaml`, con `whitespace_code_points` y los casos U+00A0, U+3000, U+FEFF, tabulador y salto de línea (NFR-U13-10, NFRD-U13-13).
> - `contracts/ui/result-labels.v2.yaml`: «Sugerencia de revisión», «Contradicción en el relato» y los 7 rótulos de tipo: «Fecha», «Número», «Lugar», «Persona», «Negación», «Secuencia» y «Otro» (FD-U1-08, BR6.1–BR6.3).
> - Módulos guardia `contracts/src/veridicus_contracts/checks/veracity.py` y `checks/scan_cases.py` (§4.8):
>   - BR3.2, BR3.3, BR5.1 y BR6.1–BR6.3 sobre todos los documentos;
>   - la forma de los casos, con uno por término y por frase (E40);
>   - E17: un décimo rótulo da rojo.
> - Pruebas nuevas en `contracts/tests/checks/test_veracity.py` y `contracts/tests/checks/test_scan_cases.py`. Rojo primero en las dos.

**Fuera** (el codificador debe rechazarlo aunque lo vea roto o incompleto):

- Ejecutar el escáner sobre salidas reales: lo hace U11.
- La lista de 9 términos se queda en 9 (decisión de Functional Design, escenario E14). No se añaden flexiones.
- Editar los *fixtures* o las pruebas de T03 (`tests/guards/`, `tests/contracts/`).
- **Archivos de las tareas vecinas de la ola 7:** `contracts/cli/`, `contracts/api/`, `contracts/health/`, `checks/report_closed.py` y `checks/servers.py`, con sus pruebas.
- `pyproject.toml`, `uv.lock`, `hatch_build.py`, `conftest.py`, `tests/helpers.py` y `registry.py`: `integrity/` y `ui/` ya se empaquetan. Si necesitas tocarlos, para y lo informas.

---

## Archivos de contexto

- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/code-generation-plan.md`: paso 13, PD-6, PD-8 y el Testing Contract.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/unit-test-instructions.md`
- `aidlc/spaces/default/intents/261002-veridicus-mvp/inception/contract-design/contract-summary.md`: C8 y los rótulos.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/functional-spec.md`: E10–E14, E17, E30 y E40.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/functional-design/rules.md`: BR3.2, BR3.3, BR5.1–BR5.8 y BR6.1–BR6.3.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/nfr-design/security-design.md`: §4.8.
- `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/contracts/code-generation/decisiones-humano.md`: P-T08-1.
- `contracts/tests/guards/test_autonomia_03.py` (T03): ya espera estos archivos. Léelo, no lo edites.

---

## Criterios de aceptación

Todos se corren desde la raíz del worktree. El revisor los corre él mismo.

- [ ] **CA-1**: verificación del paso 13.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_veracity.py tests/checks/test_scan_cases.py --no-cov
  ```
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_03.py -m "c8 or labels" --no-cov
  ```
  Esperado: verde las dos.

- [ ] **CA-2**: la guardia de vocabulario pasa sobre todos los contratos que ya existen, incluido el caso `c13-llamada` (P-T08-1).
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/guards/test_autonomia_03.py -m "not c1 and not c19 and not c21" --no-cov
  ```
  Esperado: verde. C1 es del paso 16, y C19 y C21 son de U01-T12 y U01-T13, de la misma ola. El orquestador corre los casos `c19` y `c21` cuando se integren las tres.

- [ ] **CA-3**: 100 % de ramas en `checks/veracity.py` y `checks/scan_cases.py` (módulos guardia).
  ```bash
  timeout 120 uv run --frozen --offline --directory contracts pytest tests/checks/test_veracity.py tests/checks/test_scan_cases.py --cov-fail-under=0
  ```
  ```bash
  uv run --frozen --offline --directory contracts coverage report --include=src/veridicus_contracts/checks/veracity.py,src/veridicus_contracts/checks/scan_cases.py --fail-under=100 --show-missing
  ```
  Esperado: verde las dos, 100 % de líneas y de ramas.

- [ ] **CA-4**: los datos nuevos están en la instalación editable y en la rueda.
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

1. Escribe primero las pruebas de los dos módulos guardia, con un control negativo por regla: un término en un nombre de campo, un décimo rótulo (E17), un caso de escaneo que falta para un término y una cita entre «» que no se marca.
2. Míralas fallar y pega la salida en rojo en `docs/loop/bitacoras/U01-T11.md`.
3. Escribe los datos y los módulos hasta el verde.

Los casos de escaneo se escriben en español sintético. No uses ningún fragmento de entrevista real.

---

## Reglas de la app que aplican

- **AUTONOMIA-03:** ninguna etiqueta de veracidad. Este paso escribe la lista que la hace cumplir. Los 9 términos aparecen solo en C8 y en los casos de escaneo, nunca en otro contrato.
- **Solo datos sintéticos** (`project.md`): ningún testimonio, nombre ni fragmento del piloto del TG.
- **AUTONOMIA-02:** cada criterio tiene un comando.

---

## Notas

- F-11: corre siempre con `uv run` y nunca con `--no-sync`.
- Los textos visibles de C8, el aviso y los rótulos van en español, tal como los fijan sus fuentes. Los identificadores y las claves van en inglés.
- Conventional Commits en español con alcance `contracts`, por ejemplo `feat(contracts): vocabulario C8, casos de escaneo y rótulos (U01-T11)`. Sin signo de dólar en el mensaje.
