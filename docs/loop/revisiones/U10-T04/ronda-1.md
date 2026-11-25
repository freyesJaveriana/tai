# Ronda 1 — U10-T04

**VEREDICTO: NO-VERDE.** Los seis criterios (CA-1 a CA-6) pasan con mis propias corridas. Quedan cinco NARANJA en pie: cuatro los demostré con una sonda o un mutante, y el quinto es una viñeta del plan sin implementar (F-05). No hay ningún ROJO. El worktree quedó limpio (`git status --porcelain` vacío) y no se tocó `domain/` ni `contracts/`.

## Criterios, verificados por mí (rutas absolutas del worktree)
| # | Comando | Resultado |
|---|---|---|
| — | `uv sync --frozen --directory …/libs/anonymizer` | 0 |
| CA-1 | `pytest tests/providers --cov=…providers --cov-branch --cov-fail-under=100` | 54 pasan, 100 % de ramas |
| CA-2 | `uv lock --check` | 0 |
| CA-2 | `pytest tests/guards tests/contracts tests/application --cov=…application --cov=…api --cov-branch --cov-fail-under=100` | 132 pasan, 100 % de ramas |
| CA-2 | `grep` de `veridicus-contracts` y de la versión en `uv.lock` | 0.1.1 en la línea 1676 |
| CA-3 | `git -C … diff --exit-code afa8f20 -- tests/guards tests/contracts tests/support.py tests/fixtures` | 0, sin cambios |
| CA-4 | `lint-imports` | 3 contratos KEPT |
| CA-4 | `pytest tests/boundaries --no-cov -q` | 11 pasan |
| CA-5 | `pytest -p no:cacheprovider` | 401 pasan, 0 FAILED y 0 ERROR |
| CA-6 | `mypy --strict src tests`, `ruff check .`, `ruff format --check .` | limpios |
| CA-6 | las 3 guardias `scripts/check-no-*.sh` | `0 apariciones` cada una |

No corrí `uv lock` sin `--check`, porque reescribe el lock y un revisor no debe hacerlo.

## Hallazgos

**F-01 · NARANJA · `application/generate.py:134-152` y `providers/anthropic.py:101,125` · Una excepción inesperada antes del envío no sale como `AnonymizerUnavailable`**
- **Qué falla:** BR2.1 y el paso 10 exigen que *cualquier* excepción previa al envío salga como `AnonymizerUnavailable`. Solo `_mask` la traduce.
- **Prueba:** mandé un `req.schema` anidado a 3000 niveles por `generate`. Salió un `RecursionError` crudo, con 0 peticiones: el fallo cerrado se cumple, pero no el error tipado.
- **Puntos afectados (barrido):** `catalogs.domains[...]` (l. 75); `_replacements` (l. 139); `check_schema` y `json.dumps` en `_build_body`, que no capturan `RecursionError`; `_headers`.
- **Corrección:** envolver toda la región previa al envío en un solo `try/except Exception` y lanzar `AnonymizerUnavailable` fuera del `except`. Añadir la prueba del esquema profundo.

**F-02 · NARANJA · `pyproject.toml:81-85` · El contrato `anonymizer-independent` prohíbe nombres que no usará ningún paquete**
- **Qué falla:** el contrato prohíbe `model_gateway`, `execution_profiles` e `incoherence_analyzer`. Pero la convención de PD-3 (`veridicus_errors`, `veridicus_contracts`, `veridicus_anonymizer`) apunta a nombres con prefijo.
- **Prueba:** en una copia del paquete, un módulo que importa los tres nombres con prefijo `veridicus_` deja `lint-imports` en 0 con «3 kept».
- **Corrección:** prohibir también las formas con prefijo y añadir un control negativo con ellas.

**F-03 · NARANJA · `pyproject.toml:98-103` · El contrato `anonymizer-testing-not-in-production` deja fuera la raíz del paquete**
- **Qué falla:** el paso 11 pide que nada de `src/` fuera de `testing/` importe `testing`. El contrato no cubre `veridicus_anonymizer/__init__.py` ni ningún módulo nuevo de primer nivel.
- **Prueba:** en una copia, añadir la importación de `bypass` al `__init__.py` raíz deja `lint-imports` en 0.
- **Corrección:** cubrir el módulo raíz sin sus descendientes y añadir un control negativo en `__init__`.

