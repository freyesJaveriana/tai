"""Doble determinista del gateway (team.md, Dobles de prueba): sin red y sin azar."""

import pytest
from veridicus_contracts.model_calls import ProviderError

from tests.support import make_call, make_request
from veridicus_model_gateway.testing.fake import FakeModelGateway


def test_by_default_the_judge_finds_nothing_and_both_verifiers_confirm() -> None:
    fake = FakeModelGateway()

    judge = fake.generate(make_request("judge"))
    direct = fake.generate(make_request("verifier"))
    permuted = fake.generate(make_request("verifier_permuted"))

    assert judge.content == {"hallazgos": []}
    assert direct.content == {"confirma": True}
    assert permuted.content == {"confirma": True}
    assert [request.role for request in fake.requests] == ["judge", "verifier", "verifier_permuted"]


def test_the_scripted_findings_and_verdicts_are_returned() -> None:
    finding = {"hecho": "h"}
    fake = FakeModelGateway(findings=[finding], verdict_direct=False, verdict_permuted=False)

    assert fake.generate(make_request("judge")).content == {"hallazgos": [finding]}
    assert fake.generate(make_request("verifier")).content == {"confirma": False}
    assert fake.generate(make_request("verifier_permuted")).content == {"confirma": False}


def test_a_scripted_failure_is_raised_for_its_role_only() -> None:
    error = ProviderError("fallo", make_call("verifier"))
    fake = FakeModelGateway(failures={"verifier": error})

    assert fake.generate(make_request("judge")).content == {"hallazgos": []}
    with pytest.raises(ProviderError) as raised:
        fake.generate(make_request("verifier"))

    assert raised.value is error
    assert len(fake.requests) == 2, "la petición que falla también queda registrada"


def test_the_call_record_is_deterministic_and_marks_external_destinations_as_anonymized() -> None:
    fake = FakeModelGateway()

    external = fake.generate(make_request("judge", scope="external")).call
    again = FakeModelGateway().generate(make_request("judge", scope="external")).call
    local = fake.generate(make_request("judge", scope="local")).call

    assert external == again
    assert external.anonymized is True
    assert local.anonymized is False
    assert external.role == "judge"


def test_the_fake_can_report_an_unanonymized_external_call() -> None:
    fake = FakeModelGateway(anonymized=False)

    assert fake.generate(make_request("judge", scope="external")).call.anonymized is False
