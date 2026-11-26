"""AUTONOMIA-05, citas (BR5.1 a BR5.7; AC3.4.1 a AC3.4.4, AC11.3.4).

Un hallazgo sin sus campos obligatorios, o con una cita alterada, de otro turno o inventada, no sale.
La regla del piloto solo normaliza espacios; la cita seudonimizada se restaura antes de verificarse.
En el rojo, `analyze`, `verify_quote`, `load_config` y `build` lanzan `NotImplementedError`.
"""

from typing import Any

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from veridicus_anonymizer.api import build_anonymizer
from veridicus_model_gateway.gateway import build

from tests.support import (
    T1,
    T2,
    T4,
    ScriptedGateway,
    ScriptedProvider,
    assert_error_output,
    c6_problems,
    default_turns,
    discard_reasons,
    echo_finding,
    env,
    finding,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.domain.quotes import verify_quote

REQUIRED = ["hecho", "tipo", "cita_a", "cita_b", "observaciones"]


@pytest.mark.parametrize("campo", REQUIRED)
def test_a_candidate_without_a_required_field_invalidates_the_run_and_nothing_leaves(
    campo: str,
) -> None:
    config = make_config()
    malformed = finding()
    del malformed[campo]
    gateway = ScriptedGateway(findings=[finding(), malformed, finding(hecho="Otro hecho")])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.roles() == ["judge"], "ningún candidato llega al verificador"


@pytest.mark.parametrize("campo", ["hecho", "observaciones", "cita_a", "cita_b"])
def test_a_field_with_only_whitespace_discards_the_candidate_with_campo_faltante(
    campo: str,
) -> None:
    config = make_config()
    blank = finding()
    if campo in {"cita_a", "cita_b"}:
        blank[campo]["cita"] = " \t\n "
    else:
        blank[campo] = " \t\n "
    gateway = ScriptedGateway(findings=[blank, finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert salida["estado"] == "ok"
    assert discard_reasons(salida) == ["campo_faltante"]
    assert len(salida["hallazgos"]) == 1, "el otro candidato sigue"
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
    assert c6_problems(salida) == []


@pytest.mark.parametrize("cita", ["cita_a", "cita_b"])
def test_a_quote_altered_in_one_character_is_discarded_and_never_reaches_the_verifier(
    cita: str,
) -> None:
    config = make_config()
    candidate = finding()
    candidate[cita]["cita"] = (
        candidate[cita]["cita"].replace("Roncancio", "Roncancia").replace("Altamira", "Altamiro")
    )
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(), config, gateway)

    assert salida["estado"] == "ok"
    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["cita_no_verificada"]
    assert gateway.roles() == ["judge"]


def test_a_quote_that_belongs_to_another_turn_is_discarded_as_cita_en_otro_turno() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding(a=(2, T4))])  # el texto es de T4, el turno dice T2

    salida = analyze(make_entrada(), config, gateway)

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["cita_en_otro_turno"]
    assert salida["registro"]["descartes"][0]["turno_a"] == "T2"
    assert salida["registro"]["descartes"][0]["turno_b"] == "T4"


@pytest.mark.parametrize(
    ("a", "motivo"),
    [
        ((2, "Esa noche estuvo en el puerto con su hermano."), "cita_no_verificada"),
        ((9, T2), "cita_no_verificada"),
    ],
    ids=["cita_inventada", "turno_inexistente"],
)
def test_an_invented_quote_or_an_unknown_turn_is_discarded_as_cita_no_verificada(
    a: tuple[int, str], motivo: str
) -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding(a=a)])

    salida = analyze(make_entrada(), config, gateway)

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == [motivo]
    assert gateway.roles() == ["judge"]


def test_pilot_rule_only_whitespace_is_normalized() -> None:
    config = make_config()
    spaced = "Casilda   Roncancio llegó a\tVilla Rocamora  antes del mediodía."
    gateway = ScriptedGateway(findings=[finding(a=(2, spaced))])

    salida = analyze(make_entrada(), config, gateway)

    assert len(salida["hallazgos"]) == 1
    assert salida["registro"]["descartes"] == []


