"""Paso 7: seudonimización (F4) y tabla de correspondencia (BR1.1, BR1.7, BR1.8; E1-E3, E9-E13, E15).

Cada prueba arma sus mensajes con textos sintéticos; la parte de la restauración va en
`test_restoration.py`.
"""

import copy
import json
import pickle
import re
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from veridicus_contracts.model_calls import Message

from tests.support import boom, load_seeded, turns_of
from veridicus_anonymizer.domain import masking
from veridicus_anonymizer.domain.catalogs import Catalogs, load_catalogs
from veridicus_anonymizer.domain.detection import DetectedSpan
from veridicus_anonymizer.domain.masking import (
    MaskingBudgetExceeded,
    MaskingError,
    MaskTable,
    build_table,
    propagate,
    pseudonymize,
    serialize_messages,
)

CATALOGS = load_catalogs()
SEEDED = load_seeded()
CANONICAL_MARKER = re.compile(r"\[(?:PERSONA|LUGAR|EXPEDIENTE|IDENTIFICADOR|ENTIDAD)_[1-9][0-9]*\]")


def _user(*texts: str, ensure_ascii: bool = False) -> Message:
    turns = [{"turno": i + 1, "hablante": "TES", "texto": t} for i, t in enumerate(texts)]
    return Message("user", json.dumps({"turnos": turns}, ensure_ascii=ensure_ascii))


def _texts_of(message: Message) -> list[str]:
    parsed: dict[str, Any] = json.loads(message.content)
    return [t["texto"] for t in parsed["turnos"]]


def _mask(*texts: str, catalogs: Catalogs = CATALOGS) -> tuple[list[str], MaskTable]:
    masked, table = pseudonymize([_user(*texts)], catalogs)
    return _texts_of(masked[0]), table


# --- MaskTable (BR1.8) ----------------------------------------------------------------------------


def test_the_table_numbers_each_category_by_first_appearance_and_one_marker_per_form() -> None:
    table = MaskTable()

    assert table.add("Ana", "PERSONA") == "[PERSONA_1]"
    assert table.add("Casilda", "PERSONA") == "[PERSONA_2]"
    assert table.add("Ana", "PERSONA") == "[PERSONA_1]"
    assert table.add("La Esperanza", "LUGAR") == "[LUGAR_1]"
    assert table.add("ana", "PERSONA") == "[PERSONA_3]"
    assert len(table) == 4
    assert table.forms() == ["Ana", "Casilda", "La Esperanza", "ana"]
    assert table.marker_for("Casilda") == "[PERSONA_2]"
    assert table.marker_for("Nadie") is None
    assert table.original_for("[LUGAR_1]") == "La Esperanza"
    assert table.original_for("[LUGAR_2]") is None


def test_the_table_has_no_textual_representation_that_shows_values() -> None:
    table = MaskTable()
    table.add("Hermenegildo Canaryx", "PERSONA")

    for rendering in (repr(table), str(table), f"{table}", f"{table!r}", repr([table])):
        assert "Canaryx" not in rendering
    assert repr(table) == "MaskTable(<oculta>)"


def test_the_table_is_never_serialized_or_copied() -> None:
    table = MaskTable()
    table.add("Ana", "PERSONA")

    with pytest.raises(TypeError):
        pickle.dumps(table)
    with pytest.raises(TypeError):
        copy.deepcopy(table)


def test_clear_empties_the_table_and_restarts_the_numbering() -> None:
    table = MaskTable()
    table.add("Ana", "PERSONA")
    table.add("Casilda", "PERSONA")
    assert not table.is_empty

    table.clear()

    assert table.is_empty
    assert len(table) == 0
    assert table.original_for("[PERSONA_1]") is None
    assert table.add("Aurelio", "PERSONA") == "[PERSONA_1]"


# --- Escenarios de la especificación ----------------------------------------------------------------


def test_e1_names_places_case_numbers_and_identifiers_become_markers() -> None:
    text = (
        "doña Ana Pérez vivía en la vereda La Esperanza; Ana dijo que el radicado "
        "110016000-2019-00123 era de Pérez"
    )

    masked, table = _mask(text)

    expected = (
        "doña [PERSONA_1] vivía en la vereda [LUGAR_1]; [ENTIDAD_1] dijo que el radicado "
        "[EXPEDIENTE_1] era de [ENTIDAD_2]"
    )
    assert masked == [expected]
    assert table.forms() == [
        "Ana Pérez",
        "La Esperanza",
        "Ana",
        "110016000-2019-00123",
        "Pérez",
    ]


