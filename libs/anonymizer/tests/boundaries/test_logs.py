"""Logs del módulo (paso 11; BR2.3, BR5.4): solo los campos permitidos, nunca texto ni claves."""

import logging
import re

import pytest
from veridicus_contracts.model_calls import ModelCallError

from tests.support import (
    KEY_CANARY,
    TESTIMONY_CANARY,
    load_anthropic,
    make_harness,
    make_request,
    ok_response,
)

# Campos de BR2.3 que el módulo registra (run_id y la ranura de reintento no existen aquí).
ALLOWED_FIELDS = {
    "outcome",
    "role",
    "slot",
    "provider",
    "model",
    "profile",
    "replacements",
    "tokens_in",
    "tokens_out",
    "duration_ms",
}
FIELD = re.compile(r"(\w+)=(\S*)")
REPLACEMENTS = re.compile(r"none|[A-ZÁÉÍÓÚÑ]+:[0-9]+(,[A-ZÁÉÍÓÚÑ]+:[0-9]+)*")
TURNOS = [
    {"turno": 1, "hablante": "TES", "texto": f"Vi a {TESTIMONY_CANARY} cerca de Puerto Altamira."},
]


def _module_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name.startswith("veridicus_anonymizer")]


@pytest.mark.parametrize(
    ("fixture", "outcome"),
    [
        (None, "ok"),
        ("error_503", "ProviderError"),
        ("refusal", "ContentBlocked"),
        ("max_tokens", "InvalidOutput"),
    ],
)
def test_every_module_log_line_carries_only_the_allowed_fields(
    fixture: str | None, outcome: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    response = ok_response() if fixture is None else load_anthropic(fixture)
    harness = make_harness(response)

    try:
        harness.anonymizer.generate(make_request(TURNOS))
    except ModelCallError:
        pass  # el error tipado es de la prueba de las ramas; aquí solo se miran los logs

    lines = _module_lines(caplog)
    assert len(lines) == 1, "una sola línea por llamada"
    line = lines[0]
    pairs = FIELD.findall(line)
    assert {name for name, _ in pairs} == ALLOWED_FIELDS
    assert line == "generate " + " ".join(f"{n}={v}" for n, v in pairs), "ningún texto suelto"
    values = dict(pairs)
    assert REPLACEMENTS.fullmatch(values["replacements"])
    assert values["replacements"] != "none", "hubo reemplazos y se cuentan por categoría"
    assert values["outcome"] == outcome


def test_a_call_that_fails_before_sending_logs_its_outcome_without_a_call(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    harness = make_harness(ok_response(), env={})

    with pytest.raises(ModelCallError):
        harness.anonymizer.generate(make_request(TURNOS))

    values = dict(FIELD.findall(_module_lines(caplog)[0]))
    assert values["outcome"] == "AnonymizerUnavailable"
    assert (values["tokens_in"], values["tokens_out"], values["replacements"]) == ("0", "0", "none")


def test_no_log_line_from_any_logger_carries_a_canary_or_the_url(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    harness = make_harness(ok_response())

    harness.anonymizer.generate(make_request(TURNOS))

    assert caplog.records, "el módulo registra su línea"
    for record in caplog.records:
        text = record.getMessage()
        assert KEY_CANARY not in text and TESTIMONY_CANARY not in text
        assert "api.anthropic.com" not in text
