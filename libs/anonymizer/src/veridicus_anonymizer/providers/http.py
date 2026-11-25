"""Transporte HTTP de producción (PD-7, R-12, BR3.5).

`default_transport()` es la fábrica que usa `build_anonymizer` cuando no recibe un transporte: TLS
1.2 o superior con verificación de certificado y de nombre, sin reintentos y sin leer el entorno
(`HTTPS_PROXY` o `SSL_CERT_FILE` no cambian nada). No hay ningún ajuste para desactivar la
verificación. `build_client` envuelve cualquier transporte (real o `FakeTransport`) en un cliente
que nunca sigue redirecciones.
"""

import logging
import ssl

import httpx


def tls_context() -> ssl.SSLContext:
    """Contexto TLS estricto: versión mínima 1.2, certificado exigido y nombre comprobado."""
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def default_transport() -> httpx.BaseTransport:
    """Transporte real: TLS >= 1.2 con verificación, sin reintentos y sin variables de entorno."""
    return httpx.HTTPTransport(verify=tls_context(), retries=0, trust_env=False)


def build_client(transport: httpx.BaseTransport) -> httpx.Client:
    """Cliente sobre el transporte dado: sin redirecciones, sin entorno y sin cabeceras propias.

    Silencia los logs informativos de `httpx` y `httpcore` (llevan la URL y el estado de cada
    petición): los logs del módulo llevan solo los campos de BR2.3.
    """
    for name in ("httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
    return httpx.Client(
        transport=transport,
        follow_redirects=False,
        trust_env=False,
        max_redirects=0,
    )
