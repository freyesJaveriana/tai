"""El flujo de `analyze` (F2 a F7): peticiones, verificador, permutación, errores y salida.

Complementa las guardias congeladas de `tests/guards`: aquí se comprueban las peticiones que salen
hacia el gateway, el orden de las llamadas, los dos motivos del verificador y los bordes de la
traducción de errores.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from veridicus_contracts.model_calls import AnonymizerUnavailable, ModelCallError, ProviderError
from veridicus_errors import SystemInternalError
from veridicus_model_gateway.testing.fake import FakeModelGateway

from tests.application.profiles_support import anthropic_profile
from tests.support import (
    MODEL,
    T1,
    T2,
    T4,
    ScriptedGateway,
    assert_error_output,
    c6_problems,
    discard_reasons,
    finding,
    make_call,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.application import analyze as analyze_module
from veridicus_incoherence_analyzer.application.messages import load_response_schema


def _user(request: Any) -> dict[str, Any]:
    users = [message.content for message in request.messages if message.role == "user"]
    assert len(users) == 1
    parsed: dict[str, Any] = json.loads(users[0])
    return parsed


# --- Las peticiones ------------------------------------------------------------------------------


def test_the_requests_carry_the_destination_of_the_profile_and_the_wire_schema() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()])

    analyze(make_entrada(), config, gateway)

    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
    for request in gateway.requests:
        assert request.destination_slot == "primary"
        assert request.profile_name == "demo-anthropic"
        assert request.profile_sha256 == config.profile_sha256
        assert (request.destination.provider, request.destination.model) == ("anthropic", MODEL)
        assert request.destination.scope == "external"
        assert request.destination.api_key_ref == "VERIDICUS_ANTHROPIC_API_KEY"
        assert request.seed is None
        assert isinstance(request.timeout_s, float)
    assert gateway.requests[0].schema == load_response_schema("judge", "wire")
    assert gateway.requests[1].schema == load_response_schema("verifier", "wire")
    assert gateway.requests[2].schema == load_response_schema("verifier", "wire")


def test_the_seed_of_the_profile_travels_in_every_request(tmp_path: Path) -> None:
    config = anthropic_profile(tmp_path, seed=7)
    gateway = ScriptedGateway(findings=[finding()])

    analyze(make_entrada(), config, gateway)

    assert [request.seed for request in gateway.requests] == [7, 7, 7]
    assert all(request.destination.parameters == {"seed": 7} for request in gateway.requests)


def test_the_judge_receives_every_turn_in_order_of_number() -> None:
    turns = [
        {"n": 4, "hablante": "TEST", "texto": T4},
        {"n": 1, "hablante": "ENT", "texto": T1},
        {"n": 2, "hablante": "TEST", "texto": T2, "estado": "plegado"},
    ]
    gateway = ScriptedGateway()

    analyze(make_entrada(turns), make_config(), gateway)

    sent = _user(gateway.requests[0])["turnos"]
    assert [turn["n"] for turn in sent] == [1, 2, 4]
    assert sent[1]["estado"] == "plegado"
    assert "estado" not in sent[0]


def test_the_verifier_receives_only_the_four_fields_and_the_permutation_swaps_the_quotes() -> None:
    gateway = ScriptedGateway(findings=[finding()])

    analyze(make_entrada(), make_config(), gateway)

    direct, permuted = _user(gateway.requests[1]), _user(gateway.requests[2])
    assert set(direct) == set(permuted) == {"hecho", "tipo", "cita_a", "cita_b"}
    assert "observaciones" not in json.dumps(direct)
    assert direct["cita_a"]["turno"] == "T2" and direct["cita_b"]["turno"] == "T4"
    assert permuted["cita_a"] == direct["cita_b"] and permuted["cita_b"] == direct["cita_a"]


# --- El verificador y la permutación --------------------------------------------------------------


def test_each_survivor_is_verified_in_order_of_the_first_cited_turn_direct_before_permuted() -> (
    None
):
    later = finding(hecho="Segundo hecho", a=(2, T2), b=(4, T4))
    earlier = finding(hecho="Primer hecho", a=(1, T1), b=(4, T4))
    gateway = ScriptedGateway(findings=[later, earlier])  # el juez los entrega al revés

    salida = analyze(make_entrada(), make_config(), gateway)

    assert gateway.roles() == [
        "judge",
        "verifier",
        "verifier_permuted",
        "verifier",
        "verifier_permuted",
    ]
    assert _user(gateway.requests[1])["hecho"] == "Primer hecho"
    assert _user(gateway.requests[3])["hecho"] == "Segundo hecho"
    assert [h["hecho"] for h in salida["hallazgos"]] == ["Primer hecho", "Segundo hecho"]


def test_a_repeated_pair_gets_one_verification_and_one_finding() -> None:
    gateway = ScriptedGateway(findings=[finding(), finding(hecho="Mismo par, otro hecho")])

    salida = analyze(make_entrada(), make_config(), gateway)

    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
    assert len(salida["hallazgos"]) == 1


def test_a_candidate_that_the_verifier_does_not_confirm_is_discarded_and_the_permutation_still_runs() -> (
    None
):
    gateway = ScriptedGateway(findings=[finding()], verdict_direct=False)

    salida = analyze(make_entrada(), make_config(), gateway)

    assert salida["estado"] == "ok"
    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["rechazado_verificador"]
    assert salida["registro"]["descartes"][0] == {
        "motivo": "rechazado_verificador",
        "turno_a": "T2",
        "turno_b": "T4",
    }
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"], "siempre las dos"
    assert c6_problems(salida) == []


def test_a_candidate_confirmed_only_in_the_direct_order_is_discarded_as_permutation() -> None:
    gateway = ScriptedGateway(findings=[finding()], verdict_permuted=False)

    salida = analyze(make_entrada(), make_config(), gateway)

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["rechazado_permutacion"]
    assert c6_problems(salida) == []


def test_a_candidate_rejected_by_both_orders_is_discarded_as_the_direct_verifier() -> None:
    gateway = ScriptedGateway(findings=[finding()], verdict_direct=False, verdict_permuted=False)

    salida = analyze(make_entrada(), make_config(), gateway)

    assert discard_reasons(salida) == ["rechazado_verificador"]


def test_without_permutation_there_is_one_verifier_call_per_survivor(tmp_path: Path) -> None:
    config = anthropic_profile(tmp_path, permutation=False)
    gateway = ScriptedGateway(findings=[finding()], verdict_permuted=False)

    salida = analyze(make_entrada(), config, gateway)

    assert gateway.roles() == ["judge", "verifier"]
    assert len(salida["hallazgos"]) == 1, "la permutación apagada no rechaza"


def test_discarded_candidates_never_reach_the_verifier_and_the_survivor_does() -> None:
    invented = finding(hecho="Inventado", a=(2, "Texto que no está en ningún turno."))
    gateway = ScriptedGateway(findings=[invented, finding()])

    salida = analyze(make_entrada(), make_config(), gateway)

    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"], "exactamente k = 1"
    assert discard_reasons(salida) == ["cita_no_verificada"]
    assert len(salida["hallazgos"]) == 1


def test_the_discards_of_the_filter_come_before_those_of_the_verifier() -> None:
    invented = finding(hecho="Inventado", a=(2, "Texto que no está en ningún turno."))
    gateway = ScriptedGateway(findings=[finding(), invented], verdict_direct=False)

    salida = analyze(make_entrada(), make_config(), gateway)

    assert discard_reasons(salida) == ["cita_no_verificada", "rechazado_verificador"]


# --- Fallo cerrado y errores -----------------------------------------------------------------------


def test_a_failure_of_the_permuted_verifier_discards_everything_that_was_confirmed() -> None:
    first = finding(hecho="Primero", a=(1, T1), b=(4, T4))
    second = finding(hecho="Segundo")
    error = ProviderError("fallo del proveedor", make_call("verifier_permuted"))
    gateway = ScriptedGateway(findings=[first, second], fail={"verifier_permuted": error})

    salida = analyze(make_entrada(), make_config(), gateway)

    assert_error_output(salida, "proveedor")
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
    assert [llamada["papel"] for llamada in salida["registro"]["llamadas"]] == [
        "juez",
        "verificador",
        "verificador_permutado",
    ], "el fallo trae su registro y cuenta"


def test_an_error_without_a_call_record_adds_no_row() -> None:
    gateway = ScriptedGateway(findings=[finding()], fail={"judge": AnonymizerUnavailable("caído")})

    salida = analyze(make_entrada(), make_config(), gateway)

    assert_error_output(salida, "anonimizador_no_disponible")
    assert salida["registro"]["llamadas"] == []


def test_a_model_call_error_without_a_code_is_a_defect_and_propagates() -> None:
    class Unknown(ModelCallError):
        pass

    gateway = ScriptedGateway(fail={"judge": Unknown("sin código")})

    with pytest.raises(TypeError):
        analyze(make_entrada(), make_config(), gateway)


def test_an_exception_that_is_not_from_the_model_propagates_and_is_not_an_error_state() -> None:
    gateway = ScriptedGateway(fail={"judge": RuntimeError("defecto propio")})

    with pytest.raises(RuntimeError):
        analyze(make_entrada(), make_config(), gateway)


@pytest.mark.parametrize("content", [{"otra": 1}, {"hallazgos": "no"}, {}], ids=str)
def test_a_judge_answer_with_another_shape_invalidates_the_run(content: dict[str, Any]) -> None:
    gateway = ScriptedGateway(judge_content=content)

    salida = analyze(make_entrada(), make_config(), gateway)

    assert_error_output(salida, "salida_invalida")
    assert len(salida["registro"]["llamadas"]) == 1


@pytest.mark.parametrize("content", [{"confirma": 1}, {"confirma": None}, {"x": True}], ids=str)
def test_a_verifier_answer_that_is_not_exactly_a_boolean_invalidates_the_run(
    content: dict[str, Any],
) -> None:
    gateway = ScriptedGateway(findings=[finding()], verifier_content=content)

    salida = analyze(make_entrada(), make_config(), gateway)

    assert_error_output(salida, "salida_invalida")


def test_the_replacement_output_that_does_not_validate_is_a_defect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analyze_module, "_is_valid", lambda salida: False)
    gateway = ScriptedGateway(findings=[finding()])

    with pytest.raises(SystemInternalError):
        analyze(make_entrada(), make_config(), gateway)


# --- Con el doble determinista del gateway ----------------------------------------------------------


def test_with_the_deterministic_fake_the_run_is_ok_and_valid() -> None:
    gateway = FakeModelGateway(findings=[finding()])

    salida = analyze(make_entrada(), make_config(), gateway)

    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) == 1
    assert [request.role for request in gateway.requests] == [
        "judge",
        "verifier",
        "verifier_permuted",
    ]
    assert c6_problems(salida) == []
