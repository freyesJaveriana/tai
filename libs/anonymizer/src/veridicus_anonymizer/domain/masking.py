"""Seudonimización (F4) y tabla de correspondencia (BR1.1, BR1.7, BR1.8).

Recorre los mensajes en orden. Si el contenido de un mensaje es JSON (objeto o lista), se trabaja
sobre sus valores de cadena ya decodificados, en orden de documento, sin tocar claves ni números; si
no, sobre el texto completo. Detecta con las reglas, las cadenas con forma de marca y, en `user` y
`assistant`, la red de seguridad; fusiona; propaga por forma exacta con límites de palabra Unicode;
numera por primera aparición, una marca por forma exacta; y reemplaza sin escapar caracteres no ASCII.

`pseudonymize` llama a `detection.apply_rules`, `detection.safety_net`, `build_table` y
`serialize_messages` por atributo de módulo, y crea la tabla con `MaskTable()` buscada como global de
este módulo, para que las pruebas puedan sustituirlas o espiarlas.

El dominio no lee el reloj (F-12): el presupuesto de NFR3.5 lo mide `application/generate.py` y llega
aquí como `has_budget`, una función que dice si todavía queda presupuesto.
"""

import json
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Any, NoReturn

from veridicus_contracts.model_calls import Message

from veridicus_anonymizer.domain import detection
from veridicus_anonymizer.domain.catalogs import Catalogs
from veridicus_anonymizer.domain.detection import DetectedSpan


class MaskingBudgetExceeded(Exception):
    """Se agotó el presupuesto de la seudonimización: la llamada falla cerrada (NFR3.5)."""


class MaskingError(Exception):
    """Los tramos y la tabla no concuerdan con los mensajes; nunca nombra un valor (BR1.8)."""


class MaskTable:
    """Forma exacta -> marca de una sola llamada; vive solo en memoria (BR1.8).

    No tiene `__repr__` ni `__str__` que muestren valores y no se serializa (ni `pickle` ni copia).
    """

    def __init__(self) -> None:
        self._entries: dict[str, str] = {}
        self._originals: dict[str, str] = {}
        self._counters: dict[str, int] = {}

    def __repr__(self) -> str:
        return "MaskTable(<oculta>)"

    def __reduce_ex__(self, protocol: Any) -> NoReturn:
        raise TypeError("la tabla de correspondencia no se serializa ni se copia")

    def __len__(self) -> int:
        """Cuántas formas tiene la tabla; las pruebas la leen justo antes de `clear()`."""
        return len(self._entries)

    @property
    def is_empty(self) -> bool:
        return not self._entries

    def clear(self) -> None:
        self._entries.clear()
        self._originals.clear()
        self._counters.clear()

    def add(self, form: str, category: str) -> str:
        """La marca de una forma; si es nueva, toma el siguiente número de su categoría."""
        marker = self._entries.get(form)
        if marker is None:
            number = self._counters.get(category, 0) + 1
            self._counters[category] = number
            marker = f"[{category}_{number}]"
            self._entries[form] = marker
            self._originals[marker] = form
        return marker

    def marker_for(self, form: str) -> str | None:
        return self._entries.get(form)

    def original_for(self, marker: str) -> str | None:
        """La forma original exacta de una marca canónica de esta llamada, o `None`."""
        return self._originals.get(marker)

    def forms(self) -> list[str]:
        """Las formas que tiene la tabla, en orden de inserción (solo dentro del proceso)."""
        return list(self._entries)


def _word_char(char: str) -> bool:
    return char.isalnum() or char == "_"


def _bounded(text: str, start: int, end: int) -> bool:
    """Límites de palabra Unicode: «Ana» no toca «Anabel»."""
    word = text[start:end]
    if start > 0 and _word_char(word[0]) and _word_char(text[start - 1]):
        return False
    return not (end < len(text) and _word_char(word[-1]) and _word_char(text[end]))


def _occurrences(text: str, forms: dict[str, str]) -> Iterator[DetectedSpan]:
    for form, category in forms.items():
        start = text.find(form)
        while start != -1:
            end = start + len(form)
            if _bounded(text, start, end):
                yield DetectedSpan(start, end, category, "exact_form")
            start = text.find(form, start + 1)


