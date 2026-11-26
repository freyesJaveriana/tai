"""K-89 y K-91: el plegado del texto lo declara C8 (`match.fold`) y el escáner lo lee de ahí.

Casos sonda 1 a 8 de U01-T33. Todo sintético. Los caracteres que no son ASCII se arman con `chr`
para que se vea qué se prueba.
"""

import re
import unicodedata
from collections.abc import Callable, Iterator
from importlib.resources import files
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from veridicus_contracts.loaders import load_file

from veridicus_integrity_policy import notice, scan

C8_PATH = files("veridicus_contracts") / "integrity" / "forbidden-vocabulary.v2.yaml"

# Default_Ignorable_Code_Point (Unicode 15.0/16.0), en rangos cerrados: la lista que propone la tarea.
# Es el oráculo de estas pruebas: no se lee de C8, para que un C8 recortado no las haga pasar.
DROPPED_RANGES = [
    (0x00AD, 0x00AD),
    (0x034F, 0x034F),
    (0x061C, 0x061C),
    (0x115F, 0x1160),
    (0x17B4, 0x17B5),
    (0x180B, 0x180F),
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x206F),
    (0x3164, 0x3164),
    (0xFE00, 0xFE0F),
    (0xFEFF, 0xFEFF),
    (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8),
    (0x1BCA0, 0x1BCA3),
    (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
]
HANGUL_FILLERS = [chr(0x115F), chr(0x1160), chr(0x3164), chr(0xFFA0)]
UNASSIGNED = [chr(0x2065), chr(0xFFF0), chr(0xE0002), chr(0xE0080), chr(0xE0FFF)]


def _clear_caches() -> None:
    """Vacía toda `functools.cache` del módulo, sea cual sea la forma en que el escáner guarde C8."""
    for value in vars(scan).values():
        clear = getattr(value, "cache_clear", None)
        if callable(clear):
            clear()
    notice.load_notice.cache_clear()


@pytest.fixture(autouse=True)
def _fresh_caches() -> Iterator[None]:
    _clear_caches()
    yield
    _clear_caches()


def fullwidth(text: str) -> str:
    """Las letras ASCII pasan a su forma de ancho completo (U+FF21 a U+FF3A, U+FF41 a U+FF5A)."""
    return "".join(chr(ord(c) + 0xFEE0) if c.isascii() and c.isalpha() else c for c in text)


def math_bold(text: str) -> str:
    """Las letras minúsculas ASCII pasan a letras matemáticas en negrita (U+1D41A y siguientes)."""
    return "".join(chr(0x1D41A + ord(c) - ord("a")) if "a" <= c <= "z" else c for c in text)


def terms_of(text: str) -> list[str]:
    return [match.term for match in scan.scan(text, [])]


def covered(text: str) -> list[str]:
    return [text[match.start : match.end] for match in scan.scan(text, [])]


def plain(term: str) -> str:
    """El término sin tildes ni mayúsculas, para comparar sin depender de cuál de dos gemelos nombra."""
    decomposed = unicodedata.normalize("NFD", term)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


# --- Caso sonda 1: ancho completo ---------------------------------------------------------------


def test_the_fullwidth_alphabet_is_what_the_helper_says() -> None:
    assert fullwidth("falso") == "".join(chr(c) for c in (0xFF46, 0xFF41, 0xFF4C, 0xFF53, 0xFF4F))
    assert fullwidth("MIENTE") == "".join(
        chr(c) for c in (0xFF2D, 0xFF29, 0xFF25, 0xFF2E, 0xFF34, 0xFF25)
    )


@pytest.mark.parametrize(
    ("written", "term"),
    [
        (fullwidth("falso"), "falso"),
        (fullwidth("MIENTE"), "miente"),
        ("f" + chr(0xFF41) + "l" + chr(0xFF53) + "o", "falso"),
        (fullwidth("Mentiroso"), "mentiroso"),
    ],
    ids=["lower", "upper", "mixed", "capitalised"],
)
def test_a_fullwidth_term_does_not_evade_the_scanner(written: str, term: str) -> None:
    text = f"Dijo que era {written} ayer."

    matches = scan.scan(text, [])

    assert [(match.term, text[match.start : match.end]) for match in matches] == [(term, written)]


