"""El prompt y su referencia (BR3.1, PD-13, K-88, F-03 de U11-T03): fallar cerrado antes de llamar.

`analyze` compara tres huellas: la de la configuración, la de los bytes del *prompt* leídos ahora y
la referencia versionada. Si alguna difiere, la corrida termina en `salida_invalida` sin llamar.
"""

import pytest
from veridicus_execution_profiles.loader import PROMPT_SHA256_UNSET, load_config

from tests.support import (
    PROFILE,
    ScriptedGateway,
    assert_error_output,
    env,
    finding,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.application import messages

OTHER = "ab" * 32


def test_the_default_of_load_config_is_all_zeros_and_fails_closed_without_calling() -> None:
    config = load_config(PROFILE, env())
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert config.prompt_sha256 == PROMPT_SHA256_UNSET == "0" * 64
    assert_error_output(salida, "salida_invalida")
    assert gateway.requests == [], "ninguna llamada"
    assert salida["registro"]["llamadas"] == []
    assert salida["prompt_sha256"] == "0" * 64


def test_a_changed_byte_of_the_prompt_in_memory_fails_closed_without_calling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config()
    original = messages.prompt_bytes()
    changed = original[:-1] + bytes([original[-1] ^ 0x01])
    assert changed != original
    monkeypatch.setattr(messages, "prompt_bytes", lambda: changed)
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.requests == []


def test_a_reference_file_that_does_not_match_the_prompt_fails_closed_without_calling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config()
    monkeypatch.setattr(messages, "load_prompt_reference", lambda: OTHER)
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.requests == []


def test_a_configuration_with_another_valid_hash_fails_closed_without_calling() -> None:
    config = load_config(PROFILE, env(), prompt_sha256=OTHER)
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert_error_output(salida, "salida_invalida")
    assert gateway.requests == []


def test_control_the_three_hashes_in_agreement_do_call() -> None:
    config = make_config()
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert config.prompt_sha256 == messages.prompt_sha256() == messages.load_prompt_reference()
    assert salida["estado"] == "ok"
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
