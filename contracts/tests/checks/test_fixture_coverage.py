"""Cobertura de fixtures por regla de nivel 0 (security-design §4.10, NFR12.1, BR1.6).

`checks/fixture_coverage.py` exige un fixture `accept` y uno `reject` por cada regla de U1 que se prueba con
fixtures, y falla si un `reject` no falla o falla por otra regla (otra palabra clave del validador que las
que la regla declara). Quedan fuera BR5.2 a BR5.6 (solo la forma, BR5.8), BR1.5, BR1.8 y BR12.2 (revisión
del PR).
"""

import copy
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

BASE = "analyzer/v1/fixtures/"
REGLA = {"BR3.5": frozenset({"required"})}


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.fixture_coverage", "T18, paso 19")


def _poner(raiz: Path, nombre: str, documento: Any) -> None:
    ruta = raiz / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(documento, ensure_ascii=False), encoding="utf-8")


def _aceptado() -> dict[str, Any]:
    return copy.deepcopy(load_contract(BASE + "entrada.valid.yaml"))


def _rechazado() -> dict[str, Any]:
    return copy.deepcopy(load_contract(BASE + "entrada.corpus-sin-consentimiento.yaml"))


def _arbol(raiz: Path) -> Path:
    _poner(raiz, BASE + "a.json", _aceptado())
    _poner(raiz, BASE + "r.json", _rechazado())
    return raiz


def test_cada_regla_de_fixtures_tiene_su_accept_y_su_reject_en_el_repositorio(guardia: ModuleType) -> None:
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    # No pasa en vacío: cada regla exigida tiene al menos un reject real, y los accept existen.
    rechazos = {f["reject_reason"] for _, f in guardia.fixtures(CONTRACTS_ROOT) if f["expectation"] == "reject"}
    assert set(guardia.REGLAS) <= rechazos
    assert len(guardia.REGLAS) >= 15
    assert sum(1 for _, f in guardia.fixtures(CONTRACTS_ROOT) if f["expectation"] == "accept") >= 10


def test_las_exclusiones_son_las_de_4_10_y_no_se_exigen(guardia: ModuleType) -> None:
    assert set(guardia.EXCLUIDAS) == {"BR5.2", "BR5.3", "BR5.4", "BR5.5", "BR5.6", "BR1.5", "BR1.8", "BR12.2"}
    assert not set(guardia.EXCLUIDAS) & set(guardia.REGLAS)
    assert all(re.fullmatch(r"(BR|NFR|NFRD-U)[0-9.\-]+", regla) for regla in guardia.REGLAS)
    assert all(causas for causas in guardia.REGLAS.values())


def test_un_arbol_con_su_accept_y_su_reject_pasa(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(_arbol(tmp_path), reglas=REGLA) == []


def test_un_accept_de_otro_contrato_de_la_misma_familia_basta(guardia: ModuleType, tmp_path: Path) -> None:
    raiz = tmp_path
    _poner(raiz, BASE + "r.json", _rechazado())
    salida = copy.deepcopy(load_contract(BASE + "salida.valid.yaml"))
    _poner(raiz, BASE + "s.json", salida)
    assert guardia.comprobar(raiz, reglas=REGLA) == []
    # Una familia distinta no sirve.
    ajeno = copy.deepcopy(load_contract("model_calls/fixtures/model-call.valid.yaml"))
    (raiz / BASE / "s.json").unlink()
    _poner(raiz, "model_calls/fixtures/m.json", ajeno)
    assert guardia.comprobar(raiz, reglas=REGLA) == ["BR3.5: falta un fixture accept (NFR12.1, §4.10)"]


def test_falta_el_accept_o_el_reject_se_dice_por_regla(guardia: ModuleType, tmp_path: Path) -> None:
    _poner(tmp_path, BASE + "r.json", _rechazado())
    assert guardia.comprobar(tmp_path, reglas=REGLA) == ["BR3.5: falta un fixture accept (NFR12.1, §4.10)"]
    otro = tmp_path / "otro"
    _poner(otro, BASE + "a.json", _aceptado())
    assert guardia.comprobar(otro, reglas=REGLA) == ["BR3.5: falta un fixture reject (NFR12.1, §4.10)"]
    assert guardia.comprobar(tmp_path / "vacio", reglas={"BR3.5": frozenset({"required"}), "BR3.1": frozenset({"required"})}) == [
        "BR3.1: falta un fixture accept (NFR12.1, §4.10)",
        "BR3.1: falta un fixture reject (NFR12.1, §4.10)",
        "BR3.5: falta un fixture accept (NFR12.1, §4.10)",
        "BR3.5: falta un fixture reject (NFR12.1, §4.10)",
    ]


def test_un_reject_que_no_falla_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    disfrazado = _aceptado()
    disfrazado.update(expectation="reject", reject_reason="BR3.5")
    _poner(tmp_path, BASE + "disfrazado.json", disfrazado)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/disfrazado.json: el reject no falla (BR3.5, NFR12.1)"
    ]


def test_un_reject_que_falla_por_otra_regla_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    # Un reject cuya única causa es una palabra clave que la regla no declara (`enum`, no `required`).
    solo_enum = _aceptado()
    solo_enum.update(expectation="reject", reject_reason="BR3.5")
    solo_enum["payload"]["modo"] = "otro"
    _poner(tmp_path, BASE + "solo_enum.json", solo_enum)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/solo_enum.json: el reject falla por otra regla (BR3.5, NFR12.1)"
    ]
    # Si además falla por la causa de la regla, basta: el fixture ejercita la regla.
    ambos = _rechazado()
    ambos["payload"]["modo"] = "otro"
    _poner(tmp_path, BASE + "ambos.json", ambos)
    assert len(guardia.comprobar(tmp_path, reglas=REGLA)) == 1


def test_un_accept_que_no_se_acepta_es_rojo(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    roto = _aceptado()
    roto["payload"]["modo"] = "otro"
    _poner(tmp_path, BASE + "roto.json", roto)
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/roto.json: el accept no se acepta (NFR12.1)"
    ]


def test_contrato_desconocido_y_fixture_ilegible_son_problemas(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    raro = _aceptado()
    raro["contract"] = "C99.nada"
    _poner(tmp_path, BASE + "raro.json", raro)
    (tmp_path / BASE / "roto.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path, reglas=REGLA) == [
        "analyzer/v1/fixtures/raro.json: contrato desconocido (NFR12.1)",
        "analyzer/v1/fixtures/roto.yaml: fixture ilegible (NFR12.1)",
    ]


def test_lo_que_no_es_un_fixture_o_no_declara_su_regla_se_ignora(guardia: ModuleType, tmp_path: Path) -> None:
    _arbol(tmp_path)
    _poner(tmp_path, BASE + "lista.json", [1, 2])
    _poner(tmp_path, BASE + "suelto.json", {"a": 1})
    sin_razon = _rechazado()
    del sin_razon["reject_reason"]
    _poner(tmp_path, BASE + "sin_razon.json", sin_razon)
    ajena = _rechazado()
    ajena["reject_reason"] = "BR1.5"
    _poner(tmp_path, BASE + "ajena.json", ajena)
    (tmp_path / BASE / "huella.sha256").write_text("abc\n", encoding="utf-8")
    # Los directorios ajenos no se recorren.
    _poner(tmp_path, "vendor/fixtures/x.json", _aceptado())
    assert guardia.comprobar(tmp_path, reglas=REGLA) == []


def test_las_reglas_por_omision_son_las_de_regla(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(tmp_path / "vacio") != []
    assert len(guardia.comprobar(tmp_path / "vacio")) == 2 * len(guardia.REGLAS)
