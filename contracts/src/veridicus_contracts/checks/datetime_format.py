"""Esqueleto de la guardia de fechas (U01-T17, rojo): todavía no comprueba nada."""

from pathlib import Path
from typing import Any


def fecha_valida(valor: str, patron: str) -> bool:
    """Esqueleto: toda fecha es válida."""
    return True


def comprobar_formato(documento: Any) -> list[str]:
    """Esqueleto: sin problemas."""
    return []


def comprobar_documento(archivo: str, documento: Any, patron: str) -> list[str]:
    """Esqueleto: sin problemas."""
    return []


def comprobar(contracts_root: Path) -> list[str]:
    """Esqueleto: sin problemas."""
    return []
