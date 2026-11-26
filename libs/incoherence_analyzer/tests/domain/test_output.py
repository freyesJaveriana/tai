"""Armado de la salida C6 (BR8.1 a BR8.7, BR5.7, BR7.1): hallazgo, registro de llamadas y error."""

from datetime import UTC, datetime, timedelta, timezone
from importlib.resources import files
from typing import Any

import pytest
from veridicus_contracts.loaders import load_file
from veridicus_contracts.model_calls import ModelCall

from tests.support import (
    MODEL,
    T1,
    T2,
    T3,
    T4,
    assert_error_output,
    c6_problems,
    default_turns,
    discard_reasons,
    finding,
    make_call,
    make_config,
)
from veridicus_incoherence_analyzer.domain.filter import (
    Discard,
    Survivor,
    Window,
    filter_candidates,
)
from veridicus_incoherence_analyzer.domain.output import (
    ROLE_NAMES,
    assemble_findings,
    build_call,
    build_finding,
    build_output,
)

DATE = datetime(2026, 11, 26, 15, 30, 45, tzinfo=UTC)


def turns_by_number(turns: list[dict[str, Any]] | None = None) -> dict[int, dict[str, Any]]:
    return {turn["n"]: turn for turn in (default_turns() if turns is None else turns)}


def survivors_of(candidates: list[dict[str, Any]]) -> tuple[Survivor, ...]:
    return filter_candidates([Window(candidates, [])], turns_by_number()).survivors


def test_the_role_table_is_exactly_the_one_u1_publishes() -> None:
    published = load_file(files("veridicus_contracts") / "model_calls" / "role-translation.v1.yaml")

    assert dict(ROLE_NAMES) == published["translation"]


def test_a_finding_carries_the_judge_fields_and_the_turn_page() -> None:
    built = build_finding("SINT-0001-C01", finding(), turns_by_number())

    assert built["id"] == "SINT-0001-C01"
    assert built["hecho"] == finding()["hecho"]
    assert built["tipo"] == "lugar"
    assert built["observaciones"] == finding()["observaciones"]
    assert built["cita_a"] == {"cita": T2, "turno": "T2", "pagina": 1}
    assert built["cita_b"] == {"cita": T4, "turno": "T4", "pagina": 2}
    assert set(built) == {"id", "hecho", "tipo", "cita_a", "cita_b", "observaciones"}


def test_a_turn_without_page_gives_a_quote_without_page_and_without_notices() -> None:
    turns = default_turns()
    del turns[1]["pagina"]

    built = build_finding("SINT-0001-C01", finding(), turns_by_number(turns))

    assert built["cita_a"] == {"cita": T2, "turno": "T2"}


def test_an_interviewer_turn_adds_its_notice() -> None:
    built = build_finding("X-C01", finding(a=(1, T1)), turns_by_number())

    assert built["cita_a"]["avisos"] == ["turno_entrevistador"]
    assert "pagina" not in built["cita_a"]
    assert "avisos" not in built["cita_b"]


def test_a_folded_turn_adds_its_notice_and_keeps_its_page() -> None:
    turns = default_turns()
    turns[1]["estado"] = "plegado"

    built = build_finding("X-C01", finding(), turns_by_number(turns))

    assert built["cita_a"]["avisos"] == ["turno_plegado"]
    assert built["cita_a"]["pagina"] == 1


def test_an_interviewer_turn_that_is_also_folded_carries_both_notices_in_a_fixed_order() -> None:
    turns = default_turns()
    turns[0]["estado"] = "plegado"

    built = build_finding("X-C01", finding(a=(1, T1)), turns_by_number(turns))

    assert built["cita_a"]["avisos"] == ["turno_entrevistador", "turno_plegado"]


def test_the_turn_label_is_canonical_even_if_the_judge_padded_it() -> None:
    candidate = finding()
    candidate["cita_a"]["turno"] = "T02"

    assert build_finding("X-C01", candidate, turns_by_number())["cita_a"]["turno"] == "T2"


def test_the_finding_does_not_alias_the_candidate() -> None:
    candidate = finding()

    built = build_finding("X-C01", candidate, turns_by_number())
    built["cita_a"]["cita"] = "cambiado"

    assert candidate["cita_a"]["cita"] == T2


def test_assembled_findings_are_numbered_by_the_first_cited_turn_whatever_the_input_order() -> None:
    late = finding(hecho="Tarde", a=(3, T3), b=(4, T4))
    early = finding(hecho="Temprano", a=(1, T1), b=(4, T4))

    forward = assemble_findings("SINT-0001", survivors_of([late, early]), turns_by_number())
    backward = assemble_findings("SINT-0001", survivors_of([early, late]), turns_by_number())

    assert [h["id"] for h in forward] == ["SINT-0001-C01", "SINT-0001-C02"]
    assert [h["hecho"] for h in forward] == ["Temprano", "Tarde"]
    assert forward == backward


def test_assembled_findings_use_the_module_level_build_finding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from veridicus_incoherence_analyzer.domain import output

    seen: list[str] = []

    def spy(
        finding_id: str, candidate: Any, turns: Any
    ) -> dict[str, Any]:  # la costura de BR8.1 (test_c6_output)
        seen.append(finding_id)
        return {"id": finding_id}

    monkeypatch.setattr(output, "build_finding", spy)

    assert assemble_findings("E", survivors_of([finding()]), turns_by_number()) == [{"id": "E-C01"}]
    assert seen == ["E-C01"]


