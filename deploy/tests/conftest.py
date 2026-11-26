"""Ninguna prueba hereda la clave real del proveedor del entorno del contenedor (F-04)."""

import pytest
from support import KEY_REF


@pytest.fixture(autouse=True)
def _no_real_provider_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Las pruebas arman su entorno de forma explícita; `os.environ` no lleva la clave real."""
    monkeypatch.delenv(KEY_REF, raising=False)
