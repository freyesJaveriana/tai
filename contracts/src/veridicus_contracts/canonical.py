"""Huella JCS (RFC 8785) de un objeto JSON (D14, NFR10.15).

`json.dumps(sort_keys=True)` no reproduce la forma de los números de RFC 8785, así que
la serialización canónica sale de `rfc8785`.
"""

import hashlib
from typing import Any

import rfc8785


def canonical_bytes(objeto: Any) -> bytes:
    """Serialización canónica JCS del objeto, en UTF-8."""
    return rfc8785.dumps(objeto)


def sha256_jcs(objeto: Any) -> str:
    """SHA-256, en hexadecimal, de la serialización canónica del objeto."""
    return hashlib.sha256(canonical_bytes(objeto)).hexdigest()
