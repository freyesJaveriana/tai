"""Registro de esquemas de los contratos (functional-spec §4.2, BR12.3, FD-U1-11).

Recorre los archivos `*.schema.json` y todo `.yaml`, `.yml` o `.json` cuyo documento raíz
declare `$schema` y `$id` (fuera de `fixtures/` y `tests/`) y registra cada uno bajo
`https://veridicus.invalid/` más su `$id` (relativo, con o sin barra inicial), sin tocar el archivo. Toda referencia entre esquemas usa el `$id` del destino
como ruta absoluta (BR12.3). Los meta-esquemas de `vendor/` se registran bajo su propio
`$id` absoluto. El dominio `.invalid` está reservado y nunca se consulta por red, y la
función de recuperación del registro rechaza cualquier URI que no esté registrada
(NFR10.4, NFR10.5): no hay red ni siquiera cuando está disponible.
"""

import importlib.resources
from collections.abc import Iterator
from importlib.resources.abc import Traversable
from typing import Any
from urllib.parse import urljoin, urlsplit

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from veridicus_contracts.loaders import LoadError, load_file

BASE_URI = "https://veridicus.invalid/"
SUFIJO_DE_ESQUEMA = ".schema.json"
SUFIJOS_DE_DATOS = (".yaml", ".yml", ".json")
DIRECTORIOS_SALTADOS = frozenset({"fixtures", "tests"})


class ForeignUriError(LookupError):
    """Se pidió una URI que el registro no tiene; nunca se resuelve por red."""


def _no_recuperar(uri: str) -> Resource[Any]:
    raise ForeignUriError(f"URI ajena al registro, no se consulta por red: {uri}")


def _esquemas(raiz: Traversable, en_vendor: bool) -> Iterator[tuple[Traversable, bool]]:
    """Cada archivo `.yaml`, `.yml` o `.json` bajo `raiz`, con si cuelga de `vendor/`.

    Salta `fixtures/` y `tests/`. Qué archivos son esquemas lo decide `build_registry`.
    """
    for entrada in sorted(raiz.iterdir(), key=lambda e: e.name):
        if entrada.is_dir():
            if entrada.name not in DIRECTORIOS_SALTADOS:
                yield from _esquemas(entrada, en_vendor or entrada.name == "vendor")
        elif entrada.name.endswith(SUFIJOS_DE_DATOS):
            yield entrada, en_vendor


def _declara_esquema(contenido: Any) -> bool:
    """Un documento cuya raíz declara `$schema` y `$id` es un esquema (BR12.3)."""
    return isinstance(contenido, dict) and "$schema" in contenido and "$id" in contenido


def _uri_de(archivo: Traversable, contenido: Any, en_vendor: bool) -> str:
    identificador = contenido.get("$id") if isinstance(contenido, dict) else None
    if not isinstance(identificador, str):
        raise LoadError(f"{archivo.name}: el esquema no tiene $id de texto")
    if not isinstance(contenido.get("$schema", ""), str):
        raise LoadError(f"{archivo.name}: $schema debe ser texto")
    if not identificador or "#" in identificador or "?" in identificador:
        raise LoadError(
            f"{archivo.name}: el $id no puede ser vacío, con fragmento o con consulta: "
            f"{identificador!r}"
        )
    partes = urlsplit(identificador)
    if partes.scheme:
        if en_vendor:
            return identificador
        raise LoadError(
            f"{archivo.name}: un $id absoluto solo se admite bajo vendor/: {identificador}"
        )
    if partes.netloc or ".." in partes.path.split("/"):
        raise LoadError(f"{archivo.name}: el $id relativo sale de la base: {identificador}")
    return urljoin(BASE_URI, identificador)


def build_registry(raiz: Traversable | None = None) -> Registry[Any]:
    """Registro con todos los esquemas bajo `raiz` (por defecto, los datos del paquete)."""
    if raiz is None:
        raiz = importlib.resources.files("veridicus_contracts")
    recursos = []
    origen: dict[str, str] = {}
    for archivo, en_vendor in _esquemas(raiz, raiz.name == "vendor"):
        contenido = load_file(archivo)
        if not archivo.name.endswith(SUFIJO_DE_ESQUEMA) and not _declara_esquema(contenido):
            continue
        uri = _uri_de(archivo, contenido, en_vendor)
        if uri in origen:
            raise LoadError(
                f"URI repetida {uri}: la declaran {origen[uri]} y {archivo.name}"
            )
        origen[uri] = archivo.name
        recurso = Resource.from_contents(contenido, default_specification=DRAFT202012)
        recursos.append((uri, recurso))
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
