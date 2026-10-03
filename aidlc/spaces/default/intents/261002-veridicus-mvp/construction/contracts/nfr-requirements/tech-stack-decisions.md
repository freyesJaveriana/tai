# Decisiones de pila — U1 contracts

**Insumos.** Inventario de `contracts/` y suite F1 de `functional-design/functional-spec.md`
(functional-spec); reglas BR1.1–BR8.2 de `functional-design/rules.md` (rules); restricciones de pila
y NFR2, NFR10, NFR12–NFR14 de `inception/requirements-analysis/requirements.md` (requirements);
contratos C1–C16 y reglas de propiedad de `inception/contract-design/contract-summary.md`
(contract-summary); respuestas P1–P6 de `nfr-requirements-questions.md`; `security-requirements.md`.

Lo que ya fijan `team.md` y requirements no se vuelve a decidir: Python 3.12, `uv` con un lockfile por
paquete, `pytest` + `pytest-cov` + Hypothesis, mypy estricto, Ruff con reglas `S`, CI en GitHub
Actions con `gitleaks`, `pip-audit`, Semgrep y Dependabot, TypeScript estricto en el frontend.

## 1. Decisiones

| # | Decisión | Elección | Alternativas descartadas | Por qué | Requisitos |
|---|---|---|---|---|---|
| D1 | Forma del paquete | `contracts/` es un paquete Python 3.12 autocontenido (`pyproject.toml`, `uv.lock`, `src/veridicus_contracts/`, `tests/`). Los servicios lo usan como dependencia de ruta de `uv` para leer esquemas y las interfaces C10–C12. | Suite en `libs/`; suite en Node | P1 = A. Igual que un servicio (team-practices); los contratos se versionan y prueban en un solo lugar (regla 1 de contract-summary) | NFR2.1, NFR13.1 |
| D2 | JSON Schema | `jsonschema` con *draft* 2020-12 y verificación de formatos (`uuid`, `date-time`); `date-time` además con la forma única de BR8.1 | `fastjsonschema` (no cubre bien 2020-12) | P2 = A. Es el validador de referencia en Python y el mismo que usarán los servicios en sus fronteras | NFR10.2, NFR11.2 |
| D3 | OpenAPI 3.1 (C1, C14, C16) | `openapi-spec-validator` | Spectral (Node) | P2 = A. Una sola pila y sin red | NFR10.1, NFR10.3, NFR10.11, NFR10.12 |
| D4 | AsyncAPI 3.0 (C2–C5) | Meta-esquema oficial de AsyncAPI 3.0.0 copiado en `contracts/vendor/` y fijado en `SHA256SUMS`; la suite valida cada documento contra él y extrae las cargas de los mensajes para validarlas con D2 | `@asyncapi/cli` en Node | P2 = A. Sin Node ni red; el costo es actualizar la copia a mano por PR | NFR10.5, NFR10.9 |
| D5 | Lectura de YAML | `ruamel.yaml` en modo `safe`, YAML 1.2, claves duplicadas prohibidas, en la suite y en el generador | PyYAML con `safe_load` | Una clave repetida no puede recortar en silencio la lista de C8 y «no» o «on» no se leen como booleanos | NFR10.4 |
| D6 | Red bloqueada en la suite | `pytest-socket` con `--disable-socket` en la configuración de `pytest` | Parche manual de `socket` en `conftest.py` | Falla de forma explícita ante cualquier intento de red; la suite es reproducible sin conexión | NFR10.5, NFR2.1 |
| D7 | Cobertura | `pytest-cov` con ramas; 80 % de líneas en el paquete y 100 % de ramas en `checks/` | Una sola meta global | P5 = A. Los módulos de comprobación protegen AUTONOMIA-03 y -05 | NFR13.1 |
| D8 | Patrones de los esquemas | Cada `pattern` se compila y se prueba con Hypothesis frente a entradas adversarias, con presupuesto de 50 ms | Revisión manual | Los servicios validan entrada del usuario con estos patrones | NFR10.6 |
| D9 | Tipos TypeScript del frontend | `openapi-typescript` (versión fijada en el `package.json` del frontend) genera los tipos de C1; el generador de U1 (`python -m veridicus_contracts.tools.gen_ts`) genera constantes `as const` del catálogo de `code`, los rótulos y C8. La CI regenera y falla si hay diferencia | Tipos escritos a mano; decidirlo en U4 | P3 = A. Frontend y servidor no pueden divergir sin que la CI lo note | NFR14.1, NFR11.3 |
| D10 | Datos sintéticos | Marca `synthetic: true`, lista `mentions`, catálogo `contracts/fixtures/synthetic-names.yaml` y patrones de cédula (6–10 dígitos) y radicado (23 dígitos) | Solo marca; solo marcadores `PERSONA_1` | P4 = A. Lo que se puede comprobar de forma determinista; el resto queda a la revisión del PR | NFR12.1 |
| D11 | Formato de los archivos | JSON Schema en `.json` (C6 y C7, por su `$id`); OpenAPI, AsyncAPI, catálogos y listas en YAML | Todo en YAML | Coincide con los `$id` aprobados (`judge-output.v1.json`, `alert.v1.json`) | NFR10.2 |
| D12 | Tiempo máximo | La suite completa en ≤ 60 s, en CPU y sin servicios externos | 3 minutos; sin límite | P6 = A | NFR2.1 |

