"""AUTONOMIA-05, fallo cerrado: `estado: error` implica hallazgos vacíos (BR7.1, BR5.1, BR6.4).

Nunca sale un resultado parcial: ni cuando falla el juez, ni cuando falla el verificador después de
que un candidato ya pasó el filtro, ni cuando un candidato viene mal formado entre varios buenos.
"""

import pytest
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCallError,
    ProviderError,
    Timeout,
)

from tests.support import (
    ScriptedGateway,
    assert_error_output,
    finding,
    make_call,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze


def _error(kind: str, role: str) -> ModelCallError:
    if kind == "anonymizer":
        return AnonymizerUnavailable("anonimizador no disponible")
    call = make_call(role)
    errors: dict[str, ModelCallError] = {
        "invalid": InvalidOutput("salida inválida", call),
        "blocked": ContentBlocked("contenido bloqueado", call),
        "timeout": Timeout("plazo agotado", call),
        "provider": ProviderError("fallo del proveedor", call),
    }
    return errors[kind]


CASES = [
    ("invalid", "salida_invalida"),
    ("blocked", "bloqueo_contenido"),
    ("timeout", "tiempo_agotado"),
    ("provider", "proveedor"),
    ("anonymizer", "anonimizador_no_disponible"),
]


@pytest.mark.parametrize(("kind", "codigo"), CASES, ids=[kind for kind, _ in CASES])
def test_every_gateway_error_on_the_judge_gives_an_error_output_with_nothing_partial(
    kind: str, codigo: str
) -> None:
    config = make_config()
    gateway = ScriptedGateway(fail={"judge": _error(kind, "judge")})

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, codigo)
    assert gateway.roles() == ["judge"]


@pytest.mark.parametrize(("kind", "codigo"), CASES, ids=[kind for kind, _ in CASES])
def test_an_error_on_the_verifier_discards_the_finding_that_already_passed_the_filter(
    kind: str, codigo: str
) -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()], fail={"verifier": _error(kind, "verifier")})

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, codigo)
    assert gateway.roles() == ["judge", "verifier"]


def test_a_malformed_candidate_among_valid_ones_invalidates_the_whole_run() -> None:
    config = make_config()
    malformed = finding(hecho="Otro hecho")
    malformed["extra"] = "campo que el esquema no admite"
    gateway = ScriptedGateway(findings=[finding(), malformed, finding(hecho="Tercero")])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.roles() == ["judge"]


def test_a_verifier_answer_that_is_not_exactly_a_boolean_invalidates_the_run() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()], verifier_content={"confirma": "si"})

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
