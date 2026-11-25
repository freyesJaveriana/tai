"""Transporte de producción (PD-7, R-12): se inspecciona lo que se construye, sin abrir red."""

import ssl
from typing import Any

import httpx
import pytest

from veridicus_anonymizer.providers.http import build_client, default_transport, tls_context


def test_tls_context_requires_tls_1_2_certificate_and_hostname() -> None:
    context = tls_context()

    assert context.minimum_version == ssl.TLSVersion.TLSv1_2
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_default_transport_is_built_with_verification_no_retries_and_no_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Recorder(httpx.BaseTransport):
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(httpx, "HTTPTransport", Recorder)

    assert isinstance(default_transport(), Recorder)
    assert captured["retries"] == 0
    assert captured["trust_env"] is False
    verify = captured["verify"]
    assert isinstance(verify, ssl.SSLContext)
    assert verify.verify_mode == ssl.CERT_REQUIRED
    assert verify.minimum_version == ssl.TLSVersion.TLSv1_2


def test_the_real_default_transport_builds_without_opening_any_connection() -> None:
    transport = default_transport()

    assert isinstance(transport, httpx.HTTPTransport)
    transport.close()


def test_the_client_never_follows_redirects_nor_reads_the_environment() -> None:
    client = build_client(httpx.MockTransport(lambda request: httpx.Response(204)))

    assert client.follow_redirects is False
    assert client.trust_env is False
    assert client.max_redirects == 0
    client.close()
