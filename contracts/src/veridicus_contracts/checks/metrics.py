"""Esqueleto de la guardia de métricas (U01-T17, rojo): todavía no comprueba nada."""

from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

ETIQUETAS: frozenset[str] = frozenset()


def comprobar_documentos(documentos: Mapping[str, Any], codigos: Collection[str]) -> list[str]:
    """Esqueleto: sin problemas."""
    return []


def comprobar(contracts_root: Path) -> list[str]:
    """Esqueleto: sin problemas."""
    return []
