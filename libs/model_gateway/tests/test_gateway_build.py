"""Armado del gateway por perfil (BR10.1, NFRD-U11-03, AUTONOMIA-04): falla antes de cualquier llamada."""

import pytest
from veridicus_errors import ConfigInvalidProfileError, GatewayConfigError
from veridicus_execution_profiles.floors import COMMERCIAL_MIN_CALL_TIMEOUT_S

from tests.support import (
    SpyProvider,
    external_destination,
    local_destination,
    make_config,
    make_request,
    profile_with,
    with_profile,
    with_timeout,
)
from veridicus_model_gateway.gateway import build


def test_an_external_role_without_a_provider_does_not_start() -> None:
    with pytest.raises(GatewayConfigError):
        build(make_config())


def test_an_external_role_with_the_provider_starts() -> None:
    gateway = build(make_config(), anonymizing_provider=SpyProvider())

    assert gateway.calls == ()


def test_269_seconds_do_not_start_and_270_start() -> None:
    provider = SpyProvider()

    with pytest.raises(GatewayConfigError, match="270"):
        build(with_timeout(make_config(), 269), anonymizing_provider=provider)
    build(with_timeout(make_config(), 270), anonymizing_provider=provider)

    assert provider.requests == [], "armar el gateway no hace ninguna llamada"


def test_the_loader_already_refuses_269_seconds_and_the_gateway_repeats_the_floor() -> None:
    with pytest.raises(ConfigInvalidProfileError):
        make_config(269)
    assert COMMERCIAL_MIN_CALL_TIMEOUT_S == 270


def test_a_local_role_is_deferred_to_b11b_even_with_a_provider() -> None:
    roles = {"judge": local_destination(), "verifier": external_destination()}
    config = with_profile(make_config(), profile_with(roles=roles))

    with pytest.raises(GatewayConfigError, match="B11b"):
        build(config, anonymizing_provider=SpyProvider())


def test_a_local_fallback_provider_is_deferred_too() -> None:
    config = with_profile(make_config(), profile_with(fallback_provider=local_destination()))

    with pytest.raises(GatewayConfigError, match="B11b"):
        build(config, anonymizing_provider=SpyProvider())


def test_an_external_fallback_provider_starts() -> None:
    config = with_profile(make_config(), profile_with(fallback_provider=external_destination()))

    build(config, anonymizing_provider=SpyProvider())


def test_a_request_to_a_local_destination_is_refused_and_nothing_is_called() -> None:
    provider = SpyProvider()
    gateway = build(make_config(), anonymizing_provider=provider)

    with pytest.raises(GatewayConfigError):
        gateway.generate(make_request(scope="local"))

    assert provider.requests == []
