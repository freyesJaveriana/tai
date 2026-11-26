"""Aviso de propósito limitado de VE-01 (BR9.5).

Costura de las pruebas: `cli.composition` lo llama como `notice.load_notice()`, por el nombre del
módulo, para que una prueba lo sustituya con `monkeypatch` (igual que `api.load_catalogs` en U10).
"""

from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

from veridicus_contracts.loaders import LoadError, load_file
from veridicus_errors import ConfigInvalidProfileError


@dataclass(frozen=True)
class Notice:
    """El aviso con su versión, tal como están en `contracts/integrity/notice.v1.yaml`."""

    version: str
    text: str


def _resource() -> Traversable:
    """El archivo versionado de C8 que empaqueta `veridicus_contracts`."""
    return files("veridicus_contracts") / "integrity" / "notice.v1.yaml"


def _invalid(reason: str) -> ConfigInvalidProfileError:
    return ConfigInvalidProfileError(f"aviso de VE-01 no válido: {reason}")


@cache
def load_notice() -> Notice:
    """Lee el aviso del archivo versionado de C8, sin cambiarlo.

    Se lee una sola vez y se recuerda (el escáner lo pide en cada llamada); un fallo no se recuerda.
    Si el archivo falta o no trae versión, lanza `ConfigInvalidProfileError` (CLI, código 3).
    """
    try:
        document: Any = load_file(_resource())
    except (OSError, LoadError) as error:
        raise _invalid("no se pudo leer notice.v1.yaml") from error
    if not isinstance(document, dict):
        raise _invalid("notice.v1.yaml no es un objeto")
    version = document.get("version")
    text = document.get("text")
    if not isinstance(version, str) or not version:
        raise _invalid("falta la versión")
    if not isinstance(text, str) or not text.strip():
        raise _invalid("falta el texto")
    return Notice(version=version, text=text)
