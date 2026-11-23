"""Ayudas comunes de las pruebas de contratos y guardias (paso 5, PD-5, PD-8).

Reglas que hacen que el rojo sea un fallo y no un error:

- un contrato o un fixture ausente es `pytest.fail("contrato ausente: <ruta>")`, nunca una
  excepción sin capturar (`load_contract`, `cargar_fixture`);
- lo que aún no existe en el paquete se importa dentro de la prueba con `importar_o_fallar`;
- ninguna guardia pasa en vacío: toda comprobación empieza cargando el contrato que recorre.

Los esquemas se validan siempre por `veridicus_contracts.registry` (único resolvedor, BR12.3), con
un registro construido una sola vez (aviso A-04 de la revisión de U01-T02).

Convención de `contract` en los fixtures (§4.10): `<contrato>` o `<contrato>.<parte>`, p. ej.
`C6.salida`, `C2.RunRequested`, `C21.request`.
"""

import importlib
import json
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any, NamedTuple
from urllib.parse import urljoin

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT202012

from veridicus_contracts.loaders import LoadError, load_file
from veridicus_contracts.registry import BASE_URI, build_registry
from veridicus_contracts.validators import ValidationFailure, extract_message_payloads

CONTRACTS_ROOT = Path(__file__).resolve().parent.parent

CAMPOS_DE_FIXTURE = frozenset(
    {"fixture_id", "contract", "synthetic", "expectation", "mentions", "payload"}
)

# (palabra clave del validador o None, ruta JSON de la instancia, texto del mensaje o None)
Esperado = tuple[str | None, str, str | None]


class Caso(NamedTuple):
    """Un fixture de una tabla de casos: su archivo, su `contract` y por qué se rechaza."""

    archivo: str
    contrato: str
    razon: str | None = None
    esperado: Esperado | None = None


def ruta_de(relativa: str) -> Path:
    """Ruta absoluta de un archivo de `contracts/`."""
    return CONTRACTS_ROOT / relativa


def load_contract(relativa: str) -> Any:
    """Lee un contrato de `contracts/`; si falta, la prueba falla (no es un error)."""
    ruta = ruta_de(relativa)
    if not ruta.is_file():
        pytest.fail(f"contrato ausente: {relativa}")
    try:
        return load_file(ruta)
    except LoadError as error:
        pytest.fail(f"contrato ilegible: {relativa}: {error}")


def load_text(relativa: str) -> str:
    """Texto de un archivo de `contracts/` que no es YAML ni JSON (p. ej. SHA256SUMS)."""
    ruta = ruta_de(relativa)
    if not ruta.is_file():
        pytest.fail(f"contrato ausente: {relativa}")
    return ruta.read_text(encoding="utf-8")


def importar_o_fallar(modulo: str, motivo: str) -> ModuleType:
    """Importa un módulo que aún puede no existir; su ausencia es un fallo con el motivo."""
    try:
        importado = importlib.import_module(modulo)
    except ImportError as error:
        pytest.fail(f"módulo ausente: {modulo} ({motivo}): {error}")
    if getattr(importado, "__file__", None) is None:
        # Un directorio de datos con el mismo nombre (p. ej. model_calls/) es un paquete de
        # espacios de nombres sin código: todavía no existe el módulo.
        pytest.fail(f"módulo ausente: {modulo} ({motivo}): solo existe un directorio de datos")
    return importado


@cache
def nombres_sinteticos() -> frozenset[str]:
    """Nombres y lugares inventados de `fixtures/synthetic-names.yaml`."""
    catalogo = load_contract("fixtures/synthetic-names.yaml")
    return frozenset(catalogo["personas"]) | frozenset(catalogo["lugares"])


def cargar_fixture(relativa: str, contrato: str) -> dict[str, Any]:
    """Lee un fixture y comprueba el formato de §4.10 (sintético, mentions, reject_reason)."""
    ruta = ruta_de(relativa)
    if not ruta.is_file():
        pytest.fail(f"fixture ausente: {relativa}")
    fixture = load_file(ruta)
    assert isinstance(fixture, dict), f"{relativa}: el fixture debe ser un objeto"
    assert CAMPOS_DE_FIXTURE <= fixture.keys(), f"{relativa}: faltan campos de fixture"
    sobrantes = set(fixture) - CAMPOS_DE_FIXTURE - {"reject_reason"}
    assert not sobrantes, f"{relativa}: campos fuera del formato: {sorted(sobrantes)}"
    assert fixture["synthetic"] is True, f"{relativa}: synthetic debe ser true"
    assert fixture["contract"] == contrato, f"{relativa}: contract {fixture['contract']!r}"
    assert fixture["expectation"] in {"accept", "reject"}
    razon = fixture.get("reject_reason")
    if fixture["expectation"] == "reject":
        assert isinstance(razon, str) and razon, f"{relativa}: reject exige reject_reason"
    else:
        assert razon is None, f"{relativa}: accept no lleva reject_reason"
    texto = json.dumps(fixture["payload"], ensure_ascii=False)
    for mencion in fixture["mentions"]:
        assert mencion in nombres_sinteticos(), f"{relativa}: {mencion!r} no es sintético"
        assert mencion in texto, f"{relativa}: {mencion!r} no aparece en el texto"
    return dict(fixture)


@cache
def registro_de_contratos() -> Registry[Any]:
    """Registro de los esquemas del paquete, construido una sola vez."""
    try:
        return build_registry()
    except LoadError as error:
        pytest.fail(f"el registro de esquemas no carga: {error}")


