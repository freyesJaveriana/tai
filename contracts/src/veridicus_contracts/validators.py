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
import re
from functools import cache
from importlib.resources.abc import Traversable
from typing import Any

from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.exceptions import ValidationError
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
VERSION_DEL_CONTRATO = "x-veridicus-version"
# Lista cerrada de marcas `x-veridicus-*` que usan los contratos (PD-4, K-56): cualquier otra se
# rechaza. `x-veridicus-version` solo vale en la raíz (E-30); las demás, en cualquier nivel.
MARCAS_X_VERIDICUS = frozenset(
    {
        VERSION_DEL_CONTRATO,
        "x-veridicus-limit",
        "x-veridicus-max-bytes",
        "x-veridicus-cookie",
        "x-veridicus-owner-only",
        "x-veridicus-owner-only-for-role",
        "x-veridicus-priority",
        "x-veridicus-roles",
        "x-veridicus-access-log",
        "x-veridicus-demo",
    }
)
_SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_LISTA_DE_SUBESQUEMAS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
_MAPA_DE_SUBESQUEMAS = frozenset({"properties", "patternProperties", "dependentSchemas", "$defs"})


class ValidationFailure(ValueError):
    """Un contrato, un meta-esquema o una instancia no pasa la validación."""


def _carpeta_vendor() -> Traversable:
    return importlib.resources.files("veridicus_contracts") / "vendor"


def _leer_sumas(carpeta: Traversable) -> dict[str, str]:
    """Pares nombre -> hash de SHA256SUMS; una línea mal formada es un error."""
    try:
        sumas = (carpeta / ARCHIVO_DE_SUMAS).read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ValidationFailure(f"falta {ARCHIVO_DE_SUMAS} en vendor/") from error
    except UnicodeDecodeError as error:
        raise ValidationFailure(f"{ARCHIVO_DE_SUMAS} no es texto UTF-8") from error
    pares: dict[str, str] = {}
    for linea in filter(None, sumas.splitlines()):
        esperado, separador, nombre = linea.partition("  ")
        if not separador or not nombre or "/" in nombre or "\\" in nombre:
            raise ValidationFailure(f"línea mal formada en {ARCHIVO_DE_SUMAS}: {linea!r}")
        pares[nombre] = esperado
    return pares


def verify_vendor(vendor: Traversable | None = None) -> None:
    """Comprueba que cada archivo de `vendor/` coincide con `SHA256SUMS` y no sobra ninguno."""
    carpeta = vendor if vendor is not None else _carpeta_vendor()
    listados = _leer_sumas(carpeta)
    for nombre, esperado in listados.items():
        try:
            real = hashlib.sha256((carpeta / nombre).read_bytes()).hexdigest()
        except OSError as error:
            raise ValidationFailure(
                f"vendor/{nombre} figura en {ARCHIVO_DE_SUMAS} y no se puede leer"
            ) from error
        if real != esperado:
            raise ValidationFailure(f"vendor/{nombre} no coincide con {ARCHIVO_DE_SUMAS}")
    presentes = {e.name for e in carpeta.iterdir() if e.is_file()} - {ARCHIVO_DE_SUMAS}
    sobrantes = sorted(presentes - listados.keys())
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
        if clave == VERSION_DEL_CONTRATO and ruta == "$":
            # anotacion de BR1.1 (E-30): solo la raiz del esquema, con forma semver
            if not (isinstance(valor, str) and _SEMVER.fullmatch(valor)):
                salida.append(f"{ruta}/{clave}: debe ser una versión semver X.Y.Z, no {valor!r}")
            continue
        if clave in MARCAS_X_VERIDICUS and clave != VERSION_DEL_CONTRATO:
            continue  # marca de la lista cerrada de PD-4; su valor es un dato, no un subesquema
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
        raise ValidationFailure(
            f"el esquema declara un $schema distinto de 2020-12: {esquema['$schema']}"
        )
    problemas = _errores(validator_for(_meta_registro(), META_2020_12), esquema)
    if not problemas:
        # Solo se recorre un esquema que el meta-esquema ya aceptó: sus tipos son los esperados.
        _desconocidas(esquema, "$", _palabras_conocidas(), problemas)
    if problemas:
        raise ValidationFailure("esquema no válido: " + "; ".join(problemas))


