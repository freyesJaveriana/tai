"""Salida C6 (BR8.1, BR8.6, BR8.7): toda salida valida contra el esquema común antes de devolverse.

Una salida armada que no valida se sustituye por la salida en error `salida_invalida`, que también
valida. La biblioteca no emite `observaciones_conductor` y la misma entrada da la misma salida.
"""

import copy
from collections.abc import Mapping
from typing import Any

import pytest

from tests.support import (
    T1,
    ScriptedGateway,
    assert_error_output,
    c6_problems,
    finding,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.domain import output


def _without_dates(salida: dict[str, Any]) -> dict[str, Any]:
    clean = copy.deepcopy(salida)
    clean.pop("fecha", None)
    for llamada in clean["registro"]["llamadas"]:
        llamada.pop("fecha", None)
    return clean


def test_the_output_of_a_synthetic_run_validates_against_the_c6_schema() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert c6_problems(salida) == []
    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) == 1
    assert salida["hallazgos"][0]["id"] == "SINT-0001-C01"
    assert salida["perfil"] == "demo-anthropic"


def test_the_output_of_a_run_without_findings_validates_too() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[])

    salida = analyze(make_entrada(), config, gateway)

    assert c6_problems(salida) == []
    assert salida["hallazgos"] == []
    assert gateway.roles() == ["judge"]


def test_an_assembled_output_that_does_not_validate_is_replaced_by_salida_invalida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config()

    def without_observaciones(
        finding_id: str, candidate: Mapping[str, Any], turns: Mapping[int, Mapping[str, Any]]
    ) -> dict[str, Any]:
        """Un hallazgo armado a propósito sin `observaciones` (BR8.1): C6 lo rechaza."""
        return {
            "id": finding_id,
            "hecho": candidate["hecho"],
            "tipo": candidate["tipo"],
            "cita_a": dict(candidate["cita_a"]),
            "cita_b": dict(candidate["cita_b"]),
        }

    # Costura (docstring de `domain.output`): `analyze` arma cada hallazgo con `output.build_finding`.
    monkeypatch.setattr(output, "build_finding", without_observaciones)
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    # BR7.1: la salida sustituta conserva el registro de las llamadas que ya se hicieron.
    assert [llamada["papel"] for llamada in salida["registro"]["llamadas"]] == [
        "juez",
        "verificador",
        "verificador_permutado",
    ]


def test_the_library_never_emits_conductor_observations() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert "observaciones_conductor" not in salida


def test_the_same_input_gives_the_same_output_except_for_dates() -> None:
    config = make_config()

    first = analyze(make_entrada(), config, ScriptedGateway(findings=[finding()]))
    second = analyze(make_entrada(), config, ScriptedGateway(findings=[finding()]))

    assert _without_dates(first) == _without_dates(second)


def test_finding_ids_do_not_depend_on_the_order_of_the_judge_answer() -> None:
    config = make_config()
    first_pair = finding()
    second_pair = finding(hecho="Otro hecho", a=(1, T1))

    forward = analyze(make_entrada(), config, ScriptedGateway(findings=[first_pair, second_pair]))
    backward = analyze(make_entrada(), config, ScriptedGateway(findings=[second_pair, first_pair]))

    assert [h["id"] for h in forward["hallazgos"]] == [h["id"] for h in backward["hallazgos"]]
    assert [h["hecho"] for h in forward["hallazgos"]] == [h["hecho"] for h in backward["hallazgos"]]
