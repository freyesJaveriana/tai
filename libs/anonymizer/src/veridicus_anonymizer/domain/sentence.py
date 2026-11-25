"""Qué es «abrir oración» (PD-2, CG-U10-02): una sola definición para todo el módulo.

Una palabra abre oración si está al inicio de un valor de texto o la precede, ignorando espacios,
uno de estos signos: `.`, `?`, `!`, `¿`, `¡`, `:`, `;`, un salto de línea, una comilla de apertura
(«, ", “) o una raya (—). El dominio no lee el reloj ni importa `time`: esto es una función pura.
"""

OPENERS = frozenset('.?!¿¡:;\n\r«"“—')
_SPACES = " \t" + chr(0xA0)  # espacio, tabulador y espacio de no separación


def opens_sentence(text: str, index: int) -> bool:
    """`True` si la palabra que empieza en `index` abre oración."""
    position = index
    while position > 0 and text[position - 1] in _SPACES:
        position -= 1
    return position == 0 or text[position - 1] in OPENERS
