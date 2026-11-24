"""Vectores JCS `fixtures/jcs-vectors.json` (§4.14, NFR10.15, U01-T19)."""

import math
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import importar_o_fallar, load_contract, ruta_de

from veridicus_contracts.canonical import sha256_jcs

VERSIONADO = "fixtures/jcs-vectors.json"


def herramienta() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.tools.gen_jcs_vectors", "U01-T19")


def numeros(valor: Any) -> list[float]:
    if isinstance(valor, float):
        return [valor]
    if isinstance(valor, dict):
        return [n for hijo in valor.values() for n in numeros(hijo)]
    if isinstance(valor, list):
        return [n for hijo in valor for n in numeros(hijo)]
    return []


def test_hay_doscientos_vectores_con_identificador_unico() -> None:
    documento = load_contract(VERSIONADO)
    vectores = documento["vectors"]
    assert len(vectores) == 200
    assert len({v["id"] for v in vectores}) == 200
    assert len({v["sha256"] for v in vectores}) == 200


def test_los_doscientos_vectores_recalculados_coinciden() -> None:
    for vector in load_contract(VERSIONADO)["vectors"]:
        assert sha256_jcs(vector["value"]) == vector["sha256"], vector["id"]


def test_estan_los_cuatro_numeros_limite_y_hay_claves_unicode_y_anidamiento() -> None:
    vectores = load_contract(VERSIONADO)["vectors"]
    todos = [n for v in vectores for n in numeros(v["value"])]
    assert 1e21 in todos
    assert 5e-324 in todos
    assert 0.1 in todos
    assert any(n == 0 and math.copysign(1.0, n) < 0 for n in todos), "falta -0"
    claves = {k for v in vectores if isinstance(v["value"], dict) for k in v["value"]}
    assert any(not k.isascii() for k in claves)
    anidados = [
        v
        for v in vectores
        if isinstance(v["value"], dict) and any(isinstance(h, dict | list) for h in v["value"].values())
    ]
    assert anidados


def test_lo_generado_es_igual_a_lo_versionado() -> None:
    herramientas = herramienta()
    ruta = ruta_de(VERSIONADO)
    if not ruta.is_file():
        pytest.fail(f"archivo versionado ausente: {VERSIONADO}")
    generado = herramientas.serializar(herramientas.generar())
    assert generado == ruta.read_bytes()


def test_la_semilla_fija_da_bytes_identicos_en_dos_generaciones() -> None:
    herramientas = herramienta()
    primera = herramientas.serializar(herramientas.generar())
    segunda = herramientas.serializar(herramientas.generar())
    assert primera == segunda
    assert primera.endswith(b"\n")
    assert b"\r" not in primera
    assert not primera.startswith(b"\xef\xbb\xbf")
    assert load_contract(VERSIONADO)["seed"] == herramientas.SEMILLA


def test_check_sale_con_uno_sobre_una_copia_cambiada_o_ausente(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    herramientas = herramienta()
    copia = tmp_path / "jcs-vectors.json"
    copia.write_bytes(ruta_de(VERSIONADO).read_bytes())
    assert herramientas.main(["--check", "--output", str(copia)]) == 0
    capsys.readouterr()
    copia.write_bytes(copia.read_bytes().replace(b'"vec-001"', b'"vec-xxx"', 1))
    assert herramientas.main(["--check", "--output", str(copia)]) == 1
    assert "vec-001" in capsys.readouterr().out
    assert herramientas.main(["--check", "--output", str(tmp_path / "ausente.json")]) == 1


def test_sin_check_escribe_el_archivo_y_crea_su_carpeta(tmp_path: Path) -> None:
    herramientas = herramienta()
    destino = tmp_path / "nueva" / "jcs-vectors.json"
    assert herramientas.main(["--output", str(destino)]) == 0
    assert destino.read_bytes() == ruta_de(VERSIONADO).read_bytes()
    assert herramientas.main(["--check", "--output", str(destino)]) == 0