def test_pilot_rule_fragments_joined_by_ellipsis_in_order_are_accepted() -> None:
    config = make_config()
    joined = "Casilda Roncancio llegó […] antes del mediodía."
    gateway = ScriptedGateway(findings=[finding(a=(2, joined))])

    salida = analyze(make_entrada(), config, gateway)

    assert len(salida["hallazgos"]) == 1


def test_pilot_rule_fragments_out_of_order_are_discarded() -> None:
    config = make_config()
    reversed_fragments = "antes del mediodía […] Casilda Roncancio llegó"
    gateway = ScriptedGateway(findings=[finding(a=(2, reversed_fragments))])

    salida = analyze(make_entrada(), config, gateway)

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["cita_no_verificada"]


def test_a_quote_in_an_interviewer_turn_is_accepted_with_a_notice_and_without_page() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding(a=(1, T1))])

    salida = analyze(make_entrada(), config, gateway)

    cita_a = salida["hallazgos"][0]["cita_a"]
    assert cita_a["avisos"] == ["turno_entrevistador"]
    assert "pagina" not in cita_a, "el turno no tiene página"


def test_a_quote_in_a_folded_turn_is_accepted_with_a_notice_and_the_page_of_the_turn() -> None:
    config = make_config()
    turns = default_turns()
    turns[1]["estado"] = "plegado"
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(turns), config, gateway)

    cita_a = salida["hallazgos"][0]["cita_a"]
    assert cita_a["avisos"] == ["turno_plegado"]
    assert cita_a["pagina"] == 1


def test_an_interviewer_turn_that_is_also_folded_carries_both_notices() -> None:
    config = make_config()
    turns = default_turns()
    turns[0]["estado"] = "plegado"
    gateway = ScriptedGateway(findings=[finding(a=(1, T1))])

    salida = analyze(make_entrada(turns), config, gateway)

    assert sorted(salida["hallazgos"][0]["cita_a"]["avisos"]) == [
        "turno_entrevistador",
        "turno_plegado",
    ]


def test_a_pseudonymized_quote_is_restored_and_verified_against_the_original_turn() -> None:
    config = make_config()
    provider = ScriptedProvider(echo_finding)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))

    salida = analyze(make_entrada(), config, gateway)

    assert salida["estado"] == "ok"
    assert len(salida["hallazgos"]) == 1
    assert salida["hallazgos"][0]["cita_a"]["cita"] == T2
    assert salida["hallazgos"][0]["cita_b"]["cita"] == T4
    assert provider.request_count == 3, "juez, verificador y verificador permutado"


def test_an_altered_marker_in_a_quote_discards_the_candidate_with_marca_alterada() -> None:
    config = make_config()

    def altered(turns: dict[int, str]) -> list[dict[str, Any]]:
        return [finding(a=(2, turns[2]), b=(4, "[PERSONA_9] estaba en [LUGAR_7]"))]

    provider = ScriptedProvider(altered)
    gateway = build(config, anonymizing_provider=build_anonymizer(env(), provider))

    salida = analyze(make_entrada(), config, gateway)

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == ["marca_alterada"]
    assert provider.request_count == 1, "solo el juez: el candidato no llega al verificador"


def _set_field(candidate: dict[str, Any], campo: str, valor: object) -> None:
    if campo in {"cita_a", "cita_b"}:
        candidate[campo]["cita"] = valor
    else:
        candidate[campo] = valor


@pytest.mark.parametrize("valor", [None, ""], ids=["null", "cadena_vacia"])
@pytest.mark.parametrize("campo", ["hecho", "observaciones", "cita_a", "cita_b"])
def test_a_null_or_empty_field_invalidates_the_run_and_nothing_leaves(
    campo: str, valor: object
) -> None:
    config = make_config()
    malformed = finding()
    _set_field(malformed, campo, valor)
    gateway = ScriptedGateway(findings=[finding(), malformed])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.roles() == ["judge"]


def test_a_type_outside_the_seven_values_invalidates_the_run() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding(), finding(hecho="Otro hecho", tipo="temporal")])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.roles() == ["judge"]


