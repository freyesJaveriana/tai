"""Adaptador `anonymizing`: delega todo destino externo en el `AnonymizingProvider` (BR10.1, BR10.3).

Frontera de salida de datos (AUTONOMIA-04). Reglas que cumple este módulo:

- No reintenta nunca (BR10.3): la llamada pudo haber salido del clúster, así que una segunda
  petición podría duplicar una salida. El proveedor se llama exactamente una vez.
- Deja pasar tal cual los errores tipados de `model_calls` (C13): ya traen su `ModelCall` cuando
  corresponde y el análisis los traduce a su código.
- Cualquier otra excepción del proveedor es un fallo del anonimizador y sale como
  `AnonymizerUnavailable` (BR7.4, R-05). El mensaje nombra solo el **tipo** de la excepción ajena,
  nunca su texto ni su `repr`, porque ese texto podría llevar testimonio; y el error se lanza fuera
  del `except`, para que la excepción original no quede encadenada en `__cause__` ni en
  `__context__`, donde un traceback la mostraría.
"""

from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    AnonymizingProvider,
    GenerateRequest,
    GenerateResult,
    ModelCallError,
)


class AnonymizingAdapter:
    """No reintenta; deja pasar los errores de `model_calls` y traduce cualquier otra excepción
    del proveedor a `AnonymizerUnavailable` (BR7.4)."""

    def __init__(self, provider: AnonymizingProvider) -> None:
        self._provider = provider

    def generate(self, request: GenerateRequest) -> GenerateResult:
        foreign: str | None = None
        try:
            return self._provider.generate(request)
        except ModelCallError:
            raise
        except Exception as error:  # noqa: BLE001 - toda excepción ajena es fallo cerrado
            foreign = type(error).__name__
        raise AnonymizerUnavailable(
            f"el anonimizador falló con una excepción ajena ({foreign}); no se repite la llamada"
        )
