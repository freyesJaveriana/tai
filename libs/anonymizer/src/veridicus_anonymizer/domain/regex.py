"""Envoltorio tipado de `google-re2` (tiempo lineal) para todo el dominio.

El texto del relato nunca se analiza con `re` de la biblioteca estándar: una expresión mal escrita
podría tardar un tiempo exponencial sobre un testimonio (NFR3.5). `google-re2` no publica tipos,
así que este módulo es el único lugar que lo importa y expone solo lo que el dominio usa.
"""

from collections.abc import Iterator, Mapping
from functools import cache
from typing import Protocol

import re2  # type: ignore[import-untyped]  # google-re2 no trae tipos ni py.typed

RegexError: type[Exception] = re2.error


class Match(Protocol):
    """Una coincidencia: solo se usa la posición, en caracteres, de un grupo."""

    def span(self, group: int = 0) -> tuple[int, int]: ...


class Pattern(Protocol):
    """Una expresión compilada con `google-re2`."""

    @property
    def groupindex(self) -> Mapping[str, int]: ...

    def finditer(self, text: str) -> Iterator[Match]: ...


@cache
def compile_pattern(pattern: str) -> Pattern:
    """Compila (y guarda) una expresión; una inválida lanza `RegexError`."""
    compiled: Pattern = re2.compile(pattern)
    return compiled
