"""Guardia de referencias cerradas (security-design §4.2, NFR10.5, BR12.3, E36).

`checks/refs.py` falla ante un `$ref` entre archivos que no empieza por `/veridicus/contracts/`, ante un
esquema `http:`, `https:` o `file:` y ante una ruta relativa como
`contracts/analyzer/v1/salida.schema.json#/$defs/cita`. Los `$ref` locales (`#/...`) son válidos.
"""

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

CANONICA = "/veridicus/contracts/analyzer/v1/salida#/$defs/cita"
E36 = "contracts/analyzer/v1/salida.schema.json#/$defs/cita"


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.refs", "T18, paso 19")


def _con_ref(ref: str) -> dict[str, Any]:
    return {"properties": {"cita": {"$ref": ref}}}


def test_los_contratos_versionados_resuelven_sus_referencias_por_id_canonico(
    guardia: ModuleType,
) -> None:
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    # No pasa en vacío: C1, C18 y C19 sí traen referencias entre archivos por `$id` canónico.
    assert "/veridicus/contracts/analyzer/v1/salida#" in str(load_contract("api/console.v2.yaml"))
    assert "/veridicus/contracts/profiles/" in str(
        load_contract("profiles/profiles.schema.v1.yaml")
    )
    assert "/veridicus/contracts/cli/report.schema.v2#" in str(load_contract("api/console.v2.yaml"))


def test_la_referencia_canonica_y_las_locales_son_validas(guardia: ModuleType) -> None:
    assert guardia.comprobar_documento(_con_ref(CANONICA), "c.json") == []
    assert guardia.comprobar_documento(_con_ref("#/$defs/cita"), "c.json") == []
    assert guardia.comprobar_documento({"$ref": "#"}, "c.json") == []


def test_e36_la_ruta_relativa_de_archivo_es_rojo_con_su_puntero(guardia: ModuleType) -> None:
    problemas = guardia.comprobar_documento(_con_ref(E36), "analyzer/v1/x.schema.json")
    esperado = (
        "analyzer/v1/x.schema.json#/properties/cita: "
        "$ref relativo o fuera de /veridicus/contracts/ (NFR10.5, E36)"
    )
    assert problemas == [esperado]


@pytest.mark.parametrize(
    "ref",
    [
        "https://example.invalid/esquema#/$defs/a",
        "http://example.invalid/esquema",
        "file:///etc/passwd",
        "HTTPS://example.invalid/mayusculas",
    ],
)
def test_un_esquema_de_red_o_de_archivo_es_rojo(guardia: ModuleType, ref: str) -> None:
    problemas = guardia.comprobar_documento(_con_ref(ref), "c.json")
    assert problemas == [
        "c.json#/properties/cita: $ref con esquema http, https o file (NFR10.5, E36)"
    ]


@pytest.mark.parametrize(
    "ref", ["otro.schema.json", "../x#/a", "/veridicus/otro/a", "/veridicus/contractsX/a"]
)
def test_otras_rutas_que_no_son_la_canonica_son_rojo(guardia: ModuleType, ref: str) -> None:
    problemas = guardia.comprobar_documento(_con_ref(ref), "c.json")
    assert len(problemas) == 1 and "fuera de /veridicus/contracts/" in problemas[0]


def test_el_mensaje_nombra_archivo_y_puntero_pero_no_el_valor(guardia: ModuleType) -> None:
    documento = {"a/b": {"c~d": [{"$ref": "secreto-que-no-debe-salir.json"}]}}
    problemas = guardia.comprobar_documento(documento, "c.json")
    assert len(problemas) == 1
    assert problemas[0].startswith("c.json#/a~1b/c~0d/0:")
    assert "secreto" not in problemas[0]


def test_un_ref_que_no_es_texto_se_ignora(guardia: ModuleType) -> None:
    assert guardia.comprobar_documento({"properties": {"$ref": {"type": "string"}}}, "c.json") == []


def test_comprobar_recorre_contratos_y_salta_vendor_fixtures_y_tests(
    guardia: ModuleType, tmp_path: Path
) -> None:
    (tmp_path / "analyzer").mkdir()
    (tmp_path / "analyzer" / "malo.schema.json").write_text(
        json.dumps(_con_ref(E36)), encoding="utf-8"
    )
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "malo.yaml").write_text(
        "a:\n  $ref: https://x.invalid/a\n", encoding="utf-8"
    )
    for saltado in ("vendor", "fixtures", "tests", "ts", "node_modules"):
        (tmp_path / saltado).mkdir()
        (tmp_path / saltado / "ignorado.json").write_text(
            json.dumps(_con_ref(E36)), encoding="utf-8"
        )
    (tmp_path / "notas.txt").write_text("no es un contrato", encoding="utf-8")
    problemas = guardia.comprobar(tmp_path)
    assert [p.split("#", 1)[0] for p in problemas] == ["analyzer/malo.schema.json", "api/malo.yaml"]


def test_un_contrato_ilegible_es_un_problema_y_no_una_excepcion(
    guardia: ModuleType, tmp_path: Path
) -> None:
    (tmp_path / "roto.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path) == ["roto.yaml: contrato ilegible (NFR10.5)"]
