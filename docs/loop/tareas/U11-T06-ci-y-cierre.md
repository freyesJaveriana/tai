# U11-T06: CI de nivel 0, compuerta de cobertura, documentación y versión 0.1.0

**Unidad:** U11 `incoherence-analyzer`   **Bolt:** B11a   **Rama base:** `bolt/b11a-analyzer` en `ae4b0ba`, después de fusionar U11-T05 y traer `main`.
**Pasos del plan:** 13, 14 y 15 de `/workspace/aidlc/spaces/default/intents/261002-veridicus-mvp/construction/incoherence-analyzer/code-generation/code-generation-plan.md` (revisión 3, aprobada).
**Depende de:** U11-T05.
**Riesgo (ML-4):** bajo según el plan (configuración, agregación y documentación). La revisión la hace `revisor` con `sonnet`.

ROJO_SHA: c7e6542c26f14ad6c4b35636bbfc791ff60a5145

---

## Alcance

**Entra:**

- **Paso 13, la CI:** `.github/workflows/analyzer-level0.yml`.
  - Sin filtro por rutas. Sigue el patrón de `anonymizer-level0.yml`.
  - Un *job* por paquete: `incoherence_analyzer`, `model_gateway`, `execution_profiles` e `integrity_policy`. Cada *job* corre, en este orden:
    - `uv sync --frozen` y `uv lock --check`;
    - `ruff check` y `ruff format --check`;
    - `mypy --strict`;
    - `lint-imports`, en los cuatro paquetes;
    - `pip-audit`, que bloquea `HIGH` o más cuando hay corrección;
    - la suite con su mínimo de cobertura.
  - El `coverage_gate` del paso 14.
  - Disparo también con `tags: ["analyzer-v*"]`.
  - Acciones fijadas por SHA: solo `actions/*` y el `astral-sh/setup-uv` ya permitido.
  - `permissions: contents: read`.
  - Las pruebas `manual` quedan fuera.
  - Sin `analyzer-level2-gate.yml` (CG-U11-05).
- **Paso 14, `testing/coverage_gate.py`:**
  - Lee los `coverage.json` de los cuatro paquetes.
  - Exige el 100 % de ramas en los 9 módulos guardia que nombra el plan y el 80 % de líneas por paquete.
  - Falla cerrado si falta alguno de esos archivos.
  - Tiene sus propias pruebas, con al menos dos controles negativos (R-09): un guardia al 99 % y un guardia que falta.
  - Después se corre todo «Comandos de verificación» del plan en el worktree.
- **Paso 15, la documentación, la demostración y la versión:**
  - El README del analizador, completo y en español, como pide el plan. Conserva la sección del comando manual de U11-T05.
  - `examples/demo_fake.py`.
  - La sección de U11 en `docs/glosario.md` y la entrada del Bolt en `docs/devlog.md`.
  - Los cuatro paquetes en la versión 0.1.0. La etiqueta la pone el humano.
- **Lo que dejó U11-T05**, en `docs/loop/revisiones/U11-T05/ronda-3.md`:
  - **A-01:** el README dice que el peor caso es por comando, 2 × (1 + 2N) llamadas, y recomienda `timeout 7200` para la corrida manual. Actualiza igual el docstring de `tests/manual/test_real_provider.py`.
  - **A-03:** un mensaje distinto en `cli/messages.py` para la señal que llega después de escribir la última salida. Cámbialo en `main.py` y en su prueba. No cambies el código de salida 5.
  - **A-02** no se toca en el código: queda como precisión en la bitácora.

**Fuera** (rechazar aunque se vea roto):

- **Las 6 rutas congeladas no se editan:**
  - `libs/incoherence_analyzer/tests/guards`
  - `libs/incoherence_analyzer/tests/contracts`
  - `libs/execution_profiles/tests/contracts`
  - `libs/incoherence_analyzer/tests/support.py`
  - `libs/integrity_policy/tests/guards`
  - `libs/integrity_policy/tests/conftest.py`
