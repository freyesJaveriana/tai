"""Verificación determinista de una cita contra el texto de su turno (BR5.5, AUTONOMIA-05).

Función pura, sin E/S. Es la regla del piloto del TG, para que Veridicus y el TG se comporten igual:

- **Solo se normalizan los espacios.** Cada secuencia de espacios en blanco Unicode pasa a un solo
  espacio y se recortan los extremos, en la cita y en el turno. Mayúsculas, tildes, comillas y
  puntuación cuentan: una letra cambiada hace que la cita no verifique.
- **« […] » une fragmentos del mismo turno.** La cita se parte por el separador (corchete, elipsis
  U+2026, corchete, con un espacio a cada lado). Cada fragmento tiene que aparecer en el turno, en
  orden y sin solaparse (búsqueda codiciosa de izquierda a derecha). Un fragmento vacío no verifica.

Que la cita verifique en *otro* turno (`other_turn`) o que el turno no exista (`unknown_turn`) lo
deriva el filtro (BR5.6), que conoce todos los turnos.
"""

from typing import Final, Literal

QuoteCheck = Literal["verified", "not_found"]

# Corchete, elipsis U+2026, corchete, con un espacio a cada lado (ya normalizado).
FRAGMENT_SEPARATOR: Final = " […] "


def normalize_spaces(text: str) -> str:
    """Reemplaza cada secuencia de espacios en blanco Unicode por uno solo y recorta los extremos."""
    return " ".join(text.split())


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
