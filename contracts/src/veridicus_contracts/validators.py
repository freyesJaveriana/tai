"""Validación estándar de los contratos (D2, D3, D4, BR1.9, NFR10.9).

- OpenAPI 3.1 con `openapi-spec-validator` (D3).
- AsyncAPI 3.0 contra el meta-esquema oficial empaquetado en `vendor/` (D4), con la
  extracción de la carga de cada mensaje.
- JSON Schema 2020-12 estricto: una palabra clave desconocida es un error (BR1.9), con
  los formatos `uuid` y `date-time` comprobados (D2).

Los meta-esquemas de `vendor/` se descargan una sola vez de su fuente oficial, se
versionan y se comprueban con `vendor/SHA256SUMS` antes de usarse (NFR10.9); nunca se
descargan en ejecución.
"""

import hashlib
import importlib.resources
from functools import cache
from importlib.resources.abc import Traversable
from typing import Any

from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.exceptions import ValidationError
from openapi_spec_validator import validate as validar_openapi_spec
from openapi_spec_validator.exceptions import OpenAPISpecValidatorError
from openapi_spec_validator.validation import OpenAPIV31SpecValidator
from referencing import Registry
from referencing.exceptions import Unresolvable

from veridicus_contracts.registry import build_registry, validator_for

ARCHIVO_DE_SUMAS = "SHA256SUMS"
META_2020_12 = "https://json-schema.org/draft/2020-12/schema"
VOCABULARIOS_2020_12 = tuple(
    f"https://json-schema.org/draft/2020-12/meta/{nombre}"
    for nombre in (
        "core",
        "applicator",
        "unevaluated",
        "validation",
        "meta-data",
        "format-annotation",
        "content",
    )
)
META_ASYNCAPI_3 = "http://asyncapi.com/definitions/3.0.0/asyncapi.json"

# Palabras clave 2020-12 cuyo valor es un subesquema, una lista de ellos o un mapa de ellos.
_SUBESQUEMA = frozenset(
    {
        "additionalProperties",
        "items",
        "contains",
        "not",
        "if",
        "then",
        "else",
        "propertyNames",
        "unevaluatedItems",
        "unevaluatedProperties",
        "contentSchema",
    }
)
_LISTA_DE_SUBESQUEMAS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
_MAPA_DE_SUBESQUEMAS = frozenset({"properties", "patternProperties", "dependentSchemas", "$defs"})


class ValidationFailure(ValueError):
    """Un contrato, un meta-esquema o una instancia no pasa la validación."""


def _carpeta_vendor() -> Traversable:
    return importlib.resources.files("veridicus_contracts") / "vendor"


def verify_vendor(vendor: Traversable | None = None) -> None:
    """Comprueba que cada archivo de `vendor/` coincide con `SHA256SUMS` y no sobra ninguno."""
    carpeta = vendor if vendor is not None else _carpeta_vendor()
    try:
        sumas = (carpeta / ARCHIVO_DE_SUMAS).read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ValidationFailure(f"falta {ARCHIVO_DE_SUMAS} en vendor/") from error
    listados: set[str] = set()
    for linea in filter(None, sumas.splitlines()):
        esperado, _, nombre = linea.partition("  ")
        listados.add(nombre)
        try:
            real = hashlib.sha256((carpeta / nombre).read_bytes()).hexdigest()
        except FileNotFoundError as error:
            raise ValidationFailure(f"vendor/{nombre} figura en {ARCHIVO_DE_SUMAS} y no existe") from error
        if real != esperado:
            raise ValidationFailure(f"vendor/{nombre} no coincide con {ARCHIVO_DE_SUMAS}")
    presentes = {e.name for e in carpeta.iterdir() if e.is_file()} - {ARCHIVO_DE_SUMAS}
    sobrantes = sorted(presentes - listados)
    if sobrantes:
        raise ValidationFailure(f"vendor/{sobrantes[0]} no figura en {ARCHIVO_DE_SUMAS}")


@cache
def _meta_registro() -> Registry[Any]:
    """Registro de los meta-esquemas, creado solo después de verificar `vendor/`."""
    verify_vendor()
    return build_registry(_carpeta_vendor())


