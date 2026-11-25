"""AUTONOMIA-04, payload saliente (AC11.3.1, AC11.3.7 del lado de U10; E1, E2, E9, E29).

Ningún cuerpo que capture el `FakeTransport` contiene una entidad sembrada, y todos llevan marcas.
Control negativo: con la seudonimización puenteada, la misma aserción tiene que fallar.
"""

import json
import re
from typing import Any

import pytest

from tests.support import (
    FIXTURES,
    assert_no_entity_in_payload,
    load_seeded,
    make_harness,
    make_request,
    ok_response,
    outgoing_bodies,
    turns_of,
    user_texts,
)
from veridicus_anonymizer.testing.bypass import bypass_pseudonymization

SEEDED = load_seeded()
MARKER = re.compile(r"\[(PERSONA|LUGAR|EXPEDIENTE|IDENTIFICADOR|ENTIDAD)_[1-9][0-9]*\]")
PERSONA_MARKER = re.compile(r"\[PERSONA_[1-9][0-9]*\]")


def _roles() -> list[str]:
    return ["judge", "verifier", "verifier_permuted"]


@pytest.mark.parametrize("role", _roles())
def test_e1_e29_no_seeded_entity_leaves_and_every_body_carries_markers(role: str) -> None:
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(role=role))

    assert harness.transport.request_count == 1
    assert_no_entity_in_payload(harness.transport, SEEDED["entidades"])
    for body in outgoing_bodies(harness.transport):
        assert PERSONA_MARKER.search(body), "el cuerpo saliente no lleva ninguna marca [PERSONA_n]"


@pytest.mark.parametrize("turn", SEEDED["turnos"], ids=[t["posicion"] for t in SEEDED["turnos"]])
def test_every_sentence_opening_position_is_pseudonymized(turn: dict[str, Any]) -> None:
    harness = make_harness(ok_response())
    only_this_turn = turns_of(SEEDED, positions=[turn["posicion"]])
    harness.anonymizer.generate(make_request(only_this_turn))

    assert_no_entity_in_payload(harness.transport, turn["entidades"])
    assert MARKER.search(outgoing_bodies(harness.transport)[0])


@pytest.mark.parametrize(
    "ensure_ascii", [True, False], ids=["tildes_como_escape_json", "tildes_directas"]
)
def test_e9_accented_entities_are_not_leaked_even_when_written_as_json_escapes(
    ensure_ascii: bool,
) -> None:
    accented = turns_of(
        SEEDED, positions=["tras_interrogacion_de_cierre", "tras_exclamacion_de_cierre"]
    )
    request = make_request(accented, ensure_ascii=ensure_ascii)
    if ensure_ascii:
        assert "\\u00ed" in request.messages[1].content, (
            "la entrada debe traer escapes Unicode del JSON"
        )

    harness = make_harness(ok_response())
    harness.anonymizer.generate(request)

    assert_no_entity_in_payload(
        harness.transport, ["Eufrasio Mendívelso", "Anselmo Páez", "Mendívelso", "Páez"]
    )


def test_e2_same_exact_form_gets_the_same_marker_and_a_different_form_another() -> None:
    turnos = [
        {"turno": 1, "hablante": "TES", "texto": "Vi a Casilda Roncancio en la plaza."},
        {"turno": 2, "hablante": "TES", "texto": "Casilda Roncancio compró pan."},
        {"turno": 3, "hablante": "TES", "texto": "Luego Casilda se fue."},
    ]
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(turnos))

    texts = user_texts(harness.transport)
    first = MARKER.search(texts[0])
    second = MARKER.search(texts[1])
    third = MARKER.search(texts[2])
    assert first and second and third
    assert first.group(0) == second.group(0)
    assert third.group(0) != first.group(0)
    assert_no_entity_in_payload(harness.transport, ["Casilda Roncancio", "Roncancio", "Casilda"])


def test_e1_case_number_and_identity_card_become_markers() -> None:
    turnos = turns_of(SEEDED, positions=["expediente_y_cedula"])
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(turnos))

    body = outgoing_bodies(harness.transport)[0]
    assert "[EXPEDIENTE_1]" in body
    assert "[IDENTIFICADOR_1]" in body
    assert_no_entity_in_payload(harness.transport, ["110016000-2019-00123", "1.234.567.890"])


def test_a_common_word_given_name_opening_a_sentence_does_not_leak() -> None:
    names = json.loads((FIXTURES / "common_word_names.json").read_text("utf-8"))["nombres"]
    assert "Esperanza" in names
    turnos = turns_of(SEEDED, positions=["nombre_de_pila_que_es_palabra_comun"])
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(turnos))

    assert_no_entity_in_payload(
        harness.transport, ["Esperanza Quiñones", "Paz Villamar", "Esperanza", "Villamar"]
    )


def test_negative_control_the_same_assertion_fails_with_pseudonymization_bypassed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bypass_pseudonymization(monkeypatch)
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request())

    assert harness.transport.request_count == 1
    with pytest.raises(AssertionError, match="fuga"):
        assert_no_entity_in_payload(harness.transport, SEEDED["entidades"])


def test_declared_limit_a_lowercase_nickname_is_not_detected_by_any_rule() -> None:
    fixture = json.loads((FIXTURES / "transcripts" / "nickname_lowercase.json").read_text("utf-8"))
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(fixture["turnos"]))

    # Lo detectable sí se enmascara; el apodo en minúscula pasa: es el límite declarado de PD-2
    # (CG-U10-02), documentado aquí y fuera del conjunto de fuga cero.
    assert_no_entity_in_payload(harness.transport, [fixture["entidad_enmascarada"]])
    assert fixture["apodo_limite"] in outgoing_bodies(harness.transport)[0]
