"""Escáner de vocabulario prohibido (BR9.1 a BR9.4, AUTONOMIA-03).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T02.
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Match:
    """Una coincidencia con un término de C8: el término y su posición en el texto."""

    term: str
    start: int
    end: int


def scan(text: str, literal_sources: Sequence[str]) -> list[Match]:
    """Busca los términos de C8 por palabra completa, sin distinguir mayúsculas ni tildes.

    Excluye los tramos entre «…» cuyo contenido aparece literal en alguna de `literal_sources` y la
    cadena completa del aviso de VE-01 (BR9.2). La lista sale del archivo versionado de C8.
    """
    raise NotImplementedError("scan: lo implementa U11-T02 (paso 5)")