@cache
def _palabras_conocidas() -> frozenset[str]:
    registro = _meta_registro()
    palabras: set[str] = set()
    for uri in VOCABULARIOS_2020_12:
        palabras.update(registro.get_or_retrieve(uri).value.contents["properties"])
    return frozenset(palabras)


def _errores(validador: Any, instancia: Any) -> list[str]:
    try:
        return [f"{e.json_path}: {e.message}" for e in validador.iter_errors(instancia)]
    except Unresolvable as error:
        return [f"referencia sin resolver: {error}"]


def _desconocidas(esquema: Any, ruta: str, conocidas: frozenset[str], salida: list[str]) -> None:
    if not isinstance(esquema, dict):
        return
    for clave, valor in esquema.items():
        if clave not in conocidas:
            salida.append(f"{ruta}/{clave}: palabra clave desconocida")
        elif clave in _SUBESQUEMA:
            _desconocidas(valor, f"{ruta}/{clave}", conocidas, salida)
        elif clave in _LISTA_DE_SUBESQUEMAS:
            for indice, hijo in enumerate(valor):
                _desconocidas(hijo, f"{ruta}/{clave}/{indice}", conocidas, salida)
        elif clave in _MAPA_DE_SUBESQUEMAS:
            for nombre, hijo in valor.items():
                _desconocidas(hijo, f"{ruta}/{clave}/{nombre}", conocidas, salida)


def validate_json_schema(esquema: Any) -> None:
    """Un esquema JSON 2020-12 válido contra su meta-esquema y sin palabras clave desconocidas."""
    if isinstance(esquema, dict) and esquema.get("$schema", META_2020_12) != META_2020_12:
        raise ValidationFailure(f"el esquema declara un $schema distinto de 2020-12: {esquema['$schema']}")
    problemas = _errores(validator_for(_meta_registro(), META_2020_12), esquema)
    _desconocidas(esquema, "$", _palabras_conocidas(), problemas)
    if problemas:
        raise ValidationFailure("esquema no válido: " + "; ".join(problemas))


def validate_instance(esquema: Any, instancia: Any, registro: Registry[Any] | None = None) -> None:
    """Valida una instancia contra un esquema 2020-12, con los formatos `uuid` y `date-time`."""
    validador = Draft202012Validator(
        esquema,
        registry=registro if registro is not None else build_registry(),
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    problemas = _errores(validador, instancia)
    if problemas:
        raise ValidationFailure("instancia no válida: " + "; ".join(problemas))


def validate_openapi(documento: Any) -> None:
    """Valida un documento OpenAPI 3.1."""
    try:
        validar_openapi_spec(documento, cls=OpenAPIV31SpecValidator)
    except (ValidationError, OpenAPISpecValidatorError) as error:
        raise ValidationFailure(f"OpenAPI 3.1 no válido: {error}") from error


def validate_asyncapi(documento: Any) -> None:
    """Valida un documento AsyncAPI 3.0 contra el meta-esquema oficial de `vendor/`."""
    validador = Draft7Validator({"$ref": META_ASYNCAPI_3}, registry=_meta_registro())
    problemas = _errores(validador, documento)
    if problemas:
        raise ValidationFailure("AsyncAPI 3.0 no válido: " + "; ".join(problemas[:5]))


def _carga_de(mensaje: Any, ruta: str) -> Any:
    if "payload" not in mensaje:
        raise ValidationFailure(f"{ruta}: mensaje sin carga (payload)")
    return mensaje["payload"]


def extract_message_payloads(documento: Any) -> dict[str, Any]:
    """Carga (esquema) de cada mensaje de un AsyncAPI 3.0, por ruta; omite las referencias."""
    cargas: dict[str, Any] = {}
    for canal, definicion in (documento.get("channels") or {}).items():
        for nombre, mensaje in (definicion.get("messages") or {}).items():
            if "$ref" not in mensaje:
                ruta = f"channels/{canal}/messages/{nombre}"
                cargas[ruta] = _carga_de(mensaje, ruta)
    for nombre, mensaje in ((documento.get("components") or {}).get("messages") or {}).items():
        ruta = f"components/messages/{nombre}"
        cargas[ruta] = _carga_de(mensaje, ruta)
    return cargas
