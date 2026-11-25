"""`generate` (paso 10; F1, F7, BR1.6, BR2.1, BR2.4, BR3.1): casos sonda del fallo cerrado y del envío único.

Cada condición previa al envío se rompe por separado y el `FakeTransport` cuenta las peticiones. Los
casos de los que ya se ocupa el rojo (`tests/guards`) no se repiten: aquí van las variantes finas.
"""

import logging
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import httpx
import pytest
from veridicus_contracts.model_calls import (
    AnonymizerUnavailable,
    ContentBlocked,
    InvalidOutput,
    ModelCall,
    ModelCallError,
    ProviderError,
    Timeout,
)

from tests.support import (
    KEY_CANARY,
    KEY_REF,
    TESTIMONY_CANARY,
    Ctx,
    anthropic_envelope,
    boom,
    default_env,
    exception_texts,
    install_context,
    load_anthropic,
    load_seeded,
    make_ctx,
    make_harness,
    make_request,
    ok_response,
)
from veridicus_anonymizer.api import build_anonymizer
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain.catalogs import ProviderDomain
from veridicus_anonymizer.domain.masking import MaskingError
from veridicus_anonymizer.testing.fake_transport import FakeResponse, FakeTransport

SEEDED = load_seeded()
Break = Callable[[Ctx, pytest.MonkeyPatch], None]


