"""Etiqueta de la entrega de `contracts/` (BR12.2, precisión de E-32). Esqueleto del rojo."""

import sys
from collections.abc import Sequence
from pathlib import Path

PREFIJO = "contracts-v"


class VersionInvalida(ValueError):
    """`[project].version` falta o no tiene la forma `MAYOR.MENOR.PARCHE`."""


def etiqueta_esperada(pyproject: Path) -> str:
    """Esqueleto: todavía no calcula la etiqueta."""
    return ""


def main(argumentos: Sequence[str] | None = None) -> int:
    """Esqueleto: todavía no comprueba nada."""
    return 3


if __name__ == "__main__":
    sys.exit(main())
