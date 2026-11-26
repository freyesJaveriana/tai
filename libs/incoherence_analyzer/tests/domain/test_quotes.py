"""Verificación de citas con la regla del piloto (BR5.5, AUTONOMIA-05): solo se normalizan espacios.

Función pura: devuelve `verified` o `not_found`; `other_turn` y `unknown_turn` los deriva el filtro.
Los espacios Unicode se escriben con `\\N{...}` o con `chr(...)`, nunca como caracteres invisibles:
un literal U+2028 corta la línea al leer el archivo (F-05 de U11-T03).
"""

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from veridicus_incoherence_analyzer.domain.quotes import normalize_spaces, verify_quote

TURN = "Casilda Roncancio llegó a Villa Rocamora antes del mediodía."
NBSP = chr(0xA0)
EM_SPACE = chr(0x2003)


def test_an_exact_substring_verifies() -> None:
    assert verify_quote(TURN, "llegó a Villa Rocamora") == "verified"
    assert verify_quote(TURN, TURN) == "verified"


@pytest.mark.parametrize(
    "quote",
    [
        "Casilda   Roncancio llegó",
        "Casilda\tRoncancio\nllegó",
        "  Casilda Roncancio llegó  ",
        f"Casilda{NBSP}Roncancio{EM_SPACE}llegó",
    ],
    ids=["varios_espacios", "tab_y_salto", "bordes", "unicode"],
)
def test_only_whitespace_is_normalized_so_spacing_differences_verify(quote: str) -> None:
    assert verify_quote(TURN, quote) == "verified"


def test_whitespace_in_the_turn_is_normalized_too() -> None:
    assert verify_quote("Casilda   Roncancio\n llegó", "Casilda Roncancio llegó") == "verified"


@pytest.mark.parametrize(
    "quote",
    [
        "casilda roncancio llegó",
        "CASILDA RONCANCIO",
        "llego a Villa Rocamora",
        "llegó a Villa Rocamora antes del mediodia",
        "Casilda Roncancio, llegó",
        "«Casilda Roncancio»",
    ],
    ids=["minusculas", "mayusculas", "sin_tilde", "sin_tilde_final", "coma", "comillas"],
)
def test_case_accents_and_punctuation_count_so_changes_do_not_verify(quote: str) -> None:
    assert verify_quote(TURN, quote) == "not_found"


def test_a_quote_that_is_not_in_the_turn_does_not_verify() -> None:
    assert verify_quote(TURN, "Esa noche estuvo en el puerto") == "not_found"


@pytest.mark.parametrize(
    "quote", ["", " ", " \t\n ", NBSP], ids=["vacia", "espacio", "tab", "nbsp"]
)
def test_an_empty_or_blank_quote_never_verifies(quote: str) -> None:
    assert verify_quote(TURN, quote) == "not_found"


def test_fragments_joined_by_the_ellipsis_in_order_verify() -> None:
    assert verify_quote(TURN, "Casilda Roncancio llegó […] antes del mediodía.") == "verified"
    assert verify_quote(TURN, "Casilda […] Villa […] mediodía.") == "verified"


def test_fragments_out_of_order_do_not_verify() -> None:
    assert verify_quote(TURN, "antes del mediodía. […] Casilda Roncancio") == "not_found"


def test_overlapping_fragments_do_not_verify() -> None:
    assert verify_quote("abcdef", "abcd […] cdef") == "not_found"
    assert verify_quote("abcdef", "abcd […] ef") == "verified"
    assert verify_quote("abab", "ab […] ab") == "verified"
    assert verify_quote("ab", "ab […] ab") == "not_found"


def test_an_empty_fragment_does_not_verify() -> None:
    assert verify_quote(TURN, " […] antes del mediodía.") == "not_found"
    assert verify_quote(TURN, "Casilda […] […] mediodía.") == "not_found"


def test_the_ellipsis_needs_spaces_around_it_to_be_a_separator() -> None:
    assert verify_quote(TURN, "Casilda[…]Roncancio") == "not_found"
    assert verify_quote("dijo[…]esto", "dijo[…]esto") == "verified", "literal en el turno"


def test_a_turn_that_literally_contains_the_ellipsis_still_verifies_its_pieces() -> None:
    assert verify_quote("uno […] dos", "uno […] dos") == "verified"


