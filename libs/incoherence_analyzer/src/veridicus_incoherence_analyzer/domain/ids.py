"""Identificadores deterministas de los hallazgos y su orden (BR8.2).

Los hallazgos se ordenan por (menor posición citada, mayor posición citada, posición de `cita_a`,
`cita_a` normalizada) y se numeran `<entrevista>-C01`, `-C02`… con dos dígitos como mínimo. La
posición es el lugar del turno en la lista ordenada de turnos, no su número `n`. Dos candidatos
distintos podrían empatar en esos cuatro criterios (misma `cita_a`, otra `cita_b`), así que la
clave añade `cita_b` normalizada y el `hecho` para que el orden sea total: la misma entrada da los
mismos id aunque el juez responda en otro orden (BR8.7).
"""

from collections.abc import Iterable, Mapping

SortKey = tuple[int, int, int, str, str, str]


def positions_of(turn_numbers: Iterable[int]) -> dict[int, int]:
    """La posición de cada número de turno en la lista ordenada de turnos."""
    return {number: position for position, number in enumerate(sorted(turn_numbers))}


def sort_key(
    turn_a: int,
    turn_b: int,
    quote_a: str,
    quote_b: str,
    hecho: str,
    positions: Mapping[int, int],
) -> SortKey:
    """La clave de orden de un hallazgo; las citas llegan ya normalizadas en espacios."""
    position_a, position_b = positions[turn_a], positions[turn_b]
    return (
        min(position_a, position_b),
        max(position_a, position_b),
        position_a,
        quote_a,
        quote_b,
        hecho,
    )


def format_id(interview: str, ordinal: int) -> str:
    """`<entrevista>-C<nn>`, con dos dígitos como mínimo (C6, patrón `^.+-C[0-9]{2,}$`)."""
    return f"{interview}-C{ordinal:02d}"
