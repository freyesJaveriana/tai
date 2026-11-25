"""F-11: el mensaje `system` también sale seudonimizado (AUTONOMIA-04, BR1.2, F4 paso 4).

`system` no pasa por la red de seguridad (es configuración sin testimonio), pero un nombre completo
que las reglas detectan, o que se detectó en un turno, se propaga a `system` por forma exacta. Un
`_mask` que devolviera `system` sin tocar dejaría salir el nombre: estas pruebas lo impiden.
"""

import json
import re
from dataclasses import replace

import pytest
from veridicus_contracts.model_calls import Message

from tests.support import make_harness, make_request, ok_response, user_texts

NAME = "Casilda Roncancio"
MARKER = re.compile(r"\[(?:PERSONA|ENTIDAD)_[1-9][0-9]*\]")

CASES = {
    "nombre_en_system_y_en_un_turno": (
        f"Analiza el relato de {NAME} sin etiquetas.",
        f"ayer vi a {NAME} en la plaza.",
    ),
    "nombre_con_tratamiento_solo_en_system": (
        f"Analiza el relato de doña {NAME} sin etiquetas.",
        "ayer llegó tarde a la plaza.",
    ),
}


@pytest.mark.parametrize("case", list(CASES), ids=list(CASES))
def test_a_full_seeded_name_in_system_and_in_a_turn_never_leaves_and_system_carries_its_marker(
    case: str,
) -> None:
    system_text, turn_text = CASES[case]
    request = make_request([{"turno": 1, "hablante": "TES", "texto": turn_text}])
    request = replace(request, messages=[Message("system", system_text), *request.messages[1:]])
    harness = make_harness(ok_response())

    harness.anonymizer.generate(request)

    raw = harness.transport.requests[0].body.decode("utf-8")
    body = json.loads(raw)
    assert NAME not in raw and "Casilda" not in raw and "Roncancio" not in raw
    assert MARKER.search(body["system"]), "system debe llevar su marca"
    assert "Analiza el relato de" in body["system"], "el resto de system queda intacto"
    if case == "nombre_en_system_y_en_un_turno":
        assert MARKER.search(user_texts(harness.transport)[0]).group(0) in body["system"]  # type: ignore[union-attr]
