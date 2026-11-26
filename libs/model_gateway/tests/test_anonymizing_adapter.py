"""Adaptador `anonymizing` (BR10.1, BR10.3, BR7.4): una llamada, sin reintento y sin testimonio en el error."""

import contextlib

import pytest
from hypothesis import given
from hypothesis import strategies as st
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCallError,
    ProviderError,
    Timeout,
)

from tests.support import (
    TESTIMONY,
    SpyProvider,
    StepClock,
    make_call,
    make_config,
    make_request,
    make_result,
)
from veridicus_model_gateway.adapters.anonymizing import AnonymizingAdapter
from veridicus_model_gateway.gateway import RecordingGateway, build


def test_a_foreign_exception_becomes_anonymizer_unavailable_without_the_testimony() -> None:
    provider = SpyProvider(outcome=RuntimeError(TESTIMONY))
    adapter = AnonymizingAdapter(provider)

    with pytest.raises(AnonymizerUnavailable) as raised:
        adapter.generate(make_request())

    message = str(raised.value)
    assert TESTIMONY not in message
    assert "Casilda" not in message
    assert "RuntimeError" in message, "la causa viaja como tipo, nunca como texto"
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None


@pytest.mark.parametrize(
    "error",
    [
        ContentBlocked("bloqueado", make_call()),
        Timeout("plazo", make_call()),
        ProviderError("fallo", make_call()),
        InvalidOutput("salida", make_call()),
        AnonymizerUnavailable("no disponible"),
    ],
    ids=["blocked", "timeout", "provider", "invalid", "unavailable"],
)
def test_a_model_calls_error_passes_through_unchanged(error: ModelCallError) -> None:
    provider = SpyProvider(outcome=error)
    adapter = AnonymizingAdapter(provider)

    with pytest.raises(ModelCallError) as raised:
        adapter.generate(make_request())

    assert raised.value is error


def test_a_successful_result_is_returned_as_is() -> None:
    result = make_result()
    adapter = AnonymizingAdapter(SpyProvider(outcome=result))

    assert adapter.generate(make_request()) is result


@pytest.mark.parametrize(
    "outcome",
    [
        make_result(),
        RuntimeError(TESTIMONY),
        ProviderError("fallo", make_call()),
        AnonymizerUnavailable("no disponible"),
    ],
    ids=["ok", "foreign", "typed_with_call", "unavailable"],
)
def test_the_provider_is_called_exactly_once_and_never_retried(
    outcome: object,
) -> None:
    provider = SpyProvider(outcome=outcome)  # type: ignore[arg-type]  # motivo: parametrizado
    adapter = AnonymizingAdapter(provider)

    with contextlib.suppress(Exception):  # aquí solo importa cuántas veces se llamó
        adapter.generate(make_request())

    assert len(provider.requests) == 1


@given(text=st.text(min_size=1, max_size=200))
def test_property_no_text_of_a_foreign_exception_reaches_the_error(text: str) -> None:
    sentinel = "«" + text + "»"
    adapter = AnonymizingAdapter(SpyProvider(outcome=ValueError(sentinel)))

    with pytest.raises(AnonymizerUnavailable) as raised:
        adapter.generate(make_request())

    assert sentinel not in str(raised.value)


def test_the_gateway_records_each_call_in_order_with_its_latency() -> None:
    provider = SpyProvider()
    gateway = RecordingGateway(AnonymizingAdapter(provider), clock=StepClock())

    gateway.generate(make_request("judge"))
    provider.outcome = make_result("verifier")
    gateway.generate(make_request("verifier"))

    assert [call.role for call in gateway.calls] == ["judge", "verifier"]
    assert [round(record.latency_s, 1) for record in gateway.records] == [0.1, 0.1]


def test_a_typed_error_that_carries_a_call_is_recorded_and_one_without_it_is_not() -> None:
    provider = SpyProvider(outcome=ProviderError("fallo", make_call("verifier")))
    gateway = build(make_config(), anonymizing_provider=provider)

    with pytest.raises(ProviderError):
        gateway.generate(make_request("verifier"))
    provider.outcome = AnonymizerUnavailable("no disponible")
    with pytest.raises(AnonymizerUnavailable):
        gateway.generate(make_request("verifier"))

    assert [call.role for call in gateway.calls] == ["verifier"]


def test_a_foreign_exception_adds_no_call_to_the_record() -> None:
    gateway = build(make_config(), anonymizing_provider=SpyProvider(outcome=RuntimeError("x")))

    with pytest.raises(AnonymizerUnavailable):
        gateway.generate(make_request())

    assert gateway.calls == ()
