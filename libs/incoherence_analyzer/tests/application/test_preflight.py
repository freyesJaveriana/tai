"""Validación previa de la entrada (BR1.1 a BR1.4): todo se comprueba antes de llamar.

Cada rechazo lleva su `code` y deja el gateway sin ninguna petición. Cada caso tiene su control
positivo, que sí se analiza.
"""

import copy
from pathlib import Path
from typing import Any

import pytest
from veridicus_errors import (
    ImportInvalidTranscriptError,
    InputRejected,
    ProfileNotApprovedError,
    ProfileTransferNotAuthorizedError,
    SessionConsentMissingError,
)

from tests.application.profiles_support import local_profile
from tests.support import (
    ScriptedGateway,
    default_turns,
    finding,
    make_config,
    make_entrada,
)
from veridicus_incoherence_analyzer.api import analyze
from veridicus_incoherence_analyzer.application import preflight

CONSENT: dict[str, Any] = {
    "tipo": "persona",
    "version_texto": "1.0",
    "autoriza_transferencia": True,
    "autoriza_voz": False,
    "autoriza_conservar_audio": False,
    "requiere_mandato": False,
    "registrado_en": "2026-11-26T12:00:00Z",
}


def _with(origen: str, consentimiento: dict[str, Any] | None = None) -> dict[str, Any]:
    entrada = make_entrada()
    entrada["transcripcion"]["origen"] = origen
    if consentimiento is not None:
        entrada["transcripcion"]["consentimiento"] = consentimiento
    return entrada


def _rejected(entrada: dict[str, Any], expected: type[Exception]) -> None:
    gateway = ScriptedGateway(findings=[finding()])
    with pytest.raises(expected):
        analyze(entrada, make_config(), gateway)
    assert gateway.requests == [], "0 llamadas (AC12.1.3 b)"


def test_a_valid_input_is_accepted_and_called() -> None:
    gateway = ScriptedGateway(findings=[finding()])

    salida = analyze(make_entrada(), make_config(), gateway)

    assert salida["estado"] == "ok"
    assert gateway.requests


# --- BR1.1: el esquema C6 ------------------------------------------------------------------------


@pytest.mark.parametrize("campo", ["contrato", "transcripcion", "modo", "perfil"])
def test_a_missing_required_field_is_rejected(campo: str) -> None:
    entrada = make_entrada()
    del entrada[campo]

    _rejected(entrada, ImportInvalidTranscriptError)


@pytest.mark.parametrize("campo", ["entrevista", "origen", "turnos"])
def test_a_missing_required_field_of_the_transcription_is_rejected(campo: str) -> None:
    entrada = make_entrada()
    del entrada["transcripcion"][campo]

    _rejected(entrada, ImportInvalidTranscriptError)


@pytest.mark.parametrize("campo", ["n", "hablante", "texto"])
def test_a_missing_required_field_of_a_turn_is_rejected(campo: str) -> None:
    entrada = make_entrada()
    del entrada["transcripcion"]["turnos"][0][campo]

    _rejected(entrada, ImportInvalidTranscriptError)


@pytest.mark.parametrize(
    ("ruta", "valor"),
    [
        (("contrato",), "2.0.0"),
        (("modo",), "continuo"),
        (("transcripcion", "origen"), "inventado"),
        (("transcripcion", "turnos", 0, "hablante"), "OTRO"),
        (("transcripcion", "turnos", 0, "estado"), "oculto"),
        (("transcripcion", "turnos", 0, "n"), 0),
        (("transcripcion", "turnos"), []),
        (("transcripcion", "entrevista"), ""),
    ],
)
def test_an_enum_or_a_value_outside_the_schema_is_rejected(
    ruta: tuple[str | int, ...], valor: object
) -> None:
    entrada = make_entrada()
    target: Any = entrada
    for part in ruta[:-1]:
        target = target[part]
    target[ruta[-1]] = valor

    _rejected(entrada, ImportInvalidTranscriptError)


def test_an_extra_property_is_rejected() -> None:
    entrada = make_entrada()
    entrada["veracidad"] = "alta"

    _rejected(entrada, ImportInvalidTranscriptError)


def test_an_input_that_is_not_an_object_is_rejected() -> None:
    gateway = ScriptedGateway()

    with pytest.raises(ImportInvalidTranscriptError):
        analyze(["no", "es", "un", "objeto"], make_config(), gateway)  # type: ignore[arg-type]  # motivo: entrada inválida a propósito
    assert gateway.requests == []


def test_the_message_names_the_field_and_never_the_testimony() -> None:
    entrada = make_entrada()
    entrada["transcripcion"]["turnos"][1]["hablante"] = "TESTIMONIO-SECRETO"

    with pytest.raises(ImportInvalidTranscriptError) as caught:
        analyze(entrada, make_config(), ScriptedGateway())

    assert "/transcripcion/turnos/1" in str(caught.value)
    assert "TESTIMONIO-SECRETO" not in str(caught.value)


# --- BR1.1: los límites de C25 --------------------------------------------------------------------


def test_a_turn_over_the_character_limit_is_rejected_and_the_limit_itself_is_accepted() -> None:
    turns = default_turns()
    turns[1]["texto"] = "a" * 20001
    _rejected(make_entrada(turns), ImportInvalidTranscriptError)

    turns[1]["texto"] = "a" * 20000
    salida = analyze(make_entrada(turns), make_config(), ScriptedGateway())
    assert salida["estado"] == "ok"


def test_a_transcript_over_the_turn_limit_is_rejected_and_the_limit_itself_is_accepted() -> None:
    def many(count: int) -> list[dict[str, Any]]:
        return [{"n": n, "hablante": "TEST", "texto": "dato"} for n in range(1, count + 1)]

    _rejected(make_entrada(many(2001)), ImportInvalidTranscriptError)

    salida = analyze(make_entrada(many(2000)), make_config(), ScriptedGateway())
    assert salida["estado"] == "ok"


