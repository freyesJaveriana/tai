"""Listas y tablas versionadas del módulo (BR1.2, BR1.5, BR3.1, BR5.2).

STUB de U10-T02: `load_catalogs` lo implementa U10-T03 (paso 6). Los tipos fijan la forma que usan
las pruebas rojas: un catálogo alterado se arma con `dataclasses.replace(load_catalogs(), ...)`.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


class CatalogError(ValueError):
    """Un archivo de `data/` es inválido: el módulo no se construye (falla cerrado, BR2.2)."""


@dataclass(frozen=True)
class RulePattern:
    """Un patrón de detección en `google-re2` con su categoría."""

    id: str
    category: str
    pattern: str


@dataclass(frozen=True)
class ProviderDomain:
    """Dominio fijo de un proveedor. El archivo versionado no trae puerto: siempre es 443."""

    domain: str
    port: int = 443


@dataclass(frozen=True)
class Capability:
    """Modo de salida estructurada y parámetro de esfuerzo de un modelo (BR5.2)."""

    provider: str
    model: str
    structured_mode: Literal["json_schema_native", "forced_tool"]
    effort_parameter: str


@dataclass(frozen=True)
class Catalogs:
    """Las cuatro listas del módulo, ya validadas contra `data/schemas/`."""

    rules: tuple[RulePattern, ...]
    allowed_words: frozenset[str]
    domains: Mapping[str, ProviderDomain]
    capabilities: Mapping[tuple[str, str], Capability]


def load_catalogs(data_dir: Path | None = None) -> Catalogs:
    """Carga y valida `data/` (o `data_dir`); un archivo inválido lanza `CatalogError`."""
    raise NotImplementedError("load_catalogs lo implementa U10-T03")
