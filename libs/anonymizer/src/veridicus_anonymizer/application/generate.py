"""Orquestación de una llamada `generate` (F1, F7).

STUB de U10-T02: lo implementa U10-T04 (paso 10). Contrato que fijan las pruebas rojas: este
módulo llama a `pseudonymize` y a `restore` por su nombre global, importados con
`from ... import`, para que las pruebas (y el control negativo `testing.bypass`) puedan
sustituirlos con `monkeypatch.setattr(generate, "pseudonymize", ...)`.
"""

from time import monotonic as now

from veridicus_contracts.model_calls import GenerateRequest, GenerateResult

from veridicus_anonymizer.domain.masking import pseudonymize
from veridicus_anonymizer.domain.restoration import restore

# `now` es el reloj del presupuesto de la seudonimización (NFR3.5): se lee por su nombre global
# de este módulo y las pruebas lo sustituyen, porque `build_anonymizer` no recibe reloj (PD-7).
__all__ = ["generate_call", "now", "pseudonymize", "restore"]


def generate_call(request: GenerateRequest) -> GenerateResult:
    """Una llamada completa; la implementa U10-T04."""
    raise NotImplementedError("generate_call lo implementa U10-T04")
