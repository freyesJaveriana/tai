"""Validación estándar: OpenAPI 3.1, AsyncAPI 3.0 y JSON Schema 2020-12 estricto (D2-D4, BR1.9)."""

import importlib.resources
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest

from veridicus_contracts.validators import (
    ValidationFailure,
    extract_message_payloads,
    validate_asyncapi,
    validate_instance,
    validate_json_schema,
    validate_openapi,
    verify_vendor,
)

VENDOR = importlib.resources.files("veridicus_contracts") / "vendor"

OPENAPI_MINIMO: dict[str, Any] = {
    "openapi": "3.1.0",
    "info": {"title": "Prueba", "version": "1.0.0"},
    "paths": {"/salud": {"get": {"responses": {"200": {"description": "bien"}}}}},
}

ASYNCAPI_MINIMO: dict[str, Any] = {
    "asyncapi": "3.0.0",
    "info": {"title": "Cola de prueba", "version": "1.0.0"},
    "channels": {
        "turnos": {
            "address": "turnos",
            "messages": {
                "turno": {
                    "payload": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {"id": {"type": "string", "format": "uuid"}},
                        "additionalProperties": False,
                    }
                },
                "fin": {"$ref": "#/components/messages/fin"},
            },
        }
    },
    "components": {"messages": {"fin": {"payload": {"type": "object"}}}},
}


def test_vendor_coincide_con_sha256sums() -> None:
    verify_vendor(VENDOR)


def test_un_meta_esquema_alterado_falla(tmp_path: Path) -> None:
    copia = tmp_path / "vendor"
    shutil.copytree(str(VENDOR), copia)
    verify_vendor(copia)
    objetivo = copia / "openapi-3.1.schema.json"
    objetivo.write_bytes(objetivo.read_bytes() + b" ")
    with pytest.raises(ValidationFailure, match="openapi-3.1.schema.json"):
        verify_vendor(copia)
    objetivo.write_bytes(objetivo.read_bytes().removesuffix(b" "))
    verify_vendor(copia)
    (copia / "sobrante.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationFailure, match="sobrante.json"):
        verify_vendor(copia)
    (copia / "sobrante.json").unlink()
    (copia / "SHA256SUMS").write_text("0" * 64 + "  inexistente.json\n", encoding="utf-8")
    with pytest.raises(ValidationFailure, match="inexistente.json"):
        verify_vendor(copia)
    (copia / "SHA256SUMS").unlink()
    with pytest.raises(ValidationFailure, match="SHA256SUMS"):
        verify_vendor(copia)


def test_openapi_minimo_valido_e_invalido() -> None:
    validate_openapi(OPENAPI_MINIMO)
    roto = {**OPENAPI_MINIMO, "paths": {"/salud": {"get": {"responses": {"200": {}}}}}}
    with pytest.raises(ValidationFailure):
        validate_openapi(roto)
    with pytest.raises(ValidationFailure):
        validate_openapi({"openapi": "3.0.0", "info": {"title": "x", "version": "1"}, "paths": {}})


def test_asyncapi_minimo_valido_e_invalido() -> None:
    validate_asyncapi(ASYNCAPI_MINIMO)
    sin_info = {k: v for k, v in ASYNCAPI_MINIMO.items() if k != "info"}
    with pytest.raises(ValidationFailure, match="info"):
        validate_asyncapi(sin_info)
    with pytest.raises(ValidationFailure):
        validate_asyncapi({**ASYNCAPI_MINIMO, "asyncapi": "2.6.0"})


def test_la_carga_de_cada_mensaje_se_extrae() -> None:
    cargas = extract_message_payloads(ASYNCAPI_MINIMO)
    assert set(cargas) == {"channels/turnos/messages/turno", "components/messages/fin"}
    assert cargas["components/messages/fin"] == {"type": "object"}
    with pytest.raises(ValidationFailure, match="sin carga"):
        extract_message_payloads({"channels": {"c": {"messages": {"m": {"name": "sin payload"}}}}})
    assert extract_message_payloads({"asyncapi": "3.0.0"}) == {}
    carga = cargas["channels/turnos/messages/turno"]
    validate_instance(carga, {"id": "5b2f4c0e-4f0a-4bd4-8f4e-0c4c7f6a8d11"})
    with pytest.raises(ValidationFailure):
        validate_instance(carga, {"id": "no-es-uuid"})


def test_una_palabra_clave_desconocida_se_rechaza() -> None:
    validate_json_schema({"type": "object", "properties": {"a": {"type": "string"}}})
    with pytest.raises(ValidationFailure, match="palabraInventada"):
        validate_json_schema({"type": "object", "palabraInventada": True})
    anidado = {
        "type": "object",
        "properties": {"a": {"allOf": [{"$defs": {"b": {"enum": [1], "tambien": 2}}}]}},
    }
    with pytest.raises(ValidationFailure, match="tambien"):
        validate_json_schema(anidado)
    with pytest.raises(ValidationFailure):
        validate_json_schema({"type": "no-existe"})
    # Los datos de const, enum, default y examples no son palabras clave.
    validate_json_schema(
        {"const": {"palabraInventada": 1}, "examples": [{"x": 1}], "default": {"y": 2}}
    )
    validate_json_schema(True)
    with pytest.raises(ValidationFailure, match="2020-12"):
        validate_json_schema({"$schema": "http://json-schema.org/draft-07/schema#"})


def test_los_formatos_uuid_y_date_time_se_comprueban() -> None:
    esquema = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "cuando": {"type": "string", "format": "date-time"},
        },
    }
    validate_instance(
        esquema, {"id": "5b2f4c0e-4f0a-4bd4-8f4e-0c4c7f6a8d11", "cuando": "2026-11-23T10:00:00Z"}
    )
    with pytest.raises(ValidationFailure, match="uuid"):
        validate_instance(esquema, {"id": "x"})
    with pytest.raises(ValidationFailure, match="date-time"):
        validate_instance(esquema, {"cuando": "ayer"})


