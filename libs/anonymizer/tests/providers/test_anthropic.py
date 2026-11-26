"""Adaptador de Anthropic (paso 9; F5, BR2.4–BR2.6, BR3.5, BR5.2–BR5.4; E19–E21, E23, E27).

Respuestas grabadas sintéticas, contrastadas con la documentación oficial citada en la bitácora.
Nada abre red: todo pasa por el `FakeTransport` o por un `MockTransport` propio.
"""

import gzip
import json
from collections.abc import Callable, Iterator
from dataclasses import replace
from typing import Any

import httpx
import pytest
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    GenerateRequest,
    InvalidOutput,
    ModelCallError,
    ProviderError,
    Timeout,
)

from tests.support import (
    EMPTY_FINDINGS,
    KEY_CANARY,
    MODEL,
    RESPONSE_SCHEMA,
    anthropic_envelope,
    exception_texts,
    load_anthropic,
    make_destination,
    make_request,
    ok_response,
)
from veridicus_anonymizer.providers import anthropic as anthropic_module
from veridicus_anonymizer.providers.anthropic import ProviderReply, send
from veridicus_anonymizer.providers.http import build_client
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

MAX_BYTES = 2_097_152


def run(
    transport: httpx.BaseTransport,
    *,
    request: GenerateRequest | None = None,
    mode: str = "json_schema_native",
    timeout_s: float = 30.0,
    max_bytes: int = MAX_BYTES,
) -> ProviderReply:
    chosen = request if request is not None else make_request()
    return send(
        client=build_client(transport),
        request=chosen,
        messages=chosen.messages,
        structured_mode=mode,
        effort_parameter="effort",
        api_key=KEY_CANARY,
        timeout_s=timeout_s,
        max_response_bytes=max_bytes,
    )


def raw_json(text: str) -> FakeResponse:
    """200 con un sobre válido cuyo bloque de texto es exactamente `text`."""
    return FakeResponse.ok_json(anthropic_envelope(text))


def test_a_successful_call_sends_the_native_body_once_and_returns_the_parsed_json() -> None:
    transport = FakeTransport(load_anthropic("success_empty"))
    request = make_request()

    reply = run(transport, request=request)

    assert reply.content == EMPTY_FINDINGS
    assert transport.request_count == 1
    raw = transport.requests[0]
    assert (raw.method, raw.scheme, raw.host, raw.port, raw.path) == (
        "POST",
        "https",
        "api.anthropic.com",
        443,
        "/v1/messages",
    )
    assert raw.headers["x-api-key"] == KEY_CANARY
    assert raw.headers["anthropic-version"] == "2026-10-21"
    assert raw.headers["content-type"] == "application/json"
    body = json.loads(raw.body)
    assert body["model"] == MODEL
    assert body["max_tokens"] == 16000
    assert body["output_config"] == {
        "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA},
        "effort": "medium",
    }
    assert body["system"] == request.messages[0].content
    assert [m["role"] for m in body["messages"]] == ["user"]


def test_the_model_call_records_tokens_slot_effort_and_anonymized() -> None:
    request = make_request(slot="fallback")

    reply = run(FakeTransport(ok_response()), request=request)

    call = reply.call
    assert (call.provider, call.model, call.role) == ("anthropic", MODEL, "judge")
    assert (call.input_tokens, call.output_tokens) == (412, 37)
    assert call.fallback_provider is True
    assert call.anonymized is True
    assert call.effort_or_quantization == "medium"
    assert (call.version, call.engine, call.seed) == (None, None, None)
    assert call.at.microsecond == 0


