"""Forma del catálogo de errores v2 (NFR10.3, BR7.2; paso 9, capa 1).

Cada `code` lleva un solo `status`, su clase, su unidad y `http`; `limits.exceeded` es 413 (D16);
los de arranque y de log no llevan estado.
"""

import re
from typing import Any

import pytest
from helpers import load_contract

CATALOGO = "errors/error-codes.v2.yaml"
CODE = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*$")
CLASE = re.compile(r"^[A-Z][A-Za-z0-9]*Error$")
UNIDADES = {f"U{n}" for n in range(1, 14)}
ARRANQUE_Y_LOG = ("config.invalid_profile", "config.invalid_limit", "run.publish_failed")


def _codes() -> dict[str, dict[str, Any]]:
    catalogo = load_contract(CATALOGO)
    assert catalogo["version"] == 2
    assert set(catalogo) == {"version", "codes"}
    codes: dict[str, dict[str, Any]] = catalogo["codes"]
    assert codes, "el catálogo no declara ningún code"
    return codes


def test_forma_de_cada_entrada() -> None:
    for code, entrada in _codes().items():
        assert CODE.match(code), f"{code}: nombre fuera de <familia>.<motivo>"
        assert set(entrada) <= {"status", "class", "unit", "http", "c6"}, f"{code}: {set(entrada)}"
        assert {"class", "unit", "http"} <= set(entrada), f"{code}: faltan campos"
        assert CLASE.match(entrada["class"]), f"{code}: clase {entrada['class']!r}"
        assert entrada["unit"] in UNIDADES, f"{code}: unidad {entrada['unit']!r}"
        assert isinstance(entrada["http"], bool), f"{code}: http debe ser booleano"


def test_un_solo_status_por_code_y_solo_si_es_http() -> None:
    for code, entrada in _codes().items():
        if entrada["http"]:
            status = entrada.get("status")
            assert isinstance(status, int) and not isinstance(status, bool), f"{code}: sin status"
            assert 400 <= status <= 599, f"{code}: status {status}"
        else:
            assert "status" not in entrada, f"{code}: http false no lleva status"


def test_limits_exceeded_es_413() -> None:
    assert _codes()["limits.exceeded"]["status"] == 413


@pytest.mark.parametrize("code", ARRANQUE_Y_LOG)
def test_arranque_y_log_no_son_http(code: str) -> None:
    entrada = _codes()[code]
    assert entrada["http"] is False
    assert "status" not in entrada


def test_codes_pedidos_por_las_otras_unidades() -> None:
    codes = _codes()
    assert codes["route.not_found"]["status"] == 404
    assert codes["report.view_outdated"]["status"] == 409
    assert codes["session.blocked"]["status"] == 409
    assert codes["import.invalid_type"]["status"] == 415
    assert codes["research.invalid_type"]["status"] == 415


def test_clases_y_codes_c6_no_se_repiten() -> None:
    codes = _codes()
    clases = [entrada["class"] for entrada in codes.values()]
    assert len(clases) == len(set(clases)), "dos code comparten clase"
    c6 = [entrada["c6"] for entrada in codes.values() if "c6" in entrada]
    assert len(c6) == len(set(c6)), "dos code traducen el mismo error.codigo de C6"
    assert codes["analysis.provider"]["c6"] == "proveedor"
