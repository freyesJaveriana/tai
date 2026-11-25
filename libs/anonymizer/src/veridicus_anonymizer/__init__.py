"""Anonimizador de Veridicus (C20, U10).

Superficie pública: `Anonymizer` y `build_anonymizer`. Todo lo demás es interno del módulo.
"""

from veridicus_anonymizer.api import Anonymizer, build_anonymizer

__all__ = ["Anonymizer", "build_anonymizer"]