def test_e2_the_same_exact_form_has_the_same_marker_in_every_turn_and_a_different_form_another() -> (
    None
):
    masked, _ = _mask(
        "ayer vi a Casilda Roncancio en la plaza.",
        "luego Casilda Roncancio compró pan.",
        "después Casilda se fue.",
    )

    assert masked == [
        "ayer vi a [ENTIDAD_1] en la plaza.",
        "luego [ENTIDAD_1] compró pan.",
        "después [ENTIDAD_2] se fue.",
    ]


def test_a_form_is_also_marked_where_no_detector_found_it_but_with_word_boundaries() -> None:
    # Ningún detector marca la segunda «Ana» (está en la lista de palabras permitidas); la marca la
    # propagación por forma exacta, que respeta límites de palabra: «Ana» no toca «Anabel» ni «LaAna».
    allowed = CATALOGS.allowed_words | {"Ana", "Anabel", "LaAna"}
    catalogs = replace(CATALOGS, allowed_words=allowed)

    masked, _ = _mask("doña Ana vio a Ana, a Anabel y a LaAna.", catalogs=catalogs)

    assert masked == ["doña [PERSONA_1] vio a [PERSONA_1], a Anabel y a LaAna."]


def test_e3_san_jose_gets_one_marker_whatever_it_is() -> None:
    masked, table = _mask("vivía en San José y vio a San José otra vez.")

    assert masked == ["vivía en [LUGAR_1] y vio a [LUGAR_1] otra vez."]
    assert len(table) == 1


@pytest.mark.parametrize("ensure_ascii", [True, False], ids=["escapes_json", "tildes_directas"])
def test_e9_accented_names_written_as_json_escapes_are_masked_and_output_is_not_escaped(
    ensure_ascii: bool,
) -> None:
    message = _user(
        "ayer en el río vio a Eufrasio Mendívelso con Anselmo Páez.", ensure_ascii=ensure_ascii
    )
    assert ("\\u00ed" in message.content) is ensure_ascii

    masked, _ = pseudonymize([message], CATALOGS)

    assert "\\u" not in masked[0].content
    assert _texts_of(masked[0]) == ["ayer en el río vio a [ENTIDAD_1] con [ENTIDAD_2]."]


def test_e13_the_safety_net_is_not_applied_to_system_but_the_rules_are() -> None:
    system = Message(
        "system", "Los tipos son Fecha, Número y Persona; consulta a doña Ana Pérez si dudas."
    )

    masked, table = pseudonymize([system, _user("doña Ana Pérez dijo hola.")], CATALOGS)

    assert masked[0].content == (
        "Los tipos son Fecha, Número y Persona; consulta a doña [PERSONA_1] si dudas."
    )
    assert _texts_of(masked[1]) == ["doña [PERSONA_1] dijo hola."]
    assert masked[0].role == "system"
    assert table.forms() == ["Ana Pérez"]


def test_e15_a_literal_marker_in_the_testimony_gets_its_own_marker() -> None:
    masked, table = _mask("doña Ana Pérez escribió [PERSONA_1] y persona_3 en el acta.")

    assert masked == ["doña [PERSONA_1] escribió [ENTIDAD_1] y [ENTIDAD_2] en el acta."]
    assert table.original_for("[ENTIDAD_1]") == "[PERSONA_1]"
    assert table.original_for("[PERSONA_1]") == "Ana Pérez"


def test_a_name_in_the_allowed_list_is_visible_only_where_no_rule_marks_it() -> None:
    catalogs = replace(CATALOGS, allowed_words=CATALOGS.allowed_words | {"Casilda"})

    masked, _ = _mask("Casilda llegó. Luego dijo doña Casilda que sí.", catalogs=catalogs)

    # La regla de tratamiento marca la segunda; la propagación por forma exacta marca la primera.
    assert masked == ["[PERSONA_1] llegó. Luego dijo doña [PERSONA_1] que sí."]


def test_a_given_name_that_is_a_common_word_is_masked_at_the_start_of_a_sentence() -> None:
    masked, _ = _mask("Paz llegó temprano. Luz y Esperanza la esperaban.")

    assert masked == ["[ENTIDAD_1] llegó temprano. [ENTIDAD_2] y [ENTIDAD_3] la esperaban."]


# --- Estructura del mensaje -------------------------------------------------------------------------


