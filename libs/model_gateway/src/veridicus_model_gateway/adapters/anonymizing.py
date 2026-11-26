"""Adaptador `anonymizing`: delega todo destino externo en el `AnonymizingProvider` (BR10.1, BR10.3).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T03.
"""

from veridicus_contracts.model_calls import AnonymizingProvider, GenerateRequest, GenerateResult


class AnonymizingAdapter:
    """No reintenta; deja pasar los errores de `model_calls` y traduce cualquier otra excepción
    del proveedor a `AnonymizerUnavailable` (BR7.4)."""

    def __init__(self, provider: AnonymizingProvider) -> None:
        self._provider = provider

    def generate(self, request: GenerateRequest) -> GenerateResult:
        raise NotImplementedError("AnonymizingAdapter.generate: lo implementa U11-T03 (paso 6)")