def test_a_call_is_copied_with_the_fixed_role_table_and_omits_what_is_none() -> None:
    record = build_call(make_call("verifier_permuted"))

    assert record == {
        "papel": "verificador_permutado",
        "proveedor": "anthropic",
        "modelo": MODEL,
        "tokens_entrada": 120,
        "tokens_salida": 30,
        "proveedor_alterno": False,
        "anonimizado": True,
        "fecha": "2026-11-26T12:00:00Z",
    }


@pytest.mark.parametrize(
    ("role", "name"),
    [
        ("judge", "juez"),
        ("verifier", "verificador"),
        ("verifier_permuted", "verificador_permutado"),
    ],
)
def test_each_analyzer_role_has_its_spanish_name(role: str, name: str) -> None:
    assert build_call(make_call(role))["papel"] == name


def test_a_role_outside_the_table_is_a_code_defect_and_is_not_translated() -> None:
    with pytest.raises(KeyError):
        build_call(make_call("otro_papel"))


def test_optional_fields_of_a_call_appear_only_when_they_have_a_value() -> None:
    call = ModelCall(
        role="judge",
        provider="local",
        model="modelo-local",
        input_tokens=1,
        output_tokens=2,
        fallback_provider=True,
        anonymized=False,
        at=datetime(2026, 11, 26, 9, 0, 0, tzinfo=timezone(timedelta(hours=-5))),
        version="1.2",
        effort_or_quantization="Q4_K_M",
        engine="llama-server",
        seed=7,
    )

    record = build_call(call)

    assert record["version"] == "1.2"
    assert record["esfuerzo_o_cuantizacion"] == "Q4_K_M"
    assert record["motor"] == "llama-server"
    assert record["semilla"] == 7
    assert record["proveedor_alterno"] is True
    assert record["fecha"] == "2026-11-26T14:00:00Z", "se expresa en UTC"


def test_an_ok_output_validates_against_c6_and_carries_the_configuration_references() -> None:
    config = make_config()
    survivors = survivors_of([finding()])
    findings = assemble_findings("SINT-0001", survivors, turns_by_number())

    salida = build_output(
        config,
        interview="SINT-0001",
        date=DATE,
        findings=findings,
        discards=(Discard("cita_no_verificada", "T2", "T4"),),
        calls=[make_call("judge"), make_call("verifier"), make_call("verifier_permuted")],
    )

    assert c6_problems(salida) == []
    assert salida["estado"] == "ok"
    assert "error" not in salida
    assert salida["contrato"] == "1.0.0"
    assert salida["analizador"] == "incoherencias"
    assert salida["version"] == config.analyzer_version
    assert salida["entrevista"] == "SINT-0001"
    assert salida["perfil"] == "demo-anthropic"
    assert salida["prompt_sha256"] == config.prompt_sha256
    assert salida["config_sha256"] == config.config_sha256
    assert salida["fecha"] == "2026-11-26T15:30:45Z"
    assert discard_reasons(salida) == ["cita_no_verificada"]
    assert salida["registro"]["descartes"] == [
        {"motivo": "cita_no_verificada", "turno_a": "T2", "turno_b": "T4"}
    ]
    assert salida["registro"]["fragmentado"] == {"activo": False}
    assert salida["registro"]["tokens_entrada"] == 360
    assert salida["registro"]["tokens_salida"] == 90
    assert "costo_estimado" not in salida["registro"]
    assert "observaciones_conductor" not in salida


def test_a_discard_omits_the_turns_it_does_not_know() -> None:
    salida = build_output(
        make_config(),
        interview="E",
        date=DATE,
        findings=[],
        discards=(Discard("campo_faltante", None, "T4"), Discard("marca_alterada", None, None)),
        calls=[],
    )

    assert salida["registro"]["descartes"] == [
        {"motivo": "campo_faltante", "turno_b": "T4"},
        {"motivo": "marca_alterada"},
    ]
    assert c6_problems(salida) == []


@pytest.mark.parametrize(
    "code",
    [
        "salida_invalida",
        "bloqueo_contenido",
        "tiempo_agotado",
        "proveedor",
        "anonimizador_no_disponible",
        "incidente_anonimizacion",
    ],
)
def test_an_error_output_is_closed_with_nothing_partial_and_keeps_the_calls(code: str) -> None:
    survivors = survivors_of([finding()])
    salida = build_output(
        make_config(),
        interview="SINT-0001",
        date=DATE,
        findings=assemble_findings("SINT-0001", survivors, turns_by_number()),
        discards=(Discard("cita_no_verificada", None, None),),
        calls=[make_call("judge")],
        error_code=code,
    )

    assert_error_output(salida, code)
    assert [llamada["papel"] for llamada in salida["registro"]["llamadas"]] == ["juez"]
    assert salida["registro"]["tokens_entrada"] == 120
    assert salida["registro"]["fragmentado"] == {"activo": False}


def test_the_same_inputs_give_the_same_output() -> None:
    def make() -> dict[str, Any]:
        return build_output(
            make_config(),
            interview="SINT-0001",
            date=DATE,
            findings=assemble_findings("SINT-0001", survivors_of([finding()]), turns_by_number()),
            discards=(),
            calls=[make_call("judge")],
        )

    assert make() == make()
