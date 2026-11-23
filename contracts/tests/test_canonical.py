"""Huella JCS (RFC 8785, D14): vectores límite de la forma de los números."""

import hashlib
import math

import pytest
import rfc8785

from veridicus_contracts.canonical import canonical_bytes, sha256_jcs


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (1e21, b"1e+21"),
        (-0.0, b"0"),
        (5e-324, b"5e-324"),
        (0.1, b"0.1"),
        (1.0, b"1"),
        (1e-7, b"1e-7"),
    ],
)
def test_vectores_limite_de_numeros(valor: float, esperado: bytes) -> None:
    assert canonical_bytes(valor) == esperado


def test_las_claves_se_ordenan_y_no_hay_espacios() -> None:
    assert canonical_bytes({"b": 2, "a": [True, None, "x"]}) == b'{"a":[true,null,"x"],"b":2}'


def test_la_huella_es_el_sha256_hexadecimal_de_los_bytes_canonicos() -> None:
    objeto = {"b": 1e21, "a": "ñ"}
    esperado = hashlib.sha256(rfc8785.dumps(objeto)).hexdigest()
    assert sha256_jcs(objeto) == esperado
    assert len(esperado) == 64


def test_el_orden_de_las_claves_no_cambia_la_huella() -> None:
    assert sha256_jcs({"a": 1, "b": 2}) == sha256_jcs({"b": 2, "a": 1})


def test_json_dumps_no_reproduce_la_forma_de_los_numeros() -> None:
    # Razón de D14: la forma estándar de Python difiere de RFC 8785.
    import json

    assert json.dumps(1e-7) == "1e-07"
    assert canonical_bytes(1e-7) == b"1e-7"


def test_un_numero_no_finito_no_tiene_huella() -> None:
    with pytest.raises(rfc8785.CanonicalizationError):
        sha256_jcs({"x": math.inf})
