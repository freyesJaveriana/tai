"""Seudonimización (F4) y tabla de correspondencia (BR1.1, BR1.8).

STUB de U10-T02: lo completa U10-T03 (paso 7). Contrato que fijan las pruebas rojas:

- `pseudonymize` llama a `detection.apply_rules`, `detection.safety_net`, `build_table` y
  `serialize_messages` por atributo de módulo, y crea la tabla con `MaskTable()` buscada como
  global de este módulo, para que las pruebas puedan sustituirlas o espiarlas.
- `MaskTable` no tiene `__repr__` ni `__str__` que muestren valores y `clear()` la vacía (BR1.8).
"""

from collections.abc import Sequence
from typing import Any

from veridicus_contracts.model_calls import Message

from veridicus_anonymizer.domain.catalogs import Catalogs
from veridicus_anonymizer.domain.detection import DetectedSpan


class MaskTable:
    """Forma exacta -> marca de una sola llamada; vive solo en memoria."""

    def __init__(self) -> None:
        self._entries: dict[str, str] = {}

    def __repr__(self) -> str:
        return "MaskTable(<oculta>)"

    @property
    def is_empty(self) -> bool:
        return not self._entries

    def clear(self) -> None:
        self._entries.clear()


def build_table(texts: Sequence[str], spans: Sequence[Sequence[DetectedSpan]]) -> MaskTable:
    """Numera por primera aparición y propaga por forma exacta."""
    raise NotImplementedError("build_table lo implementa U10-T03")


def serialize_messages(messages: Sequence[Message], table: MaskTable, spans: Any) -> list[Message]:
    """Reemplaza de derecha a izquierda y vuelve a serializar el JSON sin escapar no ASCII."""
    raise NotImplementedError("serialize_messages lo implementa U10-T03")


def pseudonymize(
    messages: Sequence[Message], catalogs: Catalogs
) -> tuple[list[Message], MaskTable]:
    """Mensajes seudonimizados y la tabla de la llamada."""
    raise NotImplementedError("pseudonymize lo implementa U10-T03")
