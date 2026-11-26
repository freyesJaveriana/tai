"""Restauración y marcas alteradas (F6, BR1.3, BR4.1, BR4.2).

Recorre los valores de cadena del JSON ya parseado y validado, con su puntero RFC 6901. Cada marca
canónica que está en la tabla de la llamada vuelve a su forma original exacta (con tildes y
mayúsculas), para que U11 verifique la cita contra el turno original sin casos especiales (FR4.4).
Toda forma de marca que no es, carácter por carácter, una marca de la tabla (`[Persona_1]`,
`PERSONA_3]`, `[PERSONA_9]` inventada, `[NOMBRE_1]`) queda sin restaurar y el puntero de esa cadena
entra una sola vez en `altered_markers`, en orden de recorrido. «persona 3» sin corchetes no es una
marca. Nunca se restaura sobre el texto crudo, ni en claves ni en números, y el texto restaurado no
se vuelve a analizar: una marca literal del testimonio vuelve intacta (BR1.7).

El módulo no sabe qué es un hallazgo: U11 descarta el que contiene una ruta listada y rechaza la
cita que perdió una marca al verificarla contra el turno original (BR4.2).
"""

from dataclasses import dataclass
from typing import Any

from veridicus_anonymizer.domain.detection import MARKER_FORM
from veridicus_anonymizer.domain.masking import MaskTable
from veridicus_anonymizer.domain.regex import compile_pattern


@dataclass(frozen=True)
class RestorationOutcome:
    """Contenido restaurado y punteros RFC 6901 de las cadenas con marcas alteradas."""

    content: Any
    altered_markers: list[str]


def _escape(key: str) -> str:
    """Un segmento de puntero RFC 6901: `~` y `/` se escapan."""
    return key.replace("~", "~0").replace("/", "~1")


def _restore_string(text: str, table: MaskTable) -> tuple[str, bool]:
    """La cadena restaurada y si quedó alguna forma de marca que no está en la tabla."""
    pieces: list[str] = []
    cursor = 0
    altered = False
    for match in compile_pattern(MARKER_FORM).finditer(text):
        start, end = match.span()
        original = table.original_for(text[start:end])
        altered = altered or original is None
        pieces.extend((text[cursor:start], text[start:end] if original is None else original))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces), altered


def _walk(node: Any, pointer: str, table: MaskTable, altered: list[str]) -> Any:
    if isinstance(node, str):
        restored, has_altered = _restore_string(node, table)
        if has_altered:
            altered.append(pointer)
        return restored
    if isinstance(node, dict):
        return {
            key: _walk(value, f"{pointer}/{_escape(key)}", table, altered)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_walk(value, f"{pointer}/{i}", table, altered) for i, value in enumerate(node)]
    return node


def restore(content: Any, table: MaskTable) -> RestorationOutcome:
    """Restaura las marcas de la tabla en los valores de cadena del JSON ya parseado."""
    altered: list[str] = []
    return RestorationOutcome(_walk(content, "", table, altered), altered)
