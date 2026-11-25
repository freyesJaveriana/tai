"""Invariantes de `generate` como propiedad (AUTONOMIA-04/05, F1, F6), con el `FakeTransport`.

Mensajes de todos los roles, con contenido JSON y no JSON, y las formas de los casos sonda de U10-T03
(guion, guion bajo, dígito, escapes y las aperturas de PD-2). Se comprueba que:

- el cuerpo saliente no contiene ninguna forma que la tabla de la llamada haya registrado;
- la respuesta guionada (el eco del texto ya seudonimizado) se restaura byte a byte.
"""

import json
from typing import Any
from unittest import mock

from hypothesis import given, settings
from hypothesis import strategies as st
from veridicus_contracts.model_calls import GenerateRequest, Message

from tests.domain.test_masking import CANONICAL_MARKER, _bounded_occurrence, synthetic_texts
from tests.support import (
    anthropic_envelope,
    assert_no_entity_in_payload,
    load_seeded,
    make_harness,
    make_request,
    outgoing_views,
    user_texts,
)
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain.masking import MaskTable
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

ECHO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["eco"],
    "properties": {"eco": {"type": "array", "items": {"type": "string"}}},
}
SEEDED = load_seeded()
PLAIN = st.sampled_from(["responde solo con el json", "ok", "", "dijo Ana Pérez en la plaza"])


def _request(texts: list[str], system: str, extra_user: str, assistant: str) -> GenerateRequest:
    turns = [{"turno": i, "hablante": "TES", "texto": t} for i, t in enumerate(texts)]
    base = make_request(turns)
    messages = [
        Message("system", system),
        Message("user", json.dumps({"turnos": turns}, ensure_ascii=False)),
        Message("assistant", assistant),
        Message("user", extra_user),
    ]
    return GenerateRequest(
        role=base.role,
        destination_slot=base.destination_slot,
        profile_name=base.profile_name,
        profile_sha256=base.profile_sha256,
        destination=base.destination,
        messages=messages,
        schema=ECHO_SCHEMA,
        timeout_s=base.timeout_s,
    )


def _echo(texts: list[str]) -> FakeResponse:
    return FakeResponse.ok_json(anthropic_envelope({"eco": texts}))


@settings(deadline=None, max_examples=40)
@given(
    texts=st.lists(synthetic_texts(), min_size=1, max_size=3),
    system=PLAIN,
    extra_user=st.one_of(PLAIN, synthetic_texts()),
    assistant=st.one_of(PLAIN, synthetic_texts()),
)
def test_property_nothing_detected_leaves_and_the_masked_echo_is_restored_byte_for_byte(
    texts: list[str], system: str, extra_user: str, assistant: str
) -> None:
    texts = [*texts, *(t["texto"] for t in SEEDED["turnos"])]  # con las entidades sembradas
    request = _request(texts, system, extra_user, assistant)
    forms: list[str] = []
    real = generate_module.pseudonymize

    def spy(*args: Any, **kwargs: Any) -> tuple[list[Message], MaskTable]:
        masked, table = real(*args, **kwargs)
        forms.extend(table.forms())
        return masked, table

    # Primera pasada: se captura el cuerpo saliente y las formas que registró la tabla.
    with mock.patch.object(generate_module, "pseudonymize", spy):
        first = make_harness(_echo([]))
        first.anonymizer.generate(request)
    assert_no_entity_in_payload(first.transport, SEEDED["entidades"])
    for view in outgoing_views(first.transport):
        visible = CANONICAL_MARKER.sub("", view)
        for form in forms:
            assert not _bounded_occurrence(visible, form), "una forma detectada salió"

    # Segunda pasada: la misma entrada da la misma tabla; el proveedor devuelve el texto guionado.
    echoed = user_texts_of_json_message(first.transport)
    second = make_harness(_echo(echoed))
    result = second.anonymizer.generate(request)

    assert result.content == {"eco": texts}
    assert result.altered_markers == []


def user_texts_of_json_message(transport: FakeTransport) -> list[str]:
    """Los textos de turno, ya seudonimizados, del mensaje `user` que lleva el JSON de turnos."""
    return user_texts(transport)
