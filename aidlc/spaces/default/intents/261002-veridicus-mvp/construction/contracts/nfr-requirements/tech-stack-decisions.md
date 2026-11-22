# Decisiones de pila — U1 contracts

**Revisión 2 (2026-11-22), segunda pasada.** Sustituye a la revisión 1 del 2026-10-03.
- **Numeración:** las decisiones D1–D12 conservan su número, y cada una dice si **se mantiene** o
  **cambia**. Las nuevas empiezan en D13.
- **Origen de los cambios:** la respuesta P8 = A (subpaquete `contracts/ts/`), el paquete
  `veridicus-contracts` (BR12.1), las funciones puras de FD-U1-10 y la huella JCS que pide FD-U10-12.

**Insumos.**
- Inventario de `contracts/` y flujos F1–F9 de `functional-design/functional-spec.md` (functional-spec).
- Reglas BR1.1–BR12.3 de `functional-design/rules.md` (rules).
- NFR2, NFR10–NFR15 de `inception/requirements-analysis/requirements.md` (requirements).
- C1–C25 y la regla 1 de `inception/contract-design/contract-summary.md` (contract-summary).
- Respuestas P1–P8 de `nfr-requirements-questions.md` y `security-requirements.md`, revisión 2.

Lo que ya fijan `team.md` y requirements no se vuelve a decidir: Python 3.12; `uv` con un lockfile por
paquete; `pytest` + `pytest-cov` + Hypothesis; mypy estricto; Ruff con reglas `S`; TypeScript estricto
con ESLint y Vitest; CI en GitHub Actions con `gitleaks`, `pip-audit`/`npm audit`, Semgrep y Dependabot.

## 1. Decisiones

