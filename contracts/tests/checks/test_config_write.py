"""Guardia de escritura de configuración: C1 no escribe perfiles, proveedores ni límites (§4.8, BR7.1).

Sustituye a `checks/threshold.py`, retirado con el cambio 01. El control negativo de referencia es
E15: `PUT /profiles`.
"""

import copy
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

pytestmark = pytest.mark.c1


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.config_write", "T15, paso 16")


def _c1() -> dict[str, Any]:
    return copy.deepcopy(load_contract("api/console.v2.yaml"))


def _cuerpo(**propiedades: Any) -> dict[str, Any]:
    esquema = {"type": "object", "additionalProperties": False, "properties": propiedades}
    return {"content": {"application/json": {"schema": esquema}}}


def test_el_c1_versionado_no_escribe_configuracion(guardia: ModuleType) -> None:
    assert guardia.comprobar_documento(_c1()) == []
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    # La excepción es real: el contrato la usa al crear y al importar una sesión.
    assert "profile_name" in str(_c1()["paths"]["/sessions"]["post"]["requestBody"])
    assert "profile_name" in str(_c1()["paths"]["/sessions/import"]["post"]["requestBody"])


def test_e15_put_profiles_nombra_perfil_en_la_ruta(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/profiles"]["put"] = {"operationId": "replace_profiles"}
    assert guardia.comprobar_documento(documento) == [
        "PUT /profiles: nombra «profile» en la ruta (BR7.1)"
    ]


def test_nombres_en_el_cuerpo_con_referencias_y_sin_distinguir_mayusculas_ni_tildes(
    guardia: ModuleType,
) -> None:
    documento = _c1()
    documento["components"]["schemas"]["Ajustes"] = {
        "type": "object",
        "properties": {"Proveedor": {"type": "string"}, "otro": {"$ref": "#/components/schemas/Ajustes"}},
    }
    documento["paths"]["/users"]["post"]["requestBody"] = _cuerpo(
        ajustes={"$ref": "#/components/schemas/Ajustes"},
        lista={"type": "array", "items": _cuerpo(Plantilla_prompt={})["content"]["application/json"]["schema"]},
        profile_name_override={"type": "string"},
        precio={"type": "number"},
        profile_name={"type": "string"},
    )
    assert guardia.comprobar_documento(documento) == [
        "POST /users: nombra «proveedor» en el cuerpo (BR7.1)",
        "POST /users: nombra «prompt» en el cuerpo (BR7.1)",
        "POST /users: nombra «profile» en el cuerpo (BR7.1)",
        "POST /users: nombra «precio» en el cuerpo (BR7.1)",
    ]


def test_nombres_en_parametros_y_rutas_de_escritura(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/users/{user_id}"]["patch"]["parameters"].append(
        {"name": "Límite", "in": "query", "schema": {"type": "integer"}}
    )
    documento["paths"]["/sessions/{session_id}/heartbeat"]["post"]["parameters"].append(
        {"$ref": "#/components/parameters/PerfilQuery"}
    )
    documento["components"]["parameters"]["PerfilQuery"] = {"name": "perfil", "in": "query"}
    documento["paths"]["/limites"] = {"post": {"operationId": "x"}}
    assert sorted(guardia.comprobar_documento(documento)) == [
        "PATCH /users/{user_id}: nombra «limit» en un parámetro (BR7.1)",
        "POST /limites: nombra «limit» en la ruta (BR7.1)",
        "POST /sessions/{session_id}/heartbeat: nombra «perfil» en un parámetro (BR7.1)",
    ]


PRECIO = {"precio": {"type": "number"}}
FORMAS_DE_ESQUEMA = {
    "oneOf": {"oneOf": [{"type": "object", "properties": PRECIO}]},
    "anyOf": {"anyOf": [{"type": "object", "properties": PRECIO}]},
    "allOf": {"allOf": [{"type": "object", "properties": PRECIO}]},
    "if": {"if": {"properties": PRECIO}},
    "then": {"then": {"properties": PRECIO}},
    "else": {"else": {"properties": PRECIO}},
    "patternProperties": {"patternProperties": {"^a": {"type": "object", "properties": PRECIO}}},
    "additionalProperties": {"additionalProperties": {"type": "object", "properties": PRECIO}},
    "prefixItems": {"type": "array", "prefixItems": [{"type": "object", "properties": PRECIO}]},
    "items": {"type": "array", "items": {"type": "object", "properties": PRECIO}},
}


@pytest.mark.parametrize("forma", sorted(FORMAS_DE_ESQUEMA))
def test_un_nombre_de_configuracion_dentro_de_una_forma_de_subesquema_es_rojo(
    guardia: ModuleType, forma: str
) -> None:
    documento = _c1()
    documento["paths"]["/users"]["post"]["requestBody"] = _cuerpo(
        ajuste=copy.deepcopy(FORMAS_DE_ESQUEMA[forma])
    )
    assert guardia.comprobar_documento(documento) == [
        "POST /users: nombra «precio» en el cuerpo (BR7.1)"
    ]


def test_los_parametros_de_nivel_de_ruta_valen_para_cada_escritura_de_la_ruta(
    guardia: ModuleType,
) -> None:
    documento = _c1()
    ruta = documento["paths"]["/users"]
    assert "get" in ruta and "post" in ruta
    ruta["parameters"] = [
        {"name": "price_limit", "in": "query", "schema": {"type": "integer"}},
        {"$ref": "#/components/parameters/ProveedorQuery"},
    ]
    documento["components"]["parameters"]["ProveedorQuery"] = {"name": "provider", "in": "query"}
    # La lectura de la misma ruta puede nombrarlos; la escritura no.
    assert guardia.comprobar_documento(documento) == [
        "POST /users: nombra «price» en un parámetro (BR7.1)",
        "POST /users: nombra «provider» en un parámetro (BR7.1)",
    ]
    sin_parametros = _c1()
    sin_parametros["paths"]["/users"]["parameters"] = "no es una lista"
    assert guardia.comprobar_documento(sin_parametros) == []


def test_una_lectura_puede_nombrar_perfiles_y_limites(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/users"]["get"]["parameters"] = [
        {"name": "limit", "in": "query", "schema": {"type": "integer"}},
        {"name": "profile", "in": "query", "schema": {"type": "string"}},
    ]
    assert guardia.comprobar_documento(documento) == []


def test_un_cuerpo_que_no_es_un_objeto_o_con_ciclo_no_revienta(guardia: ModuleType) -> None:
    documento = _c1()
    documento["components"]["schemas"]["Vuelta"] = {"$ref": "#/components/schemas/Vuelta"}
    documento["paths"]["/users"]["post"]["requestBody"] = {
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Vuelta"}}}
    }
    documento["paths"]["/acknowledgements"]["post"]["requestBody"] = {"content": "no es un objeto"}
    assert guardia.comprobar_documento(documento) == []


def test_comprobar_con_el_contrato_ausente_o_ilegible(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(tmp_path) == ["api/console.v2.yaml: contrato ausente (BR7.1)"]
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "console.v2.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path) == [
        "api/console.v2.yaml: contrato ilegible, no se pudo interpretar (BR7.1)"
    ]
