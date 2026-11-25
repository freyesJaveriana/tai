"""Contrato de datos C13 del módulo: el `ModelCall` (BR2.5, BR2.6).

Depende de `veridicus-contracts` 0.1.1 (K-56, U10-T01): hasta que se fusione, la validación del
esquema `model-call.v1.yaml` rechaza sus marcas `x-veridicus-*`, y ese rechazo cuenta como rojo.
"""

from collections.abc import Callable
from importlib.resources import files
from typing import Any

import pytest
from veridicus_contracts.loaders import load_file
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCall,
    ModelCallError,
    ProviderError,
    Timeout,
)
from veridicus_contracts.validators import validate_instance

from tests.support import (
    call_to_instance,
    load_anthropic,
    make_destination,
    make_harness,
    make_request,
    ok_response,
)
from veridicus_anonymizer.testing.fake_transport import FakeResponse


def _schema() -> Any:
    return load_file(files("veridicus_contracts") / "model_calls" / "model-call.v1.yaml")


def test_the_model_call_of_a_call_that_left_validates_and_is_anonymized() -> None:
    result = make_harness(ok_response()).anonymizer.generate(make_request())

    call = result.call
    assert call.anonymized is True
    assert call.provider == "anthropic"
    assert call.model == "claude-sonnet-5-5"
    assert call.fallback_provider is False
    assert (call.input_tokens, call.output_tokens) == (412, 37)
    validate_instance(_schema(), call_to_instance(call))


def test_a_call_to_the_fallback_slot_is_recorded_as_fallback_provider() -> None:
    harness = make_harness(ok_response())
    result = harness.anonymizer.generate(make_request(slot="fallback"))

    assert result.call.fallback_provider is True
    assert result.call.anonymized is True
    validate_instance(_schema(), call_to_instance(result.call))


@pytest.mark.parametrize(
    ("expected", "script"),
    [
        (ProviderError, lambda: load_anthropic("error_503")),
        (ProviderError, lambda: load_anthropic("error_529")),
        (InvalidOutput, lambda: load_anthropic("max_tokens")),
        (ProviderError, lambda: load_anthropic("redirect_307")),
        (InvalidOutput, lambda: load_anthropic("not_json")),
        (InvalidOutput, lambda: load_anthropic("invalid_schema")),
        (ContentBlocked, lambda: load_anthropic("refusal")),
        (Timeout, FakeResponse.timeout),
    ],
    ids=["503", "529", "max_tokens", "redireccion", "no_json", "no_valida", "bloqueo", "timeout"],
)
def test_every_error_after_sending_carries_a_valid_model_call(
    expected: type[ModelCallError], script: Callable[[], FakeResponse]
) -> None:
    harness = make_harness(script())

    with pytest.raises(expected) as excinfo:
        harness.anonymizer.generate(make_request())

    assert harness.transport.request_count == 1
    call = getattr(excinfo.value, "call", None)
    assert isinstance(call, ModelCall), "los errores posteriores al envío llevan su ModelCall"
    assert call.anonymized is True
    validate_instance(_schema(), call_to_instance(call))


def test_anonymizer_unavailable_never_carries_a_model_call() -> None:
    harness = make_harness(ok_response(), env={})  # sin la clave referenciada

    with pytest.raises(AnonymizerUnavailable) as excinfo:
        harness.anonymizer.generate(make_request(destination=make_destination()))

    assert not hasattr(excinfo.value, "call")
    assert harness.transport.request_count == 0