def test_a_request_without_effort_or_system_omits_both_fields() -> None:
    request = make_request(destination=make_destination(parameters={}))
    request = replace(request, messages=request.messages[1:])
    transport = FakeTransport(ok_response())

    reply = run(transport, request=request)

    body = json.loads(transport.requests[0].body)
    assert "system" not in body
    assert body["output_config"] == {"format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}}
    assert reply.call.effort_or_quantization is None


def test_the_key_travels_only_in_its_header() -> None:
    transport = FakeTransport(ok_response())

    run(transport)

    raw = transport.requests[0]
    assert KEY_CANARY.encode() not in raw.body
    assert KEY_CANARY not in raw.path
    assert [n for n, v in raw.headers.items() if KEY_CANARY in v] == ["x-api-key"]
    assert KEY_CANARY not in repr(raw)


@pytest.mark.parametrize(
    ("fixture", "expected", "tokens"),
    [
        ("error_503", ProviderError, (0, 0)),
        ("error_529", ProviderError, (0, 0)),
        ("redirect_307", ProviderError, (0, 0)),
        ("refusal", ContentBlocked, (412, 0)),
        ("max_tokens", InvalidOutput, (412, 4096)),
        ("not_json", InvalidOutput, (412, 9)),
        ("invalid_schema", InvalidOutput, (412, 12)),
    ],
)
def test_each_recorded_failure_maps_to_its_typed_error_with_one_request_and_its_call(
    fixture: str, expected: type[ModelCallError], tokens: tuple[int, int]
) -> None:
    transport = FakeTransport(load_anthropic(fixture), ok_response())

    with pytest.raises(expected) as excinfo:
        run(transport)

    assert transport.request_count == 1, "ni un reintento, ni una redirección seguida"
    call = excinfo.value.call  # type: ignore[attr-defined]
    assert (call.input_tokens, call.output_tokens) == tokens
    assert call.anonymized is True
    for text in exception_texts(excinfo.value):
        assert KEY_CANARY not in text
    assert KEY_CANARY not in repr(call)


def test_a_503_followed_by_a_200_sends_exactly_once() -> None:
    transport = FakeTransport(load_anthropic("error_503"), load_anthropic("success_empty"))

    with pytest.raises(ProviderError):
        run(transport)

    assert transport.request_count == 1


def test_a_redirect_is_never_followed() -> None:
    transport = FakeTransport(load_anthropic("redirect_307"), ok_response())

    with pytest.raises(ProviderError):
        run(transport)

    assert [r.host for r in transport.requests] == ["api.anthropic.com"]


def test_a_read_timeout_is_a_timeout_with_its_call() -> None:
    transport = FakeTransport(FakeResponse.timeout(), ok_response())

    with pytest.raises(Timeout) as excinfo:
        run(transport)

    assert transport.request_count == 1
    assert excinfo.value.call.anonymized is True


@pytest.mark.parametrize("error", [httpx.ConnectError("sin conexion"), httpx.ConnectTimeout("x")])
def test_a_connection_that_could_not_open_is_anonymizer_unavailable_without_call(
    error: Exception,
) -> None:
    transport = FakeTransport(FakeResponse(raises=error))

    with pytest.raises(AnonymizerUnavailable) as excinfo:
        run(transport)

    assert not hasattr(excinfo.value, "call")
    assert transport.request_count == 1


@pytest.mark.parametrize("error", [httpx.ReadError("corte"), RuntimeError("fallo sintetico")])
def test_a_cut_or_unexpected_transport_failure_after_sending_is_a_provider_error(
    error: Exception,
) -> None:
    transport = FakeTransport(FakeResponse(raises=error), ok_response())

    with pytest.raises(ProviderError) as excinfo:
        run(transport)

    assert transport.request_count == 1
    assert excinfo.value.__context__ is None, "no se encadena la excepción de la capa HTTP"


def test_a_connection_cut_in_the_middle_of_the_body_is_a_provider_error() -> None:
    class Cut(httpx.SyncByteStream):
        def __iter__(self) -> Iterator[bytes]:
            yield b'{"id": "msg_sintetico", '
            raise httpx.ReadError("corte sintetico")

    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, stream=Cut())

    with pytest.raises(ProviderError):
        run(httpx.MockTransport(handler))

    assert calls["n"] == 1


def test_a_body_over_the_cap_is_a_provider_error() -> None:
    transport = FakeTransport(ok_response(), ok_response())

    with pytest.raises(ProviderError):
        run(transport, max_bytes=100)

    assert transport.request_count == 1


def test_f07_a_compressed_response_is_rejected_without_decompressing_it() -> None:
    packed = gzip.compress(ok_response().body)
    headers = {"content-type": "application/json", "content-encoding": "gzip"}
    transport = FakeTransport(FakeResponse(status=200, body=packed, headers=headers))

    with pytest.raises(ProviderError) as excinfo:
        run(transport)

    assert transport.request_count == 1
    assert excinfo.value.call.anonymized is True
    assert transport.requests[0].headers["accept-encoding"] == "identity"