def test_a_fullwidth_term_at_the_edges_of_the_text_is_found() -> None:
    written = fullwidth("falso")

    assert covered(written) == [written]
    assert covered(f"{written}.") == [written]


# --- Caso sonda 2: compatibilidad -----------------------------------------------------------------


def test_a_compatibility_ligature_is_folded_to_its_letters() -> None:
    # U+FB05 (ſt) y U+FB06 (st) se pliegan a «st»; «mentisteis» es un término de C8 con «st».
    for ligature in (chr(0xFB05), chr(0xFB06)):
        written = f"menti{ligature}eis"
        text = f"Dijo que {written} ayer."

        assert [(m.term, text[m.start : m.end]) for m in scan.scan(text, [])] == [
            ("mentisteis", written)
        ]


def test_a_ligature_keeps_a_letter_next_to_it_inside_the_word() -> None:
    # La ligadura es una letra: «fi» + «falso» es una sola palabra, no una frontera.
    assert terms_of(chr(0xFB01) + "falso") == []
    assert terms_of(f"{chr(0xFB01)}nal {chr(0xFB01)}rma y falso") == ["falso"]


def test_mathematical_letters_are_folded() -> None:
    written = math_bold("falso")
    assert [hex(ord(c)) for c in written] == ["0x1d41f", "0x1d41a", "0x1d425", "0x1d42c", "0x1d428"]

    text = f"Dijo que era {written} ayer."

    assert [(m.term, text[m.start : m.end]) for m in scan.scan(text, [])] == [("falso", written)]


@pytest.mark.parametrize(
    "text",
    [
        fullwidth("falsete"),
        fullwidth("falsedad"),
        math_bold("falsete"),
        math_bold("false"),
        "falsete",
        fullwidth("mentira"),
    ],
)
def test_control_a_word_that_resembles_a_term_is_not_a_match(text: str) -> None:
    assert terms_of(f"Dijo {text} hoy.") == []


# --- Caso sonda 3: rellenos Hangul ----------------------------------------------------------------


@pytest.mark.parametrize("char", HANGUL_FILLERS, ids=[f"U+{ord(c):04X}" for c in HANGUL_FILLERS])
def test_a_hangul_filler_inside_a_term_does_not_evade_the_scanner(char: str) -> None:
    assert unicodedata.category(char) == "Lo"
    text = f"Dijo que era fal{char}so ayer."

    matches = scan.scan(text, [])

    assert [(match.term, text[match.start : match.end]) for match in matches] == [
        ("falso", f"fal{char}so")
    ]


@pytest.mark.parametrize("char", HANGUL_FILLERS, ids=[f"U+{ord(c):04X}" for c in HANGUL_FILLERS])
def test_a_hangul_filler_at_the_edge_of_a_term_keeps_the_word_boundary(char: str) -> None:
    assert terms_of(f"{char}falso{char} y nada más") == ["falso"]
    # F-04 (ronda 2): en la segunda pasada el relleno cuenta como separador, como un `Cn`.
    assert terms_of(f"es{char}falso") == ["falso"]


@pytest.mark.parametrize("char", HANGUL_FILLERS, ids=[f"U+{ord(c):04X}" for c in HANGUL_FILLERS])
def test_a_term_followed_by_a_hangul_filler_includes_it_in_the_span(char: str) -> None:
    text = f"Dijo que falso{char}{char} ayer."

    assert covered(text) == [f"falso{char}{char}"]


# --- Caso sonda 4: sin asignar ----------------------------------------------------------------------


@pytest.mark.parametrize("char", UNASSIGNED, ids=[f"U+{ord(c):04X}" for c in UNASSIGNED])
def test_an_unassigned_default_ignorable_inside_a_term_does_not_evade_the_scanner(
    char: str,
) -> None:
    assert unicodedata.category(char) == "Cn"
    text = f"el testigo mi{char}ente hoy"

    matches = scan.scan(text, [])

    assert [(match.term, text[match.start : match.end]) for match in matches] == [
        ("miente", f"mi{char}ente")
    ]


