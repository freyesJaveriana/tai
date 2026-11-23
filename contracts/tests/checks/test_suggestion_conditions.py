"""Guardia de las condiciones de C7 (BR4.4, E35, NFR11.5) y sus controles negativos.

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`, nunca sobre el contrato
versionado.
"""

import copy
import shutil
from pathlib import Path
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, cargar_fixture, errores_de, load_contract, validador_de

from veridicus_contracts.checks.suggestion_conditions import (
    C7,
    CONDICIONES,
    DIRECTORIO_DE_FIXTURES,
    comprobar,
    comprobar_documentos,
)

NOMBRES = [c.nombre for c in CONDICIONES]


def _documentos() -> tuple[dict[str, Any], dict[str, Any]]:
    """Copia en memoria de C7 y de sus seis fixtures negativos."""
    esquema = copy.deepcopy(load_contract(C7))
    fixtures = {
        c.fixture: copy.deepcopy(load_contract(f"{DIRECTORIO_DE_FIXTURES}/{c.fixture}"))
        for c in CONDICIONES
    }
    return esquema, fixtures


def _quitar_condicion(esquema: dict[str, Any], condicion: Any) -> None:
    bloques = esquema["allOf"]
    pending = next(b for b in bloques if b["if"]["properties"]["state"]["const"] == "pending")
    if condicion.nombre == "pending_sin_decision":
        del pending["then"]
    elif condicion.nombre == "decidida_con_quien":
        del pending["else"]
    elif condicion.vacio:
        del esquema["properties"][condicion.campo]["minLength"]
    else:
        bloques[:] = [
            b for b in bloques if b["if"]["properties"]["state"]["const"] != condicion.estado
        ]


def test_c7_versionado_declara_las_condiciones_y_cada_fixture_negativo_se_rechaza_por_su_regla() -> None:
    """Las seis condiciones (cuatro de BR4.4 y las dos de «no vacío») y C7 rechaza cada fixture."""
    assert len(CONDICIONES) == 6
    assert comprobar(CONTRACTS_ROOT) == []
    validador = validador_de(C7)
    for condicion in CONDICIONES:
        fixture = cargar_fixture(f"{DIRECTORIO_DE_FIXTURES}/{condicion.fixture}", "C7")
        assert errores_de(validador, fixture["payload"]), condicion.fixture


@pytest.mark.parametrize("condicion", CONDICIONES, ids=NOMBRES)
def test_c7_sin_una_de_las_condiciones_queda_en_rojo(condicion: Any) -> None:
    esquema, fixtures = _documentos()
    assert comprobar_documentos(esquema, fixtures) == [], "la base debe pasar"
    _quitar_condicion(esquema, condicion)
    problemas = comprobar_documentos(esquema, fixtures)
    assert problemas == [f"{condicion.nombre}: C7 no declara la condición de BR4.4"]


@pytest.mark.parametrize("condicion", CONDICIONES, ids=NOMBRES)
def test_una_condicion_sin_su_fixture_negativo_queda_en_rojo(condicion: Any) -> None:
    esquema, fixtures = _documentos()
    del fixtures[condicion.fixture]
    problemas = comprobar_documentos(esquema, fixtures)
    assert problemas == [f"{condicion.nombre}: falta el fixture negativo {condicion.fixture}"]


@pytest.mark.parametrize("condicion", CONDICIONES, ids=NOMBRES)
def test_un_fixture_negativo_que_no_ejerce_su_condicion_queda_en_rojo(condicion: Any) -> None:
    esquema, fixtures = _documentos()
    fixture = fixtures[condicion.fixture]
    fixture["expectation"] = "accept"
    fixture["payload"]["state"] = "pending" if condicion.estado != "pending" else "accepted"
    if condicion.presente and not condicion.vacio:
        del fixture["payload"][condicion.campo]
    else:
        fixture["payload"][condicion.campo] = "x"
    problemas = comprobar_documentos(esquema, fixtures)
    assert len(problemas) == 3, problemas
    assert "debe rechazarse con reject_reason BR4.4" in problemas[0]
    assert f"debe tener state {condicion.estado}" in problemas[1]
    assert f"debe {condicion.exigencia()}" in problemas[2]


def test_un_fixture_que_se_rechaza_por_otra_regla_queda_en_rojo() -> None:
    """F-02: `expectation: reject` con un `reject_reason` distinto de BR4.4 no ejerce la condición."""
    esquema, fixtures = _documentos()
    condicion = CONDICIONES[2]
    fixtures[condicion.fixture]["reject_reason"] = "BR4.1"
    problemas = comprobar_documentos(esquema, fixtures)
    assert problemas == [
        f"{condicion.nombre}: {condicion.fixture} debe rechazarse con reject_reason BR4.4"
    ]


def test_un_fixture_que_no_es_un_fixture_queda_en_rojo() -> None:
    esquema, fixtures = _documentos()
    primero = CONDICIONES[0].fixture
    fixtures[primero] = "texto suelto"
    problemas = comprobar_documentos(esquema, fixtures)
    assert problemas == [f"pending_sin_decision: el fixture {primero} no es un fixture con payload"]


def test_un_esquema_con_condiciones_incompletas_no_pasa_por_parecido() -> None:
    """`then` o `else` con solo uno de los dos campos, o un `allOf` ausente, no cuentan."""
    esquema, fixtures = _documentos()
    pending = next(b for b in esquema["allOf"] if b["if"]["properties"]["state"]["const"] == "pending")
    pending["else"] = {"required": ["decided_by"]}
    pending["then"] = "no es un objeto"
    problemas = comprobar_documentos(esquema, fixtures)
    assert [p.split(":")[0] for p in problemas] == ["pending_sin_decision", "decidida_con_quien"]
    del esquema["allOf"]
    assert len(comprobar_documentos(esquema, fixtures)) == 4


def test_comprobar_informa_de_los_archivos_ausentes_ilegibles_o_mal_formados(tmp_path: Path) -> None:
    assert "C7 ilegible o ausente" in comprobar(tmp_path)[0]
    (tmp_path / "integrity").mkdir()
    (tmp_path / C7).write_text("[1, 2", encoding="utf-8")
    assert "C7 ilegible o ausente" in comprobar(tmp_path)[0]
    (tmp_path / C7).write_text("[]", encoding="utf-8")
    assert comprobar(tmp_path) == ["C7 no es un objeto JSON"]
    shutil.copy(CONTRACTS_ROOT / C7, tmp_path / C7)
    ausentes = comprobar(tmp_path)
    assert len(ausentes) == 6
    assert all("falta el fixture negativo" in p for p in ausentes)
    carpeta = tmp_path / DIRECTORIO_DE_FIXTURES
    carpeta.mkdir(parents=True)
    (carpeta / CONDICIONES[0].fixture).write_text("{: roto", encoding="utf-8")
    problemas = comprobar(tmp_path)
    assert any("no es un fixture con payload" in p for p in problemas)