## 2. Estructura del paquete

```text
contracts/
  pyproject.toml            # dependencias, configuración de pytest, cobertura, mypy y Ruff
  uv.lock                   # fijado con hashes
  api/ errors/ queues/ schemas/ integrity/ ui/ db/ metrics/ health/ format/   # contratos (functional-spec §1)
  python/                   # interfaces C10–C12 (Protocol)
  fixtures/<contrato>/{valid,invalid}/   # datos sintéticos
  fixtures/synthetic-names.yaml
  vendor/                   # meta-esquemas oficiales + SHA256SUMS
  src/veridicus_contracts/
    loaders.py              # D5
    checks/                 # módulos guardia: una comprobación por regla transversal
    tools/gen_ts.py         # D9
  tests/
```

## 3. Dependencias

Todas se fijan en `contracts/uv.lock`; el rango mínimo va en `pyproject.toml`.

| Paquete | Uso | Grupo |
|---|---|---|
| `jsonschema` (con extras de formato) | D2 | principal |
| `openapi-spec-validator` | D3 | principal |
| `ruamel.yaml` | D5 | principal |
| `pytest`, `pytest-cov`, `pytest-socket`, `hypothesis` | Suite | desarrollo |
| `mypy`, `ruff`, `pip-audit` | Calidad | desarrollo |
| `openapi-typescript` | D9, en el `package.json` del frontend | frontend |

## 4. Comandos de verificación (AUTONOMIA-02)

Cada uno termina con código 0 solo si su umbral se cumple. Son los pasos del *job*
`contracts-level0`, obligatorio en la protección de `main`.

| Qué verifica | Comando | Umbral |
|---|---|---|
| Suite completa, red bloqueada, cobertura del paquete | `timeout 60 uv run --directory contracts pytest` (la configuración añade `--disable-socket --cov=veridicus_contracts --cov-branch --cov-fail-under=80`) | Verde, ≤ 60 s, ≥ 80 % de líneas |
| Ramas de los módulos guardia | `uv run --directory contracts coverage report --include="src/veridicus_contracts/checks/*" --fail-under=100` | 100 % |
| Tipos | `uv run --directory contracts mypy --strict src python` | 0 errores |
| *Lint* y seguridad del código | `uv run --directory contracts ruff check .` | 0 hallazgos |
| Dependencias | `uv run --directory contracts pip-audit` | 0 `HIGH`/`CRITICAL` con corrección |
| Tipos de TypeScript al día | `uv run --directory contracts python -m veridicus_contracts.tools.gen_ts --check` y, en el frontend, regenerar con `openapi-typescript` y `git diff --exit-code` | Sin diferencias |

## 5. Riesgos de la pila

| Riesgo | Mitigación |
|---|---|
| El meta-esquema oficial de AsyncAPI 3.0 usa referencias internas que hay que empaquetar en un solo archivo | Copiar la versión empaquetada; la suite falla si un `$ref` intenta salir de `vendor/` (NFR10.5) |
| `openapi-spec-validator` no cubre todo OpenAPI 3.1 | Las reglas propias (NFR10.1, NFR10.3, NFR10.8, NFR10.11, NFR10.12) se comprueban en `checks/` además del validador |
| El paquete del frontend aún no existe cuando se construye U1 | U1 entrega el generador y la versión de `openapi-typescript`; la primera unidad que crea la consola añade el paso de diferencia a la CI |
