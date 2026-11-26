"""Ronda 2: hosts numéricos que el sistema lee como IPv4 (F-01), familias (F-03), avisos de la
configuración (F-04) y forma de `prompt_sha256` (F-06). Todo sintético: las claves son canarios."""

from typing import Any
from unittest import mock

import pytest
from veridicus_contracts.canonical import sha256_jcs
from veridicus_errors import ConfigInvalidProfileError

from tests.test_validate import KEY_CANARY, NAME, TIMEOUT, document, env, external, local
from veridicus_execution_profiles import loader
from veridicus_execution_profiles.loader import PROMPT_SHA256_UNSET, load_config, load_profiles
from veridicus_execution_profiles.validate import _is_internal_host, validate_profile

DEMO = "demo-anthropic"
DEMO_ENV = {"VERIDICUS_ANTHROPIC_API_KEY": KEY_CANARY, TIMEOUT: "300"}


def _local_with(url: str) -> dict[str, Any]:
    return document(local("a", url), local("b", url))


@pytest.mark.parametrize(
    "host",
    [
        "134744072",  # 8.8.8.8 en decimal
        "0x8080808",  # 8.8.8.8 en hexadecimal
        "0",  # 0.0.0.0
        "010.8.8.8",  # octal: 8.8.8.8
    ],
)
def test_a_numeric_host_that_resolves_to_a_public_address_is_rejected(host: str) -> None:
    with pytest.raises(ConfigInvalidProfileError) as error:
        validate_profile(_local_with(f"http://{host}:8080"), NAME, {TIMEOUT: "300"})

    assert "base_url" in str(error.value)
    assert host not in str(error.value)


@pytest.mark.parametrize("host", ["2130706433", "0x7f000001", "127.1", "0xa000001", "167772161"])
def test_a_numeric_host_that_resolves_to_loopback_or_a_private_network_is_accepted(
    host: str,
) -> None:
    # 2130706433 y 0x7f000001 son 127.0.0.1; 127.1 es loopback; 0xa000001 y 167772161 son 10.0.0.1.
    assert validate_profile(_local_with(f"http://{host}:8080"), NAME, {TIMEOUT: "300"}) == ()


@pytest.mark.parametrize("host", ["1abc", "9service", "-servicio", "servicio-", "a" * 64])
def test_a_name_without_dots_must_be_a_dns_label_that_starts_with_a_letter(host: str) -> None:
    with pytest.raises(ConfigInvalidProfileError):
        validate_profile(_local_with(f"http://{host}:8080"), NAME, {TIMEOUT: "300"})


def test_a_dns_label_in_any_letter_case_is_a_cluster_service() -> None:
    assert validate_profile(_local_with("http://Servicio-Juez:8080"), NAME, {TIMEOUT: "300"}) == ()


def test_the_families_are_compared_without_regard_to_letter_case() -> None:
    same = document(external("Claude"), external("claude"))

    with pytest.raises(ConfigInvalidProfileError) as error:
        validate_profile(same, NAME, env())

    assert "family" in str(error.value)


def test_the_same_family_in_other_letter_case_is_a_warning_in_a_declared_demonstration() -> None:
    declared = document(
        external("Claude"), external("CLAUDE"), purpose="demonstration", same_family_declared=True
    )

    assert validate_profile(declared, NAME, env()) == ("same_family",)


def test_load_config_keeps_the_warnings_of_the_validation() -> None:
    config = load_config(DEMO, DEMO_ENV)

    assert config.warnings == ("same_family",)


_LAST_WARNINGS: dict[str, tuple[str, ...]] = {}


def _load_with_warnings(warnings: tuple[str, ...]) -> Any:
    """Carga el perfil demo con una validación que devuelve estos avisos (y los anota)."""

    def fake_validate(*_args: Any, **_kwargs: Any) -> tuple[str, ...]:
        _LAST_WARNINGS["warnings"] = warnings
        return warnings

    with mock.patch.object(loader, "validate_profile", fake_validate):
        return load_config(DEMO, DEMO_ENV)


def _assert_fingerprints_ignore_warnings() -> None:
    """Dos configuraciones del mismo perfil con avisos distintos tienen las mismas huellas, y la
    huella de todo el objeto es la del cuerpo C18 recalculado sin `warnings` (F-08)."""
    loud = _load_with_warnings(("same_family",))
    quiet = _load_with_warnings(())

    assert loud.warnings == ("same_family",)
    assert quiet.warnings == ()
    assert loud.config_sha256 == quiet.config_sha256
    assert loud.profile_sha256 == quiet.profile_sha256
    body = {
        "schema_version": loud.schema_version,
        "analyzer_version": loud.analyzer_version,
        "profile_name": loud.profile_name,
        "profile": load_profiles()["profiles"][DEMO],
        "profile_sha256": loud.profile_sha256,
        "prompt_sha256": loud.prompt_sha256,
        "limits": dict(loud.limits),
    }
    assert loud.config_sha256 == sha256_jcs(body)


def test_the_warnings_do_not_enter_the_fingerprints() -> None:
    _assert_fingerprints_ignore_warnings()


def test_a_mutant_that_hashes_the_warnings_is_detected_by_that_check() -> None:
    real = sha256_jcs

    def mutant(value: Any) -> str:
        """Como si `load_config` metiera `warnings` en el cuerpo que se hashea."""
        if isinstance(value, dict) and "profile_name" in value:
            return real({**value, "warnings": list(_LAST_WARNINGS.get("warnings", ()))})
        return real(value)

    with mock.patch.object(loader, "sha256_jcs", mutant), pytest.raises(AssertionError):
        _assert_fingerprints_ignore_warnings()


def test_a_prompt_reference_with_a_valid_form_is_accepted() -> None:
    assert load_config(DEMO, DEMO_ENV, prompt_sha256="0123456789abcdef" * 4)
    assert PROMPT_SHA256_UNSET == "0" * 64


@pytest.mark.parametrize(
    "value",
    ["", "abc", "AB" * 32, "g" * 64, "a" * 63, "a" * 65, "a" * 64 + "\n", " " + "a" * 63],
    ids=["vacio", "corto", "mayusculas", "no_hex", "63", "65", "salto_de_linea", "espacio"],
)
def test_a_prompt_reference_with_a_wrong_form_is_a_configuration_error(value: str) -> None:
    with pytest.raises(ConfigInvalidProfileError) as error:
        load_config(DEMO, DEMO_ENV, prompt_sha256=value)

    assert "prompt_sha256" in str(error.value)
    assert KEY_CANARY not in str(error.value)


def test_a_dns_label_is_ascii_only_even_for_letters_that_fold_to_ascii() -> None:
    # U+017F (s larga) y U+0131 (i sin punto) se pliegan a «s» e «i» con IGNORECASE sin ASCII.
    for host in (chr(0x17F) + "ervicio", "servicio".replace("i", chr(0x131))):
        assert not _is_internal_host(host)
    assert _is_internal_host("servicio")