def propagate(
    texts: Sequence[str], spans: Sequence[Sequence[DetectedSpan]]
) -> list[list[DetectedSpan]]:
    """Marca en todos los valores cada forma detectada en alguno, hasta que no crezca más (F4 paso 4).

    El resultado nunca deja una forma detectada fuera de una marca: si un tramo nuevo se solapa con
    otro, la unión es una forma nueva que también se propaga.
    """
    current = [list(group) for group in spans]
    while True:
        forms: dict[str, str] = {}
        for text, group in zip(texts, current, strict=True):
            for span in group:
                forms.setdefault(text[span.start : span.end], span.category)
        grown = [
            detection.merge_spans([*group, *_occurrences(text, forms)])
            for text, group in zip(texts, current, strict=True)
        ]
        if grown == current:
            return current
        current = grown


def build_table(texts: Sequence[str], spans: Sequence[Sequence[DetectedSpan]]) -> MaskTable:
    """Numera por primera aparición y propaga por forma exacta (una marca por forma)."""
    table = MaskTable()
    for text, group in zip(texts, spans, strict=True):
        for span in group:
            table.add(text[span.start : span.end], span.category)
    return table


def _container(content: str) -> Any:
    """El JSON (objeto o lista) de un mensaje, o `None` si el contenido es texto plano."""
    try:
        parsed = json.loads(content)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict | list) else None


def _strings(node: Any) -> Iterator[str]:
    """Los valores de cadena en orden de documento; las claves y los números no cuentan."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


def _units(messages: Sequence[Message]) -> list[tuple[str, str]]:
    """Cada valor de texto de la llamada con el rol del mensaje que lo trae."""
    units: list[tuple[str, str]] = []
    for message in messages:
        container = _container(message.content)
        if container is None:
            units.append((message.role, message.content))
        else:
            units.extend((message.role, text) for text in _strings(container))
    return units


def _replace(text: str, spans: Iterable[DetectedSpan], table: MaskTable) -> str:
    """Reemplaza cada tramo por su marca; equivale a ir de derecha a izquierda."""
    pieces: list[str] = []
    cursor = 0
    for span in spans:
        marker = table.marker_for(text[span.start : span.end])
        if marker is None:
            raise MaskingError("la tabla no tiene una forma detectada")
        pieces.extend((text[cursor : span.start], marker))
        cursor = span.end
    pieces.append(text[cursor:])
    return "".join(pieces)


def _rebuild(node: Any, take: Callable[[str], str]) -> Any:
    if isinstance(node, str):
        return take(node)
    if isinstance(node, dict):
        return {key: _rebuild(value, take) for key, value in node.items()}
    if isinstance(node, list):
        return [_rebuild(value, take) for value in node]
    return node


def serialize_messages(
    messages: Sequence[Message], table: MaskTable, spans: Sequence[Sequence[DetectedSpan]]
) -> list[Message]:
    """Reemplaza de derecha a izquierda y vuelve a serializar el JSON sin escapar no ASCII."""
    pending = iter(spans)

    def take(text: str) -> str:
        group = next(pending, None)
        if group is None:
            raise MaskingError("hay más valores de texto que grupos de tramos")
        return _replace(text, group, table)

    masked: list[Message] = []
    for message in messages:
        container = _container(message.content)
        if container is None:
            content = take(message.content)
        else:
            content = json.dumps(_rebuild(container, take), ensure_ascii=False)
        masked.append(Message(message.role, content))
    if next(pending, None) is not None:
        raise MaskingError("hay más grupos de tramos que valores de texto")
    return masked


def _check(has_budget: Callable[[], bool] | None) -> None:
    if has_budget is not None and not has_budget():
        raise MaskingBudgetExceeded("se agotó el presupuesto de la seudonimización")


def pseudonymize(
    messages: Sequence[Message],
    catalogs: Catalogs,
    *,
    has_budget: Callable[[], bool] | None = None,
) -> tuple[list[Message], MaskTable]:
    """Mensajes seudonimizados y la tabla de la llamada.

    `has_budget` dice si queda presupuesto (NFR3.5); si devuelve `False` entre dos pasos, lanza
    `MaskingBudgetExceeded`. Si algo falla después de crear la tabla, se vacía antes de propagar el
    error (BR1.8).
    """
    units = _units(messages)
    texts = [text for _, text in units]
    detected: list[list[DetectedSpan]] = []
    for role, text in units:
        _check(has_budget)
        found = detection.apply_rules(text, catalogs)
        if role != "system":
            found = [*found, *detection.safety_net(text, catalogs)]
        detected.append(detection.merge_spans(found))
    spans = propagate(texts, detected)
    _check(has_budget)
    table = build_table(texts, spans)
    try:
        masked = serialize_messages(messages, table, spans)
        _check(has_budget)
    except BaseException:
        table.clear()
        raise
    return masked, table
