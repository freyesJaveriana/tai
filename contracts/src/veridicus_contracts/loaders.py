"""Carga de YAML y JSON de los contratos (D5, functional-spec §4.1).

Este módulo es el único punto del paquete que crea el lector de YAML: YAML 1.2 en
modo seguro, sin claves duplicadas y sin etiquetas de objetos. Una prueba AST
(paso 19) vigila que nadie más lo cree. Todo valor leído es compatible con JSON.
"""

import json
from datetime import date, datetime
from importlib.resources.abc import Traversable
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


class LoadError(ValueError):
    """Un archivo de contrato no se pudo leer o no es compatible con JSON."""


def _lector_yaml() -> YAML:
    lector = YAML(typ="safe", pure=True)
    lector.version = (1, 2)
    lector.allow_duplicate_keys = False
    return lector


def _comprobar_json(valor: Any, ruta: str = "$") -> None:
    """Rechaza lo que YAML construye y JSON no tiene (fechas, conjuntos, bytes)."""
    if isinstance(valor, dict):
        for clave, contenido in valor.items():
            if not isinstance(clave, str):
                raise LoadError(f"clave que no es texto en {ruta}: {clave!r}")
            _comprobar_json(contenido, f"{ruta}.{clave}")
    elif isinstance(valor, list):
        for indice, contenido in enumerate(valor):
            _comprobar_json(contenido, f"{ruta}[{indice}]")
    elif isinstance(valor, date | datetime):
        raise LoadError(f"fecha sin comillas en {ruta}: escríbala entre comillas como texto")
    elif valor is not None and not isinstance(valor, str | int | float | bool):
        raise LoadError(f"valor que no es de JSON en {ruta}: {type(valor).__name__}")


def load_yaml_text(texto: str) -> Any:
    """Lee un documento YAML 1.2; rechaza claves duplicadas y etiquetas de objetos."""
    try:
        valor = _lector_yaml().load(texto)
    except YAMLError as error:
        raise LoadError(f"YAML no válido (clave duplicada o etiqueta no permitida): {error}") from error
    _comprobar_json(valor)
    return valor


def _sin_claves_duplicadas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    objeto: dict[str, Any] = {}
    for clave, valor in pares:
        if clave in objeto:
            raise LoadError(f"clave duplicada en JSON: {clave!r}")
        objeto[clave] = valor
    return objeto


def _constante_no_finita(nombre: str) -> Any:
    raise LoadError(f"constante no permitida en JSON: {nombre}")


def load_json_text(texto: str) -> Any:
    """Lee un documento JSON; rechaza claves duplicadas y NaN o Infinity."""
    try:
        return json.loads(
            texto,
            object_pairs_hook=_sin_claves_duplicadas,
            parse_constant=_constante_no_finita,
        )
    except json.JSONDecodeError as error:
        raise LoadError(f"JSON no válido: {error}") from error


def load_file(ruta: Traversable) -> Any:
    """Lee un archivo `.yaml`, `.yml` o `.json` según su sufijo."""
    nombre = ruta.name
    try:
        texto = ruta.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise LoadError(f"{nombre} no es texto UTF-8") from error
    if nombre.endswith((".yaml", ".yml")):
        return load_yaml_text(texto)
    if nombre.endswith(".json"):
        return load_json_text(texto)
    raise LoadError(f"sufijo no admitido en {nombre}: use .yaml, .yml o .json")
