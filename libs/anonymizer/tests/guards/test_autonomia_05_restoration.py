"""AUTONOMIA-05, lado de U10: la cita seudonimizada se restaura antes de verificarse (E5, E25, E26).

Una sola entidad sembrada en el turno 4 fija la marca de la llamada: `[PERSONA_1]`. La respuesta
guionada del proveedor usa esa marca (o una alterada o inventada) y se comprueba lo que devuelve
el módulo: el texto restaurado byte a byte y los punteros RFC 6901 de las cadenas alteradas.
"""

import copy
from typing import Any

import pytest
from veridicus_contracts.model_calls import GenerateResult, Message

from tests.support import (
    load_anthropic,
    make_harness,
    make_request,
    ok_response,
)
from veridicus_anonymizer.domain.catalogs import load_catalogs
from veridicus_anonymizer.domain.masking import pseudonymize
from veridicus_anonymizer.domain.restoration import restore

ORIGINAL = "Casilda Roncancio dijo que salió temprano."
SECOND = "Después Casilda Roncancio se quedó en casa."
TURNOS = [
    {"turno": 4, "hablante": "TES", "texto": ORIGINAL},
    {"turno": 5, "hablante": "TES", "texto": SECOND},
]


def _finding(**overrides: Any) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "hecho": "[PERSONA_1] salió temprano",
        "tipo": "temporal",
        "cita_a": {"texto": "[PERSONA_1] dijo que salió temprano.", "turno": 4},
        "cita_b": {"texto": "Después [PERSONA_1] se quedó en casa.", "turno": 5},
        "observaciones": "Sin observaciones",
    }
    finding.update(overrides)
    return finding


def _generate(payload: Any) -> GenerateResult:
    harness = make_harness(ok_response(payload))
    return harness.anonymizer.generate(make_request(TURNOS))


def test_e5_a_pseudonymized_quote_is_restored_byte_for_byte_before_it_can_be_verified() -> None:
    result = _generate({"hallazgos": [_finding()]})

    cita_a = result.content["hallazgos"][0]["cita_a"]["texto"]
    cita_b = result.content["hallazgos"][0]["cita_b"]["texto"]
    assert cita_a == ORIGINAL
    assert cita_b == SECOND
    # La verificación de U11 compara contra el turno original sin casos especiales (FR4.4).
    assert cita_a in ORIGINAL
    assert cita_b in SECOND
    assert result.altered_markers == []
    assert "[PERSONA_" not in str(result.content)


@pytest.mark.parametrize(
    ("campo", "puntero"),
    [
        ("hecho", "/hallazgos/0/hecho"),
        ("cita_a", "/hallazgos/0/cita_a/texto"),
        ("cita_b", "/hallazgos/0/cita_b/texto"),
        ("observaciones", "/hallazgos/0/observaciones"),
    ],
)
def test_e25_an_altered_or_invented_marker_stays_and_its_pointer_is_reported(
    campo: str, puntero: str
) -> None:
    finding = _finding()
    altered = "[Persona_1] y [PERSONA_9] aparecen aquí"
    if campo in {"cita_a", "cita_b"}:
        finding[campo]["texto"] = altered
    else:
        finding[campo] = altered

    result = _generate({"hallazgos": [finding]})

    assert result.altered_markers == [puntero]
    restored = result.content["hallazgos"][0]
    value = restored[campo]["texto"] if campo in {"cita_a", "cita_b"} else restored[campo]
    assert value == altered, "la cadena alterada se deja sin restaurar"


def test_e26_known_markers_of_the_same_string_are_restored_and_each_pointer_is_listed_once() -> (
    None
):
    finding = _finding(
        hecho="[Persona_1] salió temprano",
        observaciones="[PERSONA 1] y [PERSONA_1] aparecen",
    )
    finding["cita_a"]["texto"] = "[PERSONA_1] vio a [PERSONA_9] y a [PERSONA_8]"

    result = _generate({"hallazgos": [finding]})

    restored = result.content["hallazgos"][0]
    assert restored["cita_a"]["texto"] == "Casilda Roncancio vio a [PERSONA_9] y a [PERSONA_8]"
    assert restored["observaciones"] == "[PERSONA 1] y Casilda Roncancio aparecen"
    assert restored["hecho"] == "[Persona_1] salió temprano"
    assert restored["cita_b"]["texto"] == SECOND
    # Sin repetidos y en orden de recorrido del documento.
    assert result.altered_markers == [
        "/hallazgos/0/hecho",
        "/hallazgos/0/cita_a/texto",
        "/hallazgos/0/observaciones",
    ]


def test_a_recorded_response_with_altered_and_invented_markers_reports_the_expected_pointers() -> (
    None
):
    harness = make_harness(load_anthropic("altered_markers"))
    result = harness.anonymizer.generate(make_request(TURNOS))

    assert result.altered_markers == [
        "/hallazgos/0/hecho",
        "/hallazgos/0/cita_a/texto",
        "/hallazgos/0/observaciones",
    ]
    assert result.content["hallazgos"][0]["cita_b"]["texto"] == "Casilda Roncancio se quedó"


def test_a_valid_empty_response_is_returned_unchanged() -> None:
    result = _generate({"hallazgos": []})

    assert result.content == {"hallazgos": []}
    assert result.altered_markers == []


def test_person_3_without_brackets_is_not_a_marker_and_invalidates_nothing() -> None:
    finding = _finding(observaciones="la persona 3 declaró después")

    result = _generate({"hallazgos": [finding]})

    assert result.altered_markers == []
    assert result.content["hallazgos"][0]["observaciones"] == "la persona 3 declaró después"


def test_restore_works_on_the_table_that_pseudonymize_returned_and_never_touches_keys() -> None:
    messages = [Message("user", ORIGINAL)]
    masked, table = pseudonymize(messages, load_catalogs())
    marker = masked[0].content.split(" dijo")[0]
    content = {marker: marker, "lista": [marker, 3]}

    outcome = restore(copy.deepcopy(content), table)

    assert outcome.content == {marker: "Casilda Roncancio", "lista": ["Casilda Roncancio", 3]}
    assert outcome.altered_markers == []
