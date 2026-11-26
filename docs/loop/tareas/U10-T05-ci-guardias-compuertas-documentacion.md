# U10-T05: CI de nivel 0, huecos de las guardias (K-76), compuertas de calidad y documentación

**Unidad:** U10 `anonymizer`   **Bolt:** B10a   **Rama base:** `bolt/b10a-anonymizer`
**Pasos del plan que cubre:** pasos 12, 13, 14 y 15 de `aidlc/spaces/default/intents/261002-veridicus-mvp/construction/anonymizer/code-generation/code-generation-plan.md`
**Historias que implementa:** NFR13 y NFR14 de U10; K-76 (F-05 a F-07 de T29, A-05 de T30); la demostración de B10.
**Depende de:** pasos 12 y 13, de ninguna; pasos 14 y 15, de U10-T04.
**Riesgo (ML-4):** alto (por el paso 13, seguridad del repositorio público) → `revisor` con `opus`

**Dos fases, para ganar tiempo.** Los pasos 12 y 13 no tocan `libs/anonymizer/` y corren ya, en paralelo con U10-T03. Los pasos 14 y 15 necesitan el paquete completo: el orquestador avisa cuando U10-T04 esté fusionada, el codificador trae la rama del Bolt a su worktree con `git -C /workspace/.worktrees/U10-T05 merge --no-ff bolt/b10a-anonymizer` y sigue. La revisión es una sola, al final.

---

## Alcance

**Dentro:**

> - **Fase A, paso 12:** `.github/workflows/anonymizer-level0.yml` sin filtro por rutas (R-11), con acciones fijadas por SHA y `permissions: contents: read`; `ruff format --check` en el *job* `errors-level0` de `contracts-level0.yml`.
> - **Fase A, paso 13:** los huecos de `scripts/check-no-cluster-ids.sh` y `scripts/check-no-datos-personales.sh`, la autoprueba `scripts/tests/autoprueba-guardias.sh` y `.github/workflows/repo-level0.yml`.
> - **Fase B, paso 14:** `testing/coverage_gate.py` y la corrida de todos los «Comandos de verificación» del plan.
> - **Fase B, paso 15:** `libs/anonymizer/README.md`, `libs/anonymizer/examples/demo_fake.py`, glosario y `docs/devlog.md`; versión 0.1.0.

**Fuera** (rechazar aunque se vea roto):

- `libs/anonymizer/src/` fuera de `testing/coverage_gate.py`, y todas las pruebas de `libs/anonymizer/tests/`: son de T02 a T04. Si algo falla allí, se describe en la bitácora y se para.
- `contracts/` salvo `contracts-level0.yml` y lo que `tests/checks/test_ci_workflows.py` necesite leer.
- Crear etiquetas (`anonymizer-v0.1.0`, `contracts-v0.1.1`): las pone el humano.
- Cualquier paso que aplique cambios al clúster o lance trabajos (AUTONOMIA-01).

---

## Archivos de contexto

- El plan: PD-6, pasos 12 a 15, «Comandos de verificación» y R-11 a R-13.
- `docs/loop/CANDIDATAS.md`, fila K-76.
- `docs/loop/revisiones/` de T29 y T30 (hallazgos F-05 a F-07 y A-05), si están en el repositorio; si no, la fila K-76 basta.
- `scripts/check-no-cluster-ids.sh`, `scripts/check-no-datos-personales.sh`, `scripts/check-no-insumos.sh`, `scripts/check-no-cluster-apply.sh`.
- `.github/workflows/` y `contracts/tests/checks/test_ci_workflows.py`.

---

## Criterios de aceptación

Corren desde la raíz del worktree `/workspace/.worktrees/U10-T05`.

**Fase A**

- [ ] **CA-1 (paso 12):**
  ```bash
  timeout 60 uv run --frozen --offline --directory contracts pytest tests/checks/test_ci_workflows.py
  ```
  ```bash
  bash scripts/check-no-cluster-apply.sh
  ```
  Esperado: los dos terminan con 0; la prueba recorre todos los *workflows* reales, también los nuevos.

