"""Módulo guardia de nombres: ASCII `snake_case` y `code` en `dominio.motivo` (§4.12, CD-05).

Los controles negativos trabajan sobre copias en memoria o en `tmp_path`; los positivos, sobre el
árbol versionado. Un mensaje nombra el archivo, el puntero y la regla, nunca el valor del `code`.
"""

import copy
import json
from pathlib import Path
from typing import Any

from helpers import CONTRACTS_ROOT, load_contract

from veridicus_contracts.checks import _contratos
from veridicus_contracts.checks import naming as guardia


def _problemas(documento: Any) -> list[str]:
    return guardia.comprobar_documento("api/x.yaml", documento)


def test_el_arbol_versionado_cumple_y_el_catalogo_se_recorre() -> None:
    assert guardia.comprobar(CONTRACTS_ROOT) == []
    catalogo = load_contract("errors/error-codes.v2.yaml")
    assert guardia.comprobar_catalogo("errors/error-codes.v2.yaml", catalogo) == []
    assert len(catalogo["codes"]) > 60
    consola = load_contract("api/console.v2.yaml")
    assert _problemas(consola) == []
    assert guardia.NOMBRE.fullmatch("cita_a") and guardia.NOMBRE.fullmatch("hecho")
    # Los nombres de C6 (cita_a, observaciones, ...) ya son ASCII snake_case: la regla 8 solo
    # exime a la copia, que no se recorre (BR1.8). Se comprueba sobre la copia real.
    salida = load_contract("analyzer/v1/salida.schema.json")
    assert "cita_a" in json.dumps(salida)
    assert guardia.comprobar_documento("analyzer/v1/salida.schema.json", salida) == []
    assert not any(
        ruta.startswith("analyzer/") for ruta, _ in guardia.contratos_propios(CONTRACTS_ROOT)
    )
    # Lista exacta de lo que no es un contrato propio (F-05); toda exención nueva exige su prueba.
    # E-38: la mitad TypeScript (`ts/`, con su `node_modules/`) tampoco es un contrato propio.
    assert _contratos.EXCLUIDOS == frozenset({"analyzer", "vendor", "fixtures", "tests", "ts"})


def test_una_propiedad_que_no_es_snake_case_ascii_es_rojo() -> None:
    sano = {"properties": {"created_at": {"type": "string"}, "a1": {}}}
    assert _problemas(sano) == []
    for malo in ("createdAt", "Created", "señal", "con-guion", "1uno", "con espacio", "_a", ""):
        problemas = _problemas({"a": {"properties": {malo: {"type": "string"}}}})
        assert len(problemas) == 1, malo
        assert problemas[0].startswith("api/x.yaml: /a/properties/"), problemas
        assert problemas[0].endswith(": el nombre no es ASCII snake_case (CD-05)")
    anidado = {"items": [{"properties": {"estadoFinal": {}}}]}
    assert _problemas(anidado) == [
        "api/x.yaml: /items/0/properties/estadoFinal: el nombre no es ASCII snake_case (CD-05)"
    ]
    assert _problemas({"properties": "no es un mapa", "x": [1, "properties"]}) == []


def test_un_parametro_de_ruta_o_consulta_en_camel_case_es_rojo() -> None:
    parametros = [
        {"name": "session_id", "in": "path"},
        {"name": "pageSize", "in": "query"},
        {"name": "userId", "in": "path"},
        {"name": "X-CSRF-Token", "in": "header"},
        {"name": "veridicus_session", "in": "cookie"},
        {"$ref": "#/components/parameters/Otro"},
        "texto",
        {"name": 7, "in": "query"},
        {"name": "cookieName", "in": "cookie"},
    ]
    problemas = _problemas({"paths": {"/a": {"get": {"parameters": parametros}}}})
    assert problemas == [
        "api/x.yaml: /paths/~1a/get/parameters/1/name: el nombre no es ASCII snake_case (CD-05)",
        "api/x.yaml: /paths/~1a/get/parameters/2/name: el nombre no es ASCII snake_case (CD-05)",
        "api/x.yaml: /paths/~1a/get/parameters/7/name: el nombre no es ASCII snake_case (CD-05)",
        "api/x.yaml: /paths/~1a/get/parameters/8/name: el nombre no es ASCII snake_case (CD-05)",
    ]


def test_los_parametros_de_components_parameters_tambien_se_comprueban() -> None:
    # F-01: los parámetros de un mapa (components/parameters) también se comprueban.
    mapa = {"parameters": {"A": {"name": "pageSize", "in": "query"}, "B": {"name": "ok", "in": "path"}}}
    # Una propiedad llamada in o name no es un parámetro.
    propiedades = {"properties": {"in": {"type": "string"}, "name": {"type": "string"}}}
    # F-01: copia en memoria de C1 con SessionId y Since renombrados.
    c1 = copy.deepcopy(load_contract("api/console.v2.yaml"))
    c1["components"]["parameters"]["SessionId"]["name"] = "sessionId"
    c1["components"]["parameters"]["Since"]["name"] = "sinceCursor"
    # Una sola comparación: el mapa y C1 fallan por su propia regla, sin enmascararse.
    assert [_problemas(mapa), _problemas(propiedades), _problemas(c1)] == [
        ["api/x.yaml: /parameters/A/name: el nombre no es ASCII snake_case (CD-05)"],
        [],
        [
            (
                "api/x.yaml: /components/parameters/SessionId/name: el nombre no es ASCII "
                "snake_case (CD-05)"
            ),
            "api/x.yaml: /components/parameters/Since/name: el nombre no es ASCII snake_case (CD-05)",
        ],
    ]


