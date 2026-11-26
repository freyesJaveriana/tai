"""Escáner de vocabulario prohibido (BR9.1 a BR9.4, AUTONOMIA-03).

La lista sale de `integrity/forbidden-vocabulary.v2.yaml` (C8), empaquetado por
`veridicus_contracts`, y se lee una sola vez. La búsqueda es por palabra completa, sin distinguir
mayúsculas ni tildes (`ñ` cuenta como `n`), y cada coincidencia lleva su posición en el texto
original. Un término entre «…» queda fuera solo si el contenido aparece literal en una fuente y el
tramo es algo más que el término mismo (D-2, `scan_bare_term_spans`). El aviso de VE-01 se excluye
entero (BR9.2).
"""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from typing import Any

from veridicus_contracts.loaders import load_file

from veridicus_integrity_policy import notice

_QUOTED = re.compile("«([^«»]*)»")
_NOT_WORD_EDGES = re.compile(r"^\W+|\W+$")
_WHITESPACE = re.compile(r"\s+")
_IGNORED_CATEGORIES = frozenset({"Cf", "Mn", "Me"})


@dataclass(frozen=True)
class Match:
    """Una coincidencia con un término de C8: el término y su posición en el texto."""

    term: str
    start: int
    end: int


@dataclass(frozen=True)
class ScanResult:
    """Las coincidencias y los tramos «…» que se excluyeron por ser citas literales."""

    matches: list[Match]
    excluded: list[str]


def _dropped(part: str) -> bool:
    """El carácter no cuenta para la forma plegada.

    Los combinantes, las marcas no espaciadas (`Mn`, `Me`, aunque su clase combinante sea 0: U+034F,
    U+FE00, U+FE0F, U+E0100, U+180B, U+17B4) y los caracteres de formato (`Cf`: U+00AD, U+200B a
    U+200D, U+2060, U+FEFF) no se ven en la consola y no parten la palabra (UAX #29, WB4: `Extend`
    y `Format`).
    """
    return bool(unicodedata.combining(part)) or unicodedata.category(part) in _IGNORED_CATEGORIES


def _fold(text: str) -> tuple[str, list[int]]:
    """El texto sin mayúsculas ni tildes y, por cada carácter, su posición en el original."""
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for part in unicodedata.normalize("NFD", char):
            if _dropped(part):
                continue
            for folded in part.casefold():
                chars.append(folded)
                origin.append(index)
    return "".join(chars), origin


def _span_end(text: str, last_letter: int) -> int:
    """El final del tramo: después de la última letra y de las marcas descartadas que la siguen.

    `engañó` escrito en NFD termina en `o` seguida de un combinante; el tramo informado (K-91) lleva
    también esa marca, para que el término y su posición cubran lo que se ve escrito.
    """
    end = last_letter + 1
    while end < len(text) and all(
        _dropped(part) for part in unicodedata.normalize("NFD", text[end])
    ):
        end += 1
    return end


@cache
def _vocabulary() -> tuple[re.Pattern[str], dict[str, list[str]]]:
    """El patrón de palabra completa de C8 y los términos de la lista que cada forma plegada nombra."""
    document: Any = load_file(
        files("veridicus_contracts") / "integrity" / "forbidden-vocabulary.v2.yaml"
    )
    by_form: dict[str, list[str]] = {}
    for term in document["terms"]:
        by_form.setdefault(_fold(term)[0], []).append(str(term))
    forms = sorted(by_form, key=len, reverse=True)
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(form) for form in forms) + r")(?!\w)")
    return pattern, by_form


def _name(candidates: list[str], covered: str) -> str:
    """El término de la lista que el texto cubre.

    Dos términos que solo difieren en tildes («engaño» y «engañó») comparten forma plegada: gana el
    que el texto escribe igual, y si ninguno, el primero de la lista.
    """
    wanted = unicodedata.normalize("NFC", covered).casefold()
    for candidate in candidates:
        if unicodedata.normalize("NFC", candidate).casefold() == wanted:
            return candidate
    return candidates[0]


def _squash(text: str) -> str:
    """El texto con cada tramo de espacios reducido a un espacio: solo los espacios no cuentan."""
    return _WHITESPACE.sub(" ", text).strip()


def _is_bare_term(content: str) -> bool:
    """El contenido del tramo es solo un término de C8, con o sin signos en los bordes (D-2)."""
    pattern, _by_form = _vocabulary()
    folded, _origin = _fold(content)
    return pattern.fullmatch(_NOT_WORD_EDGES.sub("", folded)) is not None


def _literal_quotes(text: str, literal_sources: Sequence[str]) -> list[tuple[int, int, str]]:
    """Los tramos «…» literales que no son solo un término: inicio, fin y contenido."""
    sources = [_squash(source) for source in literal_sources]
    spans: list[tuple[int, int, str]] = []
    for quoted in _QUOTED.finditer(text):
        content = quoted.group(1)
        squashed = _squash(content)
        if not squashed or _is_bare_term(content):
            continue
        if any(squashed in source for source in sources):
            spans.append((quoted.start(1), quoted.end(1), content))
    return spans


def _notice_spans(text: str) -> list[tuple[int, int]]:
    """Los lugares donde el aviso de VE-01 aparece completo, salvo por los espacios."""
    words = notice.load_notice().text.split()
    pattern = re.compile(r"\s+".join(re.escape(word) for word in words))
    return [(found.start(), found.end()) for found in pattern.finditer(text)]


def scan_detailed(text: str, literal_sources: Sequence[str]) -> ScanResult:
    """Como `scan`, y además los tramos «…» que se excluyeron (los casos de C8 los comparan)."""
    pattern, by_form = _vocabulary()
    quotes = _literal_quotes(text, literal_sources)
    skipped = [(start, end) for start, end, _ in quotes] + _notice_spans(text)
    folded, origin = _fold(text)
    matches: list[Match] = []
    for found in pattern.finditer(folded):
        start = origin[found.start()]
        end = _span_end(text, origin[found.end() - 1])
        if any(start >= first and end <= last for first, last in skipped):
            continue
        term = _name(by_form[found.group()], text[start:end])
        matches.append(Match(term=term, start=start, end=end))
    return ScanResult(matches=matches, excluded=[content for _, _, content in quotes])


def scan(text: str, literal_sources: Sequence[str]) -> list[Match]:
    """Busca los términos de C8 por palabra completa, sin distinguir mayúsculas ni tildes.

    Excluye los tramos entre «…» cuyo contenido aparece literal en alguna de `literal_sources` y la
    cadena completa del aviso de VE-01 (BR9.2). La lista sale del archivo versionado de C8.
    """
    return scan_detailed(text, literal_sources).matches