def validate_instance(esquema: Any, instancia: Any, registro: Registry[Any] | None = None) -> None:
    """Valida una instancia contra un esquema 2020-12, con los formatos `uuid` y `date-time`.

    El esquema también debe ser válido y estricto (`validate_json_schema`): un esquema mal
    formado es un `ValidationFailure`, no una excepción del validador.
    """
    validate_json_schema(esquema)
    validador = Draft202012Validator(
        esquema,
        registry=registro if registro is not None else build_registry(),
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    problemas = _errores(validador, instancia)
    if problemas:
        raise ValidationFailure("instancia no válida: " + "; ".join(problemas))


def validate_openapi(documento: Any) -> None:
    """Valida un documento OpenAPI 3.1 con `openapi-spec-validator` (D3).

    Esa biblioteca es solo de desarrollo (tech-stack §3), así que se importa aquí y no al
    cargar el módulo; si falta, es un `ValidationFailure` con el motivo. Usa los esquemas
    que la propia biblioteca empaqueta, no `vendor/openapi-3.1.schema.json`: ambos llevan
    el mismo `$id` (`.../oas/3.1/schema/2022-10-07`) pero el de la biblioteca difiere en
    `path-item-or-reference` y en un `if/then` de `responses`. D3 fija la biblioteca; la copia
    de `vendor/` se empaqueta y se verifica con `SHA256SUMS` (paso 4) y queda como referencia.
    """
    try:
        from openapi_spec_validator import validate as validar_openapi_spec
        from openapi_spec_validator.exceptions import OpenAPISpecValidatorError
        from openapi_spec_validator.validation import OpenAPIV31SpecValidator
    except ImportError as error:
        raise ValidationFailure(
            "validate_openapi necesita openapi-spec-validator (dependencia de desarrollo, D3)"
        ) from error
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


def _objeto(valor: Any, ruta: str) -> dict[str, Any]:
    """El valor como objeto; si falta (None) es vacío; cualquier otro tipo es un error."""
    if valor is None:
        return {}
    if not isinstance(valor, dict):
        raise ValidationFailure(f"{ruta}: debe ser un objeto")
    return valor


def _mensajes(mensajes: Any, prefijo: str, cargas: dict[str, Any]) -> None:
    """Agrega la carga de cada mensaje; un Reference Object (`$ref`) se omite."""
    for nombre, mensaje in _objeto(mensajes, prefijo).items():
        ruta = f"{prefijo}/{nombre}"
        mensaje = _objeto(mensaje, ruta)
        if "$ref" in mensaje:
            continue
        if "payload" not in mensaje:
            raise ValidationFailure(f"{ruta}: mensaje sin carga (payload)")
        cargas[ruta] = mensaje["payload"]


def extract_message_payloads(documento: Any) -> dict[str, Any]:
    """Carga (esquema) de cada mensaje de un AsyncAPI 3.0, por ruta; omite las referencias.

    Un Reference Object es válido tanto en `channels/*/messages` como en
    `components/messages`; su definición se extrae donde está. Toda forma que no sea la
    esperada sale como `ValidationFailure`.
    """
    cargas: dict[str, Any] = {}
    if not isinstance(documento, dict):
        raise ValidationFailure("documento: debe ser un objeto")
    raiz = documento
    for canal, definicion in _objeto(raiz.get("channels"), "channels").items():
        canal_obj = _objeto(definicion, f"channels/{canal}")
        _mensajes(canal_obj.get("messages"), f"channels/{canal}/messages", cargas)
    componentes = _objeto(raiz.get("components"), "components")
    _mensajes(componentes.get("messages"), "components/messages", cargas)
    return cargas
