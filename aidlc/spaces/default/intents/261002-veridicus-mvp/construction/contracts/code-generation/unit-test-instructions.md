# Instrucciones de pruebas unitarias — U1 contracts

**Revisión 2 (2026-11-23), segunda pasada por el cambio 01.** Sustituye a la de la primera pasada.

**Insumos.** `code-generation-plan.md` de esta unidad (pasos 1–25, comandos V-* y su Testing Contract);
`construction/contracts/nfr-requirements/tech-stack-decisions.md` §4 (comandos, revisión 2);
`construction/contracts/nfr-design/security-design.md` §4.13 y §4.14 (pasos con y sin red, mitad
TypeScript); `team.md` (Testing Posture).

## Marco y configuración

- **Paquetes bajo prueba:** `contracts/` (distribución `veridicus-contracts`, importada como
  `veridicus_contracts`), Python 3.12 con `uv` y su propio `uv.lock` con *hashes*; y la mitad
  TypeScript `contracts/ts/`, Node 22 con su `package-lock.json`.
- **Herramientas Python:** `pytest`, `pytest-cov` (con ramas), `pytest-socket`, Hypothesis; mypy
  estricto y Ruff (reglas `S`) como compuertas de la misma unidad.
- **Herramientas TypeScript:** Vitest con cobertura v8, `tsc --strict`, ESLint.
- **Configuración en `contracts/pyproject.toml`:**
  - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`; `addopts = "--disable-socket
    --cov=veridicus_contracts --cov-branch --cov-fail-under=80"`.
  - Perfil de Hypothesis determinista (`derandomize = true`, sin `deadline`); solo `checks/redos.py`
    mide su techo de 1 s por caso.
  - `[tool.coverage.run] branch = true`; exclusión declarada solo para `ts/generated/` (código generado).
    Cualquier otra exclusión se justifica en el PR.
- **F7 primero:** `tests/conftest.py` comprueba la copia del contrato común en `pytest_sessionstart`;
  si las huellas no coinciden, la sesión aborta antes de recolectar pruebas.
- **Sin servicios externos:** sin red, base de datos, Redis ni GPU. Todo corre en CPU, en la máquina
  de desarrollo y en CI.

## Cómo correr las pruebas de ESTA unidad

Todos los comandos están acotados a `contracts/` y `contracts/ts/`, que pertenecen solo a U1; ninguno
corre la suite de otra unidad. Se ejecutan desde la raíz del repositorio.

| Momento | Comando | Resultado esperado |
|---|---|---|
| Instalar (una vez, con red) | `uv sync --frozen --directory contracts` y `npm --prefix contracts/ts ci` | Código 0 |
| Ejecutor listo (paso 2, antes de la primera prueba) | `timeout 60 uv run --frozen --offline --directory contracts pytest tests/test_runner.py --no-cov` | 2 pruebas en verde |
| Rojo de contratos y guardias (paso 5) | `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --co -q` y luego `timeout 60 uv run --frozen --offline --directory contracts pytest tests/contracts tests/guards --no-cov --junitxml=build/red.xml` | Recolección con código 0; ejecución con código 1, `errors="0"` y `failures` > 0 en `build/red.xml` (un contrato ausente es `pytest.fail` por `tests/helpers.py`) |
| Guardias acotadas por contrato (pasos 6–15) | `pytest <archivo> -m "<marcador>"` según el paso (PD-8) | Verde; las pruebas `c1` pasan a verde en el paso 16 |
| Excepciones de `libs/errors/` (PD-7) | `timeout 60 uv run --frozen --offline --directory libs/errors pytest`, `... mypy --strict src`, `... ruff check .` | Verde, ≥ 80 % de líneas; 0 errores; 0 hallazgos |
| Una capa (pasos 3–22) | El comando `Verificación:` del paso | Verde |
| Suite Python completa | `timeout 60 uv run --frozen --offline --directory contracts pytest` | Verde, ≤ 60 s (meta ≤ 20 s), ≥ 80 % de líneas |
| Ramas de los módulos guardia | `uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/*,python/profiles.py,python/limits.py,python/canonical.py,python/registry.py" --fail-under=100` | 100 % |
| Tipos | `uv run --frozen --offline --directory contracts mypy --strict src python` | 0 errores |
| *Lint* | `uv run --frozen --offline --directory contracts ruff check .` | 0 hallazgos |
| Mitad TypeScript | `timeout 60 npm --prefix contracts/ts test`, `npm --prefix contracts/ts run typecheck`, `npm --prefix contracts/ts run lint` | Verde, ≤ 60 s, ≥ 80 % de líneas; 0 errores |
| Generados sin diferencias | `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check`, `... tools.gen_jcs_vectors --check`, `npm --prefix contracts/ts run gen:check` | Sin diferencias |
| Paquete en entorno limpio | `timeout 180 uv run --frozen --directory contracts python -m veridicus_contracts.tools.check_package` | Verde, ≤ 180 s |

