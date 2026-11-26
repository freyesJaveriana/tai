"""Filtro determinista de candidatos y deduplicación (BR5.2 a BR5.7, BR9.3, BR4.3; AUTONOMIA-05).

Código puro, sin llamadas. Cada candidato del juez se filtra en un orden fijo y se descarta con el
motivo del **primer** filtro que falla:

1. marca alterada (BR5.3): algún puntero de `altered_markers` cae en el candidato;
2. campo solo con espacios (BR5.4): `hecho`, `observaciones` o el texto de una cita;
3. verificación de `cita_a` y después de `cita_b` contra el texto original de su turno (BR5.5,
   BR5.6): `cita_en_otro_turno` si verifica en exactamente otro turno; `cita_no_verificada` si no
   verifica, si el turno no existe o si la etiqueta del turno no es `T<n>`;
4. (el tramo incremental, BR5.8, se difiere a B11b);
5. vocabulario prohibido en `hecho` y en `observaciones`, fuera de las citas literales (BR9.3);
6. deduplicación por el par no ordenado de (turno, cita normalizada en espacios) (BR4.3): los
   repetidos se unen al de la ventana de menor índice y, dentro de ella, al de menor ordinal, sin
   descarte ni llamada al verificador.

Un puntero de marca alterada que no cae en ningún candidato invalida toda la respuesta
(`InvalidJudgeResponse`, que `analyze` traduce a `salida_invalida`); se comprueba en todas las
ventanas antes de filtrar nada. Los campos faltantes, nulos o vacíos y los tipos fuera de los siete
valores los rechaza antes el esquema local del juez (BR5.1, `application.messages`).
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal, cast

from veridicus_integrity_policy.scan import scan

from veridicus_incoherence_analyzer.domain.ids import SortKey, sort_key
from veridicus_incoherence_analyzer.domain.quotes import normalize_spaces, verify_quote

DiscardReason = Literal[
    "cita_no_verificada",
    "cita_en_otro_turno",
    "marca_alterada",
    "campo_faltante",
    "vocabulario_prohibido",
]

_TURN_LABEL: Final = re.compile(r"T([0-9]+)")
_TEXT_FIELDS: Final = ("hecho", "observaciones")
_QUOTE_FIELDS: Final = ("cita_a", "cita_b")


class InvalidJudgeResponse(Exception):
    """La respuesta del juez no se puede usar: un puntero de marca alterada no cae en ningún
    candidato (BR5.3). Lleva solo la causa, nunca texto del testimonio."""


@dataclass(frozen=True)
class Window:
    """La respuesta del juez para una ventana: sus candidatos y los punteros RFC 6901 de las marcas
    que el modelo alteró (`GenerateResult.altered_markers`)."""

    candidates: Sequence[Mapping[str, Any]]
    altered_markers: Sequence[str]


@dataclass(frozen=True)
class Discard:
    """Un candidato que no salió; sin texto de citas (C6). Los turnos van tal como los nombró el
    juez si tienen la forma `T<n>`; si no, faltan."""

    reason: DiscardReason
    turno_a: str | None = None
    turno_b: str | None = None


@dataclass(frozen=True)
class Survivor:
    """Un candidato que pasó el filtro y llega al verificador, con los números de sus dos turnos y
    su lugar de origen (ventana y ordinal)."""

    candidate: Mapping[str, Any]
    turn_a: int
    turn_b: int
    window: int
    ordinal: int

    def sort_key(self, positions: Mapping[int, int]) -> SortKey:
        """La clave de BR8.2, también el orden en que se verifica (BR6.1)."""
        return sort_key(
            self.turn_a,
            self.turn_b,
            normalize_spaces(self.candidate["cita_a"]["cita"]),
            normalize_spaces(self.candidate["cita_b"]["cita"]),
            self.candidate["hecho"],
            positions,
        )


@dataclass(frozen=True)
class FilterResult:
    survivors: tuple[Survivor, ...]
    discards: tuple[Discard, ...]


def _number(label: str) -> int | None:
    matched = _TURN_LABEL.fullmatch(label)
    return int(matched.group(1)) if matched else None


def _label(label: str) -> str | None:
    return label if _TURN_LABEL.fullmatch(label) else None


def _owns(pointer: str, index: int) -> bool:
    base = f"/hallazgos/{index}"
    return pointer == base or pointer.startswith(base + "/")


def _check_pointers(window: Window) -> None:
    for pointer in window.altered_markers:
        if not any(_owns(pointer, index) for index in range(len(window.candidates))):
            raise InvalidJudgeResponse("una marca alterada no corresponde a ningún candidato")


def _altered(window: Window, index: int) -> bool:
    return any(_owns(pointer, index) for pointer in window.altered_markers)


def _blank(candidate: Mapping[str, Any]) -> bool:
    texts = [candidate[name] for name in _TEXT_FIELDS]
    texts += [candidate[name]["cita"] for name in _QUOTE_FIELDS]
    return any(not normalize_spaces(text) for text in texts)


def _quote_failure(
    quote: Mapping[str, Any], turns: Mapping[int, Mapping[str, Any]]
) -> DiscardReason | None:
    """El motivo por el que una cita no verifica en su turno, o `None` si verifica (BR5.5, BR5.6)."""
    number = _number(quote["turno"])
    turn = turns.get(number) if number is not None else None
    if turn is None:
        return "cita_no_verificada"
    if verify_quote(turn["texto"], quote["cita"]) == "verified":
        return None
    elsewhere = [
        other
        for other, candidate_turn in turns.items()
        if other != number and verify_quote(candidate_turn["texto"], quote["cita"]) == "verified"
    ]
    return "cita_en_otro_turno" if len(elsewhere) == 1 else "cita_no_verificada"


def _forbidden(candidate: Mapping[str, Any], sources: Sequence[str]) -> bool:
    return any(scan(candidate[name], sources) for name in _TEXT_FIELDS)


def _filter_one(
    window: Window,
    index: int,
    turns: Mapping[int, Mapping[str, Any]],
    sources: Sequence[str],
) -> DiscardReason | None:
    candidate = window.candidates[index]
    if _altered(window, index):
        return "marca_alterada"
    if _blank(candidate):
        return "campo_faltante"
    for name in _QUOTE_FIELDS:
        failure = _quote_failure(candidate[name], turns)
        if failure is not None:
            return failure
    if _forbidden(candidate, sources):
        return "vocabulario_prohibido"
    return None


def _turns_of(candidate: Mapping[str, Any]) -> tuple[int, int]:
    """Los números de los dos turnos de un candidato que ya pasó la verificación de citas."""
    first, second = (cast(int, _number(candidate[name]["turno"])) for name in _QUOTE_FIELDS)
    return first, second


def _pair(candidate: Mapping[str, Any], turns: tuple[int, int]) -> frozenset[tuple[int, str]]:
    """La clave de deduplicación: el par no ordenado de (turno, cita normalizada) (BR4.3)."""
    return frozenset(
        (number, normalize_spaces(candidate[name]["cita"]))
        for number, name in zip(turns, _QUOTE_FIELDS, strict=True)
    )


def filter_candidates(
    windows: Sequence[Window], turns: Mapping[int, Mapping[str, Any]]
) -> FilterResult:
    """Filtra los candidatos de todas las ventanas, en orden de ventana y de ordinal.

    `turns` va por número `n` y trae el texto **original** de cada turno: la verificación nunca usa
    los mensajes seudonimizados (BR5.7). Lanza `InvalidJudgeResponse` si un puntero de marca
    alterada no cae en ningún candidato; en ese caso no se filtra nada.
    """
    for window in windows:
        _check_pointers(window)
    sources = [str(turn["texto"]) for turn in turns.values()]
    survivors: list[Survivor] = []
    discards: list[Discard] = []
    seen: set[frozenset[tuple[int, str]]] = set()
    for window_index, window in enumerate(windows):
        for ordinal, candidate in enumerate(window.candidates):
            reason = _filter_one(window, ordinal, turns, sources)
            if reason is not None:
                discards.append(
                    Discard(
                        reason,
                        _label(candidate["cita_a"]["turno"]),
                        _label(candidate["cita_b"]["turno"]),
                    )
                )
                continue
            turn_a, turn_b = _turns_of(candidate)
            key = _pair(candidate, (turn_a, turn_b))
            if key in seen:
                continue
            seen.add(key)
            survivors.append(Survivor(candidate, turn_a, turn_b, window_index, ordinal))
    return FilterResult(tuple(survivors), tuple(discards))
