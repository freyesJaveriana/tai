"""Paso 7: detección con reglas, formas de marca y red de seguridad (BR1.2, BR1.5, BR1.7; E3, E10-E13).

Las pruebas leen los tramos que devuelven los detectores y su fusión; la seudonimización completa
se prueba en `test_masking.py`.
"""

import json
from dataclasses import replace
from typing import Any

import pytest

from tests.support import FIXTURES, load_seeded
from veridicus_anonymizer.domain.catalogs import Catalogs, RulePattern, load_catalogs
from veridicus_anonymizer.domain.detection import (
    DetectedSpan,
    apply_rules,
    merge_spans,
    safety_net,
)

CATALOGS = load_catalogs()
SEEDED = load_seeded()


def _texts(text: str, spans: list[DetectedSpan]) -> list[str]:
    return [text[s.start : s.end] for s in spans]


def _detect(text: str, catalogs: Catalogs = CATALOGS) -> list[DetectedSpan]:
    return merge_spans([*apply_rules(text, catalogs), *safety_net(text, catalogs)])


# --- Reglas -------------------------------------------------------------------------------------


def test_e1_the_rules_mark_the_name_the_place_the_case_number_and_the_identity_card() -> None:
    text = (
        "doña Ana Pérez vivía en la vereda La Esperanza; el radicado 110016000-2019-00123 "
        "y la cédula 1.234.567.890."
    )

    found = {(text[s.start : s.end], s.category) for s in apply_rules(text, CATALOGS)}

    assert ("Ana Pérez", "PERSONA") in found
    assert ("La Esperanza", "LUGAR") in found
    assert ("110016000-2019-00123", "EXPEDIENTE") in found
    assert ("1.234.567.890", "IDENTIFICADOR") in found


def test_a_treatment_stays_visible_and_only_the_name_after_it_is_marked() -> None:
    text = "El sargento Barrantes habló con doña Casilda Roncancio."

    spans = _detect(text)

    assert _texts(text, spans) == ["Barrantes", "Casilda Roncancio"]
    assert {s.category for s in spans} == {"PERSONA"}


def test_each_rule_names_itself_as_the_source_of_its_span() -> None:
    sources = {s.source for s in apply_rules("Llamó al 310 555 1234.", CATALOGS)}

    assert "rule:phone_mobile" in sources


def test_a_rule_without_an_entity_group_marks_the_whole_match() -> None:
    catalogs = replace(CATALOGS, rules=(RulePattern("whole", "LUGAR", "Rocamora"),))

    spans = apply_rules("Llegó a Rocamora ayer.", catalogs)

    assert spans == [DetectedSpan(8, 16, "LUGAR", "rule:whole")]


def test_empty_and_unmatched_entity_groups_are_not_spans() -> None:
    rules = (
        RulePattern("empty", "PERSONA", "(?P<entity>x*)"),
        RulePattern("unmatched", "PERSONA", "(?P<entity>x)?a"),
    )

    assert apply_rules("abc", replace(CATALOGS, rules=rules)) == []


# --- Cadenas con forma de marca (BR1.7) -----------------------------------------------------------


@pytest.mark.parametrize(
    "marker",
    [
        "[PERSONA_1]",
        "[Persona_1]",
        "[PERSONA 3]",
        "[persona-3]",
        "PERSONA_3]",
        "persona_3",
        "[NOMBRE_1]",
    ],
)
def test_a_string_shaped_like_a_marker_is_an_entity_with_its_own_marker(marker: str) -> None:
    text = f"Dijo {marker} en la plaza."

    spans = [s for s in apply_rules(text, CATALOGS) if s.source == "input_marker"]

    assert [(text[s.start : s.end], s.category) for s in spans] == [(marker, "ENTIDAD")]


@pytest.mark.parametrize("text", ["la persona 3 declaró", "la [persona] declaró", "persona_ 3"])
def test_text_that_only_resembles_a_marker_is_not_one(text: str) -> None:
    assert [s for s in apply_rules(text, CATALOGS) if s.source == "input_marker"] == []


