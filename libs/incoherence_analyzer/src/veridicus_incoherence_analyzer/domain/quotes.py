"""Verificación determinista de una cita contra el texto de su turno (BR5.5, AUTONOMIA-05).

Función pura, sin E/S. Es la regla del piloto del TG, para que Veridicus y el TG se comporten igual:

- **Solo se normalizan los espacios.** Cada secuencia de caracteres con la propiedad Unicode
  `White_Space` pasa a un solo espacio y se recortan los extremos, en la cita y en el turno.
  Mayúsculas, tildes, comillas y puntuación cuentan: una letra cambiada hace que la cita no verifique.
- **« […] » une fragmentos del mismo turno.** La cita se parte por el separador (corchete, elipsis
  U+2026, corchete, con un espacio a cada lado). Cada fragmento tiene que aparecer en el turno, en
  orden y sin solaparse (búsqueda codiciosa de izquierda a derecha). Un fragmento vacío no verifica.

Que la cita verifique en *otro* turno (`other_turn`) o que el turno no exista (`unknown_turn`) lo
deriva el filtro (BR5.6), que conoce todos los turnos.
"""

import re
from typing import Final, Literal

QuoteCheck = Literal["verified", "not_found"]

# Corchete, elipsis U+2026, corchete, con un espacio a cada lado (ya normalizado).
FRAGMENT_SEPARATOR: Final = " […] "

# Exactamente los caracteres con la propiedad Unicode `White_Space`, por punto de código: U+0009 a
# U+000D, U+0020, U+0085, U+00A0, U+1680, U+2000 a U+200A, U+2028, U+2029, U+202F, U+205F y U+3000.
# `str.split()` también toma U+001C a U+001F, que no la tienen, y BR5.5 dice «nada más». Los puntos
# de código van como números para que el archivo no lleve caracteres invisibles.
WHITE_SPACE_RANGES: Final = (
    (0x09, 0x0D),
    (0x20, 0x20),
    (0x85, 0x85),
    (0xA0, 0xA0),
    (0x1680, 0x1680),
    (0x2000, 0x200A),
    (0x2028, 0x2029),
    (0x202F, 0x202F),
    (0x205F, 0x205F),
    (0x3000, 0x3000),
)
_WHITE_SPACE: Final = re.compile(
    "["
    + "".join(re.escape(chr(low)) + "-" + re.escape(chr(high)) for low, high in WHITE_SPACE_RANGES)
    + "]+"
)


def normalize_spaces(text: str) -> str:
    """Reemplaza cada secuencia de caracteres `White_Space` de Unicode por un solo espacio y
    recorta los extremos; ningún otro carácter cambia."""
    return _WHITE_SPACE.sub(" ", text).strip(" ")


def verify_quote(turn_text: str, quote: str) -> QuoteCheck:
    """Regla del piloto: solo se normalizan los espacios; « […] » une fragmentos del mismo turno,
    en orden y sin solaparse. `other_turn` y `unknown_turn` los deriva el filtro (BR5.6)."""
    turn = normalize_spaces(turn_text)
    fragments = normalize_spaces(quote).split(FRAGMENT_SEPARATOR)
    position = 0
    for fragment in fragments:
        found = turn.find(fragment, position) if fragment else -1
        if found < 0:
            return "not_found"
        position = found + len(fragment)
    return "verified"