def test_un_code_sin_la_forma_dominio_motivo_es_rojo() -> None:
    sano = {"components": {"schemas": {"ErrorCode": {"enum": ["auth.forbidden", "a_b.c_d"]}}}}
    assert _problemas(sano) == []
    for malo in ("sinpunto", "auth.", ".forbidden", "Auth.forbidden", "a.b.c", "a.b-c", "a. b"):
        enum = {"components": {"schemas": {"ErrorCode": {"enum": ["auth.forbidden", malo]}}}}
        problemas = _problemas(enum)
        assert problemas == [
            (
                "api/x.yaml: /components/schemas/ErrorCode/enum/1: el code no tiene la forma "
                "dominio.motivo (CD-05)"
            )
        ], malo
        assert malo not in problemas[0]
    propiedad = {"properties": {"code": {"const": "sinpunto"}, "otro": {"const": "x"}}}
    assert _problemas(propiedad) == [
        "api/x.yaml: /properties/code/const: el code no tiene la forma dominio.motivo (CD-05)"
    ]
    assert _problemas({"properties": {"code": {"enum": "no es una lista", "const": 4}}}) == [
        "api/x.yaml: /properties/code/const: el code no tiene la forma dominio.motivo (CD-05)",
        "api/x.yaml: /properties/code/enum: el code no tiene la forma dominio.motivo (CD-05)",
    ]
    assert _problemas({"code": {"$ref": "#/components/schemas/ErrorCode"}}) == []


def test_las_claves_del_catalogo_y_los_nombres_de_metricas_se_comprueban() -> None:
    sano = {"codes": {"a.uno": {}, "b.dos_tres": {}}}
    assert guardia.comprobar_catalogo("errors/c.yaml", sano) == []
    malo = {"codes": {"a.uno": {}, "SinPunto": {}}}
    assert guardia.comprobar_catalogo("errors/c.yaml", malo) == [
        "errors/c.yaml: /codes/SinPunto: el code no tiene la forma dominio.motivo (CD-05)"
    ]
    assert guardia.comprobar_catalogo("errors/c.yaml", {"codes": 3}) == [
        "errors/c.yaml: /codes: debe ser un mapa de codes (CD-05)"
    ]
    metricas = {"metrics": [{"name": "veridicus_a_total"}, {"name": "veridicus_runTotal"}, {}, 4]}
    assert guardia.comprobar_metricas("metrics/a.yaml", metricas) == [
        "metrics/a.yaml: /metrics/1/name: el nombre no es ASCII snake_case (CD-05)",
        "metrics/a.yaml: /metrics/2/name: el nombre no es ASCII snake_case (CD-05)",
    ]
    assert guardia.comprobar_metricas("metrics/a.yaml", {"metrics": "x"}) == []
    assert guardia.comprobar_metricas("metrics/a.yaml", "x") == []


def _raiz(tmp_path: Path) -> Path:
    raiz = tmp_path / "contracts"
    for directorio in ("api", "errors", "metrics", "analyzer/v1", "api/fixtures", "vendor"):
        (raiz / directorio).mkdir(parents=True)
    escribir = {
        "errors/error-codes.v2.yaml": {"codes": {"a.uno": {}}},
        "metrics/a.v1.yaml": {"metrics": [{"name": "veridicus_a_total"}]},
        "api/x.yaml": {"properties": {"ok_campo": {}}},
    }
    for relativa, documento in escribir.items():
        (raiz / relativa).write_text(json.dumps(documento), encoding="utf-8")
    return raiz


def test_comprobar_recorre_los_contratos_propios_y_deja_fuera_c6_y_fixtures(tmp_path: Path) -> None:
    raiz = _raiz(tmp_path)
    assert guardia.comprobar(raiz) == []
    malo = json.dumps({"properties": {"campoMalo": {}}})
    for ajeno in ("analyzer/v1/salida.schema.json", "api/fixtures/x.json", "vendor/y.json"):
        (raiz / ajeno).write_text(malo, encoding="utf-8")
    assert guardia.comprobar(raiz) == []
    (raiz / "api" / "y.json").write_text(malo, encoding="utf-8")
    # F-05: build/, dist/, node_modules/ y src/ no están exentos: se recorren como el resto.
    # E-38: `ts/` sí está exento (mitad TypeScript, con su propio node_modules/): no se recorre.
    for carpeta in ("ts", "build", "dist", "node_modules", "src"):
        (raiz / carpeta).mkdir()
        (raiz / carpeta / "x.json").write_text(malo, encoding="utf-8")
    (raiz / "metrics" / "b.v1.yaml").write_text(
        json.dumps({"metrics": [{"name": "veridicus_mal-nombre"}]}), encoding="utf-8"
    )
    (raiz / "errors" / "error-codes.v2.yaml").write_text(
        json.dumps({"codes": {"sinpunto": {}}}), encoding="utf-8"
    )
    campo = "/properties/campoMalo: el nombre no es ASCII snake_case (CD-05)"
    assert guardia.comprobar(raiz) == [
        f"api/y.json: {campo}",
        f"build/x.json: {campo}",
        f"dist/x.json: {campo}",
        (
            "errors/error-codes.v2.yaml: /codes/sinpunto: el code no tiene la forma dominio.motivo "
            "(CD-05)"
        ),
        "metrics/b.v1.yaml: /metrics/0/name: el nombre no es ASCII snake_case (CD-05)",
        f"node_modules/x.json: {campo}",
        f"src/x.json: {campo}",
    ]


