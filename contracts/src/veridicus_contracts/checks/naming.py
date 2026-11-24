"""Esqueleto de la guardia de nombres (U01-T17, rojo): todavía no comprueba nada."""

import re
from pathlib import Path
from typing import Any

from veridicus_contracts.checks._contratos import contratos_propios

__all__ = ["NOMBRE", "comprobar", "comprobar_catalogo", "comprobar_documento", "comprobar_metricas", "contratos_propios"]

NOMBRE = re.compile("")


def comprobar_documento(archivo: str, documento: Any) -> list[str]:
    """Esqueleto: sin problemas."""
    return []


def comprobar_catalogo(archivo: str, documento: Any) -> list[str]:
    """Esqueleto: sin problemas."""
    return []


def comprobar_metricas(archivo: str, documento: Any) -> list[str]:
    """Esqueleto: sin problemas."""
    return []


def comprobar(contracts_root: Path) -> list[str]:
    """Esqueleto: sin problemas."""
    return []
