"""Contrato de los perfiles de ejecución (C18; BR2.5, BR2.10, R-01, R-07).

Las pruebas pasan siempre por `load_profiles`, `load_config` y `validate_profile`, nunca leen
`config/profiles.yaml` directamente. Todo es sintético: la clave es un canario inventado.
"""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from veridicus_contracts import profiles
from veridicus_contracts.canonical import sha256_jcs
from veridicus_errors import ConfigInvalidProfileError

from veridicus_execution_profiles.loader import load_config, load_profiles
from veridicus_execution_profiles.validate import validate_profile

NAME = "demo-anthropic"
KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
OPENAI_KEY_REF = "VERIDICUS_OPENAI_API_KEY"
# Canario inventado: nunca es una clave real.
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
LIMIT = {"VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300"}


def env(key: str = KEY_CANARY) -> dict[str, str]:
    return {KEY_REF: key, OPENAI_KEY_REF: key, **LIMIT}


def destination(
    *, provider: str = "anthropic", model: str = "claude-sonnet-5-5", family: str = "claude"
) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "scope": "external",
        "family": family,
        "api_key_ref": KEY_REF if provider == "anthropic" else OPENAI_KEY_REF,
    }


def document(
    *,
    purpose: str = "demonstration",
    verifier: dict[str, Any] | None = None,
    same_family_declared: bool | None = True,
    permutation: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    """Un archivo de perfiles con un solo perfil, con la forma de `profiles.schema.v1`."""
    profile: dict[str, Any] = {
        "purpose": purpose,
        "roles": {"judge": destination(), "verifier": verifier or destination()},
        "role_aliases": {"verifier_permuted": "verifier"},
        "permutation": permutation,
        **extra,
    }
    if same_family_declared is not None:
        profile["same_family_declared"] = same_family_declared
    return {"schema_version": "1.0.0", "profiles": {NAME: profile}}


def test_the_single_profile_of_the_versioned_file_is_valid_for_u1_and_is_the_demo() -> None:
    loaded = load_profiles()

    validated = profiles.validate(loaded, key_prefix="VERIDICUS_", kind="analyzer")

    assert set(validated) == {NAME}
    profile = validated[NAME]
    assert profile["purpose"] == "demonstration"
    assert profile["same_family_declared"] is True
    assert profile["permutation"] is True
    for role in ("judge", "verifier"):
        assert profile["roles"][role]["provider"] == "anthropic"
        assert profile["roles"][role]["model"] == "claude-sonnet-5-5"
        assert profile["roles"][role]["scope"] == "external"
        assert profile["roles"][role]["family"] == "claude"
        assert profile["roles"][role]["api_key_ref"] == KEY_REF


def test_the_fingerprints_do_not_contain_the_value_of_any_key() -> None:
    config = load_config(NAME, env())

    other = load_config(NAME, env("otra-clave-sintetica-0000"))

    assert config.config_sha256 == other.config_sha256
    assert config.profile_sha256 == other.profile_sha256
    assert config.profile_sha256 == sha256_jcs(load_profiles()["profiles"][NAME])
    visible = json.dumps(dict(config.profile), default=dict) + config.config_sha256
    assert KEY_CANARY not in visible
    assert KEY_REF in visible, "solo el nombre de la variable viaja en la configuración"


@settings(max_examples=25, deadline=None)
@given(key=st.text(min_size=1, max_size=40).filter(lambda k: bool(k.strip())))
def test_property_whatever_the_key_value_the_fingerprints_do_not_change(key: str) -> None:
    baseline = load_config(NAME, env())

    config = load_config(NAME, env(key))

    assert config.config_sha256 == baseline.config_sha256
    assert config.profile_sha256 == baseline.profile_sha256


PROFILE_YAML = """\
schema_version: "1.0.0"
profiles:
  demo-anthropic:
    permutation: true
    same_family_declared: true
    role_aliases: {verifier_permuted: verifier}
    purpose: demonstration
    roles:
      verifier:
        api_key_ref: VERIDICUS_ANTHROPIC_API_KEY
        family: claude
        scope: external
        model: claude-sonnet-5-5
        provider: anthropic
      judge:
        provider: anthropic
        model: claude-sonnet-5-5
        scope: external
        family: claude
        api_key_ref: VERIDICUS_ANTHROPIC_API_KEY
"""


def _file(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


def test_key_order_and_yaml_format_do_not_change_the_fingerprints(tmp_path: Path) -> None:
    compact = _file(tmp_path, "a.yaml", json.dumps(document()))
    sorted_keys = _file(tmp_path, "b.yaml", json.dumps(document(), sort_keys=True, indent=4))
    block = _file(tmp_path, "c.yaml", PROFILE_YAML)

    first = load_config(NAME, env(), compact)
    second = load_config(NAME, env(), sorted_keys)
    third = load_config(NAME, env(), block)

    assert first.profile_sha256 == second.profile_sha256 == third.profile_sha256
    assert first.config_sha256 == second.config_sha256 == third.config_sha256


def test_changing_a_profile_parameter_changes_the_fingerprints(tmp_path: Path) -> None:
    base = _file(tmp_path, "a.yaml", json.dumps(document()))
    changed = _file(tmp_path, "b.yaml", json.dumps(document(permutation=False)))

    first = load_config(NAME, env(), base)
    second = load_config(NAME, env(), changed)

    assert first.profile_sha256 != second.profile_sha256
    assert first.config_sha256 != second.config_sha256


def test_changing_a_limit_changes_the_config_fingerprint_but_not_the_profile_one(
    tmp_path: Path,
) -> None:
    base = _file(tmp_path, "a.yaml", json.dumps(document()))
    lowered = {**env(), "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "280"}

    first = load_config(NAME, env(), base)
    second = load_config(NAME, lowered, base)

    assert first.profile_sha256 == second.profile_sha256
    assert first.config_sha256 != second.config_sha256


def test_a_profile_with_an_extra_field_is_rejected() -> None:
    with pytest.raises(ConfigInvalidProfileError):
        validate_profile(document(temperatura_global=0.2), NAME, env())


def test_the_same_family_with_a_purpose_other_than_demonstration_is_rejected() -> None:
    evaluation = document(purpose="evaluation", same_family_declared=None)

    with pytest.raises(ConfigInvalidProfileError):
        validate_profile(evaluation, NAME, env())


def test_the_same_family_declared_in_an_evaluation_profile_is_rejected() -> None:
    evaluation = document(purpose="evaluation", same_family_declared=True)

    with pytest.raises(ConfigInvalidProfileError):
        validate_profile(evaluation, NAME, env())


def test_the_same_family_in_a_demonstration_without_declaring_it_is_rejected() -> None:
    undeclared = document(same_family_declared=None)

    with pytest.raises(ConfigInvalidProfileError):
        validate_profile(undeclared, NAME, env())


def test_the_same_family_declared_in_a_demonstration_is_accepted_with_its_warning() -> None:
    warnings = validate_profile(document(), NAME, env())

    assert "same_family" in warnings


def test_different_families_in_an_evaluation_profile_are_accepted_without_warnings() -> None:
    other_family = destination(provider="openai", model="modelo-sintetico-1", family="otra")
    evaluation = document(purpose="evaluation", verifier=other_family, same_family_declared=None)

    assert validate_profile(evaluation, NAME, env()) == ()


def test_a_missing_key_variable_is_rejected_naming_the_variable_and_never_a_value() -> None:
    without_key = {name: value for name, value in env().items() if name != KEY_REF}

    with pytest.raises(ConfigInvalidProfileError) as rejected:
        validate_profile(document(), NAME, without_key)

    assert KEY_REF in str(rejected.value)
    assert KEY_CANARY not in str(rejected.value)


def test_validating_does_not_modify_the_document_it_receives() -> None:
    original = document()
    snapshot = copy.deepcopy(original)

    validate_profile(original, NAME, env())

    assert original == snapshot
