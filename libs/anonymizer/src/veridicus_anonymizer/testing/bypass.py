"""Control negativo de AUTONOMIA-04: puentea la seudonimización solo dentro de las pruebas (PD-7).

STUB de U10-T02 (paso 2): lo implementa el paso 5 de la misma tarea, después del commit rojo.
"""

from typing import Protocol


class Patcher(Protocol):
    """Lo mínimo de `pytest.MonkeyPatch` que necesita el control negativo."""

    def setattr(self, target: object, name: str, value: object) -> None: ...


def bypass_pseudonymization(monkeypatch: Patcher) -> None:
    """Reemplaza `application.generate.pseudonymize` por una función que no enmascara nada."""
    raise NotImplementedError("bypass_pseudonymization lo implementa el paso 5")
