"""Transporte HTTP falso sobre `httpx.MockTransport` (BR5.5, R-07).

STUB de U10-T02 (paso 2): lo implementa el paso 5 de la misma tarea, después del commit rojo.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass(frozen=True)
class CapturedRequest:
    """Petición cruda: guarda la clave tal cual y solo la oculta al representarla."""

    method: str
    scheme: str
    host: str
    port: int
    path: str
    headers: dict[str, str]
    body: bytes


@dataclass(frozen=True)
class FakeResponse:
    """Una respuesta guionada: grabada o un error simulado."""

    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    raises: Exception | None = None

    @classmethod
    def ok_json(cls, payload: Any) -> "FakeResponse":
        raise NotImplementedError("FakeResponse.ok_json lo implementa el paso 5")

    @classmethod
    def http_error(cls, status: int) -> "FakeResponse":
        raise NotImplementedError("FakeResponse.http_error lo implementa el paso 5")

    @classmethod
    def not_json(cls) -> "FakeResponse":
        raise NotImplementedError("FakeResponse.not_json lo implementa el paso 5")

    @classmethod
    def timeout(cls) -> "FakeResponse":
        raise NotImplementedError("FakeResponse.timeout lo implementa el paso 5")

    @classmethod
    def redirect(cls, location: str) -> "FakeResponse":
        raise NotImplementedError("FakeResponse.redirect lo implementa el paso 5")


class FakeTransport(httpx.MockTransport):
    """Captura cada petición y devuelve las respuestas guionadas, en orden. Nunca abre red."""

    requests: list[CapturedRequest]

    def __init__(self, *responses: FakeResponse) -> None:
        raise NotImplementedError("FakeTransport lo implementa el paso 5")

    @property
    def request_count(self) -> int:
        raise NotImplementedError("FakeTransport lo implementa el paso 5")
