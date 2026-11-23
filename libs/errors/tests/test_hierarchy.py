"""Jerarquía de excepciones: clases sin lógica, un `code` único por clase (BR7.4)."""

import inspect

import pytest

import veridicus_errors
from veridicus_errors import (
    LimitsExceededError,
    LimitsFamilyError,
    SessionBlockedError,
    VeridicusError,
)


def _hojas() -> list[type[VeridicusError]]:
    return [
        clase
        for _, clase in inspect.getmembers(veridicus_errors, inspect.isclass)
        if issubclass(clase, VeridicusError) and "code" in vars(clase)
    ]


def test_toda_clase_cuelga_de_la_raiz() -> None:
    assert issubclass(LimitsExceededError, LimitsFamilyError)
    assert issubclass(LimitsFamilyError, VeridicusError)
    assert issubclass(VeridicusError, Exception)


def test_code_unico_y_con_formato() -> None:
    codes = [clase.code for clase in _hojas()]
    assert len(codes) > 50
    assert len(codes) == len(set(codes)), "dos clases comparten code"
    for code in codes:
        familia, _, motivo = code.partition(".")
        assert familia
        assert motivo


def test_clases_sin_logica() -> None:
    for clase in _hojas():
        propios = {nombre for nombre in vars(clase) if not nombre.startswith("__")}
        assert propios == {"code"}, f"{clase.__name__} define {propios - {'code'}}"


def test_status_no_se_expone_en_la_clase() -> None:
    for clase in _hojas():
        assert not hasattr(clase, "status"), clase.__name__
        assert not hasattr(clase, "http_status"), clase.__name__


def test_las_bases_no_llevan_code() -> None:
    assert not hasattr(VeridicusError, "code")
    assert "code" not in vars(LimitsFamilyError)


def test_se_lanza_y_se_captura_por_familia() -> None:
    with pytest.raises(VeridicusError) as capturada:
        raise SessionBlockedError("sesión bloqueada")
    assert isinstance(capturada.value, SessionBlockedError)
    assert capturada.value.code == "session.blocked"
