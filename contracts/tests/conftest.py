"""Configuración común de la suite: rutas al árbol de contracts/ y perfil de Hypothesis."""

from pathlib import Path

import pytest
from hypothesis import settings

# Perfil determinista, sin plazo por ejemplo (D6, D7).
settings.register_profile("contracts", derandomize=True, deadline=None)
settings.load_profile("contracts")

CONTRACTS_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def contracts_root() -> Path:
    """Raíz del árbol contracts/."""
    return CONTRACTS_ROOT