def test_json_keys_numbers_and_other_values_are_never_touched() -> None:
    content = {
        "Aurelio": 5,
        "lista": ["doña Ana Pérez", 3, None, True, ["Aurelio Benavides vino"], 2.5],
        "turno": {"texto": "vio a Aurelio Benavides", "hablante": "TES"},
    }
    message = Message("user", json.dumps(content, ensure_ascii=False))

    masked, _ = pseudonymize([message], CATALOGS)

    assert json.loads(masked[0].content) == {
        "Aurelio": 5,
        "lista": ["doña [PERSONA_1]", 3, None, True, ["[ENTIDAD_1] vino"], 2.5],
        "turno": {"texto": "vio a [ENTIDAD_1]", "hablante": "TES"},
    }
    assert list(json.loads(masked[0].content)) == ["Aurelio", "lista", "turno"]


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('"doña Ana Pérez"', '"doña [PERSONA_1]"'),
        ("123", "123"),
        ("{doña Ana Pérez", "{doña [PERSONA_1]"),
        ("doña Ana Pérez", "doña [PERSONA_1]"),
        ("", ""),
    ],
    ids=["cadena_json", "numero_json", "json_roto", "texto_plano", "vacio"],
)
def test_a_content_that_is_not_a_json_object_or_list_is_plain_text(
    content: str, expected: str
) -> None:
    masked, _ = pseudonymize([Message("user", content)], CATALOGS)

    assert masked[0].content == expected


def test_with_no_messages_there_is_nothing_to_mask() -> None:
    masked, table = pseudonymize([], CATALOGS)

    assert masked == []
    assert table.is_empty


def test_numbering_follows_the_messages_in_order_and_each_text_left_to_right() -> None:
    messages = [
        Message("user", "vi a Casilda y a Aurelio."),
        Message("assistant", "dijo Aurelio que Casilda se fue con Eufrasio."),
    ]

    masked, table = pseudonymize(messages, CATALOGS)

    assert [m.content for m in masked] == [
        "vi a [ENTIDAD_1] y a [ENTIDAD_2].",
        "dijo [ENTIDAD_2] que [ENTIDAD_1] se fue con [ENTIDAD_3].",
    ]
    assert table.forms() == ["Casilda", "Aurelio", "Eufrasio"]


def test_the_assistant_role_also_gets_the_safety_net() -> None:
    masked, _ = pseudonymize([Message("assistant", "vi a Casilda.")], CATALOGS)

    assert masked == [Message("assistant", "vi a [ENTIDAD_1].")]


def test_f04_limit_a_loose_word_of_a_full_name_is_not_masked_in_system() -> None:
    # Límite declarado: `system` es texto fijo del sistema y no lleva testimonio (F-06).
    system = Message("system", "Consulta a Pérez o a Casilda si dudas.")

    masked, table = pseudonymize([system, _user("vio a Casilda Pérez ayer.")], CATALOGS)

    assert masked[0].content == "Consulta a Pérez o a Casilda si dudas."
    assert _texts_of(masked[1]) == ["vio a [ENTIDAD_1] ayer."]
    assert table.forms() == ["Casilda Pérez"]


def test_f04_a_form_that_is_a_whole_span_still_reaches_system_as_before() -> None:
    messages = [
        Message("user", "vivía en la vereda Cañada del Sauce y en La Esperanza."),
        Message("system", "Sauce, el río y Esperanza; del y La no se enmascaran."),
    ]

    masked, _ = pseudonymize(messages, CATALOGS)

    # «Esperanza» es un tramo entero (forma de tramo completo): llega a `system`. «Sauce», solo
    # palabra del tramo «Cañada del Sauce», no.
    assert masked[1].content == "Sauce, el río y [ENTIDAD_1]; del y La no se enmascaran."


def test_pd5_stable_prefix_the_same_text_with_new_turns_keeps_the_numbers() -> None:
    turns = [t["texto"] for t in turns_of(SEEDED)]
    base, _ = _mask(*turns[:9])
    extended, _ = _mask(*turns[:9], "después vieron a Hortensia Zapata y a Leocadia Mosquera.")

    assert extended[:9] == base
    assert "[ENTIDAD_" in extended[9]


SYSTEM_TEXT = Message("system", "Consulta a Pérez o a Casilda y a Ludovico si dudas.")