| # | Estado | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|---|
| D1 | cambia | Forma del paquete | `contracts/` construye la distribución `veridicus-contracts`, que se importa como `veridicus_contracts` (BR12.1). Los servicios, la biblioteca y `sistema` la usan como dependencia (ruta de `uv` en el monorepo; etiqueta `vX.Y.Z` en `sistema`) | Suite en `libs/`; importar `contracts.` como nombre de primer nivel | P1 = A y P6 de Functional Design. El nombre propio evita choques en `sistema` | NFR2.2, NFR13.1 |
| D2 | se mantiene | JSON Schema en Python | `jsonschema` (*draft* 2020-12, con formatos) y `referencing` para el registro | `fastjsonschema` | P2 = A | NFR10.2, NFR10.5, NFR11.2 |
| D3 | se mantiene | OpenAPI 3.1 (C1, C14 si se copia, C16, C21) | `openapi-spec-validator`, más las reglas propias de `checks/` | Spectral | P2 = A | NFR10.1, NFR10.3, NFR10.11, NFR10.12 |
| D4 | se mantiene | AsyncAPI 3.0 (C2, C3, C5) | Meta-esquema oficial empaquetado en `contracts/vendor/` con `SHA256SUMS`; las cargas se validan con D2 | `@asyncapi/cli` | P2 = A. P8 añade Node solo para la validación en TypeScript (D13), no para AsyncAPI | NFR10.5, NFR10.9 |
| D5 | cambia | Lectura de YAML | Python: `ruamel.yaml` en modo `safe`, YAML 1.2, claves duplicadas prohibidas, solo desde `loaders.py`, vigilado por una prueba AST. TypeScript: `yaml` con `uniqueKeys: true` | PyYAML | Una clave repetida no recorta en silencio C8; cierra R-03 de la revisión 1 | NFR10.4 |
| D6 | cambia | Red bloqueada | Python: `pytest-socket` con `--disable-socket`. TypeScript: *setup* de Vitest que hace fallar `fetch` y `net.connect` | Parches manuales | Falla de forma explícita ante cualquier intento de red | NFR10.5, NFR2.1 |
| D7 | cambia | Cobertura | `pytest-cov` con ramas: 100 % en `checks/`, `profiles.py`, `limits.py`, `canonical.py` y `registry.py`, y 80 % de líneas en el resto. En `contracts/ts/`, cobertura de Vitest (v8) con 80 % de líneas | Una meta global | P5 = A; las funciones puras protegen AUTONOMIA-04 | NFR13.1 |
| D8 | cambia | Patrones de los esquemas | Comprobación estática del árbol de cada `pattern` (cuantificadores anidados, alternativas solapadas) y prueba de Hypothesis con presupuesto de 1 s sobre 10 000 caracteres | Solo tiempo de pared a 50 ms | R-04 a de la revisión 1: no depende de la carga de la CI | NFR10.6 |
| D9 | cambia | Tipos TypeScript del frontend | `openapi-typescript` (versión fijada en `contracts/ts/package.json`) genera los tipos de C1 en `contracts/ts/generated/`. `gen_ts` genera las constantes `as const` del catálogo de `code`, los rótulos y C8. La CI regenera y falla si hay diferencia | Tipos a mano; delegarlo a U4 | P3 = A; con P8 = A los tipos viven junto a la validación que la consola importa | NFR14.1, NFR11.3 |
| D10 | se mantiene | Datos sintéticos | Marca `synthetic: true`, lista `mentions`, catálogo `synthetic-names.yaml` y patrones de cédula y radicado; aplican también a los ejemplos versionados y a los casos de escaneo | Solo la marca | P4 = A | NFR12.1 |
| D11 | se mantiene | Formato de los archivos | JSON Schema en `.json` (C6, C7); OpenAPI, AsyncAPI, catálogos y listas en YAML | Todo en YAML | Coincide con los `$id` aprobados | NFR10.2 |
| D12 | cambia | Tiempos | Suite Python ≤ 60 s y mitad TypeScript ≤ 60 s, cada una bajo su `timeout 60`. Paso del paquete ≤ 180 s. Instalación y auditorías fuera de esos límites | Un solo límite para todo | P6 = A; R-04 b de la revisión 1; precisión NFR-U1-02 | NFR2.1, NFR2.2 |
| D13 | nuevo | Mitad TypeScript (P8 = A) | `contracts/ts/` con Node 22 LTS (fijado en `engines` y `.nvmrc`), `package-lock.json`, `ajv` 8 (`Ajv2020`, `strict: true`) con `ajv-formats`, `yaml`, `canonicalize` (RFC 8785), Vitest y `typescript`. Lee los mismos archivos de `contracts/` y los mismos *fixtures* | Dejarlo a U3; retirarlo | P8 = A; regla 1 de contract-summary; BR1.9, BR9.7, BR12.3 | NFR10.15, NFR10.16 |
| D14 | nuevo | Huella JCS en Python | `rfc8785`, envuelto en `veridicus_contracts.canonical.sha256_jcs` | `json.dumps(sort_keys=True)` | `json.dumps` no reproduce la forma de los números de RFC 8785 | NFR10.15 |
| D15 | nuevo | Construcción del paquete | `hatchling` como *backend*, con el mapa de rutas de functional-spec §1 (`python/` a la raíz del paquete, esquemas como datos). `uv build`, e instalación en un entorno nuevo con `uv venv` | `setuptools` con `MANIFEST.in` | Un solo archivo de configuración para los datos del paquete | NFR2.2 |
| D16 | nuevo | Catálogo de errores con estado | `errors/error-codes.v2.yaml` declara, por `code`, su estado HTTP (uno solo) y su clase en `libs/errors/`. `limits.exceeded` es `413` | El estado lo pone cada ruta | P7 = A; BR7.4 | NFR10.3 |

## 2. Estructura del paquete

```text
contracts/
  pyproject.toml            # distribución veridicus-contracts (hatchling), pytest, cobertura, mypy, Ruff
  uv.lock                   # fijado con hashes
  api/ errors/ queues/ analyzer/v1/ integrity/ ui/ profiles/ model_calls/ cli/
  metrics/ health/ format/ transcript/ limits.v1.yaml      # contratos (functional-spec §1)
  python/                   # model_calls, human_review, report_ports, identity, access_log, retention,
                            # profiles, limits, registry, canonical (a la raíz del paquete)
  */fixtures/               # datos sintéticos; no se empaquetan
  fixtures/synthetic-names.yaml
  vendor/                   # meta-esquemas oficiales + SHA256SUMS
  src/veridicus_contracts/
    loaders.py              # D5
    checks/                 # módulos guardia: una comprobación por regla transversal
    tools/gen_ts.py         # D9
    tools/check_package.py  # F9
  tests/
  ts/                       # D13
    package.json  package-lock.json  .nvmrc  tsconfig.json  vitest.config.ts
    src/                    # registry (addSchema), canonical (JCS), loaders (yaml)
    generated/              # tipos de openapi-typescript y constantes de gen_ts
    tests/
```