@pytest.mark.parametrize("char", UNASSIGNED, ids=[f"U+{ord(c):04X}" for c in UNASSIGNED])
def test_an_unassigned_default_ignorable_at_the_edge_of_a_term_keeps_the_word_boundary(
    char: str,
) -> None:
    assert terms_of(f"{char}falso{char} y nada más") == ["falso"]


@pytest.mark.parametrize("char", UNASSIGNED, ids=[f"U+{ord(c):04X}" for c in UNASSIGNED])
def test_a_term_followed_by_an_unassigned_default_ignorable_includes_it_in_the_span(
    char: str,
) -> None:
    assert unicodedata.category(char) == "Cn"
    text = f"Dijo que falso{char}{char} ayer."

    assert covered(text) == [f"falso{char}{char}"]


# --- Caso sonda 6: sin falso positivo --------------------------------------------------------------


@pytest.mark.parametrize("code_point", [0x2010, 0x2011, 0x3165, 0x2070, 0xFFFD, 0x00B7])
def test_a_visible_character_of_a_neighbouring_range_still_splits_the_word(code_point: int) -> None:
    char = chr(code_point)
    assert char not in "".join(chr(p) for a, b in DROPPED_RANGES for p in range(a, b + 1))

    assert terms_of(f"fal{char}so") == []


def test_a_text_without_terms_and_with_fullwidth_characters_has_no_matches() -> None:
    text = f"{fullwidth('Hola mundo')} {chr(0xFF11)}{chr(0xFF12)}{chr(0xFF13)} {fullwidth('casa')}"

    assert terms_of(text) == []


# --- Caso sonda 7: las exclusiones siguen igual ----------------------------------------------------


def test_a_literal_quote_with_a_fullwidth_term_is_still_excluded() -> None:
    inner = f"era {fullwidth('falso')}, dijo"
    text = f"Dijo «{inner}» y miente."

    result = scan.scan_detailed(text, [inner])

    assert result.excluded == [inner]
    assert [match.term for match in result.matches] == ["miente"]


def test_a_quote_that_is_only_a_fullwidth_term_is_scanned() -> None:
    """D-2: el tramo «…» que es solo el término se escanea, aunque la fuente lo traiga literal."""
    written = fullwidth("falso")
    text = f"Dijo «{written}» ya."

    result = scan.scan_detailed(text, [written])

    assert result.excluded == []
    assert [(m.term, text[m.start : m.end]) for m in result.matches] == [("falso", written)]


def test_a_quote_that_is_only_a_term_with_a_hangul_filler_is_scanned() -> None:
    written = f"fal{chr(0x3164)}so"
    text = f"Dijo «{written}» ya."

    result = scan.scan_detailed(text, [written])

    assert result.excluded == []
    assert [match.term for match in result.matches] == ["falso"]


# --- Caso sonda 5: fallo cerrado --------------------------------------------------------------------


def _c8_with(change: Callable[[dict[str, Any]], Any]) -> dict[str, Any]:
    """C8 en la forma 2.1.0, armado con el oráculo de esta prueba, y luego el cambio que se ensaya."""
    document: Any = load_file(C8_PATH)
    document["schema_version"] = "2.1.0"
    document["match"]["fold"] = {
        "normalization": "NFKD",
        "compatibility_scope": "word_characters",
        "also_as_separators": "newly_dropped",
        "case": "casefold",
        "dropped_categories": ["Mn", "Me", "Cf"],
        "dropped_code_points": [list(rango) for rango in DROPPED_RANGES],
    }
    change(document)
    return dict(document)


def _scan_with(monkeypatch: pytest.MonkeyPatch, document: dict[str, Any]) -> None:
    monkeypatch.setattr(scan, "load_file", lambda _path: document)
    _clear_caches()
    scan.scan("Un texto cualquiera.", [])