# --- Red de seguridad (PD-2, F-11) ----------------------------------------------------------------


def test_f11_a_full_name_without_a_treatment_carries_a_single_span() -> None:
    text = "Ayer vieron a Casilda Roncancio Tafurt en la plaza."

    spans = safety_net(text, CATALOGS)

    assert _texts(text, spans) == ["Casilda Roncancio Tafurt"]
    assert spans[0].category == "ENTIDAD"


def test_e10_a_loose_name_and_a_nickname_in_the_middle_of_a_sentence_are_entities() -> None:
    text = "Después vieron al Mono con Hortensia en la plaza."

    spans = safety_net(text, CATALOGS)

    assert _texts(text, spans) == ["Mono", "Hortensia"]
    assert {s.source for s in spans} == {"safety_net:inline"}


def test_e3_a_name_that_is_a_person_or_a_place_gets_one_category_never_visible() -> None:
    text = "vivía en San José desde niño."

    spans = _detect(text)

    assert _texts(text, spans) == ["San José"]
    assert len({s.category for s in spans}) == 1


def test_e11_institutions_and_months_stay_visible() -> None:
    text = "Dijo que la Fiscalía y el Ejército llegaron en marzo."

    assert safety_net(text, CATALOGS) == []


def test_e12_a_date_and_a_figure_stay_visible() -> None:
    text = "El 12 de marzo de 2003 vieron a tres hombres."

    assert _detect(text) == []


def test_an_allowed_word_breaks_a_run_and_a_comma_does_not_join_two_names() -> None:
    text = "Entonces Casilda Roncancio, Aurelio Benavides y la Fiscalía."

    spans = safety_net(text, CATALOGS)

    assert _texts(text, spans) == ["Casilda Roncancio", "Aurelio Benavides"]


def test_a_lowercase_word_between_two_names_separates_them() -> None:
    text = "Casilda vio a Aurelio con Roncancio."

    assert _texts(text, safety_net(text, CATALOGS)) == ["Casilda", "Aurelio", "Roncancio"]


def test_a_hyphenated_surname_is_one_word_and_a_no_break_space_joins_a_run() -> None:
    nbsp = chr(0xA0)
    text = f"Vieron a Ana Pérez-Gómez{nbsp}Tafurt ayer."

    assert _texts(text, safety_net(text, CATALOGS)) == [f"Ana Pérez-Gómez{nbsp}Tafurt"]


F01_CASES = [
    ("vio a ex-Benavides ayer", ["Benavides"]),
    ("vio a maría-Fernanda ayer", ["Fernanda"]),
    ("vio a Benavides_2 ayer", ["Benavides"]),
    ("vio a Benavides7 ayer", ["Benavides"]),
    ("vio a ex_Benavides ayer", ["Benavides"]),
    ("vio a a7Benavides ayer", ["Benavides"]),
    ("dijo\\nBenavides vino", ["Benavides"]),
    ("vio a \\u00c1lvaro Tafurt ayer", ["lvaro", "Tafurt"]),
]


@pytest.mark.parametrize(
    ("text", "covered"),
    F01_CASES,
    ids=[
        "prefijo_con_guion",
        "pila_minuscula_con_guion",
        "guion_bajo",
        "digito",
        "prefijo_con_guion_bajo",
        "prefijo_con_digito",
        "escape_n",
        "escape_unicode",
    ],
)
def test_f01_a_word_with_any_capital_letter_is_masked_whole_whatever_it_is_glued_to(
    text: str, covered: list[str]
) -> None:
    spans = _detect(text)

    for part in covered:
        start = text.index(part)
        assert any(s.start <= start and start + len(part) <= s.end for s in spans), part


def test_f01_an_escape_sequence_separates_words_and_is_never_an_entity() -> None:
    assert _detect("hola\\nana\\tluz\\rdijo") == []
    # La palabra que sigue al escape se evalúa sola: solo ella queda marcada.
    text = "dijo\\nBenavides vino"
    assert _texts(text, _detect(text)) == ["Benavides"]


