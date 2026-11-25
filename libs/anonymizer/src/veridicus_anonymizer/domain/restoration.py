"""Restauración y marcas alteradas (F6, BR1.3, BR4.1, BR4.2).

STUB de U10-T02: lo implementa U10-T03 (paso 8).
"""

from dataclasses import dataclass
from typing import Any

from veridicus_anonymizer.domain.masking import MaskTable


@dataclass(frozen=True)
class RestorationOutcome:
    """Contenido restaurado y punteros RFC 6901 de las cadenas con marcas alteradas."""

    content: Any
    altered_markers: list[str]


def restore(content: Any, table: MaskTable) -> RestorationOutcome:
    """Restaura las marcas de la tabla en los valores de cadena del JSON ya parseado."""
    raise NotImplementedError("restore lo implementa U10-T03")