@pytest.mark.parametrize(
    ("before", "new_turn"),
    [
        (["vio a Aurelio ayer.", "luego Pérez salió."], "vieron a Casilda Pérez en la plaza."),
        (["vio a Casilda ayer."], "luego Casilda Pérez llegó con Ludovico Barrantes."),
        (["vio a Aurelio ayer."], "Entonces Ludovico Pérez y Casilda Barrantes hablaron."),
    ],
    ids=[
        "palabra_de_system_solo_en_un_tramo_nuevo",
        "palabra_suelta_en_user_anterior",
        "dos_tramos",
    ],
)
def test_f06_pd5_with_a_system_in_front_it_and_the_earlier_turns_are_identical_byte_for_byte(
    before: list[str], new_turn: str
) -> None:
    base, _ = pseudonymize([SYSTEM_TEXT, _user(*before)], CATALOGS)
    extended, _ = pseudonymize([SYSTEM_TEXT, _user(*before, new_turn)], CATALOGS)

    assert extended[0] == base[0]
    assert _texts_of(extended[1])[: len(before)] == _texts_of(base[1])


# --- Presupuesto y fallo cerrado ------------------------------------------------------------------


def _budget_that_runs_out_after(calls: int) -> Callable[[], bool]:
    state = {"left": calls}

    def has_budget() -> bool:
        state["left"] -= 1
        return state["left"] >= 0

    return has_budget


@pytest.mark.parametrize("calls", [0, 1, 2, 3, 4], ids=lambda n: f"agota_en_la_lectura_{n + 1}")
def test_nfr35_an_exhausted_budget_stops_the_pseudonymization_wherever_it_runs_out(
    calls: int,
) -> None:
    messages = [Message("system", "Eres un analista."), _user("doña Ana Pérez dijo hola.")]

    with pytest.raises(MaskingBudgetExceeded) as excinfo:
        pseudonymize(messages, CATALOGS, has_budget=_budget_that_runs_out_after(calls))

    assert "Ana" not in str(excinfo.value)


def test_a_budget_that_never_runs_out_lets_the_call_through() -> None:
    masked, table = pseudonymize(
        [_user("doña Ana Pérez dijo hola.")], CATALOGS, has_budget=lambda: True
    )

    assert _texts_of(masked[0]) == ["doña [PERSONA_1] dijo hola."]
    assert len(table) == 1


def test_a_failure_after_the_table_exists_empties_it_before_the_error_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[MaskTable] = []

    class RecordingTable(MaskTable):
        def __init__(self) -> None:
            super().__init__()
            created.append(self)

    monkeypatch.setattr(masking, "MaskTable", RecordingTable)
    monkeypatch.setattr(masking, "serialize_messages", boom)

    with pytest.raises(RuntimeError):
        pseudonymize([_user("doña Ana Pérez dijo hola.")], CATALOGS)

    assert len(created) == 1
    assert created[0].is_empty


def test_a_budget_exhausted_after_serializing_also_empties_the_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[MaskTable] = []

    class RecordingTable(MaskTable):
        def __init__(self) -> None:
            super().__init__()
            created.append(self)

    monkeypatch.setattr(masking, "MaskTable", RecordingTable)

    with pytest.raises(MaskingBudgetExceeded):
        pseudonymize(
            [_user("doña Ana Pérez dijo hola.")],
            CATALOGS,
            has_budget=_budget_that_runs_out_after(3),
        )

    assert created[0].is_empty


# --- Tramos, tabla y serialización por separado ------------------------------------------------------


def test_build_table_numbers_by_first_appearance_over_the_given_spans() -> None:
    texts = ["Ana vio a Luz", "Luz vio a Ana"]
    spans = [
        [DetectedSpan(0, 3, "PERSONA", "x"), DetectedSpan(10, 13, "PERSONA", "x")],
        [DetectedSpan(0, 3, "PERSONA", "x"), DetectedSpan(10, 13, "PERSONA", "x")],
    ]

    table = build_table(texts, spans)

    assert table.forms() == ["Ana", "Luz"]
    assert table.marker_for("Luz") == "[PERSONA_2]"


def test_propagation_grows_until_a_form_found_by_union_is_marked_everywhere() -> None:
    texts = ["Ana Pérez dijo hola.", "Ana Pérez Gómez vino. Ana Pérez Gómez se fue."]
    spans = [
        [DetectedSpan(0, 9, "ENTIDAD", "x")],
        [DetectedSpan(4, 15, "ENTIDAD", "x")],
    ]

    grown = propagate(texts, spans)

    assert [(s.start, s.end, s.category) for s in grown[0]] == [(0, 9, "ENTIDAD")]
    assert [(s.start, s.end) for s in grown[1]] == [(0, 15), (22, 37)]


