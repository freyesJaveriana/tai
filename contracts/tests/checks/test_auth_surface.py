"""Guardia de la superficie de C1: sesión, anti-CSRF, roles y rutas que encolan (§4.6, NFRD-U1-12).

Cada regla lleva un control negativo sobre una copia en memoria del contrato real y la comparación
con el original: lo que la guardia añade a lo que ya decía del contrato versionado es solo el
hallazgo que provoca la prueba. El control positivo corre sobre el contrato real.
"""

import copy
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from helpers import CONTRACTS_ROOT, importar_o_fallar, load_contract

pytestmark = pytest.mark.c1

PROBLEM = {"$ref": "#/components/responses/Problem"}


@pytest.fixture
def guardia() -> ModuleType:
    return importar_o_fallar("veridicus_contracts.checks.auth_surface", "T15, paso 16")


def _c1() -> dict[str, Any]:
    return copy.deepcopy(load_contract("api/console.v2.yaml"))


def _nuevos(guardia: ModuleType, documento: dict[str, Any]) -> list[str]:
    antes = set(guardia.comprobar_documento(_c1()))
    return [p for p in guardia.comprobar_documento(documento) if p not in antes]


def _operacion_valida(**extra: Any) -> dict[str, Any]:
    operacion: dict[str, Any] = {
        "operationId": "operacion_de_prueba",
        "x-veridicus-roles": ["admin"],
        "responses": {"200": {"description": "ok"}, "401": PROBLEM, "403": PROBLEM},
    }
    operacion.update(extra)
    return operacion


def test_el_c1_versionado_cumple_la_superficie(guardia: ModuleType) -> None:
    assert guardia.comprobar_documento(_c1()) == []
    assert guardia.comprobar(CONTRACTS_ROOT) == []