## Volumen y orden (estrategia Standard + orden del equipo)

- **Orden:** las pruebas de contratos de datos (C6, C2, C3, C5, C7, C18, C19, C21 y entradas fallidas)
  y de las guardias AUTONOMIA-03/04/05 se escriben primero y se corren en rojo (paso 5). Después, cada
  capa se implementa y enseguida se escriben y corren sus pruebas (pasos 3–4 y 6–22).
- **Volumen:** 5–8 pruebas por componente. Son componentes: `loaders`, `validators`, `registry`,
  `canonical`, `profiles`, `limits`, cada módulo de `checks/`, cada herramienta de `tools/`, el
  `Protocol` de `model_calls`, las interfaces C10–C12, C23 y C24, y los módulos de `contracts/ts/src/`.
- **Además del volumen:** las pruebas de *fixtures* (al menos un `accept` y un `reject` por cada regla
  que se prueba en nivel 0, NFR10.10), las guardias AUTONOMIA de `tests/guards/` y la comparación de
  *fixtures* y vectores JCS entre las dos mitades. Son adicionales y ningún plan las recorta.
- **Integración:** U1 no tiene fronteras en ejecución. Su prueba de integración es la validación de
  cada contrato contra su meta-esquema y de sus *fixtures* contra el contrato (`tests/contracts/`),
  más la instalación del paquete en un entorno limpio (paso 22).

## Metas de cobertura

| Alcance | Meta | Comando |
|---|---|---|
| Paquete `veridicus_contracts` | ≥ 80 % de líneas | Suite completa (`--cov-fail-under=80`) |
| `checks/`, `profiles.py`, `limits.py`, `canonical.py`, `registry.py` (módulos guardia) | 100 % de ramas | `coverage report --include=... --fail-under=100` |
| `contracts/ts/` | ≥ 80 % de líneas | `npm --prefix contracts/ts test` |

Las metas no se bajan para que una compuerta pase; un hueco se informa en el PR.

## Dobles de prueba

- No hay LLM, *embeddings*, base de datos ni Redis en U1: no hay *fakes* de servicios.
- Los controles negativos son **copias modificadas en memoria** de documentos reales (C1 con
  `PUT /profiles`, C21 con `https://api.openai.com`, `salida.schema.json` con un byte cambiado); nunca se
  escriben en `contracts/`.
- Para `checks/loader_usage.py`, los módulos con usos prohibidos (`YAML(typ="unsafe")`, `import yaml`,
  `import subprocess`) son cadenas que la prueba analiza con `ast`.
- Para el `Protocol` `AnonymizingProvider` y las interfaces C10–C12, C23 y C24, cada una tiene un doble
  mínimo en `tests/typing/` que `mypy.api.run --strict` comprueba contra el `Protocol`, y uno con firma
  distinta que debe fallar.
- La pureza de `profiles.validate` se prueba con `open`, `os.environ` y `socket.socket` sustituidos.

## Datos de prueba

- Los *fixtures* viven junto a su contrato (`<contrato>/fixtures/`) y declaran `synthetic: true`,
  `expectation`, `reject_reason` (ID de regla, obligatorio en `reject`) y `mentions`.
- Solo datos sintéticos (NFR12.1, `project.md`): personas y lugares salen de
  `contracts/fixtures/synthetic-names.yaml`. Nada del piloto del TG ni de la partición `referencia`.
- Cada *fixture* negativo debe fallar **por** su `reject_reason`; si falla por otra regla, la suite
  falla.
- La copia de C6 la pone el humano desde `/insumos/app/contratos/analizador/v1/` (PD-4); sus *fixtures*
  propios son de U1 y sintéticos.
