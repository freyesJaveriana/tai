"""Transporte HTTP de producción (PD-7, R-12).

STUB de U10-T02: lo implementa U10-T04 (paso 9).
"""

import httpx


def default_transport() -> httpx.BaseTransport:
    """TLS >= 1.2 con verificación, sin redirecciones, sin reintentos y sin variables de entorno."""
    raise NotImplementedError("default_transport lo implementa U10-T04")