def test_f07_a_chunked_body_without_content_length_stops_reading_at_the_cap() -> None:
    consumed: list[int] = []

    class Chunks(httpx.SyncByteStream):
        def __iter__(self) -> Iterator[bytes]:
            for n in range(100):
                consumed.append(n)
                yield b"x" * 1000

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/json"}, stream=Chunks())

    with pytest.raises(ProviderError):
        run(httpx.MockTransport(handler), max_bytes=2500)

    assert len(consumed) < 100, "no se leyó todo el cuerpo"


def test_a_body_exactly_at_the_cap_is_accepted() -> None:
    response = ok_response()

    reply = run(FakeTransport(response), max_bytes=len(response.body))

    assert reply.content == EMPTY_FINDINGS


def test_a_response_that_arrives_after_the_deadline_is_a_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readings = iter([0.0, 1000.0])
    monkeypatch.setattr(anthropic_module, "monotonic", lambda: next(readings))

    with pytest.raises(Timeout) as excinfo:
        run(FakeTransport(ok_response()), timeout_s=5.0)

    assert excinfo.value.call.anonymized is True


def _text_block(**changes: Any) -> dict[str, Any]:
    return {"type": "text", "text": '{"hallazgos": []}', **changes}


def _with_content(content: object, **changes: Any) -> FakeResponse:
    envelope = {**anthropic_envelope(EMPTY_FINDINGS), "content": content, **changes}
    return FakeResponse.ok_json(envelope)


def _thinking_block() -> dict[str, Any]:
    """Bloque de pensamiento con `display: "omitted"`: texto vacío y firma cifrada (sintética)."""
    return {"type": "thinking", "thinking": "", "signature": "firma_sintetica_cifrada"}


def _redacted_thinking_block() -> dict[str, Any]:
    return {"type": "redacted_thinking", "data": "datos_sinteticos_cifrados"}


@pytest.mark.parametrize(
    "content",
    [
        [_thinking_block(), _text_block()],
        [_redacted_thinking_block(), _text_block()],
        [_thinking_block(), _redacted_thinking_block(), _text_block()],
        [_text_block(), _thinking_block()],
    ],
    ids=["pensamiento_omitido", "pensamiento_redactado", "dos_pensamientos", "pensamiento_despues"],
)
def test_thinking_blocks_are_ignored_and_the_single_text_block_is_the_answer(
    content: list[dict[str, Any]],
) -> None:
    transport = FakeTransport(_with_content(content), ok_response())

    reply = run(transport)

    assert reply.content == EMPTY_FINDINGS
    assert transport.request_count == 1
    assert (reply.call.input_tokens, reply.call.output_tokens) == (412, 37)


INVALID_RESPONSES: dict[str, Callable[[], FakeResponse]] = {
    "envoltura_que_no_es_objeto": lambda: FakeResponse.ok_json([1, 2]),
    "cuerpo_que_no_es_utf8": lambda: FakeResponse(status=200, body=b"\xff\xfe"),
    "contenido_vacio": lambda: _with_content([]),
    "varios_bloques_de_texto": lambda: _with_content([_text_block(), _text_block()]),
    "bloque_que_no_es_texto": lambda: _with_content([{"type": "thinking", "thinking": "x"}]),
    "solo_pensamiento_redactado": lambda: _with_content([_redacted_thinking_block()]),
    "pensamiento_y_dos_textos": lambda: _with_content(
        [_thinking_block(), _text_block(), _text_block()]
    ),
    "pensamiento_y_herramienta": lambda: _with_content(
        [_thinking_block(), {"type": "tool_use", "id": "toolu_x", "name": "x", "input": {}}]
    ),
    "bloque_que_no_es_objeto": lambda: _with_content(["texto"]),
    "pensamiento_y_bloque_que_no_es_objeto": lambda: _with_content([_thinking_block(), "texto"]),
    "bloque_sin_texto": lambda: _with_content([{"type": "text", "text": 5}]),
    "contenido_que_no_es_lista": lambda: _with_content("texto"),
    "sin_stop_reason": lambda: _with_content([_text_block()], stop_reason=None),
    "pause_turn": lambda: _with_content([_text_block()], stop_reason="pause_turn"),
    "json_con_comentario": lambda: raw_json('{"hallazgos": [] /* x */}'),
    "json_con_nan": lambda: raw_json('{"hallazgos": [], "x": NaN}'),
    "json_con_infinito": lambda: raw_json('{"hallazgos": [], "x": Infinity}'),
    "json_con_numero_fuera_de_rango": lambda: raw_json('{"hallazgos": [], "x": 1e999}'),
    "json_con_clave_repetida": lambda: raw_json('{"hallazgos": [], "hallazgos": []}'),
    "json_demasiado_anidado": lambda: raw_json("[" * 100_000),
    "json_que_no_es_objeto": lambda: raw_json("[]"),
    "json_que_no_cumple_el_esquema": lambda: raw_json('{"hallazgos": [{"hecho": "x"}]}'),
    "json_con_campo_de_mas": lambda: raw_json('{"hallazgos": [], "extra": 1}'),
}