def test_f01_a_capital_inside_a_lowercase_word_is_masked_on_the_safe_side() -> None:
    text = "compró un iPhone ayer"

    assert _texts(text, _detect(text)) == ["iPhone"]


def test_words_that_do_not_start_with_a_capital_letter_are_never_entities() -> None:
    text = "compró un iphone en 2019 con el código a1b2 y 3 mulas."

    assert safety_net(text, CATALOGS) == []


def test_the_opening_position_is_recorded_in_the_source_of_the_span() -> None:
    text = "Casilda vio a Aurelio."

    sources = [s.source for s in safety_net(text, CATALOGS)]

    assert sources == ["safety_net:opening", "safety_net:inline"]


def test_a_collision_with_the_allowed_word_list_spares_the_word_but_a_rule_still_wins() -> None:
    catalogs = replace(CATALOGS, allowed_words=CATALOGS.allowed_words | {"Casilda"})

    assert safety_net("Casilda llegó.", catalogs) == []
    assert _texts("dijo doña Casilda llegó", _detect("dijo doña Casilda llegó", catalogs)) == [
        "Casilda"
    ]


def test_a_given_name_that_is_also_a_common_word_is_masked_when_it_opens_a_sentence() -> None:
    names: list[str] = json.loads((FIXTURES / "common_word_names.json").read_text("utf-8"))[
        "nombres"
    ]
    for name in names:
        text = f"{name} llegó temprano."

        assert _texts(text, safety_net(text, CATALOGS)) == [name]


@pytest.mark.parametrize("turn", SEEDED["turnos"], ids=[t["posicion"] for t in SEEDED["turnos"]])
def test_every_seeded_entity_lies_inside_a_detected_span(turn: dict[str, Any]) -> None:
    text = turn["texto"]
    spans = _detect(text)

    for entity in turn["entidades"]:
        start = text.index(entity)
        end = start + len(entity)
        assert any(s.start <= start and end <= s.end for s in spans), "una entidad no se detectó"


def test_the_declared_limit_a_lowercase_nickname_is_detected_by_no_detector() -> None:
    fixture = json.loads((FIXTURES / "transcripts" / "nickname_lowercase.json").read_text("utf-8"))
    text = fixture["turnos"][0]["texto"]

    spans = _detect(text)

    assert fixture["apodo_limite"] not in " ".join(_texts(text, spans))
    assert fixture["entidad_enmascarada"] in _texts(text, spans)


# --- Fusión ---------------------------------------------------------------------------------------


def test_merge_joins_overlapping_and_touching_spans_in_their_union() -> None:
    spans = [
        DetectedSpan(10, 15, "ENTIDAD", "b"),
        DetectedSpan(0, 5, "PERSONA", "a"),
        DetectedSpan(3, 8, "LUGAR", "c"),
        DetectedSpan(15, 20, "ENTIDAD", "d"),
        DetectedSpan(25, 30, "ENTIDAD", "e"),
    ]

    merged = merge_spans(spans)

    assert [(s.start, s.end) for s in merged] == [(0, 8), (10, 20), (25, 30)]


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("ENTIDAD", "PERSONA", "PERSONA"),
        ("LUGAR", "ENTIDAD", "LUGAR"),
        ("PERSONA", "LUGAR", "PERSONA"),
        ("IDENTIFICADOR", "PERSONA", "IDENTIFICADOR"),
        ("ENTIDAD", "EXPEDIENTE", "EXPEDIENTE"),
    ],
)
def test_merge_keeps_the_category_of_greater_precedence(
    first: str, second: str, expected: str
) -> None:
    merged = merge_spans([DetectedSpan(0, 5, first, "a"), DetectedSpan(2, 9, second, "b")])

    assert [(s.start, s.end, s.category) for s in merged] == [(0, 9, expected)]


def test_a_contained_span_never_shrinks_the_container() -> None:
    merged = merge_spans([DetectedSpan(0, 10, "PERSONA", "a"), DetectedSpan(2, 4, "ENTIDAD", "b")])

    assert [(s.start, s.end) for s in merged] == [(0, 10)]
