"""Verificación determinista de una cita contra el texto de su turno (BR5.5, AUTONOMIA-05).

Estado: *stub* del paso 1 (U11-T01). Lo implementa U11-T03.
"""

from typing import Literal

QuoteCheck = Literal["verified", "not_found"]


def verify_quote(turn_text: str, quote: str) -> QuoteCheck:
    """Regla del piloto: solo se normalizan los espacios; « […] » une fragmentos del mismo turno,
    en orden y sin solaparse. `other_turn` y `unknown_turn` los deriva el filtro (BR5.6)."""
    raise NotImplementedError("verify_quote: lo implementa U11-T03 (paso 7)")
