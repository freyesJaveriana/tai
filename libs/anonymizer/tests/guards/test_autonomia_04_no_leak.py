"""AUTONOMIA-04, ausencia de fugas (E6, E34; BR1.8, BR2.3, BR5.4, R-07).

Un canary va en el testimonio y otro en el valor de la clave de API. Se buscan en la petición
cruda (fuera de la cabecera de autenticación), en los logs, en el `ModelCall`, en el resultado y
en toda la cadena `__cause__`/`__context__` de cada excepción, con éxito y en cada rama de error.
"""

import logging
from collections.abc import Callable

import pytest
from veridicus_contracts.model_calls import ModelCallError

from tests.support import (
    AUTH_HEADER,
    KEY_CANARY,
    TESTIMONY_CANARY,
    boom,
    default_env,
    exception_texts,
    load_anthropic,
    make_harness,
    make_request,
    ok_response,
    outgoing_views,
)
from veridicus_anonymizer.application import generate as generate_module
from veridicus_anonymizer.domain import detection, masking
from veridicus_anonymizer.testing.fake_transport import FakeResponse

TURNOS = [
    {"turno": 1, "hablante": "TES", "texto": f"Vi a {TESTIMONY_CANARY} cerca de Puerto Altamira."},
    {"turno": 2, "hablante": "TES", "texto": "Eso fue un martes."},
]
# Cada rama: qué se sustituye y una fábrica de la respuesta (se construye dentro de la prueba).
BRANCHES: dict[str, tuple[Callable[[pytest.MonkeyPatch], None], Callable[[], FakeResponse]]] = {
    "exito": (lambda mp: None, ok_response),
    "error_503": (lambda mp: None, lambda: load_anthropic("error_503")),
    "no_es_json": (lambda mp: None, lambda: load_anthropic("not_json")),
    "redireccion_307": (lambda mp: None, lambda: load_anthropic("redirect_307")),
    "regla_que_lanza": (lambda mp: mp.setattr(detection, "apply_rules", boom), ok_response),
    "serializacion_que_lanza": (
        lambda mp: mp.setattr(masking, "serialize_messages", boom),
        ok_response,
    ),
    "restauracion_que_lanza": (
        lambda mp: mp.setattr(generate_module, "restore", boom),
        ok_response,
    ),
}


def test_the_key_canary_travels_only_in_the_authentication_header_of_the_raw_request() -> None:
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(TURNOS))

    raw = harness.transport.requests[0]
    # Control positivo: la clave está donde debe, en la petición cruda.
    assert raw.headers[AUTH_HEADER] == KEY_CANARY
    # Control negativo: no está en la URL, el cuerpo ni ninguna otra cabecera.
    assert KEY_CANARY not in raw.path
    assert KEY_CANARY not in raw.host
    assert KEY_CANARY.encode() not in raw.body
    for name, value in raw.headers.items():
        if name.lower() != AUTH_HEADER:
            assert KEY_CANARY not in value, name
    # R-07: la clave solo se oculta al representar la petición capturada.
    assert KEY_CANARY not in repr(raw)
    assert KEY_CANARY not in repr(harness.transport)


def test_the_testimony_canary_never_reaches_the_outgoing_request() -> None:
    harness = make_harness(ok_response())
    harness.anonymizer.generate(make_request(TURNOS))

    assert harness.transport.request_count == 1
    for view in outgoing_views(harness.transport):
        assert TESTIMONY_CANARY not in view
        assert "Canaryx" not in view


def test_success_leaves_no_canary_in_logs_model_call_or_result(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    harness = make_harness(ok_response())

    result = harness.anonymizer.generate(make_request(TURNOS))

    for canary in (TESTIMONY_CANARY, KEY_CANARY):
        assert canary not in caplog.text
        assert canary not in repr(result.call)
        assert canary not in repr(result)
        assert canary not in str(result.content)


@pytest.mark.parametrize("branch", list(BRANCHES), ids=list(BRANCHES))
def test_no_canary_in_logs_or_in_the_exception_chain_in_any_branch(
    branch: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    prepare, make_response = BRANCHES[branch]
    prepare(monkeypatch)
    harness = make_harness(make_response(), env=default_env())

    error: BaseException | None = None
    try:
        harness.anonymizer.generate(make_request(TURNOS))
    except ModelCallError as caught:
        error = caught

    if branch == "exito":
        assert error is None
    else:
        assert error is not None, "la rama debía terminar en un error tipado de C13"
    texts = list(exception_texts(error)) if error is not None else []
    texts.append(caplog.text)
    for canary in (TESTIMONY_CANARY, KEY_CANARY):
        for text in texts:
            assert canary not in text