def test_the_control_a_c8_with_the_approved_fold_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    _scan_with(monkeypatch, _c8_with(lambda document: None))


def test_the_versioned_c8_declares_the_fold_the_oracle_expects() -> None:
    document: Any = load_file(C8_PATH)
    fold = document["match"]["fold"]

    assert document["schema_version"] == "2.1.0"
    assert fold["normalization"] == "NFKD"
    assert fold["compatibility_scope"] == "word_characters"
    assert fold["also_as_separators"] == "newly_dropped"
    assert fold["case"] == "casefold"
    assert fold["dropped_categories"] == ["Mn", "Me", "Cf"]
    assert [tuple(rango) for rango in fold["dropped_code_points"]] == DROPPED_RANGES


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda d: d["match"].pop("fold"), id="sin-fold"),
        pytest.param(lambda d: d["match"].update(fold=None), id="fold-nulo"),
        pytest.param(lambda d: d["match"].update(fold=[]), id="fold-no-es-objeto"),
        pytest.param(lambda d: d["match"]["fold"].update(normalization="NFC"), id="nfc"),
        pytest.param(lambda d: d["match"]["fold"].update(normalization="NFD"), id="nfd"),
        pytest.param(lambda d: d["match"]["fold"].update(normalization=None), id="sin-norm"),
        pytest.param(lambda d: d["match"]["fold"].update(case="lower"), id="case-lower"),
        pytest.param(lambda d: d["match"]["fold"].pop("case"), id="sin-case"),
        pytest.param(lambda d: d["match"]["fold"].pop("dropped_code_points"), id="sin-rangos"),
        pytest.param(lambda d: d["match"]["fold"].pop("dropped_categories"), id="sin-categorias"),
        pytest.param(lambda d: d["match"]["fold"].update(dropped_categories=["Xx"]), id="cat-xx"),
        pytest.param(lambda d: d["match"]["fold"].pop("also_as_separators"), id="sin-separadores"),
        pytest.param(
            lambda d: d["match"]["fold"].update(also_as_separators="none"), id="separadores-no"
        ),
        # F-05 de la ronda 2: todo punto de `dropped_code_points` debe ser invisible.
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x20, 0x20]]),
            id="rango-sobre-el-espacio",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x2E, 0x2E]]),
            id="rango-sobre-un-signo",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x2B, 0x2B]]),
            id="rango-sobre-un-simbolo",
        ),
        pytest.param(lambda d: d["match"]["fold"].pop("compatibility_scope"), id="sin-alcance"),
        pytest.param(
            lambda d: d["match"]["fold"].update(compatibility_scope="all"), id="alcance-all"
        ),
        # F-02: un C8 adulterado no puede dejar ciego al escáner.
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_categories=["Lu", "Ll"]), id="cat-letras"
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_categories=["Mn", "Me", "Cf", "Cn"]),
            id="cat-cn",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x41, 0x7A]]),
            id="rango-letras-ascii",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x30, 0x39]]),
            id="rango-digitos",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x3164, 0x3165]]),
            id="rango-con-lo-que-no-es-relleno",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x0, 0x10FFFF]]),
            id="rango-de-todo",
        ),
        pytest.param(lambda d: d["match"]["fold"].update(dropped_categories=[]), id="cat-vacia"),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[]), id="rangos-vacio"
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[5]]), id="un-extremo"
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[["a", 5]]), id="texto"
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[9, 5]]), id="invertido"
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[1, 5], [5, 9]]), id="solapado"
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[10, 12], [1, 5]]),
            id="desordenado",
        ),
        pytest.param(
            lambda d: d["match"]["fold"].update(dropped_code_points=[[0x10FFFE, 0x110000]]),
            id="fuera-de-unicode",
        ),
        pytest.param(lambda d: d.update(match=None), id="match-nulo"),
    ],
)
def test_a_c8_without_a_known_fold_fails_closed_at_load(
    monkeypatch: pytest.MonkeyPatch, change: Callable[[dict[str, Any]], Any]
) -> None:
    """Nunca vuelve en silencio al pliegue anterior (NFD): carga y falla con `ValueError`.

    Convención fijada por esta tarea: la excepción es `ValueError` y su mensaje nombra `match.fold`.
    """
    document = _c8_with(change)

    with pytest.raises(ValueError, match=r"match\.fold"):
        _scan_with(monkeypatch, document)


