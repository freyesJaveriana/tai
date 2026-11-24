"""Esqueleto del recorrido de contratos propios (U01-T17, rojo): todavía no recorre nada."""

from collections.abc import Iterator
from pathlib import Path


def contratos_propios(raiz: Path) -> Iterator[tuple[str, Path]]:
    """Esqueleto: sin contratos."""
    return iter(())
