"""Pisos de configuración que no caben en C25, porque C25 solo guarda techos (NFRD-U11-03)."""

from typing import Final

# Con un papel externo, `model_call_timeout_s` menor que este piso impide arrancar (BR2).
COMMERCIAL_MIN_CALL_TIMEOUT_S: Final[int] = 270
