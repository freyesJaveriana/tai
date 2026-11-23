"""Registro de esquemas de los contratos (functional-spec §4.2, BR12.3, FD-U1-11).

Recorre los archivos `*.schema.json` y registra cada uno bajo `https://veridicus.invalid/`
más su `$id`, sin tocar el archivo. Toda referencia entre esquemas usa el `$id` del destino
como ruta absoluta (BR12.3). Los meta-esquemas de `vendor/` se registran bajo su propio
`$id` absoluto. El dominio `.invalid` está reservado y nunca se consulta por red, y la
función de recuperación del registro rechaza cualquier URI que no esté registrada
(NFR10.4, NFR10.5): no hay red ni siquiera cuando está disponible.
"""

import importlib.resources
from collections.abc import Iterator
from importlib.resources.abc import Traversable
from typing import Any
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from veridicus_contracts.loaders import LoadError, load_file

BASE_URI = "https://veridicus.invalid/"
SUFIJO_DE_ESQUEMA = ".schema.json"


class ForeignUriError(LookupError):
    """Se pidió una URI que el registro no tiene; nunca se resuelve por red."""


def _no_recuperar(uri: str) -> Resource[Any]:
    raise ForeignUriError(f"URI ajena al registro, no se consulta por red: {uri}")


def _esquemas(raiz: Traversable, en_vendor: bool) -> Iterator[tuple[Traversable, bool]]:
    """Cada archivo de esquema bajo `raiz`, con si cuelga de `vendor/`; salta `fixtures/`."""
    for entrada in sorted(raiz.iterdir(), key=lambda e: e.name):
        if entrada.is_dir():
            if entrada.name != "fixtures":
                yield from _esquemas(entrada, en_vendor or entrada.name == "vendor")
        elif entrada.name.endswith(SUFIJO_DE_ESQUEMA):
            yield entrada, en_vendor


def _uri_de(archivo: Traversable, contenido: Any, en_vendor: bool) -> str:
    identificador = contenido.get("$id") if isinstance(contenido, dict) else None
    if not isinstance(identificador, str):
        raise LoadError(f"{archivo.name}: el esquema no tiene $id de texto")
    if identificador.startswith("/"):
        return urljoin(BASE_URI, identificador)
    if en_vendor:
        return identificador
    raise LoadError(f"{archivo.name}: un $id absoluto solo se admite bajo vendor/: {identificador}")


def build_registry(raiz: Traversable | None = None) -> Registry[Any]:
    """Registro con todos los esquemas bajo `raiz` (por defecto, los datos del paquete)."""
    if raiz is None:
        raiz = importlib.resources.files("veridicus_contracts")
    recursos = []
    for archivo, en_vendor in _esquemas(raiz, raiz.name == "vendor"):
        contenido = load_file(archivo)
        recurso = Resource.from_contents(contenido, default_specification=DRAFT202012)
        recursos.append((_uri_de(archivo, contenido, en_vendor), recurso))
    vacio: Registry[Any] = Registry(retrieve=_no_recuperar)  # type: ignore[call-arg]  # motivo: referencing declara retrieve como parámetro público pero el plugin de attrs de mypy no lo ve
    return vacio.with_resources(recursos)


def validator_for(registro: Registry[Any], uri: str) -> Draft202012Validator:
    """Validador 2020-12 (con formatos) del esquema registrado bajo `uri`.

    Valida contra `{"$ref": uri}` para que toda referencia se resuelva contra `registro`
    con la URI absoluta, sin importar si el `$id` del archivo es relativo.
    """
    return Draft202012Validator(
        {"$ref": uri},
        registry=registro,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
