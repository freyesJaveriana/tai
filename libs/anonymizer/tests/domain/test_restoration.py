"""Paso 8: restauración y marcas alteradas (F6, BR1.3, BR4.1, BR4.2; E5, E25, E26).

Se suman a las de `tests/guards/test_autonomia_05_restoration.py`, que pasan por `Anonymizer.generate`
(U10-T04): aquí se prueba `restore` directamente, con la tabla que devuelve `pseudonymize`.
"""

import copy
import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from veridicus_contracts.model_calls import Message

from tests.domain.test_masking import synthetic_texts
from veridicus_anonymizer.domain.catalogs import load_catalogs
from veridicus_anonymizer.domain.masking import MaskTable, pseudonymize
from veridicus_anonymizer.domain.restoration import RestorationOutcome, restore

CATALOGS = load_catalogs()


def _table() -> MaskTable:
    """Una tabla con una persona y un lugar, con tildes y mayúsculas."""
    table = MaskTable()
    table.add("Ana Pérez", "PERSONA")
    table.add("La Esperanza", "LUGAR")
    return table


def test_e5_a_canonical_marker_of_the_table_returns_to_its_exact_original_form() -> None:
    content = {"hecho": "[PERSONA_1] vivía en [LUGAR_1]", "cita": {"texto": "doña [PERSONA_1]"}}

    outcome = restore(content, _table())

    assert outcome == RestorationOutcome(
        {"hecho": "Ana Pérez vivía en La Esperanza", "cita": {"texto": "doña Ana Pérez"}}, []
    )


def test_a_valid_empty_response_comes_back_unchanged() -> None:
    outcome = restore({"hallazgos": []}, _table())

    assert outcome.content == {"hallazgos": []}
    assert outcome.altered_markers == []


def test_person_3_without_brackets_is_not_a_marker() -> None:
    outcome = restore({"observaciones": "la persona 3 y el lugar 2 declararon"}, _table())

    assert outcome.altered_markers == []
    assert outcome.content == {"observaciones": "la persona 3 y el lugar 2 declararon"}


@pytest.mark.parametrize(
    "form",
    [
        "[Persona_1]",
        "[persona_1]",
        "[PERSONA 1]",
        "[PERSONA-1]",
        "[ PERSONA_1 ]",
        "PERSONA_1]",
        "persona_1",
        "[PERSONA_9]",
        "[PERSONA_01]",
        "[NOMBRE_1]",
        "[LUGAR_2]",
    ],
)
def test_e25_a_form_that_is_not_exactly_a_marker_of_the_table_stays_and_is_listed(
    form: str,
) -> None:
    outcome = restore({"observaciones": f"vio a {form} ayer"}, _table())

    assert outcome.content == {"observaciones": f"vio a {form} ayer"}
    assert outcome.altered_markers == ["/observaciones"]


def test_e26_known_markers_are_restored_unknown_ones_stay_and_the_pointer_is_listed_once() -> None:
    content = {"a": "[PERSONA_1] y [PERSONA_9] y [Persona_1] y [LUGAR_1]", "b": "[LUGAR_1]"}

    outcome = restore(content, _table())

    assert outcome.content == {
        "a": "Ana Pérez y [PERSONA_9] y [Persona_1] y La Esperanza",
        "b": "La Esperanza",
    }
    assert outcome.altered_markers == ["/a"]


def test_pointers_follow_rfc_6901_through_lists_keys_and_the_root() -> None:
    table = _table()
    bad = "[PERSONA_9]"
    content = {
        "a/b": [{"x~y": bad}, "ok", bad],
        "": {"n": 3, "z": [[bad]]},
        "limpia": "[PERSONA_1]",
    }

    outcome = restore(content, table)

    assert outcome.altered_markers == ["/a~1b/0/x~0y", "/a~1b/2", "//z/0/0"]
    assert restore(bad, table).altered_markers == [""]
    assert restore("[PERSONA_1]", table) == RestorationOutcome("Ana Pérez", [])


def test_keys_numbers_and_other_values_are_never_touched() -> None:
    content = {"[PERSONA_1]": "[PERSONA_1]", "n": 7, "f": 1.5, "t": True, "z": None, "l": [1, None]}

    outcome = restore(content, _table())

    assert outcome.content == {
        "[PERSONA_1]": "Ana Pérez",
        "n": 7,
        "f": 1.5,
        "t": True,
        "z": None,
        "l": [1, None],
    }
    assert outcome.altered_markers == []


def test_restoring_does_not_mutate_its_input() -> None:
    content: dict[str, Any] = {"a": ["[PERSONA_1]", {"b": "[PERSONA_9]"}]}
    before = copy.deepcopy(content)

    restore(content, _table())

    assert content == before


def test_a_literal_marker_in_the_original_text_is_not_scanned_again() -> None:
    # BR1.7: el testimonio trae «[PERSONA_1]»; su marca propia lo devuelve intacto y sin alerta.
    table = MaskTable()
    table.add("Ana Pérez", "PERSONA")
    entity_marker = table.add("[PERSONA_1]", "ENTIDAD")

    outcome = restore({"texto": f"vio {entity_marker} y a [PERSONA_1]"}, table)

    assert outcome.content == {"texto": "vio [PERSONA_1] y a Ana Pérez"}
    assert outcome.altered_markers == []


def test_restore_returns_the_original_text_of_what_pseudonymize_masked() -> None:
    original = {
        "turnos": [{"turno": 4, "texto": "doña Ana Pérez dijo que [PERSONA_1] vive en San José"}]
    }
    masked, table = pseudonymize(
        [Message("user", json.dumps(original, ensure_ascii=False))], CATALOGS
    )

    outcome = restore(json.loads(masked[0].content), table)

    assert "[PERSONA_1]" in masked[0].content
    assert outcome.content == original
    assert outcome.altered_markers == []


@settings(deadline=None, max_examples=80)
@given(st.lists(synthetic_texts(), min_size=1, max_size=4))
def test_property_restoring_what_was_pseudonymized_returns_the_original_byte_for_byte(
    texts: list[str],
) -> None:
    original = {
        "turnos": [{"turno": i, "hablante": "TES", "texto": t} for i, t in enumerate(texts)]
    }
    masked, table = pseudonymize(
        [Message("user", json.dumps(original, ensure_ascii=False))], CATALOGS
    )

    outcome = restore(json.loads(masked[0].content), table)

    assert outcome.content == original
    assert outcome.altered_markers == []
