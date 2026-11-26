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
# El plegado nunca debe detectar menos que el de antes de C8 2.1.0 (AUTONOMIA-03). Dos reglas lo
# garantizan:
# 1. La descomposición de compatibilidad solo se aplica a los caracteres que ya son letra o dígito
#    (`\w`). Los demás (™, №, ⓐ, ㎡…) siguen con NFD y conservan su papel de separador.
# 2. Doble pliegue (`also_as_separators: newly_dropped`): los puntos de `dropped_code_points` que
#    antes no se descartaban (los `Cn` sin asignar, que eran separadores, y los rellenos Hangul) se
#    descartan en la primera pasada y cuentan como separadores en una segunda; el resultado es la
#    unión de las dos. Una sola pasada uniría `es` + U+2065 + `falso`, que antes se detectaba.
_COMPATIBILITY_SCOPE = "word_characters"
_ALSO_AS_SEPARATORS = "newly_dropped"
_WORD_CHARACTER = re.compile(r"\w")
_MAX_CODE_POINT = 0x10FFFF
# Mínimo de fallo cerrado en tiempo de ejecución (F-02, F-05): un C8 adulterado no puede dejar ciego
# al escáner. Las categorías que se descartan son solo marcas y caracteres de formato, y todo punto
# de `dropped_code_points` debe ser invisible: `Cf`, `Mn`, `Me`, `Cn` (sin asignar) o uno de los
# cuatro rellenos Hangul (`Lo`), nombrados por su punto de código. Ningún rango cubre un espacio, un
# signo, un símbolo, una letra ni un dígito.
_DROPPABLE_CATEGORIES = frozenset({"Mn", "Me", "Cf"})
_INVISIBLE_CATEGORIES = _DROPPABLE_CATEGORIES | {"Cn"}
_HANGUL_FILLERS = frozenset({0x115F, 0x1160, 0x3164, 0xFFA0})


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
    # Los puntos de los rangos que antes no se descartaban, y un patrón para saber si el texto trae
    # alguno (la segunda pasada solo corre entonces).
    newly_dropped: frozenset[int]
    newly_dropped_pattern: re.Pattern[str]

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
    if fold.get("compatibility_scope") != _COMPATIBILITY_SCOPE:
        raise _fold_error(f"compatibility_scope desconocido (se espera {_COMPATIBILITY_SCOPE})")
    if fold.get("also_as_separators") != _ALSO_AS_SEPARATORS:
        raise _fold_error(f"also_as_separators desconocido (se espera {_ALSO_AS_SEPARATORS})")
    categories = fold.get("dropped_categories")
    if (
        not isinstance(categories, list)
        or not categories
        or not all(isinstance(c, str) and c in _DROPPABLE_CATEGORIES for c in categories)
    ):
        raise _fold_error("dropped_categories debe ser una lista no vacía dentro de Mn, Me y Cf")
    ranges = fold.get("dropped_code_points")
    if not isinstance(ranges, list) or not ranges:
        raise _fold_error("dropped_code_points debe ser una lista de rangos [inicio, fin]")
    previous_end = -1
    newly_dropped: set[int] = set()
    for item in ranges:
        if not (isinstance(item, list) and len(item) == 2 and all(_is_int(n) for n in item)):
            raise _fold_error("dropped_code_points trae un rango que no es [inicio, fin] entero")
        start, end = item
        if not previous_end < start <= end <= _MAX_CODE_POINT:
            raise _fold_error(
                "dropped_code_points trae un rango invertido, solapado o fuera de rango"
            )
        previous_end = end
        for code_point in range(start, end + 1):
            char = chr(code_point)
            if code_point not in _HANGUL_FILLERS and (
                unicodedata.category(char) not in _INVISIBLE_CATEGORIES
            ):
                raise _fold_error(
                    f"dropped_code_points cubre un carácter que no es invisible (U+{code_point:04X})"
                )
            if not (
                unicodedata.category(char) in _DROPPABLE_CATEGORIES or unicodedata.combining(char)
            ):
                newly_dropped.add(code_point)  # antes no se descartaba: era separador o letra
    return _Fold(
        categories=frozenset(categories),
        starts=tuple(item[0] for item in ranges),
        ends=tuple(item[1] for item in ranges),
        newly_dropped=frozenset(newly_dropped),
        newly_dropped_pattern=_pattern_of(sorted(newly_dropped)),
    )


def _pattern_of(code_points: list[int]) -> re.Pattern[str]:
    """Un patrón que acepta cualquiera de los puntos de código, agrupados en tramos seguidos."""
    runs: list[tuple[int, int]] = []
    for code_point in code_points:
        if runs and runs[-1][1] == code_point - 1:
            runs[-1] = (runs[-1][0], code_point)
        else:
            runs.append((code_point, code_point))
    body = "".join(f"\\U{first:08x}-\\U{last:08x}" for first, last in runs)
    return re.compile(f"[{body}]" if runs else "(?!)")


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


def _decompose(char: str) -> str:
    """La descomposición del carácter: NFKD si es letra o dígito (`\\w`), NFD si no (C8, `fold`)."""
    if _WORD_CHARACTER.match(char):
        return unicodedata.normalize(_NORMALIZATION, char)
    return unicodedata.normalize("NFD", char)


def _fold(text: str, separate_newly_dropped: bool = False) -> tuple[str, list[int]]:
    """El texto plegado y, por cada carácter, su posición en el original.

    Por carácter y en el orden de C8: descomposición (NFKD para letras y dígitos, NFD para el resto),
    descarte y plegado de mayúsculas (`casefold`). `ｆａｌｓｏ` (ancho completo) y las letras
    matemáticas pasan a ASCII; `™` o `№` no se vuelven letras y siguen separando palabras. En la
    segunda pasada (`separate_newly_dropped`), los puntos que antes no se descartaban cuentan como
    un espacio en lugar de desaparecer.
    """
    newly_dropped = _rules().newly_dropped
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for part in _decompose(char):
            if separate_newly_dropped and ord(part) in newly_dropped:
                chars.append(" ")
                origin.append(index)
                continue
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
    while end < len(text) and all(_dropped(part) for part in _decompose(text[end])):
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
    passes = [_fold(text)]
    if _rules().newly_dropped_pattern.search(text):
        passes.append(_fold(text, separate_newly_dropped=True))
    found: dict[Match, None] = {}
    for folded, origin in passes:
        for hit in pattern.finditer(folded):
            start = origin[hit.start()]
            end = _span_end(text, origin[hit.end() - 1])
            if any(start >= first and end <= last for first, last in skipped):
                continue
            term = _name(by_form[hit.group()], text[start:end])
            found[Match(term=term, start=start, end=end)] = None
    matches = sorted(found, key=lambda match: (match.start, match.end))
    return ScanResult(matches=matches, excluded=[content for _, _, content in quotes])


def scan(text: str, literal_sources: Sequence[str]) -> list[Match]:
    """Busca los términos de C8 por palabra completa, sin distinguir mayúsculas ni tildes.

    Excluye los tramos entre «…» cuyo contenido aparece literal en alguna de `literal_sources` y la
    cadena completa del aviso de VE-01 (BR9.2). La lista sale del archivo versionado de C8.
    """
    return scan_detailed(text, literal_sources).matches
