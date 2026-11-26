"""AUTONOMIA-03, el escáner de vocabulario prohibido llamado directamente (BR9.1, BR9.2).

Las coincidencias se comprueban por el texto que cubren (`texto[inicio:fin]`), no por el término
normalizado. Los casos de `contracts/integrity/scan-cases.v1.yaml` los ejecuta el paso 5 (N-01).
En el rojo, `scan` y `load_notice` lanzan `NotImplementedError`.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from veridicus_integrity_policy.notice import load_notice
from veridicus_integrity_policy.scan import scan


def _covered(text: str, sources: list[str] | None = None) -> list[str]:
    return [text[match.start : match.end] for match in scan(text, sources or [])]


@pytest.mark.parametrize(
    ("text", "covered"),
    [
        ("Ella MIENTE en esto.", ["MIENTE"]),
        ("Dijo que Miente.", ["Miente"]),
        ("El testigo mintio ayer.", ["mintio"]),
        ("Ellos mienten otra vez.", ["mienten"]),
        ("Es un engaño y no una duda.", ["engaño"]),
        ("Un relato falso.", ["falso"]),
        ("Los datos son verdaderos.", []),
        ("Es probatorio.", ["probatorio"]),
    ],
    ids=[
        "mayusculas",
        "mayuscula_inicial",
        "sin_tilde",
        "flexion_de_la_lista",
        "con_tilde",
        "termino_simple",
        "flexion_fuera_de_la_lista",
        "otro_termino",
    ],
)
def test_terms_are_found_without_regard_to_case_or_accents(text: str, covered: list[str]) -> None:
    assert _covered(text) == covered


@pytest.mark.parametrize(
    "text",
    ["Un falsete agudo.", "Hubo falsedad en el acta.", "Lo desmiente el acta.", "El sumientes."],
    ids=["falsete", "falsedad", "desmiente", "sufijo_de_otra_palabra"],
)
def test_a_term_inside_another_word_is_not_a_match(text: str) -> None:
    assert _covered(text) == []


def test_a_quoted_span_that_appears_literally_in_a_source_is_excluded() -> None:
    text = "Dijo «era falso» y se fue."

    assert _covered(text, ["Él dijo que era falso, según consta."]) == []


def test_a_quoted_span_that_is_in_no_source_is_scanned() -> None:
    text = "Dijo «era falso» y se fue."

    assert _covered(text, ["Otro turno sin relación."]) == ["falso"]


def test_a_quoted_span_that_is_only_a_forbidden_term_is_scanned_even_if_it_is_literal() -> None:
    assert _covered("Dijo «falso» y se fue.", ["falso"]) == ["falso"]


def test_whitespace_differences_do_not_break_the_literal_quote_exclusion() -> None:
    text = "Dijo «era   falso»."

    assert _covered(text, ["que era falso, según consta"]) == []


def test_the_text_of_the_notice_is_excluded_when_it_appears_whole() -> None:
    notice = load_notice()

    assert scan(notice.text, []) == []
    assert _covered(f"{notice.text} Además miente.") == ["miente"]


def test_a_term_that_is_in_the_notice_is_found_anywhere_else() -> None:
    load_notice()

    assert _covered("Esto es una prueba.") == ["prueba"]


@given(text=st.text(alphabet="xyz .,;123", max_size=60))
def test_property_a_text_without_any_term_has_no_matches(text: str) -> None:
    assert scan(text, []) == []


@given(
    prefix=st.text(alphabet="xyz .,;", max_size=20), suffix=st.text(alphabet="xyz .,;", max_size=20)
)
def test_property_a_term_between_separators_is_found_exactly_once(prefix: str, suffix: str) -> None:
    text = f"{prefix} miente {suffix}"

    assert _covered(text) == ["miente"]
