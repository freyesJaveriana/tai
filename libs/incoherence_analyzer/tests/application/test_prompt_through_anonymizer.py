"""El texto del *prompt* pasa por el `Anonymizer` real sin ninguna marca (R-14, PD-6).

Así el `system` que sale hacia el proveedor es, byte a byte, el del archivo. Es el lado del
anonimizador de K-84: si el *prompt* tuviera algo que el anonimizador toma por una entidad, saldría
cambiado y la huella `prompt_sha256` dejaría de describir lo que se envió.
"""

import json
import re

import pytest
from veridicus_anonymizer.api import build_anonymizer
from veridicus_contracts.model_calls import Destination, GenerateRequest

from tests.support import (
    KEY_REF,
    MODEL,
    ScriptedProvider,
    default_turns,
    env,
    finding,
    make_config,
)
from veridicus_incoherence_analyzer.application.messages import (
    build_messages,
    judge_payload,
    load_response_schema,
    load_system_prompt,
    verifier_payload,
)

MARK = re.compile(r"\[[A-Z]+_[0-9]+\]")


def _request(role: str, messages_role: str, payload: dict[str, object]) -> GenerateRequest:
    config = make_config()
    return GenerateRequest(
        role=role,
        destination_slot="primary",
        profile_name=config.profile_name,
        profile_sha256=config.profile_sha256,
        destination=Destination(
            provider="anthropic",
            model=MODEL,
            scope="external",
            family="claude",
            api_key_ref=KEY_REF,
        ),
        messages=build_messages(messages_role, payload),  # type: ignore[arg-type]  # motivo: Literal
        schema=load_response_schema(messages_role, "wire"),  # type: ignore[arg-type]  # motivo: Literal
        timeout_s=300.0,
    )


@pytest.mark.parametrize("role", ["judge", "verifier"])
def test_the_prompt_leaves_through_the_real_anonymizer_byte_for_byte_and_without_marks(
    role: str,
) -> None:
    provider = ScriptedProvider(lambda turns: [])
    anonymizer = build_anonymizer(env(), provider)
    payload = (
        judge_payload(default_turns())
        if role == "judge"
        else verifier_payload(finding(), permuted=False)
    )

    anonymizer.generate(_request(role, role, payload))

    assert provider.request_count == 1
    body = json.loads(provider.bodies[0])
    assert body["system"] == load_system_prompt(role)  # type: ignore[arg-type]  # motivo: parametrizado
    assert MARK.search(body["system"]) is None


def test_the_testimony_in_the_user_message_is_masked_but_the_system_is_not() -> None:
    provider = ScriptedProvider(lambda turns: [])
    anonymizer = build_anonymizer(env(), provider)

    anonymizer.generate(_request("judge", "judge", judge_payload(default_turns())))

    body = json.loads(provider.bodies[0])
    assert "Casilda Roncancio" not in body["messages"][0]["content"]
    assert body["system"] == load_system_prompt("judge")
