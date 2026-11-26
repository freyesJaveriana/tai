"""Detección de entidades (BR1.2, BR1.5, BR1.7).

Tres fuentes de tramos `[start, end)` sobre un valor de texto:

- `apply_rules`: las reglas de `DetectionRuleSet` (`google-re2`) y las cadenas con forma de marca
  (`input_marker`, BR1.7), que se tratan como `ENTIDAD`;
- `safety_net`: la red de seguridad ampliada de PD-2 (CG-U10-02). Toda palabra con alguna mayúscula,
  en cualquier posición y aunque vaya pegada con guion, guion bajo o dígitos, que no esté en `AllowedWordList` es `ENTIDAD`, abra oración o no. Las palabras con mayúscula
  seguidas y separadas solo por espacios forman un único tramo (F-11 de la revisión de U10-T02): un
  nombre completo sin tratamiento lleva una sola marca. No se aplica a `system` (lo decide `masking`);
- `merge_spans`: la unión de los tramos que se solapan o se tocan, con la categoría de mayor
  precedencia de la lista de BR1.2.

`masking` llama a estas funciones por atributo de módulo (`detection.apply_rules(...)`) para que las
pruebas puedan sustituirlas. Este módulo no importa `time` ni `datetime` (F-12).
"""

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from veridicus_anonymizer.domain.catalogs import Catalogs
from veridicus_anonymizer.domain.regex import compile_pattern
from veridicus_anonymizer.domain.sentence import opens_sentence

# Orden de precedencia de BR1.2: la primera categoría gana al fusionar.
PRECEDENCE = ("EXPEDIENTE", "IDENTIFICADOR", "PERSONA", "LUGAR", "ENTIDAD")

# Forma de marca de F6 (sin distinguir mayúsculas): canónica `[PERSONA_1]`, con otros separadores o
# espacios `[Persona 3]`, sin corchete de apertura `PERSONA_3]`, o con una categoría inventada.
MARKER_FORM = (
    r"(?i:\[[ ]*(?:persona|lugar|expediente|identificador|entidad)[ _-][ ]*[0-9]+[ ]*\])"
    r"|(?i:(?:persona|lugar|expediente|identificador|entidad)_[0-9]+\]?)"
    r"|\[[A-ZÁÉÍÓÚÑ]+_[0-9]+\]"
)
# Una palabra es una racha de letras, dígitos y guion bajo, unida por guiones, con las secuencias
# `\uXXXX` de un valor que no es JSON dentro de ella. Las secuencias `\n`, `\r` y `\t` escritas con
# barra invertida son separadores: la palabra que sigue se evalúa sola (F-01).
_UNICODE_ESCAPE = r"\\u[0-9A-Fa-f]{4}"
_PIECE = rf"(?:{_UNICODE_ESCAPE}|[\p{{L}}\p{{M}}\p{{N}}_])"
_WORD_PATTERN = rf"\\[nrt]|{_PIECE}+(?:-{_PIECE}+)*"
_BLANKS = " " + chr(0xA0)  # espacio y espacio de no separaci\u00f3n


@dataclass(frozen=True)
class DetectedSpan:
    """Tramo `[start, end)` de un valor de texto que un detector marcó."""

    start: int
    end: int
    category: str
    source: str


def apply_rules(text: str, catalogs: Catalogs) -> list[DetectedSpan]:
    """Tramos que marcan las reglas de `DetectionRuleSet` y las cadenas con forma de marca."""
    spans: list[DetectedSpan] = []
    for rule in catalogs.rules:
        compiled = compile_pattern(rule.pattern)
        group = compiled.groupindex.get("entity")
        for match in compiled.finditer(text):
            start, end = match.span() if group is None else match.span(group)
            if end > start:
                spans.append(DetectedSpan(start, end, rule.category, f"rule:{rule.id}"))
    for match in compile_pattern(MARKER_FORM).finditer(text):
        start, end = match.span()
        spans.append(DetectedSpan(start, end, "ENTIDAD", "input_marker"))
    return spans


def has_capital(word: str) -> bool:
    """`True` si la palabra tiene alguna letra mayúscula en cualquier posición (F-01).

    Las secuencias `\\uXXXX` se leen como la letra que escriben.
    """
    decoded: list[str] = []
    cursor = 0
    for match in compile_pattern(_UNICODE_ESCAPE).finditer(word):
        start, end = match.span()
        decoded.extend((word[cursor:start], chr(int(word[start + 2 : end], 16))))
        cursor = end
    decoded.append(word[cursor:])
    return any(unicodedata.category(c) == "Lu" for c in "".join(decoded))


def safety_net(text: str, catalogs: Catalogs) -> list[DetectedSpan]:
    """Red de seguridad `ENTIDAD` (PD-2): se aplica a `user` y `assistant`, nunca a `system`."""
    runs: list[tuple[int, int]] = []
    for match in compile_pattern(_WORD_PATTERN).finditer(text):
        start, end = match.span()
        token = text[start:end]
        if token.startswith("\\") and len(token) == 2:  # `\n`, `\r` o `\t`: separador
            continue
        if not has_capital(token) or token in catalogs.allowed_words:
            continue
        if runs and text[runs[-1][1] : start].strip(_BLANKS) == "":
            runs[-1] = (runs[-1][0], end)
        else:
            runs.append((start, end))
    return [
        DetectedSpan(
            start,
            end,
            "ENTIDAD",
            "safety_net:opening" if opens_sentence(text, start) else "safety_net:inline",
        )
        for start, end in runs
    ]


def merge_spans(spans: Iterable[DetectedSpan]) -> list[DetectedSpan]:
    """Une los tramos que se solapan o se tocan; nunca recorta (BR1.2)."""
    merged: list[DetectedSpan] = []
    for span in sorted(spans, key=lambda s: (s.start, s.end)):
        if merged and span.start <= merged[-1].end:
            last = merged[-1]
            category = min(last.category, span.category, key=PRECEDENCE.index)
            merged[-1] = DetectedSpan(last.start, max(last.end, span.end), category, last.source)
        else:
            merged.append(span)
    return merged