@pytest.mark.parametrize("name", list(INVALID_RESPONSES), ids=list(INVALID_RESPONSES))
def test_a_malformed_or_unexpected_200_is_invalid_output_never_a_success(name: str) -> None:
    transport = FakeTransport(INVALID_RESPONSES[name]())

    with pytest.raises(InvalidOutput) as excinfo:
        run(transport)

    assert transport.request_count == 1
    assert excinfo.value.call.anonymized is True


def test_usage_that_is_missing_or_malformed_counts_as_zero_tokens() -> None:
    bad = _with_content([_text_block()], usage={"input_tokens": True, "output_tokens": -3})
    missing = _with_content([_text_block()], usage=None)

    assert run(FakeTransport(bad)).call.input_tokens == 0
    assert run(FakeTransport(bad)).call.output_tokens == 0
    reply = run(FakeTransport(missing))
    assert (reply.call.input_tokens, reply.call.output_tokens) == (0, 0)


def test_a_finite_decimal_number_in_the_envelope_is_accepted() -> None:
    reply = run(FakeTransport(_with_content([_text_block()], temperatura=1.5)))

    assert reply.content == EMPTY_FINDINGS


def test_an_unexpected_error_while_interpreting_is_a_provider_error_with_its_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(raw: bytes, schema: dict[str, Any]) -> None:
        raise RuntimeError("fallo sintetico")

    monkeypatch.setattr(anthropic_module, "_interpret", explode)

    with pytest.raises(ProviderError) as excinfo:
        run(FakeTransport(ok_response()))

    assert excinfo.value.call.anonymized is True


@pytest.mark.parametrize(
    "case",
    ["modo_herramienta_forzada", "esquema_invalido", "sin_mensajes", "esfuerzo_numerico"]
    + ["esfuerzo_con_espacio", "esquema_no_serializable", "esquema_a_gran_profundidad"],
)
def test_a_body_that_cannot_be_built_fails_closed_with_zero_requests(case: str) -> None:
    request = make_request()
    mode = "json_schema_native"
    if case == "modo_herramienta_forzada":
        mode = "forced_tool"
    if case == "esquema_invalido":
        request = replace(request, schema={"type": 5})
    if case == "esquema_a_gran_profundidad":
        deep: dict[str, Any] = {"type": "string"}
        for _ in range(3000):
            deep = {"type": "array", "items": deep}
        request = replace(request, schema=deep)
    if case == "esquema_no_serializable":
        request = replace(request, schema={"type": "object", "default": {1, 2}})
    if case == "sin_mensajes":
        request = replace(request, messages=request.messages[:1])
    if case == "esfuerzo_numerico":
        request = replace(request, destination=make_destination(parameters={"effort": 3}))
    if case == "esfuerzo_con_espacio":
        request = replace(request, destination=make_destination(parameters={"effort": "muy alto"}))
    transport = FakeTransport(ok_response())

    with pytest.raises(AnonymizerUnavailable) as excinfo:
        run(transport, request=request, mode=mode)

    assert transport.request_count == 0
    assert not hasattr(excinfo.value, "call")
    assert KEY_CANARY not in str(excinfo.value)
