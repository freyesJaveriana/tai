"""AUTONOMIA-05: ningún hallazgo sin sus campos obligatorios ni resultado parcial (BR3.1, BR3.6, BR4.1, BR1.7).

Las mutaciones parten de los fixtures válidos, así que la guardia no depende de los fixtures
negativos. Rojo hasta T04 (C6, F7) y T06 (C7).
"""

import copy
from pathlib import Path
from typing import Any

import pytest
from helpers import (
    cargar_fixture,
    coincide,
    errores_de,
    importar_o_fallar,
    load_text,
    ruta_de,
    validador_de,
)

SALIDA = "analyzer/v1/salida.schema.json"
C7 = "integrity/review-suggestion.v2.json"
CAMPOS_DEL_HALLAZGO = ["hecho", "tipo", "cita_a", "cita_b", "observaciones"]
MENSAJE_F7 = "La copia del contrato común no es la aprobada"


def _salida_valida() -> dict[str, Any]:
    fixture = cargar_fixture("analyzer/v1/fixtures/salida.valid.yaml", "C6.salida")
    return copy.deepcopy(fixture["payload"])


def _sugerencia_valida() -> dict[str, Any]:
    fixture = cargar_fixture("integrity/fixtures/review-suggestion/valid.pending.yaml", "C7")
    return copy.deepcopy(fixture["payload"])


def _error_sin_error(salida: dict[str, Any]) -> None:
    salida["estado"] = "error"
    salida["hallazgos"] = []


def _error_con_hallazgo(salida: dict[str, Any]) -> None:
    salida["estado"] = "error"
    salida["error"] = {"codigo": "proveedor"}


def _error_con_aclaracion(salida: dict[str, Any]) -> None:
    salida["estado"] = "error"
    salida["error"] = {"codigo": "proveedor"}
    salida["hallazgos"] = []
    salida["observaciones_conductor"] = [
        {"tipo": "aclaracion_neutra", "tema": "Lugar de la noche", "turnos": ["T2"]}
    ]


def _ok_con_error(salida: dict[str, Any]) -> None:
    salida["error"] = {"codigo": "proveedor"}


@pytest.mark.c6
@pytest.mark.parametrize("campo", CAMPOS_DEL_HALLAZGO)
def test_c6_rechaza_el_hallazgo_sin_cada_campo_obligatorio(campo: str) -> None:
    validador = validador_de(SALIDA)
    salida = _salida_valida()
    assert errores_de(validador, salida) == [], "la base válida debe aceptarse"
    del salida["hallazgos"][0][campo]
    errores = errores_de(validador, salida)
    assert any(coincide(e, ("required", "$.hallazgos[0]", f"'{campo}'")) for e in errores)


@pytest.mark.c6
@pytest.mark.parametrize(
    ("mutar", "esperado"),
    [
        pytest.param(_error_con_hallazgo, ("maxItems", "$.hallazgos", None), id="error-con-hallazgo"),
        pytest.param(
            _error_con_aclaracion,
            ("maxItems", "$.observaciones_conductor", None),
            id="error-con-aclaracion",
        ),
        pytest.param(_error_sin_error, ("required", "$", "'error'"), id="error-sin-objeto-error"),
        pytest.param(_ok_con_error, ("not", "$", None), id="ok-con-error"),
    ],
)
def test_c6_estado_error_implica_hallazgos_vacios_y_ok_no_trae_error(
    mutar: Any, esperado: tuple[str, str, str | None]
) -> None:
    """BR3.6: ningún resultado parcial cuando el analizador falla."""
    validador = validador_de(SALIDA)
    salida = _salida_valida()
    assert errores_de(validador, salida) == [], "la base válida debe aceptarse"
    mutar(salida)
    errores = errores_de(validador, salida)
    assert any(coincide(e, esperado) for e in errores), [(e.validator, e.json_path) for e in errores]


@pytest.mark.c7
@pytest.mark.parametrize("campo", CAMPOS_DEL_HALLAZGO)
def test_c7_rechaza_la_sugerencia_sin_cada_campo_obligatorio(campo: str) -> None:
    validador = validador_de(C7)
    sugerencia = _sugerencia_valida()
    assert errores_de(validador, sugerencia) == [], "la base válida debe aceptarse"
    del sugerencia[campo]
    errores = errores_de(validador, sugerencia)
    assert any(coincide(e, ("required", "$", f"'{campo}'")) for e in errores)


@pytest.mark.c7
@pytest.mark.parametrize(
    ("campo", "vacio", "esperado"),
    [
        pytest.param("hecho", "", ("minLength", "$.hecho", None), id="hecho"),
        pytest.param("tipo", "", ("enum", "$.tipo", None), id="tipo"),
        pytest.param("cita_a", {}, ("required", "$.cita_a", "'cita'"), id="cita_a"),
        pytest.param("cita_b", {}, ("required", "$.cita_b", "'cita'"), id="cita_b"),
        pytest.param("observaciones", "", ("minLength", "$.observaciones", None), id="observaciones"),
    ],
)
def test_c7_rechaza_la_sugerencia_con_un_campo_obligatorio_vacio(
    campo: str, vacio: Any, esperado: tuple[str, str, str | None]
) -> None:
    validador = validador_de(C7)
    sugerencia = _sugerencia_valida()
    assert errores_de(validador, sugerencia) == [], "la base válida debe aceptarse"
    sugerencia[campo] = vacio
    errores = errores_de(validador, sugerencia)
    assert any(coincide(e, esperado) for e in errores), [(e.validator, e.json_path) for e in errores]


@pytest.mark.c6
def test_f7_detecta_e18_una_copia_con_un_byte_cambiado(tmp_path: Path) -> None:
    """BR1.7, E18: F7 acepta la copia íntegra y la rechaza con un byte cambiado en una descripción.

    Interfaz que T04 implementa en `tests/conftest.py` (o ajusta aquí en el mismo PR):
    `check_c6_copy(carpeta: Path) -> list[str]`, lista vacía si la copia es la aprobada.
    """
    sumas = load_text("analyzer/v1/SHA256SUMS")
    conftest = importar_o_fallar("conftest", "F7 vive en tests/conftest.py (T04)")
    verificar = getattr(conftest, "check_c6_copy", None)
    if verificar is None:
        pytest.fail("F7 ausente: conftest.check_c6_copy(carpeta) -> list[str] (T04)")
    carpeta = tmp_path / "v1"
    carpeta.mkdir()
    (carpeta / "SHA256SUMS").write_text(sumas, encoding="utf-8")
    for nombre in ("entrada.schema.json", "salida.schema.json"):
        (carpeta / nombre).write_bytes(ruta_de(f"analyzer/v1/{nombre}").read_bytes())
    assert verificar(carpeta) == [], "la copia íntegra debe pasar F7"
    marca = b'"description": "'
    datos = bytearray((carpeta / "salida.schema.json").read_bytes())
    posicion = bytes(datos).find(marca)
    assert posicion >= 0, "salida.schema.json no tiene ninguna description que alterar"
    posicion += len(marca)
    datos[posicion] = ord("Y") if datos[posicion] == ord("X") else ord("X")
    (carpeta / "salida.schema.json").write_bytes(bytes(datos))
    problemas = verificar(carpeta)
    assert problemas, "F7 debe detectar la copia alterada"
    assert MENSAJE_F7 in " ".join(problemas)