- [ ] **CA-2 (paso 13, rojo primero):** antes de tocar las guardias, la autoprueba corre contra las guardias sin arreglar y termina con código ≠ 0, con al menos una sonda no detectada por hueco. La bitácora guarda esa corrida.

- [ ] **CA-3 (paso 13):**
  ```bash
  bash scripts/tests/autoprueba-guardias.sh
  ```
  ```bash
  bash scripts/check-no-cluster-ids.sh
  ```
  ```bash
  bash scripts/check-no-datos-personales.sh
  ```
  Esperado: los tres terminan con 0; la autoprueba informa al menos 7 sondas, todas detectadas, y al menos 7 controles, todos limpios. Las guardias sobre el repositorio real siguen en `0 apariciones` (sin falsos positivos nuevos).

**Fase B** (después de que el orquestador avise que U10-T04 está fusionada)

- [ ] **CA-4 (paso 14):** los comandos «Suite de la unidad, con su mínimo», «Ramas de los módulos guardia», «Tipos», «*Lint* y formato», «Fronteras», «Contratos (U1)» y «Guardias del repositorio» de la tabla del plan terminan con 0. 100 % de ramas en `domain/`, `application/`, `api.py`, `providers/` y `testing/fake_transport.py`; ≥ 80 % de líneas en el paquete; la suite corre en ≤ 300 s en CPU.

- [ ] **CA-5 (paso 15):**
  ```bash
  timeout 120 uv run --frozen --offline --directory libs/anonymizer python examples/demo_fake.py
  ```
  ```bash
  bash scripts/check-no-datos-personales.sh
  ```
  Esperado: los dos terminan con 0; la salida de la demostración contiene `AnonymizerUnavailable` y `peticiones=0`, y el cuerpo que saldría solo lleva marcas.

- [ ] **CA-6:** `bash scripts/check-no-insumos.sh` imprime `0 apariciones`, y `grep -n -P "^version = " libs/anonymizer/pyproject.toml` imprime `version = "0.1.0"`.

---

## Plan de pruebas

- **Paso 13 primero en rojo:** la autoprueba se escribe y se corre contra las guardias de hoy (CA-2), en su propio commit; después se cierran los huecos.
- La autoprueba arma un repositorio de Git temporal fuera del árbol versionado, construye **en tiempo de ejecución, a partir de fragmentos**, una sonda sintética por caso y su control negativo, y corre cada guardia con esa raíz como argumento. Ninguna sonda queda escrita entera en un archivo versionado.
- **Paso 14:** `coverage_gate.py` lleva sus propias pruebas (un `coverage.json` sintético que pasa y uno que falla por módulo).
- **Paso 15:** la demostración es evidencia, no garantía: la fuga cero la da `test_autonomia_04_payload.py` (R-13).

---

## Reglas de la app que aplican

- **AUTONOMIA-01:** ningún *workflow* ni script aplica cambios al clúster; `check-no-cluster-apply.sh` lo comprueba. La CI no tiene credenciales del clúster.
- **E-40 y P-T29-2:** nunca escribas nombres reales del clúster ni datos personales del autor; en la bitácora, describe con palabras lo que detecta cada sonda.
- **AUTONOMIA-02:** cada criterio tiene su comando y su umbral.
- Acciones fijadas por SHA; `permissions: contents: read` por defecto.

---

## Notas

- Huecos de K-76 que cierra el paso 13 en `check-no-cluster-ids.sh`: una asignación con ámbito del servidor; un nombre de nodo en la ruta de un archivo versionado; archivos `.psd1`; una URL `file:` con tres barras; un host concatenado tras `@`; y la regla del destino de `scp` sin los falsos positivos de F-05 a F-07. En `check-no-datos-personales.sh`: un número exento seguido de punto y cifras ya no se exime (A-05).
- El README del paquete solo nombra variables `VERIDICUS_*`, declara lo diferido a B10b (DP-03) y el límite de PD-2 (apodo en minúscula).
- **Bitácora:** `docs/loop/bitacoras/U10-T05.md`, con el par falla-pasa de cada fase y, como máximo, una página (ML-7).
