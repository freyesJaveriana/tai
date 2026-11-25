# veridicus-contracts

Contratos de Veridicus: esquemas, catálogos, tipos y comprobaciones transversales (unidad U1, `spec`).
Es un paquete de Python (`veridicus_contracts`) con una mitad TypeScript en `ts/`. No tiene comportamiento
en ejecución propio: lo que ofrece son datos versionados, sus validadores y las guardias que los protegen.
Todo corre sin red. Los ejemplos de este archivo usan datos sintéticos.

## Inventario de contratos

Cada fila nombra el contrato con su ID (C1, C2, ...), su archivo bajo `contracts/` y su versión. La versión
mayor es siempre la del `.vN` del nombre (E-28, E-33). Un archivo nuevo entra aquí en el mismo PR que lo crea:
`tests/test_readme.py` falla si un archivo de contrato no aparece en esta sección.

| ID | Contrato | Archivo | Versión |
|---|---|---|---|
| C1 | API de la consola | `api/console.v2.yaml` | 2.0.0 |
| C2 | Cola de corridas | `queues/runs.v2.yaml` | 2.0.0 |
| C3 | Cola de resultados | `queues/results.v2.yaml` | 2.0.0 |
| C5 | Cola de voz | `queues/speech.v2.yaml` | 2.0.0 |
| C5 | Ruta interna de voz | `api/speech-internal.v1.yaml` | 1.0.0 |
| C6 | Contrato común del analizador: entrada | `analyzer/v1/entrada.schema.json` | 1.0.0 |
| C6 | Contrato común del analizador: salida | `analyzer/v1/salida.schema.json` | 1.0.0 |
| C6 | Huellas de la copia de C6 | `analyzer/v1/SHA256SUMS` | 1.0.0 |
| C7 | Sugerencia de revisión | `integrity/review-suggestion.v2.json` | 2.0.0 |
| C8 | Vocabulario prohibido | `integrity/forbidden-vocabulary.v2.yaml` | 2.0.0 |
| C8 | Aclaraciones neutras | `integrity/neutral-clarification.v1.yaml` | 1.1.0 |
| C8 | Aviso de testimonio | `integrity/notice.v1.yaml` | 1.0.0 |
| C8 | Casos del aviso de testimonio | `integrity/testimony-warning-cases.v1.yaml` | 1.0.0 |
| C8 | Casos del escáner de vocabulario | `integrity/scan-cases.v1.yaml` | 1.0.0 |
| C8 | Rótulos de resultado | `ui/result-labels.v2.yaml` | 2.0.0 |
| C13 | Registro de una llamada a un modelo | `model_calls/model-call.v1.yaml` | 1.0.0 |
| C13 | Traducción de papeles | `model_calls/role-translation.v1.yaml` | 1.0.0 |
| C15 | Métricas de revisión | `metrics/review.v2.yaml` | 2.0.0 |
| C15 | Métricas del flujo de texto | `metrics/text-flow.v1.yaml` | 1.0.0 |
| C15 | Métricas de voz | `metrics/voice.v1.yaml` | 1.0.0 |
| C15 | Métricas del ciclo de vida de la sesión | `metrics/session-lifecycle.v1.yaml` | 1.0.0 |
| C15 | Métricas del asistente | `metrics/assistant-extras.v1.yaml` | 1.0.0 |
| C15 | Métricas del anonimizador | `metrics/anonymizer.v1.yaml` | 1.0.0 |
| C16 | Salud de cada servicio | `health/health.v2.yaml` | 2.0.0 |
| C18 | Esquema base de perfiles | `profiles/profile-base.schema.v1.yaml` | 1.0.0 |
| C18 | Esquema de perfiles del analizador | `profiles/profiles.schema.v1.yaml` | 1.0.0 |
| C18 | Configuración efectiva | `profiles/effective-config.v1.yaml` | 1.0.0 |
| C18 | Tabla de precios | `profiles/prices.schema.v1.yaml` | 1.0.0 |
| C19 | Reporte de la CLI | `cli/report.schema.v2.yaml` | 2.0.0 |
| C21 | `anonymizer-proxy` por HTTP | `api/anonymizer-proxy.v1.yaml` | 1.0.0 |
| C25 | Catálogo único de límites | `limits.v1.yaml` | 1.0.0 |
| (transversal) | Catálogo de errores | `errors/error-codes.v2.yaml` | 2.0.0 |
| (transversal) | Formato de fecha | `format/datetime.v1.yaml` | 1.0.0 |

La versión del contrato no es la del paquete. El paquete (`[project].version` de `pyproject.toml`) tiene su
propia versión, que es igual a la de su etiqueta (`contracts-v<versión>`); la versión de cada contrato vive en
el contrato (`contrato: "1.0.0"` en C6, `x-veridicus-version` o `info.version` en los propios) y no cambia
cuando sube la del paquete.