**F-04 · NARANJA · ML-11, sonda del presupuesto agotado · La prueba no detecta si falta la conexión con NFR3.5**
- **Qué falla:** la prueba no distingue entre agotar el presupuesto de la seudonimización y agotar el plazo total.
- **Prueba:** un mutante que pasa a `pseudonymize` un `has_budget` que siempre devuelve verdadero deja **las 401 pruebas en verde**. El caso del rojo usa un reloj que adelanta 1000 s por lectura, así que siempre termina en «se agotó el plazo antes de enviar», y su palabra clave «plazo» lo da por bueno.
- **Corrección:** una prueba en `tests/application` donde el reloj solo avance dentro de `pseudonymize` y el plazo restante siga siendo positivo. Debe exigir `MaskingBudgetExceeded`, es decir, el mensaje «presupuesto».

**F-05 · NARANJA · `api.py:57-69`, PD-7 y la fila de ML-14 · `build_anonymizer` no lanza los errores de `libs/errors` que pide el plan**
- **Qué falla:** el paso 10 dice: «falla con el error de configuración de `libs/errors`». `libs/errors` existe y trae `ConfigInvalidProfileError` y `ConfigInvalidLimitError`. El código propaga `CatalogError` y `LimitsConfigError`.
- **Lo que declara el codificador:** que no hay dependencia de `libs/errors`. Ninguna prueba roja lo exige, pero sí contradice el plan aprobado. Además, la tabla de autorrevisión lo marca como cubierto.
- **Corrección:** traducir a los errores de `veridicus_errors` y añadir la dependencia.

**Amarillos (no bloquean):**
- **F-06** `anthropic.py:149-166`: el «plazo total» no está garantizado. El plazo de `httpx` es por operación y el reloj solo se mira al llegar un bloque, así que una respuesta lenta puede acercarse al doble de `timeout_s`. Hay que documentar ese límite o acotar cada lectura.
- **F-07** `anthropic.py:159`: `iter_bytes` descomprime antes de medir el tope. Conviene usar `iter_raw` y rechazar todo `content-encoding` distinto de `identity`, y añadir una prueba con cuerpo por trozos sin `content-length`.
- **F-08** `test_properties.py:70`: la propiedad genera los tres roles y los escapes, pero `system` solo recibe textos fijos, nunca las formas sonda.
- **F-09** `pyproject.toml:10-14`: `jsonschema` se importa directamente pero solo llega como dependencia de `contracts`; hay que declararla.
- **F-10** `http.py:36-37`: `build_client` cambia el nivel global de los *loggers* de `httpx` y `httpcore` en el proceso de quien lo usa.

## Sobre lo que declaró el codificador
- **`testing/bypass.py`:** el cambio es válido. Está fuera del candado y es necesario para la nueva firma con `has_budget`.
- **`max_tokens`:** la constante 16000 es aceptable, porque la tabla de capacidades no trae el valor.
- **Proyección del esquema (NFRD-U10-03) y `cache_control` (NFRD-U10-12):** ningún paso de 9 a 11 los pide. Son candidatas legítimas.
- **ML-11:** todas las demás sondas fallarían con una implementación mala.
- **ML-12:** se cumple, con la salvedad de F-08.
- **ML-14:** la tabla cubre las viñetas, salvo la de `libs/errors` (F-05).
- **API de Anthropic:** no pude contrastarla por MCP en esta sesión; queda la cita del orquestador en la bitácora.

## Tareas candidatas (fuera de alcance)
- `ModelGateway` (U11) debe traducir los errores de configuración del módulo, si se mantuviera el diseño actual de F-05.

```
VEREDICTO: NO-VERDE
NARANJA|libs/anonymizer/src/veridicus_anonymizer/application/generate.py:134|Excepción inesperada antes del envío sale cruda (RecursionError), no AnonymizerUnavailable (BR2.1)
NARANJA|libs/anonymizer/pyproject.toml:81|anonymizer-independent prohíbe nombres sin prefijo; veridicus_model_gateway y similares pasan
NARANJA|libs/anonymizer/pyproject.toml:98|anonymizer-testing-not-in-production no cubre el __init__ raíz
NARANJA|ML-11 sonda presupuesto agotado|Mutante sin has_budget pasa las 401 pruebas
NARANJA|libs/anonymizer/src/veridicus_anonymizer/api.py:57|PD-7: build_anonymizer no lanza los errores de libs/errors; ML-14 lo da por cubierto
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/providers/anthropic.py:149|Plazo por operación, no total
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/providers/anthropic.py:159|Tope medido tras descomprimir; falta prueba por trozos
AMARILLO|libs/anonymizer/tests/application/test_properties.py:70|system nunca recibe formas sonda
AMARILLO|libs/anonymizer/pyproject.toml:10|jsonschema no declarada como dependencia directa
AMARILLO|libs/anonymizer/src/veridicus_anonymizer/providers/http.py:36|Cambia el nivel global de los loggers de httpx
INFORME: docs/loop/revisiones/U10-T04/ronda-1.md
```
