# Instrucciones de pruebas unitarias — U1 contracts

**Insumos.** `code-generation-plan.md` de esta unidad (pasos 2–17 y su Testing Contract);
`construction/contracts/nfr-requirements/tech-stack-decisions.md` §4 (comandos);
`construction/contracts/nfr-design/security-design.md` §4.13 (pasos con y sin red); `team.md`
(Testing Posture).

## Marco y configuración

- **Paquete bajo prueba:** `contracts/` (`src/veridicus_contracts/`), Python 3.12 con `uv` y su propio
  `uv.lock`.
- **Herramientas:** `pytest`, `pytest-cov` (con ramas), `pytest-socket`, Hypothesis; mypy estricto y
  Ruff (reglas `S`) como compuertas de la misma suite.
- **Configuración en `contracts/pyproject.toml`:**
  - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`; `addopts = "--disable-socket
    --cov=veridicus_contracts --cov-branch --cov-fail-under=80"`.
  - Perfil de Hypothesis determinista (`derandomize = true`, `deadline = None`): ninguna prueba mide
    tiempo de pared.
  - `[tool.coverage.run] branch = true`; `omit` solo para `generated/` (exclusión declarada; cualquier
    otra se justifica en el PR).
- **Sin servicios externos:** la suite no usa red, base de datos, Redis ni GPU. Corre en CPU, en la
  máquina de desarrollo y en CI.

## Cómo correr las pruebas de ESTA unidad

Todos los comandos están acotados al paquete `contracts/`, que pertenece solo a U1; ninguno corre la
suite de otra unidad. Se ejecutan desde la raíz del repositorio.

| Momento | Comando | Resultado esperado |
|---|---|---|
| Ejecutor listo (paso 2, antes de la primera prueba de contrato) | `timeout 60 uv run --offline --directory contracts pytest tests/test_runner.py --no-cov` | 2 pruebas en verde |
| Rojo de contratos y guardias (paso 5) | `timeout 60 uv run --offline --directory contracts pytest tests/contracts tests/guards --no-cov` | Código distinto de 0; solo `AssertionError` o contrato ausente, ningún error de importación o de recolección |
| Una capa (pasos 3–16) | `timeout 60 uv run --offline --directory contracts pytest <rutas de prueba del paso> --no-cov` | Verde |
| Suite completa de la unidad | `timeout 60 uv run --offline --directory contracts pytest` | Verde, ≤ 60 s, ≥ 80 % de líneas |
| Ramas de los módulos guardia | `uv run --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/*" --fail-under=100` | 100 % |
| Tipos | `uv run --offline --directory contracts mypy --strict src python` | 0 errores |
| *Lint* | `uv run --offline --directory contracts ruff check .` | 0 hallazgos |

Antes de la primera ejecución, instalar con red: `uv sync --frozen --directory contracts`.

## Volumen y orden (estrategia Standard + orden del equipo)

- **Orden:** las pruebas de contratos de datos (C2–C5, C6, C7) y de las guardias AUTONOMIA-03/04/05 se
  escriben primero y se corren en rojo (paso 5). Después, cada capa se implementa y enseguida se
  escriben y corren sus pruebas (pasos 3–4 y 6–16).
- **Volumen:** 5–8 pruebas por componente. Son componentes: `loaders`, `validators`, `limits`, cada
  módulo de `checks/` (17), `tools/security_surface`, `tools/gen_ts` y las interfaces C10–C12.
- **Además del volumen:** las pruebas de *fixtures* (al menos un `accept` y un `reject` por cada regla
  BR1.1–BR8.2 que se prueba en nivel 0, NFR10.10) y las guardias AUTONOMIA de `tests/guards/`. Son
  adicionales y ningún plan las recorta (team-practices).
- **Integración:** U1 no tiene fronteras en ejecución. La prueba de integración de la unidad es la
  validación de cada contrato completo contra su meta-esquema y de sus *fixtures* contra el contrato
  (`tests/contracts/`).

## Metas de cobertura

| Alcance | Meta | Comando |
|---|---|---|
| Paquete `veridicus_contracts` | ≥ 80 % de líneas | Suite completa (`--cov-fail-under=80`) |
| `src/veridicus_contracts/checks/` (módulos guardia) | 100 % de ramas | `coverage report --include=... --fail-under=100` |

Las metas no se bajan para que una compuerta pase; un hueco se informa en el PR.

## Dobles de prueba

- No hay LLM, *embeddings*, base de datos ni Redis en U1: no se usan *mocks* ni *fakes* de servicios.
- Los controles negativos son **copias modificadas** de documentos reales (C1 con `PATCH
  /config/threshold`, C14 con `https://api.openai.com`) que se construyen en memoria dentro de la
  prueba; nunca se escriben en `contracts/`.
- Para `checks/loader_usage.py`, los módulos con usos prohibidos (`YAML(typ="unsafe")`, `import yaml`)
  son cadenas que la prueba analiza con `ast`; no son archivos `.py` del paquete.
- Para C10–C12, cada interfaz tiene un *fake* mínimo en `tests/typing/` que mypy comprueba contra el
  `Protocol`.

## Datos de prueba

- Todos los *fixtures* viven en `contracts/fixtures/<contrato>/{valid,invalid}/` y declaran
  `synthetic: true`, `expectation`, `reject_reason` (ID de regla, obligatorio en `reject`) y `mentions`.
- Solo datos sintéticos (NFR12.1, `project.md`): las personas y los lugares salen de
  `contracts/fixtures/synthetic-names.yaml`; ninguna secuencia de 6–10 dígitos ni de 23 dígitos.
- Cada *fixture* negativo debe fallar **por** su `reject_reason`; si falla por otra regla, la suite
  falla (F1 paso 3).
- Los *fixtures* de C8 (E10–E14) llevan además sus `literal_sources` para que el escáner de U4 los use.