## Cómo cambiar un contrato

Flujo F5 de la especificación funcional (BR1.5):

1. La unidad dueña propone el cambio en un PR que solo toca ese contrato.
2. Se clasifica el cambio con versión semántica:
   - un cambio aditivo en un contrato no estricto sube el menor (BR1.3);
   - un cambio de forma en un contrato estricto, o uno incompatible, sube el mayor, cambia el `$id` y el
     `.vN` del nombre, y el productor y los consumidores cambian en el mismo PR (BR1.4). La versión mayor
     es siempre igual al `.vN` del nombre (E-28, E-33).
3. Se añade al menos un *fixture* positivo y uno negativo que ejerciten el cambio. En C8, cada término nuevo
   trae su control negativo (BR5.1). Un *fixture* nuevo solo lleva datos sintéticos.
4. Se regenera lo que corresponda, desde la raíz del repositorio. Solo el humano o el codificador de la
   tarea escriben; la CI nunca regenera, solo comprueba (AUTONOMIA-01):
   - tipos y constantes de TypeScript: `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_ts` (sin `--check` escribe; con `--check` solo compara);
   - vectores JCS: `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_jcs_vectors` (sin `--check` escribe; con `--check` solo compara);
   - huella de la superficie de seguridad: `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.security_surface --write` (sin argumentos compara).
5. La suite corre en CI; en un cambio menor, los *fixtures* anteriores siguen aceptándose.
6. El autor revisa y fusiona con *squash-merge*.

## La copia de C6

C6 (contrato común del analizador) es la copia aprobada del repositorio principal del TG y **no se edita
aquí** (F7, BR1.7). `analyzer/v1/SHA256SUMS` tiene exactamente dos líneas, una por esquema, y la suite
recalcula el SHA-256 de los bytes de cada archivo. Las huellas aprobadas están fijadas en
`tests/conftest.py` (`HUELLAS_APROBADAS_C6`), de modo que nadie puede cambiar la copia recalculando
`SHA256SUMS`. Los dos esquemas declaran `contrato: { const: "1.0.0" }`.

Una versión nueva entra solo con un cambio aprobado en el repositorio principal (ADR-017): el humano copia
los archivos aprobados en su propio PR, anota la ruta de origen y las huellas que recalculó allí, y las compara
con `SHA256SUMS` antes de fusionar (BR1.8). Un cambio de forma abre `analyzer/v2/` y conserva la v1.

## Uso desde un servicio

Los tres ejemplos usan las firmas reales del paquete y datos sintéticos.

`limits.load` devuelve las cifras efectivas: el catálogo `limits.v1.yaml` con las variables
`VERIDICUS_LIMIT_<NOMBRE>` aplicadas. Una variable solo puede bajar una cifra, nunca subirla; si sube una,
nombra un límite que no existe o deja rota una relación del catálogo, lanza `LimitsConfigError`
(`config.invalid_limit`) y el pod no arranca.

```python
import os

from veridicus_contracts import limits

cifras = limits.load(os.environ)
```

`profiles.validate` valida un archivo de perfiles ya cargado y devuelve sus perfiles como valores
inmutables. `key_prefix` es obligatorio (Veridicus pasa `VERIDICUS_`) y `kind` es `"base"` o `"analyzer"`.
Ante un perfil inválido lanza `ProfileValidationError` (`config.invalid_profile`).

```python
from veridicus_contracts import profiles
from veridicus_contracts.loaders import load_yaml_text

datos = load_yaml_text(
    """
schema_version: "1.0.0"
profiles:
  prueba-generica:
    purpose: demonstration
    roles:
      prueba_a: {provider: local, model: modelo-prueba-a, scope: local, base_url: "http://veridicus-llm-a:8080"}
"""
)
perfiles = profiles.validate(datos, key_prefix="VERIDICUS_", kind="base")
```

`registry` construye un registro de referencias con todos los esquemas del paquete, sin salir a la red
(una URI ajena lanza `ForeignUriError`), y `validator_for` da el validador 2020-12 de un esquema por su URI
absoluta (`https://veridicus.invalid/` más su `$id`).

```python
from veridicus_contracts.registry import build_registry, validator_for

registro = build_registry()
validador = validator_for(
    registro, "https://veridicus.invalid/veridicus/contracts/profiles/profiles.schema.v1"
)
errores = list(validador.iter_errors({"schema_version": "1.0.0", "profiles": {}}))
```

## Comandos V-*

Todos corren desde la raíz del repositorio, en CPU y sin red, salvo los marcados «con red». Son los mismos
que corre el *workflow* `.github/workflows/contracts-level0.yml`.

