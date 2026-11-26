"""El puerto `ModelGateway` (C13): una sola operación, `generate`."""

from typing import Protocol

from veridicus_contracts.model_calls import GenerateRequest, GenerateResult


class ModelGateway(Protocol):
    """Puerta de las llamadas a modelos; solo lanza los errores tipados de `model_calls` (C13)."""

    def generate(self, request: GenerateRequest) -> GenerateResult: ...
