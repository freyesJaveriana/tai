"""Reglas de BR2 y piso de NFRD-U11-03 de `validate_profile` (BR2.1 a BR2.3, BR2.5, BR2.11).

Todo es sintético: las claves son canarios inventados y nunca una clave real.
"""

import copy
from typing import Any

import pytest
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError

from veridicus_execution_profiles import floors
from veridicus_execution_profiles.validate import _base_url_problem, validate_profile

NAME = "perfil-prueba"
KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
TIMEOUT = "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S"


def external(family: str = "claude") -> dict[str, Any]:
    return {
        "provider": "anthropic",
        "model": "claude-sonnet-5-5",
        "scope": "external",
        "family": family,
        "api_key_ref": KEY_REF,
    }


def local(
    family: str = "otra", base_url: str = "http://veridicus-llm-judge:8080"
) -> dict[str, Any]:
    return {
        "provider": "local",
        "model": "modelo-sintetico",
        "scope": "local",
        "family": family,
        "base_url": base_url,
    }


def document(
    judge: dict[str, Any] | None = None,
    verifier: dict[str, Any] | None = None,
    *,
    purpose: str = "evaluation",
    **extra: Any,
) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "purpose": purpose,
        "roles": {"judge": judge or external("claude"), "verifier": verifier or external("otra")},
        "role_aliases": {"verifier_permuted": "verifier"},
        "permutation": True,
        **extra,
    }
    return {"schema_version": "1.0.0", "profiles": {NAME: profile}}


def env(**overrides: str) -> dict[str, str]:
    return {KEY_REF: KEY_CANARY, TIMEOUT: "300", **overrides}


def rejected(doc: dict[str, Any], environment: dict[str, str] | None = None) -> str:
    with pytest.raises(ConfigInvalidProfileError) as error:
        validate_profile(doc, NAME, env() if environment is None else environment)
    assert KEY_CANARY not in str(error.value)
    return str(error.value)


def test_the_floor_is_270_seconds() -> None:
    assert floors.COMMERCIAL_MIN_CALL_TIMEOUT_S == 270


def test_with_an_external_role_269_seconds_fail_and_270_start() -> None:
    message = rejected(document(), env(**{TIMEOUT: "269"}))

    assert "model_call_timeout_s" in message
    assert "270" in message
    assert validate_profile(document(), NAME, env(**{TIMEOUT: "270"})) == ()


def test_without_an_external_role_the_floor_does_not_apply() -> None:
    both_local = document(local("a"), local("b"))

    assert validate_profile(both_local, NAME, {TIMEOUT: "10"}) == ()


def test_an_invalid_limit_in_the_environment_is_a_limit_error_not_a_profile_error() -> None:
    with pytest.raises(ConfigInvalidLimitError):
        validate_profile(document(), NAME, env(**{TIMEOUT: "no-es-un-numero"}))


def test_a_missing_key_variable_is_named_in_the_message() -> None:
    message = rejected(document(), {TIMEOUT: "300"})

    assert KEY_REF in message


def test_an_empty_key_variable_counts_as_missing() -> None:
    message = rejected(document(), env(**{KEY_REF: "   "}))

    assert KEY_REF in message


def test_an_external_role_without_api_key_ref_is_rejected() -> None:
    nameless = external()
    del nameless["api_key_ref"]

    assert "api_key_ref" in rejected(document(nameless))


def test_a_local_role_does_not_need_a_key() -> None:
    assert validate_profile(document(local("a"), local("b")), NAME, {TIMEOUT: "300"}) == ()


