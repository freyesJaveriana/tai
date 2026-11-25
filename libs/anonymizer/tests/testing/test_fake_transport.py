"""`FakeTransport` y control negativo `bypass` (paso 5; BR5.5; soporte de E19 y E23)."""

import json

import httpx
import pytest
from veridicus_contracts.model_calls import Message

from tests.support import AUTH_HEADER, KEY_CANARY, load_anthropic
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain.catalogs import Catalogs
from veridicus_anonymizer.testing.bypass import bypass_pseudonymization
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

URL = "https://api.anthropic.com/v1/messages"


def _client(transport: FakeTransport) -> httpx.Client:
    return httpx.Client(transport=transport, follow_redirects=False)


def test_captures_the_raw_request_with_the_key_untouched() -> None:
    transport = FakeTransport(FakeResponse.ok_json({"ok": True}))
    body = {"messages": [{"role": "user", "content": "hola"}]}

    response = _client(transport).post(URL, json=body, headers={AUTH_HEADER: KEY_CANARY})

    assert response.json() == {"ok": True}
    assert transport.request_count == 1
    raw = transport.requests[0]
    assert (raw.method, raw.scheme, raw.host, raw.port, raw.path) == (
        "POST",
        "https",
        "api.anthropic.com",
        443,
        "/v1/messages",
    )
    assert raw.headers[AUTH_HEADER] == KEY_CANARY, "la captura guarda la clave tal cual"
    assert json.loads(raw.body) == body


def test_hides_the_key_only_when_the_request_is_represented() -> None:
    transport = FakeTransport(FakeResponse.ok_json({}))
    _client(transport).post(
        URL, json={}, headers={AUTH_HEADER: KEY_CANARY, "anthropic-version": "v"}
    )

    for text in (repr(transport.requests[0]), repr(transport)):
        assert KEY_CANARY not in text
        assert "***" in text
        assert "anthropic-version" in text, "las demás cabeceras sí se muestran"
    assert transport.requests[0].headers[AUTH_HEADER] == KEY_CANARY


def test_returns_the_scripted_responses_in_order() -> None:
    transport = FakeTransport(FakeResponse.http_error(503), load_anthropic("success_empty"))
    client = _client(transport)

    first = client.post(URL, json={})
    second = client.post(URL, json={})

    assert (first.status_code, second.status_code) == (503, 200)
    assert first.json()["type"] == "error"
    assert second.json()["stop_reason"] == "end_turn"
    assert transport.request_count == 2


def test_simulates_a_provider_that_does_not_answer_in_time() -> None:
    transport = FakeTransport(FakeResponse.timeout())

    with pytest.raises(httpx.ReadTimeout):
        _client(transport).post(URL, json={})

    assert transport.request_count == 1, "la petición quedó capturada aunque no hubo respuesta"


def test_a_body_that_is_not_json_and_a_307_are_returned_as_they_are_without_following() -> None:
    transport = FakeTransport(
        FakeResponse.not_json(), FakeResponse.redirect("https://otro.example.com/x")
    )
    client = _client(transport)

    not_json = client.post(URL, json={})
    redirect = client.post(URL, json={})

    with pytest.raises(json.JSONDecodeError):
        not_json.json()
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://otro.example.com/x"
    assert [r.host for r in transport.requests] == ["api.anthropic.com", "api.anthropic.com"], (
        "ninguna petición llegó al host de la redirección"
    )


def test_a_request_without_a_scripted_response_fails_loudly() -> None:
    transport = FakeTransport()

    with pytest.raises(RuntimeError, match="sin respuestas guionadas"):
        _client(transport).post(URL, json={})

    assert transport.request_count == 1


@pytest.mark.parametrize(
    ("url", "scheme", "port"),
    [
        ("https://api.anthropic.com:8443/v1/messages", "https", 8443),
        ("https://api.anthropic.com/v1/messages", "https", 443),
        ("http://servidor.example.com/ruta", "http", 80),
    ],
)
def test_reports_the_port_the_request_really_targets(url: str, scheme: str, port: int) -> None:
    transport = FakeTransport(FakeResponse.ok_json({}))

    _client(transport).get(url)

    assert (transport.requests[0].scheme, transport.requests[0].port) == (scheme, port)


def test_bypass_replaces_the_internal_pseudonymization_with_one_that_masks_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = generate_module.pseudonymize

    bypass_pseudonymization(monkeypatch)

    assert generate_module.pseudonymize is not original
    messages = [Message("user", "Casilda Roncancio dijo que salió temprano.")]
    empty = Catalogs(rules=(), allowed_words=frozenset(), domains={}, capabilities={})
    unmasked, table = generate_module.pseudonymize(messages, empty)
    assert unmasked == messages
    assert table.is_empty
