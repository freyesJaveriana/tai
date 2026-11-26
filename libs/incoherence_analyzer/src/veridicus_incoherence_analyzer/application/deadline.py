"""Plazo y cancelación de la corrida (BR7.2, PD-10).

Antes de cada llamada se consulta la cancelación y se calcula el plazo de esa llamada:
`min(model_call_timeout_s, plazo de la corrida - ahora)`. Con el plazo agotado no se llama. Después de
cada llamada se vuelve a comprobar el plazo (PD-10): el *timeout* de `httpx` es por operación, así que
una llamada puede pasarse del restante, y en ese caso la corrida termina en `tiempo_agotado`. El exceso
posible queda declarado como límite en el README.

El reloj es `monotonic`, un nombre global de este módulo: las pruebas lo sustituyen con `monkeypatch`.
"""

import time
from collections.abc import Callable

from veridicus_errors import CancelledError

CancelCheck = Callable[[], bool]

# Costura de las pruebas: el reloj de la corrida.
monotonic: Callable[[], float] = time.monotonic


class DeadlineExpired(Exception):
    """El plazo de la corrida se agotó; `analyze` lo traduce a `tiempo_agotado`."""


class RunClock:
    """El plazo de una corrida y su cancelación."""

    def __init__(
        self, call_timeout_s: float, run_deadline_s: float, cancelled: CancelCheck | None = None
    ) -> None:
        self._call_timeout_s = call_timeout_s
        self._deadline = monotonic() + run_deadline_s
        self._cancelled = cancelled

    def before_call(self) -> float:
        """El *timeout* de la llamada que sigue.

        Lanza `CancelledError` si `cancelled()` es verdadero (la corrida no devuelve salida) y
        `DeadlineExpired` si ya no queda plazo (no se llama).
        """
        if self._cancelled is not None and self._cancelled():
            raise CancelledError("la corrida se canceló: no se hace ninguna llamada más")
        remaining = self._deadline - monotonic()
        if remaining <= 0:
            raise DeadlineExpired("el plazo de la corrida se agotó")
        return float(min(self._call_timeout_s, remaining))  # C25 trae enteros; la petición, float

    def after_call(self) -> None:
        """Lanza `DeadlineExpired` si la llamada que acaba de volver terminó pasado el plazo."""
        if self._deadline - monotonic() <= 0:
            raise DeadlineExpired("el plazo de la corrida se agotó durante la llamada")
