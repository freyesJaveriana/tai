"""Errores nuevos del analizador (PD-5): `code` estable y `detail` en español."""

import pytest

from veridicus_errors import (
    CancelledError,
    CliInterruptedError,
    ConfigFamilyError,
    GatewayConfigError,
    ImportInvalidTranscriptError,
    InputRejected,
    ProfileNotApprovedError,
    ProfileTransferNotAuthorizedError,
    RunFamilyError,
    SessionConsentMissingError,
    SystemFamilyError,
)


@pytest.mark.parametrize(
    ("clase", "code"),
    [
        (ImportInvalidTranscriptError, "import.invalid_transcript"),
        (SessionConsentMissingError, "session.consent_missing"),
        (ProfileTransferNotAuthorizedError, "profile.transfer_not_authorized"),
        (ProfileNotApprovedError, "profile.not_approved"),
    ],
)
def test_input_rejected_agrupa_las_clases_de_br1_con_su_code_y_su_detail(
    clase: type[Exception], code: str
) -> None:
    assert clase in InputRejected
    with pytest.raises(InputRejected) as capturada:
        raise clase("La entrada no cumple el contrato.")
    assert capturada.value.code == code  # type: ignore[attr-defined]  # motivo: la tupla agrupa clases con code
    assert str(capturada.value) == "La entrada no cumple el contrato."


def test_input_rejected_no_agrupa_otras_clases() -> None:
    assert len(InputRejected) == 4


def test_cancelled_tiene_code_fijo_y_cuelga_de_su_familia() -> None:
    assert issubclass(CancelledError, RunFamilyError)
    with pytest.raises(CancelledError) as capturada:
        raise CancelledError("La corrida se canceló.")
    assert capturada.value.code == "run.cancelled"
    assert str(capturada.value) == "La corrida se canceló."


def test_gateway_config_error_tiene_code_fijo_y_cuelga_de_su_familia() -> None:
    assert issubclass(GatewayConfigError, ConfigFamilyError)
    with pytest.raises(GatewayConfigError) as capturada:
        raise GatewayConfigError("Falta el anonimizador para un destino externo.")
    assert capturada.value.code == "config.invalid_gateway"
    assert "anonimizador" in str(capturada.value)


def test_cli_interrupted_tiene_code_fijo_y_cuelga_de_su_familia() -> None:
    assert issubclass(CliInterruptedError, SystemFamilyError)
    with pytest.raises(CliInterruptedError) as capturada:
        raise CliInterruptedError("La ejecución se interrumpió.")
    assert capturada.value.code == "system.interrupted"
    assert str(capturada.value) == "La ejecución se interrumpió."
