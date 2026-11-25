"""Orquestación de una llamada `generate` (F1, F7).

STUB de U10-T02: lo implementa U10-T04 (paso 10). Contrato que fijan las pruebas rojas: este
módulo llama a `pseudonymize` y a `restore` por su nombre global, importados con
`from ... import`, para que las pruebas (y el control negativo `testing.bypass`) puedan
sustituirlos con `monkeypatch.setattr(generate, "pseudonymize", ...)`.
"""

from veridicus_contracts.model_calls import GenerateRequest, GenerateResult

from veridicus_anonymizer.domain.masking import pseudonymize
from veridicus_anonymizer.domain.restoration import restore

__all__ = ["generate_call", "pseudonymize", "restore"]


def generate_call(request: GenerateRequest) -> GenerateResult:
    """Una llamada completa; la implementa U10-T04."""
    raise NotImplementedError("generate_call lo implementa U10-T04")
