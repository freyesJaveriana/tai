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
