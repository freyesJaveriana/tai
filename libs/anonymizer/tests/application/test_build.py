"""`build_anonymizer` (paso 10; PD-7, F3b, BR2.2): firma, configuración y transporte de producción."""

import inspect
from typing import Any

import pytest
from veridicus_contracts.model_calls import AnonymizingProvider
from veridicus_errors import ConfigInvalidLimitError, ConfigInvalidProfileError

from tests.support import KEY_CANARY, default_env, make_request, ok_response
from veridicus_anonymizer import api as api_module
from veridicus_anonymizer.api import Anonymizer, build_anonymizer
from veridicus_anonymizer.domain.catalogs import CatalogError
from veridicus_anonymizer.testing.fake_transport import FakeTransport


def test_the_signature_has_only_env_and_transport_and_no_way_to_skip_pseudonymization() -> None:
    parameters = inspect.signature(build_anonymizer).parameters

    assert list(parameters) == ["env", "transport"]
    assert parameters["transport"].default is None
    assert not any("bypass" in name or "mask" in name for name in parameters)


def test_the_module_satisfies_the_anonymizing_provider_protocol() -> None:
    provider: AnonymizingProvider = build_anonymizer(default_env(), FakeTransport(ok_response()))

    assert isinstance(provider, Anonymizer)


def test_the_representation_never_shows_the_key() -> None:
    anonymizer = build_anonymizer(default_env(), FakeTransport())

    assert KEY_CANARY not in repr(anonymizer)
    assert KEY_CANARY not in str(anonymizer)


def test_an_invalid_catalog_stops_the_construction_before_any_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(ok_response())

    def broken(*args: Any, **kwargs: Any) -> Any:
        raise CatalogError("el archivo de datos «allowed-words» es inválido")

    monkeypatch.setattr(api_module, "load_catalogs", broken)

    with pytest.raises(ConfigInvalidProfileError) as excinfo:
        build_anonymizer(default_env(), transport)

    assert transport.request_count == 0
    assert excinfo.value.code == "config.invalid_profile"
    assert KEY_CANARY not in str(excinfo.value)


@pytest.mark.parametrize(
    "variable",
    [
        "VERIDICUS_LIMIT_ANONYMIZER_RESPONSE_MAX_BYTES",  # sube la cifra
        "VERIDICUS_LIMIT_NO_EXISTE",
    ],
)
def test_an_invalid_limit_stops_the_construction(variable: str) -> None:
    env = {**default_env(), variable: "999999999999"}

    with pytest.raises(ConfigInvalidLimitError) as excinfo:
        build_anonymizer(env, FakeTransport())

    assert excinfo.value.code == "config.invalid_limit"


def test_without_a_transport_the_production_factory_is_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FakeTransport(ok_response())
    monkeypatch.setattr(api_module, "default_transport", lambda: transport)

    build_anonymizer(default_env()).generate(make_request())

    assert transport.request_count == 1


def test_the_environment_is_copied_so_a_later_change_does_not_alter_the_module() -> None:
    env = default_env()
    transport = FakeTransport(ok_response())
    anonymizer = build_anonymizer(env, transport)
    env.clear()

    anonymizer.generate(make_request())

    assert transport.request_count == 1