def _domain(value: str, port: int = 443) -> Break:
    def apply(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
        domains = {**ctx.catalogs.domains, "anthropic": ProviderDomain(domain=value, port=port)}
        ctx.catalogs = replace(ctx.catalogs, domains=domains)

    return apply


def _key(value: str | None) -> Break:
    def apply(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
        if value is None:
            del ctx.env[KEY_REF]
        else:
            ctx.env[KEY_REF] = value

    return apply


def _no_key_ref(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
    destination = replace(ctx.request.destination, api_key_ref=None)
    ctx.request = replace(ctx.request, destination=destination)


def _timeout(seconds: float) -> Break:
    def apply(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
        ctx.request = replace(ctx.request, timeout_s=seconds)

    return apply


def _masking_error(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> Any:
        raise MaskingError("la tabla no concuerda")

    mp.setattr(generate_module, "pseudonymize", fail)


def _deep_schema(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
    schema: dict[str, Any] = {"type": "string"}
    for _ in range(3000):
        schema = {"type": "array", "items": schema}
    ctx.request = replace(ctx.request, schema=schema)


def _replacements_raise(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
    mp.setattr(generate_module, "_replacements", boom)


def _catalog_without_domain(ctx: Ctx, mp: pytest.MonkeyPatch) -> None:
    ctx.catalogs = replace(ctx.catalogs, domains={})


PRE_SEND_BREAKS: dict[str, Break] = {
    "esquema_anidado_a_gran_profundidad": _deep_schema,
    "error_inesperado_al_contar_reemplazos": _replacements_raise,
    "catalogo_sin_el_dominio_del_proveedor": _catalog_without_domain,
    "dominio_con_mayusculas": _domain("API.anthropic.com"),
    "dominio_con_punto_final": _domain("api.anthropic.com."),
    "dominio_con_puerto_8443_en_el_catalogo": _domain("api.anthropic.com", 8443),
    "dominio_de_otro_proveedor": _domain("api.openai.com"),
    "clave_vacia": _key(""),
    "clave_con_salto_de_linea": _key("sk-sintetico\nx-otra: cabecera"),
    "clave_con_caracteres_no_ascii": _key("sk-sintético-ñ"),
    "clave_ausente_del_entorno": _key(None),
    "destino_sin_nombre_de_clave": _no_key_ref,
    "plazo_ya_agotado": _timeout(0.0),
    "error_de_tabla_del_dominio": _masking_error,
}


@pytest.mark.parametrize("name", list(PRE_SEND_BREAKS), ids=list(PRE_SEND_BREAKS))
def test_every_pre_send_condition_fails_closed_with_zero_requests(
    name: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    ctx = make_ctx()
    PRE_SEND_BREAKS[name](ctx, monkeypatch)
    install_context(ctx, monkeypatch)
    harness = make_harness(ok_response(), env=ctx.env)

    with pytest.raises(AnonymizerUnavailable) as excinfo:
        harness.anonymizer.generate(ctx.request)

    assert harness.transport.request_count == 0
    assert not hasattr(excinfo.value, "call")
    assert excinfo.value.__context__ is None and excinfo.value.__cause__ is None
    for text in [*exception_texts(excinfo.value), caplog.text]:
        assert KEY_CANARY not in text
        assert not any(entity in text for entity in SEEDED["entidades"])


def test_f04_the_masking_budget_is_enforced_even_when_the_total_deadline_still_has_room(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El reloj solo avanza dentro de `pseudonymize`: 10 s de 30 s pasan del presupuesto (4,5 s)
    pero no del plazo total. Un `has_budget` siempre verdadero enviaría y haría fallar la prueba."""
    clock = [0.0]
    real = generate_module.pseudonymize

    def slow(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 10.0
        return real(*args, **kwargs)

    monkeypatch.setattr(generate_module, "now", lambda: clock[0])
    monkeypatch.setattr(generate_module, "pseudonymize", slow)
    harness = make_harness(ok_response())

    with pytest.raises(AnonymizerUnavailable, match="presupuesto") as excinfo:
        harness.anonymizer.generate(make_request(timeout_s=30.0))

    assert harness.transport.request_count == 0
    assert not hasattr(excinfo.value, "call")


def test_f04_control_a_masking_that_stays_inside_the_budget_sends_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    real = generate_module.pseudonymize

    def quick(*args: Any, **kwargs: Any) -> Any:
        clock[0] += 1.0
        return real(*args, **kwargs)

    monkeypatch.setattr(generate_module, "now", lambda: clock[0])
    monkeypatch.setattr(generate_module, "pseudonymize", quick)
    harness = make_harness(ok_response())

    harness.anonymizer.generate(make_request(timeout_s=30.0))

    assert harness.transport.request_count == 1


def test_the_baseline_scenario_sends_exactly_once_and_returns_the_result() -> None:
    harness = make_harness(ok_response())

    result = harness.anonymizer.generate(make_request())

    assert harness.transport.request_count == 1
    assert result.content == {"hallazgos": []}
    assert result.call.anonymized is True


def _cut_transport() -> httpx.MockTransport:
    class Cut(httpx.SyncByteStream):
        def __iter__(self) -> Any:
            yield b'{"id": '
            raise httpx.ReadError("corte sintetico")

    return httpx.MockTransport(lambda request: httpx.Response(200, stream=Cut()))


ONE_SHOT: dict[str, tuple[type[ModelCallError], Callable[[], httpx.BaseTransport]]] = {
    "503_y_luego_200": (
        ProviderError,
        lambda: FakeTransport(load_anthropic("error_503"), ok_response()),
    ),
    "529": (ProviderError, lambda: FakeTransport(load_anthropic("error_529"), ok_response())),
    "plazo_agotado": (Timeout, lambda: FakeTransport(FakeResponse.timeout(), ok_response())),
    "redireccion_307": (
        ProviderError,
        lambda: FakeTransport(load_anthropic("redirect_307"), ok_response()),
    ),
    "corte_a_mitad_del_cuerpo": (ProviderError, _cut_transport),
    "rechazo": (ContentBlocked, lambda: FakeTransport(load_anthropic("refusal"), ok_response())),
    "max_tokens": (InvalidOutput, lambda: FakeTransport(load_anthropic("max_tokens"))),
}


@pytest.mark.parametrize("name", list(ONE_SHOT), ids=list(ONE_SHOT))
def test_a_failure_after_sending_is_typed_carries_its_call_and_is_never_retried(
    name: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    expected, make_transport = ONE_SHOT[name]
    transport = make_transport()
    sent: list[httpx.Request] = []
    anonymizer = build_anonymizer(default_env(), _Counting(transport, sent))

    with pytest.raises(expected) as excinfo:
        anonymizer.generate(make_request())

    assert len(sent) == 1, "exactamente una petición, sin reintentos"
    call = excinfo.value.call  # type: ignore[attr-defined]
    assert isinstance(call, ModelCall) and call.anonymized is True
    for text in [*exception_texts(excinfo.value), repr(call), caplog.text]:
        assert KEY_CANARY not in text
        assert TESTIMONY_CANARY not in text


class _Counting(httpx.BaseTransport):
    """Envuelve un transporte y cuenta las peticiones que llegan."""

    def __init__(self, inner: httpx.BaseTransport, sent: list[httpx.Request]) -> None:
        self._inner = inner
        self._sent = sent

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self._sent.append(request)
        return self._inner.handle_request(request)


def test_a_response_over_the_configured_cap_is_a_provider_error_after_one_request() -> None:
    env = {**default_env(), "VERIDICUS_LIMIT_ANONYMIZER_RESPONSE_MAX_BYTES": "100"}
    harness = make_harness(ok_response(), env=env)

    with pytest.raises(ProviderError) as excinfo:
        harness.anonymizer.generate(make_request())

    assert harness.transport.request_count == 1
    assert excinfo.value.call.anonymized is True


def _timeouts_seen(env: dict[str, str], timeout_s: float) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.extensions["timeout"])
        return httpx.Response(200, json=anthropic_envelope({"hallazgos": []}))

    build_anonymizer(env, httpx.MockTransport(handler)).generate(make_request(timeout_s=timeout_s))
    return seen


def test_the_effective_deadline_is_the_smaller_of_the_request_and_the_catalog_cap() -> None:
    capped = _timeouts_seen({**default_env(), "VERIDICUS_LIMIT_MODEL_CALL_TIMEOUT_S": "10"}, 30.0)
    short = _timeouts_seen(default_env(), 5.0)

    assert 0 < capped["read"] <= 10
    assert 0 < short["read"] <= 5
    assert capped["connect"] <= 10 and short["connect"] <= 5


def test_an_unexpected_error_after_sending_keeps_the_call_and_chains_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(generate_module, "restore", boom)
    harness = make_harness(ok_response())

    with pytest.raises(ProviderError) as excinfo:
        harness.anonymizer.generate(make_request())

    assert excinfo.value.__context__ is None and excinfo.value.__cause__ is None
    assert (excinfo.value.call.input_tokens, excinfo.value.call.output_tokens) == (412, 37)


def test_a_marker_altered_in_the_response_stays_unrestored_and_is_reported() -> None:
    turnos = [{"turno": 1, "hablante": "TES", "texto": "doña Casilda Roncancio salió."}]
    payload = {
        "hallazgos": [
            {
                "hecho": "[Persona_1] salió",
                "tipo": "temporal",
                "cita_a": {"texto": "[PERSONA_1] salió", "turno": 1},
                "cita_b": {"texto": "[PERSONA_1] salió", "turno": 1},
                "observaciones": "ninguna",
            }
        ]
    }
    harness = make_harness(ok_response(payload))

    result = harness.anonymizer.generate(make_request(turnos))

    assert result.altered_markers == ["/hallazgos/0/hecho"]
    assert result.content["hallazgos"][0]["hecho"] == "[Persona_1] salió"
    assert result.content["hallazgos"][0]["cita_a"]["texto"] == "Casilda Roncancio salió"
