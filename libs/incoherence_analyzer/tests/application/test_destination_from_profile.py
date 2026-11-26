"""Un destino distinto del del perfil no sale (AUTONOMIA-04; candidata de la ronda 1 de U11-T03).

El gateway real y el `Anonymizer` real de B10a van detrás de un envoltorio que cambia el `destination`
de cada petición antes de entregarla. Si el anonimizador lo rechaza, la corrida termina en
`anonimizador_no_disponible` y el transporte no registra ninguna petición.
"""

from dataclasses import replace
from typing import Any

import pytest
from veridicus_anonymizer.api import build_anonymizer
from veridicus_contracts.model_calls import Destination, GenerateRequest, GenerateResult
from veridicus_model_gateway.gateway import build
from veridicus_model_gateway.port import ModelGateway

from tests.support import (
    ScriptedProvider,
    assert_error_output,
    echo_finding,
    env,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze


class _Tampering:
    """Cambia el destino de cada petición antes de pasarla al gateway real."""

    def __init__(self, inner: ModelGateway, **changes: Any) -> None:
        self._inner = inner
        self._changes = changes
        self.seen: list[Destination] = []

    def generate(self, request: GenerateRequest) -> GenerateResult:
        destination = replace(request.destination, **self._changes)
        self.seen.append(destination)
        return self._inner.generate(replace(request, destination=destination))


@pytest.mark.parametrize(
    "changes",
    [
        {"model": "claude-modelo-que-no-es-del-perfil"},
        {"provider": "openai"},
        {"api_key_ref": "VERIDICUS_OTRA_CLAVE"},
    ],
    ids=["otro_modelo", "otro_proveedor", "otra_clave"],
)
def test_a_destination_that_is_not_the_profiles_does_not_leave(changes: dict[str, str]) -> None:
    config = make_config()
    provider = ScriptedProvider(echo_finding)
    real = build(config, anonymizing_provider=build_anonymizer(env(), provider))
    gateway = _Tampering(real, **changes)

    salida = analyze(make_entrada(), config, gateway)

    assert gateway.seen, "la petición sí llegó al gateway real"
    assert_error_output(salida, "anonimizador_no_disponible")
    assert provider.request_count == 0, "nada salió hacia el proveedor"


def test_control_the_untouched_destination_does_leave() -> None:
    config = make_config()
    provider = ScriptedProvider(echo_finding)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))

    salida = analyze(make_entrada(), config, gateway)

    assert salida["estado"] == "ok"
    assert provider.request_count == 3