- **Otros límites:**
  - No se tocan `contracts/` (salvo que `tests/checks/test_ci_workflows.py` exija registrar el *workflow* nuevo; en ese caso, para y repórtalo), `.gitleaks.toml` ni `libs/anonymizer/`.
  - Lo de B11b queda diferido: el modo fragmentado, el alterno, `reporte.json` y el nivel 2.
  - No se crea ni se empuja ninguna etiqueta.
  - No se corre `tests/manual` contra el proveedor real.

---

## Criterios de aceptación

Se corren desde la raíz del worktree `/workspace/.worktrees/U11-T06`.

- [ ] **CA-1 (paso 13):** el *workflow* pasa la prueba de *workflows* y la guardia de clúster.
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py --no-cov
  ```
  ```bash
  bash /workspace/.worktrees/U11-T06/scripts/check-no-cluster-apply.sh
  ```
  Se espera:
  - código 0 en los dos;
  - la prueba recorre el *workflow* nuevo, y la bitácora dice cómo se comprobó.
- [ ] **CA-2 (paso 14):** la compuerta tiene sus propias pruebas.
  - Pasan al menos 4 pruebas: dos casos verdes y los dos controles negativos de R-09.
  - Con los `coverage.json` reales de los cuatro paquetes, la compuerta sale con 0.
  - El comando exacto lo fija el codificador y lo deja en la bitácora y en el *workflow*.
- [ ] **CA-3 (paso 14):** todas las filas de «Comandos de verificación» del plan terminan con 0:
  - la suite de cada paquete, dentro de su `timeout 300`;
  - las ramas de los módulos guardia;
  - los tipos;
  - el *lint* y el formato;
  - las fronteras;
  - el anonimizador;
  - los errores;
  - las guardias del repositorio.

  Se pega la línea final de cada una.
- [ ] **CA-4 (paso 15):** la demostración.
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/incoherence_analyzer --extra cli python examples/demo_fake.py
  ```
  Se espera: código 0, y la salida nombra el archivo `.salida.json` y al menos 1 hallazgo.
- [ ] **CA-5:** no retrocede nada de U11-T05. Con su `--extra cli`, se corren otra vez:
  - CA-1, CA-3, CA-4 y CA-5;
  - CA-7, con mypy, ruff y formato.

  Se espera: código 0 en todos.
- [ ] **CA-6:** las rutas congeladas solo tienen el cambio de P-T04-1.
  ```bash
  git -C /workspace/.worktrees/U11-T06 diff --exit-code ae4b0ba -- libs/incoherence_analyzer/tests/guards libs/incoherence_analyzer/tests/contracts libs/execution_profiles/tests/contracts libs/incoherence_analyzer/tests/support.py libs/integrity_policy/tests/guards libs/integrity_policy/tests/conftest.py
  ```
  Se espera: código 0.
- [ ] **CA-7:** las guardias del repositorio.
  - `check-no-datos-personales.sh`, `check-no-cluster-ids.sh` y `check-no-insumos.sh` imprimen `0 apariciones`.
  - `grep -rnoP "sk-[A-Za-z0-9_-]{6,}"` sobre `libs/incoherence_analyzer`, `libs/model_gateway`, `libs/execution_profiles`, `libs/integrity_policy`, `.github` y `docs` solo encuentra `sk-sintetico-canario-7f3a91c2d4e5`. Los controles de B10a en `libs/anonymizer/tests` quedan excluidos a propósito.
  - Los cuatro `pyproject.toml` dicen `version = "0.1.0"`.

---

## Notas

- **Bitácora:** `docs/loop/bitacoras/U11-T06.md`, de una página como máximo. Debe incluir:
  - el comando de la compuerta;
  - la lista de los *jobs*;
  - la precisión A-02;
  - lo que queda para cerrar B11a: las aristas temporales y el PR del Bolt a `main`.
- **Bash:** sin `bash -c`, `time`, *pipes* ni redirecciones. El tiempo sale de la línea final de pytest.
- **Claves de prueba:** solo `sk-sintetico-canario-7f3a91c2d4e5`.
- **Datos:** solo sintéticos.
- **Red:** ninguna, salvo `uv lock` y `uv sync`.
- **Commits:** en Conventional Commits en español.
- **Plan aprobado:** no lo edites.
- **Al terminar:** haz push de `tarea/U11-T06` y vuelve con tu informe. No fusionas tú.