| Clave | Comando | Umbral |
|---|---|---|
| `V-INSTALL` | `uv sync --frozen --directory contracts` (con red) | Código 0 |
| `V-SUITE` | `timeout 60 uv run --frozen --offline --directory contracts pytest` | Verde, 60 s como máximo, 80 % de líneas como mínimo |
| `V-GUARD` | `uv run --frozen --offline --directory contracts coverage report --include="src/veridicus_contracts/checks/*,src/veridicus_contracts/profiles.py,src/veridicus_contracts/limits.py,src/veridicus_contracts/canonical.py,src/veridicus_contracts/registry.py" --fail-under=100` | 100 % de ramas |
| `V-TYPES` | `uv run --frozen --offline --directory contracts mypy --strict src` | 0 errores |
| `V-LINT` | `uv run --frozen --offline --directory contracts ruff check .` | 0 hallazgos |
| `V-AUDIT` | `uv run --frozen --directory contracts pip-audit --format json --output build/pip-audit.json` (con red) y `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.audit_gate build/pip-audit.json --ignore .pip-audit-ignore.yaml` | 0 vulnerabilidades con versión corregida fuera de excepciones vigentes |
| `V-GEN` | `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_ts --check` y `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.gen_jcs_vectors --check` | Sin diferencias |
| `V-SURFACE` | `timeout 60 uv run --frozen --offline --directory contracts pytest tests/tools/test_security_surface.py --no-cov` | Huella regenerada igual al archivo versionado |
| `V-TS` | `npm --prefix contracts/ts ci` (con red), `timeout 60 npm --prefix contracts/ts test`, `npm --prefix contracts/ts run typecheck`, `npm --prefix contracts/ts run lint` y `npm --prefix contracts/ts run gen:check` | Verde, 80 % de líneas como mínimo; 0 errores; sin diferencias |
| `V-TS-AUDIT` | `npm --prefix contracts/ts audit --audit-level=high` (con red) | 0 vulnerabilidades altas con corrección |
| `V-PKG` | `timeout 180 uv run --frozen --directory contracts python -m veridicus_contracts.tools.check_package` | Verde, 180 s como máximo |
| `V-ERRORS` | `uv sync --frozen --directory libs/errors` (con red); `timeout 60 uv run --frozen --offline --directory libs/errors pytest`; `uv run --frozen --offline --directory libs/errors mypy --strict src`; `uv run --frozen --offline --directory libs/errors ruff check .` | Verde, 80 % de líneas como mínimo; 0 errores; 0 hallazgos |
| `V-YAML` | `uv run --frozen --offline --directory contracts yamllint -s ../.github/workflows/contracts-level0.yml ../.pre-commit-config.yaml` | Código 0 |

La etiqueta de la entrega se comprueba con `uv run --frozen --offline --directory contracts python -m veridicus_contracts.tools.check_tag`
(imprime la etiqueta esperada) y, con `--tag ETIQUETA`, sale con 0 solo si es exactamente esa. El *workflow*
la corre al empujar una etiqueta `contracts-v*`.

## Glosario de identificadores

Un identificador de código se escribe en inglés y su traducción del PRD es única: ningún término se traduce
de dos formas (`team.md`, Code Style). Excepción: los campos del contrato común del TG conservan su nombre en
español.

| Identificador | Término del PRD o significado |
|---|---|
| `review_report` | «reporte de revisión»; sustituye a «reporte forense» (D10.4, VE-03) |
| `review_suggestion` | «sugerencia de revisión»: todo hallazgo de la IA, con estado editable que cambia un humano |
| `undocumented_fact` | «Hecho No Documentado»: resultado normal por debajo del umbral, no un error |
| `cancel_token` | token de cancelación cooperativa del almacén de archivos de reportes (NFRD-U7-11) |
| `view_outdated` | `report.view_outdated`, error 409 cuando el resumen cambió desde que el analista lo abrió (NFRD-U7-11) |

## Instalar desde otro repositorio

La línea que `sistema` copia tal cual, en su `pyproject.toml`, con el repositorio, la etiqueta y el
subdirectorio. La etiqueta es `contracts-v` más la versión de `[project].version`; la pone el humano al
fusionar el PR del Bolt (BR12.2).

```toml
[tool.uv.sources]
veridicus-contracts = { git = "https://github.com/freyesJaveriana/tai", tag = "contracts-v0.1.0", subdirectory = "contracts" }
```

La dependencia (`dependencies = ["veridicus-contracts"]`) se añade con `uv add`, que escribe también la
fuente de arriba:

```bash
uv add "veridicus-contracts @ git+https://github.com/freyesJaveriana/tai#subdirectory=contracts" --tag contracts-v0.1.0
```

`tests/test_readme.py` comprueba que la etiqueta de este apartado es la que imprime
`python -m veridicus_contracts.tools.check_tag`, para que al subir la versión el README no se quede atrás.