def test_a_transcript_over_the_total_character_limit_is_rejected() -> None:
    def spread(count: int) -> list[dict[str, Any]]:
        return [{"n": n, "hablante": "TEST", "texto": "a" * 20000} for n in range(1, count + 1)]

    _rejected(make_entrada(spread(13)), ImportInvalidTranscriptError)  # 260 000 > 250 000

    salida = analyze(make_entrada(spread(12)), make_config(), ScriptedGateway())  # 240 000
    assert salida["estado"] == "ok"


def test_a_repeated_turn_number_is_rejected() -> None:
    turns = default_turns()
    turns[2]["n"] = 2

    _rejected(make_entrada(turns), ImportInvalidTranscriptError)


# --- BR1.2: el consentimiento según el origen --------------------------------------------------


@pytest.mark.parametrize("origen", ["corpus", "guiada"])
def test_corpus_or_guided_without_consent_is_rejected_with_its_own_code(origen: str) -> None:
    _rejected(_with(origen), SessionConsentMissingError)


@pytest.mark.parametrize("origen", ["corpus", "guiada"])
def test_corpus_or_guided_with_consent_is_analyzed(origen: str) -> None:
    salida = analyze(_with(origen, CONSENT), make_config(), ScriptedGateway())

    assert salida["estado"] == "ok"


def test_synthetic_without_consent_is_analyzed() -> None:
    salida = analyze(_with("sintetico"), make_config(), ScriptedGateway())

    assert salida["estado"] == "ok"


def test_the_missing_consent_does_not_hide_another_schema_error() -> None:
    entrada = _with("corpus")
    entrada["modo"] = "continuo"

    _rejected(entrada, ImportInvalidTranscriptError)


def test_a_consent_block_that_is_incomplete_is_a_schema_error_and_not_a_missing_consent() -> None:
    incomplete = {key: value for key, value in CONSENT.items() if key != "tipo"}

    _rejected(_with("corpus", incomplete), ImportInvalidTranscriptError)


# --- BR1.3: la transferencia ---------------------------------------------------------------------


def test_an_external_profile_without_authorized_transfer_is_rejected() -> None:
    refused = {**CONSENT, "autoriza_transferencia": False}

    _rejected(_with("corpus", refused), ProfileTransferNotAuthorizedError)


def test_an_external_profile_with_authorized_transfer_is_analyzed() -> None:
    salida = analyze(_with("corpus", CONSENT), make_config(), ScriptedGateway())

    assert salida["estado"] == "ok"


def test_a_synthetic_input_without_consent_does_not_restrict_the_profile() -> None:
    salida = analyze(_with("sintetico"), make_config(), ScriptedGateway())

    assert salida["estado"] == "ok"


def test_an_all_local_profile_does_not_need_the_transfer(tmp_path: Path) -> None:
    config = local_profile(tmp_path)
    entrada = {
        **_with("corpus", {**CONSENT, "autoriza_transferencia": False}),
        "perfil": "todo-local",
    }

    preflight.check(entrada, config)  # no lanza


def test_a_fallback_provider_that_is_external_needs_the_transfer(tmp_path: Path) -> None:
    config = local_profile(tmp_path, fallback=True)
    refused = {
        **_with("corpus", {**CONSENT, "autoriza_transferencia": False}),
        "perfil": "todo-local",
    }

    with pytest.raises(ProfileTransferNotAuthorizedError):
        preflight.check(refused, config)


# --- BR1.4: el perfil ----------------------------------------------------------------------------


@pytest.mark.parametrize("nombre", ["perfil-inexistente", "todo-local", "DEMO-ANTHROPIC"])
def test_a_profile_that_is_not_the_one_of_the_configuration_is_rejected(nombre: str) -> None:
    entrada = make_entrada()
    entrada["perfil"] = nombre

    _rejected(entrada, ProfileNotApprovedError)


# --- BR1.5 diferido: el modo incremental -----------------------------------------------------------


def test_the_incremental_mode_is_rejected_in_this_version() -> None:
    entrada = make_entrada()
    entrada.update({"modo": "incremental", "desde_turno": 2, "hasta_turno": 4})

    _rejected(entrada, ImportInvalidTranscriptError)


# --- El orden de F1 y la tupla de InputRejected ------------------------------------------------------


def test_the_first_failure_decides_the_code_in_the_order_of_f1() -> None:
    entrada = _with("corpus", {**CONSENT, "autoriza_transferencia": False})
    entrada["perfil"] = "perfil-inexistente"
    entrada["transcripcion"]["turnos"][1]["texto"] = "a" * 20001

    with pytest.raises(ImportInvalidTranscriptError):  # BR1.1 antes que BR1.3 y BR1.4
        analyze(copy.deepcopy(entrada), make_config(), ScriptedGateway())
    entrada["transcripcion"]["turnos"][1]["texto"] = "a" * 20000
    with pytest.raises(ProfileTransferNotAuthorizedError):  # BR1.3 antes que BR1.4
        analyze(copy.deepcopy(entrada), make_config(), ScriptedGateway())
    entrada["transcripcion"]["consentimiento"]["autoriza_transferencia"] = True
    with pytest.raises(ProfileNotApprovedError):
        analyze(copy.deepcopy(entrada), make_config(), ScriptedGateway())


def test_every_rejection_is_one_of_the_classes_of_input_rejected() -> None:
    assert {
        ImportInvalidTranscriptError,
        SessionConsentMissingError,
        ProfileTransferNotAuthorizedError,
        ProfileNotApprovedError,
    } == set(InputRejected)