def test_the_fold_is_read_from_c8_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    real = load_file

    def counted(path: Any) -> Any:
        calls.append(path)
        return real(path)

    monkeypatch.setattr(scan, "load_file", counted)
    _clear_caches()

    scan.scan("Una prueba.", [])
    after_first = len(calls)

    scan.scan(fullwidth("falso"), [])
    scan.scan_detailed(f"Dijo «{fullwidth('falso')}» ya.", [])
    scan.scan("mi" + chr(0x3164) + "ente", [])

    # Cuántas lecturas hace el primer `scan` (una o varias cachés) no importa; las siguientes, ninguna.
    assert after_first >= 1
    assert len(calls) == after_first


def test_the_scanner_takes_the_ranges_from_c8_and_not_from_its_own_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un C8 con otra lista de rangos cambia lo que el escáner descarta: la lectura es real."""
    document = _c8_with(
        lambda d: d["match"]["fold"].update(dropped_code_points=[[0xE0002, 0xE0002]])
    )
    monkeypatch.setattr(scan, "load_file", lambda _path: document)
    _clear_caches()

    assert terms_of("mi" + chr(0xE0002) + "ente") == ["miente"]
    # U+FFF0 es `Cn` y no está en la lista de este C8: no se descarta y parte la palabra.
    assert terms_of("mi" + chr(0xFFF0) + "ente") == []


# --- Caso sonda 8: propiedad (ML-12) ------------------------------------------------------------------


def _terms() -> list[str]:
    document: Any = load_file(C8_PATH)
    return [str(term) for term in document["terms"]]


TERMS = _terms()
RANGE = st.sampled_from(DROPPED_RANGES).flatmap(
    lambda r: st.integers(min_value=r[0], max_value=r[1])
)
# Solo los puntos que `main` ya descartaba (`Cf`, `Mn`, `Me` o con clase combinante): no separan.
# Los `Cn` y los rellenos Hangul cuentan como separador en la segunda pasada y pueden partir una
# palabra sin término en dos, una de ellas un término (`menti` + relleno + `ra`), como en `main`.
QUIET = st.sampled_from(
    [
        code_point
        for first, last in DROPPED_RANGES
        for code_point in range(first, last + 1)
        if unicodedata.category(chr(code_point)) in {"Cf", "Mn", "Me"}
        or unicodedata.combining(chr(code_point))
    ]
)


@st.composite
def hidden_term(draw: st.DrawFn) -> tuple[str, str, int, int]:
    """Un término de C8 con inserciones y letras de ancho completo: texto, término, primera y última letra."""
    term = draw(st.sampled_from(TERMS))
    letters = [
        chr(ord(c) + 0xFEE0) if c.isascii() and c.isalpha() and draw(st.booleans()) else c
        for c in term
    ]
    insertions = draw(
        st.lists(st.tuples(st.integers(min_value=0, max_value=len(letters)), RANGE), max_size=6)
    )
    cells = [(c, True) for c in letters]
    for position, code_point in sorted(insertions, key=lambda item: item[0], reverse=True):
        cells.insert(position, (chr(code_point), False))
    prefix = "Dijo que "
    text = prefix + "".join(c for c, _ in cells) + " ayer."
    indexes = [len(prefix) + i for i, (_, is_letter) in enumerate(cells) if is_letter]
    return text, term, indexes[0], indexes[-1]


@settings(
    max_examples=120,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(case=hidden_term())
def test_property_a_term_with_hidden_characters_and_fullwidth_letters_is_always_found(
    case: tuple[str, str, int, int],
) -> None:
    text, term, first, last = case

    matches = scan.scan(text, [])

    # Con un `Cn` dentro del término, la segunda pasada lo cuenta como separador y puede añadir una
    # coincidencia más corta (`menti` + U+E0000 + `roso`, como en `main`): basta con que esté la
    # coincidencia del término entero y que todas caigan dentro del texto.
    assert any(
        plain(match.term) == plain(term) and 0 <= match.start <= first and last < match.end
        for match in matches
    )
    assert all(0 <= match.start < match.end <= len(text) for match in matches)


@settings(max_examples=60, deadline=None)
@given(
    words=st.lists(
        st.sampled_from(["hola", "mundo", "casa", "falsete", "mentira", "Ñandú"]), min_size=1
    ),
    insertions=st.lists(st.tuples(st.integers(min_value=0, max_value=30), QUIET), max_size=5),
    wide=st.booleans(),
)
def test_property_a_text_without_terms_never_matches_however_it_is_written(
    words: list[str], insertions: list[tuple[int, int]], wide: bool
) -> None:
    text = " ".join(fullwidth(word) if wide else word for word in words)
    for position, code_point in sorted(insertions, reverse=True):
        spot = position % (len(text) + 1)
        # Solo dentro de una palabra: junto a un espacio no cambia nada y junto a otra letra tampoco.
        if 0 < spot < len(text) and text[spot - 1] != " " and text[spot] != " ":
            text = text[:spot] + chr(code_point) + text[spot:]

    assert scan.scan(text, []) == []


# --- F-01 de la ronda 1: el plegado solo amplía lo que se detecta (AUTONOMIA-03) -----------------------

TRADEMARK = chr(0x2122)  # ™
NUMERO = chr(0x2116)  # №
CIRCLED_A = chr(0x24D0)  # ⓐ
SQUARE_M2 = chr(0x33A1)  # ㎡
SERVICE_MARK = chr(0x2120)  # ℠
SEPARATING_SYMBOLS = [TRADEMARK, NUMERO, CIRCLED_A, SQUARE_M2, SERVICE_MARK]


@pytest.mark.parametrize(
    "char", SEPARATING_SYMBOLS, ids=[f"U+{ord(c):04X}" for c in SEPARATING_SYMBOLS]
)
def test_a_compatibility_symbol_glued_to_a_term_still_separates_it(char: str) -> None:
    """Antes de C8 2.1.0 estos símbolos partían la palabra; NFKD los volvía letras y escondía el término."""
    assert terms_of(f"Es falso{char}") == ["falso"]
    assert terms_of(f"{char}falso y nada") == ["falso"]
    assert terms_of(f"Dijo {char}falso{char} hoy") == ["falso"]
    assert covered(f"Es falso{char}") == ["falso"]


def test_a_compatibility_letter_glued_to_a_term_still_hides_it_like_any_letter() -> None:
    """Control: una letra de compatibilidad sí es letra y pega la palabra (no hay falso positivo nuevo)."""
    assert terms_of("falso" + chr(0xFF41)) == []  # «ａ» de ancho completo
    assert terms_of(chr(0x1D41A) + "falso") == []  # «𝐚» matemática


def _old_fold(text: str) -> str:
    """El pliegue de `main` (NFD para todo carácter), escrito aparte para comparar."""
    chars: list[str] = []
    for char in text:
        for part in unicodedata.normalize("NFD", char):
            if unicodedata.combining(part) or unicodedata.category(part) in {"Cf", "Mn", "Me"}:
                continue
            chars.append(part.casefold())
    return "".join(chars)


def _old_detects(text: str) -> bool:
    return re.search(r"(?<!\w)falso(?!\w)", _old_fold(text)) is not None


def _checked_code_points() -> list[str]:
    """Los caracteres donde el pliegue pudo cambiar frente a `main`.

    Los que NFKD descompone distinto de NFD (el alcance de la compatibilidad) y todos los puntos de
    los 17 rangos de `dropped_code_points` (el descarte). En ningún otro carácter cambia la forma
    plegada. Son unos 8000 puntos; el recorrido completo tarda alrededor de un segundo, así que no se
    reduce a una muestra.
    """
    points = {
        code_point
        for code_point in range(0x110000)
        if not 0xD800 <= code_point <= 0xDFFF
        and unicodedata.normalize("NFKD", chr(code_point))
        != unicodedata.normalize("NFD", chr(code_point))
    }
    points.update(
        code_point for first, last in DROPPED_RANGES for code_point in range(first, last + 1)
    )
    return [chr(code_point) for code_point in sorted(points)]


# Las siete plantillas: letra + punto + término, término + punto + letra, el punto pegado al término
# por cada lado, dentro del término y rodeándolo.
TEMPLATES = (
    "es{c}falso",
    "falso{c}es",
    "Es falso{c}",
    "{c}falso y",
    "fal{c}so",
    "{c}fal{c}so{c}",
    "es {c}falso{c} es",
)


def test_the_fold_never_detects_less_than_before() -> None:
    """AUTONOMIA-03: todo lo que el pliegue de `main` detectaba, el escáner lo detecta.

    Para cada punto que pudo cambiar, siete plantillas: si el pliegue de `main` detectaba `falso`,
    el escáner también. El control: la comparación se hizo de verdad (más de 5000 casos).
    """
    checked = 0
    for char in _checked_code_points():
        for template in TEMPLATES:
            text = template.format(c=char)
            if _old_detects(text):
                checked += 1
                assert "falso" in terms_of(text), f"U+{ord(char):04X} en {text!r}"
    assert checked > 5000


# --- F-04 de la ronda 2: los puntos que antes separaban siguen separando (doble pliegue) -----------------


def test_an_unassigned_point_between_a_letter_and_a_term_still_separates_them() -> None:
    text = "es" + chr(0x2065) + "falso"

    assert [(m.term, m.start, m.end) for m in scan.scan(text, [])] == [("falso", 3, 8)]


def test_an_unassigned_point_inside_a_term_still_joins_it() -> None:
    text = "fal" + chr(0x2065) + "so"

    assert [(m.term, m.start, m.end) for m in scan.scan(text, [])] == [("falso", 0, 6)]


def test_a_hangul_filler_between_a_letter_and_a_term_counts_as_a_separator_in_the_second_pass() -> (
    None
):
    text = "es" + chr(0x3164) + "falso"

    assert [(m.term, m.start, m.end) for m in scan.scan(text, [])] == [("falso", 3, 8)]


def test_the_union_of_both_passes_has_no_duplicates_and_is_sorted() -> None:
    text = "es" + chr(0x2065) + "falso y miente y fal" + chr(0x2065) + "so, falso" + chr(0x2065)

    spans = [(m.term, m.start, m.end) for m in scan.scan(text, [])]

    assert spans == sorted(set(spans), key=lambda span: (span[1], span[2]))
    assert [term for term, _start, _end in spans] == ["falso", "miente", "falso", "falso"]


def test_a_text_with_an_unassigned_point_and_no_term_has_no_matches() -> None:
    assert scan.scan("es" + chr(0x2065) + "casa" + chr(0xFFF0) + "hoy", []) == []


def test_the_exclusions_apply_to_the_second_pass_too() -> None:
    inner = "era" + chr(0x2065) + "falso, dijo"
    text = f"Dijo «{inner}» y miente."

    result = scan.scan_detailed(text, [inner])

    assert result.excluded == [inner]
    assert [match.term for match in result.matches] == ["miente"]


def test_a_c8_with_only_format_characters_has_no_second_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sin puntos «nuevos» en los rangos, el patrón no acepta nada y no hay segunda pasada."""
    document = _c8_with(lambda d: d["match"]["fold"].update(dropped_code_points=[[0x200B, 0x200F]]))
    monkeypatch.setattr(scan, "load_file", lambda _path: document)
    _clear_caches()

    assert terms_of("mi" + chr(0x200B) + "ente") == ["miente"]
    # U+2065 no está en este C8: es un `Cn` sin descartar y separa, como en `main`.
    assert terms_of("es" + chr(0x2065) + "miente") == ["miente"]