def test_el_modulo_se_importa_sin_openapi_spec_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    """F-01: openapi-spec-validator es solo de desarrollo; el módulo no la importa al cargarse."""
    for nombre in (
        "openapi_spec_validator",
        "openapi_spec_validator.exceptions",
        "openapi_spec_validator.validation",
    ):
        monkeypatch.setitem(sys.modules, nombre, None)  # None hace que import falle
    monkeypatch.delitem(sys.modules, "veridicus_contracts.validators")
    modulo = importlib.import_module("veridicus_contracts.validators")
    modulo.validate_json_schema({"type": "object"})
    modulo.validate_asyncapi(ASYNCAPI_MINIMO)
    modulo.validate_instance({"type": "string"}, "x")
    with pytest.raises(modulo.ValidationFailure, match="openapi-spec-validator"):
        modulo.validate_openapi(OPENAPI_MINIMO)


@pytest.mark.parametrize(
    "esquema",
    [
        {"allOf": 5},
        {"allOf": {"a": {"type": "string"}}},
        {"properties": [1, 2]},
        {"properties": {"a": 5}},
        {"$defs": ["x"]},
        {"items": [{"type": "string"}]},
        {"not": "x"},
        5,
        None,
        [],
    ],
)
def test_un_esquema_mal_formado_sale_como_validation_failure(esquema: Any) -> None:
    with pytest.raises(ValidationFailure):
        validate_json_schema(esquema)
    with pytest.raises(ValidationFailure):
        validate_instance(esquema, {})


@pytest.mark.parametrize(
    "documento",
    [
        [],
        None,
        "texto",
        {"channels": []},
        {"channels": 5},
        {"channels": {"c": 5}},
        {"channels": {"c": []}},
        {"channels": {"c": {"messages": []}}},
        {"channels": {"c": {"messages": {"m": 5}}}},
        {"channels": {"c": {"messages": {"m": []}}}},
        {"components": 5},
        {"components": {"messages": []}},
        {"components": {"messages": {"m": 5}}},
    ],
)
def test_un_asyncapi_mal_formado_sale_como_validation_failure(documento: Any) -> None:
    with pytest.raises(ValidationFailure):
        extract_message_payloads(documento)


@pytest.mark.parametrize(
    "contenido",
    [b"\xff\xfe", b"sin separador\n", b"abc  ../fuera.json\n", b"abc  \n", b"abc  subdir\n"],
)
def test_un_sha256sums_mal_formado_sale_como_validation_failure(
    tmp_path: Path, contenido: bytes
) -> None:
    (tmp_path / "subdir").mkdir()
    (tmp_path / "SHA256SUMS").write_bytes(contenido)
    with pytest.raises(ValidationFailure):
        verify_vendor(tmp_path)


def test_un_mensaje_de_components_escrito_como_referencia_se_omite() -> None:
    """F-03: AsyncAPI 3.0 admite un Reference Object en components.messages."""
    documento = {
        **ASYNCAPI_MINIMO,
        "components": {
            "messages": {
                "fin": {"payload": {"type": "object"}},
                "alias": {"$ref": "#/components/messages/fin"},
            }
        },
    }
    validate_asyncapi(documento)
    assert set(extract_message_payloads(documento)) == {
        "channels/turnos/messages/turno",
        "components/messages/fin",
    }
