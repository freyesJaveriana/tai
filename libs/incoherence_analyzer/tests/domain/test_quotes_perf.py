"""Rendimiento de la verificación de citas (PR, R-09).

La meta es 50 ms para un turno de 20 000 caracteres; la prueba afirma 150 ms, el margen 3x de la CI.
"""

import time

from veridicus_incoherence_analyzer.domain.quotes import verify_quote

TURN_CHARS = 20_000
LIMIT_S = 0.150


def _long_turn() -> str:
    sentence = "Casilda Roncancio llegó a Villa Rocamora   antes del mediodía.\n"
    return (sentence * (TURN_CHARS // len(sentence) + 1))[:TURN_CHARS]


def test_verifying_a_quote_over_a_20000_character_turn_takes_150_ms_or_less() -> None:
    turn = _long_turn()
    assert len(turn) == TURN_CHARS
    quote = turn[:200] + " […] " + turn[-300:]

    started = time.perf_counter()
    result = verify_quote(turn, quote)
    elapsed = time.perf_counter() - started

    assert result == "verified"
    assert elapsed <= LIMIT_S, f"{elapsed:.3f} s"


def test_a_quote_that_is_not_found_also_takes_150_ms_or_less() -> None:
    turn = _long_turn()

    started = time.perf_counter()
    result = verify_quote(turn, "Esa noche estuvo en el puerto con su hermano.")
    elapsed = time.perf_counter() - started

    assert result == "not_found"
    assert elapsed <= LIMIT_S, f"{elapsed:.3f} s"
