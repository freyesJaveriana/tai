"""Doble determinista del `ModelGateway` para las pruebas de nivel 0 y 1 (team.md, Dobles de prueba).

Sin red, sin azar y sin reloj: la misma configuración da siempre las mismas respuestas. Responde por
papel (`judge`, `verifier`, `verifier_permuted`), registra cada petición, también la que falla, y
puede lanzar un error tipado de `model_calls` para un papel.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from veridicus_contracts.model_calls import (
    GenerateRequest,
    GenerateResult,
    ModelCall,
    ModelCallError,
)

_AT = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


class FakeModelGateway:
    """Gateway guionado: el juez devuelve `findings` y los verificadores sus veredictos."""

    def __init__(
        self,
        *,
        findings: Sequence[Mapping[str, Any]] = (),
        verdict_direct: bool = True,
        verdict_permuted: bool = True,
        failures: Mapping[str, ModelCallError] | None = None,
        anonymized: bool = True,
    ) -> None:
        self._findings = [dict(finding) for finding in findings]
        self._verdict_direct = verdict_direct
        self._verdict_permuted = verdict_permuted
        self._failures = dict(failures or {})
        self._anonymized = anonymized
        self.requests: list[GenerateRequest] = []

    def generate(self, request: GenerateRequest) -> GenerateResult:
        self.requests.append(request)
        if request.role in self._failures:
            raise self._failures[request.role]
        content: dict[str, Any]
        if request.role == "judge":
            content = {"hallazgos": list(self._findings)}
        elif request.role == "verifier":
            content = {"confirma": self._verdict_direct}
        else:
            content = {"confirma": self._verdict_permuted}
        external = request.destination.scope == "external"
        call = ModelCall(
            role=request.role,
            provider=request.destination.provider,
            model=request.destination.model,
            input_tokens=10,
            output_tokens=5,
            fallback_provider=request.destination_slot == "fallback",
            anonymized=external and self._anonymized,
            at=_AT,
        )
        return GenerateResult(content=content, altered_markers=[], call=call)