def test_propagation_that_changes_nothing_returns_the_same_spans() -> None:
    texts = ["vio a Ana"]
    spans = [[DetectedSpan(6, 9, "PERSONA", "x")]]

    assert propagate(texts, spans) == spans


def test_propagation_respects_word_boundaries_on_both_sides() -> None:
    texts = ["Ana vio a Anabel y a LaAna, a _Ana y a Ana"]
    spans = [[DetectedSpan(0, 3, "PERSONA", "x")]]

    grown = propagate(texts, spans)

    assert [texts[0][s.start : s.end] for s in grown[0]] == ["Ana", "Ana"]
    assert [s.start for s in grown[0]] == [0, 39]


def test_serialize_rejects_spans_that_do_not_line_up_with_the_messages() -> None:
    messages = [_user("doña Ana Pérez dijo hola.")]
    table = MaskTable()
    table.add("Ana Pérez", "PERSONA")

    with pytest.raises(MaskingError, match="más valores"):
        serialize_messages(messages, table, [])
    with pytest.raises(MaskingError, match="más grupos"):
        serialize_messages(messages, table, [[], [], []])  # «TES» y el texto: dos valores


def test_serialize_rejects_a_span_whose_form_is_not_in_the_table() -> None:
    messages = [Message("user", "doña Ana Pérez dijo hola.")]

    with pytest.raises(MaskingError) as excinfo:
        serialize_messages(messages, MaskTable(), [[DetectedSpan(5, 14, "PERSONA", "x")]])

    assert "Ana" not in str(excinfo.value)


# --- Propiedad: ninguna forma detectada queda fuera de una marca ----------------------------------------

WORDS = st.sampled_from(
    [
        "Casilda", "Roncancio", "Aurelio", "Benavides", "Ana", "Pérez", "Pérez-Gómez", "Chigüiro",
        "Eufrasio", "Paz", "Luz", "El", "Entonces", "Fiscalía", "llegó", "vio", "a", "en", "la",
        "plaza", "dijo", "doña", "don", "sargento", "vereda", "Puerto", "San", "José", "radicado",
        "110016000-2019-00123", "1.234.567.890", "[PERSONA_1]", "persona_3", "Ana@correo.example",
        "ex-Benavides", "maría-Fernanda", "Benavides_2", "Benavides7", "a7Benavides", "x_Roncancio",
        "dijo\\nBenavides", "vio\\tAna", "\\u00c1lvaro", "\\u00e9xito-Tafurt", "iPhone",
    ]
)  # fmt: skip
JOINERS = st.sampled_from(
    [" ", " ", " ", ". ", ", ", "; ", "? ", "¿", "¡", ": ", " — ", " «", "» ", "\n"]
)


@st.composite
def synthetic_texts(draw: st.DrawFn) -> str:
    count = draw(st.integers(min_value=1, max_value=22))
    pieces: list[str] = []
    for _ in range(count):
        pieces.append(draw(WORDS))
        pieces.append(draw(JOINERS))
    return "".join(pieces)


def _bounded_occurrence(text: str, form: str) -> bool:
    start = text.find(form)
    while start != -1:
        end = start + len(form)
        left = (
            start == 0
            or not (form[0].isalnum() or form[0] == "_")
            or not (text[start - 1].isalnum() or text[start - 1] == "_")
        )
        right = (
            end == len(text)
            or not (form[-1].isalnum() or form[-1] == "_")
            or not (text[end].isalnum() or text[end] == "_")
        )
        if left and right:
            return True
        start = text.find(form, start + 1)
    return False


@settings(deadline=None, max_examples=80)
@given(st.lists(synthetic_texts(), min_size=1, max_size=4))
def test_property_no_detected_form_remains_outside_a_marker(texts: list[str]) -> None:
    masked, table = _mask(*texts)

    assert len(masked) == len(texts)
    for form in table.forms():
        for text in masked:
            # Las marcas de la llamada no cuentan: una forma puede tener el aspecto de una marca.
            visible = CANONICAL_MARKER.sub("", text)
            assert not _bounded_occurrence(visible, form), "una forma detectada quedó visible"
    for marker in (table.marker_for(f) for f in table.forms()):
        assert marker is not None
        assert any(marker in text for text in masked), "toda marca de la tabla sale en algún texto"
