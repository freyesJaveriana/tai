"""Ayudas comunes de las guardias de C1, C21 y la ruta de voz (`checks/_openapi.py`)."""

from typing import Any

from veridicus_contracts.checks import _openapi as ayudas

DOCUMENTO: dict[str, Any] = {
    "components": {
        "schemas": {
            "A": {"$ref": "#/components/schemas/B"},
            "B": {"type": "string"},
            "con~barra/": {"type": "integer"},
            "Vuelta": {"$ref": "#/components/schemas/Vuelta"},
        }
    }
}


def test_resolver_sigue_las_referencias_locales() -> None:
    assert ayudas.resolver(DOCUMENTO, {"$ref": "#/components/schemas/A"}) == {"type": "string"}
    escapada = {"$ref": "#/components/schemas/con~0barra~1"}
    assert ayudas.resolver(DOCUMENTO, escapada) == {"type": "integer"}


def test_resolver_deja_intacto_lo_que_no_puede_seguir() -> None:
    externa = {"$ref": "/veridicus/contracts/otro"}
    assert ayudas.resolver(DOCUMENTO, externa) == externa
    ausente = {"$ref": "#/components/schemas/NoExiste"}
    assert ayudas.resolver(DOCUMENTO, ausente) == ausente
    por_un_texto = {"$ref": "#/components/schemas/B/type"}
    assert ayudas.resolver(DOCUMENTO, por_un_texto) == por_un_texto
    vuelta = {"$ref": "#/components/schemas/Vuelta"}
    assert ayudas.resolver(DOCUMENTO, vuelta) == vuelta
    assert ayudas.resolver(DOCUMENTO, "texto") == "texto"


def test_objeto_y_escapar() -> None:
    assert ayudas.objeto({"a": 1}) == {"a": 1}
    assert ayudas.objeto(["a"]) == {}
    assert ayudas.escapar("/a~b") == "~1a~0b"


def test_hijas_baja_por_toda_forma_de_subesquema_y_dice_su_papel() -> None:
    esquema = {
        "properties": {"a": {}},
        "$defs": {"d": {}},
        "items": {},
        "prefixItems": [{}, {}],
        "patternProperties": {"^p/": {}},
        "additionalProperties": {"type": "string"},
        "allOf": [{}],
        "if": {},
        "then": {},
        "else": {},
        "anyOf": [{}],
        "oneOf": [{}],
        "required": ["a"],
    }
    esperado = {
        "/properties/a": ayudas.PROPIEDAD,
        "/$defs/d": ayudas.DEFINICION,
        "/items": ayudas.VALOR,
        "/prefixItems/0": ayudas.VALOR,
        "/prefixItems/1": ayudas.VALOR,
        "/patternProperties/^p~1": ayudas.VALOR,
        "/additionalProperties": ayudas.VALOR,
        "/allOf/0": ayudas.REFINA,
        "/if": ayudas.REFINA,
        "/then": ayudas.REFINA,
        "/else": ayudas.REFINA,
        "/anyOf/0": ayudas.RAMA,
        "/oneOf/0": ayudas.RAMA,
    }
    assert {puntero: papel for _, puntero, papel in ayudas.hijas(esquema, "")} == esperado


def test_hijas_ignora_lo_que_no_es_un_subesquema() -> None:
    assert list(ayudas.hijas({}, "/x")) == []
    assert list(ayudas.hijas({"additionalProperties": False, "items": False}, "")) == []
    assert list(ayudas.hijas({"properties": "no es un mapa", "allOf": "no es una lista"}, "")) == []


def test_es_tipo_acepta_un_texto_o_una_lista_de_tipos() -> None:
    assert ayudas.es_tipo({"type": "string"}, "string")
    assert ayudas.es_tipo({"type": ["string", "null"]}, "string")
    assert not ayudas.es_tipo({"type": ["integer", "null"]}, "string")
    assert not ayudas.es_tipo({"type": "integer"}, "string")
    assert not ayudas.es_tipo({}, "string")


def test_es_problem_en_linea_exige_content_type_esquema_y_cabeceras_propias() -> None:
    esquema = {"$ref": "#/components/schemas/Problem"}
    cabeceras = {"Retry-After": {"schema": {"type": "integer"}}}
    assert ayudas.es_problem({"$ref": "#/components/responses/Problem"})
    completa = {"headers": cabeceras, "content": {"application/problem+json": {"schema": esquema}}}
    assert ayudas.es_problem(completa)
    sin_cabeceras = {"content": {"application/problem+json": {"schema": esquema}}}
    assert not ayudas.es_problem(sin_cabeceras)
    assert not ayudas.es_problem({**sin_cabeceras, "headers": {}})
    otro_tipo = {"headers": cabeceras, "content": {"application/json": {"schema": esquema}}}
    assert not ayudas.es_problem(otro_tipo)
    otro_esquema = {
        "headers": cabeceras,
        "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Otro"}}},
    }
    assert not ayudas.es_problem(otro_esquema)
    assert not ayudas.es_problem("texto")
    assert not ayudas.es_problem(None)