def test_a_base_url_in_an_external_destination_is_rejected_even_if_private() -> None:
    private = {**external(), "base_url": "http://10.0.0.5:8080"}

    assert "base_url" in rejected(document(private))


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://[::1]:8080",
        "http://10.1.2.3:8080",
        "http://172.16.0.9:8080",
        "http://192.168.1.4:8080",
        "http://[fc00::1]:8080",
        "http://veridicus-llm-judge:8080",
        "http://veridicus-llm.veridicus.svc:8080",
        "http://veridicus-llm.veridicus.svc.cluster.local:8080",
    ],
)
def test_an_internal_base_url_is_accepted_in_a_local_destination(url: str) -> None:
    assert validate_profile(document(local("a", url), local("b", url)), NAME, env()) == ()


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com:8080",
        "http://8.8.8.8:8080",
        "http://172.32.0.1:8080",
        "http://[2001:db8::1]:8080",
        "http://modelos.ejemplo.org",
        "http://:8080",
        "http://[::1",
    ],
)
def test_a_public_or_unparsable_base_url_is_rejected_in_a_local_destination(url: str) -> None:
    message = rejected(document(local("a", url), local("b")), {TIMEOUT: "300"})

    assert "base_url" in message
    assert "example" not in message
    assert "8.8.8.8" not in message


def test_an_unparsable_base_url_is_rejected_even_if_the_schema_did_not_catch_it() -> None:
    # El esquema ya rechaza «http://[::1» por su formato; esta defensa vale si ese formato no se
    # comprobara, y se prueba directamente porque por validate_profile nunca llega.
    destination = {"provider": "local", "model": "m", "scope": "local", "base_url": "http://[::1"}

    problems = _base_url_problem(NAME, "judge", destination)

    assert problems == [
        f"perfil {NAME}, papel judge, ajuste base_url: un destino local solo admite un destino interno"
    ]


def test_the_same_family_in_an_evaluation_profile_is_rejected() -> None:
    assert "family" in rejected(document(external("claude"), external("claude")))


def test_the_same_family_in_a_demonstration_without_the_declaration_is_rejected() -> None:
    same = document(external("claude"), external("claude"), purpose="demonstration")

    assert "same_family_declared" in rejected(same)


def test_the_same_family_declared_in_a_demonstration_is_accepted_with_its_warning() -> None:
    declared = document(
        external("claude"), external("claude"), purpose="demonstration", same_family_declared=True
    )

    assert validate_profile(declared, NAME, env()) == ("same_family",)


def test_the_declaration_in_an_evaluation_profile_is_rejected_even_without_a_shared_family() -> (
    None
):
    declared = document(same_family_declared=True)

    assert "same_family_declared" in rejected(declared)


def test_a_demonstration_with_distinct_families_has_no_warning_even_if_declared() -> None:
    declared = document(purpose="demonstration", same_family_declared=True)

    assert validate_profile(declared, NAME, env()) == ()


def test_the_fallback_provider_counts_for_the_family_rule() -> None:
    with_fallback = document(fallback_provider=external("claude"))

    assert "family" in rejected(with_fallback)


def test_the_fallback_provider_gets_the_same_checks_as_a_role() -> None:
    public = {**local("tercera", "http://example.com"), "scope": "local"}

    assert "fallback_provider" in rejected(document(fallback_provider=public))


def test_an_unknown_profile_name_is_rejected_without_echoing_a_hostile_name() -> None:
    with pytest.raises(ConfigInvalidProfileError) as error:
        validate_profile(document(), "mal nombre\n{x}", env())

    assert "?" in str(error.value)
    assert "{x}" not in str(error.value)


def test_a_profile_that_the_schema_rejects_raises_the_profile_error() -> None:
    with pytest.raises(ConfigInvalidProfileError) as error:
        validate_profile(document(temperatura_global=0.2), NAME, env())

    assert "temperatura_global" in str(error.value)


def test_an_api_key_ref_without_the_prefix_is_rejected_by_the_contract_check() -> None:
    other = {**external(), "api_key_ref": "OTRA_VARIABLE_CLAVE"}

    with pytest.raises(ConfigInvalidProfileError):
        validate_profile(document(other), NAME, env(OTRA_VARIABLE_CLAVE="x"))


def test_validating_does_not_change_the_document_or_the_environment() -> None:
    doc = document()
    snapshot = copy.deepcopy(doc)
    environment = env()
    before = dict(environment)

    validate_profile(doc, NAME, environment)

    assert doc == snapshot
    assert environment == before