def _uri_natural(documento: Any) -> str | None:
    identificador = documento.get("$id") if isinstance(documento, dict) else None
    if isinstance(identificador, str):
        return urljoin(BASE_URI, "/" + identificador.lstrip("/"))
    return None


def uri_de(relativa: str, documento: Any) -> str:
    """URI bajo la que se valida un documento: su `$id` bajo la base, o una URI de prueba."""
    return _uri_natural(documento) or f"{BASE_URI}_documentos/{relativa}"


def validador_de(relativa: str, puntero: str = "") -> Draft202012Validator:
    """Validador del documento `relativa` (o de un puntero `#/...` dentro de él)."""
    documento = load_contract(relativa)
    uri = uri_de(relativa, documento)
    recurso = Resource.from_contents(documento, default_specification=DRAFT202012)
    registro = registro_de_contratos().with_resource(uri, recurso)
    return Draft202012Validator(
        {"$ref": uri + puntero},
        registry=registro,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def puntero_de_mensaje(relativa: str, mensaje: str) -> str:
    """Puntero `#/.../payload` del mensaje de un AsyncAPI; si no existe, la prueba falla."""
    documento = load_contract(relativa)
    try:
        cargas = extract_message_payloads(documento)
    except ValidationFailure as error:
        pytest.fail(f"AsyncAPI ilegible: {relativa}: {error}")
    for ruta in cargas:
        if ruta.endswith("/" + mensaje):
            return f"#/{ruta}/payload"
    pytest.fail(f"mensaje ausente en {relativa}: {mensaje}")


def puntero_de_cuerpo(ruta_http: str, metodo: str) -> str:
    """Puntero al esquema del cuerpo JSON de la petición de una operación OpenAPI."""
    escapada = ruta_http.replace("~", "~0").replace("/", "~1")
    return f"#/paths/{escapada}/{metodo}/requestBody/content/application~1json/schema"


def _aplanar(errores: Iterator[ValidationError]) -> Iterator[ValidationError]:
    for error in errores:
        yield error
        yield from _aplanar(iter(error.context or ()))


def errores_de(validador: Draft202012Validator, instancia: Any) -> list[ValidationError]:
    """Todos los errores de una instancia, incluidos los de las ramas anidadas."""
    try:
        return list(_aplanar(validador.iter_errors(instancia)))
    except Unresolvable as error:
        pytest.fail(f"referencia sin resolver: {error}")


def coincide(error: ValidationError, esperado: Esperado) -> bool:
    """El error tiene la palabra clave, la ruta y el texto que declara la prueba.

    Una ruta que empieza por `*` se compara como fragmento de la ruta del error (para los
    casos en que el contrato puede nombrar la instancia en un nivel u otro).
    """
    palabra, ruta, texto = esperado
    ruta_ok = ruta[1:] in error.json_path if ruta.startswith("*") else error.json_path == ruta
    return (
        (palabra is None or error.validator == palabra)
        and ruta_ok
        and (texto is None or texto in error.message)
    )


def comprobar(
    fixture: dict[str, Any], errores: list[ValidationError], esperado: Esperado | None
) -> None:
    """`accept` sin errores; `reject` con errores y al menos uno por la causa que declara la prueba."""
    if fixture["expectation"] == "accept":
        assert not errores, f"{fixture['fixture_id']}: debía aceptarse: {_resumen(errores)}"
        return
    assert errores, f"{fixture['fixture_id']}: debía rechazarse por {fixture['reject_reason']}"
    assert esperado is not None, f"{fixture['fixture_id']}: la prueba no declara su causa"
    assert any(coincide(error, esperado) for error in errores), (
        f"{fixture['fixture_id']}: rechazado por otra causa que {fixture['reject_reason']} "
        f"({esperado}): {_resumen(errores)}"
    )


def _resumen(errores: list[ValidationError]) -> list[tuple[str, str, str]]:
    return [(e.validator or "", e.json_path, e.message[:80]) for e in errores]


def comprobar_caso(directorio: str, caso: Caso, validador: Draft202012Validator) -> None:
    """Carga el fixture del caso, lo valida y exige aceptación o rechazo por su causa."""
    fixture = cargar_fixture(f"{directorio}/{caso.archivo}", caso.contrato)
    assert fixture.get("reject_reason") == caso.razon, (
        f"{caso.archivo}: reject_reason {fixture.get('reject_reason')!r} distinto de {caso.razon!r}"
    )
    comprobar(fixture, errores_de(validador, fixture["payload"]), caso.esperado)


def ids_de(casos: list[Caso]) -> list[str]:
    """Identificadores legibles de una tabla de casos."""
    return [caso.archivo for caso in casos]


def recorrer(
    nodo: Any, ruta: str = "$", clave: str | None = None
) -> Iterator[tuple[str, str | None, Any]]:
    """Recorre un documento en profundidad: (ruta, clave del padre, valor).

    Los elementos de una lista conservan la clave de la lista (p. ej. `enum`).
    """
    yield ruta, clave, nodo
    if isinstance(nodo, dict):
        for hija, valor in nodo.items():
            yield from recorrer(valor, f"{ruta}.{hija}", hija)
    elif isinstance(nodo, list):
        for indice, valor in enumerate(nodo):
            yield from recorrer(valor, f"{ruta}[{indice}]", clave)
