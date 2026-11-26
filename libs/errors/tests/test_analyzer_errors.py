"""Errores nuevos del analizador (PD-5): `code` estable y `detail` en español."""

import pytest

from veridicus_errors import (
    Cancelled,
    CliInterrupted,
    ConfigFamilyError,
    GatewayConfigError,
    InputRejected,
    RunFamilyError,
    SystemFamilyError,
    VeridicusError,
)


@pytest.mark.parametrize(
    "code",
    [
        "import.invalid_transcript",
        "session.consent_missing",
        "profile.transfer_not_authorized",
        "profile.not_approved",
    ],
)
def test_input_rejected_lleva_su_code_y_su_detail(code: str) -> None:
    with pytest.raises(VeridicusError) as capturada:
        raise InputRejected(code, "La entrada no cumple el contrato.")
    error = capturada.value
    assert isinstance(error, InputRejected)
    assert error.code == code
    assert error.detail == "La entrada no cumple el contrato."
    assert str(error) == error.detail


def test_input_rejected_rechaza_un_code_ajeno_a_br1() -> None:
    with pytest.raises(ValueError, match="BR1"):
        InputRejected("auth.forbidden", "No corresponde.")


def test_cancelled_tiene_code_fijo_y_cuelga_de_su_familia() -> None:
    assert issubclass(Cancelled, RunFamilyError)
    with pytest.raises(Cancelled) as capturada:
        raise Cancelled("La corrida se canceló.")
    assert capturada.value.code == "run.cancelled"
    assert str(capturada.value) == "La corrida se canceló."


def test_gateway_config_error_tiene_code_fijo_y_cuelga_de_su_familia() -> None:
    assert issubclass(GatewayConfigError, ConfigFamilyError)
    with pytest.raises(GatewayConfigError) as capturada:
        raise GatewayConfigError("Falta el anonimizador para un destino externo.")
    assert capturada.value.code == "config.invalid_gateway"
    assert "anonimizador" in str(capturada.value)


def test_cli_interrupted_tiene_code_fijo_y_cuelga_de_su_familia() -> None:
    assert issubclass(CliInterrupted, SystemFamilyError)
    with pytest.raises(CliInterrupted) as capturada:
        raise CliInterrupted("La ejecución se interrumpió.")
    assert capturada.value.code == "system.interrupted"
    assert str(capturada.value) == "La ejecución se interrumpió."