## 3. Dependencias

Todas se fijan en `contracts/uv.lock` o en `contracts/ts/package-lock.json`; el rango mínimo va en
`pyproject.toml` o en `package.json`.

| Paquete | Uso | Grupo |
|---|---|---|
| `jsonschema` (con extras de formato), `referencing` | D2 | principal |
| `openapi-spec-validator` | D3 | desarrollo |
| `ruamel.yaml` | D5 | principal |
| `rfc8785` | D14 | principal |
| `pytest`, `pytest-cov`, `pytest-socket`, `hypothesis` | Suite | desarrollo |
| `mypy`, `ruff`, `pip-audit`, `hatchling` | Calidad y construcción | desarrollo |
| `ajv`, `ajv-formats`, `yaml`, `canonicalize` | D13 | `contracts/ts` principal |
| `vitest`, `@vitest/coverage-v8`, `typescript`, `eslint`, `openapi-typescript` | D9, D13 | `contracts/ts` desarrollo |

## 4. Comandos de verificación (AUTONOMIA-02)

Cada uno termina con código 0 solo si su umbral se cumple. Son los pasos del *job* `contracts-level0`,
obligatorio en la protección de `main`. Los pasos marcados «con red» van fuera de los `timeout` de las
suites.

| Qué verifica | Comando | Umbral |
|---|---|---|
| Instalación Python (con red) | `uv sync --directory contracts --frozen` | Termina sin error |
| Suite Python, red bloqueada, cobertura | `timeout 60 uv run --directory contracts pytest` (la configuración añade `--disable-socket --cov=veridicus_contracts --cov-branch --cov-fail-under=80`) | Verde, ≤ 60 s, ≥ 80 % de líneas |
| Ramas de los módulos guardia | `uv run --directory contracts coverage report --include="src/veridicus_contracts/checks/*,python/profiles.py,python/limits.py,python/canonical.py,python/registry.py" --fail-under=100` | 100 % |
| Tipos Python | `uv run --directory contracts mypy --strict src python` | 0 errores |
| *Lint* Python | `uv run --directory contracts ruff check .` | 0 hallazgos |
| Dependencias Python (con red) | `uv run --directory contracts pip-audit` | 0 `HIGH`/`CRITICAL` con corrección |
| Instalación TypeScript (con red) | `npm --prefix contracts/ts ci` | Termina sin error |
| Mitad TypeScript, red bloqueada, cobertura | `timeout 60 npm --prefix contracts/ts test` (Vitest con cobertura y umbral de 80 % de líneas) | Verde, ≤ 60 s, ≥ 80 % |
| Tipos y *lint* TypeScript | `npm --prefix contracts/ts run typecheck` y `npm --prefix contracts/ts run lint` | 0 errores |
| Dependencias TypeScript (con red) | `npm --prefix contracts/ts audit --audit-level=high` | 0 `HIGH`+ con corrección |
| Tipos generados al día | `uv run --directory contracts python -m veridicus_contracts.tools.gen_ts --check` y `npm --prefix contracts/ts run gen:check` | Sin diferencias |
| Paquete en entorno limpio (con red para instalar) | `timeout 180 uv run --directory contracts python -m veridicus_contracts.tools.check_package` | Verde, ≤ 180 s |

## 5. Riesgos de la pila

| Riesgo | Mitigación |
|---|---|
| El meta-esquema oficial de AsyncAPI 3.0 usa referencias internas | Se copia la versión empaquetada; la suite falla si un `$ref` sale de `vendor/` (NFR10.5) |
| `openapi-spec-validator` no cubre todo OpenAPI 3.1 | Las reglas propias se comprueban en `checks/` además del validador |
| ajv y `jsonschema` difieren en un borde de 2020-12 o de un formato | NFR10.16 compara los veredictos sobre todos los *fixtures* y falla ante cualquier diferencia; se corrige el esquema, nunca se relaja el validador |
| La comprobación estática de patrones depende del analizador interno de `re` (3.12) | Python fijado en 3.12; patrones malos conocidos como control |
| Dos cadenas de suministro (PyPI y npm) | Lockfiles con *hashes*, `pip-audit`, `npm audit` y Dependabot (NFR10.9) |