@pytest.mark.parametrize("char", [chr(code) for code in (0x1C, 0x1D, 0x1E, 0x1F)])
def test_control_separators_are_not_white_space_so_they_do_not_normalize_to_a_space(
    char: str,
) -> None:
    assert verify_quote(f"a{char}b", "a b") == "not_found"
    assert verify_quote("a b", f"a{char}b") == "not_found"
    assert normalize_spaces(f"a{char}b") == f"a{char}b"


# U+00A0, U+2003, U+3000, U+0085, U+1680, U+2028, U+202F y U+205F, por punto de código.
WHITE_SPACE = [chr(code) for code in (0xA0, 0x2003, 0x3000, 0x85, 0x1680, 0x2028, 0x202F, 0x205F)]


@pytest.mark.parametrize("char", [*WHITE_SPACE, "\v", "\f"])
def test_every_unicode_white_space_character_normalizes_to_one_space(char: str) -> None:
    assert verify_quote(f"a{char}b", "a b") == "verified"
    assert verify_quote("a b", f"a{char}{char}b") == "verified"


def test_the_normalized_characters_are_exactly_the_unicode_white_space_property() -> None:
    """`str.isspace` coincide con `White_Space` salvo U+001C a U+001F, que BR5.5 no normaliza."""
    expected = {
        code for code in range(0x110000) if chr(code).isspace() and code not in range(0x1C, 0x20)
    }

    normalized = {
        code for code in range(0x110000) if normalize_spaces("a" + chr(code) + "b") == "a b"
    }

    assert normalized == expected
    assert {0xA0, 0x2003, 0x3000} <= normalized
    assert not normalized & set(range(0x1C, 0x20))


def test_normalize_spaces_collapses_runs_and_trims() -> None:
    assert normalize_spaces("  a \t\n b  c  ") == "a b c"
    assert normalize_spaces("") == ""
    assert normalize_spaces("  a \t\n b" + NBSP + EM_SPACE + "c  ") == "a b c"


TURN_TEXT = st.text(alphabet="abcdefgh \t", min_size=1, max_size=60).filter(
    lambda text: bool(text.strip())
)


@given(turn=TURN_TEXT, data=st.data())
def test_property_every_exact_substring_verifies(turn: str, data: st.DataObject) -> None:
    start = data.draw(st.integers(min_value=0, max_value=len(turn) - 1))
    end = data.draw(st.integers(min_value=start + 1, max_value=len(turn)))
    quote = turn[start:end]
    assume(quote.strip())

    assert verify_quote(turn, quote) == "verified"


@given(turn=TURN_TEXT, data=st.data())
def test_property_a_character_changed_never_verifies(turn: str, data: st.DataObject) -> None:
    start = data.draw(st.integers(min_value=0, max_value=len(turn) - 1))
    end = data.draw(st.integers(min_value=start + 1, max_value=len(turn)))
    quote = turn[start:end]
    positions = [i for i, char in enumerate(quote) if not char.isspace()]
    assume(positions)
    position = data.draw(st.sampled_from(positions))
    altered = quote[:position] + "Ω" + quote[position + 1 :]

    assert verify_quote(turn, altered) == "not_found"


PIECE = st.text(alphabet="abcdefgh \t", max_size=20)


@given(prefix=PIECE, first=TURN_TEXT, middle=PIECE, second=TURN_TEXT, suffix=PIECE)
def test_property_two_ordered_fragments_join_with_the_ellipsis(
    prefix: str, first: str, middle: str, second: str, suffix: str
) -> None:
    turn = prefix + first + middle + second + suffix

    assert verify_quote(turn, f"{first} […] {second}") == "verified"


@settings(suppress_health_check=[HealthCheck.filter_too_much])
@given(turn=TURN_TEXT, data=st.data())
def test_property_swapping_two_distinct_fragments_cannot_verify_when_they_occur_once(
    turn: str, data: st.DataObject
) -> None:
    cut = data.draw(st.integers(min_value=1, max_value=len(turn) - 1)) if len(turn) > 1 else 0
    first, second = turn[:cut], turn[cut:]
    assume(first.strip() and second.strip())
    normalized = normalize_spaces(turn)
    left, right = normalize_spaces(first), normalize_spaces(second)
    assume(normalized.count(left) == 1 and normalized.count(right) == 1)
    assume(normalized.find(left) < normalized.find(right))

    assert verify_quote(turn, f"{right} […] {left}") == "not_found"
