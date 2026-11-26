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
from bisect import bisect_right
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from typing import Any, Literal

from veridicus_contracts.loaders import load_file

from veridicus_integrity_policy import notice

_QUOTED = re.compile("«([^«»]*)»")
_NOT_WORD_EDGES = re.compile(r"^\W+|\W+$")
_WHITESPACE = re.compile(r"\s+")
# Los valores de `match.fold` que este escáner sabe aplicar (C8 2.1.0). Cualquier otro valor es un
# C8 que el escáner no entiende y la carga falla.
_NORMALIZATION: Literal["NFKD"] = "NFKD"
_CASE = "casefold"
_MAX_CODE_POINT = 0x10FFFF
_GENERAL_CATEGORIES = frozenset(
    {"Lu", "Ll", "Lt", "Lm", "Lo", "Mn", "Mc", "Me", "Nd", "Nl", "No", "Pc", "Pd", "Ps", "Pe"}
    | {"Pi", "Pf", "Po", "Sm", "Sc", "Sk", "So", "Zs", "Zl", "Zp", "Cc", "Cf", "Cs", "Co", "Cn"}
)


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


@dataclass(frozen=True)
class _Fold:
    """El plegado que declara C8 en `match.fold`: qué se descarta, ya listo para consultar."""

    categories: frozenset[str]
    starts: tuple[int, ...]
    ends: tuple[int, ...]

    def covers(self, code_point: int) -> bool:
        """El punto de código está en alguno de los rangos cerrados (búsqueda binaria)."""
        index = bisect_right(self.starts, code_point) - 1
        return index >= 0 and code_point <= self.ends[index]


def _fold_error(problem: str) -> ValueError:
    return ValueError(f"C8: match.fold {problem}")


def _is_int(value: object) -> bool:
    return type(value) is int


@cache
def _c8() -> Any:
    """El documento de C8, leído una sola vez del archivo versionado."""
    return load_file(files("veridicus_contracts") / "integrity" / "forbidden-vocabulary.v2.yaml")


def _read_fold(document: Any) -> _Fold:
    """Lee `match.fold` de C8. Falla cerrado con `ValueError` si falta o trae un valor desconocido.

    Nunca vuelve en silencio a un pliegue anterior: un escáner que plegara distinto de C8 dejaría
    pasar lo que la consola ve (AUTONOMIA-03).
    """
    match = document.get("match") if isinstance(document, Mapping) else None
    fold = match.get("fold") if isinstance(match, Mapping) else None
    if not isinstance(fold, Mapping):
        raise _fold_error("falta o no es un objeto")
    if fold.get("normalization") != _NORMALIZATION:
        raise _fold_error(f"normalization desconocida (se espera {_NORMALIZATION})")
    if fold.get("case") != _CASE:
        raise _fold_error(f"case desconocido (se espera {_CASE})")
    categories = fold.get("dropped_categories")
    if (
        not isinstance(categories, list)
        or not categories
        or not all(isinstance(c, str) and c in _GENERAL_CATEGORIES for c in categories)
    ):
        raise _fold_error(
            "dropped_categories debe ser una lista de categorías generales de Unicode"
        )
    ranges = fold.get("dropped_code_points")
    if not isinstance(ranges, list) or not ranges:
        raise _fold_error("dropped_code_points debe ser una lista de rangos [inicio, fin]")
    previous_end = -1
    for item in ranges:
        if not (isinstance(item, list) and len(item) == 2 and all(_is_int(n) for n in item)):
            raise _fold_error("dropped_code_points trae un rango que no es [inicio, fin] entero")
        start, end = item
        if not previous_end < start <= end <= _MAX_CODE_POINT:
            raise _fold_error(
                "dropped_code_points trae un rango invertido, solapado o fuera de rango"
            )
        previous_end = end
    return _Fold(
        categories=frozenset(categories),
        starts=tuple(item[0] for item in ranges),
        ends=tuple(item[1] for item in ranges),
    )


@cache
def _rules() -> _Fold:
    """El plegado de C8, leído y comprobado una sola vez."""
    return _read_fold(_c8())


def _dropped(part: str) -> bool:
    """El carácter no cuenta para la forma plegada.

    Se descarta lo que C8 manda en `match.fold`: los combinantes (clase combinante distinta de 0),
    las categorías de `dropped_categories` (`Mn`, `Me`, `Cf`) y los rangos de
    `dropped_code_points` (Default_Ignorable_Code_Point: rellenos Hangul y `Cn` sin asignar
    incluidos). No se ven en la consola y no parten la palabra (UAX #29, WB4: `Extend` y `Format`).
    """
    rules = _rules()
    return (
        bool(unicodedata.combining(part))
        or unicodedata.category(part) in rules.categories
        or rules.covers(ord(part))
    )


def _fold(text: str) -> tuple[str, list[int]]:
    """El texto plegado y, por cada carácter, su posición en el original.

    Por carácter y en el orden de C8: descomposición de compatibilidad (NFKD), descarte y plegado de
    mayúsculas (`casefold`). `ｆａｌｓｏ` (ancho completo) y las letras matemáticas pasan a ASCII.
    """
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for part in unicodedata.normalize(_NORMALIZATION, char):
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
        _dropped(part) for part in unicodedata.normalize(_NORMALIZATION, text[end])
    ):
        end += 1
    return end


@cache
def _vocabulary() -> tuple[re.Pattern[str], dict[str, list[str]]]:
    """El patrón de palabra completa de C8 y los términos de la lista que cada forma plegada nombra."""
    document = _c8()
    _rules()
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
