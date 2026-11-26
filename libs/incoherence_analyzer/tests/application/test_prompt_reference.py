"""El prompt y su referencia (BR3.1, PD-13, K-88, F-03 de U11-T03): fallar cerrado antes de llamar.

`analyze` compara tres huellas: la de la configuración, la de los bytes del *prompt* leídos ahora y
la referencia versionada. Si alguna difiere, la corrida termina en `salida_invalida` sin llamar.
"""

import hashlib

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
    # A-01: la salida informa la huella de los bytes leídos (BR3.1), no la de la configuración.
    assert salida["prompt_sha256"] == messages.prompt_sha256() != "0" * 64


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


def test_the_changed_prompt_is_reported_with_the_hash_of_the_bytes_that_were_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = make_config()
    changed = messages.prompt_bytes() + b" "
    monkeypatch.setattr(messages, "prompt_bytes", lambda: changed)

    salida = analyze(make_entrada(), config, ScriptedGateway(findings=[finding()]))

    assert_error_output(salida, "salida_invalida")
    assert salida["prompt_sha256"] == hashlib.sha256(changed).hexdigest()
    assert salida["prompt_sha256"] != config.prompt_sha256


def test_the_prompt_is_read_once_and_the_system_sent_is_that_of_the_hashed_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # F-01: un archivo que cambia después de la primera lectura no puede llegar al proveedor.
    config = make_config()
    original = messages.prompt_bytes()
    expected = {role: messages.load_system_prompt(role) for role in ("judge", "verifier")}
    reads: list[int] = []

    def changing() -> bytes:
        reads.append(1)
        return original if len(reads) == 1 else original.replace(b"Eres", b"INYECTADO")

    monkeypatch.setattr(messages, "prompt_bytes", changing)
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), config, gateway)

    assert len(reads) == 1, "una sola lectura por corrida"
    assert salida["estado"] == "ok"
    assert salida["prompt_sha256"] == hashlib.sha256(original).hexdigest()
    assert gateway.roles() == ["judge", "verifier", "verifier_permuted"]
    for request in gateway.requests:
        system = request.messages[0].content
        assert "INYECTADO" not in system
        assert system == expected["judge" if request.role == "judge" else "verifier"]
