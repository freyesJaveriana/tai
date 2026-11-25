"""Control negativo de AUTONOMIA-04: puentea la seudonimización solo dentro de las pruebas (PD-7).

Reemplaza con `monkeypatch` la función interna `pseudonymize` de `application.generate` por una
que entrega los mensajes sin enmascarar y una tabla vacía. La prueba del payload tiene que fallar
con este control (AC11.3.7, BR5.5). `build_anonymizer` no tiene ningún parámetro equivalente, y un
contrato de import-linter impide que el código de producción importe este módulo.
"""

from collections.abc import Sequence
from typing import Protocol

from veridicus_contracts.model_calls import Message

from veridicus_anonymizer.application import generate
from veridicus_anonymizer.domain.catalogs import Catalogs
from veridicus_anonymizer.domain.masking import MaskTable


class Patcher(Protocol):
    """Lo mínimo de `pytest.MonkeyPatch` que necesita el control negativo."""

    def setattr(self, target: object, name: str, value: object) -> None: ...


def _unmasked(messages: Sequence[Message], catalogs: Catalogs) -> tuple[list[Message], MaskTable]:
    """Sustituto de `pseudonymize`: no enmascara nada."""
    return list(messages), MaskTable()


def bypass_pseudonymization(monkeypatch: Patcher) -> None:
    """Reemplaza `application.generate.pseudonymize` por una función que no enmascara nada."""
    monkeypatch.setattr(generate, "pseudonymize", _unmasked)
