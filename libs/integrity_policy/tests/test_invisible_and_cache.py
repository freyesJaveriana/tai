"""Ronda 2: caracteres de formato invisibles (F-02) y aviso en caché (F-05). Todo sintético."""

import unicodedata
from collections.abc import Iterator
from typing import Any

import pytest

from veridicus_integrity_policy import notice, scan

# Caracteres de categoría Cf que la consola no muestra: guion blando, espacios de ancho cero,
# unidor de palabras y marca de orden de bytes.
INVISIBLE = [chr(0x00AD), chr(0x200B), chr(0x200C), chr(0x200D), chr(0x2060), chr(0xFEFF)]
ZWSP = chr(0x200B)


@pytest.fixture(autouse=True)
def _fresh_notice() -> Iterator[None]:
    notice.load_notice.cache_clear()
    yield
    notice.load_notice.cache_clear()


@pytest.mark.parametrize("char", INVISIBLE, ids=[f"U+{ord(c):04X}" for c in INVISIBLE])
def test_an_invisible_format_character_inside_a_term_does_not_evade_the_scanner(char: str) -> None:
    assert unicodedata.category(char) == "Cf"
    text = f"Dijo que mi{char}ente ayer."

    matches = scan.scan(text, [])

    assert [(match.term, text[match.start : match.end]) for match in matches] == [
        ("miente", f"mi{char}ente")
    ]


@pytest.mark.parametrize("char", INVISIBLE, ids=[f"U+{ord(c):04X}" for c in INVISIBLE])
def test_an_invisible_character_at_the_edge_of_a_term_keeps_the_word_boundary(char: str) -> None:
    text = f"{char}falso{char} y nada más"

    assert [match.term for match in scan.scan(text, [])] == ["falso"]


def test_an_invisible_character_does_not_hide_a_bare_term_between_quotes() -> None:
    text = f"Dijo «fal{ZWSP}so» ya."

    assert [match.term for match in scan.scan(text, [f"fal{ZWSP}so"])] == ["falso"]


def test_a_text_that_is_only_invisible_characters_has_no_matches() -> None:
    assert scan.scan("".join(INVISIBLE), []) == []


def test_the_notice_is_read_once_and_remembered(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    real: Any = notice._resource

    def counted() -> Any:
        calls.append(1)
        return real()

    monkeypatch.setattr(notice, "_resource", counted)

    first = notice.load_notice()
    scan.scan("Una prueba.", [])
    scan.scan("Otra prueba.", [])

    assert notice.load_notice() is first
    assert len(calls) == 1


# Marcas no espaciadas con clase combinante 0 (Mn) que UAX 29, WB4, ignora como Extend (F-07).
NON_SPACING = [chr(0x034F), chr(0xFE00), chr(0xFE0F), chr(0xE0100), chr(0x180B), chr(0x17B4)]


@pytest.mark.parametrize("char", NON_SPACING, ids=[f"U+{ord(c):04X}" for c in NON_SPACING])
def test_a_non_spacing_mark_of_combining_class_zero_does_not_evade_the_scanner(char: str) -> None:
    assert unicodedata.combining(char) == 0
    assert unicodedata.category(char) in {"Mn", "Me"}
    text = f"el testigo mi{char}ente hoy"

    matches = scan.scan(text, [])

    assert [(match.term, text[match.start : match.end]) for match in matches] == [
        ("miente", f"mi{char}ente")
    ]


def test_an_enclosing_mark_does_not_evade_the_scanner() -> None:
    enclosing = chr(0x20DD)
    assert unicodedata.category(enclosing) == "Me"

    assert [match.term for match in scan.scan(f"fal{enclosing}so", [])] == ["falso"]


def test_the_exclusions_still_work_with_invisible_and_non_spacing_characters() -> None:
    mark = chr(0xFE0F)
    source = f"era fal{mark}so, dijo"
    text = f"Dijo «era fal{mark}so» y miente."

    result = scan.scan_detailed(text, [source])

    assert result.excluded == [f"era fal{mark}so"]
    assert [match.term for match in result.matches] == ["miente"]
    loaded = notice.load_notice()
    glued = f"{loaded.text} mi{mark}ente"
    assert [match.term for match in scan.scan(glued, [])] == ["miente"]


def test_a_format_character_used_as_a_separator_joins_the_two_words() -> None:
    # Limitación declarada (F-11): con U+200B sin espacios, «es​falso» es una sola palabra para
    # UAX 29 y no coincide. Es coherente con WB4; la regla de separación de la consola es una
    # candidata de C8, junto con NFKC y los Default_Ignorable fuera de WB4.
    text = "es" + chr(0x200B) + "falso"

    assert scan.scan(text, []) == []


def _nfd(text: str) -> str:
    return unicodedata.normalize("NFD", text)


# K-91 (F-12 de U11-T02): el tramo informado incluye las marcas descartadas que siguen a la última letra.
ENGANO = "enga" + chr(0xF1) + chr(0xF3)  # engañó, con ñ y ó precompuestas


def test_a_term_in_nfd_is_reported_with_its_whole_span() -> None:
    written = _nfd(ENGANO)
    assert written != ENGANO and len(written) == len(ENGANO) + 2
    text = "Dijo que " + written + " ayer."

    matches = scan.scan(text, [])

    assert [(match.term, text[match.start : match.end]) for match in matches] == [(ENGANO, written)]


def test_a_term_at_the_very_end_of_the_text_keeps_its_trailing_marks() -> None:
    written = _nfd(ENGANO)
    text = "Dijo que " + written

    matches = scan.scan(text, [])

    assert [(match.start, match.end) for match in matches] == [(9, len(text))]


@pytest.mark.parametrize("char", INVISIBLE, ids=[f"U+{ord(c):04X}" for c in INVISIBLE])
def test_a_term_followed_by_an_invisible_character_includes_it_in_the_span(char: str) -> None:
    text = f"Dijo que falso{char}{char} ayer."

    matches = scan.scan(text, [])

    assert [text[match.start : match.end] for match in matches] == [f"falso{char}{char}"]


def test_control_a_visible_character_after_the_term_is_not_part_of_the_span() -> None:
    text = "Dijo que falso. Y luego nada."

    matches = scan.scan(text, [])

    assert [text[match.start : match.end] for match in matches] == ["falso"]
