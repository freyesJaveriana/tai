"""Casos de C8 y de VE-01 contra el escáner real (BR9.1 a BR9.5; R-06; N-01).

Todo el texto es sintético. Las pruebas leen los archivos versionados de `veridicus_contracts`, así
que una ampliación de la lista de C8 sin su caso positivo y su caso negativo hace fallar la suite.
"""

from importlib.resources import files
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from veridicus_contracts.loaders import load_file
from veridicus_errors import ConfigInvalidProfileError

from veridicus_integrity_policy import notice, scan


@pytest.fixture(autouse=True)
def _fresh_notice() -> Any:
    """El aviso se recuerda entre llamadas: cada prueba parte sin memoria y la deja limpia."""
    notice.load_notice.cache_clear()
    yield
    notice.load_notice.cache_clear()


def _document(name: str) -> Any:
    return load_file(files("veridicus_contracts") / "integrity" / name)


CASES: list[dict[str, Any]] = _document("scan-cases.v1.yaml")["cases"]
VOCABULARY_CASES = [case for case in CASES if case["rule"] == "vocabulary"]
TERMS: list[str] = _document("forbidden-vocabulary.v2.yaml")["terms"]


def _check(case: dict[str, Any]) -> None:
    result = scan.scan_detailed(case["text"], case["literal_sources"])
    assert [match.term for match in result.matches] == case["expect"]["matches"]
    assert result.excluded == case["expect"]["excluded"]


@pytest.mark.parametrize("case", VOCABULARY_CASES, ids=[case["id"] for case in VOCABULARY_CASES])
def test_every_vocabulary_case_of_scan_cases_gives_what_it_expects(case: dict[str, Any]) -> None:
    _check(case)


def test_the_rule_values_of_scan_cases_are_fixed() -> None:
    assert {case["rule"] for case in CASES} == {"vocabulary", "clarification"}


def test_there_are_vocabulary_cases_for_every_term_of_c8() -> None:
    covered = {term for case in VOCABULARY_CASES for term in case["expect"]["matches"]}

    assert covered >= set(TERMS)


def test_the_negative_control_an_inverted_expectation_fails() -> None:
    case = next(case for case in VOCABULARY_CASES if case["id"] == "e10-miente-en-observaciones")
    inverted = {**case, "expect": {"matches": [], "excluded": []}}

    with pytest.raises(AssertionError):
        _check(inverted)


@pytest.mark.parametrize("term", TERMS)
def test_each_term_is_found_alone_and_not_inside_another_word(term: str) -> None:
    text = f"Se dijo {term} ayer."
    found = scan.scan(text, [])
    glued = scan.scan(f"Se dijo re{term}x ayer.", [])

    assert [text[match.start : match.end] for match in found] == [term]
    assert glued == []


@given(flips=st.lists(st.booleans(), min_size=1, max_size=12), term=st.sampled_from(TERMS))
def test_property_a_term_is_found_whatever_its_letter_case(flips: list[bool], term: str) -> None:
    shaken = "".join(
        char.upper() if flips[index % len(flips)] else char for index, char in enumerate(term)
    )

    text = f"x {shaken} y"

    matches = scan.scan(text, [])

    assert [text[match.start : match.end] for match in matches] == [shaken]


def test_a_text_with_a_decomposed_accent_is_found_at_its_original_position() -> None:
    text = "Dijo mintio y luego meńtir."  # «mentir» con la tilde suelta sobre la n

    matches = scan.scan(text, [])

    assert [text[match.start : match.end] for match in matches] == ["mintio", "meńtir"]


def test_two_terms_that_differ_only_in_accents_are_named_as_the_text_writes_them() -> None:
    matches = scan.scan("Un engaño y luego engañó, o un ENGANO.", [])

    assert [match.term for match in matches] == ["engaño", "engañó", "engaño"]


def test_the_folded_end_of_a_match_maps_back_to_the_original_text() -> None:
    text = "ENGAÑOS aquí"

    matches = scan.scan(text, [])

    assert [(match.term, match.start, match.end) for match in matches] == [("engaños", 0, 7)]


def test_an_empty_or_blank_quote_is_not_a_literal_exclusion() -> None:
    text = "Dijo «» y «  » y miente."

    assert [match.term for match in scan.scan(text, ["", "  "])] == ["miente"]


def test_a_bare_term_with_punctuation_inside_the_quotes_is_still_scanned() -> None:
    assert [match.term for match in scan.scan("Dijo «falso.» ya.", ["falso."])] == ["falso"]


def test_an_unclosed_quote_does_not_exclude_anything() -> None:
    assert [match.term for match in scan.scan("Dijo «era falso y se fue.", ["era falso"])] == [
        "falso"
    ]


def test_a_term_outside_the_literal_quote_is_still_found() -> None:
    text = "Miente, y dijo «que era falso» antes."
    source = ["Yo dije que era falso."]

    result = scan.scan_detailed(text, source)

    assert [match.term for match in result.matches] == ["miente"]
    assert result.excluded == ["que era falso"]


def test_the_notice_is_excluded_even_if_its_spaces_differ() -> None:
    loaded = notice.load_notice()
    spaced = "\n".join(loaded.text.split(" "))

    assert [match.term for match in scan.scan(f"{spaced} Y miente.", [])] == ["miente"]


def test_a_fragment_of_the_notice_is_not_excluded() -> None:
    fragment = "No son prueba, no indican falsedad"

    assert [match.term for match in scan.scan(fragment, [])] == ["prueba"]


def test_the_notice_has_its_version_and_the_text_of_the_file() -> None:
    loaded = notice.load_notice()

    assert loaded.version == "1.0.0"
    assert loaded.text.startswith("Los hallazgos son sugerencias de revisión")
    assert loaded == notice.load_notice()


class _Fake:
    """Un archivo de prueba: el nombre y el texto que lee `load_file`."""

    def __init__(self, name: str, text: str | None) -> None:
        self.name = name
        self._text = text

    def read_text(self, encoding: str) -> str:
        if self._text is None:
            raise FileNotFoundError(self.name)
        return self._text


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("notice.v1.yaml", None),
        ("notice.v1.txt", "version: 1"),
        ("notice.v1.yaml", "- una\n- lista\n"),
        ("notice.v1.yaml", "text: algo\n"),
        ("notice.v1.yaml", 'version: ""\ntext: algo\n'),
        ("notice.v1.yaml", 'version: "1.0.0"\n'),
        ("notice.v1.yaml", 'version: "1.0.0"\ntext: "   "\n'),
    ],
    ids=[
        "falta",
        "sufijo",
        "no_objeto",
        "sin_version",
        "version_vacia",
        "sin_texto",
        "texto_vacio",
    ],
)
def test_a_missing_or_incomplete_notice_is_a_configuration_error(
    monkeypatch: pytest.MonkeyPatch, name: str, text: str | None
) -> None:
    monkeypatch.setattr(notice, "_resource", lambda: _Fake(name, text))

    with pytest.raises(ConfigInvalidProfileError) as rejected:
        notice.load_notice()

    assert "aviso de VE-01" in str(rejected.value)
