"""Carga del archivo versionado y configuración efectiva (BR2.1, BR2.10, BR2.11).

El archivo versionado tiene un solo perfil, `demo-anthropic` (CG-U11-12). Las claves son canarios.
"""

import dataclasses
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from veridicus_contracts import profiles
from veridicus_contracts.canonical import sha256_jcs
from veridicus_contracts.loaders import load_file
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError

from veridicus_execution_profiles import loader
from veridicus_execution_profiles.loader import PROMPT_SHA256_UNSET, load_config, load_profiles
from veridicus_execution_profiles.validate import validate_profile

NAME = "demo-anthropic"
KEY_REF = "VERIDICUS_ANTHROPIC_API_KEY"
KEY_CANARY = "sk-sintetico-canario-7f3a91c2d4e5"
ENV = {KEY_REF: KEY_CANARY, "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300"}


def test_the_versioned_file_has_only_the_demo_profile_with_the_agreed_fields() -> None:
    document = load_profiles()

    assert list(document["profiles"]) == [NAME]
    profile = document["profiles"][NAME]
    assert set(profile) == {
        "purpose",
        "same_family_declared",
        "permutation",
        "role_aliases",
        "roles",
    }
    for role in ("judge", "verifier"):
        assert set(profile["roles"][role]) == {
            "provider",
            "model",
            "scope",
            "family",
            "api_key_ref",
        }


def test_the_versioned_file_never_carries_a_key_value() -> None:
    text = (Path(loader.__file__).parents[2] / "config" / "profiles.yaml").read_text("utf-8")

    assert "sk-" not in text
    assert text.count(f"api_key_ref: {KEY_REF}") == 2


def test_the_versioned_file_validates_with_the_real_u1_function_without_the_key() -> None:
    validated = profiles.validate(load_profiles(), key_prefix="VERIDICUS_", kind="analyzer")

    assert set(validated) == {NAME}


def test_the_demo_profile_starts_with_its_key_and_carries_the_same_family_warning() -> None:
    config = load_config(NAME, ENV)

    assert config.profile_name == NAME
    assert config.limits["model_call_timeout_s"] == 300
    assert validate_profile(load_profiles(), NAME, ENV) == ("same_family",)


def test_the_demo_profile_does_not_start_without_its_key_and_names_the_variable() -> None:
    with pytest.raises(ConfigInvalidProfileError) as error:
        load_config(NAME, {"VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "300"})

    assert KEY_REF in str(error.value)


def test_the_demo_profile_does_not_start_below_the_commercial_floor() -> None:
    with pytest.raises(ConfigInvalidProfileError):
        load_config(NAME, {**ENV, "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "269"})
    assert load_config(NAME, {**ENV, "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "270"})


def test_a_limit_that_the_catalog_forbids_is_a_limit_error() -> None:
    with pytest.raises(ConfigInvalidLimitError):
        load_config(NAME, {**ENV, "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "99999"})


def test_the_effective_config_follows_effective_config_v1() -> None:
    config = load_config(NAME, ENV, prompt_sha256="ab" * 32)
    schema = load_file(files("veridicus_contracts") / "profiles" / "effective-config.v1.yaml")
    body = {
        "schema_version": config.schema_version,
        "analyzer_version": config.analyzer_version,
        "profile_name": config.profile_name,
        "profile": load_profiles()["profiles"][NAME],
        "profile_sha256": config.profile_sha256,
        "prompt_sha256": config.prompt_sha256,
        "limits": dict(config.limits),
    }

    assert list(Draft202012Validator(schema).iter_errors(body)) == []
    assert config.config_sha256 == sha256_jcs(body)
    assert config.profile_sha256 == sha256_jcs(load_profiles()["profiles"][NAME])


def test_without_the_prompt_reference_the_fingerprint_uses_the_unset_marker() -> None:
    assert load_config(NAME, ENV).prompt_sha256 == PROMPT_SHA256_UNSET
    assert load_config(NAME, ENV, prompt_sha256="cd" * 32).prompt_sha256 == "cd" * 32
    assert (
        load_config(NAME, ENV).config_sha256
        != load_config(NAME, ENV, prompt_sha256="cd" * 32).config_sha256
    )


def test_the_effective_config_is_read_only() -> None:
    config = load_config(NAME, ENV)

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.profile_sha256 = "x"  # type: ignore[misc]  # motivo: la prueba comprueba que es inmutable
    assert isinstance(config.profile, MappingProxyType)
    assert isinstance(config.limits, MappingProxyType)
    with pytest.raises(TypeError):
        config.profile["purpose"] = "evaluation"  # type: ignore[index]  # motivo: es de solo lectura
    with pytest.raises(TypeError):
        config.profile["roles"]["judge"]["model"] = "otro"
    with pytest.raises(TypeError):
        config.limits["model_call_timeout_s"] = 1  # type: ignore[index]  # motivo: solo lectura


def test_the_profile_of_the_config_never_holds_the_key_value() -> None:
    config = load_config(NAME, ENV)

    assert KEY_CANARY not in repr(config)
    assert config.profile["roles"]["judge"]["api_key_ref"] == KEY_REF


def test_loading_a_list_inside_a_profile_gives_a_tuple(tmp_path: Path) -> None:
    assert loader._freeze({"a": [1, {"b": 2}]})["a"][1]["b"] == 2
    assert isinstance(loader._freeze({"a": [1]})["a"], tuple)


def test_an_explicit_path_is_read_and_the_file_is_not_written(tmp_path: Path) -> None:
    source = (Path(loader.__file__).parents[2] / "config" / "profiles.yaml").read_text("utf-8")
    copy = tmp_path / "otro.yaml"
    copy.write_text(source, encoding="utf-8")
    before = copy.stat().st_mtime_ns

    config = load_config(NAME, ENV, copy)

    assert config.profile_name == NAME
    assert copy.stat().st_mtime_ns == before
    assert copy.read_text("utf-8") == source


def test_the_default_path_falls_back_to_the_source_tree() -> None:
    document: dict[str, Any] = load_profiles(loader._default_path())

    assert document == load_profiles()