@pytest.mark.parametrize(
    "pointer",
    ["/hallazgos/1/observaciones", "/hallazgos/1/hecho", "/hallazgos/1/cita_a/cita"],
)
def test_an_altered_marker_in_any_field_discards_only_that_candidate(pointer: str) -> None:
    config = make_config()
    gateway = ScriptedGateway(
        findings=[finding(), finding(hecho="Segundo hecho")], altered_markers=[pointer]
    )

    salida = analyze(make_entrada(), config, gateway)

    assert discard_reasons(salida) == ["marca_alterada"]
    assert len(salida["hallazgos"]) == 1
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]


@pytest.mark.parametrize("pointer", ["/hallazgos/5/observaciones", "/comentario", "/hallazgos"])
def test_a_pointer_that_falls_in_no_candidate_invalidates_the_run(pointer: str) -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()], altered_markers=[pointer])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.roles() == ["judge"]


def test_filter_order_a_blank_field_wins_over_a_failing_quote() -> None:
    config = make_config()
    candidate = finding(a=(2, "Texto que no está en ningún turno."))
    candidate["hecho"] = " \t "
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(), config, gateway)

    assert discard_reasons(salida) == ["campo_faltante"]


def test_filter_order_an_altered_marker_wins_over_a_blank_field() -> None:
    config = make_config()
    candidate = finding()
    candidate["hecho"] = " \t "
    gateway = ScriptedGateway(findings=[candidate], altered_markers=["/hallazgos/0/hecho"])

    salida = analyze(make_entrada(), config, gateway)

    assert discard_reasons(salida) == ["marca_alterada"]


def test_filter_order_a_failing_quote_wins_over_forbidden_vocabulary() -> None:
    config = make_config()
    candidate = finding(a=(2, "Texto que no está en ningún turno."))
    candidate["observaciones"] = "La persona miente sobre este punto."
    gateway = ScriptedGateway(findings=[candidate])

    salida = analyze(make_entrada(), config, gateway)

    assert discard_reasons(salida) == ["cita_no_verificada"]


INVENTED = "Texto que no está en ningún turno."


@pytest.mark.parametrize(
    ("a", "b", "motivo"),
    [
        ((2, T2), (4, T2), "cita_en_otro_turno"),
        ((2, T2), (4, INVENTED), "cita_no_verificada"),
        ((2, T4), (4, INVENTED), "cita_en_otro_turno"),
        ((2, INVENTED), (4, T2), "cita_no_verificada"),
    ],
    ids=[
        "a_valida_b_otro_turno",
        "a_valida_b_inventada",
        "a_otro_turno_b_inventada",
        "a_inventada_b_otro_turno",
    ],
)
def test_the_first_failing_quote_decides_the_reason(
    a: tuple[int, str], b: tuple[int, str], motivo: str
) -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding(a=a, b=b)])

    salida = analyze(make_entrada(), config, gateway)

    assert salida["hallazgos"] == []
    assert discard_reasons(salida) == [motivo]
    assert gateway.roles() == ["judge"]


TURN_TEXT = st.text(alphabet="abcdefgh \t", min_size=1, max_size=60).filter(
    lambda text: bool(text.strip())
)


@given(turn=TURN_TEXT, data=st.data())
def test_property_every_exact_substring_of_a_turn_verifies_in_that_turn(
    turn: str, data: st.DataObject
) -> None:
    start = data.draw(st.integers(min_value=0, max_value=len(turn) - 1))
    end = data.draw(st.integers(min_value=start + 1, max_value=len(turn)))
    quote = turn[start:end]
    assume(quote.strip())

    assert verify_quote(turn, quote) == "verified"


@given(turn=TURN_TEXT, data=st.data())
def test_property_a_quote_with_one_character_changed_never_verifies(
    turn: str, data: st.DataObject
) -> None:
    start = data.draw(st.integers(min_value=0, max_value=len(turn) - 1))
    end = data.draw(st.integers(min_value=start + 1, max_value=len(turn)))
    quote = turn[start:end]
    positions = [i for i, char in enumerate(quote) if not char.isspace()]
    assume(positions)
    position = data.draw(st.sampled_from(positions))
    # «Ω» no está en el alfabeto de los turnos: el texto alterado no puede aparecer en ninguno.
    altered = quote[:position] + "Ω" + quote[position + 1 :]

    assert verify_quote(turn, altered) == "not_found"