def test_ruta_publica_nueva_fuera_de_la_lista(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/status"] = {"get": _operacion_valida(security=[])}
    assert _nuevos(guardia, documento) == [
        "GET /status: ruta pública fuera de la lista (login y notice; §4.6, D-1)"
    ]
    assert set(guardia.PUBLICAS) == {("post", "/auth/login"), ("get", "/notice")}


def test_escritura_sin_anti_csrf(guardia: ModuleType) -> None:
    documento = _c1()
    parametros = documento["paths"]["/users"]["post"]["parameters"]
    documento["paths"]["/users"]["post"]["parameters"] = [
        p for p in parametros if p.get("$ref") != "#/components/parameters/CsrfToken"
    ]
    mensaje = "POST /users: escritura sin X-CSRF-Token de al menos 32 caracteres (§4.6)"
    assert _nuevos(guardia, documento) == [mensaje]
    flojo = _c1()
    flojo["components"]["parameters"]["CsrfToken"]["schema"]["minLength"] = 31
    nuevos = _nuevos(guardia, flojo)
    assert len(nuevos) > 5 and all("escritura sin X-CSRF-Token" in p for p in nuevos)
    flojo_en_patch = _c1()
    flojo_en_patch["components"]["parameters"]["CsrfToken"]["in"] = "query"
    assert any("PATCH /users/{user_id}: escritura sin" in p for p in _nuevos(guardia, flojo_en_patch))


def test_operacion_sin_roles_o_con_un_rol_que_no_existe(guardia: ModuleType) -> None:
    documento = _c1()
    del documento["paths"]["/profiles"]["get"]["x-veridicus-roles"]
    esperado = "GET /profiles: sin x-veridicus-roles con valores de Role (NFRD-U1-12)"
    assert _nuevos(guardia, documento) == [esperado]
    con_rol_ajeno = _c1()
    con_rol_ajeno["paths"]["/profiles"]["get"]["x-veridicus-roles"] = ["analista", "jefe"]
    assert _nuevos(guardia, con_rol_ajeno) == [esperado]
    vacia = _c1()
    vacia["paths"]["/profiles"]["get"]["x-veridicus-roles"] = []
    assert _nuevos(guardia, vacia) == [esperado]
    # logout y me no declaran roles y no se les exige
    assert "x-veridicus-roles" not in _c1()["paths"]["/auth/logout"]["post"]


def test_ni_put_ni_delete(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/users"]["delete"] = _operacion_valida()
    documento["paths"]["/profiles"]["put"] = _operacion_valida()
    assert sorted(_nuevos(guardia, documento)) == [
        "DELETE /users: operación que reemplaza o borra (§4.6)",
        "PUT /profiles: operación que reemplaza o borra (§4.6)",
    ]


def test_las_seis_operaciones_que_encolan_solo_declaran_202(guardia: ModuleType) -> None:
    assert guardia.ENCOLAN == frozenset(
        {
            "create_turn",
            "paste_transcript",
            "launch_final_run",
            "retry_run",
            "set_analysis_paused",
            "create_voice_turn",
        }
    )
    documento = _c1()
    documento["paths"]["/sessions/{session_id}/turns"]["post"]["responses"]["200"] = {
        "description": "bloqueante"
    }
    assert _nuevos(guardia, documento) == [
        ("POST /sessions/{session_id}/turns: operación que encola con un 2xx distinto de 202 "
        "(§4.6, NFR3.1)")
    ]
    renombrada = _c1()
    renombrada["paths"]["/sessions/{session_id}/runs/{run_id}/retry"]["post"]["operationId"] = "x"
    assert _nuevos(guardia, renombrada) == [
        "operación que encola ausente: retry_run (§4.6; sumar una ruta exige actualizar la constante)"
    ]


def test_401_y_403_con_ref_a_problem(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/users"]["get"]["responses"]["403"] = {"description": "sin Problem"}
    del documento["paths"]["/auth/logout"]["post"]["responses"]["401"]
    assert sorted(_nuevos(guardia, documento)) == [
        "GET /users: 403 sin $ref a Problem (NFRD-U1-12)",
        "POST /auth/logout: 401 sin $ref a Problem (NFRD-U1-12)",
    ]
    en_linea = _c1()
    en_linea["paths"]["/auth/me"]["get"]["responses"]["401"] = {
        "description": "con cabeceras",
        "content": {
            "application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}
        },
    }
    assert _nuevos(guardia, en_linea) == []
    mal_formada = _c1()
    mal_formada["paths"]["/auth/me"]["get"]["responses"]["401"] = "texto"
    assert _nuevos(guardia, mal_formada) == ["GET /auth/me: 401 sin $ref a Problem (NFRD-U1-12)"]


def test_extension_fuera_de_la_lista_cerrada(guardia: ModuleType) -> None:
    documento = _c1()
    documento["paths"]["/users"]["get"]["x-veridicus-secreto"] = True
    documento["components"]["schemas"]["Role"]["x-veridicus-otra"] = [{"x-veridicus-mas": 1}]
    assert sorted(_nuevos(guardia, documento)) == [
        ("/components/schemas/Role/x-veridicus-otra/0/x-veridicus-mas: extensión fuera de la lista "
        "cerrada (§4.6)"),
        "/components/schemas/Role/x-veridicus-otra: extensión fuera de la lista cerrada (§4.6)",
        "/paths/~1users/get/x-veridicus-secreto: extensión fuera de la lista cerrada (§4.6)",
    ]


def test_comprobar_con_el_contrato_ausente_o_ilegible(guardia: ModuleType, tmp_path: Path) -> None:
    assert guardia.comprobar(tmp_path) == ["api/console.v2.yaml: contrato ausente (§4.6)"]
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "console.v2.yaml").write_text("a: 1\na: 2\n", encoding="utf-8")
    assert guardia.comprobar(tmp_path) == [
        "api/console.v2.yaml: contrato ilegible, no se pudo interpretar (§4.6)"
    ]
